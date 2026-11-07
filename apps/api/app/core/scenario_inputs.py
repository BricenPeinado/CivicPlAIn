"""Resolve live references before entering the pure snapshot evaluation boundary."""
from itertools import combinations
from shapely.geometry import shape

from app.schemas.roads import Evidence
from app.services.estimates import canonical_hash


class ScenarioInputError(ValueError):
    def __init__(self, status, message):
        self.status = status
        super().__init__(message)


def at_path(value, path):
    for key in path.split('.'):
        if not isinstance(value, dict) or key not in value:
            raise ScenarioInputError(422, f'Unknown provenance field {path}')
        value = value[key]
    return value


def freeze(draft, road_repo, planning, conflicts, scenario_id):
    if road_repo.snapshot() != draft.dataset_snapshot_id:
        raise ScenarioInputError(409, 'Dataset snapshot mismatch')
    # Full bounded road/catalog baseline permits honest scope-difference disclosure.
    roads = road_repo.list(100, None, None)[0]
    options = planning.options()
    projects = conflicts.projects()
    records = {r.id: r for r in [*roads, *options, *projects]}
    by_road = {r.id: r for r in roads}
    by_option = {o.id: o for o in options}
    by_project = {p.id: p for p in projects}
    project_ids = set(draft.external_project_ids) | {p for a in draft.actions for p in a.related_project_ids}
    for pid in project_ids:
        if pid not in by_project:
            raise ScenarioInputError(404, 'Referenced project not found')
        if by_project[pid].data_kind != 'synthetic':
            raise ScenarioInputError(422, 'UNSUPPORTED_SOURCE_CONTRACT: observed municipal project adapters are not implemented')
        if by_project[pid].dataset_snapshot_id != draft.dataset_snapshot_id:
            raise ScenarioInputError(409, 'Project snapshot mismatch')
    refs = {ref for r in [*roads, *options, *(by_project[p] for p in project_ids)] for ref in r.evidence_ids}
    sources = {}
    for ref in sorted(refs):
        source = road_repo.evidence(ref)
        if source is None:
            raise ScenarioInputError(409, 'Referenced source contents unavailable')
        sources[ref] = source
    baseline_sources = [s.model_dump(mode='json') for s in sources.values()]
    aliases = {}
    for a in draft.assumptions:
        content = a.model_dump(mode='json')
        sid = f'assumption-{canonical_hash([scenario_id, a.id])[:40]}'
        aliases['assumption:' + a.id] = sid
        sources[sid] = Evidence(id=sid, title='SYNTHETIC hypothetical planning assumption', publisher='Scenario author',
            source_kind='demo_assumption', verification_status='synthetic_demo', uri=f'scenario:{scenario_id}:assumption:{a.id}',
            version='scenario-assumption-v1', checksum_sha256=canonical_hash(content), original_crs='EPSG:4326',
            coverage_note=a.note, reliability_note='Authored planning assumption; no field observation or measurement.',
            license_note='Local hypothetical planning input', unknown_reasons={'observed_on': 'not_observed', 'retrieved_at': 'authored_locally'})
    assumptions = {a.id: a for a in draft.assumptions}
    def resolve_refs(ids, field=None):
        for ref in ids:
            if ref.startswith('assumption:'):
                a = assumptions.get(ref.removeprefix('assumption:'))
                if a is None:
                    raise ScenarioInputError(404, 'Assumption reference not found')
                if field and not any(field == p or field.startswith(p + '.') for p in a.field_paths):
                    raise ScenarioInputError(422, f'Assumption does not cover {field}')
            elif ref not in sources:
                source = road_repo.evidence(ref)
                if source is None:
                    raise ScenarioInputError(404, 'Evidence reference not found')
                sources[ref] = source
        return [aliases.get(r, r) for r in ids]
    for action in draft.actions:
        if action.road_segment_id not in by_road:
            raise ScenarioInputError(404, 'Referenced road not found')
        if action.repair_option_id:
            option = by_option.get(action.repair_option_id)
            if option is None:
                raise ScenarioInputError(404, 'Referenced repair option not found')
            if option.treatment != action.repair_category:
                raise ScenarioInputError(422, 'Repair category and option disagree')
        raw = action.model_dump(mode='json')
        for path, prov in action.input_provenance.items():
            resolve_refs(prov.evidence_ids, path)
            if prov.basis == 'planning_assumption' and not any(r.startswith('assumption:') for r in prov.evidence_ids):
                raise ScenarioInputError(422, 'Planning provenance requires an inline assumption reference')
            if prov.basis == 'source_record':
                record = records.get(prov.record_id)
                if record is None:
                    raise ScenarioInputError(404, 'Provenance source record not found')
                if prov.record_id not in {action.road_segment_id, action.repair_option_id, *action.related_project_ids}:
                    raise ScenarioInputError(422, 'Source record is unrelated to this action')
                upstream = getattr(record, 'field_evidence', {}).get(prov.record_field, record.evidence_ids if prov.record_id in by_option else [])
                if not set(prov.evidence_ids) <= set(upstream) or at_path(raw, path) != at_path(record.model_dump(mode='json'), prov.record_field):
                    raise ScenarioInputError(422, 'Source provenance does not match the exact field/value and upstream evidence')
        if action.quantity.derivation.startswith('explicit') and action.input_provenance['quantity'].basis not in {'source_record', 'planning_assumption'}:
            raise ScenarioInputError(422, 'Explicit quantity requires a labeled planning assumption or exact source')
        s = action.schedule
        if s:
            resolve_refs(s.assumption_evidence_ids, 'schedule')
            if s.work_calendar:
                resolve_refs(s.work_calendar.evidence_ids, 'schedule')
            for c in s.closure_intervals or []:
                resolve_refs(c.evidence_ids, 'schedule')
                road = by_road[action.road_segment_id]
                if road.lane_count is not None and c.lanes_closed > road.lane_count:
                    raise ScenarioInputError(422, 'Closure exceeds known road lane count')
    for a, b in combinations(draft.actions, 2):
        if a.road_segment_id != b.road_segment_id:
            continue
        distinct_footprints = (a.scope.geometry is not None and b.scope.geometry is not None
            and not shape(a.scope.geometry.model_dump()).intersects(shape(b.scope.geometry.model_dump())))
        disjoint_dates = (a.schedule and b.schedule and a.schedule.start_date and a.schedule.end_date
            and b.schedule.start_date and b.schedule.end_date
            and (a.schedule.end_date <= b.schedule.start_date or b.schedule.end_date <= a.schedule.start_date))
        repeat = any(x.action_kind == 'repeat_restoration' and 'repeat_justification' in x.input_provenance for x in (a,b))
        if not distinct_footprints and not (repeat and disjoint_dates):
            raise ScenarioInputError(422, 'Repeated road scopes require disjoint explicit footprints or justified repeat work with distinct dates; overlapping alternatives would double count')
    for o in draft.project_overrides:
        resolve_refs(o.evidence_ids, 'project_overrides')
    baseline = dict(roads=[r.model_dump(mode='json') for r in roads], options=[o.model_dump(mode='json') for o in options],
        projects=[by_project[p].model_dump(mode='json') for p in sorted(project_ids)], sources=baseline_sources)
    return dict(screen_road_scope='all_baseline_roads-v1', baseline=baseline, baseline_source_hash=canonical_hash(baseline), sources=[sources[k].model_dump(mode='json') for k in sorted(sources)],
        source_aliases=aliases, assessments={r.id: a.model_dump(mode='json') if (a := planning.latest(r.id)) else None for r in roads})
