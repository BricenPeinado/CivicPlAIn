# Architecture

Status: M2 implements the existing React/FastAPI modular monolith, selectable map, related maintenance attributes, normalized assessment history, pure estimate calculations and immutable SQLite estimate snapshots. Projects, conflicts, scenarios and AI below remain planned.

## Boundaries and data flow

React/Vite is a separate presentation client of one FastAPI process. Python domain services own all calculations; the browser formats results and gathers scenario inputs. Pydantic validates API contracts; SQLite stores normalized records and immutable evaluation snapshots. No microservices, Kubernetes, spatial database server, or background queue is needed for the demo.

```mermaid
flowchart LR
  W[React map and planner panels] --> R[FastAPI routes and schemas]
  R --> A[Asset and project services]
  R --> E[Estimate service]
  R --> C[Conflict service]
  R --> S[Scenario evaluation service]
  S --> E
  S --> C
  A --> DB[(SQLite repositories)]
  S --> DB
  I[Replaceable data adapters] --> V[Validation and provenance]
  V --> DB
  R --> X[Explanation service]
  X --> F[Validated evaluation facts]
  F --> DB
  X --> T[Deterministic templates]
  X -. optional .-> L[Backend LLM adapter]
  L --> G[Claim validation gate]
  T --> O[Explanation response]
  G --> O
```

`routes/` handles HTTP; `schemas/` request/response validation; `models/` persistence records; `services/` domain functions and orchestration; `core/` configuration, errors, repositories, adapter interfaces, and audit helpers. Submodules are introduced with their milestone, not as unused source placeholders. Routes never perform spatial math or embed prompts; domain functions never call an LLM or HTTP service.

Planned web features group map, assets, estimates, conflicts, scenarios, and explanations. `services/` holds the typed API client; `types/` mirrors validated transport shapes; no calculation is duplicated in components.

## Calculation services

M2 uses Decimal: `bundled_roadwork = area_m2 × scenario_rate`; `subtotal = rounded_roadwork + rounded_mobilization + rounded_traffic_allowance`; `contingency = round(subtotal × contingency_fraction)`; `total = subtotal + contingency`. Materials/labor/equipment are included once in the bundled rate. Quantities, rate units, rates, exclusions, bounds, and method versions are evidence inputs. Round each line to cents with ROUND_HALF_UP, then subtotal; round contingency to cents and add. Persist integer cents; serialize money as two-decimal USD strings. Costs are estimates, not bids.

M2 duration is `ceil(area_m2 / productivity_m2_per_active_workday) + setup_days + curing_days`. It separates active workdays, setup and curing allowances; these sequential preliminary days are not a contractor calendar or elapsed scheduled dates. No inferred crew/weather model. Lifespan is an option assumption with bounds, not a prediction of actual pavement performance. Bounds are sensitivity ranges, not statistical confidence intervals unless a justified model is later added. Missing dimensions/rates block the affected estimate; do not substitute zero.

## Geographic and temporal rules

- Exchange GeoJSON in EPSG:4326, longitude then latitude. Require valid finite coordinates and supported geometry types; preserve original geometry and source CRS metadata. Reject rather than silently repair malformed features.
- Transform to EPSG:32618 (metres, NYC study window) for length, distance, and buffer operations. GeoPandas may handle bulk ingestion; Shapely handles domain geometry. Record CRS and library/method versions. Never buffer decimal degrees or treat a centerline as measured pavement area.
- MVP spatial candidate rule: projected distance between project footprints is at most `proximity_m`. A default **synthetic assumption** of 5 m is proposed; validate against the chosen source in M3. It is a screening tolerance, not utility positional accuracy. Use direct distance or buffer one geometry once, avoiding accidental doubled tolerance. Intersection at the boundary counts as proximity.
- Dates are local civil dates in America/New_York with half-open intervals `[start_date, end_date)`. Temporal overlap: `max(starts) < min(ends)`. Adjacent intervals do not overlap. Calendar-day durations are date differences; audit timestamps use UTC.
- Emit `concurrent_work` when proximity and interval overlap hold. Emit `reopening_risk` when utility work is nearby and starts from 0 through `reopening_horizon_days` after road repair ends (inclusive threshold; proposed demo horizon 30). Reopening is a potential restoration risk, not a predicted event.
- Missing dates or geometry produce `indeterminate` checks with missing-field evidence, not negative findings. Existing known findings remain visible even if some other projects cannot be checked. Coverage status is independent of finding count.
- No observed utility location/depth is inferred from a permit or a line intersection. Grade-separated crossings and permits without confirmed schedules require human interpretation. Deduplicate findings by ordered project pair, rule type, and method version.

