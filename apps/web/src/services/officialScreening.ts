import {readJSON,APIError} from './http';
import {verifyMeta} from './municipal';
import type {MunicipalEnvelope} from '../types/municipal';
import type {ScreeningRecord,ScreeningNote} from '../types/officialScreening';
const base=(import.meta.env.VITE_MUNICIPAL_API_BASE_URL||'http://127.0.0.1:8000/api/v2').replace(/\/$/,'');
const path='/planning/conflict-analyses';
function checked(r:MunicipalEnvelope<ScreeningRecord>,snapshot:string){
 verifyMeta(r.meta,snapshot);const value=r.data;
 if(value.result?.snapshot_id!==snapshot||value.input_snapshot?.request?.snapshot_id!==snapshot||value.result.method_version!=='official-screen-v1'||value.result.contains_synthetic!==false||value.result.human_review_required!==true||value.result.coverage?.utilities!=='unknown'||value.result.coverage.excavation_clearance!==false||!Array.isArray(value.result.base?.findings)||value.result.base.findings.some(f=>f.human_review_required!==true))throw new Error('Screening context or provenance differs from selection.');return value;
}
async function post<T>(endpoint:string,body:unknown,signal?:AbortSignal):Promise<MunicipalEnvelope<T>>{
 const timeout=AbortSignal.timeout(15000);const r=await fetch(base+endpoint,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal:signal?AbortSignal.any([signal,timeout]):timeout});
 if(!r.ok){let message=`Screening request failed (${r.status}).`;try{const e=await r.json();message=e.error?.message||message;if(e.error?.field_errors)message+=' '+e.error.field_errors.map((v:{path:string;reason:string})=>v.path+': '+v.reason).join('; ');}catch{/* sanitized fallback */}throw new APIError(message,'SCREENING_ERROR',r.status);}return r.json();
}
export async function computeScreening(body:Record<string,unknown>,save:boolean,signal?:AbortSignal){const r=checked(await post<ScreeningRecord>(path+(save?'':'/preview'),body,signal),String(body.snapshot_id));if(save&&!/^screen-[a-f0-9]{64}$/.test(r.id||''))throw new Error('Invalid saved screening ID');return r;}
export async function getScreening(snapshot:string,id:string,signal?:AbortSignal){const r=checked(await readJSON<MunicipalEnvelope<ScreeningRecord>>(base,path+'/'+encodeURIComponent(id)+'?'+new URLSearchParams({snapshot_id:snapshot}),signal),snapshot);if(r.id!==id)throw new Error('Screening identity differs');return r;}
export async function getScreenings(snapshot:string,cursor?:string,signal?:AbortSignal){const r=await readJSON<MunicipalEnvelope<{id:string;created_at:string}[]>>(base,path+'?'+new URLSearchParams({snapshot_id:snapshot,...(cursor?{cursor}:{})}),signal);verifyMeta(r.meta,snapshot);return r;}
export async function getScreeningNotes(snapshot:string,id:string,signal?:AbortSignal){const r=await readJSON<MunicipalEnvelope<ScreeningNote[]>>(base,path+'/'+encodeURIComponent(id)+'/notes?'+new URLSearchParams({snapshot_id:snapshot}),signal);verifyMeta(r.meta,snapshot);return r.data;}
export async function addScreeningNote(snapshot:string,id:string,body:unknown,signal?:AbortSignal){const r=await post<ScreeningNote>(path+'/'+encodeURIComponent(id)+'/notes?'+new URLSearchParams({snapshot_id:snapshot}),body,signal);verifyMeta(r.meta,snapshot);return r.data;}
