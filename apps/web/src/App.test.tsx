import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import App from './App';
import { getEvidence, getRoad, getRoads, getProjects } from './services/api';
import type { RoadsCollection } from './types/api';
// Reuse the reviewed API fixture in tests only; production has no bundled road data.
import { readFileSync } from 'node:fs';
const fixture = readFileSync('../../data/demo/roads.geojson', 'utf8');
const manifest = JSON.parse(readFileSync('../../data/demo/manifest.json', 'utf8'));
vi.mock('./services/api');
vi.mock('./features/map/RoadMap', () => ({
  colors: { good: '#277953', fair: '#bd831f', poor: '#c45e4d', unknown: '#859198' },
  RoadMap: ({ onSelect }: { onSelect: (id: string) => void }) => <button onClick={() => onSelect('demo-r-001')}>Select map segment</button>,
}));
const collection: RoadsCollection = { ...JSON.parse(fixture), meta: {
  request_id: 'test', dataset_snapshot_id: 'demo-m1-v1', warnings: ['DEMO DATA'], next_cursor: null,
} };
beforeEach(() => {
  vi.mocked(getRoads).mockResolvedValue(collection);
  vi.mocked(getProjects).mockResolvedValue({ data: [], meta: collection.meta });
  vi.mocked(getRoad).mockImplementation(async id => {
    const feature = collection.features.find(f => f.id === id)!;
    return { data: { ...feature.properties, geometry: feature.geometry }, meta: collection.meta };
  });
  vi.mocked(getEvidence).mockResolvedValue({ data: manifest.evidence_source as never, meta: collection.meta });
});
describe('workspace', () => {
  it('renders loading state, real dataset metrics and demo disclosure', async () => {
    render(<App/>);
    expect(screen.getByRole('heading', { name: 'Loading the study area' })).toBeInTheDocument();
    await screen.findByRole('region', { name: 'Keyboard accessible road list' });
    const summary = screen.getByRole('region', { name: 'Loaded dataset summary' });
    expect(within(summary).getByText('24')).toBeInTheDocument();
    expect(within(summary).getAllByText('6')).toHaveLength(4);
    expect(screen.getByText('DEMO DATA')).toBeInTheDocument();
    expect(screen.getByText('All road geometries and conditions are synthetic. No NYC municipal observations are displayed.', { exact: false })).toBeInTheDocument();
  });
  it('selects from the list and loads correct details and provenance', async () => {
    const user = userEvent.setup(); render(<App/>);
    const list = await screen.findByRole('region', { name: 'Keyboard accessible road list' });
    await user.click(within(list).getByRole('button', { name: /Demo segment R-001/ }));
    const detail = screen.getByRole('complementary', { name: 'Road details' });
    expect(await within(detail).findByRole('heading', { name: 'Demo segment R-001' })).toBeInTheDocument();
    expect(within(detail).getByText('3 / 10 (demo)')).toBeInTheDocument();
    expect(await within(detail).findByText(manifest.evidence_source.title)).toBeInTheDocument();
    expect(within(list).getByRole('button', { name: /Demo segment R-001/ })).toHaveAttribute('aria-pressed', 'true');
    await user.click(within(list).getByRole('button', { name: /Demo segment R-004/ }));
    await within(detail).findByRole('heading', { name: 'Demo segment R-004' });
    expect(within(detail).queryByText('3 / 10 (demo)')).not.toBeInTheDocument();
    expect(within(detail).getAllByText('Unknown').length).toBeGreaterThan(1);
  });
  it('keeps map selection in React state and filters list without changing dataset counts', async () => {
    const user = userEvent.setup(); render(<App/>);
    await user.click(await screen.findByRole('button', { name: 'Select map segment' }));
    expect(await screen.findByRole('heading', { name: 'Demo segment R-001' })).toBeInTheDocument();
    await user.type(screen.getByRole('textbox', { name: 'Find road segments' }), 'absent');
    expect(screen.getByText('No segments match this search.')).toBeInTheDocument();
    expect(within(screen.getByRole('region', { name: 'Loaded dataset summary' })).getByText('24')).toBeInTheDocument();
  });
  it('supports keyboard road selection', async () => {
    const user = userEvent.setup(); render(<App/>);
    const list = await screen.findByRole('region', { name: 'Keyboard accessible road list' });
    const road = within(list).getByRole('button', { name: /Demo segment R-002/ });
    road.focus(); await user.keyboard('{Enter}');
    expect(await screen.findByRole('heading', { name: 'Demo segment R-002' })).toBeInTheDocument();
  });
  it('handles API failure and retry', async () => {
    vi.mocked(getRoads).mockRejectedValueOnce(new Error('API unavailable'));
    const user = userEvent.setup(); render(<App/>);
    expect(await screen.findByRole('alert')).toHaveTextContent('Unable to load road data');
    await user.click(screen.getByRole('button', { name: 'Retry connection' }));
    await screen.findByRole('region', { name: 'Keyboard accessible road list' });
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });
  it('handles empty records without fabricated metrics', async () => {
    vi.mocked(getRoads).mockResolvedValue({ ...collection, features: [] });
    render(<App/>);
    await screen.findByRole('heading', { name: 'No road segments loaded' });
    expect(within(screen.getByRole('region', { name: 'Loaded dataset summary' })).getAllByText('0')).toHaveLength(5);
  });
  it('handles detail failures while retaining list and map', async () => {
    vi.mocked(getRoad).mockRejectedValue(new Error('Road not available'));
    const user = userEvent.setup(); render(<App/>);
    await user.click(await screen.findByRole('button', { name: 'Select map segment' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Road not available');
    expect(screen.getByRole('region', { name: 'Keyboard accessible road list' })).toBeInTheDocument();
    await waitFor(() => expect(getRoad).toHaveBeenCalled());
  });
});

it('loads the M3 analysis and filters findings using project selection', async () => {
  const { projects, analysis } = await import('./features/conflicts/testData');
  const { analyzeConflicts } = await import('./services/api');
  vi.mocked(getProjects).mockResolvedValue({ data: projects, meta: collection.meta });
  vi.mocked(analyzeConflicts).mockResolvedValue({ data: analysis, meta: collection.meta });
  const user = userEvent.setup(); render(<App/>);
  const review = await screen.findByRole('region', { name: 'Project coordination and conflict review' });
  const finding = await within(review).findByRole('button', { name: /Potential pavement rework/ });
  await user.click(finding);
  expect(await within(review).findByRole('article', { name: 'Selected conflict evidence' })).toHaveTextContent('Sequential gap: 2');
  await user.click(within(review).getByRole('button', { name: /Fictional distant telecom inspection/ }));
  expect(within(review).getByText(/No conflicts detected in the checked records/)).toBeInTheDocument();
  await user.click(within(review).getByRole('button', { name: 'Show all conflicts' }));
  expect(within(review).getByRole('button', { name: /Potential pavement rework/ })).toBeInTheDocument();
  expect(analyzeConflicts).toHaveBeenCalledWith('demo-m1-v1', projects.map(p => p.id), expect.any(AbortSignal));
});

it('keeps roads usable when project data fail and retries M3 independently', async () => {
  vi.mocked(getProjects).mockRejectedValueOnce(new Error('Project storage unavailable'));
  const user = userEvent.setup(); render(<App/>);
  expect(await screen.findByRole('alert')).toHaveTextContent('Project storage unavailable');
  expect(screen.getByRole('region', { name: 'Keyboard accessible road list' })).toBeInTheDocument();
  await user.click(screen.getByRole('button', { name: 'Retry project analysis' }));
  await waitFor(() => expect(screen.queryByRole('alert')).not.toBeInTheDocument());
  expect(screen.getByText('No project records loaded. Utility coverage remains unknown.')).toBeInTheDocument();
});
it('rejects mismatched project snapshots before analysis', async () => {
  vi.mocked(getProjects).mockResolvedValue({ data: [], meta: { ...collection.meta, dataset_snapshot_id: 'different' } });
  render(<App/>);
  expect(await screen.findByRole('alert')).toHaveTextContent('Project snapshot differs from roads');
});

it('guides the loaded demo records without creating substitute data', async () => {
  const { projects, analysis } = await import('./features/conflicts/testData');
  const { analyzeConflicts } = await import('./services/api');
  vi.mocked(getProjects).mockResolvedValue({ data: projects, meta: collection.meta });
  vi.mocked(analyzeConflicts).mockResolvedValue({ data: analysis, meta: collection.meta });
  const user = userEvent.setup(); render(<App/>);
  await user.click(screen.getByRole('button', { name: 'Explore Demo' }));
  const guide = await screen.findByRole('region', { name: 'Synthetic demo guide' });
  await user.click(within(guide).getByRole('button', { name: /Inspect demo road/ }));
  expect(await screen.findByRole('heading', { name: 'Demo segment R-001' })).toBeInTheDocument();
  await waitFor(() => expect(within(guide).getByRole('button', { name: /Review potential/ })).toBeEnabled());
  await user.click(within(guide).getByRole('button', { name: /Review potential/ }));
  expect(await screen.findByRole('article', { name: 'Selected conflict evidence' })).toHaveTextContent('Sequential gap: 2');
});
it('keeps unavailable demo data explicit and compact navigation named', async () => {
  vi.mocked(getRoads).mockResolvedValue({ ...collection, features: collection.features.slice(1) });
  const user = userEvent.setup(); render(<App/>);
  await user.click(screen.getByRole('button', { name: 'Explore Demo' }));
  const guide = await screen.findByRole('region', { name: 'Synthetic demo guide' });
  expect(within(guide).getByRole('button', { name: /Inspect demo road/ })).toBeDisabled();
  expect(guide).toHaveTextContent('Primary demo road is absent');
  expect(screen.getByRole('button', { name: 'Infrastructure map' })).toHaveAttribute('title');
  expect(screen.getByRole('button', { name: 'Scenario planner' })).toHaveAttribute('aria-expanded', 'false');
});
it('reopening scenario navigation preserves the unsaved editor', async () => {
  const { getScenarios, getRepairCatalog } = await import('./services/api');
  vi.mocked(getScenarios).mockResolvedValue({data:[],meta:collection.meta});
  vi.mocked(getRepairCatalog).mockResolvedValue({data:[],meta:collection.meta});
  const user=userEvent.setup(); render(<App/>);
  await screen.findByRole('region',{name:'Keyboard accessible road list'});
  const navigation=screen.getByRole('button',{name:'Scenario planner'});
  await user.click(navigation);
  await waitFor(()=>expect(screen.getByRole('button',{name:'Create scenario'})).toBeEnabled());
  await user.click(screen.getByRole('button',{name:'Create scenario'}));
  await user.type(screen.getByRole('textbox',{name:'Name'}),'Unfinished review plan');
  await user.click(navigation);
  expect(screen.getByRole('textbox',{name:'Name'})).toHaveValue('Unfinished review plan');
});
