# M8.5 — Official-Data Construction Conflict and Coordination Screening

Implemented/verified **2026-11-08**. Status: **software gate PASS; positive independently documented actual-work evidence gate BLOCKED**. Stop at M8.5. No M8.6, project approval, work order, spending authorization, optimization or excavation clearance.

## Baseline and authorized scope

Reviewed the actual local branch `bp/specify-civicplain-milestone-7`, status, AGENTS/README, milestone/shared contracts, M8.1–M8.4 implementation, M3 `conflicts`, synthetic schemas and M4 `hypothetical` adapter, M8.2 permit intelligence, M8.3 estimate replay and M8.4 immutable repository/migration conventions. Preserved extensive preexisting uncommitted work; no remote replacement, reset, commit or push. Baseline executed: **459 backend tests / 122 frontend tests passed**.

The latest explicit M8.5 request moves original A6 official construction screening into this stage. Earlier source/acceptance blockers remain open; independently authorized implementation is not retroactive source approval. General official scenario CRUD/evaluation remains future. Original M3 synthetic DTOs require synthetic/bounded source semantics, so official records are not coerced into them. Reuse is at the pure mathematical boundary: M3 projection/metric roundoff constant and extracted shared half-open `overlap_bounds`; the old engine calls the same unchanged max-start/min-end operation. Existing v1 validators, stored snapshots and fixture semantics remain intact.

## Evidence contract and adapter

Method/request: **`official-screen-v1`**. All policy thresholds are explicit with attributed evidence: proximity 0–100 metres and rework horizon integer 0–365 days; no default municipality-wide tolerance or horizon. They are planning assumptions, not source positional accuracy or safety thresholds.

A run pins one official base, up to 30 supplied works, up to 30 distinct selected/linked administrative permits, optional exact reviewed permit release, up to three named schedule alternatives and optional same-scope cost assumptions. Supplied work includes ID/title/type, its own provenance, optional referenced roads/permits, EPSG:4326 geometry and certainty, schedule, grade, excavation requirement/depth and closure envelope. All populated grade/excavation/depth fields require their own provenance. Unknown fields remain null/unknown; no centerline buffering, utility inference, inferred calendar or synthetic price substitution.

- `planning_assumption`: authored date/rationale; numerical values or geometry are explicitly supplied, not source observations.
- `supplied_document`: author/date/rationale plus at least one structured citation (title, URL, dates, locator, applicability/limits). It remains **independently unverified**. Citations are not fetched, authenticated or promoted to official observation status.
- Imported roads/permits/sources retain exact IDs, classifications, raw checksums/attributes, release/review/candidate lineage and dates. Synthetic-origin imports are rejected by the production adapter. Synthetic test fixtures use a visibly explicit test-only bypass for storage tests; they do not establish actual coverage.

Road references resolve only inside the exact base. A supplied geometry far from any of its declared road references is marked `DECLARED_GEOMETRY_DISAGREES_WITH_ROAD_REFERENCE`; it is not used as a usable work footprint. Multiple/candidate permit references remain visible and unconfirmed. Even a reviewed permit road reference is a partial administrative reference, **never a work footprint**. The adapter freezes the full imported road matching universe, selected permits, existing candidate algorithm/parameters, exact accepted/rejected associations and release to reproduce ambiguity detection.

Permit entries always have **null work geometry and schedule**, retaining issue/effective/expiration dates and source status separately as `administrative_dates`. Raw WKT is not interpreted as a work zone; its existing CRS caveat remains. A permit linked to a supplied work declaration does not validate the latter's geometry or dates. No fictional persistent project is created from a permit.

## Deterministic screening rules

All bounded selected pairs are checked (at most 60 entries, 1,770 pairs), including missing-location pairs. No candidate index is used to erase unknown checks. Outputs separate per-activity unknowns, per-pair checks, findings, administrative evidence and snapshot-wide missing coverage.

