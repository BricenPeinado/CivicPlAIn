"""Server-side allowlisted evidence projection. No narrative or geometry reaches a model."""
import json
from app.schemas.ai import Context, EvidencePackage, EvidenceRecord, Fact
from app.services.estimates import canonical_hash
from app.schemas.planning import Calculation
from app.services.scenario_comparison import compare

LIMITATIONS = [
    'Utility coverage is unknown. No finding or empty search establishes excavation safety.',
    'Synthetic inputs are authored demonstrations, not municipal observations or measured accuracy.',
    'Estimates use supplied scope and rate sensitivities, not bids or probability bounds. Catalog exclusions remain outside costs.',
    'Spatial and schedule screens indicate potential coordination issues, not confirmed damage, loss or savings.',
    'Human engineering and coordination review is required. This assistant cannot approve projects or authorize spending.',
    'Source notes and descriptions are untrusted and excluded. Inspect original records for full assumptions and limitations.',
]
MAX_FACTS = 96
MAX_BYTES = 48000


class EvidenceError(ValueError):
    def __init__(self, status, message):
        self.status = status
        super().__init__(message)


def require(record):
    if record is None:
        raise EvidenceError(404, 'Referenced evidence record not found')
    return record


def check_hashes(record, kind):
    """Validate existing semantic hashes without changing any historical calculations."""
    raw = record.model_dump(mode='json')
    if canonical_hash(record.input_snapshot) != record.input_hash:
        raise EvidenceError(409, 'Source input snapshot integrity check failed')
    if kind == 'estimate':
        result = Calculation.model_validate({k: raw[k] for k in Calculation.model_fields})
        expected = canonical_hash(result.model_dump(mode='json'))
    elif kind == 'evaluation':
        expected = canonical_hash(record.model_dump(mode='json', exclude={'id', 'evaluated_at', 'input_snapshot', 'result_hash'}))
    if expected != record.result_hash:
        raise EvidenceError(409, 'Source result integrity check failed')


