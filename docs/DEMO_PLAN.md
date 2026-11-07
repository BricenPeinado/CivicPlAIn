# Hackathon demo plan

Status: M1–M3 map, estimates and fictional project/conflict review are implemented. M3.5 reconciles the proposed M4 narrative with those working contracts; no scenarios/evaluations, scenario UI, generative explanations or review-note submission are implemented. Current dataset snapshot is `demo-m1-v1`, with separate immutable M2/M3 import manifests. There is no imported `demo-v1` full-workflow dataset. Every current geometry, dimension, condition, schedule and price is synthetic, not a municipal observation.

## Implemented demonstration and authoritative arithmetic

Use the M3 walkthrough below for the current application. Select schematic R-001; its three assessment records include the latest synthetic 3/10 rating dated 2026-10-01, not an inspection. Its 100 m × 8 m dimensions are authored rectangular planning scope, not measurements from the map. Utility coverage remains unknown.

Current supported methods are `demo-preventive`, `demo-resurface`, and `demo-reconstruct`. The source of truth is `data/demo/maintenance.json`, its immutable manifest and `repair-estimate-v1`. Rates have not been changed to match a narrative.

| R-001 option (800 m²) | Low / base / high USD | Preliminary duration | Demo suitability |
| --- | --- | --- | --- |
| Preventive maintenance | 7,008 / 8,160 / 9,888 | 1 active + 1 setup + 0 curing = 2 days | not_indicated |
| Resurfacing or rehabilitation | 44,760 / 53,400 / 66,360 | 2 active + 2 setup + 1 curing = 5 days | not_indicated |
| Full-depth reconstruction | 144,500 / 172,500 / 214,500 | 4 active + 3 setup + 3 curing = 10 days | candidate_requires_review |

Every alternative requires qualified engineering review. For resurfacing, base roadwork is 800 × $45 = $36,000; mobilization $6,000 and traffic allowance $2,500 give $44,500 subtotal; 20% contingency is $8,900, yielding $53,400. Low bundled rate $36 gives $44,760 total; high bundled rate $58.50 gives $66,360. Fixed allowances are unchanged. Each line and contingency round to cents using ROUND_HALF_UP. Do not multiply the complete total by 0.8 or 1.3. Productivity is 600 m²/active_workday, hence ceil(800/600)=2 active workdays. Five preliminary days do not establish a completion date or five calendar/work-calendar days.

Current options carry no lifespan values. Show unknown lifespan, never the old narrative's 10-year resurfacing or half-year patch assumptions. The previously illustrative $120,000 resurfacing, $48,000 repeat restoration and $19,200 patch, their scenario totals and claimed $48,000 difference are retired; none is an accepted M4 fixture, source or expected output.

## Proposed M4 narrative and source gate (not implemented)

Compare manually proposed immediate, coordinated and staged actions using DATA_MODEL's `scenario-v1`/`scenario-action-v1`. All use the same frozen source contents, price basis, horizon and `roadwork_only` scope. Utility construction, monetized delay, design fees and other catalog exclusions remain outside this scope. No utility subtype record is needed: M3 utility fields are part of WorkProject.

For future acceptance examples, an explicitly hypothetical budget of **$60,000** would distinguish the known resurfacing base ($53,400, within) from its upper bound ($66,360, over). This is a test assumption, not a stored municipal budget. It does not make resurfacing suitable for R-001's poor-condition case or establish safe deferral. Record the budget assumption in a future reviewed scenario fixture; no such fixture is imported now.

| Proposed alternative | Available M2 component | Complete cost / scheduling status |
| --- | --- | --- |
| Immediate resurfacing plus explicit repeat restoration | resurfacing low/base/high 44,760 / 53,400 / 66,360 USD | total and affordability indeterminate: restoration scope/method/price missing |
| Coordinated resurfacing after supplied utility interval | same resurfacing low/base/high | price available; any proposed dates/closures require explicit independent assumptions; deferral review mandatory |
| Temporary patch followed by coordinated resurfacing | same resurfacing low/base/high | total and affordability indeterminate: patch scope/method/price missing |

These are planned comparison rows, not calculated scenarios. Do not add restoration merely because M3 reports reopening risk. An explicit justification and quantity/source are required. Partial/trench area must be supplied or derived from sourced dimensions; never infer it from a line intersection. A cheaper partial component is not a complete scenario price. No savings/delta is available when either complete total is unknown.

