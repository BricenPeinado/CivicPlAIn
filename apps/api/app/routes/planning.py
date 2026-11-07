"""M2 REST orchestration; arithmetic stays in the pure domain service."""
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request

from app.routes.roads import metadata
from app.schemas.planning import Assessment, Estimate, EstimateRequest, OptionComparison, RepairOption
from app.schemas.roads import Envelope
from app.services.estimates import MissingInputs, calculate, canonical_hash, suitability

router = APIRouter(prefix='/api/v1')


def require_road(request, road_id):
    road = request.app.state.repository.get(road_id)
    if road is None:
        raise HTTPException(404, 'Road segment not found')
    return road


@router.get('/road-segments/{road_id}/conditions', response_model=Envelope[list[Assessment]])
def conditions(request: Request, road_id: str):
    require_road(request, road_id)
    records = request.app.state.planning.assessments(road_id)
    latest = request.app.state.planning.latest(road_id)
    meta = metadata(request)
    meta.latest_usable_id = latest.id if latest else None
    return Envelope(data=records, meta=meta)


@router.get('/repair-options', response_model=Envelope[list[RepairOption]])
def options(request: Request):
    return Envelope(data=request.app.state.planning.options(), meta=metadata(request))


@router.get('/road-segments/{road_id}/repair-options', response_model=Envelope[list[OptionComparison]])
def comparison(request: Request, road_id: str):
    road = require_road(request, road_id)
    assessment = request.app.state.planning.latest(road_id)
    results = []
    for option in request.app.state.planning.options():
        try:
            preview = calculate(road, assessment, option)
            reason = None
        except MissingInputs as exc:
            preview, reason = None, str(exc)
        results.append(OptionComparison(option=option, suitability=suitability(road, assessment, option),
            preview=preview, unavailable_reason=reason))
    return Envelope(data=results, meta=metadata(request))


@router.post('/estimates', status_code=201, response_model=Envelope[Estimate])
def create_estimate(request: Request, body: EstimateRequest):
    road = require_road(request, body.road_segment_id)
    if body.dataset_snapshot_id != road.dataset_snapshot_id:
        raise HTTPException(409, 'Dataset snapshot mismatch')
    option = next((o for o in request.app.state.planning.options() if o.id == body.repair_option_id), None)
    if option is None:
        raise HTTPException(404, 'Repair option not found')
    assessment = request.app.state.planning.latest(road.id)
    result = calculate(road, assessment, option, body.planning_assumptions)
    refs = [r for r in result.evidence_ids if r != 'user-planning-assumption']
    evidence = [request.app.state.repository.evidence(r) for r in refs]
    if any(e is None for e in evidence):
        raise HTTPException(409, 'Input evidence is unavailable')
    snapshot = dict(road=road.model_dump(mode='json'), assessment=assessment.model_dump(mode='json') if assessment else None,
        option=option.model_dump(mode='json'), request=body.model_dump(mode='json'),
        evidence=[e.model_dump(mode='json') for e in evidence], method_version=result.method_version)
    if body.planning_assumptions:
        snapshot['user-planning-assumption'] = body.planning_assumptions.model_dump(mode='json')
    record = Estimate(**result.model_dump(), id=str(uuid4()), created_at=datetime.now(timezone.utc).isoformat(),
        dataset_snapshot_id=road.dataset_snapshot_id, input_snapshot=snapshot, input_hash=canonical_hash(snapshot),
        result_hash=canonical_hash(result.model_dump(mode='json')))
    request.app.state.planning.save(record)
    return Envelope(data=record, meta=metadata(request))


@router.get('/estimates/{estimate_id}', response_model=Envelope[Estimate])
def estimate(request: Request, estimate_id: str):
    record = request.app.state.planning.get_estimate(estimate_id)
    if record is None:
        raise HTTPException(404, 'Estimate not found')
    return Envelope(data=record, meta=metadata(request))
