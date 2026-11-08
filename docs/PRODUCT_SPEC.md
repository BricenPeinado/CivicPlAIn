# CivicPlAIn product specification

Status: M2 implements local map/list selection, synthetic maintenance attributes and assessment history, three repair categories, deterministic cost/preliminary-duration estimates, immutable snapshots and comparison/breakdown panels. M3 additionally implements persisted fictional work projects, deterministic spatial/temporal conflict screening, source snapshots and map/review panels. M4 adds hypothetical scenario editing, immutable evaluation and budget/tradeoff comparison. M5 implements bounded evidence explanations, optional provider fact selection, offline fallback and human review-note submission. M6 verifies final local integration/demo readiness; see FINAL_QA_REPORT. No unrestricted generative factual prose or production authorization is offered.

M7.1 now adds official NYC acquisition, immutable geographic/condition/administrative snapshots, safe explicit migration and read-only v2 inspection in the same backend. M7.2 provides the map-first official/synthetic interface. M7.3 delivers purposeful Overview, Infrastructure map, Projects & coordination and Scenario planner navigation; 7.4 retains broader polish/accessibility verification. Initial official permits are bounded unverified street-name/date candidates and categories/road links remain unknown until supported. See [M7.1 implementation](M7_1_IMPLEMENTATION.md).

## Implemented M7.2–M7.3 interface boundary

The initial screen is a full-height street map, narrow charcoal navigation and one evidence inspector; no dashboard card stack, expanded planning forms, guide or placeholder Settings item. Floating search/list, layer toggles, zoom and geographic focus expose map actions. Selection shows identifiers, latest accepted dated pavement evidence or an explicit unknown, physical/source attributes, accepted permit links, provenance and coverage. Raw inspection lines remain separate from accepted road condition; historical observations are not a current condition forecast. All initial permit locations remain unknown, so none are drawn.

Overview, Infrastructure map, Projects & coordination and Scenario planner are separately addressable. Overview shows whole-snapshot inventory/condition coverage, raw permit-status counts and issue-date range, per-source retrieval/cadence and investigation links. No permit status proves active work, and unsupported road categories remain unknown. Projects supports exact source-status/location filters, paginated search, independent record detail and qualified accepted/candidate road links. The planner loads saved histories on demand and focuses one editor, immutable result or comparison; selecting a related project offers explicit inclusion as a hypothetical screening input. See [M7.3 implementation](M7_3_IMPLEMENTATION.md). The official planning capability view cannot call v1 estimates/conflicts/scenarios/AI; explicit context switching reaches the original synthetic tools. Synthetic conflict analysis is an explicit action, never a navigation side effect. Existing saved results, deterministic engines and review/advisor tools remain unchanged. Unsaved scenario drafts remain mounted in their original synthetic context while hidden and across mode changes; the browser warns on dirty reload where supported. No automatic save/retry or persistent browser storage is introduced.

Desktop uses a 100px rail and 344px inspector (310px at intermediate widths); mobile uses labeled bottom navigation and a bounded, scrollable inspector sheet. Local labels and shoreline keep data usable without external tiles. Search, record-list selection and geographic query refinement remain functional if WebGL fails; inspection/located-permit records can be browsed independently of visible overlays. See [M7.2 implementation](M7_2_IMPLEMENTATION.md) and [design system](M7_DESIGN_SYSTEM.md) for precise implemented behavior versus planned refinements.

## Users and problem

The primary user is a municipal pavement planner preparing a small road-maintenance program. A utility coordinator checks schedule assumptions, and an engineering/budget reviewer evaluates alternatives. One solo developer must be able to build and demonstrate the complete vertical workflow.

The expensive mistake to prevent is paying for new pavement and then reopening the same area for utility work soon afterward, creating repeat restoration costs and public disruption. A potential overlap is a coordination signal, not proof of a buried utility or a legal prohibition.

## Study area and workflow

M0–M6 use the 24 synthetic segments in lower-manhattan-window-v1. M7 uses the separately versioned Lower Manhattan pilot scope and complete bounded selection in [DATA_SOURCES](DATA_SOURCES.md); the old first-30 target applies only to the historical demonstrator. Both use frozen local snapshots, with distinct official and synthetic modes.

