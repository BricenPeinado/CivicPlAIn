vi.mock('../features/standardized/StreetEvidence',()=>({StreetEvidence:()=>null}));
vi.mock('../features/decisions/DecisionContext',()=>({DecisionContext:()=>null}));
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, expect, it, vi } from 'vitest';
import { OfficialMapPage } from './OfficialMapPage';
import { getIntelligenceReleases, getConditionSummary, getMunicipalViewport, getMunicipalRoad, getMunicipalPage, getRoadConditions, getShoreline, getSource } from '../services/municipal';
import { meta, road, condition, snapshot, permit, conditionSummary } from '../test-municipal';
vi.mock('../services/municipal');
vi.mock('../features/map/RoadMap', () => ({ RoadMap: (p: any) => <div aria-label="Test map"><button onClick={() => p.onSelect(road.id)}>Select street</button><button onClick={() => p.onObservation(condition.id)}>Select observation</button><button onClick={() => p.onViewport([-74.009,40.711,-74.004,40.715])}>Pan map</button><output aria-label="Visible streets">{p.layers.streets ? p.features.features.length : 0}</output><output aria-label="Visible observations">{p.layers.conditions ? p.observations.features.length : 0}</output></div> }));
beforeEach(() => {
  vi.mocked(getIntelligenceReleases).mockResolvedValue([]);
  vi.mocked(getConditionSummary).mockResolvedValue(conditionSummary);
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
  render(<OfficialMapPage snapshot={snapshot} selected={road.id} onSelect={vi.fn()} onProjects={vi.fn()}/>); fireEvent.click(await screen.findByText('Verified segment evidence and engineering review')); expect(await screen.findByText('No accepted road assessment')).toBeVisible(); expect(screen.queryByText('3.38')).not.toBeInTheDocument();
  const related = screen.getByText(/Related permit records/); fireEvent.click(related); expect(await screen.findByText(/No accepted or candidate permit links/)).toBeVisible(); expect(getMunicipalPage).toHaveBeenCalledWith('permits', snapshot.id, { road_id: road.id, evidence:'true', include_candidates:'true',permit_release_id:undefined }, expect.any(AbortSignal));
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
  vi.mocked(getConditionSummary).mockResolvedValue({...conditionSummary, latest_usable_id: condition.id, rating: '3.38', inspection_at: condition.values.inspection_at, source_revision_id: condition.source_revision_id});
  vi.mocked(getRoadConditions).mockResolvedValue({ data: [{ ...condition, match: { ...condition.match!, status: 'matched', target_road_id: road.id } }], meta: { ...meta, latest_usable_id: condition.id } }); const props = { snapshot, selected: road.id, onSelect: vi.fn(), onProjects: vi.fn() }; const view = render(<OfficialMapPage {...props}/>); fireEvent.click(await screen.findByText('Verified segment evidence and engineering review')); expect(await screen.findByText('3.38')).toBeVisible(); expect(screen.getByText(/Inspected 2025-08-03/)).toBeVisible(); view.unmount();
  vi.mocked(getConditionSummary).mockResolvedValue({...conditionSummary, reason: 'CONFLICTING_LATEST_RATINGS'});
  vi.mocked(getRoadConditions).mockResolvedValue({ data: [{ ...condition, match: { ...condition.match!, status: 'matched', target_road_id: road.id } }], meta: { ...meta, latest_usable_id: null, conflicting_latest_ratings: true } }); render(<OfficialMapPage {...props}/>); fireEvent.click(await screen.findByText('Verified segment evidence and engineering review')); expect(await screen.findByText(/Latest inspection records disagree/)).toBeVisible(); expect(screen.queryByText('3.38')).not.toBeInTheDocument();
});
it('cancels stale viewport reads after pan and keeps the newer geometry', async () => {
  let resolve!: (r: typeof road[]) => void;
  vi.mocked(getMunicipalViewport).mockImplementationOnce(() => new Promise(r => { resolve = r; })).mockResolvedValueOnce([road, { ...road, id: 'road-test-b' }]);
  const user = userEvent.setup(); render(<OfficialMapPage snapshot={snapshot} selected={null} onSelect={vi.fn()} onProjects={vi.fn()}/>);
  await waitFor(() => expect(getMunicipalViewport).toHaveBeenCalledOnce()); const signal = vi.mocked(getMunicipalViewport).mock.calls[0][3]!;
  await user.click(screen.getByRole('button', { name: 'Pan map' })); await waitFor(() => expect(screen.getByLabelText('Visible streets')).toHaveTextContent('2')); expect(signal.aborted).toBe(true);
  resolve([road]); await waitFor(() => expect(screen.getByLabelText('Visible streets')).toHaveTextContent('2'));
});

