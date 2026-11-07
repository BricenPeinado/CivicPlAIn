"""M3 REST orchestration; no spatial or schedule calculations in routes."""
import base64
import json
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query, Request

from app.core.repository import InvalidQuery, decode_cursor
from app.routes.roads import metadata
from app.schemas.conflicts import WorkProject, AnalysisParameters, AnalysisRequest, ConflictAnalysis, ConflictFinding
from app.schemas.roads import Envelope
from app.services.conflicts import analyze

router = APIRouter(prefix='/api/v1')


def require_filters(request, road_id=None, project_id=None, analysis_id=None):
    if road_id and request.app.state.repository.get(road_id) is None:
        raise HTTPException(404, 'Road segment not found')
    if project_id and request.app.state.conflicts.project(project_id) is None:
        raise HTTPException(404, 'Project not found')
    if analysis_id and request.app.state.conflicts.analysis(analysis_id) is None:
        raise HTTPException(404, 'Analysis not found')


def page(request, records, limit, cursor, filters):
    snapshot = request.app.state.repository.snapshot()
    filters = {'endpoint': request.url.path, 'filters': filters}
    after = decode_cursor(cursor, snapshot, filters)
    records = [r for r in records if r.id > after]
    selected = records[:limit]
    next_cursor = None
    if len(records) > limit:
        next_cursor = base64.urlsafe_b64encode(json.dumps(dict(after=selected[-1].id, snapshot=snapshot, bbox=filters)).encode()).decode()
    return Envelope(data=selected, meta=metadata(request, next_cursor))


@router.get('/projects', response_model=Envelope[list[WorkProject]])
def projects(request: Request, road_segment_id: str | None = None,
             kind: Literal['road_repair', 'utility', 'other'] | None = None,
             schedule_status: Literal['planned', 'tentative', 'active', 'completed', 'cancelled', 'unknown'] | None = None,
             limit: Annotated[int, Query(ge=1, le=100)] = 30, cursor: str | None = None):
    require_filters(request, road_id=road_segment_id)
    records = [p for p in request.app.state.conflicts.projects() if (not road_segment_id or road_segment_id in p.road_segment_ids)
               and (not kind or p.kind == kind) and (not schedule_status or p.schedule_status == schedule_status)]
    return page(request, records, limit, cursor, [road_segment_id, kind, schedule_status])


@router.get('/projects/{project_id}', response_model=Envelope[WorkProject])
def project(request: Request, project_id: str):
    record = request.app.state.conflicts.project(project_id)
    if record is None:
        raise HTTPException(404, 'Project not found')
    return Envelope(data=record, meta=metadata(request))


@router.post('/conflicts/analyze', response_model=Envelope[ConflictAnalysis])
def analysis(request: Request, body: AnalysisRequest):
    if request.app.state.repository.snapshot() != body.dataset_snapshot_id:
        raise HTTPException(409, 'Dataset snapshot mismatch')
    records = [request.app.state.conflicts.project(pid) for pid in body.project_ids]
    if any(p is None for p in records):
        raise HTTPException(404, 'Project not found')
    if any(p.dataset_snapshot_id != body.dataset_snapshot_id for p in records):
        raise HTTPException(409, 'Project snapshot mismatch')
    roads, _ = request.app.state.repository.list(100, None, None)
    refs = sorted({e for p in records for e in p.evidence_ids} | {e for r in roads for e in r.evidence_ids})
    sources = [request.app.state.repository.evidence(e) for e in refs]
    if any(e is None for e in sources):
        raise HTTPException(409, 'Input evidence is unavailable')
    try:
        result = analyze(records, roads, AnalysisParameters(**body.model_dump(include=set(AnalysisParameters.model_fields))), sources)
    except ValueError:
        raise InvalidQuery('Invalid project references or analysis inputs') from None
    saved = request.app.state.conflicts.save(result)
    return Envelope(data=saved, meta=metadata(request))


@router.get('/conflict-analyses/{analysis_id}', response_model=Envelope[ConflictAnalysis])
def saved_analysis(request: Request, analysis_id: str):
    result = request.app.state.conflicts.analysis(analysis_id)
    if result is None:
        raise HTTPException(404, 'Analysis not found')
    return Envelope(data=result, meta=metadata(request))


@router.get('/conflicts', response_model=Envelope[list[ConflictFinding]])
def findings(request: Request, project_id: str | None = None, road_segment_id: str | None = None,
             analysis_id: str | None = None, limit: Annotated[int, Query(ge=1, le=100)] = 30, cursor: str | None = None):
    require_filters(request, road_segment_id, project_id, analysis_id)
    records = [f for f in request.app.state.conflicts.findings() if (not project_id or project_id in f.project_ids)
               and (not road_segment_id or road_segment_id in f.affected_road_ids) and (not analysis_id or f.analysis_id == analysis_id)]
    return page(request, records, limit, cursor, [project_id, road_segment_id, analysis_id])


@router.get('/conflicts/{finding_id}', response_model=Envelope[ConflictFinding])
def finding(request: Request, finding_id: str):
    record = request.app.state.conflicts.finding(finding_id)
    if record is None:
        raise HTTPException(404, 'Conflict finding not found')
    return Envelope(data=record, meta=metadata(request))
