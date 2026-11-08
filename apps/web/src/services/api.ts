import { categories, type Envelope, type Evidence, type Road, type RoadsCollection, type Assessment, type OptionComparison, type Estimate, type EstimateRequest, type WorkProject, type ConflictAnalysis, type ConflictFinding, type Meta } from '../types/api';
const base = (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1').replace(/\/$/, '');
const TIMEOUT_MS = 10000;
async function request<T>(path: string, signal?: AbortSignal, body?: unknown, method = body ? 'POST' : 'GET'): Promise<T> {
  const timeout = AbortSignal.timeout(TIMEOUT_MS);
  try {
    const response = await fetch(`${base}${path}`, { signal: signal ? AbortSignal.any([signal, timeout]) : timeout, ...(body ? { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) } : {}) });
    if (!response.ok) {
      let message = `API returned HTTP ${response.status}.`;
      try { const error = await response.json(); if (typeof error.error?.message === 'string') message += ` ${error.error.message}`; if (Array.isArray(error.error?.field_errors)) message += error.error.field_errors.map((f: { path: string; reason: string }) => ` ${f.path}: ${f.reason}`).join(';'); } catch { /* retain HTTP status */ }
      throw new Error(message);
    }
    return await response.json() as T;
  } catch (error) {
    if (signal?.aborted) throw error;
    if (timeout.aborted) throw new Error('The local API took too long to respond.');
    throw new Error(error instanceof Error ? error.message : 'Unable to reach the local API.');
  }
}
export async function getRoads(signal?: AbortSignal): Promise<RoadsCollection> {
  const pages: RoadsCollection[] = [];
  const seen = new Set<string>();
  let cursor: string | null = null;
  do {
    const page: RoadsCollection = await request(`/road-segments/geojson?limit=30${cursor ? `&cursor=${encodeURIComponent(cursor)}` : ''}`, signal);
    if (page.type !== 'FeatureCollection' || !Array.isArray(page.features) || !page.meta ||
        page.features.some(f => f.geometry?.type !== 'LineString' || !f.properties?.id ||
          !categories.includes(f.properties.condition_summary?.category))) {
      throw new Error('The API returned an unsupported road dataset.');
    }
    if (pages.length && page.meta.dataset_snapshot_id !== pages[0].meta.dataset_snapshot_id) {
      throw new Error('Dataset changed while loading. Reload the workspace.');
    }
    pages.push(page);
    cursor = page.meta.next_cursor;
    if (cursor && seen.has(cursor)) throw new Error('Invalid API pagination.');
    if (cursor) seen.add(cursor);
    if (pages.flatMap(p => p.features).length > 30) throw new Error('Dataset exceeds the 30-road study limit.');
  } while (cursor);
  const result = { ...pages[0], features: pages.flatMap(p => p.features) };
  if (new Set(result.features.map(f => f.properties.id)).size !== result.features.length) {
    throw new Error('Dataset contains duplicate road IDs.');
  }
  return result;
}
export const getRoad = (id: string, signal?: AbortSignal) => request<Envelope<Road>>(`/road-segments/${encodeURIComponent(id)}`, signal);
export const getEvidence = (id: string, signal?: AbortSignal) => request<Envelope<Evidence>>(`/evidence-sources/${encodeURIComponent(id)}`, signal);

export const getAssessments = (id: string, signal?: AbortSignal) => request<Envelope<Assessment[]>>(`/road-segments/${encodeURIComponent(id)}/conditions`, signal);
export const getRepairOptions = (id: string, signal?: AbortSignal) => request<Envelope<OptionComparison[]>>(`/road-segments/${encodeURIComponent(id)}/repair-options`, signal);
export const createEstimate = (body: EstimateRequest, signal?: AbortSignal) => request<Envelope<Estimate>>('/estimates', signal, body);
export const getEstimate = (id: string, signal?: AbortSignal) => request<Envelope<Estimate>>(`/estimates/${encodeURIComponent(id)}`, signal);

export async function getProjects(signal?: AbortSignal): Promise<Envelope<WorkProject[]>> {
  const records: WorkProject[] = [];
  const seen = new Set<string>();
  let cursor: string | null = null;
  let first: { meta: Meta } | undefined;
  do {
    const page: Envelope<WorkProject[]> = await request(`/projects?limit=100${cursor ? `&cursor=${encodeURIComponent(cursor)}` : ''}`, signal);
    if (!Array.isArray(page.data) || !page.meta || page.data.some(p => !p.id || !Array.isArray(p.road_segment_ids) || (p.geometry !== null && !['Polygon', 'LineString'].includes(p.geometry?.type)))) throw new Error('Unsupported project response.');
    if (first && page.meta.dataset_snapshot_id !== first.meta.dataset_snapshot_id) throw new Error('Project snapshot changed. Reload the workspace.');
    first = first || page;
    records.push(...page.data);
    cursor = page.meta.next_cursor;
    if (cursor && seen.has(cursor)) throw new Error('Invalid project pagination.');
    if (cursor) seen.add(cursor);
    if (records.length > 50) throw new Error('Project dataset exceeds the 50-project analysis limit.');
  } while (cursor);
  if (new Set(records.map(p => p.id)).size !== records.length) throw new Error('Duplicate project IDs.');
  return { data: records, meta: first!.meta };
}
export const analyzeConflicts = (dataset_snapshot_id: string, project_ids: string[], signal?: AbortSignal) =>
  request<Envelope<ConflictAnalysis>>('/conflicts/analyze', signal, { dataset_snapshot_id, project_ids });
