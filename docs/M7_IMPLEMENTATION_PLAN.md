# M7 implementation plan and architecture audit

**M7.0 audit/specification retained; M7.1–M7.3 implemented locally. M7.4 remains planned.** See [M7.3 delivered files and verification](M7_3_IMPLEMENTATION.md). See [M7.1 evidence](M7_1_IMPLEMENTATION.md) and [M7.2 evidence](M7_2_IMPLEMENTATION.md). The inspected-baseline table below describes the original M6 checkout; the stage plans describe intended work and must be read with the concrete delivery notes. No historical milestone report is rewritten.

## Scope and release gates

Goal: a professional map-first Lower Manhattan planning interface backed by reviewed real geographic data, with distinct Dashboard, Map, Projects and Scenarios views. Keep one existing React/Vite client → REST → FastAPI modular monolith → SQLite. Preserve deterministic calculation/AI boundaries and every saved record. Do not add tours, presentation scripts or judge UI. No dependency installation, migration, application feature, deployment, commit or push belongs to 7.0.

M7's real-data capabilities are **official geographic/condition/administrative inspection, source coverage and navigation**. Existing synthetic estimates, conflicts, scenarios, explanations and reviews remain functional in explicitly synthetic mode. Real-road costing/screening/scenario execution is gated by a future source-neutral calculation contract and reviewed planning inputs. No verified NYC construction-price/catalog or utility-schedule source exists in this audit. This is a deliberate bounded scope decision: real geometry must not inherit demo rates/projects or be mislabeled synthetic merely to satisfy existing validators. PRODUCT_SPEC owns this scope; DATA_MODEL/API_SPEC/ARCHITECTURE reflect it consistently. If real-data calculation execution is required within M7, expand those contracts and acceptance gates before coding that extension; do not quietly relax v1 literals.

Complete one stage at a time: 7.0 → 7.1 → 7.2 → 7.3 → 7.4. Within 7.1 track geometry, condition, permits and context separately. Geometry/context are mandatory for a recognizable real map; missing ratings/permits may be delivered as explicit unavailable states but make 7.1 partial until their payload/semantics gates pass. A source outage is not a successful zero-row import. Any adjusted stage scope must be recorded across roadmap/product/contracts, not disguised as completion.

## Inspected baseline and findings

Initial Git status was clean on `feat/m6-final-integration`. Read root instructions/README, roadmap, shared contracts, source/limitation/AI/responsibility documents; inspected historical milestone/demo/report structure and relevant compatibility evidence. Inventoried all tracked application/configuration/fixture/test modules and traced UI → transport → validation → SQL → deterministic engine → immutable snapshot/replay → AI projection. No branch change or user data rewrite was needed. IDE metadata was present and left intact. Static code inspection plus automated baseline checks informed the findings; no current UI screenshot/accessibility audit or real-data payload validation is claimed.

