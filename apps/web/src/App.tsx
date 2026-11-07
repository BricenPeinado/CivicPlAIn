import { AIAdvisor } from './features/ai/AIAdvisor';
import { ScenarioPlanner } from './features/scenarios/ScenarioPlanner';
import { RepairPlanner } from './features/estimates/RepairPlanner';
import { useEffect, useState } from 'react';
import { RoadMap, colors } from './features/map/RoadMap';
import { getEvidence, getRoad, getRoads } from './services/api';
import { categories, summarize, type Evidence, type Road, type RoadsCollection } from './types/api';
import { infrastructureCategories, type InfrastructureCategory } from './types/api';
import { ConflictReview } from './features/conflicts/ConflictReview';
import { useConflicts } from './features/conflicts/useConflicts';

function Glyph({ kind }: { kind: 'map' | 'grid' | 'layers' | 'road' }) {
  return <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" aria-hidden="true">
    {kind === 'map' ? <><path d="m3 5 6-2 6 2 6-2v16l-6 2-6-2-6 2Z"/><path d="M9 3v16M15 5v16"/></> :
      kind === 'grid' ? <><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></> :
      kind === 'road' ? <><path d="M7 3 4 21M17 3l3 18M12 3v4m0 3v4m0 3v4"/></> :
        <><path d="m3 8 9-5 9 5-9 5Zm0 5 9 5 9-5M3 18l9 5 9-5"/></>}
  </svg>;
}
const title = (value: string) => value.charAt(0).toUpperCase() + value.slice(1);
function Condition({ category }: { category: keyof typeof colors }) {
  return <span className={`condition condition-${category}`}><i style={{ background: colors[category] }} />{title(category)}</span>;
}
export default function App() {
  const [roads, setRoads] = useState<RoadsCollection | null>(null);
  const [error, setError] = useState('');
  const [reload, setReload] = useState(0);
  const [selected, setSelected] = useState<string | null>(null);
  const [detail, setDetail] = useState<Road | null>(null);
  const [evidence, setEvidence] = useState<Evidence[]>([]);
  const [detailError, setDetailError] = useState('');
  const [detailRetry, setDetailRetry] = useState(0);
  const [query, setQuery] = useState('');
  const [plannerOpen, setPlannerOpen] = useState(false);
  const [view, setView] = useState<'map' | 'dashboard'>('map');
  const coordination = useConflicts(roads);
  const [selectedProject, setSelectedProject] = useState<string | null>(null);
  const [selectedFinding, setSelectedFinding] = useState<string | null>(null);
  const [showProjects, setShowProjects] = useState(true);
  const [visibleCategories, setVisibleCategories] = useState<InfrastructureCategory[]>([...infrastructureCategories]);
  const chooseRoad = (id: string) => { setSelected(id); setSelectedProject(null); setSelectedFinding(null); };
  const chooseProject = (id: string) => { setSelectedProject(id); setSelectedFinding(null); };
  const highlighted = coordination.analysis?.findings.find(f => f.id === selectedFinding);
  useEffect(() => { setSelectedProject(null); setSelectedFinding(null); }, [coordination.analysis]);
  useEffect(() => {
    const controller = new AbortController();
    setRoads(null); setError(''); setSelected(null);
    getRoads(controller.signal).then(setRoads).catch(e => {
      if (!controller.signal.aborted) setError(e.message);
    });
    return () => controller.abort();
  }, [reload]);
  useEffect(() => {
    const controller = new AbortController();
    setDetail(null); setEvidence([]); setDetailError('');
    if (selected && roads) {
      getRoad(selected, controller.signal).then(async result => {
        if (result.data.id !== selected || result.meta.dataset_snapshot_id !== roads.meta.dataset_snapshot_id) {
          throw new Error('The road snapshot changed. Reload the workspace.');
        }
        if (!controller.signal.aborted) setDetail(result.data);
        const sources = await Promise.all(result.data.evidence_ids.map(id => getEvidence(id, controller.signal)));
        if (!controller.signal.aborted) setEvidence(sources.map(source => source.data));
      }).catch(e => { if (!controller.signal.aborted) setDetailError(e.message); });
    }
    return () => controller.abort();
  }, [selected, roads, detailRetry]);
  const counts = summarize(roads?.features || []);
  const filtered = (roads?.features || []).filter(f => `${f.properties.name} ${f.properties.id}`.toLowerCase().includes(query.toLowerCase()));
  return <div className="app-shell">
    <aside className="sidebar">
      <a href="#workspace" className="brand" aria-label="CivicPlAIn workspace"><span className="brand-mark"><Glyph kind="road"/></span><span>Civic<span className="brand-ai">PlAIn</span><small>INFRASTRUCTURE INTELLIGENCE</small></span></a>
      <div className="workspace-switch"><span className="workspace-avatar">LM</span><span>Local workspace<small>Lower Manhattan</small></span><span className="local-dot" /></div>
      <p className="nav-label">WORKSPACE</p>
      <nav aria-label="Workspace navigation">
        <button className={view === 'dashboard' ? 'nav-item active' : 'nav-item'} onClick={() => setView('dashboard')}><Glyph kind="grid"/>Dashboard</button>
        <button className={view === 'map' ? 'nav-item active' : 'nav-item'} onClick={() => setView('map')}><Glyph kind="map"/>Infrastructure map</button>
        <a className="nav-item" href="#coordination"><Glyph kind="layers"/>Project coordination</a>
        <button className={plannerOpen ? "nav-item active" : "nav-item"} onClick={() => { setPlannerOpen(v => !v); }}><Glyph kind="road"/>Scenario planner</button>
        <div className="nav-item unavailable"><span aria-hidden="true">⚙</span>Settings <small>SOON</small></div>
      </nav>
      <div className="sidebar-bottom"><span className="outline-label">MILESTONE 05</span><h3>Coordinate with evidence.</h3><p>Inspect work zones, schedules and uncertainty before human review.</p><div className="sidebar-foot">LOCAL DEVELOPMENT <span>v0.1</span></div></div>
    </aside>
    <div className="workspace" id="workspace">
      <header className="topbar"><div><span className="breadcrumb">Workspace</span><span className="slash">/</span><strong>Lower Manhattan</strong></div><div className="source-status"><span className={error ? 'status-dot error-dot' : 'status-dot'} />{error ? 'API unavailable' : roads ? 'Local snapshot loaded' : 'Connecting to local API'}</div></header>
      <main>
        <div className="page-heading"><div><p className="eyebrow">ROAD ASSET WORKSPACE</p><h1>{view === 'map' ? 'Infrastructure map' : 'Dataset overview'}</h1><p>Explore the study area. Inspect the evidence behind every segment.</p></div><span className="demo-badge">DEMO DATA</span></div>
        <div className="demo-notice"><span aria-hidden="true">ⓘ</span><p><strong>A schematic, not a street survey.</strong> All road geometries and conditions are synthetic. No NYC municipal observations are displayed.</p></div>
        <section className="summary-grid" aria-label="Loaded dataset summary">
          <article className="summary-total"><div className="metric-label">Road segments <Glyph kind="road"/></div><strong>{roads ? roads.features.length : '—'}</strong><small>In the loaded snapshot</small></article>
          {categories.map(category => <article key={category}><div className="metric-label"><span className="metric-dot" style={{ background: colors[category] }}/>{title(category)}</div><strong>{roads ? counts[category] : '—'}</strong><small>{category === 'unknown' ? 'No demo assessment' : 'Synthetic condition'}</small></article>)}
        </section>
        {error ? <section className="state-card" role="alert"><h2>Unable to load road data</h2><p>{error}</p><p>Start the local API and check its configured address, then try again.</p><button className="primary-button" onClick={() => setReload(v => v + 1)}>Retry connection</button></section> : !roads ? <section className="state-card" role="status"><span className="loading-ring"/><h2>Loading the study area</h2><p>Fetching road geometry and provenance from the local API…</p></section> : roads.features.length === 0 ? <section className="state-card"><h2>No road segments loaded</h2><p>The API is connected. Seed the local demonstration database to explore synthetic roads.</p><button className="primary-button" onClick={() => setReload(v => v + 1)}>Reload dataset</button></section> : <>
          {plannerOpen && <ScenarioPlanner roads={roads} selectedRoad={selected} projects={coordination.projects}/>}
          <div className="explorer-grid">
            <section className="map-card"><div className="card-heading"><div><Glyph kind="map"/><h2>{view === 'map' ? 'Study area' : 'Study area preview'}</h2><span className="quiet-tag">Lower Manhattan, NYC</span></div><span className="subtle">{roads.features.length} segments</span></div>
              <RoadMap roads={roads} selectedId={selected} onSelect={chooseRoad} projects={coordination.projects}
                onSelectProject={chooseProject} showProjects={showProjects} visibleCategories={visibleCategories}
                highlightedProjects={highlighted?.project_ids || (selectedProject ? [selectedProject] : [])}
                highlightedRoads={highlighted?.affected_road_ids || []}/>
              <div className="legend" aria-label="Road condition legend"><strong>DEMO CONDITION</strong>{categories.map(category => <span key={category}><i style={{ background: colors[category] }}/>{title(category)}</span>)}</div>
            </section>
            <aside className="detail-card" aria-label="Road details"><div className="card-heading"><h2>Segment details</h2><span className="subtle">{selected ? '01 selected' : 'No selection'}</span></div>
              {!selected ? <div className="detail-empty"><span className="empty-icon"><Glyph kind="road"/></span><h3>A closer look starts here</h3><p>Select a segment on the map or in the road list to inspect its condition and source.</p><span className="small-label">MAP + KEYBOARD ROAD LIST</span></div> : <div className="detail-content" aria-live="polite">
                <span className="small-label">{selected}</span>
                {detail ? <><h3>{detail.name || 'Unnamed segment'}</h3><div className="detail-badges"><Condition category={detail.condition_summary.category}/><span className="demo-badge">SYNTHETIC</span></div>
                  <dl className="metadata"><div><dt>Condition score</dt><dd>{detail.condition_summary.rating ? `${detail.condition_summary.rating} / 10 (demo)` : 'Unknown'}</dd></div><div><dt>Last assessed</dt><dd>{detail.condition_summary.assessed_on || 'Unknown'}</dd></div><div><dt>Length / width</dt><dd>{detail.length_m ? `${detail.length_m} m` : 'Unknown'} / {detail.width_m ? `${detail.width_m} m` : 'Unknown'}</dd></div><div><dt>Repairable area</dt><dd>{detail.repairable_area_m2 ? `${detail.repairable_area_m2} m² (length × width)` : 'Unknown'}</dd></div><div><dt>Dimension provenance</dt><dd>{Object.values(detail.dimension_basis || {}).length ? [...new Set(Object.values(detail.dimension_basis || {}))].join(', ').replaceAll('_', ' ') : 'Unknown'}</dd></div><div><dt>Surface / classification</dt><dd>{detail.surface_material || 'unknown'} / {detail.functional_class || 'unknown'}</dd></div><div><dt>Utility coverage</dt><dd>Unknown</dd></div><div><dt>Snapshot</dt><dd>{detail.dataset_snapshot_id}</dd></div></dl>
                  <div className="provenance"><p className="eyebrow">DATA PROVENANCE</p>{evidence.length ? evidence.map(source => <div key={source.id}><h4>{source.title}</h4><p>{source.publisher} · {source.version}</p><p>{source.reliability_note}</p><details><summary>Source and record limitations</summary><p>Repository source: {source.uri}</p><p>CRS: {source.original_crs}</p><p>{source.coverage_note}</p><p>{source.license_note}</p><p className="checksum">SHA-256: {source.checksum_sha256}</p><ul>{detail.limitations.map(item => <li key={item}>{item}</li>)}</ul></details></div>) : !detailError && <p role="status">Loading source evidence…</p>}</div>
                  <p>{detail.notes}</p><AIAdvisor context={{ type: 'road', record_ids: [detail.id] }} label="Explain this road"/></> : !detailError && <p role="status">Loading segment details…</p>}
                {detailError && <div role="alert"><p>Details or source evidence unavailable. {detailError}</p><button className="text-button" onClick={() => setDetailRetry(v => v + 1)}>Retry details</button></div>}
              </div>}
              <div className="coverage-note"><strong>Utility information is unknown.</strong><p>This map does not establish excavation safety or authorize work.</p></div>
            </aside>
          </div>
          <div id="coordination"><ConflictReview {...coordination} selectedRoad={selected} selectedProject={selectedProject}
            selectedFinding={selectedFinding} onProject={chooseProject} onFinding={setSelectedFinding}
            onAll={() => { setSelected(null); setSelectedProject(null); setSelectedFinding(null); }}
            showProjects={showProjects} setShowProjects={setShowProjects} visibleCategories={visibleCategories} setVisibleCategories={setVisibleCategories}/></div>
          {detail && <RepairPlanner key={detail.id} road={detail}/>}
          <section className="road-list-card" aria-label="Keyboard accessible road list"><div className="list-heading"><div><p className="eyebrow">EXPLORE THE SNAPSHOT</p><h2>Road segments <span>{filtered.length}</span></h2></div><label className="search-box"><span aria-hidden="true">⌕</span><input aria-label="Find road segments" placeholder="Find a segment by name or ID" value={query} onChange={e => setQuery(e.target.value)}/></label></div>
            <div className="road-list">{filtered.map(f => <button key={f.properties.id} className={selected === f.properties.id ? 'road-row selected' : 'road-row'} aria-pressed={selected === f.properties.id} onClick={() => chooseRoad(f.properties.id)}><span className="road-row-icon"><Glyph kind="road"/></span><span className="road-row-name"><strong>{f.properties.name || f.properties.id}</strong><small>{f.properties.id} · Synthetic geometry</small></span><Condition category={f.properties.condition_summary.category}/><span className="row-arrow" aria-hidden="true">↗</span></button>)}</div>
            {filtered.length === 0 && <p className="search-empty">No segments match this search.</p>}
          </section>
        </>}
        <footer className="workspace-footer"><span>CivicPlAIn <span className="footer-dot">·</span> Local decision-support prototype</span><span>{roads?.meta.dataset_snapshot_id || 'No snapshot'} <span className="footer-dot">·</span> Human review required</span></footer>
      </main>
    </div>
  </div>;
}
