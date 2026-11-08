# M8.1 owner-approved pavement pilot — implementation and acceptance

Verified locally 2026-11-08, branch `bp/specify-civicplain-milestone-7`; uncommitted work retained. **Five approved road references are published on an isolated copy. Four accepted observations grade Good and one Unknown under the project policy. All 4,150 road-level summaries remain Unknown. M8.1 is partial; M8.2 has not started.**

This checkpoint supersedes the pre-approval zero-acceptance checkpoint in [M8_1_IMPLEMENTATION](M8_1_IMPLEMENTATION.md) and the pending-review status of **only these five associations and this pilot policy** in the [authoritative-source audit](verification/m8.1-pavement-lion-decisions.md). It does not replace historical source facts or claim NYC DOT approval. The [owner authorization](verification/M8_1_OWNER_APPROVAL.md) records the exact scope; executable decisions are in [m8.1-owner-approved-associations.json](verification/m8.1-owner-approved-associations.json).

## Decisions and actual coverage

Every decision was resolved against the archived candidate overlay. Complete source/target content, base, candidate evidence, complete ordered candidate-set hash, parameter hash, reviewer, rationale and scope are bound into the existing immutable decision release. The original candidate association ID is retained in `evidence_refs`; an accepted annotation changes its content-derived association ID. No additional link was accepted and no competitor was removed.

| Approved observation | LION SegmentID:OBJECTID | Street | Exact raw rating | Rounded | Observation grade | Inspection date |
| --- | --- | --- | --- | --- | --- | --- |
| `condition-8d7e97c9b05832b7f976715f` | `0031869:93678` | CANAL STREET | `10.0` | 10 | Good | 2024-05-04 |
| `condition-b3fbf48779766247f0094f6d` | `0024365:106478` | ESSEX STREET | `9.69` | 10 | Good | 2021-12-19 |
| `condition-af6497ae3976ac464387b86a` | `0023459:95443` | SOUTH STREET | `7.72` | 8 | Good | 2024-08-31 |
| `condition-d94ea30139a3eee0b3882d0d` | `0032097:97186` | BROADWAY | `8.36` | 8 | Good | 2024-06-15 |
| `condition-189d3413f583f508da25efe8` | `0032478:102671` | CANAL STREET | `0.0` | — | Unknown | 2019-06-06 |

The fifth record retains `NonRatingReason = Road Identification`. It stays Unknown even though its road reference is accepted. All five annotations have conservative `partial` scope: the owner approved references but did not establish whole-road assessment extent, grade, roadbed/pass selection or compatible source editions. This is a restriction on interpretation, not a fabricated partial measurement. Three records lack direction/road type; the two Canal records are multipass. No rule silently removes those eligibility limitations.

| Metric | Count / denominator | Percentage |
| --- | --- | --- |
| Accepted observations | 5 / 8,726 observations | 0.0573% |
| Observations without an accepted link | 8,721 / 8,726 | 99.9427% |
| Distinct referenced road rows | 5 / 4,150 road rows | 0.1205% |
| Accepted partial links | 5 / 5 accepted links | 100% |
| Accepted observation grades | Good 4, Fair 0, Poor 0, Unknown 1 / 5 accepted observations | 80%, 0%, 0%, 20% |
| Supported road-level categories | Good 0, Fair 0, Poor 0, Unknown 4,150 / 4,150 road rows | 0%, 0%, 0%, 100% |
| Association rows | 85,905 total = 5 accepted + 85,900 candidate | 100% retained |
| Rejected links / observations with no candidates | 0 / 0 | Not evidence of match quality |

The 85,900 remaining candidate payloads are exactly unchanged; the complete 85,905 source/target pair set is identical to the prior overlay. Multiple candidates remain for unresolved observations; accepted reference does not reject other candidate rows. No genuine reviewed multi-row observation is claimed. The actual numeric A1.5 minimum is now satisfied; positive whole-road condition capability and full A1 remain open. Source SegmentID/UsageClass are absent in this exact feed; missing/duplicate identifier, release-mismatch and source-category diagnostics remain as documented in the source audit. No synthetic result is used as evidence of real coverage.

## Deterministic classification and integration

`services/pavement_policy.py` centralizes **CivicPlAIn Pilot Policy v1.0** (`civicplain-pilot-pavement-v1.0`). It is a project-owner `planning_assumption`, explicitly `official_nyc_dot_policy=false`. Hash: `f5bc49ead260616cb7bfa995faf0d60a5bcc4d4afa0f9cc170055049c69d9a5e`.

Zero, missing/null, nonnumeric, nonfinite or outside 0–10 => Unknown. Any populated NonRatingReason wins => Unknown. For 0 < score ≤ 10, Decimal `ROUND_HALF_UP` chooses the integer: 0 Unknown, 1–3 Poor, 4–7 Fair, 8–10 Good. Raw decimal strings and non-rating reasons are preserved. No local-street exception, PCI conversion, averaging, inferred UsageClass or AI output is used.

