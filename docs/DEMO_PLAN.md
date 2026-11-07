# Hackathon demo plan

Status: M1–M3 map, asset/estimate inspection and fictional project/conflict review are implemented. The three-scenario comparison, generative explanation/review-note controls and full M6 presentation below remain future work. Use the implemented M3 walkthrough at the end of this document; the earlier M4/M6 narrative is illustrative. The current M1 snapshot is demo-m1-v1; demo-v1 below remains the proposed full-workflow snapshot. Numeric examples are **synthetic assumptions**, not NYC measurements, bids, planned projects, or verified savings.

## Narrative and screens

A municipal planner opens the bounded Lower Manhattan map and selects **Demo segment R-001**. Its assumed condition rating is 3 on a synthetic 1–10 higher-is-better scale; no real pavement observation or safety judgment is asserted. The repair panel shows why the cost estimate depends on an assumed 100 m length and 8 m width. A utility-work overlay makes the coordination risk visible before the planner commits to a scenario.

Use one map page with asset/condition, repair estimate, conflict evidence, scenario comparison, and explanation/review panels. Show fixture/version and coverage badges from the opening frame. An equivalent road list supports keyboard use and tile-failure fallback.

The planner first inspects a deliberately overlapping schedule, then compares immediate repair, coordinated resurfacing, and a temporary patch followed by resurfacing. The final view explains the hypothetical advantage of coordination and the unresolved safety/utility questions. The presenter records a review note; there is no approval button.

## Required frozen data

- 20–30 labeled segments if feasible, maximum 30, within `lower-manhattan-window-v1`; exact selection and any shortfall in the manifest.
- Road/asset records and synthetic condition assessments, including a missing assessment case.
- `demo-r-001`, `demo-road-project`, `demo-utility-project`, utility subtype record, and at least one utility record with missing geometry or dates for the unknown-data path.
- `demo-resurface`, `demo-restoration`, and `demo-patch` options with explicit rate, mobilization, contingency, duration, lifespan bounds, and scope evidence.
- Three Scenario records, positive conflict expectations, an indeterminate case, and expected estimates/evaluations derived from the assumptions below.
- EvidenceSource records including `demo-assumptions-v1`; a `demo-v1` manifest with checksums, study bbox, provenance and synthetic flags. These identifiers are illustrative reserved fixture IDs, not existing records.

All below use local civil dates in 2027, half-open intervals, and calendar days. Common planning horizon is `[2027-04-01, 2027-05-01)`. The assumed utility project is `[2027-04-10, 2027-04-15)`, with a footprint within the proposed 5 m tolerance of the road repair. There is no real utility location, project, owner, permit or confirmed schedule behind this example.

## Key interactions and conflict evidence

1. Select R-001 and open assumptions/provenance; show unknown real utility coverage.
2. Request a resurfacing estimate and expand the itemized calculation.
3. Inspect a separate illustrative road schedule `[2027-04-12, 2027-04-19)` against the utility interval. The deterministic concurrent finding is `[2027-04-12, 2027-04-15)`.
4. Switch to immediate repair `[2027-04-01, 2027-04-08)`. Utility start is 2 days after repair end, inside the assumed 30-day reopening horizon. Explain that this is a potential reopening risk, not proof the pavement will be cut.
5. Compare the three alternatives below, then change the budget to show a boundary. Explain both central and upper-bound affordability.
6. Open explanation facts, toggle optional AI if available, show evidence and mandatory caveats, then record a non-approving human review note.

## Reproducible synthetic arithmetic

Cost scope is **roadwork only**; utility construction costs are excluded equally from all alternatives. No monetized traffic delay, injuries, inflation, financing, or underground project cost is modeled. Mobilization and contingency are explicit roadwork assumptions, not market rates.

| Action | Assumed quantity and cost | Calendar duration / one closed lane |
| --- | --- | --- |
| Full resurfacing | 100 m × 8 m = 800 m²; 800 × $100/m² + $20,000 mobilization = $100,000; 20% contingency → **$120,000** | 7 days |
| Repeat restoration after utility work | 200 m² × $100/m² + $20,000 mobilization = $40,000; 20% contingency → **$48,000** | 3 days |
| Temporary patch | 60 m² × $100/m² + $10,000 mobilization = $16,000; 20% contingency → **$19,200** | 2 days |

