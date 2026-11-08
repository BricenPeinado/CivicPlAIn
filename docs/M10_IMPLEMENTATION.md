# M10 — Interactive construction planning and conflict visualization

Implemented locally **2026-11-08**. **Status: Complete for the bounded interactive software milestone.** Earlier M8 source, engineering and release gates remain open. No municipal construction verification, approval or production readiness is implied.

## Delivered interactions

- Select an existing official street and choose **Plan construction**. With no existing declaration, this explicit action creates zone A and enters drawing mode. It clears only the viewed screening/alternative/finding route pins, retaining the street and all saved records. An existing draft is retained. **Open construction screening** also opens the existing tool without creating inputs or calculations.
- Click the existing MapLibre canvas to define an EPSG:4326 LineString. Preview follows the pointer; vertices remain visible. Finish, undo, cancel, edit by appending/undoing vertices, remove alignment and remove work are supported. Cancel preserves the previously committed alignment. Native map keyboard shortcuts: Enter finishes, Backspace/Delete undoes, Escape cancels. A disclosed longitude/latitude form provides keyboard coordinate entry.
- The simplified editor supports two hypothetical zones with distinct purple/teal overlays, titles, work types, linked road references, proposed work dates, optional closure dates, geometry certainty, grade and Yes/No/Unknown excavation declarations. Work author/date/rationale may override the explicitly attributed shared basis. Populated declarations retain that basis; unknown fields stay unknown. Thresholds start blank.
- Proposed dates are half-open `[start,end)` civil dates, with `start < end`; closure intervals must lie within work intervals. Neither dates nor geometry come from permit administrative fields. Selecting a street links its ID only. Drawing always commits approximate certainty; a later declared choice remains independently unverified.
- **Create alternative schedule** copies the two currently supplied schedules into editable dates. Up to two alternatives are available in the simple editor. Complete JSON work/alternative/cost inputs remain under **Advanced inputs**, retaining the existing API limits (30 works, three alternatives). Advanced declarations override form works; form overlays are hidden until a validated response supplies their actual geometry.
- **Analyze construction conflicts** validates and previews through the existing engine. It does not save. The result shows findings, the two submitted alignments, indeterminate checks, missing evidence, utility/depth unknowns and required human review. **Inspect … on map** focuses submitted finding geometry without replacing the selected street or saved record identity.
- A compact comparison table shows actual returned original/alternative dates, finding counts, indeterminate counts, supported same-scope cost totals or Unknown, and mandatory human review. Added/removed finding types and activity pairs are compared by semantic identity, rather than unstable finding hashes. Fewer findings imply neither optimality nor feasibility, savings or safety.
- **Save immutable screening** explicitly invokes the existing save endpoint. Saved route IDs and alternative selection replay with GET after reload. Loading a result never replaces input drafts. Saved inputs remain inspectable under frozen lineage; importing/cloning a saved run into a fresh editor is not added.
- **Explain planning tradeoffs** is available only for a saved result. It calls the existing replay-validated decision explanation endpoint, defaulting to deterministic/no-key mode. Existing optional AI selection/fallback remains available. The deterministic comparison stays in the UI; model authority and evidence projection are unchanged.

## State, validation and map boundary

Drafts, preview/saved-result state and unfinished drawing sessions are retained separately per snapshot in browser memory across ordinary tool/view/mode navigation. Discard requires **Keep editing** or **Discard changes**. Browser reload/close warns for unsaved cached drafts or unfinished drawing where supported. This is session memory, not durable draft storage; after an intentional reload only explicitly saved results are restored.

Drawing uses 2–500 distinct finite longitude/latitude points inside the intersection of the pinned snapshot coverage and the existing map bounds `[-74.030,40.695,-73.980,40.730]`. Invalid/incomplete/out-of-bounds drawing cannot be committed. The server remains authoritative for geometry topology, references, declared-road disagreement, provenance, policy limits and replay. Geographic selection/matching rules are unchanged.

All feature-click handlers consult the current drawing state; street/rating/observation/permit/project selection is suppressed during drawing. Map instance and independent GeoJSON sources are reused: work zones, temporary line/vertices, selected finding and selected investigation street remain separate. Closing the panel clears overlays/callbacks while retaining drafts. Snapshot changes remount the map and clear context-bound overlays. Initial camera fitting now respects a supplied route camera before publishing a default viewport.

Obsolete requests abort on edited inputs, replacement requests or unmount; every asynchronous write to UI checks its signal. Failed requests preserve inputs and show a retryable error. Preview/save/explanation remain explicit actions; editing, navigation and panning never initiate calculation or AI audit writes. The existing service timeout remains 15 seconds; no automatic save/retry or refresh is introduced.

Desktop retains the existing inspector-column planning panel. Mobile uses a scrollable lower sheet while retaining the map above it. Forms disclose optional evidence/closures and advanced JSON. A textual map legend and findings list supplement color; the comparison fits the narrow panel and remains a keyboard-focusable table region.

## Existing architecture and APIs reused

