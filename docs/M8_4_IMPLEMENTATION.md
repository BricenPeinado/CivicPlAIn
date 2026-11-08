# M8.4 — Transparent Road Maintenance Prioritization

Implementation and verification: **2026-11-08**. Status: **software gate PASS; positive verified maintenance-need and independent policy-review gates BLOCKED**. Stop at M8.4. No M8.5 implementation, citywide optimal schedule, spending authorization or production activation.

## Baseline, scope and authority

Inspected the local branch `bp/specify-civicplain-milestone-7`, Git status, AGENTS/README, roadmap/M8 plan/shared contracts, M8.1 conditions, M8.2 permit intelligence, M8.3 estimates and existing deterministic M2/M4 services before implementation. Extensive preexisting uncommitted M8.0–M8.3 work remains preserved. Baseline: **433 backend / 116 frontend tests passed**. Remote code was not substituted.

The current explicit owner request implements original M8 plan A5 prioritization as M8.4, following the previously authorized M8.3 estimate stage. This does not retroactively pass earlier evidence gates. M8.1 partial references do not establish whole-road conditions; M8.2 administrative permits do not establish actual work; M8.3 technical QA quantities/prices are not approved municipal inputs.

Reuse: existing snapshot/source/import tables and v2 envelopes, reviewed intelligence releases, `road_conditions.summarize`, M8.3 immutable estimate verification, Decimal arithmetic, strict typed boundary validation, context-bound pagination and additive SQLite migration machinery. No parallel importer, new dependency, synthetic validator change, demo fixture change, AI computation or external request.

## Implemented method and units

Contract/method: **`maintenance-priority-v1`**. No default municipal policy exists. Every policy requires its ID/version, objective, three decimal-string weights, age horizon, maximum condition age, stale behavior and attributed `planning_assumption` evidence (author/date/rationale and optional citations). Authorship is an assertion, not identity-verified review or approval.

| Factor | Dimensionless definition | Evidence boundary |
|---|---|---|
| `condition_need` | `(10 - exact eligible raw rating) / 9`, for supported 1–10 ratings | Application planning normalization only. Not an official category, calibrated risk, failure probability, treatment suitability or safe-deferral assessment. No rounding of the source rating. |
| `inspection_age` | `min(age_days / explicit age_horizon_days, 1)` | Accepted inspection date relative to explicit as-of date; review age, not predicted deterioration. Publication/retrieval dates never substitute for inspection. |
| `evidence_gap` | 1 if no eligible accepted road-wide assessment; otherwise 0 | Absence of eligible evidence is observable as a data gap, not pavement condition or danger. |

Weights are plain decimal strings in [0,1], up to six decimal places, and sum exactly to 1. All-zero, non-summing, exponent, negative, non-finite and excessive-precision settings are rejected. Arithmetic uses a local Decimal context of precision 40, including recurring divisions; full resulting strings persist without presentation rounding determining order. Day horizons are explicit integer planning assumptions, not NYC inspection standards.

Two separate objectives prevent completeness being disguised as maintenance need:

- `maintenance_review`: requires eligible accepted road-wide official rating/date; evidence-gap weight must be zero. Need and inspection age may be weighted. A qualified review score is not a repair prescription.
- `inspection_review`: condition-need weight must be zero. Evidence gaps and available inspection age may inform a review queue; gap-only policies can rank roads whose maintenance need remains Unknown.

Unsupported nonzero factors never receive zero or redistributed weights. Any missing positively weighted factor leaves score/rank null and the road visibly unranked. Disabled missing factors also retain null values/reasons. Exact ties use competition ranks (1,1,3); road ID orders tied display only. Stale means age strictly greater than the explicit maximum; `exclude` makes maintenance evidence ineligible, while `allow_qualified` retains it with visible qualification. Zero age thresholds and exact boundary values are valid.

## Supported evidence and constraints

The request pins one official base, 1–100 explicit unique road-row IDs, as-of date, optional exact condition/permit releases, up to three complete alternative policies with the same objective, and optional explicit M8.3 estimate/treatment per road. No newest-release, cheapest/latest-estimate or hidden rate selection.

