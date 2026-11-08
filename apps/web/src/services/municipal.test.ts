import { afterEach, expect, it, vi } from 'vitest';
import { getMunicipalViewport, getMunicipalRoad, getRoadConditions, getSource, getSnapshots, getWorkspace } from './municipal';
import { readJSON } from './http';
import { sid, meta, road, snapshot } from '../test-municipal';
const reply = (data: unknown) => ({ ok: true, json: async () => data }) as Response;
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
