"""Small deterministic planning helper. No weighted score or automatic choice."""
from decimal import Decimal
from itertools import combinations

from app.schemas.scenarios import ScenarioComparison
from app.services.estimates import canonical_hash, money


class IncompatibleComparison(ValueError):
    pass


def basis(e):
    s = e.input_snapshot['scenario']
    return dict(screen_road_scope=e.input_snapshot['context'].get('screen_road_scope', 'declared_roads-pre-release'), baseline_source_hash=e.baseline_source_hash, horizon=[s['planning_start'], s['planning_end']],
        currency=s['currency'], cost_scope=s['cost_scope'], versions=e.analysis_versions,
        parameters=e.input_snapshot['parameters'], price_basis=sorted({o['price_basis_date'] for o in e.input_snapshot['context']['baseline']['options']}))


def scope(e):
    return sorted([(a['road_segment_id'], a['repair_category'], a['scope']['extent'], str(c.quantity_m2) if c.quantity_m2 is not None else None,
        a['scope']['geometry']) for a, c in sorted([(a, next(c for c in e.action_costs if c.action_id == a['id'])) for a in e.input_snapshot['scenario']['actions']], key=lambda pair: pair[0]['id'])], key=lambda s: str(s))


def compare(evaluations):
    if not 2 <= len(evaluations) <= 3 or len({e.id for e in evaluations}) != len(evaluations):
        raise ValueError('compare requires 2–3 distinct saved evaluations')
    evaluations = sorted(evaluations, key=lambda e: e.id)
    common = basis(evaluations[0])
    if any(basis(e) != common for e in evaluations[1:]):
        raise IncompatibleComparison('Evaluations have incompatible baseline contents, horizon, price basis, scope, parameters or versions; re-evaluate using a common basis')
    warnings = ['Hypothetical planning comparison; no universal best or safest plan. Human review remains required.']
    rows, deltas, dominance, tradeoffs = [], [], [], []
    for e in evaluations:
        s = e.input_snapshot['scenario']
        analysis = e.conflict_screen.analysis
        rows.append(dict(evaluation_id=e.id, scenario_id=e.scenario_id, name=s['name'], revision=e.scenario_revision,
            cost_total_usd=e.cost_total_usd, known_subtotal_usd=e.known_subtotal_usd,
            budget_usd=e.budget_usd, budget_headroom_usd=e.budget_headroom_usd, budget_status=e.budget_status,
            upper_bound_within_budget=e.upper_bound_within_budget, preliminary_days_sum=e.preliminary_days_sum,
            elapsed_days=e.elapsed_days, scheduled_completion=max((a['schedule']['end_date'] for a in s['actions'] if a['schedule'] and a['schedule']['end_date']), default=None)
                if e.elapsed_days is not None else None,
            lane_closure_days=e.lane_closure_days, scheduled_road_workdays=e.scheduled_road_workdays,
            conflict_count=len(analysis.findings) if analysis else None,
            conflict_types={t: sum(f.finding_type == t for f in analysis.findings) for t in sorted({f.finding_type for f in analysis.findings})} if analysis else {},
            incomplete_checks=len(e.indeterminate_checks), affected_road_ids=e.affected_road_ids,
            priced_actions=sum(c.costs is not None for c in e.action_costs), total_actions=len(e.action_costs),
            assumptions=s['assumptions'], action_lifespan_years=e.action_lifespan_years))
    for (a, ra), (b, rb) in combinations(zip(evaluations, rows), 2):
        same_scope = scope(a) == scope(b)
        same_assumptions = a.input_snapshot['scenario']['assumptions'] == b.input_snapshot['scenario']['assumptions']
        if not same_scope:
            warnings.append(f'{ra["name"]} / {rb["name"]}: different road/repair/quantity/footprint scopes; numeric differences are not equivalent-service savings; dominance unavailable.')
        if not same_assumptions:
            warnings.append(f'{ra["name"]} / {rb["name"]}: authored assumptions differ; inspect sources, dates, closures and overrides.')
        delta = money(Decimal(b.cost_total_usd['base']) - Decimal(a.cost_total_usd['base'])) if a.cost_total_usd and b.cost_total_usd else None
        deltas.append(dict(from_evaluation_id=a.id, to_evaluation_id=b.id, base_cost_difference_usd=delta,
            elapsed_days_difference=b.elapsed_days-a.elapsed_days if a.elapsed_days is not None and b.elapsed_days is not None else None,
            comparable_scope=same_scope))
        if delta is not None:
            d = Decimal(delta)
            tradeoffs.append(f'{rb["name"]} has ' + ('the same estimated base cost as ' if d == 0 else f"a ${money(abs(d))} {'higher' if d > 0 else 'lower'} estimated base cost than ") + f'{ra["name"]}.'
                + ('' if same_scope else ' Work scopes differ.'))
        else:
            tradeoffs.append(f'{ra["name"]} / {rb["name"]}: complete cost difference is unavailable because required costs are missing.')
        if ra['scheduled_completion'] and rb['scheduled_completion'] and ra['scheduled_completion'] != rb['scheduled_completion']:
            later, earlier = (rb, ra) if rb['scheduled_completion'] > ra['scheduled_completion'] else (ra, rb)
            tradeoffs.append(f'{later["name"]} has a later supplied completion ({later["scheduled_completion"]}) than {earlier["name"]} ({earlier["scheduled_completion"]}). These are planning assumptions.')
        # Dominance is intentionally conservative: matching service, assumptions, budgets and complete checks.
        # Dates/closures can differ, so compare only declared numeric minimization objectives, with explicit scope.
        eligible = same_scope and same_assumptions and a.budget_usd == b.budget_usd and not a.indeterminate_checks and not b.indeterminate_checks
        keys = ['lane_closure_days', 'scheduled_road_workdays']
        if eligible and a.cost_total_usd and b.cost_total_usd and all(getattr(e, k) is not None for e in (a, b) for k in keys):
            va = [Decimal(a.cost_total_usd['base']), a.lane_closure_days, a.scheduled_road_workdays, len(a.conflict_screen.analysis.findings)]
            vb = [Decimal(b.cost_total_usd['base']), b.lane_closure_days, b.scheduled_road_workdays, len(b.conflict_screen.analysis.findings)]
            for x, y, vx, vy in [(a, b, va, vb), (b, a, vb, va)]:
                if all(l <= r for l, r in zip(vx, vy)) and any(l < r for l, r in zip(vx, vy)):
                    dominance.append(dict(dominant_evaluation_id=x.id, dominated_evaluation_id=y.id,
                        objectives=['base_cost_usd', 'lane_closure_days', 'scheduled_road_workdays', 'screened_conflict_count'],
                        limitation='Only these complete numeric objectives; utility coverage and safety remain unknown.'))
    if not dominance:
        tradeoffs.append('No dominance established across the available comparable objectives. Review the tradeoffs and incomplete evidence.')
    ih = canonical_hash([[e.id, e.result_hash] for e in evaluations])
    return ScenarioComparison(id='comparison-' + ih, evaluation_ids=[e.id for e in evaluations], common_basis=common,
        rows=rows, deltas=deltas, dominance=dominance, tradeoffs=tradeoffs, warnings=warnings, input_hash=ih)