No backend code, schema, algorithm, migration, dependencies, rates, source artifacts or historical payloads changed.

- `OfficialMapPage`, `RoadMap`, map GeoJSON sources and existing official snapshot/route machinery.
- `officialScreening.ts`: `POST /api/v2/planning/conflict-analyses/preview`, explicit `POST /planning/conflict-analyses`, snapshot-pinned GET history/replay, existing append-only human notes.
- `schemas/official_screening.py` and `services/official_screening.py`: unchanged `official-screen-v1`, proximity/overlap, half-open timing, reopening horizon, uncertainty and schedule override rules.
- `decisionSupport.ts`: existing `POST /api/v2/planning/decision-support/explanations`; unchanged scalar projection, selection-only model authority, citations/audit and deterministic fallback. No API credential setup or external provider call was required.
- Existing SQLite schema 12 and immutable repositories. All browser writes were confined to a new ignored QA copy.

## Run the verified local pair

This checkout has the already imported and migrated official database and standardized artifact. The QA copy was created using SQLite backup from a read-only source; nothing was migrated, reseeded or rebuilt. From the repository root:

```sh
CIVICPLAIN_DATABASE_PATH="$PWD/data/tmp/m10-interactive-qa.sqlite3" \
CIVICPLAIN_STANDARDIZED_DATABASE_PATH="$PWD/data/processed/CivicPlAIn_standardized.sqlite3" \
CIVICPLAIN_DATA_MODE=official \
CIVICPLAIN_OFFICIAL_SNAPSHOT_ID=nyc-4620b9e30c1c0bd5be4252fe27999c80 \
CIVICPLAIN_AI_PROVIDER=deterministic \
CIVICPLAIN_ALLOWED_ORIGINS=http://127.0.0.1:5200 \
PYTHONPATH=apps/api .venv/bin/python -m uvicorn app.main:app \
  --host 127.0.0.1 --port 8100 --no-access-log
```

In another terminal:

```sh
VITE_API_BASE_URL=http://127.0.0.1:8100/api/v1 \
VITE_MUNICIPAL_API_BASE_URL=http://127.0.0.1:8100/api/v2 \
VITE_BASEMAP=local npm run dev --prefix apps/web -- --port 5200
```

