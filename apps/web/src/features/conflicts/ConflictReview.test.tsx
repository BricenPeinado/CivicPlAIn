import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { expect, it, vi } from 'vitest';
import { ConflictReview } from './ConflictReview';
import { projects, analysis } from './testData';
import { infrastructureCategories } from '../../types/api';
function props() {
  return { projects, analysis, loading: false, error: '', reload: vi.fn(), selectedRoad: null, selectedProject: null,
    selectedFinding: null, onProject: vi.fn(), onFinding: vi.fn(), onAll: vi.fn(), showProjects: true,
    setShowProjects: vi.fn(), visibleCategories: [...infrastructureCategories], setVisibleCategories: vi.fn() };
}
it('selects a project and finding with keyboard controls and preserves non-color uncertainty', async () => {
  const p = props(), user = userEvent.setup();
  render(<ConflictReview {...p}/>);
  const project = screen.getByRole('button', { name: /Fictional gas project — location unknown/ });
  project.focus(); await user.keyboard('{Enter}');
  expect(p.onProject).toHaveBeenCalledWith('demo-unknown-location');
  await user.click(screen.getByRole('button', { name: /Potential pavement rework/ }));
  expect(p.onFinding).toHaveBeenCalledWith('conflict-test');
  expect(screen.getByText(/not final engineering determinations/)).toBeInTheDocument();
  expect(screen.getByText(/demo-unknown-location.geometry/)).toBeInTheDocument();
});
it('renders dates, evidence, source contents and required human review', () => {
  render(<ConflictReview {...props()} selectedProject="demo-road-project" selectedFinding="conflict-test"/>);
  const evidence = screen.getByRole('article', { name: 'Selected conflict evidence' });
  expect(within(evidence).getByText(/Sequential gap: 2 calendar days/)).toBeInTheDocument();
  expect(within(evidence).getByText(/2027-04-10 → 2027-04-15/)).toBeInTheDocument();
  expect(within(evidence).getByText('Verify excavation scope with the utility coordinator.')).toBeInTheDocument();
  expect(screen.getByText(analysis.input_snapshot.sources[0].title)).toBeInTheDocument();
  expect(screen.getByRole('article', { name: 'Selected project details' })).toHaveTextContent('Unknown; no loss or savings calculated');
});
it('toggles all work zones and individual categories without removing findings', async () => {
  const p = props(), user = userEvent.setup(); render(<ConflictReview {...p}/>);
  await user.click(screen.getByRole('checkbox', { name: 'Show project work zones' }));
  expect(p.setShowProjects).toHaveBeenCalledWith(false);
  await user.click(screen.getByRole('checkbox', { name: 'water' }));
  expect(p.setVisibleCategories).toHaveBeenCalledWith(infrastructureCategories.filter(c => c !== 'water'));
  expect(screen.getByRole('button', { name: /Potential pavement rework/ })).toBeInTheDocument();
});
it('filters road/project findings, qualifies zero findings, and handles retry', async () => {
  const p = props(); const view = render(<ConflictReview {...p} selectedRoad="demo-r-009"/>);
  expect(screen.queryByRole('button', { name: /Potential pavement rework/ })).not.toBeInTheDocument();
  expect(screen.getByText(/No conflicts detected in the checked records/)).toHaveTextContent('coverage may be incomplete');
  view.rerender(<ConflictReview {...p} error="API unavailable"/>);
  await userEvent.click(screen.getByRole('button', { name: 'Retry project analysis' }));
  expect(p.reload).toHaveBeenCalledOnce();
});
