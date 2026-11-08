import type {FeatureCollection, LineString} from 'geojson';
import type {Bbox} from '../../types/municipal';
export type Coordinate=[number,number];
export type DrawingSession={points:Coordinate[];onPoint:(point:Coordinate)=>void;onUndo:()=>void;onCancel:()=>void;onFinish:()=>void};
export const DRAW_BOUNDS:Bbox=[-74.030,40.695,-73.980,40.730];
export const zoneColors=['#7042ad','#087e86'];
export function validPoint(p:unknown,bounds:Bbox=DRAW_BOUNDS):p is Coordinate{
 return Array.isArray(p)&&p.length===2&&p.every(v=>typeof v==='number'&&Number.isFinite(v))&&p[0]>=bounds[0]&&p[0]<=bounds[2]&&p[1]>=bounds[1]&&p[1]<=bounds[3];
}
export function lineGeometry(points:Coordinate[],bounds:Bbox=DRAW_BOUNDS):LineString{
 if(points.length<2||points.length>500||!points.every(p=>validPoint(p,bounds))||new Set(points.map(p=>p.join(','))).size!==points.length)throw new Error('Draw 2–500 distinct points inside the supported map bounds (longitude, latitude).');
 return {type:'LineString',coordinates:points};
}
export function drawingFeatures(points:Coordinate[],cursor?:Coordinate|null):FeatureCollection{
 const tail=cursor&&validPoint(cursor)?[...points,cursor]:points;
 return {type:'FeatureCollection',features:[...(tail.length>1?[{type:'Feature' as const,properties:{},geometry:{type:'LineString' as const,coordinates:tail}}]:[]),...points.map(p=>({type:'Feature' as const,properties:{},geometry:{type:'Point' as const,coordinates:p}}))]};
}
export type WorkDraft={id:string;title:string;type:string;roads:string;permits:string;geometry:string;certainty:string;start:string;end:string;grade:string;excavation:string;closureStart:string;closureEnd:string;author:string;date:string;note:string};
export const blankWork=():WorkDraft=>({id:'',title:'',type:'other',roads:'',permits:'',geometry:'',certainty:'approximate',start:'',end:'',grade:'unknown',excavation:'unknown',closureStart:'',closureEnd:'',author:'',date:'',note:''});
export type AlternativeDraft={id:string;dates:{work_id:string;start:string;end:string;closureStart:string;closureEnd:string}[]};
export type Draft={author:string;date:string;note:string;proximity:string;horizon:string;permits:string;release:string;works:WorkDraft[];advancedWorks:string;alternatives:string;cost:string;schedules:AlternativeDraft[]};
export const blank=():Draft=>({author:'',date:'',note:'',proximity:'',horizon:'',permits:'',release:'',works:[],advancedWorks:'',alternatives:'',cost:'',schedules:[]});
export const ids=(s:string)=>s.split(/[,\n]/).map(v=>v.trim()).filter(Boolean);
function date(value:string){return /^\d{4}-\d{2}-\d{2}$/.test(value)&&!Number.isNaN(Date.parse(value))&&new Date(value).toISOString().slice(0,10)===value;}
function basis(author:string,entered_on:string,note:string){
 if(!author.trim()||!date(entered_on)||!note.trim())throw new Error('Author, valid entered date and rationale are required for every declaration.');
 return {classification:'planning_assumption',author,entered_on,note,citations:[]};
}
function interval(start:string,end:string,evidence:ReturnType<typeof basis>,label:string,required=false){
 if(!start&&!end&&!required)return null;
 if(!date(start)||!date(end)||start>=end)throw new Error(`${label}: supply valid start and end dates with start before end (end exclusive).`);
 return {start,end,basis:evidence};
}
function schedules(w:{start:string;end:string;closureStart:string;closureEnd:string},evidence:ReturnType<typeof basis>,label:string,required=false){
 const schedule=interval(w.start,w.end,evidence,label,required),closure=interval(w.closureStart,w.closureEnd,evidence,`${label} closure`);
 if(closure&&(!schedule||closure.start<schedule.start||closure.end>schedule.end))throw new Error(`${label}: closure must be within the proposed work schedule.`);
 return {schedule,closure};
}
export function planningRequest(draft:Draft,snapshot:string,bounds:Bbox=DRAW_BOUNDS){
 const evidence=basis(draft.author,draft.date,draft.note);
 if(!/^\d+(\.\d+)?$/.test(draft.proximity)||Number(draft.proximity)>100||!/^\d+$/.test(draft.horizon)||Number(draft.horizon)>365)throw new Error('Explicit proximity 0–100 metres and integer horizon 0–365 days are required.');
 const works=draft.advancedWorks.trim()?JSON.parse(draft.advancedWorks):draft.works.map((w,i)=>{
  const label=`Work ${i+1}`;
  if(!w.title.trim())throw new Error(`${label}: project title is required.`);
  const own=basis(w.author||draft.author,w.date||draft.date,w.note||draft.note);
  let geometry=null;
  if(w.geometry.trim()){
   geometry=JSON.parse(w.geometry);
   // Advanced geometry remains validated by the existing server topology contract.
   if(geometry.type==='LineString')lineGeometry(geometry.coordinates,bounds);
   else if(geometry.type!=='Polygon')throw new Error(`${label}: use LineString or advanced Polygon geometry.`);
  }
  if(!geometry)throw new Error(`${label}: draw a work-zone alignment before analyzing. Use Advanced inputs for explicitly incomplete evidence.`);
  return {id:w.id,title:w.title,work_type:w.type,basis:own,road_ids:ids(w.roads),permit_ids:ids(w.permits),location:{geometry,crs:'EPSG:4326',certainty:w.certainty,basis:own},...schedules(w,own,label,true),grade:w.grade,grade_basis:w.grade==='unknown'?null:own,excavation_required:w.excavation==='unknown'?null:w.excavation==='yes',excavation_basis:w.excavation==='unknown'?null:own};
 });
 const alternatives=draft.alternatives.trim()?JSON.parse(draft.alternatives):draft.schedules.map(a=>({id:a.id,evidence,overrides:a.dates.map(d=>({work_id:d.work_id,...schedules(d,evidence,`Alternative ${a.id} / ${d.work_id}`,true)}))}));
 if(!works.length&&!ids(draft.permits).length)throw new Error('Add a work zone or select administrative evidence.');
 return {contract_version:'official-screen-v1',snapshot_id:snapshot,works,permit_ids:ids(draft.permits),permit_release_id:draft.release||null,proximity_m:Number(draft.proximity),reopening_horizon_days:Number(draft.horizon),policy_evidence:evidence,alternatives,cost_comparison:draft.cost.trim()?JSON.parse(draft.cost):null};
}
