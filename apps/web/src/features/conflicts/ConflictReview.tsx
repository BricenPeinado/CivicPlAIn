import type { ConflictAnalysis, ConflictFinding, InfrastructureCategory, WorkProject } from '../../types/api';
import { infrastructureCategories } from '../../types/api';

export const categoryColors: Record<InfrastructureCategory, string> = {
  water: '#2378a5', sewer: '#756043', gas: '#a56c05', electric: '#95559d', telecommunications: '#5d658f',
  road_resurfacing: '#25664d', road_reconstruction: '#993e34', other: '#55616c',
};
const label = (s: string) => s.replaceAll('_', ' ');
export const findingLabels: Record<ConflictFinding['finding_type'], string> = {
  concurrent_work: 'Concurrent work', reopening_risk: 'Potential pavement rework', multiple_closures: 'Multiple corridor closures', sequencing_review: 'Sequencing review',
};
interface Props {
  projects: WorkProject[]; analysis: ConflictAnalysis | null; loading: boolean; error: string; reload: () => void;
  selectedRoad: string | null; selectedProject: string | null; selectedFinding: string | null;
  onProject: (id: string) => void; onFinding: (id: string) => void; onAll: () => void;
  showProjects: boolean; setShowProjects: (value: boolean) => void;
  visibleCategories: InfrastructureCategory[]; setVisibleCategories: (value: InfrastructureCategory[]) => void;
}
export function ConflictReview(props: Props) {
  const { projects, analysis, selectedRoad, selectedProject, selectedFinding } = props;
  const project = projects.find(p => p.id === selectedProject);
  const inScope = (projectIds: string[], roadIds: string[]) => selectedProject ? projectIds.includes(selectedProject) : selectedRoad ? roadIds.includes(selectedRoad) : true;
  const findings = (analysis?.findings || []).filter(f => inScope(f.project_ids, f.affected_road_ids));
  const unknowns = (analysis?.indeterminate_checks || []).filter(c => inScope(c.project_ids, [...c.spatial_evidence.shared_road_ids, ...c.spatial_evidence.shared_corridor_ids, ...projects.filter(p => c.project_ids.includes(p.id)).flatMap(p => p.road_segment_ids)]));
  const selected = findings.find(f => f.id === selectedFinding);
  const name = (id: string) => projects.find(p => p.id === id)?.title || id;
  return <section className="coordination-card" aria-label="Project coordination and conflict review">
    <div className="list-heading"><div><p className="eyebrow">M3 · DETERMINISTIC SCREENING</p><h2>Project coordination</h2></div><span className="demo-badge">FICTIONAL DEMO PROJECTS</span></div>
    <p className="coverage-note"><strong>Human coordination review required.</strong> Findings are screening signals, not final engineering determinations. Utility coverage is unknown; an empty result never establishes excavation safety.</p>
    {props.loading ? <p role="status">Loading projects and analyzing supplied evidence…</p> : props.error ? <div role="alert"><p>Project analysis unavailable. {props.error}</p><button onClick={props.reload}>Retry project analysis</button></div> : <>
      <fieldset className="project-layers"><legend>Work-zone map layers</legend>
        <label><input type="checkbox" checked={props.showProjects} onChange={e => props.setShowProjects(e.target.checked)}/>Show project work zones</label>
        {infrastructureCategories.filter(c => projects.some(p => p.infrastructure_category === c)).map(c => <label key={c}><input type="checkbox" checked={props.visibleCategories.includes(c)} onChange={e => props.setVisibleCategories(e.target.checked ? [...props.visibleCategories, c] : props.visibleCategories.filter(v => v !== c))}/><i style={{ background: categoryColors[c] }}/>{label(c)}</label>)}
      </fieldset>
      <p className="subtle">Approximate work zones have dashed outlines. Selected projects and finding work zones receive a thick outline. Records without geometry remain in this list.</p>
      <div className="coordination-grid"><div><h3>Work projects ({projects.length})</h3>
        <div className="project-list" aria-label="Selectable work projects">{projects.map(p => <button key={p.id} aria-pressed={p.id === selectedProject} className={p.id === selectedProject ? 'project-row selected' : 'project-row'} onClick={() => props.onProject(p.id)}>
          <strong>{p.title}</strong><span>{label(p.infrastructure_category)} · {label(p.work_type)} · {label(p.schedule_status)}</span>
          <span>[{p.start_date || '?'} → {p.end_date || '?'}) · {p.road_segment_ids.join(', ') || 'Roads unknown'}</span>
          <span>{p.data_kind === 'synthetic' ? 'SYNTHETIC' : 'Source-reported'} · {label(p.location_status)} location{(!p.geometry || !p.start_date || !p.end_date) && ' · ⚠ Incomplete evidence'}</span>
        </button>)}</div>
        {!projects.length && <p>No project records loaded. Utility coverage remains unknown.</p>}
        {project && <article className="project-detail" aria-label="Selected project details"><h3>{project.title}</h3><p>{project.description}</p><dl className="metadata">
          <div><dt>Organization</dt><dd>{project.responsible_organization || 'Unknown'}</dd></div>
          <div><dt>Schedule source</dt><dd>{label(project.schedule_basis)}</dd></div><div><dt>Actual dates</dt><dd>{project.actual_start_date || '?'} → {project.actual_end_date || '?'}</dd></div>
          <div><dt>Location</dt><dd>{label(project.location_status)}; no depth or measurement accuracy established</dd></div>
          <div><dt>Excavation / lane closures</dt><dd>{project.excavation_required === null ? 'Unknown' : project.excavation_required ? 'Potential excavation' : 'No excavation in supplied scope'} / {project.lanes_closed ?? 'Unknown'}</dd></div>
          <div><dt>Project estimate</dt><dd>{project.estimated_cost_usd === null ? 'Unknown; no loss or savings calculated' : `${project.estimated_cost_usd} USD (source estimate)`}</dd></div></dl>
          <ul>{Object.entries(project.unknown_reasons).map(([key, reason]) => <li key={key}>⚠ {label(key)}: {label(reason)}</li>)}</ul><p>Sources: {project.evidence_ids.join(', ')}</p>
          <ul>{project.limitations.map(item => <li key={item}>{item}</li>)}</ul>
        </article>}
      </div><div className="conflict-review" aria-label="Conflict review panel"><div className="list-heading"><h3>Review findings ({findings.length})</h3><button className="text-button" onClick={props.onAll}>Show all conflicts</button></div>
        <p>Scope: {selectedProject ? name(selectedProject) : selectedRoad || 'All supplied projects'}. Layer visibility changes the map only.</p>
        {analysis && <p className="subtle">{analysis.checked_pair_count} indexed candidate pairs / {analysis.possible_pair_count} possible pairs · {analysis.parameters.proximity_m} m proximity · {analysis.parameters.corridor_m} m centerline corridor · {analysis.parameters.reopening_horizon_days} day sequencing window.</p>}
        <div className="finding-list">{findings.map(f => <button key={f.id} aria-pressed={f.id === selectedFinding} className={f.id === selectedFinding ? 'finding-row selected' : 'finding-row'} onClick={() => props.onFinding(f.id)}>
          <strong>⚑ {findingLabels[f.finding_type]}</strong><span>Coordination review · {f.synthetic_input ? 'Synthetic inputs' : 'Source inputs'}</span><span>{f.project_ids.map(name).join(' + ')}</span>
        </button>)}</div>
        {!findings.length && <p>No conflicts detected in the checked records for this selection; utility coverage may be incomplete.</p>}
        {selected && <article className="finding-detail" aria-label="Selected conflict evidence"><h3>{findingLabels[selected.finding_type]}</h3><p>{selected.explanation}</p>
          <p><strong>Priority:</strong> Coordination review; no validated safety assessment.</p><p><strong>Affected roads:</strong> {selected.affected_road_ids.join(', ') || 'Unresolved'}</p>
          <h4>Computed spatial evidence</h4><p>{selected.spatial_evidence.classifications.map(label).join(' · ')}</p><p>Footprint distance: {selected.spatial_evidence.distance_m === null ? 'Unknown' : `${selected.spatial_evidence.distance_m.toFixed(2)} m (computed; accuracy unverified)`}. Polygon area overlap: {selected.spatial_evidence.polygon_overlap ? 'Yes, in supplied geometry' : 'No'}.</p>
          <p>Shared roads: {selected.spatial_evidence.shared_road_ids.join(', ') || 'None declared'}. Screened corridors: {selected.spatial_evidence.shared_corridor_ids.join(', ') || 'None'}.</p><p>{selected.spatial_evidence.basis}</p>
          <h4>Schedule evidence</h4><ul>{Object.entries(selected.temporal_evidence.intervals).map(([id, dates]) => <li key={id}>{name(id)}: [{dates[0] || '?'} → {dates[1] || '?'}) · {selected.temporal_evidence.interval_basis[id]}</li>)}</ul>
          {selected.temporal_evidence.overlap_start && <p>Computed overlap: [{selected.temporal_evidence.overlap_start} → {selected.temporal_evidence.overlap_end})</p>}
          {selected.temporal_evidence.gap_days !== null && <p>Sequential gap: {selected.temporal_evidence.gap_days} calendar days.</p>}<p>{selected.temporal_evidence.basis}</p>
          <h4>Required human review</h4><ul>{selected.required_review.map(r => <li key={r}>{r}</li>)}</ul><h4>Uncertainty and unverified assumptions</h4><ul>{selected.data_quality_warnings.map(w => <li key={w}>⚠ {w}</li>)}</ul>
          <p>Sources: {selected.evidence_ids.join(', ')}</p><p className="checksum">Finding: {selected.id}</p>
        </article>}
        <details open={unknowns.length > 0}><summary>⚠ Incomplete pair checks ({unknowns.length})</summary><ul>{unknowns.map(c => <li key={c.project_ids.join(':')}><strong>{c.project_ids.map(name).join(' + ')}</strong><p>{c.reason}</p><p>Missing: {c.missing_fields.join(', ')}</p></li>)}</ul></details>
        {analysis && <details><summary>Analysis snapshot, source data and method</summary><p>{analysis.method_version} · {analysis.detected_at}</p><p>EPSG:4326 exchange → EPSG:32618 meters. {JSON.stringify(analysis.input_snapshot.libraries)}</p><p className="checksum">Input SHA-256: {analysis.input_hash}<br/>Result SHA-256: {analysis.result_hash}</p>
          <p>Excluded cancelled records: {analysis.excluded_project_ids.join(', ') || 'None'}</p><ul>{analysis.warnings.map(w => <li key={w}>{w}</li>)}</ul>
          {analysis.input_snapshot.sources.map(s => <div key={s.id}><h4>{s.title}</h4><p>{s.id} · {s.publisher} · {s.version}</p><p>{s.uri}</p><p>{s.reliability_note}</p><p>{s.coverage_note}</p><p className="checksum">SHA-256: {s.checksum_sha256}</p></div>)}
        </details>}
      </div></div>
    </>}
  </section>;
}