1. Open the map and inspect source coverage, snapshot dates, and demo labels.
2. Select a segment; inspect assets, latest usable condition assessment, and planned work. Unknown condition is visible.
3. Choose a repair option and inspect dimensions, unit rates, duration, lifespan, uncertainty bounds, and exclusions.
4. Review overlapping work and near-term reopening risks with spatial and date evidence. Distinguish known findings from incomplete utility coverage.
5. Compare manually defined before-utility, after-utility, and explicitly coordinated scenarios under an explicit roadwork budget.
6. Inspect assumptions and a deterministic explanation, optionally request an AI explanation, and record human review. No project approval or spending action exists.

## User stories and screens

| Story | Screen / acceptance behavior |
| --- | --- |
| As a planner, I need to find and select roads | Map with legend, selectable segments, and equivalent keyboard-accessible list |
| I need to know what is observed versus assumed | Asset/condition panel with source, observation date, missing-data badges, and synthetic labels |
| I need a defensible estimate | Repair panel with itemized cost, duration, bounds, units, method version, and assumptions |
| I need to coordinate work before resurfacing | Conflict panel with both projects, spatial rule, intervals, evidence, and coverage limitations |
| I need options within my budget | Scenario comparison showing central and upper-bound affordability, elapsed days, lane-closure-days proxy, and limitations |
| I need to explain a recommendation to a reviewer | Evidence/explanation panel with claim references, review status, deterministic fallback, and no approval control |

M0–M6 implemented these as panels on one page. M7 supersedes that layout with the four distinct views below; the existing workflows and saved records remain available in synthetic mode.

## Functional requirements

- FR1: Display GeoJSON road features and linked infrastructure/condition/project records for the documented study area.
- FR2: Compute repair costs and preliminary active/setup/curing durations (calendar scheduling remains future work) from validated quantities and explicit assumptions; include maintenance lifespan assumptions when available.
- FR3: Detect spatial proximity plus temporal overlap and near-term reopening risk using the versioned rules in ARCHITECTURE. Potential utility work is explicitly qualified.
- FR4: Evaluate at least three manually defined scenarios using the same snapshot, roadwork cost scope, and planning horizon. Never call enumeration a global optimum.
- FR5: Compare central and upper cost bounds with a nonnegative budget. Incomplete cost produces indeterminate affordability. Safety and deferral remain a separate mandatory review requirement regardless of price; an affordable result is never a safe-work badge.
- FR6: Present deterministic evidence summaries without AI; optional AI prose cites only validated facts and preserves unknowns.
- FR7: Retain input provenance, synthetic/observed/derived distinctions, immutable evaluation snapshots, method versions, and review events.
- FR8: Preserve coverage warnings even when zero conflicts are found; capture reviewer notes without authorizing work.

## Nonfunctional requirements

- NFR1: Repeated domain calculations with identical canonical inputs and method version yield identical semantic results; timestamps/IDs may differ and are excluded from result hashes.
- NFR2: Target map readiness within 3 seconds and domain evaluations within 1 second on a documented local demo machine, for at most 30 segments and 50 projects. M6 measured warm loopback domain requests on the small fixture below one second; cold map readiness remains an unmeasured target. See FINAL_QA_REPORT for samples and limits.
- NFR3: Core demo runs locally without an API key or external data service after setup; local GeoJSON remains usable when map tiles fail.
- NFR4: Keyboard selection, text alternatives, visible focus, and non-color warning indicators are required. M6 records accessibility checks; no certification is claimed.
- NFR5: Reject malformed geometry, invalid schedules, inconsistent units, and missing references. Errors identify fields without exposing stack traces or secrets.
- NFR6: Bind the unauthenticated MVP to local development only. Authentication, tenant isolation, production security, and operational engineering are future release gates.

## Exclusions and success