Maintenance need, data completeness, implementation cost, scheduling context and final score remain separate output fields. A cost ceiling is an optional attributed USD planning constraint on the **declared estimate scope**, not a program budget or equal-benefit comparison. Missing/incomplete selected cost under a ceiling yields indeterminate eligibility and no rank; above-ceiling records are excluded. Costs are not automatically scored as maintenance need or efficiency. An available patch/resurface estimate does not establish need or suitability.

| Evidence | Current use / confirmed limitation |
|---|---|
| Accepted official condition | Existing conservative whole-road eligibility, exact raw rating/date/history, release and source hashes; reviewed partial observations never become a road-wide rating. Official category remains Unknown where unsupported. |
| Inspection date | Source date only; no future/source-update date substitution. Missing/stale states visible. |
| LION | Pinned actual road row/geometry/source. Imported feature type 0 is a regular street; no functional road hierarchy, traffic or safety class is inferred from it. |
| Cost | Only explicitly selected, replay-verified M8.3 estimate on the identical road/base, including declared scope, exclusions and human assumptions. No M2 synthetic price reads. |
| Permits | Optional accepted administrative road-reference counts and frozen records/release. Actual footprint, schedule and verified coordination benefit remain Unknown. M8.2 screening candidates are not promoted to scored opportunities. |
| Traffic/disruption | No independently verified input contract/feed activated; Unknown, unweighted. No traffic count, safety risk, failure probability or lifespan invented. |
| Utilities | Unknown; ranking never establishes excavation clearance. |

No new government feed or official numeric policy was activated during M8.4. Existing source investigation and dates remain in [M8.1](M8_1_IMPLEMENTATION.md), [M8.2](M8_2_IMPLEMENTATION.md), [M8.3](M8_3_IMPLEMENTATION.md) and [DATA_SOURCES](DATA_SOURCES.md). The normalization and queue definitions above are explicit application methods, not attributed government guidance.

## Persistence, API and interface

Schema **11**, migration marker `m8-prioritization-v1`, adds only `prioritization_runs`, its snapshot index and immutable UPDATE/DELETE triggers. Full request, complete roads/accepted observations/matches, computed condition summaries, source metadata, explicitly selected complete estimates, optional permit references, policy/definitions and derived projections freeze into content-hashed inputs. ID is `priority-<input_hash>`; result and policy hashes persist separately. Equivalent road-scope order is canonicalized. Same canonical input returns the same run, not a duplicate.

Replay recomputes summaries, verifies selected estimate snapshots and projections, and re-evaluates base/sensitivity from frozen inputs without consulting new observations, wall-clock dates or AI. Integrity/replay mismatch fails closed with 409. Unknown/foreign contexts fail 404; invalid inputs fail 422; persistence/history without explicit schema 11 fails 503. Preview needs no migration beyond the existing compatible base/evidence schema.

V2 `/planning/prioritization-runs` provides explicit POST `/preview`, POST collection, GET history, GET `/{id}`, GET `/{id}/roads` and GET `/{id}/compare` (2–5 distinct same-run roads). Filters/cursors retain the saved universe and rank; no filtered renumbering. POST save recalculates server-side; GET/navigation never creates a run, scenario, evaluation or AI audit. [API_SPEC](API_SPEC.md) is the transport contract.

Dashboard Overview and Map both expose the shared road-review panel: blank numerical policy inputs, attributed assumptions, imported-road search/explicit selection, explicit preview/save, saved history, status/name filters, compare, per-factor contributions, source/inspection dates, unknowns, human-review requirement, frozen JSON lineage and alternative policy rank changes. Missing sensitivity is labeled unavailable. No client-side numerical ranking. Per-snapshot session drafts survive view navigation; edits invalidate results, in-flight work is aborted, discard and unload protection are provided. Draft notes are not written into URLs. Map inspection carries road/date/release context into the existing official inspector and geometry; no invented risk choropleth or footprint.

## Actual pinned-data verification

