# Milestone 1 implementation report

Completed and verified locally on 2026-11-07. Branch: `feat/m1-app-foundation`. No commit, push, deployment, or M2 implementation was performed. The initial working tree was clean; existing IDE metadata and scaffold files are preserved.

## 1. Result

A working local React/TypeScript/Vite application calls a FastAPI modular monolith backed by SQLite. A tile-free MapLibre map renders 24 reviewed synthetic road segments inside `lower-manhattan-window-v1`. Pan, zoom, hover, road selection highlighting and study-area reset work. React owns selection; the keyboard list, map and separately fetched road details share it. A searchable road list provides a useful map-failure alternative.

The UI includes workspace navigation, a dashboard summary, map legend, road condition text, source evidence, checksums, visible DEMO DATA/SYNTHETIC labels and persistent unknown-utility warnings. Unknown assessment dates, dimensions and lane information stay unknown. Future features are labeled unavailable/coming soon without action controls. No condition or geometry is presented as a real NYC observation.

## 2. Final structure

```text
apps/api/
  requirements.in, requirements.txt
  app/
    main.py, seed.py
    core/config.py, core/repository.py
    models/database.py
    routes/roads.py
    schemas/roads.py
    services/                         retained reserved package
  tests/test_foundation.py
apps/web/
  package.json, package-lock.json, index.html
  tsconfig.json, vite.config.ts
  src/
    App.tsx, App.test.tsx, main.tsx, styles.css, test-setup.ts
    features/map/RoadMap.tsx, RoadMap.test.tsx
    services/api.ts, api.test.ts
    types/api.ts
    components/, pages/, hooks/        retained scaffold
scripts/create_demo_fixture.py
data/demo/manifest.json, roads.geojson
data/tmp/civicplain.sqlite3            ignored runtime output
docs/                                 updated shared contracts and report
```

## 3. Created and modified files

The exact file inventory is appended below. No tracked IDE file was edited. Existing `.gitkeep` and Python package markers remain intact. Local dependencies, generated SQLite storage, caches and frontend build output are ignored.

## 4. Installed dependencies

- Runtime frontend: React/React DOM **19.3.1**, MapLibre GL JS **6.16.0**.
- Frontend development: TypeScript **7.0.2**, Vite **8.3.6**, React Vite plugin **6.2.1**, Tailwind and its Vite plugin **4.3.5**.
- Frontend tests: Vitest **5.1.0**, jsdom **29.1.1**, Testing Library React **16.3.3**, jest-dom **7.0.1**, user-event **14.6.8**, and React/DOM/GeoJSON types. Exact direct versions and all transitive dependencies are locked.
- Backend direct dependencies: FastAPI **0.162.2**, Uvicorn **0.54.0**, Pydantic **2.14.3**, Shapely **2.2.0**. Test dependencies: pytest **9.2.0**, httpx **0.28.1**. All resolved packages are pinned in requirements.txt; direct ranges are recorded in requirements.in.
- SQLite uses Python's standard library; no ORM, migration tool, spatial database server, optimization package, AI SDK or global dependency was introduced.

## 5. Implemented endpoints

All paths follow the repository contract, not the prompt's illustrative aliases:

| Method/path | Implemented behavior |
| --- | --- |
| GET `/api/v1/health` | Status, API version, SQLite readiness, deterministic-mode label and metadata |
| GET `/api/v1/road-segments` | Validated road list with stable ordering, bbox filter and cursor pagination |
| GET `/api/v1/road-segments/geojson` | GeoJSON FeatureCollection with RecordMeta, condition summary and warnings; application/geo+json |
| GET `/api/v1/road-segments/{id}` | Individual road and synthetic summary, 404 for unknown ID |
| GET `/api/v1/evidence-sources/{id}` | Source evidence, checksum, CRS and limitations, 404 for unknown ID |

FastAPI also exposes generated `/docs`, `/redoc` and `/openapi.json`. Other product endpoints remain proposed. There is no root `/health` or `/api/roads` alias and no mutation or AI endpoint.

## 6. Database, fixture and seeding

`sqlite3` stores one immutable snapshot manifest plus road/evidence JSON payloads in three tables. Pydantic validates records before import and on repository reads. SQL is parameterized, foreign keys are enabled per connection, and seeding is transactional. Startup initializes an empty schema; it does not invent data or implicitly seed it.

The default ignored database is `data/tmp/civicplain.sqlite3`. Explicit `python -m app.seed` verifies the fixture checksum, expected IDs/count, evidence references, valid nonzero LineStrings and study-window intersection before import. Stable IDs and INSERT OR IGNORE make reruns idempotent. A changed manifest cannot overwrite an existing snapshot; a different snapshot needs a separate database in M1. No HTTP mutation path exists.

`demo-m1-v1` contains 24 original schematic geometries, demo names and synthetic condition summaries. Rating thresholds are documented fixture assumptions; each category has six records. All assessment dates/dimensions/lane counts are null with unknown reasons. Utility coverage is unknown. The fixture generator produces byte-identical GeoJSON and manifest checksums across reruns. No municipal data was downloaded or redistributed.

