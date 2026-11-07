import { useEffect, useRef, useState } from 'react';
import { saveReviewNote } from '../../services/api';
export function ReviewNote({ evaluationId }: { evaluationId: string }) {
  return <ReviewForm key={evaluationId} evaluationId={evaluationId}/>;
}
function ReviewForm({ evaluationId }: { evaluationId: string }) {
  const [alias, setAlias] = useState(''); const [note, setNote] = useState(''); const [ack, setAck] = useState(false);
  const [busy, setBusy] = useState(false); const [message, setMessage] = useState('');
  const pending = useRef<AbortController | null>(null);
  useEffect(() => () => pending.current?.abort(), []);
  return <details className="ai-advisor"><summary>Record a human review note</summary><p>Notes are stored locally with this immutable evaluation. Use a reviewer alias and avoid personal or sensitive information. A note does not approve projects or spending and is never sent to AI.</p><form onSubmit={async e => {
    e.preventDefault(); setBusy(true); setMessage(''); const c = new AbortController(); pending.current = c;
    try { const r = await saveReviewNote(evaluationId, alias.trim(), note.trim(), c.signal); if (!c.signal.aborted) { setMessage(`Review note recorded: ${r.data.id}. No work authorized.`); setNote(''); } }
    catch { if (!c.signal.aborted) setMessage('Review note could not be saved. Retry after checking the local API.'); }
    finally { if (!c.signal.aborted) setBusy(false); }
  }}><label>Reviewer alias<input required maxLength={100} value={alias} onChange={e => setAlias(e.target.value)}/></label><label>Review note<textarea required maxLength={2000} value={note} onChange={e => setNote(e.target.value)}/></label><label><input type="checkbox" required checked={ack} onChange={e => setAck(e.target.checked)}/>I acknowledge synthetic inputs, unknown utility coverage, and the need for qualified human review.</label><button className="primary-button" disabled={busy || !ack || !alias.trim() || !note.trim()}>Save human review note</button>{message && <p role="status">{message}</p>}</form></details>;
}
