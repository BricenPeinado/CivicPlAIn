"""Read-only integration projections and explicit, allowlisted explanation requests."""
from typing import Literal
from fastapi import APIRouter, Request, HTTPException
from app.schemas.roads import Schema
from app.schemas.ai import Mode
from app.routes.municipal import (strict, envelope, repo, accepted_groups, validate_as_of,
                                 validate_policy_context)
from app.core.municipal_planning_repository import MunicipalPlanningRepository
from app.core.prioritization_repository import PrioritizationRepository
from app.core.official_screening_repository import OfficialScreeningRepository
from app.services.road_conditions import summarize
from app.services.ai.official_evidence import build

router = APIRouter(prefix='/api/v2/planning/decision-support')

def repositories(request):
    path = request.app.state.settings.database_path
    return {'estimate': MunicipalPlanningRepository(path), 'priority': PrioritizationRepository(path),
            'screening': OfficialScreeningRepository(path)}

@router.get('')
def overview(request: Request, snapshot_id: str, as_of_date: str,
             release_id: str | None = None, policy_id: str | None = None):
    strict(request, ['snapshot_id', 'as_of_date', 'release_id', 'policy_id'])
    validate_as_of(as_of_date)
    validate_policy_context(policy_id, snapshot_id, release_id)
    roads = repo(request).records(snapshot_id, 'road')
    groups = accepted_groups(request, snapshot_id, release_id) if release_id else {}
    if not release_id:
        for key, match in repo(request).matches(snapshot_id).items():
            if match['source_kind'] == 'condition' and match['status'] == 'matched':
                groups.setdefault(match['target_road_id'], {})[key] = match
    categories = dict(good=0, fair=0, poor=0, unknown=0)
    eligible = 0
    reasons = {}
    for road in roads:
        matches = groups.get(road['id'], {})
        records = [repo(request).get(snapshot_id, 'condition', key) for key in sorted(matches)]
        summary = summarize(records, matches, road['id'], snapshot_id, as_of_date,
                            release_id=release_id, policy_id=policy_id)
        categories[summary['category']] += 1
        eligible += summary['latest_usable_id'] is not None
        reason = summary['reason'] or 'eligible'
        reasons[reason] = reasons.get(reason, 0) + 1
    histories = {}
    for kind, repository in repositories(request).items():
        try:
            rows = repository.summaries(snapshot_id)
            histories[kind] = {'status': 'available', 'count': len(rows), 'records': rows[:100],
                               'truncated': len(rows) > 100}
        except HTTPException as exc:
            if exc.status_code != 503: raise
            histories[kind] = {'status': 'unavailable', 'count': None, 'records': [],
                               'reason': str(exc.detail), 'truncated': False}
    return envelope(request, {'version': 'decision-context-v1', 'snapshot_id': snapshot_id,
        'as_of_date': as_of_date, 'release_id': release_id, 'policy_id': policy_id,
        'condition': {'roads': len(roads), 'eligible': eligible, 'requiring_review': len(roads)-eligible,
                      'categories': categories, 'reasons': reasons},
        'saved': histories, 'utility_coverage': 'unknown', 'human_review_required': True,
        'meaning': 'Saved runs are separate planning assumptions, not unique projects or actual work. No cross-run totals or automatic latest selection.'}, snapshot_id)

class ExplainRequest(Schema):
    snapshot_id: str
    kind: Literal['estimate', 'priority', 'screening']
    record_id: str
    mode: Mode = 'deterministic'

@router.post('/explanations')
async def explain(request: Request, body: ExplainRequest):
    strict(request, [])
    record = repositories(request)[body.kind].get(body.snapshot_id, body.record_id)
    evidence = build(body.kind, record)
    result = await request.app.state.ai.explain(evidence, 'explain_official', body.mode, request.state.request_id)
    return envelope(request, result.model_dump(mode='json'), body.snapshot_id)
