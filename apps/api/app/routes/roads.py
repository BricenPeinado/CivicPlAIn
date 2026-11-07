import math
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from app.core.repository import InvalidQuery
from app.schemas.roads import Envelope, Evidence, Feature, FeatureCollection, Health, Meta, Road

router = APIRouter(prefix="/api/v1")
WARNINGS = ["DEMO DATA: schematic synthetic roads and conditions; not municipal observations.",
            "Utility coverage is unknown. This map does not establish excavation safety."]


def metadata(request: Request, cursor=None):
    return Meta(request_id=request.state.request_id,
                dataset_snapshot_id=request.app.state.repository.snapshot(),
                warnings=WARNINGS, next_cursor=cursor)


def parse_bbox(bbox):
    if bbox is None:
        return None
    try:
        values = [float(v) for v in bbox.split(",")]
        if (len(values) != 4 or not all(math.isfinite(v) for v in values)
                or not -180 <= values[0] < values[2] <= 180
                or not -90 <= values[1] < values[3] <= 90):
            raise ValueError
        return values
    except ValueError:
        raise InvalidQuery("bbox requires west,south,east,north with valid increasing bounds") from None


def query_roads(request, bbox, limit, cursor):
    return request.app.state.repository.list(limit, cursor, parse_bbox(bbox))


@router.get("/health", response_model=Envelope[Health])
def health(request: Request):
    return Envelope(data=Health(data_ready=request.app.state.repository.count() > 0),
                    meta=metadata(request))


@router.get("/road-segments", response_model=Envelope[list[Road]])
def roads(request: Request, bbox: str | None = None,
          limit: Annotated[int, Query(ge=1, le=100)] = 30, cursor: str | None = None):
    records, next_cursor = query_roads(request, bbox, limit, cursor)
    return Envelope(data=records, meta=metadata(request, next_cursor))


@router.get("/road-segments/geojson", response_model=FeatureCollection,
            responses={200: {"content": {"application/geo+json": {}}}})
def geojson(request: Request, bbox: str | None = None,
            limit: Annotated[int, Query(ge=1, le=100)] = 30, cursor: str | None = None):
    records, next_cursor = query_roads(request, bbox, limit, cursor)
    response = FeatureCollection(features=[Feature(id=road.id, geometry=road.geometry,
        properties=road.model_dump(mode="json", exclude={"geometry"})) for road in records],
        meta=metadata(request, next_cursor))
    return JSONResponse(response.model_dump(mode="json"), media_type="application/geo+json")


@router.get("/road-segments/{road_id}", response_model=Envelope[Road])
def road(request: Request, road_id: str):
    record = request.app.state.repository.get(road_id)
    if record is None:
        raise HTTPException(404, "Road segment not found")
    return Envelope(data=record, meta=metadata(request))


@router.get("/evidence-sources/{evidence_id}", response_model=Envelope[Evidence])
def evidence(request: Request, evidence_id: str):
    record = request.app.state.repository.evidence(evidence_id)
    if record is None:
        raise HTTPException(404, "Evidence source not found")
    return Envelope(data=record, meta=metadata(request))
