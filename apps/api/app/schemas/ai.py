"""M5 contracts: the provider selects claims; only the server renders assertions."""
from datetime import datetime
from typing import Annotated, Literal
from pydantic import Field, StringConstraints, model_validator
from app.schemas.roads import Schema

ID = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=150)]
ContextType = Literal['road', 'assessment', 'estimate', 'conflict', 'project', 'evaluation', 'comparison']
TaskType = Literal['explain_estimate', 'explain_conflict', 'explain_comparison', 'explain_official', 'ask']
Mode = Literal['deterministic', 'ai']
Classification = Literal['verified_record_fact', 'deterministic_calculation', 'conditional_interpretation', 'requires_human_review']


class Context(Schema):
    type: ContextType
    record_ids: list[ID] = Field(min_length=1, max_length=3)

    @model_validator(mode='after')
    def cardinality(self):
        if len(set(self.record_ids)) != len(self.record_ids):
            raise ValueError('record references must be distinct')
        if (self.type == 'comparison' and len(self.record_ids) < 2) or (self.type != 'comparison' and len(self.record_ids) != 1):
            raise ValueError('comparison requires 2–3 evaluations; other contexts require one record')
        return self


class EstimateExplanationRequest(Schema):
    estimate_id: ID
    mode: Mode = 'deterministic'


class ConflictExplanationRequest(Schema):
    conflict_id: ID
    mode: Mode = 'deterministic'


class ComparisonExplanationRequest(Schema):
    evaluation_ids: list[ID] = Field(min_length=2, max_length=3)
    mode: Mode = 'deterministic'

    @model_validator(mode='after')
    def distinct(self):
        Context(type='comparison', record_ids=self.evaluation_ids)
        return self


class AskRequest(Schema):
    context: Context
    question: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]
    mode: Mode = 'deterministic'


class EvidenceRecord(Schema):
    evidence_id: str
    entity_type: ContextType
    record_id: str
    record_hash: str
    input_hash: str | None
    calculation_version: str | None
    dataset_snapshot_id: str | None
    source_revisions: dict[str, str]
    synthetic_input: bool
    data_kind: Literal['synthetic', 'observed', 'derived']


class Fact(Schema):
    fact_id: str
    evidence_id: str
    field: str
    label: str
    value: str | int | float | bool | None
    unit: str | None
    classification: Classification


class EvidencePackage(Schema):
    version: Literal['ai-evidence-v1'] = 'ai-evidence-v1'
    context: Context
    records: list[EvidenceRecord]
    facts: list[Fact]
    missing_information: list[str]
    limitations: list[str]
    truncated: bool
    omitted_fact_count: int
    snapshot_hash: str


class ClaimSelection(Schema):
    fact_id: str
    evidence_id: str
    template_id: Literal['fact_value']


class ProviderSelection(Schema):
    # No free prose, monetary amounts, units, dates, SQL or tool arguments are accepted.
    evidence_snapshot_hash: str
    summary_template_id: Literal['bounded_summary']
    claim_selections: list[ClaimSelection] = Field(min_length=1, max_length=12)
    limitation_codes: list[Literal['source_limits', 'human_review', 'unknown_utilities', 'synthetic_labels']]
    recommendation_code: Literal['verify_inputs', 'coordinate_projects', 'review_tradeoffs']


class Finding(Schema):
    finding_id: str
    claim_text: str
    supporting_evidence_ids: list[str]
    fact_refs: list[str]
    classification: Classification


class Explanation(Schema):
    explanation_id: str
    task_type: TaskType
    evidence_snapshot_hash: str
    summary: str
    key_findings: list[Finding]
    tradeoffs: list[str]
    uncertainties: list[str]
    missing_information: list[str]
    suggested_review_actions: list[str]
    citations: list[EvidenceRecord]
    evidence: EvidencePackage
    provider_status: Literal['deterministic', 'openai', 'fallback']
    validation_status: Literal['validated', 'fallback_validated', 'insufficient_evidence']
    fallback_reason: str | None
    model_label: str | None
    generated_at: datetime
    source_classification: Literal['synthetic', 'observed', 'mixed', 'derived']
    human_review_required: Literal[True] = True
    warnings: list[str]
    audit_reference: str


class ReviewRequest(Schema):
    reviewer_label: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
    note: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]
    acknowledged_limitations: list[Literal['synthetic_inputs', 'unknown_utilities', 'human_review']] = Field(min_length=1, max_length=3)
