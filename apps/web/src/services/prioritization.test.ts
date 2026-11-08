import {afterEach,expect,it,vi} from 'vitest';
import {computePriority,getPriority} from './prioritization';
import {sid,meta} from '../test-municipal';
import type {PriorityRequest} from '../types/prioritization';
afterEach(()=>vi.unstubAllGlobals());
const body={contract_version:'maintenance-priority-v1',snapshot_id:sid,road_ids:['a']} as PriorityRequest;
it('uses explicit POST and rejects cross-snapshot provenance',async()=>{
 const fetcher=vi.fn().mockResolvedValue({ok:true,json:async()=>({meta:meta,data:{input_snapshot:{request:body},result:{snapshot_id:'foreign',method_version:'maintenance-priority-v1'}}})});vi.stubGlobal('fetch',fetcher);
 await expect(computePriority(body,false)).rejects.toThrow('context');expect(fetcher.mock.calls[0][0]).toMatch(/\/preview$/);expect(fetcher.mock.calls[0][1].method).toBe('POST');
});
it('retrieves saved runs by exact pinned snapshot and propagates caller cancellation',async()=>{
 const ac=new AbortController();ac.abort();const fetcher=vi.fn().mockRejectedValue(new DOMException('aborted','AbortError'));vi.stubGlobal('fetch',fetcher);await expect(getPriority(sid,'priority-'+'a'.repeat(64),ac.signal)).rejects.toThrow();expect(fetcher.mock.calls[0][0]).toContain('snapshot_id='+sid);
});
