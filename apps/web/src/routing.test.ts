import { expect, it } from 'vitest';
import { parseRoute, routeHref } from './routing';
it('round-trips pinned context and selected road without mutation commands', () => {
  const route = { view: 'map' as const, mode: 'official' as const, snapshot: 'nyc-11111111111111111111111111111111', road: 'road-abc' }; expect(parseRoute(routeHref(route))).toEqual(route);
});
it('rejects malformed mode, pin, road and unknown path', () => {
  for (const hash of ['#/missing', '#/map?mode=other', '#/map?snapshot=latest', '#/map?road=<script>']) expect(parseRoute(hash).error).toBeTruthy(); expect(parseRoute('')).toEqual({ view: 'map', road: null, mode: undefined, snapshot: undefined });
});
