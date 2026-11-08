import type { Geometry, FeatureCollection } from 'geojson';

export type Bbox = [number, number, number, number];
export type Classification = 'official_observation' | 'imported_administrative_record' | 'derived_calculation' | 'planning_assumption' | 'synthetic_fixture' | 'unknown';
export interface Coverage { study_area_id: string; bbox: Bbox; context_bbox: Bbox; utility_coverage: 'unknown'; source_status: Record<string, string>; permit_selection: { issued_on_or_after: string | null; administrative_window?: {start:string;end:string}; completeness: string; membership: string; method: string }; selection: string }
export interface Capabilities { [key: string]: { available: boolean; reason: string | null } }
export interface Snapshot { id: string; contract_version: 'municipal-record-v2'; mode: 'official'; coverage: Coverage; capabilities: Capabilities; source_revision_ids: string[]; published_at: string; warnings: string[] }
export interface MunicipalMeta { contract_version: 'municipal-record-v2'; snapshot_id: string | null; mode: 'official'; next_cursor: string | null; total_matching: number | null; returned_count: number; coverage: Coverage | null; warnings: string[]; latest_usable_id?: string | null; conflicting_latest_ratings?: boolean }
export interface MunicipalEnvelope<T> { data: T; meta: MunicipalMeta }
export interface GeographicMatch { status: 'matched' | 'ambiguous' | 'unmatched'; target_road_id: string | null; candidates: { road_id: string; distance_m: number | null; street_code_agrees: boolean }[]; reason: string; method: string; confidence: string }
export interface MunicipalRecord {
  contract_version: 'municipal-record-v2'; id: string; kind: 'road' | 'condition' | 'permit' | 'context'; source_revision_id: string;
  source_record_key: string; classification: Classification; geometry: Geometry | null; bbox: Bbox | null;
  raw_identifiers: Record<string, string | null>; values: Record<string, string | null>;
  field_classifications: Record<string, Classification>; field_provenance: Record<string, { source_field: string | null; original_value?: unknown; original_unit?: string | null }>;
  unknown_reasons: Record<string, string>; limitations: string[]; contains_synthetic: boolean; contains_assumptions: boolean;
  lineage: Record<string, unknown>; match?: GeographicMatch | null; location_basis?: 'source_geometry' | 'matched_road_reference' | 'unknown';
  scope_membership?: string; same_oft_records?: { id: string; kind: string }[];
  permit_location?: PermitLocationEvidence;
  condition_summary?: ConditionSummary | {category: 'unknown'};
}
export interface SourceRevision { id: string; source_id: string; source_url: string; endpoint: string; retrieved_at: string; source_updated_at: number | Record<string, number> | null; release_note: string; source_crs: string; attribution: string; cadence: string; raw_sha256: string; dictionary_url: string; dictionary_sha256: string; terms_urls: string[]; license: { identifier: string | null; note: string; application_disclaimer_required?: boolean; application_disclaimer_url?: string } }
export type MunicipalGeoJSON = FeatureCollection<Geometry, { id: string; kind: string; source_revision_id: string; source_record_key: string; classification: Classification; values: Record<string, string | null>; field_classifications: Record<string, Classification> }> & { meta: MunicipalMeta };
export interface Dashboard { permit_status_counts?: { status: string | null; count: number }[]; permit_issue_date_range?: [string, string] | null; source_freshness?: Pick<SourceRevision, 'id' | 'source_id' | 'retrieved_at' | 'source_updated_at' | 'cadence' | 'release_note'>[]; dated_road_coverage?: { value: number; denominator: number }; method_version?: string; counts: { roads: number; condition: Record<string, number>; assessments: { total: number; dated: number; accepted: number; ambiguous: number; unmatched: number }; permits: { total: number; confirmed_in_scope: number; scope_candidates: number; matched: number; ambiguous: number; unmatched: number; unlocated: number } }; observation_date_range: [string, string] | null; latest_retrieved_at: string; coverage: Coverage }
export interface Workspace { mode: 'official' | 'synthetic'; snapshot_id: string | null }

export interface ConditionSummary {
 intelligence_release_id: string | null; method_version: 'road-condition-v1' | 'road-condition-v2-pilot'; snapshot_id: string; road_id: string; category: 'good' | 'fair' | 'poor' | 'unknown';
 rounded_rating?: number | null; policy?: {id: string; name: string; hash: string; classification: string; official_nyc_dot_policy: boolean} | null;
 category_reason: string; rating: string | null; inspection_at: string | null; source_revision_id: string | null;
 latest_usable_id: string | null; as_of_date: string; age_days: number | null; stale: boolean | null;
 reason: string | null; result_hash: string; history: {non_rating_reason?: string | null; multipass?: string | null; id: string; eligible: boolean; reason: string | null; rating: string | null; inspection_at: string | null; direction: string | null; road_type: string | null; source_revision_id: string; record_hash: string; association_id: string; association_hash: string; grading?: {rounded_rating: number | null; category: string; reason: string | null; policy_id: string} | null; association_review?: {reviewer: string; reason: string; scope: string; scope_reason: string; candidate_set_hash?: string; evidence_refs: string[]} | null}[];
}

export interface IntelligenceRelease { id: string; base_snapshot_id: string; contract_version: 'road-intelligence-v1'; contains_synthetic: boolean; counts: { observations: number; accepted_observations: number; accepted_road_rows: number; unresolved_observations: number }; warnings: string[] }

export type PermitEvidenceStatus = 'located' | 'candidate' | 'unlocated' | 'outside_coverage' | 'invalid_evidence';
export interface PermitLocationEvidence {classification:'derived_calculation';
 method_version: 'permit-road-reference-v1'; snapshot_id: string; permit_release_id: string | null;
 status: PermitEvidenceStatus; accepted_road_ids: string[]; accepted_associations: {id:string; decision:{reviewer:string;reason:string;scope:string};candidate_hash:string}[];
 rejected_associations?: {id:string;target_road_id:string;decision:{reviewer:string;reason:string;scope:string}}[];
 candidates: {road_id:string;distance_m:number|null;street_code_agrees:boolean;on_street_name_agrees:boolean;from_endpoint_road_ids:string[];to_endpoint_road_ids:string[]}[];
 candidate_set_hash:string; reasons:string[]; actual_schedule:'unknown'; location_meaning:string; parameter_hash:string;result_hash:string;
}
export interface PermitCoverage {utility_coverage:'unknown';method_version:'permit-road-reference-v1';snapshot_id:string;permit_release_id:string|null;total_permits:number;status_counts:Record<PermitEvidenceStatus,number>;accepted_road_rows:number;precision:string;limitations:string[];source_selection:Record<string,unknown>;result_hash:string}
export interface PermitRelease {id:string;base_snapshot_id:string;contract_version:'permit-intelligence-v1';contains_synthetic:boolean;counts:{observations:number;accepted_observations:number;accepted_road_rows:number};warnings:string[]}
export interface CoordinationCandidate {id:string;related_permit_id:string;permit_ids:string[];snapshot_id:string;permit_release_id:string|null;label:string;spatial_basis:string;administrative_window_relation:string;actual_work_overlap:'unknown';confirmed_conflict:false;same_application:boolean;shared_road_ids:string[];record_hashes:string[];location_hashes:string[];parameter_hash:string}
