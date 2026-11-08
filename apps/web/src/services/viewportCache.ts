import type {Bbox} from '../types/municipal';
import {countMap} from '../features/map/performance';
export const covers = (outer: Bbox, inner: Bbox) => outer[0] <= inner[0] && outer[1] <= inner[1] && outer[2] >= inner[2] && outer[3] >= inner[3];
/** View framing only, never a matching/measurement tolerance. */
export function paddedViewport(b: Bbox): Bbox {
  const x = (b[2]-b[0])*.2, y = (b[3]-b[1])*.2;
  return [Math.max(-74.06,b[0]-x),Math.max(40.67,b[1]-y),Math.min(-73.95,b[2]+x),Math.min(40.76,b[3]+y)];
}
interface Entry<T> {context:string; bounds:Bbox; data:T[]}
interface Flight<T> {controller:AbortController; promise:Promise<T[]>; users:number}
/** Complete pages only. 24 coverages / 12,000 records, LRU; immutable pinned snapshots. */
export class ViewportCache<T> {
  private entries = new Map<string,Entry<T>>();
  private flights = new Map<string,Flight<T>>();
  constructor(private maxEntries=24, private maxRecords=12000) {}
  find(context:string,bounds:Bbox): T[] | undefined {
    for (const [key,entry] of [...this.entries].reverse()) if (entry.context===context && covers(entry.bounds,bounds)) {
      this.entries.delete(key); this.entries.set(key,entry); countMap('cache.hit'); return entry.data;
    }
    countMap('cache.miss'); return undefined;
  }
  acquire(context:string,bounds:Bbox,load:(signal:AbortSignal)=>Promise<T[]>) {
    const key=JSON.stringify([context,bounds]);
    let flight=this.flights.get(key);
    if (!flight) {
      const controller=new AbortController();
      flight={controller,users:0,promise:Promise.resolve().then(()=>load(controller.signal)).then(data=>{
        if (!controller.signal.aborted) {
          this.entries.set(key,{context,bounds,data});
          let records=[...this.entries.values()].reduce((n,e)=>n+e.data.length,0);
          while (this.entries.size>this.maxEntries || records>this.maxRecords) {
            const oldest=this.entries.keys().next().value!;
            records-=this.entries.get(oldest)!.data.length; this.entries.delete(oldest); countMap('cache.eviction');
          }
        }
        return data;
      }).finally(()=>{if(this.flights.get(key)?.controller===controller)this.flights.delete(key);})};
      this.flights.set(key,flight); countMap('viewport.request');
    } else countMap('request.deduplicated');
    flight.users++;
    let released=false;
    return {promise:flight.promise,release:()=>{
      if(released)return;released=true;
      if (--flight!.users===0 && this.flights.get(key)===flight) {flight!.controller.abort();this.flights.delete(key);countMap('request.cancelled');}
    }};
  }
  clear() {this.entries.clear(); for(const f of this.flights.values())f.controller.abort();this.flights.clear();}
}
