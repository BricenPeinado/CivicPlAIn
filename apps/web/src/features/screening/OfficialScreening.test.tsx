import {afterEach,beforeEach,expect,it,vi} from 'vitest';
import {cleanup,fireEvent,render,screen} from '@testing-library/react';
import {OfficialScreening} from './OfficialScreening';
import * as service from '../../services/officialScreening';
import {explainDecision} from '../../services/decisionSupport';
import {answer} from '../ai/testData';
vi.mock('../../services/decisionSupport',()=>({explainDecision:vi.fn()}));
import type {ScreeningRecord} from '../../types/officialScreening';
vi.mock('../../services/officialScreening',()=>({computeScreening:vi.fn(),getScreening:vi.fn(),getScreenings:vi.fn(),getScreeningNotes:vi.fn(),addScreeningNote:vi.fn()}));
const value=():ScreeningRecord=>({input_hash:'a'.repeat(64),result_hash:'b'.repeat(64),input_snapshot:{request:{snapshot_id:'test'}},result:{method_version:'official-screen-v1',snapshot_id:'test',contains_synthetic:false,human_review_required:true,coverage:{utilities:'unknown',excavation_clearance:false},warnings:['No clearance'],cost_comparison:{status:'unavailable'},alternatives:[{id:'later',result_hash:'c'.repeat(64),interpretation:'Changed dates only',screen:{activities:[],findings:[],pair_checks:[],activity_unknowns:[],indeterminate_pair_count:1,possible_pair_count:1,checked_pair_count:1}}],base:{activities:[{id:'a',activity_id:'work:a',title:'SYNTHETIC work',origin:'supplied_work',road_ids:['r'],schedule:null,location_issue:null,location:{certainty:'approximate',geometry:{type:'LineString',coordinates:[[-74.01,40.712],[-74.009,40.712]]}}}],findings:[{id:'finding-'+'c'.repeat(64),activity_ids:['work:a','work:b'],finding_type:'potential_pavement_rework',category:'potential_coordination_opportunity',spatial:{distance_m:0},temporal:{relation:'adjacent'},explanation:'SYNTHETIC supplied scopes require review',qualified_by:['grade_separation'],human_review_required:true,evidence_status:'supplied_evidence_only_not_independently_verified',required_review:['Confirm actual timing']}],pair_checks:[],activity_unknowns:[],indeterminate_pair_count:1,possible_pair_count:1,checked_pair_count:1}}});
function fill(){for(const [label,v] of Object.entries({'Screening author':'SYNTHETIC TEST','Evidence entered date':'2026-11-08','Assumption rationale':'Synthetic schedule declaration, no real work','Spatial proximity (m)':'5','Rework review horizon (days)':'30','Selected administrative permit IDs':'p'}))fireEvent.change(screen.getByLabelText(label),{target:{value:v}});}
beforeEach(()=>{vi.mocked(service.computeScreening).mockResolvedValue(value());});afterEach(()=>{cleanup();vi.clearAllMocks();});
it('keeps thresholds blank and never creates analysis on navigation',async()=>{render(<OfficialScreening snapshot="blank"/>);expect(service.computeScreening).not.toHaveBeenCalled();expect((screen.getByLabelText('Spatial proximity (m)') as HTMLInputElement).value).toBe('');fireEvent.click(screen.getByText('Analyze construction conflicts'));expect(await screen.findByRole('alert')).toHaveTextContent('Author');expect(service.computeScreening).not.toHaveBeenCalled();});
it('inspects supplied finding geometry, switches alternatives and invalidates old output',async()=>{const map=vi.fn();render(<OfficialScreening snapshot="preview" onMap={map}/>);fill();fireEvent.click(screen.getByText('Analyze construction conflicts'));await screen.findByText('Unsaved screening preview');fireEvent.click(screen.getByText('Inspect potential pavement rework on map'));expect(map.mock.lastCall?.[0].features.features).toHaveLength(1);expect(screen.getByRole('article',{name:'Selected screening finding'})).toHaveTextContent('Human review required');fireEvent.change(screen.getByLabelText('Schedule comparison'),{target:{value:'later'}});expect(screen.getByText(/No conflicts were established/)).toBeTruthy();expect(service.computeScreening).toHaveBeenCalledTimes(1);fireEvent.change(screen.getByLabelText('Spatial proximity (m)'),{target:{value:'6'}});expect(screen.queryByText('Unsaved screening preview')).toBeNull();expect(map.mock.lastCall?.[0].features.features).toHaveLength(0);});
it('saves only on explicit action and records separate human notes',async()=>{vi.mocked(service.computeScreening).mockResolvedValue({...value(),id:'screen-'+'a'.repeat(64)});vi.mocked(service.addScreeningNote).mockResolvedValue({id:'review-1',author:'TEST',note:'Needs field inspection',disposition:'needs_review',finding_id:null,meaning:'No approval'});render(<OfficialScreening snapshot="save"/>);fill();fireEvent.click(screen.getByText('Save immutable screening'));await screen.findByText('Saved immutable screening');expect(vi.mocked(service.computeScreening).mock.calls[0][1]).toBe(true);fireEvent.change(screen.getByLabelText('Review author'),{target:{value:'TEST'}});fireEvent.change(screen.getByLabelText('Review note'),{target:{value:'Needs field inspection'}});fireEvent.click(screen.getByText('Record review note'));await screen.findByText('Needs field inspection');expect(service.addScreeningNote).toHaveBeenCalledTimes(1);expect(service.computeScreening).toHaveBeenCalledTimes(1);});
it('keeps per-snapshot drafts and reports source failures without substituted findings',async()=>{const first=render(<OfficialScreening snapshot="draft-a"/>);fireEvent.change(screen.getByLabelText('Screening author'),{target:{value:'TEST'}});first.unmount();const second=render(<OfficialScreening snapshot="draft-b"/>);expect((screen.getByLabelText('Screening author') as HTMLInputElement).value).toBe('');second.unmount();render(<OfficialScreening snapshot="draft-a"/>);expect((screen.getByLabelText('Screening author') as HTMLInputElement).value).toBe('TEST');fireEvent.click(screen.getByText('Discard screening draft'));fireEvent.click(screen.getByText('Discard changes'));fill();vi.mocked(service.computeScreening).mockRejectedValueOnce(new Error('Pinned source unavailable'));fireEvent.click(screen.getByText('Analyze construction conflicts'));await screen.findByText('Pinned source unavailable');expect(screen.queryByText('Unsaved screening preview')).toBeNull();});
it('adds explicit work without importing a road footprint or a schedule',()=>{render(<OfficialScreening snapshot="work" currentRoad="r"/>);fireEvent.click(screen.getByText('Add hypothetical work'));expect((screen.getByLabelText('Work 1 roads') as HTMLInputElement).value).toBe('r');expect((screen.getByLabelText('Work 1 GeoJSON geometry (EPSG:4326)') as HTMLTextAreaElement).value).toBe('');expect((screen.getByLabelText('Work 1 start (end exclusive)') as HTMLInputElement).value).toBe('');});