Explicit policy projection is `road-condition-v2-pilot`; default no-policy `road-condition-v1` replay is retained. The v2 input/result hashes include the policy ID/hash as well as complete accepted source/review evidence, base/release/road, explicit as-of date and age threshold. Grading an accepted observation in history does not make it a road's current condition. Whole-road/scope, direction/roadbed, pass, date/latest/conflict and recency checks still apply; all five current summaries therefore have `NO_ACCEPTED_ELIGIBLE_ASSESSMENT`, null road rating/date/recency and visible accepted history. Their original inspection dates remain visible in history. Missing is never Good. No schema 9 or second importer was added.

The existing v2 road list/GeoJSON, condition history/current overlay and condition-summary routes accept explicit policy context. Road category filters use the same complete accepted-assessment summary as the inspector before viewport filtering. Context membership, dates and policy are validated; unsupported policy/base or omitted explicit release is 422. No GET imports, approves, calculates a saved plan or writes an AI audit.

The official map uses Green/Yellow/Red/Gray for supported Good/Fair/Poor/Unknown road summaries. Raw observation geometry retains its separate numeric scale. All real pilot roads are gray because no complete-road category is supported. The inspector displays accepted raw and rounded observation values, derived grade, date/source, review/scope, missing evidence and content hashes without asserting that observation grade as the road category. Release and reference date survive shareable URLs and client responses are checked against the requested context. Good/Fair/Poor filters are enabled only in the explicit pilot policy context; actual counts are zero. The legend scrolls within small viewports. Synthetic map/calculations and historical records retain their previous semantics.

## Isolated publication and preservation evidence

| Artifact | Exact identity |
| --- | --- |
| Original, unchanged | `data/tmp/m7-official-pilot.sqlite3`, schema 7 |
| Verified isolated copy | `data/tmp/m81-owner-approved-pilot.sqlite3`, schema 8 |
| Private pre-upgrade recovery backup | `data/tmp/m81-owner-approved-before-schema8.sqlite3`, schema 7 |
| Base snapshot | `nyc-3947b35876a619b31067db96b1409ad8` |
| Published owner-approved release | `intel-3c0dcf87bd5d2803339d04d6368113d2` |
| Full release manifest hash | `3c0dcf87bd5d2803339d04d6368113d2857f1a52526480845c4e7b53d9df8327` |
| Dry-run report approval hash | `80cfd46a32eb0865bddc5a1e550fb9b9ba8b0d1d2983abd5bb419245a610dc10` |
| Candidate parameter hash | `432910fd330f1797b70850e56eaf80fbf5411e9cf3fad05736564782e3434001` |
| Original full legacy fingerprint | `9b911881e9f53805400062e00bdb6faca9bc355963643e55cacd261bb2833e44` |
| Offline verification report hash | `403e4655b3d9f082ed2a1e0df89e9ee061c3eb912bffcf678b48331967359327` |
| Actual API/preservation report hash | `e52f9911288339adf7b4795a0e1331e753dc0c0bf87564d5e3209b728a2aed4e` |

A new exclusive private SQLite backup copy was verified against the original before migration. Only that copy was explicitly migrated to schema 8 with the separate private backup above; then the existing intelligence dry-run and report-hash publication commands published the five decisions. All preexisting rows, raw payloads, schema definitions and prior migration markers were preserved (only additive tables/marker introduced). Integrity and FK checks passed. Actual API GETs left the entire isolated database fingerprint unchanged. After the browser checks and server shutdown, the original and pre-upgrade backup retain their exact schema-7 fingerprint; all prior copy rows/schema and the five strict review records were checked again. The legacy fingerprint uses the migration tool’s SHA-256 of sorted-key JSON serialization. The previous zero-acceptance verification copy/release remains intact.

Ignored runtime artifacts: `data/processed/m81-owner-approved-{report,bundle,verification,verification-replay,api-verification,final-preservation}.json`. Archive checks reproduce the original snapshot and all source records from 110 checksum-verified acquisition files; overlay rebuild verifies stored review rows against archived evidence. Two offline runs produced exactly equal reports and the same report hash above. The verifier uses read-only SQLite and no network. Official raw extracts, databases and large bundles remain ignored, not committed fixtures.

Recovery: stop only this pilot's API/writers and point prior software to the separate verified **pre-upgrade backup**. Retain both copies and pins; never overwrite the original or destructively downgrade. A backup cannot supply records created after it. This run does not establish actual disk-full/power-loss recovery or the whole prior-software matrix.

## Tests and checks actually executed

