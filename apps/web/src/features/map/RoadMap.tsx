import { useEffect, useRef, useState } from 'react';
import * as maplibregl from 'maplibre-gl';
import type { GeoJSONSource, Map as MapInstance, MapLayerMouseEvent } from 'maplibre-gl';
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?url';
import type { RoadsCollection } from '../../types/api';
// Bundle the ESM worker locally; MapLibre v6 cannot infer its URL after Vite bundling.
maplibregl.setWorkerUrl(workerUrl);
export const colors = { good: '#277953', fair: '#bd831f', poor: '#c45e4d', unknown: '#859198' };
const BOUNDS: [number, number, number, number] = [-74.012, 40.710, -74.000, 40.720];
interface Props { roads: RoadsCollection; selectedId: string | null; onSelect: (id: string) => void }
export function RoadMap({ roads, selectedId, onSelect }: Props) {
  const container = useRef<HTMLDivElement>(null);
  const map = useRef<MapInstance | null>(null);
  const select = useRef(onSelect);
  select.current = onSelect;
  const [ready, setReady] = useState(false);
  const [failure, setFailure] = useState(false);
  const [hover, setHover] = useState<string | null>(null);
  useEffect(() => {
    let active = true;
    setReady(false); setFailure(false);
    let instance: MapInstance | undefined;
    let observer: ResizeObserver | undefined;
    try {
      instance = new maplibregl.Map({
        container: container.current!, center: [-74.006, 40.715], zoom: 15.4,
        maxZoom: 19, minZoom: 12, attributionControl: false,
        style: { version: 8, sources: {}, layers: [{ id: 'paper', type: 'background', paint: { 'background-color': '#edf0e9' } }] },
      });
      map.current = instance;
      instance.addControl(new maplibregl.NavigationControl({ showCompass: true }), 'top-right');
      instance.addControl(new maplibregl.AttributionControl({ compact: false,
        customAttribution: 'CivicPlAIn synthetic schematic · No municipal observations · No basemap tiles' }), 'bottom-right');
      instance.on('load', () => {
        if (!instance || !active) return;
        instance.addSource('roads', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
        instance.addLayer({ id: 'road-casing', type: 'line', source: 'roads', layout: { 'line-cap': 'round', 'line-join': 'round' }, paint: { 'line-color': '#ffffff', 'line-width': 13 } });
        instance.addLayer({ id: 'road-color', type: 'line', source: 'roads', layout: { 'line-cap': 'round', 'line-join': 'round' }, paint: {
          'line-color': ['match', ['get', 'condition'], 'good', colors.good, 'fair', colors.fair, 'poor', colors.poor, colors.unknown], 'line-width': 6 } });
        instance.addLayer({ id: 'road-selected', type: 'line', source: 'roads', filter: ['==', ['get', 'road_id'], ''], paint: { 'line-color': '#173f3a', 'line-width': 16, 'line-opacity': .32 } }, 'road-color');
        instance.addLayer({ id: 'road-hover', type: 'line', source: 'roads', filter: ['==', ['get', 'road_id'], ''], paint: { 'line-color': '#142e2b', 'line-width': 11, 'line-opacity': .25 } });
        instance.addLayer({ id: 'road-hit', type: 'line', source: 'roads', paint: { 'line-width': 24, 'line-opacity': 0 } });
        instance.on('click', 'road-hit', (e: MapLayerMouseEvent) => {
          const id = e.features?.[0]?.properties?.road_id;
          if (id) select.current(String(id));
        });
        instance.on('mousemove', 'road-hit', (e: MapLayerMouseEvent) => {
          const id = String(e.features?.[0]?.properties?.road_id || '');
          instance!.getCanvas().style.cursor = 'pointer';
          instance!.setFilter('road-hover', ['==', ['get', 'road_id'], id]);
          setHover(e.features?.[0]?.properties?.name || id);
        });
        instance.on('mouseleave', 'road-hit', () => {
          instance!.getCanvas().style.cursor = '';
          instance!.setFilter('road-hover', ['==', ['get', 'road_id'], '']); setHover(null);
        });
        instance.fitBounds(BOUNDS, { padding: 65, duration: 0 });
        setReady(true);
      });
      instance.on('error', () => { if (active) setFailure(true); });
      instance.getCanvas().addEventListener('webglcontextlost', () => { if (active) setFailure(true); });
      observer = new ResizeObserver(() => instance?.resize());
      observer.observe(container.current!);
    } catch { setFailure(true); }
    return () => { active = false; observer?.disconnect(); instance?.remove(); map.current = null; };
  }, []);
  useEffect(() => {
    if (!ready || !map.current) return;
    const source = map.current.getSource('roads') as GeoJSONSource;
    source.setData({ type: 'FeatureCollection', features: roads.features.map(f => ({ ...f,
      id: f.properties.id, properties: { road_id: f.properties.id, name: f.properties.name, condition: f.properties.condition_summary.category } })) });
  }, [roads, ready]);
  useEffect(() => {
    if (ready) map.current?.setFilter('road-selected', ['==', ['get', 'road_id'], selectedId || '']);
  }, [selectedId, ready]);
  return <section className="map-stage" aria-label="Interactive schematic infrastructure map">
    <div ref={container} className="map-canvas" />
    <div className="map-stamp"><span className="live-dot" /> LOCAL SCHEMATIC <span>EPSG:4326</span></div>
    <div className="map-place" aria-hidden="true">LOWER MANHATTAN<span>Illustrative study window</span></div>
    {failure ? <div className="map-message" role="alert"><strong>Map rendering unavailable</strong><p>Use the road list below to select segments and inspect the same records.</p></div> : !ready && <div className="map-message" role="status">Preparing local map…</div>}
    {hover && <div className="map-tooltip">{hover} · Demo data</div>}
    <button className="map-reset" onClick={() => map.current?.fitBounds(BOUNDS, { padding: 65 })} disabled={!ready || failure}>⌖ <span>Study area</span></button>
    <div className="map-note">Schematic geometry. Does not trace actual streets.</div>
  </section>;
}
