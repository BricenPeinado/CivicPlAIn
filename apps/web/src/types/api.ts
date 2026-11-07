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
  condition_summary: {
    category: Category; rating: string | null; rating_scale: string | null;
    assessed_on: string | null; evidence_ids: string[]; data_kind: 'synthetic'; synthetic_input: true;
  };
}
export type Road = RoadProperties & { geometry: LineString };
export interface Meta { request_id: string; dataset_snapshot_id: string | null; warnings: string[]; next_cursor: string | null }
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