| Area / existing files | Observed architecture / risk for M7 |
| --- | --- |
| `apps/web/src/App.tsx`, `main.tsx`, `components/FeatureBoundary.tsx` | One App owns roads/detail/evidence, selection, search, two-name view state, project visibility and guide. Dashboard changes titles while rendering the same map/coordination/road-list workspace. Scenario planner is conditionally mounted above the map; navigation scrolls anchors. Lazy boundaries are useful and should stay. |
| `features/map/RoadMap.tsx`, `colors.ts`, map tests | Blank local MapLibre background + API synthetic lines/projects, hard-coded old bbox/center/labels and synthetic attribution. Worker bundled locally; stable IDs, separate highlight updates, cleanup, resize, WebGL failure behavior already covered. No street basemap, glyphs or actual shoreline exists. |
| `styles.css`, Vite/package/TS config | 1,058 lines of global selectors, original 6–12px labels and later overrides; pale green palette, stacked cards, fixed breakpoints and feature additions in one stylesheet. Tailwind is installed but most UI uses custom CSS. Keep existing build tooling; replace conflicting rules incrementally with tokens/scoped styles. |
| `features/estimates/RepairPlanner.tsx` and tests | API history/comparisons, optional dimensions, POST then GET estimate, source/hash breakdown and advisor. It assumes synthetic rates/labels. Reuse in synthetic view; do not pass a municipal DTO through a type cast. |
| `features/conflicts/ConflictReview.tsx`, `useConflicts.ts`, tests | List/evidence/layers share loaded projects. Hook POSTs analysis automatically after loading roads/projects; default dataset ≤50. Must separate explicit analysis from route/data loading; visibility is not checked scope. |
| `features/scenarios/ScenarioPlanner.tsx`, `ScenarioResults.tsx`, tests | Mutable draft held inside component, normalized synthetic assumptions, optimistic revisions, per-scenario history loads, only default newest 30 evaluations rendered, comparison and unknown metrics. Unmounting can lose unsaved edits. Lift draft state, retain advanced fields and paginate history deliberately. |
| `features/ai/*`, `types/ai.ts`, advisor/review tests | Bounded reference requests, cancellation, source focus, explicit human notes. Legacy labels/acknowledgement codes are synthetic. Do not extend to official records by changing strings; M7 official source inspector uses deterministic descriptions. |
| `services/api.ts`, transport tests, `types/api.ts`, `types/scenarios.ts` | Shared 10s request timeout/abort/error helper; v1 base; manual response checks; getRoads combines pages then rejects >30, getProjects rejects >50. Several TS types hard-code synthetic/true. New v2 client needs complete typed contract and isolated cache keys; preserve old tests/shapes. |
| `apps/api/app/main.py`, `core/config.py`, `http_limits.py`, routes | One app factory, configured repositories/provider, lifespan schema initialization, sanitized handlers, local CORS/origin/body limits. No auth. Startup currently catches schema init SQLite/OSError; v2 readiness must distinguish missing migration from loaded data. No remote-data fetching in routes. |
| `models/database.py`, repository modules | Standard sqlite3 connections/FKs, parameterized SQL, explicit write transactions; 20 existing tables through schema 5, immutable triggers for calculations/audits. RoadRepository.snapshot chooses first legacy dataset, count/list are global; per-road enrich queries are acceptable for 24 roads but wrong for mixed snapshots. Official sidecar repository avoids changing that universe. |
| `schemas/roads.py`, `planning.py`, `conflicts.py`, `scenarios.py`, `ai.py` | Road/Evidence/Assessment/catalog/calculations embed synthetic literals/scale/prefix. WorkProject permits observed structurally but still uses old bounding box; scenario freeze rejects observed projects. Exact field provenance and geometry/date validation are strengths to preserve. |
| `services/estimates.py`, `scenarios.py`, `scenario_identity.py`, `scenario_comparison.py` | Pure Decimal costing/quantity/calendar metrics, canonical source hashes/replay and comparison basis; M2/M4 share cost_scenarios. Suitability/warnings are explicitly demo-based. No real catalog/measurement adapter or global optimization. |
| `services/conflicts.py`, `hypothetical.py`, `core/scenario_inputs.py` | EPSG:32618 projection/STRtree, 5m screening assumptions, half-open dates, incomplete checks, exact source union, snapshots/library versions. Hypothetical adapter retains originals/replacements and never writes projects. Revalidates synthetic Road/Evidence, so official permit feeds cannot be sent into it unchanged. |
| `services/ai/evidence.py`, `providers.py`, `explanations.py`, `core/ai_repository.py`, AI routes | Typed reduced fact projection, hash/replay checks, provider selects IDs/templates, deterministic renderer/fallback, append-only audits/notes. Model has no tools/source mutation. Real-source ingestion, narrative and geometry must remain outside provider input. |
| `seed*.py`, `scripts/create_*_fixture.py`, `scripts/demo.py`, verify helpers | Four fixture/manifest pairs, stable IDs/checksums, explicit seeds; one synthetic snapshot per legacy DB. Scenario seed preserves edited drafts and appends evaluations. Startup helper creates retained isolated demo DB. Do not turn seed into an official updater or require a destructive reset. |
| `apps/api/tests/test_foundation.py`, `test_planning.py` | Geometry/provenance/cursor/error/config validation, transactional/idempotent seeds, cents math, missing inputs, assumptions, immutable estimates/replay. Keep numerical oracles and fixture bytes unchanged. |
| `test_conflicts.py`, `test_scenarios.py`, `test_ai.py`, `test_m6.py` | Spatial/date boundaries, unknowns/caps, deterministic canonical results, replacement/no-write, budgets/revisions/replay, source mutation, injection/provider/fallback/audit, integrated persistence and transport limits. These are the preservation gate, not evidence official import works. |
| Nine web test files, `test-setup.ts`, `vite.config.ts` | jsdom/Testing Library/Vitest API, map mocks, workspace selection/error/fallback, estimates/conflicts/scenarios/advisor/source focus and guide. Mocked WebGL does not establish real geography, layout, contrast or browser performance. Preserve assertions; adapt route-aware interaction paths only when UX changes. |
| `data/demo`, `data/raw`, `data/processed`, `.gitignore`, `.env.example`, dependency locks | Reviewed synthetic fixtures tracked; downloads/normalized/runtime DB/build outputs ignored. No official extract or provenance manifest exists. Secrets stay backend-only; no provider key required. No package/lock/env template changed in 7.0. |

