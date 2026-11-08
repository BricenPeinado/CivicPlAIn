import type {Screen,ScreeningRecord} from '../../types/officialScreening';
const scheduleText=(schedule:unknown)=>{
 const v=schedule as {start?:string;end?:string}|null;
 return v?.start&&v?.end?`${v.start} → ${v.end} (end exclusive)`:'Unknown';
};
const key=(f:Screen['findings'][number])=>[f.finding_type,...[...f.activity_ids].sort()].join('|');
export function ScheduleComparison({record}:{record:ScreeningRecord}){
 const base=record.result.base,variants=[{id:'Original plan',screen:base},...record.result.alternatives];
 const costs=record.result.cost_comparison;
 const cost=(id:string)=>{
  if(costs.status!=='declared_comparable_scope')return 'Unknown · no supported cost basis';
  const total=id==='Original plan'?costs.base_total_usd:(costs.comparisons as {alternative_id:string;total_usd:string}[]|undefined)?.find(c=>c.alternative_id===id)?.total_usd;
  return typeof total==='string'?`USD ${total} · declared comparable scope only`:'Unknown';
 };
 return <section aria-label="Calculated schedule comparison"><h3>Calculated schedule comparison</h3>
 {!record.result.alternatives.length&&<p>No alternative supplied in this result. Create an alternative schedule and analyze to compare.</p>}
 <div className="schedule-table" role="region" aria-label="Schedule comparison table" tabIndex={0}><table><caption>Frozen supplied schedules · deterministic evidence, human review required</caption><thead><tr><th scope="col">Evidence</th>{variants.map(v=><th key={v.id} scope="col">{v.id}</th>)}</tr></thead><tbody>
 {base.activities.filter(a=>a.origin==='supplied_work').map(a=><tr key={a.activity_id}><th scope="row">{a.title}</th>{variants.map(v=><td key={v.id}>{scheduleText(v.screen.activities.find(w=>w.activity_id===a.activity_id)?.schedule)}</td>)}</tr>)}
 <tr><th scope="row">Supported findings</th>{variants.map(v=><td key={v.id}>{v.screen.findings.length}</td>)}</tr>
 <tr><th scope="row">Indeterminate checks</th>{variants.map(v=><td key={v.id}>{v.screen.indeterminate_pair_count}</td>)}</tr>
 <tr><th scope="row">Cost impact</th>{variants.map(v=><td key={v.id}>{cost(v.id)}</td>)}</tr>
 <tr><th scope="row">Human review</th>{variants.map(v=><td key={v.id}>Required</td>)}</tr>
 </tbody></table></div>
 {record.result.alternatives.map(a=>{const added=a.screen.findings.filter(f=>!base.findings.some(b=>key(b)===key(f))),removed=base.findings.filter(f=>!a.screen.findings.some(b=>key(b)===key(f)));return <p key={a.id}><strong>{a.id}:</strong> {added.length} added finding types/pairs ({added.map(f=>f.finding_type.replaceAll('_',' ')).join(', ')||'none'}); {removed.length} removed ({removed.map(f=>f.finding_type.replaceAll('_',' ')).join(', ')||'none'}). {a.interpretation}</p>;})}
 <p>Utility locations/depth, traffic impact, engineering feasibility and actual construction remain unverified. Finding changes establish neither savings nor a recommended schedule.</p></section>;
}
