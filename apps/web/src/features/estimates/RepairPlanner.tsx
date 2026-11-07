import { useEffect, useRef, useState } from 'react';
import { createEstimate, getAssessments, getEstimate, getRepairOptions } from '../../services/api';
import type { Assessment, Estimate, EstimateRequest, OptionComparison, Road } from '../../types/api';

const usd = (value: string) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(Number(value));
const quantity = (value: string) => new Intl.NumberFormat('en-US', { maximumFractionDigits: 3 }).format(Number(value));
const statusLabel = { candidate_requires_review: 'Candidate — requires engineering review', not_indicated: 'Not indicated by demo condition rule', requires_review: 'Requires review — incomplete evidence' };

export function RepairPlanner({ road }: { road: Road }) {
  const [open, setOpen] = useState(false);
  const [options, setOptions] = useState<OptionComparison[] | null>(null);
  const [history, setHistory] = useState<Assessment[]>([]);
  const [error, setError] = useState('');
  const [retry, setRetry] = useState(0);
  const [estimate, setEstimate] = useState<Estimate | null>(null);
  const [busy, setBusy] = useState(false);
  const [saveError, setSaveError] = useState('');
  const [length, setLength] = useState('');
  const [width, setWidth] = useState('');
  const [note, setNote] = useState('');
  const pending = useRef<AbortController | null>(null);
  useEffect(() => () => pending.current?.abort(), []);
  useEffect(() => {
    if (!open) return;
    const controller = new AbortController();
    setOptions(null); setError('');
    Promise.all([getRepairOptions(road.id, controller.signal), getAssessments(road.id, controller.signal)]).then(([choices, assessments]) => {
      if (!controller.signal.aborted) { setOptions(choices.data); setHistory(assessments.data); }
    }).catch(e => { if (!controller.signal.aborted) setError(e.message); });
    return () => controller.abort();
  }, [open, retry, road.id]);
  async function inspect(optionId: string) {
    setSaveError(''); setEstimate(null);
    if ((length || width) && (!note.trim() || [length, width].filter(Boolean).some(v => !Number.isFinite(Number(v)) || Number(v) <= 0))) {
      setSaveError('Enter positive dimensions in meters and a planning assumption note.'); return;
    }
    const body: EstimateRequest = { road_segment_id: road.id, repair_option_id: optionId, dataset_snapshot_id: road.dataset_snapshot_id };
    if (length || width) body.planning_assumptions = { ...(length ? { length_m: length } : {}), ...(width ? { width_m: width } : {}), unit: 'm', note };
    pending.current?.abort();
    const controller = new AbortController(); pending.current = controller; setBusy(true);
    try {
      const saved = await createEstimate(body, controller.signal);
      const retrieved = await getEstimate(saved.data.id, controller.signal);
      if (!controller.signal.aborted) setEstimate(retrieved.data);
    } catch (e) { if (!controller.signal.aborted) setSaveError(e instanceof Error ? e.message : 'Estimate unavailable'); }
    finally { if (!controller.signal.aborted) setBusy(false); }
  }
  return <section className="repair-planner" aria-label="Repair planning">
    <button className="primary-button" aria-expanded={open} onClick={() => setOpen(v => !v)}>Compare Repair Options</button>
    {open && <div className="repair-workspace">
      <div className="list-heading"><div><p className="eyebrow">SYNTHETIC PLANNING ESTIMATES</p><h2>Compare repairs · {road.name || road.id}</h2><p>All alternatives require engineering review. Lower cost does not establish suitability.</p></div></div>
      {error ? <div role="alert"><p>Repair options unavailable. {error}</p><button className="text-button" onClick={() => setRetry(v => v + 1)}>Retry repair options</button></div> : !options ? <p role="status">Loading repair options and assessment history…</p> : <>
        <details className="assessment-history"><summary>Condition assessment history ({history.length})</summary>
          {history.length ? <ul>{history.map(a => <li key={a.id}>{a.assessed_on || 'Undated'} · {a.rating || 'Unknown'} / 10 · {a.category} · SYNTHETIC · {a.assessment_method}<p>{a.notes}</p><small>{a.id} · Sources: {a.evidence_ids.join(', ')}</small></li>)}</ul> : <p>No assessment records available. Condition requires review.</p>}
        </details>
        <fieldset className="planning-inputs"><legend>Optional explicit planning dimensions</legend><p>Previews below use stored inputs. Entered assumptions apply when you save an estimate and are preserved in its snapshot. These are not measured values.</p>
          <label>Planning length (m)<input type="number" min="0.001" max="100000" step="any" value={length} onChange={e => setLength(e.target.value)}/></label>
          <label>Planning width (m)<input type="number" min="0.001" max="100" step="any" value={width} onChange={e => setWidth(e.target.value)}/></label>
          <label>Planning assumption note<input maxLength={1000} value={note} onChange={e => setNote(e.target.value)}/></label>
        </fieldset>
        {options.length === 0 && <p>No repair catalog loaded. Seed the reviewed M2 demo fixtures.</p>}
        <div className="repair-grid">{options.map(({ option, suitability, preview, unavailable_reason }) => <article className="repair-option" key={option.id}>
          <span className="demo-badge">SYNTHETIC COSTS</span><h3>{option.label}</h3><p>{option.description}</p><p className="suitability">⚠ {statusLabel[suitability.status]}</p><p>{suitability.rationale}</p>
          {preview ? <><strong className="repair-total">{usd(preview.scenarios.base.total_usd)}</strong><p>Low–high: {usd(preview.scenarios.low.total_usd)} – {usd(preview.scenarios.high.total_usd)}</p><p>{preview.duration.total_preliminary_days} preliminary days · {preview.duration.active_workdays} active workdays</p><p>{quantity(preview.quantity)} m² · {usd(option.unit_rates_usd.base)}/m² bundled base rate</p></> : <p className="unavailable-estimate">Estimate unavailable: {unavailable_reason}</p>}
          <p>{option.material_assumptions}</p><p>{option.sensitivity_basis}</p><p>Price basis: {option.price_basis_date}. Demonstration assumptions.</p>
          <details><summary>Scope, inputs and limitations</summary><p>{option.scope_of_work}</p><p>Activities: {option.work_activities.join(', ')}</p><p>{option.rate_inclusions}</p><p>Mobilization {usd(option.mobilization_usd)}; traffic allowance {usd(option.traffic_management_usd)}; contingency {quantity(String(Number(option.contingency_fraction) * 100))}%.</p><p>Productivity {quantity(option.productivity_per_day)} {option.productivity_unit}; setup {option.setup_days} days; curing {option.curing_days} days.</p><ul>{[...option.exclusions, ...option.limitations].map(s => <li key={s}>{s}</li>)}</ul><p>Sources: {option.evidence_ids.join(', ')}</p></details>
          <button className="primary-button" disabled={busy} onClick={() => inspect(option.id)}>Save & inspect {option.label}</button>
        </article>)}</div>
        {busy && <p role="status">Saving and retrieving immutable estimate…</p>}
        {saveError && <p role="alert">{saveError}</p>}
        {estimate && <EstimateDetail estimate={estimate}/>}
      </>}
    </div>}
  </section>;
}

