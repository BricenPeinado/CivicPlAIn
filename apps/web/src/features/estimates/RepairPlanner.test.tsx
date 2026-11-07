import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, expect, it, vi } from 'vitest';
import { readFileSync } from 'node:fs';
import { RepairPlanner } from './RepairPlanner';
import { createEstimate, getAssessments, getEstimate, getRepairOptions } from '../../services/api';
import type { Calculation, Estimate, OptionComparison, RepairOption, Road } from '../../types/api';

vi.mock('../../services/api');
const fixtures = JSON.parse(readFileSync('../../data/demo/maintenance.json', 'utf8'));
const feature = JSON.parse(readFileSync('../../data/demo/roads.geojson', 'utf8')).features[0];
const road: Road = { ...feature.properties, geometry: feature.geometry };
const option: RepairOption = fixtures.repair_options.find((o: RepairOption) => o.id === 'demo-resurface');
const calculation: Calculation = {
  road_segment_id: road.id, repair_option_id: option.id, repair_category: 'resurface', currency: 'USD', quantity: '800', quantity_unit: 'm2',
  dimension_provenance: { length_m: { value: '100', unit: 'm', basis: 'synthetic_planning_assumption', evidence_ids: option.evidence_ids, note: 'Not measured.' } },
  scenarios: Object.fromEntries(['low', 'base', 'high'].map((s, i) => [s, {
    line_items: [{ label: 'Bundled roadwork: materials + labor + equipment', quantity: '800', unit: 'm2', unit_rate_usd: '45', amount_usd: '36000.00', evidence_ids: option.evidence_ids }],
    subtotal_usd: '44500.00', contingency_fraction: '.20', contingency_usd: '8900.00', total_usd: ['44760.00', '53400.00', '66360.00'][i],
  }])) as Calculation['scenarios'],
  duration: { active_workdays: 2, setup_days: 2, curing_days: 1, total_preliminary_days: 5, productivity_per_day: '600', productivity_unit: 'm2/active_workday', basis: 'Not a contractor schedule.' },
  suitability: { status: 'not_indicated', rule_id: 'test-rule', rationale: 'Condition score alone cannot establish engineering feasibility.', human_review_required: true },
  assumptions: ['USD; ROUND_HALF_UP', 'Sensitivity scenarios are not probabilities.'], warnings: ['SYNTHETIC DEMONSTRATION ESTIMATE'], evidence_ids: option.evidence_ids,
  method_version: 'repair-estimate-v1', data_kind: 'derived', synthetic_input: true,
};
const estimate: Estimate = { ...calculation, id: 'saved-id', created_at: '2026-11-07T12:00:00Z', dataset_snapshot_id: road.dataset_snapshot_id, input_hash: 'input-hash', result_hash: 'result-hash', input_snapshot: { option } };
const comparisons: OptionComparison[] = fixtures.repair_options.map((o: RepairOption) => ({ option: o, suitability: calculation.suitability, preview: calculation, unavailable_reason: null }));
const meta = { request_id: 'test', dataset_snapshot_id: road.dataset_snapshot_id, warnings: [], next_cursor: null };
beforeEach(() => {
  vi.mocked(getRepairOptions).mockResolvedValue({ data: comparisons, meta });
  vi.mocked(getAssessments).mockResolvedValue({ data: fixtures.assessments.filter((a: { road_segment_id: string }) => a.road_segment_id === road.id), meta });
  vi.mocked(createEstimate).mockResolvedValue({ data: estimate, meta });
  vi.mocked(getEstimate).mockResolvedValue({ data: estimate, meta });
});

it('loads three API options, displays provenance, history, money and durations', async () => {
  const user = userEvent.setup(); render(<RepairPlanner road={road}/>);
  expect(getRepairOptions).not.toHaveBeenCalled();
  await user.click(screen.getByRole('button', { name: 'Compare Repair Options' }));
  await screen.findByRole('heading', { name: 'Resurfacing or rehabilitation' });
  expect(screen.getAllByText('SYNTHETIC COSTS')).toHaveLength(3);
  expect(screen.getAllByText('$53,400.00')).toHaveLength(3);
  expect(screen.getAllByText(/5 preliminary days · 2 active workdays/)).toHaveLength(3);
  expect(screen.getAllByText(/Not indicated by demo condition rule/)).toHaveLength(3);
  await user.click(screen.getByText('Condition assessment history (3)'));
  expect(screen.getByText(/Undated · 3 \/ 10/)).toBeInTheDocument();
});

