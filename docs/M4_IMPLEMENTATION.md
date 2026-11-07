# Milestone 4 implementation and verification

Implemented locally on 2026-11-07 on `feat/m4-scenario-planning`, starting from a clean `bp/m3-5-compatibility` working tree. M3.5 requirements were inspected and its baseline verified: 93 backend tests and 32 frontend tests passed. No commit, push, deployment, OpenAI call, new dependency or M5 implementation was made.

## 1. Result and scope

The existing React/FastAPI/SQLite application now supports hypothetical scenario creation/editing, multiple repair actions, explicit scopes/quantities/assumptions, optional supplied schedules/closures, external project selection and explicit exclusions/replacements, deterministic evaluation, budget sensitivity, immutable history and two/three-plan comparison. The existing map and keyboard road list supply the selected road. The modular monolith and REST boundary are unchanged.

M4 uses the M3.5 nested scenario-v1, scenario-action-v1 and schedule-proposal-v1 contracts. Reconciliations are explicit: empty drafts are allowed but cannot be feasible zero-cost scenarios; draft edits retain stable IDs with optimistic revisions instead of creating an unrelated Scenario ID; PATCH atomically replaces a complete typed draft/action inside an expected_revision envelope; the authoritative comparison route remains `/scenario-comparisons`. The new demo follows the authorized before/after/coordinated narrative with equal road scope. The old proposed staged-patch/restoration story remains unpriced rather than receiving invented methods.

## 2. Model and transport

Additive schema migration 4 creates scenarios, scenario_actions, scenario_projects and scenario_evaluations with foreign keys. BEGIN IMMEDIATE serializes draft writes and revision checks. Evaluations are append-only with SQLite UPDATE/DELETE rejection triggers. No existing tables are reset or rewritten. Evaluations retain the complete scenario revision/hash, inputs, source contents/aliases, analysis versions, quantities, line/contingency calculations, low/base/high totals, budget headroom, schedules, hypothetical findings and result hashes. Snapshot replay requires no live source lookup. Source changes append history rather than updating earlier results.

ScenarioEvidence validates per-field source-record links or explicit authored assumptions. Exact source record/field/value/upstream evidence must match; unrelated records and missing references fail. Assumption content is frozen as namespaced synthetic Evidence records with version/checksum/limitations. Action classification is fixed to derived, synthetic_input=true and hypothetical=true; callers cannot claim observed work. General observed municipal adapters remain unsupported.

Implemented `/api/v1` routes:

- POST/GET `/scenarios`; GET/PATCH `/scenarios/{id}`.
- POST `/scenarios/{id}/actions`; PATCH/DELETE `/scenarios/{id}/actions/{action_id}`.
- POST `/scenarios/{id}/evaluate`; GET `/scenarios/{id}/evaluations`.
- GET `/scenario-evaluations/{evaluation_id}`; POST `/scenario-comparisons`.

The existing envelopes and sanitized 404/409/422/503 errors are retained. Scenario listing uses limit/after; history uses limit/offset. The API contract documents the exact typed bodies and pagination. CORS extends the same configured loopback origins to PATCH/DELETE. Evaluating a scenario cannot write a real work project or M3 finding.

## 3. Reused calculations and comparison

`services/estimates.cost_scenarios` is factored from the existing M2 implementation; M2 calculate still supplies its original dimension wrapper, output shape and repair-estimate-v1. M4 supplies validated quantities to that same helper and reuses M2 duration and suitability. No formula or whole-total sensitivity multiplier is duplicated.

Each low/base/high action result rounds roadwork, mobilization and traffic lines to cents with Decimal ROUND_HALF_UP, sums those lines, rounds contingency and adds it. The scenario sums the already rounded action totals; it adds neither contingency nor mobilization again. Default mobilization remains per action. Same-road scopes require disjoint explicit footprints or justified repeat work with distinct dates; IDs/descriptions/method changes alone cannot double charge a scope. Unsupported cost overrides and nonempty shared-mobilization groups are explicitly rejected.

Whole-road quantity resolves the frozen road's planning dimensions. Explicit rectangles preserve dimensions; explicit partial area has no fabricated rectangle. Trench scope cannot borrow a whole-road catalog method. Unknown quantity/method leaves the action unavailable; any unavailable required action or empty action set nulls complete scenario totals/headroom and forces indeterminate budget feasibility. Known component subtotal remains separately labeled incomplete.

