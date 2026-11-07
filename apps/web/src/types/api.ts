import type { FeatureCollection, LineString, Feature } from 'geojson';
export const categories = ['good', 'fair', 'poor', 'unknown'] as const;
export type Category = typeof categories[number];
export interface RoadProperties {
  id: string; name: string | null; dataset_snapshot_id: string;
  evidence_ids: string[]; data_kind: 'synthetic'; synthetic_input: true;
  field_evidence: Record<string, string[]>; unknown_reasons: Record<string, string>;
  limitations: string[]; created_at: string; source_segment_key: string | null;
  study_area_id: string; length_m: string | null; width_m: string | null;
  lane_count: number | null; utility_coverage: 'unknown'; coverage_as_of: string | null;
  surface_material?: string; functional_class?: string; repairable_area_m2?: string | null;
  dimension_basis?: Record<string, string>; notes?: string | null;
  condition_summary: {
    category: Category; rating: string | null; rating_scale: string | null;
    assessed_on: string | null; evidence_ids: string[]; data_kind: 'synthetic'; synthetic_input: true;
  };
}
export type Road = RoadProperties & { geometry: LineString };
export interface Meta { request_id: string; dataset_snapshot_id: string | null; warnings: string[]; next_cursor: string | null; latest_usable_id?: string | null }
export type RoadsCollection = FeatureCollection<LineString, RoadProperties> & { meta: Meta };
export type RoadFeature = Feature<LineString, RoadProperties>;
export interface Envelope<T> { data: T; meta: Meta }
export interface Evidence {
  id: string; title: string; publisher: string; source_kind: 'demo_assumption';
  verification_status: 'synthetic_demo'; uri: string; retrieved_at: string | null;
  observed_on: string | null; version: string; checksum_sha256: string; original_crs: string;
  coverage_note: string; reliability_note: string; license_note: string; unknown_reasons: Record<string, string>;
}
export function summarize(features: RoadFeature[]) {
  const counts: Record<Category, number> = { good: 0, fair: 0, poor: 0, unknown: 0 };
  for (const feature of features) counts[feature.properties.condition_summary.category]++;
  return counts;
}

export type Assessment = RoadProperties['condition_summary'] & {
  id: string; road_segment_id: string; dataset_snapshot_id: string;
  assessment_method: string; notes: string;
}
export interface Suitability { status: 'candidate_requires_review' | 'not_indicated' | 'requires_review'; rule_id: string; rationale: string; human_review_required: true }
export interface RepairOption {
  id: string; treatment: string; label: string; description: string; scope_of_work: string;
  suitability_conditions: string; material_assumptions: string; work_activities: string[];
  quantity_unit: 'm2'; unit_rates_usd: { low: string; base: string; high: string };
  rate_inclusions: string; mobilization_usd: string; traffic_management_usd: string;
  contingency_fraction: string; productivity_per_day: string; productivity_unit: string;
  setup_days: number; curing_days: number; price_basis_date: string; sensitivity_basis: string;
  exclusions: string[]; limitations: string[]; evidence_ids: string[]; synthetic_input: true;
}
export interface CostScenario {
  line_items: { label: string; quantity: string; unit: string; unit_rate_usd: string; amount_usd: string; evidence_ids: string[] }[];
  subtotal_usd: string; contingency_fraction: string; contingency_usd: string; total_usd: string;
}
export interface Calculation {
  road_segment_id: string; repair_option_id: string; repair_category: string; currency: 'USD';
  quantity: string; quantity_unit: 'm2';
  dimension_provenance: Record<string, { value: string; unit: string; basis: string; evidence_ids: string[]; note: string }>;
  scenarios: Record<'low' | 'base' | 'high', CostScenario>;
  duration: { active_workdays: number; setup_days: number; curing_days: number; total_preliminary_days: number; productivity_per_day: string; productivity_unit: string; basis: string };
  suitability: Suitability; assumptions: string[]; warnings: string[]; evidence_ids: string[];
  method_version: string; data_kind: 'derived'; synthetic_input: true;
}
export interface Estimate extends Calculation {
  id: string; created_at: string; dataset_snapshot_id: string; input_hash: string; result_hash: string; input_snapshot: Record<string, unknown>;
}
export interface OptionComparison { option: RepairOption; suitability: Suitability; preview: Calculation | null; unavailable_reason: string | null }
export interface EstimateRequest {
  road_segment_id: string; repair_option_id: string; dataset_snapshot_id: string;
  planning_assumptions?: { length_m?: string; width_m?: string; unit: 'm'; note: string };
}
