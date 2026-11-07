"""Versioned M4 proposals. Unknown values are valid drafts, never zero inputs."""
from datetime import date
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import Field, StringConstraints, model_validator
from shapely.geometry import box, shape

from app.schemas.roads import Schema, Geometry
from app.schemas.conflicts import WorkPolygon, ConflictAnalysis, AnalysisParameters
from app.schemas.planning import CostScenario, Duration, Suitability

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]
ID = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
Money = Annotated[Decimal, Field(ge=0, max_digits=16, decimal_places=2)]


def distinct(values, label):
    if len(set(values)) != len(values):
        raise ValueError(f'{label} must be distinct')


class Assumption(Schema):
    id: ID
    note: Text
    field_paths: list[Text] = Field(min_length=1)


class ScenarioEvidence(Schema):
    basis: Literal['source_record', 'planning_assumption', 'derived']
    evidence_ids: list[ID] = Field(min_length=1)
    record_id: ID | None = None
    record_field: Text | None = None
    note: Text | None = None
    method_version: ID | None = None

    @model_validator(mode='after')
    def valid(self):
        if self.basis == 'source_record':
            if not self.record_id or not self.record_field:
                raise ValueError('source_record requires record_id and record_field')
        elif self.record_id or self.record_field:
            raise ValueError('non-source provenance cannot assert a source record')
        if self.basis == 'planning_assumption' and not self.note:
            raise ValueError('assumptions require a note')
        if self.basis == 'derived' and not self.method_version:
            raise ValueError('derived provenance requires a version')
        return self


class Scope(Schema):
    extent: Literal['whole_segment', 'partial_area', 'utility_trench', 'unknown']
    description: Text
    geometry: WorkPolygon | Geometry | None = None
    location_status: Literal['approximate', 'unknown'] = 'unknown'

    @model_validator(mode='after')
    def valid(self):
        if (self.geometry is None) != (self.location_status == 'unknown'):
            raise ValueError('geometry and location_status disagree')
        if self.geometry and not box(-74.012, 40.710, -74.000, 40.720).covers(shape(self.geometry.model_dump())):
            raise ValueError('proposal geometry lies outside study window')
        return self


class QuantityProposal(Schema):
    value: Decimal | None = Field(default=None, gt=0, le=10000000, decimal_places=6)
    unit: Literal['m2'] = 'm2'
    derivation: Literal['road_dimensions', 'explicit_rectangle', 'explicit_area', 'unknown']
    length_m: Decimal | None = Field(default=None, gt=0, le=100000, decimal_places=3)
    width_m: Decimal | None = Field(default=None, gt=0, le=100, decimal_places=3)

    @model_validator(mode='after')
    def valid(self):
        if self.derivation in ('road_dimensions', 'explicit_area', 'unknown') and (self.length_m is not None or self.width_m is not None):
            raise ValueError('dimensions only accepted for explicit_rectangle')
        if self.derivation == 'explicit_rectangle':
            if self.length_m is None or self.width_m is None:
                raise ValueError('explicit rectangle requires both dimensions')
            if self.value is not None and self.value != self.length_m * self.width_m:
                raise ValueError('asserted area differs from rectangle')
        if self.derivation == 'explicit_area' and self.value is None:
            raise ValueError('explicit_area requires a positive area')
        if self.derivation == 'unknown' and self.value is not None:
            raise ValueError('unknown quantity cannot have a value')
        return self


class WorkCalendar(Schema):
    id: ID
    version: ID
    timezone: Literal['America/New_York'] = 'America/New_York'
    working_weekdays: list[Annotated[int, Field(strict=True, ge=1, le=7)]] = Field(min_length=1)
    excluded_dates: list[date] = Field(default_factory=list)
    evidence_ids: list[ID] = Field(min_length=1)
    note: Text

    @model_validator(mode='after')
    def valid(self):
        distinct(self.working_weekdays, 'weekdays')
        distinct(self.excluded_dates, 'excluded dates')
        return self