Historical reports (FOUNDATION_INSPECTION, M1–M5 reports, M3_5_COMPATIBILITY, FINAL_QA_REPORT) and existing DEMO_PLAN/HACKATHON_DEMO/PRESENTATION_OUTLINE are retained unchanged. Their completion/performance/security statements refer to their original synthetic release. Current shared specifications distinguish delivered 7.0/7.1/7.2 from planned 7.3/7.4.

## Architecture and contract decisions

ARCHITECTURE records ADR-M7-01…07 with rationale/tradeoffs. Implementation follows those decisions:

1. Keep domain services, formulas, result hashes and old replay models intact; no synthetic-to-official ID mapping. Source-backed readings are not calculations.
2. Add source revision/snapshot/record/match tables in the same SQLite database through explicit schema migration 7; preserve legacy 20-table contents. Back up/verify/recover first. No runtime DB migration in 7.0.
3. Add snapshot-scoped `/api/v2` **read-only** routes; v1 remains legacy synthetic. Explicit context per tab/request, no mutable global “current snapshot”.
4. Explicit local source-specific ingest CLI with dry-run/approved manifest, bounded acquisition, quarantine, exact provenance, deterministic matching and atomic publication. No live background sync/URL HTTP mutation.
5. Six field classifications; separate observation/retrieval/release dates; distinguish administrative permits from physical WorkProject. Spatial/name candidates need review.
6. One React shell, four hash routes, shared feature modules and state; lazy MapLibre/editor, server aggregate counts and viewport/paged reads. No frontend domain calculator.
7. Local approved geographic context/labels/attribution; external outage does not trigger fixture substitution. No hosted basemap dependency is assumed. An extraction/font dependency needs evidence and review before addition.

## File-by-file execution plan

Paths are relative to repository root. The 7.1 table records the original coding plan; actual implemented files/combined adapter module and departures are enumerated in M7_1_IMPLEMENTATION. The original 7.2 table is reconciled by the delivered file map at the end; the original 7.3 table is reconciled by M7_3_IMPLEMENTATION; 7.4 paths remain proposed. Create a module only when its stage implements/uses it. Shared semantics belong in existing docs, not competing specification copies.

### 7.1 Official NYC ingestion and read boundary (implemented; original work plan below)

Dependencies: M7.0 contracts; retrieve exact official payloads/dictionaries/CRS/terms; settle source field mappings and identity grain. No implementation can truthfully predeclare those unresolved fields. First commit-sized work is payload/metadata verification and a mapping report, then typed adapters/migration/routes. No commit permission is implied.

| File | Planned change / review focus |
| --- | --- |
| `docs/DATA_SOURCES.md` | Replace candidate entries with exact observed payload/schema/terms evidence, retrieval dates, release/checksums, field maps and actual coverage/reject counts. Do not mark catalog-only verification as payload-ready. |
| `apps/api/app/schemas/municipal.py` (new) | Strict SourceRevision, DataSnapshot, six classifications/field lineage, road/assessment/permit/context/match/coverage/capability DTOs and DashboardSummary from DATA_MODEL/API_SPEC. Reuse base Schema/geometry primitives without altering synthetic validators. |
| `apps/api/app/ingestion/__init__.py`, `registry.py`, `acquire.py` (new) | Allowlisted resources/adapter protocol; bounded verified-HTTPS fetch/archive path validation; raw byte hashing and schema fingerprints. Standard-library/httpx first; no arbitrary user URL. |
| `apps/api/app/ingestion/lion.py`, `pavement.py`, `permits.py`, `context.py` (new) | Exact source-specific field mapping after verification, source key/revision grain, unit/date/CRS semantics, normalization and privacy allowlist. Tests cover documented field changes/duplicates. |
| `apps/api/app/services/municipal_data.py` (new) | Pure selection, transformations, candidate matching, reviewed-decision application, condition summary and deterministic aggregate definitions. No network/SQL/model imports. Store original and normalized values; don't duplicate conflict/estimate algorithms. |
| `apps/api/app/ingest.py` (new) | Explicit CLI stages acquire, dry-run/validate, publish using reviewed local manifest. Pin input/output paths safely, emit sanitized counts/codes, verify approvals/hash and publish transaction. Exact executable flags/help are 7.1 output, not commands that work today. |
| `apps/api/app/models/migrations.py` (new), `migrate.py` (new), `models/database.py` | Explicit schema inspection/backup/version-7 DDL/recovery interface; separate from legacy initialize startup. Use sqlite3 backup, transactional execute (no executescript implicit commit inside transaction), validate existing shapes. Keep old initialization and replay behavior. |
| `apps/api/app/core/municipal_repository.py` (new) | Snapshot-scoped parameterized reads, bbox prefilter + exact intersection, stable cursors, summaries, source membership and atomic publication. Bulk read instead of per-road enrichment. No official rows inserted into old dataset/roads/work_projects. |
| `apps/api/app/routes/municipal.py` (new), `app/main.py` | Mount `/api/v2` read routes, DTO validation/error mapping, explicit schema readiness, existing request/CORS guards. Keep v1 routing and HTTP safeguards intact. |
| `apps/api/app/core/config.py`, `.env.example`, `README.md` | Document migration/import paths/limits and planned public v2 base URL when implemented; defaults local, no implicit import or secret logging. Existing DB path remains supported. |
| `apps/api/tests/test_m7_ingestion.py`, `test_m7_migrations.py`, `test_m7_api.py` (new) | G1–G5 acceptance below using disposable DBs, mocked fetches and reviewed synthetic source-shaped fixtures. No paid/network dependency in normal CI. |
| `data/demo/m7-adapters/` (new only if needed) | Tiny expressly synthetic source-shaped fixtures + manifest. Tests must label them synthetic and cannot publish them as approved official snapshots; isolated test harness exercises acceptance internals. Actual NYC extracts stay ignored unless reviewed redistribution is separately documented. |
| `requirements.in`, `requirements.txt` | No planned change by default. If verified FileGDB requires tooling, document alternatives, exact added dependency/lock and offline/runtime consequences before introduction. Do not blanket-install a GIS stack. |

