# M7 design system and view specification

Status: **M7.2 map shell and M7.3 purposeful views/navigation implemented locally; comprehensive accessibility remains 7.4**. See [M7.3 delivery evidence](M7_3_IMPLEMENTATION.md). Actual test/browser evidence is in [M7_2_IMPLEMENTATION](M7_2_IMPLEMENTATION.md). Scope/semantics remain in PRODUCT_SPEC and DATA_MODEL. This specification replaces the crowded M6 layout for M7 while preserving its workflows and records. No new demo, tour, presentation or judge-specific experience.

## Product character and hierarchy

A restrained municipal planning workspace: geographic context first, evidence second, advanced tools on deliberate request. Use a light neutral canvas, dark readable text, a blue primary action and limited semantic colors. Keep CivicPlAIn identity without oversized promotional copy, “intelligence” claims, fake live indicators or milestone labels in product navigation. Surface source dates/status instead of a decorative green connection dot implying fresh data.

One primary question per page. Show one inspector/editor at a time. Source/AI details use progressive disclosure; material unknowns remain visible without expansion. A compact global context strip states “Official NYC snapshot” or “Synthetic fixtures”, selected snapshot and utility coverage unknown. Record badges and evidence show finer classifications. Do not repeatedly stack full-width disclaimers around the map; never hide the applicable synthetic/unknown/review caveat to save space.

## Implemented tokens and refinement targets

Define CSS custom properties in `src/styles/tokens.css`; retain MapLibre's required local stylesheet. Replace old global overrides in stages rather than stacking another theme at the bottom of the 1,058-line stylesheet. Scope feature classes to avoid `.metadata`, `.summary` and `button` regressions.

| Token group | Initial values / rules |
| --- | --- |
| Background / surfaces | `--canvas:#f5f7fa`, `--surface:#ffffff`, `--surface-subtle:#eef2f6` |
| Text / borders | `--text:#172b3a`, `--text-muted:#526575`, `--border:#c4cdd6` (decorative separator only; input boundary must meet nontext contrast) |
| Action / focus | `--primary:#185b75`, `--primary-hover:#12475c`, white on primary; `--focus:#005fcc`, 3px outline + 3px offset, use contrasting outer surface where necessary |
| Condition | good `#23664a`, fair `#875400`, poor `#b12d37`, unknown `#667385`; visible text labels and line/pattern/selection distinctions |
| Classification | observation `#1b5e7a`, administrative `#51458c`, derived `#4b5d6b`, assumption `#855300`, synthetic `#833e75`, unknown `#526575`; dark text on white or separately contrast-verified subtle badge background |
| Font | Local system sans stack; no remote font request. Body 15px/1.5 (rem units), form controls 16px, labels 14px, secondary minimum 13px, h1 24px/1.25, h2 20px/1.3, metric 28px. Tabular numerals for amounts/dates. |
| Spacing | 4/8/12/16/24/32px scale; 16px panel padding small screens, 24px desktop; no nested card borders for every datum |
| Shape / elevation | 6px controls, 8px cards/inspector; one subtle inspector/dialog shadow; borders for most separation, no decorative gradients |
| Controls | 40px desktop visual height with ≥44×44px touch target/hit area; 44px mobile; text + optional existing inline SVG, no icon-only action without accessible name |
| Motion | 120–180ms opacity/position only where helpful; reduced-motion removes animated camera flights/transitions; no pulsing “live” source status |
| Layers | map base 0, map controls 10, inspector 20, navigation 30, modal 50, skip/focus 100; keyboard focus never hidden by overlays |

Tokens are implemented in styles/tokens.css and styles/map.css. Map-specific controls/tertiary attribution use compact text; 7.4 retains a full typography/contrast audit. These are not an accessibility certification. 7.4 measures actual text/background combinations (≥4.5:1 normal text, ≥3:1 large text), UI/focus boundaries (≥3:1), hover/disabled states and map-label readability. Do not use border token alone as an input/focus boundary. Classification colors are independent from condition colors; text always explains their meanings.

## Navigation and state

Persistent primary navigation order: **Infrastructure map, Overview, Projects & coordination, Scenario planner**. Map is the initial entry. A compact data-context control selects official/synthetic mode and an available immutable snapshot. Source details open from context/record disclosure, not a fifth primary workflow. No nonfunctional Settings/Soon item.

Implemented hash routes: `#/map`, `#/dashboard`, `#/projects`, `#/scenarios`, with validated `mode=official|synthetic`, `snapshot=<id>` and `road=<id>`. The `#/overview` alias is accepted. M7.3 also validates record/analysis/scenario/evaluation IDs, mapq/permitq, exact source status, location/category filters, official bbox and independent layers. Other/repeated/malformed parameters show a correction state while preserving an existing synthetic editor. Backend /workspace supplies initial context; an explicit user mode selection can choose a published snapshot, and an existing pin never advances automatically. Missing official data stays unavailable with a deliberate synthetic switch. Search/layers/camera and additional record links are implemented 7.3 URL state; see the exact route schema in M7_3_IMPLEMENTATION. Per-context memory prevents IDs/filters leaking across official snapshots or synthetic mode. Typing/panning replaces history; deliberate navigation/enum filters uses named links/history.

