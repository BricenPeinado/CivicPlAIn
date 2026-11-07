# CivicPlAIn

BUHACKS 2026 — local municipal infrastructure decision-support prototype.

Milestone 1 is implemented: React/TypeScript/Vite, Tailwind CSS, a selectable MapLibre map, FastAPI, and SQLite-backed synthetic roads. The map, road list, detail panel, provenance, and summary counts all use the same API dataset. There are no estimates, conflicts, forecasting, optimization, scenarios, or AI calls yet. See [M1 implementation and verification](docs/M1_IMPLEMENTATION.md).

**DEMO DATA:** the 24 road segments are an authored schematic inside the chosen Lower Manhattan study window, not actual streets or municipal condition observations. There are six good, six fair, six poor, and six unknown demo conditions. Assessment dates, dimensions, lane counts, and utility information are unknown. This application cannot establish excavation safety or authorize work.

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

## Implemented read-only API

The documented `/api/v1` boundary is preserved; `/api/roads` and root `/health` aliases are not implemented.

| GET path | Response |
| --- | --- |
| `/api/v1/health` | Status, API version, data-ready flag, deterministic mode in envelope |
| `/api/v1/road-segments` | Validated roads, stable ID order, bbox filtering and cursor pagination |
| `/api/v1/road-segments/geojson` | `application/geo+json` FeatureCollection with provenance and metadata |
| `/api/v1/road-segments/{id}` | Road metadata/geometry and synthetic condition summary; unknown ID → 404 |
| `/api/v1/evidence-sources/{id}` | Fixture provenance, checksum, CRS, limitations; unknown ID → 404 |

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
    routes/        read-only REST routes
    schemas/       Pydantic geometry, roads, evidence and envelopes
    services/      reserved domain-services package (no calculations yet)
  tests/           backend contract and persistence tests
apps/web/
  package.json, package-lock.json, vite.config.ts, tsconfig.json, index.html
  src/
    App.tsx, main.tsx, styles.css
    features/map/  MapLibre component and regression tests
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

One React client calls one FastAPI modular monolith through REST. Standard-library `sqlite3` provides short-lived connections, parameterized SQL, foreign keys and transactional imports. Pydantic validates stored/read records and API responses; Shapely validates geometry and bbox intersections. No ORM or migration framework is needed for three M1 tables.

The requested persisted end-to-end M1 expands the original roadmap's file-backed M1: only road/evidence persistence and a read-only synthetic condition summary move forward from M2. Full normalized assessments, assets/projects, reproducible repair estimates and their UI remain **M2**, which has not begun. AI, conflicts, scenarios, deployment and production authentication remain later work.

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
