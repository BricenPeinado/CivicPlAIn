# M7.3 — Dashboard and application navigation

Implemented locally on 2026-11-07. M0–M6 functionality and M7.1–M7.2 source/map boundaries are retained. M7.4 comprehensive polish/accessibility remains next. No dependency installation, database migration, fixture rewrite, deployment, commit or push was performed.

## Delivered behavior

The application has four named destinations, with Map as the entry point:

| Destination | Purpose and actual behavior |
| --- | --- |
| Overview | Whole-snapshot street-row, inspection and administrative-permit counts; condition categories and dated accepted-road denominator; exact raw permit statuses; available issue-date range; source retrieval/cadence; investigation links and expandable provenance. It does not load WebGL or derive metrics from the current map page. |
| Infrastructure map | Existing M7.2 MapLibre workspace, independent layers and one inspector. Official street search/category filter, camera extent and layer choices persist in the URL. Selection and supported permit-location links use actual source geometry or an accepted road reference. |
| Projects & coordination | Official permits: snapshot-wide text search, exact source-status and all/matched/ambiguous/unmatched/unlocated filters, explicit pagination, independently fetched selected detail and evidence. Accepted road links and unconfirmed candidate-road investigation links are distinct. Synthetic projects: explicit all-loaded-project deterministic screening, saved-analysis restoration, selected project/finding evidence and direct affected-road/planner actions. |
| Scenario planner | Existing synthetic plans/revisions, explicit Create/Edit, one editor/result/comparison workspace, lazy paginated evaluation history, explicit project inclusion, save/evaluate and 2–3 saved latest-evaluation comparison, evidence advisor and review tools. Official mode explains missing prerequisites and offers an explicit synthetic context switch. |

Initial real snapshot remains `nyc-3947b35876a619b31067db96b1409ad8`: 4,150 LION export rows, 8,726 dated observations, 4,735 permit scope candidates. Street SegmentID is not a unique row count. All initial pavement associations are ambiguous, accepted links are zero, categories unsupported/unknown, and all permits are unmatched/unlocated. These are imported coverage facts, not zero poor streets, zero construction or zero conflicts. Exact acquisition/source evidence remains in [M7_1_IMPLEMENTATION](M7_1_IMPLEMENTATION.md); it was not reacquired or reinterpreted for this milestone.

Overview investigation items point to ambiguous observation lines, unlocated permits and unknown utility coverage. It does not invent recommendations, scores, budgets, costs, traffic, schedules or activity trends. Source cadence/retrieval is displayed without a stale/fresh threshold. Permit issuance/status/validity never establishes that work started or identifies a confirmed construction interval. Official permits are not converted into WorkProject inputs.

## Navigation contract and state ownership

Retain the tested dependency-free hash router. `#/map`, `#/dashboard`, `#/projects`, `#/scenarios` are canonical; `#/overview` is an accepted Overview alias. Existing M7.2 links remain valid. Named links support Back/Forward and refresh without a server-side history fallback.

| Optional parameter | Meaning / validation |
| --- | --- |
| mode, snapshot | Explicit official/synthetic context; official immutable `nyc-` plus 32 lowercase hexadecimal characters. Snapshot is serialized only for official mode. |
| road | Selected road identifier. |
| permit, mappermit | Independent Projects detail and Map permit inspection IDs. Following a related road can retain Projects detail without reopening a permit inspector. |
| project, finding, analysis | Synthetic review selection and immutable saved-analysis ID; GET restores saved analysis with snapshot checks. Selection filters review/highlights, not screening input scope. |
| scenario, evaluation | Saved synthetic plan/evaluation IDs; GET restoration only. Unsaved authored fields are never URL parameters. |
| mapq, permitq, status | Separate bounded search text and exact raw permit status; 1–100 characters, nonblank, no control characters. Empty UI filters omit the parameter. |
| location | all, matched, ambiguous, unmatched or unlocated. |
| condition | good, fair, poor or unknown, applied to official road viewport and search queries. Current pilot is all unknown. |
| bbox | Four finite ordered WGS84 west/south/east/north values within the presentation guard [-74.06,40.67,-73.95,40.76]. This guard is not an ingestion boundary or spatial matching tolerance. The map retains its narrower M7.2 navigation bounds. |
| layers | Unique comma-separated streets, conditions, permits, shoreline, basemap keys, or `none`. |

