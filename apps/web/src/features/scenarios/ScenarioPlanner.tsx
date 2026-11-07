import { useEffect, useRef, useState } from 'react';
import { compareScenarios, createScenario, evaluateScenario, getRepairCatalog, getScenarios, getScenarioEvaluations, updateScenario } from '../../services/api';
import type { RepairOption, RoadsCollection, WorkProject } from '../../types/api';
import type { Scenario, ScenarioAction, ScenarioDraft, ScenarioEvaluation, ScenarioComparison, Provenance } from '../../types/scenarios';
import { ScenarioResults, ScenarioComparisonView, usd } from './ScenarioResults';

const fields = ['repair_category','repair_option_id','scope','quantity','schedule','constraints','project_overrides','budget_usd','repeat_justification'];
const fresh = (snapshot: string): ScenarioDraft => ({ contract_version:'scenario-v1', name:'', description:'', planning_objective:'Compare roadwork costs and coordination requirements', dataset_snapshot_id:snapshot, budget_usd:'0', currency:'USD', planning_start:'', planning_end:'', cost_scope:'roadwork_only', status:'draft', actions:[], assumptions:[], external_project_ids:[], project_overrides:[], mobilization_groups:[] });
const asDraft = (s: Scenario): ScenarioDraft => {
  const { id: _id, revision: _revision, revision_hash: _hash, created_at: _created, updated_at: _updated, method_version: _method, data_kind: _kind, synthetic_input: _synthetic, hypothetical: _hypothetical, ...draft } = s;
  return draft;
};
function normalize(d: ScenarioDraft, note: string): ScenarioDraft {
  const provenance: Provenance = { basis:'planning_assumption', evidence_ids:['assumption:editor'], note };
  return { ...d, assumptions:[...d.assumptions.filter(a=>a.id!=='editor'), { id:'editor', note, field_paths:fields }],
    project_overrides:d.project_overrides.map(o=>({ ...o, evidence_ids:['assumption:editor'] })), actions:d.actions.map(a=>{
      const unknown: Record<string,string> = {};
      if (!a.repair_option_id) unknown.repair_option_id='No reviewed method selected; cost unavailable.';
      if (a.quantity.derivation==='unknown') unknown.quantity='Quantity awaits explicit scope/area inputs.';
      if (!a.scope.geometry) unknown['scope.geometry']='Proposed work footprint is unknown.';
      if (a.scope.extent==='unknown') unknown['scope.extent']='Scope awaits review.';
      if (!a.schedule) unknown.schedule='No calendar schedule supplied.';
      else for (const field of ['start_date','end_date','closure_intervals'] as const) if (a.schedule[field]===null) unknown[`schedule.${field}`]='Not supplied; remains unknown.';
      return { ...a, unknown_reasons:unknown, input_provenance:{ ...Object.fromEntries(Object.entries(a.input_provenance).filter(([key])=>key!=='repeat_justification'||a.action_kind==='repeat_restoration')), ...Object.fromEntries(fields.filter(f=>f!=='project_overrides'&&f!=='budget_usd'&&f!=='repeat_justification').map(f=>[f,provenance])), ...(a.scope.geometry ? { 'scope.geometry': a.input_provenance['scope.geometry'] || provenance } : {}) },
        schedule:a.schedule ? { ...a.schedule, assumption_evidence_ids:['assumption:editor'], note, closure_intervals:a.schedule.closure_intervals?.map(c=>({ ...c,evidence_ids:['assumption:editor'] })) ?? null } : null };
    }) };
}
const newAction = (road: string): ScenarioAction => ({ id:crypto.randomUUID(), road_segment_id:road, action_kind:'repair', repair_category:'unknown', repair_option_id:null,
  scope:{ extent:'whole_segment', description:'Hypothetical whole-segment road repair; scope requires human review.', geometry:null, location_status:'unknown' },
  quantity:{ value:null, unit:'m2', derivation:'road_dimensions', length_m:null, width_m:null }, input_provenance:{}, unknown_reasons:{}, related_project_ids:[], schedule:null, constraints:{must_follow_action_ids:[],human_review_required:true} });