Geometry is topology/finite-coordinate validated without repair, constrained to the pinned base's coverage bbox, then projected with existing EPSG:32618 logic. The M3 roundoff epsilon is `1e-7` m, solely for numerical projection boundaries. Exact computed 2D intersection and positive polygon area overlap are reported separately from proximity (distance ≤ explicit threshold + epsilon). Reported distances round to six decimal places; predicates use unrounded distances. There is no claimed centimetre/survey accuracy.

Dates are explicit strict `YYYY-MM-DD` civil dates, half-open `[start,end)`; same-day end/start is adjacency, not concurrency. Missing schedule prevents date-dependent findings. A closure requires its own interval/provenance within the supplied work envelope; overlapping work envelopes alone do not establish multiple closures.

| Check/finding | Required evidence and interpretation |
|---|---|
| Spatial overlap | Both usable supplied geometries; exact 2D intersection/area overlap is computed. Shared roads alone never establish overlap. |
| Temporal overlap / `concurrent_work` | Two usable geometries within threshold and two explicit overlapping work intervals. Supports a relation between supplied plans, not actual simultaneous activity. |
| `multiple_closure_plans` | Above plus explicitly overlapping closure intervals. No inferred lane count, capacity or observed closure. |
| `resurfacing_coordination` | Concurrent supplied plan includes declared resurfacing. Suitability, damage or actual excavation not inferred. |
| `potential_pavement_rework` | Declared resurfacing ends before explicitly declared required excavation begins; gap 0..horizon inclusive, usable nearby shapes. Merely naming excavation is insufficient without `excavation_required=true` and provenance. |
| `adjacent_work_coordination` | Other spatially related sequential work within the horizon; generic opportunity, no shared mobilization discount or avoided loss. |
| Different declared grades | Suppress interference/closure/rework findings; report `grade_separated`. Declaration is not field verification/clearance. |
| Unknown grade | Checks remain indeterminate; any date/spatial finding is a qualified **potential coordination opportunity**, not supported physical interference. |
| Missing/conflicting footprint or schedule | Indeterminate checks; road names, permit validity and candidate links do not fill gaps. |

A `supported_conflict_finding` requires usable intersecting supplied shapes, same explicitly declared grade, declared (not approximate) certainty, required explicit dates and applicable rule. Even this label means **supported by supplied evidence only**, with `evidence_status=supplied_evidence_only_not_independently_verified` and mandatory human review. Approximate/proximity/unknown-grade relations are potential opportunities. Depth relation and physical interference remain unknown/unverified; the engine does not conclude that buried assets collide or do not collide. Relevant missing checks can coexist with qualified findings.

Findings are stable content hashes of method/parameters/pair evidence/kind. Sorted IDs and complete bounded pairs prevent duplicate findings and input-order dependence. Method, Shapely/GEOS/pyproj/PROJ versions and full frozen inputs persist; incompatible runtime replay fails closed rather than silently updating output. No wall-clock date or AI generates numerical results.

## Alternatives, comparable costs and human review

Named alternatives override only known work schedules/closure intervals, retaining identical work/permit scope. Every override is validated as a complete half-open interval; omitted closure explicitly becomes unknown, not retained silently. Alternative output includes the same unknown coverage and separate hashes. Finding-count differences are not optimized outcomes, safety improvements or monetary savings.

Optional cost comparison explicitly chooses one saved M8.3 estimate/treatment on the same base and declared work road. Its full frozen input/road/scope/result replays before use. Every alternative uses the **same estimate, quantity, scope, exclusions and cost basis**. Each schedule requires its own nonnegative USD addition, evidence and explicit same-scope/nonoverlap declaration; no hidden zero additions. Differences are the alternative addition minus base addition, rounded per declared line to cents with existing Decimal `ROUND_HALF_UP`, precision 40. No traffic delay, damage, shared mobilization, life expectancy or rework loss is manufactured. Missing selections/assumptions mean cost comparison unavailable. The declaration is not independently verified procurement/engineering approval.

