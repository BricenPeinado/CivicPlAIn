import { onlineBasemap } from '../features/map/mapStyle';
import { useEffect, useState } from 'react';
import { getMunicipalViewport, getShoreline } from '../services/municipal';
import type { Bbox, MunicipalRecord, Snapshot } from '../types/municipal';
import type { FeatureCollection } from 'geojson';

export interface LayerState { streets: boolean; conditions: boolean; permits: boolean; shoreline: boolean; basemap: boolean }
export const initialLayers: LayerState = { streets: true, conditions: false, permits: false, shoreline: true, basemap: onlineBasemap };
export interface ReadState<T> { data: T; loading: boolean; error: string }
const empty: MunicipalRecord[] = [];

/** Each read is keyed by pinned snapshot + viewport + layer, and cancelled independently. */
function useLayer(kind: 'roads' | 'conditions' | 'permits', snapshot: string, bounds: Bbox, enabled: boolean, retry: number, condition?: string) {
  const [state, setState] = useState<ReadState<MunicipalRecord[]>>({ data: empty, loading: false, error: '' });
  const bbox = bounds.join(',');
  useEffect(() => {
    const ac = new AbortController();
    setState({ data: empty, loading: enabled, error: '' });
    if (!enabled) return () => ac.abort();
    const timer = setTimeout(() => {
      (condition && kind === 'roads' ? getMunicipalViewport(kind, snapshot, bounds, ac.signal, {condition}) : getMunicipalViewport(kind, snapshot, bounds, ac.signal)).then(data => { if (!ac.signal.aborted) setState({ data, loading: false, error: '' }); })
        .catch(e => { if (!ac.signal.aborted) setState({ data: empty, loading: false, error: e.message }); });
    }, 180);
    return () => { clearTimeout(timer); ac.abort(); };
    // The serialized bounds are the effect's immutable request key.
  }, [kind, snapshot, bbox, enabled, retry, condition]);
  return state;
}
export function useMunicipalData(snapshot: Snapshot, bounds: Bbox, layers: LayerState, retry: number, condition?: string) {
  const roads = useLayer('roads', snapshot.id, bounds, true, retry, condition); // keyboard list stays available with streets hidden
  const conditions = useLayer('conditions', snapshot.id, bounds, layers.conditions, retry);
  const permits = useLayer('permits', snapshot.id, bounds, layers.permits, retry);
  const [shoreline, setShoreline] = useState<ReadState<FeatureCollection>>({ data: { type: 'FeatureCollection', features: [] }, loading: true, error: '' });
  useEffect(() => {
    const ac = new AbortController();
    setShoreline({ data: { type: 'FeatureCollection', features: [] }, loading: true, error: '' });
    getShoreline(snapshot.id, snapshot.coverage.context_bbox, ac.signal).then(data => { if (!ac.signal.aborted) setShoreline({ data, loading: false, error: '' }); })
      .catch(e => { if (!ac.signal.aborted) setShoreline({ data: { type: 'FeatureCollection', features: [] }, loading: false, error: e.message }); });
    return () => ac.abort();
  }, [snapshot.id, retry]);
  return { roads, conditions, permits, shoreline };
}
