# M7.1 — Official NYC data integration

Implemented and verified **2026-11-07 America/New_York / 2026-11-08 UTC**. Backend integration only; existing web design/navigation, deterministic calculations, synthetic fixture bytes and historical milestone reports are unchanged. No commit/push, dependency installation, paid AI call or deployment was performed.

## Result and honest scope

One existing FastAPI/sqlite3 application now supports reviewed official NYC snapshots alongside the existing synthetic database contract. Explicit local acquisition → offline typed staging/quarantine → report-hash approval → atomic immutable publication. Source/network failures never substitute fixtures. The ordinary runtime database was not modified; actual official records are in a **new ignored isolated** `data/tmp/m7-official-pilot.sqlite3`, containing the synthetic workflow records as well as official sidecars. Default configuration remains synthetic.

Initial snapshot **`nyc-3947b35876a619b31067db96b1409ad8`**, full manifest SHA-256 `3947b35876a619b31067db96b1409ad88a81b27606b79894a8e4704e5bb523b2`, published `2026-11-08T00:26:27.345252+00:00`. Acquisition started `2026-11-08T00:20:11.757223+00:00`; that timestamp is retrieval, not inspection. Evidence bundle: ignored `data/raw/nyc-2026-11-07-pilot-04/`; reviewed report: ignored `data/processed/m7-1-review-01.json`. Report SHA-256 `323027a1f267c6599bbb4119dc524054bee62dbdd5ecba59b334ff150b17a73d`. Artifacts are retained locally and are not packaged as synthetic or committed extracts.

| Layer | Raw | Accepted | Duplicates / rejects / excluded | Link status |
| --- | ---: | ---: | --- | --- |
| DCP LION regular street rows | 4,150 | 4,150 | 0 / 0 / 0 | SegmentID may repeat; export rows preserved |
| DOT pavement observations | 8,726 | 8,726 | 0 / 0 / 0 | 8,726 ambiguous/unreviewed candidate sets, 0 accepted road links |
| DOT construction permits | 4,735 | 4,735 | 0 / 0 / 0 | 4,735 unmatched/unlocated street-name candidates; no source OFT supplied in this selection |
| OTI shoreline features | 3 | 3 | 0 / 0 / 0 | Separate geographic context |

There are **17,614 imported records**, 13,461 match decisions, four revisions and one snapshot/publication audit. All 8,726 selected pavement observations are dated, ranging from **2006-10-20 through 2026-08-29**; a recent feed update does not make old inspections current. Road categories remain unknown; zero classified poor/good/fair means classification unavailable, not absence of those conditions. Permits have **0 confirmed in-scope / 4,735 scope candidates**. Do not add unlocated to the match buckets: it overlaps them.

Pilot bbox is [-74.020,40.700,-73.985,40.725]; context [-74.030,40.695,-73.980,40.730]. Chosen application extents, not an official neighborhood boundary. All intersecting supported full geometries are retained, with no clipping or first-N sample. Permit selection is **MANHATTAN, issue date ≥2026-10-01, on-street name in selected LION streets**, partitioned in sets of 20. It can include distant stretches of long streets and omit aliases/unknown names/older permits still in effect. This is not complete geographic permit coverage.

## Verified sources and field decisions

Exact downloadable dictionaries/attachment IDs and full name/type arrays are pinned in `ingestion/registry.py` and `source_schemas.json`. Both source payloads and dictionaries were inspected; old documentation links/field assumptions were not trusted. See [DATA_SOURCES](DATA_SOURCES.md) for official links, cadence, terms and geographic coverage.

