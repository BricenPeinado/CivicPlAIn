import {render,screen,waitFor,fireEvent} from '@testing-library/react';
import {describe,it,expect,vi,beforeEach} from 'vitest';
import userEvent from '@testing-library/user-event';
import {DecisionContext} from './DecisionContext';
import {getDecisionSummary,explainDecision,type DecisionSummary} from '../../services/decisionSupport';
import {getMunicipalEstimate} from '../../services/municipalPlanning';
import {getPriority} from '../../services/prioritization';
import {getScreening} from '../../services/officialScreening';
import {snapshot,road} from '../../test-municipal';
import {parseRoute,routeHref,type Route} from '../../routing';
import type {MunicipalEstimate} from '../../types/municipalPlanning';
import type {PriorityRecord} from '../../types/prioritization';
import type {ScreeningRecord} from '../../types/officialScreening';
import type {AIExplanation} from '../../types/ai';
vi.mock('../../services/decisionSupport');vi.mock('../../services/municipalPlanning');vi.mock('../../services/prioritization');vi.mock('../../services/officialScreening');
const estimate='estimate-'+'a'.repeat(64),priority='priority-'+'b'.repeat(64),screening='screen-'+'c'.repeat(64);
const history:DecisionSummary['saved']['priority']={status:'available',count:0,records:[],truncated:false};
const summary:DecisionSummary={version:'decision-context-v1',snapshot_id:snapshot.id,as_of_date:'2026-11-01',release_id:null,policy_id:null,condition:{roads:10,eligible:0,requiring_review:10,categories:{good:0,fair:0,poor:0,unknown:10},reasons:{NO_ELIGIBLE_ASSESSMENT:10}},saved:{estimate:{...history,count:1,records:[{id:estimate,road_id:road.id,created_at:'2026-11-08'}]},priority:history,screening:history},meaning:'Separate assumptions, no actual work',utility_coverage:'unknown',human_review_required:true};
const estimateRecord={id:estimate,input_hash:'input',result_hash:'result',input_snapshot:{request:{snapshot_id:snapshot.id,road_id:road.id}},result:{method_version:'municipal-area-cost-v1',comparison_basis:'Independent declared scopes, no equal-benefit claim',warnings:['Human review required'],alternatives:[{treatment:'resurface',status:'available',scope:{description:'Technical QA scope',extent:'partial'},quantity_m2:'20',cases:{base:{total_usd:'20.10'}},duration:null,exclusions:['Traffic control'],unknowns:['Condition unknown'],price_basis_date:'2026-11-08',geography:'QA only'}]}} as unknown as MunicipalEstimate;
const route:Route={view:'dashboard',mode:'official',snapshot:snapshot.id,road:null};
beforeEach(()=>{vi.resetAllMocks();vi.mocked(getDecisionSummary).mockResolvedValue(summary);vi.mocked(getMunicipalEstimate).mockResolvedValue(estimateRecord);});
describe('official decision integration',()=>{
 it('shows unknown coverage and empty histories without triggering calculations or explanations',async()=>{
  render(<DecisionContext snapshot={snapshot} route={route} onRoute={vi.fn()}/>);
  expect(await screen.findByText(/0 \/ 10 road rows/)).toBeVisible();expect(screen.getByText(/Missing is never Good/)).toBeVisible();expect(screen.getAllByText(/No saved results/)).toHaveLength(2);expect(explainDecision).not.toHaveBeenCalled();expect(getMunicipalEstimate).not.toHaveBeenCalled();
 });
 it('retains exact saved context in all four views and resolves estimate road on selection',async()=>{
  const onRoute=vi.fn();const user=userEvent.setup();render(<DecisionContext snapshot={snapshot} route={route} onRoute={onRoute}/>);
  await user.selectOptions(await screen.findByLabelText(/Repair estimates ·/),estimate);expect(onRoute).toHaveBeenCalledWith({estimate,alternative:undefined,road:road.id});
  for(const view of ['map','dashboard','projects','scenarios'] as const){const pinned={...route,view,road:road.id,estimate,priority,screening,tool:'screening' as const,alternative:'later'};expect(parseRoute(routeHref(pinned))).toMatchObject(pinned);}
 });
 it('requires explicit explanation, keeps unavailable duration/sensitivity and exposes sources',async()=>{
  vi.mocked(explainDecision).mockResolvedValue({summary:'Validated result',provider_status:'fallback',fallback_reason:'not_configured',key_findings:[{finding_id:'f',claim_text:'Base assumption-based total: 20.10 USD.'}],missing_information:['Utilities unknown'],uncertainties:['No approval'],suggested_review_actions:['Verify assumptions'],citations:[],audit_reference:'audit'} as unknown as AIExplanation);
  const user=userEvent.setup();render(<DecisionContext snapshot={snapshot} route={{...route,road:road.id,estimate}} onRoute={vi.fn()}/>);
  expect(await screen.findByText(/Base USD 20.10/)).toBeVisible();expect(screen.getByText('Duration unavailable.')).toBeVisible();expect(screen.getByText(/Low USD Unavailable/)).toBeVisible();expect(explainDecision).not.toHaveBeenCalled();
  await user.click(screen.getByText('Explain this validated result'));await user.selectOptions(screen.getByLabelText('Explanation mode'),'ai');await user.click(screen.getByRole('button',{name:'Explain saved evidence'}));
  expect(await screen.findByText('Base assumption-based total: 20.10 USD.')).toBeVisible();expect(explainDecision).toHaveBeenCalledWith(snapshot.id,'estimate',estimate,'ai');expect(screen.getByText('Utilities unknown')).toBeVisible();expect(screen.getByText('Sources, assumptions, exclusions and frozen inputs')).toBeVisible();
 });
 it('fails closed for foreign pinned results and offers retry rather than replacing them',async()=>{
  vi.mocked(getMunicipalEstimate).mockRejectedValue(new Error('Foreign snapshot'));
  render(<DecisionContext snapshot={snapshot} route={{...route,road:road.id,estimate}} onRoute={vi.fn()}/>);expect(await screen.findByRole('alert')).toHaveTextContent('Foreign snapshot');expect(screen.queryByText(/Base USD/)).not.toBeInTheDocument();
 });
 it('keeps missing priority outside a saved universe explicit with keyboard road links',async()=>{
  vi.mocked(getPriority).mockResolvedValue({id:priority,input_snapshot:{request:{}},result_hash:'h',input_hash:'i',result:{method_version:'maintenance-priority-v1',as_of_date:'2026-11-08',base:{ranked:0,unranked:1,objective:'inspection_review',rows:[]},coverage:{scoped_road_rows:1,snapshot_road_rows:10},sensitivity:[],warnings:[]}} as unknown as PriorityRecord);
  render(<DecisionContext snapshot={snapshot} route={{...route,priority}} road={road.id} onRoute={vi.fn()}/>);expect(await screen.findByText(/outside this run’s explicit universe/)).toBeVisible();
 });
 it('never substitutes base findings for a missing pinned schedule alternative',async()=>{
  vi.mocked(getScreening).mockResolvedValue({id:screening,input_hash:'i',result_hash:'r',input_snapshot:{request:{}},result:{method_version:'official-screen-v1',base:{findings:[],indeterminate_pair_count:1,possible_pair_count:1},alternatives:[],warnings:[]}} as unknown as ScreeningRecord);
  render(<DecisionContext snapshot={snapshot} route={{...route,screening,alternative:'missing'}} onRoute={vi.fn()}/>);expect(await screen.findByRole('alert')).toHaveTextContent('No base result substituted');expect(screen.queryByText(/0 screening findings/)).not.toBeInTheDocument();
 });
 it('handles summary failure, retries and keeps the reference date stable',async()=>{
  vi.mocked(getDecisionSummary).mockRejectedValueOnce(new Error('Unavailable')).mockResolvedValue(summary);
  render(<DecisionContext snapshot={snapshot} route={route} onRoute={vi.fn()}/>);fireEvent.click(await screen.findByRole('button',{name:'Retry planning summary'}));await waitFor(()=>expect(screen.getByText(/0 \/ 10 road rows/)).toBeVisible());expect(getDecisionSummary).toHaveBeenLastCalledWith(snapshot.id,snapshot.published_at.slice(0,10),route,expect.any(AbortSignal));
 });
});
