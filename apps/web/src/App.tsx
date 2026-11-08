import {DecisionContext} from './features/decisions/DecisionContext';
import { useEffect, useRef, useState } from 'react';
import { DataTerms } from './components/DataTerms';
import { Icon } from './components/Icon';
import { FeatureBoundary } from './components/FeatureBoundary';
import { getWorkspace, getSnapshots, getSnapshot } from './services/municipal';
import type { Snapshot, Workspace } from './types/municipal';
import { parseRoute, routeHref, type Route, type View } from './routing';
import { OfficialMapPage } from './pages/OfficialMapPage';
import { OfficialOverview, OfficialPermits } from './pages/OfficialRecordsPage';
import { SyntheticWorkspace } from './pages/SyntheticWorkspace';
const names: Record<View, string> = { map: 'Infrastructure map', dashboard: 'Overview', projects: 'Projects & coordination', scenarios: 'Scenario planner' };
export default function App() {
  const [route, setRoute] = useState(() => parseRoute(window.location.hash));
  const [config, setConfig] = useState<Workspace | null>(null), [catalog, setCatalog] = useState<Snapshot[]>([]), [snapshot, setSnapshot] = useState<Snapshot | null>(null);
  const [error, setError] = useState(''), [catalogError, setCatalogError] = useState(''), [retry, setRetry] = useState(0), [snapshotError, setSnapshotError] = useState('');
  const [syntheticVisited, setSyntheticVisited] = useState(route.mode === 'synthetic');
  const [syntheticRoad, setSyntheticRoad] = useState<string | null>(route.mode === 'synthetic' ? route.road : null);
  const heading = useRef<HTMLDivElement>(null);
  const contexts = useRef<Record<string, Route>>({});
  const mode = route.mode || config?.mode;
  const pin = route.snapshot || (config?.mode === 'official' ? config.snapshot_id : null);
  useEffect(() => { const listener = () => setRoute(parseRoute(window.location.hash)); window.addEventListener('hashchange', listener); return () => window.removeEventListener('hashchange', listener); }, []);
  useEffect(() => {
    const ac = new AbortController(); setError(''); setCatalogError('');
    getWorkspace(ac.signal).then(c => { if (!ac.signal.aborted) setConfig(c); }).catch(e => { if (!ac.signal.aborted) setError(e.message); });
    getSnapshots(ac.signal).then(c => { if (!ac.signal.aborted) setCatalog(c); }).catch(e => { if (!ac.signal.aborted) setCatalogError(e.message); });
    return () => ac.abort();
  }, [retry]);
  useEffect(() => { if (mode === 'synthetic') { setSyntheticVisited(true); setSyntheticRoad(route.road); } }, [mode, route.road]);
  useEffect(() => { const ac = new AbortController(); setSnapshot(null); setSnapshotError(''); if (mode === 'official' && pin) getSnapshot(pin, ac.signal).then(s => { if (!ac.signal.aborted) setSnapshot(s); }).catch(e => { if (!ac.signal.aborted) setSnapshotError(e.message); }); return () => ac.abort(); }, [mode, pin, retry]);
  useEffect(() => { heading.current?.focus(); }, [route.view, mode]);
  useEffect(() => { if (mode && !route.error) contexts.current[`${mode}:${mode === 'official' ? pin || '' : ''}`] = { ...route, mode, snapshot: mode === 'official' ? pin || undefined : undefined }; }, [route, mode, pin]);
  function navigate(next: Route, replace = false) { const href = routeHref(next); if (replace) window.history.replaceState(null, '', href); else if (window.location.hash !== href) window.location.hash = href; setRoute(next); }
  function patchRoute(patch: Partial<Route>, replace = false) { navigate({ ...route, mode, snapshot: pin || undefined, ...patch }, replace); }
  function changeMode(next: string) { const id = next === 'official' ? pin || catalog[0]?.id : undefined; navigate({ ...(contexts.current[`${next}:${id || ''}`] || { road: next === 'synthetic' ? syntheticRoad : null }), view: route.view, mode: next as Route['mode'], snapshot: id }); }
  function changeSnapshot(id: string) { navigate({ ...(contexts.current[`official:${id}`] || { road: null }), view: route.view, mode: 'official', snapshot: id }); }
  return <div className="app-shell"><a className="skip-link" href="#main-content" onClick={e => { e.preventDefault(); heading.current?.focus(); }}>Skip to workspace</a>
    <aside className="sidebar"><a className="brand" href={routeHref({ ...route, view: 'map' })} aria-label="CivicPlAIn map"><span className="brand-mark"><Icon name="road"/></span><span>Civic<span>PlAIn</span></span></a><nav aria-label="Workspace navigation">{(Object.keys(names) as View[]).map(view => <a key={view} className={route.view === view ? 'nav-item active' : 'nav-item'} href={routeHref({ ...route, view, mode, snapshot: pin || undefined })} aria-current={route.view === view ? 'page' : undefined}><Icon name={view}/><span>{names[view]}</span></a>)}</nav><span className="nav-foot">Evidence<br/>before action.</span></aside>
    <div className="workspace"><header className="topbar"><div className="workspace-name"><strong>Lower Manhattan</strong><span>New York City</span></div><div className="data-context"><label><span className="sr-only">Dataset mode</span><select aria-label="Dataset mode" value={mode || ''} onChange={e => changeMode(e.target.value)}>{!mode && <option value="" disabled>Select data</option>}<option value="official">Official NYC snapshot</option><option value="synthetic">Synthetic fixtures</option></select></label>{mode === 'official' && <label><span className="sr-only">Official snapshot</span><select aria-label="Official snapshot" value={pin || ''} onChange={e => changeSnapshot(e.target.value)}><option value="" disabled>Choose snapshot</option>{pin && !catalog.some(s => s.id === pin) && <option value={pin}>{pin}</option>}{catalog.map(s => <option value={s.id} key={s.id}>{s.published_at.slice(0, 10)} · {s.id.slice(0, 12)}</option>)}</select></label>}<span className="context-unknown">Utilities unknown</span></div></header>
      <main id="main-content" ref={heading} tabIndex={-1} aria-label={`${names[route.view]} workspace`}>
        {route.error && <section className="state-card" role="alert"><h1>{route.error}</h1><button onClick={() => navigate({ view: 'map', mode, snapshot: pin || undefined, road: null })}>Return to map</button></section>}<>
          {!mode && <section className="state-card" role={error ? 'alert' : 'status'}><h1>{error ? 'Workspace configuration unavailable' : 'Connecting to workspace'}</h1><p>{error || 'Reading the explicit data configuration…'}</p>{error && <><button onClick={() => setRetry(v => v + 1)}>Retry connection</button><button onClick={() => changeMode('synthetic')}>Open synthetic fixtures</button></>}</section>}
          <div hidden={!!route.error || mode !== 'synthetic'} className="workspace-content">{syntheticVisited && <FeatureBoundary name="Synthetic workspace"><SyntheticWorkspace route={route.mode === 'official' ? contexts.current['synthetic:'] : route} onRoute={(patch, replace) => { if (mode === 'synthetic') patchRoute(patch, replace); else contexts.current['synthetic:'] = { ...(contexts.current['synthetic:'] || { view: 'scenarios', mode: 'synthetic', road: syntheticRoad }), ...patch }; }} view={mode === 'synthetic' ? route.view : contexts.current['synthetic:']?.view || 'map'} onView={view => navigate({ ...route, mode: 'synthetic', view, road: syntheticRoad })} selected={syntheticRoad} onSelect={id => { setSyntheticRoad(id); navigate({ ...route, mode: 'synthetic', road: id, project: undefined, finding: undefined }); }}/></FeatureBoundary>}</div>
          {!route.error && mode === 'official' && <div className="workspace-content">{snapshotError || !pin ? <section className="state-card" role="alert"><h1>Official data unavailable</h1><p>{snapshotError || catalogError || 'Select an available published snapshot. No synthetic records have been substituted.'}</p><button onClick={() => setRetry(v => v + 1)}>Retry official data</button><button onClick={() => changeMode('synthetic')}>Open synthetic fixtures</button></section> : !snapshot ? <p className="state-card" role="status">Loading official snapshot…</p> : <FeatureBoundary key={snapshot.id} name="Official workspace">{route.view === 'map' ? <OfficialMapPage route={route} onRoute={patchRoute} snapshot={snapshot} onSynthetic={() => changeMode('synthetic')} selected={route.road} onSelect={id => navigate({ ...route, mode: 'official', snapshot: snapshot.id, road: id, mappermit: undefined })} onProjects={() => navigate({ ...route, view: 'projects', mode: 'official', snapshot: snapshot.id, road: null })}/> : route.view === 'dashboard' ? <OfficialOverview snapshot={snapshot} route={route} onRoute={patchRoute}/> : route.view === 'projects' ? <OfficialPermits snapshot={snapshot} route={route} onRoute={patchRoute}/> : <section className="page-scroll"><div className="page-title"><h1>Official planning comparisons</h1><p>Compare treatments, policy sensitivities and schedule alternatives within explicitly selected frozen results. General official scenario evaluation remains unavailable; no synthetic prices or projects are substituted.</p></div><DecisionContext snapshot={snapshot} route={route} onRoute={patchRoute}/><button onClick={() => changeMode('synthetic')}>Open synthetic scenario planner</button></section>}</FeatureBoundary>}</div>}
        </>
      </main><footer className="global-footer"><span>{mode === 'official' ? snapshot ? `Official NYC snapshot · Published ${snapshot.published_at.slice(0,10)}` : 'No official snapshot selected' : mode === 'synthetic' ? 'Synthetic fixtures · Not municipal observations' : 'No dataset selected'}</span><span className="footer-coverage">Utilities unknown · Human review required</span>{mode === 'official' && <DataTerms/>}</footer>
    </div>
  </div>;
}
