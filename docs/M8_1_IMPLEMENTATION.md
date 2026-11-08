# M8.1 — Official NYC pavement condition integration

> **Current follow-up (2026-11-08):** [Owner-approved pilot implementation](M8_1_PILOT_IMPLEMENTATION.md) records five approved associations across five roads, a separate approved project grading policy, isolated publication and current test/gate results. Four accepted observations grade Good; all road conditions remain Unknown due to partial scope. The zero-acceptance metrics and pending-review statements below describe the **pre-approval checkpoint**, retained for audit. Full M8.1 remains partial; M8.2 has not started.

**Status: implemented review foundation and conservative condition projection; acceptance gate remains partial. M8.2 has not started.** Local work dates: 2026-11-07–08 America/New_York. The A1 positive-evidence gate still requires human-reviewed actual associations for at least five observations across three LION rows. Current accepted coverage is **0 / 8,726 observations and 0 / 4,150 road rows**. No automatic nearest-road promotion or unsupported classification was introduced.

The subsequent [authoritative verification and proposed decisions](verification/m8.1-pavement-lion-decisions.md) records exact source applicability, complete-denominator coverage, an unreviewed five-pair investigation shortlist, executable offline verification and per-requirement PASS/FAIL/BLOCKED status. It is **Proposed — Pending Review**, not an approved matching or classification policy. Current follow-up checks: **343 backend tests / 98 frontend tests passed**, build including type check passed; two complete offline reports match. The earlier checks below retain their original results.

## Scope and baseline

Inspected the actual working branch `bp/specify-civicplain-milestone-7`, HEAD `19b4d5e`, preserving the uncommitted M8.0 documentation. Read AGENTS, README, M8 plan, roadmap, shared contracts and M7 implementation/final QA. The user’s M8.1 instruction explicitly includes condition summaries, recency and the official map inspector: those read-only parts are included here, superseding the original plan’s exclusion of condition UI from 8.1. This does not begin M8.2’s broader condition-policy stage, costing or planning engines.

The original `data/tmp/m7-official-pilot.sqlite3` remains pinned to `nyc-3947b35876a619b31067db96b1409ad8`, schema 7, 4,150 road rows, 8,726 condition records, 4,735 permits and three context records. Original pavement matches remain 8,726 ambiguous; original permits remain 4,735 unmatched. No historical snapshot, v1 fixture, imported record or old match was edited. There is no dependency installation, remote branch assumption, commit, push or deployment.

## Source verification and classification decision

