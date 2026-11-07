"""Snapshot-only deterministic M4 cost, budget and scheduling evaluation."""
from datetime import datetime, timezone
from decimal import Decimal, localcontext
from itertools import combinations

from app.schemas.conflicts import AnalysisParameters
from app.schemas.roads import Road
from app.schemas.planning import RepairOption, Assessment
from app.schemas.scenarios import Scenario, ScenarioEvaluation, ActionCost
from app.services.estimates import cost_scenarios, duration, canonical_hash, money, suitability
from app.services.hypothetical import screen, ADAPTER
from app.services.scenario_identity import canonical_proposal

VERSIONS = dict(evaluation='scenario-evaluation-v1', cost='scenario-cost-v1', estimate='repair-estimate-v1',
    adapter=ADAPTER, conflict='conflict-screen-v1', quantity='rectangular-scope-v1', schedule='supplied-calendar-v1')


def action_cost(action, context):
    roads = {r['id']: Road.model_validate(r) for r in context['baseline']['roads']}
    options = {o['id']: RepairOption.model_validate(o) for o in context['baseline']['options']}
    road, q = roads[action.road_segment_id], action.quantity
    quantity, reason = None, None
    provenance = dict(proposal=q.model_dump(mode='json'), input_provenance=action.input_provenance['quantity'].model_dump(mode='json'))
    if q.derivation == 'road_dimensions':
        provenance.update(length_m=str(road.length_m) if road.length_m is not None else None,
            width_m=str(road.width_m) if road.width_m is not None else None,
            dimension_basis=road.dimension_basis, field_evidence=road.field_evidence, method_version='rectangular-scope-v1')
        if road.length_m is not None and road.width_m is not None:
            quantity = road.length_m * road.width_m
            if q.value is not None and q.value != quantity:
                raise ValueError('Asserted quantity disagrees with frozen road dimensions')
        else:
            if q.value is not None:
                raise ValueError('Asserted quantity cannot replace unknown road dimensions')
            reason = 'Road dimensions are unknown; explicit dimensions/partial area assumptions are required.'
    elif q.derivation == 'explicit_rectangle':
        quantity = q.length_m * q.width_m
    elif q.derivation == 'explicit_area':
        quantity = q.value
    else:
        reason = 'Quantity unavailable: ' + action.unknown_reasons['quantity']
    option = options.get(action.repair_option_id)
    if option is None:
        reason = (reason + ' ' if reason else '') + 'Repair method unavailable: ' + action.unknown_reasons['repair_option_id']
    costs = cost_scenarios(quantity, option) if quantity is not None and option is not None else None
    snapshot = dict(action=action.model_dump(mode='json'), road=road.model_dump(mode='json'),
        option=option.model_dump(mode='json') if option else None, assessment=context['assessments'].get(road.id),
        sources=context['sources'], resolved_quantity=str(quantity) if quantity is not None else None,
        quantity_provenance=provenance, versions=VERSIONS)
    return ActionCost(action_id=action.id, quantity_m2=quantity, quantity_provenance=provenance,
        unavailable_reason=reason, costs=costs, duration=duration(quantity, option) if costs else None,
        suitability=suitability(road, Assessment.model_validate(context["assessments"][road.id]) if context["assessments"].get(road.id) else None, option) if option else None,
        warnings=[*(option.exclusions + option.limitations if option else []), "SYNTHETIC planning estimate; method suitability needs engineering review."],
        input_snapshot=snapshot, input_hash=canonical_hash(snapshot))


