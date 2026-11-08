export type View = 'map' | 'dashboard' | 'projects' | 'scenarios';
export interface Route { view: View; mode?: 'synthetic' | 'official'; snapshot?: string; road: string | null; error?: string }
export function parseRoute(hash: string): Route {
  const [path, query = ''] = hash.replace(/^#/, '').split('?');
  const view = path.replace(/^\//, '') || 'map', p = new URLSearchParams(query);
  if (!['map', 'dashboard', 'projects', 'scenarios'].includes(view)) return { view: 'map', road: null, error: 'Page not found. Return to the map.' };
  if ([...p.keys()].some(k => !['mode', 'snapshot', 'road'].includes(k) || p.getAll(k).length !== 1)) return { view: view as View, road: null, error: 'Unsupported or repeated workspace parameter.' };
  const mode = p.get('mode'), snapshot = p.get('snapshot'), road = p.get('road');
  if (mode && !['official', 'synthetic'].includes(mode) || snapshot && !/^nyc-[a-f0-9]{32}$/.test(snapshot) || road && (road.length > 180 || !/^[\w.:-]+$/.test(road))) return { view: view as View, road: null, error: 'Invalid workspace link. Select a dataset to continue.' };
  return { view: view as View, mode: mode as Route['mode'] || undefined, snapshot: snapshot || undefined, road: road || null };
}
export function routeHref(route: Route) {
  const p = new URLSearchParams(); if (route.mode) p.set('mode', route.mode); if (route.mode === 'official' && route.snapshot) p.set('snapshot', route.snapshot); if (route.road) p.set('road', route.road);
  return `#/${route.view}${p.size ? `?${p}` : ''}`;
}
