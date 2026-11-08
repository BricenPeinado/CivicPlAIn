import {act,renderHook} from '@testing-library/react';
import {afterEach,expect,it,vi} from 'vitest';
import {ViewportCache,paddedViewport} from '../services/viewportCache';
import {useViewportLayer} from './useViewportLayer';
import {APIError} from '../services/http';
import type {Bbox} from '../types/municipal';
const a:Bbox=[-74.01,40.71,-74.008,40.712],b:Bbox=[-74,40.71,-73.998,40.712];
afterEach(()=>vi.useRealTimers());
const tick=()=>act(async()=>{await vi.advanceTimersByTimeAsync(181);});
it('retains same-context roads while refreshing/errors and reuses cached coverage without HTTP',async()=>{
 vi.useFakeTimers();const cache=new ViewportCache<string>();let resolve!:(d:string[])=>void;
 const load=vi.fn().mockResolvedValueOnce(['old']).mockImplementationOnce(()=>new Promise<string[]>(r=>{resolve=r;})).mockRejectedValueOnce(Error('offline'));
 const hook=renderHook(({bounds})=>useViewportLayer(cache,'s',bounds,true,0,load),{initialProps:{bounds:a}});await tick();expect(hook.result.current.data).toEqual(['old']);
 hook.rerender({bounds:b});expect(hook.result.current.data).toEqual(['old']);await tick();expect(hook.result.current.loading).toBe(true);
 await act(async()=>resolve(['new']));expect(hook.result.current.data).toEqual(['new']);
 hook.rerender({bounds:a});await act(async()=>{});expect(hook.result.current.data).toEqual(['old']);expect(load).toHaveBeenCalledTimes(2);
 hook.rerender({bounds:[-74.02,40.71,-74.018,40.712]});await tick();expect(hook.result.current.error).toBe('offline');expect(hook.result.current.data).toEqual(['old']);
});
it('aborts obsolete reads, ignores out-of-order results and clears foreign context synchronously',async()=>{
 vi.useFakeTimers();const cache=new ViewportCache<string>();let resolve!:(d:string[])=>void;let signal!:AbortSignal;
 const load=vi.fn().mockImplementationOnce((_:Bbox,s:AbortSignal)=>{signal=s;return new Promise<string[]>(r=>{resolve=r;});}).mockResolvedValue(['new']);
 const hook=renderHook(({bounds,context})=>useViewportLayer(cache,context,bounds,true,0,load),{initialProps:{bounds:a,context:'s'}});await tick();
 hook.rerender({bounds:b,context:'s'});expect(signal.aborted).toBe(true);await tick();expect(hook.result.current.data).toEqual(['new']);
 await act(async()=>resolve(['obsolete']));expect(hook.result.current.data).toEqual(['new']);
 hook.rerender({bounds:b,context:'other-snapshot'});expect(hook.result.current.data).toEqual([]);await tick();expect(load).toHaveBeenCalledTimes(3);
});
it('debounces rapid panning and does not refetch on loader identity or visibility changes',async()=>{
 vi.useFakeTimers();const cache=new ViewportCache<string>(),load=vi.fn().mockResolvedValue(['a']);
 const hook=renderHook(({bounds,enabled})=>useViewportLayer(cache,'s',bounds,enabled,0,(...args)=>load(...args)),{initialProps:{bounds:a,enabled:true}});
 hook.rerender({bounds:b,enabled:true});hook.rerender({bounds:a,enabled:true});await tick();expect(load).toHaveBeenCalledOnce();
 hook.rerender({bounds:a,enabled:false});hook.rerender({bounds:a,enabled:true});await tick();expect(load).toHaveBeenCalledOnce();
});
it('retries exact view when margin is too broad and never caches the failed margin as complete',async()=>{
 vi.useFakeTimers();const cache=new ViewportCache<string>(),load=vi.fn().mockRejectedValueOnce(new APIError('zoom','VIEWPORT_TOO_BROAD',422)).mockResolvedValueOnce(['complete exact']);
 const hook=renderHook(()=>useViewportLayer(cache,'s',a,true,0,load));await tick();expect(hook.result.current.data).toEqual(['complete exact']);
 expect(cache.find('s',a)).toEqual(['complete exact']);expect(cache.find('s',paddedViewport(a))).toBeUndefined();
});
