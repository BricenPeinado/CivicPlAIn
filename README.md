# CivicPlAIn

BUHACKS 2026 — local municipal infrastructure decision-support prototype.

Milestones 1, 2 and 3 are implemented: React/TypeScript/Vite, Tailwind CSS, a selectable MapLibre map, FastAPI, and SQLite-backed synthetic roads. The map, road list, detail panel, provenance, and summary counts all use the same API dataset. M2 adds read-only assessment history, three repair alternatives, deterministic Decimal cost/duration calculations, immutable saved estimates, and comparison/detail panels. M3 adds persisted fictional work projects, projected spatial/temporal screening, immutable conflict snapshots and map/review panels. Forecasting, optimization, scenarios and AI remain unimplemented. See [M3 implementation and verification](docs/M3_IMPLEMENTATION.md). See [M2 implementation and verification](docs/M2_IMPLEMENTATION.md) and the historical [M1 report](docs/M1_IMPLEMENTATION.md).

**DEMO DATA:** the 24 road segments are an authored schematic inside the chosen Lower Manhattan study window, not actual streets or municipal condition observations. There are six good, six fair, six poor, and six unknown demo conditions. M2 explicitly adds synthetic planning dimensions and dated synthetic assessments to four roads, plus an incomplete fifth asset. These dimensions are authored rectangular scopes, not measurements from geometry. Other dimensions, lane counts and utility information remain unknown. This application cannot establish excavation safety or authorize work.

## Prerequisites and installation

Use Python **3.12** and Node.js **22.12+** (verified with Python 3.12.5, Node 24.5.0, npm 11.6.0 on macOS). A browser with WebGL is needed for the map; the keyboard road list remains usable without it. Initial dependency installation needs registry access; subsequent demo operation needs only the local API.

Run these commands from the repository root:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r apps/api/requirements.txt
npm ci --prefix apps/web
PYTHONPATH=apps/api .venv/bin/python -m app.seed
```

Python's complete resolved dependency set is pinned in `apps/api/requirements.txt`; direct dependency ranges are recorded in `requirements.in`. JavaScript dependencies use exact versions and `package-lock.json`. No global installs, external database, map-provider key, or OpenAI key are required.

## Start and stop

Start the API in terminal 1, from the repository root:

```sh
PYTHONPATH=apps/api .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Start the frontend in terminal 2, also from the root:

```sh
npm run dev --prefix apps/web
```

Open **http://127.0.0.1:5173/**. API health is **http://127.0.0.1:8000/api/v1/health**; interactive API documentation is at **http://127.0.0.1:8000/docs**. Stop each process with **Ctrl+C**. Bind both servers only to loopback; this unauthenticated prototype must not be publicly exposed.

The database defaults to ignored `data/tmp/civicplain.sqlite3` and survives restarts. Startup initializes tables but does not seed implicitly. Repeat the seed command safely: stable IDs, checksum checks, a transaction, and immutable manifest metadata prevent duplicate imports. To demonstrate a genuinely empty dataset, start the API with a new local database path and do not seed it.

## Configuration

No environment file is required. `.env.example` documents supported variable names without credentials. Backend variables must be exported in the launching shell; the backend does not load `.env` automatically.

| Variable | Default / purpose |
| --- | --- |
| `CIVICPLAIN_DATABASE_PATH` | Absolute repository `data/tmp/civicplain.sqlite3`; override with another local SQLite file path |
| `CIVICPLAIN_ALLOWED_ORIGINS` | Comma-separated `http://127.0.0.1:5173,http://localhost:5173`; explicit local HTTP origins with ports only |
| `VITE_API_BASE_URL` | `http://127.0.0.1:8000/api/v1`; frontend public configuration, never a secret |

For a frontend override, create ignored `apps/web/.env.local` containing `VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1`, then restart Vite. Blank backend values use the documented defaults. Never place credentials in `VITE_*` variables.

## Implemented API

The documented `/api/v1` boundary is preserved; `/api/roads` and root `/health` aliases are not implemented.

| Method/path | Response |
| --- | --- |
| GET `/api/v1/health` | Status, API version, data-ready flag, deterministic mode in envelope |
| GET `/api/v1/road-segments` | Validated roads, stable ID order, bbox filtering and cursor pagination |
| GET `/api/v1/road-segments/geojson` | `application/geo+json` FeatureCollection with provenance and metadata |
| GET `/api/v1/road-segments/{id}` | Road metadata/geometry and synthetic condition summary; unknown ID → 404 |
| GET `/api/v1/evidence-sources/{id}` | Fixture provenance, checksum, CRS, limitations; unknown ID → 404 |
| GET `/api/v1/road-segments/{id}/conditions` | Complete bounded assessment history, latest usable ID in meta |
| GET `/api/v1/repair-options` | Three synthetic treatment/rate/productivity definitions |
| GET `/api/v1/road-segments/{id}/repair-options` | Three suitability results and nonpersisted previews; unavailable reasons for missing dimensions |
| POST `/api/v1/estimates` | 201 immutable estimate; explicit planning dimensions optional |
| GET `/api/v1/estimates/{id}` | Saved output and complete reproducible input/source snapshot |

