# REST API contract

**Implemented through M4:** the five M1 GET paths plus GET `/api/v1/road-segments/{id}/conditions`, GET `/api/v1/repair-options`, GET `/api/v1/road-segments/{id}/repair-options`, POST `/api/v1/estimates`, GET `/api/v1/estimates/{id}`. M3 additionally implements project list/detail, conflict analysis/list/detail and saved analysis retrieval below. M3.5 provided the scenario contracts; M4 implements scenario CRUD, immutable evaluation and comparison below. Reviews and explanation routes remain unimplemented. Base `/api/v1`, local server `http://127.0.0.1:8000`; no `/api/roads` or root `/health` aliases.

## Transport conventions

JSON except road feature collection responses, which use `application/geo+json`. Required request fields are listed with `!`; other fields are optional. IDs reference the same snapshot. Unknown fields are rejected in mutation/calculation inputs. Money is a two-decimal USD string; dates and geometry follow DATA_MODEL. Lists use `limit` 1–100 (default 30), opaque `cursor`, and stable ID ordering. M1 cursors encode the last ID, snapshot and bbox and reject mismatched filters/snapshots; clients must treat them as opaque. Bbox is an exact geometry intersection filter, including boundary contact. Proposed deterministic routes never invoke an LLM.

Ordinary success: `{ "data": <entity or list>, "meta": { "request_id": "...", "dataset_snapshot_id": "...", "warnings": [], "next_cursor": null } }`. For health, dataset_snapshot_id is null before seed. For GeoJSON, the top-level object is a FeatureCollection with `features` plus foreign member `meta` using the same metadata. Each feature ID is the RoadSegment ID and properties contain RecordMeta and non-geometry RoadSegment fields. M1 also includes the documented synthetic `condition_summary` projection (category, nullable decimal rating/scale/date, evidence_ids, data_kind and synthetic_input); it is not a municipal assessment or a separate mutable entity. Record detail includes nullable fields and unknown reasons, not fabricated defaults.

Errors: `{ "error": { "code": "VALIDATION_ERROR", "message": "...", "field_errors": [{"path":"...","reason":"..."}], "request_id": "..." } }`. No stack trace or secrets. Common errors: 422 malformed fields/geometry/unknown query value; 404 unknown referenced record; 409 incompatible snapshot or comparison basis; 503 persistence unavailable; 500 unexpected server fault. Unsupported methods use 405. List endpoints return empty lists for valid filters with no matches, never 404 for an empty collection. Demo imports reject geometry wholly outside the study window; intersecting source segments remain unclipped per DATA_SOURCES. No arbitrary client-supplied URL fetching.

The local MVP has no authentication and must not be publicly exposed. There are no project approval, spending, arbitrary SQL, ingestion-by-URL, or model tool-execution endpoints. `POST` below persists results when specified; it does not perform municipal actions.

## Endpoint contracts

Roads, planning, projects and M3 conflict routes listed as implemented below work locally. Generic assets and review/explanation routes remain future contracts; M4 scenario routes are implemented as clarified below.

| Method and path | Input | Output / success | Validation and specific errors | Computation |
| --- | --- | --- | --- | --- |
| GET `/health` | none | 200 `{status:"ok", api_version:"v1", data_ready:bool, ai_mode:"deterministic" or "optional_provider"}` in envelope | 503 if configured required storage unavailable; missing key is not a health failure | deterministic; no provider probe |
| GET `/road-segments` | bbox optional `[west,south,east,north]` as comma-separated query; limit/cursor | 200 RoadSegment list | valid lon/lat bounds, west<east, south<north; 422 invalid cursor/bbox | deterministic read |
| GET `/road-segments/geojson` | same filters/pagination as list | 200 GeoJSON FeatureCollection | same 422 rules; implement static route before `/{id}` | deterministic read |
| GET `/road-segments/{id}` | ID | 200 RoadSegment | 404 missing ID | deterministic read |
| GET `/road-segments/{id}/assets` | road ID, limit/cursor | 200 InfrastructureAsset list | 404 road not found | deterministic read |
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
| POST `/explanations` | evaluation_id!, mode optional enum deterministic/ai default deterministic | 200 ExplanationResult; explanation audit saved | 404 evaluation; 422 invalid mode; provider timeout, missing key or bad output return 200 explicit deterministic fallback; storage failure 503 | deterministic facts/templates, AI prose only when requested and configured |
| POST `/scenario-evaluations/{id}/reviews` | reviewer_label! 1–100 chars, note! 1–2000 chars, acknowledged_limitations! nonempty code list | 201 AuditEvent with action=review_note | 404 evaluation; 422 lengths/unknown limitation codes | human note recorded deterministically; not approval |
| GET `/evidence-sources/{id}` | ID | 200 EvidenceSource | 404 missing ID | deterministic read |

Road conditions are read-only assessments in the MVP. Project and asset creation are fixture/import responsibilities, not open user mutations. Scenario draft edits retain their stable ID and increment an optimistic revision; evaluations and audit events are immutable. Schema/system fields are populated by the service, not trusted from the caller.

## Calculation response details

**ConflictAnalysis** (M3): concrete fields are specified in DATA_MODEL. Includes findings, indeterminate_checks with spatial evidence, excluded_project_ids, utility_coverage=unknown, possible_pair_count, checked_pair_count, method_version, parameters, detection time, complete input_snapshot, input_hash, result_hash and stable ID. Only the explicit selected project set is checked. All roads are retained for corridor analysis; this does not imply all projects or utilities are known. A one-project scope returns zero pairs and a warning. Empty project_ids is 422. Missing project geometry/dates are accepted and remain unknown. Invalid topology is rejected, not repaired.

