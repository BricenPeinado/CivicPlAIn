"""Validated M1 road transport and fixture contracts."""
import math
from datetime import date, datetime
from decimal import Decimal, DecimalException
from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field, model_validator
from shapely.geometry import LineString as SpatialLine


class Schema(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class Geometry(Schema):
    type: Literal["LineString"]
    coordinates: list[tuple[float, float]] = Field(min_length=2)

    @model_validator(mode="after")
    def valid_line(self):
        if any(not math.isfinite(x) or not math.isfinite(y) or not -180 <= x <= 180
               or not -90 <= y <= 90 for x, y in self.coordinates):
            raise ValueError("coordinates must be finite EPSG:4326 longitude/latitude")
        line = SpatialLine(self.coordinates)
        if not line.is_valid or line.length == 0:
            raise ValueError("geometry must be a valid nonzero-length LineString")
        return self


class ConditionSummary(Schema):
    category: Literal["good", "fair", "poor", "unknown"]
    rating: Decimal | None = None
    rating_scale: Literal["synthetic-1-10-higher-better"] | None = None
    assessed_on: date | None = None
    evidence_ids: list[str] = Field(min_length=1)
    data_kind: Literal["synthetic"] = "synthetic"
    synthetic_input: Literal[True] = True

    @model_validator(mode="after")
    def valid_rating(self):
        if self.category == "unknown":
            if self.rating is not None or self.rating_scale is not None or self.assessed_on is not None:
                raise ValueError("unknown condition cannot carry an assessment")
        else:
            if self.rating is None or not 1 <= self.rating <= 10 or self.rating_scale is None:
                raise ValueError("known demo condition requires a rating and its scale")
            expected = "good" if self.rating >= 8 else "fair" if self.rating >= 5 else "poor"
            if self.category != expected:
                raise ValueError("category does not match documented synthetic rating rule")
        return self


class Road(Schema):
    id: str = Field(min_length=1)
    dataset_snapshot_id: str
    evidence_ids: list[str] = Field(min_length=1)
    data_kind: Literal["synthetic"]
    synthetic_input: Literal[True]
    field_evidence: dict[str, list[str]]
    unknown_reasons: dict[str, str]
    limitations: list[str]
    created_at: datetime
    name: str | None
    source_segment_key: str | None = None
    geometry: Geometry
    study_area_id: Literal["lower-manhattan-window-v1"]
    length_m: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=3)
    width_m: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=3)
    lane_count: int | None = Field(default=None, ge=1)
    utility_coverage: Literal["unknown"] = "unknown"
    coverage_as_of: date | None = None
    condition_summary: ConditionSummary
    surface_material: Literal["asphalt", "concrete", "gravel", "unknown"] = "unknown"
    functional_class: Literal["local", "collector", "arterial", "unknown"] = "unknown"
    dimension_basis: dict[str, Literal["synthetic_planning_assumption", "legacy_synthetic_basis_unknown"]] = Field(default_factory=dict)
    notes: str | None = None

    repairable_area_m2: Decimal | None = Field(default=None, ge=0)

    @model_validator(mode="before")
    @classmethod
    def legacy_dimensions(cls, value):
        # M1 allowed sourced dimensions but had no area/basis fields. Preserve
        # readable historical records without relabeling them as measurements.
        if isinstance(value, dict) and "dimension_basis" not in value and "repairable_area_m2" not in value:
            value = {**value, "dimension_basis": {}}
            for field in ("length_m", "width_m"):
                if value.get(field) is not None:
                    value["dimension_basis"][field] = "legacy_synthetic_basis_unknown"
            try:
                if value.get("length_m") is not None and value.get("width_m") is not None:
                    value["repairable_area_m2"] = Decimal(str(value["length_m"])) * Decimal(str(value["width_m"]))
            except (DecimalException, ValueError, TypeError):
                pass  # Field validation supplies the actual error.
        return value

    @model_validator(mode="after")
    def provenance(self):
        if self.created_at.utcoffset() is None:
            raise ValueError("created_at requires a UTC offset")
        if not self.id.startswith("demo-"):
            raise ValueError("synthetic road IDs require a demo- prefix")
        for path, refs in self.field_evidence.items():
            if not refs or not set(refs) <= set(self.evidence_ids):
                raise ValueError(f"unresolved evidence for {path}")
        expected_area = self.length_m * self.width_m if self.length_m is not None and self.width_m is not None else None
        if self.repairable_area_m2 != expected_area:
            raise ValueError("repairable_area_m2 must equal length_m * width_m or remain null when dimensions are unknown")
        required = ["geometry"]
        for field in ("length_m", "width_m"):
            if getattr(self, field) is not None and field not in self.dimension_basis:
                raise ValueError(f"{field} requires an explicit dimension basis")
        for field in ("surface_material", "functional_class"):
            if getattr(self, field) != "unknown":
                required.append(field)
        for field in ("length_m", "width_m", "lane_count"):
            if getattr(self, field) is not None:
                required.append(field)
        if self.condition_summary.category != "unknown":
            required += ["condition_summary.rating", "condition_summary.category"]
        if self.condition_summary.assessed_on is not None:
            required.append("condition_summary.assessed_on")
        if any(field not in self.field_evidence for field in required):
            raise ValueError("material fields require provenance")
        for field in ("name", "source_segment_key", "length_m", "width_m", "lane_count", "coverage_as_of"):
            if getattr(self, field) is None and field not in self.unknown_reasons:
                raise ValueError(f"null {field} requires an unknown reason")
        for field in ("rating", "rating_scale", "assessed_on"):
            if getattr(self.condition_summary, field) is None and f"condition_summary.{field}" not in self.unknown_reasons:
                raise ValueError(f"unknown condition {field} requires a reason")
        if not set(self.condition_summary.evidence_ids) <= set(self.evidence_ids):
            raise ValueError("condition evidence must resolve")
        return self


class Evidence(Schema):
    id: str
    title: str
    publisher: str
    source_kind: Literal["demo_assumption"]
    verification_status: Literal["synthetic_demo"]
    uri: str
    retrieved_at: datetime | None = None
    observed_on: date | None = None
    version: str
    checksum_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    original_crs: Literal["EPSG:4326"]
    coverage_note: str
    reliability_note: str
    license_note: str
    unknown_reasons: dict[str, str]


class Meta(Schema):
    request_id: str
    dataset_snapshot_id: str | None
    warnings: list[str]
    next_cursor: str | None = None
    latest_usable_id: str | None = None


T = TypeVar("T")


class Envelope(Schema, Generic[T]):
    data: T
    meta: Meta


class Health(Schema):
    status: Literal["ok"] = "ok"
    api_version: Literal["v1"] = "v1"
    data_ready: bool
    ai_mode: Literal["deterministic"] = "deterministic"


class Feature(Schema):
    type: Literal["Feature"] = "Feature"
    id: str
    geometry: Geometry
    properties: dict


class FeatureCollection(Schema):
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[Feature]
    meta: Meta
