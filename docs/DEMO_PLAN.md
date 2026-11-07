# Hackathon demo plan

Status: proposed M6 presentation. All data and interactions below are future work. Numeric examples are **synthetic assumptions**, not NYC measurements, bids, planned projects, or verified savings.

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
