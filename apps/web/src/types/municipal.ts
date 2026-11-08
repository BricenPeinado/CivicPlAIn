import type { Geometry, FeatureCollection } from 'geojson';

export type Bbox = [number, number, number, number];
export type Classification = 'official_observation' | 'imported_administrative_record' | 'derived_calculation' | 'planning_assumption' | 'synthetic_fixture' | 'unknown';
export interface Coverage { study_area_id: string; bbox: Bbox; context_bbox: Bbox; utility_coverage: 'unknown'; source_status: Record<string, string>; permit_selection: { issued_on_or_after: string; completeness: string; membership: string; method: string }; selection: string }
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
}
export interface SourceRevision { id: string; source_id: string; source_url: string; endpoint: string; retrieved_at: string; source_updated_at: number | Record<string, number> | null; release_note: string; source_crs: string; attribution: string; cadence: string; raw_sha256: string; dictionary_url: string; dictionary_sha256: string; terms_urls: string[]; license: { identifier: string | null; note: string; application_disclaimer_required?: boolean; application_disclaimer_url?: string } }
export type MunicipalGeoJSON = FeatureCollection<Geometry, { id: string; kind: string; source_revision_id: string; source_record_key: string; classification: Classification; values: Record<string, string | null>; field_classifications: Record<string, Classification> }> & { meta: MunicipalMeta };
export interface Dashboard { counts: { roads: number; condition: Record<string, number>; assessments: { total: number; dated: number; accepted: number; ambiguous: number; unmatched: number }; permits: { total: number; confirmed_in_scope: number; scope_candidates: number; matched: number; ambiguous: number; unmatched: number; unlocated: number } }; observation_date_range: [string, string] | null; latest_retrieved_at: string; coverage: Coverage }
export interface Workspace { mode: 'official' | 'synthetic'; snapshot_id: string | null }
