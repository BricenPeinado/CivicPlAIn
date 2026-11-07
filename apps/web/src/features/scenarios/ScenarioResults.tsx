import type { ScenarioEvaluation, ScenarioComparison } from '../../types/scenarios';
export const usd = (value: string | null | undefined) => value == null ? 'Unknown' : new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(Number(value));
const val = (value: number | null) => value == null ? 'Unknown' : value;
export function ScenarioResults({ evaluation: e }: { evaluation: ScenarioEvaluation }) {
  const analysis = e.conflict_screen.analysis;
  return <section className="scenario-result" aria-label="Scenario evaluation">
    <div className="list-heading"><div><p className="eyebrow">IMMUTABLE EVALUATION · REVISION {e.scenario_revision}</p><h3>{e.input_snapshot.scenario.name}</h3></div><span className="demo-badge">HYPOTHETICAL · SYNTHETIC</span></div>
    <div className="scenario-metrics"><article><span>Base estimate</span><strong>{usd(e.cost_total_usd?.base)}</strong><small>Low {usd(e.cost_total_usd?.low)} / high {usd(e.cost_total_usd?.high)}</small></article>
      <article><span>Base budget headroom</span><strong>{usd(e.budget_headroom_usd?.base)}</strong><small>Budget {usd(e.budget_usd)}</small></article>
      <article><span>Budget feasibility</span><strong>{e.budget_status.replaceAll('_',' ')}</strong><small>High sensitivity within budget: {e.upper_bound_within_budget == null ? 'Unknown' : e.upper_bound_within_budget ? 'Yes' : 'No'}</small></article></div>
    {!e.cost_total_usd && <p className="coverage-note">Complete total unavailable. Known components: {usd(e.known_subtotal_usd.base)}. Missing costs are not zero.</p>}
    <p>Low / high headroom: {usd(e.budget_headroom_usd?.low)} / {usd(e.budget_headroom_usd?.high)}. Sensitivity ranges are assumptions, not probabilities.</p>
    <dl className="scenario-facts"><div><dt>Preliminary days, summed allowances</dt><dd>{val(e.preliminary_days_sum)}</dd></div><div><dt>Supplied calendar span (days)</dt><dd>{val(e.elapsed_days)}</dd></div><div><dt>Scheduled road-workdays, action envelopes</dt><dd>{val(e.scheduled_road_workdays)}</dd></div><div><dt>Lane-closure-days, declared intervals</dt><dd>{val(e.lane_closure_days)}</dd></div><div><dt>Overlapping closure interval pairs</dt><dd>{val(e.overlapping_closure_pairs)}</dd></div><div><dt>Affected roads</dt><dd>{e.affected_road_ids.join(', ') || 'None'}</dd></div><div><dt>Utility coverage / lifespan</dt><dd>Unknown / Unknown</dd></div></dl>
    <h4>Action estimates and sources</h4>{e.action_costs.map(c => <details key={c.action_id}><summary>{c.action_id} · {c.quantity_m2 ?? 'Unknown'} m² · {usd(c.costs?.base?.total_usd)}</summary>
      {c.suitability && <p>{c.suitability.status.replaceAll('_',' ')}: {c.suitability.rationale}</p>}<ul>{c.warnings.map(w=><li key={w}>{w}</li>)}</ul>{c.unavailable_reason && <p role="note">{c.unavailable_reason}</p>}{c.duration && <p>{c.duration.active_workdays} active + {c.duration.setup_days} setup + {c.duration.curing_days} curing = {c.duration.total_preliminary_days} preliminary days. No calendar dates inferred.</p>}
      {c.costs && <div className="table-scroll"><table><thead><tr><th>Component</th><th>Low</th><th>Base</th><th>High</th></tr></thead><tbody>{c.costs.base.line_items.map((item,i) => <tr key={item.label}><th>{item.label}</th>{['low','base','high'].map(k => <td key={k}>{usd(c.costs![k].line_items[i].amount_usd)}</td>)}</tr>)}<tr><th>Contingency</th>{['low','base','high'].map(k=><td key={k}>{usd(c.costs![k].contingency_usd)}</td>)}</tr></tbody></table></div>}
      <pre>{JSON.stringify({ quantity: c.quantity_provenance, inputs: c.input_snapshot, input_hash: c.input_hash },null,2)}</pre></details>)}
    <h4>Conflict screening ({analysis?.findings.length ?? 'not run'})</h4>
    {analysis?.findings.map(f => <details key={f.id}><summary>{e.conflict_screen.finding_contexts[f.id].replaceAll('_',' ')} · {f.finding_type.replaceAll('_',' ')}</summary><p>{f.explanation}</p><p>{f.project_ids.join(' / ')}</p><pre>{JSON.stringify({ spatial: f.spatial_evidence, temporal: f.temporal_evidence, sources: f.evidence_ids, review: f.required_review },null,2)}</pre></details>)}
    {analysis && !analysis.findings.length && <p>No findings in checked records. Utility coverage remains unknown; this is not excavation clearance.</p>}
    {e.conflict_screen.not_run_reason && <p>{e.conflict_screen.not_run_reason}</p>}
    <h4>Incomplete checks ({e.indeterminate_checks.length})</h4>{e.indeterminate_checks.length ? <ul>{e.indeterminate_checks.map((c,i)=><li key={i}>{c}</li>)}</ul> : <p>No incomplete checks in supplied inputs. Utility coverage remains unknown.</p>}
    <details><summary>Assumptions, provenance and reproducibility</summary><p>Evaluated {e.evaluated_at} · {e.method_version}</p><p>Input SHA-256: {e.input_hash}</p><p>Result SHA-256: {e.result_hash}</p><p>Baseline SHA-256: {e.baseline_source_hash}</p><pre>{JSON.stringify({ assumptions: e.input_snapshot.scenario.assumptions, sources: e.input_snapshot.context.sources, versions: e.analysis_versions, originals: e.conflict_screen.original_projects, overrides: e.conflict_screen.overrides },null,2)}</pre></details>
    <ul className="scenario-warnings">{e.warnings.map(w=><li key={w}>{w}</li>)}</ul>
  </section>;
}
export function ScenarioComparisonView({ comparison: c }: { comparison: ScenarioComparison }) {
  return <section className="scenario-result" aria-label="Scenario comparison"><p className="eyebrow">DETERMINISTIC TRADEOFFS</p><h3>Compare hypothetical plans</h3><div className="table-scroll"><table><thead><tr><th>Metric</th>{c.rows.map(r=><th key={r.evaluation_id}>{r.name}<small>Revision {r.revision}</small></th>)}</tr></thead><tbody>
    {(['base','low','high'] as const).map(k=><tr key={k}><th>{k} estimate</th>{c.rows.map(r=><td key={r.evaluation_id}>{usd(r.cost_total_usd?.[k])}</td>)}</tr>)}
    <tr><th>Base budget headroom</th>{c.rows.map(r=><td key={r.evaluation_id}>{usd(r.budget_headroom_usd?.base)}</td>)}</tr>
    <tr><th>Budget feasibility</th>{c.rows.map(r=><td key={r.evaluation_id}>{r.budget_status.replaceAll('_',' ')}<small>High sensitivity: {r.upper_bound_within_budget==null?'Unknown':r.upper_bound_within_budget?'Within budget':'Over budget'}</small></td>)}</tr>
    {(['preliminary_days_sum','elapsed_days','lane_closure_days','scheduled_road_workdays','conflict_count','incomplete_checks'] as const).map(k=><tr key={k}><th>{k.replaceAll('_',' ')}</th>{c.rows.map(r=><td key={r.evaluation_id}>{r[k] ?? 'Unknown'}</td>)}</tr>)}
    <tr><th>Supplied completion</th>{c.rows.map(r=><td key={r.evaluation_id}>{r.scheduled_completion || 'Unknown'}</td>)}</tr>
    <tr><th>Cost completeness</th>{c.rows.map(r=><td key={r.evaluation_id}>{r.priced_actions} / {r.total_actions} actions priced</td>)}</tr>
    <tr><th>Roads / finding types</th>{c.rows.map(r=><td key={r.evaluation_id}>{r.affected_road_ids.join(', ')}<small>{Object.entries(r.conflict_types).map(([t,n])=>`${t.replaceAll('_',' ')}: ${n}`).join('; ') || 'No known findings'}</small></td>)}</tr>
    <tr><th>Key assumptions</th>{c.rows.map(r=><td key={r.evaluation_id}>{r.assumptions.map(a=><p key={a.id}>{a.note}</p>)}</td>)}</tr>
  </tbody></table></div><ul>{c.tradeoffs.map(t=><li key={t}>{t}</li>)}</ul>
    {c.dominance.map(d=><p key={d.dominant_evaluation_id}>{c.rows.find(r=>r.evaluation_id===d.dominant_evaluation_id)?.name} dominates {c.rows.find(r=>r.evaluation_id===d.dominated_evaluation_id)?.name} across {d.objectives.join(', ')}. {d.limitation}</p>)}
    <ul className="scenario-warnings">{c.warnings.map(w=><li key={w}>{w}</li>)}</ul><details><summary>Common comparison basis</summary><pre>{JSON.stringify(c.common_basis,null,2)}</pre><p>{c.id}</p></details></section>;
}