| Check | Actual result |
| --- | --- |
| `PYTHONPATH=apps/api .venv/bin/python -m pytest apps/api/tests -q` | **383 passed**, 176 deprecation warnings, 23.82 s. Includes M0–M7 regressions and 40 new pilot tests. |
| `npm test --prefix apps/web` | **104 passed** across 14 files. |
| `npm run build --prefix apps/web` | TypeScript and Vite production build passed; existing large MapLibre chunk advisory. |
| Actual archive/release/API verification | Five exact reviews accepted; 85,900 unchanged competitors; current 0, historical 5, unaccepted 8,721; Good/Fair/Poor road filter totals 0, Unknown 4,150; original preserved; GETs read-only. |
| Markdown consistency / `git diff --check` | 33 Markdown files; 161 local targets resolve, code fences paired; whitespace check passed. |
| Local in-app browser, API 8129 / Vite 5179, `VITE_BASEMAP=local` | Restored explicit release/date URL; South Street accepted history raw 7.72 / rounded 8 / observation Good while road Unknown; reviewer/scope/hash and coverage visible; Good filter removes roads, Unknown restores gray roads; zero-rating accepted history stays Unknown with Road Identification reason. Scroll-bounded four-color legend checked at narrow viewport. Screenshots retained at ignored `data/tmp/m81-owner-approved-legend.jpg` and `m81-owner-approved-zero.jpg`. Bounded smoke, not a full accessibility/performance audit. |

Tests cover Decimal boundaries including 0.49/0.5, 3.5, 7.0/7.4/7.5/7.9 and 9.6, invalid/non-rating inputs, accepted/unaccepted and partial/directional/multipass exclusions, date/duplicate/conflict/current-history behavior, competing candidates, leading zeros/repeated LION identifiers, supported many-to-many shape, stale hash/candidate-set review rejection, immutable/atomic publication, migration preservation, policy-context API/GeoJSON/filter agreement, map colors, context response rejection and synthetic regressions. Real coverage is established separately above. No dependencies installed, external tiles, provider calls or official planning-engine execution occurred. No commit/push/deployment or original database mutation.

## Acceptance gate — unchanged A1 requirements

| Criterion | Status and evidence |
| --- | --- |
| A1.1 field/revision/dictionary/CRS/hash and repeated-ID audit | **PASS** for documented exact archived inputs in the source audit and replay. **BLOCKED** for proof of compatible pavement reference/LION edition and release-pair split/merge reconciliation: current feed lacks SegmentID and edition linkage. Owner acceptance is a local pilot annotation, not that external evidence. |
| A1.2 candidate attributes, projected evidence and frozen parameters | **PASS** for existing OFT/on/from/to/proximity/coverage evidence, explicit unknown attributes and parameter hash; source audit and matching tests. No automatic acceptance threshold introduced. Missing grade/roadbed/node/alias evidence remains unknown. |
| A1.3 zero/one/many/partial links; dangerous geometry cannot auto-accept | **PASS** for deterministic unit/API/review tests and explicit-only promotion. Actual reviewed links all partial; no genuine reviewed multi-row case established. Synthetic shape coverage is explicitly distinguished. |
| A1.4 every accepted link human reviewed and hash-bound | **PASS — project-owner pilot approval** for exactly five supplied pairs, with source/target/base/candidate/full candidate-set/parameter hashes; stale/invalid decisions rejected. No independent municipal identity or engineering review claimed. |
| A1.5 ≥5 actual observations / ≥3 road rows and honest unresolved counts | **PASS — project-owner pilot approval**: five observations across five road rows, exact archived/API trace and full retained candidate set. No defensible reviewed multi-row example; limitation recorded and shape tested synthetically. This count does not establish whole-road condition support. |
| A1.6 deterministic replay, atomic immutable publication and no auto-activation | **PASS** for archive/overlay replay, content/decision changes, collision/rollback/idempotence tests and explicit real isolated publication. Full release/report hashes above; explicit release/date/policy reads only. |
| A1.7 membership, tests, complete preservation/recovery gate | **PASS** for executed membership/geometry/synthetic-isolation/migration/backup/rollback/WAL/preservation regression cases and actual copy checks. **BLOCKED** for complete operational recovery matrix, including actual disk-full/power-loss and all prior-software backup reopening cases; no such success fabricated. |
| User-expanded deterministic pilot classification, API/UI/history/filters | **PASS** for approved project policy and tested implementation. **BLOCKED** for a positive actual road-wide eligible condition: five partial references supply no complete-road scope/pass/grade evidence. Synthetic eligible examples test implementation only. |
| External official DOT complete grading policy | **BLOCKED** for exact-feed fractional semantics, legacy UsageClass exception and PCI applicability. The approved project policy supplies an expressly different application assumption; it does not close this external gate. |

