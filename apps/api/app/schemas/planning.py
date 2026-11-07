"""M2 contracts. All current import/rate catalogs are explicitly synthetic."""
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import Field, model_validator

from app.schemas.roads import ConditionSummary, Schema

Surface = Literal['asphalt', 'concrete', 'gravel', 'unknown']
Treatment = Literal['preventive', 'resurface', 'reconstruct']


class AssetAttributes(Schema):
    road_segment_id: str
    length_m: Decimal | None = Field(default=None, gt=0, le=100000, max_digits=12, decimal_places=3)
    width_m: Decimal | None = Field(default=None, gt=0, le=100, max_digits=12, decimal_places=3)
    surface_material: Surface = 'unknown'
    functional_class: Literal['local', 'collector', 'arterial', 'unknown'] = 'unknown'
    dimension_basis: Literal['synthetic_planning_assumption'] = 'synthetic_planning_assumption'
    evidence_ids: list[str] = Field(min_length=1)
    data_kind: Literal['synthetic'] = 'synthetic'
    synthetic_input: Literal[True] = True
    notes: str


class Assessment(ConditionSummary):
    id: str = Field(min_length=1)
    road_segment_id: str
    dataset_snapshot_id: str
    assessment_method: Literal['synthetic_fixture'] = 'synthetic_fixture'
    notes: str
    field_evidence: dict[str, list[str]]
    unknown_reasons: dict[str, str]
    limitations: list[str]
    created_at: datetime

    @model_validator(mode='after')
    def assessment_provenance(self):
        if self.created_at.utcoffset() is None:
            raise ValueError('created_at requires a UTC offset')
        for field in ('rating', 'category', 'assessed_on'):
            if getattr(self, field) is not None:
                refs = self.field_evidence.get(field, [])
                if not refs or not set(refs) <= set(self.evidence_ids):
                    raise ValueError(f'{field} requires resolved provenance')
            elif field not in self.unknown_reasons:
                raise ValueError(f'{field} requires an unknown reason')
        return self


class CostRates(Schema):
    low: Decimal = Field(ge=0, le=100000)
    base: Decimal = Field(ge=0, le=100000)
    high: Decimal = Field(ge=0, le=100000)

    @model_validator(mode='after')
    def ordered(self):
        if not self.low <= self.base <= self.high:
            raise ValueError('rates require low <= base <= high')
        return self


class RepairOption(Schema):
    id: str
    treatment: Treatment
    label: str
    description: str
    scope_of_work: str
    suitability_conditions: str
    material_assumptions: str
    work_activities: list[str] = Field(min_length=1)
    quantity_unit: Literal['m2'] = 'm2'
    unit_rates_usd: CostRates
    rate_inclusions: Literal['materials, labor and equipment bundled; do not add them again']
    mobilization_usd: Decimal = Field(ge=0, le=10000000)
    traffic_management_usd: Decimal = Field(ge=0, le=10000000)
    contingency_fraction: Decimal = Field(ge=0, le=1)
    productivity_per_day: Decimal = Field(gt=0, le=1000000)
    productivity_unit: Literal['m2/active_workday'] = 'm2/active_workday'
    setup_days: int = Field(ge=0, le=365)
    curing_days: int = Field(ge=0, le=365)
    price_basis_date: date
    sensitivity_basis: str
    exclusions: list[str]
    limitations: list[str]
    evidence_ids: list[str] = Field(min_length=1)
    data_kind: Literal['synthetic'] = 'synthetic'
    synthetic_input: Literal[True] = True


class PlanningAssumptions(Schema):
    length_m: Decimal | None = Field(default=None, gt=0, le=100000, max_digits=12, decimal_places=3)
    width_m: Decimal | None = Field(default=None, gt=0, le=100, max_digits=12, decimal_places=3)
    unit: Literal['m'] = 'm'
    note: str = Field(min_length=1, max_length=1000)

    @model_validator(mode='after')
    def explicit(self):
        if not self.note.strip() or (self.length_m is None and self.width_m is None):
            raise ValueError('an explicit dimension and a nonblank assumption note are required')
        return self


class EstimateRequest(Schema):
    road_segment_id: str = Field(min_length=1)
    repair_option_id: str = Field(min_length=1)
    dataset_snapshot_id: str = Field(min_length=1)
    planning_assumptions: PlanningAssumptions | None = None


class Suitability(Schema):
    status: Literal['candidate_requires_review', 'not_indicated', 'requires_review']
    rule_id: str
    rationale: str
    human_review_required: Literal[True] = True


class LineItem(Schema):
    label: str
    quantity: Decimal = Field(ge=0)
    unit: Literal['m2', 'allowance']
    unit_rate_usd: str
    amount_usd: str
    evidence_ids: list[str]


class CostScenario(Schema):
    line_items: list[LineItem]
    subtotal_usd: str
    contingency_fraction: Decimal
    contingency_usd: str
    total_usd: str


class Duration(Schema):
    active_workdays: int = Field(ge=1)
    setup_days: int = Field(ge=0)
    curing_days: int = Field(ge=0)
    total_preliminary_days: int = Field(ge=1)
    productivity_per_day: Decimal = Field(gt=0)
    productivity_unit: Literal['m2/active_workday'] = 'm2/active_workday'
    basis: str


class Calculation(Schema):
    road_segment_id: str
    repair_option_id: str
    repair_category: Treatment
    currency: Literal['USD'] = 'USD'
    quantity: Decimal = Field(gt=0)
    quantity_unit: Literal['m2'] = 'm2'
    dimension_provenance: dict
    scenarios: dict[Literal['low', 'base', 'high'], CostScenario]
    duration: Duration
    suitability: Suitability
    assumptions: list[str]
    warnings: list[str]
    evidence_ids: list[str]
    method_version: Literal['repair-estimate-v1'] = 'repair-estimate-v1'
    data_kind: Literal['derived'] = 'derived'
    synthetic_input: Literal[True] = True


class Estimate(Calculation):
    id: str
    created_at: str
    dataset_snapshot_id: str
    input_hash: str
    result_hash: str
    input_snapshot: dict


class OptionComparison(Schema):
    option: RepairOption
    suitability: Suitability
    preview: Calculation | None
    unavailable_reason: str | None
