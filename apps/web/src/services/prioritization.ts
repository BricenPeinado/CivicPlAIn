import {readJSON,APIError} from './http';
import {verifyMeta} from './municipal';
import type {MunicipalEnvelope} from '../types/municipal';
import type {PriorityRecord,PriorityRequest,PrioritySummary} from '../types/prioritization';
const base=(import.meta.env.VITE_MUNICIPAL_API_BASE_URL||'http://127.0.0.1:8000/api/v2').replace(/\/$/,'');
const path='/planning/prioritization-runs';
function checked(envelope:MunicipalEnvelope<PriorityRecord>,snapshot:string){
 verifyMeta(envelope.meta,snapshot);const r=envelope.data;
 if(r.result?.snapshot_id!==snapshot||r.input_snapshot?.request?.snapshot_id!==snapshot||r.result.method_version!=='maintenance-priority-v1'||r.result.contains_synthetic!==false||r.result.utility_coverage!=='unknown'||!Array.isArray(r.result.base?.rows)||r.result.base.rows.length!==r.input_snapshot.request.road_ids.length||r.result.base.rows.some(v=>!r.input_snapshot.request.road_ids.includes(v.road_id)||v.human_review_required!==true||!['ranked','unranked'].includes(v.status)))throw new Error('Priority context or provenance differs from selection.');
 return r;
}
export async function computePriority(body:PriorityRequest,save:boolean,signal?:AbortSignal){
 const timeout=AbortSignal.timeout(10000);const response=await fetch(base+path+(save?'':'/preview'),{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal:signal?AbortSignal.any([signal,timeout]):timeout});
 if(!response.ok){let message=`Priority request failed (${response.status}).`;try{const e=await response.json();message=e.error?.message||message;if(e.error?.field_errors)message+=' '+e.error.field_errors.map((v:{path:string;reason:string})=>v.path+': '+v.reason).join('; ');}catch{/* sanitized fallback */}throw new APIError(message,'PRIORITY_ERROR',response.status);}
 const r=checked(await response.json(),body.snapshot_id);
 if(save&&(!r.id||!/^priority-[a-f0-9]{64}$/.test(r.id)))throw new Error('Invalid saved priority identity.');return r;
}
export async function getPriority(snapshot:string,id:string,signal?:AbortSignal){
 const result=checked(await readJSON<MunicipalEnvelope<PriorityRecord>>(base,path+'/'+encodeURIComponent(id)+'?'+new URLSearchParams({snapshot_id:snapshot}),signal),snapshot);
 if(result.id!==id)throw new Error('Priority identity differs.');return result;
}
export async function getPriorities(snapshot:string,cursor?:string,signal?:AbortSignal){
 const r=await readJSON<MunicipalEnvelope<PrioritySummary[]>>(base,path+'?'+new URLSearchParams({snapshot_id:snapshot,...(cursor?{cursor}:{})}),signal);verifyMeta(r.meta,snapshot);return r;
}
