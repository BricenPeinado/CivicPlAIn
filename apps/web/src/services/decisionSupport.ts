import {readJSON} from './http';
import {verifyMeta} from './municipal';
import type {MunicipalEnvelope} from '../types/municipal';
import type {Route} from '../routing';
import type {AIExplanation} from '../types/ai';
export type DecisionKind='estimate'|'priority'|'screening';
export interface DecisionSummary {version:'decision-context-v1';snapshot_id:string;as_of_date:string;release_id:string|null;policy_id:string|null;condition:{roads:number;eligible:number;requiring_review:number;categories:Record<'good'|'fair'|'poor'|'unknown',number>;reasons:Record<string,number>};saved:Record<DecisionKind,{status:'available'|'unavailable';count:number|null;records:{id:string;created_at:string;road_id?:string}[];truncated:boolean;reason?:string}>;meaning:string;utility_coverage:'unknown';human_review_required:true}
const base=(import.meta.env.VITE_MUNICIPAL_API_BASE_URL||'http://127.0.0.1:8000/api/v2').replace(/\/$/,'');
export async function getDecisionSummary(snapshot:string,asof:string,route:Route,signal?:AbortSignal){
 const policy=route.intelligence&&snapshot==='nyc-3947b35876a619b31067db96b1409ad8'?'civicplain-pilot-pavement-v1.0':undefined;
 const r=await readJSON<MunicipalEnvelope<DecisionSummary>>(base,'/planning/decision-support?'+new URLSearchParams({snapshot_id:snapshot,as_of_date:asof,...(route.intelligence?{release_id:route.intelligence}:{}),...(policy?{policy_id:policy}:{})}),signal);verifyMeta(r.meta,snapshot);
 if(r.data.version!=='decision-context-v1'||r.data.snapshot_id!==snapshot||r.data.as_of_date!==asof||r.data.release_id!==(route.intelligence||null)||r.data.policy_id!==(policy||null)||r.data.utility_coverage!=='unknown'||r.data.human_review_required!==true)throw new Error('Decision context differs from selection.');return r.data;
}
export async function explainDecision(snapshot:string,kind:DecisionKind,record_id:string,mode:'deterministic'|'ai',signal?:AbortSignal){
 const response=await fetch(base+'/planning/decision-support/explanations',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({snapshot_id:snapshot,kind,record_id,mode}),signal:signal?AbortSignal.any([signal,AbortSignal.timeout(15000)]):AbortSignal.timeout(15000)});
 if(!response.ok)throw new Error(`Explanation unavailable (${response.status}). Saved evidence remains accessible.`);
 const r=await response.json() as MunicipalEnvelope<AIExplanation>;verifyMeta(r.meta,snapshot);
 if(r.data.source_classification!=='derived'||r.data.human_review_required!==true||r.data.evidence.records.length!==1||r.data.evidence.records.some(e=>e.dataset_snapshot_id!==snapshot||e.record_id!==record_id||e.synthetic_input))throw new Error('Explanation provenance differs from selection.');return r.data;
}
