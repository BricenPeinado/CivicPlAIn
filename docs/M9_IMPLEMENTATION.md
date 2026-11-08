# M9 implementation and verification — 2026-11-08

**Delivered locally:** detailed OSM background, local/offline presentation, retained geometry during refresh, bounded viewport caching and bulk indicative ratings in the existing application. No commit/push/deployment, dependency installation, ingestion, migration or artifact rebuild. Existing `.gitignore` edit was preserved. M8 source/engineering/release gates remain open.

## Behavior

- MapLibre initializes its local style first and attaches optional OSM below infrastructure afterward. Remote tiles cannot delay infrastructure initialization. OSM retains street/building/intersection detail and attribution; `VITE_BASEMAP=local` creates no external basemap source. Visibility switches keep the same map instance.
- Same snapshot/filter/release/policy/date retains geometry during refresh or failure, with updating/previous-coverage disclosure. Different context is cleared synchronously. Complete results replace previous coverage; stale responses never do. Selected geometry stays independent.
- Covering-bounds LRU caches: at most 24 entries / 12,000 records each for municipal data and ratings. Local-data margin is 20% each side, never a matching tolerance or external-tile prefetch. Reads debounce 180ms, deduplicate identical in-flight requests, cancel when obsolete and validate complete pagination. A too-broad margin retries exact bounds under a separate cache key. Failed/aborted/incomplete results never cache; no entire-NYC default download. Cache lifetime is the mounted Map; reload/unmount clears it.
- Road geometry uses one bounded <=2000 record page, preserving provenance. JSON-mode validated rows serialize directly. Other municipal layers retain their stable complete pagination. Full histories never load to color roads.
- `GET /api/v2/standardized/map-ratings`: exact source snapshot, validated bounded bbox, all intersecting profiles or explicit zoom-required error. Read-only artifact access and one bounded in-memory spatial index; no per-street color requests or database writes. Warm queries use STRtree intersections. File identity/snapshot invalidates the index after explicit artifact replacement; reload the frontend to clear its prior cached coverage.
- Independent **Indicative Street Ratings** layer: Good `#277953`, Fair `#e2b52b`, Poor `#c43d3d`, Unknown `#859198`; Unclassified/missing rating stays neutral. Stored categories are used directly. Rating lines remain selectable when ordinary street geometry is hidden. Selection remains above ratings. Existing verified colors and overlays are separate.
- Six accessible checkboxes, always-visible rating legend and disclosure, responsive mobile controls, original shareable layer/camera/record state, keyboard list fallback. Incompatible/missing artifacts disable ratings with a reason; definitive compatibility failures are retained across pans until explicit retry/context change. Transient API errors remain visible and retryable.
- Inspector retains original numerical rating, date, counts, source and street-name limitation. Observation/permit lists still load ten at a time only on expansion. Verified inspection history/summary and hidden saved-planning catalog are now on demand. Existing engineering tools remain available; no indicative value enters calculations, priorities, screening, saved inputs or AI.
- GeoJSON updates skip unchanged references/content and initial empty-source re-publication. Visibility and unrelated overlay changes do not re-send roads. WebGL cleanup, map/source errors, tile-failure fallback and map retry are preserved.

## API changes

1. New `/api/v2/standardized/map-ratings?snapshot_id=…&bbox=w,s,e,n&limit=2000`: `standardized-read-v1` profiles plus `indicative-map-v1`, echoed bbox, `complete:true`, `road_id:null`. Limit 1–2000; no partial results. Geographic context `[-74.06,40.67,-73.95,40.76]`. Exact artifact `source_snapshot` required. Existing 409/503 compatibility errors; 422 for invalid/too-broad views.
2. Existing `/api/v2/road-segments` and `/road-segments/geojson`: limit ceiling 2000, default unchanged at 100. Bounded large-page map reads reject >2000 total matches. Original stable cursor, provenance, conditions and policy validation remain. Other collection limits unchanged.

