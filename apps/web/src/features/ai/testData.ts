// Authored evidence transport examples for offline tests only.
import type { AIExplanation } from '../../types/ai';
export const meta = { request_id:'test',dataset_snapshot_id:'demo-m1-v1',warnings:[],next_cursor:null };
const source = { evidence_id:'ev-test',entity_type:'estimate' as const,record_id:'saved-estimate',record_hash:'record-sha',input_hash:'input-sha',calculation_version:'repair-estimate-v1',dataset_snapshot_id:'demo-m1-v1',source_revisions:{'fixture':'fixture-sha'},synthetic_input:true,data_kind:'derived' };
export const answer: AIExplanation = {
  explanation_id:'answer',task_type:'explain_estimate',evidence_snapshot_hash:'evidence-sha',summary:'Explanation from supplied records.',
  key_findings:[{ finding_id:'fact-cost',claim_text:'Base sensitivity total: 53400.00 USD.',supporting_evidence_ids:['ev-test'],fact_refs:['fact-cost'],classification:'deterministic_calculation' },{ finding_id:'fact-method',claim_text:'Repair method: resurface.',supporting_evidence_ids:['ev-test'],fact_refs:['fact-method'],classification:'verified_record_fact' }],
  tradeoffs:['Preliminary days do not establish calendar dates.'],uncertainties:['Human review required.'],missing_information:['Utility coverage is unknown.'],suggested_review_actions:['Verify scope and condition.'],citations:[source],evidence:{records:[source],facts:[{fact_id:'fact-cost',evidence_id:'ev-test',field:'scenarios.base.total_usd',label:'Base total',value:'53400.00',unit:'USD',classification:'deterministic_calculation'}],truncated:false,omitted_fact_count:0,limitations:['Human review required.']},
  provider_status:'fallback',validation_status:'fallback_validated',fallback_reason:'not_configured',model_label:null,generated_at:'2026-11-07T12:00:00Z',source_classification:'synthetic',human_review_required:true,warnings:['Human review required.'],audit_reference:'audit-1',
};