Original runtime databases were opened read-only for backup/fingerprints. A new ignored copy, `data/tmp/m84-priority-pilot.sqlite3`, was migrated 10→11 with verified new backup `data/tmp/m84-before-schema11.sqlite3`. It retained all preexisting schemas/rows, including two bases and two technical estimate examples. Legacy logical fingerprint: `e34a533b2d19d1a90bd3297b1b3a4bb20fb604edfc1234b3d158eeb63a2ba2bb`.

Pinned base: `nyc-4620b9e30c1c0bd5be4252fe27999c80`, **4,150 road rows**. The first 100 IDs in stable ID order form the bounded API QA universe: **100/4,150 = 2.41%** of imported road rows, not a geographic census or random sample. As-of 2026-11-08; QA age horizon/maximum both explicitly 365 days, exclusion mode. Policies are labeled agent technical QA, pending independent human review, never approved municipal policy.

| Technical exercise | Results (denominator = scoped road rows) |
|---|---|
| Inspection evidence-gap weight 1 | 100/100 ranked (100%), all tied rank 1; 0/100 eligible official conditions. Need remains Unknown. |
| Same universe, age-only sensitivity | 0/100 ranked; 100/100 unranked (100%) because eligible inspection dates are missing. |
| Maintenance need weight 1 | 0/100 ranked; 100/100 unranked (100%). No fabricated positive need ranking. |
| Gap-only inspection with explicit USD 1,000 declared-scope ceiling and one selected M8.3 QA resurfacing estimate | 1/100 ranked (1%); 99/100 cost-indeterminate/unranked (99%). This is arithmetic QA, not an approved price or project budget. |
| Browser WHITE STREET/BROOME STREET explicit gap-only policy | 2/2 ranked (100%), both rank 1; 0/2 eligible conditions. These two overlap the 100-row universe; do not add run counts as distinct coverage. |

Zero verified coordination opportunities in every run. Separate base `nyc-3947b35876a619b31067db96b1409ad8` remains isolated. Permuting scope preserves run ID; explicit save is idempotent. Full saved IDs, input/result/policy hashes, sensitivity and actual counts are in [verification/m8.4-priority-qa.json](verification/m8.4-priority-qa.json). Four runs replay and match pinned evidence; database integrity/FKs pass. Verification hash: `f37c65c8cb25609d84596dc350d907d594861994386d2b2a748cc813d91b8706`.

Read-only reproducible verification (choose a new output path; existing reports are never overwritten by the verifier):

```sh
PYTHONPATH=apps/api .venv/bin/python scripts/verify_m8_4.py \
  --database data/tmp/m84-priority-pilot.sqlite3 \
  --snapshot nyc-4620b9e30c1c0bd5be4252fe27999c80 \
  --report data/processed/m84-verification-new.json
```

The ignored runtime DB is required to independently replay these actual examples; checked-in hashes alone do not distribute original government records or prove independent approval. No live ingestion or source refresh occurred.

## Tests and acceptance gate

Executed before changes: backend 433 passed; frontend 116 passed. Final commands:

- `PYTHONPATH=apps/api .venv/bin/python -m pytest apps/api/tests -q`: **459 passed, 287 existing-library deprecation warnings, 27.00s**.
- `npm test` in `apps/web`: **122 passed, 19 files, 6.40s**.
- `npm run build` in `apps/web`: TypeScript check and production build **PASS**; existing large-chunk warning remains.
- Read-only actual-data verifier: **4/4 saved runs PASS**, exact pinned evidence, hashes, replay, integrity and cross-base isolation.
- Browser: explicit blank form → two-road preview → immutable save → comparison → Map navigation/preserved date and saved result → actual WHITE STREET inspector. An initial map API timeout displayed unavailable/retry; retry succeeded. Screenshot is ignored `data/tmp/m84-priority-map.png`. Mobile layout and concurrent-load performance were not comprehensively tested.
- Documentation checks: `git diff --check`, Markdown fence balance, 162 local documentation links and verification JSON parse **PASS**. Four original runtime DB byte fingerprints remain identical; demo fixtures and dependency lockfiles have no diff. Owned QA servers and browser tab were stopped/closed after verification.
- An initial root-level pytest invocation without `PYTHONPATH` failed collection (`app` not found); corrected command above passed. Actual larger-pilot QA found a pagination row-ID adapter defect; fixed with a regression before final verification.