it('requires explicit release selection and exposes exact rating, history, coverage and recency', async () => {
  const id='intel-'+'2'.repeat(32);
  vi.mocked(getIntelligenceReleases).mockResolvedValue([{id,base_snapshot_id:snapshot.id,contract_version:'road-intelligence-v1',contains_synthetic:false,counts:{observations:8,accepted_observations:1,accepted_road_rows:1,unresolved_observations:7},warnings:[]}]);
  vi.mocked(getConditionSummary).mockImplementation(async (_s,_r,asOf,_days,_signal,releaseId) => releaseId ? {...conditionSummary,intelligence_release_id:id,as_of_date:asOf,rating:'7.52',inspection_at:'2026-01-01',age_days:304,stale:true,latest_usable_id:condition.id,source_revision_id:'test-source',history:[{id:condition.id,rating:'7.52',inspection_at:'2026-01-01',eligible:true,reason:null,direction:'East',road_type:'Main',source_revision_id:'test-source',association_id:'test-association',record_hash:'record-hash',association_hash:'association-hash'}]} : conditionSummary);
  const user=userEvent.setup();render(<OfficialMapPage snapshot={snapshot} selected={road.id} onSelect={vi.fn()} onProjects={vi.fn()}/>);
  await screen.findByRole('heading',{name:'Test Street'});
  await user.click(screen.getByText('Verified segment evidence and engineering review')); const select=screen.getByRole('combobox',{name:'Reviewed intelligence release'});
  await waitFor(()=>expect(within(select).getByRole('option',{name:id})).toBeInTheDocument());
  expect(select).toHaveValue('');expect(screen.queryByText('Supported road rating: 7.52')).not.toBeInTheDocument();
  await user.selectOptions(select,id);
  expect(await screen.findByText('Supported road rating: 7.52')).toBeVisible();expect(screen.getByText(/Outside review threshold/)).toBeVisible();expect(screen.getByText(/1 \/ 8 observations accepted/)).toBeVisible();
  await user.click(screen.getByText('Accepted assessment history and lineage'));expect(screen.getByText(/Association: test-association/)).toBeVisible();expect(screen.getByText(/association-hash/)).toBeVisible();
  await user.click(screen.getByText('Map legend'));await user.selectOptions(screen.getByRole('combobox',{name:'Observation overlay'}),'current');
  expect(screen.getByRole('option',{name:'Good'})).toBeDisabled();
});

it('keeps a failed summary unavailable instead of asserting that no accepted evidence exists', async () => {
  vi.mocked(getConditionSummary).mockRejectedValue(new Error('Projection unavailable'));
  render(<OfficialMapPage snapshot={snapshot} selected={road.id} onSelect={vi.fn()} onProjects={vi.fn()}/>);
  fireEvent.click(await screen.findByText('Verified segment evidence and engineering review')); expect(await screen.findByText('Condition summary unavailable: Projection unavailable')).toBeVisible();
  expect(screen.queryByText('No accepted road assessment')).not.toBeInTheDocument();
  expect(screen.getByRole('button',{name:'Retry condition summary'})).toBeVisible();
});

