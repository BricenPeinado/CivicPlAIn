# Hackathon demo plan

Status: M1–M4 map, estimates, fictional project/conflict review and hypothetical scenario planning/comparison are implemented. M3.5 provided the compatibility contracts. M5 evidence-based explanations and human review-note submission are implemented in the M5 walkthrough below. The current M4 walkthrough below supersedes the older proposed narrative/source gate. Current dataset snapshot is `demo-m1-v1`, with separate immutable M2/M3 import manifests. There is no imported `demo-v1` full-workflow dataset. Every current geometry, dimension, condition, schedule and price is synthetic, not a municipal observation.

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

## Historical M3.5 optional narrative and source gate (not implemented)

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
9. Select R-001 and **Compare Repair Options** to demonstrate M2 still works: resurfacing base **$53,400**, low **$44,760**, high **$66,360**, five preliminary days. These authoritative M2 values also anchor the proposed M4 comparison; patch/restoration totals remain unavailable. Do not switch price bases. Scenario planning is now implemented in M4 below; AI/review-note submission remain unimplemented.

M3 tests/manual reasoning cover exact meter thresholds (projection roundoff epsilon only), 0/30/31-day sequential boundaries, adjacent intervals, shared roads/corridors, polygon overlap, nearby separation, invalid geometry, completed/cancelled records, missing information, replay and duplicate prevention. M3_IMPLEMENTATION records actual test/build/browser results. The unchecked M6 full-workflow checklist above remains future work.

## Implemented M4 walkthrough

Run the normal additive seed command and restart the updated API/web. `scripts/create_m4_fixture.py` reproduces reviewed `data/demo/scenarios.json` and its checksum manifest. Seeding adds stable IDs demo-scenario-a/b/c and their immutable initial evaluations; repeat runs retain edits/history. Existing road/catalog/project fixtures are unchanged. All dimensions, prices, budgets, dates, footprints, closures and coordination assumptions are synthetic, not municipal records.

1. Open **Scenario planner**. The list shows names, description, budget, revision and last evaluated budget status. Compare all three seeded plans using their checkboxes and **Compare selected (3/3)**.
2. A uses road repair `[2027-04-01,2027-04-08)` before the fictional utility `[2027-04-10,2027-04-15)`. It explicitly replaces only demo-road-project in this hypothetical screen. M3 emits one **reopening_risk** (two-day gap). This is a potential consequence; restoration scope/cost and any actual rework remain unknown.
3. B uses road repair `[2027-04-15,2027-04-22)`. Date adjacency avoids overlap and the road-before-utility rework rule, but M3 retains one **sequencing_review** (zero-day gap). Deferral requires engineering review; no safety or optimality conclusion follows.
4. C explicitly assumes coordinated road/utility teams with road interval `[2027-04-10,2027-04-17)`. M3 still emits **concurrent_work** and **multiple_closures** over the supplied envelopes. Coordination does not erase evidence, share a mobilization allowance, reduce setup time or price a benefit.
5. All three actions reuse the same catalog and 800 m² authored whole-road scope: low/base/high **$44,760 / $53,400 / $66,360**. Synthetic budget **$60,000** gives headroom **$15,240 / $6,600 / −$6,360**. Base is within budget; high sensitivity is over budget. Cost differences are zero. Utility construction and catalog exclusions are outside the roadwork budget; no restoration action or charge is inferred. Complete costs for these explicitly selected actions do not mean complete project lifecycle costs.
6. Every demo has **5 preliminary days**, independent supplied **7 calendar days**, **7 lane-closure-days** (one authored lane for the full interval including setup/curing), one affected road and no incomplete checks within the selected two-project inputs. Utility coverage and lifespan remain unknown. No Pareto dominance is established because assumptions differ; deterministic text reports completion-date tradeoffs instead of a winner.
7. Edit a demo, change its budget, save/evaluate and select the previous evaluation in history. Old inputs/results remain unchanged. To preserve the reviewed demo in a presentation, use a separate synthetic database for this exercise.
8. Select a road using the existing map or keyboard list, create a new scenario, enter name/horizon/budget and a nonblank synthetic assumption note, choose **Add selected map road**, select a catalog method and scope, and save/evaluate. Without dates or a footprint the price can be available while scheduling/screening checks remain incomplete. Explicit partial area never becomes whole-road area.
9. Rehearse an unpriced patch or trench-restoration action with method null, unknown quantity/geometry and explicit reasons (API fixtures/tests cover this). Complete costs and budget feasibility must become unavailable/indeterminate; no delta is shown against a complete total. Shared mobilization and unsupported overrides are rejected, not silently discounted.

