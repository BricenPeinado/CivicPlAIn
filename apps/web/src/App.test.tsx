import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import App from './App';
import { getEvidence, getRoad, getRoads, getProjects, analyzeConflicts } from './services/api';
import { getWorkspace, getSnapshots, getSnapshot } from './services/municipal';
import type { RoadsCollection } from './types/api';
import { readFileSync } from 'node:fs';
const fixture = readFileSync('../../data/demo/roads.geojson', 'utf8');
const manifest = JSON.parse(readFileSync('../../data/demo/manifest.json', 'utf8'));
vi.mock('./services/api'); vi.mock('./services/municipal');
vi.mock('./features/map/RoadMap', () => ({ RoadMap: ({ onSelect }: { onSelect: (id: string) => void }) => <button onClick={() => onSelect('demo-r-001')}>Select map segment</button> }));
const collection: RoadsCollection = { ...JSON.parse(fixture), meta: { request_id: 'test', dataset_snapshot_id: 'demo-m1-v1', warnings: ['DEMO DATA'], next_cursor: null } };
beforeEach(() => {
  window.history.replaceState(null, '', '/');
  vi.mocked(getWorkspace).mockResolvedValue({ mode: 'synthetic', snapshot_id: 'demo-m1-v1' }); vi.mocked(getSnapshots).mockResolvedValue([]);
  vi.mocked(getRoads).mockResolvedValue(collection); vi.mocked(getProjects).mockResolvedValue({ data: [], meta: collection.meta });
  vi.mocked(getRoad).mockImplementation(async id => { const f = collection.features.find(f => f.id === id)!; return { data: { ...f.properties, geometry: f.geometry }, meta: collection.meta }; });
  vi.mocked(getEvidence).mockResolvedValue({ data: manifest.evidence_source as never, meta: collection.meta });
});
async function openList(user: ReturnType<typeof userEvent.setup>) { await user.click(await screen.findByRole('button', { name: 'Open street list' })); return screen.getByRole('region', { name: 'Keyboard accessible road list' }); }
async function nav(user: ReturnType<typeof userEvent.setup>, name: string) { await user.click(screen.getByRole('link', { name: ({Map:'Infrastructure map',Dashboard:'Overview',Projects:'Projects & coordination',Scenarios:'Scenario planner'} as Record<string,string>)[name] || name })); }
describe('map-first workspace', () => {
  it('opens on the map with concise synthetic disclosure and focused navigation', async () => {
    render(<App/>); await screen.findByRole('button', { name: 'Select map segment' });
    expect(screen.getByRole('combobox', { name: 'Dataset mode' })).toHaveValue('synthetic');
    expect(screen.getByText(/All geometry, conditions and costs/)).toBeInTheDocument();
    expect(screen.queryByRole('region', { name: 'Loaded dataset summary', hidden: true })).not.toBeVisible();
    expect(screen.queryByText('Explore Demo')).not.toBeInTheDocument(); expect(analyzeConflicts).not.toHaveBeenCalled();
    expect(screen.getAllByRole('link').filter(l => l.getAttribute('aria-current') === 'page')).toHaveLength(1);
  });
  it('selects with the keyboard and preserves source evidence and unknowns', async () => {
    const user = userEvent.setup(); render(<App/>); const list = await openList(user);
    const first = within(list).getByRole('button', { name: /Demo segment R-001/ }); first.focus(); await user.keyboard('{Enter}');
    const detail = screen.getByRole('complementary', { name: 'Road details' });
    await within(detail).findByRole('heading', { name: 'Demo segment R-001' }); expect(within(detail).getByText('3 / 10 (demo)')).toBeInTheDocument();
    await user.click(within(detail).getByText('Attributes and provenance')); expect(await within(detail).findByText(manifest.evidence_source.title)).toBeInTheDocument();
    expect(first).toHaveAttribute('aria-pressed', 'true');
    await user.click(within(list).getByRole('button', { name: /Demo segment R-004/ })); await within(detail).findByRole('heading', { name: 'Demo segment R-004' });
    expect(within(detail).queryByText('3 / 10 (demo)')).not.toBeInTheDocument(); expect(within(detail).getAllByText('Unknown').length).toBeGreaterThan(1);
  });
  it('keeps map selection while filtering streets; dashboard counts stay snapshot-wide', async () => {
    const user = userEvent.setup(); render(<App/>); await user.click(await screen.findByRole('button', { name: 'Select map segment' })); await screen.findByRole('heading', { name: 'Demo segment R-001' });
    await user.type(screen.getByRole('textbox', { name: 'Find road segments' }), 'absent'); expect(screen.getByText('No segments match this search.')).toBeInTheDocument();
    await nav(user, 'Dashboard'); const summary = screen.getByRole('region', { name: 'Loaded dataset summary' }); expect(within(summary).getByText('24')).toBeInTheDocument(); expect(within(summary).getAllByText('6')).toHaveLength(4);
    expect(screen.queryByRole('button', { name: 'Select map segment', hidden: true })).not.toBeVisible();
  });
  it('handles API failures and retry without substitute roads', async () => {
    vi.mocked(getRoads).mockRejectedValueOnce(new Error('API unavailable')); const user = userEvent.setup(); render(<App/>);
    expect(await screen.findByRole('alert')).toHaveTextContent('Unable to load road data'); await user.click(screen.getByRole('button', { name: 'Retry connection' })); await openList(user); expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });
  it('shows an empty inventory without invented records', async () => {
    vi.mocked(getRoads).mockResolvedValue({ ...collection, features: [] }); const user = userEvent.setup(); render(<App/>); const list = await openList(user); expect(list).toHaveTextContent('No segments match'); await nav(user, 'Dashboard'); expect(within(screen.getByRole('region', { name: 'Loaded dataset summary' })).getAllByText('0')).toHaveLength(5);
  });
  it('retains map and street list after a detail failure', async () => {
    vi.mocked(getRoad).mockRejectedValue(new Error('Road not available')); const user = userEvent.setup(); render(<App/>); await openList(user); await user.click(screen.getByRole('button', { name: 'Select map segment' })); expect(await screen.findByRole('alert')).toHaveTextContent('Road not available'); expect(screen.getByRole('region', { name: 'Keyboard accessible road list' })).toBeVisible();
  });
  it('runs screening only on explicit action and retains finding selection', async () => {
    const { projects, analysis } = await import('./features/conflicts/testData'); vi.mocked(getProjects).mockResolvedValue({ data: projects, meta: collection.meta }); vi.mocked(analyzeConflicts).mockResolvedValue({ data: analysis, meta: collection.meta });
    const user = userEvent.setup(); render(<App/>); await screen.findByRole('button', { name: 'Select map segment' }); await nav(user, 'Projects'); const review = screen.getByRole('region', { name: 'Project coordination and conflict review' });
    expect(review).toHaveTextContent('Screening has not been run'); expect(analyzeConflicts).not.toHaveBeenCalled(); await user.click(screen.getByRole('button', { name: 'Run conflict screening' }));
    await user.click(await within(review).findByRole('button', { name: /Potential pavement rework/ })); expect(await within(review).findByRole('article', { name: 'Selected conflict evidence' })).toHaveTextContent('Sequential gap: 2');
    await user.click(within(review).getByRole('button', { name: /Fictional distant telecom inspection/ })); expect(review).toHaveTextContent('No conflicts detected in the checked records'); await user.click(within(review).getByRole('button', { name: 'Show all conflicts' })); expect(within(review).getByRole('button', { name: /Potential pavement rework/ })).toBeInTheDocument();
    expect(analyzeConflicts).toHaveBeenCalledOnce();
  });
  it('isolates project failures from the map and retries independently', async () => {
    vi.mocked(getProjects).mockRejectedValueOnce(new Error('Project storage unavailable')); const user = userEvent.setup(); render(<App/>); await openList(user); expect(screen.getByRole('region', { name: 'Keyboard accessible road list' })).toBeVisible(); await nav(user, 'Projects'); expect(await screen.findByRole('alert')).toHaveTextContent('Project storage unavailable'); await user.click(screen.getByRole('button', { name: 'Retry project analysis' })); await waitFor(() => expect(screen.queryByRole('alert')).not.toBeInTheDocument()); expect(screen.getByText('No project records loaded. Utility coverage remains unknown.')).toBeVisible();
  });
  it('rejects mismatched project snapshots before screening', async () => {
    vi.mocked(getProjects).mockResolvedValue({ data: [], meta: { ...collection.meta, dataset_snapshot_id: 'other' } }); const user = userEvent.setup(); render(<App/>); await screen.findByRole('button', { name: 'Select map segment' }); await nav(user, 'Projects'); expect(await screen.findByRole('alert')).toHaveTextContent('Project snapshot differs from roads'); expect(analyzeConflicts).not.toHaveBeenCalled();
  });
  it('preserves scenario drafts across views and explicit dataset switches', async () => {
    const { getScenarios, getRepairCatalog } = await import('./services/api'); vi.mocked(getScenarios).mockResolvedValue({ data: [], meta: collection.meta }); vi.mocked(getRepairCatalog).mockResolvedValue({ data: [], meta: collection.meta });
    const user = userEvent.setup(); render(<App/>); await screen.findByRole('button', { name: 'Select map segment' }); await nav(user, 'Scenarios'); await user.click(await screen.findByRole('button', { name: 'Create scenario' })); await user.type(screen.getByRole('textbox', { name: 'Name' }), 'Unfinished review plan'); const unload = new Event('beforeunload', { cancelable: true }); window.dispatchEvent(unload); expect(unload.defaultPrevented).toBe(true);
    await nav(user, 'Map'); await nav(user, 'Scenarios'); expect(screen.getByRole('textbox', { name: 'Name' })).toHaveValue('Unfinished review plan');
    await user.selectOptions(screen.getByRole('combobox', { name: 'Dataset mode' }), 'official'); expect(await screen.findByRole('heading', { name: 'Official data unavailable' })).toBeInTheDocument(); await user.selectOptions(screen.getByRole('combobox', { name: 'Dataset mode' }), 'synthetic'); expect(screen.getByRole('textbox', { name: 'Name' })).toHaveValue('Unfinished review plan');
  });
  it('fails closed for unavailable official snapshot without loading synthetic records', async () => {
    window.history.replaceState(null, '', '/#/map?mode=official&snapshot=nyc-11111111111111111111111111111111'); vi.mocked(getSnapshot).mockRejectedValue(new Error('Published snapshot not found')); render(<App/>); expect(await screen.findByRole('heading', { name: 'Official data unavailable' })).toBeVisible(); expect(getRoads).not.toHaveBeenCalled(); expect(screen.queryByText('Synthetic geometry')).not.toBeInTheDocument();
  });
  it('offers a named invalid-link state without data mutations', async () => {
    window.history.replaceState(null, '', '/#/no-such-page'); const user = userEvent.setup(); render(<App/>); expect(screen.getByRole('alert')).toHaveTextContent('Page not found'); await user.click(screen.getByRole('button', { name: 'Return to map' })); await screen.findByRole('button', { name: 'Select map segment' }); expect(analyzeConflicts).not.toHaveBeenCalled();
  });
});

it('a direct dashboard link does not instantiate a map', async () => {
  window.history.replaceState(null, '', '/#/dashboard?mode=synthetic'); render(<App/>); await screen.findByRole('region', { name: 'Loaded dataset summary' }); expect(screen.queryByText('Select map segment')).not.toBeInTheDocument(); expect(analyzeConflicts).not.toHaveBeenCalled();
});
