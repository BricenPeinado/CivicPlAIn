import { useEffect, useState } from 'react';
import { analyzeConflicts, getProjects } from '../../services/api';
import type { ConflictAnalysis, RoadsCollection, WorkProject } from '../../types/api';

export function useConflicts(roads: RoadsCollection | null) {
  const [projects, setProjects] = useState<WorkProject[]>([]);
  const [analysis, setAnalysis] = useState<ConflictAnalysis | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    setProjects([]); setAnalysis(null); setError('');
    if (!roads?.features.length || !roads.meta.dataset_snapshot_id) return;
    setLoading(true);
    const load = async () => {
      const response = await getProjects(controller.signal);
      if (response.meta.dataset_snapshot_id !== roads.meta.dataset_snapshot_id) throw new Error('Project snapshot differs from roads. Reload the workspace.');
      let result: ConflictAnalysis | null = null;
      if (response.data.length) {
        const checked = await analyzeConflicts(roads.meta.dataset_snapshot_id!, response.data.map(p => p.id), controller.signal);
        if (checked.data.dataset_snapshot_id !== roads.meta.dataset_snapshot_id || checked.meta.dataset_snapshot_id !== roads.meta.dataset_snapshot_id) throw new Error('Analysis snapshot changed. Reload the workspace.');
        result = checked.data;
      }
      if (!controller.signal.aborted) { setProjects(response.data); setAnalysis(result); }
    };
    load().catch(e => { if (!controller.signal.aborted) setError(e instanceof Error ? e.message : 'Conflict data unavailable.'); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [roads, retry]);
  return { projects, analysis, error, loading, reload: () => setRetry(v => v + 1) };
}