7.1 outputs: working explicit migration/acquisition/dry-run/publish/help commands, reviewed source mappings/manifests, tests and actual evidence report. Do not publish partial official snapshot tables before all selected records/links validate. An optional unavailable layer is explicit, and unfinished layer gates stay open.

### 7.2 Map-first client

Dependencies: 7.1 accepted geometry/context snapshot and v2 contracts, verified attribution/label resources. No v1 30-road loader can serve the new viewport client.

| File | Planned change / review focus |
| --- | --- |
| `apps/web/src/types/municipal.ts` (new) | Exact v2 discriminated DTOs, classifications, capabilities and nullable values; no `as Road` casts or invented data defaults. |
| `src/services/http.ts`, `municipal.ts` (new), `services/api.ts` | Extract shared timeout/abort/error transport without v1 behavior changes; explicit v2 base and parameter/cursor validation. Keep legacy cap semantics and all request tests. |
| `src/hooks/useMunicipalData.ts` (new) | Debounced viewport/search/paged reads; abort/race guards and cache identity containing mode/snapshot/bbox/filter; explicit broad-viewport/unavailable/partial states. No mutations. |
| `src/features/map/RoadMap.tsx`, `colors.ts`, new `mapStyle.ts` | Props for context/bounds/attribution/source-aware labels and layer state. Preserve existing worker, stable IDs, cleanup, resize, selection/list fallback. Use type-safe presentation adapter for v1/v2; no fabricated analytic fields. |
| `src/features/map/MapToolbar.tsx`, `RoadList.tsx`, `RecordInspector.tsx` (new) | Search/list/layers and one closable inspector; sources/unknowns/tabs, honest unavailable real-planning capabilities; reuse existing RepairPlanner for synthetic detail only. |
| `src/components/data/{ClassificationBadge,UnknownValue,SourceDisclosure,CoverageNotice,AsyncState}.tsx` (new as used) | Shared truthful labels, dates/units, provenance/terms, errors/retry. Text plus color; support long source names/hashes. |
| `src/pages/MapPage.tsx` (new), `App.tsx` | Extract map workflow from existing App, establish initial shared context owner for 7.3, omit permanent dashboard/coordination/editor stacks. Preserve existing actions through purposeful links/subviews. |
| `src/styles/tokens.css`, `map.css` (new), `styles.css` | Apply layout/type/spacing tokens; remove migrated conflicting global selectors. Keep unmigrated feature styling until its gate. No theme/component-library dependency. |
| `apps/web/public/` approved local font/glyph/attribution assets (if needed) | Only license-reviewed map-label resources. No downloaded secrets or blanket remote glyph URLs. Exact contents determined by label rendering approach and measured offline test. |
| `RoadMap.test.tsx`, `services/api.test.ts`, new `municipal.test.ts`, `MapPage.test.tsx` | Preserve legacy selection/error tests; add official lineage/mode/cursor/race/limits and real-vs-synthetic display tests. Browser checks required in addition to mocks. |

### 7.3 Dashboard, Projects, Scenarios and navigation (delivered; original work plan below)

Dependencies: working source-aware Map page/state. Route split changes composition, not saved calculation contracts. Actual implementation reuses App/routing, OfficialRecordsPage, OfficialMapPage and SyntheticWorkspace rather than adding unused shell/hooks/pages. One views.css scopes the page additions. No new dependency, migration or calculation service; file-by-file delivery and actual gates are in M7_3_IMPLEMENTATION.

