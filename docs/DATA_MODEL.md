# Preliminary data model

Status: M2 implements synthetic RoadSegment maintenance attributes, related asset records, normalized ConditionAssessment history, a synthetic RepairOption catalog and immutable CostEstimate snapshots. M3 adds implemented WorkProject, ConflictFinding and immutable ConflictAnalysis records below. M3.5 defines versioned proposed scenario/action contracts; scenarios, generic infrastructure assets and AuditEvent workflows remain unimplemented. The concrete M2 shapes below supersede their former planning drafts. Existing M1 JSON remains unchanged in storage; enriched reads preserve its API shape.

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

### Proposed patch/restoration catalog extensions (M4 source gate)

The existing RepairOption schema accepts only three treatments. No patch/restoration alias or new option is added in M3.5. Proposed `repair-option-v2` extends treatment with `temporary_patch` and `trench_restoration`, retaining the current explicit m² rates/allowances/productivity/contingency fields and their typed bounds. It also requires a sourced `conflict_work_type` mapping to an existing M3 work type and `lifespan_years` (nullable Range with reason/source). V1 catalog payloads and M2 estimate responses stay unchanged; absence of lifespan means unknown.

A new method needs nonblank reviewed scope, material/activity description, compatible extent/unit, applicability and exclusions; low/base/high bundled rates with derivation and USD price date; mobilization/traffic/contingency; positive m²/active_workday productivity and setup/curing allowances; complete evidence, limitations, version and immutable manifest checksums. The existing Decimal line/allowance/contingency and ceiling-duration rules are reused through the single factored costing helper. V2 options use a separately versioned scenario result supporting the new categories, not the current three-category M2 Calculation DTO or endpoint. No geometry-derived trench area or automatic repeat charge is permitted. Missing source-backed parameters leave the method unavailable. Any future lifespan range is a labeled assumption with basis/evidence, never verified performance by default. No numerical rates, productivity or lifespan values for these methods have been adopted.

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

## Scenario (proposed M4; contract `scenario-v1`)

M3.5 freezes the following design only. No Scenario/ScenarioAction Pydantic models, database tables, routes, evaluation service or UI are implemented. These definitions supersede the earlier flat quantity/date/action draft. Runtime M1–M3 contracts and immutable fixtures are unchanged.

A scenario has system-generated RecordMeta (`data_kind=derived`, transitive synthetic flag), `contract_version=scenario-v1`, nonblank `name` (1–200 chars), `dataset_snapshot_id`, nonnegative two-decimal `budget_usd`, `currency=USD`, `planning_start` and `planning_end` (start < end), `cost_scope=roadwork_only`, optional `cost_scope_note` (1–2000 chars), and 1–50 `actions`. The horizon is half-open in America/New_York. `review_note` is optional text (1–2000 chars), never an approval. Comparisons require the same horizon, currency, cost scope, baseline_source_hash, price basis and method versions, not just matching display labels or dataset ID. baseline_source_hash covers the common original roads, catalog, selected external projects (before overrides) and their evidence. Scenario-specific action assumptions, quantities, dates and overrides may differ and remain visible; they are not required to hash identically across alternatives.

Scenario-level `assumptions` is a list of `{id, note, field_paths}`: distinct IDs (1–100 chars), nonblank notes (1–2000 chars), and nonempty material field paths. These are explicitly authored planning assumptions, not measurements. The future service will generate complete inline synthetic EvidenceSource records with stable namespaced IDs, version, limitations, canonical content checksum and source URI `scenario:<scenario-id>:assumption:<id>`. Hash content before adding its checksum to avoid circular hashing. These records stay inside the immutable scenario/evaluation snapshot, not in the M1 evidence table. Request provenance may use `assumption:<local-id>` references to that list; the service resolves these aliases to namespaced snapshot source IDs. Existing sources resolve by ID; callers cannot overwrite their contents. General observed-source adapters remain unimplemented.