Separate append-only review notes reference the saved run/optional base-or-alternative finding. Author/text/disposition (`needs_review`, `reviewed_with_limitations`, `dismissed_for_planning`) are human assertions, not authenticated official approval. Notes neither mutate the frozen result nor create a project/work order. Identical note content is idempotent. Users should avoid sensitive data in this local unauthenticated prototype.

## API, persistence and map

Existing v2 municipal envelopes are extended through `/planning/conflict-analyses`: explicit POST preview (no write), POST save/recalculate (201/200 idempotent), snapshot-bound GET history/detail, and separate GET/POST notes. Unknown/repeated query fields and invalid DTOs fail validation. Foreign references return 404; invalid topology/CRS/interval/provenance/units/unsupported treatment fail 422; missing explicit persistence schema returns 503; integrity/runtime/replay failure returns 409. GET/navigation/replay never creates a new run, evaluation, project or AI audit.

Schema **12**, `m8-official-screening-v1`, adds immutable `official_screenings`, separate immutable `official_screening_notes`, foreign keys and indexes. Complete canonical input/source/road/permit/release/estimate snapshots and result hashes are saved; identity `screen-<input_hash>`. Created/review times are storage metadata, not source work dates or calculation inputs. No original import/synthetic table or payload rewrite, new dependency, automatic migration/activation or startup refresh.

Map → **Open construction screening** exposes blank numeric policy inputs; attributable hypothetical work forms; independent permit search/selection; optional advanced cited work/alternative/cost contracts; explicit preview/save/history; finding filters/inspection; alternative selector; full source/unknown/check details and review-note actions. Input changes invalidate prior results/overlays and abort requests. Per-snapshot session drafts are retained; discard/unload protection is available. Loading saved results preserves the input draft and explicitly identifies frozen inputs. Numerical rules stay server-side.

Selected findings draw only usable supplied geometry as dashed orange shapes with an explicit assumption/field-verification caveat, alongside related road inspection. Unlocated/candidate permits receive no fictional footprint. Overlay selection clears on changed inputs/alternatives/history or snapshot changes. Keyboard-accessible finding lists and JSON evidence remain available without relying on color. General official scenario workflows are not introduced.

## Actual pinned-data QA and limitations

Original M7, M8.1, M8.2, M8.3 and M8.4 pilot files were fingerprinted before work. A new ignored SQLite backup copy, `data/tmp/m85-screening-pilot.sqlite3`, was explicitly migrated **11→12**, with new verified backup `data/tmp/m85-before-schema12.sqlite3`. Legacy logical fingerprint: `74a052b7fb9efe6a1c609d0f8c68aadcdd2a3a69c3ba7e7c5191f83db179e9a1`. Original files remain unchanged; no existing runtime was activated/migrated.

Pinned base `nyc-4620b9e30c1c0bd5be4252fe27999c80`: 4,150 road rows / 23,047 permits. QA selects one actual WHITE STREET row and two actual permits: **1/2 candidate (50%)**, **1/2 unlocated (50%)**, **0/2 accepted work footprints or schedules (0%)**. Selection is explicit technical QA, not a random/citywide sample; 2/23,047 records (about 0.0087%) cannot establish overall conflict coverage or match precision. No new real construction/utility feed was obtained or independently verified.

Two API saved runs:

1. `screen-8f64d5c10a1d1d6602693ff40ddec6c04c15c630f07ff770ce2b4f57f569e610`: two **agent-authored hypothetical** work declarations aligned to an actual road reference, two selected permits. Resurfacing assumed 2027-01-01–10, excavation assumed 2027-01-12–15; approximate geometry, unknown grade/depth. **1 qualified potential-rework opportunity, 0 supported actual-work conflicts, 6/6 indeterminate pairs**. Alternative assumed roadwork 2027-03-01–10 has **0 findings / 6 indeterminate pairs**, retaining coverage warnings. These dates are QA assumptions, not a verified construction schedule.
2. `screen-0f83edc2c87ef78a821bc6954b8360e16f56b99bf1b5d1ed8ad23e2fc387e54b`: same two administrative records only. **0 findings, 1/1 indeterminate pair**, zero promoted footprints/schedules; cost unavailable.

