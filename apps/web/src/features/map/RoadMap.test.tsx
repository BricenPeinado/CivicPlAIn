import { StrictMode } from 'react';
import { act, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, expect, it, vi } from 'vitest';
import { RoadMap } from './RoadMap';
import type { RoadsCollection } from '../../types/api';
import { pilotColors } from './mapStyle';
const state = vi.hoisted(() => ({ maps: [] as any[] }));
vi.mock('maplibre-gl', () => ({
  setWorkerUrl: vi.fn(), NavigationControl: class {}, AttributionControl: class {},
  Map: class {
    handlers = new Map<string, (...args: any[]) => void>();
    canvas = document.createElement('canvas');
    source = { setData: vi.fn() };
    queryRenderedFeatures = vi.fn(() => []); setLayoutProperty = vi.fn(); getLayer = vi.fn(() => true);
    getBounds() { return { getWest: () => -74.01, getSouth: () => 40.71, getEast: () => -74.0, getNorth: () => 40.72 }; }
    setFilter = vi.fn(); addControl = vi.fn(); addSource = vi.fn(); addLayer = vi.fn();
    fitBounds = vi.fn(); resize = vi.fn(); remove = vi.fn();
    constructor(public options: any) { state.maps.push(this); }
    on(event: string, layerOrHandler: string | ((...args: any[]) => void), handler?: (...args: any[]) => void) {
      this.handlers.set(handler ? `${event}:${layerOrHandler}` : event, handler || layerOrHandler as (...args: any[]) => void);
    }
    getCanvas() { return this.canvas; }
    getSource() { return this.source; }
  },
}));
vi.stubGlobal('ResizeObserver', class { observe() {} disconnect() {} });
afterEach(() => { state.maps = []; });
const roads = { type: 'FeatureCollection', features: [{ type: 'Feature', id: 'demo-r-001',
  geometry: { type: 'LineString', coordinates: [[-74.01,40.71],[-74.009,40.711]] },
  properties: { id:'demo-r-001', name:'Demo segment R-001', condition_summary: { category:'poor' } },
}], meta: { next_cursor:null } } as RoadsCollection;
it('uses the pilot green/yellow/red/gray palette for official road classifications', () => {
  render(<RoadMap official features={{type:'FeatureCollection',features:[]}} selectedId={null} onSelect={vi.fn()}/>);
  const map=state.maps[0];act(()=>map.handlers.get('load')());
  const layer=map.addLayer.mock.calls.map((c:any[])=>c[0]).find((l:any)=>l.id==='road-color');
  expect(layer.paint['line-color']).toEqual(['match',['get','condition'],'good',pilotColors.good,'fair',pilotColors.fair,'poor',pilotColors.poor,pilotColors.unknown]);
});
it('transports stable IDs to MapLibre properties and updates selection highlighting', () => {
  const onSelect = vi.fn();
  const rendered = render(<RoadMap roads={roads} selectedId={null} onSelect={onSelect}/>);
  const map = state.maps[0];
  act(() => map.handlers.get('load')());
  expect(map.source.setData.mock.calls[0][0].features[0].properties.road_id).toBe('demo-r-001');
  act(() => map.handlers.get('click:road-hit')({ features:[{properties:{road_id:'demo-r-001'}}] }));
  expect(onSelect).toHaveBeenCalledWith('demo-r-001');
  rendered.rerender(<RoadMap roads={roads} selectedId="demo-r-001" onSelect={onSelect}/>);
  expect(map.setFilter).toHaveBeenLastCalledWith('road-selected', ['==', ['get','road_id'], 'demo-r-001']);
});
it('shows hover feedback and preserves the list fallback on map errors', () => {
  render(<RoadMap roads={roads} selectedId={null} onSelect={vi.fn()}/>);
  const map = state.maps[0];
  act(() => map.handlers.get('load')());
  act(() => map.handlers.get('mousemove:road-hit')({features:[{properties:{road_id:'demo-r-001',name:'Demo segment R-001'}}]}));
  expect(screen.getByText('Demo segment R-001 · Synthetic fixture')).toBeInTheDocument();
  act(() => map.handlers.get('error')());
  expect(screen.getByRole('alert')).toHaveTextContent('Search and the street list');
  expect(screen.getByRole('button', {name:/Return to study focus/})).toBeDisabled();
});
it('handles WebGL context loss and cleans up the instance', () => {
  const rendered = render(<RoadMap roads={roads} selectedId={null} onSelect={vi.fn()}/>);
  const map = state.maps[0];
  act(() => map.handlers.get('load')());
  fireEvent(map.canvas, new Event('webglcontextlost'));
  expect(screen.getByRole('alert')).toBeInTheDocument();
  rendered.unmount();
  expect(map.remove).toHaveBeenCalledOnce();
});

