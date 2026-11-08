import type { FeatureCollection, Geometry } from 'geojson';
import type { StyleSpecification } from 'maplibre-gl';
import type { MunicipalRecord } from '../../types/municipal';
export const onlineBasemap = !import.meta.env.VITE_BASEMAP || import.meta.env.VITE_BASEMAP === 'osm';
export const PILOT: [number, number, number, number] = [-74.020, 40.700, -73.985, 40.725];
export const FOCUS: [number, number, number, number] = [-74.011, 40.709, -74.003, 40.716];
export const emptyCollection = (): FeatureCollection => ({ type: 'FeatureCollection', features: [] });
export function recordFeatures(records: MunicipalRecord[]): FeatureCollection<Geometry> {
  return { type: 'FeatureCollection', features: records.filter(r => r.geometry).map(r => ({ type: 'Feature', id: r.id, geometry: r.geometry!, properties: {
    road_id: r.kind === 'road' ? r.id : '', record_id: r.id, name: r.values.name || r.values.on_street || r.source_record_key,
    rating: r.values.rating !== null && r.values.rating !== undefined && Number.isFinite(Number(r.values.rating)) ? Number(r.values.rating) : -1,
    condition: 'unknown', location_basis: r.location_basis || 'source_geometry',
  } })) };
}
export function mapStyle(online: boolean): StyleSpecification {
  return { version: 8, sources: online ? { basemap: { type: 'raster', tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'], tileSize: 256,
    maxzoom: 19, attribution: '© <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">OpenStreetMap contributors</a> · ODbL' } } : {},
    layers: [{ id: 'paper', type: 'background', paint: { 'background-color': '#f1f3f2' } }, ...(online ? [{ id: 'basemap', type: 'raster' as const, source: 'basemap', paint: { 'raster-saturation': -.8, 'raster-opacity': .6, 'raster-contrast': -.12 } }] : [])] };
}
/** Accepted road references remain lines, never fabricated permit points or work zones. */
export function permitMapFeatures(records: MunicipalRecord[], roads: MunicipalRecord[]): FeatureCollection {
  const byId = new Map(roads.map(r => [r.id, r]));
  return recordFeatures(records.flatMap(record => {
    if (record.location_basis === 'source_geometry' && record.geometry) return [record];
    if (record.location_basis === 'matched_road_reference' && record.match?.status === 'matched' && record.match.target_road_id) {
      const road = byId.get(record.match.target_road_id);
      if (road?.geometry) return [{ ...record, geometry: road.geometry }];
    }
    return [];
  }));
}
