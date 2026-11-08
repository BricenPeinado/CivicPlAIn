# M7.2 — Map-first interface redesign

Implemented and verified locally **2026-11-07 America/New_York / 2026-11-08 UTC**. This report records the interface checkpoint after [M7.1](M7_1_IMPLEMENTATION.md); it does not replace the shared API/data contracts or historical milestone reports. No commit, push, deployment, dependency installation, backend/schema change or new demo experience was performed for 7.2.

## Delivered behavior

The existing React application now opens to a full-height map workspace with a 100px charcoal navigation rail, compact data context, floating search/layers and one 344px inspector (310px at intermediate widths). Map, Dashboard, Projects and Scenarios are distinct views. The old guide, milestone labels, placeholder controls and stacked main-screen feature panels are removed. Existing planning features are relocated, not replaced.

Official mode reads immutable `/api/v2` snapshots from the existing FastAPI application. Synthetic mode retains `/api/v1`, its authored fixture labels, estimates, conflict screening, scenario drafts/history/evaluations/comparisons, advisor fallback and review notes. No real road is priced or screened with synthetic inputs. No read, route change or camera movement runs a calculation or writes an analysis. Synthetic Projects requires an explicit **Run conflict screening** action.

The road inspector shows the source name, SegmentID **and export row identity**, accepted dated pavement evidence or a clear unknown state, available physical attributes, accepted permit links, coverage, provenance and explicit planning capability limits. Native disclosures keep raw identifiers, source revisions, checksums, matching evidence and terms available without crowding the overview. Original floating inspection timestamps are displayed as their local calendar date without timezone conversion; the full value remains in the element title and source evidence.

Desktop map/search/list share stable record IDs. Search spans the pinned road snapshot by name/source key, uses bounded server pages and explicit Load more. The keyboard list also exposes inspection records and located permits within the current geographic view, even with those map overlays hidden. **Narrow geographic view** and **Reset view** update query bounds without requiring WebGL; choosing a road frames its source bbox with a 0.0005-degree presentation margin. This margin only frames a view: it is not an accuracy claim, spatial matching threshold or calculation input. Escape closes transient search/layers and restores search focus.

At ≤760px, labeled bottom navigation replaces the rail. A selected inspector occupies at most 53% of the workspace, with its own scroll region; the map retains 47%. Opening the record list gives the list the full map area. Selecting a record closes the mobile list. At narrow widths, layer controls compact and popovers remain within the map. Attribution and Sources & terms remain reachable.

## Geographic sources and truthful display

The local pilot is **`nyc-3947b35876a619b31067db96b1409ad8`**, in ignored `data/tmp/m7-official-pilot.sqlite3`. Exact acquired endpoints, schema/CRS decisions, hashes, licenses and ingestion procedures remain authoritative in [M7.1](M7_1_IMPLEMENTATION.md) and [DATA_SOURCES](DATA_SOURCES.md). This stage made no new acquisition or match decisions.

| Layer | Rendering and evidence boundary |
| --- | --- |
| NYC DCP LION | Actual full WGS84 line coordinates supplied by the backend; source street-name labels. 4,150 export rows in the snapshot, not necessarily distinct SegmentIDs. No schematic substitution, clipping or authored landmark coordinates. |
| NYC DOT pavement observations | Opt-in original inspection geometries, all imported dates, original decimal rating on a continuous blue scale; missing rating gray. No inferred good/fair/poor category or accepted road association. The pilot contains 8,726 dated observations, **zero accepted road links**. Raw inspection selection exposes rating/date/uncertainty separately from the road assessment. |
| NYC DOT permits | Opt-in source geometry or accepted road-reference geometry only. Road references remain dashed lines with work footprint unknown, never invented point markers. The pilot's 4,735 records are **all unlocated/unmatched**; therefore there are no pilot permit markers or accepted related-road permits. Projects retains and searches these administrative records. A permit does not establish work started, a confirmed schedule or a conflict. |
| NYC OTI/DOITT shoreline | Three genuine source lines, separate context overlay; no invented land polygon. |
| Optional OpenStreetMap | Standard interactive raster context at `https://tile.openstreetmap.org/{z}/{x}/{y}.png`, max source zoom 19, visible OpenStreetMap contributors/ODbL attribution. Source geometry and labels remain independently available. |

The study selection is [-74.020,40.700,-73.985,40.725]; context bounds [-74.030,40.695,-73.980,40.730]. The initial City Hall/Broadway focus is [-74.011,40.709,-74.003,40.716] to avoid an unnecessarily broad first read. These are application extents, not official neighborhood boundaries. Camera interaction is bounded by the context window. Full source geometries remain intact and the API performs geographic intersection queries.

No utility coordinates/depths, traffic, costs, budgets, predictions or actual construction schedules are introduced. Original source coverage/matching limitations remain visible. Synthetic records never enter official map sources; a failed official request never substitutes fixtures.

## Basemap, attribution and local assets