class Closure(Schema):
    start_date: date
    end_date: date
    lanes_closed: int = Field(strict=True, ge=0)
    evidence_ids: list[ID] = Field(min_length=1)
    note: Text

    @model_validator(mode='after')
    def valid(self):
        if self.start_date >= self.end_date:
            raise ValueError('closure start must precede end')
        return self


class SchedulingProposal(Schema):
    contract_version: Literal['schedule-proposal-v1'] = 'schedule-proposal-v1'
    start_date: date | None = None
    end_date: date | None = None
    basis: Literal['supplied_calendar_interval'] = 'supplied_calendar_interval'
    assumption_evidence_ids: list[ID] = Field(min_length=1)
    note: Text
    work_calendar: WorkCalendar | None = None
    closure_intervals: list[Closure] | None = None

    @model_validator(mode='after')
    def valid(self):
        if self.start_date and self.end_date and self.start_date >= self.end_date:
            raise ValueError('schedule start must precede end')
        previous = None
        for c in sorted(self.closure_intervals or [], key=lambda c: c.start_date):
            if not self.start_date or not self.end_date or c.start_date < self.start_date or c.end_date > self.end_date:
                raise ValueError('closures require a complete enclosing schedule')
            if previous and c.start_date < previous:
                raise ValueError('one action cannot have overlapping closure intervals')
            previous = c.end_date
        return self


class Constraints(Schema):
    earliest_start: date | None = None
    latest_end: date | None = None
    must_follow_action_ids: list[ID] = Field(default_factory=list)
    human_review_required: Literal[True] = True


class ScenarioAction(Schema):
    data_kind: Literal['derived'] = 'derived'
    synthetic_input: Literal[True] = True
    hypothetical: Literal[True] = True
    contract_version: Literal['scenario-action-v1'] = 'scenario-action-v1'
    id: ID
    road_segment_id: ID
    action_kind: Literal['repair', 'temporary_patch', 'repeat_restoration'] = 'repair'
    repair_category: Literal['preventive', 'resurface', 'reconstruct', 'temporary_patch', 'trench_restoration', 'unknown']
    repair_option_id: ID | None = None
    scope: Scope
    quantity: QuantityProposal
    input_provenance: dict[str, ScenarioEvidence]
    unknown_reasons: dict[str, Text] = Field(default_factory=dict)
    related_project_ids: list[ID] = Field(default_factory=list)
    schedule: SchedulingProposal | None = None
    constraints: Constraints = Field(default_factory=Constraints)

    @model_validator(mode='after')
    def valid(self):
        distinct(self.related_project_ids, 'related projects')
        distinct(self.constraints.must_follow_action_ids, 'predecessors')
        if self.id in self.constraints.must_follow_action_ids:
            raise ValueError('action cannot follow itself')
        if self.quantity.derivation == 'road_dimensions' and self.scope.extent != 'whole_segment':
            raise ValueError('road dimensions apply only to explicit whole-segment scope')
        if self.quantity.derivation == 'explicit_area' and self.scope.extent not in ('partial_area', 'utility_trench'):
            raise ValueError('direct area requires partial or trench scope')
        if self.scope.extent == 'unknown' and self.quantity.derivation != 'unknown':
            raise ValueError('unknown scope cannot have known quantity')
        if self.repair_category == 'temporary_patch' and self.action_kind != 'temporary_patch':
            raise ValueError('patch requires temporary_patch action')
        if self.repair_category == 'trench_restoration' and self.scope.extent != 'utility_trench':
            raise ValueError('restoration requires explicit trench scope')
        if self.scope.extent == 'utility_trench' and self.repair_option_id is not None:
            raise ValueError('current catalog has no reviewed trench-restoration method')
        required = ['repair_category', 'scope', 'quantity', 'constraints']
        if self.repair_option_id:
            required.append('repair_option_id')
        if self.scope.geometry:
            required.append('scope.geometry')
        if self.schedule:
            required.append('schedule')
        for path in required:
            if path not in self.input_provenance:
                raise ValueError(f'{path} requires provenance')
        missing = []
        if not self.repair_option_id:
            missing.append('repair_option_id')
        if self.quantity.derivation == 'unknown':
            missing.append('quantity')
        if not self.scope.geometry:
            missing.append('scope.geometry')
        if not self.schedule:
            missing.append('schedule')
        else:
            missing += [f'schedule.{f}' for f in ('start_date', 'end_date', 'closure_intervals') if getattr(self.schedule, f) is None]
        if self.scope.extent == 'unknown':
            missing.append('scope.extent')
        for path in missing:
            if path not in self.unknown_reasons:
                raise ValueError(f'{path} requires an unknown reason')
        if self.action_kind == 'repeat_restoration' and 'repeat_justification' not in self.input_provenance:
            raise ValueError('repeat work requires repeat_justification provenance')
        return self