Fetched the current official [dataset metadata](https://data.cityofnewyork.us/api/views/6yyb-pb25.json) and its attached [DOT data dictionary](https://data.cityofnewyork.us/api/views/6yyb-pb25/files/0582f80f-e210-4d2d-91e2-9e0a14917ee5?download=true). Inspected the XLSX XML with the standard library, without installing a reader. The current column names/types exactly match the archived acquisition, and the dictionary bytes have the same SHA-256 as the archived source revision. This verifies metadata/dictionary continuity, not that new live observations were acquired.

| Evidence | SHA-256 / finding |
| --- | --- |
| Downloaded metadata | `9cb83005926075383761a3311b9264a93423d5a686613aaf7818ed7d3f6f3cf4` |
| Attached dictionary | `2964de73020454a6bd7053b0cc969b4946633a6eb5bf88f87c0ec560e10a1a50` |
| Version boundary | Mutable feed; the archived source-revision/content hashes define the processed version, not the present source update timestamp. |

Exact current public fields: `the_geom` (multiline), `oftcode` (text), `boroughname`, `onstreetna`, `fromstreet`, `tostreetna` (text), `ismultipass` (number), `direction`, `road_type` (text), `systemrating` (number), `nonratingreason` (text), `inspection` (calendar_date), `locationgeometry_stlength` (number). Internal Socrata columns are excluded from this list.

- OFT is three six-digit on/from/to street codes, **not** a LION SegmentID. Preserve leading zeroes. Duplicate LION SegmentIDs remain distinct export rows through their row/OID identities.
- The dictionary defines SystemRating as 1.00–10, up to two decimal places, while its category table includes Poor 0–3. It gives Fair 4–7 with a local-street exception at 7, and Good 8–10. It does not fill the open decimal gaps between 3 and 4 or between 7 and 8. `Main`/`Service`/`OverPass`/`UnderPass` are road-type values, not evidence that a road is functionally a local street.
- `inspection` means collection date/time. It is retained as a source floating/local timestamp, without assigning a timezone. Metadata update, acquisition and publication dates never become inspection dates.
- `ismultipass` identifies multiple road-type/direction combinations. The dictionary does not establish an averaging or precedence rule. `nonratingreason` says why a rating was not conducted, including weather, duplicate, construction and multipass reasons; a simultaneous numeric score does not resolve that contradiction.
- Source GeoJSON is normalized through the existing reviewed adapter. Its archived CRS/transform lineage is retained. The dictionary mentions native StatePlane/US feet for geospatial length; this does not justify treating the optional length as a surveyed repair dimension or guessing permit-WKT coordinates.

The [older DOT metadata](https://www.nyc.gov/html/dot/downloads/pdf/street-pavement-rating-metadata.pdf) and [2025 DOT indicator definitions](https://www.nyc.gov/assets/operations/downloads/pdf/mmr2025/dot_idf.pdf) describe different category schemes. The newer PCI boundaries (<2.7, 2.7 to <6.7, ≥6.7) are **not established as applicable to these archived SystemRating assessments**. A current attachment can itself contain historical guidance. No interpolation, rounding to an integer, generic PCI conversion or inferred local-street exception is activated. `category=unknown`, reason `OFFICIAL_POLICY_APPLICABILITY_UNRESOLVED`, applies consistently. The Good/Fair/Poor map options are visibly unavailable until that source gate is resolved.

## Implemented association architecture

Reuses `services/municipal_data.candidate_matches` and existing adapters/snapshots. `reviewed-candidates-v1` and original acquisition/dry-run/publication semantics remain unchanged. The existing `app.ingest` entry point gains **read-derived overlay** subcommands, not another source importer.

`reviewed-candidates-v2` validates full municipal geometry/record boundaries and duplicate input IDs. It retains the reviewed UTM18N ≤5 m minimum-separation screen and existing unlocated OFT-prefix candidate logic. Candidate evidence adds exact source/target content hashes, whitespace/case-normalized on-street name agreement, exact on-street code agreement, and buffered road/observation intersection-length fractions rounded to six decimals. Source direction and road type are exposed; roadbed and grade agreement remain `unknown`. Name agreement, identifier agreement, high overlap, unique proximity and ties **never auto-accept** a link. From/to topology, aliases and grade/roadbed identity cannot be verified from the current nine-field LION extract; those remain review limitations.

`schemas/road_intelligence.AssociationReview` requires exact base snapshot, source/target IDs and hashes, candidate hash, parameter hash, accepted/rejected status, whole-road/partial scope with rationale, reviewer label, reason and nonblank evidence references. Reviews are local annotations, not verified municipal identity or engineering approval. Duplicate pair decisions, wrong context, blank rationale/evidence, stale hashes and ineligible targets reject the entire stage. Zero, one and multiple reviewed targets per observation are supported. A new release is required to change a decision.

Schema **8 / `m8-road-intelligence-v1`** adds only:

- `intelligence_releases`: immutable ID/full manifest hash, base snapshot FK, source/runtime/parameter/decision/content hashes, coverage counts and first publication timestamp.
- `road_associations`: release/base/source/target membership FKs, immutable candidate/accepted/rejected/unmatched payloads, scope and review evidence. Multiple target rows represent one-to-many observations. Source/target duplicate pairs are disallowed within a release. Null target is reserved for unmatched observations.

Both tables reject UPDATE and DELETE. Publication reproduces the staged artifact from the stored base and reviews, verifies report/full content hashes and commits the release plus every association in one transaction. No browser mutation endpoint, background refresh, startup migration or automatic release selection exists. Properly labeled synthetic harness records cannot enter production overlay staging; synthetic tests are isolated and never counted as official coverage.

## Condition projection and map

Pure `services/road_conditions.summarize` / **`road-condition-v1`** is a read projection, with typed response models. It reads all accepted evidence for the requested road/context, independently of history-page size or map viewport:

1. Only accepted v2, explicitly reviewed whole-road scope can supply the road’s current summary. Legacy links without scope review and partial links remain in accepted history with an ineligibility reason.
2. Require an interpretable floating inspection timestamp not after explicit `as_of_date`, a finite reported rating in 1–10, no non-rating reason, known direction/road type, and explicit non-multipass source flag. Original 0–<1 ratings remain in history but cannot become a current rating while the dictionary’s scale/zero discrepancy is unresolved.
3. Preserve separate direction/roadbed streams. Multiple eligible streams make the scalar summary unavailable; nothing is averaged. Multipass and missing pass metadata remain unavailable pending a reviewed selection rule.
4. Select the latest eligible timestamp within the single remaining stream. Different numeric scores at equivalent latest timestamps yield `CONFLICTING_LATEST_RATINGS`. Identical scores use stable ID order without averaging. Exact original decimal text is retained. Identical duplicate IDs deduplicate; conflicting duplicate IDs fail validation.
5. Keep all accepted history, eligibility/reason, raw rating/date/non-rating/pass/direction/type, source revision, record hash and association hash. “Latest eligible” is a selection rule, not a claim about current physical condition or every unassociated pass.
6. Age is `as_of_date - source inspection calendar date`. Recency is unknown without a selected record or explicit threshold; stale is strictly `age_days > stale_after_days`. Threshold bounds are integer 0–36,500. The UI’s editable initial 365 days is an application planning assumption, not DOT policy. Its initial reference date is snapshot publication, expressly not inspection date.

Input/result hashes bind method, snapshot, release, road, date, threshold and complete accepted record/association hashes. Projection field classifications retain original rating/date classifications and label recency outputs derived, comparison date/threshold planning assumptions, and unavailable values unknown. There is no wall-clock input or persisted projection/audit write. The base snapshot/release retain evidence needed to reproduce the result offline; original raw values remain unchanged.

OfficialMapPage adds explicit reviewed-release selection, release coverage denominators, as-of/age controls, supported rating or unknown reason, accepted assessment history and source/hash lineage. No release activates automatically. The overlay selector distinguishes all source observations, observations with no accepted association in the selected context, current eligible assessments across all road summaries, and accepted history excluding current assessments. Current/history selection derives the complete context before intersecting the viewport; a newer off-viewport assessment cannot cause an older viewport record to be mislabeled current. Road categories remain Unknown; no category colors are invented. Existing keyboard/list fallback and original observation inspector remain usable.

New release/date/age/overlay selection is component-local; it is not yet shareable in the hash route or retained after leaving Map. Map observations are still limited to the explicitly loaded viewport. Global current/history/unaccepted observation filters are implemented. Overview still reports the original snapshot aggregates; wider shared-route/dashboard integration belongs to later integration work and is not claimed here.

## API and commands

All new routes are GET under `/api/v2`, use the existing envelope and strict single-use query parameters, and never save an estimate/evaluation/AI interaction:

| Route | Contract |
| --- | --- |
| `/intelligence-releases?snapshot_id=…&limit=…&cursor=…` | Snapshot-bound immutable release manifests, stable ID pagination; schema 8 required, otherwise 503 `MIGRATION_REQUIRED`. |
| `/intelligence-releases/{release_id}?snapshot_id=…` | Exact snapshot membership; missing/wrong-context release 404. |
| `/road-associations?snapshot_id=…&release_id=…&road_id=…&status=…&limit=…&cursor=…` | Optional road/status filters; candidate/accepted/rejected/unmatched; cursor binds exact filters/context. |
| `/conditions?release_id=…&assessment_scope=…&as_of_date=…` | Adds all/current/historical/unaccepted scope to existing source observation/viewport reads. Current/historical require an explicit reference date. Cursor binds context/scope/date. |
| `/road-segments/{road_id}/condition-summary?snapshot_id=…&as_of_date=YYYY-MM-DD&stale_after_days=…&release_id=…` | Road/date required; optional threshold/release. Original scoped links when release omitted. Response includes exact rating/date, nullable recency, history, category/reasons and hashes. Schema 7 remains sufficient when release omitted. Wrong references 404, invalid/repeated/unknown parameters 422. |

Examples below are operational instructions, not evidence that a user DB was changed. Stop writers, preserve the original and use **new** paths:

```sh
PYTHONPATH=apps/api .venv/bin/python -m app.ingest intelligence-dry-run \
  --database <existing-schema7-or8-db> --snapshot <base-snapshot-id> \
  --report data/processed/<new-report>.json \
  --review-bundle data/processed/<new-review-bundle>.json

PYTHONPATH=apps/api .venv/bin/python -m app.migrate \
  --database <isolated-copy-db> --backup <new-private-backup> --target-version 8

PYTHONPATH=apps/api .venv/bin/python -m app.ingest intelligence-dry-run \
  --database <isolated-copy-db> --snapshot <base-snapshot-id> \
  --decisions <reviewed-decision-list>.json \
  --report data/processed/<new-reviewed-report>.json \
  --review-bundle data/processed/<new-reviewed-bundle>.json

PYTHONPATH=apps/api .venv/bin/python -m app.ingest intelligence-publish \
  --database <isolated-copy-db> --snapshot <base-snapshot-id> \
  --decisions <reviewed-decision-list>.json --approve-report <reviewed-report-hash>
```

Review bundles are ignored runtime files. Each candidate includes the hashes needed to author an explicit review; retrieve exact originals through the existing source/record APIs or base repository. No generated review template is an accepted human decision. Dry-run outputs use exclusive creation and cannot overwrite earlier reviews. Publication is idempotent. Default migration target remains 7 for existing commands; target 8 must be explicit, and no downgrade occurs on an already-newer DB.

## Actual pilot evidence and remaining gate

Executed the new overlay dry-run against the original archived pilot, with **no decisions**:

| Count | Actual |
| --- | ---: |
| Pavement observations / LION road rows | 8,726 / 4,150 |
| Candidate association rows | 85,905 |
| Observations with at least one candidate | 8,726 |
| Accepted links / accepted observations / accepted road rows | 0 / 0 / 0 |
| Unresolved observations | 8,726 |
| Observations without a candidate / rejected links | 0 / 0 |

Dry-run identity `intel-84d2be55d81c423363e54c0748779e86`; full manifest hash `84d2be55d81c423363e54c0748779e86d7666a127fa074d8136fdc39c3091a28`; report hash `b9c7e35a592195513ce82da55e3416334723da779f799f090e13c35f0770d3f2`; parameter hash `432910fd330f1797b70850e56eaf80fbf5411e9cf3fad05736564782e3434001`. Files: ignored `data/processed/m81-overlay-report.json` and `m81-overlay-review.json` (about 103 MiB). Candidate multiplicity is expected from a proximity screen, not evidence of 85,905 valid links. No acceptance percentage target rewards false positives.

An earlier exploratory v2 snapshot dry-run was also executed (report `m81-reviewed-candidates-v2.json`, 0 accepted/8,726 ambiguous). Its temporary CLI switch was removed before delivery: the final implementation keeps M7 acquisition identities unchanged and uses only the overlay path for M8 reviews. That exploratory report is not an activated or supported M8 base snapshot.

Created a **new** SQLite backup copy at ignored `data/tmp/m81-verification.sqlite3`, explicitly migrated only that copy to 8 with private backup `m81-verification-schema7-backup.sqlite3`, reproduced the archived review bundle byte-for-semantic-byte, and published the zero-acceptance candidate release there. Checked integrity/FKs and exact preservation of all preexisting rows/schema, including original official/synthetic payloads; re-fingerprinted the original pilot and confirmed it unchanged. Legacy fingerprint: `9b911881e9f53805400062e00bdb6faca9bc355963643e55cacd261bb2833e44`. This is an isolated verification release, not activation or positive human-review evidence.

## Verification and recovery

Final executed checks:

| Command/check | Actual result |
| --- | --- |
| `PYTHONPATH=apps/api .venv/bin/pytest apps/api/tests -q` | **308 passed**, 150 deprecation warnings, 26.40 s; includes existing M7/v1 regressions. |
| `npm test --prefix apps/web -- --reporter=dot` | **98 passed**, 14 files, 4.74 s. |
| `npm run typecheck --prefix apps/web` | Passed; also included in final build. |
| `npm run build --prefix apps/web` | Passed: 44 modules; existing large MapLibre chunk advisory. |
| New official overlay dry-run / isolated replay | 85,905 candidate links; 0 accepted; replay equals archived bundle; no source refresh. |
| Explicit migration/publication on isolated real-pilot copy | Passed schema 8, verified private backup, integrity/FKs, all prior rows/schema unchanged and original DB unchanged. |
| Final `app.ingest intelligence-publish` on the isolated copy with the recorded approval hash | `status=unchanged`; idempotent release `intel-84d2be55d81c423363e54c0748779e86`. |
| Changed Markdown fences/local links + `git diff --check` | Passed (12 Markdown files / 111 local links at first check); final recheck recorded in delivery. |

Real-browser development smoke used the default in-app browser on loopback API 8128 / Vite 5178, the **isolated** copy, and `VITE_BASEMAP=local` (no external tiles). Verified keyboard street list, Fulton Street selection, original-context default, explicit candidate-release selection, 0/8,726 coverage, Unknown condition/date/recency, current/history/unaccepted controls, unavailable Good/Fair/Poor options and the empty-current-overlay warning that absence is not Good. Screenshots: ignored `data/tmp/m81-browser-current.png` and `m81-browser-inspector.png`. The final code was checked again after restarting the isolated API; original and backup fingerprints were compared again after browser checks. Verification servers were then stopped. Local servers initially could not bind under sandbox; permitted loopback retries succeeded. No live provider or official planning-engine call occurred.

This bounded development smoke is not a full production-browser/device/accessibility or p95 performance gate. Those wider checks were not run and are not claimed.

Migration tests cover legacy 0/1/2/3/4/5/7, exact prior rows/schema/triggers, 0600 new backups, injected rollback and backup equivalence, malformed/future versions, repeated/current migration, committed WAL and busy writers. Overlay tests cover multiple targets, reordered inputs, stale source/target/candidate/parameter hashes, duplicate decisions, synthetic rejection, atomic publication failure/idempotence, membership/filter validation and read-only transport. Condition tests cover crossing/parallel roads, duplicate road identifiers and input IDs, malformed/zero-length geometry, different dates/timestamp spellings, raw decimal boundaries, non-rating/missing/pass/direction cases, conflicting latest values, zero-rating ambiguity, stale boundary and source/review replay hashes. Existing M7 and v1 regressions remain part of the full suite.

No dependencies were installed. Existing Shapely transform and Starlette/httpx deprecation warnings and the MapLibre >500 kB bundle advisory remain; they are not test failures. An initial frontend run failed four tests because the new GET was absent from test mocks; mocks now supply the new read explicitly and the final suite is recorded above. A root-level typecheck invocation found no script; the command was rerun in `apps/web`.

Recovery: quiesce all writers, retain the failed/new DB, verify the private SQLite backup, and reopen a verified backup at a **new path** with the prior schema-7-compatible software/pin. Do not drop new tables, downgrade markers, replace source payloads or reseed. Backup includes committed WAL. Migration transaction failure leaves the exact original schema/rows; publication failure leaves no partial release. Existing pins do not automatically select a newly published release.

## Unresolved inputs and next work

- Real human review with reproducible archived evidence for A1’s five-observation/three-road minimum, including multi-row/partial scope where defensible. No reviewed decisions were supplied or fabricated. Scope, grade, parallel-road and pass ambiguities remain unknown until supported.
- Feed/version-specific classification applicability, fractional gaps, local-street exception and non-rating/multipass selection policy. No substitute cutoffs were chosen.
- Full category policy/filter activation still depends on source evidence. Shareable release/date/age/overlay routes and release-aware Overview aggregates remain later integration work; only the bounded browser smoke below was run.

**Do not mark A1/M8.1 complete or proceed to M8.2.** The next work stays within M8.1: review actual candidates, supply applicable source evidence, publish/select the reviewed overlay on an explicitly chosen isolated DB, trace the required real associations, verify the positive reviewed-road condition presentation and rerun the affected acceptance checks. Costing, prioritization, permits, conflict/scenario execution, AI evidence extension and source refresh remain outside this change.

## Changed files

Follow-up verification also adds `apps/api/app/services/pavement_verification.py`, `apps/api/tests/test_m8_verification.py`, `scripts/verify_m8_1.py` and `docs/verification/m8.1-pavement-lion-decisions.md`; updates this report, README, roadmap and DATA_SOURCES. The audit helper's literal legacy-policy interpretation is a proposal with no runtime import, activation or approved feed applicability. See the decision record for new executed checks and actual counts.

Includes preserved/updated M8.0 planning documents; historical M7 reports and `data/demo` fixtures are unchanged. Runtime/download/review/verification DB/image artifacts remain ignored.

- Updated `README.md`.
- Created `apps/api/app/core/intelligence_repository.py`.
- Updated `apps/api/app/ingest.py`.
- Updated `apps/api/app/migrate.py`.
- Updated `apps/api/app/models/migrations.py`.
- Updated `apps/api/app/routes/municipal.py`.
- Updated `apps/api/app/schemas/municipal.py`.
- Created `apps/api/app/schemas/road_intelligence.py`.
- Updated `apps/api/app/services/municipal_data.py`.
- Created `apps/api/app/services/road_conditions.py`.
- Created `apps/api/app/services/road_intelligence.py`.
- Created `apps/api/tests/test_m8_conditions.py`.
- Created `apps/api/tests/test_m8_intelligence.py`.
- Updated `apps/web/src/Navigation.test.tsx`.
- Updated `apps/web/src/hooks/useMunicipalData.ts`.
- Updated `apps/web/src/pages/OfficialMapPage.test.tsx`.
- Updated `apps/web/src/pages/OfficialMapPage.tsx`.
- Updated `apps/web/src/services/municipal.test.ts`.
- Updated `apps/web/src/services/municipal.ts`.
- Updated `apps/web/src/test-municipal.ts`.
- Updated `apps/web/src/types/municipal.ts`.
- Updated `docs/AI_SYSTEM.md`.
- Updated `docs/API_SPEC.md`.
- Updated `docs/ARCHITECTURE.md`.
- Updated `docs/DATA_MODEL.md`.
- Updated `docs/DATA_SOURCES.md`.
- Updated `docs/KNOWN_LIMITATIONS.md`.
- Created `docs/M8_1_IMPLEMENTATION.md`.
- Created `docs/M8_IMPLEMENTATION_PLAN.md`.
- Updated `docs/MVP_ROADMAP.md`.
- Updated `docs/PRODUCT_SPEC.md`.
- Updated `docs/RESPONSIBLE_AI.md`.
