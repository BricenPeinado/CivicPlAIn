# Preliminary data model

Status: M2 implements synthetic RoadSegment maintenance attributes, related asset records, normalized ConditionAssessment history, a synthetic RepairOption catalog and immutable CostEstimate snapshots. M3 adds implemented WorkProject, ConflictFinding and immutable ConflictAnalysis records below. Scenarios, generic infrastructure assets and AuditEvent workflows remain proposed. The concrete M2 shapes below supersede their former planning drafts. Existing M1 JSON remains unchanged in storage; enriched reads preserve its API shape.

## Shared conventions

`!` means required and non-null; `?` means optional/nullable. Collections marked `!` must be present (empty allowed unless specified). IDs are stable opaque strings, unique by entity; demo IDs use `demo-` prefixes. Foreign keys must resolve in the same dataset snapshot. Dates are ISO `YYYY-MM-DD`; work intervals are `[start_date, end_date)` local to America/New_York. Instants are RFC3339 UTC. Money is a nonnegative two-decimal USD string over REST. M2 stores low/base/high totals in integer-cent columns alongside immutable JSON that preserves response strings and decimal inputs. Finite decimal quantities/rates use decimal strings; counts are integers.

The general planned entity convention is **RecordMeta** below (except EvidenceSource/AuditEvent). Implemented RoadSegment and Assessment use these applicable provenance fields. M2 catalog configuration and calculation/snapshot transport use their explicit source-aware shapes below: calculation provenance is in dimension_provenance/evidence_ids/input_snapshot and limits are in warnings/assumptions, rather than duplicate RecordMeta maps. Those concrete M2 definitions take precedence over the earlier generic draft:

| Field | Type / validation |
| --- | --- |
| id! | string, immutable |
| dataset_snapshot_id! | string, identifies frozen import/fixture manifest |
| evidence_ids! | nonempty list of EvidenceSource IDs; derived rows include inputs and method/assumption evidence |
| data_kind! | enum observed, synthetic, derived; derived does not imply observed inputs |
| synthetic_input! | bool; true for synthetic records or any synthetic dependency; propagated transitively |
| field_evidence! | map of material field path to nonempty source ID list, subset of evidence_ids; required for geometry, dimensions, condition, schedules, and numerical assumptions when populated |
| unknown_reasons! | map of null/omitted material field path to reason such as not_supplied, not_verified, not_applicable |
| limitations! | list of human-readable limitations, present even if empty |
| created_at! | UTC instant; record creation, not observation date |

Null means unknown/not applicable with a reason; zero is a known zero, never a replacement for missing data. Observed records need source observation/retrieval context; synthetic records need an explicit fixture assumption source. Derived results retain all upstream references and method versions. Mixed inputs remain derived with `synthetic_input=true`; labels must survive aggregation. Review annotations append an AuditEvent rather than silently changing history.

**Geometry** is a valid nonempty GeoJSON geometry in EPSG:4326, `[longitude, latitude]`, finite coordinate bounds. Validate topology and supported type. Record original CRS in source metadata; projected EPSG:32618 calculations are versioned derivations. **Range** contains decimal `lower`, `central`, `upper` with `0 ≤ lower ≤ central ≤ upper`, unit, and required method/basis text. Bounds are assumptions, not probabilities. Unknown range is null plus reason.

## RoadSegment

| Field | Type / validation |
| --- | --- |
| name? | string; no inferred official name for synthetic geometry |
| source_segment_key? | string, scoped to evidence dataset/version; not assumed unique citywide |
| geometry! | GeoJSON LineString; no empty/zero-length segments |
| study_area_id! | string, `lower-manhattan-window-v1` for MVP |
| length_m? | positive decimal; source measurement or documented projected derivation |
| width_m? | positive decimal; explicitly measured or assumed, never inferred from centerline |
| lane_count? | integer ≥1 |
| utility_coverage! | enum unknown, partial, verified_for_scope; last requires documented scope/time evidence, never excavation clearance |
| coverage_as_of? | date; mandatory for verified_for_scope in future observed ingestion |
| surface_material! | asphalt, concrete, gravel, unknown; unknown by default |
| functional_class! | local, collector, arterial, unknown |
| dimension_basis! | map length_m/width_m to synthetic_planning_assumption in current fixtures; legacy M1 sourced dimensions without basis are labeled legacy_synthetic_basis_unknown, never measured |
| repairable_area_m2? | nonnegative decimal, exactly length × width; null unless both dimensions known; zero cannot be estimated |
| notes? | authored planning note; never an inspection claim |