Same frozen M8.3 technical-QA estimate in the first run: USD **20.10** for its declared test scope, with **explicit QA zero additions in each schedule**, difference **USD 0.00**. This tests comparability/replay, not NYC pricing or a complete actual project budget. It does not establish a monetary benefit from changing dates. No independently reviewed actual quantity/price/work policy was supplied.

Read-only verification instructions (new output path required):

```sh
PYTHONPATH=apps/api .venv/bin/python scripts/verify_m8_5.py \
  --database data/tmp/m85-screening-pilot.sqlite3 \
  --snapshot nyc-4620b9e30c1c0bd5be4252fe27999c80 \
  --report data/processed/m85-verification-new.json
```

[verification/m8.5-screening-qa.json](verification/m8.5-screening-qa.json) records run/input/result/alternative hashes, counts, costs and notes. It reports technical QA only; hashes are not independent approval. Final verification hash: `d81ccff4ac6294e6ad1261a7424f9411f570a943c1db11132e0b2bbfd7442dde`. Both runs replay with exact pinned evidence; three separate technical review notes (two API, one browser) validate their run/finding references and content identities. Actual replay requires the ignored pinned DB; raw government records/geometries are not redistributed in the report. The verifier reads original pinned import/source/estimate equality, SQLite integrity/FKs, replay and review references/hash identity.

## Validation and acceptance

Browser verification: opened blank-threshold screening form, loaded exact saved history, inspected a qualified finding and dashed supplied geometry on the actual WHITE STREET map, switched to an alternative with zero findings / six indeterminate pairs, and recorded a separate finding-bound technical review note without changing the saved run. Cold-load map verification confirmed the work layer remains visible above blue road selection; a regression covers layer order/clearing. Related street-evidence requests timed out during load and showed unavailable/retry; retry restored the inspector. This existing large-pilot read latency is not certified away. Proof screenshot: ignored `data/tmp/m85-screening-map.png`. Automated frontend tests mock transport/map and make no actual planning or tile calls. Mobile/accessibility/concurrent-load performance was not comprehensively audited.

Documentation consistency: Markdown fences, **158 local links**, aggregate report JSON and `git diff --check` passed. Demo fixtures, dependency lockfiles/requirements and all five prior runtime DB byte fingerprints remain unchanged. Local QA servers/tab were stopped/closed after verification. Initial loopback server starts were sandbox-blocked; approved loopback-only runs used the new isolated DB and local basemap. No external deployment or source refresh occurred.

Executed baseline: backend 459 passed, frontend 122 passed. Current full suite: `PYTHONPATH=apps/api .venv/bin/python -m pytest apps/api/tests -q` → **495 passed, 316 library deprecation warnings, 27.47s**. `npm test --prefix apps/web` → **131 passed / 21 files, 9.34s**. `npm run build --prefix apps/web` → TypeScript and build **PASS**, existing large-bundle warning remains. New targeted tests: **36 backend / 9 frontend**. An initial new frontend fixture had a syntax error, corrected before passing checks; an initial typecheck was run from the root without its app prefix, then corrected.

