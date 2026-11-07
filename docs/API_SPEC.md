# REST API contract

**Implemented through M2:** the five M1 GET paths plus GET `/api/v1/road-segments/{id}/conditions`, GET `/api/v1/repair-options`, GET `/api/v1/road-segments/{id}/repair-options`, POST `/api/v1/estimates`, GET `/api/v1/estimates/{id}`. All projects, conflicts, scenarios, comparisons, reviews and explanation routes below remain proposed. Base `/api/v1`, local server `http://127.0.0.1:8000`; no `/api/roads` or root `/health` aliases.

## Transport conventions

JSON except road feature collection responses, which use `application/geo+json`. Required request fields are listed with `!`; other fields are optional. IDs reference the same snapshot. Unknown fields are rejected in mutation/calculation inputs. Money is a two-decimal USD string; dates and geometry follow DATA_MODEL. Lists use `limit` 1–100 (default 30), opaque `cursor`, and stable ID ordering. M1 cursors encode the last ID, snapshot and bbox and reject mismatched filters/snapshots; clients must treat them as opaque. Bbox is an exact geometry intersection filter, including boundary contact. Proposed deterministic routes never invoke an LLM.

Ordinary success: `{ "data": <entity or list>, "meta": { "request_id": "...", "dataset_snapshot_id": "...", "warnings": [], "next_cursor": null } }`. For health, dataset_snapshot_id is null before seed. For GeoJSON, the top-level object is a FeatureCollection with `features` plus foreign member `meta` using the same metadata. Each feature ID is the RoadSegment ID and properties contain RecordMeta and non-geometry RoadSegment fields. M1 also includes the documented synthetic `condition_summary` projection (category, nullable decimal rating/scale/date, evidence_ids, data_kind and synthetic_input); it is not a municipal assessment or a separate mutable entity. Record detail includes nullable fields and unknown reasons, not fabricated defaults.

Errors: `{ "error": { "code": "VALIDATION_ERROR", "message": "...", "field_errors": [{"path":"...","reason":"..."}], "request_id": "..." } }`. No stack trace or secrets. Common errors: 422 malformed fields/geometry/unknown query value; 404 unknown referenced record; 409 incompatible snapshot or comparison basis; 503 persistence unavailable; 500 unexpected server fault. Unsupported methods use 405. List endpoints return empty lists for valid filters with no matches, never 404 for an empty collection. Demo imports reject geometry wholly outside the study window; intersecting source segments remain unclipped per DATA_SOURCES. No arbitrary client-supplied URL fetching.

The local MVP has no authentication and must not be publicly exposed. There are no project approval, spending, arbitrary SQL, ingestion-by-URL, or model tool-execution endpoints. `POST` below persists results when specified; it does not perform municipal actions.

## Endpoint contracts

Only the ten paths identified above are implemented. Assets/projects, conflict/scenario/review/explanation routes remain future work. The table includes their future contracts explicitly for planning; it does not claim implementation.

