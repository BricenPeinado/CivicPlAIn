# MVP implementation roadmap

Status: M0–M3 and M3.5 are complete locally; M4 is implemented locally; M5 is implemented locally; M6 remains unimplemented. See [M5_IMPLEMENTATION](M5_IMPLEMENTATION.md). See [M4_IMPLEMENTATION](M4_IMPLEMENTATION.md). M3.5 verification is recorded in [M3_5_COMPATIBILITY](M3_5_COMPATIBILITY.md). M3 verification is recorded in [M3_IMPLEMENTATION](M3_IMPLEMENTATION.md). M2 verification is recorded in [M2_IMPLEMENTATION](M2_IMPLEMENTATION.md). M1 verification is recorded in [M1_IMPLEMENTATION](M1_IMPLEMENTATION.md). Each milestone must satisfy its gate before the next; keep scope viable for one developer. M1–M3 file locations now exist; M4 files now exist; M5 file locations now exist; M6 remains planned.

## M0 — Foundation and repository setup

- Objective: establish one consistent, honest implementation contract and preserve the repository.
- Dependencies: inspect repository, Git, and existing configurations before edits.
- Files/modules: root README, AGENTS, environment/ignore templates, docs, empty apps/data/scripts scaffold, Python package markers.
- Tasks: document product, schemas, API, AI controls, study window, demo assumptions, roadmap, discrepancies, and unresolved decisions.
- Acceptance: requested documents exist and cross-link; no application logic, migrations, dependency installation, deployment, commit, or push; existing IDE files remain intact.
- Testing: validate links, requested paths/entities/API coverage, Git diff/whitespace, ignored secret/runtime paths, tracked demo path, and baseline file hashes. No application tests exist.
- Definition of done: report tree, changed/new files, validation results, open questions, and exact M1 scope.

## M1 — Local frontend/backend foundation and map (complete)

- Objective: runnable local web/API shell with a selectable bounded map and visible data status.
- Dependencies: M0; select runtime versions, dependency manager/locks, and local map style/license strategy. No API key prerequisite.
- Files/modules: apps/web package/Vite/TypeScript/Tailwind configuration, src/pages and map feature; apps/api dependency manifest, app entry/config, routes/health; scripts development helpers; .env.example, README, minimal data/demo geometry and manifest.
- Tasks: initialize one React application and one FastAPI application; add validated local CORS/config; implement proposed health route; load at most 30 labeled demo roads; map selection plus equivalent list; provide local empty-style/GeoJSON fallback when basemap unavailable. Lock only needed dependencies.
- Acceptance: documented fresh setup launches both processes; health returns the proposed schema; segment selection works; no-key/no-tiles mode works; synthetic labels and source legend visible. No estimate/conflict functionality claimed.
- Testing: backend health/config checks, frontend typecheck/build, map selection smoke check, absent-key and tile-failure paths; record actual commands.
- Definition of done: local run and stop commands verified, versions locked, supported endpoints marked implemented with evidence, M1 acceptance checklist recorded. See M1_IMPLEMENTATION for actual checks and known build/test warnings.
- Scope reconciliation: the explicit M1 implementation request requires SQLite persistence, idempotent seeding, basic condition categories/details and summary counts. Minimal road/evidence SQLite storage and a read-only synthetic condition_summary therefore move forward from M2. At the M1 gate no full assessment/asset/project lifecycle or estimate functionality was implemented; M2 is recorded below.

## M2 — Road assets and repair estimates (complete)

- Objective: inspect records and reproduce assumption-based cost/duration estimates.
- Dependencies: M1; review DATA_MODEL, fixture coverage, and per-field provenance; extend the M1 sqlite3 persistence adapter for related maintenance attributes, assessments and estimate snapshots. Projects/utility work are deferred to M3 under the explicit M2 task scope.
- Files/modules: RoadSegment maintenance attributes, ConditionAssessment, RepairOption, CostEstimate and EvidenceSource; services/estimates and repositories; routes roads/conditions/estimates/repair-options; web assets/estimates; tests; demo fixture manifest/import script.
- Tasks: validate/load reviewed fixtures, extend SQLite persistence and introduce migrations only if justified, implement asset detail and latest assessment selection; tie-break equal assessment dates by stable ID; implement decimal cost math, duration assumptions, bounds, explicit scope and missing-input errors. Record source snapshot and method version.
- Acceptance: known records and unknown fields render correctly; estimate totals can be reproduced manually; source/synthetic distinctions survive import; immutable estimates and M1 records survive local restart; API/UI expose the same values.
- Testing: validation and repository integration; cents rounding, negative rates, mismatched units, missing geometry/dimensions, invalid ranges, equal-date assessments, fixture import idempotence, and estimate details UI smoke test.
- Definition of done: supported routes documented, formula and evidence tests pass, setup includes repeatable seeding, no unlabelled synthetic observations.