IDs permit letters/digits/underscore/dot/colon/hyphen and at most 180 characters. Unknown, repeated, empty or malformed parameters show a correction state. Backend record identity and snapshot checks remain authoritative; parsing a syntactically valid ID does not prove membership.

App owns the route and remembers context separately by mode/official snapshot. Deliberate navigation, feature selection and enumerated filters create history entries. Typing and camera updates replace the current entry to avoid a history entry per keystroke/pan. Camera restoration fits saved bounds without extra padding; fresh selected-road framing uses a presentation margin. Floating-point differences and aspect-ratio changes can adjust the resulting bounds; no source coordinates are altered.

SyntheticWorkspace stays mounted once visited, with its original context while hidden. Planner mounts on first actual synthetic visit. Form values, review/estimate state, comparisons and pending writes remain in that workspace across ordinary view/mode changes; nothing is copied to official records. Hidden write responses update the remembered synthetic route rather than the visible official URL. Invalid-route correction also retains the mounted synthetic editor. Pending calculation writes are never automatically retried.

Opening another saved plan or Create scenario while dirty shows **Keep editing** / **Discard editor changes and continue**. Keep restores the current editor's link; explicit discard replaces only that editor. A linked evaluation for another scenario is deferred until the editor replacement is accepted, then verified against scenario/snapshot. Linked result reads have loading/error states and do not display a prior result as the requested one. Reload/close uses native dirty/busy beforeunload where supported. No localStorage, auto-save or crash-recovery guarantee is introduced.

Transient disclosures, list-open state, inspection selection, synthetic map camera/category visibility and comparison selections/results are not serialized. Comparisons remain in the mounted synthetic workspace; URL refresh is not a saved comparison deep link.

## Backend and API decisions

One existing FastAPI/SQLite application; no new endpoint or service. The only backend behavior addition is the existing GET `/api/v2/dashboard` derivation `municipal-summary-2`:

- `permit_status_counts`: exact raw nullable status buckets as `{status,count}` rows; null is distinct from the source string `"null"`.
- `permit_issue_date_range`: min/max known issued_at values, or null. Permit validity dates never substitute for missing issue dates.
- `source_freshness`: source revision ID/source ID, retrieved_at, nullable source_updated_at, cadence and release_note copied from frozen revisions.

All existing fields, v1 routes, calculation versions, deterministic services and immutable record identities remain compatible. No table, trigger or saved JSON changed. Older summaries without additive fields show unavailable status/freshness detail rather than invented zero values. Full contracts are updated in [API_SPEC](API_SPEC.md) and [DATA_MODEL](DATA_MODEL.md).

Existing GET `/api/v2/permits/{id}` now supports independent linked detail in the client. Selected detail can remain outside the filtered list; the scope caption explains this. Changed filters abort/restart list pagination, cancel stale reads and retain detail. Load more deduplicates IDs. Unsupported locations have explanatory text instead of an inferred pin. Mobile selected details hide filters/list until Back to permit list.

Synthetic histories use the existing GET `/api/v1/scenarios/{id}/evaluations?limit=30&offset=...` contract on demand; no eager per-scenario history requests at list entry. History requests are independently cancelled and checked against scenario/source context. Older pages can be loaded into the history selector. Comparisons continue calling the backend; money, timing, risk and conflict calculations are not implemented in React.

## File-by-file delivery

Paths below are repository relative. Existing modules are extended instead of adding the unused page/shell abstractions in the original 7.0 proposal.

