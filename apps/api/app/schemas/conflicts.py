"""M3 validated project, evidence and immutable analysis transport contracts."""
import math
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import Field, model_validator
from shapely.geometry import shape, box

from app.schemas.roads import Schema, Geometry


class WorkPolygon(Schema):
    type: Literal['Polygon']
    coordinates: list[list[tuple[float, float]]] = Field(min_length=1)

    @model_validator(mode='after')
    def topology(self):
        for ring in self.coordinates:
            if len(ring) < 4 or ring[0] != ring[-1]:
                raise ValueError('polygon rings must be explicitly closed with at least four positions')
            if any(not math.isfinite(x) or not math.isfinite(y) or not -180 <= x <= 180 or not -90 <= y <= 90 for x, y in ring):
                raise ValueError('coordinates must be finite EPSG:4326 longitude/latitude')
        geom = shape(self.model_dump())
        if geom.is_empty or not geom.is_valid or geom.area == 0:
            raise ValueError('invalid or empty polygon; geometry is never silently repaired')
        return self


class WorkProject(Schema):
    id: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=2000)
    kind: Literal['road_repair', 'utility', 'other']
    infrastructure_category: Literal['water', 'sewer', 'gas', 'electric', 'telecommunications', 'road_resurfacing', 'road_reconstruction', 'other']
    work_type: Literal['resurfacing', 'reconstruction', 'excavation', 'inspection', 'maintenance', 'other']
    responsible_organization: str | None = Field(default=None, min_length=1, max_length=200)
    schedule_status: Literal['planned', 'tentative', 'active', 'completed', 'cancelled', 'unknown']
    schedule_basis: Literal['confirmed_source', 'permit_window', 'assumed_demo', 'unknown']
    start_date: date | None
    end_date: date | None
    actual_start_date: date | None = None
    actual_end_date: date | None = None
    geometry: WorkPolygon | Geometry | None
    location_status: Literal['source_reported', 'approximate', 'unknown']
    road_segment_ids: list[str] = Field(max_length=30)
    excavation_required: bool | None = None
    lanes_closed: int | None = Field(default=None, ge=0, strict=True)
    estimated_cost_usd: Decimal | None = Field(default=None, ge=0, max_digits=16, decimal_places=2)
    currency: Literal['USD'] = 'USD'
    dataset_snapshot_id: str
    evidence_ids: list[str] = Field(min_length=1)
    field_evidence: dict[str, list[str]]
    unknown_reasons: dict[str, str]
    limitations: list[str]
    data_kind: Literal['synthetic', 'observed']
    synthetic_input: bool
    created_at: datetime
    updated_at: datetime

    @model_validator(mode='after')
    def consistent(self):
        for start, end in [('start_date', 'end_date'), ('actual_start_date', 'actual_end_date')]:
            if getattr(self, start) and getattr(self, end) and getattr(self, start) >= getattr(self, end):
                raise ValueError(f'{start} must precede {end}; intervals are half-open')
        if self.actual_end_date and not self.actual_start_date:
            raise ValueError('actual end requires actual start')
        if self.actual_end_date and self.schedule_status != 'completed':
            raise ValueError('actual end requires completed status')
        if self.created_at.utcoffset() is None or self.updated_at.utcoffset() is None or self.updated_at < self.created_at:
            raise ValueError('timestamps require offsets and updated_at >= created_at')
        if not self.title.strip() or not self.description.strip():
            raise ValueError('title and description cannot be blank')
        if len(set(self.road_segment_ids)) != len(self.road_segment_ids):
            raise ValueError('duplicate road references')
        if (self.geometry is None) != (self.location_status == 'unknown'):
            raise ValueError('unknown geometry requires unknown location status; approximate geometry must be explicit')
        if self.geometry and not box(-74.012, 40.710, -74.000, 40.720).covers(shape(self.geometry.model_dump())):
            raise ValueError('work geometry must lie within the bounded study window')
        if self.synthetic_input != (self.data_kind == 'synthetic'):
            raise ValueError('project classification and synthetic flag disagree')
        if self.data_kind == 'synthetic' and not self.id.startswith('demo-'):
            raise ValueError('synthetic project IDs require demo- prefix')
        expected_kind = 'utility' if self.infrastructure_category in {'water', 'sewer', 'gas', 'electric', 'telecommunications'} else 'road_repair' if self.infrastructure_category.startswith('road_') else 'other'
        if self.kind != expected_kind:
            raise ValueError('infrastructure category and project kind disagree')
        if self.schedule_basis == 'unknown' and (self.start_date or self.end_date):
            raise ValueError('populated planned dates require schedule source basis')
        for refs in self.field_evidence.values():
            if not refs or not set(refs) <= set(self.evidence_ids):
                raise ValueError('field evidence must resolve to project sources')
        for field in ['infrastructure_category', 'work_type', 'schedule_status', 'schedule_basis', 'location_status', 'road_segment_ids', 'geometry', 'start_date', 'end_date', 'actual_start_date', 'actual_end_date', 'responsible_organization', 'excavation_required', 'lanes_closed', 'estimated_cost_usd']:
            value = getattr(self, field)
            if value is None:
                if not self.unknown_reasons.get(field):
                    raise ValueError(f'unknown {field} requires a reason')
            elif not self.field_evidence.get(field):
                raise ValueError(f'{field} requires provenance')
        return self