| Resource | Endpoint and revision evidence | Mappings / constraints |
| --- | --- | --- |
| DCP catalog **2v4z-66xt** | External ZIP catalog; not a `/resource` table. Official bounded acquisition uses `https://services5.arcgis.com/GfwWNkhOj9bNBqoJ/arcgis/rest/services/LION/FeatureServer/0/query`; metadata `.../0?f=json`. Item **db6fdacfc5ff44e7a244e2f798d98a7d**, owner **DCP_GIS**, organization **GfwWNkhOj9bNBqoJ**, DCP attribution verified. EditingInfo data/schema marker **1787338583319** = 2026-08-21T18:56:23.319Z. Catalog says quarterly/26c, which is not asserted equal to this service revision. | `FeatureTyp='0'`, LBoro/RBoro=1, OBJECTID, SegmentID, Street/StreetCode/nodes and native polyline paths. Native 102718/latestWkid2263, US survey feet. pyproj always_xy transforms EPSG:2263 →4326; full original paths/attributes retained. SegmentID repeats: row key `SegmentID:OBJECTID`; OIDs are not durable across a future service rebuild. |
| DOT **6yyb-pb25** | `https://data.cityofnewyork.us/resource/6yyb-pb25.json`; metadata `/api/views/6yyb-pb25.json`; rowsUpdatedAt **1793531948** = 2026-11-01T11:19:08Z. Publisher monthly, underlying daily. | `the_geom` WGS84 MultiLineString, oftcode, systemrating decimal, inspection floating datetime, nonratingreason, direction/road_type/ismultipass, names. SODA `:id AS source_row_id` is preserved. Current dictionary no longer exposes the old SegmentID/manual-rating schema. No guessed category: fractional-range gaps and local-street exception remain unresolved. |
| DOT **tqtj-sjs8** | `/resource/tqtj-sjs8.json`, `/api/views/tqtj-sjs8.json`; rowsUpdatedAt **1794081673** = 2026-11-07T20:01:13Z; daily. | PermitNumber documented PK. Preserve issue/status/type/effectiveness/expiration/modified datetimes and raw identifiers. Source borough uppercase MANHATTAN. WKT and LocationGeometry have no declared CRS in the dictionary: retain raw, normalized geometry unknown. Permit validity is not a confirmed work schedule or start. Download SELECT excludes contacts/company/narrative and unrelated measurements. |
| OTI **59xk-wagz** | `/resource/59xk-wagz.json`, `/api/views/59xk-wagz.json`; rowsUpdatedAt **1713989156** = 2024-04-24T20:05:56Z; as needed, Planimetrics 2022 metadata. | WGS84 MultiLineString the_geom and source_id/feature/status. Display context lines; no fabricated land polygon or inferred utility boundary. |

Socrata GeoJSON is serialized longitude/latitude; this is separate from the native CRS of an agency's underlying geodatabase. Permit WKT is not GeoJSON and receives no inferred CRS. System-provided metadata/schema/update markers and source counts are compared before/after acquisition. APIs do not guarantee transactionally consistent exports; these checks detect observed changes, not every possible concurrent edit.

### Content evidence

Raw hashes below are SHA-256 of canonical sorted source record sets; actual physical page hashes are retained separately on each source revision and in the acquisition bundle. This distinction avoids calling a normalized byte stream the original HTTP response. Dictionary hashes identify exact downloaded XLSX bytes.

| Source | Canonical raw-record-set SHA-256 | Dictionary SHA-256 |
| --- | --- | --- |
| LION | `290d1fc4b9f6c428e419c05fd6140c49bf3d04c9a00cb79aae9cb7f5bd5263c1` | `b37b4466ef79abf2153cedf7a7a925a779a3ea3dda8d80ccbc61b8ece33c6038` |
| Pavement | `3adaf801340745327fee0d5508da977dd9ada0d7cefb7c34f7c6a320aaa195e4` | `2964de73020454a6bd7053b0cc969b4946633a6eb5bf88f87c0ec560e10a1a50` |
| Permits | `206d4a7a409c3240c5a9dd8ad2a675d5f05a80f576ba77c701b5d20a3c4113a1` | `a188e14e7e635b3422d39146b437883dea47f78f4ba236fdd04e9f51086002da` |
| Shoreline | `4be627dae6270ae13d0c3ae895161abf8ef04dbd2ee4a83a4d9945ad60d2be44` | `878a926faec5f8480ab5f7eddb8f2b7fcd8ec3fd75e016e4abc2c2a2122ea8a6` |

