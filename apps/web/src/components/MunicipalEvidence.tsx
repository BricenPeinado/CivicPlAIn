import { useEffect, useState } from 'react';
import { getSource } from '../services/municipal';
import type { MunicipalRecord, SourceRevision } from '../types/municipal';
export const human = (value: string) => value.replaceAll('_', ' ');
export const shown = (value: string | null | undefined) => value || 'Unknown';
// Keep the source's local calendar date; never reinterpret a floating timestamp as UTC.
export const sourceDate = (value: string | null | undefined) => value && /^\d{4}-\d{2}-\d{2}T/.test(value) ? value.slice(0, 10) : shown(value);
export function SourceEvidence({ snapshot, revision }: { snapshot: string; revision: string }) {
  const [source, setSource] = useState<SourceRevision | null>(null), [error, setError] = useState(''), [retry, setRetry] = useState(0);
  useEffect(() => { const ac = new AbortController(); setSource(null); setError(''); getSource(snapshot, revision, ac.signal).then(s => { if (!ac.signal.aborted) setSource(s); }).catch(e => { if (!ac.signal.aborted) setError(e.message); }); return () => ac.abort(); }, [snapshot, revision, retry]);
  return error ? <div role="alert">Source unavailable. {error}<button onClick={() => setRetry(v => v + 1)}>Retry source</button></div> : !source ? <p role="status">Loading provenance…</p> : <div className="source-evidence">
    <h4>{source.attribution}</h4><p><a href={source.source_url} target="_blank" rel="noreferrer">Official source ↗</a> · <a href={source.dictionary_url} target="_blank" rel="noreferrer">Data dictionary ↗</a></p>
    <dl className="metadata"><div><dt>Retrieved</dt><dd>{source.retrieved_at}</dd></div><div><dt>Release</dt><dd>{source.release_note}</dd></div><div><dt>Update cadence</dt><dd>{source.cadence}</dd></div><div><dt>Original CRS</dt><dd>{source.source_crs}</dd></div></dl>
    <p>{source.license.note}</p>{source.license.application_disclaimer_required && <p className="notice">NYC DOT data carries no accuracy or completeness warranty. <a href={source.license.application_disclaimer_url} target="_blank" rel="noreferrer">Read the required NYC DOT application disclaimer.</a></p>}
    <details><summary>Source revision and integrity</summary><p>{source.id}</p><p className="checksum">Raw SHA-256: {source.raw_sha256}</p><p>Source updated: {JSON.stringify(source.source_updated_at) || 'Unknown'}</p>{source.terms_urls.map(url => <p key={url}><a href={url} target="_blank" rel="noreferrer">Terms and attribution ↗</a></p>)}</details>
  </div>;
}
export function RecordEvidence({ record, snapshot }: { record: MunicipalRecord; snapshot: string }) {
  return <><span className={`record-badge ${record.classification}`}>{human(record.classification)}</span><details><summary>Identifiers and source fields</summary><dl className="metadata">{Object.entries(record.raw_identifiers).map(([key, value]) => <div key={key}><dt>{human(key)}</dt><dd>{shown(value)}</dd></div>)}</dl><p>Source record: {record.source_record_key}</p><p>Record ID: {record.id}</p></details>
    <details><summary>Provenance and limitations</summary><SourceEvidence snapshot={snapshot} revision={record.source_revision_id}/><ul>{record.limitations.map(l => <li key={l}>{l}</li>)}</ul>{Object.entries(record.unknown_reasons).map(([key, value]) => <p key={key}>{human(key)}: {human(value)}</p>)}<details><summary>Field provenance and matching method</summary><pre>{JSON.stringify({ fields: record.field_provenance, classifications: record.field_classifications, match: record.match, lineage: record.lineage }, null, 2)}</pre></details></details></>;
}
