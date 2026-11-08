vi.mock('./features/standardized/StreetEvidence',()=>({StreetEvidence:()=>null}));
vi.mock('./features/decisions/DecisionContext',()=>({DecisionContext:()=>null}));
import { act, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, expect, it, vi } from 'vitest';
import { readFileSync } from 'node:fs';
import App from './App';
import * as api from './services/api';
import * as municipal from './services/municipal';
import { roads, catalog, scenario, evaluation, meta } from './features/scenarios/testData';
import { projects, analysis } from './features/conflicts/testData';
import { answer } from './features/ai/testData';
import { snapshot, road, permit, condition, conditionSummary, meta as officialMeta } from './test-municipal';
import type { Dashboard } from './types/municipal';
vi.mock('./services/api'); vi.mock('./services/municipal');
vi.mock('./features/map/RoadMap', () => ({ RoadMap: (props: any) => <section aria-label="Test map"><button onClick={() => props.onSelect(props.official ? road.id : 'demo-r-001')}>Select a mapped road</button><button onClick={() => props.onViewport?.([-74.010,40.710,-74.005,40.715])}>Pan test map</button><output aria-label="Restored map extent">{props.focusBounds?.join(',') || 'default'}</output></section> }));
const source = JSON.parse(readFileSync('../../data/demo/manifest.json','utf8')).evidence_source;
const dashboard: Dashboard = { counts:{roads:1,condition:{good:0,fair:0,poor:0,unknown:1},assessments:{total:1,dated:1,accepted:0,ambiguous:1,unmatched:0},permits:{total:1,confirmed_in_scope:0,scope_candidates:1,matched:0,ambiguous:0,unmatched:1,unlocated:1}},observation_date_range:['2025-08-03','2025-08-03'],latest_retrieved_at:'2026-11-01',coverage:snapshot.coverage,dated_road_coverage:{value:0,denominator:1},permit_status_counts:[{status:'ISSUED',count:1}],permit_issue_date_range:null,source_freshness:[] };
beforeEach(() => {
  vi.mocked(municipal.getPermitReleases).mockResolvedValue([]);
  vi.mocked(municipal.getPermitCoverage).mockResolvedValue({method_version:'permit-road-reference-v1',utility_coverage:'unknown',snapshot_id:snapshot.id,permit_release_id:null,total_permits:1,status_counts:{located:0,candidate:1,unlocated:0,outside_coverage:0,invalid_evidence:0},accepted_road_rows:0,precision:'No reviewed permit labels',limitations:[],source_selection:{},result_hash:'test'});
  vi.mocked(municipal.getPermitCoordination).mockResolvedValue({data:[],meta:officialMeta});
  vi.mocked(municipal.getIntelligenceReleases).mockResolvedValue([]);
  vi.mocked(municipal.getConditionSummary).mockResolvedValue(conditionSummary);
  window.history.replaceState(null,'','/');
  vi.mocked(municipal.getWorkspace).mockResolvedValue({mode:'synthetic',snapshot_id:'demo-m1-v1'}); vi.mocked(municipal.getSnapshots).mockResolvedValue([snapshot]); vi.mocked(municipal.getSnapshot).mockResolvedValue(snapshot);
  vi.mocked(municipal.getDashboard).mockResolvedValue(dashboard); vi.mocked(municipal.getMunicipalViewport).mockImplementation(async kind => kind === 'roads' ? [road] : kind === 'conditions' ? [condition] : []);
  vi.mocked(municipal.getMunicipalRoad).mockResolvedValue(road); vi.mocked(municipal.getRoadConditions).mockResolvedValue({data:[],meta:{...officialMeta,latest_usable_id:null}}); vi.mocked(municipal.getShoreline).mockResolvedValue({type:'FeatureCollection',features:[]});
  vi.mocked(municipal.getMunicipalPage).mockImplementation(async kind => ({data:kind==='permits' ? [permit] : [road],meta:officialMeta}));
  vi.mocked(municipal.getMunicipalPermit).mockResolvedValue({...permit,match:{...permit.match!,candidates:[{road_id:road.id,distance_m:5,street_code_agrees:false}]}});
  vi.mocked(municipal.getSource).mockResolvedValue({id:'test-source',source_id:'test',source_url:'https://nyc.gov',endpoint:'https://nyc.gov',retrieved_at:'2026-11-01',source_updated_at:null,release_note:'test',source_crs:'EPSG:4326',attribution:'Test provenance',cadence:'monthly',raw_sha256:'a',dictionary_url:'https://nyc.gov',dictionary_sha256:'b',terms_urls:[],license:{identifier:null,note:'Test terms'}});
  vi.mocked(api.getRoads).mockResolvedValue(roads); vi.mocked(api.getProjects).mockResolvedValue({data:projects,meta}); vi.mocked(api.getConflictAnalysis).mockResolvedValue({data:analysis,meta}); vi.mocked(api.analyzeConflicts).mockResolvedValue({data:analysis,meta});
  vi.mocked(api.getRoad).mockImplementation(async id => {const f=roads.features.find(f=>f.properties.id===id)!; return {data:{...f.properties,geometry:f.geometry},meta};}); vi.mocked(api.getEvidence).mockResolvedValue({data:source,meta});
  vi.mocked(api.getScenarios).mockResolvedValue({data:[scenario(),scenario(1)],meta}); vi.mocked(api.getRepairCatalog).mockResolvedValue({data:catalog,meta}); vi.mocked(api.getScenarioEvaluations).mockImplementation(async id => ({data:[evaluation(id==='scenario-0'?0:1)],meta}));
  vi.mocked(api.getScenarioEvaluation).mockResolvedValue({data:evaluation(),meta}); vi.mocked(api.createScenario).mockResolvedValue({data:scenario(),meta}); vi.mocked(api.updateScenario).mockResolvedValue({data:{...scenario(),revision:2},meta}); vi.mocked(api.evaluateScenario).mockResolvedValue({data:evaluation(),meta}); vi.mocked(api.explainContext).mockResolvedValue({data:answer,meta});
});
async function nav(user: ReturnType<typeof userEvent.setup>, name:string) {await user.click(screen.getByRole('link',{name}));}
it('links whole-snapshot overview → filtered unlocated permit → unconfirmed road and preserves permit selection on return',async()=>{
  window.history.replaceState(null,'',`/#/dashboard?mode=official&snapshot=${snapshot.id}`);const user=userEvent.setup();render(<App/>);
  await screen.findByRole('heading',{name:'Infrastructure overview'}); await screen.findByText(/No supported category mapping/); expect(screen.queryByRole('region',{name:'Test map'})).not.toBeInTheDocument();
  await user.click(screen.getByRole('link',{name:'Inspect unlocated permits →'})); await screen.findByRole('heading',{name:'Projects & coordination'}); expect(screen.getByRole('combobox',{name:'Location evidence'})).toHaveValue('unlocated');
  await user.click(await screen.findByRole('button',{name:/Test Street.*TEST-P-001/})); const detail=screen.getByRole('complementary',{name:'Permit details'});await within(detail).findByRole('heading',{name:'TEST-P-001'});expect(detail).toHaveTextContent('Map location unavailable'); expect(screen.queryByRole('link',{name:'Inspect location on map →'})).not.toBeInTheDocument();
  await user.click(within(detail).getByText('Unconfirmed spatial associations (1)')); await user.click(within(detail).getByRole('link',{name:`Investigate road ${road.id} →`})); await screen.findByRole('heading',{name:'Test Street'}); expect(window.location.hash).toContain(`road=${road.id}`); await user.click(screen.getByText('Verified segment evidence and engineering review')); expect(screen.getByText('No accepted road assessment')).toBeVisible();
  await nav(user,'Projects & coordination'); await within(screen.getByRole('complementary',{name:'Permit details'})).findByRole('heading',{name:'TEST-P-001'});expect(screen.getByRole('combobox',{name:'Location evidence'})).toHaveValue('unlocated');
  expect(api.analyzeConflicts).not.toHaveBeenCalled();expect(api.createScenario).not.toHaveBeenCalled();expect(api.explainContext).not.toHaveBeenCalled();
});
it('restores official camera/layers/search across views and browser history without creating analysis writes',async()=>{
  window.history.replaceState(null,'',`/#/map?mode=official&snapshot=${snapshot.id}&mapq=Test&layers=streets,conditions&bbox=-74.01,40.71,-74.005,40.715`);const user=userEvent.setup();render(<App/>);await screen.findByRole('region',{name:'Test map'});
  expect(screen.getByRole('textbox',{name:'Find road segments'})).toHaveValue('Test');expect(screen.getByLabelText('Restored map extent')).toHaveTextContent('-74.01,40.71,-74.005,40.715');
  await nav(user,'Overview');await screen.findByRole('heading',{name:'Infrastructure overview'});await act(async()=>window.history.back());await screen.findByRole('region',{name:'Test map'});expect(screen.getByRole('textbox',{name:'Find road segments'})).toHaveValue('Test');
  await user.click(screen.getByRole('button',{name:'Layers'}));expect(screen.getByRole('checkbox',{name:'Pavement observations'})).toBeChecked();expect(screen.getByRole('checkbox',{name:'Permit locations'})).not.toBeChecked(); expect(api.analyzeConflicts).not.toHaveBeenCalled();
});
it('runs explicit synthetic coordination, links project→road→planner, preserves draft across views and evaluates only on request',async()=>{
  const user=userEvent.setup();render(<App/>);await user.click(await screen.findByRole('button',{name:'Select a mapped road'}));await screen.findByRole('heading',{name:/Demo segment R-001/});
  await nav(user,'Projects & coordination');expect(api.analyzeConflicts).not.toHaveBeenCalled();await user.click(screen.getByRole('button',{name:'Run conflict screening'}));await user.click(await screen.findByRole('button',{name:/Potential pavement rework/}));
  const finding=screen.getByRole('article',{name:'Selected conflict evidence'});expect(finding).toHaveTextContent('Sequential gap: 2'); await user.click(within(finding).getByRole('button',{name:'Inspect affected road demo-r-001'}));await screen.findByRole('heading',{name:/Demo segment R-001/});
  await nav(user,'Projects & coordination');await user.click(screen.getByRole('button',{name:new RegExp('^'+projects[0].title)}));await user.click(screen.getByRole('button',{name:'Use project in scenario planner'}));await user.click(await screen.findByRole('button',{name:'Create scenario'}));
  await user.type(screen.getByLabelText('Name'),'Linked hypothetical plan');await user.type(screen.getByLabelText('Planning start'),'2027-04-01');await user.type(screen.getByLabelText('Planning end (exclusive)'),'2027-05-01');await user.type(screen.getByLabelText('Explicit synthetic planning assumptions'),'Hypothetical scope and timing; engineering review required.');
  await user.click(screen.getByRole('button',{name:/Add selected map road/}));await user.selectOptions(screen.getByLabelText('Repair method, action 1'),'demo-resurface');await user.click(screen.getByRole('button',{name:'Include selected project in screening'}));
  await nav(user,'Overview');expect(screen.queryByRole('form',{name:'Scenario editor'})).not.toBeInTheDocument();await nav(user,'Scenario planner');expect(screen.getByLabelText('Name')).toHaveValue('Linked hypothetical plan');expect(api.createScenario).not.toHaveBeenCalled();
  await user.click(screen.getByRole('button',{name:'Save and evaluate'}));const result=await screen.findByRole('region',{name:'Scenario evaluation'});expect(result).toHaveTextContent('$53,400.00');expect(api.createScenario).toHaveBeenCalledWith(expect.objectContaining({name:'Linked hypothetical plan',external_project_ids:[projects[0].id]}),expect.any(AbortSignal));expect(api.evaluateScenario).toHaveBeenCalledWith('scenario-0',1,expect.any(AbortSignal));expect(window.location.hash).toContain('evaluation=evaluation-0');
  await user.click(within(result).getByRole('button',{name:'Explain this evaluation'}));expect(await screen.findByRole('article',{name:'Grounded explanation'})).toHaveTextContent('DETERMINISTIC FALLBACK');expect(api.explainContext).toHaveBeenCalledWith({type:'evaluation',record_ids:['evaluation-0']},'deterministic',undefined,expect.any(AbortSignal));expect(api.analyzeConflicts).toHaveBeenCalledOnce();
});
it('restores a saved analysis link with GET without running another screening',async()=>{
  window.history.replaceState(null,'',`/#/projects?mode=synthetic&analysis=${analysis.id}&finding=${analysis.findings[0].id}`);render(<App/>);await screen.findByRole('article',{name:'Selected conflict evidence'});expect(api.getConflictAnalysis).toHaveBeenCalledWith(analysis.id,expect.any(AbortSignal));expect(api.analyzeConflicts).not.toHaveBeenCalled();
});
it('rejects a linked analysis from a different snapshot without replacing it with a new calculation',async()=>{
  vi.mocked(api.getConflictAnalysis).mockResolvedValue({data:{...analysis,dataset_snapshot_id:'different-snapshot'},meta});
  window.history.replaceState(null,'',`/#/projects?mode=synthetic&analysis=${analysis.id}`);render(<App/>);
  expect(await screen.findByText(/Analysis snapshot changed\. Reload the workspace\./)).toBeVisible();expect(screen.queryByRole('article',{name:'Selected conflict evidence'})).not.toBeInTheDocument();expect(api.analyzeConflicts).not.toHaveBeenCalled();
});
it('shows overview request failure without fabricated zero counts and retries the read',async()=>{
  vi.mocked(municipal.getDashboard).mockRejectedValueOnce(new Error('Summary unavailable')).mockResolvedValue(dashboard);
  window.history.replaceState(null,'',`/#/dashboard?mode=official&snapshot=${snapshot.id}`);const user=userEvent.setup();render(<App/>);
  expect(await screen.findByText(/Summary unavailable/)).toBeVisible();expect(screen.queryByRole('region',{name:'Official snapshot coverage'})).not.toBeInTheDocument();
  await user.click(screen.getByRole('button',{name:/Retry/}));await screen.findByText(/No supported category mapping/);expect(municipal.getDashboard).toHaveBeenCalledTimes(2);
});
it('keeps permit details independent of paged filters and cancels stale detail reads',async()=>{
  window.history.replaceState(null,'',`/#/projects?mode=official&snapshot=${snapshot.id}&permit=${permit.id}`);let resolve!: (value:typeof permit)=>void;vi.mocked(municipal.getMunicipalPermit).mockImplementationOnce(()=>new Promise(r=>resolve=r)).mockResolvedValueOnce({...permit,id:'permit-b',source_record_key:'TEST-P-002'});
  const user=userEvent.setup();render(<App/>);await screen.findByRole('heading',{name:'Projects & coordination'});await act(async()=>{window.location.hash=`#/projects?mode=official&snapshot=${snapshot.id}&permit=permit-b&location=unlocated`;});await screen.findByRole('heading',{name:'TEST-P-002'});resolve(permit);await waitFor(()=>expect(screen.queryByRole('heading',{name:'TEST-P-001'})).not.toBeInTheDocument());expect(vi.mocked(municipal.getMunicipalPermit).mock.calls[0][2]?.aborted).toBe(true);
  await user.type(screen.getByRole('textbox',{name:'Find permits'}),'no-match');expect(screen.getByRole('heading',{name:'TEST-P-002'})).toBeVisible();
});
it('reconciles a pending synthetic revision in its original workspace while official mode is visible',async()=>{
  const user=userEvent.setup();let resolve!: (value:{data:ReturnType<typeof scenario>;meta:typeof meta})=>void;
  vi.mocked(api.updateScenario).mockImplementationOnce(()=>new Promise(r=>resolve=r));
  window.history.replaceState(null,'','/#/scenarios?mode=synthetic&scenario=scenario-0');render(<App/>);
  await user.type(await screen.findByLabelText('Name'),' revised');await user.click(screen.getByRole('button',{name:'Save draft'}));
  expect(api.updateScenario).toHaveBeenCalledOnce();await user.selectOptions(screen.getByRole('combobox',{name:'Dataset mode'}),'official');await screen.findByRole('heading',{name:'Official planning comparisons'});
  await act(async()=>resolve({data:{...scenario(),name:scenario().name+' revised',revision:2},meta}));
  expect(window.location.hash).toContain('mode=official');expect(window.location.hash).not.toContain('scenario=');
  await user.selectOptions(screen.getByRole('combobox',{name:'Dataset mode'}),'synthetic');expect(screen.getByLabelText('Name')).toHaveValue(scenario().name+' revised');expect(screen.getByText(/Saved revision 2/)).toBeVisible();expect(window.location.hash).toContain('scenario=scenario-0');expect(api.evaluateScenario).not.toHaveBeenCalled();
});
