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
from app.core.http_limits import RequestLimits
from app.core.repository import InvalidQuery, RoadRepository
from app.models.database import initialize
from app.routes.roads import router
from app.routes.planning import router as planning_router
from app.core.planning_repository import PlanningRepository
from app.services.estimates import MissingInputs
from app.core.conflict_repository import ConflictRepository
from app.routes.conflicts import router as conflicts_router
from app.core.scenario_repository import ScenarioRepository
from app.routes.scenarios import router as scenarios_router
from app.routes.ai import router as ai_router, review_router
from app.core.ai_repository import AIInteractionAuditRepository
from app.services.ai.providers import AISettings, OpenAIProvider
from app.services.ai.explanations import AIExplanationService
from app.core.municipal_repository import MunicipalRepository
from app.routes.municipal import router as municipal_router


def error(request, status, code, message, fields=None):
    return JSONResponse(status_code=status, content={"error": {
        "code": code, "message": message, "field_errors": fields or [],
        "request_id": getattr(request.state, "request_id", "unavailable")}})


def create_app(settings: Settings | None = None, ai_settings=None, ai_provider=None):
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
    app.state.settings = settings
    app.state.municipal = MunicipalRepository(settings.database_path)
    app.state.planning = PlanningRepository(settings.database_path)
    app.state.conflicts = ConflictRepository(settings.database_path)
    app.state.scenarios = ScenarioRepository(settings.database_path)
    ai_settings = ai_settings or AISettings()
    app.state.ai = AIExplanationService(ai_settings, ai_provider or OpenAIProvider(ai_settings), AIInteractionAuditRepository(settings.database_path))
    app.add_middleware(RequestLimits, allowed_origins=settings.allowed_origins)
    app.add_middleware(CORSMiddleware, allow_origins=list(settings.allowed_origins),
                       allow_methods=["GET", "POST", "PATCH", "DELETE"], allow_headers=["Accept", "Content-Type"], expose_headers=["X-Request-ID"])

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
        for code in ['MIGRATION_REQUIRED','VIEWPORT_TOO_BROAD','SOURCE_LAYER_UNAVAILABLE']:
            if str(exc.detail).startswith(code+':'):
                codes[exc.status_code]=code
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
    app.include_router(scenarios_router)
    app.include_router(ai_router)
    app.include_router(review_router)
    app.include_router(municipal_router)
    return app


app = create_app()
