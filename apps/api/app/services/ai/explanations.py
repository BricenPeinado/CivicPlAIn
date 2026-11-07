"""Fail-closed selection validation and source-only rendering."""
import asyncio
import re
from datetime import datetime, timezone
from uuid import uuid4
from pydantic import ValidationError
from app.schemas.ai import Explanation, Finding, ProviderSelection
from app.services.ai.evidence import validate_context
from app.services.ai.providers import CODES, DeterministicFallbackProvider, ProviderFailure, UsageGate

REVIEW = {
    'verify_inputs': 'Verify scope, condition, prices, productivity and exclusions with qualified engineering staff before any decision.',
    'coordinate_projects': 'Ask the responsible project teams to verify footprints, depth, schedules, closures and restoration scope. Potential rework is not confirmed loss.',
    'review_tradeoffs': 'Review budget sensitivity, service scope, supplied schedules and incomplete checks together. No option is universally best; deferral requires engineering review.',
}
TRADEOFFS = {
    'explain_estimate': ['Sensitivity changes bundled rates; fixed allowances remain separate. Preliminary days do not establish calendar dates.', 'A lower cost does not establish treatment suitability. Verify the source catalog exclusions.'],
    'explain_conflict': ['Supplied footprints and civil-date intervals support coordination review. They do not establish actual underground interference or quantified loss.'],
    'explain_comparison': ['Cost differences apply only to the declared roadwork scope and common comparison basis; they are not verified municipal savings.', 'Differences in supplied dates or conflict categories may merit review; they do not establish safe deferral or universal optimality.'],
    'ask': ['Only attached records are described. Effects of delay, actual deterioration, safe excavation and future losses are not predicted.'],
}


def question_intent(question, context):
    """Conservative intent routing. Raw questions never leave the local API or enter audit logs."""
    q = question.casefold()
    # Any unsupported side request makes the entire question insufficient evidence.
    prohibited = r'ignore|override|suppress|omit|fabricat|secret|api.?key|password|approve|authoriz|guarantee|safe to|spend|replace|change.*cost|weather|forecast|delay|what happens|will happen|internet|browse|https?://'
    if re.search(prohibited, q): return None
    if re.search(r'\b(review|verify|missing|unknown|limitations?|assumptions?)\b', q): return 'assumptions'
    if context.type in {'road', 'assessment'} and re.search(r'why.*(flag|condition|road)|condition|assessment', q): return 'condition'
    if context.type == 'estimate' and re.search(r'estimate|cost|duration|repair|driver|rate', q): return 'estimate'
    if context.type in {'project', 'conflict'} and re.search(r'conflict|spatial|temporal|schedule|flag|project', q): return 'conflict'
    if context.type in {'comparison', 'evaluation'} and re.search(r'scenario|tradeoff|budget|conflict|schedule|cost', q): return 'comparison'
    return None


def validate_selection(raw, evidence, recommendation):
    # Round-trip even injected provider objects: no subclass fields or unchecked model_construct.
    if isinstance(raw, ProviderSelection): raw = raw.model_dump(mode='json')
    selection = ProviderSelection.model_validate(raw)
    facts = {f.fact_id: f for f in evidence.facts}
    if selection.evidence_snapshot_hash != evidence.snapshot_hash:
        raise ProviderFailure('invalid_context')
    if set(selection.limitation_codes) != set(CODES) or len(selection.limitation_codes) != len(CODES):
        raise ProviderFailure('missing_caveats')
    if selection.recommendation_code != recommendation:
        raise ProviderFailure('unsupported_claim')
    if len({c.fact_id for c in selection.claim_selections}) != len(selection.claim_selections):
        raise ProviderFailure('unsupported_claim')
    for c in selection.claim_selections:
        if c.fact_id not in facts or facts[c.fact_id].evidence_id != c.evidence_id:
            raise ProviderFailure('invalid_citation')
    return selection