| File | Planned change / review focus |
| --- | --- |
| `src/App.tsx`, `main.tsx`, `hooks/useWorkspace.ts`, `services/navigation.ts` (new extractions) | Shell/hash route parser, shared context/selection/camera/filter/draft ownership, context-aware cancellation and pending-write reconciliation. No router/store dependency initially. |
| `src/components/layout/{AppShell,PrimaryNav,DataContext}.tsx` (new) | Four named destinations, source/snapshot control, active/focus/skip behavior, mobile navigation; no placeholder Settings or new tour. |
| `src/pages/DashboardPage.tsx` (new) | Fetch authoritative v2 summary; no WebGL import. Synthetic counts remain visibly synthetic; no viewport-derived official totals or fake costs/trends. |
| `src/pages/ProjectsPage.tsx`, `features/projects/{PermitList,PermitDetail}.tsx` (new) | Official administrative list/detail/search/status/location filters, including unmatched/unlocated and date conventions; deep links to accepted map references. |
| `src/features/conflicts/ConflictReview.tsx`, `useConflicts.ts` | Reuse synthetic review UI; explicit analyze/run/reuse with stated project scope instead of navigation-triggered POST. No official permit promotion into WorkProject or v1 engine. Preserve category/layer filtering and unknown coverage. |
| `src/pages/ScenariosPage.tsx` (new), `features/scenarios/ScenarioPlanner.tsx`, `ScenarioResults.tsx` | One saved list/editor/result/comparison; lift draft state for route persistence, handle revision conflicts and paged histories without eager per-scenario history explosion. Preserve advanced API fields, actions, assumptions and review/advisor. Official-mode capability state prevents synthetic-price leakage. |
| `features/estimates/RepairPlanner.tsx`, `features/ai/AIAdvisor.tsx`, `ReviewNote.tsx` | Reuse existing synthetic functionality in focused subviews; preserve explicit writes, citations, replay/fallback and acknowledgement semantics. No new real-source provider contract. |
| New `styles/layout.css`, `dashboard.css`, `projects.css`, `scenarios.css`; `styles.css` | Finish scoped style migration with consistent shared controls/tables/metadata and responsive state ownership. Avoid selector order fighting with retained M2–M6 rules. |
| `App.test.tsx`, existing feature/request tests, new `navigation.test.ts`, page tests | Keep old regression meanings; use route-aware interactions where navigation changed. No deleting/weakening numerical, missing-data, source or draft-preservation assertions to achieve green tests. |

The original 7.0 proposal allowed retaining the M6 guide. The explicit 7.2 redesign removes that guide/chrome while retaining the same planning/selection/source functionality and historical guide documents. No new guide content, walkthrough, demo data, narrative or presentation deliverable is authorized. Existing demo helper/historical documentation stays intact.

### 7.4 Verification and polish

Dependencies: 7.1–7.3 acceptance; no new domain features. Apply design tokens/accessibility repairs in actual page/component files; inspect real local geographic labels and attribution. Add an integration/browser runner only if needed and justified; existing jsdom mocks alone are insufficient. Use available browser automation against isolated copies for actual WebGL and navigation, preserving runtime DBs.

Update README, roadmap, architecture/API/data/source/limitation and AI/responsibility docs to describe only implemented behavior, record actual source versions and observed QA outcomes. Create a new M7 verification report at completion; never rewrite historical FINAL_QA_REPORT or milestone reports to imply they tested real data. Record changed files, exact commands, hardware/browser/viewport, source hashes, migration preservation and unrun/failed checks.

## Acceptance and testing matrix

The matrix below is the original **acceptance plan**. Actual 7.1/7.2/7.3 results are recorded in their implementation reports; unrun 7.4 gates remain future checks. Existing test names/oracles stay. Real-source smoke verification is a separately recorded network exercise; normal suites use deterministic fixtures/mocks and must pass offline without a provider key.