it('ignores late errors from the disposed StrictMode instance', () => {
  render(<StrictMode><RoadMap roads={roads} selectedId={null} onSelect={vi.fn()}/></StrictMode>);
  expect(state.maps).toHaveLength(2);
  act(() => state.maps[0].handlers.get('error')());
  act(() => state.maps[1].handlers.get('load')());
  expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  expect(screen.getByRole('button', {name:/Return to study focus/})).toBeEnabled();
});

it('renders project geometry, toggles the work-zone source and highlights all finding assets', async () => {
  const { projects } = await import('../conflicts/testData');
  const { infrastructureCategories } = await import('../../types/api');
  const onProject = vi.fn();
  const props = { roads, selectedId: null, onSelect: vi.fn(), projects, visibleCategories: [...infrastructureCategories],
    highlightedProjects: ['demo-road-project', 'demo-utility-project'], highlightedRoads: ['demo-r-001'], onSelectProject: onProject };
  const view = render(<RoadMap {...props}/>);
  const map = state.maps[0]; act(() => map.handlers.get('load')());
  const projectData = map.source.setData.mock.calls.at(-1)[0];
  expect(projectData.features).toHaveLength(projects.filter(p => p.geometry).length);
  expect(projectData.features.some((f: any) => f.id === 'demo-unknown-location')).toBe(false);
  expect(map.setFilter).toHaveBeenCalledWith('project-selected', ['in', ['get', 'project_id'], ['literal', props.highlightedProjects]]);
  expect(map.setFilter).toHaveBeenCalledWith('road-conflict', ['in', ['get', 'road_id'], ['literal', ['demo-r-001']]]);
  act(() => map.handlers.get('click:project-fill')({ features: [{ properties: { project_id: 'demo-road-project' } }] }));
  expect(onProject).toHaveBeenCalledWith('demo-road-project');
  view.rerender(<RoadMap {...props} showProjects={false}/>);
  expect(map.source.setData.mock.calls.at(-1)[0].features).toEqual([]);
  view.rerender(<RoadMap {...props} visibleCategories={['water']}/>);
  expect(map.source.setData.mock.calls.at(-1)[0].features.every((f: any) => f.properties.category === 'water')).toBe(true);
});

it('isolates tile failure while keeping official layers interactive and independently visible', () => {
  const layers = { streets: true, conditions: false, permits: false, shoreline: true, basemap: true };
  const onSelect = vi.fn(), onViewport = vi.fn();
  const view = render(<RoadMap official selectedId={null} onSelect={onSelect} layers={layers} onViewport={onViewport}/>);
  const map = state.maps[0]; act(() => map.handlers.get('load')());
  act(() => map.handlers.get('error')({ sourceId: 'basemap' }));
  expect(screen.getByRole('status')).toHaveTextContent('Official layers remain available'); expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  act(() => map.handlers.get('click:road-hit')({ features: [{ properties: { road_id: 'road-real' } }] })); expect(onSelect).toHaveBeenCalledWith('road-real');
  view.rerender(<RoadMap official selectedId={null} onSelect={onSelect} layers={{ ...layers, conditions: true, streets: false }} onViewport={onViewport}/>);
  expect(map.setLayoutProperty).toHaveBeenCalledWith('observations', 'visibility', 'visible'); expect(map.setLayoutProperty).toHaveBeenCalledWith('road-hit', 'visibility', 'none'); expect(map.setLayoutProperty).toHaveBeenLastCalledWith('basemap', 'visibility', 'none');
  act(() => map.handlers.get('moveend')()); expect(onViewport).toHaveBeenCalledWith([-74.01,40.71,-74.0,40.72]);
});
it('preserves records while exposing an official source-rendering failure', () => {
  render(<RoadMap official selectedId={null} onSelect={vi.fn()}/>); const map = state.maps[0]; act(() => map.handlers.get('load')()); act(() => map.handlers.get('error')({ sourceId: 'roads' })); expect(screen.getByRole('status')).toHaveTextContent('A map layer could not render'); expect(screen.getByRole('button', { name: 'Return to study focus' })).toBeEnabled();
});