def render_fact(f):
    value = 'Unknown / not applicable; inspect source' if f.value is None else str(f.value).lower() if isinstance(f.value, bool) else str(f.value)
    return f'{f.label}: {value}' + (f' {f.unit}' if f.unit and f.value is not None else '') + '.'


class AIExplanationService:
    def __init__(self, settings, provider, audit):
        self.settings, self.provider, self.audit = settings, provider, audit
        self.gate = UsageGate(settings.max_calls_per_hour)

    async def explain(self, evidence, task, mode, request_id, question=None):
        validate_context(evidence)
        recommendation = 'review_tradeoffs' if evidence.context.type in {'comparison', 'evaluation'} else 'coordinate_projects' if evidence.context.type in {'conflict', 'project'} else 'verify_inputs'
        intent = question_intent(question, evidence.context) if question is not None else task
        fallback = DeterministicFallbackProvider().generate(evidence, intent, recommendation) if evidence.facts else None
        selection, reason, status, model = fallback, None, 'deterministic', None
        insufficient = intent is None or not evidence.facts
        if mode == 'ai' and not insufficient:
            if not self.settings.configured:
                reason, status = 'not_configured', 'fallback'
            else:
                acquired = False
                model = self.settings.model
                try:
                    self.gate.acquire(); acquired = True
                    raw = await asyncio.wait_for(self.provider.generate(evidence, intent, recommendation), self.settings.timeout_seconds)
                    selection = validate_selection(raw, evidence, recommendation)
                    status = 'openai'
                except (asyncio.TimeoutError, TimeoutError):
                    reason, status = 'timeout', 'fallback'
                except ProviderFailure as exc:
                    reason, status = exc.category, 'fallback'
                except (ValidationError, ValueError, TypeError, KeyError):
                    reason, status = 'invalid_output', 'fallback'
                except Exception:
                    # Never log raw provider exception bodies or submitted context.
                    reason, status = 'provider_unavailable', 'fallback'
                finally:
                    if acquired: self.gate.release()
        # Fact completeness is server-controlled; the model cannot omit material facts/caveats.
        chosen = {s.fact_id for s in selection.claim_selections} if selection else set()
        ordered = [f for f in evidence.facts if f.fact_id in chosen] + [f for f in evidence.facts if f.fact_id not in chosen]
        findings = [] if insufficient else [Finding(finding_id=f.fact_id, claim_text=render_fact(f),
            supporting_evidence_ids=[f.evidence_id], fact_refs=[f.fact_id], classification=f.classification) for f in ordered]
        source = 'synthetic' if all(e.synthetic_input for e in evidence.records) else 'observed' if not any(e.synthetic_input for e in evidence.records) else 'mixed'
        summary = ('Insufficient evidence to answer this question. Ask about supplied costs, conditions, schedules, conflicts or assumptions; future effects and approvals are outside this evidence.' if insufficient else
            'Explanation of attached records and deterministic results. Inspect findings, assumptions and source references before human review.')
        eid = str(uuid4())
        result = Explanation(explanation_id=eid, task_type=task, evidence_snapshot_hash=evidence.snapshot_hash,
            summary=summary, key_findings=findings, tradeoffs=TRADEOFFS[task], uncertainties=evidence.limitations,
            missing_information=evidence.missing_information, suggested_review_actions=[REVIEW[recommendation]],
            citations=evidence.records, evidence=evidence, provider_status=status,
            validation_status='insufficient_evidence' if insufficient else 'fallback_validated' if status == 'fallback' else 'validated',
            fallback_reason=reason, model_label=model, generated_at=datetime.now(timezone.utc), source_classification=source,
            warnings=evidence.limitations + ([f'Evidence truncated: {evidence.omitted_fact_count} facts omitted. Inspect original source snapshots.'] if evidence.truncated else []), audit_reference=eid)
        self.audit.save(result, request_id)
        return result