Each action has synthetic lower/upper sensitivity multipliers **0.8 / 1.3** of its central total. They are not calibrated confidence intervals. Assumed full resurfacing lifespan is central 10 years with range 8–12; patch lifespan is central 0.5 years with range 0.25–1. Restoration lifespan is unknown. These do not establish engineering suitability. Present per-action lifespan, never sum years across actions.

All alternatives share a **$150,000 roadwork budget** and the same snapshot/horizon/cost scope:

| Scenario | Roadwork actions | Central cost (lower–upper) | Budget central / upper | Elapsed / lane-closure-days |
| --- | --- | --- | --- | --- |
| Immediate repair, assumed repeat restoration | Resurface Apr 1–8; restoration Apr 15–18 | **$168,000** ($134,400–$218,400) | over / over | 17 / 10 |
| Coordinate after utility | Resurface Apr 15–22 | **$120,000** ($96,000–$156,000) | within / over | 7 / 7 |
| Temporary patch, then coordinate | Patch Apr 1–3; resurface Apr 15–22 | **$139,200** ($111,360–$180,960) | within / over | 21 / 9 |

Elapsed days include gaps within each scenario's first/last action, not days from planning-horizon start. Lane-closure-days sum action duration × closed lanes; utility closure days are excluded consistently, and the proxy is not measured traffic delay. Temporary patch may itself be disturbed by utility work; the scenario assumes no separately priced patch restoration, and this limitation must be visible.

The $48,000 central difference between immediate and coordinated scenarios exists only because the immediate scenario explicitly assumes a 200 m² repeat-restoration action. A rule match alone cannot establish that cost or guaranteed savings. Both later-repair alternatives require an unresolved field/safety review of the deferral. The temporary patch is illustrative, not an engineer-approved mitigation.

## Explanation and responsible-AI moment

The evidence panel shows the date gap, proximity rule, rate/quantity assumptions, excluded costs, source IDs, and unknown utility coverage. Deterministic text can say: “Under these synthetic roadwork assumptions, the coordinated scenario has a lower central cost. Its upper estimate exceeds the budget. Confirm utility scope and review the safety of delaying resurfacing.”

Optional AI selects approved evidence-backed explanation templates; the displayed numbers/dates still come from deterministic facts. The presenter states that AI does not calculate costs, identify buried infrastructure from nothing, or approve a city decision. No-key mode must deliver the same useful factual explanation.

## Failure fallback and rehearsal

- Data/network unavailable: use reviewed frozen local fixtures, show offline and synthetic labels; no fabricated live update.
- Basemap unavailable: render local GeoJSON on a plain MapLibre style and use the segment list. Do not depend on online tiles for the core story.
- Provider absent/timeout/invalid output: show deterministic summary with mode and fallback reason.
- Missing utility information: show an indeterminate check and the need to contact the utility coordinator, retaining any known findings.
- Missing cost: show unknown total/indeterminate budget status, not a zero-cost option.

## Demo verification checklist (M6, currently unchecked)

- [ ] Fresh documented setup and fixture import work; versions and checksums recorded.
- [ ] Study bbox, segment count, geometry labels and source statuses match manifest.
- [ ] Estimate subtotal/contingency/bounds reconcile to the arithmetic above.
- [ ] Concurrent and reopening examples show correct date boundaries and evidence.
- [ ] Three scenarios use identical cost scope, snapshot and planning horizon.
- [ ] Central and upper-budget statuses, elapsed days and closure-day proxy reconcile.
- [ ] Deferral safety warning and unknown utility coverage stay visible in all relevant panels.
- [ ] No-key, missing-input and tile-failure flows work; provider failure is demonstrated with a mock if needed.
- [ ] Keyboard/list flow and non-color warning indicators are checked.
- [ ] Explanation/review logs contain evidence references and no secrets; no approval is claimed.
- [ ] Rehearsal completes within the allotted presentation time (TBD from hackathon rules); actual timing and remaining limitations recorded.

