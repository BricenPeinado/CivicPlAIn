"""M5 bounded references only; no client evidence, tools, money or mutation operations."""
from fastapi import APIRouter, HTTPException, Request
from app.schemas.ai import (AskRequest, Context, EstimateExplanationRequest, ConflictExplanationRequest,
    ComparisonExplanationRequest, Explanation)
from app.schemas.roads import Envelope
from app.routes.roads import metadata
from app.services.ai.evidence import EvidenceBuilder, EvidenceError
from app.services.scenario_comparison import IncompatibleComparison

router = APIRouter(prefix='/api/v1/ai')


async def explain(request, context, task, mode, question=None):
    state = request.app.state
    try:
        evidence = EvidenceBuilder(state.repository, state.planning, state.conflicts, state.scenarios).build(context)
    except EvidenceError as e:
        raise HTTPException(e.status, str(e)) from None
    except IncompatibleComparison:
        raise HTTPException(409, 'Evaluations have incompatible comparison bases') from None
    except (ValueError, KeyError, TypeError):
        raise HTTPException(409, 'Source snapshot cannot be validated for explanation') from None
    result = await state.ai.explain(evidence, task, mode, request.state.request_id, question)
    return Envelope(data=result, meta=metadata(request))


@router.post('/explain-estimate', response_model=Envelope[Explanation])
async def estimate(request: Request, body: EstimateExplanationRequest):
    return await explain(request, Context(type='estimate', record_ids=[body.estimate_id]), 'explain_estimate', body.mode)


@router.post('/explain-conflict', response_model=Envelope[Explanation])
async def conflict(request: Request, body: ConflictExplanationRequest):
    return await explain(request, Context(type='conflict', record_ids=[body.conflict_id]), 'explain_conflict', body.mode)


@router.post('/explain-scenario-comparison', response_model=Envelope[Explanation])
async def comparison(request: Request, body: ComparisonExplanationRequest):
    return await explain(request, Context(type='comparison', record_ids=sorted(body.evaluation_ids)), 'explain_comparison', body.mode)


@router.post('/ask', response_model=Envelope[Explanation])
async def ask(request: Request, body: AskRequest):
    return await explain(request, body.context, 'ask', body.mode, body.question)


@router.get('/status')
def status(request: Request):
    s = request.app.state.ai.settings
    return Envelope(data=dict(default_mode='deterministic', provider_configured=s.configured,
        configured_provider=s.provider, model_label=s.model if s.configured else None,
        timeout_seconds=s.timeout_seconds, max_output_tokens=s.max_output_tokens,
        max_calls_per_hour=s.max_calls_per_hour, live_provider_verified=False,
        review_required=True, free_text_generation=False), meta=metadata(request))


@router.get('/interactions/{interaction_id}')
def interaction(request: Request, interaction_id: str):
    audit = request.app.state.ai.audit.get(interaction_id)
    if audit is None: raise HTTPException(404, 'AI interaction not found')
    return Envelope(data=audit, meta=metadata(request))


# Existing proposed review route is kept at the /api/v1 boundary, separate from AI calls.
review_router = APIRouter(prefix='/api/v1')
from app.schemas.ai import ReviewRequest


@review_router.post('/scenario-evaluations/{evaluation_id}/reviews', status_code=201)
def review(request: Request, evaluation_id: str, body: ReviewRequest):
    if request.app.state.scenarios.evaluation(evaluation_id) is None:
        raise HTTPException(404, 'Evaluation not found')
    event = request.app.state.ai.audit.review(evaluation_id, body, request.state.request_id)
    return Envelope(data=event, meta=metadata(request))