class ProjectOverride(Schema):
    project_id: ID
    operation: Literal['exclude', 'replace']
    replacement_action_ids: list[ID] = Field(default_factory=list)
    reason: Text
    evidence_ids: list[ID] = Field(min_length=1)

    @model_validator(mode='after')
    def valid(self):
        distinct(self.replacement_action_ids, 'replacement actions')
        if bool(self.replacement_action_ids) != (self.operation == 'replace'):
            raise ValueError('only replace requires replacement actions')
        return self


class ScenarioDraft(Schema):
    contract_version: Literal['scenario-v1'] = 'scenario-v1'
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
    description: str = Field(default='', max_length=2000)
    planning_objective: Text = 'Compare planning costs and coordination requirements'
    dataset_snapshot_id: ID
    budget_usd: Money
    currency: Literal['USD'] = 'USD'
    planning_start: date
    planning_end: date
    cost_scope: Literal['roadwork_only'] = 'roadwork_only'
    cost_scope_note: Text | None = None
    review_note: Text | None = None
    status: Literal['draft', 'ready', 'archived'] = 'draft'
    actions: list[ScenarioAction] = Field(default_factory=list, max_length=50)
    assumptions: list[Assumption] = Field(default_factory=list)
    external_project_ids: list[ID] = Field(default_factory=list, max_length=50)
    project_overrides: list[ProjectOverride] = Field(default_factory=list)
    mobilization_groups: list[dict] = Field(default_factory=list)

    @model_validator(mode='after')
    def valid(self):
        if self.planning_start >= self.planning_end:
            raise ValueError('planning start must precede end')
        if self.mobilization_groups:
            raise ValueError('shared mobilization adjustments are unsupported; use independent catalog allowances')
        distinct([a.id for a in self.actions], 'action IDs')
        distinct([a.id for a in self.assumptions], 'assumption IDs')
        distinct(self.external_project_ids, 'external projects')
        distinct([o.project_id for o in self.project_overrides], 'project overrides')
        by_id = {a.id: a for a in self.actions}
        seen_semantics = set()
        for a in self.actions:
            semantic = a.model_dump_json(exclude={'id', 'input_provenance', 'unknown_reasons', 'constraints'})
            if semantic in seen_semantics:
                raise ValueError('duplicate semantic action would double count work')
            seen_semantics.add(semantic)
            c, s = a.constraints, a.schedule
            for d in [c.earliest_start, c.latest_end, s.start_date if s else None, s.end_date if s else None]:
                if d and not self.planning_start <= d <= self.planning_end:
                    raise ValueError('action dates/constraints must lie inside planning horizon')
            if c.earliest_start and c.latest_end and c.earliest_start >= c.latest_end:
                raise ValueError('constraint bounds are reversed')
            if s:
                if s.start_date and c.earliest_start and s.start_date < c.earliest_start:
                    raise ValueError('start violates earliest constraint')
                if s.end_date and c.latest_end and s.end_date > c.latest_end:
                    raise ValueError('end violates latest constraint')
            for pred in c.must_follow_action_ids:
                if pred not in by_id:
                    raise ValueError('unknown predecessor')
                ps = by_id[pred].schedule
                if s and ps and s.start_date and ps.end_date and ps.end_date > s.start_date:
                    raise ValueError('schedule violates precedence')
        visited = set()
        def visit(key, path):
            if key in path:
                raise ValueError('precedence cycle')
            if key in visited:
                return
            for pred in by_id[key].constraints.must_follow_action_ids:
                visit(pred, path | {key})
            visited.add(key)
        for key in by_id:
            visit(key, set())
        for o in self.project_overrides:
            if o.project_id not in self.external_project_ids:
                raise ValueError('override must reference selected external project')
            for aid in o.replacement_action_ids:
                if aid not in by_id or o.project_id not in by_id[aid].related_project_ids:
                    raise ValueError('replacement must identify related action')
        return self