Back/forward/refresh restore view, data context and selected road. Navigation is ordinary named links with aria-current; skip link/route focus reaches main content. Street results and map share stable row IDs (SegmentID alone is not unique). Typing/panning does not steal focus. Escape closes map search/layers and returns to the search input. The list toggle remains usable without WebGL. Its Streets, Inspections and Located permits choices expose source records independently of overlay visibility; Narrow geographic view and Reset view refine the same query bounds without a WebGL camera. Closing an inspector clears selection. URL contains no private notes/geometry/credentials.

ScenarioPlanner stays mounted after first use within the retained SyntheticWorkspace, including while official mode is visible. Route/context changes preserve its original draft/revision and pending-write reconciliation; nothing is copied into the official context. Ordinary navigation preserves the editor in memory. Opening a different saved plan or Create scenario while dirty shows an inline Keep editing / Discard editor changes and continue choice; no unsolicited automatic save or modal is needed. Browser reload uses a native dirty/busy warning where supported. No automatic saving/retry or localStorage. Full browser close/restart can still lose unsaved input.

## Map view

Implemented desktop: 100px charcoal rail, 72px topbar, floating 46px controls; map fills the remaining viewport. At 1280×720 the map region is at least 560px tall; inspector is about 344px, max 380px, and leaves ≥60% of workspace width unobscured. The unselected inspector gives concise street-selection guidance and coverage context, without a grid of empty detail cards. No KPI grid, expanded repair cards, full project findings table or scenario editor below/above the main map.

Toolbar: bounded street/ID search, list toggle, Layers, Reset extent. Official search uses a bounded server query and explicit Load more; selecting a result opens the inspector and fits its real extent without animated flights. List and map share stable record IDs. Show loaded viewport count (and snapshot-wide total matching count during search); never imply the current page is the complete dataset. A “zoom to load detail” response is distinct from no records. Keep map/list usable on timeout, API failure or unavailable layers.

Layer order: neutral local geographic context → street casing/line and real source street names → condition (off by default when condition source unavailable) → administrative permit reference geometry (opt-in) → selected feature outline. No official categorical condition is inferred. Original decimal inspection ratings use a continuous blue scale, unknown is gray, and all dates are explicitly described. Synthetic poor condition and screening use amber rather than a red safety implication; selected line has high-contrast casing, not only a hue change. Permits drawn along linked roads use dashed strokes labeled “Road reference; work footprint unknown”. Ambiguous/unlocated permits are listed, never placed at guessed centroids. No map pin denotes an underground asset without evidence.

Context acceptance: real street alignments/names and approved waterfront context make the pilot recognizable against the source extract. Labels come from source fields, not authored landmark coordinates. Shorelines remain lines unless a separately verified polygon layer exists. MapLibre 6.16 uses installed system fonts and generates labels locally without external glyph resources; labels must still be readable after external requests are blocked. Basemap/context attribution is separate from road/condition/permit attribution and always reachable.

Implemented inspector: name/source key + classifications, one dated evidence summary and progressive native disclosures for physical attributes, related records, provenance and coverage. Native disclosures replace the originally proposed three tabs to reduce controls and provide keyboard behavior without a component library. Overview shows dated condition/source scale (or unknown reason), administrative geometry/dimension basis and utility unknown. Related records links to Projects. Sources gives publisher, release/retrieval/observation dates, original units, matching/transform methods, checksum and coverage/terms. Show the relevant review caveat adjacent to any unsupported action. In official mode repair estimate/scenario execution/AI controls display capability-unavailable explanation rather than loading demo engines. In synthetic mode open existing RepairPlanner in a deliberate detail subview; preserve save/retrieve, sources, advisor and review features.

At 761–1150px the named rail remains 100px and the inspector narrows to 310px; the map toolbar compacts. At ≤760px use a labeled bottom navigation, compact header and map/list switch. Inspector becomes a dismissible bottom sheet with bounded height (53% of the workspace; 47% remains map) and its own readable scroll region; list remains a full usable view. Use dynamic viewport height; navigation respects safe-area padding. At 390×844 controls, attribution and coverage cannot obscure each other.

## Dashboard view

M7.3 implements a separate server-backed overview: street-row/inspection/permit counts, category unknowns, dated accepted-road denominator, raw source-status count links, issue-date range where known, investigation actions and per-source retrieval/cadence. Official coordination is unavailable, not zero findings. Technical provenance expands below the concise summary; unavailable summary reads show an error/retry instead of zero cards.


A page of source-backed summaries, no WebGL dependency. Heading names snapshot/study area and retrieval context. Four concise groups: loaded road count; dated condition coverage; permit matching coverage; unavailable/missing source status. Group values use server aggregate definitions and denominators in API_SPEC. An unavailable value is “Unavailable — source not imported”, not zero or an unlabeled dash.

