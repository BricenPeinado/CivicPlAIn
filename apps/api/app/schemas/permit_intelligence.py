"""Typed permit evidence projections; never accepted by work-project engines."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

class PermitCandidate(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)
    road_id: str
    source_record_hash: str = Field(pattern=r'^[a-f0-9]{64}$')
    target_record_hash: str = Field(pattern=r'^[a-f0-9]{64}$')
    on_street_name_agrees: bool
    street_code_agrees: bool
    from_endpoint_road_ids: list[str]
    to_endpoint_road_ids: list[str]
    distance_m: float | None = Field(ge=0,allow_inf_nan=False)
    grade_agreement: Literal['unknown']
    roadbed_agreement: Literal['unknown']
    work_footprint: Literal['unknown']


class PermitLocation(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)
    method_version: Literal['permit-road-reference-v1']
    snapshot_id: str
    permit_release_id: str | None
    status: Literal['located','candidate','unlocated','outside_coverage','invalid_evidence']
    accepted_road_ids: list[str]
    accepted_associations: list[dict]
    rejected_associations: list[dict]
    candidates: list[PermitCandidate]
    candidate_set_hash: str = Field(pattern=r'^[a-f0-9]{64}$')
    reasons: list[str]
    location_meaning: str
    actual_schedule: Literal['unknown']
    parameter_hash: str = Field(pattern=r'^[a-f0-9]{64}$')
    classification: Literal['derived_calculation']
    result_hash: str = Field(pattern=r'^[a-f0-9]{64}$')
