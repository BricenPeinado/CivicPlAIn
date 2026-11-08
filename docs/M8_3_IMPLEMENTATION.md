# M8.3 — Source-Backed Real-Road Repair Estimation

Implementation/verification date: 2026-11-08. Status: **software implementation verified; positive real planning-input acceptance BLOCKED**. No M8.4 work was started. Existing M8.1 source/whole-road and M8.2 reviewed-location blockers remain open. This is not municipal approval, pricing validation or production readiness.

## Baseline and authorization

Inspected the actual local branch `bp/specify-civicplain-milestone-7`, Git status, AGENTS/README, M8.0 plan/shared contracts, M8.1 implementation/pilot, M8.2 report, M2 estimate/schema/repository and M4 evaluation services before coding. The checkout already contained extensive uncommitted M8.0–M8.2 work; it was preserved. No remote checkout was substituted. Initial suites: **400 backend tests / 109 frontend tests passed**.

The explicit M8.3 request moves original planned M8.4 estimate scope into M8.3; the original A4 evidence gate is retained. Prior gates are not declared complete to permit implementation. Shared roadmap/plan now records this scope override and stop boundary.

M8.1 has five owner-reviewed partial pavement references, not whole-road current conditions. M8.2 has 23,047 imported administrative permits, 6,052 candidate locations and zero accepted permit links. Those records do not supply repair areas, installation prices, utility evidence or actual schedules. M2 synthetic catalog prices are never read for an official road. M4 remains synthetic-only; this milestone does not attach official estimates to scenarios.

## Sources investigated and activation decisions

All sources below retrieved/read on **2026-11-08**, except explicitly identified inaccessible material. Retrieval is research, not an automatic pricing import or independent approval of planner-entered citations.

