import {useEffect,useState} from 'react';
import type {Bbox} from '../types/municipal';
import {ViewportCache,paddedViewport} from '../services/viewportCache';
import {APIError} from '../services/http';
import {timeMap} from '../features/map/performance';
export interface ReadState<T> {data:T; loading:boolean; error:string}
const EMPTY: never[]=[];
/** Rendering is identity-gated as well as effect-gated: foreign data never flashes. */
export function useViewportLayer<T>(cache:ViewportCache<T>,context:string,bounds:Bbox,enabled:boolean,retry:number,load:(bbox:Bbox,signal:AbortSignal)=>Promise<T[]>,metricName='viewport') {
  const [stored,setStored]=useState<ReadState<T[]> & {context:string}>({context:'',data:EMPTY,loading:enabled,error:''});
  const bbox=bounds.join(',');
  useEffect(()=>{
    if(!enabled)return;
    let active=true,release:(()=>void)|undefined;
    const start=performance.now();
    const cached=cache.find(context,bounds);
    if(cached){setStored({context,data:cached,loading:false,error:''});timeMap(`${metricName}.cached`,start);return;}
    setStored(old=>({context,data:old.context===context?old.data:EMPTY,loading:true,error:''}));
    const timer=setTimeout(()=>{
      const padded=paddedViewport(bounds);
      let request=cache.acquire(context,padded,signal=>load(padded,signal));
      release=request.release;
      const complete=request.promise.catch(e=>{
        if(e instanceof APIError && e.code==='VIEWPORT_TOO_BROAD' && active){
          // Cache exact coverage separately; a rejected margin is never marked loaded.
          request=cache.acquire(context,bounds,signal=>load(bounds,signal));release=request.release;
          return request.promise;
        }
        throw e;
      });
      complete.then(data=>{if(active){setStored({context,data,loading:false,error:''});timeMap(`${metricName}.refresh`,start);}})
        .catch(e=>{if(active)setStored(old=>({...old,loading:false,error:e.message}));});
    },180);
    return()=>{active=false;clearTimeout(timer);release?.();};
    // load is captured by the complete serialized context, not its render identity.
  },[cache,context,bbox,enabled,retry]);
  if(stored.context!==context)return {data:EMPTY,loading:enabled,error:''};
  return {...stored,loading:enabled&&stored.loading,error:enabled?stored.error:''};
}
