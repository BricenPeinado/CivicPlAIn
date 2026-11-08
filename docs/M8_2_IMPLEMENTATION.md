# M8.2 Geographic Matching and Construction Coordination

Implementation and evidence date: 2026-11-08. Scope follows the owner's explicit M8.2 request, superseding the original M8.0 numbering (condition/recency was 8.2; permits were 8.3). M8.1 was reviewed first: its owner-approved five partial pavement references and pilot grading remain intact; external source/release/whole-road acceptance blockers remain open. This work does not close those blockers or start costing, prioritization, official work-project scenarios or M8.3.

**Status: implemented candidate/reference workflow; positive real-world accepted-location/precision gate BLOCKED.** No reviewed permit decisions were supplied or fabricated. All 23,047 actual permit locations remain unresolved. Source CRS and real schedules remain unknown. Original A3 positive reviewed-reference requirements remain applicable to this revised scope; unknowns do not satisfy them.

## Baseline and preserved architecture

Local branch `bp/specify-civicplain-milestone-7`; extensive uncommitted M8.0/M8.1 work predates this change. Initial regressions: 383 backend tests and 104 frontend tests passed. Reused the existing M7 fixed-source acquisition, offline adapter/staging/quarantine/report/atomic publication, immutable snapshot repository, v2 envelopes/cursors, M8 hash-bound reviewed association builder, and Projects/synthetic workflows. No second importer, new dependency, startup acquisition, automatic activation, deployment, commit or push.

Only a new private copy, `data/tmp/m82-permit-pilot.sqlite3`, was migrated/published. M7 and M8.1 owner databases stayed unchanged. New additive schema 9 (`m8-permit-intelligence-v1`) adds immutable `permit_associations` and its lookup index, retaining schema 8's condition-only CHECK and every historical table/payload. Both association families share `intelligence_releases`, separated by contract and read validation. Schema 7 remains the migration default; schema 9 is explicit.

## Official evidence and field semantics