No verified implementation failure remains in the executed checks. The full M8.1 gate is **BLOCKED / partial**, not complete. Next work stays within M8.1: obtain compatible edition/crosswalk evidence; review whole-road/grade/roadbed/direction/pass scope for defensible accepted observations (new hash-bound release if evidence changes); establish supported actual-road summaries; finish the unrun operational recovery cases. Obtain agency feed-policy applicability evidence if official classes are to be claimed. No additional link, inferred scope or external-policy approval is requested or fabricated by this report. M8.2 remains unstarted.

## Run and inspect locally

Use existing installed dependencies, from the repository root. **Do not run seed, ingestion or migrations to inspect this already-published pilot.** Ports must be free. In terminal 1:

```sh
CIVICPLAIN_DATABASE_PATH="$PWD/data/tmp/m81-owner-approved-pilot.sqlite3" \
CIVICPLAIN_DATA_MODE=official \
CIVICPLAIN_OFFICIAL_SNAPSHOT_ID=nyc-3947b35876a619b31067db96b1409ad8 \
CIVICPLAIN_ALLOWED_ORIGINS=http://127.0.0.1:5179 \
PYTHONPATH=apps/api .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8129
```

In terminal 2:

```sh
VITE_MUNICIPAL_API_BASE_URL=http://127.0.0.1:8129/api/v2 \
VITE_API_BASE_URL=http://127.0.0.1:8129/api/v1 VITE_BASEMAP=local \
npm run dev --prefix apps/web -- --host 127.0.0.1 --port 5179 --strictPort
```

Open [the South Street pilot inspector](http://127.0.0.1:5179/#/map?mode=official&snapshot=nyc-3947b35876a619b31067db96b1409ad8&road=road-3788993721d12a9e8b07501f&intelligence=intel-3c0dcf87bd5d2803339d04d6368113d2&asof=2026-11-08). Expand **Accepted assessment history and lineage**: raw 7.72, rounded 8, observation Good; road Unknown with partial-scope reason. The release must match above, not Original snapshot links. On narrow screens close the inspector to access **Map legend** → Road category / Observation overlay. Unknown returns roads; Good/Fair/Poor return none in this pilot. Enable Pavement observations and select Accepted history to inspect accepted historical geometry; current eligible is empty. These are distinct from all historical/unaccepted source observations. The zero-rating road is `road-0d2c2752b2849c767482fa63`; replace only the `road` query value to inspect it.

Exact API inspection (GET only):

```sh
curl --get http://127.0.0.1:8129/api/v2/road-segments/road-3788993721d12a9e8b07501f/condition-summary \
  --data-urlencode snapshot_id=nyc-3947b35876a619b31067db96b1409ad8 \
  --data-urlencode release_id=intel-3c0dcf87bd5d2803339d04d6368113d2 \
  --data-urlencode as_of_date=2026-11-08 --data-urlencode stale_after_days=365 \
  --data-urlencode policy_id=civicplain-pilot-pavement-v1.0
```

Offline reproduction, choosing a **new output filename** each time (existing output is refused):

```sh
PYTHONPATH=apps/api .venv/bin/python scripts/verify_m8_1.py \
  --database data/tmp/m81-owner-approved-pilot.sqlite3 \
  --snapshot nyc-3947b35876a619b31067db96b1409ad8 \
  --acquisition data/raw/nyc-2026-11-07-pilot-04/acquisition.json \
  --review-bundle data/processed/m81-owner-approved-bundle.json \
  --as-of-date 2026-11-08 --stale-after-days 365 \
  --policy-id civicplain-pilot-pavement-v1.0 \
  --output data/processed/m81-owner-approved-new-verification.json
```

Ctrl+C in each terminal stops its own server; data is retained. Servers used for this verification are stopped at delivery. The original pinned M7 startup remains independent.

## Changed files for this owner-approval checkpoint

- Backend: new `apps/api/app/services/pavement_policy.py`; extended `services/road_intelligence.py`, `services/road_conditions.py`, `schemas/road_intelligence.py` and `routes/municipal.py` under `apps/api/app`; new `apps/api/tests/test_m8_pilot_policy.py`; extended `scripts/verify_m8_1.py`.
- Frontend: `apps/web/src/pages/OfficialMapPage.tsx`, `services/municipal.ts`, `hooks/useMunicipalData.ts`, `types/municipal.ts`, `routing.ts`, `features/map/{mapStyle.ts,RoadMap.tsx}`, `styles/map.css` and their affected existing tests.
- Documentation: this report; owner approval and executable five decisions in `docs/verification`; current checkpoint links/semantics in README, M8 implementation/plan/roadmap, prior verification decision record and affected shared data/API/architecture/source/product/AI/responsibility/limitations specifications.

Other uncommitted M8.0/M8.1 files predate this checkpoint and are preserved; the complete working-tree diff also includes those earlier changes. Historical M0–M7 reports, original snapshots, synthetic fixtures, dependency declarations and IDE metadata were not changed by this checkpoint.
