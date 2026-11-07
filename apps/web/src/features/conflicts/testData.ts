// Shared test helper, never imported by production components.
import { readFileSync } from 'node:fs';
import type { ConflictAnalysis, ConflictFinding, WorkProject } from '../../types/api';
export const projects: WorkProject[] = JSON.parse(readFileSync('../../data/demo/projects.json', 'utf8')).projects;
const source = JSON.parse(readFileSync('../../data/demo/projects-manifest.json', 'utf8')).evidence_source;
export const finding: ConflictFinding = {
  id: 'conflict-test', analysis_id: 'analysis-test', project_ids: ['demo-road-project', 'demo-utility-project'], affected_road_ids: ['demo-r-001'],
  finding_type: 'reopening_risk', priority: 'coordination_review',
  spatial_evidence: { classifications: ['shared_affected_road', 'proximity_based_potential_overlap'], distance_m: 0, polygon_overlap: true, geometry_intersects: true, shared_road_ids: ['demo-r-001'], shared_corridor_ids: ['demo-r-001'], basis: 'Projected EPSG:32618; screening only.' },
  temporal_evidence: { intervals: { 'demo-road-project': ['2027-04-01', '2027-04-08'], 'demo-utility-project': ['2027-04-10', '2027-04-15'] }, interval_basis: { 'demo-road-project': 'planned', 'demo-utility-project': 'planned' }, overlap_start: null, overlap_end: null, gap_days: 2, preceding_project_id: 'demo-road-project', basis: 'America/New_York civil dates; [start, end).' },
  explanation: 'Potential pavement rework requires inspection of actual work scope.', required_review: ['Verify excavation scope with the utility coordinator.'], data_quality_warnings: ['Approximate geometry; depth unverified.'], evidence_ids: [source.id], method_version: 'conflict-screen-v1', input_hash: 'input-test', detected_at: '2026-11-07T12:00:00Z', synthetic_input: true,
};
export const analysis: ConflictAnalysis = {
  id: 'analysis-test', dataset_snapshot_id: 'demo-m1-v1', findings: [finding],
  indeterminate_checks: [{ project_ids: ['demo-road-project', 'demo-unknown-location'], missing_fields: ['demo-unknown-location.geometry'], reason: 'Location unknown; not clearance.', spatial_evidence: { ...finding.spatial_evidence, classifications: ['insufficient_spatial_information'], distance_m: null } }],
  excluded_project_ids: [], possible_pair_count: 21, checked_pair_count: 16, utility_coverage: 'unknown', warnings: ['Utility coverage unknown.'],
  parameters: { proximity_m: 5, corridor_m: 5, reopening_horizon_days: 30 }, method_version: 'conflict-screen-v1', detected_at: finding.detected_at,
  input_hash: 'input-test', result_hash: 'result-test', input_snapshot: { projects, roads: [], sources: [source], exchange_crs: 'EPSG:4326', calculation_crs: 'EPSG:32618', libraries: { shapely: '2.2.0', pyproj: '3.7.2' } },
};