No live utility clearance, excavation authorization, engineering certification, procurement, automatic approval, payments, traffic simulation, or citywide predictive claims. Prioritization and real-road planning have proposed M8 gates below; detours, forecasting, continuous live synchronization, other asset categories and multi-tenancy remain deferred. Manually reviewed official geographic snapshots are implemented M7 scope.

MVP success means a reviewer can complete the workflow above on frozen fixtures, reproduce each total and conflict from cited inputs, distinguish synthetic examples from observations, see a budget tradeoff and a missing-utility warning, and recover to deterministic explanations when AI fails. M6 must demonstrate both a detected conflict and an indeterminate case. Demo savings are hypothetical and are not validated municipal savings.


## M7 product requirements (7.1–7.3 delivered locally; 7.4 verification pending)

The primary entry is Map. A municipal planner should recognize real Lower Manhattan streets, locate a record, inspect its evidence and understand unavailable information without traversing unrelated panels. The redesign does not imply municipal endorsement, survey accuracy or production readiness.

| View | Main question / content | Excluded from initial view |
| --- | --- | --- |
| Map | Where is the record? Full-height geographic canvas, compact search/layers, selected road or permit inspector, source/coverage status; equivalent paged list | Dashboard KPI grid, expanded repair cards, full scenario editor, always-open advisor |
| Dashboard | What is loaded and missing? Snapshot-specific counts, dated condition coverage, permit linkage completeness, source retrieval/observation ages and links to filtered records | Large interactive map, invented savings, risk rankings, model forecasts or synthetic values in official totals |
| Projects | What administrative work records require review? Searchable permit/project list, raw status/window, matched roads, unknown locations, sources and limitations; synthetic conflicts in synthetic mode | Treating permit issuance as actual construction, inferred excavation/closures, automatic analysis on page load |
| Scenarios | What saved hypothetical plans exist? Existing synthetic draft/edit/evaluate/history/comparison workflow, one editor or comparison at a time, links to related map records | Silent conversion of plans to official roads, demo prices on real roads, implied real-data execution |

M7-F1: Persist mode (`official` or `synthetic`) and snapshot in navigation. Official mode defaults only when an approved geographic snapshot exists; otherwise show official-data unavailable with an explicit switch to synthetic. Never silently fall back to fixtures. Every record, map legend, summary and evidence disclosure carries applicable classifications. Field-level provenance distinguishes mixed records.

M7-F2: Official roads depict published centerlines; condition uses the actual DOT scale/category/date and documented matching. Unsupported or missing values stay unknown. Centerline length is not repair scope; administrative widths are not surveyed dimensions. All six classifications in DATA_MODEL must render consistently.

M7-F3: Official permits remain administrative records with source windows/statuses and match limitations. Unlocated and ambiguous records are reviewable in Projects and included in coverage denominators. No permit-based utility-location, schedule commitment or financial inference is allowed.

M7-F4: Source/coverage details disclose retrieval time, source release/date when known, study rule, count exclusions, matching method and update limitations. The initial M7 real-data feature is inspection, not real-road costing/screening/scenario execution. Explain unavailable capabilities and missing prerequisites; keep existing synthetic planning available through explicit navigation. Enabling real planning requires a separately approved, versioned contract, not relaxed synthetic flags.

M7-F5: Preserve all old saved records, IDs, calculation/replay versions, optimistic draft edits and explicit review notes. No migration maps a synthetic road to a similarly named official street. M7.2 removes the old guide/chrome; historical guide documents remain. Do not add or expand guide/tour/presentation features.

M7-F6: Navigation loads one primary workflow. View/mode/snapshot/road, official map camera/layers, separate map/permit searches, permit status/location, road category and record/analysis/scenario/evaluation selections are shareable in 7.3. Invalid links show a correction state while retaining an already mounted synthetic editor. Replacing a dirty scenario requires explicit keep/discard; ordinary view switches do not replace it. Filters are scoped visibly. Pending writes and dirty scenario edits survive ordinary route changes; mode changes retain mounted synthetic drafts and pending-write reconciliation in their original context, without copying or discarding them. No navigation/GET creates estimates, analyses, evaluations or AI audits.

