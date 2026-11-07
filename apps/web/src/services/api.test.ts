import { afterEach, expect, it, vi } from 'vitest';
import { getRoads } from './api';
import { readFileSync } from 'node:fs';
const fixture = readFileSync('../../data/demo/roads.geojson', 'utf8');
const page = { ...JSON.parse(fixture), meta: { dataset_snapshot_id: 'demo-m1-v1', next_cursor: null } };
afterEach(() => vi.unstubAllGlobals());
it('loads GeoJSON through FastAPI, not a bundled production fixture', async () => {
  const fetcher = vi.fn().mockResolvedValue({ ok: true, json: async () => page });
  vi.stubGlobal('fetch', fetcher);
  expect((await getRoads()).features).toHaveLength(24);
  expect(fetcher.mock.calls[0][0]).toBe('http://127.0.0.1:8000/api/v1/road-segments/geojson?limit=30');
});
it('rejects failed requests', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 503 }));
  await expect(getRoads()).rejects.toThrow('HTTP 503');
});
it('rejects malformed responses', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => ({ type: 'no' }) }));
  await expect(getRoads()).rejects.toThrow('unsupported road dataset');
});
it('rejects duplicate records instead of double-counting metrics', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => ({ ...page, features: [page.features[0], page.features[0]] }) }));
  await expect(getRoads()).rejects.toThrow('duplicate road IDs');
});
