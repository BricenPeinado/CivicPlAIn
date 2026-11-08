# M8.6 — Product Integration, Decision Workflows and Responsible AI

Implementation/verification: **2026-11-08**. **Integration software gate PASS (bounded local verification); earlier positive municipal-source and independent-review gates remain BLOCKED.** No M8.7 work, production deployment or municipal authorization.

## Baseline and scope authority

Reviewed the actual local branch `bp/specify-civicplain-milestone-7`, Git/AGENTS/README, roadmap/shared contracts, M8.1–M8.5 reports, existing deterministic/saved-result/AI modules and M7 design system. Extensive existing uncommitted M8 work was retained. Fresh baseline: **495 backend / 131 frontend tests passed**. The remote branch was not substituted.

The latest explicit M8.6 request authorizes four-view product integration, supported saved-result comparisons and responsible explanations. Original plan A6's proposed general municipal scenario CRUD/optimistic evaluations remains **deferred, not passed**. Original broad M8.7 production recovery/performance certification is not claimed here. Earlier source/review blockers cannot be solved through UI integration.

Reuse: one existing React/Vite client, FastAPI REST modular monolith and SQLite; M7 navigation/tokens/responsive map/list; immutable snapshots/releases; M8.3 Decimal estimates, M8.4 priorities and M8.5 screening/alternatives/notes; existing selection-only AI service/provider/citation validation/fallback/audit. No parallel application/importer/engine, dependency installation, new migration, synthetic validator relaxation or automatic runtime activation.

## Delivered behavior

| Surface | Integration and evidence boundaries |
|---|---|
| Overview | Original import inventory/freshness remains labeled separately from selected-context eligible road/category/review coverage. Saved estimate/priority/screening counts are independent histories, not summed costs, projects or unique conflicts. Explicit selection shows replayed treatment totals/unknowns, qualified priority rows/policy sensitivity or screening findings/indeterminate coverage. |
| Map | Existing road-condition/history/unmatched observation layers remain intact. Selected priority tool adds purple dashed ranked vs gray dashed unranked road references within loaded geometry. Selected permit evidence can show brown dashed candidate road references, never work footprints. Supplied screening geometry stays dashed orange with uncertainty caption. Text legend and keyboard lists/details accompany colors. Tools share the existing inspector column/mobile sheet; street-list opening/Escape closes the active tool while preserving its draft. |
| Road inspector | Actual LION information, existing supported condition/history/date/lineage, on-demand accepted OR candidate permit references, selected saved priority and estimate details, treatment/rate sensitivity and exclusions. A selected estimate from another road fails context validation rather than pricing the newly selected road. No eligible condition, absent run membership or unsupported duration remains explicitly Unknown/unavailable. |
| Projects | Existing searchable administrative records/location confidence/source/issue/validity/status stay separate from actual schedules. A disclosure opens shared reviewed-planning context, qualified findings/alternative schedules and links to the existing human-note tool. Candidate road investigation can draw only loaded candidate reference lines and exposes the full candidate list. No permit becomes a project. |
| Scenarios | Existing synthetic scenarios remain unchanged in their own workspace. Official mode presents **within-result** M8.3 treatment/rate sensitivity, M8.4 same-universe policy alternatives and M8.5 same-work schedule alternatives/qualified same-scope costs. General official scenario evaluation/portfolio budgets/cross-run equal-benefit comparisons remain unavailable. No synthetic rates/projects appear automatically. |
| Grounded explanation | Explicit action on one saved result verifies/replays its existing frozen contract, projects allowlisted scalars, then uses the existing deterministic or optional selection-only provider. Exact saved amounts/counts/nulls, review requirements and source/input/result/projection hashes remain accessible. No source prose/geometry/notes/policy rationale/raw question reaches a model. |

Route context pins `estimate`, `priority`, `screening`, `tool`, `alternative`, plus existing base/road/finding/release/as-of/filter/camera fields. Strict identifier shapes, duplicate/unknown query rejection and snapshot-bound GET preserve Back/Forward/refresh/view/mode context. URL pinning selects existing immutable results; it is not new analysis persistence. No private rates, geometries or review text in URLs. Loading a saved result does not replace input drafts. An absent alternative/finding stays unavailable with no base overlay substitution. Cached tool state cannot overwrite a newly requested saved ID.

Large frozen JSON is rendered only when explicitly expanded. Projects planning context mounts on disclosure. Related permit candidate projection loads on request, separately from initial road/condition rendering. Selected-road legacy condition history now fetches only already-associated record IDs rather than validating every unrelated observation. These read optimizations preserve existing sorting/tie/unknown semantics and snapshot membership; no calculation version or historical result changed.

## Backend contracts and responsible AI

New read-only GET `/api/v2/planning/decision-support` requires exact `snapshot_id` and `as_of_date`, optional existing condition `release_id`/`policy_id`. `decision-context-v1` returns eligible/review counts, categories/reasons and per-kind saved metadata histories. First 100 summaries, explicit truncation; existing tool histories retain pagination. No latest-result selection, cross-run numerical aggregation or GET writes. Older schemas return partial unavailable/null histories, preserving source coverage.