For each sensitivity case, headroom = budget − cost. Base cost equal to budget is within_budget; high-case affordability is reported independently. Calendar envelope, declared lane-closure-days, closure-overlap pairs and summed preliminary workdays remain separate metrics. Dates are never inferred from estimated workdays. Missing schedules/closures produce null affected metrics and incomplete checks. No traffic-delay/economic-cost/lifespan values are invented.

`services/hypothetical.screen` projects validated actions into WorkProject snapshots and invokes the unchanged M3 engine once. It imports no repositories or mutation tools. The original projects, explicit override history, sources and action/project origin map remain frozen. Findings are labeled hypothetical or existing_project_screen. New runs pass all bounded road snapshots for the same M3 projected corridor rules, including roads not explicitly declared by a project. The screen_road_scope context versions this input-universe choice; the pre-release M4 snapshots authored during this task retain their earlier declared-road context for reproducible replay, and cross-scope comparison is rejected. EPSG:4326 → EPSG:32618, method/library versions, half-open date semantics and missing-data limitations are retained. Patch/restoration/unknown categories get generic spatial/temporal checks plus UNCLASSIFIED_REOPENING_RULE, never a fabricated resurfacing mapping.

`services/scenario_comparison` is a separate lightweight planning helper over saved evaluations. It rejects incompatible baseline contents, horizon, price basis, currency/cost scope, versions, screening parameters or road universe. Rows disclose scope and authored-assumption differences. Cost deltas are null when either complete cost is unavailable. Differing service scopes are not equivalent-service savings. Pareto dominance requires matching scope/assumptions/budgets and complete objective/check inputs and names its numeric objectives: base cost, lane-closure-days, scheduled road-workdays and screened conflict count. It is not a safety assessment or general winner. Deterministic sentences report supported cost/date tradeoffs; no weighted score, automatic schedule choice or OR-Tools is used.

## 4. Demo and data preservation

Reviewed new fixtures: data/demo/scenarios.json and scenarios-manifest.json; reproducible authoring script scripts/create_m4_fixture.py. M1–M3 fixtures/catalog are unchanged. seed_m4 validates checksum/IDs and preserves existing draft edits and evaluation history. It evaluates the current retained draft/context; identical input reuses its saved content-addressed result, while changed source/method context appends a snapshot. Repeated seeding is idempotent.

| Synthetic plan | Supplied road dates | Reused M3 findings | Low/base/high USD |
| --- | --- | --- | --- |
| A, road repair before utility | [2027-04-01, 2027-04-08) | reopening_risk, 2-day gap | 44,760 / 53,400 / 66,360 |
| B, road repair after utility | [2027-04-15, 2027-04-22) | sequencing_review, 0-day gap | 44,760 / 53,400 / 66,360 |
| C, explicitly coordinated overlap | [2027-04-10, 2027-04-17) | concurrent_work + multiple_closures | 44,760 / 53,400 / 66,360 |

The fictional utility interval is [2027-04-10, 2027-04-15). Every plan explicitly replaces only the original fictional road-project snapshot. Every action prices the same authored 800 m² resurfacing scope. A synthetic $60,000 roadwork budget yields low/base/high headroom $15,240 / $6,600 / −$6,360; base within budget, upper case over budget. Each has five preliminary days, independently supplied seven calendar days and seven authored one-lane closure days. Cost differences are zero; C receives no fabricated discount. Utility costs, possible restoration and catalog exclusions are outside the declared action cost; potential rework is not automatically monetized. Unknown utility coverage/lifespan and human review remain visible.

Before edits, a read-only baseline of all 13 original SQLite tables and a backup were saved under /private/tmp/civicplain-m4. After additive migration and repeat seed, every original row remains identical. Existing counts remain 24 roads, 5 maintenance records, 26 assessments, 3 repair options, 3 evidence sources, 7 work projects, 6 project-road links, 1 conflict analysis, 8 findings and 0 estimates. Only the two metadata tables add the intended migration/import entries. The local runtime now also has three scenarios and six evaluations, including three earlier M4 development snapshots retained through the corridor-scope correction. All six replay with matching hashes. Fresh final-source databases have three scenarios/evaluations; repeated seed leaves their counts unchanged. Runtime databases/backups remain ignored/outside the source tree.

