import { expect, it } from 'vitest';
import { parseRoute, routeHref } from './routing';
it('round-trips pinned context and selected road without mutation commands', () => {
  const route = { view: 'map' as const, mode: 'official' as const, snapshot: 'nyc-11111111111111111111111111111111', road: 'road-abc' }; expect(parseRoute(routeHref(route))).toEqual(route);
});
it('rejects malformed mode, pin, road and unknown path', () => {
  for (const hash of ['#/missing', '#/map?mode=other', '#/map?snapshot=latest', '#/map?road=<script>']) expect(parseRoute(hash).error).toBeTruthy(); expect(parseRoute('')).toEqual({ view: 'map', road: null, mode: undefined, snapshot: undefined });
});
it('round-trips record, filter, camera and layer links and keeps dashboard compatibility', () => {
  const route = { view:'projects' as const,mode:'official' as const,road:'road-a',snapshot:'nyc-11111111111111111111111111111111',permit:'permit-a',mapq:'BROADWAY',permitq:'M02',location:'unlocated' as const,status:'ISSUED',bbox:[-74.02,40.70,-73.99,40.72] as [number,number,number,number],layers:'streets,shoreline',condition:'unknown' as const };
  expect(parseRoute(routeHref(route))).toEqual(route); expect(parseRoute('#/overview').view).toBe('dashboard');
  for (const hash of ['#/projects?location=nearby','#/map?layers=streets,streets','#/map?bbox=1,2,3,4','#/map?bbox=-74.02,40.7,-74.02,40.72','#/projects?status=%20','#/scenarios?scenario=a&scenario=b','#/map?mode=official?road=a','#/map?mapq='+ 'a'.repeat(101),'#/map?layers=not-a-layer']) expect(parseRoute(hash).error).toBeTruthy();
});