The previous proposed `/conflicts/check` and ConflictCheckResult draft are superseded by `/conflicts/analyze` and ConflictAnalysis; no compatibility alias is implemented. There is no date-range project-list filter in M3. M3 flattens utility scope/category fields into WorkProject and has no UtilityWork child. Saved analysis history provides reproducibility; the general AuditEvent and review-note workflow remains M5 work.

Project/conflict lists use the existing limit 1–100/default 30, stable-ID order and opaque cursors. M3 cursors bind to snapshot plus endpoint filters and reject reuse with different filters. Findings across all saved analyses are returned by default; use analysis_id for one version. Different input snapshots can intentionally retain findings for the same pair, with distinct analysis IDs. Valid no-match filters return empty arrays; incomplete coverage warning remains in metadata. Empty unseeded databases return empty lists. Unknown filter references return 404. GET never triggers analysis.

POST persists immutable analyses/findings transactionally. Identical inputs return the existing record/time; no duplicate findings are added. Changed inputs/parameters yield a new analysis. GET returns saved output without recomputation. The web client checks all loaded projects automatically after loading them (≤50); its layer controls only affect presentation. Project editing/creation is a fixture adapter responsibility, without an open mutation endpoint.

Implemented request:

```json
{"dataset_snapshot_id":"demo-m1-v1","project_ids":["demo-road-project","demo-utility-project"],"proximity_m":5,"corridor_m":5,"reopening_horizon_days":30}
```

This fictional pair yields one reopening_risk, a two-calendar-day gap, computed polygon overlap and shared R-001, with approximate-location/source-schedule warnings and required human review. No loss, savings, safe-deferral or clearance value is calculated. Query `/conflict-analyses/{id}` to retrieve complete provenance; numerical/source methods are documented in ARCHITECTURE.

**ScenarioComparison**: `evaluation_ids`, `common_basis` (snapshot, baseline_source_hash, horizon, cost_scope, currency, price basis and method versions), `rows` (evaluation ID, cost range or null, budget and status, upper-bound status, elapsed days, lane-closure-days, per-action lifespan ranges, known findings count, indeterminate checks count, review flags), `deltas` (pair IDs and central cost/closure-day differences, nullable when incomplete), `warnings`. No ranking is implied. Cost differences use the same cost scope and remain hypothetical when synthetic inputs occur.

**ExplanationResult**: `id`, `evaluation_id`, `mode_used` deterministic/ai, `fallback_reason` nullable enum not_configured/provider_unavailable/timeout/invalid_output/unsupported_claim, `summary`, `claims` (claim_id, fact_refs, evidence_ids, rendered_text), `unknowns`, `limitations`, `human_review_required=true`, `input_hash`, `prompt_version` nullable, `model_label` nullable. Claims expose source references even in deterministic mode. AI_SYSTEM defines the stricter provider-only contract; its raw output is not the public response.

## M4 scenario transport (implemented; clarifications below supersede design wording)

POST `/scenarios` accepts `contract_version=scenario-v1`, name, dataset_snapshot_id, budget_usd, `currency=USD`, planning_start/end, `cost_scope=roadwork_only`, and 0–50 actions conforming to DATA_MODEL's `scenario-action-v1`. Optional cost_scope_note/review_note have the documented length bounds. `assumptions`, `external_project_ids`, `project_overrides` and `mobilization_groups` default to empty lists. Dates remain half-open local civil dates; money and quantities are decimal strings. Scenario ID, resolved quantities, source contents, hashes and timestamps are server-controlled output. Classification is constrained to derived/hypothetical/synthetic literals; callers cannot assert observed work. Input provenance is validated against frozen sources or explicit synthetic assumptions, never trusted as a measurement. Nonblank text, strict integer counts, finite numbers and unknown-field rejection follow existing Pydantic boundary conventions.

Action requests contain id, contract_version, road_segment_id, action_kind, repair_category, nullable repair_option_id, scope, quantity, input_provenance, unknown_reasons, related_project_ids, nullable schedule and constraints. The DATA_MODEL tables define the nested fields and cross-field validation, not an unversioned flat quantity/date override. `source_project_id`, top-level action `start_date`/`end_date`, flat `quantity` string and `assumption_evidence_ids` from the former draft are superseded; no compatibility alias is needed because the draft was never implemented.

For example, this is only a QuantityProposal fragment for whole-segment R-001, not a complete POST body:

```json
{"value":null,"unit":"m2","derivation":"road_dimensions","length_m":null,"width_m":null}
```

The future service resolves the exact frozen road inputs to 100 m × 8 m = 800 m², preserving synthetic dimension provenance. It does not derive scope from the map geometry. A partial-area fragment instead uses explicit_area with a positive sourced value or unknown with a missing-input reason; there is no implicit whole-road fallback. Inline assumptions must be authored and referenced as specified in DATA_MODEL, not presented as observed records.

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

All paths below have the existing `/api/v1` prefix and `Envelope {data,meta}` response. Validation errors use the existing sanitized error envelope with field_errors; unknown references → 404, stale revision/incompatible comparison basis → 409, invalid inputs/unsupported adjustments → 422, storage failures → 503. No LLM/provider dependency. The earlier scenario table is a design summary; the concrete M4 transport here takes precedence. M5 explanation/review routes remain unimplemented.

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
