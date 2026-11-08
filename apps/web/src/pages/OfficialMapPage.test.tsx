import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, expect, it, vi } from 'vitest';
import { OfficialMapPage } from './OfficialMapPage';
import { getMunicipalViewport, getMunicipalRoad, getMunicipalPage, getRoadConditions, getShoreline, getSource } from '../services/municipal';
import { meta, road, condition, snapshot, permit } from '../test-municipal';
vi.mock('../services/municipal');
vi.mock('../features/map/RoadMap', () => ({ RoadMap: (p: any) => <div aria-label="Test map"><button onClick={() => p.onSelect(road.id)}>Select street</button><button onClick={() => p.onObservation(condition.id)}>Select observation</button><button onClick={() => p.onViewport([-74.009,40.711,-74.004,40.715])}>Pan map</button><output aria-label="Visible streets">{p.layers.streets ? p.features.features.length : 0}</output><output aria-label="Visible observations">{p.layers.conditions ? p.observations.features.length : 0}</output></div> }));
beforeEach(() => {
  vi.mocked(getMunicipalViewport).mockImplementation(async kind => kind === 'roads' ? [road] : kind === 'conditions' ? [condition] : []);
  vi.mocked(getMunicipalRoad).mockResolvedValue(road); vi.mocked(getMunicipalPage).mockResolvedValue({ data: [], meta: { ...meta, total_matching: 0 } });
  vi.mocked(getRoadConditions).mockResolvedValue({ data: [], meta: { ...meta, total_matching: 0, latest_usable_id: null } }); vi.mocked(getShoreline).mockResolvedValue({ type: 'FeatureCollection', features: [] });
  vi.mocked(getSource).mockResolvedValue({ id: 'test-source', source_id: 'test', source_url: 'https://nyc.gov', endpoint: 'https://nyc.gov', retrieved_at: '2026-11-01', source_updated_at: null, release_note: 'test', source_crs: 'EPSG:2263', attribution: 'Test provenance', cadence: 'monthly', raw_sha256: 'abc', dictionary_sha256: 'def', dictionary_url: 'https://nyc.gov', license: { identifier: null, note: 'Test license' }, terms_urls: [] });
});
it('loads real-mode records, independent layers and a keyboard street list', async () => {
  const user = userEvent.setup(), select = vi.fn(); render(<OfficialMapPage snapshot={snapshot} selected={null} onSelect={select} onProjects={vi.fn()}/>);
  await waitFor(() => expect(screen.getByLabelText('Visible streets')).toHaveTextContent('1')); expect(screen.getByRole('heading', { name: 'Start with a street.' })).toBeVisible(); expect(getMunicipalViewport).not.toHaveBeenCalledWith('conditions', expect.anything(), expect.anything(), expect.anything());
  await user.click(screen.getByRole('button', { name: 'Layers' })); await user.click(screen.getByRole('checkbox', { name: 'Pavement observations' })); await waitFor(() => expect(screen.getByLabelText('Visible observations')).toHaveTextContent('1'));
  await user.click(screen.getByRole('checkbox', { name: 'Official streets' })); expect(screen.getByLabelText('Visible streets')).toHaveTextContent('0'); expect(screen.getByLabelText('Visible observations')).toHaveTextContent('1');
  await user.click(screen.getByRole('button', { name: 'Open street list' })); const list = screen.getByRole('region', { name: 'Keyboard accessible road list' }); const street = within(list).getByRole('button', { name: /Test Street/ }); street.focus(); await user.keyboard('{Enter}'); expect(select).toHaveBeenCalledWith(road.id);
  await user.keyboard('{Escape}'); expect(screen.queryByRole('region', { name: 'Keyboard accessible road list' })).not.toBeInTheDocument(); expect(screen.getByRole('textbox', { name: 'Find road segments' })).toHaveFocus();
});
it('does not present ambiguous ratings or unlocated permits as road evidence', async () => {
  render(<OfficialMapPage snapshot={snapshot} selected={road.id} onSelect={vi.fn()} onProjects={vi.fn()}/>); expect(await screen.findByText('No accepted road assessment')).toBeVisible(); expect(screen.queryByText('3.38')).not.toBeInTheDocument();
  const related = screen.getByText('Related permit records (0)'); fireEvent.click(related); expect(screen.getByText(/No accepted permit links/)).toBeVisible(); expect(getMunicipalPage).toHaveBeenCalledWith('permits', snapshot.id, { road_id: road.id }, expect.any(AbortSignal));
  fireEvent.click(screen.getByText('Provenance and limitations')); expect(await screen.findByText('Test provenance')).toBeVisible(); expect(screen.getByText('2026-11-01')).toBeVisible();
});
it('shows raw inspection date, rating and uncertainty separately', async () => {
  const user = userEvent.setup(); render(<OfficialMapPage snapshot={snapshot} selected={null} onSelect={vi.fn()} onProjects={vi.fn()}/>);
  await user.click(screen.getByRole('button', { name: 'Layers' })); await user.click(screen.getByRole('checkbox', { name: 'Pavement observations' })); await waitFor(() => expect(screen.getByLabelText('Visible observations')).toHaveTextContent('1')); await user.click(screen.getByRole('button', { name: 'Select observation' }));
  expect(screen.getByText('3.38 / 10')).toBeVisible(); expect(screen.getByText(/2025-08-03 \(source local date\)/)).toBeVisible(); expect(screen.getByTitle('2025-08-03T00:00:00.000')).toBeVisible(); expect(screen.getByText(/not an accepted link/)).toBeVisible();
});
it('offers inspection and located permit evidence by keyboard without enabling their map layers', async () => {
  vi.mocked(getMunicipalViewport).mockImplementation(async kind => kind === 'roads' ? [road] : kind === 'conditions' ? [condition] : [{ ...permit, geometry: road.geometry, bbox: road.bbox, location_basis: 'source_geometry' }]);
  const user = userEvent.setup(); render(<OfficialMapPage snapshot={snapshot} selected={null} onSelect={vi.fn()} onProjects={vi.fn()}/>);
  await user.click(screen.getByRole('button', { name: 'Open street list' })); const list = screen.getByRole('region', { name: 'Keyboard accessible road list' });
  await user.click(within(list).getByRole('button', { name: 'Inspections' })); const inspection = await within(list).findByRole('button', { name: /3.38.*2025-08-03/ });
  expect(screen.getByLabelText('Visible observations')).toHaveTextContent('0'); inspection.focus(); await user.keyboard('{Enter}'); expect(screen.getByText('3.38 / 10')).toBeVisible(); expect(screen.getByText(/not an accepted link/)).toBeVisible();
  await user.click(within(list).getByRole('button', { name: 'Located permits' })); const record = await within(list).findByRole('button', { name: new RegExp(permit.source_record_key) }); record.focus(); await user.keyboard('{Enter}'); expect(screen.getByText(/not a confirmed construction footprint/)).toBeVisible();
  const previous = vi.mocked(getMunicipalViewport).mock.calls.at(-1)![2]; await user.click(within(list).getByRole('button', { name: 'Narrow geographic view' })); await waitFor(() => expect(vi.mocked(getMunicipalViewport).mock.calls.at(-1)![2]).not.toEqual(previous));
});
it('retains the street list when an optional layer fails and explains unlocated coverage', async () => {
  vi.mocked(getMunicipalViewport).mockImplementation(async kind => { if (kind === 'conditions') throw new Error('Inspection source unavailable'); return kind === 'roads' ? [road] : []; });
  const user = userEvent.setup(); render(<OfficialMapPage snapshot={snapshot} selected={null} onSelect={vi.fn()} onProjects={vi.fn()}/>); await user.click(screen.getByRole('button', { name: 'Layers' })); await user.click(screen.getByRole('checkbox', { name: 'Pavement observations' })); expect(await screen.findByRole('alert')).toHaveTextContent('Inspection source unavailable'); await user.click(screen.getByRole('checkbox', { name: 'Located permits' })); expect(await screen.findByText(/No located permits in this viewport/)).toBeVisible(); await user.click(screen.getByRole('button', { name: 'Open street list' })); expect(await screen.findByRole('button', { name: /Test Street.*LION/ })).toBeVisible();
});
it('ignores a stale selected-road response after switching selection', async () => {
  let resolve!: (r: typeof road) => void; vi.mocked(getMunicipalRoad).mockImplementationOnce(() => new Promise(r => { resolve = r; })).mockResolvedValueOnce({ ...road, id: 'road-test-b', values: { name: 'Second Street' } });
  const props = { snapshot, onSelect: vi.fn(), onProjects: vi.fn() }; const view = render(<OfficialMapPage {...props} selected={road.id}/>); view.rerender(<OfficialMapPage {...props} selected="road-test-b"/>); await screen.findByRole('heading', { name: 'Second Street' }); resolve(road); await waitFor(() => expect(screen.queryByRole('heading', { name: 'Test Street' })).not.toBeInTheDocument());
});
it('shows an accepted assessment only with its official date and suppresses conflicting latest ratings', async () => {
  vi.mocked(getRoadConditions).mockResolvedValue({ data: [{ ...condition, match: { ...condition.match!, status: 'matched', target_road_id: road.id } }], meta: { ...meta, latest_usable_id: condition.id } }); const props = { snapshot, selected: road.id, onSelect: vi.fn(), onProjects: vi.fn() }; const view = render(<OfficialMapPage {...props}/>); expect(await screen.findByText('3.38')).toBeVisible(); expect(screen.getByText(/Inspected 2025-08-03/)).toBeVisible(); view.unmount();
  vi.mocked(getRoadConditions).mockResolvedValue({ data: [{ ...condition, match: { ...condition.match!, status: 'matched', target_road_id: road.id } }], meta: { ...meta, latest_usable_id: null, conflicting_latest_ratings: true } }); render(<OfficialMapPage {...props}/>); expect(await screen.findByText(/Latest inspection records disagree/)).toBeVisible(); expect(screen.queryByText('3.38')).not.toBeInTheDocument();
});
it('cancels stale viewport reads after pan and keeps the newer geometry', async () => {
  let resolve!: (r: typeof road[]) => void;
  vi.mocked(getMunicipalViewport).mockImplementationOnce(() => new Promise(r => { resolve = r; })).mockResolvedValueOnce([road, { ...road, id: 'road-test-b' }]);
  const user = userEvent.setup(); render(<OfficialMapPage snapshot={snapshot} selected={null} onSelect={vi.fn()} onProjects={vi.fn()}/>);
  await waitFor(() => expect(getMunicipalViewport).toHaveBeenCalledOnce()); const signal = vi.mocked(getMunicipalViewport).mock.calls[0][3]!;
  await user.click(screen.getByRole('button', { name: 'Pan map' })); await waitFor(() => expect(screen.getByLabelText('Visible streets')).toHaveTextContent('2')); expect(signal.aborted).toBe(true);
  resolve([road]); await waitFor(() => expect(screen.getByLabelText('Visible streets')).toHaveTextContent('2'));
});
