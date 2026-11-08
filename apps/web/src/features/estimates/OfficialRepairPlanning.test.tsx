import {afterEach,beforeEach,expect,it,vi} from 'vitest';
import {cleanup,fireEvent,render,screen} from '@testing-library/react';
import {OfficialRepairPlanning} from './OfficialRepairPlanning';
import * as service from '../../services/municipalPlanning';
import type {EstimatePreview,PlanningCapabilities} from '../../types/municipalPlanning';
import {sid} from '../../test-municipal';
vi.mock('../../services/municipalPlanning',()=>({calculateMunicipalEstimate:vi.fn(),getPlanningCapabilities:vi.fn(),getMunicipalEstimates:vi.fn(),getMunicipalEstimate:vi.fn()}));
const capabilities:PlanningCapabilities={snapshot_id:sid,road_id:'test',contract_version:'municipal-estimate-v1',method_version:'municipal-area-cost-v1',treatments:{patch:{label:'patch',scope:'declared',source:'https://example.org'},resurface:{label:'resurface',scope:'declared',source:'https://example.org'}},persistence_available:true,rate_catalog_available:false,reason:'No reviewed NYC price catalog',utility_coverage:'unknown',reconstruction_available:false};
const preview:EstimatePreview={input_snapshot:{request:{contract_version:'municipal-estimate-v1',snapshot_id:sid,road_id:'test',alternatives:[]},road:{},road_source:{},base:{},method_version:'municipal-area-cost-v1',arithmetic_version:'area-cost-decimal-v1',conversions:{},methods:{}},input_hash:'a'.repeat(64),result_hash:'b'.repeat(64),result:{contract_version:'municipal-estimate-v1',method_version:'municipal-area-cost-v1',arithmetic_version:'area-cost-decimal-v1',snapshot_id:sid,road_id:'test',currency:'USD',contains_synthetic:false,contains_assumptions:true,utility_coverage:'unknown',comparison_basis:'Independent declared scopes',warnings:['No market-price claim'],alternatives:[{treatment:'resurface',status:'unavailable',input_path:'request.alternatives.0',missing_fields:['rate','scope'],quantity_m2:null,cases:null,duration:null,scope:null,price_basis_date:null,geography:null,inclusions:null,exclusions:[],allowance_declarations:[],unknowns:['Unknown structural suitability'],suitability:'requires_engineering_review'}]}};
beforeEach(()=>{vi.mocked(service.getPlanningCapabilities).mockResolvedValue(capabilities);vi.mocked(service.calculateMunicipalEstimate).mockResolvedValue(preview);});
afterEach(()=>{cleanup();vi.clearAllMocks();});
it('keeps numeric prices/quantities blank, uses explicit POST only, and renders unavailable states',async()=>{
 render(<OfficialRepairPlanning snapshot={sid} road="blank-test"/>);await screen.findByText('No reviewed NYC price catalog');expect(service.calculateMunicipalEstimate).not.toHaveBeenCalled();expect((screen.getByLabelText('Bundled unit rate') as HTMLInputElement).value).toBe('');expect((screen.getByLabelText('Treatment area') as HTMLInputElement).value).toBe('');
 fireEvent.click(screen.getByRole('button',{name:'Calculate planning comparison'}));await screen.findByText('Estimate unavailable: rate, scope.');expect(service.calculateMunicipalEstimate).toHaveBeenCalledWith(expect.objectContaining({road_id:'blank-test',alternatives:[expect.objectContaining({treatment:'resurface',rate:undefined})]}),false,expect.any(AbortSignal));expect(screen.getByText(/Duration unavailable; no construction schedule/)).toBeTruthy();expect(screen.queryByRole('button',{name:'Save immutable estimate'})).toBeNull();
});
it('retains distinct unsaved drafts per road and never places assumptions in links',()=>{
 const a=render(<OfficialRepairPlanning snapshot={sid} road="draft-a"/>);fireEvent.change(screen.getByLabelText('Planner / author'),{target:{value:'SYNTHETIC TEST AUTHOR'}});a.unmount();const b=render(<OfficialRepairPlanning snapshot={sid} road="draft-b"/>);expect((screen.getByLabelText('Planner / author') as HTMLInputElement).value).toBe('');b.unmount();render(<OfficialRepairPlanning snapshot={sid} road="draft-a"/>);expect((screen.getByLabelText('Planner / author') as HTMLInputElement).value).toBe('SYNTHETIC TEST AUTHOR');fireEvent.click(screen.getByText('Discard this road’s input draft'));expect((screen.getByLabelText('Planner / author') as HTMLInputElement).value).toBe('');
});
it('requires provenance for a supplied value and refuses incomplete rate sensitivity',async()=>{
 render(<OfficialRepairPlanning snapshot={sid} road="provenance-test"/>);fireEvent.change(screen.getByLabelText('Bundled unit rate'),{target:{value:'1'}});fireEvent.click(screen.getByText('Calculate planning comparison'));await screen.findByRole('alert');expect(service.calculateMunicipalEstimate).not.toHaveBeenCalled();
});
it('preserves an explicit zero assumption with provenance and omits blank optional inputs',async()=>{
 render(<OfficialRepairPlanning snapshot={sid} road="zero-test"/>);
 fireEvent.change(screen.getByLabelText('Planner / author'),{target:{value:'SYNTHETIC TEST'}});
 fireEvent.change(screen.getByLabelText('Assumption entered date'),{target:{value:'2026-11-08'}});
 fireEvent.change(screen.getByLabelText('Assumption rationale (applies to supplied fields)'),{target:{value:'Authored test assumption'}});
 fireEvent.change(screen.getByLabelText('Contingency fraction (0–1; explicit zero permitted)'),{target:{value:'0'}});
 fireEvent.click(screen.getByText('Calculate planning comparison'));await screen.findByText('Unsaved calculation preview');
 const body=vi.mocked(service.calculateMunicipalEstimate).mock.calls[0][0];expect(body.alternatives[0].contingency).toMatchObject({value:'0',unit:'fraction',evidence:{classification:'planning_assumption',author:'SYNTHETIC TEST'}});expect(body.alternatives[0].productivity).toBeUndefined();
});
it('saves only after explicit preview and shows the returned immutable result',async()=>{
 const available=structuredClone(preview);available.result.alternatives[0]={...available.result.alternatives[0],status:'available',missing_fields:[],quantity_m2:'20',cases:{base:{line_items:[],subtotal_usd:'20.10',contingency_usd:'0.00',total_usd:'20.10',contingency_fraction:'0',total_cents:2010}}};
 vi.mocked(service.calculateMunicipalEstimate).mockResolvedValueOnce(available).mockResolvedValueOnce({...available,id:'estimate-'+'a'.repeat(64),created_at:'2026-11-08T00:00:00Z'});
 render(<OfficialRepairPlanning snapshot={sid} road="save-test"/>);await screen.findByText('No reviewed NYC price catalog');
 expect(screen.queryByText('Save immutable estimate')).toBeNull();fireEvent.click(screen.getByText('Calculate planning comparison'));await screen.findByText('Unsaved calculation preview');
 expect(service.calculateMunicipalEstimate).toHaveBeenCalledTimes(1);fireEvent.click(screen.getByText('Save immutable estimate'));await screen.findByText('Saved immutable estimate');
 expect(vi.mocked(service.calculateMunicipalEstimate).mock.calls[1][1]).toBe(true);expect(screen.getByText(/estimate-aaaa/)).toBeTruthy();
});