class Scenario(ScenarioDraft):
    id: str
    revision: int
    revision_hash: str
    created_at: str
    updated_at: str
    method_version: Literal['scenario-v1'] = 'scenario-v1'
    data_kind: Literal['derived'] = 'derived'
    synthetic_input: Literal[True] = True
    hypothetical: Literal[True] = True


class ScenarioPatch(Schema):
    expected_revision: int = Field(ge=1, strict=True)
    # Full validated draft replacement inside PATCH keeps cross-field validation atomic.
    draft: ScenarioDraft


class ActionMutation(Schema):
    expected_revision: int = Field(ge=1, strict=True)
    action: ScenarioAction


class EvaluateRequest(AnalysisParameters):
    expected_revision: int = Field(ge=1, strict=True)


class ActionCost(Schema):
    action_id: str
    quantity_m2: Decimal | None
    quantity_provenance: dict
    unavailable_reason: str | None
    costs: dict[str, CostScenario] | None
    duration: Duration | None
    suitability: Suitability | None
    warnings: list[str]
    input_snapshot: dict
    input_hash: str
    method_version: Literal['scenario-cost-v1'] = 'scenario-cost-v1'


class HypotheticalScreen(Schema):
    adapter_version: Literal['hypothetical-conflict-adapter-v1'] = 'hypothetical-conflict-adapter-v1'
    analysis_context: Literal['hypothetical'] = 'hypothetical'
    scenario_id: str
    project_origins: dict
    original_projects: list[dict]
    overrides: list[dict]
    assumption_sources: list[dict]
    adapter_indeterminate_checks: list[str]
    warnings: list[str]
    analysis: ConflictAnalysis | None
    not_run_reason: str | None
    finding_contexts: dict[str, Literal['hypothetical', 'existing_project_screen']]
    input_hash: str
    result_hash: str


class ScenarioEvaluation(Schema):
    id: str
    scenario_id: str
    scenario_revision: int
    scenario_revision_hash: str
    evaluated_at: str
    baseline_source_hash: str
    input_snapshot: dict
    input_hash: str
    result_hash: str
    method_version: Literal['scenario-evaluation-v1'] = 'scenario-evaluation-v1'
    analysis_versions: dict[str, str]
    action_costs: list[ActionCost]
    known_subtotal_usd: dict[str, str]
    cost_total_usd: dict[str, str] | None
    budget_usd: str
    budget_headroom_usd: dict[str, str] | None
    budget_status: Literal['within_budget', 'over_budget', 'indeterminate']
    upper_bound_within_budget: bool | None
    preliminary_days_sum: int | None
    elapsed_days: int | None
    scheduled_road_workdays: int | None
    lane_closure_days: int | None
    overlapping_closure_pairs: int | None
    affected_road_ids: list[str]
    action_lifespan_years: dict[str, None]
    conflict_screen: HypotheticalScreen
    indeterminate_checks: list[str]
    warnings: list[str]
    utility_coverage: Literal['unknown'] = 'unknown'
    review_required: Literal[True] = True
    data_kind: Literal['derived'] = 'derived'
    synthetic_input: Literal[True] = True
    hypothetical: Literal[True] = True


class ComparisonRequest(Schema):
    evaluation_ids: list[ID] = Field(min_length=2, max_length=3)

    @model_validator(mode='after')
    def valid(self):
        distinct(self.evaluation_ids, 'evaluations')
        return self


class ScenarioComparison(Schema):
    id: str
    evaluation_ids: list[str]
    common_basis: dict
    rows: list[dict]
    deltas: list[dict]
    dominance: list[dict]
    tradeoffs: list[str]
    warnings: list[str]
    input_hash: str
    method_version: Literal['scenario-comparison-v1'] = 'scenario-comparison-v1'