An independent comparison against HEAD's original M2 implementation verified all 12 available road/option calculations and semantic hashes unchanged, and all 60 unavailable combinations still unavailable. The original saved M3 analysis replayed with matching input/result hashes: eight findings and ten incomplete pair checks.

## 5. Executed checks and actual outcomes

Commands run from the repository root unless an absolute prefix is shown. Inspection used git status/branch/diff, rg --files, rg searches and cat/sed reads of AGENTS, README, the eight requested contracts, M3.5 verification, schema/repository/service/route/frontend/test sources, requirements and reviewed fixtures. These reads succeeded; an exploratory rg of nonexistent .github exited 2 and the memory keyword search had no matching context. No repository work was based on historical memory.

| Executed command / check | Actual result |
| --- | --- |
| `git status --short`, `git status --porcelain=v1`, `git branch --show-current` | Clean baseline on bp/m3-5-compatibility |
| `git switch -c feat/m4-scenario-planning` | Initial sandbox lock denied; reviewed retry succeeded; feature branch created |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=apps/api .venv/bin/python -B -m pytest apps/api/tests -q -p no:cacheprovider` | Baseline 93 passed; final development runs 141 passed |
| `npm test --prefix apps/web` | Baseline 32 passed; final 44 passed across seven files |
| `npm run typecheck --prefix apps/web` | Passed after test-fixture corrections |
| `npm run build --prefix apps/web` | Passed; Vite's existing MapLibre large-chunk advisory remains |
| `python3 scripts/create_m4_fixture.py` | Authored deterministic fixture/manifest; seed checksum validation passed |
| `PYTHONPATH=apps/api .venv/bin/python -m app.seed` (repeated) | 24 roads; M2 (5,26,3); 7 projects; 3 scenarios; originals preserved |
| `CIVICPLAIN_DATABASE_PATH=/private/tmp/civicplain-m4/demo.sqlite3 PYTHONPATH=apps/api .venv/bin/python -m app.seed` | Isolated initial synthetic demo seeded successfully |
| Same seed with browser.sqlite3 and final-browser.sqlite3 under the same temporary directory | Both isolated browser databases seeded successfully |
| `.venv/bin/python -m venv /private/tmp/civicplain-m4/api-venv` | New isolated Python environment created |
| `/private/tmp/civicplain-m4/api-venv/bin/python -m pip install --disable-pip-version-check --no-cache-dir --retries 0 --timeout 20 -r apps/api/requirements.txt` | First sandbox attempt could not resolve pinned package; reviewed network retry installed all 25 pinned packages successfully |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=apps/api /private/tmp/civicplain-m4/api-venv/bin/python -B -m pytest apps/api/tests -q -p no:cacheprovider` | Final isolated backend: 141 passed; one existing Starlette/httpx TestClient deprecation warning |
| `/private/tmp/civicplain-m4/api-venv/bin/python -m pip check` | No broken requirements found; pip emitted a non-writable-cache advisory |
| `.venv/bin/python -m pip cache list` | Cache command unavailable in sandbox; no cached-package claim made |
| `rsync -a --exclude=node_modules --exclude=dist --exclude='.env*' apps/web /private/tmp/civicplain-m4/isolated/apps/` and copy of data/demo | Clean frontend source/fixture copy created without modules, build or local environment files |
| `env -u NODE_PATH -u NODE_OPTIONS npm ci --prefix /private/tmp/civicplain-m4/isolated/apps/web --offline --cache /private/tmp/civicplain-m35.61EgYb/npm-clean-cache --no-audit --no-fund` | Installed 197 lockfile packages into the isolated copy; no dependency/lockfile edits |
| `rsync -a --delete --exclude=node_modules --exclude=dist --exclude='.env*' apps/web/ /private/tmp/civicplain-m4/isolated/apps/web/` | Refreshed only the agent-created temporary source copy for final checks |
| `env -u NODE_PATH -u NODE_OPTIONS npm run typecheck --prefix /private/tmp/civicplain-m4/isolated/apps/web` | Final isolated typecheck passed |
| `env -u NODE_PATH -u NODE_OPTIONS npm test --prefix /private/tmp/civicplain-m4/isolated/apps/web` | Final isolated frontend: 44 passed |
| `env -u NODE_PATH -u NODE_OPTIONS npm run build --prefix /private/tmp/civicplain-m4/isolated/apps/web` | Final isolated production build passed; large-chunk advisory only |
| `PYTHONPATH=apps/api .venv/bin/python scripts/verify_m4.py` | integrity_check=ok; foreign_key_check empty; six local immutable evaluations replay with matching hashes |
| Inline read-only SQLite comparison against /private/tmp/civicplain-m4/baseline.sqlite3 | All original table rows retained identically; metadata additions only |
| `git show HEAD:apps/api/app/services/estimates.py > /private/tmp/civicplain-m4/original_estimates.py` plus independent calculation/replay script | 12 M2 outputs/hash matches; 60 unknown cases unchanged; original M3 hashes match |
| `git diff --check` | Passed |