export function ScenarioPlanner({ roads, selectedRoad, projects }: { roads: RoadsCollection; selectedRoad: string | null; projects: WorkProject[] }) {
  const [scenarios,setScenarios]=useState<Scenario[]>([]);
  const [histories,setHistories]=useState<Record<string,ScenarioEvaluation[]>>({});
  const [options,setOptions]=useState<RepairOption[]>([]);
  const [loading,setLoading]=useState(true); const [busy,setBusy]=useState(false); const [error,setError]=useState('');
  const [saved,setSaved]=useState<Scenario|null>(null); const [draft,setDraft]=useState<ScenarioDraft|null>(null);
  const [note,setNote]=useState(''); const [evaluation,setEvaluation]=useState<ScenarioEvaluation|null>(null);
  const [selected,setSelected]=useState<string[]>([]); const [comparison,setComparison]=useState<ScenarioComparison|null>(null);
  const [retry,setRetry]=useState(0); const sequence=useRef(0); const controller=useRef<AbortController|null>(null);
  useEffect(()=>{
    const ac=new AbortController(); setLoading(true); setError('');
    Promise.all([getScenarios(ac.signal),getRepairCatalog(ac.signal)]).then(async ([list,catalog])=>{
      const history=await Promise.all(list.data.map(s=>getScenarioEvaluations(s.id,ac.signal)));
      if (!ac.signal.aborted) { setScenarios(list.data); setOptions(catalog.data); setHistories(Object.fromEntries(list.data.map((s,i)=>[s.id,history[i].data]))); }
    }).catch(e=>{ if(!ac.signal.aborted)setError(e.message); }).finally(()=>{ if(!ac.signal.aborted)setLoading(false); });
    return ()=>{ ac.abort(); controller.current?.abort(); sequence.current++; };
  },[retry]);
  function change(d: ScenarioDraft) { setDraft(d); setComparison(null); }
  function edit(s: Scenario) { setSaved(s); setDraft(asDraft(s)); setNote(s.assumptions.find(a=>a.id==='editor')?.note || s.assumptions.map(a=>a.note).join('\n')); setEvaluation(histories[s.id]?.[0] || null); setError(''); }
  async function persist(shouldEvaluate: boolean) {
    if(!draft) return;
    const normalized=normalize(draft,note.trim());
    if(!draft.name.trim() || !note.trim() || !draft.planning_start || !draft.planning_end) { setError('Enter a name, planning horizon and explicit assumption note.'); return; }
    if(!/^\d+(\.\d{1,2})?$/.test(draft.budget_usd)) { setError('Budget must be a nonnegative USD amount with at most two decimal places.'); return; }
    if(draft.planning_start>=draft.planning_end) { setError('Planning start must precede end.'); return; }
    if(draft.actions.some(a=>a.quantity.derivation==='explicit_area'&&(!a.quantity.value || !Number.isFinite(Number(a.quantity.value)) || Number(a.quantity.value)<=0))) { setError('Enter a positive partial repair area in m².'); return; }
    setBusy(true);setError('');const ac=new AbortController();controller.current=ac;const seq=++sequence.current;
    try {
      const result=saved ? await updateScenario(saved.id,saved.revision,normalized,ac.signal) : await createScenario(normalized,ac.signal);
      if(ac.signal.aborted||seq!==sequence.current)return;
      setSaved(result.data);setDraft(asDraft(result.data));setScenarios(old=>[...old.filter(s=>s.id!==result.data.id),result.data]);
      if(shouldEvaluate) {
        const r=await evaluateScenario(result.data.id,result.data.revision,ac.signal);
        if(ac.signal.aborted||seq!==sequence.current)return;
        setEvaluation(r.data);setHistories(old=>({ ...old,[result.data.id]:[r.data,...(old[result.data.id]||[]).filter(e=>e.id!==r.data.id)] }));
      }
    } catch(e) { if(!ac.signal.aborted)setError(e instanceof Error?e.message:'Scenario request failed.'); }
    finally { if(!ac.signal.aborted)setBusy(false); }
  }
  async function compareSelected() {
    setBusy(true);setError('');const ac=new AbortController();controller.current=ac;
    try { setComparison((await compareScenarios(selected,ac.signal)).data); } catch(e) { if(!ac.signal.aborted)setError(e instanceof Error?e.message:'Comparison failed.'); } finally { if(!ac.signal.aborted)setBusy(false); }
  }
  function updateAction(index:number,a:ScenarioAction) { if(draft) change({ ...draft,actions:draft.actions.map((old,i)=>i===index?a:old) }); }
  function addRoad(road:string) { if(draft) change({ ...draft,actions:[...draft.actions,newAction(road)] }); }
  return <section className="scenario-planner" id="scenario-planner" aria-label="Scenario planner">
    <div className="list-heading"><div><p className="eyebrow">BUDGET + COORDINATION</p><h2>Scenario Planner</h2><p>Hypothetical plans · Planning-level estimates · Human review required.</p></div><button className="primary-button" disabled={busy||loading} onClick={()=>{ setDraft(fresh(roads.meta.dataset_snapshot_id!));setSaved(null);setNote('');setEvaluation(null);setComparison(null);setError(''); }}>Create scenario</button></div>
    <div className="coverage-note">SYNTHETIC DEMONSTRATION. Unknown information remains unknown. Utility coverage is unknown. A budget result cannot establish suitability, safe deferral or excavation safety.</div>
    {loading&&<p role="status">Loading scenarios and repair catalog…</p>}
    {error&&<div role="alert"><p>{error}</p><button className="text-button" onClick={()=>setRetry(v=>v+1)}>Retry loading scenarios</button></div>}
    {!loading&&!scenarios.length&&<p>No saved scenarios. Create a hypothetical plan to begin.</p>}
    <div className="scenario-list">{scenarios.map(s=>{ const latest=histories[s.id]?.[0]; return <article key={s.id}><div><h3>{s.name}</h3><p>{s.description}</p><small>Budget {usd(s.budget_usd)} · {s.status} · Revision {s.revision}</small><p>{latest?`Last evaluated revision ${latest.scenario_revision}: ${latest.budget_status.replaceAll('_',' ')}${latest.scenario_revision!==s.revision?' — older than draft':''}`:'Not evaluated'}</p></div><button className="text-button" disabled={busy} onClick={()=>edit(s)}>Edit {s.name}</button>
      {latest&&<label><input type="checkbox" checked={selected.includes(latest.id)} disabled={busy||(!selected.includes(latest.id)&&selected.length>=3)} onChange={e=>{setSelected(old=>e.target.checked?[...old,latest.id]:old.filter(id=>id!==latest.id));setComparison(null);}}/>Compare {s.name}</label>}</article>; })}</div>
    <button className="primary-button" disabled={busy||selected.length<2} onClick={compareSelected}>Compare selected ({selected.length}/3)</button>
    {busy&&<p role="status">Saving or calculating from supplied inputs…</p>}
    {draft&&<form className="scenario-editor" aria-label="Scenario editor" onSubmit={e=>{e.preventDefault();void persist(true);}}>
      <h3>{saved?'Edit hypothetical plan':'New hypothetical plan'}</h3><p>{saved?`Saved revision ${saved.revision}. Saving creates a new revision; prior evaluations remain frozen.`:'Save a draft even when quantities, methods or dates are unknown.'}</p>
      <fieldset disabled={busy}><div className="scenario-form-grid">
        <label>Name<input required maxLength={200} value={draft.name} onChange={e=>change({...draft,name:e.target.value})}/></label>
        <label>Budget (USD)<input required inputMode="decimal" value={draft.budget_usd} onChange={e=>change({...draft,budget_usd:e.target.value})}/></label>
        <label>Planning start<input type="date" required value={draft.planning_start} onChange={e=>change({...draft,planning_start:e.target.value})}/></label>
        <label>Planning end (exclusive)<input type="date" required value={draft.planning_end} onChange={e=>change({...draft,planning_end:e.target.value})}/></label>
        <label>Description<textarea value={draft.description} maxLength={2000} onChange={e=>change({...draft,description:e.target.value})}/></label>
        <label>Planning objective<input value={draft.planning_objective} onChange={e=>change({...draft,planning_objective:e.target.value})}/></label>
        <label>Status<select value={draft.status} onChange={e=>change({...draft,status:e.target.value as ScenarioDraft['status']})}>{['draft','ready','archived'].map(s=><option key={s}>{s}</option>)}</select></label>
        <label>Explicit synthetic planning assumptions<textarea required value={note} maxLength={2000} onChange={e=>setNote(e.target.value)} placeholder="Explain method, scope, quantity, date, closure and budget assumptions; these are not observations."/></label>
      </div>
      <h4>Repair actions</h4><button type="button" className="text-button" disabled={!selectedRoad} onClick={()=>selectedRoad&&addRoad(selectedRoad)}>Add selected map road{selectedRoad?` (${selectedRoad})`:''}</button>
      <label>Add a road<select value="" onChange={e=>e.target.value&&addRoad(e.target.value)}><option value="">Choose road…</option>{roads.features.map(f=><option key={f.properties.id} value={f.properties.id}>{f.properties.name || f.properties.id} ({f.properties.id})</option>)}</select></label>
      {!draft.actions.length&&<p>No repair actions. Evaluation will be incomplete.</p>}
      {draft.actions.map((a,i)=><ActionEditor key={a.id} action={a} index={i} options={options} roads={roads} projects={projects} onChange={a=>updateAction(i,a)} onRemove={()=>change({...draft,actions:draft.actions.filter((_,n)=>n!==i)})}/>)}
      <h4>External project screening scope</h4><p>Select known projects explicitly. Related project links do not exclude or replace records.</p>
      <div className="scenario-projects">{projects.map(p=><div key={p.id}><label><input type="checkbox" checked={draft.external_project_ids.includes(p.id)} onChange={e=>change({...draft,external_project_ids:e.target.checked?[...draft.external_project_ids,p.id]:draft.external_project_ids.filter(id=>id!==p.id),project_overrides:e.target.checked?draft.project_overrides:draft.project_overrides.filter(o=>o.project_id!==p.id)})}/>{p.title} · SYNTHETIC · {p.start_date||'Unknown start'} → {p.end_date||'Unknown end'}</label>
        {draft.external_project_ids.includes(p.id)&&<><label>Hypothetical treatment of {p.title}<select value={draft.project_overrides.find(o=>o.project_id===p.id)?.operation==='exclude'?'exclude':draft.project_overrides.find(o=>o.project_id===p.id)?.replacement_action_ids[0]||'keep'} onChange={e=>{
          const value=e.target.value;const overrides=draft.project_overrides.filter(o=>o.project_id!==p.id);
          if(value!=='keep')overrides.push({project_id:p.id,operation:value==='exclude'?'exclude':'replace',replacement_action_ids:value==='exclude'?[]:[value],reason:'',evidence_ids:['assumption:editor']});
          change({...draft,project_overrides:overrides,actions:value!=='exclude'&&value!=='keep'?draft.actions.map(a=>a.id===value?{...a,related_project_ids:[...new Set([...a.related_project_ids,p.id])]}:a):draft.actions});
        }}><option value="keep">Keep original snapshot</option><option value="exclude">Explicitly exclude from this evaluation</option>{draft.actions.map(a=><option key={a.id} value={a.id}>Replace with action {draft.actions.indexOf(a)+1} ({a.road_segment_id})</option>)}</select></label>
        {draft.project_overrides.some(o=>o.project_id===p.id)&&<label>Reason for excluding or replacing {p.title}<input required value={draft.project_overrides.find(o=>o.project_id===p.id)!.reason} onChange={e=>change({...draft,project_overrides:draft.project_overrides.map(o=>o.project_id===p.id?{...o,reason:e.target.value}:o)})}/></label>}</>}
      </div>)}</div><p>Mobilization and contingency use separate per-action catalog allowances. Shared discounts are unsupported.</p>
      <div className="scenario-actions"><button type="button" className="text-button" onClick={()=>void persist(false)}>Save draft</button><button className="primary-button" type="submit">Save and evaluate</button></div></fieldset>
    </form>}
    {saved&&histories[saved.id]?.length>0&&<label>Saved evaluation history<select aria-label="Saved evaluation history" value={evaluation?.id||''} onChange={e=>setEvaluation(histories[saved.id].find(x=>x.id===e.target.value)||null)}><option value="">Choose snapshot…</option>{histories[saved.id].map(e=><option key={e.id} value={e.id}>Revision {e.scenario_revision} · {e.evaluated_at} · {e.budget_status}</option>)}</select></label>}
    {evaluation&&<ScenarioResults evaluation={evaluation}/>}{comparison&&<ScenarioComparisonView comparison={comparison}/>}
  </section>;
}