Full contract: [API_SPEC](API_SPEC.md). Cache/index boundary: [ARCHITECTURE](ARCHITECTURE.md#m9-map-presentation-and-performance). Presentation semantics: [DATA_MODEL](DATA_MODEL.md#m9-indicative-map-projection).

## Actual measurements

Existing macOS development machine, installed dependencies, Python 3.12, local SQLite, exact source snapshot `nyc-4620b9e30c1c0bd5be4252fe27999c80`. No fabricated FPS, internet-latency guarantee or cold-machine benchmark. API measurements use FastAPI TestClient, include response parsing, and are **in-process rather than HTTP/browser timing**.

| Measurement | Actual result |
| --- | --- |
| Baseline viewport `-74.011,40.709,-74.003,40.716` | 426 roads; 5 sequential API requests; 945.33 / 978.58 / 980.37 ms |
| Final same viewport, 10 reads | 426 roads; 1 request; 182.48–328.87 ms; median 216.88 ms, nearest-rank p95 328.87 ms (includes first read) |
| Road improvement in this sample | 80% fewer requests; about 78% lower median total read time |
| New bulk ratings, same 426 roads | first index build/read 91.98 ms; 9 warm reads 13.31–14.87 ms; warm median 13.96 ms |
| Road/rating payload sizes | 1,570,535 / 282,643 bytes respectively; original road provenance retained, rating histories excluded |
| Browser local map readiness | 21.7 / 33.5 / 35.9 ms samples after Map construction; does not include app bundle/workspace discovery |
| Browser cached navigation | 0–2.3 ms cache-state handling; geometry already visible; no viewport HTTP request or road-source update for covered pans |
| Browser selected White Street rating | 38.6 ms to profile state |
| Browser initial larger coverage | 1,018–1,097 prefetched roads; observed 3,005–4,746 ms road refreshes including debounce; 3,188 ms also observed without test workers |
| Rating browser refresh | samples 238.9 / 354.9 ms; one 1,777.2 ms sample during concurrent test activity |

**Target assessment:** cached navigation comfortably meets the 300ms state/display target because existing geometry stays visible. Typical bounded in-process local reads meet 1 second. Larger initial browser loads do **not** consistently meet the 1-second target; this remains an optimization limit, not a claim of complete target attainment. Full road provenance payloads, initial concurrent workspace reads and browser processing remain costs. Browser source-worker completion/paint time and FPS were not independently instrumented; timing samples measure state readiness and `setData` submission, not GPU completion.

Development only: `window.civicplainMapMetrics`, `[map-count]` and `[map-time]` console entries. Counters include API reads, viewport requests, cache hits/misses/evictions/deduplication/cancellation and per-source GeoJSON submissions. Up to 100 timing samples per fixed metric, no record IDs, source text, geometry, personal data or external telemetry. Production recording is disabled. Ignored evidence: `data/processed/m9-baseline.json`, `m9-benchmarks.json` (intermediate/concurrent), `m9-final-benchmarks.json`, `m9-rating-coverage.json`.

## Executed QA

| Check | Result |
| --- | --- |
| `PYTHONPATH=apps/api .venv/bin/python -m pytest apps/api/tests -q` | **509 passed**, 344 existing library deprecation warnings, 31.62s |
| `npm test --prefix apps/web -- --reporter=dot` | **162 passed / 27 files**, 6.98s |
| `npm run typecheck --prefix apps/web` | PASS |
| `npm run build --prefix apps/web` | PASS; existing large MapLibre chunk advisory remains |
| `git diff --check` | PASS |
| Existing SQLite preservation | **26 preexisting SQLite files byte-identical**, including standardized artifact; read-only integrity_check `ok` |
| Standardized SHA-256 | `4b2f298b4903dbace7de5cd1f2c0dc29567e0c86ada8d76e8ee55352fc612752` unchanged |
| Complete rating coverage | Five in-process requests: one explicit broad rejection, four complete subdivisions; **all 4,150 unique roads** retrieved. Stored categories: 1,508 Good / 1,297 Fair / 76 Poor / 1,269 Unknown. No arbitrary category recomputation |

Tests cover covering-cache hits/misses/context invalidation, LRU/record budget, shared cancellation, rapid panning, out-of-order results, same-context retention/errors, synchronous cross-context clearing, rejected-margin coverage, incomplete/duplicate pagination, no repeated reads on visibility changes, source update isolation, local-first initialization, tile-failure isolation, independent rating hit layers, palette/unknown semantics, compatibility disabling/retry, read-only index reuse/replacement, bbox/limit validation, provenance preservation and existing synthetic/official planning/AI regressions. Authored miniature synthetic SQLite fixtures only. Automated tests make no external tile or NYC service requests.

Actual Chrome browser on matched 5199/8099:

- Detailed OSM streets/buildings/labels, infrastructure/rating overlays, attribution and selection rendered.
- Toggled detailed basemap and official streets independently; colored rating geometry remained when both were hidden. Keyboard panning reused coverage without clearing roads; resizing showed prior coverage with updating disclosure.
- With official streets hidden, clicked a green rating line directly: Centre Street LION 0032303 opened with retrieved 8.25/Good/115 observations/31 permits. Browser Back restored White Street; re-enabled ordinary streets.
- White Street selected through search: LION 0032075, actual profile 4.91/Fair/53 observations/33 permits; expanded both related lists and saw actual records and Load more controls. Pagination itself is covered by unchanged/new automated tests and prior integration evidence, not a new claim of browsing every history page.
- Selected older snapshot: explicit standardized mismatch disabled ratings; original street geometry stayed available. Returned to compatible snapshot without foreign evidence leakage.
- Restarted only the newly launched M9 frontend with `VITE_BASEMAP=local`: local streets/labels/shoreline/rating controls worked and Detailed basemap disabled with explanation. Returned it to `osm` afterward. Full OS-wide network disconnection and a real tile outage were not performed; tile-failure behavior was exercised with the MapLibre mock.
- 390×844 mobile unselected/selected views, controls, legend and White Street inspector inspected visually; corrected legend/action/zoom overlap. Restored the browser viewport.
- Synthetic mode loaded 24 authored roads and selected demo-r-001 with its existing inspector, repair and advisor actions. Full planning/AI/scenario behavior is supported by regressions; no new full manual replay of every historical workflow claimed.
- Bookmark selected-road state restored after reload. Final screenshot: ignored `data/processed/m9-map-proof.jpg`.

Preservation evidence: ignored `m9-preservation-before.json`, `m9-preservation-final.json`. No production database reset, migration, source rewrite, automatic refresh or saved-calculation mutation occurred.

## Run locally

From `/Users/bpeinado/Desktop/CivicPlAIn/CivicPlAIn`, terminal 1:

```sh
CIVICPLAIN_DATABASE_PATH="$PWD/data/tmp/standardized-integration.sqlite3" \
CIVICPLAIN_STANDARDIZED_DATABASE_PATH="$PWD/data/processed/CivicPlAIn_standardized.sqlite3" \
CIVICPLAIN_DATA_MODE=official \
CIVICPLAIN_OFFICIAL_SNAPSHOT_ID=nyc-4620b9e30c1c0bd5be4252fe27999c80 \
CIVICPLAIN_ALLOWED_ORIGINS=http://127.0.0.1:5199 \
PYTHONPATH=apps/api .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8099 --no-access-log
```

Terminal 2, same directory:

```sh
VITE_API_BASE_URL=http://127.0.0.1:8099/api/v1 \
VITE_MUNICIPAL_API_BASE_URL=http://127.0.0.1:8099/api/v2 \
VITE_BASEMAP=osm npm run dev --prefix apps/web -- --port 5199
```

Open [the map](http://127.0.0.1:5199/#/map?mode=official&snapshot=nyc-4620b9e30c1c0bd5be4252fe27999c80) or [White Street](http://127.0.0.1:5199/#/map?mode=official&snapshot=nyc-4620b9e30c1c0bd5be4252fe27999c80&road=road-0003cbb8adbb7e90987b689e). Stop each process with Ctrl+C. These paths already exist locally; no installation/import/migration is required. For offline mode restart frontend with `VITE_BASEMAP=local`. Keep matched v1/v2 URLs; refreshing an old frontend cannot upgrade a stale API. Earlier 8000/5173 and 8091/5191 processes were not stopped.

## Files changed and remaining work

Backend: `core/standardized_repository.py`, `routes/standardized.py`, `routes/municipal.py`, tests `test_standardized.py`, `test_m7_api.py`.

Frontend: existing `RoadMap`, `mapStyle`, `OfficialMapPage`, `MapToolbar`, `StreetEvidence`, `useMunicipalData`, `municipal.ts`, `standardized.ts`, routing and styles; new `performance.ts`, `viewportCache.ts`, `useViewportLayer.ts`, `useMapRatings.ts`. Added/extended their tests plus existing Navigation regression assertions for renamed controls. Shared docs: README, roadmap, API_SPEC, ARCHITECTURE, DATA_MODEL, M9 plan and this report. Existing `.gitignore` change belongs to the starting working tree.

Remaining: larger browser refresh target above; full clean installation, production-browser run, OS-offline/outage, screen-reader and broad accessibility certification were not repeated. OSM is best effort and requires internet for detail; local official geometry remains useful. Cache is session-memory only; broad >2000 views require zoom. The index supports bounded artifacts up to 100,000 roads, not a citywide scalable tile backend. Indicative named-street evidence is never verified segment condition, municipal approval or excavation clearance. Existing M8 engineering/source/operational gates and MapLibre bundle/deprecation advisories remain. Next separately authorized work should address those M8 gates and further bounded initial-map payload/performance work; none is silently marked complete here.

Manual action required now: none to prepare data. Use/restart the matched commands if servers are stopped; select local mode when offline. No commit/push/deployment was performed.
