import { useEffect, useRef, useState } from 'react';
import * as maplibregl from 'maplibre-gl';
import type { GeoJSONSource, Map as MapInstance, MapLayerMouseEvent } from 'maplibre-gl';
import type { FeatureCollection } from 'geojson';
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?url';
import type { RoadsCollection, WorkProject, InfrastructureCategory } from '../../types/api';
import type { Bbox } from '../../types/municipal';
import type { LayerState } from '../../hooks/useMunicipalData';
import { categoryColors } from '../conflicts/ConflictReview';
import { colors } from './colors';
import { emptyCollection, FOCUS, mapStyle, onlineBasemap, pilotColors } from './mapStyle';
maplibregl.setWorkerUrl(workerUrl);
export { colors } from './colors';
interface Props {
  roads?: RoadsCollection; features?: FeatureCollection; observations?: FeatureCollection; permits?: FeatureCollection; shoreline?: FeatureCollection;
  screeningFeatures?: FeatureCollection; priorityFeatures?: FeatureCollection; candidateFeatures?: FeatureCollection; selectedGeometry?: FeatureCollection; focusPadding?: number; focusBounds?: Bbox | null; official?: boolean; layers?: LayerState;
  selectedId: string | null; onSelect: (id: string) => void; onViewport?: (bbox: Bbox) => void;
  onObservation?: (id: string) => void; onPermit?: (id: string) => void;
  projects?: WorkProject[]; highlightedProjects?: string[]; highlightedRoads?: string[];
  onSelectProject?: (id: string) => void; showProjects?: boolean; visibleCategories?: InfrastructureCategory[];
}
const EMPTY: never[] = [];
export function RoadMap({ screeningFeatures, priorityFeatures, candidateFeatures, roads, features, observations, permits, shoreline, selectedGeometry, focusBounds, focusPadding = 55, official = false, layers,
  selectedId, onSelect, onViewport, onObservation, onPermit, projects = EMPTY, highlightedProjects = EMPTY, highlightedRoads = EMPTY,
  onSelectProject, showProjects = true, visibleCategories = EMPTY }: Props) {
  const container = useRef<HTMLDivElement>(null), map = useRef<MapInstance | null>(null);
  const callbacks = useRef({ onSelect, onViewport, onObservation, onPermit, onSelectProject });
  callbacks.current = { onSelect, onViewport, onObservation, onPermit, onSelectProject };
  const [ready, setReady] = useState(false), [failure, setFailure] = useState(false), [tileFailure, setTileFailure] = useState(false);
  const [hover, setHover] = useState<string | null>(null), [retry, setRetry] = useState(0);
  const [layerError, setLayerError] = useState(false);
  useEffect(() => {
    let active = true, loaded = false; setReady(false); setFailure(false); setTileFailure(false); setLayerError(false);
    let instance: MapInstance | undefined, observer: ResizeObserver | undefined;
    const deadline = window.setTimeout(() => { if (active && !loaded) setFailure(true); }, 12000);
    try {
      instance = new maplibregl.Map({ container: container.current!, center: [-74.007, 40.7125], zoom: 15.8,
        maxZoom: 20, minZoom: 13, maxBounds: official ? [-74.030, 40.695, -73.980, 40.730] : undefined,
        attributionControl: false, style: mapStyle(official && onlineBasemap),
      });
      map.current = instance;
      instance.getCanvas().setAttribute('aria-label', official ? 'Lower Manhattan map. Arrow keys pan; plus and minus zoom. Use the street list to select records.' : 'Synthetic map. Use the street list to select records.');
      instance.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'bottom-left');
      instance.addControl(new maplibregl.AttributionControl({ compact: false, customAttribution: official
        ? 'NYC DCP LION · NYC DOT observations · NYC DOITT shoreline'
        : 'CivicPlAIn · Synthetic geometry and conditions' }), 'bottom-right');
      instance.on('load', () => {
        if (!instance || !active) return;
        loaded = true; clearTimeout(deadline);
        for (const id of ['shoreline', 'roads', 'observations', 'permits', 'selection', 'projects', 'screening', 'priorities', 'candidates']) instance.addSource(id, { type: 'geojson', data: emptyCollection() });
        instance.addLayer({ id: 'shoreline', type: 'line', source: 'shoreline', paint: { 'line-color': '#9ab5c5', 'line-width': 2 } });
        instance.addLayer({ id: 'road-casing', type: 'line', source: 'roads', layout: { 'line-cap': 'round', 'line-join': 'round' }, paint: { 'line-color': '#fff', 'line-width': official ? 6 : 13 } });
        instance.addLayer({ id: 'road-color', type: 'line', source: 'roads', layout: { 'line-cap': 'round', 'line-join': 'round' }, paint: {
          'line-color': ['match', ['get', 'condition'], 'good', official ? pilotColors.good : colors.good, 'fair', official ? pilotColors.fair : colors.fair, 'poor', official ? pilotColors.poor : colors.poor, official ? pilotColors.unknown : colors.unknown], 'line-width': official ? 2.3 : 6 } });
        instance.addLayer({ id: 'road-selected', type: 'line', source: 'roads', filter: ['==', ['get', 'road_id'], ''], paint: { 'line-color': '#086cc9', 'line-width': 10, 'line-opacity': .5 } });
        instance.addLayer({ id: 'road-hover', type: 'line', source: 'roads', filter: ['==', ['get', 'road_id'], ''], paint: { 'line-color': '#194d78', 'line-width': 8, 'line-opacity': .4 } });
        instance.addLayer({ id: 'road-hit', type: 'line', source: 'roads', paint: { 'line-width': 18, 'line-opacity': 0 } });
        instance.addLayer({ id: 'road-conflict', type: 'line', source: 'roads', filter: ['in', ['get', 'road_id'], ['literal', []]], paint: { 'line-color': '#a46e12', 'line-width': 8, 'line-dasharray': [2, 1] } });
        instance.addLayer({ id: 'observations', type: 'line', source: 'observations', paint: { 'line-width': 5, 'line-opacity': .8,
          'line-color': ['case', ['<', ['get', 'rating'], 0], '#667385', ['interpolate', ['linear'], ['get', 'rating'], 0, '#c3d9e9', 10, '#185b8f']] } });
        instance.addLayer({ id: 'permit-lines', type: 'line', source: 'permits', filter: ['!=', ['geometry-type'], 'Point'], paint: { 'line-color': '#9c650c', 'line-width': 5, 'line-dasharray': [1, 1] } });
        instance.addLayer({ id: 'permit-points', type: 'circle', source: 'permits', filter: ['==', ['geometry-type'], 'Point'], paint: { 'circle-radius': 6, 'circle-color': '#9c650c', 'circle-stroke-color': '#fff', 'circle-stroke-width': 2 } });
        instance.addLayer({id:'permit-candidates',type:'line',source:'candidates',paint:{'line-color':'#8c6a2d','line-width':6,'line-dasharray':[1,2]}});
        instance.addLayer({id:'priorities',type:'line',source:'priorities',paint:{'line-color':['match',['get','priority_status'],'ranked','#7951a6','#667385'],'line-width':5,'line-dasharray':[3,2]}});
        instance.addLayer({ id: 'selection', type: 'line', source: 'selection', paint: { 'line-color': '#0069c7', 'line-width': 6 } });
        instance.addLayer({id:'screening-fill',type:'fill',source:'screening',filter:['==',['geometry-type'],'Polygon'],paint:{'fill-color':'#c65e05','fill-opacity':.16}});
        instance.addLayer({id:'screening-lines',type:'line',source:'screening',paint:{'line-color':'#c65e05','line-width':5,'line-dasharray':[2,1]}});
        if (official) instance.addLayer({ id: 'road-labels', type: 'symbol', source: 'roads', minzoom: 13,
          layout: { 'symbol-placement': 'line', 'text-field': ['get', 'name'], 'text-font': ['Arial', 'Helvetica', 'sans-serif'], 'text-size': 11, 'symbol-spacing': 350 },
          paint: { 'text-color': '#344c5e', 'text-halo-color': '#fff', 'text-halo-width': 2 } });
        instance.addLayer({ id: 'project-fill', type: 'fill', source: 'projects', filter: ['==', ['geometry-type'], 'Polygon'], paint: { 'fill-color': ['get', 'color'], 'fill-opacity': .15 } });
        instance.addLayer({ id: 'project-lines', type: 'line', source: 'projects', paint: { 'line-color': ['get', 'color'], 'line-width': 3, 'line-dasharray': [2, 1] } });
        instance.addLayer({ id: 'project-selected', type: 'line', source: 'projects', filter: ['in', ['get', 'project_id'], ['literal', []]], paint: { 'line-color': '#0069c7', 'line-width': 7 } });
        instance.on('click', 'road-hit', (e: MapLayerMouseEvent) => { if (official && instance!.queryRenderedFeatures(e.point, { layers: ['observations', 'permit-lines', 'permit-points'] }).length) return; const id = e.features?.[0]?.properties?.road_id; if (id) callbacks.current.onSelect(String(id)); });
        instance.on('mousemove', 'road-hit', (e: MapLayerMouseEvent) => {
          if (!active) return;
          const id = String(e.features?.[0]?.properties?.road_id || '');
          instance!.getCanvas().style.cursor = 'pointer'; instance!.setFilter('road-hover', ['==', ['get', 'road_id'], id]); setHover(e.features?.[0]?.properties?.name || id);
        });
        instance.on('mouseleave', 'road-hit', () => { if (active) { instance!.getCanvas().style.cursor = ''; instance!.setFilter('road-hover', ['==', ['get', 'road_id'], '']); setHover(null); } });
        for (const layer of ['project-fill', 'project-lines']) instance.on('click', layer, (e: MapLayerMouseEvent) => { const id = e.features?.[0]?.properties?.project_id; if (id) callbacks.current.onSelectProject?.(String(id)); });
        for (const layer of ['observations', 'permit-lines', 'permit-points']) instance.on('click', layer, (e: MapLayerMouseEvent) => {
          if (layer === 'observations' && instance!.queryRenderedFeatures(e.point, { layers: ['permit-lines', 'permit-points'] }).length) return;
          const id = e.features?.[0]?.properties?.record_id; if (id) (layer === 'observations' ? callbacks.current.onObservation : callbacks.current.onPermit)?.(String(id));
        });
        instance.fitBounds(official ? FOCUS : [-74.012, 40.710, -74.000, 40.720], { padding: 40, duration: 0 });
        setReady(true);
      });
      instance.on('moveend', () => {
        if (!active || !official || !callbacks.current.onViewport) return;
        const b = instance!.getBounds();
        const bbox: Bbox = [b.getWest(), b.getSouth(), b.getEast(), b.getNorth()];
        if (bbox.every(Number.isFinite) && bbox[0] < bbox[2] && bbox[1] < bbox[3]) callbacks.current.onViewport(bbox);
      });
      instance.on('error', event => {
        if (!active) return;
        if ((event as unknown as { sourceId?: string })?.sourceId === 'basemap') { setTileFailure(true); if (instance?.getLayer('basemap')) instance.setLayoutProperty('basemap', 'visibility', 'none'); }
        else if (official) setLayerError(true); else setFailure(true);
      });
      instance.getCanvas().addEventListener('webglcontextlost', () => { if (active) setFailure(true); });
      observer = new ResizeObserver(() => instance?.resize()); observer.observe(container.current!);
    } catch { setFailure(true); }
    return () => { active = false; clearTimeout(deadline); observer?.disconnect(); instance?.remove(); map.current = null; };
  }, [official, retry]);
  useEffect(() => {
    if (!ready || !map.current) return;
    const synthetic: FeatureCollection = { type: 'FeatureCollection', features: (roads?.features || []).map(f => ({ ...f, id: f.properties.id,
      properties: { road_id: f.properties.id, name: f.properties.name, condition: f.properties.condition_summary.category } })) };
    for (const [id, data] of Object.entries({ roads: features || synthetic, observations, permits, shoreline, screening:screeningFeatures, priorities:priorityFeatures, candidates:candidateFeatures, selection: selectedGeometry }))
      (map.current.getSource(id) as GeoJSONSource)?.setData(data || emptyCollection());
  }, [roads, features, observations, permits, shoreline, screeningFeatures, priorityFeatures, candidateFeatures, selectedGeometry, ready]);
  useEffect(() => { if (ready) map.current?.setFilter('road-selected', ['==', ['get', 'road_id'], selectedId || '']); }, [selectedId, ready]);
  useEffect(() => {
    if (!ready || !map.current || !layers) return;
    const groups = { streets: ['road-casing', 'road-color', 'road-hover', 'road-hit', 'road-labels'], conditions: ['observations'], permits: ['permit-lines', 'permit-points'], shoreline: ['shoreline'], basemap: ['basemap'] };
    for (const key of Object.keys(groups) as (keyof LayerState)[]) for (const id of groups[key])
      if (map.current.getLayer(id)) map.current.setLayoutProperty(id, 'visibility', layers[key] && !(key === 'basemap' && tileFailure) ? 'visible' : 'none');
  }, [layers, ready, tileFailure]);
  useEffect(() => {
    if (!ready || !map.current) return;
    const visible = showProjects ? projects.filter(p => p.geometry && visibleCategories.includes(p.infrastructure_category)) : [];
    (map.current.getSource('projects') as GeoJSONSource).setData({ type: 'FeatureCollection', features: visible.map(p => ({ type: 'Feature', id: p.id, geometry: p.geometry!, properties: { project_id: p.id, category: p.infrastructure_category, color: categoryColors[p.infrastructure_category], name: p.title } })) });
  }, [projects, showProjects, visibleCategories, ready]);
  useEffect(() => {
    if (!ready || !map.current) return;
    map.current.setFilter('project-selected', ['in', ['get', 'project_id'], ['literal', highlightedProjects]]);
    map.current.setFilter('road-conflict', ['in', ['get', 'road_id'], ['literal', highlightedRoads]]);
  }, [highlightedProjects, highlightedRoads, ready]);
  useEffect(() => { if (ready && focusBounds) map.current?.fitBounds(focusBounds, { padding: focusPadding, maxZoom: focusPadding === 0 ? 20 : 18, duration: 0 }); }, [ready, focusBounds, focusPadding]);
  return <section className="map-stage" aria-label={official ? 'Interactive Lower Manhattan map' : 'Interactive synthetic infrastructure map'}>
    <div ref={container} className="map-canvas" />
    {failure ? <div className="map-message" role="alert"><strong>Map rendering unavailable</strong><p>Search and the street list still provide access to records.</p><button onClick={() => setRetry(v => v + 1)}>Retry map</button></div> : !ready && <div className="map-message" role="status">Preparing map…</div>}
    {(tileFailure || layerError) && !failure && <div className="tile-notice" role="status">{tileFailure ? 'Background tiles unavailable. Official layers remain available.' : 'A map layer could not render. Use the street list to inspect records.'}<button onClick={() => setRetry(v => v + 1)}>Retry map</button></div>}
    {hover && !failure && <div className="map-tooltip">{hover}{!official && ' · Synthetic fixture'}</div>}
    <button className="map-reset" onClick={() => map.current?.fitBounds(official ? FOCUS : [-74.012, 40.710, -74.000, 40.720], { padding: 40, duration: 0 })} disabled={!ready || failure} aria-label="Return to study focus">⌖</button>
  </section>;
}