No standardized licenseId was supplied. Official portal/city/DOT terms and DCP use limitations were reviewed, without assuming a CC/public-domain grant. Portal terms HTML is hash-verified; city/DOT pages returned 403 to automated curl while being readable through official web browsing, so only reviewed URLs/profile are recorded for those pages. DOT requires an application disclaimer: source provenance flags that requirement and links the official text. Future UI/redistribution must satisfy applicable attribution/disclosure; this local archive is not blanket production/redistribution clearance. No attempt bypassed an access restriction.

Trace-back smoke samples (public source fields only): WHITE STREET, SegmentID `0032075`, OBJECTID `106200`, StreetCode `145290`, first transformed coordinate approximately [-74.0015882484,40.7172918940]; pavement source row `row-9gcn-w62x_fe6j`, OFT `120090116310129890`, raw rating `3.38`, inspection `2025-08-03T00:00:00.000`; permit `M022026301E71`, issued `2026-10-28T15:28:12.000`, OFT and mapped location unknown. These were read from published records traceable to archived source pages, not authored examples. They are not a claimed relationship to each other.

## Matching and missingness

The documented DOT OFT code is three concatenated six-digit on/from/to street codes. Equal full OFT values create inspectable same-location groups across DOT records; multiple directions/passes remain distinct. It is not a unique LION SegmentID and is never truncated into a confirmed segment key.

For spatial candidates, transform source geometries to EPSG:32618, build a Shapely STRtree, query a 5 m buffer and retain road geometries with minimum distance ≤5 m. Store candidate IDs, distances, street-code agreement, CRS, method/tolerance and ambiguity reason. This is a screen, not an accuracy/conflict claim. An unlocated OFT can suggest all selected roads with StreetCode equal to its first six digits; names alone do not accept a link. Parallel streets/grade separation/long road segments remain ambiguous. No closest/unique candidate is auto-promoted.

Optional reviewed decisions JSON is keyed by normalized condition/permit record ID, each `{road_id,record_hash,reviewer,reason}`. The complete normalized record content hash must match and target must be an eligible candidate. Changed source content makes stale reviews fail; decisions enter snapshot identity. Initial import uses **no reviewed decisions**. A matched road reference still does not create a permit footprint. Unknown dimensions/utility coordinates/depths, prices/traffic/budget, construction start/schedule and decimal category remain null with reasons.

## Commands and safe operation

From the repository root, using installed pinned dependencies. No provider key is needed. Acquisition requires verified HTTPS and system `/usr/bin/curl`; no redirects/arbitrary URLs/archive expansion. Each request is capped at 25 MB, 30 seconds per attempt, two bounded transient retries. LION batches contain 100 OIDs to avoid URL-size limits; Socrata pages contain 1,000 rows. Selection caps block rather than truncate. Earlier failed acquisition directories are retained without a completed acquisition.json; they were never published.

```sh
# Stop writers before migrating any existing database. Use a new ignored path to leave the ordinary DB intact.
PYTHONPATH=apps/api .venv/bin/python -m app.migrate --database data/tmp/official-new.sqlite3 --backup data/tmp/official-new-before-v7.sqlite3
PYTHONPATH=apps/api .venv/bin/python -m app.ingest acquire --output data/raw/nyc-next --permit-since 2026-10-01
PYTHONPATH=apps/api .venv/bin/python -m app.ingest dry-run --acquisition data/raw/nyc-next/acquisition.json --report data/processed/nyc-next-review.json
# Inspect report and source evidence. Substitute its exact report_hash after review:
PYTHONPATH=apps/api .venv/bin/python -m app.ingest publish --acquisition data/raw/nyc-next/acquisition.json --database data/tmp/official-new.sqlite3 --approve-report <reviewed-hash>
```

Dry-run writes no SQLite/schema state and refuses an existing report path. Raw/output directories and backup paths must be new. A nonzero quarantine requires explicit `--allow-rejects` in addition to approved report hash; rejected rows/reasons remain in original evidence/report. Unknown schema/resource, incomplete page or changed marker fails closed. Acquisition is separate from publication, so a timeout cannot erase an earlier snapshot. Only successful publication creates import_runs audit; failed/acquired attempts remain disk evidence, not a resumable job queue.