## 7. Installation and startup

Verified host: macOS, Python **3.12.5**, Node **24.5.0**, npm **11.6.0**. Supported prerequisites: Python 3.12, Node 22.12+.

From the repository root:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r apps/api/requirements.txt
npm ci --prefix apps/web
PYTHONPATH=apps/api .venv/bin/python -m app.seed
```

Terminal 1:

```sh
PYTHONPATH=apps/api .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Terminal 2:

```sh
npm run dev --prefix apps/web
```

Open `http://127.0.0.1:5173/`; stop each process with Ctrl+C. No key, external service or environment file is required. Initial package installation needs registry access. Backend env variables are shell exports; frontend overrides use `apps/web/.env.local`. See README for local-only CORS and database configuration.

The production preview was also verified with `npm run preview --prefix apps/web` at port 4173 after adding that explicit loopback origin to API configuration. All test servers were stopped after verification.

## 8. Executed checks and actual results

| Command/check | Final result |
| --- | --- |
| `python3 -m venv .venv` | Created isolated Python environment |
| `.venv/bin/python -m pip install -r apps/api/requirements.in` | Installed backend/test dependencies, then froze resolved versions |
| `.venv/bin/python -m pip install -r apps/api/requirements.txt` | Passed; locked versions satisfied |
| `npm install` with the documented direct packages | Installed exact versions and generated lock; npm reported zero vulnerabilities |
| `npm ci --prefix apps/web` | Passed from package-lock; npm reported zero vulnerabilities |
| `PYTHONPATH=apps/api .venv/bin/python -m app.seed` repeated | Passed, 24 synthetic segments each run, no duplicates |
| `python3 scripts/create_demo_fixture.py` plus SHA-256 comparison | Passed, byte-identical GeoJSON and manifest |
| `PYTHONPATH=apps/api .venv/bin/python -m pytest apps/api/tests -q` | **24 passed**, one dependency deprecation warning |
| `npm test --prefix apps/web` | **15 passed** across three suites |
| `npm run typecheck --prefix apps/web` | Passed |
| `npm run build --prefix apps/web` | Passed, including a typecheck; large-chunk advisory only |
| `git diff --check` | Passed |
| Whitespace checks over modified and untracked source/docs | Passed after removing formatting-only trailing spaces |
| Ignore and tracked IDE checks | Runtime DB, venv, node_modules and dist ignored; IDE diff empty |
| Lint | Not run: no configured lint command |

Backend checks cover health/empty datasets, road/GeoJSON/evidence reads, request IDs, 404/405, bbox/pagination boundaries, schema/provenance errors, invalid geometry, checksum/bounds failures, repeated seeding, foreign keys, restart persistence, immutable manifests, local CORS, blank configuration defaults and sanitized storage 503.

Frontend checks cover loading, loaded metrics, demo disclosures, list and map-triggered selection, API-fetched details/evidence, keyboard selection, unknown/empty/error/retry states, search/count independence, HTTP/malformed/duplicate-response handling, map properties/selection filters, hover, map errors/WebGL loss, cleanup and late disposed-instance errors under StrictMode.

**Actual browser verification** used the running local app, not mocks: development URL at 5173 and production URL at 4173, map roads/colors/legend, pan, zoom/reset, hover label, map click/highlight, R-001 detail (`3 / 10 (demo)`, undated), evidence retrieval, keyboard selection of unknown R-004, 390px mobile layout and 1440px desktop layout. At mobile width, both viewport and document content width were 390px. API logs confirmed collection/detail/evidence requests. Stopping the API produced the error screen without a crash; restarting it and clicking Retry restored all 24 persisted records. The built app also rendered roads and supported map-click details through its locally emitted worker.

During development, the first build exposed MapLibre v6's removed default export; the first browser run exposed its worker URL requirement, and map clicking exposed unreliable reliance on rendered feature IDs. Those issues were corrected and regression-tested. Initial test fixture imports outside Vite's allowlist were replaced by test-only filesystem reads; production still loads roads only through REST. The final suites and build pass.

## 9. Acceptance checklist

