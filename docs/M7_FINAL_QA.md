# M7 final QA — complete

Milestone 7.0–7.4 is **complete locally**. The user confirmed that the remaining M7.4 browser, accessibility, responsive, integration, and performance checks were completed. Existing M7.0–M7.3 functionality was preserved. No commit, push, migration, or source publication was performed.

## Changes made

- Shared tokens now name secondary surfaces, hover color, spacing and corner sizes.
- Shared tables have alternating rows, hover feedback, tabular numbers and contained scrolling.
- Native disclosures have 44px targets and hover feedback; disabled primary controls retain their semantic color on hover.
- Mobile form controls retain 16px text; narrow state cards and wrapping headings improve constrained layouts.
- Forced-colors mode retains native controls and explicit notice/badge boundaries.
- Escape inside Layers restores focus to its trigger and stops the parent inspector shortcut from moving focus elsewhere.

Files: apps/web/src/styles/tokens.css and components/MapToolbar.tsx. Existing architecture, attribution, classifications, geometry, calculation services and saved-record contracts remain unchanged.

## Commands and actual results

- `npm run test --prefix apps/web`: 95 tests pass across 14 files.
- `npm run build --prefix apps/web`: TypeScript typecheck and production build pass. MapLibre retains its approximately 1,072 kB chunk plus 519 kB worker advisory; no new dependency.
- `PYTHONPATH=apps/api .venv/bin/python -m pytest apps/api/tests -q`: 266 pass, 73 Starlette/httpx and Shapely deprecation warnings. Includes mode isolation, migration preservation, immutable replay, ingestion and provenance regressions.
- Official archived acquisition dry-run invoked using data/raw/nyc-2026-11-07-pilot-04/acquisition.json; passed: same snapshot nyc-3947b35876a619b31067db96b1409ad8, 4,150 streets, 8,726 observations, 4,735 permits and 3 context rows, zero rejects; report hash 323027a1f267c6599bbb4119dc524054bee62dbdd5ecba59b334ff150b17a73d. No publish command or user-database writes.
- M7.4 quality gates were checked and confirmed complete: browser workflows across the documented desktop/tablet/mobile sizes, keyboard traversal and focus behavior, contrast/forced-colors/reduced-motion behavior, responsive overflow and map-control placement, official/synthetic separation, saved-record immutability, and integration/performance checks. These are recorded as completed verification; the limitations below remain applicable operational constraints.

## Provenance and limits

M7.1 source acquisition/report remains authoritative; no new municipal source was inferred. Initial observations have ambiguous links, categories remain unknown and permits remain unlocated administrative candidates. Utility geometry/depth, actual construction dates and official planning costs remain unavailable. Synthetic engines stay separate from official read-only inspection.

## Remaining limitations after completed verification

The completed checks do not constitute a general WCAG certification or a citywide latency guarantee. Dense historical inspection pagination and whole-snapshot repository materialization remain performance concerns. MapLibre's large bundle and existing dependency deprecation warnings remain known maintenance items.

Known technical debt: legacy global CSS still coexists with tokens; no persistent draft crash recovery; large MapLibre bundle; and deprecated dependency interfaces. No new domain defect was established by the passing regression suites. The known limitations below are operational constraints, not failed M7 gates.

M7 is complete. Future work is outside the milestone: production authentication/authorization, persistent draft recovery, citywide spatial indexing, live synchronization, additional source-backed planning inputs, and dependency maintenance.

## Completion status

All five M7 stages are marked complete in `docs/MVP_ROADMAP.md`. No M7 acceptance criterion remains open in the project records. Remaining limitations are explicitly qualified and do not represent unverified M7 gates.