Show condition distribution with named rows/counts (optional simple proportional bars), and a source table with publisher, observation range, retrieval time and limitations. Counts/actions link to Map/Projects with explicit layer, unknown-category or exact status/location filters. Separate synthetic saved-scenario status is visible only in synthetic mode. No invented “savings”, condition trend, predicted failure or active-construction card. Whole-snapshot metrics do not change on map pan or list search; a visible filter-scope caption accompanies any future filtered summary.

## Projects view

M7.3 implements paginated permit search with exact source-status and all/matched/ambiguous/unmatched/unlocated filters. The selected detail loads independently of the current page/filter. On mobile, selected details hide the list and filter form; Back to permit list restores them. Accepted geometry/reference links open Map; unconfirmed candidate-road links say Investigate and never create permit pins.


Desktop list/table plus one selected record; responsive labeled cards below 768px. Official mode calls these “Administrative work records / permits”. Columns: source ID/type, reported street/location, raw status, source window, location/match status. All/matched/ambiguous/unmatched/unlocated filters and search; default includes unlocated. Unknown dates read Unknown. Permit revision/status metadata is not a promised construction schedule. Source organization only where public/appropriate; no personal contacts.

Record detail shows source field values, accepted and candidate road links, date convention, missingness and source evidence. “View on map” is available only for supported source geometry or an accepted road reference; reference geometry is labeled. Unknown/unmatched records keep an explanatory disabled action. Synthetic mode reuses ConflictReview and its explicit all-loaded-project screening, evidence, category visibility and advisor. Road/project selection filters review/highlights only; the heading states the screening scope. Project/finding details link to affected roads and the selected project can be explicitly included in a hypothetical scenario. Official mode does not run the synthetic conflict engine or equate permits with WorkProject.

## Scenarios view

Synthetic mode: saved drafts/revisions first; histories load only on explicit request or editing a linked plan, with Load older evaluations and local read errors. Large forms appear only after Create/Edit; saved plans collapse during editing, with separate editor/result/comparison switches. One editor, saved result or comparison occupies the main area. Existing ScenarioPlanner/Results retain quantities, assumptions, dates/closures, repeat justification, exclusions/replacements, revision-conflict handling, saved hashes, budget bounds, indeterminate results, advisor and explicit review-note workflows. Select 2–3 saved evaluations for comparison; labels/state make clear when an evaluation predates its draft. Advanced inputs use grouped disclosures without discarding unsupported-in-editor API fields.

Official mode: an honest capability view states that real-road calculation/scenario execution is unavailable pending reviewed cost/scope/schedule inputs and a versioned contract. Link to explicitly labeled synthetic saved plans via deliberate context change. Do not show synthetic plans as official plans, clone them onto real roads, display fabricated zero totals or add a separate demonstration flow. M7 does not implement real-data draft mutation.

## Shared components and interaction acceptance

Original component extraction targets: AppShell/Nav/DataContext, ClassificationBadge, UnknownValue, SourceDisclosure, CoverageNotice, AsyncState, Inspector, FilterBar and TableRegion. Reuse existing FeatureBoundary. These are targeted extractions from existing UI, not a new component-library dependency.

Every page has loading, empty, unavailable-source, partial-source, API timeout/error/retry and stale-context states. A map-layer retry reloads independent layer reads; street detail/source/overview/permit reads also have local retries. Optional-layer failure does not block streets. A failed layer does not blank other sources. All API values are escaped text; no source HTML injection. Errors retain field paths and do not clear authored input. Tables use captions and scoped headers, with labeled keyboard-scroll regions for intrinsically wide comparison tables; the page itself never requires horizontal scrolling at 390px or 200% zoom.

7.4 must verify keyboard-only navigation/selection/layer controls/inspector/estimates/scenarios/source links; dialog focus trap/Escape/restoration; no color-only statuses; visible focus; readable labels; no map keyboard trap; reduced-motion behavior; screen-reader names/status announcements; viewport/resizing/WebGL loss; long names, large monetary strings and unknown-heavy records. Browser tests use actual WebGL/local assets, since jsdom MapLibre mocks cannot establish geographic recognizability or visual accessibility. No accessibility pass is claimed by this specification.

## M7.2 concrete component inventory

Implemented: App shell + routing, Icon, MapToolbar, MunicipalEvidence (RecordEvidence/SourceEvidence), DataTerms, OfficialMapPage, OfficialRecordsPage (basic overview/permits), SyntheticWorkspace, municipal read client/hooks and extended existing RoadMap. Existing FeatureBoundary, RepairPlanner, ConflictReview, ScenarioPlanner/Results and AIAdvisor are retained. No new router, state manager, UI kit, geocoder, font package or proprietary asset.

See [M7.2 report](M7_2_IMPLEMENTATION.md) for actual test results, deviations, basemap policy and browser boundaries. The M7.3 report reconciles delivered navigation/filter/editor behavior with this design. Comprehensive 7.4 contrast, screen-reader, zoom and cross-browser gates remain targets, not certification.

M7.4 polish, accessibility and integration verification are complete locally; see [M7 final QA evidence](M7_FINAL_QA.md). Remaining items are limitations and technical debt, not open milestone gates.