Existing `/permits` adds `include_candidates=true` only with an explicit `road_id`; default accepted-only semantics remain. Enhanced evidence preserves statuses/ambiguity/release. No candidate promotion or inferred footprint/actual work date.

POST `/api/v2/planning/decision-support/explanations` accepts only base, saved kind/ID and deterministic/optional-AI mode. Reuses existing repositories' hash/replay checks. `official-scalar-projection-v1` maps to existing `ai-evidence-v1` (estimate/evaluation/conflict contexts), task `explain_official`, `source_classification=derived`; immutable frozen-input/result/method and projection hashes identify evidence. Static fact labels and verified deterministic result fields only. Raw source descriptions/titles, citation prose, contact information, work geometry, author/review notes and questions are excluded from provider evidence, while full source assumptions remain accessible locally from the saved result.

The provider can select IDs/templates only, never generate numerical claims or free prose. Existing exact-hash/citation/schema/caveat/recommendation validation applies; the server renders all material facts and mandatory unknowns. Default deterministic mode works with no key/network. Optional AI with no key returns `fallback/not_configured`; invalid numerical/prose/provider output falls back with reason. Audit failure fails closed through existing storage handling. Explicit POST alone appends existing minimal audit/evidence storage; GET/navigation never adds an interaction or run. No approval, spending, missing measurements, source fetch, work order, safety clearance or AI ranking.

## Actual pinned-data verification

Only a **new ignored copy**, `data/tmp/m86-integration-pilot.sqlite3`, was created using SQLite backup from M8.5 opened read-only. Existing schema **12** suffices; no migration or source/decision publication. Six previous pilot databases were fingerprinted before work and verified unchanged afterward. QA servers and temporary browser tabs were stopped/closed after verification. No original runtime selection changed. Existing services on ports 8000/5173 were left untouched; QA used explicit loopback 8086/5186 and the local basemap.

Pinned base: `nyc-4620b9e30c1c0bd5be4252fe27999c80`, reference date **2026-11-08**, original condition links (no implicit release):

- **4,150 road rows; 0 eligible whole-road assessments; 4,150 requiring evidence review; Good/Fair/Poor 0 each, Unknown 4,150.** This is evidence coverage, not a condition census or zero physical need.
- **2 saved estimate records, 4 priority runs, 2 screenings** replayed from their frozen inputs; no new planning result was created. They remain the previous agent-authored technical QA assumptions on actual roads, not independently reviewed municipal prices/policies/work plans.
- Selected WHITE STREET estimate: **USD 20.10** for its explicitly labeled hypothetical 20 m² technical QA scope; no claimed NYC rate applicability, missing duration/rate bounds. Explanation retained this exact amount and Unknown fields; optional-AI/no-key browser action returned deterministic fallback and one explicit audit in the isolated copy.
- Selected screening: **1 potential rework opportunity / 6 indeterminate pairs**; saved `roadwork-after` alternative **0 findings / 6 indeterminate pairs**. These are supplied hypothetical plans, not actual conflicts. Current permit coverage remains **0 accepted work footprints/actual schedules**; M8.2's 6,052 candidate and 16,995 unlocated records are not promoted by integration.
- The earlier five owner-reviewed partial pavement references belong to the earlier pinned pilot/release and are not transferred to this base. Observation grades never establish whole-road condition.

Aggregate replay evidence: [verification/m8.6-integration-qa.json](verification/m8.6-integration-qa.json). It includes saved input/result/explanation-evidence hashes, selected scoped results and unchanged storage counts. It contains no raw government geometries, invented positive coverage or independent approvals. Reproduce read-only with a **new** report path:

```sh
PYTHONPATH=apps/api .venv/bin/python scripts/verify_m8_6.py \
  --database data/tmp/m86-integration-pilot.sqlite3 \
  --snapshot nyc-4620b9e30c1c0bd5be4252fe27999c80 \
  --as-of 2026-11-08 --report data/processed/m86-verification-new.json
```

## Validation and acceptance

Executed commands and actual results:

- `PYTHONPATH=apps/api .venv/bin/python -m pytest apps/api/tests -q`: **503 passed / 341 library deprecation warnings, 30.08s**. Includes all synthetic M0–M7/M8 regressions and new integration coverage.
- `npm test --prefix apps/web`: **141 passed / 22 files**.
- `npm run typecheck --prefix apps/web`: **PASS**.
- `npm run build --prefix apps/web`: **PASS**; existing large MapLibre chunk advisory remains.
- Read-only pinned verifier: **8 saved records replayed**; no new result/review/audit from verifier; aggregate report hash retained in JSON.
- Markdown link/fence consistency, aggregate report hash, `git diff --check`, original pilot/fixture/dependency preservation: **PASS**.