M2 result: five linked maintenance fixtures, 26 assessment records, three treatments, read-only history, comparison previews, explicit dimension assumptions, Decimal line/contingency math, duration allowances, saved source snapshots, and UI breakdowns. No project lifecycle, conflicts, scenarios or AI were added. See M2_IMPLEMENTATION for actual checks.

## M3 — Geospatial and temporal conflict detection (complete)

- Objective: flag concurrent work and near-term reopening risks while preserving unknown coverage.
- Dependencies: M2; freeze CRS, proximity tolerance, interval, and horizon semantics in ARCHITECTURE.
- Files/modules: schemas/models ConflictFinding; services conflicts/spatial adapter; routes/conflicts; web conflicts overlays/panel; tests and demo fixtures.
- Tasks: validate/project geometry; evaluate project pairs deterministically; emit findings and indeterminate checks; persist evidence/method parameters; map both work footprints; separate utility coverage from findings.
- Acceptance: overlapping synthetic road/utility case is detected; adjacent dates do not overlap; later utility case triggers reopening rule; missing utility geometry/schedule produces a warning; no screen says excavation is safe.
- Testing: projected metre thresholds including exact boundary, crossing/grade ambiguity, date adjacency, 0/30/31-day horizons, missing inputs, invalid geometry, duplicate findings, stable input-order-independent results.
- Definition of done: fixtures and manual reasoning agree; API and map reference identical findings; coverage limitations persist even with zero findings.

M3 result: seven persisted fictional work projects, multi-road links, explicit approximate/unknown location and schedule provenance; EPSG:32618 spatial screening with STRtree; concurrent work, multiple closures, potential rework and sequencing findings; separate indeterminate checks; immutable source/parameter snapshots and stable IDs; six REST routes; project map layers, category controls, selection/filtering and evidence panels. Default demo: 8 findings, 10 indeterminate checks, 16 candidates of 21 possible pairs. Contract reconciliation: `/conflicts/analyze` replaces the unimplemented `/conflicts/check`; utility classification/scope fields are part of WorkProject, avoiding an unnecessary subtype table. Full generic assets and AuditEvent/review-note workflows remain deferred. See M3_IMPLEMENTATION for actual verification and limits.

## M3.5 — Compatibility and architecture preparation (complete)

- Objective: remove ambient Node type dependency and reconcile M4 design with the working M2/M3 contracts.
- Implementation: pinned project-local @types/node and explicit Node type inclusion; no TypeScript/runtime dependency upgrades. The transitive undici-types addition belongs to that type package.
- Contracts: DATA_MODEL defines scenario-v1/scenario-action-v1, quantity/provenance, supplied schedules/calendars/closures and explicit mobilization groups; ARCHITECTURE defines a pure hypothetical adapter that delegates to the unchanged M3 engine without writing projects.
- Reconciliation: current M2 rates, rate-only sensitivity and five preliminary days are authoritative. The old demo's $120,000 resurfacing, patch/restoration prices, whole-total multipliers and unsourced lifespan values are retired. Patch/restoration methods and lifespans remain unavailable, with future source requirements documented.
- Acceptance: clean isolated npm ci, frontend tests/typecheck/build, backend regressions, database integrity and saved-input replay pass; existing data preserved; no scenario runtime models/tables/routes/evaluator/UI or calendar optimizer added. Actual commands and results are in M3_5_COMPATIBILITY.
- Remaining M4 work: implement the frozen proposed contracts, shared quantity/cost helper and hypothetical adapter, snapshot persistence and comparison UI under separate authorization. Either retain honest indeterminate patch/restoration rows or add reviewed versioned catalog methods; never invent prices to complete a narrative.

## M4 — Budget-aware scenario comparison (complete locally)

- Objective: compare three manually constructed alternatives with transparent scope and tradeoffs.
- Dependencies: M3.5 contracts and regression gate; explicit repair/action assumptions and common source contents, roadwork-only budget basis and planning horizon.
- Files/modules: models/schemas Scenario and ScenarioEvaluation; services scenarios/evaluation; routes scenarios/evaluations; web comparison; tests; demo scenarios.
- Tasks: save draft scenarios with actions and budget; calculate costs, bounds, supplied-calendar elapsed time, explicit lane-closure-days, sourced-or-unknown lifespan and review flags; check central/upper affordability; store immutable snapshots/hashes; show exclusions and explicit repeat-restoration costs.
- Acceptance: before/after/coordinated synthetic scenarios match authoritative M2 components in DEMO_PLAN; optional explicit unpriced patch/restoration actions retain indeterminate totals; budget changes are visible; missing cost returns indeterminate; coordination includes a deferral review warning; no global optimality or safety claim.
- Testing: totals and bounds, budget equality/zero, empty or duplicate actions, mismatched snapshots/cost scopes, unknown rates, shared mobilization, repeat runs, source mutation producing a new snapshot, immutable old evaluation.
- Definition of done: complete comparison from saved input to UI is reproducible; constraints and assumptions are inspectable; all affordability labels qualified.

