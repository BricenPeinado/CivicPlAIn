import { afterEach, expect, it, vi } from 'vitest';
import { getMunicipalViewport, getMunicipalRoad, getMunicipalPermit, getRoadConditions, getSource, getSnapshots, getWorkspace } from './municipal';
import { readJSON } from './http';
import { sid, meta, road, permit, snapshot } from '../test-municipal';
const reply = (data: unknown) => ({ ok: true, json: async () => data }) as Response;
it('validates independently linked permit identity, snapshot and synthetic boundary', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValueOnce(reply({data:permit,meta})).mockResolvedValueOnce(reply({data:{...permit,id:'wrong'},meta})).mockResolvedValueOnce(reply({data:permit,meta:{...meta,snapshot_id:'wrong'}})).mockResolvedValueOnce(reply({data:{...permit,contains_synthetic:true},meta})));
  expect((await getMunicipalPermit(sid,permit.id)).id).toBe(permit.id);
  await expect(getMunicipalPermit(sid,permit.id)).rejects.toThrow('identity');
  await expect(getMunicipalPermit(sid,permit.id)).rejects.toThrow('snapshot');
  await expect(getMunicipalPermit(sid,permit.id)).rejects.toThrow('Synthetic');
});
afterEach(() => vi.unstubAllGlobals());
it('reads all snapshot-bound pages with exact geographic coordinates', async () => {
  const fetch = vi.fn().mockResolvedValueOnce(reply({ data: [road], meta: { ...meta, next_cursor: 'page2', total_matching: 2 } })).mockResolvedValueOnce(reply({ data: [{ ...road, id: 'road-test-b' }], meta: { ...meta, total_matching: 2 } })); vi.stubGlobal('fetch', fetch);
  const values = await getMunicipalViewport('roads', sid, [-74.01,40.71,-74,40.72]); expect(values).toHaveLength(2); expect(values[0].geometry).toEqual(road.geometry);
  expect(fetch.mock.calls[0][0]).toContain(`snapshot_id=${sid}`); expect(fetch.mock.calls[1][0]).toContain('cursor=page2'); expect(fetch.mock.calls[0][1].method).toBeUndefined();
});
it('fails closed on a mixed snapshot or synthetic official payload', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValueOnce(reply({ data: [road], meta: { ...meta, snapshot_id: 'other' } })).mockResolvedValueOnce(reply({ data: [{ ...road, contains_synthetic: true }], meta })));
  await expect(getMunicipalViewport('roads', sid, snapshot.coverage.bbox)).rejects.toThrow('snapshot changed'); await expect(getMunicipalViewport('roads', sid, snapshot.coverage.bbox)).rejects.toThrow('Synthetic records');
});
it('rejects oversize viewports before silently truncating or paging', async () => {
  const fetch = vi.fn().mockResolvedValue(reply({ data: [road], meta: { ...meta, total_matching: 2001, next_cursor: 'more' } })); vi.stubGlobal('fetch', fetch);
  await expect(getMunicipalViewport('roads', sid, snapshot.coverage.bbox)).rejects.toThrow('Zoom in'); expect(fetch).toHaveBeenCalledOnce();
});
it('rejects duplicate records and repeated cursors', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValueOnce(reply({ data: [road, road], meta }))); await expect(getMunicipalViewport('roads', sid, snapshot.coverage.bbox)).rejects.toThrow('Duplicate');
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(reply({ data: [road], meta: { ...meta, next_cursor: 'repeat' } }))); await expect(getMunicipalViewport('roads', sid, snapshot.coverage.bbox)).rejects.toThrow('Repeated');
});
it('validates road identity, condition context and source context', async () => {
  const fetch = vi.fn().mockResolvedValueOnce(reply({ data: { ...road, id: 'wrong' }, meta })).mockResolvedValueOnce(reply({ data: [], meta: { ...meta, snapshot_id: 'wrong' } })).mockResolvedValueOnce(reply({ data: {}, meta: { ...meta, snapshot_id: 'wrong' } })); vi.stubGlobal('fetch', fetch);
  await expect(getMunicipalRoad(sid, road.id)).rejects.toThrow('identity'); await expect(getRoadConditions(sid, road.id)).rejects.toThrow('snapshot'); await expect(getSource(sid, 'source')).rejects.toThrow('snapshot');
});
it('requires explicit official pin and bounds catalog pagination', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValueOnce(reply({ data: { mode: 'official', snapshot_id: null } })).mockResolvedValue(reply({ data: [snapshot], meta: { ...meta, next_cursor: 'repeat' } })));
  await expect(getWorkspace()).rejects.toThrow('configuration'); await expect(getSnapshots()).rejects.toThrow('pagination');
});
it('reports a sanitized API error and propagates caller cancellation', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 503, json: async () => ({ error: { message: 'Migration required', code: 'UNAVAILABLE' } }) })); await expect(readJSON('/api', '/test')).rejects.toMatchObject({ message: 'Migration required', status: 503 });
  const ac = new AbortController(); ac.abort(); vi.stubGlobal('fetch', vi.fn().mockRejectedValue(ac.signal.reason)); await expect(readJSON('/api', '/test', ac.signal)).rejects.toBe(ac.signal.reason);
});
it('rejects unaccepted road-condition links even when a latest ID is supplied', async () => {
  const { condition } = await import('../test-municipal'); vi.stubGlobal('fetch', vi.fn().mockResolvedValue(reply({ data: [condition], meta: { ...meta, latest_usable_id: condition.id } })));
  await expect(getRoadConditions(sid, road.id)).rejects.toThrow('unaccepted road link');
});