`external_project_ids` explicitly selects existing projects. `project_overrides` is a list of `{project_id, operation: exclude|replace, replacement_action_ids, reason, evidence_ids}`. IDs must resolve in the same snapshot. Exclude requires an empty replacement list; replace requires at least one distinct existing action ID. Each project has at most one operation. Related-project references alone never exclude anything. The saved snapshot retains originals, selected scope, overrides and reasons. `mobilization_groups` defaults to an empty list; its proposed contract is below.

### ScenarioAction (proposed `scenario-action-v1`)

| Field | Type / validation |
| --- | --- |
| `contract_version` | literal `scenario-action-v1` |
| `id` | nonblank string, 1–100 chars, unique in scenario |
| `road_segment_id` | required existing target road ID in scenario snapshot |
| `action_kind` | `repair`, `temporary_patch`, `repeat_restoration`; repeats need explicit justification in scope/provenance |
| `repair_category` | `preventive`, `resurface`, `reconstruct`, `temporary_patch`, `trench_restoration`, `unknown`; last three have no current catalog method |
| `repair_option_id` | existing catalog ID or null with reason; when present its treatment must match the category; unknown non-null IDs are errors |
| `scope` | `{extent: whole_segment\|partial_area\|utility_trench\|unknown, description, geometry, location_status}`; nonblank description; nullable valid M3 work-zone geometry; status `approximate` or `unknown` for a proposal |
| `quantity` | required QuantityProposal below; known quantity is finite, strictly positive and in m²; null is never zero |
| `input_provenance` | map of populated material field paths to `{basis: source_record\|planning_assumption\|derived, evidence_ids, record_id, record_field, note, method_version}`; nonempty resolved source IDs; record_id/record_field non-null for source_record and null otherwise and validated against the exact frozen field/value; derived values require method version; assumptions require note |
| `unknown_reasons` | nonblank reason for every material null/unknown, including absent method, quantity, geometry, schedule or closure declaration |
| `related_project_ids` | distinct existing IDs, empty allowed; relationship only, not replacement or inherited schedule/location |
| `schedule` | nullable SchedulingProposal below |
| `constraints` | `{earliest_start, latest_end, must_follow_action_ids, human_review_required:true}`; dates nullable, precedence IDs distinct; no self-reference or cycles |

System-controlled fields identify `hypothetical=true`, `data_kind=derived` and transitive `synthetic_input`; they are not caller claims of observed work. Every proposal in the current synthetic demonstration has `synthetic_input=true`. Null scope geometry requires location_status=unknown; non-null proposal geometry requires approximate. Scope geometry must pass M3 longitude/latitude, topology and study-bound checks; a road centerline can be an explicitly labeled corridor reference, never a measured pavement or trench footprint. Unknown geometry stays null. No buffer infers utility width, depth or location. Category `temporary_patch` requires action_kind `temporary_patch`; `trench_restoration` requires scope extent `utility_trench`. Whole-segment/partial-area resurfacing is not automatically an appropriate utility-restoration method.

Material fields include category, option, scope, quantity inputs/output, geometry, dates, closures, constraints and project overrides. Provenance references must resolve to frozen existing evidence or scenario assumptions, and source-record references must match their typed record_id/record_field and actual upstream field evidence; a caller note cannot establish an observation. Derived provenance records the derivation and upstream sources. Blank text, extra fields, invalid geometry, incompatible units/categories, duplicate semantic actions and contradictory inputs are rejected. Repeated work needs a distinct scope/time and explicit repeat justification; a second ID does not justify double charging.

### QuantityProposal and repair scope

`quantity = {value, unit:m2, derivation, length_m, width_m}`. Decimal fields serialize as strings, not floats. `derivation` is `road_dimensions`, `explicit_rectangle`, `explicit_area` or `unknown`. Inputs retain the current M2 positive dimension bounds (length ≤100,000 m; width ≤100 m; at most three decimal places); direct area is ≤10,000,000 m² with at most six decimal places. Product precision is retained through the existing Decimal rounding path.