it.each([{raw:'7.72',rounded:8,grade:'good',nonRating:null},{raw:'0.0',rounded:null,grade:'unknown',nonRating:'Road Identification'}])('pins pilot policy, displays $raw accepted history and enables category filters', async ({raw,rounded,grade,nonRating}) => {
  const id='intel-'+'3'.repeat(32), sid='nyc-3947b35876a619b31067db96b1409ad8';
  const pilot={...snapshot,id:sid}, policy={id:'civicplain-pilot-pavement-v1.0',name:'CivicPlAIn Pilot Policy v1.0',hash:'a'.repeat(64),classification:'planning_assumption',official_nyc_dot_policy:false};
  vi.mocked(getIntelligenceReleases).mockResolvedValue([{id,base_snapshot_id:sid,contract_version:'road-intelligence-v1',contains_synthetic:false,counts:{observations:8726,accepted_observations:5,accepted_road_rows:5,unresolved_observations:8721},warnings:[]}]);
  vi.mocked(getConditionSummary).mockImplementation(async (_s,_r,asOf,_days,_signal,releaseId,policyId)=>({...conditionSummary,snapshot_id:sid,as_of_date:asOf,intelligence_release_id:releaseId||null,method_version:policyId?'road-condition-v2-pilot':'road-condition-v1',policy:policyId?policy:null,history:releaseId?[{id:condition.id,rating:raw,non_rating_reason:nonRating,multipass:'1',inspection_at:'2024-08-31',direction:null,road_type:null,eligible:false,reason:'PARTIAL_OR_UNREVIEWED_SCOPE',source_revision_id:'test-source',record_hash:'source-hash',association_id:'approved-association',association_hash:'review-hash',grading:{rounded_rating:rounded,category:grade,reason:nonRating?'NON_RATING_REASON':null,policy_id:policy.id},association_review:{reviewer:'Project owner; pilot only',reason:'Owner approval',scope:'partial',scope_reason:'Whole-road scope unverified',candidate_set_hash:'competitors-hash',evidence_refs:['owner-approval']}}]:[]}));
  const onRoute=vi.fn(),user=userEvent.setup();
  render(<OfficialMapPage snapshot={pilot} selected={road.id} onSelect={vi.fn()} onProjects={vi.fn()} onRoute={onRoute} route={{view:'map',road:road.id,intelligence:id,asof:'2026-11-08'}}/>);
  await user.click(await screen.findByText('Verified segment evidence and engineering review')); expect(await screen.findByText('Accepted road reference; condition Unknown')).toBeVisible();
  expect(screen.getByText(/5 \/ 8726 observations accepted/)).toBeVisible();
  expect(screen.getByText(/Derived using CivicPlAIn Pilot Policy v1.0/)).toHaveTextContent('not official NYC DOT classification');
  await user.click(screen.getByText('Accepted assessment history and lineage'));
  expect(screen.getByText(new RegExp('Accepted observation grade: '+grade))).toHaveTextContent('Rounded rating: '+(rounded??'Unknown'));
  expect(screen.getByText(/Non-rating reason:/)).toHaveTextContent(nonRating||'None reported');
  expect(screen.getByText(/Multipass flag:/)).toHaveTextContent('1');
  expect(screen.getByText(/Project owner; pilot only/)).toHaveTextContent('Whole-road scope unverified');
  expect(getConditionSummary).toHaveBeenLastCalledWith(sid,road.id,'2026-11-08','365',expect.any(AbortSignal),id,policy.id);
  await user.click(screen.getByText('Map legend'));
  expect(screen.getByRole('option',{name:'Good'})).toBeEnabled();
  await user.selectOptions(screen.getByRole('combobox',{name:'Road category'}),'good');
  expect(onRoute).toHaveBeenCalledWith({condition:'good'});
  await waitFor(()=>expect(getMunicipalViewport).toHaveBeenCalledWith('roads',sid,expect.anything(),expect.any(AbortSignal),{release_id:id,as_of_date:'2026-11-08',policy_id:policy.id}));
});
