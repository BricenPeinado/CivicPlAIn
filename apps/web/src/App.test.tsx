import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import App from './App';
import { getEvidence, getRoad, getRoads } from './services/api';
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