it('restores an explicit saved alternative without computation or substituting its missing finding',async()=>{
 const id='screen-'+'d'.repeat(64),finding=value().result.base.findings[0].id,map=vi.fn(),pin=vi.fn();
 vi.mocked(service.getScreening).mockResolvedValue({...value(),id});
 const view=render(<OfficialScreening snapshot="pinned" initialId={id} initialFinding={finding} onMap={map} onRecord={pin}/>);
 await screen.findByText('Saved immutable screening');expect(service.computeScreening).not.toHaveBeenCalled();expect(pin).not.toHaveBeenCalled();
 expect(map.mock.lastCall?.[0].features.features).toHaveLength(1);
 view.rerender(<OfficialScreening snapshot="pinned" initialId={id} initialFinding={finding} initialAlternative="later" onMap={map} onRecord={pin}/>);
 expect(await screen.findByRole('alert')).toHaveTextContent('No finding overlay substituted');expect(map.mock.lastCall?.[0].features.features).toHaveLength(0);
});

it('draws, undoes, edits, cancels and removes approximate work geometry without JSON',async()=>{
 const {act}=await import('@testing-library/react');
 const map=vi.fn(),zones=vi.fn(),drawing=vi.fn();render(<OfficialScreening snapshot="visual-draw" currentRoad="road-reference" onMap={map} onZones={zones} onDrawing={drawing}/>);
 fireEvent.click(screen.getByText('Add hypothetical work'));expect(drawing.mock.lastCall?.[0].points).toEqual([]);
 fireEvent.click(screen.getByText('Finish alignment'));expect(screen.getByRole('alert')).toHaveTextContent('2–500');
 act(()=>drawing.mock.lastCall?.[0].onPoint([-74.01,40.712]));act(()=>drawing.mock.lastCall?.[0].onPoint([-74.009,40.712]));
 fireEvent.click(screen.getByText('Undo point'));expect(drawing.mock.lastCall?.[0].points).toHaveLength(1);
 act(()=>drawing.mock.lastCall?.[0].onPoint([40.712,-74.01]));expect(screen.getByRole('alert')).toHaveTextContent('outside');
 act(()=>drawing.mock.lastCall?.[0].onPoint([-74.008,40.712]));fireEvent.click(screen.getByText('Finish alignment'));
 expect(drawing.mock.lastCall?.[0]).toBeNull();expect(zones.mock.lastCall?.[0].features[0].geometry.coordinates).toEqual([[-74.01,40.712],[-74.008,40.712]]);
 fireEvent.click(screen.getByText('Edit work zone 1'));act(()=>drawing.mock.lastCall?.[0].onPoint([-74.007,40.712]));fireEvent.click(screen.getByText('Cancel drawing'));
 expect(JSON.parse((screen.getByLabelText('Work 1 GeoJSON geometry (EPSG:4326)') as HTMLTextAreaElement).value).coordinates).toHaveLength(2);
 fireEvent.click(screen.getByText('Remove alignment 1'));expect(zones.mock.lastCall?.[0].features).toHaveLength(0);
 fireEvent.change(screen.getByLabelText('Work 1 GeoJSON geometry (EPSG:4326)'),{target:{value:'{"type":"LineString","coordinates":[[40.7,-74],[40.71,-74]]}'}});expect(zones.mock.lastCall?.[0].features).toHaveLength(0);
 fireEvent.click(screen.getByText('Remove work 1'));expect(screen.queryByLabelText('Work 1 title')).toBeNull();expect(service.computeScreening).not.toHaveBeenCalled();
});
it('submits visual schedules, keeps preview separate from save and renders calculated comparison',async()=>{
 const {act}=await import('@testing-library/react');const drawing=vi.fn();render(<OfficialScreening snapshot="visual-submit" onDrawing={drawing}/>);
 fill();fireEvent.change(screen.getByLabelText('Selected administrative permit IDs'),{target:{value:''}});
 for(let i=1;i<=2;i++){
  fireEvent.click(screen.getByText('Add hypothetical work'));act(()=>drawing.mock.lastCall?.[0].onPoint([-74.01,40.712]));act(()=>drawing.mock.lastCall?.[0].onPoint([-74.009,40.712]));fireEvent.click(screen.getByText('Finish alignment'));
  for(const [k,v] of Object.entries({title:`SYNTHETIC ${i}`,'start (end exclusive)':'2027-01-01','end (end exclusive)':'2027-01-10'}))fireEvent.change(screen.getByLabelText(`Work ${i} ${k}`),{target:{value:v}});
 }
 expect(screen.getByText('Add hypothetical work')).toBeDisabled();fireEvent.click(screen.getByText('Create alternative schedule'));
 fireEvent.change(screen.getByLabelText('alternative-1 work 1 start'),{target:{value:'2027-03-01'}});fireEvent.change(screen.getByLabelText('alternative-1 work 1 end'),{target:{value:'2027-03-10'}});
 fireEvent.click(screen.getByText('Analyze construction conflicts'));await screen.findByText('Unsaved screening preview');
 const [request,save]=vi.mocked(service.computeScreening).mock.calls[0];expect(save).toBe(false);expect(request).toMatchObject({works:[{id:'zone-1',schedule:{start:'2027-01-01'}},{id:'zone-2'}],alternatives:[{id:'alternative-1',overrides:[{work_id:'zone-1',schedule:{start:'2027-03-01'}},{work_id:'zone-2'}]}]});
 expect(screen.getByRole('region',{name:'Schedule comparison table'})).toHaveTextContent('Unknown · no supported cost basis');expect(screen.getByLabelText('Calculated schedule comparison')).toHaveTextContent('1 removed');expect(screen.queryByText('Explain planning tradeoffs')).toBeNull();
});
it('preserves inputs on failed requests, cancels obsolete previews and protects discard',async()=>{
 const {act}=await import('@testing-library/react');let resolve!:(v:ScreeningRecord)=>void;
 vi.mocked(service.computeScreening).mockImplementationOnce(()=>new Promise(r=>{resolve=r;}));render(<OfficialScreening snapshot="obsolete-preview"/>);fill();fireEvent.click(screen.getByText('Analyze construction conflicts'));const signal=vi.mocked(service.computeScreening).mock.calls[0][2];
 fireEvent.change(screen.getByLabelText('Spatial proximity (m)'),{target:{value:'8'}});expect(signal?.aborted).toBe(true);await act(async()=>resolve(value()));expect(screen.queryByText('Unsaved screening preview')).toBeNull();
 vi.mocked(service.computeScreening).mockRejectedValueOnce(new Error('Retry required'));fireEvent.click(screen.getByText('Analyze construction conflicts'));await screen.findByText('Retry required');expect(screen.getByLabelText('Spatial proximity (m)')).toHaveValue('8');
 fireEvent.click(screen.getByText('Discard screening draft'));fireEvent.click(screen.getByText('Keep editing'));expect(screen.getByLabelText('Spatial proximity (m)')).toHaveValue('8');fireEvent.click(screen.getByText('Discard screening draft'));fireEvent.click(screen.getByText('Discard changes'));expect(screen.getByLabelText('Spatial proximity (m)')).toHaveValue('');
});
it('views saved results without overwriting drafts and ignores out-of-order saved retrieval',async()=>{
 const {act}=await import('@testing-library/react');let old!:(v:ScreeningRecord)=>void;
 const first='screen-'+'1'.repeat(64),second='screen-'+'2'.repeat(64);
 vi.mocked(service.getScreening).mockImplementationOnce(()=>new Promise(r=>{old=r;})).mockResolvedValueOnce({...value(),id:second});
 const view=render(<OfficialScreening snapshot="saved-race"/>);fireEvent.change(screen.getByLabelText('Screening author'),{target:{value:'My draft'}});
 view.rerender(<OfficialScreening snapshot="saved-race" initialId={first}/>);const signal=vi.mocked(service.getScreening).mock.calls[0][2];view.rerender(<OfficialScreening snapshot="saved-race" initialId={second}/>);await screen.findByText(second);await act(async()=>old({...value(),id:first}));expect(signal?.aborted).toBe(true);expect(screen.queryByText(first)).toBeNull();expect(screen.getByLabelText('Screening author')).toHaveValue('My draft');expect(service.computeScreening).not.toHaveBeenCalled();
});

