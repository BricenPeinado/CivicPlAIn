import { APIError, readJSON } from './http';
import type { Bbox, Dashboard, MunicipalEnvelope, MunicipalGeoJSON, MunicipalMeta, MunicipalRecord, Snapshot, SourceRevision, Workspace } from '../types/municipal';
const base = (import.meta.env.VITE_MUNICIPAL_API_BASE_URL || 'http://127.0.0.1:8000/api/v2').replace(/\/$/, '');
const query = (params: Record<string, string | undefined>) => new URLSearchParams(Object.entries(params).filter((p): p is [string, string] => p[1] !== undefined)).toString();
export const readMunicipal = <T,>(path: string, signal?: AbortSignal) => readJSON<T>(base, path, signal);
export function verifyMeta(meta: MunicipalMeta, snapshot: string) {
  if (meta?.contract_version !== 'municipal-record-v2' || meta.snapshot_id !== snapshot || meta.mode !== 'official') throw new Error('The source snapshot changed. Select the dataset again.');
}
function verifyConditionContext(value: import('../types/municipal').ConditionSummary | undefined, snapshot: string, road: string, asOf: string, releaseId?: string, policyId?: string) {
 if (!value || value.road_id !== road || value.snapshot_id !== snapshot || value.method_version !== (policyId ? 'road-condition-v2-pilot' : 'road-condition-v1') || (value.policy?.id || undefined) !== policyId || value.as_of_date !== asOf || value.intelligence_release_id !== (releaseId || null) || !['good','fair','poor','unknown'].includes(value.category) || policyId && value.policy?.official_nyc_dot_policy !== false) throw new Error('Condition context differs from selection.');
}
export async function getWorkspace(signal?: AbortSignal): Promise<Workspace> {
  const result = await readMunicipal<{ data: Workspace }>('/workspace', signal);
  if (!['official', 'synthetic'].includes(result.data?.mode) || result.data.mode === 'official' && !/^nyc-[a-f0-9]{32}$/.test(result.data.snapshot_id || '')) throw new Error('Unsupported workspace configuration.');
  return result.data;
}
export async function getSnapshots(signal?: AbortSignal): Promise<Snapshot[]> {
  const values: Snapshot[] = []; let cursor: string | undefined; const seen = new Set<string>();
  do {
    const result = await readMunicipal<MunicipalEnvelope<Snapshot[]>>(`/data-snapshots?${query({ limit: '100', cursor })}`, signal);
    if (!Array.isArray(result.data) || result.data.some(s => s.contract_version !== 'municipal-record-v2' || !/^nyc-[a-f0-9]{32}$/.test(s.id))) throw new Error('Unsupported snapshot catalog.');
    values.push(...result.data); cursor = result.meta.next_cursor || undefined;
    if (cursor && seen.has(cursor) || values.length > 1000) throw new Error('Invalid snapshot pagination.');
    if (cursor) seen.add(cursor);
  } while (cursor);
  return values;
}
export async function getSnapshot(id: string, signal?: AbortSignal) {
  const result = await readMunicipal<MunicipalEnvelope<Snapshot>>(`/data-snapshots/${encodeURIComponent(id)}`, signal); verifyMeta(result.meta, id); if (result.data.id !== id || result.data.contract_version !== 'municipal-record-v2' || result.data.mode !== 'official') throw new Error('Unsupported snapshot manifest.'); return result.data;
}
export async function getMunicipalPage(kind: 'road-segments' | 'conditions' | 'permits', snapshot: string, filters: Record<string, string | undefined> = {}, signal?: AbortSignal) {
  const result = await readMunicipal<MunicipalEnvelope<MunicipalRecord[]>>(`/${kind}?${query({ ...filters, snapshot_id: snapshot, limit: '100' })}`, signal);
  verifyMeta(result.meta, snapshot);
  if (!Array.isArray(result.data) || result.data.some(r => !r.id || !r.source_revision_id || r.contains_synthetic || r.classification === 'synthetic_fixture' || r.contract_version !== 'municipal-record-v2' || r.kind !== (kind === 'road-segments' ? 'road' : kind === 'conditions' ? 'condition' : 'permit'))) throw new Error('Unsupported official records. Synthetic records cannot enter this workspace.');
  if (kind === 'road-segments' && filters.release_id) for (const r of result.data) verifyConditionContext(r.condition_summary as import('../types/municipal').ConditionSummary, snapshot, r.id, filters.as_of_date || '', filters.release_id, filters.policy_id);
  if (kind==='permits' && (filters.evidence==='true' || filters.permit_release_id)) for (const r of result.data) verifyPermitContext(r,snapshot,filters.permit_release_id);
  return result;
}
export async function getMunicipalViewport(kind: 'roads' | 'conditions' | 'permits', snapshot: string, bbox: Bbox, signal?: AbortSignal, filters: Record<string,string> = {}): Promise<MunicipalRecord[]> {
  const records: MunicipalRecord[] = []; const seen = new Set<string>(); let cursor: string | undefined;
  do {
    const result = await getMunicipalPage(kind === 'roads' ? 'road-segments' : kind, snapshot, { ...filters, bbox: bbox.join(','), cursor }, signal);
    records.push(...result.data); cursor = result.meta.next_cursor || undefined;
    if ((result.meta.total_matching ?? 0) > 2000 || records.length > 2000) throw new APIError('Zoom in to load this layer. More than 2,000 records intersect the viewport.', 'VIEWPORT_TOO_BROAD', 422);
    if (cursor && seen.has(cursor)) throw new Error('Repeated viewport cursor.');
    if (cursor) seen.add(cursor);
  } while (cursor);
  if (new Set(records.map(r => r.id)).size !== records.length) throw new Error('Duplicate viewport records.');
  return records;
}
export async function getMunicipalRoad(snapshot: string, id: string, signal?: AbortSignal) {
  const result = await readMunicipal<MunicipalEnvelope<MunicipalRecord>>(`/road-segments/${encodeURIComponent(id)}?${query({ snapshot_id: snapshot })}`, signal);
  verifyMeta(result.meta, snapshot); if (result.data.contract_version !== 'municipal-record-v2' || result.data.kind !== 'road' || result.data.id !== id || result.data.contains_synthetic) throw new Error('Road identity differs from selection.'); return result.data;
}
export async function getRoadConditions(snapshot: string, id: string, cursor?: string, signal?: AbortSignal) {
  const result = await readMunicipal<MunicipalEnvelope<MunicipalRecord[]>>(`/road-segments/${encodeURIComponent(id)}/conditions?${query({ snapshot_id: snapshot, limit: '100', cursor })}`, signal); verifyMeta(result.meta, snapshot);
  if (!Array.isArray(result.data) || result.data.some(r => r.kind !== 'condition' || r.contains_synthetic || r.match?.status !== 'matched' || r.match.target_road_id !== id)) throw new Error('Condition history contains an unaccepted road link.');
  return result;
}
export async function getShoreline(snapshot: string, bbox: Bbox, signal?: AbortSignal) {
  const features: MunicipalGeoJSON['features'] = []; let cursor: string | undefined; const seen = new Set<string>();
  do {
    const result = await readMunicipal<MunicipalGeoJSON>(`/context/geojson?${query({ snapshot_id: snapshot, bbox: bbox.join(','), limit: '100', cursor })}`, signal); verifyMeta(result.meta, snapshot);
    if (result.type !== 'FeatureCollection' || !Array.isArray(result.features)) throw new Error('Unsupported shoreline geometry.');
    features.push(...result.features); cursor = result.meta.next_cursor || undefined;
    if (features.length > 2000 || cursor && seen.has(cursor)) throw new Error('Unsupported shoreline pagination.');
    if (cursor) seen.add(cursor);
  } while (cursor);
  return { type: 'FeatureCollection' as const, features };
}
export async function getSource(snapshot: string, id: string, signal?: AbortSignal) {
  const result = await readMunicipal<MunicipalEnvelope<SourceRevision>>(`/source-revisions/${encodeURIComponent(id)}?${query({ snapshot_id: snapshot })}`, signal); verifyMeta(result.meta, snapshot); if (result.data.id !== id) throw new Error('Source revision differs from selection.'); return result.data;
}
export async function getDashboard(snapshot: string, signal?: AbortSignal) {
  const result = await readMunicipal<MunicipalEnvelope<Dashboard>>(`/dashboard?${query({ snapshot_id: snapshot })}`, signal); verifyMeta(result.meta, snapshot); return result.data;
}