it('binds condition summaries to road, snapshot, date and explicit intelligence release', async () => {
  const { getConditionSummary } = await import('./municipal');
  const { conditionSummary } = await import('../test-municipal');
  const fetch = vi.fn().mockResolvedValueOnce(reply({data:conditionSummary,meta})).mockResolvedValueOnce(reply({data:{...conditionSummary,intelligence_release_id:'wrong'},meta})).mockResolvedValueOnce(reply({data:{...conditionSummary,as_of_date:'2025-01-01'},meta}));vi.stubGlobal('fetch',fetch);
  expect(await getConditionSummary(sid,road.id,'2026-11-01','365')).toEqual(conditionSummary);
  expect(fetch.mock.calls[0][0]).toContain('stale_after_days=365');
  await expect(getConditionSummary(sid,road.id,'2026-11-01','365',undefined,'intel-selected')).rejects.toThrow('context');
  await expect(getConditionSummary(sid,road.id,'2026-11-01','365')).rejects.toThrow('context');
});
it('rejects road colors from an unrelated policy or release context', async () => {
 const {getMunicipalPage}=await import('./municipal');const {conditionSummary}=await import('../test-municipal');
 const policy={id:'civicplain-pilot-pavement-v1.0',name:'CivicPlAIn Pilot Policy v1.0',hash:'a'.repeat(64),classification:'planning_assumption',official_nyc_dot_policy:false};
 const filters={release_id:'intel-selected',as_of_date:'2026-11-01',policy_id:policy.id};
 const summary={...conditionSummary,method_version:'road-condition-v2-pilot',intelligence_release_id:filters.release_id,category:'good',policy};
 vi.stubGlobal('fetch',vi.fn().mockResolvedValueOnce(reply({data:[{...road,condition_summary:summary}],meta})).mockResolvedValueOnce(reply({data:[{...road,condition_summary:{...summary,road_id:'wrong'}}],meta})).mockResolvedValueOnce(reply({data:[{...road,condition_summary:{...summary,policy:{...policy,official_nyc_dot_policy:true}}}],meta})));
 expect((await getMunicipalPage('road-segments',sid,filters)).data).toHaveLength(1);
 await expect(getMunicipalPage('road-segments',sid,filters)).rejects.toThrow('context');
 await expect(getMunicipalPage('road-segments',sid,filters)).rejects.toThrow('context');
});
it('rejects cross-release permit evidence and confirmed coordination claims',async()=>{
 const {getPermitCoordination}=await import('./municipal');
 vi.stubGlobal('fetch',vi.fn().mockResolvedValueOnce(reply({data:{...permit,permit_location:{snapshot_id:sid,permit_release_id:'foreign',status:'located',method_version:'permit-road-reference-v1',actual_schedule:'unknown'}},meta})).mockResolvedValueOnce(reply({data:[{snapshot_id:sid,permit_release_id:null,permit_ids:[permit.id],confirmed_conflict:true,actual_work_overlap:'unknown'}],meta})));
 await expect(getMunicipalPermit(sid,permit.id,undefined,undefined,true)).rejects.toThrow('context');
 await expect(getPermitCoordination(sid,permit.id)).rejects.toThrow('Unsupported coordination');
});
it('rejects incomplete final viewport pages instead of caching a silent omission',async()=>{
 vi.stubGlobal('fetch',vi.fn().mockResolvedValue(reply({data:[road],meta:{...meta,total_matching:2}})));
 await expect(getMunicipalViewport('roads',sid,snapshot.coverage.bbox)).rejects.toThrow('Incomplete viewport');
});
