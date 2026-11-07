# Milestone 3 implementation and verification

Completed locally on 2026-11-07 on `feat/m3-conflict-detection`. The initial tree was clean. No commit, push, deployment, M4 scenario optimization or M5 generative AI was performed. Existing IDE files and the M1/M2 fixture bytes were preserved.

## Result

The existing modular monolith now persists seven fictional work projects, links multi-road scopes, screens projected spatial and civil-date evidence, saves immutable reproducible analyses/findings, and exposes project layers and an accessible conflict review panel in the existing map. All current project geometry, organizations, lane closures, excavation assumptions and dates are synthetic. The default 5 m footprint/5 m centerline-corridor/30-day review parameters produce **8 findings and 10 incomplete pair checks**, examining **16 candidate pairs of 21 possible pairs**.

The core example pairs fictional R-001 resurfacing `[2027-04-01,2027-04-08)` with fictional water excavation `[2027-04-10,2027-04-15)`: positive supplied polygon overlap, shared R-001 and a **2-day gap** yield potential pavement rework requiring human scope/schedule review. Concurrent sewer work overlaps the resurfacing on `[2027-04-05,2027-04-08)` and supplies the multiple-closure example. A nearby nonintersecting water inspection, unrelated telecom inspection, unknown-location gas project and unknown-schedule electric project exercise potential, separated and indeterminate cases.

## Contracts, assumptions and architecture decisions

- WorkProject extends the existing model conventions with title/description, category/type/organization/status, planned/actual dates, approximate/unknown geometry, road references, nullable cost/excavation/closures, timestamps and field-level provenance. Current imports are synthetic only. Unknown values stay null with reasons. A future observed adapter requires reviewed evidence support.
- Geometry exchange is EPSG:4326 longitude/latitude; local **pyproj 3.7.2** transforms to **EPSG:32618 meters**. This is the only new direct dependency. Shapely/GEOS supplies validation, distance, intersection and STRtree. Polygon rings must close; invalid topology, nonfinite values, reversed intervals and out-of-study work zones are rejected without repair. M3 work zones must lie wholly inside the bounded study window; existing road-import behavior is unchanged.
- STRtree supplies proximity candidates and footprint-to-road corridor membership. Inverted road memberships add declared shared-road pairs; unknown footprints pair explicitly with active projects. Dense/shared-road/unknown inputs may still require quadratic candidate counts. No citywide performance result is claimed.
- Positive supplied polygon area overlap, shared roads, centerline-corridor proximity and missing location are distinct evidence fields. Approximate geometry receives potential classification even when the supplied polygons overlap. A 1e-7 m roundoff epsilon handles projection threshold equality only; it is not location accuracy. No pavement width or underground depth is derived from centerlines.
- Civil dates use America/New_York half-open `[start,end)` intervals; adjacency is not overlap. Sequential gap 0–30 days is included by default, day 31 excluded. Concurrent work, multiple closures, potential reopening and general sequencing review have explicit deterministic rules. Completed work uses actual dates only and can precede sequential work; cancelled records are explicitly excluded.
- Every priority is `coordination_review`, without validated safety significance. Possible rework requires affirmative excavation or excavation type not explicitly negated; other nearby sequential work gets sequencing review. No repeat-restoration action, monetary loss, savings, traffic delay, safe deferral or project approval is manufactured.
- Missing location/schedule produces warnings and separate indeterminate checks. Known shared-road findings can coexist with incomplete footprints. No number of findings establishes utility coverage; it stays unknown.
- Input snapshots freeze complete projects, roads, source contents, parameters, method and library versions. Canonical M2 JSON hashing supplies stable analysis/finding IDs. Result hashes exclude detection time. Repeated identical requests reuse the first saved record/time; changed inputs or parameters create distinct history. Replay is verified within the recorded runtime, not promised across arbitrary library versions.
- Additive schema version 3 adds work_projects, project_roads, conflict_analyses and conflict_findings plus indexes and immutability triggers. Existing road JSON and immutable estimates are unchanged. Seed validates checksums/identities/references and preserves existing project payloads/links.
- The former planned `/conflicts/check` draft is replaced by implemented `/conflicts/analyze`. Utility scope fields live on WorkProject; no duplicate UtilityWork table/transport model was introduced. General AuditEvent and review-note workflows remain M5 work. These contract reconciliations are documented in DATA_MODEL/API_SPEC/ARCHITECTURE/roadmap.