At ≤50 projects, deterministic pairwise comparisons are sufficient. Add spatial indexing only when measurements justify it. NetworkX is reserved for stretch detours; OR-Tools is deferred unless a documented scheduling/selection formulation exceeds simple enumeration.

## Scenario evaluation

A scenario is a manually specified list of repair actions, proposed dates, and optional explicit repeat-restoration actions. A conflict does not automatically create a monetary loss. Reopening cost appears only if a scenario includes a separately justified restoration action. Evaluate the same immutable source snapshot, price basis, cost scope, and planning horizon across alternatives.

Sum action central/lower/upper estimates without double counting shared mobilization; sharing must be an explicit line-item assumption. Report `within_budget` when central total ≤ budget, `over_budget` otherwise, and `indeterminate` if required estimates are incomplete. A separate `upper_bound_within_budget` can be true/false/null. Neither affordability field implies safety or approval. Enumerate alternatives without automatic scheduling or a hidden weighted score.

Report elapsed days as latest end minus earliest start; report disruption proxy as sum of `lanes_closed * action_calendar_days` per action, including repeats. This proxy is not vehicle delay and can double count simultaneous closures; label that limitation. Condition/safety observations, lifespan ranges, scheduling gaps, and risk flags remain separate tradeoff dimensions. If safety review is absent, report review required rather than inferring acceptable deferral.

Persist a canonical input snapshot plus hash and algorithm version. Re-evaluation after a source or assumption change produces a new evaluation; never silently mutate the old result. Hash canonical semantic inputs and results, excluding generated IDs and timestamps.

## AI and persistence

The explanation service reads saved evaluation facts, then renders deterministic templates or calls an optional backend provider. It never writes estimates, projects, or scenarios. Strict claim references and rendered numerical facts gate generated output; failure returns deterministic text. See AI_SYSTEM.

SQLite stores entity references, indexed IDs/date fields, geometry JSON text, evidence, scenario actions, and snapshot JSON. Shapely performs spatial operations in memory; no SpatiaLite requirement. Enforce foreign keys and transactionally save evaluations/audits. M1 uses the Python standard-library sqlite3 driver, with three tables (`dataset`, `evidence`, `roads`) and validated JSON payloads. Connections are short-lived, SQL is parameterized, foreign keys are enabled, and imports are transactional. There is one immutable demo snapshot per database; schema initialization uses CREATE TABLE IF NOT EXISTS, with no migration framework. M2 adds `schema_migrations`, `fixture_imports`, `maintenance_assets`, `assessments`, `repair_options` and `estimates`. Existing M1 payloads are untouched. Estimate JSON retains immutable inputs/results with low/base/high integer-cent columns, foreign keys and update/delete rejection triggers. Scenario evaluations are not implemented. Frozen GeoJSON/JSON fixture imports are repeatable by manifest IDs and checksums.

## Errors, security, and evolution

Use the API error envelope with field errors and request IDs. Schema violations are 422, unknown IDs 404, incompatible scenario/snapshot state 409, unavailable storage 503, unexpected failures 500. A valid but incomplete dataset returns warnings/indeterminate results rather than a success-shaped empty clearance. Provider failures use an explicit fallback response.

MVP is local-only, unauthenticated, with restricted local CORS. Do not expose it publicly. Later commercial work requires identity/roles, tenant scoping in every repository, isolation tests, durable backups, retention, ingestion jobs, licensing review, security assessment, and municipal procurement/engineering review. Adapter and repository interfaces permit those changes without splitting the monolith prematurely.