Relationships: one segment has many assets, assessments, and projects via their IDs; do not duplicate mutable lists on this record. Geometry provenance and width uncertainty are field-level evidence. Missing width blocks area-based estimates unless an explicitly sourced scenario assumption supplies it.

## InfrastructureAsset

| Field | Type / validation |
| --- | --- |
| road_segment_id? | RoadSegment ID; null allowed for unlinked utility asset |
| asset_type! | enum pavement, water, sewer, gas, electric, telecom, unknown |
| geometry? | GeoJSON Point, LineString, or Polygon; null means location unverified |
| owner_name? | string; avoid individual contact details |
| installed_on? | date; cannot assert later than an observed assessment without explanation |
| depth_m? | decimal ≥0; source evidence required, never inferred from permit |
| location_status! | enum observed, assumed_demo, unknown |

Validation: at least segment reference or geometry for pavement; utilities may have neither and remain unknown. Location status must match provenance. Asset existence is not proof of planned utility work. Assessments reference assets when appropriate.

## ConditionAssessment (implemented M2)

Read-only records contain `id`, `road_segment_id`, `dataset_snapshot_id`, `category` (good/fair/poor/unknown), nullable decimal `rating`, nullable `rating_scale`, nullable `assessed_on`, `assessment_method=synthetic_fixture`, `notes`, nonempty `evidence_ids`, `data_kind=synthetic`, `synthetic_input=true`, `field_evidence`, `unknown_reasons`, `limitations`, and offset-aware `created_at`. Populated rating/category/date fields require evidence; null fields require unknown reasons. These are authored demo dates, not certified inspections. No observed import or edit endpoint is implemented.

Preserve the established `synthetic-1-10-higher-better` scale: 1 ≤ rating ≤10; good ≥8, fair ≥5 and <8, poor <5. Unknown has no rating, scale or date. This is not official PCI. Configuring a different scale is deferred until a reviewed source requires it. History retains dated and undated records. Latest usable = newest dated record with rating, stable ID ascending ties; if only undated ratings exist, lowest ID is the undated summary. Undated rows never supersede dated evidence and never mean current. No freshness/engineering safety certification is inferred.

The API returns the complete bounded per-road history and `meta.latest_usable_id`; road collection, GeoJSON and detail share the same derived condition summary. In an M1-only database, the original undated summary remains visible until the explicit M2 seed adds historical records.

## WorkProject (implemented M3)

Required fields: `id`, `title`, `description`, `kind` (road_repair/utility/other), `infrastructure_category` (water/sewer/gas/electric/telecommunications/road_resurfacing/road_reconstruction/other), `work_type` (resurfacing/reconstruction/excavation/inspection/maintenance/other), `schedule_status` (planned/tentative/active/completed/cancelled/unknown), `schedule_basis` (confirmed_source/permit_window/assumed_demo/unknown), `location_status` (source_reported/approximate/unknown), `road_segment_ids` (distinct, ≤30, empty allowed), and the provenance fields below. Category and kind must agree. Titles/descriptions cannot be blank. Responsible organization is nullable; no individual contacts are stored.

`geometry` is a nullable valid nonzero LineString or positive-area Polygon in EPSG:4326, longitude/latitude, wholly within the Lower Manhattan study window. Polygon rings must explicitly close and be topologically valid. No silent repair, clipping, guessed position or numeric location-confidence probability. Null geometry requires location_status=unknown; approximate geometry must be labeled approximate. Source-reported geometry does not establish physical utility position/depth. Multi-road projects use one work-zone geometry plus multiple affected road references, not duplicated project rows. MultiPolygon and general geographic ingestion are deferred.

Nullable `start_date`/`end_date` are planned civil dates; `actual_start_date`/`actual_end_date` are actual civil dates when supported. Every complete pair must have start < end under `[start,end)`. Actual end requires actual start and completed status. Completed status may have unknown actual dates, which yields indeterminate temporal checks. Unknown schedule basis cannot carry planned dates. A permit_window is a source window, not an assertion that construction will occur then. Cancelled records are stored but explicitly excluded from screening; completed records are only considered as preceding sequential work using actual dates.

