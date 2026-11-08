import {useEffect,useRef,useState} from 'react';
import type {Bbox} from '../../types/municipal';
import {DRAW_BOUNDS,blankWork,lineGeometry,validPoint,zoneColors,type Coordinate,type Draft,type DrawingSession,type WorkDraft} from './planningDraft';
type Props={autoStart?:boolean;snapshot:string;draft:Draft;change:(patch:Partial<Draft>)=>void;currentRoad?:string;bounds?:Bbox;onDrawing?:(session:DrawingSession|null)=>void};
export const sessions=new Map<string,{id:string;points:Coordinate[]}>();
export function PlanningForms({autoStart=false,snapshot,draft,change,currentRoad,bounds=DRAW_BOUNDS,onDrawing}:Props){
 const [drawing,setDrawing]=useState(sessions.get(snapshot)||null),[error,setError]=useState(''),[longitude,setLongitude]=useState(''),[latitude,setLatitude]=useState('');
 useEffect(()=>{if(drawing&&!draft.works.some(w=>w.id===drawing.id))setDrawing(null);},[draft.works,drawing]);
 const started=useRef(false);
 const addWork=()=>{const id=Array.from({length:3},(_,i)=>`zone-${i+1}`).find(id=>!draft.works.some(w=>w.id===id))!;change({works:[...draft.works,{...blankWork(),id,roads:currentRoad||''}]});setDrawing({id,points:[]});};
 useEffect(()=>{if(autoStart&&!started.current){started.current=true;if(!draft.works.length&&!draft.advancedWorks.trim())addWork();}},[autoStart]);
 const workChange=(index:number,patch:Partial<WorkDraft>)=>change({works:draft.works.map((w,i)=>i===index?{...w,...patch}:w)});
 const addPoint=(point:Coordinate)=>{
  if(!validPoint(point,bounds)){setError('Point outside supported snapshot/map bounds. Use longitude, latitude in EPSG:4326.');return;}
  if(drawing&&(drawing.points.length>=500||drawing.points.some(p=>p[0]===point[0]&&p[1]===point[1]))){setError('Use distinct points, maximum 500.');return;}
  setError('');setDrawing(d=>d?{...d,points:[...d.points,point]}:d);
 };
 const cancel=()=>{setDrawing(null);setError('');};
 const undo=()=>setDrawing(d=>d?{...d,points:d.points.slice(0,-1)}:d);
 const finish=()=>{if(!drawing)return;try{const geometry=lineGeometry(drawing.points,bounds);const index=draft.works.findIndex(w=>w.id===drawing.id);if(index<0)throw new Error('Work zone no longer exists.');workChange(index,{geometry:JSON.stringify(geometry),certainty:'approximate'});cancel();}catch(e){setError((e as Error).message);}};
 useEffect(()=>{if(drawing)sessions.set(snapshot,drawing);else sessions.delete(snapshot);onDrawing?.(drawing?{points:drawing.points,onPoint:addPoint,onUndo:undo,onCancel:cancel,onFinish:finish}:null);},[drawing,draft,bounds,onDrawing,snapshot]);
 useEffect(()=>()=>{onDrawing?.(null);},[onDrawing]);
 const begin=(w:WorkDraft)=>{let points:Coordinate[]=[];try{const g=JSON.parse(w.geometry);if(g.type==='LineString')points=lineGeometry(g.coordinates,bounds).coordinates as Coordinate[];}catch{/* New alignment */}setDrawing({id:w.id,points});setError('');};
 return <>
 <h3>1. Create hypothetical work zones</h3><p>Draw approximate alignments, then enter proposed schedules. Street selection only links a reference; it never supplies a verified footprint.</p>
 {!draft.works.length&&<p>Select a street, then add your first work zone.</p>}
 <button disabled={draft.works.length>=2||!!drawing||!!draft.advancedWorks.trim()} onClick={addWork}>Add hypothetical work</button>
 {drawing&&<section className="drawing-controls" aria-label="Work-zone drawing controls"><strong>Drawing mode active · {drawing.points.length} points</strong><p>Click the map to add vertices. Finish with at least two points. Map keyboard: Enter finishes, Backspace undoes, Escape cancels. Street selection is paused.</p><div className="planning-actions"><button onClick={finish}>Finish alignment</button><button disabled={!drawing.points.length} onClick={undo}>Undo point</button><button onClick={cancel}>Cancel drawing</button></div><details><summary>Enter coordinates with keyboard</summary><label>Longitude<input inputMode="decimal" value={longitude} onChange={e=>setLongitude(e.target.value)}/></label><label>Latitude<input inputMode="decimal" value={latitude} onChange={e=>setLatitude(e.target.value)}/></label><button onClick={()=>{if(!longitude.trim()||!latitude.trim()){setError('Both longitude and latitude are required.');return;}addPoint([Number(longitude),Number(latitude)]);}}>Add coordinate</button><ol>{drawing.points.map((p,i)=><li key={i}>{p.join(', ')}</li>)}</ol></details></section>}
 {error&&<p role="alert">{error}</p>}
 {draft.works.map((w,i)=><fieldset className="work-zone-form" key={w.id} style={{borderLeftColor:zoneColors[i%2]}}><legend>Work zone {String.fromCharCode(65+i)} · planning assumption</legend>
 <p>{w.title||'Untitled zone'} · {w.start||'Start unknown'} → {w.end||'End unknown'}</p>
 <label>Work {i+1} title<input maxLength={200} value={w.title} onChange={e=>workChange(i,{title:e.target.value})}/></label>
 <label>Work {i+1} type<select value={w.type} onChange={e=>workChange(i,{type:e.target.value})}>{['resurfacing','excavation','maintenance','inspection','other'].map(t=><option key={t} value={t}>{t[0].toUpperCase()+t.slice(1)}</option>)}</select></label>
 <label>Work {i+1} roads<input value={w.roads} onChange={e=>workChange(i,{roads:e.target.value})}/></label><small>Linked road reference · exact snapshot IDs. No geometry copied.</small>
 <p>{w.geometry?'Alignment supplied; field accuracy unverified.':'No alignment supplied.'}</p><button disabled={!!drawing} onClick={()=>begin(w)}>{w.geometry?'Edit':'Draw'} work zone {i+1}</button><button disabled={!!drawing||!w.geometry} onClick={()=>workChange(i,{geometry:''})}>Remove alignment {i+1}</button>
 <div className="planning-date-grid">{(['start','end'] as const).map(k=><label key={k}>Proposed {k}{k==='end'?' (exclusive)':''}<input aria-label={`Work ${i+1} ${k} (end exclusive)`} type="date" value={w[k]} onChange={e=>workChange(i,{[k]:e.target.value})}/></label>)}</div><small>Proposed work start/end; optional lane-closure start/end. Dates are planning assumptions, never permit dates.</small>
 <details><summary>Work evidence and optional lane closures</summary><label>Work {i+1} geometry certainty<select value={w.certainty} onChange={e=>workChange(i,{certainty:e.target.value})}><option value="approximate">Approximate</option><option value="declared">Declared · independently unverified</option></select></label>
 <div className="planning-date-grid">{(['closureStart','closureEnd'] as const).map(k=><label key={k}>Lane-closure {k==='closureStart'?'start':'end (exclusive)'}<input aria-label={`Work ${i+1} ${k} (end exclusive)`} type="date" value={w[k]} onChange={e=>workChange(i,{[k]:e.target.value})}/></label>)}</div>
 <label>Work {i+1} grade assumption<select value={w.grade} onChange={e=>workChange(i,{grade:e.target.value})}>{['unknown','surface','underground','elevated'].map(t=><option key={t} value={t}>{t[0].toUpperCase()+t.slice(1)}</option>)}</select></label>
 <label>Work {i+1} excavation assumption<select value={w.excavation} onChange={e=>workChange(i,{excavation:e.target.value})}><option value="unknown">Unknown</option><option value="yes">Yes</option><option value="no">No</option></select></label>
 <details><summary>Work author, date and rationale</summary><p>Blank overrides use the shared author, date entered and planning rationale below. Populated grade and excavation declarations carry this same attributed basis; unknown stays unknown.</p>{(['author','date','note'] as const).map(k=><label key={k}>Work {i+1} {k}<input type={k==='date'?'date':'text'} value={w[k]} placeholder={k==='date'?undefined:`Shared ${k}`} onChange={e=>workChange(i,{[k]:e.target.value})}/></label>)}</details>
 <details><summary>Advanced work geometry and references</summary><label>Work {i+1} GeoJSON geometry (EPSG:4326)<textarea value={w.geometry} onChange={e=>workChange(i,{geometry:e.target.value})}/></label><label>Work {i+1} permits<input value={w.permits} onChange={e=>workChange(i,{permits:e.target.value})}/></label></details></details>
 <button onClick={()=>{if(drawing?.id===w.id)cancel();change({works:draft.works.filter((_,index)=>index!==i),schedules:[]});}}>Remove work {i+1}</button></fieldset>)}
 <h3>2. Compare proposed schedules</h3><p>Alternatives change supplied dates only. Fewer findings do not establish an optimal or feasible plan.</p>
 <button disabled={draft.works.length!==2||draft.schedules.length>=2||!!draft.alternatives.trim()||!!draft.advancedWorks.trim()||!!drawing} onClick={()=>{const id=['alternative-1','alternative-2'].find(id=>!draft.schedules.some(a=>a.id===id))!;change({schedules:[...draft.schedules,{id,dates:draft.works.map(w=>({work_id:w.id,start:w.start,end:w.end,closureStart:w.closureStart,closureEnd:w.closureEnd}))}]});}}>Create alternative schedule</button>
 {draft.schedules.map((a,ai)=><fieldset key={a.id}><legend>{a.id} · proposed dates</legend>{a.dates.map((d,di)=><div key={d.work_id}><strong>{draft.works.find(w=>w.id===d.work_id)?.title||d.work_id}</strong><div className="planning-date-grid">{(['start','end','closureStart','closureEnd'] as const).map(k=><label key={k}>{a.id} · zone {di+1} · {{start:'Proposed start',end:'Proposed end (exclusive)',closureStart:'Optional closure start',closureEnd:'Optional closure end (exclusive)'}[k]}<input aria-label={`${a.id} work ${di+1} ${k}`} type="date" value={d[k]} onChange={e=>change({schedules:draft.schedules.map((v,j)=>j===ai?{...v,dates:v.dates.map((row,n)=>n===di?{...row,[k]:e.target.value}:row)}:v)})}/></label>)}</div></div>)}<button onClick={()=>change({schedules:draft.schedules.filter((_,i)=>i!==ai)})}>Remove {a.id}</button></fieldset>)}
 </>;
}