New tests cover overlapping/adjacent dates, metre thresholds 4.999/5/5.001, true line crossings with separate grades, unknown grade, missing schedule/geometry/depth, conflicting declared locations, multiple candidate/unlocated permits, known spatial separation despite shared long-road references, closure envelopes, duplicate finding IDs, 0/30/31-day rework horizons, all-indeterminate/no-finding coverage, schedule alternatives, Decimal cost additions/rounding, frozen replay/version failure, synthetic-origin rejection, idempotence/atomic storage, notes/triggers/foreign context, and migration preservation/rollback from schemas 0/7/8/9/10/11. Existing synthetic M3/M4/M5 and M8.1–M8.4 regressions pass. No AI provider, network data call, external tile or official planning call is used in automated frontend tests.

| Gate | Status | Evidence / remaining limit |
|---|---|---|
| Validated source-neutral adapter with separate facts/assumptions/candidates | PASS | Strict DTOs, immutable pinned adapter, actual two-permit retention and source-origin rejection. |
| Deterministic spatial/date/rework/closure/adjacent-work rules | PASS (software) | Boundary tests and real-road hypothetical QA; no assertion that actual work occurs. |
| Indeterminate checks, zero-result coverage and no-clearance behavior | PASS | Unknown/crossing tests; both actual-data runs retain missing coverage. |
| Same-scope assumption cost differences or explicit unavailable states | PASS (software) | Decimal tests, replay-verified common actual-road QA estimate and explicit additions. |
| Map inspection, alternatives, source details and separate human notes | PASS (bounded verification) | Frontend tests and local browser workflow; no comprehensive mobile/concurrency certification. |
| Immutable replay, atomic schema/backup/recovery and v1 preservation | PASS (bounded verification) | Full regressions, six migration starting-state rollback tests, isolated copy and read-only replay/preservation checks. Full production restore drill not performed. |
| Positive independently documented actual-work conflict with verified footprint/schedule/grade | BLOCKED | Current permits are administrative; no independently verified actual project/utility coverage supplied. Agent QA declarations do not pass this gate. |
| Independent review of policy thresholds, actual scope, schedule and procurement assumptions | BLOCKED | Attributed QA authors/notes are not authorized municipal/engineering approval. |

Full evidence acceptance is not complete. No blocked criterion is weakened to claim a verified municipal conflict or source coverage.

## Recovery, files and exact next steps

With writers stopped, use explicit `app.migrate --target-version 12` on the intended database and a new private backup path. Check backup, all old schema/rows, integrity/FKs before selecting any migrated DB. Default remains schema 7; API startup never migrates. Transaction failure rolls back. Recovery: stop writers, restore a verified backup to a **new** path, validate prior schema/content and select it explicitly. Do not overwrite user data, reseed, downgrade destructively or delete immutable results/notes. Earlier-schema recovery preserves earlier features and reports screening persistence unavailable.

New files: `apps/api/app/schemas/official_screening.py`, `services/official_screening.py`, `services/screening_math.py`, `core/official_screening_repository.py`, `routes/official_screening.py`, `tests/test_m8_screening.py`; frontend `types/officialScreening.ts`, `services/officialScreening.ts` and tests, `features/screening/OfficialScreening.tsx` and tests; `scripts/verify_m8_5.py`, this report and aggregate QA JSON. Integration edits: API main/migrate/migrations, M3 shared interval operation, existing official Map/RoadMap and scoped CSS. Shared contracts updated: README, roadmap/M8 plan, PRODUCT_SPEC, DATA_MODEL, API_SPEC, ARCHITECTURE, DATA_SOURCES, RESPONSIBLE_AI, AI_SYSTEM, KNOWN_LIMITATIONS. Preexisting changes retained.

Remaining decisions: obtain independently documented work footprints and actual/explicitly reviewed planned schedules, grade and relevant excavation scope from responsible organizations; review their source applicability and permit relationships without assuming a buried asset; independently review policy thresholds and any cost additions/comparable scope. Missing utility inventory/depth remains unknown even after better project coverage. Resolve earlier M8 source/estimate/policy gates separately. M8.6 scenarios, autonomous approval/work orders, utility-clearance analysis, damage/savings models, traffic optimization and source refresh remain outside this milestone.
