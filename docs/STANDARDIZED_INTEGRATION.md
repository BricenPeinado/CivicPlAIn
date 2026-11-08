# Standardized NYC Map integration — 2026-11-08

Focused owner-authorized integration of the supplied derived application read model. No additional NYC download, database rebuild, new matching pipeline, migration, dependency, deployment, commit or push. Existing verification/engineering gates remain unchanged.

## Start locally

Run from the repository root in two terminals. The already prepared ignored `data/tmp/standardized-integration.sqlite3` is a SQLite backup copy of the existing schema-12 M8.6 planning database; original databases and saved results are preserved. The standardized artifact was extracted unchanged from the supplied ZIP to its requested ignored path. Its supplied README is retained as `README_CivicPlAIn_standardized.md`; its transformation script was not executed.

```sh
CIVICPLAIN_DATABASE_PATH="$PWD/data/tmp/standardized-integration.sqlite3" \
CIVICPLAIN_STANDARDIZED_DATABASE_PATH="$PWD/data/processed/CivicPlAIn_standardized.sqlite3" \
CIVICPLAIN_DATA_MODE=official \
CIVICPLAIN_OFFICIAL_SNAPSHOT_ID=nyc-4620b9e30c1c0bd5be4252fe27999c80 \
CIVICPLAIN_ALLOWED_ORIGINS=http://127.0.0.1:5191 \
PYTHONPATH=apps/api .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8091 --no-access-log
```

```sh
VITE_API_BASE_URL=http://127.0.0.1:8091/api/v1 \
VITE_MUNICIPAL_API_BASE_URL=http://127.0.0.1:8091/api/v2 \
VITE_BASEMAP=local npm run dev --prefix apps/web -- --port 5191
```

Open [White Street](http://127.0.0.1:5191/#/map?mode=official&snapshot=nyc-4620b9e30c1c0bd5be4252fe27999c80&road=road-0003cbb8adbb7e90987b689e). Stop each server with Ctrl+C in its own terminal. Existing 8000/5173 processes were preserved. Their running API currently returns 200 for the formerly reported missing decision-support summary, **but 404 for the newly added standardized route**. The freshly launched 8091 API returns 200 for both; 5191 explicitly targets it for v1 and v2. Use the matched pair above or restart both ordinary services with equivalent paths/pin/base URLs; frontend refresh alone cannot upgrade an old backend.

## Delivered behavior

- Same FastAPI application: configurable read-only standardized repository and three GET endpoints under `/api/v2/standardized/roads/{road_id}` (profile, `/pavement`, `/permits`). Exact source snapshot and road identities; explicit missing/incompatible/mismatched errors, bounded deterministic pagination. SQLite URI `mode=ro`, `query_only`, context validation and connection closing. No startup ingestion or silent synthetic fallback.
- Same Map: primary **Indicative pavement condition**, original numerical rating/date/count, **Permits naming this street**, and expandable activity lists. These name matches are available without approval as presentation evidence. Cross-street mentions are excluded. Stored profile values are not replaced by the existing whole-road engine's unknown result.
- Existing selected-segment geometry/highlighting/search/list/routes are reused. Street-level observations may be shared among several LION rows; the screen says so. Segment verification, source history and accepted/candidate permit review remain separately available in a closed disclosure. Repair planning/saved decisions remain on demand; a linked estimate opens its disclosure. No indicative values are sent to suitability, prioritization, screening, AI or saved-calculation inputs.
- Abort controllers, keyed components and returned-context checks suppress stale responses and reset expanded-record state when street/snapshot changes. Related records load only on expansion, ten at a time; Load more appends subsequent stable pages. No data is reported as a real zero after an API error.

## Actual local verification

Source artifact schema/metadata inspected read-only; integrity and record counts verified. Counts: 4,150 roads, 8,726 pavement observations, 23,047 permits, 249 normalized names. Exact requested road IDs and geometries were compared to the existing official API. Every related page for these five roads was compared with the selected-road database view: all IDs equal, no duplicates, no unrelated cross-street-only permits.

| Street | Rating | Indicative category | Named observations | On-street permits |
| --- | ---: | --- | ---: | ---: |
| WHITE STREET | 4.91 | Fair | 53 | 33 |
| AVENUE OF THE AMERICAS | 9.69 | Good | 8 | 0 |
| PIKE SLIP | Unknown | Unknown | 0 | 20 |
| MANHATTAN BRIDGE | Unknown | Unknown | 0 | 0 |
| FRONT STREET | 2.66 | Poor | 54 | 37 |

Actual running browser, local basemap, matched 5191/8091 pair: selected all five streets through search/list; verified displayed ratings/bands/counts and corresponding road IDs; expanded White Street observations/permits, loaded all 33 permits; verified empty lists; navigated to Overview and back, refreshed with selected Front Street restored; switched to Synthetic fixtures and selected demo-r-001, opened all three repair previews ($8,160 / $172,500 / $53,400). Full automated regressions cover synthetic screening/scenarios/AI and official planning/replay; this focused browser run is not a repeat of the entire historical accessibility or planning matrix.

Commands:

```sh
PYTHONPATH=apps/api .venv/bin/python -m pytest apps/api/tests -q
npm test --prefix apps/web -- --reporter=dot
npm run build --prefix apps/web
# build invokes TypeScript noEmit before Vite; also run independently during development:
npm run typecheck --prefix apps/web
git diff --check
```

**Final checks:** 506 backend tests and 147 frontend tests passed; TypeScript and production build passed; `git diff --check` passed. Backend reported 341 preexisting deprecation warnings. Vite retained its existing large MapLibre chunk warning. SHA-256 checks of all 21 preexisting SQLite files (20 original databases plus the standardized artifact) found no byte changes. Standardized integrity check: `ok`; artifact SHA-256 `4b2f298b4903dbace7de5cd1f2c0dc29567e0c86ada8d76e8ee55352fc612752`. Local ignored evidence: `data/processed/standardized-live-verification.json`, `standardized-preservation-before.json` and `standardized-preservation-final.json`. The final browser also selected White Street directly from its map line after clearing selection, producing exactly `road-0003cbb8adbb7e90987b689e` and the expected primary evidence. New API tests use an authored miniature synthetic read-model database, never copied official records. Tests cover schema/file/snapshot/road errors, invalid row data, limits, pagination, cross-street exclusion and byte-identical read preservation. Frontend tests cover indicative values, explicit failures/retry, stale response cancellation, lazy activity reads and foreign context rejection; existing verification assertions now explicitly open their disclosure. Automated tests do not fetch NYC data or external tiles.

## Changed files and remaining boundaries

Backend: `core/config.py`, `core/standardized_repository.py`, `routes/standardized.py`, `main.py`, `tests/test_standardized.py`. Frontend: `services/standardized.ts` and tests, `features/standardized/StreetEvidence.tsx` and tests, existing `OfficialMapPage.tsx`, its tests and `Navigation.test.tsx`. Configuration/docs: `.env.example`, README, supplied dataset README, shared PRODUCT_SPEC/DATA_MODEL/API_SPEC/ARCHITECTURE, roadmap and this report. Existing uploaded ZIP/gzip files remain untracked and untouched; runtime artifacts remain ignored.

The name-only read model is deliberately not segment-level verification, a permit footprint, excavation clearance or a construction schedule. Old snapshots cannot use this newer artifact. Original verified map filters/overlays/Overview retain their own evidence semantics; the primary selected-street inspector uses indicative semantics. No earlier M8 engineering gate is declared complete by this integration. Next milestone remains the separately authorized source/planning-evidence work; none was started here. Existing Shapely/Starlette deprecations and the large MapLibre bundle remain.
