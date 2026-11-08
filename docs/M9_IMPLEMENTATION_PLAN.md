# M9 — Map performance, detailed basemap and indicative street ratings

Owner-authorized scope, 2026-11-08. Preserve the existing uncommitted `.gitignore` change. No dependencies, migrations, ingestion, artifact mutation, AI changes, commits or deployment. M8 engineering/source/release gates stay open.

## Strategy

1. Keep the existing MapLibre instance and local style; attach optional OSM raster after local style readiness, independently of infrastructure readiness. Toggle layer visibility in place.
2. Replace clearing viewport reads with context-isolated stale-while-revalidate display, a bounded covering-viewport LRU, modest margin, debounce, shared abortable requests and complete-result publication. Key snapshot, layer and all policy/filter context. Use a single bounded road page rather than repeated full query/enrichment per 100 records.
3. Read the supplied standardized artifact in SQLite read-only mode. Build a bounded process-local spatial index once per artifact identity/snapshot; return all intersecting profiles up to a hard limit, otherwise require zoom. No per-street coloring calls or engineering inputs.
4. Draw a separate indicative rating layer using stored categories, with unknown neutral, independent hit/hover, selection, accessible controls/legend and explicit name-association disclosure. Keep verified evidence distinct; load collapsed histories on demand.
5. Record development-only bounded timings/counters without source text or personal data. Test cancellation, cache identity, complete results, tile independence, stable source updates, read-only behavior and regressions. Measure real local reads and browser behavior where available.

## Acceptance

- Online OSM detail and local/offline layers work; tile errors cannot prevent local readiness.
- Same-context streets remain visible during refresh/errors, with updating or retained-data disclosure; no cross-snapshot/filter/policy leakage.
- Covered navigation reuses cached geometry; complete results only; bounded memory/response sizes, safe eviction and cancellation.
- Indicative green/yellow/red/gray lines, selection, keyboard inspector, controls and legend use actual standardized profiles; compatibility errors disable ratings with a reason.
- Original numerical rating, counts, dates, provenance and expandable records remain available. Indicative values never enter planning or AI.
- Required API/web tests, typecheck, build and whitespace pass; actual measurements, browser checks, preservation evidence and limitations are documented in M9_IMPLEMENTATION.
