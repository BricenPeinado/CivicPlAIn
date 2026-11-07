"""Pure adapter to M3. It has no repository or mutation capability."""
from datetime import datetime

from app.schemas.conflicts import WorkProject, AnalysisParameters
from app.schemas.roads import Road, Evidence
from app.schemas.scenarios import Scenario, HypotheticalScreen
from app.services.conflicts import analyze
from app.services.estimates import canonical_hash
from app.services.scenario_identity import canonical_proposal

ADAPTER = 'hypothetical-conflict-adapter-v1'


def screen(scenario: Scenario, context: dict, parameters: AnalysisParameters):
    scenario = Scenario.model_validate(canonical_proposal(scenario.model_dump(mode='json')))
    baseline = context['baseline']
    all_roads = [Road.model_validate(r) for r in baseline['roads']]
    sources = {e['id']: Evidence.model_validate(e) for e in context['sources']}
    aliases = context['source_aliases']
    originals = [p for p in baseline['projects'] if p['id'] in scenario.external_project_ids]
    excluded = {o.project_id for o in scenario.project_overrides}
    projects = [WorkProject.model_validate(p) for p in originals if p['id'] not in excluded]
    origins = {p.id: dict(origin='existing_project', project_id=p.id) for p in projects}
    checks = []
    warnings = ['Hypothetical screening only. Unknown utility coverage is never excavation clearance.',
        'M3 multiple_closures uses schedule envelopes and maximum declared lanes; inspect exact closure intervals separately.']
    for a in sorted(scenario.actions, key=lambda a: a.id):
        aid = 'demo-hyp-' + canonical_hash(a.model_dump(mode='json'))
        if aid in origins:
            raise ValueError('hypothetical projection ID collision')
        origins[aid] = dict(origin='proposed_action', action_id=a.id)
        category, work_type = {'preventive': ('road_resurfacing', 'maintenance'),
            'resurface': ('road_resurfacing', 'resurfacing'), 'reconstruct': ('road_reconstruction', 'reconstruction')}.get(a.repair_category, ('other', 'other'))
        if category == 'other':
            checks.append(f'{a.id}: UNCLASSIFIED_REOPENING_RULE; generic spatial/temporal screening only.')
        refs = sorted({aliases.get(r, r) for p in a.input_provenance.values() for r in p.evidence_ids}
            | {aliases.get(r, r) for r in (a.schedule.assumption_evidence_ids if a.schedule else [])})
        schedule = a.schedule
        closures = schedule.closure_intervals if schedule else None
        lanes = max((c.lanes_closed for c in closures), default=0) if closures is not None else None
        start, end = (schedule.start_date, schedule.end_date) if schedule else (None, None)
        material = dict(infrastructure_category=category, work_type=work_type,
            schedule_status='planned' if start and end else 'unknown', schedule_basis='assumed_demo' if start or end else 'unknown',
            geometry=a.scope.geometry, location_status=a.scope.location_status, road_segment_ids=[a.road_segment_id],
            start_date=start, end_date=end, actual_start_date=None, actual_end_date=None,
            responsible_organization=None, excavation_required=None, lanes_closed=lanes, estimated_cost_usd=None)
        project = WorkProject(id=aid, title=f'Hypothetical action {a.id}'[:200], description=a.scope.description,
            kind='road_repair' if category.startswith('road_') else 'other', **material,
            dataset_snapshot_id=scenario.dataset_snapshot_id, evidence_ids=refs,
            field_evidence={k: refs for k, v in material.items() if v is not None},
            unknown_reasons={k: 'Not supplied by proposal; costs are evaluated separately.' for k, v in material.items() if v is None},
            limitations=['Hypothetical synthetic action; supplied geometry is approximate, never measured utility location.'],
            data_kind='synthetic', synthetic_input=True, created_at=scenario.created_at, updated_at=scenario.created_at)
        projects.append(project)
    if len(projects) > 50:
        raise ValueError('hypothetical analysis requires at most 50 projects after overrides')
    road_ids = {rid for p in projects for rid in p.road_segment_ids}
    # Preserve replay of pre-release M4 snapshots while new runs screen the full
    # bounded road universe, matching the existing M3 corridor analysis.
    roads = all_roads if context.get('screen_road_scope') == 'all_baseline_roads-v1' else [r for r in all_roads if r.id in road_ids]
    refs = {r for p in [*projects, *roads] for r in p.evidence_ids}
    analysis = analyze(projects, roads, parameters, [sources[r] for r in sorted(refs)],
        detected_at=datetime.fromisoformat(scenario.created_at)) if projects else None
    identity = dict(scenario=scenario.model_dump(mode='json', exclude={'updated_at'}), context=context,
        parameters=parameters.model_dump(mode='json'), adapter_version=ADAPTER,
        engine_input_hash=analysis.input_hash if analysis else None)
    finding_contexts = {f.id: 'hypothetical' if any(origins[p]['origin'] == 'proposed_action' for p in f.project_ids)
        else 'existing_project_screen' for f in analysis.findings} if analysis else {}
    result = dict(analysis_hash=analysis.result_hash if analysis else None, finding_contexts=finding_contexts, checks=checks, warnings=warnings)
    return HypotheticalScreen(scenario_id=scenario.id, project_origins=origins, original_projects=originals,
        overrides=[o.model_dump(mode='json') for o in scenario.project_overrides],
        assumption_sources=[s.model_dump(mode='json') for sid, s in sources.items() if sid in aliases.values()],
        adapter_indeterminate_checks=checks, warnings=warnings, analysis=analysis,
        not_run_reason=None if analysis else 'EMPTY_SCOPE: no proposed actions or selected external projects',
        finding_contexts=finding_contexts, input_hash=canonical_hash(identity), result_hash=canonical_hash(result))