| ID / stage | Test / concrete expected result |
| --- | --- |
| G0 / 7.0 | Requested shared documents agree on status/scope/six classifications/v1-v2 boundary; new plan/design links resolve; only Markdown changes; tests/typecheck/build baseline recorded; no runtime migration/install/commit/push. |
| G1 / 7.1 source | Verify each payload against exact official origin/release/dictionary/CRS/terms and SHA-256; source point samples/streets/dates traced back to original record fields. A readable catalog alone fails. No provider text supplies measurements. Confirmed-scope vs unverified permit candidates and match status vs location availability have independent denominators; do not sum overlapping unlocated counts. |
| G2 / 7.1 ingestion | Repeated identical raw bytes/adapter/rule/decisions produce same normalized content/snapshot identity, including later acquisition timestamps; exclude self-referential snapshot IDs/hashes before identity binding; reordered set-like records stable; changed raw content/decision/version creates new snapshot. Dedup exact repeats deterministically, reject conflicting identity, report all counts. 429/timeout/truncated/HTML response/unsafe ZIP/schema drift cannot publish data or erase last snapshot. |
| G3 / 7.1 boundaries | Invalid/nonfinite/swapped CRS coordinates, zero line, invalid polygon, unsupported multipart, wrong borough/code, out-of-scope, leading-zero ID, duplicate segment record, unit ambiguity, undated/reversed/inclusive-date interval, null dimensions, category disagreement/local rating-7 rule, and same-date conflicting ratings. Unknown stays null; unsupported mappings fail source gate. |
| G4 / 7.1 joins | Unique documented release-compatible exact keys accepted; ambiguous/parallel/grade-separated/name-only/nearest-road candidates not auto-accepted. Candidate reviews recorded/hash-stable; multi-road permit counted once. Unmatched assessments/permits retained with reason and no condition/footprint invented. |
| G5 / 7.1 migration/API | Empty/M1/M2/M3/M4/M5 disposable DBs, local edited drafts and old saved snapshots upgrade without existing-row changes; immutable triggers/FKs persist; repeated upgrade no-op; unknown version rejected; backup/WAL recovery, busy/disk-full/injected DDL/import rollback tested. V1 works before/after upgrade; v2 missing schema gives migration-required. Real/synthetic same IDs across stores cannot cross-reference. |
| G6 / 7.1 transport | Every new route validates snapshot/filters/cursor/source membership; 404/409/422/503/405 envelopes; exact bbox intersection includes boundary; pagination has no gaps/duplicates or filter/snapshot reuse. 2,000-feature viewport threshold explicit, never truncation. Dashboard denominators and null-vs-zero reconcile to DB and remain invariant under map pan/page size. |
| U1 / 7.2 map | Actual source street alignments/names and verified shoreline match frozen source sample. Local worker/labels/attribution function with external requests blocked. Official/synthetic context is unmistakable, no synthetic project/condition/rate leaks. Map occupies specified desktop space; one inspector only. |
| U2 / 7.2 failure | API timeout, partial optional source, broad bbox, empty viewport, glyph/context failure and WebGL loss retain usable named list/retry/source status. Abort old request on route/snapshot/filter change; late old result cannot replace current selection. |
| U3 / 7.3 navigation | Four distinct deep links; Back/Forward/refresh restore mode/snapshot/selection/filter/camera. Dashboard loads no WebGL and no domain mutation; Projects includes unlocated; route/map load writes no analysis/audit. Unsaved synthetic draft survives ordinary navigation; context-switch choices preserve or deliberately discard, pending write reconciled, stale revision shows conflict with input retained. |
| U4 / 7.3 preserved planning | Existing synthetic map→road/history→preview→save/retrieve estimate→explicit conflict review→draft/evaluate/history→2–3 comparison→sources/advisor/fallback/review works with same authoritative values/hashes. Old DBs/IDs remain usable and no synthetic plan becomes an official one. The old guide is removed by M7.2; existing tools remain directly navigable. |
| A1 / 7.4 access | Keyboard-only four views, list selection, layers, inspector close/focus return, tables, forms, disclosure/advisor/review. Screen-reader smoke with named tool/version; focus/contrast/non-color status; 200% zoom and reduced motion; 390×844, 768×1024, 1280×720, 1440×900 without page-level horizontal overflow. No certification claim. |
| I1 / 7.4 integration | Full offline suites/typecheck/build plus actual dev and production browser workflows against isolated migrated/imported copies; old estimates/analyses/evaluations replay from frozen inputs with original result hashes/runtime; all prior table contents/fixtures preserved; AI key absent/provider mocks/failure/injection boundaries retain safeguards. No raw permit narrative/contact/geometry enters AI. |
| P1 / 7.4 performance | Measure warm/cold map-ready (street labels + selectable record + attribution) target ≤3s, viewport/summary reads target p95 ≤500ms warm loopback, on recorded hardware/browser/record counts. Record ≥20 read samples and 5 cold starts; report failures, not tuned-away limits. Inspect 2,000-feature viewport, long lists and lazy bundles; no citywide/mobile guarantee. |

Migration comparisons hash canonical ordered complete rows for **every existing table**, retaining raw JSON bytes and schema/trigger definitions, not just a subset. `schema_migrations` legitimately gains new entries; compare its preexisting rows separately. Capture non-primary-key table rows in deterministic full-row order. New import_runs may differ by operational attempts without changing published snapshot identity. Saved v1 outputs never regenerate against new catalogs. Preserve old runtime/library metadata; unsupported replay runtime yields explicit incompatibility, not silently changed semantics.