it('draws supplied screening shapes above road selection and clears the overlay independently', () => {
  const shapes={type:'FeatureCollection' as const,features:[{type:'Feature' as const,id:'work:test',properties:{evidence:'SYNTHETIC TEST supplied geometry'},geometry:{type:'LineString' as const,coordinates:[[-74.01,40.712],[-74.009,40.712]]}}]};
  const view=render(<RoadMap official screeningFeatures={shapes} selectedId={null} onSelect={vi.fn()}/>);
  const map=state.maps[0];act(()=>map.handlers.get('load')());
  const layers=map.addLayer.mock.calls.map((call:any[])=>call[0].id);
  expect(layers.indexOf('screening-lines')).toBeGreaterThan(layers.indexOf('selection'));
  expect(map.addSource).toHaveBeenCalledWith('screening',expect.anything());
  expect(map.source.setData).toHaveBeenCalledWith(shapes);
  const empty={type:'FeatureCollection' as const,features:[]};
  view.rerender(<RoadMap official screeningFeatures={empty} selectedId={null} onSelect={vi.fn()}/>);
  expect(map.source.setData).toHaveBeenCalledWith(empty);
});

it('keeps priority and permit candidate reference overlays distinct from observed condition and supplied work',()=>{
 const priorities={type:'FeatureCollection' as const,features:[{type:'Feature' as const,properties:{road_id:'r',priority_status:'unranked'},geometry:{type:'LineString' as const,coordinates:[[-74.01,40.71],[-74.009,40.71]]}}]};
 const candidates={...priorities,features:priorities.features.map(f=>({...f,properties:{road_id:'r',record_id:'p',evidence:'Candidate reference, not footprint'}}))};
 render(<RoadMap official priorityFeatures={priorities} candidateFeatures={candidates} selectedId={null} onSelect={vi.fn()}/>);
 const map=state.maps[0];act(()=>map.handlers.get('load')());
 const layers=map.addLayer.mock.calls.map((v:any[])=>v[0]);
 expect(layers.find((l:any)=>l.id==='priorities').paint['line-color']).toEqual(['match',['get','priority_status'],'ranked','#7951a6','#667385']);
 expect(layers.find((l:any)=>l.id==='permit-candidates').paint['line-dasharray']).toEqual([1,2]);
 expect(map.source.setData).toHaveBeenCalledWith(priorities);expect(map.source.setData).toHaveBeenCalledWith(candidates);
});
it('initializes locally before attaching online tiles and only updates changed sources',()=>{
 const features={type:'FeatureCollection' as const,features:[]};
 const props={official:true,features,selectedId:null,onSelect:vi.fn()};const view=render(<RoadMap {...props}/>),map=state.maps[0];
 expect(map.options.style.sources).toEqual({});act(()=>map.handlers.get('load')());const count=map.source.setData.mock.calls.length;
 view.rerender(<RoadMap {...props} candidateFeatures={{type:'FeatureCollection',features:[]}}/>);expect(map.source.setData).toHaveBeenCalledTimes(count);
 const layers={streets:true,ratings:true,conditions:false,permits:false,shoreline:true,basemap:true};
 view.rerender(<RoadMap {...props} layers={layers}/>);view.rerender(<RoadMap {...props} layers={{...layers,ratings:false,basemap:false}}/>);
 expect(state.maps).toHaveLength(1);expect(map.source.setData).toHaveBeenCalledTimes(count);expect(map.setLayoutProperty).toHaveBeenCalledWith('indicative-ratings','visibility','none');
 const ids=map.addLayer.mock.calls.map((c:any[])=>c[0].id);expect(ids).toContain('indicative-ratings');expect(ids.indexOf('indicative-ratings')).toBeLessThan(ids.indexOf('selection'));
});
it('allows clicking the rating line independently of official street visibility',()=>{
 const select=vi.fn();render(<RoadMap official selectedId={null} onSelect={select}/>);const map=state.maps[0];act(()=>map.handlers.get('load')());
 act(()=>map.handlers.get('click:rating-hit')({features:[{properties:{road_id:'road-standardized'}}]}));expect(select).toHaveBeenCalledWith('road-standardized');
});