For a refresh, acquire into a new directory, review a new report, publish; records never update in place. Same bytes/query/versions/decisions reuse the snapshot despite changed retrieval time. Changed source or decisions produce a new snapshot with added/changed/removed record diff and previous snapshot ID. Pin the new snapshot explicitly only after review; no global automatic activation. Physical page-byte changes can change source revision identity even when normalized records are semantically equal. IDs based on source OIDs can change after upstream rebuild; removed/new rows do not mean physical streets vanished/appeared.

Start the backend against this checkout's actual imported snapshot:

```sh
CIVICPLAIN_DATABASE_PATH="$PWD/data/tmp/m7-official-pilot.sqlite3" CIVICPLAIN_DATA_MODE=official CIVICPLAIN_OFFICIAL_SNAPSHOT_ID=nyc-3947b35876a619b31067db96b1409ad8 PYTHONPATH=apps/api .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

GET `/api/v2/workspace`, `/api/v2/data-snapshots`; data reads require explicit snapshot_id, e.g. `/api/v2/conditions?snapshot_id=nyc-3947b35876a619b31067db96b1409ad8`. Read routes, limits/errors are in [API_SPEC](API_SPEC.md). Official mode requires a valid published pin and has no fallback. V1 always remains synthetic; the current web client still reads v1. VITE_MUNICIPAL_API_BASE_URL is reserved, not wired into the client yet.

### Migration and recovery

Explicit schema 7 / `m7-official-snapshots-v1` adds six tables and immutable triggers/indexes, following old schema 5 (no schema 6). The existing startup initializer does not migrate 7 or ingest. Migration inspects history plus required DDL shapes, integrity/FKs; rejects malformed/future schemas; creates a new mode-0600 backup using SQLite backup API including committed WAL; compares all preexisting complete rows and schema/trigger definitions; then runs older required additive DDL plus 7 in one transaction. No table rebuild, ID mapping, JSON rewrite, reset or reseed is required. Repeat valid migration is a verified no-op.

For the actual isolated pilot, every preexisting row across the 20 legacy tables and schema object compared equal to `data/tmp/m7-official-pilot-before-v7.sqlite3` after migration/publication. Integrity check is `ok`, foreign_key_check has zero findings. Original user database was never selected for migration/import. Recovery: stop writers and run the prior application against the retained verified backup at a **new configured path**; retain upgraded file/evidence. No destructive downgrade/automatic overwrite. The earlier 7.0 inventory said 17 tables; actual sqlite_master inspection confirms **20**, including the M5 audit/review tables. This correction applies to current shared specifications; historical reports are retained. This is a local procedure, not a backup service or tested power-loss recovery system.

## Files and architecture decisions

| Implemented files | Responsibility |
| --- | --- |
| `ingestion/registry.py`, `source_schemas.json` | Fixed source identity/endpoints/dictionary assets/scope/caps and reviewed full schemas |
| `ingestion/acquire.py` | Verified system HTTPS, bounded OID/name/page queries, metadata/count drift checks, complete raw evidence bundle |
| `ingestion/adapters.py` | Four source-specific adapters in one small module; exact field maps, string IDs, date/decimal/geometry/unknown handling and quarantine; no duplicated adapter framework |
| `services/municipal_data.py` | Canonical hashing, native CRS transformation, indexed candidate matching and record-hash-bound reviews; no SQL/network/model calls |
| `schemas/municipal.py` | Typed records, field provenance/classification, source revisions and match status/review invariants; no v1 validator changes |
| `ingestion/pipeline.py`, `app/ingest.py` | Separate acquisition/staging/approval/publication commands, reproducible identities, atomic snapshots/diffs/audits |
| `models/migrations.py`, `app/migrate.py` | Explicit backup/DDL validation/preservation/transaction/recovery interface; legacy initializer unchanged |
| `core/municipal_repository.py`, `routes/municipal.py` | Snapshot-isolated read API, source membership, exact bbox filters, stable cursors, unmatched access and whole-snapshot summaries |
| `core/config.py`, `main.py`, `.env.example` | Validated explicit workspace mode/pin, mount v2 in existing app/HTTP error guards; v1 unchanged |
| `tests/test_m7_ingestion.py`, `test_m7_migrations.py`, `test_m7_api.py` | Offline synthetic source-shaped tests and disposable migrations/API checks; no live service dependency |
| README, roadmap, architecture, data/API/source/limitation/product/AI/responsibility docs, AGENTS and M7 plan | Concrete implemented status/contracts/commands/caveats; historical reports retained |

Deliberate refinements of M7.0 proposals: use the official bounded ArcGIS service rather than a large FileGDB; share four small adapters in one module; common compact `values`/field provenance DTO; use `condition` kind and `/conditions` for all unmatched observations; no unsupported category normalization; no unknown-CRS permit transformation; compact aggregate provenance envelope rather than repeated wrappers; all four pilot layers required rather than pretending optional-layer behavior exists. Failed imports stay disk evidence; only successful publications enter import_runs. These are reconciled in the shared contracts. No new infrastructure/dependencies or second calculator/application.

## Verification

Commands actually run:

| Command/check | Outcome |
| --- | --- |
| `PYTHONPATH=apps/api .venv/bin/python -m pytest apps/api/tests -q` | **265 passed**, 20.26 s on the final full run: 212 preserved regressions +53 new tests; 70 deprecation warnings (existing TestClient adapter and new Shapely transform calls). |
| `python -m app.ingest --help`, `python -m app.migrate --help` with PYTHONPATH/venv | Commands/help work; no schema writes from help |
| Actual fixed-source acquire, dry-run and reviewed publish | Four layers, zero rejects; 17,614 records published atomically; exact repeat returned `unchanged` |
| `git diff --check`, all local Markdown link targets and new-file whitespace check | Pass; apps/web, data/demo and IDE files unchanged; runtime extracts/DBs ignored |
| Actual isolated database / verified backup comparison | Every old row/schema object preserved; integrity ok/FK zero; private retained backup |
| TestClient against actual imported DB, explicit official config | Workspace/dashboard/roads/conditions/permits/context/v1 health all HTTP 200; provenance samples above traced to source pages |

Offline tests cover exact/conflicting duplicates and primary keys/leading zeros, decimal dates/nulls/reversed windows, swapped/nonfinite/zero/invalid polygon geometries, CRS control point, missing CRS/OFT/unmatched rows, provenance/evidence tampering, reviewed/stale candidates, report approval, repeated and changed snapshots, SQL rollback on broken references, allowlisted fetches/HTML/API errors/page caps/truncation, empty/M1–M5 migration shapes, malformed/future schema, busy writer/committed WAL/private backup/full saved-output preservation/injected rollback, unchanged v1, strict query/mode/snapshot membership/cursors, bbox/GeoJSON, unlocated filtering and dashboard denominators. Test SQL/API harness records are expressly synthetic_fixture; no test fixture is presented as a live imported observation.

Observed warm local TestClient reads on this actual snapshot: workspace 0.016 s, dashboard 1.137 s, three roads 0.258 s, two conditions 0.669 s, two permits 0.262 s, shoreline 0.039 s; these are individual samples, not guarantees. Database approximately 125 MB due to full geometry/raw lineage/candidate evidence, retained locally. GeoJSON viewport >2,000 features requires refinement; no citywide or real-browser map performance acceptance. Existing Starlette/httpx and Shapely transform deprecation warnings are reported, not hidden by a dependency change.

Remaining limitations/questions: authoritative permit CRS and geographic completeness; upstream OFT sparsity and LION repeated/rebuilt IDs; supported decimal categories/local-street mapping; human-reviewed road matches; required DOT notice rendering during 7.2; redistribution/product terms; current bounded Python materialization/geometry lineage storage; actual disk-full/power-loss recovery and exhaustive audit-history/OS variants unrun. Frontend redesign/browser/accessibility checks are intentionally not part of 7.1; frontend tests/typecheck/build were not rerun because no frontend/dependency changes were made (7.0 baseline remains separate). Real costs/traffic/budgets/schedules/utility data/AI predictions are unavailable. Next milestone: **7.2 map-first client integration and design**, with these unknowns visible.
