import {APIError,readJSON} from './http';
import {verifyMeta} from './municipal';
import type {MunicipalEnvelope} from '../types/municipal';
import type {EstimatePreview,MunicipalEstimate,MunicipalEstimateRequest,EstimateSummary,PlanningCapabilities} from '../types/municipalPlanning';
const base=(import.meta.env.VITE_MUNICIPAL_API_BASE_URL||'http://127.0.0.1:8000/api/v2').replace(/\/$/,'');
function verify(value:EstimatePreview,snapshot:string,road:string) {
 const r=value.result;
 if(!r || r.contract_version!=='municipal-estimate-v1' || r.method_version!=='municipal-area-cost-v1' || r.snapshot_id!==snapshot || r.road_id!==road || r.contains_synthetic!==false || r.contains_assumptions!==true || r.utility_coverage!=='unknown' || value.input_snapshot?.request.snapshot_id!==snapshot || value.input_snapshot.request.road_id!==road || !Array.isArray(r.alternatives) || r.alternatives.some(a=>!['available','unavailable'].includes(a.status)))throw new Error('Estimate context or provenance differs from selection.');
}
export async function calculateMunicipalEstimate(body:MunicipalEstimateRequest,save:boolean,signal?:AbortSignal):Promise<EstimatePreview|MunicipalEstimate> {
 const timeout=AbortSignal.timeout(10000);
 const response=await fetch(`${base}/planning/estimates${save?'':'/preview'}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal:signal?AbortSignal.any([signal,timeout]):timeout});
 if(!response.ok){let message=`Estimate request failed (${response.status}).`;try{const e=await response.json();message=e.error?.message||message;if(e.error?.field_errors)message+=' '+e.error.field_errors.map((f:{path:string;reason:string})=>`${f.path}: ${f.reason}`).join('; ');}catch{/* sanitized fallback */}throw new APIError(message,'ESTIMATE_ERROR',response.status);}
 const value=await response.json() as MunicipalEnvelope<EstimatePreview|MunicipalEstimate>;verifyMeta(value.meta,body.snapshot_id);verify(value.data,body.snapshot_id,body.road_id);
 if(save && (!('id' in value.data) || !/^estimate-[a-f0-9]{64}$/.test(value.data.id)))throw new Error('Invalid saved estimate identity.');return value.data;
}
export async function getPlanningCapabilities(snapshot:string,road:string,signal?:AbortSignal){
 const r=await readJSON<MunicipalEnvelope<PlanningCapabilities>>(base,`/planning/capabilities?${new URLSearchParams({snapshot_id:snapshot,road_id:road})}`,signal);verifyMeta(r.meta,snapshot);if(r.data.snapshot_id!==snapshot || r.data.road_id!==road || r.data.rate_catalog_available!==false)throw new Error('Unsupported planning context.');return r.data;
}
export async function getMunicipalEstimates(snapshot:string,road:string,cursor?:string,signal?:AbortSignal){
 const r=await readJSON<MunicipalEnvelope<EstimateSummary[]>>(base,`/planning/estimates?${new URLSearchParams({snapshot_id:snapshot,road_id:road,...(cursor?{cursor}:{})})}`,signal);verifyMeta(r.meta,snapshot);if(r.data.some(e=>e.road_id!==road))throw new Error('Estimate history context differs.');return r;
}
export async function getMunicipalEstimate(snapshot:string,road:string,id:string,signal?:AbortSignal){
 const r=await readJSON<MunicipalEnvelope<MunicipalEstimate>>(base,`/planning/estimates/${encodeURIComponent(id)}?${new URLSearchParams({snapshot_id:snapshot})}`,signal);verifyMeta(r.meta,snapshot);verify(r.data,snapshot,road);if(r.data.id!==id)throw new Error('Saved estimate identity differs.');return r.data;
}
