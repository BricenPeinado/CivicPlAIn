# Milestone 2 implementation and verification

Completed locally on 2026-11-07 on `feat/m2-repair-estimation`. The initial tree was clean. No commit, push, deployment, dependency installation, M3 conflicts, M4 optimization/scenarios or M5 AI was performed. Existing IDE metadata and M1 geometry/manifest files are preserved.

## Result and scope

The existing map/list/asset panel now supports maintenance dimensions and rectangular area, surface/classification, latest assessment plus history, three repair categories, explainable condition screening, cost/duration comparisons, explicit dimension assumptions, and a saved estimate breakdown. Every price, assessment, dimension and productivity in the catalog is synthetic. There is no actual NYC price/engineering claim. Unknown dimensions block estimates unless explicitly supplied as planning assumptions. Utility coverage stays unknown.

The established 1–10 synthetic scale is retained rather than replaced by an invented 0–100/PCI conversion. Good ≥8 screens preventive maintenance; fair ≥5 and <8 screens resurfacing; poor <5 screens reconstruction. A dated assessment and asphalt information are required for that screen. All alternatives require engineering review; incomplete evidence returns requires_review. A condition score or low price never establishes safety or structural feasibility.

Five related asset fixtures use stable existing road IDs. R-001 poor has 100×8 m; R-002 good 120×7 m; R-003 fair 150×8 m; R-004 lacks dimensions/surface/assessment; R-005 poor has a large 900×12 m scope. These authored repair scopes are independent of schematic centerlines, with no geographic length calculation or measurement accuracy claimed. There are 26 history records: 18 original undated M1 ratings and eight synthetic dated records for four roads. Latest dated assessment wins, stable ID ascending ties; undated records remain visible.

The roadmap's broader generic InfrastructureAsset/WorkProject/UtilityWork/AuditEvent lifecycle is deferred until needed by M3 or later. M2 uses a related pavement-attribute model, normalized history, catalog and immutable estimates. This preserves the modular monolith and the task's explicit maintenance/estimate boundary. No unused future lifecycle or AI service was added.

## Formulas and reproducibility

For each low/base/high cost scenario:

```text
area_m2 = length_m * width_m
roadwork = round_cents(area_m2 * bundled_unit_rate)
mobilization = round_cents(1 * mobilization_allowance)
traffic = round_cents(1 * traffic_management_allowance)
subtotal = roadwork + mobilization + traffic
contingency = round_cents(subtotal * contingency_fraction)
total = subtotal + contingency

active_workdays = ceil(area_m2 / productivity_m2_per_active_workday)
total_preliminary_days = active_workdays + setup_days + curing_days
```

Decimal arithmetic uses ROUND_HALF_UP to USD cents per line and contingency. Bundled roadwork includes materials, labor and equipment exactly once. Low/high rates are explicitly −20%/+30% of base; other inputs stay fixed. Bounds are sensitivity assumptions, not probabilities. No contractor calendar or completion dates are generated. Duration separates active work, setup and curing.

R-001 resurfacing is reproducible manually: 800×$45 = $36,000 roadwork; +$6,000 mobilization +$2,500 traffic = $44,500 subtotal; +20%/$8,900 contingency = **$53,400 base**, **$44,760 low**, **$66,360 high**. Duration is ceil(800/600)=2 active +2 setup +1 curing =5 preliminary days. Despite its price, resurfacing is not indicated by this poor-condition demo rule.

Each saved estimate freezes the full enriched road, selected assessment, option/rate/productivity definition, request, source records, optional inline user assumptions, and `repair-estimate-v1`. Canonical sorted-key compact ASCII JSON yields input/result SHA-256 hashes. Semantic result hashing excludes generated ID/time. Tests replay saved inputs independently of SQLite/FastAPI and obtain the same result hash. Later catalog/asset changes leave saved outputs unchanged.

## Actual endpoints

All use `/api/v1` and the established envelopes/error structure. No `/api/roads` aliases were introduced.

| Method | Path | Behavior |
| --- | --- | --- |
| GET | `/health` | Existing local health/readiness |
| GET | `/road-segments` | Existing paginated/bbox road reads with enriched attributes |
| GET | `/road-segments/geojson` | Existing map collection with matching enriched properties |
| GET | `/road-segments/{id}` | Asset overview and latest assessment projection |
| GET | `/evidence-sources/{id}` | M1 or M2 source metadata |
| GET | `/road-segments/{id}/conditions` | Complete bounded history; meta.latest_usable_id |
| GET | `/repair-options` | Complete three-option catalog |
| GET | `/road-segments/{id}/repair-options` | Three suitability results and nonpersisted previews or missing-input reasons |
| POST | `/estimates` | 201 immutable snapshot |
| GET | `/estimates/{id}` | Saved result, inputs, sources and hashes without recalculation |