Retrieved 2026-11-08 from [NYC DOT Street Construction Permits catalog](https://data.cityofnewyork.us/d/tqtj-sjs8), [Socrata metadata](https://data.cityofnewyork.us/api/views/tqtj-sjs8.json), and its attached [Street Construction Permit Collections Data Dictionary 2025](https://data.cityofnewyork.us/api/views/tqtj-sjs8/files/7e404c9a-4419-4c05-a321-03c3d9e7cfbc?download=true&filename=Street_Construction_Permit_Collections_Data_Dictionary2025.xlsx). The [DOT permit overview](https://www.nyc.gov/html/dot/html/infrastructure/permits.shtml) describes administrative permits, without establishing actual work at a particular record's location/date. Dictionary filename indicates 2025; no separate document publication date was established. Revision-sheet Excel serials 44894 and 45787 record OFT and WKT/location-field additions, respectively; these do not establish historical row completeness or CRS.

Field definitions below are paraphrases of dictionary entries:

| Source field | Supported meaning and application handling |
|---|---|
| `PermitIssueDate` | Permit approval date; `issued_at`, never actual start. |
| `IssuedWorkStartDate` | Permit effectiveness; `valid_from`, never confirmed work start. |
| `IssuedWorkEndDate` | Permit expiration; `valid_to`, never confirmed completion. |
| `PermitStatusShortDesc` | Source administrative status retained verbatim, including expired/voided records. |
| `OnStreetName`, `FromStreetName`, `ToStreetName` | Named work street and cross-street endpoints; candidate evidence, not a bounded footprint. |
| `OFTCode` | Unique 18-digit on/from/to code based on LION StreetCode. Leading zeros preserved; first/middle/last six digits used as candidate street codes. |
| `LocationGeometry` | Geometry-type enumeration; does not declare a coordinate reference system. |
| `WKT` | Text geometry representation; no applicable EPSG/CRS declaration was found. Retained raw, never guessed/transformed into confirmation. |

The dictionary SHA-256 is `a188e14e7e635b3422d39146b437883dea47f78f4ba236fdd04e9f51086002da`. Permit source update stamp is `1794081673`; it is a source revision marker, not a work date. Metadata and counts were checked before/after paginated acquisition. The exact archived version and file hashes are recorded in the [aggregate verification report](verification/m8.2-permit-coverage.json). No documentation of actual work dates, closure footprint, grade/roadbed agreement or excavation clearance was established.

## Broader acquisition and actual coverage

Added an explicit **1–31 day** administrative-window mode to `app.ingest acquire`. It reuses the same importer. A validated pinned base acquisition supplies unchanged LION/pavement/context archives; only permits are re-acquired. No name filter or issue-year floor applies in this mode. Exact reviewed one-day query:

```sql
boroughname='MANHATTAN' AND ((issuedworkstartdate <= '2026-11-09T00:00:00' AND issuedworkenddate >= '2026-11-08T00:00:00') OR (permitissuedate >= '2026-11-08T00:00:00' AND permitissuedate < '2026-11-09T00:00:00'))
```

Inclusive administrative overlap deliberately retains boundary uncertainty; the source endpoint convention is unverified. The issue branch is half-open. Window mode records `issued_on_or_after: null`, an explicit window and caveats, so an administrative window is never mislabeled as an issue cutoff. This is possible validity overlap or recent issuance, **not an active-work census**. Older records with missing validity dates are omitted unless issued in the window. Cancelled/voided/expired source statuses remain searchable; they neither prove work nor suppress evidence automatically.

The previous pilot had 4,735 permits selected by Manhattan pilot street names and issue date from 2026-01-01. The new query has a different temporal and borough scope, so counts are not a monotonic expansion: 2,599 prior IDs retained, 20,448 added, 2,136 absent from the new selection. Neither snapshot is overwritten. Fifty new-selection records were issued before 2026-01-01 (0.2169%); this demonstrates recovery of older administrative records, not proof they are physically active. Aliases are retained without guessed normalization or expansion; borough-wide acquisition avoids omission at the download stage, while exact-name candidate matching can still miss aliases.

All percentages below use **23,047 imported permit records**. Import accepted means adapter-valid, not location accepted.

| Evidence status/field | Count | Percent |
|---|---:|---:|
| Located with accepted evidence | 0 | 0.0000% |
| Candidate location requiring review | 6,052 | 26.2594% |
| Unlocated | 16,995 | 73.7406% |
| Outside verified geographic coverage | 0 | 0.0000% |
| Invalid or unavailable evidence | 0 | 0.0000% |
| Missing OFT | 23,047 | 100.0000% |
| Present WKT / usable source geometry | 0 / 0 | 0.0000% / 0.0000% |
| Known actual schedules | 0 | 0.0000% |

No duplicate source primary keys, invalid OFT, rejected/quarantined records, or duplicate valid OFT groups occurred in this bounded archive. These are selection-specific findings, not citywide claims. There are **204,069 unreviewed candidate links** plus 16,995 explicit no-candidate rows. Maximum candidate degree is 136, demonstrating long-street ambiguity. No name absence is promoted to “outside coverage”: without verified spatial evidence it remains unlocated. Outside/invalid branches are automated-test verified but have zero real examples here. **Accepted permit coverage is 0%; precision is unmeasured (zero independent reviewed labels), not 100% or a synthetic-test accuracy claim.**

## Deterministic location and review policy

`permit-road-reference-v1`, parameters SHA-256 `5874bf7ef7d6f2cf78a8ed11e140ae0694ae4b2e87422c8f7ccc7f67dee1bbd2`:

- Exact normalized on-street name (uppercase, punctuation to spaces, whitespace collapse), OFT on-street code, or usable explicitly declared EPSG:4326 geometry within 5 metric metres forms a **union of candidates**. The 5 m radius is an application candidate-generation assumption, not measurement accuracy. Metric work uses EPSG:32618. Current permit source declares CRS unknown, so no source geometry branch is activated for it.
- Shared LION NodeIDs plus from/to names or OFT slices supply endpoint evidence. Geometric crossings without common node evidence, parallel roads, duplicate LION IDs and multiple candidates remain distinct; no inferred alias, grade, direction or roadbed equivalence.
- No automatic acceptance, even for a unique candidate. Existing explicit review machinery requires base, source record, target record, candidate, **complete candidate set**, parameter hashes and reviewer/reason. Permit decisions require `scope: partial`; an accepted reference is never a work footprint. Reviewers inspect the existing generated review bundle; there is no automatic acceptance UI.
- Status precedence: valid outside geometry → outside coverage; accepted review → located; remaining candidates → candidate; unusable/invalid location evidence without candidates → invalid evidence; otherwise unlocated. All explicitly rejected candidate references are removed from screening, preserved with reviewer reasons, and yield unlocated if none remain. Candidate-set hash continues to bind the full original competing set, including rejected alternatives.
- No automatic transfer of old permit decisions or M8.1 pavement reviews to a changed source revision/base. Legacy M7 reads stay unchanged; enhanced evidence explicitly uses its selected permit release. Zero/one/many accepted partial references are representable through distinct reviewed pairs.

Hash calculation excludes runtime timings/publication timestamps from deterministic results. Inputs are immutable import payloads, source revisions, selected base/release and versioned parameters. No AI or network is used by projections/screens. Snapshots and releases are selected explicitly; no “latest” activation.

## Read API and Projects integration

Existing `municipal-record-v2` GET routes retain their legacy defaults. Enhanced Projects requests opt into `evidence=true` and optional `permit_release_id`; `location_status` filters the five new statuses separately from legacy `location`. Search includes source key, street/cross-street names, administrative values and raw identifiers; exact `status` remains separate. Reviewed `road_id` and bbox filters use **accepted references only**, never candidates. Bounds can exclude unknown locations; exclusion count remains visible.

- GET `/api/v2/intelligence-releases?kind=permit&snapshot_id=…` selects permit contracts; default kind remains condition.
- GET `/api/v2/permits` and `/permits/{id}` optionally add typed `permit_location` evidence, including statuses, active candidates, rejected reviews, accepted references, hash lineage and unknown schedule.
- GET `/api/v2/permit-location-coverage` reports whole-snapshot denominators, selection/limitations, precision status and hash, independent of search.
- GET `/api/v2/permit-associations` requires base/release; supports `road_id`, `source_record_id`, `status`, pagination.
- GET `/api/v2/permits/{id}/coordination-candidates` screens one explicit selected record; defaults to 30 findings/page (maximum 100), snapshot/release/filter-bound cursors, deterministic ordering and totals. No persisted analysis/audit/project writes.

Unknown/repeated query keys and unsupported enums/limits →422; foreign record/snapshot/release or release kind →404; required explicit migration missing →503. A process-local two-context LRU caches immutable location projections, with locked construction to avoid duplicate concurrent builds; each read still validates base/release membership. Review reads fetch only accepted/rejected rows rather than all 204,069 candidates. No persisted GET result or implicit external refresh.

Projects shows search, exact status, five evidence statuses, full coverage, explicit permit-release selection, issue/effective/expiry values, actual dates Unknown, provenance and accepted/rejected reviews. Candidate lists display 20 at a time and preserve totals/hash; road links inspect road geometry for investigation, never draw an invented permit point or footprint. Existing synthetic project/scenario functionality and M7 map layers remain intact. Map links select existing road geometry at the stated candidate/accepted-reference level; permit markers remain unavailable for this archive. URL `permitrelease` is distinct from pavement `intelligence`; `locstatus` is validated and context-preserved.

## Potential coordination screen

`permit-coordination-v1` compares the selected record to other imported permits using common candidate/accepted road references. It does **not** establish nearby physical footprints. With both ordered floating administrative windows present, inclusive possible overlap produces `possible_overlap`; disjoint windows are omitted. Missing, reversed or timezone-incompatible windows produce `unknown` rather than fabricated overlap. Shared accepted road references are distinguished from shared candidates. Same application IDs flag potentially related revisions; distinct permit numbers remain distinct records. Source statuses stay visible, without guessing status-transition semantics.

Every finding includes both record and location hashes, base/release/parameter hash, shared road IDs, `confirmed_conflict:false`, `actual_work_overlap:unknown`, utility coverage Unknown and a screening label. Empty results never establish no work/no conflict. This is an explicit on-demand, ephemeral GET, not the later persisted project conflict/scenario engine. No permit is converted to a fictional WorkProject.

Reproducible worst-degree sample: selected `permit-fd33c9c505575d29b3e8b33d`, 136 candidate roads, 314 potential coordination candidates, **zero confirmed conflicts**. This deliberately exposes broad long-street uncertainty; it is not a precision estimate. The candidate list hash is `7485d12d276524dd4de74c136219e485efc2f471efbb41d9b8df0edf2f57c5d5`.

## Reproduction and publication

Ignored archives/extracts/DBs are not redistribution fixtures. Use new output paths; all report/archive writes refuse overwrite. Stop writers before migration; verify a private SQLite backup/copy before operating. Executed:

```sh
PYTHONPATH=apps/api .venv/bin/python -m app.ingest acquire --output data/raw/m82-administrative-window-2026-11-08 --permit-since 2026-01-01 --permit-window-start 2026-11-08 --permit-window-end 2026-11-09 --permit-cap 30000 --base-acquisition data/raw/nyc-2026-11-07-pilot-04/acquisition.json
PYTHONPATH=apps/api .venv/bin/python -m app.ingest dry-run --acquisition data/raw/m82-administrative-window-2026-11-08/acquisition.json --report data/processed/m82-window-review.json
PYTHONPATH=apps/api .venv/bin/python -m app.migrate --database data/tmp/m82-permit-pilot.sqlite3 --backup data/tmp/m82-permit-before-schema9.sqlite3 --target-version 9
PYTHONPATH=apps/api .venv/bin/python -m app.ingest publish --database data/tmp/m82-permit-pilot.sqlite3 --acquisition data/raw/m82-administrative-window-2026-11-08/acquisition.json --approve-report 6a980e6a4aeee54e286a049448bb29e00f7c601c0bf45e68e2bc60c399ffae29
PYTHONPATH=apps/api .venv/bin/python -m app.ingest permit-intelligence-dry-run --database data/tmp/m82-permit-pilot.sqlite3 --snapshot nyc-4620b9e30c1c0bd5be4252fe27999c80 --report data/processed/m82-permit-review.json --review-bundle data/processed/m82-permit-bundle.json
PYTHONPATH=apps/api .venv/bin/python -m app.ingest permit-intelligence-publish --database data/tmp/m82-permit-pilot.sqlite3 --snapshot nyc-4620b9e30c1c0bd5be4252fe27999c80 --approve-report 103113342a5aefba47dafe0eed14a2748c6c581bcdc974813f08d26cda36ca88
PYTHONPATH=apps/api .venv/bin/python scripts/verify_m8_2.py --database data/tmp/m82-permit-pilot.sqlite3 --snapshot nyc-4620b9e30c1c0bd5be4252fe27999c80 --acquisition data/raw/m82-administrative-window-2026-11-08/acquisition.json --bundle data/processed/m82-permit-bundle.json --report data/processed/m82-verification-final.json
```

The private copy was first created exclusively using SQLite's backup API and verified against the complete schema/rows fingerprint of M8.1. Publication approving a **zero-decision candidate report** authorizes no relationship. New base `nyc-4620b9e30c1c0bd5be4252fe27999c80`; permit release `intel-70143d56a462b1f080786a04dab65fe6`. Earlier snapshots, five pavement reviews and synthetic rows remain in the isolated copy. Pavement reviews on the old base are not silently transferred to this new base.

Offline verifier validates every archived file checksum/page concatenation, adapter replay, stored import payloads, review-overlay replay, and reports actual coverage. Verification hash `aafd7b3c8e3b556c22bc9a9206bcaf7385f9ea47d9c850986a8b037a64635bed`; projection hash `41ccc5b67d0b88a5412996c5bff3f284802bb4f83632a6091c31a258ebe76b9b`. Projection calculation observed 6.546 seconds on this machine; a single timing is not a latency percentile or production performance guarantee.

## Acceptance and remaining blockers

| Requirement | Result | Evidence / limitation |
|---|---|---|
| Review M8.1 and run baseline regressions first | PASS | 383 backend / 104 web baseline; source blockers retained. |
| Reuse ingestion/snapshots/review architecture | PASS | Same CLI/adapter; new explicit query mode and immutable permit association family; no parallel importer. |
| Investigate OFT/WKT/CRS and dates | PASS | Archived official dictionary/metadata; no CRS invented; raw dates/status retained. |
| Broaden bounded coverage incl older permits | PASS | 23,047 actual records; 50 pre-2026 issues; no name restriction; before/after count/revision checks, 0 quarantines. Completeness not claimed. |
| Five location statuses and reviewed many-candidate boundaries | PASS | Typed projections, API/UI, automated accepted/rejected/outside/invalid/unlocated cases, full candidate-set review hashes. |
| Actual verified accepted permit references and measured precision (original A3 positive evidence) | BLOCKED | 0 accepted; no reviewed permit decisions or independent labels. No threshold was weakened. |
| Accurate physical footprint/CRS/direction/grade | BLOCKED | Unknown source CRS; no OFT/WKT values in this selection; street references are only candidates. |
| Separate administrative dates/status and actual dates | PASS | Source fields exposed separately; all actual schedules Unknown; no active-work or closure claim. |
| Searchable Projects, coverage/provenance/release/context | PASS | API/browser/component checks; candidate links inspect road geometry without invented permit marker. |
| Deterministic potential-coordination indicators | PASS | Stable shared-reference/administrative-window rules, on-demand paginated GET, hashes and zero-result caveats; 314 actual sample candidates. |
| Confirmed construction conflicts/work schedules | BLOCKED | Independent work evidence unavailable; deliberately not asserted or executed. |
| Regression, replay and additive recovery safeguards | PASS within tested bounds | Tests and real isolated-copy/replay below; comprehensive power-loss/filesystem recovery certification remains untested. |

No failed numeric threshold is hidden as a pass. Full positive permit-location acceptance remains blocked. Next acceptance work: an authorized reviewer must inspect actual candidate bundles and reject/accept precise source-target references with the required hashes and rationale; a separately labeled sample must measure precision/false matches; DOT must provide feed-specific CRS/coverage and alias/identifier evidence before geometry/alias assumptions can be activated. Re-run dry-run/replay and publish a new explicit release only after those decisions. Independent confirmed work dates/footprints are needed before any actual-overlap claim. Do not proceed to M8.3 or later engines from this result.

## Tests and recovery evidence

- `PYTHONPATH=apps/api .venv/bin/python -m pytest apps/api/tests -q`: **400 passed**, 275 deprecation warnings, 27.59 s after final changes.
- `npm test --prefix apps/web`: **109 passed**, 15 files, 5.70 s after final changes.
- `npm run build --prefix apps/web`: typecheck and production build passed; existing large map chunk warning remains. No dependency installation.
- New backend tests exercise punctuation normalization, OFT leading zeros/endpoints, duplicate IDs/parallel/crossing candidates, unknown CRS/outside evidence, stale review hashes, explicit rejection, API context/filters/read-only fingerprints, atomic failed publication, immutability, admin boundaries/missing/reversed dates and bounded query validation. Migration 9 tests cover starts 0/1/2/3/4/5/7/8, injected transaction failure, verified backups, additive rows/schema preservation and repeated invocation.
- Frontend tests exercise all five choices, whole-snapshot denominators, explicit-only screening, empty-result caveats, accepted review display, candidate road links, selection reset, route validation, and rejection of foreign-release or fabricated confirmed-conflict payloads. Existing M7/M8.1 and synthetic tests remain included.
- Original canonical fingerprint digests: M7 `f90ea52fdd9991b8b870b9e2f8270404f4eb00dd27e699fa304dbd6e5a6a3838`; M8.1 owner DB `9a1347ea0fa3462d0c569bc8212c2ac16db06dd04c3a8800b6a9876c70d459f7`. These use `digest(fingerprint(conn))`; the migration CLI's noncompact serialization fingerprint differs by convention, not content. Backup copy was verified equal before migration. No migration/downgrade was run on either original DB.

Recovery: stop writers; preserve failed archive/report/DB rather than overwrite; use verified private backup in a **new path**, run integrity/foreign-key checks and compare the pre-migration fingerprint before explicitly selecting the recovered DB/pin. No destructive downgrade or table rewrite. Simulated migration/publication rollback and actual backup identity are verified; disk-full, process-kill/power-loss, permissions failure, and multi-process cache/performance certification have not been exercised. Runtime archives/DBs remain ignored; historical and synthetic fixture files are unchanged.

Final verification: the initial report and independent replay were byte-equivalent as parsed JSON, including projection/screen hashes. The final verifier additionally checks stored published release/association rows and reports administrative-date missingness/application groups; its expanded report hash above is authoritative. All 23,047 records have usable ordered administrative windows and nonmissing issue dates (unknown-date pools both 0); there are 2900 repeated application-ID groups (not duplicate permit primary keys). Actual schedules remain unknown for every record. Final projection timing under concurrent test load was 10.051 s; these observations do not establish a performance SLA.

Local browser verification against the isolated snapshot/release: actual whole-snapshot counts/release and date disclosures loaded; the selected South Street permit exposed 136 candidates; explicit screening showed 314 findings with 30 displayed, Unknown actual work overlap and a load-more control; selecting Located returned 0 records with incomplete-coverage wording and unchanged whole-snapshot denominators. Permit-number search, explicit record deep link and back-to-list navigation were checked; candidate road-link construction is covered by component tests. No external basemap was configured. Only loopback development servers were started; sandbox bind restrictions required authorized escalation. The servers were stopped after checking.

Files added for this stage: `apps/api/app/services/permit_intelligence.py`, `apps/api/app/schemas/permit_intelligence.py`, `apps/api/tests/test_m8_permits.py`; `apps/web/src/features/permits/PermitEvidence.tsx` and its test; `scripts/verify_m8_2.py`; this report and the aggregate coverage JSON. Existing ingestion/acquisition/CLI, schema migration, intelligence repository/review builder, v2 routes, Projects/types/services/routing/tests and shared contracts were extended. Earlier uncommitted M8.1 map/policy files were preserved, not attributed to this stage.

Post-check preservation audit: both original full fingerprints still match; all preexisting rows across 28 backup tables survive in the schema-9 isolated copy (SQL EXCEPT comparison), and integrity/foreign-key checks pass. Final documentation check validated relative links and fenced blocks in 11 touched documents plus aggregate JSON parsing; `git diff --check` passes. No synthetic fixture or dependency-lockfile change was present.