| Input | Source, date/version and locator | Applicability and decision |
| --- | --- | --- |
| Road reference/dimensions | [NYC DCP LION](https://www.nyc.gov/content/planning/pages/resources/datasets/lion); exact already-pinned source revision/geometry retained in calculation input | Landing page returned a JavaScript shell in this research. Existing imported centerline geometry/length is a reference, not measured repair area or surveyed pavement width. No live release switch, lane-count × assumed width, buffered road polygon or area inference. Require declared area or length/width. |
| Resurfacing/reconstruction definition | [NYC DOT Street and Roadway Construction](https://www.nyc.gov/html/dot/html/infrastructure/construction.shtml), Resurfacing / Reconstruction sections; publication date not established | Resurfacing concerns surface renewal; reconstruction includes deeper work. Informational method source only. No generic page duration is converted into road productivity, closure dates, structural suitability or a price. Reconstruction unsupported. |
| Maintenance concepts | [FHWA Guidance on Highway Preservation and Maintenance](https://www.fhwa.dot.gov/preservation/memos/160225.cfm), memorandum 2016-02-25, page updated 2017-06-27, Maintenance Q1–2 | Federal conceptual distinction of maintenance/reactive work; not NYC treatment eligibility or engineering selection. Replaces use of the historical [2001 eligibility memorandum](https://www.fhwa.dot.gov/preservation/memos/011126.cfm), which explicitly identifies itself as superseded. No funding or legal determination. |
| NYC operational cost context | [FY2026 PMMR DOT Indicator Definitions](https://www.nyc.gov/assets/operations/downloads/pdf/pmmr2026/dot_idf.pdf), printed p.248, average resurfacing cost/lane-mile definition | Aggregate labor/materials/capital/overhead/contractor measure excludes contract milling costs. No complete installed USD/m² rate, work scope or road dimensions supplied. Not activated, not divided by an assumed lane width. |
| Historical bid-item costs | [NYSDOT Weighted Average Item Price Report](https://www.dot.ny.gov/divisions/engineering/design/dqab/dqab-repository/usc_waipr_0723_0624_pdf.pdf), cover dated 2024-08-19; contracts let 2023-07-01–2024-06-30; item/region/quarter tables | Credible historical item-specific procurement evidence, including varying units/regions. Not a current NYC complete pavement-treatment bundle or guaranteed local market price. No numbers loaded, automatic inflation or geographic adjustment. A planner must review the exact item/specification/unit/region/date, inclusions and exclusions before declaring a rate. |
| Pay-item meaning | [NYSDOT Pay Item Catalog FAQ](https://www.dot.ny.gov/main/business-center/engineering/specifications/pay-item-catalog/pic-faq), publication date not established | Specification/status catalog, not universal current NYC pricing. No item-code-to-area bundle mapping activated. |
| Exact unit conversions | [NIST Handbook 44, 2024, Appendix C](https://www.nist.gov/system/files/documents/2024/01/14/NIST%20HB%2044%202024%20Appendix%20C%20General%20Tables%20of%20Units%20of%20Measurement.pdf), international-foot note and Tables of Equivalents | 1 international ft = 0.3048 m exactly; 1 ft² = 0.09290304 m²; 1 yd² = 0.83612736 m². These exact area conversions are activated in the versioned math contract. `ft` does not mean US survey foot. No density/thickness/tonnage conversion. |
| Patching treatment guidance candidate | [Caltrans MTAG patching chapter](https://dot.ca.gov/-/media/dot-media/programs/maintenance/documents/mtag/fpmtag-chapter-5-patching.pdf), search result identified 2026-03-16 | Direct retrieval timed out. Not claimed as reviewed or used to activate costs, production or suitability. California guidance would require NYC applicability review in any case. |
| Production, mobilization, traffic, contingency, exclusions | Above sources do not establish a complete defensible road-specific basis | No verified numeric catalog activated. These require explicit human assumptions; there are no hidden zero allowances, generic crews, default contingency, traffic costs or durations. |

No authoritative classification assumption or pavement rating is needed to perform declared-scope arithmetic. Available cost does not imply the road needs, supports or is suited to that treatment. No independent planner has supplied/approved a real quantity/rate basis during this task.

## Delivered calculation contract

`municipal-estimate-v1`, method `municipal-area-cost-v1`, arithmetic `area-cost-decimal-v1` are separate from v1 synthetic DTOs. No synthetic validators, fixtures, snapshots or catalog semantics were relaxed.

- Exact official snapshot, road-row ID, full road/source/base and source checksums freeze into the input snapshot. Synthetic-origin records are rejected. A LION road row may be chosen even with Unknown condition; it remains a reference, not a confirmed treatment footprint.
- One or two unique alternatives: `patch` / `resurface`. Each has independent scope description and `partial|entire_road_reference` declaration; an entire-road declaration is not independent confirmation of dimensions. Enter positive area (`m2|yd2|ft2`) **or** explicit rectangle (`m|ft`). Both forms together are invalid. Missing dimensions are unavailable.
- Each number is a plain decimal JSON **string**, max 12 integer and 6 fractional digits, with unit and `planning_assumption` evidence: nonblank author, entered date, rationale and optional citations. Citations contain title/HTTPS URL/accessed date/optional published date/locator/geography/limitations. No URL is fetched; citing an agency does not self-certify verification. Original entered values and units remain frozen.
- Required base costs: positive bundled area rate (`USD/m2|USD/yd2|USD/ft2`), price date/geographic applicability/inclusions/exclusions, distinct mobilization and traffic-control declarations, explicit contingency and `cost_overlap_review=declared_nonoverlapping`. The checkbox records a declaration, not identity-verified engineering approval. Taxes/permits/disposal/milling/markings/etc. must be explicitly addressed in the chosen bundle/allowances/exclusions; nothing is silently added.
- Allowances: priced USD (including explicitly justified zero), included in bundle, excluded, or unknown. Included/excluded lines retain evidence and no separate amount; unknown blocks complete base cost. Excluded costs remain excluded from the displayed estimate, never a complete project-budget claim. Duplicate labels/categories rejected; optional additional priced allowances supported by API (UI exposes the two required categories).
- Optional low/high area rates require same units as base, ordered `0 ≤ low ≤ base ≤ high`, explicit rationale and each value’s evidence. Only the treatment rate varies; allowance/quantity/contingency remain fixed. This is rate sensitivity, not a probabilistic cost range or multi-variable risk model. Missing bounds yield base-only, no invented percentages.
- Duration requires explicit productivity (`m2|yd2|ft2` per active workday), setup and curing days, including explicit zero. It is ceiling(quantity/productivity) + setup + curing, sequential preliminary days, not dates, a work schedule, closure duration, calendar days or weather/crew simulation. Missing any duration input returns null without disabling an otherwise complete cost.
- USD only. Area ≤10,000,000 m²; area rate ≤1,000,000 USD/unit; each allowance ≤1,000,000,000 USD; contingency 0–1; productivity positive ≤10,000,000 area units/day; setup/curing each integer 0–365. These are validation bounds, not engineering guidance. Unknown fields, numeric JSON floats, negative/nonfinite/exponent/comma/whitespace values, inconsistent units, duplicate treatments and reconstruction are rejected.

Decimal context precision 40. Convert exact entered area/rectangle to m², then to declared rate units; do not round area to cents or borrow an observed road width. Round **each cost line** to cents with ROUND_HALF_UP, sum rounded lines, round subtotal × contingency to cents, add. Each cost case includes itemized amounts/integer cents, subtotal, contingency and total. Results link each cost line to the exact frozen request field. Independent scopes are not equal-benefit comparisons; no automatic ranking, savings or lifespan.

Manual arithmetic QA (not prices/quantities for actual work): 10 × 2 m = 20 m²; 20 × 1.005 = 20.10; two 0.005 allowances round individually to 0.01 each; subtotal 20.12; 10% contingency 2.01; total **22.13**. Supplied low 0.5 gives **11.02**; high 2 gives **44.02**. A separate zero-contingency UI example gives **20.10** with included mobilization/excluded traffic. Both are prominently marked technical QA, not approved municipal estimates. Unit tests separately verify productivity 10 m²/day + 0 setup + 1 curing = 3 preliminary days; real QA snapshots deliberately omit productivity and preserve null duration.

## API, persistence and workflow

All paths extend `/api/v2` and return existing municipal envelopes; no v1 schema/catalog reclassification. See shared [API_SPEC](API_SPEC.md) and [DATA_MODEL](DATA_MODEL.md).

| Route | Behavior |
| --- | --- |
| GET `/planning/capabilities?snapshot_id=…&road_id=…` | Validate road/base, advertise two methods, no reviewed rate catalog, explicit schema readiness; no write/calculation. |
| POST `/planning/estimates/preview` | Strict request; valid incomplete alternatives return 200 `unavailable` with missing fields and null costs. Pure calculation, no write or migration. |
| POST `/planning/estimates` | Recalculate on server, require complete costs for every alternative; 201 new, 200 identical frozen input. Missing base inputs: 422 `MISSING_PLANNING_INPUTS`. |
| GET `/planning/estimates?snapshot_id=…&road_id=…` | Snapshot/optional-road history; limit 1–100 and context-bound cursor. Reads metadata only. |
| GET `/planning/estimates/{id}?snapshot_id=…` | Exact selected-snapshot membership; hash/frozen-input replay integrity verification, 404 foreign/absent; 409 integrity failure. |

Invalid contracts/units/values/unknown or repeated query fields →422. Missing explicit schema 10 for persistence/history →503 `MIGRATION_REQUIRED`; schema-7+ preview remains possible. Cross-snapshot road references →404. Request-size/origin safeguards remain existing middleware. Identity is `estimate-<canonical input SHA-256>`; versioned canonical input/result hashes exclude creation timestamp. Identical POST is idempotent; a changed assumption/order/input identity creates a distinct record. Saved GET replays **frozen** inputs, not a newer road/source/catalog. Future versions must retain the v1 implementation for replay.

Schema 10 (`m8-municipal-estimates-v1`) adds `municipal_estimates`, composite snapshot/road FK, road-history index, unique input hash, full immutable payload and UPDATE/DELETE rejection triggers. INSERT transaction failures roll back. Hashes/triggers detect accidental inconsistency, not a malicious DB administrator or false source assertions.

In the official Map inspector select a street → **Plan repair estimate**. Numeric fields, dates, authorship and cost declarations start blank. The initial visible m² unit and resurfacing form are input choices, not quantities, prices or recommendations. Calculate is explicit POST; Save is explicit and recalculates. Saved road history and replay detail load on demand. Show all scope, exclusions, source notes, unavailable reasons, case lines, unknowns, hashes and frozen JSON. Per-road/snapshot drafts stay separate in browser memory and survive in-app navigation; edits invalidate preview. Discard is explicit; browser refresh may lose drafts and is warned. Nothing goes into URL/localStorage. No GET/navigation calculation, automatic refresh, source download, AI call or spending action.

## Migration, recovery and actual-pilot verification

Only a **new isolated copy** `data/tmp/m83-estimate-pilot.sqlite3` was migrated. Existing M7/M8.1/M8.2 databases remain unchanged. Copied committed state through SQLite backup with originals opened read-only; new files are private and ignored. Explicit migration created `data/tmp/m83-before-schema10.sqlite3`, verified all preexisting schema/full rows and SQLite integrity/FKs before commit. Legacy logical fingerprint: `6055a1a16b9819770118f79b26153721d83ea57ee1c6a1adf11eecc17e1b73c5`. Default migration target remains 7 and no startup activation was added.

```sh
PYTHONPATH=apps/api .venv/bin/python -m app.migrate \
  --database data/tmp/m83-estimate-pilot.sqlite3 \
  --backup data/tmp/m83-before-schema10.sqlite3 --target-version 10
PYTHONPATH=apps/api .venv/bin/python scripts/verify_m8_3.py \
  --database data/tmp/m83-estimate-pilot.sqlite3 \
  --snapshot nyc-4620b9e30c1c0bd5be4252fe27999c80 \
  --report data/processed/m83-verification-new.json
```

Run migration only with writers stopped; use a new backup path, never overwrite. Restore by stopping writers, preserving the failed copy, making a **new** working copy from the verified backup and checking integrity/FKs/frozen source membership before re-pin. Do not drop tables, reseed, downgrade or overwrite the original. Tests inject migration failure from schema 0/7/8/9, verify exact rollback and backup and check idempotence. Real schema-9→10 migration/backup passed; a full manual restore drill on the large pilot was not performed.

Actual official road: **WHITE STREET**, LION SegmentID `0032075`, export row `106200`, immutable ID `road-0003cbb8adbb7e90987b689e`, base `nyc-4620b9e30c1c0bd5be4252fe27999c80`. Two technical QA records saved: one API two-treatment comparison, one browser-entered zero-contingency example. These use authored test inputs, not the synthetic repair catalog, and remain unapproved technical examples. They do not establish accurate road dimensions, prices or source-backed planning coverage.

[Aggregate read-only verification](verification/m8.3-estimate-qa.json): two records, three alternatives; pinned road/source equality, exact canonical replay, database integrity/FKs and other-existing-snapshot isolation pass. Verification hash `127b7c1ccc3f20070c677ae56fd1e16cdfefdaa9a617dee62c8692c44d85456e`. Actual API requests against the other existing base `nyc-3947b35876a619b31067db96b1409ad8` return 404 for the saved ID and empty history. No full assessment/permit re-ingestion or automatic source refresh occurred.

Browser verification used loopback API 8012 and frontend 5175 with local basemap on the isolated DB. Checked WHITE STREET selection, blank numeric inputs, missing-input preview, explicit entry, zero contingency, included/excluded allowances, cost preview **20.10**, explicit save, two-record history and replay of the two-treatment **22.13** comparison; range/duration unknowns and technical-QA scope stay visible. Date entry used the native date control after browser automation’s generic date fill left the field blank; server correctly refused missing provenance. The owned loopback servers were stopped after QA. Desktop inspector/table screenshot retained in ignored `data/tmp/m83-estimate-inspector.png`. This is bounded desktop smoke coverage, not a new accessibility/device certification.

## Tests actually executed

| Command/check | Actual result |
| --- | --- |
| Before feature work: `PYTHONPATH=apps/api .venv/bin/python -m pytest apps/api/tests -q` | 400 passed, 275 warnings. |
| Before feature work: `npm test --prefix apps/web` | 109 passed, 15 files. |
| M2/M4: `PYTHONPATH=apps/api .venv/bin/python -m pytest apps/api/tests/test_planning.py apps/api/tests/test_scenarios.py -q` | 77 passed after neutral helper extraction; frozen cents/hash regressions preserved. |
| New estimate suite + M2/M4 (initial 31 new cases) | 108 passed after correcting two test unit-change expectations. |
| Final full backend: `PYTHONPATH=apps/api .venv/bin/python -m pytest apps/api/tests -q` | 433 passed, 281 warnings; Starlette/httpx and Shapely deprecations retained. |
| Final full frontend: `npm test --prefix apps/web` | 116 passed, 17 files. Initial new-suite run found an omitted-vs-undefined test expectation; corrected. |
| `npm run typecheck --prefix apps/web`; `npm run build --prefix apps/web` | Passed; existing large MapLibre chunk advisory retained. |
| Isolated pilot explicit migration / API / offline verifier / browser | Passed as technical QA only, as above. |
| Documentation consistency / whitespace / preservation | 12 documents, 148 relative links and code fences checked; no errors. `git diff --check` passed. All three original pilot database files byte-identical by streamed SHA-256; demo fixtures/dependency lockfiles unchanged. |

New backend cases cover Decimal fractional-cent/line contingency, exact area/dimension conversion and rate-unit conversion, zero values with provenance, invalid/nonfinite/precision/units/ordering, limits, duplicate allowances, no synthetic origin, incomplete inputs, independent scopes/input paths, optional duration/range, immutable storage, idempotency, write-free preview/GET, rollback/backup, tamper detection and snapshot isolation. Storage tests use explicitly marked synthetic test evidence at a test-only pure-math boundary, preserving the fixture classification; the actual pinned pilot is separately verified without this substitution. Frontend tests cover blank inputs/no auto-POST, explicit zero/provenance, draft separation/discard, available/unavailable results, context/provenance rejection, caller abort and explicit save.

## Acceptance gate

| Requirement | Status | Evidence / remaining condition |
| --- | --- | --- |
| Neutral typed official contract and no synthetic price leakage | PASS | Separate schemas/services, synthetic-origin rejection; actual official road identity verified. |
| Decimal reuse, itemization, units, contingency, sensitivity and duration boundaries | PASS | Manual reconciliation above; 33 new backend cases plus M2/M4 regressions. Exact NIST area conversion extends original m²-only proposal without tonnage/lane-mile inference. |
| Actual road preview/save/retrieve/replay and context isolation | PASS (technical software capability) | Isolated actual WHITE STREET API/browser examples and read-only verifier. No measurement/price truth asserted. |
| Required quantities/prices/planner provenance or unavailable behavior | PASS (software) | No defaults; strict server validation, null optional outputs, explicit human declarations and visible exclusions. |
| Source investigation / preservation of source dates/versions/limitations | PASS | Research matrix and frozen source/request snapshots. No historical aggregate silently activated. |
| Immutable persistence / atomic migration / unchanged synthetic outputs | PASS (bounded verification) | Schema 0/7/8/9 rollback tests, real 9→10 backup, full regressions and original preservation. Large-pilot manual restore drill remains unperformed. |
| Original A4.1 positive real planning example with reviewed source-backed or explicitly supplied planner inputs | **BLOCKED** | No authorized municipal planner has supplied/reviewed an actual work quantity and price basis. Agent technical-QA inputs do not satisfy this requirement. |
| Independently reviewed road-specific treatment applicability, rate adequacy and complete project scope | **BLOCKED** | Actual engineering/procurement review required. Current citations are informational/unverified declarations, not approval. |
| M8.4 or official scenario execution | Not started | Explicit stop boundary. |

No confirmed failed acceptance claim is hidden as a pass. Existing source/precision gates remain blocked, and software pass status does not claim an approved municipal estimate. The full positive M8.3/A4 gate is **not complete**.

## Files and exact next steps

New backend: `schemas/municipal_planning.py`, `services/cost_math.py`, `services/municipal_estimates.py`, `core/municipal_planning_repository.py`, `routes/municipal_planning.py`, `tests/test_m8_estimates.py`. Modified backend: `services/estimates.py` (neutral arithmetic reuse only), `models/migrations.py`, `migrate.py`, `main.py`.

New frontend: `types/municipalPlanning.ts`, `services/municipalPlanning.ts` and its tests, `features/estimates/OfficialRepairPlanning.tsx` and its tests. Updated existing `pages/OfficialMapPage.tsx`. New verifier/report: `scripts/verify_m8_3.py`, `docs/verification/m8.3-estimate-qa.json`. This report plus README/shared roadmap, plan, DATA_MODEL/API_SPEC/ARCHITECTURE/PRODUCT_SPEC/DATA_SOURCES/KNOWN_LIMITATIONS/AI_SYSTEM/RESPONSIBLE_AI record current behavior. Prior uncommitted M8.0–M8.2 files were retained.

To close positive acceptance: an authorized planner selects the exact road/reference and supplies a measured or explicitly assumed treatment area/scope, an item/bundle-specific dated/geographic rate with inclusions/exclusions, mobilization/traffic declarations, cost-overlap review and explicit contingency. Provide optional rate bounds/productivity/setup/curing only when defensible. Review that basis, calculate/save under an explicitly migrated isolated context, independently reconcile cents, record human review accurately and rerun offline replay. A source catalog activation, reconstruction model or official scenario integration requires separately reviewed scope/versioned contracts. Stop before M8.4 until the gate and next-stage authorization are resolved. No commit, push, deployment or dependency installation was performed.