it('saves, retrieves and renders cost/duration breakdown and sensitivity scenarios', async () => {
  const user = userEvent.setup(); render(<RepairPlanner road={road}/>);
  await user.click(screen.getByRole('button', { name: 'Compare Repair Options' }));
  await user.click(await screen.findByRole('button', { name: 'Save & inspect Resurfacing or rehabilitation' }));
  const detail = await screen.findByRole('region', { name: 'Estimate breakdown' });
  expect(getEstimate).toHaveBeenCalledWith('saved-id', expect.any(AbortSignal));
  expect(within(detail).getByText('$8,900.00')).toBeInTheDocument();
  expect(within(detail).getByText('Curing allowance days')).toBeInTheDocument();
  expect(within(detail).getByText(/length_m: 100 m · synthetic planning assumption/)).toBeInTheDocument();
  await user.selectOptions(within(detail).getByRole('combobox'), 'high');
  expect(within(detail).getByText('$66,360.00')).toBeInTheDocument();
  await user.click(within(detail).getByText('Immutable snapshot and reproducibility'));
  expect(within(detail).getByText('Estimate ID: saved-id')).toBeInTheDocument();
});

it('validates and sends explicit dimension assumptions without inventing inputs', async () => {
  const user = userEvent.setup(); render(<RepairPlanner road={road}/>);
  await user.click(screen.getByRole('button', { name: 'Compare Repair Options' }));
  await screen.findByRole('heading', { name: option.label });
  await user.type(screen.getByLabelText('Planning width (m)'), '7.5');
  await user.click(screen.getByRole('button', { name: 'Save & inspect Resurfacing or rehabilitation' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('planning assumption note');
  expect(createEstimate).not.toHaveBeenCalled();
  await user.type(screen.getByLabelText('Planning assumption note'), 'Hypothetical width for review');
  await user.click(screen.getByRole('button', { name: 'Save & inspect Resurfacing or rehabilitation' }));
  await screen.findByRole('region', { name: 'Estimate breakdown' });
  expect(createEstimate).toHaveBeenCalledWith({ road_segment_id: road.id, repair_option_id: option.id, dataset_snapshot_id: road.dataset_snapshot_id,
    planning_assumptions: { width_m: '7.5', unit: 'm', note: 'Hypothetical width for review' } }, expect.any(AbortSignal));
});

it('shows loading, option failure and retry without losing the selected road', async () => {
  vi.mocked(getRepairOptions).mockImplementationOnce(() => new Promise(() => {}));
  const user = userEvent.setup(); const view = render(<RepairPlanner road={road}/>);
  await user.click(screen.getByRole('button', { name: 'Compare Repair Options' }));
  expect(screen.getByRole('status')).toHaveTextContent('Loading repair options');
  view.unmount();
  vi.mocked(getRepairOptions).mockRejectedValueOnce(new Error('API unavailable'));
  render(<RepairPlanner road={road}/>);
  await user.click(screen.getByRole('button', { name: 'Compare Repair Options' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('API unavailable');
  await user.click(screen.getByRole('button', { name: 'Retry repair options' }));
  await screen.findByRole('heading', { name: option.label });
});

it('shows empty assessments and unavailable estimates, and handles save failures', async () => {
  vi.mocked(getAssessments).mockResolvedValue({ data: [], meta });
  vi.mocked(getRepairOptions).mockResolvedValue({ data: comparisons.map(o => ({ ...o, preview: null, unavailable_reason: 'width_m is unknown' })), meta });
  vi.mocked(createEstimate).mockRejectedValueOnce(new Error('Missing dimensions'));
  const user = userEvent.setup(); render(<RepairPlanner road={road}/>);
  await user.click(screen.getByRole('button', { name: 'Compare Repair Options' }));
  expect(await screen.findAllByText('Estimate unavailable: width_m is unknown')).toHaveLength(3);
  await user.click(screen.getByText('Condition assessment history (0)'));
  expect(screen.getByText('No assessment records available. Condition requires review.')).toBeInTheDocument();
  await user.click(screen.getByRole('button', { name: 'Save & inspect Resurfacing or rehabilitation' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('Missing dimensions');
});