POST requires road_segment_id, repair_option_id, dataset_snapshot_id. Optional planning_assumptions accepts length_m and/or width_m in meters with a nonblank note. Dimensions must be positive, finite and at most three decimal places; length ≤100,000 m and width ≤100 m for the bounded prototype. This is supported input resolution, not measured accuracy. No arbitrary rate/area-only/productivity override is supported. Extra fields and inconsistent units return 422; missing dimensions return 422 MISSING_ESTIMATE_INPUTS; missing references return 404; snapshot incompatibility returns 409. No distinct 400 case is necessary for this typed request contract. Unavailable storage retains sanitized 503 handling.

## Database evolution and preservation

The additive `m2-additive-v1` migration runs with BEGIN IMMEDIATE and records version 2 in schema_migrations. It only creates missing tables, an assessment index and immutable-estimate triggers. It never rewrites the existing dataset/evidence/roads tables or their payloads.

Added tables: schema_migrations, fixture_imports, maintenance_assets, assessments, repair_options, estimates. Estimates store immutable validated JSON plus low/base/high integer-cent totals with ordered/nonnegative checks. Foreign keys link roads/snapshots. SQLite triggers reject estimate UPDATE/DELETE; no HTTP edit/delete path exists. Connections close after each transaction. This is application immutability, not a tamper-proof storage claim.

Startup initializes schema only. Explicit seeding checks fixture checksums/counts/IDs/references and freezes the M2 manifest separately from the unchanged M1 dataset manifest. INSERT OR IGNORE adds missing stable records and preserves local edits. Changed manifests cannot overwrite imported fixture identities. A populated three-table M1 database is exercised in tests; raw road payloads and original manifest remain byte-identical. Legacy M1 sourced dimensions lacking the new basis fields remain readable under legacy_synthetic_basis_unknown, with review warnings rather than a measurement claim.

## Local startup

From repository root, with the already installed Python/Node dependencies:

```sh
PYTHONPATH=apps/api .venv/bin/python -m app.seed
PYTHONPATH=apps/api .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

In a separate terminal:

```sh
npm run dev --prefix apps/web
```

Open http://127.0.0.1:5173/; select R-001, R-002, R-003, R-004 or R-005, then Compare Repair Options. Inspect history/scope, optionally enter explicit dimensions with a note, then Save & inspect. The UI creates and retrieves the snapshot before showing the saved breakdown. Low/base/high details are selectable. Stop newly launched servers with Ctrl+C. Restart a pre-existing M1 API to load M2 code after seeding; no database reset is needed. Fresh installation prerequisites and locked dependency commands remain in README.

## Executed verification and outcomes

| Command/check | Actual result |
| --- | --- |
| Baseline `PYTHONPATH=apps/api .venv/bin/python -m pytest apps/api/tests -q` | 24 M1 tests passed before feature work |
| Baseline `npm test --prefix apps/web` | 15 M1 tests passed before feature work |
| Final `PYTHONPATH=apps/api .venv/bin/python -m pytest apps/api/tests -q` | **53 passed**, one existing Starlette/httpx deprecation warning |
| Final `npm test --prefix apps/web` | **22 passed**, four suites |
| `npm run typecheck --prefix apps/web` | Passed |
| `npm run build --prefix apps/web` | Passed including typecheck; existing MapLibre large-chunk advisory |
| `python3 scripts/create_m2_fixture.py` with before/after SHA-256 comparison | JSON and manifest byte-identical |
| `python -m app.seed` against isolated verification databases | 24 roads; M2 counts (5,26,3); successful startup afterward |
| `git diff --check` | Passed |
| Lint | Not run: no lint command is configured |

Backend coverage includes M1 endpoints, negative/nonfinite dimensions, zero/inconsistent area, invalid condition scores, missing dimensions/basis/provenance, scale/category agreement, latest-assessment ties and undated evidence, exact component/contingency arithmetic, rounding, low/base/high ordering, unit mismatches, rate validation, duration ceil/setup/curing, zero/negative productivity, deterministic repeatability, saved-input replay, 404/409/422 handling, CORS POST preflight, storage persistence/restart, immutable snapshots/triggers, source checksum/reference rejection, existing-asset edits preserved by seed, immutable fixture manifests, no implicit seed, and populated-M1 migration preservation.

Frontend coverage includes existing map/list/keyboard selection, loading/empty/error/retry behavior, condition/provenance labels, three repair cards, history, money/quantity/duration formatting, estimate save/retrieve/breakdown, sensitivity selection, explicit assumption validation/payloads, missing-input API errors and component failure/retry. Map tests preserve no-WebGL/resource-error fallback behavior.

Actual browser verification used isolated local servers on **8001/5174**, leaving pre-existing 8000/5173 servers untouched. Observed the 24-road MapLibre rendering and legend; clicked a real map line to select R-010; selected R-004 with Enter; inspected unavailable previews and a real 422 error; entered explicit 100×8 m assumptions with a note; observed POST 201 followed by saved GET 200 and labeled user-assumption provenance. R-001 showed both M1 and M2 source records, three alternative totals, saved $53,400 base breakdown and separated duration. High sensitivity displayed $66,360. At 390px width, document width was exactly 390px; table overflow stayed inside its labeled, keyboard-focusable scroll region. Desktop was checked at 1440px. Temporary viewport overrides were reset. Verification servers were stopped afterward; pre-existing user processes were preserved.

Browser proof is an ignored local artifact: `data/tmp/m2-browser-estimate.jpg`. Runtime SQLite files, screenshots, build output and caches remain untracked. Browser checks do not claim cross-browser coverage, full accessibility certification or an M2 production-bundle browser smoke test; the production build itself passed.

## Acceptance criteria

| # | Criterion | Status / evidence |
| --- | --- | --- |
| 1 | Maintenance asset attributes | PASS — enriched roads and five related fixture records |
| 2 | Assessment history retrieval | PASS — conditions endpoint, ordering tests and history UI |
| 3 | Three repair categories | PASS — catalog/API/UI |
| 4 | Transparent suitability | PASS — versioned rule/rationale, review required |
| 5 | Deterministic costs | PASS — pure Decimal engine, exact arithmetic tests |
| 6 | Inspectable components | PASS — three bundled/allowance lines plus contingency |
| 7 | Explicit duration productivity | PASS — active/setup/curing breakdown and validation |
| 8 | Reproducible low/base/high | PASS — documented rate sensitivity and ordering/replay tests |
| 9 | Source/assumption snapshots | PASS — complete immutable inputs, hashes and version |
| 10 | FastAPI create/retrieve | PASS — 201/GET, persistence/restart, browser |
| 11 | Frontend comparison | PASS — three API-derived previews, missing-input state |
| 12 | Cost/duration breakdown UI | PASS — frontend tests and actual browser |
| 13 | Synthetic labeling | PASS — record, source, card and saved-estimate labels |
| 14 | Existing map preserved | PASS — M1 tests and actual map-click selection |
| 15 | Data-preserving schema changes | PASS — populated M1 migration and unchanged raw payload tests |
| 16 | Backend tests | PASS — 53 |
| 17 | Frontend checks/build | PASS — 22 tests, typecheck, build |
| 18 | Consistent documentation | PASS — README and shared contracts updated; later scope explicitly deferred |

## Known limits and next milestone

No M2 acceptance criterion is left incomplete on the verified local host. All current source imports are synthetic-only; real municipal data, measured dimensions and verified prices require a reviewed adapter and schema extension. No certified engineering feasibility, official PCI, geographic measurement accuracy, statistical cost intervals, crew/weather calendar, utility clearance, lifespan prediction or project authorization is provided. Unit costs/productivity are catalog-only; editable assessments, arbitrary overrides, general ingestion, estimate listing/history navigation and production authentication are deferred. Each save intentionally creates a new estimate; no POST idempotency key is implemented.

The existing dependency deprecation and MapLibre chunk-size advisories remain nonblocking. No new dependencies were introduced. Local regression and browser evidence are adequate for **M3 integration readiness**; M3 itself has not begun. M3 should add actual projected spatial calculations and project/utility temporal contracts, retaining these immutable estimate inputs and unknown-coverage controls.

## Exact changed-file inventory

Modified:

- `README.md`
- `apps/api/app/core/repository.py`
- `apps/api/app/main.py`
- `apps/api/app/models/database.py`
- `apps/api/app/schemas/roads.py`
- `apps/api/app/seed.py`
- `apps/web/src/App.tsx`
- `apps/web/src/services/api.test.ts`
- `apps/web/src/services/api.ts`
- `apps/web/src/styles.css`
- `apps/web/src/types/api.ts`
- `docs/AI_SYSTEM.md`
- `docs/API_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/DATA_MODEL.md`
- `docs/DATA_SOURCES.md`
- `docs/DEMO_PLAN.md`
- `docs/MVP_ROADMAP.md`
- `docs/PRODUCT_SPEC.md`
- `docs/RESPONSIBLE_AI.md`

Created:

- `apps/api/app/core/planning_repository.py`
- `apps/api/app/routes/planning.py`
- `apps/api/app/schemas/planning.py`
- `apps/api/app/seed_m2.py`
- `apps/api/app/services/estimates.py`
- `apps/api/tests/test_planning.py`
- `apps/web/src/features/estimates/RepairPlanner.test.tsx`
- `apps/web/src/features/estimates/RepairPlanner.tsx`
- `data/demo/maintenance-manifest.json`
- `data/demo/maintenance.json`
- `docs/M2_IMPLEMENTATION.md`
- `scripts/create_m2_fixture.py`