No lint command/configuration exists; no lint pass is claimed. Dependency security auditing was not run. No tests require a provider key, LLM or live municipal data.

Development failures were resolved, not counted as passing checks: the first post-migration backend run had 91 passes and two assertions pinned to schema version 3; those were updated to the new additive version 4. The first M4 suite had 133 passes/two test-oracle failures: a replacement reference was already structurally invalid before unknown-project lookup, and B correctly produces a sequencing review. The test now isolates the unknown reference and asserts the actual M3 rule. The first new frontend test file failed on browser URL versus Node file URL use; fixture reads now follow the existing tests' filesystem convention. Typecheck caught six duplicate fixture-default property declarations; these were corrected. All final suites pass.

## 6. Browser verification

Local servers were exercised against isolated synthetic databases on API 127.0.0.1:8001 and Vite 127.0.0.1:5174. Initial sandbox binding was denied; reviewed loopback launches succeeded. Commands:

```sh
CIVICPLAIN_DATABASE_PATH=/private/tmp/civicplain-m4/final-browser.sqlite3 CIVICPLAIN_ALLOWED_ORIGINS=http://127.0.0.1:5174 PYTHONPATH=apps/api .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8001
VITE_API_BASE_URL=http://127.0.0.1:8001/api/v1 npm run dev --prefix apps/web -- --port 5174
```

Actual UI checks: loaded 24 roads and seven projects; M3 displayed eight findings/ten incomplete checks; opened Scenario Planner; compared A/B/C through the API with actual prices, budget/headroom, findings and dates; selected R-001 in the existing road list; created a new plan with explicit budget/horizon/assumptions, added the selected road, chose resurfacing and saved/evaluated it. The browser visibly displayed $53,400 base, $6,600 headroom, upper-case over-budget sensitivity, frozen revision/history, and unknown schedule/closure metrics when omitted. The POST returned 201 and evaluation 200 in local server logs.

A browser automation label lookup failed to match an action select; inspecting the DOM and using its combobox role resolved it. The browser fill helper did not populate native date controls; native date setters supplied the dates, and the real form then submitted. These were automation issues, not bypassed form validation. Final-source comparison was rechecked after restarting the API. M2 R-001 repair options still render original $8,160 / $172,500 / $53,400 base totals and five preliminary resurfacing days. Narrow (~490 px) and desktop (1280×900) layouts were inspected; temporary viewport override was reset. This is a manual browser smoke check, not an automated accessibility certification or performance benchmark.

Screenshot artifacts from this run: /private/tmp/civicplain-m4/browser-evaluation.png and /private/tmp/civicplain-m4/browser-comparison.png; the latter is also delivered from the Codex visualizations directory. Browser/server fixtures contain only synthetic data. Temporary verification servers were stopped after testing.

## 7. Acceptance criteria

| # | Criterion | Status / evidence |
| --- | --- | --- |
| 1 | Create/edit scenarios | Pass: API and editor, revisions and stale-write tests |
| 2 | Multiple repair actions | Pass: editor and aggregation/duplicate/repeat tests |
| 3 | Reuse M2 estimates | Pass: shared cost/duration/suitability helpers; original outputs unchanged |
| 4 | Correct aggregation | Pass: independent component/contingency/cents/multiple-action oracles |
| 5 | Budget feasibility | Pass: under/equal/over/zero/unknown and sensitivity tests |
| 6 | Reuse hypothetical M3 screening | Pass: same engine/CRS/interval rules; full evidence retained |
| 7 | Real projects unchanged | Pass: zero-write checks and exact original-row comparison |
| 8 | Reproducible evaluation | Pass: saved-input replay, source/parameter mutation and canonical ordering |
| 9 | Immutable snapshots | Pass: SQLite triggers, edit/source mutation/restart retrieval tests |
| 10 | Compare 2–3 scenarios | Pass: API, tests, real three-plan browser comparison |
| 11 | Expose tradeoffs | Pass: deterministic cost/date text, scope/assumption warnings, conservative dominance/non-dominance tests |
| 12 | Expose missing data | Pass: null totals/metrics, indeterminate status, missing/unavailable comparison tests |
| 13 | Synthetic demos work | Pass: checksum-verified repeat seed and authoritative catalog arithmetic |
| 14 | Complete frontend workflow | Pass: list/editor/evaluation/history/comparison; map-road reuse; loading/validation/errors |
| 15 | Preserve M1–M3 | Pass: regressions, original M2 numerical/hash comparison and original M3 replay/browser smoke |
| 16 | Backend suite | Pass: 141 tests, including isolated installation |
| 17 | Frontend tests/build | Pass: 44 tests, typecheck and production build, including isolated installation |
| 18 | Accurate documentation | Updated README, roadmap, architecture, data/API contracts, product status, responsible-AI limits and demo walkthrough |