export async function getMunicipalPermit(snapshot: string, id: string, signal?: AbortSignal, releaseId?: string, evidence=false) {
  const result = await readMunicipal<MunicipalEnvelope<MunicipalRecord>>(`/permits/${encodeURIComponent(id)}?${query({ snapshot_id: snapshot,permit_release_id:releaseId,evidence:evidence?'true':undefined })}`, signal); verifyMeta(result.meta, snapshot);
  if (evidence || releaseId) verifyPermitContext(result.data,snapshot,releaseId);
  if (result.data.contains_synthetic) throw new Error('Synthetic records cannot enter the official workspace.');
  if (result.data.id !== id || result.data.kind !== 'permit' || result.data.contract_version !== 'municipal-record-v2') throw new Error('Permit identity differs from selection.');
  return result.data;
}

export async function getConditionSummary(snapshot: string, road: string, asOf: string, staleDays: string, signal?: AbortSignal, releaseId?: string, policyId?: string) {
 const result = await readMunicipal<MunicipalEnvelope<import('../types/municipal').ConditionSummary>>(`/road-segments/${encodeURIComponent(road)}/condition-summary?${query({snapshot_id:snapshot,as_of_date:asOf,stale_after_days:staleDays || undefined,release_id:releaseId,policy_id:policyId})}`,signal);
 verifyMeta(result.meta,snapshot);
 verifyConditionContext(result.data,snapshot,road,asOf,releaseId,policyId);
 return result.data;
}