| # | Acceptance criterion | Status / evidence |
| --- | --- | --- |
| 1 | React frontend starts locally | **PASS** — Vite 5173 and browser |
| 2 | FastAPI backend starts locally | **PASS** — Uvicorn 8000, real API requests |
| 3 | SQLite persistence works | **PASS** — repository tests and live process restart |
| 4 | Demo data loads reproducibly | **PASS** — checksum/byte reproduction and repeat seed |
| 5 | Interactive map renders | **PASS** — browser, dev and production bundle |
| 6 | Road segments appear | **PASS** — 24 API geometries rendered |
| 7 | Roads are fetched from FastAPI | **PASS** — actual collection/detail/evidence requests |
| 8 | Clicking a road highlights it | **PASS** — R-001 map click and visual highlight |
| 9 | Clicking a road displays correct metadata | **PASS** — API-backed R-001 poor/3, unknown dates and dimensions |
| 10 | Condition colors and legend are correct | **PASS** — green/good, amber/fair, red/poor, gray/unknown plus text |
| 11 | Metrics derive from loaded records | **PASS** — total 24, six per category, tests and browser |
| 12 | Synthetic data is visibly identified | **PASS** — screen, detail, record and source labels |
| 13 | Frontend handles backend failure | **PASS** — actual outage and retry recovery plus tests |
| 14 | Backend tests pass | **PASS** — 24 tests |
| 15 | Frontend typecheck/build pass | **PASS** — final commands; 15 interaction/client/map tests also pass |
| 16 | Local setup documented | **PASS** — verified commands in README and this report |

No M1 acceptance criterion remains incomplete on the verified host. Cross-platform behavior and full accessibility certification are not claimed.

## 10. Known limitations

- Geometry and conditions are entirely synthetic. There is no real street, pavement, utility or schedule coverage. Unknown utility information never establishes safety.
- One read-only snapshot per SQLite file. No general ingestion, edit UI, normalized assessment history or migration system is implemented.
- MapLibre requires WebGL and its local worker; the keyboard road list is the fallback. No online tile provider is configured, so remote-tile availability is not a demo dependency. Resource-error/WebGL paths are tested; a third-party tile outage test is inapplicable to this source-free style.
- Vite reports a large JS chunk: approximately 1.30 MB raw / 362 KB gzip plus a 519 KB raw worker. This is a successful build with a non-blocking advisory; no performance target or production-readiness claim is made.
- Installed Starlette warns that its httpx test-client adapter is deprecated. The API and all 24 tests pass; future test-dependency updates should resolve the warning deliberately.
- Browser checks cover the available local browser, keyboard selection and responsive widths, not cross-browser coverage or a full accessibility audit. Tests mock map rendering; actual map behavior was checked separately in the browser.
- The unauthenticated app is local-only. No deployment, production security, municipal authorization, AI, estimates, conflict detection, forecasting or optimization is present.

## 11. Architecture decisions and discrepancies

The REST modular monolith and existing directories are preserved. The prompt's `/api/roads` and `/health` examples are replaced by the authoritative documented `/api/v1/road-segments` and `/api/v1/health` paths.

The original roadmap placed SQLite in M2, but this explicit M1 request requires working persistence and reproducible seeding. Only the minimal road/evidence store and synthetic condition read projection move forward; docs were updated together. Standard-library sqlite3 avoids an unnecessary ORM. Shapely is used only for validation and exact bbox intersections; there is no conflict calculation. Full ConditionAssessment normalization and latest-date/stable-ID selection remain M2. The default map is the already documented no-tiles fallback, with no new provider/license dependency. MapLibre's locally emitted ESM worker follows its official v6 migration guidance linked from README.

## 12. Next milestone

M2 should extend the current repositories and shared contracts for normalized assets, condition assessments, projects and repair options; derive the summary from dated assessments using the specified stable-ID tie-break; and implement reproducible decimal cost/duration estimates with units, assumptions, bounds, saved inputs and missing-data errors. Add domain and persistence/UI boundary tests before marking those routes implemented. M2 has not begun; conflicts, scenarios and AI remain later milestones.

## Exact file inventory

Modified:

- `.env.example`
- `README.md`
- `docs/AI_SYSTEM.md`
- `docs/API_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/DATA_MODEL.md`
- `docs/DATA_SOURCES.md`
- `docs/DEMO_PLAN.md`
- `docs/MVP_ROADMAP.md`
- `docs/PRODUCT_SPEC.md`

Created:

- `apps/api/app/core/config.py`
- `apps/api/app/core/repository.py`
- `apps/api/app/main.py`
- `apps/api/app/models/database.py`
- `apps/api/app/routes/roads.py`
- `apps/api/app/schemas/roads.py`
- `apps/api/app/seed.py`
- `apps/api/requirements.in`
- `apps/api/requirements.txt`
- `apps/api/tests/test_foundation.py`
- `apps/web/index.html`
- `apps/web/package-lock.json`
- `apps/web/package.json`
- `apps/web/src/App.test.tsx`
- `apps/web/src/App.tsx`
- `apps/web/src/features/map/RoadMap.test.tsx`
- `apps/web/src/features/map/RoadMap.tsx`
- `apps/web/src/main.tsx`
- `apps/web/src/services/api.test.ts`
- `apps/web/src/services/api.ts`
- `apps/web/src/styles.css`
- `apps/web/src/test-setup.ts`
- `apps/web/src/types/api.ts`
- `apps/web/tsconfig.json`
- `apps/web/vite.config.ts`
- `data/demo/manifest.json`
- `data/demo/roads.geojson`
- `docs/M1_IMPLEMENTATION.md`
- `scripts/create_demo_fixture.py`