New backend tests cover stable permutations/ties, missing values, zero/extreme/invalid weights, changed/conflicting factors, decimal rating boundaries, stale boundaries/capping, incomplete costs/ceiling eligibility, objective separation, sensitivity/replay, strict context/unit/date validation, synthetic-origin rejection, atomic persistence/tamper/immutability, pagination context, cross-snapshot isolation, migration from 0/7/8/9/10 and rollback/idempotency. Test-only source-shaped fixtures prove software behavior, never real coverage. New frontend tests cover explicit actions, provenance errors, no automatic calculation, draft isolation/discard, comparison/filter display, invalidation, foreign context and abort behavior. Existing synthetic M0–M7 and M8 regressions remain passing.

| Acceptance requirement | Status | Evidence / limit |
|---|---|---|
| Deterministic versioned method, stable ties and reproducibility | PASS | Pure Decimal service, 26 new backend tests, four actual saved replay checks. |
| Transparent policies, factor separation and missing-data safety | PASS | Strict objectives/weights, null unranked states, explicit contributions/unknowns; no silent redistribution. |
| Use available official condition and declared estimates without inventing unsupported factors | PASS (software) | Existing eligibility/replay reused; missing class/traffic/work benefit unweighted and visible. |
| Dashboard/Map ranking, search/filter/compare and explanations | PASS (bounded verification) | Shared panel tests and actual two-road browser save/compare/map navigation. |
| Sensitivity and immutable snapshots, no GET/AI numerical writes | PASS | Frozen alternative policies, deterministic rank-change output, read-only replay and regression tests. |
| Migration and synthetic preservation | PASS (bounded verification) | Additive schema/backup/rollback tests; isolated actual copy; original database fingerprints unchanged. Large-production restore rehearsal not performed. |
| Positive real maintenance ranking from verified eligible road conditions | BLOCKED | Actual QA universe has 0 eligible road-wide conditions. Simulated test ratings are not field evidence. |
| Independently reviewed municipal weights/constraints and road-specific cost applicability | BLOCKED | Only agent technical-QA policies/estimates used. Authorized human policy/engineering/procurement review remains required. |

No confirmed failed requirement is relabeled as PASS. Full positive evidence/approval acceptance remains incomplete; software completion does not imply municipal readiness.

## Migration, recovery, files and remaining work

Stop application writers before an explicitly requested production migration. Use a new private backup path and `app.migrate --target-version 11`; the default remains 7 and startup does not migrate. Verify backup/schema/FKs/old logical content before activating any new DB. On failure the transaction rolls back. For recovery, stop writers, restore the verified backup to a **new** path, verify its prior schema/data and select it explicitly; do not destructively downgrade, overwrite originals, delete saved inputs or reseed. A schema-10 recovery can serve historical features while prioritization persistence reports unavailable.

New modules: backend `schemas/prioritization.py`, `services/prioritization.py`, `core/prioritization_repository.py`, `routes/prioritization.py`; frontend `types/prioritization.ts`, `services/prioritization.ts`, `features/priorities/RoadPriorities.tsx`; respective tests; `scripts/verify_m8_4.py`; this report and verification JSON. Integration changes: API main/migrate/migrations, existing official Overview/Map and map CSS. Shared changes: README, MVP_ROADMAP, M8_IMPLEMENTATION_PLAN, PRODUCT_SPEC, DATA_MODEL, API_SPEC, ARCHITECTURE, DATA_SOURCES, AI_SYSTEM, RESPONSIBLE_AI, KNOWN_LIMITATIONS. Preexisting unrelated edits retained.

Remaining decisions/evidence: obtain accepted whole-road condition coverage; have an authorized municipality review weights/objective/horizons and any supplied cost/constraint basis; separately establish functional class, independently sourced traffic/disruption or actual construction evidence before adding numerical factors under a new reviewed method version. Do not infer these from street name, feature type, permits or AI. Resolve earlier M8.1–M8.3 gates separately. No citywide optimization, budget allocation, treatment recommendation, automatic approval, schedule, new traffic feed or M8.5 feature was implemented. No commit, push, deploy, dependency installation or original runtime activation occurred.