export const getConflict = (id: string, signal?: AbortSignal) => request<Envelope<ConflictFinding>>(`/conflicts/${encodeURIComponent(id)}`, signal);
export const getConflictAnalysis = (id: string, signal?: AbortSignal) => request<Envelope<ConflictAnalysis>>(`/conflict-analyses/${encodeURIComponent(id)}`, signal);

import type { Scenario, ScenarioDraft, ScenarioEvaluation, ScenarioComparison } from '../types/scenarios';
export async function getScenarios(signal?: AbortSignal): Promise<Envelope<Scenario[]>> {
  const records: Scenario[] = []; let after = ''; let first: Envelope<Scenario[]> | undefined;
  const seen = new Set<string>();
  do {
    const page = await request<Envelope<Scenario[]>>(`/scenarios?limit=100${after ? `&after=${encodeURIComponent(after)}` : ''}`, signal);
    first = first || page; records.push(...page.data); after = page.meta.next_cursor || '';
    if (after && seen.has(after)) throw new Error('Invalid scenario pagination.');
    seen.add(after);
  } while (after);
  return { data: records, meta: first!.meta };
}
export const getScenario = (id: string, signal?: AbortSignal) => request<Envelope<Scenario>>(`/scenarios/${encodeURIComponent(id)}`, signal);
export const createScenario = (body: ScenarioDraft, signal?: AbortSignal) => request<Envelope<Scenario>>('/scenarios', signal, body);
export const updateScenario = (id: string, expected_revision: number, draft: ScenarioDraft, signal?: AbortSignal) => request<Envelope<Scenario>>(`/scenarios/${encodeURIComponent(id)}`, signal, { expected_revision, draft }, 'PATCH');
export const evaluateScenario = (id: string, expected_revision: number, signal?: AbortSignal) => request<Envelope<ScenarioEvaluation>>(`/scenarios/${encodeURIComponent(id)}/evaluate`, signal, { expected_revision });
export const getScenarioEvaluations = (id: string, signal?: AbortSignal, offset = 0) => request<Envelope<ScenarioEvaluation[]>>(`/scenarios/${encodeURIComponent(id)}/evaluations?limit=30&offset=${offset}`, signal);
export const getScenarioEvaluation = (id: string, signal?: AbortSignal) => request<Envelope<ScenarioEvaluation>>(`/scenario-evaluations/${encodeURIComponent(id)}`, signal);
export const compareScenarios = (evaluation_ids: string[], signal?: AbortSignal) => request<Envelope<ScenarioComparison>>('/scenario-comparisons', signal, { evaluation_ids });
export const getRepairCatalog = (signal?: AbortSignal) => request<Envelope<import('../types/api').RepairOption[]>>('/repair-options', signal);

import type { AIContext, AIExplanation, AIStatus } from '../types/ai';
export function explainContext(context: AIContext, mode: 'deterministic' | 'ai', question?: string, signal?: AbortSignal) {
  if (question !== undefined) return request<Envelope<AIExplanation>>('/ai/ask', signal, { context, mode, question });
  if (context.type === 'estimate') return request<Envelope<AIExplanation>>('/ai/explain-estimate', signal, { estimate_id: context.record_ids[0], mode });
  if (context.type === 'conflict') return request<Envelope<AIExplanation>>('/ai/explain-conflict', signal, { conflict_id: context.record_ids[0], mode });
  if (context.type === 'comparison') return request<Envelope<AIExplanation>>('/ai/explain-scenario-comparison', signal, { evaluation_ids: context.record_ids, mode });
  return request<Envelope<AIExplanation>>('/ai/ask', signal, { context, mode, question: 'Which assumptions should we verify before review?' });
}
export const getAIStatus = (signal?: AbortSignal) => request<Envelope<AIStatus>>('/ai/status', signal);
export const saveReviewNote = (evaluationId: string, reviewer_label: string, note: string, signal?: AbortSignal) => request<Envelope<{ id: string; action: 'review_note'; authorizes_work: false }>>(`/scenario-evaluations/${encodeURIComponent(evaluationId)}/reviews`, signal, { reviewer_label, note, acknowledged_limitations: ['synthetic_inputs', 'unknown_utilities', 'human_review'] });