## Dependencies and implementation constraints

- Already installed: Python 3.12, FastAPI/Pydantic/sqlite3, Shapely/pyproj, httpx; React/TypeScript/Vite/MapLibre/Vitest/Testing Library. No ORM, Redux/router, component kit, geocoding service, PostGIS, worker queue, OR-Tools or microservice is required by this plan.
- Potential narrowly scoped needs: official FileGDB conversion and local map glyph packaging. Resolve actual format/license first, compare existing tools against one-time conversion, pin any necessary tool and document reproducibility. No installation in 7.0.
- Geographic context and source fields are dependencies, not assets that can be authored to resemble NYC. Review exact attribution/disclaimer/redistribution terms before packaging. Use mocked synthetic source-shaped adapter fixtures for CI, not unaudited official extracts in data/demo.
- A production deployment/authentication/access/retention/backup service is separate work. M7 backup is a tested local migration prerequisite, not a disaster-recovery service. No public URL or deployment is part of acceptance.

## Risks and responses

| Risk | Consequence / required response |
| --- | --- |
| Metadata/payload availability or rate limits | Can't honestly finalize adapter mappings or claim source freshness; cache immutable source bytes after approved retrieval, report unavailable layers and keep gate open. |
| Schema/release drift and SegmentID grain | Duplicate or wrong joins, renamed/split streets; scope by release, preserve record-vs-segment IDs and original values, reject conflicts, review change/match reports. Never rewrite saved synthetic IDs. |
| Rating normalization mismatch | Historic demo output changes or incorrect official condition; distinct scale/normalization version and original source category, test local-street exception/disagreement. No generic `>=5` reuse. |
| Permit granularity/date/location ambiguity | False project/schedule/utility claim; retain administrative semantics, raw interval convention/revisions/candidates, default unknown analytical fields. No construction footprint from geocoding. |
| Old repositories scan/revalidate all rows | Mixed-snapshot results and slow page loads; v2 explicit scoped repository/bulk/indexed prefilter, snapshot-bound cursor; keep old 24-road API behavior separate. |
| SQLite startup/implicit commit/concurrent writes | Partial schema or unverified backup; explicit quiesced backup/DDL transaction/version marker, rollback injection and read-only old-software recovery. Never destructive downgrade. |
| Map labels/context/glyph license and offline assets | Another blank/unrecognizable city or unlicensed redistribution; treat verified context and locally readable labels as acceptance dependencies, not optional polish. |
| Global CSS/cascade and small-text regressions | New theme breaks old advanced forms, focus or mobile tables; incremental scoped extraction, token contrast checks and cross-feature/browser matrix. |
| Route remount/race/pending write | Draft loss, wrong inspector data or duplicate mutation; shared keyed draft state, abort/sequence guards, explicit conflict/retry behavior. |
| Dashboard completeness and apparent authority | Counts imply full city coverage or zero utility risk; source-dependent nullable metrics, denominators/study filters/retrieval dates and permanent unknown-utility caveat. |
| Legacy guide/behavior tests | Redesign unintentionally deletes M6 function or adds prohibited demo work; remove obsolete guide/chrome per the 7.2 product request, preserve actual selection/planning/source/retry/keyboard assertions in route-aware tests and retain historical reports. No new demo flow. |
| Future pressure to price real roads | Synthetic catalog contamination and misleading savings; enforce official capability flags/API isolation; a source-neutral real planning extension requires separate contracts and inputs. |

## Remaining questions and default decisions

These are tracked gates, not a request for permission to perform the already authorized documentation work.

| Question | Current decision / when it must resolve |
| --- | --- |
| Which exact LION release/export and row key/feature codes are available? | Do not pin from a search snippet. Verify payload/dictionary/terms in 7.1; prefer official GeoJSON, document any FileGDB conversion. |
| Does current ratings export follow older PDF units/usage-class exception? | Preserve original category/scale/date, verify current release before normalization. No fabricated current field map. |
| What is the permit revision key, window end convention and usable geographic linkage? | Unresolved until payload inspection; keep permit distinct from WorkProject, no grouping/actual dates inferred. |
| Can shoreline/label assets be redistributed and served locally? | Gate 7.1 context/7.2 acceptance; no assumed tile provider. Verify catalog identity/version and license/glyph approach. |
| Is a wider pilot boundary desired? | Use DATA_SOURCES chosen pilot-v2 rectangle plus Manhattan source filter; it is not a municipal boundary. Any change creates a new study/snapshot version. |
| Is real-road scenario/cost/conflict execution required inside M7? | Default bounded scope is official inspection + preserved synthetic planning. Expanding needs source-neutral DTO/engine version/persistence/AI evidence and reviewed catalog/schedule gates before implementation. No hidden synthetic inputs. |
| Refresh cadence/retention? | Manual explicit imports only; show frozen snapshot dates; retain prior published snapshots/backups. No automatic deletion or freshness guarantee. Operational retention policy is future work. |
| New dependencies/router/design framework? | None by default; justify only against verified source/label needs. Keep current component ecosystem. |

