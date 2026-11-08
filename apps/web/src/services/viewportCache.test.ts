import {expect,it,vi} from 'vitest';
import {ViewportCache,paddedViewport} from './viewportCache';
import type {Bbox} from '../types/municipal';
const b:Bbox=[-74.01,40.71,-74,40.72];
it('reuses complete covering areas and isolates snapshot/layer/filter/release keys',async()=>{
 const cache=new ViewportCache<string>();const data=['synthetic-test'];
 const request=cache.acquire('snapshot:roads:release:filter',paddedViewport(b),async()=>data);await request.promise;
 expect(cache.find('snapshot:roads:release:filter',b)).toBe(data);
 for(const context of ['new-snapshot:roads:release:filter','snapshot:permits:release:filter','snapshot:roads:new-release:filter','snapshot:roads:release:new-filter'])expect(cache.find(context,b)).toBeUndefined();
 expect(cache.find('snapshot:roads:release:filter',[-74.03,40.71,-74.02,40.72])).toBeUndefined();
 cache.clear();expect(cache.find('snapshot:roads:release:filter',b)).toBeUndefined();
});
it('deduplicates consumers and aborts only after the last consumer leaves; aborted results never cache',async()=>{
 const cache=new ViewportCache<string>();let resolve!:(data:string[])=>void;let signal!:AbortSignal;
 const load=vi.fn((s:AbortSignal)=>{signal=s;return new Promise<string[]>(r=>{resolve=r;});});
 const a=cache.acquire('s',b,load),c=cache.acquire('s',b,load);await Promise.resolve();expect(load).toHaveBeenCalledOnce();
 a.release();expect(signal.aborted).toBe(false);c.release();expect(signal.aborted).toBe(true);
 resolve(['late']);await a.promise;expect(cache.find('s',b)).toBeUndefined();
 const fresh=cache.acquire('s',b,async()=>['fresh']);await fresh.promise;expect(cache.find('s',b)).toEqual(['fresh']);
});
it('evicts least recently used coverage and enforces a record budget',async()=>{
 const cache=new ViewportCache<string>(2,3);
 for(const key of ['a','b'])await cache.acquire(key,b,async()=>[key]).promise;
 cache.find('a',b);await cache.acquire('c',b,async()=>['c']).promise;
 expect(cache.find('b',b)).toBeUndefined();expect(cache.find('a',b)).toEqual(['a']);
 await cache.acquire('oversize',b,async()=>['1','2','3','4']).promise;
 expect(cache.find('oversize',b)).toBeUndefined();
});
it('does not cache failed or partial requests',async()=>{
 const cache=new ViewportCache<string>();await expect(cache.acquire('s',b,async()=>{throw Error('failed page');}).promise).rejects.toThrow('failed page');expect(cache.find('s',b)).toBeUndefined();
});
