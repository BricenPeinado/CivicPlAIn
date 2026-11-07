# CivicPlAIn product specification

Status: M2 implements local map/list selection, synthetic maintenance attributes and assessment history, three repair categories, deterministic cost/preliminary-duration estimates, immutable snapshots and comparison/breakdown panels. M3 additionally implements persisted fictional work projects, deterministic spatial/temporal conflict screening, source snapshots and map/review panels. Scenarios and generative explanations remain unimplemented.

## Users and problem

The primary user is a municipal pavement planner preparing a small road-maintenance program. A utility coordinator checks schedule assumptions, and an engineering/budget reviewer evaluates alternatives. One solo developer must be able to build and demonstrate the complete vertical workflow.

The expensive mistake to prevent is paying for new pavement and then reopening the same area for utility work soon afterward, creating repeat restoration costs and public disruption. A potential overlap is a coordination signal, not proof of a buried utility or a legal prohibition.

## Study area and workflow

Use the Lower Manhattan window and bounded segment selection defined in [DATA_SOURCES](DATA_SOURCES.md). Aim for 20–30 segments; accept fewer with an explicit coverage explanation. The demo uses frozen local fixtures rather than requiring live municipal services.

1. Open the map and inspect source coverage, snapshot dates, and demo labels.
2. Select a segment; inspect assets, latest usable condition assessment, and planned work. Unknown condition is visible.
3. Choose a repair option and inspect dimensions, unit rates, duration, lifespan, uncertainty bounds, and exclusions.
4. Review overlapping work and near-term reopening risks with spatial and date evidence. Distinguish known findings from incomplete utility coverage.
5. Compare manually defined immediate, coordinated, and staged scenarios under an explicit roadwork budget.
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

These may be panels on one page; separate routed pages are not required.

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
- NFR2: Target map readiness within 3 seconds and domain evaluations within 1 second on a documented local demo machine, for at most 30 segments and 50 projects. These are unmeasured targets, verified in M6.
- NFR3: Core demo runs locally without an API key or external data service after setup; local GeoJSON remains usable when map tiles fail.
- NFR4: Keyboard selection, text alternatives, visible focus, and non-color warning indicators are required. M6 records accessibility checks; no certification is claimed.
- NFR5: Reject malformed geometry, invalid schedules, inconsistent units, and missing references. Errors identify fields without exposing stack traces or secrets.
- NFR6: Bind the unauthenticated MVP to local development only. Authentication, tenant isolation, production security, and operational engineering are future release gates.

## Exclusions and success

No live utility clearance, excavation authorization, engineering certification, procurement, automatic approval, payments, traffic simulation, or citywide predictive claims. Prioritization and detours are stretch; forecasting, live integrations, other asset categories, and multi-tenancy are post-MVP.

MVP success means a reviewer can complete the workflow above on frozen fixtures, reproduce each total and conflict from cited inputs, distinguish synthetic examples from observations, see a budget tradeoff and a missing-utility warning, and recover to deterministic explanations when AI fails. M6 must demonstrate both a detected conflict and an indeterminate case. Demo savings are hypothetical and are not validated municipal savings.