| Files | Change |
| --- | --- |
| `apps/web/src/App.tsx`, `routing.ts` | Purposeful destination names; validated shareable state; context memories; history/focus handling; protected hidden synthetic workspace and pending-write route reconciliation. |
| `pages/OfficialRecordsPage.tsx` | Source-backed overview, status/location/text filters, independent permit detail, accepted/candidate map links, local loading/error/retry/empty states and mobile detail focus. |
| `pages/OfficialMapPage.tsx`, `features/map/RoadMap.tsx`, `hooks/useMunicipalData.ts` | Restore official search/layers/bounds/permit inspection; category-scoped road reads/search; preserve selected-road and camera context without changing source geometry. |
| `pages/SyntheticWorkspace.tsx`, `features/conflicts/ConflictReview.tsx`, `useConflicts.ts` | Restore saved analysis through GET; related road/project/finding/planner actions; explicit screening scope, missing selection/context errors; preserve existing overlays, indeterminate checks and advisor. |
| `features/scenarios/ScenarioPlanner.tsx` | Deliberate editor/result/comparison; on-demand paginated histories; linked saved-result checks; dirty replacement guard; project inclusion action; existing optimistic revisions, hypothetical normalization and backend computation retained. |
| `services/api.ts`, `services/municipal.ts`, `types/municipal.ts` | Existing history pagination query; independently verified permit detail; optional additive summary DTO fields; category-aware viewport transport. |
| `styles/views.css`, `styles.css` | Scoped overview/status/source-table/filter/action/disclosure styles and responsive mobile detail layout using existing tokens. |
| `apps/api/app/core/municipal_repository.py` | Additive summary fields and method version; no model/schema/domain-engine mutation. |
| `apps/web/src/Navigation.test.tsx`, `routing.test.ts`, `services/municipal.test.ts` | Full App cross-view integration, URL round-trip/validation, stale reads, failure paths, snapshot/identity/synthetic boundary. MapLibre alone is mocked in navigation tests; actual planner/advisor components run against mocked REST. |
| `App.test.tsx`, `features/scenarios/ScenarioPlanner.test.tsx`, `features/ai/AIAdvisor.test.tsx`, feature `testData.ts` files | Adapt interactions to renamed destinations/lazy history; retain original numerical/unknown/immutable-result assertions. Extract existing authored test DTOs for reuse, without changing data/demo fixtures. Add dirty linked-plan replacement, mismatched saved result and older-history cases. |
| `apps/api/tests/test_m7_api.py` | Exact status/date/freshness provenance semantics and existing filter compatibility. |
| `README.md`, `AGENTS.md`, shared M7 specs and this report | Current behavior/contracts, delivered-vs-planned scope, commands, limitations and next gate. Historical M0–M6/M7.1/M7.2 reports untouched. |

No changes to RepairPlanner calculations, ScenarioResults math, AI provider/grounding safeguards, ingestion adapters, schemas, migration code, package manifests/locks or reviewed synthetic fixtures.

## Acceptance and verification

Commands run from repository root:

```sh
npm run test --prefix apps/web
npm run typecheck --prefix apps/web
npm run build --prefix apps/web
PYTHONPATH=apps/api .venv/bin/python -m pytest apps/api/tests -q
git diff --check
```

Final results: **95 frontend tests across 14 files; 266 backend tests; TypeScript and production build pass**. Build runs typecheck too. Backend retains 73 existing Starlette/httpx and Shapely transform deprecation warnings. Vite retains the MapLibre >500 kB chunk advisory (about 1,072 kB raw plus local 519 kB worker; scenario bundle about 38 kB); no unrelated dependency upgrade. No lint script exists. Local Markdown links and diff were checked separately.

| Acceptance | Evidence |
| --- | --- |
| Overview distinct from Map; authoritative counts and unknowns | Navigation test enters directly at official Overview, verifies no map region; server summary test checks exact status and frozen source metadata, including null issue range despite known validity dates. Read-failure test verifies error/retry and absence of fabricated zero cards. |
| Official investigation → permit → road → return | Full App test follows unlocated filter, independent permit detail, explicit unconfirmed road link, accepted-condition unknown and retained permit/filter on return. No analysis/scenario/AI writes. Actual browser exercised unlocated permit detail and exact EXPIRED status link. |
| Stable shareable navigation | Route parser tests round-trip record/filter/layer/camera state and reject invalid parameters. App integration restores map search/layers/camera through Back; existing tests retain selected road/context and draft checks. Actual browser Back restored Wall Street and camera/layers. |
| Supported synthetic cross-view workflow | Full App test selects road, explicitly screens, inspects finding evidence, follows affected road, selects project and starts a scenario; inputs persist across Overview; explicit inclusion/save/evaluate calls the existing backend contract, displays $53,400 test evaluation and invokes evidence-grounded fallback only on action. |
| Saved records and incomplete checks preserved | Original estimate/conflict/scenario/AI tests and all backend regressions remain passing; saved-analysis GET restores evidence, mismatch fails closed without POST. Saved evaluation links reject wrong scenario/source context. |
| Avoid accidental draft replacement | Tests cover ordinary navigation preservation, explicit Keep/Discard, deferred linked-plan/evaluation replacement, optimistic revision failure, frozen old evaluation and older paged histories without replacing draft. Full App integration also resolves a pending synthetic revision while official mode is visible, verifies the official URL stays unchanged and restores the saved revision on return. Actual browser retained unsaved name/assumptions across Overview and official/synthetic switch; Keep editing protected it. |
| Cancellation and failure handling | Independent late permit reads cannot replace a newer ID; selected detail survives changed filters. Existing map/source/WebGL/cursor failure tests remain. Snapshot/synthetic/identity checks cover independently linked permit reads. |
| Backend-only computation | No frontend calculation implementation; tests assert no navigation-triggered mutations and exact explicit POST arguments. Existing deterministic/replay regression suite passes. |