| Scope / derivation | Resolution rule |
| --- | --- |
| Whole segment / `road_dimensions` | Resolve length and width from the exact enriched road snapshot, retaining dimension basis/evidence. Request dimensions must be null; optional asserted value must equal the resolved product. Snapshot records resolved dimensions/value and method `rectangular-scope-v1`. Missing dimension gives unavailable quantity with reason; an asserted value cannot replace missing source dimensions or be accepted as a measurement. |
| Whole, partial or trench / `explicit_rectangle` | Both positive dimensions and a planning-assumption source are required; derive exact length × width, reject a conflicting asserted value. A whole-segment override must explicitly acknowledge the changed scope. Do not modify the source road. |
| Partial area or utility trench / `explicit_area` | Positive `value` and an explicit area assumption/source required; length/width must be null. No fabricated rectangular dimensions. Trench area is supplied restoration scope, not inferred from utility centerlines or conflict geometry. |
| Unknown extent / `unknown` | Value and dimensions null with reasons; no cost/quantity available. A known extent may also use unknown derivation while awaiting inputs. |

For computed methods, request `value` may be null pending resolution; canonical snapshots record the resolved value or missing-input reason. An authored synthetic dimension stays synthetic even when its product is deterministic. No geometric measurement method is added. A missing/unsupported repair option or quantity makes action cost unavailable and the complete scenario total/budget status indeterminate; known component subtotals may be shown separately as incomplete. Never map `demo-preventive` to patch or `demo-resurface` to trench restoration just to obtain a number.

M4 must reuse the existing estimate engine: full-road actions can use `calculate`; explicit-area support needs a pure validated quantity/costing helper factored from that same implementation, with the M2 wrapper preserving `repair-estimate-v1` output/hashes. No second formula, fake road dimensions or new area override on the existing `/estimates` endpoint. Refactoring and the new `scenario-cost-v1` path are M4 work, not implemented in M3.5.

### SchedulingProposal (proposed `schedule-proposal-v1`)

`{contract_version, start_date, end_date, basis:supplied_calendar_interval, assumption_evidence_ids, note, work_calendar, closure_intervals}`. Either date may be null with a reason; every complete pair must have start < end and lie within the planning horizon and supplied constraints. All dates are America/New_York civil dates with half-open intervals. Nonempty assumption references and a nonblank note explain any supplied proposal dates. No dates are inferred from the estimate, related project, current date or utility end date. Present constraint bounds must be ordered and within the horizon; every precedence reference must resolve to another action and the graph must be acyclic. Known dates must satisfy bounds and the precedence relation predecessor end ≤ successor start; reject a violation. If required dates are missing, constraint satisfaction remains indeterminate, not satisfied.

M2 `active_workdays` is the ceiling of quantity/productivity. `setup_days` and `curing_days` are separate preliminary allowances. Their sum `total_preliminary_days` is a planning duration, not a calibrated work-calendar duration or promised completion date. The R-001 result remains 2 active + 2 setup + 1 curing = 5 preliminary days. Do not require a calendar interval's length to equal 5: weekends, curing treatment, access and phasing may differ and need explicit assumptions.

Optional `work_calendar` is `{id, version, timezone:America/New_York, working_weekdays, excluded_dates, evidence_ids, note}`; weekdays are distinct ISO integers 1–7, at least one; exclusions are distinct dates. This records assumptions only. It does not activate date generation, weather modeling, holiday discovery or scheduling optimization. Missing calendar never implies weekdays, weekends or an official holiday schedule.

`closure_intervals` is null (unknown) or a list of `{start_date,end_date,lanes_closed,evidence_ids,note}` within a complete supplied action interval. Lane counts are strict nonnegative integers; a known road lane count caps closures. Intervals for one action must not overlap. An empty list needs an explicit sourced assertion of no closure; null never becomes zero. Setup/curing may cause closure only when explicitly included. Lane-closure-days use these supplied intervals, not active workdays or an implicit full-schedule closure. Missing required dates/closures gives null metrics and incomplete conflict checks; it need not prevent a separately available cost estimate.