## M7.0 validation record

Actual checks run against existing installed dependencies on 2026-11-07, with isolated test DBs. No fresh installs or live provider calls:

| Command | Actual outcome |
| --- | --- |
| `git status --short` before edits | Clean; branch feat/m6-final-integration. |
| `PYTHONPATH=apps/api .venv/bin/python -m pytest apps/api/tests -q` | **212 passed**, 18.32s, one existing Starlette/httpx TestClient deprecation warning. |
| `npm test --prefix apps/web` | **57 passed in 9 files**, 3.18s. |
| `npm run typecheck --prefix apps/web` | Passed. |
| `npm run build --prefix apps/web` | Passed; existing MapLibre >500 kB chunk advisory remains (about 1,069 kB raw plus 519 kB worker); app shell about 273 kB. |

Final document checks: local Markdown link targets resolve; git diff --check passes; all changes/new files are Markdown only. Byte comparison against HEAD confirms tracked application/tests/scripts/fixtures, historical reports/demo documents and IDE files are unchanged. At the original 7.0 checkpoint, no M7 source import/migration/new endpoint or redesign browser test had run. M7.1 now has separate actual backend evidence in M7_1_IMPLEMENTATION; no redesign browser/accessibility acceptance is implied. Existing dependency tests demonstrate the M0–M6 baseline, not M7 functionality. Historical milestone reports and eight fixture/manifest files are unchanged. Next implementation milestone: **7.1 source verification, explicit additive migration and official read ingestion**, one gate at a time.

## M7.2 delivered file map and scope refinements

| Files | Delivered responsibility |
| --- | --- |
| `apps/web/src/App.tsx`, `routing.ts` | Existing app shell, narrow rail, explicit data context/pin, named four-view hash routes, no Settings/Soon/milestone/guide chrome |
| `pages/OfficialMapPage.tsx`, `hooks/useMunicipalData.ts` | Official viewport/search/detail state; independent cancelled reads, bounded pagination, optional overlays, one inspector, ambiguous/unlocated safeguards |
| `features/map/RoadMap.tsx`, `mapStyle.ts`, `colors.ts` | Existing MapLibre/worker extended with true geometry, local-font labels, shoreline/OSM context, pan/zoom/hover/selection and graceful source/tile/WebGL fallback |
| `pages/OfficialRecordsPage.tsx` | Basic separate server overview and all-permit search/detail, sufficient to relocate data inspection without claiming full 7.3 |
| `pages/SyntheticWorkspace.tsx`, `features/conflicts/useConflicts.ts`, `ConflictReview.tsx`, `features/scenarios/ScenarioPlanner.tsx` | Original feature workflows retained; explicit screening instead of page-load POST; persistent in-memory scenario editor and native dirty reload guard |
| `components/Icon.tsx`, `MapToolbar.tsx`, `MunicipalEvidence.tsx`, `DataTerms.tsx` | Small inline SVG identity, progressive sources/fields/unknowns and mandatory NYC DOT disclaimer |
| `services/municipal.ts`, `http.ts`, `types/municipal.ts` | Read-only v2 boundary separated from unchanged v1 DTOs/transport; snapshot/identity/classification/match guards and cancellation |
| `styles/tokens.css`, `styles/map.css`, `styles.css` | Replace obsolete shell cascade, scope new shell/map styles, retain repair/scenario/advisor styles with responsive adjustments |
| App/map/routing/municipal service/presentation/page tests; `test-municipal.ts` | Route-aware retained regression assertions plus authored source-shaped unit fixtures; no real downloaded extract shipped in tests |
| README, AGENTS, shared design/product/architecture/API/source/limitation docs, this plan, `M7_2_IMPLEMENTATION.md`, `.env.example` | Concrete current behavior/configuration, actual results, explicit remaining work |

No backend/schema/domain-engine/dependency/fixture change belongs to 7.2. Basic four-view routing/browsing is brought forward only to remove the original crowded main screen while preserving access to tools. M7.3 now delivers richer dashboard grouping, permit status/location filters and record/camera/filter links as documented in M7_3_IMPLEMENTATION; comprehensive accessibility remains 7.4. System-font label rendering replaces packaged glyph assets; native disclosures replace inspector tabs; retained mounted editors replace a global draft reducer/Save-Discard dialog. V1 transport stays unchanged to reduce regression risk. Each decision is reflected in ARCHITECTURE and M7_DESIGN_SYSTEM.