Open [White Street in the local map](http://127.0.0.1:5200/#/map?mode=official&snapshot=nyc-4620b9e30c1c0bd5be4252fe27999c80&road=road-0003cbb8adbb7e90987b689e). Both URLs must target this matching API/frontend pair. Existing 8099/5199 servers were left untouched; refresh alone cannot upgrade their backend process. Local basemap mode requires no external tile requests. Stop only these new processes with Ctrl+C when finished; the ignored QA database remains available.

Other installations must select their own already reviewed snapshot and explicitly migrated database using existing setup documentation. Do not copy these IDs into an unrelated database or run ingestion/migration just to render this interface.

## Exact workflow to exercise

1. Open the White Street link, or select/search any loaded official street. Choose **Plan construction**; draw two points along a short part of the selected blue street. Choose **Finish alignment**.
2. Title zone A “Hypothetical resurfacing”; select Resurfacing. Supply proposed dates **2027-01-01** through **2027-01-10**. These are exercise assumptions, not actual NYC schedules.
3. Choose **Add hypothetical work**, draw a nearby overlapping alignment on the same street, and finish. Title zone B “Hypothetical excavation”; select Excavation. Supply **2027-01-05** through **2027-01-12**. Leave grade/excavation evidence explicitly Unknown unless deliberately supplying an attributed assumption.
4. Choose **Create alternative schedule**. Change A to **2027-03-01** through **2027-03-10**; leave B at its original dates. Optional closures stay blank.
5. Enter an author, date entered, and rationale explicitly describing these hypothetical assumptions. Supply proximity **10 m** and reopening horizon **30 days** as exercise planning assumptions, not engineering/safety thresholds.
6. Choose **Analyze construction conflicts**. Inspect findings on the map. Compare original and alternative rows; review missing grade/depth and utility coverage. If your drawn geometry disagrees with its road reference or lies beyond the proximity threshold, the result can instead be indeterminate or show no findings; inspect the reported evidence rather than assuming the exercise counts.
7. Choose **Save immutable screening**. Use **Explain planning tradeoffs** with deterministic mode. Select the alternative in **Schedule comparison**; retain the qualified zero-finding language. Reload the saved URL to verify read-only replay.
8. To revise current-session inputs, expand **Enter or revise explicit planning assumptions**. Navigate to Overview and back; the draft is retained. Discard requires an explicit inline choice. A fresh reload does not clone saved inputs into a new draft.

## Actual verification

| Executed check | Result |
|---|---|
| `PYTHONPATH=apps/api .venv/bin/python -m pytest apps/api/tests -q` | **509 passed**, 344 existing library deprecation warnings, 26.61s |
| `npm test --prefix apps/web -- --reporter=dot` | **178 passed / 28 files**; 6.41s in the final complete run |
| `npm run typecheck --prefix apps/web` | PASS |
| `npm run build --prefix apps/web` | PASS; existing MapLibre large-chunk advisory remains |
| `git diff --check` | PASS |
| Preexisting database/fixture fingerprints | **35 / 35 files unchanged**, including the standardized SQLite artifact |

New automated cases cover finite/bounds/order/count geometry validation, preview vertices, map click routing and suppression of every ordinary selection path, undo/cancel/edit/removal, keyboard shortcuts and listener cleanup, proposed date ordering/closure containment, required attribution, unknown vs explicit excavation declarations, alternative payloads and calculated comparisons, unsupported costs, zero-finding wording, preview/save separation, stale preview/saved requests, failure input retention, keep/discard, per-snapshot draft/drawing isolation and remount retention, missing pinned alternatives, explicit saved explanation/fallback and pinned-camera initialization. Frontend transport/map mocks make no real planning-engine or external tile requests. Full backend regressions retain actual deterministic calculation/replay/boundary/fallback coverage; no duplicate frontend engine was introduced.

Actual Chrome verification used newly launched **8100/5200**, the pinned official base above and `data/tmp/m10-interactive-qa.sqlite3`:

- Selected actual White Street and drew both alignments through canvas clicks. No JSON was used. Browser native date segments were entered with keyboard; the automation's date `fill()` did not enter complete dates and was replaced with native segment entry.
- Original supplied dates returned **2 findings** (concurrent work and resurfacing coordination), **1 indeterminate pair**. Alternative A in March returned **0 findings / 1 indeterminate pair**. Cost remained Unknown. These are agent-authored hypothetical QA declarations, not actual municipal work.
- Finding inspection fitted both supplied zones while preserving selected street; save produced `screen-1c9605a6fb5b822ef30244843837f6f414cb7e90986d719a7ea7944144fd4b62`. Reload retrieved the same saved record/results/alternative. Explicit deterministic explanation returned exact 2/0 finding counts, 1/1 indeterminate counts, mandatory unknowns and a separate audit.
- Unsaved title survived Map → Overview → Map. Keep editing retained it; explicit discard cleared only session state. Synthetic mode still displayed 24 fixtures, selected `demo-r-001` and its existing repair/advisor actions. Full synthetic scenario behavior was regression-tested rather than manually replaying every historical action.
- Desktop and **390×844** mobile inspected. Fixed a mobile sheet containing-block error; final mobile panel was x=0/y≈396.69/width=390/height≈359.31 with page width/scroll width both 390. This is bounded usability evidence, not screen-reader/accessibility certification.
- Source database had 2 screenings/3 notes/6 AI interactions. QA copy after the single explicit save/explanation had 3 screenings/3 notes/7 interactions. Navigating/reloading did not create another screening or audit. Original hashes remained unchanged.

## Responsible AI and remaining limits

All math stays server-side in `official-screen-v1`; no AI scheduling optimizer, new projection, inferred utility, traffic/cost predictor or construction approval was added. Only the existing saved-result scalar projection reaches an optional provider; source prose, drawn geometry, author/rationale and notes remain outside model authority. UI comparison can state deterministic added/removed findings even when the explanation projection lacks a specific cross-alternative statement.

LineString drawing is the basic workflow. Polygon JSON remains advanced; no polygon drawing, vertex dragging, snapping, road-centerline copying or measured-footprint claim. Geometry may be approximate and road-reference disagreement can make checks indeterminate. Shared provenance is an explicit planner declaration, not separately verified evidence for each field. Unsaved drafts do not survive a full browser restart. Saved runs replay read-only; fresh editor import/cloning is not implemented. Optional provider/network operation was not newly smoke-tested; existing failure regressions and deterministic browser output were verified. Existing source gates, utility unknowns, unauthenticated local-only operation, MapLibre bundle size and M9 initial large-viewport latency remain.

## Files changed

- `apps/web/src/features/screening/OfficialScreening.tsx`
- `apps/web/src/features/screening/PlanningForms.tsx` (new)
- `apps/web/src/features/screening/planningDraft.ts` (new)
- `apps/web/src/features/screening/ScheduleComparison.tsx` (new)
- `apps/web/src/features/screening/OfficialScreening.test.tsx`
- `apps/web/src/features/screening/planningDraft.test.ts` (new)
- `apps/web/src/features/map/RoadMap.tsx`
- `apps/web/src/features/map/RoadMap.test.tsx`
- `apps/web/src/pages/OfficialMapPage.tsx`
- `apps/web/src/pages/OfficialMapPage.test.tsx`
- `apps/web/src/styles/map.css`
- `README.md`, `docs/MVP_ROADMAP.md`, `docs/PRODUCT_SPEC.md`, `docs/DATA_MODEL.md`, `docs/API_SPEC.md`, `docs/ARCHITECTURE.md`, and this report.

Next separately authorized work: resolve earlier source/engineering/release gates or improve durable draft editing/accessibility/performance. No subsequent milestone, commit, push or deployment was performed.
