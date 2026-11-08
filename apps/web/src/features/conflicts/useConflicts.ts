import { useEffect, useRef, useState } from 'react';
import { analyzeConflicts, getProjects, getConflictAnalysis } from '../../services/api';
import type { ConflictAnalysis, RoadsCollection, WorkProject } from '../../types/api';

/** Reading/navigating never creates an analysis. Screening is an explicit user action. */
export function useConflicts(roads: RoadsCollection | null, analysisId?: string) {
  const [projects, setProjects] = useState<WorkProject[]>([]), [analysis, setAnalysis] = useState<ConflictAnalysis | null>(null);
  const [error, setError] = useState(''), [loading, setLoading] = useState(false), [retry, setRetry] = useState(0);
  const [analysisLoading,setAnalysisLoading]=useState(false);
  const pending = useRef<AbortController | null>(null);
  useEffect(() => {
    const ac = new AbortController(); setProjects([]); if (!analysisId) setAnalysis(null); setError(''); setLoading(false);
    if (!roads?.features.length) return () => ac.abort();
    setLoading(true);
    getProjects(ac.signal).then(r => { if (r.meta.dataset_snapshot_id !== roads.meta.dataset_snapshot_id) throw new Error('Project snapshot differs from roads. Reload the workspace.'); if (!ac.signal.aborted) setProjects(r.data); })
      .catch(e => { if (!ac.signal.aborted) setError(e.message); }).finally(() => { if (!ac.signal.aborted) setLoading(false); });
    return () => { ac.abort(); pending.current?.abort(); };
  }, [roads, retry]);
  useEffect(() => {
    const ac = new AbortController();
    if (!analysisId || !roads || analysis?.id === analysisId && analysis.dataset_snapshot_id === roads.meta.dataset_snapshot_id) { setAnalysisLoading(false); return () => ac.abort(); }
    setAnalysis(null); setAnalysisLoading(true); setError('');
    getConflictAnalysis(analysisId,ac.signal).then(r => { if (r.meta.dataset_snapshot_id !== roads.meta.dataset_snapshot_id || r.data.dataset_snapshot_id !== roads.meta.dataset_snapshot_id) throw new Error('Analysis snapshot changed. Reload the workspace.'); if (!ac.signal.aborted) setAnalysis(r.data); }).catch(e => {if (!ac.signal.aborted) setError(e.message);}).finally(()=>{if (!ac.signal.aborted) setAnalysisLoading(false);});
    return () => ac.abort();
  },[analysisId,roads,retry]);
  async function analyze() {
    if (!roads?.meta.dataset_snapshot_id || !projects.length || loading) return;
    const ac = new AbortController(); pending.current = ac; setLoading(true); setError('');
    try { const r = await analyzeConflicts(roads.meta.dataset_snapshot_id, projects.map(p => p.id), ac.signal);
      if (r.data.dataset_snapshot_id !== roads.meta.dataset_snapshot_id || r.meta.dataset_snapshot_id !== roads.meta.dataset_snapshot_id) throw new Error('Analysis snapshot changed. Reload the workspace.');
      if (!ac.signal.aborted) setAnalysis(r.data);
    } catch (e) { if (!ac.signal.aborted) setError((e as Error).message); } finally { if (!ac.signal.aborted) setLoading(false); }
  }
  return { projects, analysis, error, loading: loading || analysisLoading, reload: () => setRetry(v => v + 1), analyze };
}