TBD decisions and recommendations are tracked in FOUNDATION_INSPECTION. M1 dependency versions are pinned in apps/web/package-lock.json and apps/api/requirements.txt; see README for prerequisites.

## Implemented M1 path and scope reconciliation

`GET /api/v1/road-segments/geojson` → RoadRepository → SQLite → validated Road/FeatureCollection → centralized web API client → MapLibre local GeoJSON source. React owns selection; road detail and evidence are separately read through REST. Dataset counts use the fully loaded collection; a search does not change the snapshot counts. Loading and failure states do not fabricate records. Requests have abort support and a 10-second timeout.

The original roadmap deferred SQLite to M2. The explicit M1 request requires persistence and repeatable seeding, so M1 brings forward only road/evidence storage. A synthetic `condition_summary` read projection supports the requested map categories without pretending to implement full ConditionAssessment lifecycle/selection. This is documented in DATA_MODEL and API_SPEC. No estimates, conflicts, projects, AI or scenario work was brought forward.

Default map style: local background-only MapLibre style with API GeoJSON, no remote tile/font/sprite URLs. Attribution: CivicPlAIn synthetic schematic; no municipal observations; no basemap tiles. The MapLibre 6 ESM worker is bundled locally via a Vite URL import and setWorkerUrl, following the [official migration guidance](https://maplibre.org/maplibre-gl-js/docs/guides/v5-to-v6-migration-guide/). Map and resource/WebGL failures keep the equivalent searchable road list available. There is no optional online basemap to fail over from; the documented empty-style fallback is the default.

Local CORS is restricted to explicit loopback HTTP origins. Configuration uses environment variables without an implicit dotenv loader. Startup creates an empty schema; explicit `python -m app.seed` validates manifest checksums, count/IDs, geometry, evidence and bounds before any transactional import. Changed manifests cannot overwrite the same snapshot. Runtime databases and build outputs are ignored.

## Implemented M2 boundaries and migration

`services/estimates.py` is independently callable with validated Road, Assessment, RepairOption and optional PlanningAssumptions objects. It imports neither FastAPI nor SQLite, and performs no HTTP/model calls. `routes/planning.py` resolves references, checks snapshot identity, calls the engine and persists a new UUID estimate. `core/planning_repository.py` owns assessment/catalog/snapshot SQL. RoadRepository overlays related asset dimensions and the latest assessment on reads so collection, GeoJSON and detail agree, while raw M1 rows remain byte-identical. The bounded ≤30-road demo accepts this simple per-record repository lookup; bulk loading can follow measured need.

M2 migration `m2-additive-v1` uses an explicit BEGIN IMMEDIATE transaction and executes only CREATE TABLE/INDEX/TRIGGER IF NOT EXISTS, then records version 2 transactionally. The existing three-table store is preserved. Connections close after each operation; foreign keys and transactions apply. No reset, schema drop or import runs on server startup. Explicit seed runs checksum-verify reviewed M2 records, reject changed fixture manifests, and INSERT OR IGNORE; user-modified existing rows are not overwritten. Runtime databases remain ignored. Estimate snapshots are append-only through API and SQLite triggers; this is not a tamper-proof database or production audit system.

Geographic scope: M2 does **not** calculate distances, buffers or lengths from longitude/latitude. Authored synthetic lengths and widths define a hypothetical rectangular repair scope, independent of the drawn centerline. Area is their product and retains both dimension sources. No measured/derived ground-distance accuracy is asserted. EPSG:32618 projection remains the M3 contract for future actual spatial calculations. This avoids a new projection dependency before such calculations exist.

The web `features/estimates/RepairPlanner` consumes API comparisons/history and saves then retrieves the selected estimate. It only formats money, quantities and explicitly displayed fractions as percentages; it does not calculate costs or duration. All alternatives remain inspectable even when the condition rule does not indicate them. Missing-dimension previews return null and a reason; POST requires an explicit assumption to fill the gap. No recommendation model, approval control, budget optimization or project scheduling was introduced.
