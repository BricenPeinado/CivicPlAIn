import {afterEach,expect,it,vi} from 'vitest';
import {calculateMunicipalEstimate,getMunicipalEstimate} from './municipalPlanning';
import {meta,sid} from '../test-municipal';
import type {MunicipalEstimateRequest} from '../types/municipalPlanning';
const request:MunicipalEstimateRequest={contract_version:'municipal-estimate-v1',snapshot_id:sid,road_id:'road-test',alternatives:[{treatment:'resurface',exclusions:[],allowances:[]}]};
const response=(data:unknown)=>({ok:true,json:async()=>({data,meta})}) as Response;
afterEach(()=>vi.unstubAllGlobals());
it('never accepts a calculation from a different road/snapshot or a synthetic result',async()=>{
 const r={input_snapshot:{request},result:{contract_version:'municipal-estimate-v1',method_version:'municipal-area-cost-v1',snapshot_id:sid,road_id:'different',contains_synthetic:false,contains_assumptions:true,utility_coverage:'unknown',alternatives:[]}};
 const fetch=vi.fn().mockResolvedValueOnce(response(r)).mockResolvedValueOnce(response({...r,result:{...r.result,road_id:'road-test',contains_synthetic:true}}));vi.stubGlobal('fetch',fetch);
 await expect(calculateMunicipalEstimate(request,false)).rejects.toThrow('context');await expect(calculateMunicipalEstimate(request,true)).rejects.toThrow('context');expect(fetch.mock.calls[0][0]).toContain('/preview');expect(fetch.mock.calls[1][1].method).toBe('POST');
});
it('binds saved reads to explicit snapshot and caller cancellation',async()=>{
 const ac=new AbortController();ac.abort();const fetch=vi.fn().mockRejectedValue(ac.signal.reason);vi.stubGlobal('fetch',fetch);await expect(getMunicipalEstimate(sid,'road-test','estimate-'+'1'.repeat(64),ac.signal)).rejects.toBeTruthy();expect(fetch.mock.calls[0][0]).toContain(`snapshot_id=${sid}`);
});
