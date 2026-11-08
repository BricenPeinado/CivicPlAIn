import type { Bbox } from './types/municipal';
export type View = 'map' | 'dashboard' | 'projects' | 'scenarios';
export type PermitLocation = 'all' | 'matched' | 'ambiguous' | 'unmatched' | 'unlocated';
export interface Route {
  view: View; mode?: 'synthetic' | 'official'; snapshot?: string; road: string | null; error?: string;
  permit?: string; mappermit?: string; project?: string; finding?: string; analysis?: string; scenario?: string; evaluation?: string;
  mapq?: string; permitq?: string; status?: string; location?: PermitLocation;
  condition?: 'good' | 'fair' | 'poor' | 'unknown'; bbox?: Bbox; layers?: string;
}
const ids = ['permit', 'mappermit', 'project', 'finding', 'analysis', 'scenario', 'evaluation'] as const;
const texts = ['mapq', 'permitq', 'status'] as const;
const allowed = ['mode', 'snapshot', 'road', ...ids, ...texts, 'location', 'condition', 'bbox', 'layers'];
const validId = (id: string) => id.length <= 180 && /^[\w.:-]+$/.test(id);
export function parseRoute(hash: string): Route {
  const [path, query = '', extra] = hash.replace(/^#/, '').split('?');
  const view = path.replace(/^\//, '') || 'map', p = new URLSearchParams(query);
  if (!['map', 'dashboard', 'overview', 'projects', 'scenarios'].includes(view)) return { view: 'map', road: null, error: 'Page not found. Return to the map.' };
  const result: Route = { view: view === 'overview' ? 'dashboard' : view as View, road: p.get('road') || null, mode: undefined, snapshot: undefined };
  const invalid = () => ({ ...result, error: 'Invalid workspace link. Select a dataset or return to the map.' });
  if (extra !== undefined || [...p.keys()].some(k => !allowed.includes(k) || p.getAll(k).length !== 1 || !p.get(k))) return invalid();
  const mode = p.get('mode'), snapshot = p.get('snapshot');
  if (mode && !['official', 'synthetic'].includes(mode) || snapshot && !/^nyc-[a-f0-9]{32}$/.test(snapshot) || result.road && !validId(result.road)) return invalid();
  result.mode = mode as Route['mode'] || undefined; result.snapshot = snapshot || undefined;
  for (const key of ids) { const v = p.get(key); if (v) { if (!validId(v)) return invalid(); result[key] = v; } }
  for (const key of texts) { const v = p.get(key); if (v) { if (v.length > 100 || !v.trim() || /[\u0000-\u001f]/.test(v)) return invalid(); result[key] = v; } }
  const location = p.get('location'), condition = p.get('condition'), layers = p.get('layers'), bbox = p.get('bbox');
  if (location) { if (!['all','matched','ambiguous','unmatched','unlocated'].includes(location)) return invalid(); result.location = location as PermitLocation; }
  if (condition) { if (!['good','fair','poor','unknown'].includes(condition)) return invalid(); result.condition = condition as Route['condition']; }
  if (layers !== null) { const values = layers === 'none' ? [] : layers.split(','); if (new Set(values).size !== values.length || values.some(v => !['streets','conditions','permits','shoreline','basemap'].includes(v))) return invalid(); result.layers = layers; }
  if (bbox) { const b = bbox.split(',').map(Number); if (b.length !== 4 || bbox.split(',').some(v => !v.trim()) || !b.every(Number.isFinite) || b[0] >= b[2] || b[1] >= b[3] || b[0] < -74.06 || b[2] > -73.95 || b[1] < 40.67 || b[3] > 40.76) return invalid(); result.bbox = b as Bbox; }
  return result;
}
export function routeHref(route: Route) {
  const p = new URLSearchParams(); if (route.mode) p.set('mode', route.mode); if (route.mode === 'official' && route.snapshot) p.set('snapshot', route.snapshot); if (route.road) p.set('road', route.road);
  for (const key of [...ids, ...texts, 'location', 'condition', 'layers'] as const) if (route[key]) p.set(key, route[key]);
  if (route.bbox) p.set('bbox', route.bbox.join(','));
  return `#/${route.view}${p.size ? `?${p}` : ''}`;
}
