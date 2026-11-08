/** Development-only bounded scalars; no record IDs, geometry or source/user text. */
export const mapMetrics = {counters: {} as Record<string,number>, timings: {} as Record<string,number[]>};
export function countMap(name: string) {
  if (import.meta.env.DEV) {mapMetrics.counters[name] = (mapMetrics.counters[name] || 0) + 1; console.debug('[map-count]',name,mapMetrics.counters[name]);}
}
export function timeMap(name: string, start: number) {
  if (!import.meta.env.DEV) return;
  const values = mapMetrics.timings[name] ||= [];
  values.push(Math.round((performance.now() - start) * 100) / 100);
  console.debug('[map-time]',name,values[values.length-1]);
  if (values.length > 100) values.shift();
}
if (import.meta.env.DEV) Object.assign(window, {civicplainMapMetrics: mapMetrics});