function ActionEditor({action:a,index,options,roads,projects,onChange,onRemove}:{action:ScenarioAction;index:number;options:RepairOption[];roads:RoadsCollection;projects:WorkProject[];onChange:(a:ScenarioAction)=>void;onRemove:()=>void}) {
  const schedule=a.schedule;
  function dates(start:string|null,end:string|null) {
    onChange({...a,schedule:{...schedule,start_date:start,end_date:end,assumption_evidence_ids:['assumption:editor'],note:'Explicit proposed calendar interval; independent of work duration.',closure_intervals:schedule?.closure_intervals?.length===1&&start&&end?[{...schedule.closure_intervals[0],start_date:start,end_date:end}]:schedule?.closure_intervals||null}});
  }
  return <fieldset className="scenario-action"><legend>Action {index+1} · {a.road_segment_id}</legend><div className="scenario-form-grid">
    <label>Work stage, action {index+1}<select value={a.action_kind} onChange={e=>onChange({...a,action_kind:e.target.value as ScenarioAction['action_kind'],input_provenance:{...a.input_provenance,repeat_justification:{basis:'planning_assumption',evidence_ids:['assumption:editor'],note:''}}})}><option value="repair">Repair</option><option value="repeat_restoration">Explicit repeat work (requires distinct dates and justification)</option>{a.action_kind==='temporary_patch'&&<option value="temporary_patch">Unpriced temporary patch</option>}</select></label>
    {a.action_kind==='repeat_restoration'&&<label>Repeat-work justification, action {index+1}<input required value={a.input_provenance.repeat_justification?.note||''} onChange={e=>onChange({...a,input_provenance:{...a.input_provenance,repeat_justification:{basis:'planning_assumption',evidence_ids:['assumption:editor'],note:e.target.value}}})}/></label>}
    <label>Repair method, action {index+1}<select value={a.repair_option_id||''} onChange={e=>{const option=options.find(o=>o.id===e.target.value);onChange({...a,repair_option_id:option?.id||null,repair_category:option?.treatment||'unknown',action_kind:a.action_kind==='repeat_restoration'?'repeat_restoration':'repair'});}}><option value="">Method unknown / unavailable</option>{options.map(o=><option key={o.id} value={o.id}>{o.label} · synthetic</option>)}</select></label>
    {!a.repair_option_id&&<label>Unpriced category, action {index+1}<select value={a.repair_category} onChange={e=>onChange({...a,repair_category:e.target.value,action_kind:e.target.value==='temporary_patch'?'temporary_patch':'repair',scope:e.target.value==='trench_restoration'?{...a.scope,extent:'utility_trench'}:a.scope,quantity:{...a.quantity,derivation:'unknown',value:null,length_m:null,width_m:null}})}>{['unknown','preventive','resurface','reconstruct','temporary_patch','trench_restoration'].map(c=><option key={c}>{c}</option>)}</select></label>}
    <label>Repair scope, action {index+1}<select value={a.scope.extent} onChange={e=>{const extent=e.target.value as ScenarioAction['scope']['extent'];onChange({...a,scope:{...a.scope,extent},quantity:{value:null,unit:'m2',derivation:extent==='whole_segment'?'road_dimensions':'unknown',length_m:null,width_m:null}});}}><option value="whole_segment">Whole segment</option><option value="partial_area">Explicit partial area</option><option value="utility_trench">Utility trench (no priced method)</option><option value="unknown">Unknown scope</option></select></label>
    <label>Scope description, action {index+1}<input required value={a.scope.description} onChange={e=>onChange({...a,scope:{...a.scope,description:e.target.value}})}/></label>
    <label>Quantity derivation, action {index+1}<select value={a.quantity.derivation} onChange={e=>onChange({...a,quantity:{value:null,unit:'m2',derivation:e.target.value as ScenarioAction['quantity']['derivation'],length_m:null,width_m:null}})}><option value="unknown">Unknown, awaiting inputs</option>{a.scope.extent==='whole_segment'&&<option value="road_dimensions">Frozen road planning dimensions</option>}{['partial_area','utility_trench'].includes(a.scope.extent)&&<option value="explicit_area">Explicit area assumption (m²)</option>}{a.scope.extent!=='unknown'&&<option value="explicit_rectangle">Explicit rectangle assumption (m)</option>}</select></label>
    {a.quantity.derivation==='explicit_area'&&<label>Repair area (m²), action {index+1}<input required inputMode="decimal" value={a.quantity.value||''} onChange={e=>onChange({...a,quantity:{...a.quantity,value:e.target.value||null}})}/></label>}
    {a.quantity.derivation==='explicit_rectangle'&&(['length_m','width_m'] as const).map(f=><label key={f}>{f==='length_m'?'Length':'Width'} (m), action {index+1}<input required inputMode="decimal" value={a.quantity[f]||''} onChange={e=>onChange({...a,quantity:{...a.quantity,[f]:e.target.value||null}})}/></label>)}
    <label>Proposed start, action {index+1}<input type="date" value={schedule?.start_date||''} onChange={e=>dates(e.target.value||null,schedule?.end_date||null)}/></label>
    <label>Proposed end (exclusive), action {index+1}<input type="date" value={schedule?.end_date||''} onChange={e=>dates(schedule?.start_date||null,e.target.value||null)}/></label>
    <label>Closure declaration, action {index+1}<select value={schedule?.closure_intervals==null?'unknown':schedule.closure_intervals.length?'closure':'none'} disabled={!schedule?.start_date||!schedule?.end_date} onChange={e=>{if(schedule)onChange({...a,schedule:{...schedule,closure_intervals:e.target.value==='unknown'?null:e.target.value==='none'?[]:[{start_date:schedule.start_date!,end_date:schedule.end_date!,lanes_closed:1,evidence_ids:['assumption:editor'],note:'Authored whole-envelope closure including setup/curing; verify with engineers.'}]}});}}><option value="unknown">Unknown</option><option value="none">Explicit assumption: no closure</option><option value="closure">Explicit closure for supplied interval</option></select></label>
    {!!schedule?.closure_intervals?.length&&<label>Declared lanes closed, action {index+1}<input type="number" min="0" step="1" required value={schedule.closure_intervals[0].lanes_closed} onChange={e=>onChange({...a,schedule:{...schedule,closure_intervals:schedule.closure_intervals!.map((c,j)=>j===0?{...c,lanes_closed:Number(e.target.value)}:c)}})}/></label>}
  </div><p>Preliminary workdays never set calendar dates. Missing closure data remains unknown.</p>
    <label><input type="checkbox" checked={a.scope.geometry!==null} onChange={e=>{const road=roads.features.find(f=>f.properties.id===a.road_segment_id);onChange({...a,scope:{...a.scope,geometry:e.target.checked&&road?road.geometry:null,location_status:e.target.checked?'approximate':'unknown'},input_provenance:{...a.input_provenance,'scope.geometry':{basis:'planning_assumption',evidence_ids:['assumption:editor'],note:'Explicit approximate road-centerline corridor reference; not a measured work footprint.'}}});}}/>Use approximate map corridor reference (not a measured work footprint)</label>
    <details><summary>Related utility/work projects, action {index+1}</summary>{projects.map(p=><label key={p.id}><input type="checkbox" checked={a.related_project_ids.includes(p.id)} onChange={e=>onChange({...a,related_project_ids:e.target.checked?[...a.related_project_ids,p.id]:a.related_project_ids.filter(id=>id!==p.id)})}/>{p.title}</label>)}</details>
    <button type="button" className="text-button" onClick={onRemove}>Remove action {index+1}</button>
  </fieldset>;
}