Nullable `excavation_required` is an explicit boolean; null means unestablished. Nullable nonnegative integer `lanes_closed` is a source declaration, not inferred from category. Nullable `estimated_cost_usd` is a finite nonnegative Decimal with at most two decimal places; `currency=USD`. No cost is inferred or used to compute savings/loss. Actual estimates remain the separate M2 CostEstimate contract.

Provenance: `dataset_snapshot_id`, nonempty `evidence_ids`, `field_evidence`, `unknown_reasons`, `limitations`, `data_kind` (synthetic/observed), `synthetic_input`, offset-aware `created_at`/`updated_at` (updated ≥ created). Synthetic status and flag must agree; synthetic IDs require `demo-`. Material category/type/status/basis/location/roads, populated geometry/dates/organization/excavation/closures/cost require source IDs drawn from evidence_ids. Null material fields require a nonempty unknown reason. The current seed imports synthetic records only with full EvidenceSource contents; accepting an observed classification structurally is not an implemented observed-data adapter or a claim that any observed project exists.

Persistence: `work_projects(id,dataset_id REFERENCES dataset,payload)` and normalized `project_roads(project_id REFERENCES work_projects,road_id REFERENCES roads,PRIMARY KEY(project_id,road_id))`; a road-first index supports linkage. No open create/update/delete endpoint exists. Stable seed IDs preserve local payloads and links on repeat import. References must resolve in the same snapshot.

## UtilityWork boundary

M3 keeps utility category, work type, organization, excavation requirement and location uncertainty directly on WorkProject. This supersedes the former planned optional UtilityWork child and avoids duplicate schedule/geometry models. No UtilityWork table or `utility_work` API child exists. The broader generic utility-asset lifecycle, permit linkage, depth and observed ingestion remain future contracts. Missing utility records/location never establishes safe excavation.

## RepairOption (implemented M2 catalog)

`id`, `treatment` (preventive, resurface, reconstruct), `label`, `description`, `scope_of_work`, `suitability_conditions`, `material_assumptions`, `work_activities`, `quantity_unit=m2`, `unit_rates_usd={low,base,high}`, `rate_inclusions`, `mobilization_usd`, `traffic_management_usd`, `contingency_fraction`, `productivity_per_day`, `productivity_unit=m2/active_workday`, nonnegative integer `setup_days`/`curing_days`, `price_basis_date`, `sensitivity_basis`, `exclusions`, `limitations`, `evidence_ids`, `data_kind=synthetic`, `synthetic_input=true`. Catalog configuration is not a municipal observation or independently mutable domain asset.

Rates and allowances are finite nonnegative Decimals; low ≤ base ≤ high; contingency in [0,1]; productivity strictly positive. Only metric m² quantity and m²/active_workday productivity are accepted. Bundled rates include materials/labor/equipment once. The reviewed fixture explicitly defines low bundled rates at −20%, high at +30% from base; quantity, mobilization, traffic allowance, productivity and contingency fraction remain fixed. No statistical confidence is implied. No arbitrary rate, area-only, productivity or duration override API is supported.

Suitability is `candidate_requires_review` when a dated synthetic asphalt assessment's category matches its demo treatment (good→preventive, fair→resurface, poor→reconstruct); `not_indicated` for another category/treatment pairing; `requires_review` for missing/undated assessment or unknown/non-asphalt surface. Every result has `rule_id`, rationale and `human_review_required=true`. These are condition-screening rules, not feasibility judgments or safe-work labels.

## CostEstimate (implemented M2)

An estimate has `id`, UTC `created_at`, `dataset_snapshot_id`, `road_segment_id`, `repair_option_id`, `repair_category`, `currency=USD`, positive decimal `quantity` with `quantity_unit=m2`, `dimension_provenance`, three `scenarios` (low/base/high), `duration`, `suitability`, `assumptions`, `warnings`, `evidence_ids`, `method_version=repair-estimate-v1`, `data_kind=derived`, `synthetic_input=true`, `input_snapshot`, `input_hash` and `result_hash`.

Each scenario has `line_items` (label, decimal quantity, unit m2/allowance, decimal unit_rate_usd, two-decimal amount_usd, evidence_ids), two-decimal `subtotal_usd`, decimal `contingency_fraction`, two-decimal `contingency_usd` and `total_usd`. Round each line using Decimal ROUND_HALF_UP, sum lines, round contingency, then add. Mobilization/traffic each use quantity 1 allowance. No component double counting. Monetary totals persist as integer cents alongside frozen JSON; REST amounts are strings. Unit rates retain decimal precision instead of being rounded before multiplication.

