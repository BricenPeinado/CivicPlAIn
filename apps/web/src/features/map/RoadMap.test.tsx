import { StrictMode } from 'react';
import { act, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, expect, it, vi } from 'vitest';
import { RoadMap } from './RoadMap';
import type { RoadsCollection } from '../../types/api';
const state = vi.hoisted(() => ({ maps: [] as any[] }));
vi.mock('maplibre-gl', () => ({
  setWorkerUrl: vi.fn(), NavigationControl: class {}, AttributionControl: class {},
  Map: class {
    handlers = new Map<string, (...args: any[]) => void>();
    canvas = document.createElement('canvas');
    source = { setData: vi.fn() };
    setFilter = vi.fn(); addControl = vi.fn(); addSource = vi.fn(); addLayer = vi.fn();
    fitBounds = vi.fn(); resize = vi.fn(); remove = vi.fn();
    constructor() { state.maps.push(this); }
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
  expect(screen.getByText('Demo segment R-001 · Demo data')).toBeInTheDocument();
  act(() => map.handlers.get('error')());
  expect(screen.getByRole('alert')).toHaveTextContent('Use the road list below');
  expect(screen.getByRole('button', {name:/Study area/})).toBeDisabled();
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
  expect(screen.getByRole('button', {name:/Study area/})).toBeEnabled();
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