## 8. Limitations and M5 handoff

No required M4 workflow remains blocked. Optional/new catalog methods, shared mobilization adjustments, automated alternatives/schedule optimization, observed municipal ingestion, measured utility coverage, traffic/economic models and lifespan remain unavailable. The API records advanced work calendars/precedence and validates them; the initial editor has no specialized calendar/precedence editor, while retaining those existing values. It supports explicit repeat-work stages/justification, dates and closure envelopes; independently authored complex closure intervals can be supplied through the API. Nonempty shared-cost groups and unsupported overrides fail explicitly rather than being ignored. No production authentication, deployment, safety certification or performance claim is made. Known warnings remain the existing Starlette deprecation and large MapLibre bundle advisory.

Exact next M5 scope, not started:

1. Read AI_SYSTEM/RESPONSIBLE_AI and consume saved immutable evaluations plus validated comparison snapshots as the sole numerical evidence.
2. Implement deterministic explanation templates and typed fact/source references first, useful without a key/network.
3. Add an optional backend-only provider interface with timeout and structured template/claim selection; independently validate every reference and render numeric facts server-side.
4. Add failure tests for missing key, outage, timeout/rate limit, malformed/unsupported claims and malicious source text; fall back deterministically.
5. Add review-note/AuditEvent storage and UI that records accountability without approving work or exposing municipal mutation tools.
6. Update the M5 contracts and report actual tests/browser checks. Credential setup, paid calls and any deployment remain separately authorized work; do not obtain a key to implement the fallback.

## 9. File inventory

The exact changed/new source and documentation paths follow. Existing IDE metadata, credentials, original fixtures and package lockfiles were preserved.

```text
 M README.md
 M apps/api/app/main.py
 M apps/api/app/models/database.py
 M apps/api/app/seed.py
 M apps/api/app/services/estimates.py
 M apps/api/tests/test_conflicts.py
 M apps/api/tests/test_planning.py
 M apps/web/src/App.tsx
 M apps/web/src/services/api.ts
 M apps/web/src/styles.css
 M docs/API_SPEC.md
 M docs/ARCHITECTURE.md
 M docs/DATA_MODEL.md
 M docs/DEMO_PLAN.md
 M docs/MVP_ROADMAP.md
 M docs/PRODUCT_SPEC.md
 M docs/RESPONSIBLE_AI.md
?? apps/api/app/core/scenario_inputs.py
?? apps/api/app/core/scenario_repository.py
?? apps/api/app/routes/scenarios.py
?? apps/api/app/schemas/scenarios.py
?? apps/api/app/seed_m4.py
?? apps/api/app/services/hypothetical.py
?? apps/api/app/services/scenario_comparison.py
?? apps/api/app/services/scenario_identity.py
?? apps/api/app/services/scenarios.py
?? apps/api/tests/test_scenarios.py
?? apps/web/src/features/scenarios/ScenarioPlanner.test.tsx
?? apps/web/src/features/scenarios/ScenarioPlanner.tsx
?? apps/web/src/features/scenarios/ScenarioResults.tsx
?? apps/web/src/services/scenarios.test.ts
?? apps/web/src/types/scenarios.ts
?? data/demo/scenarios-manifest.json
?? data/demo/scenarios.json
?? docs/M4_IMPLEMENTATION.md
?? scripts/create_m4_fixture.py
?? scripts/verify_m4.py
```