M7 nonfunctional acceptance is defined by test IDs in M7_IMPLEMENTATION_PLAN: explicit snapshot isolation; reproducible local ingestion; atomic publication; bounded paginated reads; accessible fallback; verified source attribution; local/no-key operation after import; preservation of immutable history. Performance numbers are targets to measure on stated hardware, not verified claims. New architecture does not remove the unauthenticated local-only release boundary.

## M8 product scope (partially implemented)

[M8_IMPLEMENTATION_PLAN](M8_IMPLEMENTATION_PLAN.md) defines sequential A1–A7 acceptance gates. M8.0 changed documentation only. M8.1 now partially implements M8-F1 and the user-requested read-only M8-F2/Map subset; its real human-review/category source gates remain open. [M8_1_IMPLEMENTATION](M8_1_IMPLEMENTATION.md) is the implementation record. Completed M7 inspection behavior remains the baseline; its statement that official planning is unavailable describes current runtime, not a prohibition on separately gated M8 contracts.

- M8-F1: Associate actual NYC road rows and pavement observations through reviewed versioned scope-aware links, including partial/one-to-many coverage; retain competing and unknown associations and original evidence.
- M8-F2: Present defensible source-applicable or explicitly labeled application-policy condition classifications and recency relative to a supplied date; preserve decimal ratings, non-rating reasons, pass/direction, conflicts and unknowns. No condition forecast or automatic treatment prescription.
- M8-F3: Improve bounded permit coverage and reviewed road references without converting administrative windows/statuses into physical work/utility facts.
- M8-F4: Enable explicit real-road estimates only from reviewed quantities/methods/prices or supplied planning assumptions; show units, price basis, nullable bounds/duration, exclusions and immutable inputs. Never reuse synthetic rates/suitability.
- M8-F5: Provide transparent maintenance planning priorities with components, policy weights, tied ranks, sensitivity and an unknown/unranked queue. No safety urgency, automatic funding or program selection.
- M8-F6: Screen qualified spatial/temporal evidence and compare explicitly authored official-road scenarios with unknown coverage/incomplete checks, protected drafts and reproducible saved results. Administrative-window findings are labeled separately from actual-work/hypothetical findings.
- M8-F7: Integrate into the same Map, Overview, Projects and Scenarios; explicit pinned intelligence context, source disclosure, keyboard/no-WebGL fallback, deterministic no-key explanations and accountable human review. Navigation/GET never execute or persist planning analyses/evaluations or write AI audits; deterministic inspection projections remain read-only. All M0–M7 saved records and synthetic semantics remain usable.

M8 does not add live synchronization, excavation clearance, utility inference, autonomous approvals/spending, automatic schedules, forecasts, citywide coverage/performance claims or production deployment. Source gates may block a stage; disclose partial delivery rather than filling gaps to meet a screen narrative.


### M8.1 owner-approved pilot checkpoint

The [owner-approved M8.1 pilot](M8_1_PILOT_IMPLEMENTATION.md) supplies five explicit reviewed road references and a visibly project-defined grading assumption. The map/inspector/filter path distinguishes accepted observation grades from eligible road conditions; it preserves raw values, inspection/source/review/policy lineage, Unknown reasons and explicit release/date context. Five partial links do not supply a supported whole-road rating. This authorized M8.1 extension does not complete M8.2 or enable official costing/ranking/scenario/AI engines.

Current owner-authorized M8.2 scope is Geographic Matching and Construction Coordination; see [M8_2_IMPLEMENTATION](M8_2_IMPLEMENTATION.md) for the revised stage gate. Projects now supports searchable official permits, five location-evidence statuses, review/provenance/date disclosures, snapshot-wide coverage and explicit potential coordination screening. Permit road references remain candidates until reviewed; administrative windows remain separate from actual schedules. Zero accepted permit links means positive real-world accepted-location/precision acceptance remains blocked. Synthetic projects/scenarios are preserved; costing, ranking, confirmed conflicts and later-stage work are not started.


## M8.3 current official-road repair planning

