# REST API contract

**Implemented through M5; integrated/verified in M6:** the five M1 GET paths plus GET `/api/v1/road-segments/{id}/conditions`, GET `/api/v1/repair-options`, GET `/api/v1/road-segments/{id}/repair-options`, POST `/api/v1/estimates`, GET `/api/v1/estimates/{id}`. M3 additionally implements project list/detail, conflict analysis/list/detail and saved analysis retrieval below. M3.5 provided the scenario contracts; M4 implements scenario CRUD, immutable evaluation and comparison below. M5 explanation and human-review routes are implemented in the M5 section below. Base `/api/v1`, local server `http://127.0.0.1:8000`; no `/api/roads` or root `/health` aliases.


## M7 official-data read API (implemented in 7.1)

One FastAPI process serves read-only `/api/v2` alongside unchanged synthetic `/api/v1`. Contract `municipal-record-v2` is defined in DATA_MODEL. No official IDs resolve through v1 or enter v1 calculations. M7.2 uses a separate read-only v2 client for official inspection and unchanged v1 transport for the explicit synthetic planning workspace.

| Method/path under `/api/v2` | Query | Result |
| --- | --- | --- |
| GET `/workspace` | none | Configured synthetic context or explicitly pinned published official snapshot; missing official snapshot is 404, never synthetic fallback |
| GET `/data-snapshots` | limit/cursor | Published snapshots, newest publication then ID; discovery meta snapshot_id null |
| GET `/data-snapshots/{snapshot_id}` | none | Full frozen manifest and publication timestamp |
| GET `/road-segments` | snapshot_id required; bbox, q, condition, limit/cursor | Full municipal road records, unknown normalized category and provenance |
| GET `/road-segments/geojson` | same, bbox required | GeoJSON features with compact values/classifications/source identity; no raw geometry lineage/narrative in properties |
| GET `/road-segments/{id}` | snapshot_id required | Record, condition summary, lineage and unknowns |
| GET `/road-segments/{id}/conditions` | snapshot_id required; limit/cursor | Only reviewed matched condition history, source date descending then ID; latest_usable_id nullable, original decimal ratings |
| GET `/conditions` | snapshot_id required; bbox, limit/cursor | All imported observations, including unmatched/ambiguous records; added so unaccepted readings remain inspectable |
| GET `/permits` | snapshot_id required; road_id, q, status, location, bbox, limit/cursor | Administrative permit records; location all/matched/ambiguous/unmatched/unlocated; road_id selects accepted links only |
| GET `/permits/{id}` | snapshot_id required | Unlocated records remain valid detail records with raw WKT and reason, candidates and same-OFT references |
| GET `/context/geojson` | snapshot_id and bbox required; layer=shoreline, limit/cursor | Real local shoreline lines; bbox must be within approved context extent |
| GET `/source-revisions/{id}` | snapshot_id required | Source provenance only if a member of that snapshot |
| GET `/dashboard` | snapshot_id required | Whole-snapshot counts/coverage/date range/capabilities; independent of map pan and page size |

Responses use `{data,meta}`; GeoJSON uses `{type,features,meta}` and `application/geo+json`. Meta includes request_id, contract_version, snapshot_id, mode official, coverage, capabilities, warnings, returned_count, total_matching and next_cursor. Workspace has the smaller `{data:{mode,snapshot_id,...},meta:{request_id}}` selection response. No global mutation endpoint exists. Snapshot ID remains mandatory on data reads even when workspace is configured official; this prevents tab/context leakage.

Lists default to 100, limit 1–100. Opaque base64 cursors bind endpoint, contract, snapshot, exact supplied filters (excluding page size) and last record ID. Immutable records make continuation stable; changing bbox/search/status/snapshot invalidates a cursor. Clients restart pagination when filter text changes, including equivalent alternate bbox formatting. Discovery ordering uses publication/ID; condition history ordering uses date/ID. Repeating the same valid cursor repeats its page; there is no stateful consumed-token store. Unknown/repeated parameters, malformed cursor, invalid enum, q/status outside 1–100 characters, invalid bbox and missing required fields return 422. Search is literal case-insensitive substring of name/on-street/source key, not SQL LIKE syntax.

Bbox is finite ordered EPSG:4326 west,south,east,north, no antimeridian. Indexed envelopes prefilter; Shapely exact full-geometry intersection includes boundary. No geometry is clipped. GeoJSON viewports exceeding 2,000 matching features return 422 `VIEWPORT_TOO_BROAD`, never truncation; paged record lists are separately available. A broad entire-pilot viewport can require refinement. Permit bbox uses source geometry or explicitly accepted road reference; unlocated records are excluded with unlocated_excluded_count. Unknown permit geometry never gets a synthetic point.

Dashboard concrete shape: snapshot_id, coverage, source_status, counts, capabilities, observation_date_range, latest_retrieved_at, method_version, classification derived_calculation, source_revision_ids, dated_road_coverage and limitations. `counts.roads` is an integer; condition good/fair/poor/unknown counts sum to roads (currently all unknown because no supported category mapping). Assessments contain total/dated/undated/accepted/ambiguous/unmatched; permits contain total/confirmed_in_scope/scope_candidates/matched/ambiguous/unmatched/unlocated. Match buckets sum to total. Unlocated overlaps ambiguous/unmatched; never add it to total. Confirmed_in_scope + scope_candidates = total. Counts have a common derivation/provenance envelope; dated_road_coverage has explicit value/denominator. This compact shared-provenance shape replaces M7.0's proposed individual metric wrappers. All required layers must pass publication, so missing-layer null aggregates are deferred until an actual optional-layer contract exists. No cost/savings/active-construction/safety prediction metric is inferred. M7.3 adds `method_version=municipal-summary-2`, `permit_status_counts: [{status: string|null, count: integer}]` (exact raw statuses, including an explicit null bucket), `permit_issue_date_range: [min,max]|null` using known issued_at values only, and `source_freshness: [{id,source_id,retrieved_at,source_updated_at,cadence,release_note}]` copied from frozen source revisions. Validity dates never substitute for issue/construction dates. Null source update dates remain null; retrieval/cadence does not establish currentness. Existing fields and endpoints remain compatible; the UI shows unavailable summaries against older servers rather than invented zeros.

Errors retain the existing sanitized envelope/X-Request-ID. Unknown snapshot/member/record/reference →404; unsupported official mutations on read resources →405; invalid query →422; missing explicit schema-7 migration →503 `MIGRATION_REQUIRED`; other storage failures →503 `STORAGE_UNAVAILABLE`. Source-layer-unavailable/409 is reserved, not an implemented partial-layer response. Official calculation endpoints do not exist. V1 routes and saved replay are unchanged. No route downloads data or starts an import.

