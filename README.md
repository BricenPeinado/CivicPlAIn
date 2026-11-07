# CivicPlAIn

BUHACKS 2026 — local municipal infrastructure decision-support prototype.

Milestones **0–6 are complete locally** for the bounded hackathon demonstrator. One React/TypeScript/Vite client calls one FastAPI modular monolith with SQLite. Select a road on the local MapLibre schematic, inspect synthetic condition/provenance, compare deterministic repair estimates, review spatial/date conflicts, compare saved hypothetical scenarios and inspect evidence-grounded explanations with useful offline fallback. M6 adds an API-backed **Explore Demo** guide, focused accessibility/readability fixes, lazy map/scenario loading, local request safeguards and an isolated startup helper. See [final QA and the 24-item acceptance checklist](docs/FINAL_QA_REPORT.md), [demo script](docs/HACKATHON_DEMO.md), [limitations](docs/KNOWN_LIMITATIONS.md) and [presentation outline](docs/PRESENTATION_OUTLINE.md).

No production municipal use, verified cost savings, excavation clearance, automatic approval, live data ingestion or forecasting is claimed. Historical milestone reports record their original scope; the M6 report and current shared contracts describe this release.

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

Python's complete resolved dependency set is pinned in `apps/api/requirements.txt`; direct dependency ranges are recorded in `requirements.in`. JavaScript dependencies use exact versions and `package-lock.json`, including project-local `@types/node` 22.20.5 with explicit Node typing for the test/configuration imports. No parent-directory type installation is required. No global installs, external database, map-provider key, or OpenAI key are required.

## Quick isolated demo

After installing dependencies above, run:

```sh
.venv/bin/python scripts/demo.py
```

Open **http://127.0.0.1:5173/** → **Explore Demo**. Every run creates a fresh ignored `data/tmp/m6-demo-*/demo.sqlite3`, seeds deterministically and forces no-key deterministic AI. The ordinary database and every earlier demo remain intact. Ctrl+C stops only the helper's child servers; files are retained. This is the safe reset procedure: initialize a new isolated environment, with no deletion/reset of existing records.

Occupied ports: `.venv/bin/python scripts/demo.py --api-port 8016 --web-port 5186`. Production assets: add `--production` (builds first). The helper waits for API health, refuses occupied ports, and never installs dependencies. It supports the verified POSIX/macOS environment. See [exact demo interactions and recovery](docs/HACKATHON_DEMO.md).

## Start and stop with the ordinary persistent database

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

No lint command is configured. M6 verification: **212 backend / 57 frontend tests pass**, typecheck and production build pass, including clean dependency installations. MapLibre is lazy-loaded separately from the ~273 kB application shell; its ~1,069 kB module and ~519 kB local worker retain Vite's large-chunk advisory. Starlette's httpx test-client deprecation remains nonblocking. Browser dev/production checks and scoped npm audit results are recorded in FINAL_QA_REPORT; no lint command is configured.

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

## Architecture and release boundary

One React client calls one FastAPI modular monolith through REST. Standard-library `sqlite3` provides short-lived connections, parameterized SQL, foreign keys and transactional imports. Pydantic validates stored/read records and API responses; Shapely validates geometry and bbox intersections. No ORM or migration framework is needed; versioned additive SQLite DDL extends the three M1 tables without rewriting their payloads.

M2 extends the existing repository with related maintenance attributes, normalized assessment history, a repair catalog and append-only estimates. M3 extends the same application with projects, conflict analysis and evidence review. M5 AI explanations are implemented below; deployment and production authentication remain later work. M4 scenario services reuse M2 costing and the unchanged M3 engine.

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
- [Current hackathon demo and recovery](docs/HACKATHON_DEMO.md)
- [Final QA report](docs/FINAL_QA_REPORT.md)
- [Known limitations](docs/KNOWN_LIMITATIONS.md)
- [Presentation outline](docs/PRESENTATION_OUTLINE.md)
- [Demo plan index](docs/DEMO_PLAN.md)
- [M3.5 compatibility verification](docs/M3_5_COMPATIBILITY.md)
- [Historical foundation inspection](docs/FOUNDATION_INSPECTION.md)
- [M1 implementation and verification](docs/M1_IMPLEMENTATION.md)
- [M2 implementation and verification](docs/M2_IMPLEMENTATION.md)

## M2 planning workflow and formulas

Re-run the documented seed command against an existing M1 database to **add** M2 records. Startup only initializes the schema. Seeding verifies both manifests, inserts missing stable IDs, and preserves existing records. Never delete/reset an existing database to upgrade it. The command reports 24 roads, M2 counts `(5, 26, 3)`, seven M3 projects and three M4 scenarios.

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

Fixtures: `data/demo/projects.json` and `projects-manifest.json`; reproduce with `python3 scripts/create_m3_fixture.py`. Additive schema version 3 stores projects, project-road links, analyses and findings; estimate immutability and original road payloads are retained. Identical input snapshots reuse the original analysis/findings and detection timestamp. Changed source contents or parameters produce a distinct snapshot. General project editing/import, observed municipal adapters and a general cross-module audit stream remain future work. M4 and M5 additions are documented below.

## Historical M3.5 compatibility and M4 preparation

The existing three-method M2 catalog remains authoritative: R-001 resurfacing is low/base/high $44,760/$53,400/$66,360 and five preliminary days. Patch/restoration methods and lifespans are unavailable; the former demo's alternative prices are retired. No rates, fixture payloads, database records or calculation versions were changed.