| Method and path | Input | Output / success | Validation and specific errors | Computation |
| --- | --- | --- | --- | --- |
| GET `/health` | none | 200 `{status:"ok", api_version:"v1", data_ready:bool, ai_mode:"deterministic" or "optional_provider"}` in envelope | 503 if configured required storage unavailable; missing key is not a health failure | deterministic; no provider probe |
| GET `/road-segments` | bbox optional `[west,south,east,north]` as comma-separated query; limit/cursor | 200 RoadSegment list | valid lon/lat bounds, west<east, south<north; 422 invalid cursor/bbox | deterministic read |
| GET `/road-segments/geojson` | same filters/pagination as list | 200 GeoJSON FeatureCollection | same 422 rules; implement static route before `/{id}` | deterministic read |
| GET `/road-segments/{id}` | ID | 200 RoadSegment | 404 missing ID | deterministic read |
| GET `/road-segments/{id}/assets` | road ID, limit/cursor | 200 InfrastructureAsset list | 404 road not found | deterministic read |
| GET `/road-segments/{id}/conditions` | road ID; complete bounded fixture history (no pagination) | 200 Assessment list in newest-date/stable-ID order; meta.latest_usable_id nullable | 404 road not found; latest selection uses date/stable-ID rule | deterministic read |
| GET `/projects` | road_segment_id, kind, schedule_status, start_date, end_date, limit/cursor optional | 200 WorkProject list with nullable UtilityWork `utility_work` child | 422 enum/date range; 404 supplied road missing; missing project dates included with warnings when filtering cannot resolve | deterministic read/filter |
| GET `/projects/{id}` | ID | 200 WorkProject plus nullable UtilityWork child | 404 missing ID | deterministic read |
| GET `/repair-options` | none; complete bounded catalog | 200 RepairOption list with full rates/productivity and assumption evidence | storage 503 | deterministic read |
| GET `/road-segments/{id}/repair-options` | road ID | 200 list of {option, suitability, preview, unavailable_reason}; preview is Calculation or null | 404 missing road; missing dimensions produce null preview and explicit reason | deterministic preview, no persistence |
| POST `/estimates` | road_segment_id!, repair_option_id!, dataset_snapshot_id!, optional planning_assumptions {length_m?,width_m?,unit:m,note!} | 201 saved Estimate; full input/output and sources | 404 road/option; 409 snapshot/evidence mismatch; 422 unknown fields, missing dimensions, nonpositive/nonfinite dimensions, invalid units or blank note | deterministic estimate, no AI |
| GET `/estimates/{id}` | ID | 200 saved CostEstimate | 404 missing ID | deterministic read |
| POST `/conflicts/check` | dataset_snapshot_id!, project_ids! nonempty distinct list capped at 50, proximity_m optional ≥0 default 5, reopening_horizon_days optional integer 0–365 default 30 | 200 ConflictCheckResult; persists positive findings and audit | 404 references; 409 snapshot mismatch; 422 invalid parameters; incomplete project fields produce indeterminate checks | deterministic geometry/date rules |
| GET `/conflicts/{id}` | ID | 200 ConflictFinding | 404 missing ID | deterministic read |
| POST `/scenarios` | name!, dataset_snapshot_id!, budget_usd!, planning_start!, planning_end!, cost_scope!, actions! per ScenarioAction; review_note optional | 201 saved Scenario with system-populated RecordMeta | 422 invalid dates, duplicates, no actions, invalid budget/units; 404 references; 409 snapshot mismatch | deterministic validation/save |
| GET `/scenarios` | dataset_snapshot_id optional, limit/cursor | 200 Scenario list | 422 invalid filters | deterministic read |
| GET `/scenarios/{id}` | ID | 200 Scenario | 404 missing ID | deterministic read |
| POST `/scenarios/{id}/evaluations` | proximity_m optional ≥0 default 5; reopening_horizon_days optional integer 0–365 default 30 | 201 immutable ScenarioEvaluation | 404 scenario; 409 invalid/stale source snapshot that cannot be reconstructed; incomplete data returns indeterminate fields, not fake zero totals | deterministic evaluation |
| GET `/scenario-evaluations/{id}` | ID | 200 immutable ScenarioEvaluation | 404 missing ID | deterministic read |
| POST `/scenario-comparisons` | evaluation_ids! 2–5 distinct IDs | 200 ComparisonResult table with metrics, deltas, common basis and warnings | 404 references; 409 mismatched snapshots, horizon, price basis, scope or method versions; 422 duplicate/invalid count | deterministic comparison; no automatic optimum |
| POST `/explanations` | evaluation_id!, mode optional enum deterministic/ai default deterministic | 200 ExplanationResult; explanation audit saved | 404 evaluation; 422 invalid mode; provider timeout, missing key or bad output return 200 explicit deterministic fallback; storage failure 503 | deterministic facts/templates, AI prose only when requested and configured |
| POST `/scenario-evaluations/{id}/reviews` | reviewer_label! 1–100 chars, note! 1–2000 chars, acknowledged_limitations! nonempty code list | 201 AuditEvent with action=review_note | 404 evaluation; 422 lengths/unknown limitation codes | human note recorded deterministically; not approval |
| GET `/evidence-sources/{id}` | ID | 200 EvidenceSource | 404 missing ID | deterministic read |

Road conditions are read-only assessments in the MVP. Project and asset creation are fixture/import responsibilities, not open user mutations. Scenario changes create a new Scenario ID; evaluations and audit events are immutable. Schema/system fields are populated by the service, not trusted from the caller.

## Calculation response details

**ConflictCheckResult**: `findings` (ConflictFinding list), `indeterminate_checks` (pair IDs, missing fields, reasons), `utility_coverage` (status plus scope/as-of/evidence), `checked_pair_count`, `method_version`, `input_hash`, `warnings`. One input project produces zero pairs and a warning; it never proves clearance. Check the selected set only and expose that scope. Scenario evaluation checks proposed action projects against all non-cancelled external projects within the saved snapshot and records that exact set. Hypothetical action-project records and stable IDs are embedded in the evaluation snapshot; findings can resolve both stored and hypothetical project references.

**ComparisonResult**: `evaluation_ids`, `common_basis` (snapshot, horizon, cost_scope, currency, price basis and method), `rows` (evaluation ID, cost range or null, budget and status, upper-bound status, elapsed days, lane-closure-days, per-action lifespan ranges, known findings count, indeterminate checks count, review flags), `deltas` (pair IDs and central cost/closure-day differences, nullable when incomplete), `warnings`. No ranking is implied. Delta savings use the same cost scope and remain hypothetical when synthetic inputs occur.

**ExplanationResult**: `id`, `evaluation_id`, `mode_used` deterministic/ai, `fallback_reason` nullable enum not_configured/provider_unavailable/timeout/invalid_output/unsupported_claim, `summary`, `claims` (claim_id, fact_refs, evidence_ids, rendered_text), `unknowns`, `limitations`, `human_review_required=true`, `input_hash`, `prompt_version` nullable, `model_label` nullable. Claims expose source references even in deterministic mode. AI_SYSTEM defines the stricter provider-only contract; its raw output is not the public response.

## Illustrative request, not a working endpoint

```json
{
  "name": "Demo coordinated repair",
  "dataset_snapshot_id": "demo-v1",
  "budget_usd": "150000.00",
  "planning_start": "2027-04-01",
  "planning_end": "2027-05-01",
  "cost_scope": "roadwork only; utility construction excluded",
  "actions": [{
    "id": "demo-action-coordinated",
    "road_segment_id": "demo-r-001",
    "repair_option_id": "demo-resurface",
    "source_project_id": "demo-road-project",
    "action_kind": "repair",
    "start_date": "2027-04-15",
    "end_date": "2027-04-22",
    "quantity": "800.00",
    "lanes_closed": 1,
    "assumption_evidence_ids": ["demo-assumptions-v1"]
  }]
}
```

This synthetic example asserts no real road dimensions, prices, schedule, or municipal budget. No update or approval is implied. Pagination and endpoint compatibility need contract tests as each milestone implements them; document the implemented subset explicitly.

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
