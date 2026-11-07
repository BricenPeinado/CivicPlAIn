"""FastAPI factory: local storage initialization does not implicitly seed data."""
import sqlite3
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from app.core.config import Settings
from app.core.repository import InvalidQuery, RoadRepository
from app.models.database import initialize
from app.routes.roads import router
from app.routes.planning import router as planning_router
from app.core.planning_repository import PlanningRepository
from app.services.estimates import MissingInputs
from app.core.conflict_repository import ConflictRepository
from app.routes.conflicts import router as conflicts_router


def error(request, status, code, message, fields=None):
    return JSONResponse(status_code=status, content={"error": {
        "code": code, "message": message, "field_errors": fields or [],
        "request_id": getattr(request.state, "request_id", "unavailable")}})


def create_app(settings: Settings | None = None):
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app):
        # Requests return a sanitized 503 if storage is unavailable.
        try:
            initialize(settings.database_path)
        except (sqlite3.Error, OSError):
            pass
        yield

    app = FastAPI(title="CivicPlAIn local API", version="0.1.0", lifespan=lifespan)
    app.state.repository = RoadRepository(settings.database_path)
    app.state.planning = PlanningRepository(settings.database_path)
    app.state.conflicts = ConflictRepository(settings.database_path)
    app.add_middleware(CORSMiddleware, allow_origins=list(settings.allowed_origins),
                       allow_methods=["GET", "POST"], allow_headers=["Accept", "Content-Type"], expose_headers=["X-Request-ID"])

    @app.middleware("http")
    async def request_id(request: Request, call_next):
        request.state.request_id = str(uuid4())
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response

    @app.exception_handler(RequestValidationError)
    async def validation(request, exc):
        return error(request, 422, "VALIDATION_ERROR", "Invalid request fields", [
            {"path": ".".join(map(str, e["loc"])), "reason": e["msg"]} for e in exc.errors()])

    @app.exception_handler(MissingInputs)
    async def missing_inputs(request, exc):
        return error(request, 422, "MISSING_ESTIMATE_INPUTS", str(exc),
                     [{"path": "planning_assumptions", "reason": str(exc)}])

    @app.exception_handler(InvalidQuery)
    async def invalid_query(request, exc):
        return error(request, 422, "VALIDATION_ERROR", str(exc),
                     [{"path": "query", "reason": str(exc)}])

    @app.exception_handler(HTTPException)
    async def http_error(request, exc):
        codes = {404: "NOT_FOUND", 405: "METHOD_NOT_ALLOWED"}
        return error(request, exc.status_code, codes.get(exc.status_code, "HTTP_ERROR"), str(exc.detail))

    @app.exception_handler(sqlite3.Error)
    async def storage(request, exc):
        return error(request, 503, "STORAGE_UNAVAILABLE", "Local storage is unavailable")

    @app.exception_handler(Exception)
    async def unexpected(request, exc):
        return error(request, 500, "INTERNAL_ERROR", "Unexpected service error")

    app.include_router(router)
    app.include_router(planning_router)
    app.include_router(conflicts_router)
    return app


app = create_app()