`duration` has `active_workdays=ceil(quantity/productivity_per_day)`, `setup_days`, `curing_days`, `total_preliminary_days` (their sum), productivity and unit, and a basis/limitation string. These preliminary sequential days are not a contractor calendar. No calendar date or lifespan is manufactured.

`dimension_provenance` records each input's value, meter unit, basis, evidence IDs and note. A request may supply `planning_assumptions={length_m?,width_m?,unit:m,note}` with at least one positive dimension and a nonblank note. Dimensions support at most three decimal places (input resolution, not measured accuracy). Length is capped at 100,000 m, width at 100 m for this bounded prototype. Unknown required dimensions return 422; no estimate is saved. Overrides are labeled `user_planning_assumption` and stored under inline source ID `user-planning-assumption`, not silently treated as measured evidence.

`input_snapshot` contains the exact enriched road, chosen assessment, complete repair option, request, evidence records and method version; user assumptions are retained inline. SHA-256 hashes use sorted-key compact ASCII JSON; input hash covers snapshot, result hash covers the Calculation fields. IDs and creation times are excluded from semantic result hashing. Replay calls the pure calculation engine with these saved model inputs. Subsequent record/catalog changes cannot rewrite history. No estimate update/delete route exists; SQLite triggers reject both operations.

## ConflictFinding (implemented M3)

`id`, `analysis_id`, exactly two canonical distinct `project_ids`, `affected_road_ids`, `finding_type`, `priority=coordination_review`, `spatial_evidence`, `temporal_evidence`, deterministic `explanation`, `required_review`, `data_quality_warnings`, `evidence_ids`, `method_version=conflict-screen-v1`, `input_hash`, offset-aware `detected_at`, `data_kind=derived`, and transitive `synthetic_input`.

Types: `concurrent_work`, `reopening_risk` (potential pavement rework), `multiple_closures`, `sequencing_review`. Priority is a transparent review policy, not validated severity/safety. `affected_road_ids` is the union of both projects' declared roads and their shared screened corridor IDs; it is not a surveyed conflict footprint. Evidence references include project and affected-road sources.

`spatial_evidence`: `classifications` (confirmed_geometric_overlap/shared_affected_road/proximity_based_potential_overlap/insufficient_spatial_information), nullable nonnegative computed `distance_m`, `polygon_overlap`, `geometry_intersects`, `shared_road_ids`, `shared_corridor_ids`, and `basis`. Positive polygon area is computed separately from the potential classification for approximate footprints. Missing distance is unknown, never zero. Geometry confirmation means supplied-shape overlap only. Point/line contact, shared road and centerline corridor are screening signals without depth/grade confirmation. No derived overlap geometry is persisted; map highlights the original work zones.

`temporal_evidence`: project-keyed `intervals` and `interval_basis` (planned/actual), nullable `overlap_start`/`overlap_end`, nullable nonnegative `gap_days`, nullable `preceding_project_id`, and `basis`. Concurrent findings retain the positive half-open intersection; sequential findings retain the preceding project and 0–horizon gap. Original planned and actual dates remain in the source snapshot. Human review covers location/depth/grade, work scope, restoration, schedule and access. No financial-loss or safety conclusion is generated.

## ConflictAnalysis (implemented M3)

`id`, `dataset_snapshot_id`, `findings`, separate `indeterminate_checks` (project_ids, missing_fields, reason, spatial_evidence), `excluded_project_ids` (cancelled), `possible_pair_count`, `checked_pair_count` (indexed candidates actually examined), `utility_coverage=unknown`, `warnings`, `parameters`, `method_version`, `detected_at`, `input_snapshot`, `input_hash`, `result_hash`. One selected non-cancelled project is valid, with zero pairs and an explicit warning. Missing location checks may coexist with known shared-road findings; unknown schedules cannot create positive temporal findings. Unknown coverage does not depend on count.

Parameters: finite meter-valued `proximity_m` 0–100 (default 5), `corridor_m` 0–50 (default 5), integer `reopening_horizon_days` 0–365 (default 30). Parameter keys encode units; extra or inconsistent unit fields are rejected. Bounds cap this study-area screening prototype and are not engineering standards.