## M2 implementation boundary

M2 now implements road/assessment inspection and repair estimates using the separately reviewed `data/demo/maintenance.json` catalog. The scenario arithmetic and future utility work in this document remain illustrative M3/M4/M6 targets; their prices, durations and quantities are not the current M2 catalog. Do not present those narrative scenarios as implemented screens or saved estimates. See M2_IMPLEMENTATION for the verified local workflow.

## Implemented M3 walkthrough

Prerequisites: updated pinned Python requirements (including pyproj), explicit `PYTHONPATH=apps/api .venv/bin/python -m app.seed`, and restarted local API/web servers per README. The seed reports 24 synthetic roads, M2 counts (5,26,3), and seven M3 projects. Existing local records are preserved; no reset/delete command is needed.

All M3 project records, organizations, polygons, closure declarations and dates are authored **fictional demonstration inputs**, not municipal observations or utility locations. Actual utility coverage and depth remain unknown. Fixtures and expected examples live in `data/demo/projects.json` and `projects-manifest.json`; `scripts/create_m3_fixture.py` regenerates identical bytes.

1. Open the map and choose **Project coordination**. The client loads all seven projects and checks that explicit set using the default 5 m footprint proximity, 5 m road-centerline corridor tolerance and 30-day sequencing window. Expect **8 findings**, **10 incomplete pair checks**, and **16 indexed candidates of 21 possible pairs**. These are rule counts, not engineering/safety counts.
2. Select **Fictional R-001 resurfacing** (`demo-road-project`), scheduled `[2027-04-01,2027-04-08)`. Its authored approximate rectangle lies on schematic R-001. Four findings involve that project. Its cost is unknown; the existing M2 repair option estimate is a separate hypothetical planning calculation.
3. Select **Potential pavement rework** involving `demo-utility-project`, the fictional water excavation scheduled `[2027-04-10,2027-04-15)`. Both supplied polygons overlap and declare R-001; the utility starts **2 calendar days** after the road-work end. The engine says potential rework and requests excavation/restoration-scope and schedule review. It does not predict pavement destruction or calculate loss/savings.
4. Inspect the selected conflict's spatial evidence, half-open schedules, gap, sources and unverified assumptions. The map outlines both original work zones and related roads. Approximate polygon overlap remains a computed geometry fact with a potential-evidence classification. No buried route/depth is inferred.
5. Select a concurrent finding involving `demo-concurrent-project`, fictional sewer work affecting R-001 and R-002 on `[2027-04-05,2027-04-11)`. Its overlap with resurfacing is `[2027-04-05,2027-04-08)`. Both declare lane closures, so a separate multiple_closures coordination finding is retained. No measured traffic delay is supplied.
6. Toggle **Show project work zones** and individual category checkboxes; confirm only geometry display changes. Select roads with the existing map/list to filter findings by declared/screened related assets. Thick outlines and selected text supplement color. Use **Show all conflicts** to clear the filter.
7. Select **Fictional distant telecom inspection** (`demo-unrelated-project`). It has zero positive findings and a qualified utility-coverage warning; its pairing with the unknown-location gas project remains indeterminate. This is not clearance.
8. Select the gas project with **location unknown** and the electric project with **schedule unknown**. Missing geometry stays off the map and in the list; incomplete checks and reasons remain visible. Expand the analysis source/method disclosure to inspect source contents, parameters and hashes.
9. Select R-001 and **Compare Repair Options** to demonstrate M2 still works: resurfacing base **$53,400**, low **$44,760**, high **$66,360**, five preliminary days. These are the M2 catalog assumptions, not the earlier M4 narrative's $120,000 resurfacing scenario. Do not switch price bases or present scenarios/AI/review-note submission as implemented.

M3 tests/manual reasoning cover exact meter thresholds (projection roundoff epsilon only), 0/30/31-day sequential boundaries, adjacent intervals, shared roads/corridors, polygon overlap, nearby separation, invalid geometry, completed/cancelled records, missing information, replay and duplicate prevention. M3_IMPLEMENTATION records actual test/build/browser results. The unchecked M6 full-workflow checklist above remains future work.