The verified [OSM standard tile policy](https://operations.osmfoundation.org/policies/tiles/) requires the exact HTTPS tile URL, visible attribution, ordinary browser Referer/cache behavior and no bulk/prefetch/offline tile fetching. The service is **best-effort, without an SLA**. This application uses normal browser requests, with no tile proxy, cache-busting, archive download or offline tile package. [OSM copyright/ODbL](https://www.openstreetmap.org/copyright) is linked on the map and in Sources & terms. A future high-volume deployment requires a separately reviewed provider/service plan.

[MapLibre's local-font label support](https://maplibre.org/maplibre-gl-js/docs/examples/style-labels-with-local-fonts/) renders source names using installed Arial/Helvetica/system sans fonts without external glyph URLs. Existing local MapLibre ESM worker, stylesheet and dependency notices remain. There are no new font, sprite, icon, geocoder, router, state-library or UI-kit dependencies. Icons are simple inline SVG authored in the repository.

Sources & terms reproduces the complete application disclaimer required by [NYC DOT](https://www.nyc.gov/html/dot/html/about/datafeeds.shtml#disclaimer), separately from each record's publisher/dictionary/terms. Catalog license fields remain null where M7.1 found them null; this interface does not relicense municipal data or claim blanket redistribution clearance.

Automated/browser checks used **`VITE_BASEMAP=local`**, without requesting OSM tiles. Hosted tile availability and production provider suitability were not certified. The official local streets/labels and coastline provide geographic context in that mode.

## Implementation and architectural decisions

The modular monolith, REST boundary, SQLite storage and deterministic domain engines are unchanged. V1 transport stays unchanged to reduce regression risk. Basic four-view relocation moved forward from 7.3 because removing the crowded stack required usable destinations; deeper filters/navigation remain 7.3 work.

| Files under `apps/web/src` unless stated | Responsibility |
| --- | --- |
| `App.tsx`, `routing.ts` | Shell, named navigation, validated hash route, explicit mode/snapshot discovery, no silent fallback, route focus/skip link and retained synthetic workspace |
| `types/municipal.ts`, `services/http.ts`, `services/municipal.ts` | Source-neutral typed DTOs, 10-second per-request deadline, abort, sanitized errors, pinned snapshot/identity checks, pagination and viewport guard |
| `hooks/useMunicipalData.ts` | Independent debounced/cancelled viewport layer reads; no stale response replacement; shoreline context separate from viewport |
| `pages/OfficialMapPage.tsx` | Official map/search/keyboard list, geographic refinement, dated evidence inspector, raw record selection, independent retries and capability states |
| `pages/OfficialRecordsPage.tsx` | Basic snapshot-wide overview and paginated all-permit search/detail; no WebGL dependency |
| `pages/SyntheticWorkspace.tsx` | Existing repair/advisor, conflict and scenario workflows in their explicit synthetic context |
| `features/map/RoadMap.tsx`, `mapStyle.ts`, `colors.ts` | Extended existing MapLibre map, true source geometry/local labels, independent overlays, selected/hover/screening styles and error fallback; synthetic poor condition now amber |
| `components/MapToolbar.tsx`, `Icon.tsx`, `MunicipalEvidence.tsx`, `DataTerms.tsx` | Floating controls, inline icons, progressive source evidence and required attribution/disclaimer |
| `styles/tokens.css`, `styles/map.css`, `styles.css` | Tokens, responsive shell/map/inspector, visible focus/reduced-motion rules and retained planning-feature styles; obsolete guide/layout styles removed |
| `features/conflicts/useConflicts.ts`, `ConflictReview.tsx` | Read-only initial project loading; explicit screening action; no false “no conflicts” before analysis |
| `features/estimates/RepairPlanner.tsx` | Catalog-unavailable copy without developer/milestone instructions; repair behavior unchanged |
| `features/scenarios/ScenarioPlanner.tsx` | Native dirty/busy beforeunload warning; existing calculation/save semantics retained |
| Tests adjacent to modules; `test-municipal.ts` | Route-aware regression and source-shaped test-only records, never an official acquisition fixture |
| Root `.env.example`, `scripts/demo.py` | Public v2/base-map configuration; existing startup helper passes both API bases on alternate ports, explicitly synthetic/local and no obsolete guide instruction |

Native disclosures replace proposed inspector tabs to reduce control density. Local fonts replace planned packaged glyph assets. The synthetic workspace and scenario editor remain mounted after first use across navigation/context switches, preserving drafts, original revisions and pending-write reconciliation without global state-library or automatic saves. Inactive content is hidden and keyboard inaccessible; direct Dashboard/Scenarios navigation does not instantiate the map. Reload warnings are browser-dependent; full browser close/restart is not durable draft recovery.

Implemented hash routes: `#/map`, `#/dashboard`, `#/projects`, `#/scenarios`. Accepted query keys are only `mode`, `snapshot`, `road`; unknown/repeated/malformed parameters show a correction state. Back/forward/refresh restore valid view/context/road; a selected road restores source focus. Camera/search/layer state and permit/scenario/evaluation deep links are not yet persisted in URLs.

## Run and verify

Use an already published database/pin; do not import or migrate just to start the interface. From the repository root, start the API and frontend in separate terminals:

```sh
CIVICPLAIN_DATABASE_PATH="$PWD/data/tmp/m7-official-pilot.sqlite3" CIVICPLAIN_DATA_MODE=official CIVICPLAIN_OFFICIAL_SNAPSHOT_ID=nyc-3947b35876a619b31067db96b1409ad8 PYTHONPATH=apps/api .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
VITE_BASEMAP=local npm run dev --prefix apps/web
```

Open `http://127.0.0.1:5173/`. Omit `VITE_BASEMAP=local` for optional ordinary interactive OSM context. `VITE_BASEMAP=osm` is the other recognized value; unsupported values fail closed to local mode. Both synthetic and official reads need the same running application, using independent public `VITE_API_BASE_URL` (default `/api/v1` on port 8000) and `VITE_MUNICIPAL_API_BASE_URL` (default `/api/v2` on port 8000). Vite values are build-time and never contain keys. Alternate frontend ports must also appear in `CIVICPLAIN_ALLOWED_ORIGINS`; bind only to loopback. Synthetic mode uses existing seeded fixtures; the ordinary database is not modified by this UI stage.

Verification commands:

```sh
npm test --prefix apps/web
npm run typecheck --prefix apps/web
npm run build --prefix apps/web
PYTHONPATH=apps/api .venv/bin/python -m pytest apps/api/tests -q
git diff --check
```

Frontend: **80 tests across 13 files passed**, typecheck passed, production build passed. Backend regression: **265 passed**, with 70 existing Starlette/httpx and M7.1 Shapely deprecation warnings. No lint command exists. The MapLibre chunk remains about 1,072 kB raw/291 kB gzip plus its 519 kB local worker; Vite's existing large-chunk advisory remains. The shell is about 307 kB raw/92 kB gzip; ScenarioPlanner is separately lazy-loaded. No performance SLA follows from build sizes.

Tests retain meaningful M1–M6 planning/source/selection/scenario/advisor assertions, replacing obsolete guide/layout assertions. New coverage includes snapshot and record identity, synthetic rejection, cursor loops/duplicates/broad views, exact coordinate presentation, decimal ratings and unknown categories, no ambiguous/unlocated pins, accepted road references, independent layers, stale viewport/selection cancellation, raw dated inspection selection, keyboard list selection/geographic refinement, optional-source/tile/WebGL failure, invalid routes, no navigation analysis writes and retained dirty scenario drafts across modes. MapLibre unit mocks do not establish actual geographic recognizability or accessibility.

Actual browser verification used the isolated M7.1 database with API port 8001 and frontend port 5174, and the existing isolated synthetic helper on ports 8012/5182. Both development and production assets were exercised. Chromium/WebGL checks covered 1280px desktop, 768px tablet, 390px mobile and 320px narrow layouts; real LION lines/names, pointer road/inspection selection, keyboard raw inspection selection, source evidence, search/list, layers/legend, map resize, bottom inspector/list behavior, source-backed Dashboard, unlocated permit detail and a synthetic repair preview. No saved official or synthetic calculation was created by these checks. Browser logs for the final official map contained no warnings/errors. Hosted OSM tiles were not fetched by automation.

## Remaining limits and next stages

- Source accuracy, accepted road links and geographic permit precision remain M7.1 limitations. “No accepted road assessment/permit links” is expected for this pilot, not an empty source or evidence of safe excavation.
- Viewport reads page full records and reject >2,000 records per layer rather than truncating. Historical inspection views can exceed that count; zoom or use keyboard geographic refinement. Initial load and local API page count are not citywide performance benchmarks.
- Latest accepted inspection is shown only when the backend supplies `latest_usable_id`; conflicting latest evidence stays unknown. All-date raw overlays must not be interpreted as a current condition map.
- 7.3 owns richer Dashboard grouping/filter links, permit status/location filters, additional record/camera/filter deep links and navigation refinement. The four basic destinations are already usable.
- 7.4 owns the full browser matrix, screen-reader and contrast audit, 200% zoom, touch-target audit, sustained CPU/GPU/latency checks and complete integration certification. Scoped responsive/browser checks here are not WCAG certification. Basemap service availability/deployment suitability remains an operational choice.
- Real-road planning calculations require reviewed costs/scopes/schedules and a versioned source-neutral calculation boundary. That remains unavailable; no guessed inputs or AI predictions fill it.

Open product decisions: which hosted basemap service/SLA is appropriate for a future deployed workload; which source-approved rating definition and reviewed road-link process should enable current-road condition summaries; what official permit geography can legitimately support locations; and which richer 7.3 filter/deep-link workflows have priority. None requires inventing data or blocking this local interface checkpoint.
