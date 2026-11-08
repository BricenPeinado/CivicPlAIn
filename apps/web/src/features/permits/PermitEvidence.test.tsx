import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,fireEvent,render,screen,waitFor} from '@testing-library/react';
import {PermitLocationAndCoordination,PermitCoverageControls} from './PermitEvidence';
import * as service from '../../services/municipal';
import {permit,sid,meta,road} from '../../test-municipal';
import type {PermitLocationEvidence} from '../../types/municipal';
vi.mock('../../services/municipal',()=>({getPermitCoordination:vi.fn(),getPermitCoverage:vi.fn(),getPermitReleases:vi.fn()}));
afterEach(()=>{cleanup();vi.clearAllMocks();});
const evidence:PermitLocationEvidence={method_version:'permit-road-reference-v1',snapshot_id:sid,permit_release_id:null,status:'candidate',accepted_road_ids:[],accepted_associations:[],candidates:[{road_id:road.id,distance_m:null,street_code_agrees:false,on_street_name_agrees:true,from_endpoint_road_ids:[],to_endpoint_road_ids:[]}],candidate_set_hash:'a'.repeat(64),parameter_hash:'b'.repeat(64),result_hash:'c'.repeat(64),reasons:['WKT_CRS_UNVERIFIED'],actual_schedule:'unknown',location_meaning:'road reference only; work footprint unknown',classification:'derived_calculation'};
it('keeps candidate certainty and only screens on explicit action, then resets with record context',async()=>{
 vi.mocked(service.getPermitCoordination).mockResolvedValue({data:[],meta:{...meta,total_matching:0}});
 const view=render(<PermitLocationAndCoordination record={{...permit,permit_location:evidence}} snapshot={sid} route={{view:'projects',road:null,mode:'official',snapshot:sid}}/>);
 expect(screen.getByText(/Candidate location requiring review/)).toBeTruthy();expect(service.getPermitCoordination).not.toHaveBeenCalled();
 fireEvent.click(screen.getByText('Candidate road references (1)'));expect(screen.getByRole('link',{name:/Investigate candidate/}).getAttribute('href')).toContain('road=road-test-a');expect(screen.getByText(/Distance unknown/)).toBeTruthy();
 fireEvent.click(screen.getByRole('button',{name:'Find coordination candidates'}));await screen.findByText(/0 screening candidates/);expect(screen.getByText(/Zero findings never establishes/)).toBeTruthy();
 view.rerender(<PermitLocationAndCoordination record={{...permit,id:'other',permit_location:evidence}} snapshot={sid} route={{view:'projects',road:null}}/>);await waitFor(()=>expect(screen.queryByText(/0 screening candidates/)).toBeNull());
});
it('displays accepted review evidence without converting it to a footprint or schedule',()=>{
 render(<PermitLocationAndCoordination record={{...permit,permit_location:{...evidence,status:'located',accepted_road_ids:[road.id],accepted_associations:[{id:'test-review',candidate_hash:'a'.repeat(64),decision:{reviewer:'Authored test reviewer',reason:'Test evidence only',scope:'partial'}}]}}} snapshot={sid} route={{view:'projects',road:null}}/>);
 expect(screen.getByText(/Located with accepted evidence/)).toBeTruthy();expect(screen.getByText(/Actual schedule: unknown/)).toBeTruthy();expect(screen.getByText(/Test evidence only/)).toBeTruthy();expect(screen.getByRole('link',{name:/Inspect accepted road reference/})).toBeTruthy();
});
it('shows whole snapshot denominators, all five status choices, and forwards selected filter',async()=>{
 vi.mocked(service.getPermitReleases).mockResolvedValue([]);vi.mocked(service.getPermitCoverage).mockResolvedValue({snapshot_id:sid,permit_release_id:null,method_version:'permit-road-reference-v1',total_permits:12,accepted_road_rows:0,status_counts:{located:0,candidate:7,unlocated:3,outside_coverage:1,invalid_evidence:1},precision:'Unmeasured without independent review',source_selection:{},limitations:['Incomplete administrative selection'],result_hash:'a'.repeat(64),utility_coverage:'unknown'});
 const onRoute=vi.fn();render(<PermitCoverageControls snapshot={sid} route={{view:'projects',road:null}} onRoute={onRoute}/>);await screen.findByText(/12 administrative records/);expect(screen.getByText(/Unmeasured/)).toBeTruthy();fireEvent.change(screen.getByLabelText('Evidence status'),{target:{value:'outside_coverage'}});expect(onRoute).toHaveBeenCalledWith({locstatus:'outside_coverage'});
});