The official street inspector now opens an explicit repair-planning form with blank numeric inputs. A planner can declare independent localized-patch/resurfacing scopes, provenance, area rates, allowances, contingency and optional rate sensitivity/productivity, then preview/save/retrieve immutable estimates. Results are calculated planning assumptions, never bids, expenditures, measured road dimensions, engineering suitability or construction schedules. No authoritative NYC pricing catalog is activated; missing required inputs make cost unavailable. Reconstruction and official scenario execution remain unavailable. [Implementation and open acceptance gate](M8_3_IMPLEMENTATION.md); this owner-authorized milestone does not resolve prior data-source/review gates or start M8.4.


## M8.4 transparent road review priorities

Dashboard and Map now expose explicit road-review policies over a bounded selected road-row set. Maintenance-need and inspection-evidence objectives remain distinct. Per-road explanations expose exact contributions, unknowns, source/inspection dates, costs, administrative-reference limits and required human review. Search/status filters preserve saved ranks; compare 2–5 roads and inspect explicitly supplied policy variants. Numeric policy fields start blank. Users explicitly preview/save/retrieve frozen runs; current policy/source evidence limits can yield all-unranked results. No default municipal weights, traffic/risk/failure/lifespan assumptions, budget allocation or optimal citywide repair schedule. The positive data/policy gate is recorded in [M8_4_IMPLEMENTATION](M8_4_IMPLEMENTATION.md), independently of prior milestone blockers.

## M8.5 delivered construction coordination scope

Map offers explicit official-context construction screening: choose administrative evidence separately from hypothetical/cited work declarations, provide geometry/schedules/assumptions and policy thresholds, inspect qualified concurrent work, multiple closure plans, sequential pavement-rework or adjacent-work opportunities, compare named schedule alternatives, save replayable results and record separate human notes. Planner declarations do not become official observations. Unknown grade/location/timing/depth and missing utility coverage remain visible; no finding is clearance. Same-scope cost differences require a frozen estimate and explicit schedule-cost additions; fewer findings never imply savings. Supported findings relate supplied plans, not verified actual municipal construction. General official scenario management and M8.6 remain unimplemented. See M8_5_IMPLEMENTATION for actual gate limits.

## M8.6 owner-authorized product integration

The latest M8.6 scope integrates existing M8.1–M8.5 contracts in the four M7 destinations, adds pinned saved planning context and evidence-grounded explanations, and retains the map as primary surface. Official Scenarios presents within-result treatment, policy and schedule alternatives only where the existing saved contract supports them. No new general municipal scenario CRUD/evaluation, cross-scope budget model or real-work source claim is introduced. This supersedes earlier planned stage numbering, without passing earlier positive source/review gates. Existing synthetic scenarios remain separate and intact. Acceptance evidence and deferred capabilities: [M8_6_IMPLEMENTATION](M8_6_IMPLEMENTATION.md).

## Focused standardized NYC Map integration

Owner-authorized 2026-11-08 scope: use the supplied derived standardized SQLite read model for **primary selected-street information** in official Map. Show indicative pavement rating/band/date/count, expandable observations, on-street permit count/details and then repair planning. Clearly label street-level evidence shared among LION segments and administrative permit dates. Keep whole-road condition verification and all existing planning systems independent. No full redesign, additional NYC fetch, database rebuild, new matching pipeline, automatic planning, deployment or broadened safety claim is included. [Integration evidence and startup](STANDARDIZED_INTEGRATION.md).

## M10 interactive construction planning

The owner-authorized M10 scope adds a map-first editor over existing official-screen-v1: draw up to two approximate hypothetical LineStrings, supply attributed proposed schedules and work declarations, explicitly analyze/save, compare up to two manually entered alternative schedules and request the existing grounded saved explanation. Advanced JSON and its original limits remain. Street IDs are references, never copied verified work footprints; permits never supply actual schedules. Findings relate supplied plans, and zero findings retain uncertainty. [M10 delivery](M10_IMPLEMENTATION.md) supersedes earlier UI-only limitations within this bounded scope without closing source/engineering gates.
