export interface AIContext { type: 'road' | 'assessment' | 'estimate' | 'conflict' | 'project' | 'evaluation' | 'comparison'; record_ids: string[] }
export interface AIEvidenceRecord { evidence_id: string; entity_type: AIContext['type']; record_id: string; record_hash: string; input_hash: string | null; calculation_version: string | null; dataset_snapshot_id: string | null; source_revisions: Record<string,string>; synthetic_input: boolean; data_kind: string }
export interface AIFact { fact_id: string; evidence_id: string; field: string; label: string; value: string | number | boolean | null; unit: string | null; classification: string }
export interface AIExplanation {
  explanation_id: string; task_type: string; evidence_snapshot_hash: string; summary: string;
  key_findings: { finding_id: string; claim_text: string; supporting_evidence_ids: string[]; fact_refs: string[]; classification: string }[];
  tradeoffs: string[]; uncertainties: string[]; missing_information: string[]; suggested_review_actions: string[];
  citations: AIEvidenceRecord[]; evidence: { records: AIEvidenceRecord[]; facts: AIFact[]; truncated: boolean; omitted_fact_count: number; limitations: string[] };
  provider_status: 'deterministic' | 'openai' | 'fallback'; validation_status: 'validated' | 'fallback_validated' | 'insufficient_evidence';
  fallback_reason: string | null; model_label: string | null; generated_at: string; source_classification: string;
  human_review_required: true; warnings: string[]; audit_reference: string;
}
export interface AIStatus { default_mode: string; provider_configured: boolean; configured_provider: string; model_label: string | null; timeout_seconds: number; max_output_tokens: number; max_calls_per_hour: number; live_provider_verified: boolean; free_text_generation: boolean }