class EvidenceBuilder:
    def __init__(self, roads, planning, conflicts, scenarios):
        self.roads, self.planning, self.conflicts, self.scenarios = roads, planning, conflicts, scenarios
        self.records, self.facts = [], []

    def record(self, entity, kind, sources=(), input_hash=None, version=None):
        raw = entity.model_dump(mode='json') if hasattr(entity, 'model_dump') else entity
        rid = raw['id']
        revisions = {}
        for source in sources:
            s = source.model_dump(mode='json') if hasattr(source, 'model_dump') else source
            revision = canonical_hash(s)
            if s['id'] in revisions and revisions[s['id']] != revision:
                raise EvidenceError(409, 'Incompatible source revisions in one snapshot')
            revisions[s['id']] = revision
        e = EvidenceRecord(evidence_id='ev-' + canonical_hash([kind, rid, raw])[:24], entity_type=kind,
            record_id=rid, record_hash=canonical_hash(raw), input_hash=input_hash, calculation_version=version,
            dataset_snapshot_id=raw.get('dataset_snapshot_id'), source_revisions=revisions,
            synthetic_input=raw.get('synthetic_input', True), data_kind=raw.get('data_kind', 'derived'))
        self.records.append(e)
        return e.evidence_id

    def fact(self, eid, field, label, value, unit=None, calculated=False):
        # All labels/paths are application constants; values originate in typed fields.
        self.facts.append(Fact(fact_id='fact-' + canonical_hash([eid, field])[:24], evidence_id=eid,
            field=field, label=label, value=value, unit=unit,
            classification='deterministic_calculation' if calculated else 'verified_record_fact'))

    def sources(self, ids):
        return [require(self.roads.evidence(sid)) for sid in sorted(set(ids))]

    def road(self, road):
        eid = self.record(road, 'road', self.sources(road.evidence_ids))
        for key, label, unit in [('length_m', 'Planning length', 'm'), ('width_m', 'Planning width', 'm'), ('lane_count', 'Declared lanes', 'lanes'), ('surface_material', 'Surface', None)]:
            v = getattr(road, key)
            self.fact(eid, key, label, str(v) if v is not None else None, unit)
        self.fact(eid, 'condition_summary.category', 'Demo condition category', road.condition_summary.category)
        self.fact(eid, 'condition_summary.rating', 'Demo condition rating', str(road.condition_summary.rating) if road.condition_summary.rating is not None else None, 'synthetic 1–10 higher better')
        self.fact(eid, 'condition_summary.assessed_on', 'Demo assessment date', str(road.condition_summary.assessed_on) if road.condition_summary.assessed_on else None, 'date')

    def estimate(self, e):
        check_hashes(e, 'estimate')
        s = e.input_snapshot
        from app.schemas.roads import Road
        from app.schemas.planning import Assessment, RepairOption, PlanningAssumptions
        from app.services.estimates import calculate
        assumptions = s['request'].get('planning_assumptions')
        replayed = calculate(Road.model_validate(s['road']), Assessment.model_validate(s['assessment']) if s['assessment'] else None,
            RepairOption.model_validate(s['option']), PlanningAssumptions.model_validate(assumptions) if assumptions else None)
        if canonical_hash(replayed.model_dump(mode='json')) != e.result_hash:
            raise EvidenceError(409, 'Estimate calculation does not match its frozen inputs')
        expected_sources = set(e.evidence_ids) - {'user-planning-assumption'}
        if expected_sources != {source['id'] for source in s['evidence']}:
            raise EvidenceError(409, 'Estimate provenance references cannot be resolved')
        eid = self.record(e, 'estimate', s['evidence'], e.input_hash, e.method_version)
        # Use frozen inputs, never join a saved estimate to a changed catalog/road.
        if s['road']['id'] != e.road_segment_id or s['option']['id'] != e.repair_option_id:
            raise EvidenceError(409, 'Estimate source references are inconsistent')
        self.fact(eid, 'repair_category', 'Repair method', e.repair_category)
        for name in ('base', 'low', 'high'):
            self.fact(eid, f'scenarios.{name}.total_usd', f'{name.capitalize()} sensitivity total', e.scenarios[name].total_usd, 'USD', True)
        for i, (label, item) in enumerate(zip(['Bundled materials, labor and equipment', 'Mobilization allowance', 'Traffic management allowance'], e.scenarios['base'].line_items)):
            self.fact(eid, f'scenarios.base.line_items.{i}.amount_usd', label, item.amount_usd, 'USD', True)
            self.fact(eid, f'scenarios.base.line_items.{i}.unit_rate_usd', label + ' rate', item.unit_rate_usd, 'USD/m2' if i == 0 else 'USD/allowance')
        self.fact(eid, 'scenarios.base.contingency_usd', 'Base contingency', e.scenarios['base'].contingency_usd, 'USD', True)
        self.fact(eid, 'scenarios.base.contingency_fraction', 'Contingency fraction', str(e.scenarios['base'].contingency_fraction), 'fraction')
        self.fact(eid, 'quantity', 'Rectangular planning scope', str(e.quantity), 'm2', True)
        for key, unit in [('active_workdays', 'active_workdays'), ('setup_days', 'days'), ('curing_days', 'days'), ('total_preliminary_days', 'preliminary_days'), ('productivity_per_day', 'm2/active_workday')]:
            self.fact(eid, 'duration.' + key, key.replace('_', ' ').capitalize(), str(getattr(e.duration, key)), unit, True)
        self.fact(eid, 'suitability.status', 'Condition screening suitability', e.suitability.status, None, True)
        self.fact(eid, 'price_basis_date', 'Synthetic catalog price basis', s['option']['price_basis_date'], 'date')
        for key, item in sorted(e.dimension_provenance.items()):
            self.fact(eid, 'dimension_provenance.' + key, 'Dimension basis: ' + key, item['basis'] if item['basis'] in {'user_planning_assumption','synthetic_planning_assumption','source_supplied','legacy_synthetic_basis_unknown'} else 'unknown')
        self.fact(eid, 'assessed_rating', 'Frozen demo condition rating', s['assessment']['rating'] if s['assessment'] else None, 'synthetic 1–10 higher better')
        self.fact(eid, 'assessment.assessed_on', 'Frozen demo assessment date', s['assessment']['assessed_on'] if s['assessment'] else None, 'date')

    def project(self, p, sources=None):
        eid = self.record(p, 'project', sources if sources is not None else self.sources(p.evidence_ids))
        for key, unit in [('kind', None), ('work_type', None), ('schedule_status', None), ('schedule_basis', None), ('location_status', None), ('start_date', 'date'), ('end_date', 'date'), ('actual_start_date', 'date'), ('actual_end_date', 'date'), ('lanes_closed', 'lanes'), ('estimated_cost_usd', 'USD'), ('excavation_required', None)]:
            v = getattr(p, key)
            self.fact(eid, key, key.replace('_', ' ').capitalize(), v if isinstance(v, (int, bool)) or v is None else str(v), unit)

    def conflict(self, f, analysis):
        # Replay is source-only, has no SQL writes, and checks both semantic hashes.
        from app.services.conflicts import analyze
        from app.schemas.conflicts import WorkProject
        from app.schemas.roads import Road, Evidence
        s = analysis.input_snapshot
        replayed = analyze([WorkProject.model_validate(p) for p in s['projects']], [Road.model_validate(r) for r in s['roads']],
            analysis.parameters, [Evidence.model_validate(x) for x in s['sources']])
        if replayed.input_hash != analysis.input_hash or replayed.result_hash != analysis.result_hash or not any(x.model_dump(mode='json', exclude={'detected_at'}) == f.model_dump(mode='json', exclude={'detected_at'}) for x in replayed.findings):
            raise EvidenceError(409, 'Conflict snapshot integrity check failed')
        eid = self.record(f, 'conflict', s['sources'], f.input_hash, f.method_version)
        self.fact(eid, 'finding_type', 'Potential coordination finding', f.finding_type, None, True)
        self.fact(eid, 'affected_road_ids', 'Affected road references', ', '.join(f.affected_road_ids))
        self.fact(eid, 'project_ids', 'Involved project references', ', '.join(f.project_ids))
        self.fact(eid, 'spatial_evidence.classifications', 'Supplied spatial evidence classification', ', '.join(f.spatial_evidence.classifications), None, True)
        self.fact(eid, 'spatial_evidence.distance_m', 'Computed footprint distance; accuracy unverified', f.spatial_evidence.distance_m, 'm', True)
        self.fact(eid, 'spatial_evidence.polygon_overlap', 'Overlap in supplied polygons', f.spatial_evidence.polygon_overlap, None, True)
        self.fact(eid, 'temporal_evidence.gap_days', 'Sequential calendar gap', f.temporal_evidence.gap_days, 'calendar_days', True)
        for key in ('overlap_start', 'overlap_end'):
            v = getattr(f.temporal_evidence, key)
            self.fact(eid, 'temporal_evidence.' + key, key.replace('_', ' ').capitalize(), str(v) if v else None, 'date', True)
        for i, pid in enumerate(f.project_ids):
            for j, value in enumerate(f.temporal_evidence.intervals[pid]):
                self.fact(eid, f'temporal_evidence.intervals.{i}.{j}', f'Project {i+1} supplied interval ' + ('start' if j == 0 else 'end (exclusive)'), str(value) if value else None, 'date')

    def evaluation(self, e):
        first_fact = len(self.facts)
        check_hashes(e, 'evaluation')
        from app.services.scenarios import replay
        replayed = replay(e)
        if (replayed.input_hash, replayed.result_hash) != (e.input_hash, e.result_hash):
            raise EvidenceError(409, 'Evaluation does not match its frozen source snapshot')
        eid = self.record(e, 'evaluation', e.input_snapshot['context']['sources'], e.input_hash, e.method_version)
        for field, label in [('cost_total_usd', 'Complete action cost'), ('budget_headroom_usd', 'Budget headroom')]:
            for name in ('base', 'low', 'high'):
                v = getattr(e, field)
                self.fact(eid, field + '.' + name, label + ' ' + name, v[name] if v else None, 'USD', True)
        self.fact(eid, 'budget_usd', 'Hypothetical roadwork budget', e.budget_usd, 'USD')
        self.fact(eid, 'budget_status', 'Base budget status', e.budget_status, None, True)
        self.fact(eid, 'upper_bound_within_budget', 'High sensitivity within budget', e.upper_bound_within_budget, None, True)
        for key, label, unit in [('elapsed_days', 'Supplied calendar span', 'calendar_days'), ('preliminary_days_sum', 'Preliminary allowances, summed', 'preliminary_days'), ('lane_closure_days', 'Declared lane closure proxy', 'lane_days')]:
            self.fact(eid, key, label, getattr(e, key), unit, True)
        a = e.conflict_screen.analysis
        self.fact(eid, 'conflict_count', 'Screened potential findings', len(a.findings) if a else None, 'findings', True)
        for t in ('reopening_risk', 'concurrent_work', 'multiple_closures', 'sequencing_review'):
            self.fact(eid, 'conflict_types.' + t, 'Potential finding: ' + t, sum(f.finding_type == t for f in a.findings) if a else None, 'findings', True)
        self.fact(eid, 'incomplete_checks', 'Incomplete checks in selected inputs', len(e.indeterminate_checks), 'checks', True)
        self.fact(eid, 'lifespan', 'Supported lifespan', None, 'years')
        self.fact(eid, 'hypothetical', 'Hypothetical plan', True)
        actions = e.input_snapshot['scenario']['actions']
        for i, action in enumerate(actions):
            cost = next(c for c in e.action_costs if c.action_id == action['id'])
            for path, label, value, unit in [
                ('quantity', 'Priced scope', str(cost.quantity_m2) if cost.quantity_m2 is not None else None, 'm2'),
                ('method', 'Supported repair category', action['repair_category'] if action['repair_option_id'] else None, None),
                ('geometry', 'Supplied footprint present', True if action['scope']['geometry'] is not None else None, None),
                ('closures', 'Supplied closure declarations present', True if action['schedule'] and action['schedule']['closure_intervals'] is not None else None, None)]:
                self.fact(eid, f'actions.{i}.{path}', f'Action {i+1} {label}', value, unit)
            for key in ('start_date', 'end_date'):
                self.fact(eid, f'actions.{i}.schedule.{key}', f'Action {i+1} supplied {key}', action['schedule'][key] if action['schedule'] else None, 'date')
        for fact in self.facts[first_fact:]:
            fact.label = f'Scenario {e.scenario_id} revision {e.scenario_revision}: ' + fact.label

    def build(self, context: Context):
        if context.type == 'road': self.road(require(self.roads.get(context.record_ids[0])))
        elif context.type == 'assessment':
            # Direct keyed lookup avoids accepting a client-supplied assessment snapshot.
            a = require(self.planning.assessment(context.record_ids[0]))
            eid = self.record(a, 'assessment', self.sources(a.evidence_ids))
            for key, unit in [('category', None), ('rating', 'synthetic 1–10 higher better'), ('assessed_on', 'date')]:
                v = getattr(a, key)
                self.fact(eid, key, 'Demo ' + key, str(v) if v is not None else None, unit)
        elif context.type == 'estimate': self.estimate(require(self.planning.get_estimate(context.record_ids[0])))
        elif context.type == 'project': self.project(require(self.conflicts.project(context.record_ids[0])))
        elif context.type == 'conflict':
            f = require(self.conflicts.finding(context.record_ids[0]))
            self.conflict(f, require(self.conflicts.analysis(f.analysis_id)))
        else:
            evaluations = [require(self.scenarios.evaluation(i)) for i in sorted(context.record_ids)]
            for e in evaluations: self.evaluation(e)
            if context.type == 'comparison':
                c = compare(evaluations)  # existing M4 basis checks; never recompute costs
                eid = self.record(c, 'comparison', input_hash=c.input_hash, version=c.method_version)
                by_id = {e.id: e.scenario_id for e in evaluations}
                for i, d in enumerate(c.deltas):
                    pair = by_id[d['from_evaluation_id']] + ' to ' + by_id[d['to_evaluation_id']]
                    self.fact(eid, f'deltas.{i}.base_cost_difference_usd', pair + ': base cost difference; inspect scope equivalence', d['base_cost_difference_usd'], 'USD', True)
                    self.fact(eid, f'deltas.{i}.comparable_scope', pair + ': comparable work scope', d['comparable_scope'], None, True)
                self.fact(eid, 'dominance_count', 'Dominance relations across disclosed objectives only', len(c.dominance), 'relations', True)
        missing = sorted(set(['Utility coverage and buried depth are unknown.'] + [f'{f.label} is unknown or not applicable; inspect source record.' for f in self.facts if f.value is None]))
        facts = self.facts[:MAX_FACTS]
        raw = dict(version='ai-evidence-v1', context=context.model_dump(mode='json'), records=[r.model_dump(mode='json') for r in self.records], facts=[f.model_dump(mode='json') for f in facts], missing_information=missing, limitations=LIMITATIONS,
            truncated=len(facts) < len(self.facts), omitted_fact_count=len(self.facts)-len(facts))
        # Stable prefix projection; no unannounced omission or partial JSON slicing.
        while len(json.dumps(raw, ensure_ascii=True).encode()) > MAX_BYTES and raw['facts']:
            raw['facts'].pop(); raw['omitted_fact_count'] += 1; raw['truncated'] = True
        if len(json.dumps(raw, ensure_ascii=True).encode()) > MAX_BYTES:
            raise EvidenceError(422, 'Evidence metadata exceeds bounded context; select a smaller context')
        package = EvidencePackage(**raw, snapshot_hash=canonical_hash(raw))
        validate_context(package)
        return package


def validate_context(package):
    raw = package.model_dump(mode='json', exclude={'snapshot_hash'})
    expected_kind = 'evaluation' if package.context.type == 'comparison' else package.context.type
    source_ids = {r.record_id for r in package.records if r.entity_type == expected_kind}
    if source_ids != set(package.context.record_ids):
        raise EvidenceError(409, 'Evidence does not belong to the requested context')
    ids = {r.evidence_id for r in package.records}
    if canonical_hash(raw) != package.snapshot_hash or len(ids) != len(package.records) or any(f.evidence_id not in ids for f in package.facts) or len({f.fact_id for f in package.facts}) != len(package.facts):
        raise EvidenceError(409, 'Evidence package integrity check failed')
