import {readMunicipal} from './municipal';
import {APIError} from './http';
export interface Profile {
  road_id: string; street_name: string | null; segment_id: string | null; object_id: string | null;
  geometry: GeoJSON.Geometry; source_revision_id: string; street_observation_count: number;
  permits_on_street: number; latest_rating: number | null; latest_inspection_at: string | null;
  display_condition: 'Good' | 'Fair' | 'Poor' | 'Unknown' | 'Unclassified'; display_basis: string | null;
}
export interface Pavement {
  road_id: string; observation_id: string; on_street: string | null; from_street: string | null; to_street: string | null;
  rating: number | null; display_condition: string | null; inspection_at: string | null; source_revision_id: string;
  non_rating_reason: string | null;
}
export interface StreetPermit {
  road_id: string; permit_id: string; permit_number: string | null; permit_type: string | null; permit_status: string | null;
  on_street: string | null; from_street: string | null; to_street: string | null; issue_date: string | null;
  valid_from: string | null; valid_to: string | null; source_revision_id: string;
}
export interface Result<T> {data: T; meta: {contract_version: string; snapshot_id: string; road_id: string; total_matching: number; next_offset: number | null; association_basis: string; verified_segment_condition: boolean}}
export async function getStandardized<T>(snapshot: string, road: string, kind?: 'pavement' | 'permits', offset = 0, signal?: AbortSignal) {
  const query = new URLSearchParams({snapshot_id: snapshot, ...(kind ? {limit:'10',offset:String(offset)} : {})});
  const result = await readMunicipal<Result<T>>(`/standardized/roads/${encodeURIComponent(road)}${kind ? `/${kind}` : ''}?${query}`,signal).catch(error=>{
    if(error instanceof APIError && error.status===404 && error.message==='Not Found') throw new Error('Standardized API endpoint is unavailable. Restart the backend from this checkout and verify the frontend API URL.');
    throw error;
  });
  if (result.meta?.contract_version !== 'standardized-read-v1' || result.meta.snapshot_id !== snapshot || result.meta.road_id !== road || result.meta.association_basis !== 'on_street_name' || result.meta.verified_segment_condition !== false) throw new Error('Standardized evidence context differs from selection.');
  const rows = Array.isArray(result.data) ? result.data : [result.data];
  if (rows.some(r => !r || r.road_id !== road)) throw new Error('Standardized road identity differs from selection.');
  return result;
}

export async function getMapRatings(snapshot:string,bbox:import('../types/municipal').Bbox,signal?:AbortSignal):Promise<Profile[]> {
  const q=new URLSearchParams({snapshot_id:snapshot,bbox:bbox.join(',')});
  const result=await readMunicipal<{data:Profile[];meta:Omit<Result<Profile>['meta'],'road_id'> & {map_contract:string;complete:boolean;bbox:number[];road_id:null}}>(`/standardized/map-ratings?${q}`,signal);
  const m=result.meta;
  if(m?.contract_version!=='standardized-read-v1'||m.map_contract!=='indicative-map-v1'||m.snapshot_id!==snapshot||m.association_basis!=='on_street_name'||m.verified_segment_condition!==false||m.complete!==true||m.bbox?.join(',')!==bbox.join(',')||!Array.isArray(result.data)||result.data.length>2000||m.total_matching!==result.data.length)throw new Error('Indicative map context differs from selection.');
  if(new Set(result.data.map(r=>r.road_id)).size!==result.data.length||result.data.some(r=>!r.road_id||!r.source_revision_id||!['LineString','MultiLineString'].includes(r.geometry?.type)||!['Good','Fair','Poor','Unknown','Unclassified'].includes(r.display_condition)||r.latest_rating!==null&&!Number.isFinite(r.latest_rating)))throw new Error('Unsupported indicative map evidence.');
  return result.data;
}