Snapshot freezes sorted complete projects, all roads used for corridor/reference screening, complete source contents, parameters, exchange/calculation CRS and method/library versions. Canonical M2 hash encoding applies. Analysis IDs hash inputs; finding IDs hash the input hash, sorted pair and type; semantic result hash excludes detection time. Same inputs reuse the first saved time and result; changes create distinct immutable history. Replay uses saved inputs and recorded library versions.

Storage: `conflict_analyses(id,dataset_id,payload)` and `conflict_findings(id,analysis_id,payload)`, with foreign keys, analysis index and UPDATE/DELETE rejection triggers. Migration version 3 is additive. JSON is Pydantic validated on reads. No general AuditEvent/review-note lifecycle is claimed. See ARCHITECTURE for exact spatial/temporal rules and false-positive limits.

## Scenario

| Field | Type / validation |
| --- | --- |
| name! | nonempty string |
| budget_usd! | money ≥0, roadwork-only scope for demo |
| planning_start!, planning_end! | dates, start < end; common comparison horizon |
| cost_scope! | string, same basis across compared scenarios |
| actions! | nonempty list of ScenarioAction objects |
| review_note? | human text, limited length; no authorization semantics |

**ScenarioAction**: `id!` string unique within scenario; `road_segment_id!`, `repair_option_id!`; `source_project_id?`; `action_kind!` enum repair, temporary_patch, repeat_restoration; `start_date!`, `end_date!` with start<end within planning horizon; `quantity!` positive decimal in option units; `lanes_closed?` integer ≥0; `assumption_evidence_ids!` nonempty list. Dates/quantity are proposals, not changes to observed projects. Duration must match the chosen estimate or have an explicit versioned override. Duplicate identical actions are rejected. Repeat restoration must be explicit and justified, never auto-added by a finding. Scenario data_kind is synthetic or derived and never implies approval.

## ScenarioEvaluation

| Field | Type / validation |
| --- | --- |
| scenario_id! | Scenario ID; snapshot retains exact scenario version |
| evaluated_at! | UTC instant |
| input_snapshot! | canonical JSON of scenario/actions, records, evidence, parameters, and per-action estimates or missing reasons |
| input_hash!, result_hash!, method_version! | strings; timestamps/generated IDs excluded from semantic hashes |
| cost_total_usd? | Range in USD, null if any required action estimate missing |
| budget_usd! | money copied into immutable snapshot |
| budget_status! | enum within_budget, over_budget, indeterminate; central estimate criterion only |
| upper_bound_within_budget? | bool, null if bounds unavailable |
| elapsed_days? | integer ≥0, null if required dates missing |
| lane_closure_days? | decimal ≥0, null if required lane assumptions missing |
| action_lifespan_years! | map action ID to Range or null; never sum lifespans |
| conflict_finding_ids! | list of ConflictFinding IDs calculated for proposed actions plus external work |
| indeterminate_checks! | list of project/action pairs, missing_fields, and reason |
| utility_coverage! | enum unknown, partial, verified_for_scope, with explicit scope limitations |
| review_required! | bool; true for demo and unresolved safety/coverage assumptions |
| warnings! | list of typed codes and messages |

data_kind=derived. Unknown totals force budget_status=indeterminate. Comparison requires matching snapshot, horizon, currency, price basis, and cost scope; reject incompatible evaluations. Evaluation is append-only. Domain findings against hypothetical actions use stable action-derived project IDs recorded in input_snapshot and response evidence.

## EvidenceSource

| Field | Type / validation |
| --- | --- |
| id! | stable string |
| title!, publisher! | nonempty strings; synthetic sources name CivicPlAIn demo assumptions |
| source_kind! | enum public_dataset, manual_observation, demo_assumption, calculation_method |
| verification_status! | enum verified_accessible, candidate_unverified, synthetic_demo; matches DATA_SOURCES meanings |
| uri? | verified source URL or repository-relative fixture/method path; do not accept arbitrary remote fetch instructions |
| retrieved_at?, observed_on? | UTC instant / civil date; synthetic assumptions need no invented observation date |
| version? | source release or method version if known |
| checksum_sha256? | 64 lowercase hex characters; required for imported local fixture/source payload |
| original_crs? | string; required for geographic imports when known, otherwise unknown reason |
| coverage_note!, reliability_note! | strings, describing scope and limitations |
| license_note? | actual reviewed terms or explicit unknown; not inferred from public access |
| unknown_reasons! | map field path to reason |

Catalog accessibility and imported payload validation are different facts. Candidate sources cannot back a claimed observation until actually reviewed/imported. Assumption evidence includes formulas, units, bounds, and synthetic status. Derived records link upstream evidence, avoiding circular references.

