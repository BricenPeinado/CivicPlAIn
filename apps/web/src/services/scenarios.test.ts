import { afterEach, expect, it, vi } from 'vitest';
import { getScenarios, updateScenario, compareScenarios, evaluateScenario } from './api';
import type { ScenarioDraft } from '../types/scenarios';
const meta={request_id:'test',dataset_snapshot_id:'demo-m1-v1',warnings:[],next_cursor:null};
afterEach(()=>vi.unstubAllGlobals());
it('uses PATCH and optimistic revision payloads, and reports field-level validation errors',async()=>{
  const fetch=vi.fn().mockResolvedValueOnce(new Response(JSON.stringify({data:{id:'saved'},meta}),{status:200})).mockResolvedValueOnce(new Response(JSON.stringify({error:{message:'Invalid request fields',field_errors:[{path:'body.budget_usd',reason:'Must be nonnegative'}]}}),{status:422}));
  vi.stubGlobal('fetch',fetch);
  await updateScenario('scenario/a',2,{name:'Revised'} as ScenarioDraft);
  expect(fetch.mock.calls[0][0]).toMatch(/\/scenarios\/scenario%2Fa$/);
  expect(fetch.mock.calls[0][1].method).toBe('PATCH');
  expect(JSON.parse(fetch.mock.calls[0][1].body)).toEqual({expected_revision:2,draft:{name:'Revised'}});
  await expect(evaluateScenario('saved',2)).rejects.toThrow('body.budget_usd: Must be nonnegative');
});
it('loads all scenario pages with stable cursor and rejects a repeated cursor',async()=>{
  const fetch=vi.fn().mockResolvedValueOnce(new Response(JSON.stringify({data:[{id:'a'}],meta:{...meta,next_cursor:'a'}}))).mockResolvedValueOnce(new Response(JSON.stringify({data:[{id:'b'}],meta})));
  vi.stubGlobal('fetch',fetch);
  expect((await getScenarios()).data.map(s=>s.id)).toEqual(['a','b']);
  expect(fetch.mock.calls[1][0]).toMatch(/after=a/);
  fetch.mockReset().mockImplementation(()=>Promise.resolve(new Response(JSON.stringify({data:[],meta:{...meta,next_cursor:'a'}}))));
  await expect(getScenarios()).rejects.toThrow('Invalid scenario pagination');
});
it('compares immutable evaluation references using the documented route',async()=>{
  const fetch=vi.fn().mockResolvedValue(new Response(JSON.stringify({data:{id:'comparison'},meta})));
  vi.stubGlobal('fetch',fetch);await compareScenarios(['a','b']);
  expect(fetch.mock.calls[0][0]).toMatch(/\/scenario-comparisons$/);
  expect(JSON.parse(fetch.mock.calls[0][1].body)).toEqual({evaluation_ids:['a','b']});
});
