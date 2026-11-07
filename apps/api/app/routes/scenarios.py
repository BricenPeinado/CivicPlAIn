"""M4 REST boundary; proposed actions never mutate real projects."""
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import ValidationError

from app.core.scenario_inputs import freeze, ScenarioInputError
from app.core.scenario_repository import RevisionConflict
from app.routes.roads import metadata
from app.schemas.roads import Envelope
from app.schemas.conflicts import AnalysisParameters
from app.schemas.scenarios import (Scenario, ScenarioDraft, ScenarioPatch, ActionMutation,
    EvaluateRequest, ScenarioEvaluation, ComparisonRequest, ScenarioComparison)
from app.services.scenarios import evaluate, action_cost
from app.services.scenario_comparison import compare, IncompatibleComparison

router = APIRouter(prefix='/api/v1')


def require(request, sid):
    record = request.app.state.scenarios.get(sid)
    if record is None:
        raise HTTPException(404, 'Scenario not found')
    return record


def validated_context(request, draft, sid):
    try:
        context = freeze(draft, request.app.state.repository, request.app.state.planning, request.app.state.conflicts, sid)
        # Validate asserted source quantities even when saving an incomplete draft.
        for a in draft.actions:
            action_cost(a, context)
        active_count = len(draft.actions) + len(set(draft.external_project_ids) - {o.project_id for o in draft.project_overrides})
        if active_count > 50:
            raise ValueError('hypothetical analysis supports at most 50 projects including actions')
        return context
    except ScenarioInputError as exc:
        raise HTTPException(exc.status, str(exc)) from None
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from None


def save_change(request, old, draft, expected):
    validated_context(request, draft, old.id)
    try:
        record = request.app.state.scenarios.save(draft, old.id, expected)
    except RevisionConflict as exc:
        raise HTTPException(409, str(exc)) from None
    return Envelope(data=record, meta=metadata(request))


@router.post('/scenarios', status_code=201, response_model=Envelope[Scenario])
def create(request: Request, body: ScenarioDraft):
    sid = str(uuid4())
    validated_context(request, body, sid)
    return Envelope(data=request.app.state.scenarios.save(body, sid), meta=metadata(request))


@router.get('/scenarios', response_model=Envelope[list[Scenario]])
def listing(request: Request, limit: int = Query(default=30, ge=1, le=100), after: str = Query(default='', max_length=100)):
    records = request.app.state.scenarios.list(after, limit)
    meta = metadata(request)
    if len(records) > limit:
        meta.next_cursor = records[limit-1].id  # explicit stable-ID cursor, passed as after
    return Envelope(data=records[:limit], meta=meta)


@router.get('/scenarios/{scenario_id}', response_model=Envelope[Scenario])
def detail(request: Request, scenario_id: str):
    return Envelope(data=require(request, scenario_id), meta=metadata(request))


@router.patch('/scenarios/{scenario_id}', response_model=Envelope[Scenario])
def patch(request: Request, scenario_id: str, body: ScenarioPatch):
    old = require(request, scenario_id)
    return save_change(request, old, body.draft, body.expected_revision)


@router.post('/scenarios/{scenario_id}/actions', status_code=201, response_model=Envelope[Scenario])
def add_action(request: Request, scenario_id: str, body: ActionMutation):
    old = require(request, scenario_id)
    if any(a.id == body.action.id for a in old.actions):
        raise HTTPException(409, 'Action ID already exists')
    raw = old.model_dump(include=set(ScenarioDraft.model_fields))
    raw['actions'].append(body.action.model_dump())
    try:
        draft = ScenarioDraft.model_validate(raw)
    except ValidationError:
        raise HTTPException(422, 'Action violates scenario scope, date or precedence constraints') from None
    return save_change(request, old, draft, body.expected_revision)


@router.patch('/scenarios/{scenario_id}/actions/{action_id}', response_model=Envelope[Scenario])
def patch_action(request: Request, scenario_id: str, action_id: str, body: ActionMutation):
    old = require(request, scenario_id)
    if not any(a.id == action_id for a in old.actions):
        raise HTTPException(404, 'Action not found')
    if body.action.id != action_id:
        raise HTTPException(422, 'Action ID cannot change')
    raw = old.model_dump(include=set(ScenarioDraft.model_fields))
    raw['actions'] = [body.action.model_dump() if a['id'] == action_id else a for a in raw['actions']]
    try:
        draft = ScenarioDraft.model_validate(raw)
    except ValidationError:
        raise HTTPException(422, 'Action violates scenario scope, date or precedence constraints') from None
    return save_change(request, old, draft, body.expected_revision)


@router.delete('/scenarios/{scenario_id}/actions/{action_id}', response_model=Envelope[Scenario])
def delete_action(request: Request, scenario_id: str, action_id: str, expected_revision: int = Query(ge=1)):
    old = require(request, scenario_id)
    if not any(a.id == action_id for a in old.actions):
        raise HTTPException(404, 'Action not found')
    raw = old.model_dump(include=set(ScenarioDraft.model_fields))
    raw['actions'] = [a for a in raw['actions'] if a['id'] != action_id]
    try:
        draft = ScenarioDraft.model_validate(raw)
    except ValidationError:
        raise HTTPException(422, 'Remove dependent precedence/replacement references before deleting this action') from None
    return save_change(request, old, draft, expected_revision)


@router.post('/scenarios/{scenario_id}/evaluate', response_model=Envelope[ScenarioEvaluation])
def run(request: Request, scenario_id: str, body: EvaluateRequest):
    scenario = require(request, scenario_id)
    if scenario.revision != body.expected_revision:
        raise HTTPException(409, 'Scenario changed; reload before evaluating')
    context = validated_context(request, scenario, scenario.id)
    try:
        result = evaluate(scenario, context, AnalysisParameters(**body.model_dump(exclude={'expected_revision'})))
        record = request.app.state.scenarios.save_evaluation(result)
    except RevisionConflict as exc:
        raise HTTPException(409, str(exc)) from None
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from None
    return Envelope(data=record, meta=metadata(request))


@router.get('/scenario-evaluations/{evaluation_id}', response_model=Envelope[ScenarioEvaluation])
def evaluation(request: Request, evaluation_id: str):
    record = request.app.state.scenarios.evaluation(evaluation_id)
    if record is None:
        raise HTTPException(404, 'Evaluation not found')
    return Envelope(data=record, meta=metadata(request))


@router.get('/scenarios/{scenario_id}/evaluations', response_model=Envelope[list[ScenarioEvaluation]])
def history(request: Request, scenario_id: str, limit: int = Query(default=30, ge=1, le=100), offset: int = Query(default=0, ge=0)):
    require(request, scenario_id)
    records = request.app.state.scenarios.evaluations(scenario_id)
    meta = metadata(request)
    if len(records) > offset + limit:
        meta.next_cursor = str(offset + limit)
    return Envelope(data=records[offset:offset+limit], meta=meta)


@router.post('/scenario-comparisons', response_model=Envelope[ScenarioComparison])
def comparison(request: Request, body: ComparisonRequest):
    records = [request.app.state.scenarios.evaluation(eid) for eid in body.evaluation_ids]
    if any(e is None for e in records):
        raise HTTPException(404, 'Evaluation not found')
    try:
        result = compare(records)
    except IncompatibleComparison as exc:
        raise HTTPException(409, str(exc)) from None
    return Envelope(data=result, meta=metadata(request))