See [API contract](docs/API_SPEC.md). Roads support `limit=1..100` (default 30), `bbox=west,south,east,north`, and opaque `cursor`. The web client enforces the study's hard cap of 30 records. A valid no-match filter returns an empty collection. Invalid inputs return a sanitized 422 error; unavailable storage returns 503.

## Checks

From the repository root:

```sh
PYTHONPATH=apps/api .venv/bin/python -m pytest apps/api/tests -q
npm test --prefix apps/web
npm run typecheck --prefix apps/web
npm run build --prefix apps/web
git diff --check
```

No lint command is configured. The frontend build emits Vite's large-chunk advisory for MapLibre; the build succeeds. Starlette currently emits a deprecation warning for its httpx-based test client; tests pass. These limits are recorded in the M1 report.

To preview the production build, allow `http://127.0.0.1:4173` in the API's local origins, restart the API, then run `npm run preview --prefix apps/web`. The ordinary dev commands use port 5173.

## Map and fixture strategy

The default MapLibre style is an authored, local background plus API GeoJSON. It has **no remote tiles, fonts, sprites, or hosted GIS dependencies**. The MapLibre ESM worker is emitted as a local Vite asset using `setWorkerUrl`; see the [official v6 migration guide](https://maplibre.org/maplibre-gl-js/docs/guides/v5-to-v6-migration-guide/). Attribution identifies CivicPlAIn synthetic geometry and the absence of municipal observations. MapLibre's BSD license notice is preserved by the build. No third-party geographic dataset is redistributed.

Pan, zoom, hover, selection highlights, study-area reset, and resize are supported. An equivalent searchable keyboard list supports selection when WebGL or map resources fail. The frontend shows loading, empty, timeout, API failure/retry, and detail failure states. Green/good, amber/fair, red/poor, gray/unknown have corresponding text labels.

Reviewed fixtures live in `data/demo/roads.geojson` and `manifest.json`. Reproduce them with `python3 scripts/create_demo_fixture.py`; this writes the same bytes and checksum, not newly sampled observations. The manifest records IDs, exact bounds, synthetic category rules, per-field assumptions, expected counts, and provenance. Generated databases, downloads, node modules, and build outputs remain ignored.

## Repository structure

```text
apps/api/
  requirements.in, requirements.txt
  app/
    main.py, seed.py
    core/          configuration and road repository
    models/        SQLite schema/connection management
    routes/        roads, planning, projects and conflicts REST routes
    schemas/       Pydantic geometry, roads, planning, evidence and envelopes
    services/      pure deterministic estimate and conflict engines
  tests/           backend contract and persistence tests
apps/web/
  package.json, package-lock.json, vite.config.ts, tsconfig.json, index.html
  src/
    App.tsx, main.tsx, styles.css
    features/      MapLibre map and repair comparison/detail components with tests
    services/      typed API client and request tests
    types/         shared frontend transport types and dataset counts
    *.test.tsx     workspace interaction tests
    test-setup.ts  browser-test setup
    components/, pages/, hooks/  retained scaffold directories
scripts/create_demo_fixture.py
data/demo/         reviewed synthetic geometry and manifest
data/tmp/          ignored local runtime database
docs/              contracts, roadmap, design and verification evidence
```

## Architecture and next milestone

One React client calls one FastAPI modular monolith through REST. Standard-library `sqlite3` provides short-lived connections, parameterized SQL, foreign keys and transactional imports. Pydantic validates stored/read records and API responses; Shapely validates geometry and bbox intersections. No ORM or migration framework is needed; versioned additive SQLite DDL extends the three M1 tables without rewriting their payloads.

M2 extends the existing repository with related maintenance attributes, normalized assessment history, a repair catalog and append-only estimates. M3 extends the same application with projects, conflict analysis and evidence review. AI, scenarios, deployment and production authentication remain later work.

## Documentation

- [Development rules](AGENTS.md)
- [Product specification](docs/PRODUCT_SPEC.md)
- [MVP roadmap](docs/MVP_ROADMAP.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Data model](docs/DATA_MODEL.md)
- [API contract](docs/API_SPEC.md)
- [AI system](docs/AI_SYSTEM.md)
- [Responsible AI](docs/RESPONSIBLE_AI.md)
- [Data sources and study area](docs/DATA_SOURCES.md)
- [Demo plan](docs/DEMO_PLAN.md)
- [Historical foundation inspection](docs/FOUNDATION_INSPECTION.md)
- [M1 implementation and verification](docs/M1_IMPLEMENTATION.md)
- [M2 implementation and verification](docs/M2_IMPLEMENTATION.md)

## M2 planning workflow and formulas

Re-run the documented seed command against an existing M1 database to **add** M2 records. Startup only initializes the schema. Seeding verifies both manifests, inserts missing stable IDs, and preserves existing records. Never delete/reset an existing database to upgrade it. The command reports 24 roads and M2 counts `(5, 26, 3)`.

Select R-001 (poor), R-002 (good), R-003 (fair), R-004 (unknown), or R-005 (large scope), then **Compare Repair Options**. Inspect history, suitability, scope and sensitivity previews; optionally enter a positive length/width in meters with a planning assumption note. **Save & inspect** creates an estimate and retrieves the saved result. Previews use stored dimensions; entered overrides apply to the saved result. There is no assessment editing, arbitrary unit-rate override or area-only override.

`area_m2 = length_m × width_m`. For each low/base/high scenario, round `area × bundled_rate` and each mobilization/traffic allowance to cents; sum those lines; round `subtotal × contingency_fraction` to cents; add subtotal and contingency. Bundled roadwork already includes materials/labor/equipment. Use USD, Decimal, ROUND_HALF_UP. Low/high bundled rates are explicitly −20%/+30% from base; allowances, quantity, contingency rate and productivity stay fixed. These are sensitivity assumptions, not probabilities or official NYC prices.

`active_workdays = ceil(area / productivity_m2_per_active_workday)`; `total_preliminary_days = active_workdays + setup_days + curing_days`. No calendar completion date, weather/weekend model or contractor schedule is supplied. Missing dimensions block estimates unless explicitly supplied as planning assumptions. Every alternative requires engineering review; no price establishes feasibility or excavation safety.

Rates, exclusions, productivity, source IDs and fixtures are in `data/demo/maintenance.json`, checked by `maintenance-manifest.json`; reproduce them with `python3 scripts/create_m2_fixture.py`. Estimates preserve complete input and evidence snapshots, hashes and `repair-estimate-v1`, with integer-cent totals and immutable JSON. See [M2 contracts](docs/DATA_MODEL.md) and [API request examples](docs/API_SPEC.md).

## M3 project coordination workflow

Install the updated pinned requirements (`.venv/bin/python -m pip install -r apps/api/requirements.txt`) and rerun the existing seed command to add seven **fictional** projects while preserving roads, estimates and local project edits. It now reports `M3 projects 7`. Restart the API to load M3; startup alone never imports fixtures. No key, LLM, external tiles, spatial database or remote projection service is used.

The map loads all seven project records and automatically checks that bounded set. Select **Project coordination** in the sidebar, then a project or road to filter the review panel. Select **Potential pavement rework** to highlight both supplied work zones and related roads; inspect the two-day gap, sources, assumptions and required human review. The master checkbox and category checkboxes control map visibility only. Unknown-location records remain selectable in the list. Every finding has text, a selection mark and a thick outline; color is supplemented by category labels. See [demo steps](docs/DEMO_PLAN.md).

The default fictional dataset yields **8 findings and 10 incomplete pair checks**, from 16 indexed candidate pairs out of 21 possible pairs. A finding is a coordination signal, never a final engineering determination, clearance, validated safety priority, proven damage or financial loss. Utility coverage stays unknown even with zero findings. No redundant cost or savings value is calculated.

| Method/path | M3 behavior |
| --- | --- |
| GET `/api/v1/projects` | Stable-ID project list; road/kind/status filters and cursor pagination |
| GET `/api/v1/projects/{id}` | Full project, schedule/location uncertainty and provenance |
| POST `/api/v1/conflicts/analyze` | Validated selected scope, deterministic analysis, saved immutable source snapshot |
| GET `/api/v1/conflicts` | Saved findings; project/road/analysis filters and pagination |
| GET `/api/v1/conflicts/{id}` | Saved finding and analysis reference |
| GET `/api/v1/conflict-analyses/{id}` | Saved inputs, sources, parameters, findings, unknown checks and hashes |

Analysis uses valid GeoJSON in EPSG:4326, longitude/latitude, transformed by pinned pyproj to EPSG:32618 meters. STRtree narrows distance/corridor candidates; shared road references and unknown footprints are handled explicitly. Defaults: 5 m footprint proximity, 5 m centerline corridor tolerance, and a 30-calendar-day sequencing review window. These are screening assumptions, not positional accuracy. Civil-date intervals are half-open `[start, end)` in America/New_York; adjacent intervals do not overlap. Invalid topology and reversed intervals are rejected without geometry repair. Work zones must lie inside the bounded study window. See [method and limitations](docs/ARCHITECTURE.md).

Fixtures: `data/demo/projects.json` and `projects-manifest.json`; reproduce with `python3 scripts/create_m3_fixture.py`. Additive schema version 3 stores projects, project-road links, analyses and findings; estimate immutability and original road payloads are retained. Identical input snapshots reuse the original analysis/findings and detection timestamp. Changed source contents or parameters produce a distinct snapshot. General project editing/import, observed municipal adapters and full review audit-event workflows remain future work. M4 is the next milestone and has not started.
