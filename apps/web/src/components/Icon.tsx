export function Icon({ name }: { name: string }) {
  const paths: Record<string, string> = { map: 'm3 5 6-2 6 2 6-2v16l-6 2-6-2-6 2ZM9 3v16M15 5v16', dashboard: 'M3 3h7v7H3ZM14 3h7v7h-7ZM3 14h7v7H3ZM14 14h7v7h-7Z', projects: 'M3 7h18v14H3ZM7 7V3h10v4M3 12h18', scenarios: 'M4 5h16M4 12h16M4 19h16M8 3v4M16 10v4M10 17v4', road: 'M7 3 4 21M17 3l3 18M12 3v4m0 3v4m0 3v4', search: 'M20 20l-5-5M17 10a7 7 0 1 1-14 0 7 7 0 0 1 14 0', layers: 'm3 7 9-4 9 4-9 4ZM3 12l9 4 9-4M3 17l9 4 9-4', close: 'm6 6 12 12M6 18 18 6', list: 'M8 5h13M8 12h13M8 19h13M3 5h1M3 12h1M3 19h1' };
  return <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={paths[name] || paths.road}/></svg>;
}
