"""Separate indicative street-name presentation, never engineering evidence."""
from typing import Annotated, Literal
from fastapi import APIRouter, Query, Request
from pydantic import BaseModel
from app.routes.municipal import strict

router = APIRouter(prefix='/api/v2/standardized')
Limit = Annotated[int, Query(ge=1, le=100)]
Offset = Annotated[int, Query(ge=0, le=1000000)]


class Profile(BaseModel):
    road_id: str
    street_key: str
    street_name: str | None
    segment_id: str | None
    object_id: str | None
    geometry: dict
    source_revision_id: str
    street_observation_count: int
    permits_on_street: int
    latest_rating: float | None
    latest_inspection_at: str | None
    display_condition: Literal['Good', 'Fair', 'Poor', 'Unknown', 'Unclassified']
    display_basis: str | None


class Pavement(BaseModel):
    road_id: str
    observation_id: str
    on_street: str | None
    from_street: str | None
    to_street: str | None
    rating: float | None
    display_condition: str | None
    inspection_at: str | None
    geometry: dict | None
    association_basis: Literal['on_street_name']
    source_revision_id: str
    source_row_key: str | None
    non_rating_reason: str | None


class Permit(BaseModel):
    road_id: str
    permit_id: str
    permit_number: str | None
    permit_type: str | None
    permit_status: str | None
    on_street: str | None
    from_street: str | None
    to_street: str | None
    issue_date: str | None
    valid_from: str | None
    valid_to: str | None
    association_basis: Literal['on_street_name']
    source_revision_id: str


def envelope(snapshot, road, data, total=None, next_offset=None):
    return {'data': data, 'meta': {'contract_version': 'standardized-read-v1',
        'snapshot_id': snapshot, 'road_id': road, 'classification': 'derived_calculation',
        'association_basis': 'on_street_name', 'verified_segment_condition': False,
        'actual_construction_schedule': 'unknown', 'total_matching': total, 'next_offset': next_offset}}


@router.get('/roads/{road_id}')
def profile(request: Request, road_id: str, snapshot_id: str):
    strict(request, ['snapshot_id'])
    repo = request.app.state.standardized
    with repo.connection(snapshot_id) as conn:
        data = Profile.model_validate(repo.profile(conn, road_id)).model_dump()
    return envelope(snapshot_id, road_id, data)


@router.get('/roads/{road_id}/{kind}')
def related(request: Request, road_id: str, kind: Literal['pavement', 'permits'], snapshot_id: str,
            limit: Limit = 10, offset: Offset = 0):
    strict(request, ['snapshot_id', 'limit', 'offset'])
    repo = request.app.state.standardized
    with repo.connection(snapshot_id) as conn:
        rows, total, next_offset = repo.page(conn, road_id, kind, limit, offset)
        model = Pavement if kind == 'pavement' else Permit
        data = [model.model_validate(row).model_dump() for row in rows]
    return envelope(snapshot_id, road_id, data, total, next_offset)