## Implemented REST boundary

All use `/api/v1`, existing validated envelopes/errors, local CORS and no provider key.

| Method | Path | Actual behavior |
| --- | --- | --- |
| GET | `/projects` | Stable-ID list; road_segment_id/kind/schedule_status filters and limit/cursor |
| GET | `/projects/{id}` | Project with schedule/location uncertainty and provenance |
| POST | `/conflicts/analyze` | Validated explicit scope of 1–50 projects; persisted immutable analysis/findings |
| GET | `/conflicts` | Saved findings; project_id/road_segment_id/analysis_id filters and limit/cursor |
| GET | `/conflicts/{id}` | Saved finding with evidence and analysis reference |
| GET | `/conflict-analyses/{id}` | Complete saved input/source snapshot, output and hashes |

Unknown references return 404; incompatible snapshots or unavailable evidence return 409; malformed inputs, parameters or mismatched cursors return sanitized 422; SQLite failure retains 503 handling. Valid no-match filters return empty arrays with coverage warnings. GET does not recalculate. Distinct historical analyses may retain the same pair under different source/parameter snapshots; analysis_id selects one version.

## Frontend and actual browser checks

The API-backed map has project polygon/line layers, category controls, master visibility, project selection, project details, finding selection and related-road highlights. Textual category labels, dashed work-zone outlines, thick selected outlines, warning symbols and selected text supplement color. Projects without geometry remain selectable through the keyboard list. Layer visibility only changes presentation; it does not hide analytical warnings or narrow the saved scope. Project/road filters and Show all conflicts control review selection. Evidence includes dates, spatial facts, schedule source, unknown fields, source contents, method/tolerances and required human review.

Browser verification used isolated loopback API/web servers on **8001/5174**, preserving pre-existing user processes. It exercised the actual API-backed map, selected the potential-rework finding, visually inspected thick work-zone/road highlights, switched the master project layer off/on, toggled the water category, selected the road project (four findings), and selected the unrelated telecom project (zero findings with incomplete-coverage wording and an unknown-location pair check). Keyboard Enter selected R-001; its existing assessment/provenance and repair-option cards remained available with **$53,400 base / $44,760 low / $66,360 high**, five preliminary days.

A 390×844 mobile viewport exposed inherited nowrap text overflowing the page. M3 styles now wrap the method/legend text; the recheck measured **390 px document width at 390 px viewport width**, with readable stacked project/review content. The viewport override was reset. Final code was reloaded against a fresh isolated database, the two-day-gap evidence was inspected again, and browser error logs were empty. Temporary verification servers were stopped; their frontend exit 130 is the intentional Ctrl+C stop. Existing user servers were left untouched.

Ignored proof artifacts: `data/tmp/m3-map-highlight.jpg` and `data/tmp/m3-conflict-review.jpg`. These are local verification screenshots, not municipal data. Browser checks do not constitute full accessibility certification, cross-browser testing or production-bundle browser testing. The production bundle was built successfully; the browser used Vite development mode.

## Executed commands and actual outcomes

| Command/check | Outcome |
| --- | --- |
| Baseline `PYTHONPATH=apps/api .venv/bin/python -m pytest apps/api/tests -q` | **53 passed** |
| Baseline `npm test --prefix apps/web` | **22 passed** |
| Final `PYTHONPATH=apps/api .venv/bin/python -m pytest apps/api/tests -q` | **93 passed**, one existing Starlette/httpx deprecation warning |
| Final `npm test --prefix apps/web` | **32 passed**, five suites |
| `npm run typecheck --prefix apps/web` | Passed; production build repeats typecheck |
| `npm run build --prefix apps/web` | Passed; existing MapLibre chunk-size advisory remains |
| `.venv/bin/python -m pip install 'pyproj==3.7.2'` | Installed after sandbox network retry with authorized escalation |
| `.venv/bin/python -m pip check` | No broken requirements; sandbox cache warning only |
| `git switch -c feat/m3-conflict-detection` | Succeeded after sandbox Git-metadata retry with authorized escalation |
| `python3 scripts/create_m3_fixture.py` with before/after SHA-256 assertion | Fixture and manifest regenerated byte-identically |
| Explicit `python -m app.seed` in isolated verification databases | 24 roads, M2 (5,26,3), 7 M3 projects |
| Additive seed against the ordinary local demo database | 24 roads, M2 (5,26,3), 7 projects; existing road/estimate rows byte-identical before/after; foreign_key_check empty |
| `git diff --check` | Passed |
| README/docs relative Markdown-link validation | Passed |
| Lint | Not run: no lint script is configured |
| M4/M5, live municipal data, paid AI calls, deployment | Not performed |