export async function getIntelligenceReleases(snapshot: string, signal?: AbortSignal) {
 const values: import('../types/municipal').IntelligenceRelease[] = []; let cursor: string | undefined; const seen = new Set<string>();
 do {
  const result = await readMunicipal<MunicipalEnvelope<import('../types/municipal').IntelligenceRelease[]>>(`/intelligence-releases?${query({snapshot_id:snapshot,limit:'100',cursor})}`, signal);
  verifyMeta(result.meta,snapshot);
  if (!Array.isArray(result.data) || result.data.some(r => r.base_snapshot_id !== snapshot || r.contract_version !== 'road-intelligence-v1' || r.contains_synthetic)) throw new Error('Unsupported intelligence release context.');
  values.push(...result.data);cursor = result.meta.next_cursor || undefined;
  if (values.length > 1000 || cursor && seen.has(cursor)) throw new Error('Unsupported release pagination.');
  if (cursor) seen.add(cursor);
 } while(cursor);
 return values;
}

function verifyPermitContext(record: MunicipalRecord,snapshot:string,releaseId?:string) {
 const p=record.permit_location;
 if (!p || p.snapshot_id!==snapshot || p.permit_release_id!==(releaseId||null) || p.method_version!=='permit-road-reference-v1' || !['located','candidate','unlocated','outside_coverage','invalid_evidence'].includes(p.status) || p.actual_schedule!=='unknown') throw new Error('Permit evidence context differs from selection.');
}
export async function getPermitReleases(snapshot:string,signal?:AbortSignal) {
 const all:import('../types/municipal').PermitRelease[]=[];let cursor:string|undefined;const seen=new Set<string>();
 do {
  const r=await readMunicipal<MunicipalEnvelope<import('../types/municipal').PermitRelease[]>>(`/intelligence-releases?${query({snapshot_id:snapshot,kind:'permit',cursor})}`,signal);verifyMeta(r.meta,snapshot);
  if (!Array.isArray(r.data) || r.data.some(p=>p.base_snapshot_id!==snapshot || p.contract_version!=='permit-intelligence-v1' || p.contains_synthetic)) throw new Error('Unsupported permit release.');
  all.push(...r.data);cursor=r.meta.next_cursor||undefined;
  if(all.length>1000 || cursor && seen.has(cursor))throw new Error('Unsupported permit release pagination.');if(cursor)seen.add(cursor);
 }while(cursor);return all;
}
export async function getPermitCoverage(snapshot:string,releaseId?:string,signal?:AbortSignal) {
 const r=await readMunicipal<MunicipalEnvelope<import('../types/municipal').PermitCoverage>>(`/permit-location-coverage?${query({snapshot_id:snapshot,permit_release_id:releaseId})}`,signal);verifyMeta(r.meta,snapshot);
 if(r.data.snapshot_id!==snapshot || r.data.permit_release_id!==(releaseId||null))throw new Error('Permit coverage context differs from selection.');return r.data;
}
export async function getPermitCoordination(snapshot:string,id:string,releaseId?:string,cursor?:string,signal?:AbortSignal) {
 const r=await readMunicipal<MunicipalEnvelope<import('../types/municipal').CoordinationCandidate[]>>(`/permits/${encodeURIComponent(id)}/coordination-candidates?${query({snapshot_id:snapshot,permit_release_id:releaseId,cursor})}`,signal);verifyMeta(r.meta,snapshot);
 if(!Array.isArray(r.data) || r.data.some(p=>p.snapshot_id!==snapshot || p.permit_release_id!==(releaseId||null) || !p.permit_ids.includes(id) || p.confirmed_conflict!==false || p.actual_work_overlap!=='unknown'))throw new Error('Unsupported coordination evidence.');return r;
}
