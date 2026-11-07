import { useEffect, useId, useRef, useState } from 'react';
import { explainContext, getAIStatus } from '../../services/api';
import type { AIContext, AIExplanation, AIStatus } from '../../types/ai';

export function AIAdvisor({ context, label = 'Explain selected evidence' }: { context: AIContext; label?: string }) {
  // Remount on context change: no stale answer or in-flight response can cross contexts.
  return <Advisor key={JSON.stringify(context)} context={context} label={label}/>;
}
function Advisor({ context, label }: { context: AIContext; label: string }) {
  const [open, setOpen] = useState(false);
  const [question, setQuestion] = useState('');
  const [useAI, setUseAI] = useState(false);
  const [answer, setAnswer] = useState<AIExplanation | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [provider, setProvider] = useState<AIStatus | null>(null);
  const pending = useRef<AbortController | null>(null);
  const statusPending = useRef<AbortController | null>(null);
  const sourcePrefix = useId();
  const sources = useRef<HTMLDetailsElement>(null);
  function inspectSource(id: string) {
    if (sources.current) sources.current.open = true;
    const target = document.getElementById(id);
    target?.scrollIntoView?.({ block: 'nearest' });
    target?.focus();
  }
  useEffect(() => () => { pending.current?.abort(); statusPending.current?.abort(); }, []);
  async function run(ask = false) {
    pending.current?.abort(); const controller = new AbortController(); pending.current = controller;
    setBusy(true); setOpen(true); setError(''); setAnswer(null);
    try {
      const r = await explainContext(context, useAI ? 'ai' : 'deterministic', ask ? question.trim() : undefined, controller.signal);
      if (!controller.signal.aborted) setAnswer(r.data);
    } catch (e) { if (!controller.signal.aborted) setError(e instanceof Error ? e.message : 'Explanation unavailable'); }
    finally { if (!controller.signal.aborted) setBusy(false); }
  }
  async function status() {
    statusPending.current?.abort(); const controller = new AbortController(); statusPending.current = controller;
    try { const r = await getAIStatus(controller.signal); if (!controller.signal.aborted) setProvider(r.data); }
    catch { if (!controller.signal.aborted) setError('Provider status unavailable. Local explanations can still be requested.'); }
  }
  const findings = (classification: string) => answer?.key_findings.filter(f => f.classification === classification) || [];
  const list = (items: string[]) => <ul>{items.map((s,i) => <li key={i}>{s}</li>)}</ul>;
  function factList(classification: string) {
    return <ul className="advisor-findings" tabIndex={0} aria-label="Scrollable source-backed findings">{findings(classification).map(f => <li key={f.finding_id}><p>{f.claim_text}</p><small>{f.classification.replaceAll('_',' ')}</small> {f.supporting_evidence_ids.map(ref => <a key={ref} href={`#${sourcePrefix}-${ref}`} onClick={e => { e.preventDefault(); inspectSource(`${sourcePrefix}-${ref}`); }}>Inspect source {answer!.citations.findIndex(c => c.evidence_id === ref)+1}</a>)}</li>)}</ul>;
  }
  return <section className="ai-advisor" aria-label={`Contextual advisor: ${context.type}`}>
    <button className="primary-button" disabled={busy} onClick={() => run()}>{label}</button>
    {!open && <button className="text-button" onClick={() => setOpen(true)}>Ask about this evidence</button>}
    {open && <div className="advisor-panel">
      <div className="list-heading"><h3>Evidence advisor</h3><span className="quiet-tag">{context.type.replaceAll('_',' ')} context</span></div>
      <p>Ask about these supplied records, costs, conflicts or assumptions. Human review is required for decisions.</p>
      <label className="advisor-mode"><input type="checkbox" checked={useAI} onChange={e => setUseAI(e.target.checked)}/>Request configured AI emphasis (optional; offline fallback available)</label>
      <form onSubmit={e => { e.preventDefault(); if (question.trim()) void run(true); }}>
        <label>Question about attached evidence<textarea maxLength={500} required value={question} onChange={e => setQuestion(e.target.value)} placeholder="Which assumptions should we verify before review?"/></label>
        <button className="primary-button" disabled={busy || !question.trim()}>Ask contextual question</button>
      </form>
      {busy && <p role="status">Building evidence and validating explanation…</p>}
      {error && <div role="alert"><p>{error}</p><button className="text-button" onClick={() => run()}>Retry explanation</button></div>}
      {answer && <article aria-label="Grounded explanation" aria-live="polite">
        <p className="eyebrow">{answer.provider_status === 'fallback' ? 'DETERMINISTIC FALLBACK' : answer.provider_status === 'openai' ? 'AI-SELECTED EMPHASIS · SERVER-RENDERED FACTS' : 'DETERMINISTIC EXPLANATION'}</p>
        <span className="demo-badge">{answer.source_classification.toUpperCase()} INPUTS</span>
        <p>Validation: {answer.validation_status.replaceAll('_',' ')}{answer.model_label && ` · Model: ${answer.model_label}`}</p>
        {answer.fallback_reason && <p role="note">Fallback reason: {answer.fallback_reason.replaceAll('_',' ')}. Source-based templates were used.</p>}
        <p>{answer.summary}</p>
        {!!findings('deterministic_calculation').length && <details open><summary>Calculated facts and cost drivers</summary>{factList('deterministic_calculation')}</details>}
        {!!findings('verified_record_fact').length && <details open><summary>Recorded fields and assumptions · {answer.source_classification}</summary>{factList('verified_record_fact')}</details>}
        <h4>Tradeoffs and review considerations</h4>{list(answer.tradeoffs)}
        <h4>Missing information</h4>{list(answer.missing_information)}
        <h4>Suggested human review</h4>{list(answer.suggested_review_actions)}
        <details open><summary>Uncertainty and limitations</summary>{list(answer.uncertainties)}</details>
        {answer.evidence.truncated && <p className="coverage-note">Evidence truncated: {answer.evidence.omitted_fact_count} facts omitted. Inspect original source snapshots.</p>}
        <details ref={sources}><summary>Supporting evidence ({answer.citations.length})</summary>{answer.citations.map((s,i) => <div key={s.evidence_id} id={`${sourcePrefix}-${s.evidence_id}`} className="advisor-source" tabIndex={-1}>
          <h4>Source {i+1} · {s.entity_type} · {s.synthetic_input ? 'SYNTHETIC' : 'Source reported'}</h4>
          <p>Record: {s.record_id}</p><p>{s.calculation_version || 'Recorded fields'} · Dataset: {s.dataset_snapshot_id || 'See saved inputs'}</p>
          <p className="checksum">Record SHA-256: {s.record_hash}</p><p className="checksum">Input SHA-256: {s.input_hash || 'Not a calculation'}</p>
          <pre>{JSON.stringify({ source_revisions: s.source_revisions, fields: answer.evidence.facts.filter(f => f.evidence_id === s.evidence_id) }, null, 2)}</pre>
        </div>)}<p className="checksum">Evidence SHA-256: {answer.evidence_snapshot_hash}</p><p>Audit reference: {answer.audit_reference} · {answer.generated_at}</p></details>
      </article>}
      <details><summary>How AI works</summary><p>Costs and preliminary durations are calculated by deterministic algorithms. Spatial and schedule conflicts are computed by deterministic services. Optional AI selects supporting facts to emphasize; the server renders the explanation and validates references against the attached records. Missing information and synthetic inputs remain labeled. AI does not approve projects or spending. Human engineering review is required. Offline templates remain available without a key or network. These safeguards do not make source data complete or infallible.</p>
        <button className="text-button" onClick={status}>Check provider status</button>{provider && <p>Provider {provider.provider_configured ? 'configured' : 'not configured'} · default {provider.default_mode} · {provider.max_calls_per_hour} calls/hour per API process · {provider.timeout_seconds}s timeout. A live provider call has not been verified by this status check.</p>}
      </details>
    </div>}
  </section>;
}
