// Authored synthetic calculation transport examples for offline tests only.
import { readFileSync } from 'node:fs';
import type { RepairOption, RoadsCollection } from '../../types/api';
import type { Scenario, ScenarioEvaluation, ScenarioDraft } from '../../types/scenarios';
const fixtures=JSON.parse(readFileSync('../../data/demo/scenarios.json','utf8'));
export const catalog=JSON.parse(readFileSync('../../data/demo/maintenance.json','utf8')).repair_options as RepairOption[];
export const roads=JSON.parse(readFileSync('../../data/demo/roads.geojson','utf8')) as RoadsCollection;
roads.meta={request_id:'test',dataset_snapshot_id:'demo-m1-v1',warnings:[],next_cursor:null};
export const meta=roads.meta;
export function scenario(index=0):Scenario {
  const d={...fixtures[index].draft,contract_version:'scenario-v1',currency:'USD',cost_scope:'roadwork_only',mobilization_groups:[],planning_objective:'Compare alternatives',status:'draft'} as ScenarioDraft;
  return {...d,actions:d.actions.map(a=>({...a,constraints:{must_follow_action_ids:[],human_review_required:true}})),id:`scenario-${index}`,revision:1,revision_hash:'revision',created_at:'2026-11-07T12:00:00Z',updated_at:'2026-11-07T12:00:00Z',method_version:'scenario-v1',data_kind:'derived',synthetic_input:true,hypothetical:true};
}
export function evaluation(index=0):ScenarioEvaluation {
  const s=scenario(index);
  return {id:`evaluation-${index}`,scenario_id:s.id,scenario_revision:1,scenario_revision_hash:'revision',evaluated_at:s.created_at,baseline_source_hash:'baseline',input_snapshot:{scenario:s,context:{sources:[]}},input_hash:'input',result_hash:'result',method_version:'scenario-evaluation-v1',analysis_versions:{cost:'scenario-cost-v1'},action_costs:[],known_subtotal_usd:{low:'44760.00',base:'53400.00',high:'66360.00'},cost_total_usd:{low:'44760.00',base:'53400.00',high:'66360.00'},budget_usd:'60000.00',budget_headroom_usd:{low:'15240.00',base:'6600.00',high:'-6360.00'},budget_status:'within_budget',upper_bound_within_budget:false,preliminary_days_sum:5,elapsed_days:7,scheduled_road_workdays:7,lane_closure_days:7,overlapping_closure_pairs:0,affected_road_ids:['demo-r-001'],action_lifespan_years:{'road-repair':null},conflict_screen:{analysis:null,finding_contexts:{},adapter_version:'adapter',not_run_reason:'Scope not run',project_origins:{},original_projects:[],overrides:[],assumption_sources:[],input_hash:'ci',result_hash:'cr'},indeterminate_checks:['Unknown utility coverage'],warnings:['SYNTHETIC HYPOTHETICAL planning estimate; human review required.'],utility_coverage:'unknown',review_required:true,hypothetical:true,synthetic_input:true};
}
