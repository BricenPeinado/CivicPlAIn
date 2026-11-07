import { categories, type Envelope, type Evidence, type Road, type RoadsCollection } from '../types/api';
const base = (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1').replace(/\/$/, '');
const TIMEOUT_MS = 10000;
async function request<T>(path: string, signal?: AbortSignal): Promise<T> {
  const timeout = AbortSignal.timeout(TIMEOUT_MS);
  try {
    const response = await fetch(`${base}${path}`, { signal: signal ? AbortSignal.any([signal, timeout]) : timeout });
    if (!response.ok) throw new Error(`API returned HTTP ${response.status}.`);
    return await response.json() as T;
  } catch (error) {
    if (signal?.aborted) throw error;
    if (timeout.aborted) throw new Error('The local API took too long to respond.');
    throw new Error(error instanceof Error ? error.message : 'Unable to reach the local API.');
  }
}
export async function getRoads(signal?: AbortSignal): Promise<RoadsCollection> {
  const pages: RoadsCollection[] = [];
  const seen = new Set<string>();
  let cursor: string | null = null;
  do {
    const page: RoadsCollection = await request(`/road-segments/geojson?limit=30${cursor ? `&cursor=${encodeURIComponent(cursor)}` : ''}`, signal);
    if (page.type !== 'FeatureCollection' || !Array.isArray(page.features) || !page.meta ||
        page.features.some(f => f.geometry?.type !== 'LineString' || !f.properties?.id ||
          !categories.includes(f.properties.condition_summary?.category))) {
      throw new Error('The API returned an unsupported road dataset.');
    }
    if (pages.length && page.meta.dataset_snapshot_id !== pages[0].meta.dataset_snapshot_id) {
      throw new Error('Dataset changed while loading. Reload the workspace.');
    }
    pages.push(page);
    cursor = page.meta.next_cursor;
    if (cursor && seen.has(cursor)) throw new Error('Invalid API pagination.');
    if (cursor) seen.add(cursor);
    if (pages.flatMap(p => p.features).length > 30) throw new Error('Dataset exceeds the 30-road study limit.');
  } while (cursor);
  const result = { ...pages[0], features: pages.flatMap(p => p.features) };
  if (new Set(result.features.map(f => f.properties.id)).size !== result.features.length) {
    throw new Error('Dataset contains duplicate road IDs.');
  }
  return result;
}
export const getRoad = (id: string, signal?: AbortSignal) => request<Envelope<Road>>(`/road-segments/${encodeURIComponent(id)}`, signal);
export const getEvidence = (id: string, signal?: AbortSignal) => request<Envelope<Evidence>>(`/evidence-sources/${encodeURIComponent(id)}`, signal);
