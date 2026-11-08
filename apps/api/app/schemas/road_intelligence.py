"""Local human review annotations; not municipal verification or work authorization."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.municipal import Classification


class AssociationReview(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    base_snapshot_id: str
    source_record_id: str
    target_road_id: str
    source_record_hash: str = Field(pattern=r'^[0-9a-f]{64}$')
    target_record_hash: str = Field(pattern=r'^[0-9a-f]{64}$')
    candidate_hash: str = Field(pattern=r'^[0-9a-f]{64}$')
    candidate_set_hash: str | None = Field(default=None, pattern=r'^[0-9a-f]{64}$')
    parameter_hash: str = Field(pattern=r'^[0-9a-f]{64}$')
    status: Literal['accepted', 'rejected']
    scope: Literal['whole_road', 'partial']
    scope_reason: str = Field(min_length=1, max_length=2000)
    reviewer: str = Field(min_length=1, max_length=200)
    reason: str = Field(min_length=1, max_length=2000)
    evidence_refs: list[str] = Field(min_length=1, max_length=20)


class PilotGrading(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    raw_rating: str | None
    rounded_rating: int | None = Field(ge=0, le=10)
    category: Literal['good', 'fair', 'poor', 'unknown']
    reason: str | None
    non_rating_reason: str | None
    policy_id: Literal['civicplain-pilot-pavement-v1.0']
    policy_version: Literal['1.0']
    policy_hash: str = Field(pattern=r'^[0-9a-f]{64}$')
    classification: Literal['derived_calculation']
    policy_classification: Literal['planning_assumption']
    official_nyc_dot_policy: Literal[False]


class ConditionHistory(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    id: str
    rating: str | None
    inspection_at: str | None
    direction: str | None
    road_type: str | None
    non_rating_reason: str | None
    multipass: object | None
    source_revision_id: str
    eligible: bool
    reason: str | None
    record_hash: str
    association_id: str
    association_hash: str
    field_classifications: dict[str, Classification]
    grading: PilotGrading | None = None
    association_review: dict | None = None


class ConditionSummary(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    method_version: Literal['road-condition-v1', 'road-condition-v2-pilot']
    intelligence_release_id: str | None
    snapshot_id: str
    road_id: str
    classification: Literal['derived_calculation']
    category: Literal['good', 'fair', 'poor', 'unknown']
    category_reason: str | None
    rounded_rating: int | None = None
    policy: dict | None = None
    rating: str | None
    inspection_at: str | None
    source_revision_id: str | None
    latest_usable_id: str | None
    as_of_date: str
    age_days: int | None = Field(ge=0)
    stale_after_days: int | None = Field(ge=0, le=36500)
    stale: bool | None
    recency_basis: str
    reason: str | None
    history: list[ConditionHistory]
    utility_coverage: Literal['unknown']
    field_classifications: dict[str, Classification]
    input_hash: str
    result_hash: str
