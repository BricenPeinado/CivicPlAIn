# M7 final QA — in progress

M7.4 is **not complete**. This report distinguishes current verification from historical M7.3 browser evidence. Existing uncommitted M7.3 changes were preserved. No commit, push, migration or source publication was performed.

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

## Provenance and limits

M7.1 source acquisition/report remains authoritative; no new municipal source was inferred. Initial observations have ambiguous links, categories remain unknown and permits remain unlocated administrative candidates. Utility geometry/depth, actual construction dates and official planning costs remain unavailable. Synthetic engines stay separate from official read-only inspection.

## Open accessibility and integration gates

Not performed in this pass: fresh real-browser desktop/tablet/mobile checks, production-browser workflow, screen-reader testing, full keyboard traversal, measured rendered contrast, 200% zoom, reduced-motion browser verification and complete control-overlap audit. Historical M7.3 browser results do not validate these new styles. Automated DOM tests are not accessibility certification.

Not measured: map-ready latency, 20-sample read p95, five cold starts, duplicate-request counts and React profiler traces. Dense historical inspection pagination and whole-snapshot repository materialization remain performance concerns. Do not claim the roadmap performance gates pass.

Known technical debt: legacy global CSS still coexists with tokens; disabled opacity requires rendered contrast review; dense comparison tables need tablet/browser checks; no persistent draft crash recovery; large MapLibre bundle; deprecated dependency interfaces. No new domain defect was established by the passing regression suites, but visual and assistive-technology defects remain unexcluded.

Next work: complete A1/I1/P1 in M7_IMPLEMENTATION_PLAN, repair observed failures, add focused keyboard tests for Layers dismissal, then update this report and milestone status. M7.4 must remain open until those actual criteria pass.