M4 reconciliation: the authorized demo now uses the same resurfacing scope in three supplied schedule alternatives (before, after, coordinated overlap). The older immediate-plus-restoration/staged-patch narrative remains unpriced, with unavailable-input behavior tested rather than invented methods. Empty drafts are allowed; mutable drafts carry optimistic revisions; saved evaluations remain append-only. Calendar assumptions are recorded, not optimized. Nonempty shared-mobilization groups are explicitly rejected. M4 includes conservative Pareto comparison of fully available comparable objectives, with no weighted winner. See M4_IMPLEMENTATION for actual verification and limitations.

## M5 — AI explanations and responsible-AI controls (complete locally)

- Objective: explain validated results with safe deterministic fallback and optional evidence-grounded AI.
- Dependencies: M4; AI_SYSTEM contracts and responsible-AI test cases. Any credential setup is a separate authorized task; do not obtain a key merely to implement fallback.
- Files/modules: services explanations/provider interface/claim validator; routes explanations/reviews; AuditEvent persistence; web evidence/review panels; tests; AI docs and environment configuration.
- Tasks: deterministic templates first; optional backend-only provider with timeout; structured claim references; reject unsupported content; expose mode/fallback reason; record review notes and audit metadata without approving work.
- Acceptance: no-key workflow fully useful; injected instructions in evidence cannot alter behavior; numbers/dates are rendered from facts; invalid/missing citations or outage fall back; reviewer remains accountable.
- Testing: grounding, unknown omission, unsupported numbers/claims, malicious source text, schema failures, timeout/rate limit/unavailable key, provider mock, redacted logging and review audit. Live paid calls are optional and never required by tests.
- Definition of done: failure matrix passes and fallback is demonstrated; generated output cannot mutate facts; API/user interface distinguish facts, assumptions, and prose.

M5 result: seven bounded context types; frozen estimate/analysis/evaluation replay and content/source hashes; strict fact/template selections through the official server-side SDK; deterministic default/fallback; contextual REST advisor integrated into existing views; inspectable evidence, synthetic/unknown labels, How AI works and separate human-review notes; additive append-only evidence/interaction/review persistence. The explicit M5 request selects `/api/v1/ai/*` instead of the older proposed `/explanations` path, reconciled in API_SPEC. No arbitrary AI prose, tools, source mutations, paid calls, new demo prices or autonomous agents. Local acceptance and limitations are recorded in [M5_IMPLEMENTATION](M5_IMPLEMENTATION.md).

## M6 — Integration testing, demo and presentation

- Objective: reliable end-to-end demo with clear limits and a defensible presentation.
- Dependencies: M1–M5 gates; frozen reviewed manifest and offline fallback.
- Files/modules: API integration and web end-to-end tests, scripts/demo reset/verification, data/demo manifest, README and DEMO_PLAN, presentation notes in docs.
- Tasks: verify fresh setup, full workflow and empty/unknown/provider-failure paths; measure local performance targets; inspect keyboard/non-color flows; rehearse the narrative; record limitations and actual commands.
- Acceptance: complete map → asset → estimate → conflict → three-scenario comparison → evidence/review journey; no-key/no-network-data demonstration; all displayed demo numbers reconcile; no synthetic observation is presented as real.
- Testing: integration and regression suite, build/typecheck, snapshot reproducibility, secret checks, accessibility smoke checks, performance measurements on documented hardware, demo rehearsal checklist.
- Definition of done: verified demo can be repeated from documented instructions; outstanding failures and municipal-use limits are disclosed; no production readiness claim or deployment required.

## Separate stretch backlog

Only after M6: condition-based prioritization with explainable policy weights; NetworkX detours/disruption analysis with verified graph semantics; extra optimization constraints with an explicit OR-Tools justification if needed. None blocks hackathon acceptance.

## Post-MVP backlog

Progress forecasting, live municipal integrations, additional infrastructure classes, and commercial multi-tenant controls. Each requires separate source validation, domain review, security and licensing work, and new acceptance criteria.