Backend configuration: CIVICPLAIN_DATA_MODE defaults synthetic; official requires CIVICPLAIN_OFFICIAL_SNAPSHOT_ID with valid nyc-hex format and a published snapshot at read time. It selects `/workspace`, never reroutes v1. M7.2 reads public VITE_MUNICIPAL_API_BASE_URL (default http://127.0.0.1:8000/api/v2) independently of VITE_API_BASE_URL. The client reads /workspace for initial mode/pin unless a validated URL explicitly selects context. No UI selection changes server configuration, ingestion or stored snapshots.

## M8 staged v2 extension (implemented read subset below)

M8.0 is documentation/audit only. [M8_IMPLEMENTATION_PLAN](M8_IMPLEMENTATION_PLAN.md) section 6 lists proposed paths, request/result boundaries and stage ownership; [DATA_MODEL](DATA_MODEL.md) defines the new semantic entities. Freeze concrete typed schemas in these shared contracts before coding each stage. Existing M7 reads and `municipal-record-v2` envelopes remain compatible; the assertion above that official calculation endpoints do not exist is still true at M8.0.

M8.1 implements GET `/api/v2/intelligence-releases`, `/intelligence-releases/{id}`, `/road-associations` and `/road-segments/{id}/condition-summary`, plus condition-layer scope filters; the concrete contract below supersedes earlier proposed names. Exact snapshot/release membership is required. Releases are published by explicit reviewed local CLI only; no HTTP ingestion/review-promotion endpoint.

Later proposed resources: `/api/v2/intelligence/road-segments` (list/detail), `/intelligence/dashboard` and `/intelligence/permits` (list/detail); `/api/v2/planning/capabilities`, `/planning/rate-catalogs` (list/detail), `/planning/assumption-sets`, `/planning/estimates` (explicit create/saved detail), `/planning/prioritization-runs` and `/planning/conflict-analyses` (explicit create/saved detail), municipal scenario draft/evaluation/history/comparison resources, then `/planning/explanations` and explicit official evaluation review notes. They are proposals, not working endpoints or aliases to v1. No existing read resource gains a mutation side effect.

New reads identify contract_version, snapshot_id, intelligence_release_id and applicable condition/priority policy, catalog and explicit as_of_date, plus coverage/capabilities/warnings. Condition reads require explicit condition policy/date; every cursor binds all semantic filters, endpoint and pinned context. Existing 1–100 page limits and 2,000-feature guard remain unless separately reviewed. Do not mutate frozen M7 manifests to advertise new planning readiness: use the separate capability response with missing stage/source/input reasons. A bare road selection cannot enable all planning.

Strict explicit calculation bodies resolve source/catalog/assumption/work references server-side and never accept authoritative client results. New content-addressed calculation POSTs return 201 new or 200 identical saved result; GETs only retrieve. Official mutable drafts use expected_revision. Invalid/extra fields, units or missing required estimate inputs →422; unknown refs→404; context/revision/basis/replay incompatibility→409; migration/storage/audit unavailable→503. Incomplete valid drafts/evaluations retain null metrics, indeterminate status and reasons. Source-integrity failure cannot become a fallback explanation; provider failure can use the established deterministic fallback pattern. No automatic mutation retry. All existing local transport/origin/body/privacy safeguards apply.

## Transport conventions

JSON except road feature collection responses, which use `application/geo+json`. Required request fields are listed with `!`; other fields are optional. IDs reference the same snapshot. Unknown fields are rejected in mutation/calculation inputs. Money is a two-decimal USD string; dates and geometry follow DATA_MODEL. Lists use `limit` 1–100 (default 30), opaque `cursor`, and stable ID ordering. M1 cursors encode the last ID, snapshot and bbox and reject mismatched filters/snapshots; clients must treat them as opaque. Bbox is an exact geometry intersection filter, including boundary contact. Deterministic domain routes never invoke an LLM. In the implemented API, only explicit AI-mode requests to /ai/* may attempt a configured provider; the separate M8.7 explanation route is proposed above.

Ordinary success: `{ "data": <entity or list>, "meta": { "request_id": "...", "dataset_snapshot_id": "...", "warnings": [], "next_cursor": null } }`. For health, dataset_snapshot_id is null before seed. For GeoJSON, the top-level object is a FeatureCollection with `features` plus foreign member `meta` using the same metadata. Each feature ID is the RoadSegment ID and properties contain RecordMeta and non-geometry RoadSegment fields. M1 also includes the documented synthetic `condition_summary` projection (category, nullable decimal rating/scale/date, evidence_ids, data_kind and synthetic_input); it is not a municipal assessment or a separate mutable entity. Record detail includes nullable fields and unknown reasons, not fabricated defaults.

Errors: `{ "error": { "code": "VALIDATION_ERROR", "message": "...", "field_errors": [{"path":"...","reason":"..."}], "request_id": "..." } }`. No stack trace or secrets. Common errors: 422 malformed fields/geometry/unknown query value; 404 unknown referenced record; 409 incompatible snapshot or comparison basis; 503 persistence unavailable; 500 unexpected server fault. Unsupported methods use 405. List endpoints return empty lists for valid filters with no matches, never 404 for an empty collection. Demo imports reject geometry wholly outside the study window; intersecting source segments remain unclipped per DATA_SOURCES. No arbitrary client-supplied URL fetching.

The local MVP has no authentication and must not be publicly exposed. There are no project approval, spending, arbitrary SQL, ingestion-by-URL, or model tool-execution endpoints. `POST` below persists results when specified; it does not perform municipal actions.

## Endpoint contracts

Roads, planning, projects and M3 conflict routes listed as implemented below work locally. Generic asset routes remain future contracts; M4 scenario and M5 explanation/review routes are implemented as clarified below.

| Method and path | Input | Output / success | Validation and specific errors | Computation |
| --- | --- | --- | --- | --- |
| GET `/health` | none | 200 `{status:"ok", api_version:"v1", data_ready:bool, ai_mode:"deterministic" or "optional_provider"}` in envelope | 503 if configured required storage unavailable; missing key is not a health failure | deterministic; no provider probe |
| GET `/road-segments` | bbox optional `[west,south,east,north]` as comma-separated query; limit/cursor | 200 RoadSegment list | valid lon/lat bounds, west<east, south<north; 422 invalid cursor/bbox | deterministic read |
| GET `/road-segments/geojson` | same filters/pagination as list | 200 GeoJSON FeatureCollection | same 422 rules; implement static route before `/{id}` | deterministic read |
| GET `/road-segments/{id}` | ID | 200 RoadSegment | 404 missing ID | deterministic read |
| GET `/road-segments/{id}/assets` | Future contract only | Not implemented (404) | Generic asset ingestion remains deferred | none |
| GET `/road-segments/{id}/conditions` | road ID; complete bounded fixture history (no pagination) | 200 Assessment list in newest-date/stable-ID order; meta.latest_usable_id nullable | 404 road not found; latest selection uses date/stable-ID rule | deterministic read |
| GET `/projects` | road_segment_id, kind, schedule_status, limit/cursor optional | 200 WorkProject list, stable ID order; no utility_work child | 422 invalid enum/cursor; 404 supplied road missing | implemented deterministic read/filter |
| GET `/projects/{id}` | ID | 200 WorkProject including uncertainty and provenance | 404 missing ID | implemented deterministic read |
| GET `/repair-options` | none; complete bounded catalog | 200 RepairOption list with full rates/productivity and assumption evidence | storage 503 | deterministic read |
| GET `/road-segments/{id}/repair-options` | road ID | 200 list of {option, suitability, preview, unavailable_reason}; preview is Calculation or null | 404 missing road; missing dimensions produce null preview and explicit reason | deterministic preview, no persistence |
| POST `/estimates` | road_segment_id!, repair_option_id!, dataset_snapshot_id!, optional planning_assumptions {length_m?,width_m?,unit:m,note!} | 201 saved Estimate; full input/output and sources | 404 road/option; 409 snapshot/evidence mismatch; 422 unknown fields, missing dimensions, nonpositive/nonfinite dimensions, invalid units or blank note | deterministic estimate, no AI |
| GET `/estimates/{id}` | ID | 200 saved CostEstimate | 404 missing ID | deterministic read |
| POST `/conflicts/analyze` | dataset_snapshot_id!, project_ids! 1–50 distinct IDs; proximity_m 0–100 default 5; corridor_m 0–50 default 5; reopening_horizon_days integer 0–365 default 30 | 200 saved ConflictAnalysis, positive findings and separate incomplete checks | 404 projects; 409 snapshot/evidence mismatch; 422 malformed/extra fields or invalid references/parameters; missing dates/geometry return explicit warnings/checks | implemented deterministic geometry/date rules; no LLM |
| GET `/conflicts` | project_id, road_segment_id, analysis_id, limit/cursor optional | 200 saved ConflictFinding list in stable ID order | 404 missing filter references; 422 cursor/filter mismatch | implemented deterministic read |
| GET `/conflict-analyses/{id}` | analysis ID | 200 immutable ConflictAnalysis with complete input/source snapshot and parameters | 404 missing ID | implemented deterministic read |
| GET `/conflicts/{id}` | ID | 200 saved ConflictFinding, including analysis_id | 404 missing ID | implemented deterministic read |
| POST `/scenarios` | scenario-v1 request below: contract_version!, name!, dataset_snapshot_id!, budget_usd!, currency!, planning_start!, planning_end!, cost_scope!, actions!; assumptions, external_project_ids, project_overrides, mobilization_groups, cost_scope_note, review_note | 201 saved Scenario with system-populated RecordMeta | 422 invalid dates, duplicate scopes, invalid budget/units; 404 references; 409 snapshot mismatch | deterministic validation/save |
| GET `/scenarios` | limit and after stable-ID cursor | 200 Scenario list | 422 invalid filters | deterministic read |
| GET `/scenarios/{id}` | ID | 200 Scenario | 404 missing ID | deterministic read |
| POST `/scenarios/{id}/evaluate` | expected_revision! and M3 AnalysisParameters: proximity_m 0–100 default 5; corridor_m 0–50 default 5; reopening_horizon_days integer 0–365 default 30 | 200 immutable ScenarioEvaluation | 404 scenario; 409 invalid/stale source snapshot that cannot be reconstructed; incomplete data returns indeterminate fields, not fake zero totals | deterministic evaluation |
| GET `/scenario-evaluations/{id}` | ID | 200 immutable ScenarioEvaluation | 404 missing ID | deterministic read |
| POST `/scenario-comparisons` | evaluation_ids! 2–3 distinct IDs | 200 ScenarioComparison table with metrics, deltas, common basis and warnings | 404 references; 409 mismatched snapshots, horizon, price basis, scope or method versions; 422 duplicate/invalid count | deterministic comparison; no automatic optimum |
| POST `/scenario-evaluations/{id}/reviews` | reviewer_label! 1–100 chars, note! 1–2000 chars, acknowledged_limitations! nonempty code list | 201 review event with action=review_note | 404 evaluation; 422 lengths/unknown limitation codes | human note recorded deterministically; not approval |
| GET `/evidence-sources/{id}` | ID | 200 EvidenceSource | 404 missing ID | deterministic read |

Road conditions are read-only assessments in the MVP. Project and asset creation are fixture/import responsibilities, not open user mutations. Scenario draft edits retain their stable ID and increment an optimistic revision; evaluations and audit events are immutable. Schema/system fields are populated by the service, not trusted from the caller.

## Calculation response details

**ConflictAnalysis** (M3): concrete fields are specified in DATA_MODEL. Includes findings, indeterminate_checks with spatial evidence, excluded_project_ids, utility_coverage=unknown, possible_pair_count, checked_pair_count, method_version, parameters, detection time, complete input_snapshot, input_hash, result_hash and stable ID. Only the explicit selected project set is checked. All roads are retained for corridor analysis; this does not imply all projects or utilities are known. A one-project scope returns zero pairs and a warning. Empty project_ids is 422. Missing project geometry/dates are accepted and remain unknown. Invalid topology is rejected, not repaired.

The previous proposed `/conflicts/check` and ConflictCheckResult draft are superseded by `/conflicts/analyze` and ConflictAnalysis; no compatibility alias is implemented. There is no date-range project-list filter in M3. M3 flattens utility scope/category fields into WorkProject and has no UtilityWork child. Saved analysis history provides reproducibility; M5 implements its scoped interaction audit and separate review-note workflow below. A general cross-module AuditEvent stream remains a future contract.

Project/conflict lists use the existing limit 1–100/default 30, stable-ID order and opaque cursors. M3 cursors bind to snapshot plus endpoint filters and reject reuse with different filters. Findings across all saved analyses are returned by default; use analysis_id for one version. Different input snapshots can intentionally retain findings for the same pair, with distinct analysis IDs. Valid no-match filters return empty arrays; incomplete coverage warning remains in metadata. Empty unseeded databases return empty lists. Unknown filter references return 404. GET never triggers analysis.

POST persists immutable analyses/findings transactionally. Identical inputs return the existing record/time; no duplicate findings are added. Changed inputs/parameters yield a new analysis. GET returns saved output without recomputation. M7.2 loads projects without creating analyses. The user explicitly invokes Run conflict screening in synthetic Projects (≤50); its layer controls only affect presentation. M7.3 saved-analysis URLs restore through GET `/conflict-analyses/{id}` with dataset checks; project/finding selection does not alter the stated screening scope. Failed reads may be retried; analyses/calculation writes are never retried automatically. Project editing/creation is a fixture adapter responsibility, without an open mutation endpoint.

Implemented request:

```json
{"dataset_snapshot_id":"demo-m1-v1","project_ids":["demo-road-project","demo-utility-project"],"proximity_m":5,"corridor_m":5,"reopening_horizon_days":30}
```

This fictional pair yields one reopening_risk, a two-calendar-day gap, computed polygon overlap and shared R-001, with approximate-location/source-schedule warnings and required human review. No loss, savings, safe-deferral or clearance value is calculated. Query `/conflict-analyses/{id}` to retrieve complete provenance; numerical/source methods are documented in ARCHITECTURE.

**ScenarioComparison**: `evaluation_ids`, `common_basis` (snapshot, baseline_source_hash, horizon, cost_scope, currency, price basis and method versions), `rows` (evaluation ID, cost range or null, budget and status, upper-bound status, elapsed days, lane-closure-days, per-action lifespan ranges, known findings count, indeterminate checks count, review flags), `deltas` (pair IDs and central cost/closure-day differences, nullable when incomplete), `warnings`. No ranking is implied. Cost differences use the same cost scope and remain hypothetical when synthetic inputs occur.

**M5 Explanation**: the implemented public schema and separate provider selection contract are specified in the M5 section below and DATA_MODEL. The earlier ExplanationResult draft is superseded.

## M4 scenario transport (implemented; clarifications below supersede design wording)

POST `/scenarios` accepts `contract_version=scenario-v1`, name, dataset_snapshot_id, budget_usd, `currency=USD`, planning_start/end, `cost_scope=roadwork_only`, and 0–50 actions conforming to DATA_MODEL's `scenario-action-v1`. Optional cost_scope_note/review_note have the documented length bounds. `assumptions`, `external_project_ids`, `project_overrides` and `mobilization_groups` default to empty lists. Dates remain half-open local civil dates; money and quantities are decimal strings. Scenario ID, resolved quantities, source contents, hashes and timestamps are server-controlled output. Classification is constrained to derived/hypothetical/synthetic literals; callers cannot assert observed work. Input provenance is validated against frozen sources or explicit synthetic assumptions, never trusted as a measurement. Nonblank text, strict integer counts, finite numbers and unknown-field rejection follow existing Pydantic boundary conventions.

Action requests contain id, contract_version, road_segment_id, action_kind, repair_category, nullable repair_option_id, scope, quantity, input_provenance, unknown_reasons, related_project_ids, nullable schedule and constraints. The DATA_MODEL tables define the nested fields and cross-field validation, not an unversioned flat quantity/date override. `source_project_id`, top-level action `start_date`/`end_date`, flat `quantity` string and `assumption_evidence_ids` from the former draft are superseded; no compatibility alias is needed because the draft was never implemented.

For example, this is only a QuantityProposal fragment for whole-segment R-001, not a complete POST body:

```json
{"value":null,"unit":"m2","derivation":"road_dimensions","length_m":null,"width_m":null}
```

The implemented service resolves the exact frozen road inputs to 100 m × 8 m = 800 m², preserving synthetic dimension provenance. It does not derive scope from the map geometry. A partial-area fragment instead uses explicit_area with a positive sourced value or unknown with a missing-input reason; there is no implicit whole-road fallback. Inline assumptions must be authored and referenced as specified in DATA_MODEL, not presented as observed records.

Validation/save: 201 for a structurally valid draft, including explicit unknown quantity/method/dates; until shared-cost support exists, nonempty mobilization_groups must instead return an explicit 422 unsupported-adjustment error. 422 for invalid geometry, inconsistent quantities/units/category, extra fields, duplicate actions/IDs, reversed/out-of-horizon dates, constraint cycles, malformed overrides or negative budget; 404 for unknown non-null road/option/project/source references; 409 for incompatible snapshot or source contents. A known category with null method is allowed only with a reason and unavailable cost; a named option inconsistent with category is 422. Missing required estimate inputs still return 422 on the existing `/estimates` endpoint, whose request shape is unchanged.

Evaluation uses frozen proposal/source contents and the internal hypothetical adapter. Unknown quantity/method yields null complete cost and indeterminate budget status. Unknown dates/closures yield null affected metrics and incomplete checks. Nonempty mobilization_groups must be explicitly rejected until the documented adjustment path is implemented. Comparison basis includes baseline_source_hash (original common source contents before scenario overrides), horizon, currency, price basis, cost scope, action/cost/adapter/method versions; scenario-specific action assumptions and quantities may differ; incompatible bases return 409. Patch/restoration prices and lifespans remain unavailable until reviewed source-backed catalog extensions exist.

The hypothetical adapter is internal: no new endpoint accepts arbitrary client WorkProject snapshots, and `/conflicts/analyze` continues to accept persisted project IDs only. ScenarioEvaluation exposes `conflict_screen` with adapter version, hypothetical analysis context, project/action origin mapping, override history, hashes and complete M3 spatial/temporal/source evidence. Findings involving proposals are labeled hypothetical; existing-project pairs are labeled existing_project_screen, never observed collisions. They are not inserted into the existing `/conflicts` history. A missing or empty screening scope has an explicit not-run reason, not an empty-clearance response. See ARCHITECTURE for projection, source-shape limits and replay semantics.

## M1 validation evidence

Health is read-only and checks SQLite availability; it returns data_ready=false and a null snapshot for a newly initialized, unseeded database. The absence of an AI key is never checked or required. An unseeded roads query is a successful empty collection. Seed import is an explicit local CLI, not an HTTP endpoint. Every current dataset is labeled synthetic; meta warnings retain unknown utility coverage.

Backend tests cover the five route contracts, geometry/provenance validation, stable pagination, bbox errors, 404/405 envelopes, request IDs, CORS, storage 503, immutable fixture checks and persistence/repeated seed. Browser checks exercise GeoJSON loading, separate road/evidence reads and unavailable-API retry. See M1_IMPLEMENTATION.md for commands and actual outcomes.

## Implemented M2 example and response

```json
{"road_segment_id":"demo-r-001","repair_option_id":"demo-resurface","dataset_snapshot_id":"demo-m1-v1"}
```

POST this body to `/api/v1/estimates` after explicit seeding. For unknown R-004 dimensions, add `"planning_assumptions":{"length_m":"100","width_m":"8","unit":"m","note":"Hypothetical rectangular scope for human review"}` and change the road ID. Extra request fields (including arbitrary rate/quantity overrides) are rejected. Unknown road/option is 404; incompatible snapshot is 409; missing mandatory dimensions is 422 `MISSING_ESTIMATE_INPUTS`; malformed requests are 422 `VALIDATION_ERROR`. No special 400 case is needed: typed boundary failures consistently use 422. CORS allows GET/POST and Content-Type only from configured local origins.

The standard envelope's data is the implemented CostEstimate shape in DATA_MODEL. `scenarios.low/base/high` each expose three line items, subtotal, contingency and total. R-001 resurfacing (800 m²) returns base roadwork $36,000 + mobilization $6,000 + traffic $2,500 = subtotal $44,500; contingency $8,900; total $53,400; low $44,760 and high $66,360. Duration: ceil(800/600)=2 active +2 setup +1 curing =5 preliminary days. These are synthetic sensitivity examples, not official prices, probabilities or completion dates. Suitability for this poor-condition resurfacing case is `not_indicated`, with human review required.

GET `/estimates/{id}` returns the saved data without recalculation. Input snapshot includes full evidence contents and the request, dimension basis and selected assessment/option. Hash/version details are inspectable. GET comparisons do not save estimates; POST saves a new record on each call. There is no idempotency key or deduplication of intentional estimate requests. Read-only conditions/catalog collections are small and returned in full; general ingestion/pagination is deferred. An M1-only seeded database returns no M2 options/history until the explicit seed upgrade.

## Implemented M4 routes and reconciliation

All paths below have the existing `/api/v1` prefix and `Envelope {data,meta}` response. Validation errors use the existing sanitized error envelope with field_errors; unknown references → 404, stale revision/incompatible comparison basis → 409, invalid inputs/unsupported adjustments → 422, storage failures → 503. No LLM/provider dependency. The earlier scenario table is a design summary; the concrete M4 transport here takes precedence. M5 explanation/review transport is implemented in the section below.

| Method/path | Body/query | Result |
| --- | --- | --- |
| POST `/scenarios` | ScenarioDraft nested scenario-v1 contract | 201 Scenario with stable ID, revision=1/hash and server provenance |
| GET `/scenarios` | limit 1–100 default 30; after stable-ID cursor | 200 Scenario list; meta.next_cursor passed back as after |
| GET `/scenarios/{id}` | — | 200 current Scenario; 404 unknown |
| PATCH `/scenarios/{id}` | `{expected_revision, draft: <complete ScenarioDraft>}` | 200 validated atomic draft replacement, same ID/new revision |
| POST `/scenarios/{id}/actions` | `{expected_revision, action: <ScenarioAction>}` | 201 updated Scenario; 409 existing action ID |
| PATCH `/scenarios/{id}/actions/{action_id}` | `{expected_revision, action: <complete ScenarioAction>}` | 200 updated Scenario; action ID cannot change |
| DELETE `/scenarios/{id}/actions/{action_id}` | query expected_revision | 200 updated Scenario; dependencies must be removed explicitly |
| POST `/scenarios/{id}/evaluate` | `{expected_revision, proximity_m?:5, corridor_m?:5, reopening_horizon_days?:30}` | 200 immutable ScenarioEvaluation; identical canonical input reuses first saved result |
| GET `/scenarios/{id}/evaluations` | limit 1–100 default 30, offset ≥0; next_cursor is next offset | 200 newest-first saved evaluation history |
| GET `/scenario-evaluations/{evaluation_id}` | — | 200 complete immutable evaluation; 404 unknown |
| POST `/scenario-comparisons` | `{evaluation_ids:[<2–3 distinct saved IDs>]}` | 200 reproducible ScenarioComparison; 409 incompatible bases |

PATCH accepts a complete draft/action inside its typed envelope so cross-field validation and optimistic revision checking are atomic. Use GET then PATCH for edits; generated metadata is not accepted as draft fields. No scenario deletion endpoint is offered; archive via status. No `/scenarios/compare` alias is added because the documented `/scenario-comparisons` boundary is authoritative. CORS now permits PATCH/DELETE from the same configured loopback origins.

Valid incomplete drafts can omit actions and explicitly retain unknown methods, quantity, geometry or schedules with reasons. Empty drafts evaluate as indeterminate, never within-budget zero. Shared mobilization and arbitrary cost overrides return explicit 422 errors. Unsupported patch/restoration methods can remain null, not mapped to an existing method. Proposed actions cannot be submitted as WorkProject snapshots and never enter the real project/history tables.

For a runnable complete request, use `data/demo/scenarios.json` entry `.draft` (exclude fixture `.id`). Those are synthetic plans using existing roads/projects/catalog, with declared assumptions, source geometry and explicit project replacement. Server-side IDs and timestamps differ for manually created copies. Inspect `cost_total_usd`, nullable `budget_headroom_usd`, base budget_status and upper_bound_within_budget separately. GET evaluations includes exact inputs, source aliases/contents, per-action estimates, versions, hypothetical/existing finding contexts and hashes; it is sufficient for offline replay through services.scenarios.replay.

## Implemented M5 AI and review transport (supersedes proposed explanation contract)

All responses use the existing Envelope `{data,meta}` and `/api/v1` base. The former proposed POST `/explanations` and its draft ExplanationResult were never implemented; the explicit M5 task selects the `/ai/*` routes below. There is no compatibility alias. Existing M1–M4 requests/responses/calculations are unchanged. Defaults are deterministic; the optional provider is requested with `mode=ai` and must also be enabled server-side.

| Method/path | Strict request | Response |
| --- | --- | --- |
| POST `/ai/explain-estimate` | `{estimate_id,mode?:deterministic\|ai}` | 200 Explanation from immutable saved estimate |
| POST `/ai/explain-conflict` | `{conflict_id,mode?:deterministic\|ai}` | 200 Explanation from saved finding and parent analysis |
| POST `/ai/explain-scenario-comparison` | `{evaluation_ids:[2–3 distinct saved IDs],mode?:deterministic\|ai}` | 200 Explanation after existing M4 basis checks |
| POST `/ai/ask` | `{context:{type,record_ids},question,mode?:deterministic\|ai}` | 200 bounded explanation or explicit insufficient_evidence |
| GET `/ai/status` | none | Default mode, provider configured boolean/name, model if configured, timeout/output/call limits, free_text_generation=false, live_provider_verified=false |
| GET `/ai/interactions/{id}` | audit reference | 200 minimal interaction metadata; 404 absent |
| POST `/scenario-evaluations/{id}/reviews` | `{reviewer_label,note,acknowledged_limitations}` | 201 immutable human review event; authorizes_work=false |

Context type is road, assessment, estimate, conflict, project, evaluation or comparison. Non-comparison contexts require exactly one ID. Comparison requires 2–3 distinct evaluation IDs; no stored comparison-ID lookup is offered. IDs have 1–150 nonblank characters; question 1–500 stripped nonblank characters; all extra input fields are rejected. The local intent matcher can decline future-effect, approval, secret, override or unrelated questions; it never uses client money/evidence as truth. `insufficient_evidence` has an empty key_findings list, explicit reason, attached evidence/unknowns and human-review requirements.

Review aliases are 1–100 stripped nonblank characters; notes 1–2000. acknowledged_limitations is a nonempty list of 1–3 allowed codes: synthetic_inputs, unknown_utilities, human_review. This is an annotation, not a legally significant acknowledgement or municipal approval. Do not enter sensitive data. Notes are never sent to the provider.

Public Explanation fields are defined in [DATA_MODEL](DATA_MODEL.md), and the separate provider-only schema in [AI_SYSTEM](AI_SYSTEM.md). All numerical/date/unit claims are server-rendered from typed evidence facts. Citations expose record IDs/content hashes/source revision hashes/method versions; evidence carries field-level references and truncation indicators. Summary, tradeoff and review language uses fixed templates. All fact-catalog entries are retained in the answer (up to projection limits), independent of model emphasis. Synthetic source labels, unknown utility coverage and human-review requirements cannot be suppressed by model selections.

Unknown reference → 404; malformed body, extra fields, invalid mode/question/count or oversized mandatory evidence metadata → 422; source-integrity/replay/basis mismatch → 409; storage/audit failure → sanitized 503. No secrets, provider exception text or stack traces appear. The source record must validate before a useful fallback can be returned.

Provider failure remains a 200 Explanation with provider_status=fallback, validation_status=fallback_validated, and fallback_reason such as not_configured, timeout, rate_limit, provider_unavailable, invalid_output, invalid_context, invalid_citation, missing_caveats, unsupported_claim, usage_limit or busy. Deterministic requests return provider_status=deterministic. Valid model selections return openai; they are selections of safe templates, not independently verified LLM prose. `GET /ai/status` verifies configuration only and makes no live call. Audit references exist only after successful persistence.

Examples (replace saved IDs with API results):

```json
{"estimate_id":"<saved-estimate-id>","mode":"deterministic"}
```

```json
{"context":{"type":"road","record_ids":["demo-r-001"]},"question":"Why is this road flagged?","mode":"deterministic"}
```

The established local-only unauthenticated deployment remains; no production authorization/tenant isolation is introduced. No endpoint exposes AI mutation tools or changes existing municipal/domain records.


## M6 transport reliability and security boundary

No domain route shape, calculation version or fixture changed. All HTTP request bodies are capped at **1,048,576 bytes (1 MiB)** before JSON parsing, including chunked bodies without Content-Length. Oversize requests return **413 REQUEST_TOO_LARGE**; invalid content lengths return **400 INVALID_CONTENT_LENGTH**; body arrival exceeding 10 seconds returns **408 REQUEST_TIMEOUT**. These errors use the existing sanitized envelope and X-Request-ID. Domain-specific count/length/geometry validation still applies within this cap.

POST/PATCH/DELETE carrying an Origin outside the configured explicit loopback origins return **403 ORIGIN_NOT_ALLOWED**, including Origin null. Missing Origin remains supported for local CLI clients. CORS continues restricting browser reads/preflights to the configured loopback origins. These are local demo protections, not authentication or authorization; untrusted local processes remain outside the protection boundary. Bind only to loopback. The frontend retains its 10-second request deadline and explicit retry states; never assume an interrupted POST did not persist.

M6 browser checks exercise actual REST requests in development and production, including saved estimate creation/retrieval, conflict evidence, scenario creation/evaluation/comparison and explanation fallback. Exact evidence is in [FINAL_QA_REPORT](FINAL_QA_REPORT.md).

## M7.3 client navigation compatibility

The hash-route schema is documented in [M7_3_IMPLEMENTATION](M7_3_IMPLEMENTATION.md). It does not add backend routes. Permit detail is independently read through the existing snapshot-bound GET `/api/v2/permits/{id}` even outside a filtered list page; client checks identity, contract, snapshot and non-synthetic classification. Synthetic evaluation histories use existing GET `/api/v1/scenarios/{id}/evaluations?limit=30&offset=0` and explicit later offsets. Saved evaluation links use GET, never evaluate POST. No calculation, source import, record promotion or AI audit is triggered by route changes.

## M8.1 implemented read contracts (A1 gate still open)

This implemented subset supersedes the corresponding proposed M8 paths; all costing/ranking/screening/scenario/advisor routes remain unavailable. See [M8_1_IMPLEMENTATION](M8_1_IMPLEMENTATION.md) for exact commands and evidence. Existing M7 reads and v1 schemas/replay are unchanged.

- GET `/api/v2/intelligence-releases`: required `snapshot_id`, optional `limit` 1–100 / snapshot-bound `cursor`; returns immutable `road-intelligence-v1` manifests, counts and source/parameter/runtime/decision/content hashes.
- GET `/api/v2/intelligence-releases/{release_id}`: required `snapshot_id`; exact release/base membership or 404.
- GET `/api/v2/road-associations`: required `snapshot_id`, `release_id`; optional `road_id`, `status` candidate/accepted/rejected/unmatched, `limit`, `cursor`. Cursor binds release and all filters. Association payloads expose source/target/candidate/parameter hashes, evidence, local review and scope; candidate is not accepted.
- GET `/api/v2/road-segments/{road_id}/condition-summary`: required `snapshot_id`, `as_of_date` strict YYYY-MM-DD; optional `release_id`, integer `stale_after_days` 0–36,500. Returns typed `road-condition-v1` projection: road/snapshot/release identity, raw nullable rating and source-local inspection timestamp, source revision, latest eligible ID, category=unknown / applicability reason, age/stale or null, complete accepted history with eligibility/unknown reasons and source/association hashes, input/result hashes, utility coverage unknown. Missing threshold leaves staleness unknown. Release omitted uses original scoped links and works on schema 7.
- GET `/api/v2/conditions` additionally accepts `release_id`, `assessment_scope=all|current|historical|unaccepted` (default all) and `as_of_date`. Current/historical require an explicit date. Current is the distinct union of eligible road summaries across the complete context, then intersected with viewport; historical is accepted non-current dated observations at/before the reference date; unaccepted means no accepted association in that context. Original records/matches remain unchanged. Envelope echoes release/scope/date; pagination binds them.

Release reads require explicitly migrated schema 8 (503 `MIGRATION_REQUIRED` otherwise). Unknown references are 404; unsupported, repeated or unknown parameters/invalid dates/thresholds are 422. GETs are deterministic read projections with zero analysis/evaluation/AI-audit writes. Local CLI alone stages/publishes a release with reviewed report hash; there is no mutation/import/migration endpoint or automatic release selection. Current/history filters do not imply that an unassociated observation describes a road or that missing evidence is Good.


### M8.1 owner-approved pilot read extension

See [pilot report and runnable examples](M8_1_PILOT_IMPLEMENTATION.md). The existing `/api/v2/road-segments`, `/road-segments/geojson`, `/conditions` and `/road-segments/{road_id}/condition-summary` accept optional `policy_id=civicplain-pilot-pavement-v1.0`. It requires the approved base `nyc-3947b35876a619b31067db96b1409ad8`, an explicit valid `release_id` in that base. Road list/summary and current/historical observations require explicit `as_of_date`; all/unaccepted source overlays may omit it because they do not select a current assessment. Unsupported policy/base/release/date context fails closed (422 invalid query; 404 absent/foreign release); there is no newest-release fallback. Omit policy_id to retain legacy projection semantics. No new mutation route.

Road list/GeoJSON also accept `release_id` and `as_of_date`; an explicit release requires the date. `condition=good|fair|poor|unknown` filters the complete eligible road summary before pagination/viewport output. Returned roads may contain `condition_summary`; GeoJSON exposes it in properties. Condition summary method becomes `road-condition-v2-pilot` with policy metadata/hash, raw nullable road rating, rounded_rating and accepted history grading/review (DATA_MODEL). Condition all/current/historical/unaccepted filters honor the same policy context and preserve source record payloads. Pagination binds query context. Actual pilot road category totals are 0/0/0/4,150; accepted historical observations total 5, current eligible 0, unaccepted 8,721.

Client shareable hash routes add `intelligence=intel-<32 lowercase hex>` and strict real-date `asof=YYYY-MM-DD`; explicit release selection on the approved base selects the pilot policy. Client checks returned road/snapshot/release/date/policy/version/classification identity and refuses incompatible responses. Release/date survive navigation; age threshold and observation-overlay selection remain local controls. No route/GET creates reviews, planning results or AI audits.

## M8.2 implemented permit reference/coordination reads

Current owner-authorized scope and evidence: [M8_2_IMPLEMENTATION](M8_2_IMPLEMENTATION.md). Uses existing `/api/v2`, explicit `snapshot_id`, `municipal-record-v2` envelopes and filter-bound cursors; no new official mutation/planning endpoint.

| GET path | Additive query/result contract |
|---|---|
| `/intelligence-releases` | Optional `kind=condition|permit` (default condition), selecting the matching manifest contract. |
| `/permits` | Existing parameters plus `evidence:bool=false`, `permit_release_id`, `location_status=located|candidate|unlocated|outside_coverage|invalid_evidence`. Any enhanced parameter opts into typed `permit_location`. `road_id`/bbox use accepted references only. Enhanced `q` searches source key, administrative values/street endpoints and identifiers; legacy defaults unchanged. |
| `/permits/{id}` | Optional `evidence`, `permit_release_id`; record membership checked. |
| `/permit-location-coverage` | Optional `permit_release_id`; whole-snapshot five-status counts, total permits, distinct accepted roads, precision/limitations/source selection and deterministic hash. |
| `/permit-associations` | Required `release_id`, optional `road_id`, `source_record_id`, `status=accepted|candidate|rejected|unmatched`, `limit` 1–100 and `cursor`. Permit-contract release only. |
| `/permits/{id}/coordination-candidates` | Optional `permit_release_id`, `limit` 1–100 (default 30), `cursor`; explicit selected record vs other imported records; total and paginated deterministic findings. Meta includes selected release, actual schedule Unknown, confirmed-conflict capability false. No write or external call. |

Enhanced projection includes accepted/rejected review evidence, active road candidates, complete candidate-set/parameter/result hashes and unknown actual schedule. Permit release IDs cannot select condition evidence and vice versa (404). Unknown/repeated keys, invalid enums/limits →422; foreign IDs/context →404; missing explicit required schema →503. Navigating/GET never creates projects, saved analyses, evaluations or AI audits. Coordination is an ephemeral reference/window screening read, deliberately separate from the later persisted conflict/scenario engine. Empty results retain coverage/unknown caveats. UI routes add separately validated `permitrelease` and five-value `locstatus`, preserving existing `intelligence` semantics.

## M8.3 repair planning boundary

Owner-authorized scope supersedes original M8.4 estimate numbering. V2 uses `municipal-record-v2` envelopes and explicit snapshots. POST `/planning/estimates/preview` accepts strict `municipal-estimate-v1` input and returns available/unavailable alternatives without writes; POST `/planning/estimates` recalculates and saves complete alternatives only (201 new/200 identical). GET `/planning/estimates` requires snapshot, optional road and pagination; GET `/planning/estimates/{id}` requires snapshot and returns frozen inputs/results after integrity/replay checks. No synthetic rates, URL fetching, auto-selection or external calculation calls. GET `/planning/capabilities` requires snapshot/road and reports supported treatments, missing pricing/quantity evidence and schema readiness. Valid incomplete preview →200 with unavailable alternatives; incomplete save →422 `MISSING_PLANNING_INPUTS`; unsupported units/invalid values →422; foreign snapshot/road/result →404; missing explicit schema 10 for persistence →503. Decimal inputs are JSON strings, each with units and human provenance; no client-computed result is accepted. Source citations remain unverified human assertions. Full field definitions and acceptance evidence are in M8_3_IMPLEMENTATION.md upon delivery.


## M8.4 implemented prioritization boundary

`/api/v2/planning/prioritization-runs` extends the existing municipal envelope. Strict `PriorityRequest` is the implemented contract in `schemas/prioritization.py`, documented in [M8_4_IMPLEMENTATION](M8_4_IMPLEMENTATION.md). POST `/preview` calculates without writes; POST to the collection recalculates/freeze-saves (201 new / 200 same canonical input), including all-unranked evidence-review results. GET collection lists saved snapshot-bound metadata with 1–100 limit/cursor; GET `/{id}?snapshot_id=…` verifies hashes and replays frozen inputs. GET `/{id}/roads` supports snapshot, q (1–100), status ranked/unranked, limit/cursor; row `id` aliases road_id for existing context-bound pagination, preserving saved rank order. Filters never renumber ranks. GET `/{id}/compare` takes snapshot and comma-separated road_ids (2–5 distinct members); returns same-run factors and sensitivity, no aggregate benefit or optimal schedule. All GETs are write-free; replay verification does not create a new run.

Unsupported factors/fields, invalid/non-summing weights, invalid dates/units, duplicate/oversize scope or foreign chosen treatment →422. Unknown/foreign base, road, release, selected estimate or saved run →404. Persistence/history requires explicit schema 11 (503 MIGRATION_REQUIRED); preview works on a valid schema-7+ base unless explicitly selected later-stage evidence requires its own schema. Integrity/replay mismatch →409. No newest policy/release/estimate fallback, user-provided URL fetcher, AI ranking or automatic migration. No client-supplied factual factor values/ranks.

## M8.5 implemented official construction screening

Current explicit owner scope implements screening from original A6 in M8.5; official scenario CRUD/evaluation remains future. V2 `/planning/conflict-analyses` uses existing municipal envelopes, exact snapshot isolation and strict `ScreeningRequest` in `schemas/official_screening.py`. This endpoint is now implemented, superseding its earlier proposed status.

| Method/path | Implemented behavior |
|---|---|
| POST `/planning/conflict-analyses/preview` | Validate/collect pinned records; pure screening without a DB write. |
| POST `/planning/conflict-analyses` | Recalculate and append immutable input/results; 201 new, 200 identical canonical input. All-indeterminate/zero-finding runs may be saved with coverage caveats. |
| GET `/planning/conflict-analyses` | Required `snapshot_id`, optional limit 1–100/cursor; saved metadata only. |
| GET `/planning/conflict-analyses/{id}` | Required snapshot; integrity and pinned-runtime frozen replay, never a new analysis write. |
| GET `/planning/conflict-analyses/{id}/notes` | Required snapshot; separately recorded review notes. |
| POST `/planning/conflict-analyses/{id}/notes` | Required snapshot; strict `ReviewNote`: author, note, disposition `needs_review|reviewed_with_limitations|dismissed_for_planning`, optional same-run base/alternative finding ID. 201/200 idempotent. No approval state. |

Requests contain bounded declared work/permit selection, explicit thresholds with human provenance, optional cited documentary declarations, optional exact release, alternative schedule overrides and an optional declared-comparable-scope estimate/additions contract. Unknown/foreign references →404; invalid geometry/CRS/interval/closure/provenance/parameters, incompatible treatment/scope or extra fields →422. Persistence/history/notes require explicit schema 12 (503 MIGRATION_REQUIRED). Integrity/runtime/projection mismatch fails 409. No GET/navigation writes, AI calls, default source dates, newest release/estimate fallback, automatic project creation or schedule activation. Results use `official-screen-v1`, `derived_calculation`, `human_review_required=true`, utilities unknown and `excavation_clearance=false`. Exact acceptance/reproduction is in [M8_5_IMPLEMENTATION](M8_5_IMPLEMENTATION.md).

## M8.6 integrated decision context

Implemented in the existing v2 envelope, separate from synthetic v1:

- GET `/api/v2/planning/decision-support?snapshot_id=…&as_of_date=YYYY-MM-DD&release_id=…&policy_id=…`: `decision-context-v1`. Optional condition release/policy obey the existing condition-summary eligibility and policy gates. Returns exact-context road category counts, eligible/requiring-review counts and reason distribution; independent estimate/priority/screening saved-history metadata (count, first 100, explicit truncation). No automatic newest result, cross-run cost sum, project count or actual-conflict total. Missing persistence schema is a partial per-kind `unavailable` with null count; never a fabricated zero. Invalid date/context/query fields fail closed. GET performs no calculation persistence or AI audit.
- Existing GET `/permits` additionally accepts `include_candidates=true` **only with road_id**. It enables the existing enhanced evidence projection; returns accepted references OR unrejected candidates for that exact road, with unchanged location statuses/provenance. Default filtering remains accepted-only. Candidates never become geometry footprints, confirmed work or accepted associations.
- POST `/api/v2/planning/decision-support/explanations`: strict `{snapshot_id,kind:estimate|priority|screening,record_id,mode:deterministic|ai}`. Default deterministic. Replays the selected immutable record through its existing repository, then applies `official-scalar-projection-v1` into existing `ai-evidence-v1` and selection-only explanation service. Result task `explain_official`, source classification `derived`, exact snapshot/input/result/projection hashes, mandatory review/unknowns/citations. Unknown/foreign reference 404; replay mismatch 409; storage/audit unavailable 503. Only this explicit POST writes the existing minimal AI audit; source prose/geometry/notes/questions never enter provider context. No arbitrary client evidence or mutation tools. Provider failure/no key retains validated deterministic fallback. See [M8.6 report](M8_6_IMPLEMENTATION.md).

Shareable client route fields: `estimate=estimate-<64hex>`, `priority=priority-<64hex>`, `screening=screen-<64hex>`, `tool=estimate|priority|screening`, `alternative=<bounded identifier>`, existing finding/road/base/release/date/filter fields. Repeated/unknown/malformed fields rejected. Alternative not found is unavailable, never silently replaced with base. These pin existing results; they are not a new saved scenario/evaluation contract. No notes, raw work geometry, rates or assumptions in URLs.

## Standardized street read boundary (implemented 2026-11-08)

Same FastAPI process, separate `/api/v2/standardized`, contract `standardized-read-v1`. All requests require `snapshot_id` equal to the artifact's `metadata.source_snapshot`. Exact `road_id` is preserved end to end. No synthetic fallback, writes, ingestion, migration or engineering-engine change.

| GET path | Response |
| --- | --- |
| `/roads/{road_id}` | `data` profile: street/name IDs, selected GeoJSON geometry, road source revision, stored latest_rating/latest_inspection_at/display_condition/display_basis, street_observation_count and permits_on_street |
| `/roads/{road_id}/pavement` | Named-street observations with source IDs, rating/category/date, on/from/to, original geometry, non-rating reason, source row key/revision |
| `/roads/{road_id}/permits` | On-street-name permits only, with unique permit ID, number/type/status, on/from/to, issue/valid dates and source revision |

Related lists accept `limit` (1–100; default 10) and `offset` (0–1,000,000; default 0). Order: inspection/issue date descending, then stable observation/permit ID ascending, null dates last. `meta.total_matching` counts the exact selected-road view; `next_offset` is null at end. Pagination is repeatable over the supplied unchanged artifact; offsets are scoped by the requested road/snapshot. Unknown/repeated parameters, invalid limits/offsets/kinds return 422. Road absent: 404. Missing file: 503 `STANDARDIZED_DATABASE_MISSING`; incompatible schema/metadata/row: 503 `STANDARDIZED_DATABASE_INCOMPATIBLE`; wrong source snapshot: 409 `STANDARDIZED_SNAPSHOT_MISMATCH`. Errors never include local paths or raw SQLite errors.

Every response has `data` and `meta` containing contract_version, snapshot_id, road_id, classification=derived_calculation, association_basis=on_street_name, verified_segment_condition=false, actual_construction_schedule=unknown, total_matching and next_offset. Individual values retain the classifications described in DATA_MODEL: rating/date observations; permits administrative records; name associations and bands derived. This envelope is deliberately separate from municipal-record-v2 and cannot be sent to existing planning endpoints as verified road evidence.

## M9 map reads

Implemented `GET /api/v2/standardized/map-ratings?snapshot_id=<exact-source-snapshot>&bbox=west,south,east,north&limit=2000`.

- Required bbox: finite, increasing WGS84, contained within `[-74.06,40.67,-73.95,40.76]` (approved map context). Required snapshot must equal the artifact's `metadata.source_snapshot`.
- `limit`: integer 1–2000, default 2000. Returns **all** intersecting road profiles in ascending road_id order. No cursor or partial success: more than limit returns 422 `VIEWPORT_TOO_BROAD`; zoom in. Unknown/repeated parameters, malformed/outside bounds or invalid limits return 422.
- `data`: existing Profile shape: road_id, street_key/name, segment_id, object_id, geometry, source_revision_id, original latest_rating/date, display_condition/basis, street_observation_count and permits_on_street. No inspection or permit histories. Geometry is selected LION reference geometry, not the scope of the named-street rating.
- Existing `standardized-read-v1` envelope, `road_id:null`, `total_matching=returned count`, `next_offset:null`, plus `map_contract:indicative-map-v1`, echoed numeric `bbox`, `complete:true`. Always `association_basis:on_street_name`, `classification:derived_calculation`, `verified_segment_condition:false`, `actual_construction_schedule:unknown`.
- Missing/incompatible artifact: existing sanitized 503 codes; snapshot mismatch: existing 409 code. There is no synthetic fallback, database mutation or automatic source refresh. Nonfinite ratings, negative counts and invalid map geometries fail explicitly. Unclassified/null ratings render neutral, without reclassifying source values.

`GET /api/v2/road-segments` and `/road-segments/geojson` now accept `limit` 1–2000 (default remains 100). Existing stable cursor and context binding remain. A bbox with limit >100, or any GeoJSON request, rejects >2000 total matches with 422 rather than silently omitting roads. Ordinary <=100 paged inventory reads remain compatible. The map requests one complete bounded road page; observations and permits retain their existing 100-record deterministic pagination. Already validated JSON-mode road records serialize directly without a second recursive framework conversion; provenance is retained.

## M10 visual planning client (no transport changes)

The visual editor uses existing official-screen-v1 preview/save/replay/notes and decision-support explanation endpoints above. LineStrings/forms translate to existing source-neutral work declarations and date-only alternative overrides; no new endpoints or request fields. Simple editor: two works/two alternatives; advanced API limits remain 30 works/three alternatives. Preview is explicit and unsaved; Save is explicit and immutable; saved-link navigation uses GET only. Explanations use exact saved ID/base and the unchanged allowlisted scalar projection. Invalid geometry/references/provenance/intervals retain authoritative server validation, errors and frozen replay. [M10 delivery and actual checks](M10_IMPLEMENTATION.md).