def evaluate(scenario: Scenario, context: dict, parameters: AnalysisParameters | None = None):
    scenario = Scenario.model_validate(canonical_proposal(scenario.model_dump(mode="json")))
    parameters = parameters or AnalysisParameters()
    with localcontext() as ctx:
        ctx.prec = 40
        costs = [action_cost(a, context) for a in sorted(scenario.actions, key=lambda a: a.id)]
        known = {k: money(sum((Decimal(c.costs[k].total_usd) for c in costs if c.costs), Decimal(0))) for k in ('low', 'base', 'high')}
        total = known if costs and all(c.costs for c in costs) else None
        headroom = {k: money(scenario.budget_usd - Decimal(total[k])) for k in total} if total else None
    checks = [f'{c.action_id}: {c.unavailable_reason}' for c in costs if c.unavailable_reason]
    if not costs:
        checks.append('No repair actions; complete costs and feasibility unavailable.')
    for a in scenario.actions:
        checks.extend(f'{a.id}: {path}: {reason}' for path, reason in sorted(a.unknown_reasons.items())
            if path not in {'quantity', 'repair_option_id'})
    schedules = [a.schedule for a in scenario.actions]
    complete_schedule = bool(schedules) and all(s and s.start_date and s.end_date for s in schedules)
    elapsed = (max(s.end_date for s in schedules) - min(s.start_date for s in schedules)).days if complete_schedule else None
    scheduled_days = sum((s.end_date - s.start_date).days for s in schedules) if complete_schedule else None
    closures_known = complete_schedule and all(s.closure_intervals is not None for s in schedules)
    closures = [(a, c) for a in scenario.actions if a.schedule for c in a.schedule.closure_intervals or []]
    lane_days = sum((c.end_date - c.start_date).days * c.lanes_closed for _, c in closures) if closures_known else None
    overlap_pairs = sum(1 for (a, c), (b, d) in combinations(closures, 2) if a.id != b.id and a.road_segment_id == b.road_segment_id
        and c.lanes_closed > 0 and d.lanes_closed > 0 and max(c.start_date, d.start_date) < min(c.end_date, d.end_date)) if closures_known else None
    if not complete_schedule:
        checks.append('Calendar dates incomplete; elapsed and scheduled road-workdays unavailable.')
    if not closures_known:
        checks.append('Closure declarations incomplete; lane-closure-days and overlap counts unavailable.')
    for a in scenario.actions:
        for pred in a.constraints.must_follow_action_ids:
            p = next(x for x in scenario.actions if x.id == pred)
            if not a.schedule or not p.schedule or not a.schedule.start_date or not p.schedule.end_date:
                checks.append(f'{a.id}: precedence after {pred} cannot be checked without dates.')
        if (a.constraints.earliest_start or a.constraints.latest_end) and (not a.schedule or not a.schedule.start_date or not a.schedule.end_date):
            checks.append(f'{a.id}: date-bound satisfaction is indeterminate.')
    conflict_screen = screen(scenario, context, parameters)
    checks.extend(conflict_screen.adapter_indeterminate_checks)
    analysis = conflict_screen.analysis
    if analysis:
        checks.extend(f'{", ".join(c.project_ids)}: {c.reason} Missing: {", ".join(c.missing_fields)}' for c in analysis.indeterminate_checks)
    else:
        checks.append(conflict_screen.not_run_reason)
    snapshot = dict(scenario=scenario.model_dump(mode='json'), context=context, parameters=parameters.model_dump(mode='json'),
        versions=VERSIONS, conflict_input_hash=conflict_screen.input_hash)
    ih = canonical_hash(snapshot)
    result = dict(scenario_id=scenario.id, scenario_revision=scenario.revision, scenario_revision_hash=scenario.revision_hash,
        baseline_source_hash=context['baseline_source_hash'], input_snapshot=snapshot, input_hash=ih, analysis_versions=VERSIONS,
        action_costs=costs, known_subtotal_usd=known, cost_total_usd=total, budget_usd=money(scenario.budget_usd), budget_headroom_usd=headroom,
        budget_status='indeterminate' if not total else 'within_budget' if Decimal(total['base']) <= scenario.budget_usd else 'over_budget',
        upper_bound_within_budget=Decimal(total['high']) <= scenario.budget_usd if total else None,
        preliminary_days_sum=sum(c.duration.total_preliminary_days for c in costs) if costs and all(c.duration for c in costs) else None,
        elapsed_days=elapsed, scheduled_road_workdays=scheduled_days, lane_closure_days=lane_days, overlapping_closure_pairs=overlap_pairs,
        affected_road_ids=sorted({a.road_segment_id for a in scenario.actions}), action_lifespan_years={a.id: None for a in scenario.actions},
        conflict_screen=conflict_screen, indeterminate_checks=checks,
        warnings=['SYNTHETIC HYPOTHETICAL PLAN: planning-level estimates; human review required. Utility coverage remains unknown.',
            'Roadwork-only budget excludes utility construction and catalog exclusions. Unknown costs are never zero.',
            'Low/high are rate sensitivity assumptions, not confidence intervals. Separate per-action mobilization and contingency.',
            'Preliminary duration is a sum of allowances, not a calendar commitment. Scheduled road-workdays sum supplied envelopes per action; concurrent actions may double count.',
            'Deferral and coordination require engineering review. No quantified avoided rework, savings, traffic delays or lifespan.',
            *conflict_screen.warnings])
    provisional = ScenarioEvaluation(id='evaluation-' + ih, evaluated_at=datetime.now(timezone.utc).isoformat(), result_hash='pending', **result)
    provisional.result_hash = canonical_hash(provisional.model_dump(mode='json', exclude={'id', 'evaluated_at', 'input_snapshot', 'result_hash'}))
    return provisional


def replay(evaluation):
    """No live repository reads: re-evaluate the complete frozen input."""
    s = evaluation.input_snapshot
    return evaluate(Scenario.model_validate(s['scenario']), s['context'], AnalysisParameters.model_validate(s['parameters']))