New backend cases cover exact-context coverage, no GET writes, unknown categories, strict/foreign contexts, missing-schema partial behavior, explicit audit/no-key fallback, raw source-text injection exclusion, invalid provider numerical/prose fallback, accepted-or-candidate road filtering, and bounded history reads. New frontend cases cover shared context across four routes, explicit selection/explanation, unknown duration/sensitivity, unavailable/mismatched pinned context, missing ranking membership, missing schedule alternatives, retries, distinct overlay sources/styles, pinned finding/alternative restoration without computation, stale-overlay clearing and route validation. Existing fake provider timeout/citation/audit-failure and synthetic scenario/draft tests remain passing. Automated frontend tests mock transport/maps and make no real planning-engine or external tile calls.

Local in-app browser checks: Overview → saved estimate → Scenarios retained exact base/road/ID; explicit no-key fallback; saved screening base/alternative; finding link → map restored exact finding and supplied overlay; reload retained IDs; keyboard controls/list/Escape; source/unknown disclosures. Responsive bounds inspected at **390×844, 768×1024, 1280×720 and 1440×900**, no page horizontal overflow in inspected views. At 390 px, the planning sheet occupies about 53% of available workspace and leaves the map visible. Saved screenshots (ignored): `data/tmp/m86-map-integration.png`, `data/tmp/m86-mobile-integration.png`. This is bounded browser verification, not accessibility certification, full screen-reader/200%-zoom matrix or a production performance/restore audit.

Cold related-evidence/layer reads did hit the existing 10-second client deadline during concurrent large-pilot replay and exposed retry/unavailable states. On-demand permit matching, bounded history reads and lazy frozen JSON reduce avoidable work; no p95/throughput or citywide responsiveness guarantee is claimed. Complete runtime performance certification remains deferred to M8.7.

| Acceptance requirement | Status | Evidence / limit |
|---|---|---|
| Four-view integration of supported saved official capabilities | PASS | Shared decision context, explicit within-result alternatives, existing editors and regression/browser evidence. |
| Map/list/inspector provenance and distinct unknown/candidate/assumed states | PASS (bounded verification) | Separate layer sources/legends, linked typed records, keyboard list, road history and on-demand candidate evidence. |
| Snapshot/release/date/selection preservation without synthetic leakage or GET writes | PASS | Strict routes/context tests, replay verifier, existing protected synthetic drafts and write-free GET checks. |
| Deterministic/optional grounded explanation, injection handling and no-key path | PASS | Existing selection validator reused; new scalar projection/provider-attack/no-key tests and actual fallback browser evidence. |
| Loading/empty/partial/error, keyboard and responsive integration | PASS (bounded verification) | Component tests, mobile/tablet/laptop/desktop bounds and browser list/finding restoration; latency caveat retained. |
| Existing calculations, immutable results and original data preserved | PASS | Full regression suites, eight saved replays, no migration; prior DB/fixture/dependency checks. |
| Earlier positive verified condition/work/cost/policy source gates | BLOCKED (unchanged) | No new source or independent reviewer supplied; UI/agent QA cannot pass those gates. |
| General official scenario CRUD/evaluation, broad production performance/recovery certification | DEFERRED | No validated general contract; explicitly outside the latest bounded M8.6 request. Not marked passed. |

## Files, recovery and remaining decisions

Created: `apps/api/app/routes/decision_support.py`, `services/ai/official_evidence.py`, `tests/test_m8_decisions.py`; `apps/web/src/services/decisionSupport.ts`, `features/decisions/DecisionContext.tsx` and its tests; `scripts/verify_m8_6.py`; this report and aggregate QA JSON.

Integration edits: API main registration, shared AI schema/explanation task, existing municipal candidate/history reads; React App/routes, official Map/Overview/Projects, existing repair/priority/screening editors, PermitEvidence/RoadMap, scoped map CSS and affected navigation/routing/map/screening tests. Shared docs: README, MVP_ROADMAP, M8_IMPLEMENTATION_PLAN, PRODUCT_SPEC, DATA_MODEL, API_SPEC, ARCHITECTURE, AI_SYSTEM, RESPONSIBLE_AI, KNOWN_LIMITATIONS. Preexisting M8 work remains uncommitted and intact.

Recovery needs no new migration: stop only QA servers; preserve the new copy and separate audit; select the unchanged earlier database explicitly if desired. Do not overwrite originals, reset fixtures, drop immutable rows, reseed or downgrade. Earlier schema 7/10/11 remains readable with explicit unavailable later histories. Existing schema/backup/replay regressions cover prior migration behavior; no new restore drill was required or claimed.

Remaining human/source decisions: obtain applicable whole-road pavement evidence/classification policy, accepted permit/work location evidence and independently supported schedules/grade/scope; obtain planner-reviewed road quantities/prices and policy weights/thresholds. Missing utilities/depth remains Unknown. No new authorization is required merely to preserve these unknowns. General official scenarios and M8.7 final QA remain deferred; **stop at M8.6**.