DATA_MODEL now defines proposed `scenario-action-v1` scope/quantity/provenance, supplied calendar assumptions, closure intervals and explicit mobilization groups. ARCHITECTURE defines a future hypothetical adapter that reuses the M3 engine with immutable proposal snapshots and explicit project overrides, without saving proposals as work projects. API_SPEC marks all scenario transport as proposed. These are documentation contracts; there are no new runtime scenario schemas, routes, migrations, evaluation services or screens. These statements describe the M3.5 baseline; the implemented M4 and M5 additions follow below. See M3_5_COMPATIBILITY for the historical isolated-install regression evidence and source requirements.

## M4 scenario workflow

Rerun `PYTHONPATH=apps/api .venv/bin/python -m app.seed` to add three **synthetic hypothetical** scenarios and immutable initial evaluations without overwriting existing drafts, projects, estimates or conflict analyses. Restart the API after updating source. Open **Scenario planner** in the existing sidebar. The map and keyboard road list remain the selection surface; select a road, then use **Add selected map road** in a new plan.

Create or edit name, description, objective, nonnegative USD budget, common planning horizon, repair methods, whole-segment/explicit partial scope, authored assumptions, optional dates and closure declarations. Select external projects explicitly; optionally exclude or replace a snapshot with a reason. Related-project links alone never replace a project. Save a draft or save and evaluate; inspect older frozen evaluation history. Compare two or three saved evaluations from the scenario list. Unsaved form changes never alter an old evaluation.

The three reviewed demos model roadwork before utility work, after utility work and an explicitly coordinated overlapping window. Each prices the same 800 m² resurfacing action at low/base/high **$44,760 / $53,400 / $66,360** using the original catalog. A $60,000 synthetic roadwork budget leaves $6,600 base headroom and a $6,360 high-case shortfall. M3 returns respectively a potential rework finding, a sequencing review, and concurrent work plus multiple closures. Coordination is an assumption requiring review, not a discount or clearance. No restoration charge is inferred from a conflict.

Unknown quantities/methods yield null complete totals and indeterminate budget feasibility; separately known components remain visible. Patch/trench-restoration methods and shared-mobilization adjustments are unsupported (the latter rejected explicitly). Calendar dates are supplied independently of preliminary workdays. Lifespan, actual traffic delay, economic disruption and utility coverage remain unknown. The M4 calculation path has no AI or optimizer dependency and does not approve projects or mutate source schedules. M5 adds explanations below.

M4 API uses `/api/v1/scenarios`, `/scenarios/{id}/actions`, `/scenarios/{id}/evaluate`, `/scenarios/{id}/evaluations`, `/scenario-evaluations/{id}` and `/scenario-comparisons`. Writes require optimistic revisions; see [API contract](docs/API_SPEC.md). The complete file inventory, checks, acceptance matrix and M5 handoff are in [M4 report](docs/M4_IMPLEMENTATION.md).

## M5 evidence advisor and optional OpenAI configuration

Install the updated pinned backend requirements, then restart the API. Startup adds M5 audit tables without rewriting existing source/estimate/conflict/evaluation records. The application defaults to deterministic explanations with no key. On saved estimates, selected conflicts and scenario comparisons, use **Explain this estimate**, **Explain this conflict** and **Explain tradeoffs**. Road, project and evaluation contexts also have advisors. Ask bounded questions, inspect source references/unknowns, and open **How AI works**. Actual future deterioration, excavation safety, approvals and spending are outside the assistant's scope. Human notes are stored separately and authorize no work.

| Server variable | Default / behavior |
| --- | --- |
| `CIVICPLAIN_AI_PROVIDER` | `deterministic`; opt in with `openai` |
| `OPENAI_API_KEY` | Absent; optional server-side secret, never `VITE_*` |
| `OPENAI_MODEL` | `gpt-5.4-mini-2026-03-17`, verified against official documentation; configurable |
| `CIVICPLAIN_AI_MAX_CALLS_PER_HOUR` | 20 per process, range 0–100; failed attempts count |

The backend reads exported shell variables, not `.env` automatically. No credential setup or live paid call is required for testing. Optional OpenAI uses the official Python SDK, Pydantic Structured Outputs, an 8-second deadline, zero retries, 1,200 output tokens and two concurrent calls. A project-level provider budget is needed for a financial ceiling; local counters reset on restart. Requests default to deterministic; checking the optional AI box requests configured model emphasis and falls back explicitly when unavailable. The model selects supported facts; the server renders and validates values/references. Unsupported prose is never returned as a verified recommendation.

Implemented routes are POST `/api/v1/ai/explain-estimate`, `/ai/explain-conflict`, `/ai/explain-scenario-comparison`, `/ai/ask`, GET `/api/v1/ai/status`, `/ai/interactions/{id}`, and POST `/api/v1/scenario-evaluations/{id}/reviews`. See [API_SPEC](docs/API_SPEC.md) for strict bodies and errors. Evidence projections and minimal audit metadata are append-only; no raw questions, prompts, provider prose, credentials or utility geometry are stored in AI interactions. Human review notes stay local and separate; avoid sensitive text. Keep this unauthenticated prototype on loopback.

Run the offline demonstration without modifying existing databases:

```sh
PYTHONPATH=apps/api .venv/bin/python scripts/verify_m5.py
```

See [AI_SYSTEM](docs/AI_SYSTEM.md), [RESPONSIBLE_AI](docs/RESPONSIBLE_AI.md), historical [M5 verification](docs/M5_IMPLEMENTATION.md), the current [demo walkthrough](docs/HACKATHON_DEMO.md) and [final M6 verification](docs/FINAL_QA_REPORT.md).