export function EstimateDetail({ estimate: e }: { estimate: Estimate }) {
  const [scenario, setScenario] = useState<'low' | 'base' | 'high'>('base');
  const cost = e.scenarios[scenario];
  return <section className="estimate-detail" aria-label="Estimate breakdown">
    <p className="eyebrow">SAVED SYNTHETIC DEMONSTRATION ESTIMATE</p><h2>Cost and duration breakdown</h2><p>{e.repair_category} · {quantity(e.quantity)} m² · USD · {e.method_version}</p>
    <label>Cost sensitivity scenario <select value={scenario} onChange={event => setScenario(event.target.value as typeof scenario)}><option value="low">Low</option><option value="base">Base</option><option value="high">High</option></select></label>
    <div className="table-scroll" tabIndex={0} role="region" aria-label="Scrollable cost breakdown"><table><caption>{scenario} cost components — synthetic assumptions</caption><thead><tr><th scope="col">Component</th><th scope="col">Quantity</th><th scope="col">Unit</th><th scope="col">Unit rate</th><th scope="col">Subtotal</th></tr></thead><tbody>{cost.line_items.map(item => <tr key={item.label}><th scope="row">{item.label}<small>Sources: {item.evidence_ids.join(', ')}</small></th><td>{quantity(item.quantity)}</td><td>{item.unit}</td><td>{usd(item.unit_rate_usd)}</td><td>{usd(item.amount_usd)}</td></tr>)}</tbody></table></div>
    <dl className="metadata"><div><dt>Subtotal</dt><dd>{usd(cost.subtotal_usd)}</dd></div><div><dt>Contingency ({quantity(String(Number(cost.contingency_fraction) * 100))}%)</dt><dd>{usd(cost.contingency_usd)}</dd></div><div><dt>Estimated total</dt><dd>{usd(cost.total_usd)}</dd></div><div><dt>Active workdays</dt><dd>{e.duration.active_workdays}</dd></div><div><dt>Setup / mobilization days</dt><dd>{e.duration.setup_days}</dd></div><div><dt>Curing allowance days</dt><dd>{e.duration.curing_days}</dd></div><div><dt>Total preliminary days</dt><dd>{e.duration.total_preliminary_days}</dd></div><div><dt>Productivity</dt><dd>{quantity(e.duration.productivity_per_day)} {e.duration.productivity_unit}</dd></div></dl>
    <p>{e.duration.basis}</p><p>⚠ {e.suitability.rationale}</p>
    <h3>Dimension provenance</h3><ul>{Object.entries(e.dimension_provenance).map(([field, d]) => <li key={field}>{field}: {quantity(d.value)} {d.unit} · {d.basis.replaceAll('_', ' ')}<p>{d.note} Sources: {d.evidence_ids.join(', ')}</p></li>)}</ul>
    <h3>Assumptions and limitations</h3><ul>{[...e.assumptions, ...e.warnings].map((s, i) => <li key={i}>{s}</li>)}</ul>
    <details><summary>Immutable snapshot and reproducibility</summary><p>Estimate ID: {e.id}</p><p>Snapshot: {e.dataset_snapshot_id}</p><p>Created: {e.created_at}</p><p className="checksum">Input SHA-256: {e.input_hash}</p><p className="checksum">Result SHA-256: {e.result_hash}</p><p>Sources: {e.evidence_ids.join(', ')}</p><pre>{JSON.stringify(e.input_snapshot, null, 2)}</pre></details>
  </section>;
}