### Mobilization (proposed representation, not an implemented adjustment)

Default is independent per-action mobilization and traffic allowances from each option. `mobilization_groups` may explicitly contain `{id, action_ids, allowance_usd, allocations_usd, evidence_ids, note}`: at least two distinct members, each action in at most one group, nonnegative two-decimal USD allowance/allocations, allocations keyed exactly by member IDs and summing to allowance. The fixed allowance applies to all sensitivity cases; no percentage saving is inferred. Evidence must justify common scope, price basis and the proposed allowance; the note identifies replaced mobilization lines. Traffic allowances are not shared by this field.

Future costing must replace only those mobilization lines, recalculate affected contingency through the single shared costing helper, and record `scenario-cost-v1`, original lines, replacements and source contents. A group may cost more, less or the same as separate mobilizations; no discount or setup-day reduction is automatic. Until that path is implemented, reject a nonempty group explicitly rather than silently ignoring it. Compatibility between shared activities and schedules requires human review; no optimizer is specified.

## ScenarioEvaluation (proposed M4)

| Field | Type / validation |
| --- | --- |
| scenario_id! | Scenario ID; snapshot retains exact scenario/action contract versions |
| evaluated_at! | UTC instant |
| baseline_source_hash! | canonical common original road/catalog/external-project/evidence contents before scenario overrides; excludes scenario-specific action/assumption inputs |
| input_snapshot! | canonical scenario/actions, resolved/missing quantities, schedules/calendars/closures, mobilization, original/overridden external projects, roads, evidence and per-action estimates |
| input_hash!, result_hash!, method_version! | timestamps/generated evaluation IDs excluded from semantic hashes; include all sources, parameters, adapter/cost/method/library versions |
| cost_total_usd? | Range in USD, null if any required action cost is unavailable |
| budget_usd! | money copied into immutable snapshot |
| budget_status! | within_budget / over_budget / indeterminate; central criterion only |
| upper_bound_within_budget? | bool, null if complete bounds unavailable |
| elapsed_days? | latest supplied end minus earliest supplied start; null if any required schedule date missing |
| lane_closure_days? | sum supplied closure interval days × declared lanes; null if incomplete |
| action_lifespan_years! | map action ID to sourced Range or null plus reason; currently all unknown, never sum years |
| conflict_screen! | hypothetical adapter result defined in ARCHITECTURE; retains finding context, complete M3 analysis and mapping to actions |
| indeterminate_checks! | missing quantities/methods/schedules/closures and M3 pair checks with reasons |
| utility_coverage! | remains unknown for current data, independent of finding count |
| review_required! | true for demo and unresolved safety/coverage assumptions |
| warnings! | typed codes/messages including synthetic and hypothetical status |

data_kind=derived. Unknown totals force budget_status=indeterminate. Comparison requires matching baseline_source_hash, horizon, currency, price basis, cost scope and method versions, while permitting explicit action/assumption differences. Evaluation is append-only; source changes produce a new immutable snapshot. Hypothetical findings live in the scenario snapshot, not the existing-project conflict history. Superseded flat `conflict_finding_ids` alone is insufficient to preserve hypothetical context; no current API used that draft field.

## EvidenceSource

| Field | Type / validation |
| --- | --- |
| id! | stable string |
| title!, publisher! | nonempty strings; synthetic sources name CivicPlAIn demo assumptions |
| source_kind! | enum public_dataset, manual_observation, demo_assumption, calculation_method |
| verification_status! | enum verified_accessible, candidate_unverified, synthetic_demo; matches DATA_SOURCES meanings |
| uri? | verified source URL or repository-relative fixture/method path; proposed inline assumptions may use scenario: URIs as defined above; no arbitrary remote fetching |
| retrieved_at?, observed_on? | UTC instant / civil date; synthetic assumptions need no invented observation date |
| version? | source release or method version if known |
| checksum_sha256? | 64 lowercase hex characters; required for imported local fixture/source payload and proposed canonical inline assumption content |
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