it('explains only a selected saved result with the existing deterministic fallback',async()=>{
 const id='screen-'+'3'.repeat(64);vi.mocked(service.getScreening).mockResolvedValue({...value(),id});vi.mocked(explainDecision).mockResolvedValue({...answer,summary:'Saved screening evidence only',key_findings:[],source_classification:'derived'});
 render(<OfficialScreening snapshot="explain-saved" initialId={id}/>);await screen.findByText('Saved immutable screening');expect(explainDecision).not.toHaveBeenCalled();fireEvent.click(screen.getByText('Explain planning tradeoffs'));await screen.findByText(/Saved screening evidence only/);expect(explainDecision).toHaveBeenCalledWith('explain-saved','screening',id,'deterministic',expect.any(AbortSignal));expect(screen.getByLabelText('Planning tradeoffs explanation')).toHaveTextContent('not_configured');expect(service.computeScreening).not.toHaveBeenCalled();
});
it('does not substitute a draft or base when a pinned saved alternative is missing',async()=>{
 const id='screen-'+'4'.repeat(64),zones=vi.fn();vi.mocked(service.getScreening).mockResolvedValue({...value(),id});render(<OfficialScreening snapshot="missing-variant" initialId={id} initialAlternative="absent" onZones={zones}/>);expect(await screen.findByRole('alert')).toHaveTextContent('No base result or draft overlay substituted');expect(zones.mock.lastCall?.[0].features).toHaveLength(0);expect(service.computeScreening).not.toHaveBeenCalled();
});

