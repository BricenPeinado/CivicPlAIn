import {useState} from 'react';
import {getMapRatings,type Profile} from '../services/standardized';
import {APIError} from '../services/http';
import {ViewportCache} from '../services/viewportCache';
import {useViewportLayer} from './useViewportLayer';
import type {Bbox} from '../types/municipal';
export function useMapRatings(snapshot:string,bounds:Bbox,retry:number) {
  const [cache]=useState(()=>new ViewportCache<Profile>());
  const [blocked,setBlocked]=useState<{snapshot:string;retry:number;error:string}|null>(null);
  const reason=blocked?.snapshot===snapshot && blocked.retry===retry?blocked.error:'';
  // Check compatibility once; do not repeat an impossible artifact read on every pan.
  const state=useViewportLayer(cache,JSON.stringify([snapshot,'indicative-map-v1']),bounds,!reason,retry,(bbox,signal)=>getMapRatings(snapshot,bbox,signal).catch(error=>{
    if(!signal.aborted && error instanceof APIError && (error.status===409 || error.code.startsWith('STANDARDIZED_DATABASE_') || error.status===404))setBlocked({snapshot,retry,error:error.message});
    throw error;
  }),'ratings');
  return reason?{...state,loading:false,error:reason}:state;
}
