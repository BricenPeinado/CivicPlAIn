import { expect, it } from 'vitest';
import { parseRoute, routeHref } from './routing';
it('round-trips pinned context and selected road without mutation commands', () => {
  const route = { view: 'map' as const, mode: 'official' as const, snapshot: 'nyc-11111111111111111111111111111111', road: 'road-abc' }; expect(parseRoute(routeHref(route))).toEqual(route);
});
it('pins an explicit intelligence release and date without auto selecting a release', () => {
  const r={view:'map' as const,mode:'official' as const,snapshot:'nyc-'+'1'.repeat(32),road:'road-a',intelligence:'intel-'+'2'.repeat(32),asof:'2026-11-08'};
  expect(parseRoute(routeHref(r))).toEqual(r);
  expect(parseRoute('#/map').intelligence).toBeUndefined();
  for (const hash of ['#/map?intelligence=latest','#/map?asof=2026-02-30','#/map?asof=20261108']) expect(parseRoute(hash).error).toBeTruthy();
});
it('rejects malformed mode, pin, road and unknown path', () => {
  for (const hash of ['#/missing', '#/map?mode=other', '#/map?snapshot=latest', '#/map?road=<script>']) expect(parseRoute(hash).error).toBeTruthy(); expect(parseRoute('')).toEqual({ view: 'map', road: null, mode: undefined, snapshot: undefined });
});
it('round-trips record, filter, camera and layer links and keeps dashboard compatibility', () => {
  const route = { view:'projects' as const,mode:'official' as const,road:'road-a',snapshot:'nyc-11111111111111111111111111111111',permit:'permit-a',mapq:'BROADWAY',permitq:'M02',location:'unlocated' as const,status:'ISSUED',bbox:[-74.02,40.70,-73.99,40.72] as [number,number,number,number],layers:'streets,shoreline',condition:'unknown' as const };
  expect(parseRoute(routeHref(route))).toEqual(route); expect(parseRoute('#/overview').view).toBe('dashboard');
  for (const hash of ['#/projects?location=nearby','#/map?layers=streets,streets','#/map?bbox=1,2,3,4','#/map?bbox=-74.02,40.7,-74.02,40.72','#/projects?status=%20','#/scenarios?scenario=a&scenario=b','#/map?mode=official?road=a','#/map?mapq='+ 'a'.repeat(101),'#/map?layers=not-a-layer']) expect(parseRoute(hash).error).toBeTruthy();
});
it('separately pins permit reviews and validates five geographic evidence statuses',()=>{
 const r={view:'projects' as const,road:null,mode:'official' as const,snapshot:'nyc-'+'1'.repeat(32),permitrelease:'intel-'+'2'.repeat(32),locstatus:'candidate' as const};expect(parseRoute(routeHref(r))).toEqual(r);
 for(const href of ['#/projects?locstatus=confirmed','#/projects?permitrelease=latest'])expect(parseRoute(href).error).toBeTruthy();
});

it('validates exact official planning identities and never stores private assumptions',()=>{
 const suffix='a'.repeat(64);
 expect(parseRoute('#/scenarios?estimate=estimate-'+suffix+'&priority=priority-'+suffix+'&screening=screen-'+suffix+'&tool=screening&alternative=later')).toMatchObject({estimate:'estimate-'+suffix,priority:'priority-'+suffix,screening:'screen-'+suffix,tool:'screening',alternative:'later'});
 for(const query of ['estimate=demo','screening=estimate-'+suffix,'priority=priority-'+suffix+'&priority=priority-'+suffix,'tool=approve','note=private'])expect(parseRoute('#/map?'+query).error).toBeTruthy();
});