class AnalysisParameters(Schema):
    proximity_m: float = Field(default=5, ge=0, le=100, strict=True, allow_inf_nan=False)
    corridor_m: float = Field(default=5, ge=0, le=50, strict=True, allow_inf_nan=False)
    reopening_horizon_days: int = Field(default=30, ge=0, le=365, strict=True)


class AnalysisRequest(AnalysisParameters):
    dataset_snapshot_id: str = Field(min_length=1)
    project_ids: list[str] = Field(min_length=1, max_length=50)

    @model_validator(mode='after')
    def unique_ids(self):
        if len(set(self.project_ids)) != len(self.project_ids):
            raise ValueError('project IDs must be distinct')
        return self


class SpatialEvidence(Schema):
    classifications: list[Literal['confirmed_geometric_overlap', 'shared_affected_road', 'proximity_based_potential_overlap', 'insufficient_spatial_information']]
    distance_m: float | None = Field(default=None, ge=0)
    polygon_overlap: bool
    shared_road_ids: list[str]
    shared_corridor_ids: list[str]
    geometry_intersects: bool
    basis: str


class TemporalEvidence(Schema):
    intervals: dict[str, list[date | None]]
    interval_basis: dict[str, Literal['planned', 'actual']]
    overlap_start: date | None = None
    overlap_end: date | None = None
    gap_days: int | None = Field(default=None, ge=0)
    preceding_project_id: str | None = None
    basis: str = 'America/New_York civil dates; [start, end); adjacent intervals do not overlap.'


class ConflictFinding(Schema):
    id: str
    analysis_id: str
    project_ids: list[str] = Field(min_length=2, max_length=2)
    affected_road_ids: list[str]
    finding_type: Literal['concurrent_work', 'reopening_risk', 'multiple_closures', 'sequencing_review']
    priority: Literal['coordination_review'] = 'coordination_review'
    spatial_evidence: SpatialEvidence
    temporal_evidence: TemporalEvidence
    explanation: str
    required_review: list[str]
    data_quality_warnings: list[str]
    evidence_ids: list[str]
    method_version: str
    input_hash: str
    detected_at: datetime
    data_kind: Literal['derived'] = 'derived'
    synthetic_input: bool

    @model_validator(mode='after')
    def coherent_evidence(self):
        if self.project_ids != sorted(set(self.project_ids)):
            raise ValueError('finding pair must be distinct and canonically sorted')
        if self.detected_at.utcoffset() is None:
            raise ValueError('finding detection timestamp requires an offset')
        t = self.temporal_evidence
        if set(t.intervals) != set(self.project_ids) or set(t.interval_basis) != set(self.project_ids):
            raise ValueError('temporal evidence must identify both projects')
        if self.finding_type in ('concurrent_work', 'multiple_closures'):
            if t.overlap_start is None or t.overlap_end is None or t.overlap_start >= t.overlap_end:
                raise ValueError('concurrent finding requires positive date overlap')
        elif t.gap_days is None or t.preceding_project_id not in self.project_ids:
            raise ValueError('sequential finding requires a gap and preceding project')
        return self


class IndeterminateCheck(Schema):
    project_ids: list[str]
    missing_fields: list[str]
    reason: str
    spatial_evidence: SpatialEvidence


class ConflictAnalysis(Schema):
    id: str
    dataset_snapshot_id: str
    findings: list[ConflictFinding]
    indeterminate_checks: list[IndeterminateCheck]
    excluded_project_ids: list[str]
    possible_pair_count: int
    checked_pair_count: int
    utility_coverage: Literal['unknown'] = 'unknown'
    warnings: list[str]
    parameters: AnalysisParameters
    method_version: str
    detected_at: datetime
    input_snapshot: dict
    input_hash: str
    result_hash: str