During integration, the old M2 test's exact migration-version expectation failed after additive version 3 was introduced; it now verifies both retained version 2 and added version 3. Initial frontend integration exposed a MapLibre expression type error and missing project API mocks in existing App tests; both were corrected. The mobile overflow above was fixed. No final check remains failing. Sandbox port binding initially failed, then the loopback verification servers started successfully with authorized escalation; this was an environment restriction, not a claimed passing run.

Backend coverage includes polygon overlap/separation, same-road unknown footprints, nearby nonintersecting zones, exact meter thresholds, shared corridor and line-crossing ambiguity, overlapping/adjacent dates, 0/30/31-day sequencing boundaries, missing dates/location, actual/completed and cancelled handling, multi-road and multiple-project scopes, invalid geometry/schedules/status/cost/units, deterministic input-order stability, saved-input replay, changed source/project/parameters creating distinct history, duplicate prevention, provenance preservation and transitive synthetic-source labeling, immutable storage, repeated seed/local edits, checksum/manifest rejection, pagination/cross-filter/endpoint cursor rejection, empty datasets, HTTP errors/restart persistence, and exact existing estimate API arithmetic. All M1/M2 tests remain included.

Frontend coverage includes existing map/list/estimate behavior, source-backed project fetching, analysis POST/retrieval paths, pagination/duplicates, project/finding keyboard selection, map-source layer toggles and multi-project/road filters, displayed schedules/sources/unknowns/human review, selected-road/project filtering, qualified zero findings, independent failure/retry and snapshot mismatch rejection.

## Acceptance and remaining limits

All fourteen requested M3 definition-of-done items are implemented and locally verified: persisted projects; mapped zones; road/utility comparison; spatial and temporal screening; sequential rework review; missing-data warnings; deterministic explanations; working APIs; review UI; fictional demo examples; M1/M2 regressions; passing checks; updated documentation. The ordinary local demo is seeded; restart any pre-existing API process to load M3 code. README contains the same local start/stop commands.

No unresolved M3 implementation blocker remains. Limitations: this is a bounded ≤50-project, ≤30-road local prototype; broad road/corridor references, grade separation, approximate zones, stale/permit schedules and unlisted projects can cause false positives/negatives. Utilities, coverage, depth, actual excavation and engineering feasibility are unverified. No MultiPolygon/general observed ingestion, project editing, project date-range filter, global optimizer, review-note submission, generic audit-event lifecycle or generative provider is implemented. No production security, citywide performance or calibrated spatial/safety accuracy is claimed. Existing dependency deprecation/build advisories are nonblocking.

The next milestone is **M4 — budget-aware scenario comparison**, not started. It must retain these immutable source snapshots, require explicit restoration/cost assumptions and avoid inferring damage or safe deferral from a finding.

## Exact changed-file inventory

Modified:

- `README.md`
- `apps/api/app/main.py`
- `apps/api/app/models/database.py`
- `apps/api/app/seed.py`
- `apps/api/requirements.in`
- `apps/api/requirements.txt`
- `apps/api/tests/test_planning.py`
- `apps/web/src/App.test.tsx`
- `apps/web/src/App.tsx`
- `apps/web/src/features/map/RoadMap.test.tsx`
- `apps/web/src/features/map/RoadMap.tsx`
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

- `apps/api/app/core/conflict_repository.py`
- `apps/api/app/routes/conflicts.py`
- `apps/api/app/schemas/conflicts.py`
- `apps/api/app/seed_m3.py`
- `apps/api/app/services/conflicts.py`
- `apps/api/tests/test_conflicts.py`
- `apps/web/src/features/conflicts/ConflictReview.test.tsx`
- `apps/web/src/features/conflicts/ConflictReview.tsx`
- `apps/web/src/features/conflicts/testData.ts`
- `apps/web/src/features/conflicts/useConflicts.ts`
- `data/demo/projects-manifest.json`
- `data/demo/projects.json`
- `docs/M3_IMPLEMENTATION.md`
- `scripts/create_m3_fixture.py`
