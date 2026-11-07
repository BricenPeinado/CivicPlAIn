import type { LineString, Polygon } from 'geojson';
import type { Calculation, CostScenario, ConflictAnalysis, Evidence, Suitability } from './api';
export interface Provenance { basis: 'source_record' | 'planning_assumption' | 'derived'; evidence_ids: string[]; record_id?: string | null; record_field?: string | null; note?: string | null; method_version?: string | null }
export interface Assumption { id: string; note: string; field_paths: string[] }
export interface ScenarioAction {
  data_kind?: 'derived'; synthetic_input?: true; hypothetical?: true; contract_version?: 'scenario-action-v1'; id: string; road_segment_id: string;
  action_kind: 'repair' | 'temporary_patch' | 'repeat_restoration'; repair_category: string; repair_option_id: string | null;
  scope: { extent: 'whole_segment' | 'partial_area' | 'utility_trench' | 'unknown'; description: string; geometry: LineString | Polygon | null; location_status: 'approximate' | 'unknown' };
  quantity: { value: string | null; unit: 'm2'; derivation: 'road_dimensions' | 'explicit_area' | 'explicit_rectangle' | 'unknown'; length_m: string | null; width_m: string | null };
  input_provenance: Record<string, Provenance>; unknown_reasons: Record<string, string>; related_project_ids: string[];
  schedule: { contract_version?: 'schedule-proposal-v1'; start_date: string | null; end_date: string | null; basis?: 'supplied_calendar_interval'; assumption_evidence_ids: string[]; note: string;
    work_calendar?: { id: string; version: string; timezone: string; working_weekdays: number[]; excluded_dates: string[]; evidence_ids: string[]; note: string } | null;
    closure_intervals: { start_date: string; end_date: string; lanes_closed: number; evidence_ids: string[]; note: string }[] | null } | null;
  constraints: { earliest_start?: string | null; latest_end?: string | null; must_follow_action_ids: string[]; human_review_required: true };
}
export interface ScenarioDraft {
  contract_version: 'scenario-v1'; name: string; description: string; planning_objective: string;
  dataset_snapshot_id: string; budget_usd: string; currency: 'USD'; planning_start: string; planning_end: string;
  cost_scope: 'roadwork_only'; cost_scope_note?: string | null; review_note?: string | null; status: 'draft' | 'ready' | 'archived';
  actions: ScenarioAction[]; assumptions: Assumption[]; external_project_ids: string[];
  project_overrides: { project_id: string; operation: 'exclude' | 'replace'; replacement_action_ids: string[]; reason: string; evidence_ids: string[] }[];
  mobilization_groups: unknown[];
}
export interface Scenario extends ScenarioDraft { id: string; revision: number; revision_hash: string; created_at: string; updated_at: string; method_version: string; data_kind: 'derived'; synthetic_input: true; hypothetical: true }
export interface ActionCost { action_id: string; quantity_m2: string | null; quantity_provenance: Record<string, unknown>; unavailable_reason: string | null; costs: Record<string, CostScenario> | null; duration: Calculation['duration'] | null; suitability: Suitability | null; warnings: string[]; input_snapshot: Record<string, unknown>; input_hash: string; method_version: string }
export interface ScenarioEvaluation {
  id: string; scenario_id: string; scenario_revision: number; scenario_revision_hash: string; evaluated_at: string; baseline_source_hash: string;
  input_snapshot: { scenario: Scenario; context: { sources: Evidence[] }; [key: string]: unknown }; input_hash: string; result_hash: string; method_version: string; analysis_versions: Record<string,string>;
  action_costs: ActionCost[]; known_subtotal_usd: Record<string,string>; cost_total_usd: Record<string,string> | null;
  budget_usd: string; budget_headroom_usd: Record<string,string> | null; budget_status: string; upper_bound_within_budget: boolean | null;
  preliminary_days_sum: number | null; elapsed_days: number | null; scheduled_road_workdays: number | null; lane_closure_days: number | null; overlapping_closure_pairs: number | null;
  affected_road_ids: string[]; action_lifespan_years: Record<string,null>; indeterminate_checks: string[]; warnings: string[];
  conflict_screen: { analysis: ConflictAnalysis | null; finding_contexts: Record<string,string>; adapter_version: string; not_run_reason: string | null; project_origins: Record<string,unknown>; original_projects: unknown[]; overrides: unknown[]; assumption_sources: Evidence[]; input_hash: string; result_hash: string };
  utility_coverage: 'unknown'; review_required: true; hypothetical: true; synthetic_input: true;
}
export interface ComparisonRow {
  evaluation_id: string; scenario_id: string; name: string; revision: number; cost_total_usd: Record<string,string> | null; known_subtotal_usd: Record<string,string>;
  budget_usd: string; budget_headroom_usd: Record<string,string> | null; budget_status: string; upper_bound_within_budget: boolean | null;
  preliminary_days_sum: number | null; elapsed_days: number | null; scheduled_completion: string | null; lane_closure_days: number | null; scheduled_road_workdays: number | null;
  conflict_count: number | null; conflict_types: Record<string,number>; incomplete_checks: number; affected_road_ids: string[];
  priced_actions: number; total_actions: number; assumptions: Assumption[]; action_lifespan_years: Record<string,null>;
}
export interface ScenarioComparison { id: string; evaluation_ids: string[]; common_basis: Record<string,unknown>; rows: ComparisonRow[]; deltas: unknown[]; dominance: { dominant_evaluation_id: string; dominated_evaluation_id: string; objectives: string[]; limitation: string }[]; tradeoffs: string[]; warnings: string[]; input_hash: string; method_version: string }