Patch/restoration methods are optional future M4 catalog extensions, not aliases for existing options. Each needs reviewed scope/material/bundled rate, USD price basis, inclusions/exclusions, mobilization/traffic allowances, contingency, productivity/unit, setup/curing, sensitivity derivation, applicability and conflict-work-type mapping. Synthetic sources must explicitly identify invented assumptions with immutable checksums and versions. Lifespan stays unknown unless a separately sourced, labeled range is introduced; no verified-performance claim. M3.5 adds no method, rate, quantity or lifespan fixture. M4 can first implement honest unavailable/indeterminate rows; a fully priced three-alternative narrative needs these sources.

## Schedule and conflict rehearsal contract

The existing fictional road project is `[2027-04-01,2027-04-08)` and utility work `[2027-04-10,2027-04-15)`, with a two-calendar-day gap. Those are authored M3 fixture dates independent of the five-day M2 estimate. A future coordinated action might explicitly propose `[2027-04-15,2027-04-22)` inside `[2027-04-01,2027-05-01)`; that is a new scheduling assumption, not a conversion or automatic recommendation. Date adjacency has no overlap. Calendars, setup/curing closure treatment and closed lanes must be stated. Missing dates/closures yield null schedule metrics and incomplete checks, not zero disruption.

Future evaluation uses the internal hypothetical adapter in ARCHITECTURE. Explicitly replace the selected original road project when modeling its alternative; related_project_ids alone does not remove it. Preserve original snapshots and replacement reasons. The utility fixture remains an external project. Proposals and their findings never become persistent municipal work projects or enter M3's saved existing-project finding history. Findings involving proposed actions must say hypothetical; all current external projects remain fictional too. The adapter reuses the unchanged M3 engine and retains its limitations.

Default mobilization is separate per action. A proposed shared group needs explicit allowance, allocations, sources and replaced lines; overlapping dates do not imply a discount or fewer setup days. No calendar optimization, automatic project mutation, traffic-delay model or safe-deferral conclusion is part of this plan.

## Future explanation and failure rehearsal (M5/M6)

Show sources, action quantities, missing methods, supplied schedules, price basis, exclusions, hypothetical context and unknown utilities before any explanatory prose. A future deterministic summary may report the known resurfacing component and indeterminate total; it cannot claim the coordinated scenario saves money while restoration/patch costs are missing. Optional AI only selects supported evidence-backed templates; the server renders facts. No-key mode must remain useful. Review notes never approve work.

Use the local background-only map and keyboard list; no remote tiles are required. API failure remains a visible retry state, not a switch to fabricated live records. Missing utility information remains an incomplete check; missing rates remain unavailable costs; provider outage later uses the deterministic fallback.

## M6 full-workflow checklist (not yet verified)

- [ ] Fresh setup, checksums, exact source versions and hypothetical fixture assumptions recorded.
- [ ] Map/assessment/estimate/conflict journey matches implemented fixtures and arithmetic above.
- [ ] Three scenarios preserve common source contents, horizon, cost scope and price/method basis.
- [ ] Unpriced scopes return indeterminate totals and qualified budget status, with no invented savings.
- [ ] Supplied calendar/closure intervals, optional calendars and mobilization assumptions remain inspectable.
- [ ] Adapter retains originals, explicit replacements, pair evidence, hypothetical labels and unknown coverage.
- [ ] Deferral review, no-key/provider failure, incomplete-data and keyboard/non-color paths are demonstrated.
- [ ] Optional explanations/review events are implemented and verified before presenting them as working.
- [ ] Rehearsal timing and remaining municipal-use limits are recorded; presentation time remains TBD.

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
9. Select R-001 and **Compare Repair Options** to demonstrate M2 still works: resurfacing base **$53,400**, low **$44,760**, high **$66,360**, five preliminary days. These authoritative M2 values also anchor the proposed M4 comparison; patch/restoration totals remain unavailable. Do not switch price bases or present scenarios/AI/review-note submission as implemented.

M3 tests/manual reasoning cover exact meter thresholds (projection roundoff epsilon only), 0/30/31-day sequential boundaries, adjacent intervals, shared roads/corridors, polygon overlap, nearby separation, invalid geometry, completed/cancelled records, missing information, replay and duplicate prevention. M3_IMPLEMENTATION records actual test/build/browser results. The unchecked M6 full-workflow checklist above remains future work.
