import { expect, it } from 'vitest';
import { recordFeatures, permitMapFeatures, mapStyle, pilotColors } from './mapStyle';
import { road, permit, condition, conditionSummary } from '../../test-municipal';
it('preserves geometry and raw fractional ratings without inventing a category', () => {
  const data = recordFeatures([road, condition, permit]); expect(data.features).toHaveLength(2); expect(data.features[0].geometry).toEqual(road.geometry); expect(data.features[1].properties).toMatchObject({ rating: 3.38, condition: 'unknown' });
  expect(recordFeatures([{ ...condition, values: { rating: null } }]).features[0].properties?.rating).toBe(-1);
});
it('maps only server-supported road categories to the pilot palette', () => {
  for (const category of ['good','fair','poor','unknown'] as const) {
    const f = recordFeatures([{...road,condition_summary:{...conditionSummary,category}}]).features[0];
    expect(f.properties?.condition).toBe(category);
  }
  expect(recordFeatures([road]).features[0].properties?.condition).toBe('unknown');
  expect(pilotColors).toEqual({good:'#277953',fair:'#e2b52b',poor:'#c43d3d',unknown:'#859198'});
});
it('never places unlocated or ambiguous permit records; accepted references remain road lines', () => {
  expect(permitMapFeatures([permit], [road]).features).toHaveLength(0);
  const reference = { ...permit, location_basis: 'matched_road_reference' as const, match: { ...condition.match!, status: 'matched' as const, target_road_id: road.id } };
  const result = permitMapFeatures([reference], [road]); expect(result.features[0].geometry).toEqual(road.geometry); expect(result.features[0].properties?.location_basis).toBe('matched_road_reference');
  expect(permitMapFeatures([{ ...reference, match: condition.match }], [road]).features).toHaveLength(0); expect(permitMapFeatures([reference], []).features).toHaveLength(0);
});
it('has a licensed opt-out raster background and no external glyph dependency', () => {
  expect(mapStyle(false).sources).toEqual({}); const style = mapStyle(true); expect(style.sources.basemap).toMatchObject({ type: 'raster', tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'] }); expect(JSON.stringify(style.sources)).toContain('OpenStreetMap contributors'); expect(style.glyphs).toBeUndefined();
});