### Actual browser procedure and boundaries

Used the host's in-app Chromium/WebGL browser against an agent-owned loopback API on 8001 and Vite dev frontend on 5174, `VITE_BASEMAP=local`. A new ignored `data/tmp/m73-browser.sqlite3` was created with SQLite backup from the existing ignored M7.1 pilot; all test writes went to that copy. The original pilot and user database were not used as write targets. API configured with CIVICPLAIN_DATABASE_PATH pointing to the copy, CIVICPLAIN_DATA_MODE=official, the explicit pin above and CIVICPLAIN_ALLOWED_ORIGINS=http://127.0.0.1:5174. Frontend API bases point to the same test process's `/api/v1` and `/api/v2`. No external tiles, source refresh or paid provider call was needed.

Desktop 1280×720: source-backed overview counts; unlocated-filter investigation; permit source values, unknown location and absence of map pin; Wall Street search/selection; pavement layer toggle; Overview → browser Back restores street/search/layers/geographic extent; Projects retains permit; official planner capability gate; synthetic saved A/B comparison displays unchanged $53,400 base, $44,760 low and $66,360 high per plan and qualified timing; unsaved draft/name/assumptions persist across views/mode switches; Keep editing guard; saved revision 2 of an existing plan; prior immutable revision-1 evaluation remains inspectable; explicit deterministic advisor explanation still cites revision 1.

Mobile 390×844: named bottom navigation, permit selected detail/back with filters hidden, and Overview; document width equals scroll width (390), no page-level horizontal overflow in those checked states. Source/comparison tables retain their existing local scroll containers. Viewport override was reset and the temporary browser tab closed. Agent-owned servers were stopped after verification; preexisting user servers were left alone. Local proof image: `/private/tmp/civicplain-m73-overview.jpg` (temporary artifact, not a tracked repository asset).

Initial browser connection failed because the test launch used the wrong CORS variable; corrected to the repository's CIVICPLAIN_ALLOWED_ORIGINS and verified the explicit retry succeeded. Browser automation's date fill did not reliably update controlled React date state, so no successful new-draft browser save/evaluation is claimed. New-draft save/evaluation remains covered by frontend integration and backend tests; actual browser revision saving used a preexisting plan's supplied dates. No application date-input workaround was added solely for the automation behavior.

## Remaining limits and next milestone

M7.4 owns full contrast/screen-reader/200% zoom/reduced-motion/cross-browser and wider responsive/performance checks. This milestone's tests and two browser sizes are not accessibility certification or a citywide latency guarantee. Official viewport/record reads retain the M7.2 cap and pagination; dense historical inspection reads can be slow. No citywide spatial server rewrite is introduced.

Editor preservation lasts for the current application lifetime. Full restart/crash can lose unsaved input despite native warnings; no persistent draft service exists. Synthetic camera/project-layer visibility and transient comparison/disclosure/list state are not deep links. Comparison selection uses loaded latest evaluations; older evaluation inspection is supported, arbitrary older-version comparison selection is not new scope. V1 scenario-list bounds remain unchanged.

The initial data still cannot support accepted road categories, located permits, official conflict analysis, costs, construction schedules or official scenario/AI execution. Enabling those requires reviewed matches/inputs and a separately versioned source-neutral calculation gate. No source quality issue is hidden by the redesigned navigation. See [KNOWN_LIMITATIONS](KNOWN_LIMITATIONS.md).