## AuditEvent

| Field | Type / validation |
| --- | --- |
| id!, occurred_at! | stable ID, UTC instant |
| actor_kind! | enum human, system; model cannot be an approving actor |
| actor_label! | local reviewer label or system component, not verified identity in unauthenticated MVP |
| action! | enum import, estimate, conflict_check, evaluate, explain, review_note |
| entity_type!, entity_id! | target type/ID; explanation IDs may identify transport-only results |
| request_id! | correlation ID |
| input_hash?, result_hash?, method_version? | metadata needed to reproduce relevant derived operations |
| evidence_ids! | source ID list, required nonempty for derived operations |
| mode? | enum deterministic, ai; explanation events only |
| outcome! | enum success, fallback, failed |
| detail! | typed, redacted JSON; review text, warning codes, model/prompt version, validation result as applicable |

Append-only at the application boundary, not claimed tamper-proof. Never store API keys, authorization headers, hidden model reasoning, raw personal information, or unredacted prompts. A review note records acknowledgement and remaining questions, not engineering approval or spending consent.

## Historical M1 storage and condition projection

SQLite tables: `dataset(id PRIMARY KEY, manifest_json)`, `evidence(id PRIMARY KEY, dataset_id REFERENCES dataset(id), payload)`, `roads(id PRIMARY KEY, dataset_id REFERENCES dataset(id), payload)`. Payloads are JSON validated through Pydantic on import and read, preserving nullable decimal strings, dates, geometry and per-field provenance. Only synthetic records are accepted by the M1 implementation; observed/derived entities above are future contracts, not working import types. M1 supports exactly one snapshot per database. Imports use stable IDs, checksum validation, foreign keys and a transaction. No mutation endpoint existed in M1; M2 adds only estimate creation.

The RoadSegment transport additionally includes a required, read-only **condition_summary** for this milestone:

| Field | Implemented meaning |
| --- | --- |
| category | good, fair, poor, unknown; text accompanies all color styling |
| rating | Decimal string 1–10 or null |
| rating_scale | `synthetic-1-10-higher-better`, or null without an assessment |
| assessed_on | Nullable ISO date; all M1 fixtures are undated, not current observations |
| evidence_ids | Nonempty subset of the road evidence references |
| data_kind / synthetic_input | `synthetic` / true |

The fixture-only categorization rule is good ≥8, fair ≥5 and <8, poor <5; unknown has no rating, scale or date. This is an authored demo rule, not normalization of an official NYC scale. The manifest freezes it. Material populated fields have field_evidence; null material fields have unknown_reasons. Geometry is a nonzero valid EPSG:4326 LineString. All records preserve unknown utility coverage.

The projection carries no independently mutable assessment list. M2 now derives this projection from full ConditionAssessment history using latest-dated/stable-ID selection when M2 records exist. No costs, dimensions, observed dates, utility routes or schedules are inferred for M1.

## M2 related records and storage

`maintenance_assets(road_id REFERENCES roads PRIMARY KEY, payload)` stores one optional AssetAttributes record per road: nullable positive `length_m`/`width_m`, surface, functional class, synthetic dimension basis, evidence IDs, synthetic designation and notes. This is a related pavement-planning extension, not the proposed generic InfrastructureAsset lifecycle. The read projection copies related dimensions/provenance, derives rectangular area, and retains raw M1 JSON. All current imports remain synthetic-only; future observed ingestion must extend schemas with reviewed provenance semantics first.

`assessments(id PRIMARY KEY, road_id REFERENCES roads, assessed_on, payload)` retains history with a road/date/ID index. `repair_options(id PRIMARY KEY, dataset_id REFERENCES dataset, payload)` holds the validated catalog. `fixture_imports` freezes M2 manifest identity without changing the M1 dataset manifest. `schema_migrations` records additive version 2. `estimates(id, road_id, dataset_id, payload, low_cents, base_cents, high_cents)` enforces nonnegative ordered totals and immutable records. All JSON is validated on import/read. Referenced road and source IDs must resolve in the same dataset during seed. Startup creates schema only; the explicit CLI adds fixtures idempotently without overwriting existing records.

M3 now implements WorkProject and conflict snapshots as specified above. Generic assets, scenarios and audit-event/review-note workflows remain unimplemented. M2 estimates and original stored road payloads are preserved.
