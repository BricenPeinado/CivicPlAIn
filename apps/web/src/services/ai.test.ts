import { afterEach, expect, it, vi } from 'vitest';
import { explainContext, getAIStatus, saveReviewNote } from './api';
const meta={request_id:'test',dataset_snapshot_id:'demo-m1-v1',warnings:[],next_cursor:null};
afterEach(()=>vi.unstubAllGlobals());
it('uses versioned bounded AI routes and references without client totals',async()=>{
  const fetch=vi.fn().mockImplementation(()=>Promise.resolve(new Response(JSON.stringify({data:{},meta}))));vi.stubGlobal('fetch',fetch);
  await explainContext({type:'estimate',record_ids:['estimate/a']},'deterministic');
  await explainContext({type:'conflict',record_ids:['f']},'ai');
  await explainContext({type:'comparison',record_ids:['a','b','c']},'ai');
  await explainContext({type:'road',record_ids:['r']},'deterministic','Why flagged?');
  await getAIStatus();
  expect(fetch.mock.calls.map(c=>c[0].split('/api/v1')[1])).toEqual(['/ai/explain-estimate','/ai/explain-conflict','/ai/explain-scenario-comparison','/ai/ask','/ai/status']);
  expect(JSON.parse(fetch.mock.calls[0][1].body)).toEqual({estimate_id:'estimate/a',mode:'deterministic'});
  expect(JSON.parse(fetch.mock.calls[2][1].body)).toEqual({evaluation_ids:['a','b','c'],mode:'ai'});
  expect(JSON.parse(fetch.mock.calls[3][1].body)).toEqual({context:{type:'road',record_ids:['r']},mode:'deterministic',question:'Why flagged?'});
});
it('records acknowledged human notes at the evaluation route',async()=>{
  const fetch=vi.fn().mockResolvedValue(new Response(JSON.stringify({data:{id:'review'},meta})));vi.stubGlobal('fetch',fetch);
  await saveReviewNote('evaluation/a','Planner','Verify scope.');
  expect(fetch.mock.calls[0][0]).toMatch(/scenario-evaluations\/evaluation%2Fa\/reviews$/);
  expect(JSON.parse(fetch.mock.calls[0][1].body).acknowledged_limitations).toEqual(['synthetic_inputs','unknown_utilities','human_review']);
});