The older restoration/patch narrative above is an optional future catalog extension, not one of the three new seeds. Its full prices remain unavailable. Calendar generation, automatic alternatives, work approval, observed municipal ingestion, monetary savings and generative AI remain outside this milestone. See M4_IMPLEMENTATION for actual backend/frontend/build/browser evidence and limitations.

## Implemented M5 evidence-advisor walkthrough

M5 supersedes earlier future-tense AI/review statements. No new prices, roads, utility observations or fake model responses are added. Use the existing reviewed M1–M4 fixtures and ordinary additive seed/start instructions. Offline operation after dependency installation needs no key, remote tiles or network data. `PYTHONPATH=apps/api .venv/bin/python scripts/verify_m5.py` runs a repeatable API walkthrough against a new temporary synthetic database, leaving existing local data untouched.

1. Select **Demo segment R-001** using map or keyboard list. Inspect its synthetic poor condition, 3/10 rating and authored dimensions. **Explain this road** and a question such as “Why is this road flagged?” return only supplied condition/scope evidence.
2. Open **Compare Repair Options**, then **Save & inspect Resurfacing or rehabilitation**. **Explain this estimate** reports saved base $53,400, low $44,760, high $66,360, itemized components and 5 preliminary days. Resurfacing is still not indicated by the demo poor-condition rule; no treatment/safety conclusion changes.
3. Choose **Potential pavement rework** in Project coordination and **Explain this conflict**. Inspect the two-calendar-day gap, supplied spatial classifications/intervals and project/road references. The assistant requests review; no damage, restoration charge or loss is invented.
4. Open **Scenario planner**, select the three demo alternatives and **Compare selected (3/3)**. **Explain tradeoffs** retrieves those saved evaluations, labels each scenario reference/revision and exposes identical costs/headroom alongside different potential finding categories and supplied schedules. All are synthetic and hypothetical; no universally best plan or fabricated saving appears.
5. Follow **Inspect source** to reveal **Supporting evidence**. Compare record/source-content hashes, calculation versions, scalar fields/units and the evidence snapshot hash. The source views retain complete original snapshots; the advisor shows a bounded projection.
6. Inspect **Missing information**: utility coverage/depth and scenario lifespan remain unknown. Ask “What happens if the city delays this repair?” to demonstrate explicit **insufficient evidence**, rather than a deterioration forecast.
7. Check **Request configured AI emphasis**, then explain again with the default unconfigured server. Expect **DETERMINISTIC FALLBACK**, reason **not configured**, with the same authoritative values and caveats. This is a real API fallback, not hardcoded frontend output. Automated tests additionally simulate timeout/rate limit/outage/invalid provider output through mocks; no paid request is made.
8. Expand **How AI works** and **Check provider status**. It explains deterministic calculations, source validation, synthetic data, offline templates and human responsibility. Status checks configuration only.
9. Optionally open an individual evaluation and **Record a human review note**, use a nonpersonal alias, enter an actual review question and acknowledge the displayed limitations. The local audit event explicitly says no work authorized. The note is never sent to AI.

M5 verifies this local workflow and provider mocks. M6 remains the separate fresh-environment, accessibility, performance, full-demo rehearsal and presentation gate; do not mark its unchecked checklist complete based on M5.
