import {expect,it} from 'vitest';
import {blank,blankWork,lineGeometry,validPoint,planningRequest,drawingFeatures} from './planningDraft';
const geometry=JSON.stringify({type:'LineString',coordinates:[[-74.01,40.712],[-74.009,40.712]]});
const draft=()=>({...blank(),author:'SYNTHETIC QA',date:'2026-11-08',note:'Synthetic test assumptions only',proximity:'5',horizon:'30',works:[{...blankWork(),id:'a',title:'SYNTHETIC A',geometry,start:'2027-01-01',end:'2027-01-10'},{...blankWork(),id:'b',title:'SYNTHETIC B',geometry,start:'2027-01-05',end:'2027-01-12'}]});
it('validates coordinate order, finite values, supported bounds, point count and distinctness',()=>{
 expect(lineGeometry([[-74.01,40.712],[-74.009,40.713]])).toEqual({type:'LineString',coordinates:[[-74.01,40.712],[-74.009,40.713]]});
 for(const p of [[40.712,-74.01],[NaN,40.712],[-74.5,40.712],[-74.01,40.712,1]])expect(validPoint(p)).toBe(false);
 for(const points of [[],[[-74.01,40.712]],[[-74.01,40.712],[-74.01,40.712]]])expect(()=>lineGeometry(points as [number,number][])).toThrow();
 expect(drawingFeatures([[-74.01,40.712]]) .features).toHaveLength(1);
 expect(drawingFeatures([[-74.01,40.712]],[-74.009,40.712]).features).toHaveLength(2);
 expect(drawingFeatures([]).features).toEqual([]);
});
it('builds two attributed, approximate declarations without inventing unknown grade or excavation',()=>{
 const r=planningRequest(draft(),'snapshot');expect(r.works).toHaveLength(2);expect(r.works[0]).toMatchObject({location:{crs:'EPSG:4326',certainty:'approximate'},grade:'unknown',grade_basis:null,excavation_required:null,excavation_basis:null});expect(r.cost_comparison).toBeNull();
 const d=draft();d.works[0].grade='surface';d.works[0].excavation='no';d.works[0].author='QA author override';expect(planningRequest(d,'snapshot').works[0]).toMatchObject({grade_basis:{author:'QA author override'},excavation_required:false,excavation_basis:{classification:'planning_assumption'}});
});
it('rejects missing evidence, reversed/invalid dates, incomplete geometry and closures outside schedule',()=>{
 for(const patch of [{author:''},{date:'2026-02-30'},{note:' '},{proximity:''},{horizon:'366'}])expect(()=>planningRequest({...draft(),...patch},'s')).toThrow();
 for(const patch of [{title:''},{start:''},{end:'2026-12-31'},{end:'2027-01-01'},{closureStart:'2027-01-02'},{closureStart:'2026-12-30',closureEnd:'2027-01-02'},{geometry:''},{geometry:'{"type":"Point","coordinates":[-74.01,40.712]}'}]){
  const d=draft();d.works[0]={...d.works[0],...patch};expect(()=>planningRequest(d,'s')).toThrow();
 }
});
it('uses existing schedule-only alternative contract and explicit closure overrides',()=>{
 const d=draft();d.schedules=[{id:'later',dates:d.works.map(w=>({work_id:w.id,start:'2027-03-01',end:'2027-03-10',closureStart:'',closureEnd:''}))}];
 const a=planningRequest(d,'s').alternatives[0];expect(a).toMatchObject({id:'later',evidence:{classification:'planning_assumption'},overrides:[{work_id:'a',schedule:{start:'2027-03-01',end:'2027-03-10'},closure:null},{work_id:'b',closure:null}]});
 d.schedules[0].dates[0].end='2027-02-01';expect(()=>planningRequest(d,'s')).toThrow(/Alternative/);
});
it('preserves the advanced contract for incomplete inputs and up to 30 work declarations',()=>{
 const d=draft();d.advancedWorks=JSON.stringify(Array.from({length:30},(_,i)=>({id:String(i),location:null,schedule:null})));d.alternatives='[]';expect(planningRequest(d,'s').works).toHaveLength(30);
});
