import { readFileSync } from 'node:fs';
import { beforeEach, expect, it, vi } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ScenarioPlanner } from './ScenarioPlanner';
import { ScenarioResults, ScenarioComparisonView } from './ScenarioResults';
import * as api from '../../services/api';
import type { RepairOption, RoadsCollection } from '../../types/api';
import type { Scenario, ScenarioEvaluation, ScenarioDraft, ScenarioComparison } from '../../types/scenarios';
vi.mock('../../services/api',()=>({ getScenarios:vi.fn(), getRepairCatalog:vi.fn(),getScenarioEvaluations:vi.fn(),getScenarioEvaluation:vi.fn(),createScenario:vi.fn(),updateScenario:vi.fn(),evaluateScenario:vi.fn(),compareScenarios:vi.fn() }));
import { scenario, evaluation, roads, catalog, meta } from './testData';
beforeEach(()=>{
  vi.mocked(api.getScenarios).mockResolvedValue({data:[],meta});
  vi.mocked(api.getRepairCatalog).mockResolvedValue({data:catalog,meta});
  vi.mocked(api.getScenarioEvaluations).mockResolvedValue({data:[],meta});
  vi.mocked(api.createScenario).mockResolvedValue({data:scenario(),meta});
  vi.mocked(api.updateScenario).mockResolvedValue({data:{...scenario(),revision:2},meta});
  vi.mocked(api.evaluateScenario).mockResolvedValue({data:evaluation(),meta});
});
const show=()=>render(<ScenarioPlanner roads={roads} selectedRoad="demo-r-001" projects={[]}/>);
async function newPlan(user:ReturnType<typeof userEvent.setup>) {
  await user.click(await screen.findByRole('button',{name:'Create scenario'}));
  await user.type(screen.getByLabelText('Name'),'Hypothetical road plan');
  await user.type(screen.getByLabelText('Planning start'),'2027-04-01');
  await user.type(screen.getByLabelText('Planning end (exclusive)'),'2027-05-01');
  await user.type(screen.getByLabelText('Explicit synthetic planning assumptions'),'Authored demo budget and work assumptions; validate before implementation.');
}
it('shows loading, empty state, and API failure with retry',async()=>{
  vi.mocked(api.getScenarios).mockRejectedValueOnce(new Error('Backend unavailable'));
  const user=userEvent.setup();show();expect(screen.getByRole('status')).toHaveTextContent('Loading scenarios');
  expect(await screen.findByRole('alert')).toHaveTextContent('Backend unavailable');
  await user.click(screen.getByRole('button',{name:'Retry loading scenarios'}));
  expect(await screen.findByText(/No saved scenarios/)).toBeInTheDocument();
});
it('creates a plan from selected map road and displays a saved evaluation',async()=>{
  const user=userEvent.setup();show();await newPlan(user);
  await user.click(screen.getByRole('button',{name:/Add selected map road/}));
  await user.selectOptions(screen.getByLabelText('Repair method, action 1'),'demo-resurface');
  await user.click(screen.getByRole('button',{name:'Save and evaluate'}));
  expect(await screen.findByRole('region',{name:'Scenario evaluation'})).toHaveTextContent('$53,400.00');
  const body=vi.mocked(api.createScenario).mock.calls[0][0];
  expect(body.actions[0].road_segment_id).toBe('demo-r-001');
  expect(body.actions[0].quantity.derivation).toBe('road_dimensions');
  expect(body.actions[0].schedule).toBeNull();
  expect(body.actions[0].unknown_reasons['scope.geometry']).toBeTruthy();
  expect(body.actions[0].input_provenance.quantity.evidence_ids).toEqual(['assumption:editor']);
  expect(api.evaluateScenario).toHaveBeenCalledWith('scenario-0',1,expect.any(AbortSignal));
});
it('requires explicit assumptions and validates partial areas before requests',async()=>{
  const user=userEvent.setup();show();await newPlan(user);
  await user.clear(screen.getByLabelText('Explicit synthetic planning assumptions'));
  await user.click(screen.getByRole('button',{name:'Save draft'}));
  expect(await screen.findByRole('alert')).toHaveTextContent('explicit assumption note');
  await user.type(screen.getByLabelText('Explicit synthetic planning assumptions'),'Explicit area for review');
  await user.click(screen.getByRole('button',{name:/Add selected map road/}));
  await user.selectOptions(screen.getByLabelText('Repair scope, action 1'),'partial_area');
  expect(screen.getByLabelText('Quantity derivation, action 1')).toHaveValue('unknown');
  await user.selectOptions(screen.getByLabelText('Quantity derivation, action 1'),'explicit_area');
  await user.type(screen.getByLabelText('Repair area (m²), action 1'),'-1');
  await user.click(screen.getByRole('button',{name:'Save draft'}));
  expect(await screen.findByRole('alert')).toHaveTextContent('positive partial repair area');
  expect(api.createScenario).not.toHaveBeenCalled();
});
it('can add, edit and remove multiple actions and preserves unknown method',async()=>{
  const user=userEvent.setup();show();await newPlan(user);
  await user.selectOptions(screen.getByLabelText('Add a road'),'demo-r-002');
  await user.selectOptions(screen.getByLabelText('Add a road'),'demo-r-003');
  await user.click(screen.getByRole('button',{name:'Remove action 1'}));
  expect(screen.getByText('Action 1 · demo-r-003')).toBeInTheDocument();
  await user.click(screen.getByRole('button',{name:'Save draft'}));
  await screen.findByRole('button',{name:/Edit A/});
  expect(vi.mocked(api.createScenario).mock.calls[0][0].actions[0].repair_option_id).toBeNull();
});
it('edits with revision protection and retains saved evaluation history',async()=>{
  vi.mocked(api.getScenarios).mockResolvedValue({data:[scenario()],meta});
  vi.mocked(api.getScenarioEvaluations).mockResolvedValue({data:[evaluation()],meta});
  const user=userEvent.setup();show();await user.click(await screen.findByRole('button',{name:/Edit A/}));
  expect(await screen.findByLabelText('Saved evaluation history')).toHaveValue('evaluation-0');
  await user.clear(screen.getByLabelText('Name'));await user.type(screen.getByLabelText('Name'),'Revised plan');
  await user.click(screen.getByRole('button',{name:'Save draft'}));
  expect(api.updateScenario).toHaveBeenCalledWith('scenario-0',1,expect.objectContaining({name:'Revised plan'}),expect.any(AbortSignal));
  await user.click(screen.getByRole('button',{name:'Review saved evaluation'}));
  expect(screen.getByRole('region',{name:'Scenario evaluation'})).toHaveTextContent('REVISION 1');
});
it('surfaces backend validation and stale revision failures',async()=>{
  vi.mocked(api.createScenario).mockRejectedValueOnce(new Error('HTTP 409: Scenario changed; reload'));
  const user=userEvent.setup();show();await newPlan(user);await user.click(screen.getByRole('button',{name:'Save draft'}));
  expect(await screen.findByRole('alert')).toHaveTextContent('Scenario changed');
  expect(api.evaluateScenario).not.toHaveBeenCalled();
});
it('compares two saved evaluation snapshots with transparent tradeoffs',async()=>{
  vi.mocked(api.getScenarios).mockResolvedValue({data:[scenario(),scenario(1)],meta});
  vi.mocked(api.getScenarioEvaluations).mockImplementation(async id=>({data:[evaluation(id==='scenario-0'?0:1)],meta}));
  const c:ScenarioComparison={id:'comparison',evaluation_ids:['evaluation-0','evaluation-1'],common_basis:{currency:'USD'},rows:[],deltas:[],dominance:[],tradeoffs:['No dominance established. Review tradeoffs.'],warnings:['Human review required'],input_hash:'c',method_version:'comparison'};
  vi.mocked(api.compareScenarios).mockResolvedValue({data:c,meta});
  const user=userEvent.setup();show();await user.click(await screen.findByRole('button',{name:/Load evaluations for A/})); await user.click(screen.getByRole('button',{name:/Load evaluations for B/})); await user.click(await screen.findByLabelText(/Compare A/));await user.click(screen.getByLabelText(/Compare B/));await user.click(screen.getByRole('button',{name:'Compare selected (2/3)'}));
  expect(await screen.findByRole('region',{name:'Scenario comparison'})).toHaveTextContent('No dominance established');
  expect(api.compareScenarios).toHaveBeenCalledWith(['evaluation-0','evaluation-1'],expect.any(AbortSignal));
});
it('renders unknown totals separately from known subtotals and sensitivity budget failure',()=>{
  const e={...evaluation(),cost_total_usd:null,budget_headroom_usd:null,budget_status:'indeterminate',upper_bound_within_budget:null};
  render(<ScenarioResults evaluation={e}/>);
  const result=screen.getByRole('region',{name:'Scenario evaluation'});
  expect(within(result).getByText(/Complete total unavailable/)).toHaveTextContent('$53,400.00');
  expect(result).toHaveTextContent('indeterminate');expect(result).toHaveTextContent('High sensitivity within budget: Unknown');
  expect(result).toHaveTextContent('Unknown utility coverage');
});
it('renders comparison columns including unknown cost, conflict types and assumptions',()=>{
  const e=evaluation();
  const row={evaluation_id:e.id,scenario_id:e.scenario_id,name:'Plan A',revision:1,cost_total_usd:null,known_subtotal_usd:e.known_subtotal_usd,budget_usd:e.budget_usd,budget_headroom_usd:null,budget_status:'indeterminate',upper_bound_within_budget:null,preliminary_days_sum:null,elapsed_days:null,scheduled_completion:null,lane_closure_days:null,scheduled_road_workdays:null,conflict_count:1,conflict_types:{reopening_risk:1},incomplete_checks:2,affected_road_ids:e.affected_road_ids,priced_actions:0,total_actions:1,assumptions:e.input_snapshot.scenario.assumptions,action_lifespan_years:e.action_lifespan_years};
  render(<ScenarioComparisonView comparison={{id:'c',evaluation_ids:[e.id],common_basis:{},rows:[row],deltas:[],dominance:[],tradeoffs:['Cost unavailable'],warnings:['SYNTHETIC'],input_hash:'c',method_version:'comparison'}}/>);
  expect(screen.getByRole('table')).toHaveTextContent('0 / 1 actions priced');expect(screen.getByRole('table')).toHaveTextContent('reopening risk: 1');
});
it('loads history on deliberate action and protects an unsaved editor from replacement',async()=>{
  vi.mocked(api.getScenarios).mockResolvedValue({data:[scenario(),scenario(1)],meta});
  const user=userEvent.setup();show();await newPlan(user);expect(api.getScenarioEvaluations).not.toHaveBeenCalled();
  await user.click(screen.getByRole('button',{name:'Create scenario'})); expect(screen.getByRole('alert')).toHaveTextContent('Keep your unsaved scenario?');
  await user.click(screen.getByRole('button',{name:'Keep editing'})); expect(screen.getByLabelText('Name')).toHaveValue('Hypothetical road plan');
  await user.click(screen.getByRole('button',{name:'Create scenario'})); await user.click(screen.getByRole('button',{name:'Discard editor changes and continue'})); expect(screen.getByLabelText('Name')).toHaveValue(''); expect(api.createScenario).not.toHaveBeenCalled();
});
it('loads an explicit saved evaluation link without evaluating or changing the draft',async()=>{
  vi.mocked(api.getScenarios).mockResolvedValue({data:[scenario()],meta}); vi.mocked(api.getScenarioEvaluations).mockResolvedValue({data:[evaluation()],meta}); vi.mocked(api.getScenarioEvaluation).mockResolvedValue({data:evaluation(),meta});
  render(<ScenarioPlanner roads={roads} selectedRoad={null} projects={[]} scenarioId="scenario-0" evaluationId="evaluation-0"/>);
  expect(await screen.findByRole('region',{name:'Scenario evaluation'})).toHaveTextContent('$53,400.00'); expect(api.evaluateScenario).not.toHaveBeenCalled(); expect(api.updateScenario).not.toHaveBeenCalled();
});
it('rejects a saved evaluation for a different scenario while retaining the editor',async()=>{
  vi.mocked(api.getScenarios).mockResolvedValue({data:[scenario()],meta});vi.mocked(api.getScenarioEvaluations).mockResolvedValue({data:[],meta});vi.mocked(api.getScenarioEvaluation).mockResolvedValue({data:evaluation(1),meta});
  render(<ScenarioPlanner roads={roads} selectedRoad={null} projects={[]} scenarioId="scenario-0" evaluationId="evaluation-1"/>);
  expect(await screen.findByRole('alert')).toHaveTextContent('Linked evaluation differs from the scenario/source context.');expect(screen.queryByRole('region',{name:'Scenario evaluation'})).not.toBeInTheDocument();expect(screen.getByLabelText('Name')).toHaveValue(scenario().name);expect(api.evaluateScenario).not.toHaveBeenCalled();
});
it('pages older immutable evaluations on demand without replacing the draft',async()=>{
  vi.mocked(api.getScenarios).mockResolvedValue({data:[scenario()],meta}); vi.mocked(api.getScenarioEvaluations).mockResolvedValueOnce({data:[evaluation()],meta:{...meta,next_cursor:'30'}}).mockResolvedValueOnce({data:[{...evaluation(),id:'older',scenario_revision:0}],meta});
  const user=userEvent.setup();show();await user.click(await screen.findByRole('button',{name:/Edit A/})); await user.click(await screen.findByRole('button',{name:'Load older evaluations'}));
  expect(await screen.findByRole('option',{name:/Revision 0/})).toBeInTheDocument(); expect(api.getScenarioEvaluations).toHaveBeenLastCalledWith('scenario-0',expect.any(AbortSignal),30); expect(screen.getByLabelText('Name')).toHaveValue(scenario().name);
});
it('defers a different saved-plan link until the unsaved editor is explicitly replaced',async()=>{
  vi.mocked(api.getScenarios).mockResolvedValue({data:[scenario(),scenario(1)],meta});
  vi.mocked(api.getScenarioEvaluations).mockResolvedValue({data:[],meta});
  vi.mocked(api.getScenarioEvaluation).mockResolvedValue({data:evaluation(1),meta});
  const user=userEvent.setup();const props={roads,selectedRoad:null,projects:[]};const view=render(<ScenarioPlanner {...props} scenarioId="scenario-0"/>);
  await user.type(await screen.findByLabelText('Name'),' unsaved');
  view.rerender(<ScenarioPlanner {...props} scenarioId="scenario-1" evaluationId="evaluation-1"/>);
  expect(await screen.findByRole('alert')).toHaveTextContent('Keep your unsaved scenario?');expect(api.getScenarioEvaluation).not.toHaveBeenCalled();
  expect(screen.getByLabelText('Name')).toHaveValue(scenario().name+' unsaved');
  await user.click(screen.getByRole('button',{name:'Discard editor changes and continue'}));
  expect(await screen.findByRole('region',{name:'Scenario evaluation'})).toHaveTextContent('REVISION 1');expect(api.getScenarioEvaluation).toHaveBeenCalledWith('evaluation-1',expect.any(AbortSignal));expect(api.updateScenario).not.toHaveBeenCalled();
});