it('retains unfinished drawing across navigation and cleans overlays when the panel unmounts',async()=>{
 const {act}=await import('@testing-library/react');const drawing=vi.fn(),zones=vi.fn();const first=render(<OfficialScreening snapshot="unfinished-navigation" onDrawing={drawing} onZones={zones}/>);fireEvent.click(screen.getByText('Add hypothetical work'));act(()=>drawing.mock.lastCall?.[0].onPoint([-74.01,40.712]));first.unmount();expect(drawing.mock.lastCall?.[0]).toBeNull();expect(zones.mock.lastCall?.[0].features).toHaveLength(0);
 const second=render(<OfficialScreening snapshot="different-drawing-context" onDrawing={drawing}/>);expect(drawing.mock.lastCall?.[0]).toBeNull();second.unmount();render(<OfficialScreening snapshot="unfinished-navigation" onDrawing={drawing}/>);expect(drawing.mock.lastCall?.[0].points).toEqual([[-74.01,40.712]]);fireEvent.click(screen.getByText('Discard screening draft'));fireEvent.click(screen.getByText('Discard changes'));expect(drawing.mock.lastCall?.[0]).toBeNull();expect(screen.queryByLabelText('Work 1 title')).toBeNull();
});
it('starts drawing only from an explicit Plan construction action and preserves existing work',async()=>{
 const drawing=vi.fn();const view=render(<OfficialScreening snapshot="explicit-start" autoStart onDrawing={drawing} currentRoad="r"/>);expect(await screen.findByLabelText('Work-zone drawing controls')).toBeVisible();expect(screen.getByLabelText('Work 1 roads')).toHaveValue('r');expect(service.computeScreening).not.toHaveBeenCalled();fireEvent.click(screen.getByText('Cancel drawing'));fireEvent.change(screen.getByLabelText('Work 1 title'),{target:{value:'Keep this declaration'}});view.unmount();render(<OfficialScreening snapshot="explicit-start" autoStart onDrawing={drawing}/>);expect(screen.getByLabelText('Work 1 title')).toHaveValue('Keep this declaration');expect(screen.queryByLabelText('Work-zone drawing controls')).toBeNull();
});
