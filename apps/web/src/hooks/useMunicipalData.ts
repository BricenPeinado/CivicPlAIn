import { onlineBasemap } from '../features/map/mapStyle';
import { useEffect, useState } from 'react';
import { getMunicipalViewport, getShoreline } from '../services/municipal';
import type { Bbox, MunicipalRecord, Snapshot } from '../types/municipal';
import type { FeatureCollection } from 'geojson';

import {ViewportCache} from '../services/viewportCache';
import {useViewportLayer} from './useViewportLayer';
export type {ReadState} from './useViewportLayer';
import type {ReadState} from './useViewportLayer';
export interface LayerState { streets: boolean; ratings?: boolean; conditions: boolean; permits: boolean; shoreline: boolean; basemap: boolean }
export const initialLayers: LayerState = { streets: true, ratings: true, conditions: false, permits: false, shoreline: true, basemap: onlineBasemap };
function useLayer(cache: ViewportCache<MunicipalRecord>, kind: 'roads' | 'conditions' | 'permits', snapshot: string, bounds: Bbox, enabled: boolean, retry: number, condition?: string, observationFilters?: Record<string,string>) {
  const filters={...observationFilters,...(kind==='roads' && condition?{condition}:{})};
  const context=JSON.stringify([snapshot,kind,Object.entries(filters).sort()]);
  return useViewportLayer(cache,context,bounds,enabled,retry,(bbox,signal)=>getMunicipalViewport(kind,snapshot,bbox,signal,filters),kind);
}
export function useMunicipalData(snapshot: Snapshot, bounds: Bbox, layers: LayerState, retry: number, condition?: string, observationFilters?: Record<string,string>, roadFilters?: Record<string,string>) {
  const [cache] = useState(()=>new ViewportCache<MunicipalRecord>());
  const roads = useLayer(cache, 'roads', snapshot.id, bounds, true, retry, condition, roadFilters); // keyboard list stays available with streets hidden
  const conditions = useLayer(cache, 'conditions', snapshot.id, bounds, layers.conditions, retry, undefined, observationFilters);
  const permits = useLayer(cache, 'permits', snapshot.id, bounds, layers.permits, retry);
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
