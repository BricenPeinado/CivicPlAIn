# Data model and versioned contracts

Status: M2 implements synthetic RoadSegment maintenance attributes, related asset records, normalized ConditionAssessment history, a synthetic RepairOption catalog and immutable CostEstimate snapshots. M3 adds implemented WorkProject, ConflictFinding and immutable ConflictAnalysis records below. M4 implements the versioned scenario/action contracts below, editable revisions and immutable evaluations. Generic infrastructure assets remain unimplemented; M5 implements the bounded AI interaction and human-review audit records below. The concrete M2 shapes below supersede their former planning drafts. Existing M1 JSON remains unchanged in storage; enriched reads preserve its API shape.


## M7 official-data inspection contract (implemented in 7.1)

M0–M6 models below remain unchanged. Official facts use separate immutable sidecar tables and `municipal-record-v2`; no synthetic-only validator was relaxed. [M7_1_IMPLEMENTATION](M7_1_IMPLEMENTATION.md) records verified source mappings, commands and evidence. This concrete contract supersedes the M7.0 proposed DTOs.

| Classification | Meaning |
| --- | --- |
| `official_observation` | Published geographic feature or agency observation, with its original source/date; no independent survey-accuracy claim |
| `imported_administrative_record` | Permit status/effectiveness/expiration and other administrative facts; no actual-work assertion |
| `derived_calculation` | Explicit deterministic transformation/count/candidate computation retaining source inputs and method |
| `planning_assumption` | Explicit human hypothetical input, never silently inferred from source data; no new official calculation execution in 7.1 |
| `synthetic_fixture` | Authored test/example data; isolated automated fixtures and existing v1 records only |
| `unknown` | Null value with a reason; never a guessed coordinate, zero budget or retrieval-date inspection |

### MunicipalRecord

Pydantic `schemas/municipal.py` validates the common persisted shape: `contract_version`, namespaced `id`, `kind` (`road`, `condition`, `permit`, `context`), `source_revision_id`, string `source_record_key`, record `classification`, nullable GeoJSON `geometry`, nullable `[west,south,east,north]` bbox, `raw_identifiers`, `values`, `field_classifications`, `field_provenance`, `unknown_reasons`, `lineage`, `limitations`, `contains_synthetic`, `contains_assumptions`. Every `values` key has a classification and provenance entry; nulls require unknown reasons. Provenance retains source revision/record/field/original value/unit; geometry provenance distinguishes the derived LION coordinate transformation. Raw source geometry/allowlisted material fields remain in lineage. A record's origin does not override individual unknown fields.

Records are stored under a composite snapshot/kind/ID key; snapshot context is in the REST envelope rather than duplicated in every immutable payload. Raw field lineage plus `field_provenance` replaces the earlier proposed more deeply nested generic lineage DTO. Text/numbers retain source strings; decimal ratings are not float-rounded. Original inspection/permit floating datetimes are retained without inventing a timezone or converting to analytical half-open dates. V1 calendar semantics are unaffected.

| Kind | Current exact semantics |
| --- | --- |
| `road` | Manhattan LION regular street (`FeatureTyp='0'`, LBoro or RBoro=1), full MultiLineString transformed EPSG:2263 → 4326; regular nonzero valid line parts required. SegmentID **repeats** in the live service: source key is `SegmentID:OBJECTID`; preserve both and StreetCode as strings. OID is an export row identity, not durable segment identity across republishes. Width/area/cost/utility depth/schedule remain unknown. |
| `condition` | DOT `systemrating` decimal string, `inspection` floating timestamp, OFT, direction/type/non-rating reason. Source row ID (`:id AS source_row_id`) is the row key; content hash fallback for source-shaped adapter tests/exports without a row ID. Same OFT can have several observations/passes; never select a segment by OFT alone. No official category inferred: current dictionary has decimal-range gaps and a local-street exception with no usable local-street field. |
| `permit` | PermitNumber is documented primary key; OFT is an 18-digit location code if supplied. Issue/status/type/validity and modified timestamp are administrative fields. WKT and LocationGeometry retained raw; CRS is unspecified, so `geometry` and bbox stay null. No snapped coordinate, footprint, started-work status or confirmed dates created. |
| `context` | OTI shoreline lines, WGS84 GeoJSON; display context only. No closed shoreline polygons or inferred land/water fill. |

Read DTOs additionally expose `match`, `location_basis` (`source_geometry`, `matched_road_reference`, `unknown`), `scope_membership` (`confirmed_geometry`, `accepted_road_link`, `unverified_candidate`) and `same_oft_records`. Same-OFT relationships identify the documented DOT on/from/to location, **not** a particular LION roadbed, direction, conflict or actual construction project. Road summaries remain category unknown. Accepted linked condition history is available independently; `/conditions` also exposes unaccepted/unmatched observations.

### SourceRevision / DataSnapshot

Each source revision stores `id`, source ID/catalog/endpoint, canonical raw-record-set SHA-256, physical page checksums, exact query, source update marker, serialized/native CRS statement, cadence, attribution, schema fingerprint, dictionary URL/hash, license identifier (nullable), terms URLs/review version, source disclaimer, adapter version/release note, and first acquisition UTC timestamp. Live feeds have no immutable release number: checksums plus source metadata provide the version. ArcGIS editingInfo is not asserted to be the separately advertised LION ZIP edition. Full metadata, dictionaries and terms evidence are retained in ignored acquisition bundles. Portal terms HTML is hashed; city/DOT terms reviewed through official browser-readable pages return 403 to the downloader, recorded honestly without invented page hashes. No standard CC/public-domain license is inferred from null licenseId.

Source identity excludes retrieval timestamps and volatile portal-session HTML. It includes source rows/page checksums, query, update marker, reviewed schema/dictionary/terms profile, CRS and adapter. Snapshot identity hashes coverage, source revision IDs, counts, normalized record/match content, decision hash and PROJ/GEOS/pyproj/Shapely versions. It excludes publication/attempt/retrieval clocks. IDs use `nyc-` plus the first 32 hex characters of the full manifest SHA-256; the full unique hash is stored. Exact repeats reuse a snapshot; changed content/rules/reviews create another. Source retrieval time is retained from first publication; later successful new snapshots have import-run evidence. No automatically activated current snapshot exists.

The manifest includes coverage (pilot/context bbox, source readiness, exact bounded permit query/completeness limitations), capabilities, counts, source revision IDs, method/runtime versions, OFT groups and warnings. Original full geometry is retained; selection intersects rather than clips. All four layers must have valid records for this pilot release; failure/zero-row acquisition is not optional-layer success. Unknown utility coverage is independent of available permits.

### SQLite schema 7

Explicit migration marker: **7 / m7-official-snapshots-v1**, after existing 2–5; no fictitious schema 6. Existing 20 tables/JSON/saved calculations are untouched.

| Table | Concrete layout |
| --- | --- |
| `source_revisions` | id PK, source_id, raw_sha256, payload |
| `import_runs` | id PK, checked status (validated/rejected/published/failed), report_json; current CLI writes published audits only, including acquisition hash, rejects and refresh diff; dry-run/failure reports stay on disk |
| `data_snapshots` | id PK, study_area_id, full manifest_hash UNIQUE, manifest_json, published_at |
| `snapshot_sources` | snapshot_id/source_revision_id composite PK and FKs |
| `import_records` | snapshot_id/kind/id composite PK; source revision/key unique per snapshot/kind; west/south/east/north nullable; payload; composite FK to membership; snapshot/kind/bbox index |
| `geographic_matches` | snapshot_id/id PK, source kind/record and target kind/road composite FKs within same snapshot; target kind fixed road; status matched/ambiguous/unmatched; payload with candidates, metric CRS, tolerance, review evidence |

Source revisions, snapshots, membership, records and matches reject UPDATE/DELETE through triggers. Publication uses one transaction. Match candidates use UTM18N minimum separation ≤5 m for available geometry, or documented OFT's first 6-digit StreetCode as **candidate** street membership when unlocated; no nearest/unique candidate auto-acceptance. Explicit review binds the complete normalized record hash, reviewer, rationale and eligible road. Initial live import has no reviewed links. A reviewed street reference is not a permit footprint. See ARCHITECTURE for backup/recovery and API_SPEC for read semantics.

No official costing, conflict, scenario or AI execution is enabled; v1 replay/calculators stay synthetic. Derived presentation projections never reserialize saved v1 payloads.

## M8 extensions (implemented subset and future proposal)

M8.0 is documentation only. [M8_IMPLEMENTATION_PLAN](M8_IMPLEMENTATION_PLAN.md) sections 5–7 define the staged storage/transport/formula proposal; freeze exact DTO/DDL changes here before each implementation stage. Existing `municipal-record-v2`, schema-7 manifests/matches and all synthetic contracts below remain unchanged. M8 uses the same six field classifications; an authored assumption on an actual road is `planning_assumption`, not `synthetic_fixture` or an official observation.

| Proposed entity / contract | Required semantics |
| --- | --- |
| IntelligenceRelease / `road-intelligence-release-v1` (8.1) | One immutable base_snapshot_id, full manifest/content hash, exact source/target hashes, matching/parameter/runtime versions, decision/report hash, coverage counts and operational publication time. Pin explicitly; no automatic newest activation. |
| RoadAssociation / `road-association-v1` (8.1) | Source observation/permit and zero/one/many road-target rows; candidate/accepted/rejected state, scope/partial/direction evidence, competing candidates, method parameters and review. Accepted links bind complete source **and target** hashes plus base snapshot, candidate evidence, reviewer/rationale. Null target for no-candidate evidence. Review all accepted links initially; no name/nearest/unique-distance auto-acceptance. |
| ConditionPolicy / ConditionProjection (8.2) | Immutable source/release/date applicability, scale/thresholds, non-rating/pass/direction/coverage/latest-selection rules and policy basis. Projection retains accepted associations, chosen observations, raw values, category or explicit unknown/conflict, scope, method and input/result hashes. Policy-derived category never overwrites source `official_category`. Official-rule interpretation is derived; application-policy choices remain explicit assumptions. |
| RecencyProjection / `road-recency-v1` (8.2) | Explicit as_of_date, documented inspection-local civil date, age_days and policy thresholds/bucket/reasons. Future, missing or conflicting evidence cannot become current. Retrieval/release is separate; no deterioration model. |
| Permit coverage artifacts (8.3) | New base snapshots/overlays retain original administrative timestamps/revisions, exact bounded selection/exclusions, located vs road-reference vs unknown and scope membership. Many links count one permit once; utility coverage independent. No guessed WKT CRS or interval semantics. |
| PlanningAssumptionSet and RateCatalog (8.4) | Immutable content hashes, typed values/units/field paths and source references or explicit authored basis/note; method scope/applicability, inclusions/exclusions, currency/price date/geography, line/sensitivity/allowance/contingency provenance and review basis. No default rates, productivity or ranges. |
| MunicipalEstimate / `municipal-estimate-v1` (8.4) | Base snapshot/release/road, exact catalog/method/assumption set, explicit area/scope or reviewed rectangle, rounded cost lines/central cents, nullable sourced bounds/duration/lifespan, unknown reasons, full frozen inputs and hashes. Cost remains a planning estimate; method suitability requires separate evidence. |
| PrioritizationPolicy/Run / `maintenance-priority-v1` (8.5) | Explicit eligible road universe/as_of_date/condition policy, normalized typed components/weights, missingness behavior, contributions, tied ranks, unranked queue and sensitivity runs, coverage and full hashes. Score is a planning review policy, never observed safety risk. |
| WorkEvidence / `municipal-work-evidence-v1` (8.6) | Administrative-window, reviewed source-work or hypothetical kind; complete upstream field provenance, nullable geometry/road references/dates/closures/excavation, original temporal convention plus separately reviewed analytical mapping. Permit presence cannot manufacture verified work. |
| MunicipalScenario/Action/Evaluation (8.6) | Separate `municipal-scenario-v1`/action contract, optimistic draft revision/hash, immutable evaluation with complete base/release/catalog/policy/assumption/work snapshots, comparisons only under compatible bases. Missing required costs yield null complete totals/indeterminate budget; known subtotal separate. Hypothetical proposals never mutate import/project rows. |
| MunicipalEvidence / `municipal-ai-evidence-v1` (8.7) | Typed bounded fact projection with all six classifications, source/release/association/policy/calculation hashes, unknowns and integrity/replay status. Separate official interactions and human review notes; no raw narrative, contacts, geometry or provider-written facts. |

First additive version (implemented in M8.1): 8 / `m8-road-intelligence-v1`, only `intelligence_releases` and `road_associations` families. Later versions add only the delivered stage's required condition, planning, priority, scenario and evidence families. New composite keys/FKs enforce base-snapshot/release/source/target membership; new derived records are append-only, drafts alone mutable. No table/payload rewrite, reseed, synthetic-ID mapping or schema-7 match replacement. Complete old row/schema/trigger preservation, verified WAL-aware backup and prior-software recovery are mandatory. M8.1 now implements the two schema-8 families as detailed below; later families remain proposed.

All new deterministic snapshots retain complete inputs and field-level lineage, units, original values/dates, explicit as_of_date, policy/catalog/parameter/decision hashes and relevant runtime/method versions. Canonical set-like ordering and timestamp exclusions follow M8 plan section 7; observations/price/as-of dates remain semantic inputs. Calculated centerline length never silently becomes repair area. Missing required data is null plus reason, not zero or fixture fallback. Existing v1 versions and semantic hashes must remain identical under any shared-helper extraction.

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

## Scenario (implemented M4; contract `scenario-v1`)

M4 implements these nested contracts in schemas/scenarios.py and the existing SQLite monolith. The implementation clarifications below supersede M3.5 future-tense wording where they differ. M1–M3 contracts and existing immutable fixtures remain unchanged.

A scenario has system-generated RecordMeta (`data_kind=derived`, transitive synthetic flag), `contract_version=scenario-v1`, nonblank `name` (1–200 chars), `dataset_snapshot_id`, nonnegative two-decimal `budget_usd`, `currency=USD`, `planning_start` and `planning_end` (start < end), `cost_scope=roadwork_only`, optional `cost_scope_note` (1–2000 chars), and 0–50 `actions` (zero is an incomplete draft, never a zero-cost feasible plan). The horizon is half-open in America/New_York. `review_note` is optional text (1–2000 chars), never an approval. Comparisons require the same horizon, currency, cost scope, baseline_source_hash, price basis and method versions, not just matching display labels or dataset ID. baseline_source_hash covers the common original roads, catalog, selected external projects (before overrides) and their evidence. Scenario-specific action assumptions, quantities, dates and overrides may differ and remain visible; they are not required to hash identically across alternatives.

Scenario-level `assumptions` is a list of `{id, note, field_paths}`: distinct IDs (1–100 chars), nonblank notes (1–2000 chars), and nonempty material field paths. These are explicitly authored planning assumptions, not measurements. The service generates complete inline synthetic EvidenceSource records with stable namespaced IDs, version, limitations, canonical content checksum and source URI `scenario:<scenario-id>:assumption:<id>`. Hash content before adding its checksum to avoid circular hashing. These records stay inside the immutable scenario/evaluation snapshot, not in the M1 evidence table. Request provenance may use `assumption:<local-id>` references to that list; the service resolves these aliases to namespaced snapshot source IDs. Existing sources resolve by ID; callers cannot overwrite their contents. General observed-source adapters remain unimplemented.

`external_project_ids` explicitly selects existing projects. `project_overrides` is a list of `{project_id, operation: exclude|replace, replacement_action_ids, reason, evidence_ids}`. IDs must resolve in the same snapshot. Exclude requires an empty replacement list; replace requires at least one distinct existing action ID. Each project has at most one operation. Related-project references alone never exclude anything. The saved snapshot retains originals, selected scope, overrides and reasons. `mobilization_groups` defaults to an empty list; its proposed contract is below.

### ScenarioAction (implemented `scenario-action-v1`)

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

Validated fixed classification fields identify `hypothetical=true`, `data_kind=derived` and transitive `synthetic_input`; only these literals are accepted; callers cannot claim observed work. Every proposal in the current synthetic demonstration has `synthetic_input=true`. Null scope geometry requires location_status=unknown; non-null proposal geometry requires approximate. Scope geometry must pass M3 longitude/latitude, topology and study-bound checks; a road centerline can be an explicitly labeled corridor reference, never a measured pavement or trench footprint. Unknown geometry stays null. No buffer infers utility width, depth or location. Category `temporary_patch` requires action_kind `temporary_patch`; `trench_restoration` requires scope extent `utility_trench`. Whole-segment/partial-area resurfacing is not automatically an appropriate utility-restoration method.

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

A future shared-cost extension must replace only those mobilization lines, recalculate affected contingency through the single shared costing helper, and record `scenario-cost-v1`, original lines, replacements and source contents. A group may cost more, less or the same as separate mobilizations; no discount or setup-day reduction is automatic. Until that path is implemented, reject a nonempty group explicitly rather than silently ignoring it. Compatibility between shared activities and schedules requires human review; no optimizer is specified.

## ScenarioEvaluation (implemented M4)

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

## General AuditEvent contract (future cross-module stream)

M5 implements the scoped AI interaction metadata and separate human review event shapes documented below. It does not create this generalized table or retrofit imports/calculations with events.

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

M3 now implements WorkProject and conflict snapshots as specified above. Generic assets and audit-event/review-note workflows remain unimplemented; M4 scenario persistence is described below. M2 estimates and original stored road payloads are preserved.

## M4 persistence and implementation clarifications

`Scenario` additionally has a server-generated stable UUID, description, planning_objective, status draft/ready/archived, created_at/updated_at, positive integer revision, canonical revision_hash, method_version, data_kind=derived, synthetic_input=true and hypothetical=true. Status is an author organization label, not validation or approval. Draft edits increment the revision; evaluation freezes the exact revision/hash and the complete draft/source contents. The initial M3.5 wording that edits create a new Scenario ID is superseded by explicit user-authorized editing; evaluation history never changes. Canonical set-like lists are sorted; geometry coordinate order remains untouched.

Schema migration 4 (`m4-additive-v1`) adds scenarios, scenario_actions (composite scenario/action ID, road/catalog FKs), scenario_projects (project FKs), and scenario_evaluations (scenario FK, revision, full frozen payload). Evaluation UPDATE/DELETE triggers reject writes. Existing M1 JSON, M2 estimates and M3 projects/analyses/findings are not rewritten. Storage is local SQLite, not tamper-proof auditing. References are resolved before saving; unknown IDs return 404 and incompatible snapshots 409. Updates are serialized with BEGIN IMMEDIATE and checked against expected_revision; evaluation persistence rechecks the revision after calculation.

`ScenarioEvidence` is the typed per-field provenance shape above. The path in input_provenance identifies the relevant field, source_record names the exact upstream record/field, and frozen Evidence contents retain classification, version, checksum, coverage and limitations. Inline synthetic assumptions have namespaced IDs, scenario URIs and content hashes; source_aliases resolves the request's assumption references. No remote source is fetched. Current observed municipal adapters are explicitly unsupported. Source-record field/value/evidence must match, and unrelated records cannot supply provenance. Explicit quantities require exact-source or authored planning-assumption provenance.

Cost assembly uses the factored M2 cost_scenarios helper with Decimal/ROUND_HALF_UP. Each ActionCost freezes the action, road, assessment, option, sources, resolved quantity/provenance, line items, contingency, low/base/high totals, preliminary duration, M2 suitability result, warnings and scenario-cost-v1. No second pricing formula exists. Costs aggregate independently rounded action totals; contingency is not added a second time. Same-road work requires disjoint explicit footprints or justified repeat work with distinct dates; changing an ID, description or method alone cannot charge the same scope twice. No per-action rate/contingency override is supported; extra fields and nonempty mobilization_groups are rejected explicitly.

ScenarioEvaluation adds stable content-addressed id, scenario_revision/hash, evaluated_at, analysis_versions, action_costs, known_subtotal_usd, nullable complete cost_total_usd, budget_headroom_usd (low/base/high), preliminary_days_sum, scheduled_road_workdays, overlapping_closure_pairs, affected_road_ids and immutable input/result hashes. Each budget headroom is budget minus the corresponding cost; base equality is within_budget. Any required unavailable cost or empty action set forces indeterminate and null complete totals/headroom. Known subtotal is explicitly partial, never the total. All current action lifespans are null with an explicit unknown warning.

Scheduled road-workdays sum supplied calendar envelope days per action (not contractor working days); elapsed_days is the earliest-start/latest-end span. Lane-closure-days sum explicit closure intervals × lanes. Cross-action overlaps can double count and are labeled. overlapping_closure_pairs counts positive-lane interval pairs on the same road, not vehicle delay. Unknown dates/closures yield null metrics and incomplete checks even for a single action; no closure, schedule or utility clearance is inferred from an estimate. Work calendars are recorded only. Constraints validate dates/acyclic precedence; missing required dates leave satisfaction indeterminate.

`ScenarioComparison` is a reproducible comparison snapshot with input_hash and method scenario-comparison-v1, involved evaluation IDs, common_basis, rows, deltas, dominance, deterministic tradeoffs and warnings. Compare 2–3 distinct saved evaluations; source/horizon/currency/price/cost-method/parameter incompatibility returns 409. Road, category, quantity and footprint scope differences are disclosed; cost deltas with differing service are not equivalent-service savings. Different authored assumptions are disclosed. Conservative Pareto dominance requires matching service scope, assumptions and budgets plus complete objective inputs/checks. It minimizes only the disclosed numeric objectives; it never implies safety, utility completeness or approval. Missing costs have null deltas. No weighted winner is selected.

## Implemented M5 evidence, explanations and audit

`schemas/ai.py` is the strict Pydantic boundary (extra fields forbidden; nonfinite values rejected). `Context` has type road/assessment/estimate/conflict/project/evaluation/comparison and 1 record ID, or 2–3 distinct evaluation IDs for comparison. IDs are stripped/nonblank and bounded to 150 characters. The server constructs evidence; clients cannot submit authoritative amounts, source snapshots or evidence objects.

`EvidencePackage` (`ai-evidence-v1`) has canonical context, records, facts, missing_information, limitations, truncated, omitted_fact_count and snapshot_hash. Each `EvidenceRecord` contains evidence_id, entity_type, record_id, canonical record_hash, nullable input_hash/calculation_version/dataset_snapshot_id, source_revisions (source ID → canonical complete-source hash), synthetic_input and data_kind. A comparison record has no dataset ID of its own; common basis is verified through its saved evaluations. Facts contain fact_id, evidence_id, source field path, fixed label, typed scalar/null value, unit and classification. Scenario labels identify the source scenario reference/revision. Record hashes cover complete originals; persisted projections contain no raw source narratives or geometry.

Package hashing uses the existing sorted-key compact ASCII JSON helper over the package excluding snapshot_hash. Context reference sets and fact/evidence membership must match. Stable projection limits are 96 facts and 48,000 canonical bytes before the hash field; missing-field warnings survive truncation. Oversized metadata cannot be silently truncated. Estimate/analysis/evaluation snapshots retain their original versions and are independently replay-checked; comparison requires compatible M4 bases. Synthetic dimensions, prices and schedules never become observed facts.

`ProviderSelection` contains only the exact evidence hash, bounded_summary, 1–12 `{fact_id,evidence_id,template_id:fact_value}` selections, mandatory limitation codes and a context-compatible review code. Unsupported amounts, dates, units, free prose, extra fields or approval codes are rejected. The public `Explanation` contains explanation_id, task_type, evidence_snapshot_hash, summary, key_findings (finding_id, claim_text, supporting_evidence_ids, fact_refs, classification), tradeoffs, uncertainties, missing_information, suggested_review_actions, citations, evidence, provider_status (deterministic/openai/fallback), validation_status (validated/fallback_validated/insufficient_evidence), nullable fallback_reason/model_label, generated_at, source_classification (synthetic/observed/mixed), human_review_required=true, warnings and audit_reference. Record fact means verified against the supplied record, not field verification. No LLM values or prose become record facts.

Migration `m5-additive-v1` adds `ai_evidence(hash PRIMARY KEY,payload)`, `ai_interactions(id PRIMARY KEY,evidence_hash REFERENCES ai_evidence(hash),payload)` and `review_events(id PRIMARY KEY,evaluation_id REFERENCES scenario_evaluations(id),payload)`. All have UPDATE/DELETE rejection triggers. Projections deduplicate by evidence hash; each request has a separate interaction ID. Metadata stores source references, task/context type, evidence hash, provider/model when attempted, mode, validation/error category, UTC timestamp, request correlation, contract version and output hash. No raw question, prompt, generated prose, secrets, hidden reasoning, personal contacts or utility geometry are saved in these AI records. Explicit human aliases/notes are stored only in review_events with action=review_note and authorizes_work=false. The API never treats them as an approval.

These are local application controls, not tamper-proof records or a production retention policy. Existing calculation snapshots are not updated or deleted by explanation/audit operations.

## M7.3 aggregate extension (implemented)

No schema migration, record rewrite or new calculation model. The read-only dashboard derivation is now municipal-summary-2: exact nullable raw permit-status buckets, known permit issue-date range and per-source frozen retrieval/update/cadence/release metadata supplement the existing snapshot-wide counts and denominators. These are derived summaries/source metadata, not observations of work started, current pavement categories or confirmed coordination findings. Exact transport fields are in [API_SPEC](API_SPEC.md). Existing saved estimate/analysis/scenario/evaluation identities and replay versions remain unchanged.

## M8.1 concrete overlay and condition semantics

`schemas/road_intelligence.py` defines strict `AssociationReview`, `ConditionHistory` and `ConditionSummary` boundaries. The implemented schema 8 contains `intelligence_releases(id,base_snapshot_id,manifest_hash,manifest_json,published_at)` and `road_associations(release_id,id,base_snapshot_id,source_kind,source_record_id,target_kind,target_road_id,status,payload)`. Release/base composite membership and base/source/target composite FKs preserve snapshot isolation. Immutable triggers reject UPDATE/DELETE. Source kind is condition; target kind road; accepted/candidate/rejected require a target, unmatched forbids one. Unique release/source/target prevents duplicate pair decisions; multiple targets remain separate rows.

A review binds base snapshot, full source/target content hashes, candidate/parameter hashes, accepted/rejected status, whole_road/partial scope with rationale, reviewer label, reason and evidence references. Local annotations are not verified municipal endorsement. Canonical release identity freezes sorted association content, sorted reviews, original source/base content hashes, parameters and GIS runtime versions. Operational publication time is excluded. Source and schema-7 match payloads are never rewritten.

`road-condition-v1` is an unpersisted derived projection over the selected immutable context. Exact raw rating/date/source references remain observation evidence. Latest selection requires accepted v2 whole-road scope, known direction/road type, explicit non-multipass source flag, no non-rating reason, interpretable source-floating date at/before explicit as-of date and rating 1–10. Reported zero remains in history with unresolved-validity reason because published definitions disagree. Multiple eligible streams, conflicting equal-time ratings, partial/missing evidence yield null current rating with reasons. No averaging, integer rounding or PCI conversion. Category is always unknown until applicability review resolves the source gate.

Age uses source calendar date; stale is strictly age > supplied integer threshold, nullable when unavailable. UI initial 365 days is `planning_assumption`; reference defaults to snapshot publication only as a comparison date. Input hash includes method/base/release/road/date/threshold and full accepted record/association hashes; result hash covers the derived response. Complete accepted history retains eligibility, original rating/date/pass/non-rating/direction/type, source ID and source/association hashes. No wall clock, inferred schedule or AI value enters this projection. See [M8_1_IMPLEMENTATION](M8_1_IMPLEMENTATION.md) for limitations and acceptance status.


### M8.1 approved pilot projection extension

[Owner-approved pilot](M8_1_PILOT_IMPLEMENTATION.md) adds optional `AssociationReview.candidate_set_hash` (64 lowercase hex), validated against the complete canonical candidate list; older absent values preserve existing release identity. Every new owner review supplies it. Complete source/target/base/candidate/parameter references and review/scope remain required. No schema-7 payload changes.

`road-condition-v2-pilot` is selected only with explicit `policy_id=civicplain-pilot-pavement-v1.0`, its approved base snapshot and an explicit compatible intelligence release/date. It preserves v1 eligibility except the approved valid numerical interval is 0 < rating ≤ 10. The owner policy is `planning_assumption`; calculated grades/rounded scores are `derived_calculation`, never source categories. Policy identity/hash and semantic inputs bind replay. Default no-policy v1 above remains unchanged.

`ConditionSummary` adds optional `rounded_rating` and `policy` (ID/name/version/hash, approval scope, classification, official_nyc_dot_policy=false, rounding/categories/limitations/evidence reference); category is good/fair/poor/unknown, with nullable category_reason. Eligible selected raw rating/date/source stay source evidence; unsupported current rating/category fields retain unknown classification. Each accepted `ConditionHistory` may add typed `grading` (raw_rating unchanged, rounded_rating, category, reason, non_rating_reason, policy_id/version/hash, derived_calculation, policy_classification=planning_assumption, official_nyc_dot_policy=false) and complete `association_review`. A history observation grade cannot populate an ineligible road summary. For these five partial links all road-level rating/date/recency remain null.

Road list and GeoJSON may include the same optional `condition_summary`, computed server-side before category filtering from all accepted context history. No missing/unaccepted observation is promoted and no different direction/pass is averaged. No official_category or source record is overwritten.

## M8.2 permit reference evidence (current owner-authorized scope)

See [M8_2_IMPLEMENTATION](M8_2_IMPLEMENTATION.md). Additive schema 9 (`m8-permit-intelligence-v1`) adds immutable `permit_associations` with the schema-8 association shape, `source_kind=permit`, base/release/source/target FKs and immutable triggers. `intelligence_releases` distinguishes `permit-intelligence-v1` from condition contracts; no historical CHECK, table, import payload or v1 fixture changes. No official WorkProject is created.

Derived `permit-road-reference-v1` projection adds optional `permit_location`: explicit base/release, five statuses (`located`, `candidate`, `unlocated`, `outside_coverage`, `invalid_evidence`), accepted partial road references/reviewer rationale, active candidates, rejected associations, reasons, parameter/result hashes, `actual_schedule=unknown`, `classification=derived_calculation`. The candidate-set hash binds all original alternatives, including rejected rows; active candidate lists exclude explicit rejections. Located requires hash-bound review; unique name/OFT/proximity candidates never auto-accept. Outside coverage requires verified geometry; missing name agreement is not outside evidence. Raw WKT without verified CRS stays uninterpreted.

`issued_at`, `valid_from`, `valid_to`, source status and modified date remain administrative. Work-start/confirmed dates/utility locations remain null/Unknown. New explicit acquisition window coverage has `issued_on_or_after:null` plus `administrative_window {start,end,cap,method,limitations}`; legacy coverage unchanged. Borough acquisition is not confirmed geographic membership or an active-work census.

Ephemeral `permit-coordination-v1` findings contain two record IDs/hashes, location hashes, base/release/parameter hash, shared road references, candidate-vs-accepted basis, `possible_overlap|unknown` administrative-window relation, same-application flag, `confirmed_conflict:false`, actual work overlap/utility coverage Unknown. Inclusive administrative endpoints express uncertainty, never verified concurrency. Results are deterministic reads, not persisted conflict analyses or project schedules.

## M8.3 repair planning contract (owner-authorized scope)

`municipal-estimate-v1` / `municipal-area-cost-v1` is separate from synthetic M2/M4 schemas. Request pins an official base snapshot and exact LION export road row, with 1–2 uniquely named alternatives (`patch`, `resurface`); reconstruction remains unsupported. Each alternative explicitly describes extent/inclusions/exclusions, area (m2/yd2/ft2) or a rectangle (m/ft), USD area rate and price date/geography, mobilization and traffic-control disposition (priced/included/excluded/unknown), contingency fraction and optional ordered low/high rates and productivity/setup/curing inputs. No numeric default. Each numeric input carries value/unit, author/date/note and optional human-supplied citations; these are `planning_assumption`, never auto-verified source observations. Source URLs are metadata only, never fetched. Published agency method guidance supplies treatment descriptions, not loaded prices or suitability.

Positive finite bounded quantities, consistent units, explicit zero assumptions, unique allowances and non-overlapping bundled cost declarations are validated. Incomplete preview returns unavailable with field reasons; save rejects incomplete alternatives. Absent rate bounds/duration remain null. Costs use Decimal, per-line cents ROUND_HALF_UP, sum rounded lines then round contingency; sensitivity changes only explicit area rates. Exact conversion constants are versioned; no thickness/density/tonnage, centerline-to-area, lifespan, savings or schedule inference. Frozen results include raw request/road/source/base, derived quantity, all cost cases, assumptions/unknowns, versions and full hashes. Additive explicit schema 10 stores immutable `municipal_estimates` with base/road membership FKs; no v1/schema-7/8/9 rewrites or automatic migration. Navigation/GET never creates an estimate.


## M8.4 implemented priority contract

`maintenance-priority-v1` inputs pin 1–100 unique exact road-row IDs, base snapshot, strict as-of civil date, optional explicit condition/permit intelligence releases, one attributed policy and up to three complete sensitivity policies for the same objective. Policy includes id/version, `planning_assumption` author/date/rationale, three nonnegative Decimal-string weights summing exactly to one, explicit day horizon/maximum condition age and stale exclusion/qualified-use rule. No submitted observations, traffic counts or scores are accepted. Need normalization `(10 - eligible raw rating)/9` is application policy, not official category. Inspection age is bounded age/horizon. Evidence-gap 1/0 describes absent/present eligible official road-wide evidence only. Maintenance forbids a positive evidence-gap weight; inspection forbids condition-need weight. Missing enabled factors produce null score/rank with reasons; no redistribution. Equal exact scores share competition rank; stable road ID sorts display only.

Optional explicit M8.3 estimate ID/treatment choices retain complete frozen estimate/source/assumption scope; no latest/cheapest fallback. A human-evidenced per-declared-scope USD ceiling can exclude over-ceiling records or leave missing costs unranked. It is not a portfolio budget. Functional class, traffic/disruption and verified coordination stay unavailable, separately from administrative accepted-reference counts. Source/inspection dates, factors/contributions, completeness, need, cost, scheduling unknowns, human review, base/sensitivity ranks/hashes remain distinct. Additive explicit schema 11 `m8-prioritization-v1` stores immutable `prioritization_runs` with snapshot FK, unique full input hash, JSON inputs/result, result hash, timestamp and update/delete rejection triggers. No old snapshot/fixture/DTO or v1 payload changes. See [M8_4_IMPLEMENTATION](M8_4_IMPLEMENTATION.md).

## M8.5 official-context construction screening

`official-screen-v1` is a source-neutral deterministic contract, separate from synthetic `WorkProject` and v1 scenarios. It pins one official base, up to 30 supplied work declarations and 30 distinct selected/linked administrative permits, exact optional permit intelligence release, explicit metre proximity (0–100), integer rework horizon (0–365 days) and attributed policy evidence. No numerical defaults. Supplied work independently declares its work type, referenced road/permit IDs, optional EPSG:4326 geometry, certainty, optional half-open civil-date work/closure intervals, grade, excavation requirement/depth and field provenance. Missing values remain unknown. `planning_assumption` remains an assumption; `supplied_document` is a local evidence-basis discriminator for an attributed independently unverified citation/declaration, never an imported official observation or reviewed match. It does not add a seventh municipal field classification or change source record classifications; the submitted assertion remains unverified planning input. Populated grade/excavation/depth requires separate provenance. Supplied documents require citations. Closure intervals must lie within the work envelope. No source administrative date or WKT supplies these fields.

The adapter preserves exact official source/record/release/accepted-or-candidate lineage. Permit entries always have null work geometry and schedule, even with accepted road references. All road candidates remain visible; work declaration/road geometry disagreement is indeterminate. The full pinned road universe is frozen to reproduce candidate detection (not just selected matches). All pairs in the bounded selected universe are checked, including unlocated entries; road references alone never establish work overlap. Results separate supported relations of supplied plans, potential coordination opportunities, indeterminate checks and incomplete coverage. Any supported finding is explicitly `supplied_evidence_only_not_independently_verified`; it is not actual physical interference.

Up to three named alternative schedule/closure overrides freeze/replay on identical work/permit scopes. Optional cost comparison uses one explicitly selected replayable M8.3 estimate on the declared work road/treatment and the same frozen scope/quantity in every schedule, plus independently attributed nonnegative USD additions and explicit scope/nonoverlap declaration. Differences reflect those additions only; no finding-derived losses/savings. Missing cost inputs return unavailable. Actual expenditures, bids and complete project costs are not inferred.

Additive explicit schema 12 stores immutable `official_screenings` (base FK, unique input hash, result hash, full frozen payload/time) and separate append-only `official_screening_notes` (screening FK, note content hash identity). Review notes reference a saved run/optional finding and carry author, text, disposition and timestamp; they do not alter calculations or authorize work. Method/GIS library versions, base/source checksums, raw administrative dates, projections, assumptions, alternatives, cost basis and complete hashes persist for offline replay. No changes to historical official snapshots, v1 DTOs or saved synthetic inputs.

## M8.6 presentation and explanation projections

`decision-context-v1` is a read-only aggregate of one explicit base/as-of/optional condition-release/policy context and independent histories. Condition counts reuse whole-road eligibility; observation grades never become whole-road category coverage. `requiring_review` means no eligible current road assessment, not observed physical failure. Saved-run counts count calculations, not unique roads/projects/work. Missing schema yields unknown/null history count. Histories are bounded to 100 with explicit truncation and existing paged tool histories.

No new table/migration. Existing schemas 10/11/12 freeze estimates/priorities/screenings; existing schema 5 AI evidence/audit storage receives only explicit explanations. `official-scalar-projection-v1` reuses `ai-evidence-v1`, with derived non-synthetic EvidenceRecords, exact base, frozen-input/result/method hashes and hashed projection identity. Only allowlisted result scalars enter Fact fields; labels are application constants. Null sensitivity/duration/utility information stays null with mandatory caveats. The explanation adds `derived` to the response source-classification enum without relabeling existing synthetic records. Explanations never mutate government source records, reviewed associations or calculations. Source citations/assumptions remain in the selected frozen record; source prose and human review text are excluded from model input.

Official comparisons currently present alternatives **within** an M8.3/M8.4/M8.5 result: independent treatment scopes/rate sensitivity, same-universe policy sensitivity, same-work schedule alternatives and qualified same-scope costs. No cross-estimate addition, cross-run score comparison, budget optimization, municipal scenario CRUD or general evaluation is implied. Route pinning is saved selection context, not new analysis persistence. See [M8.6](M8_6_IMPLEMENTATION.md).

## Standardized named-street presentation (2026-11-08)

The owner-supplied `data/processed/CivicPlAIn_standardized.sqlite3` is a separate derived read model, opened with SQLite `mode=ro` and `query_only`. Its `metadata.source_snapshot` must equal the selected official snapshot. It is neither an activated official snapshot nor a replacement planning database. No ingestion, matching, migration, source rewrite or automatic refresh is performed. [Supplied dataset semantics](README_CivicPlAIn_standardized.md) define its existing records and views.

`road_profiles.road_id` is the exact existing LION row identity. Geometry is that selected segment; `latest_rating`, `latest_inspection_at`, `display_condition`, observation count and permit count are shared **named-street** evidence. Application indicative bins (1–<4 Poor, 4–<8 Fair, 8–10 Good) are derived calculations, not NYC DOT categories or segment measurements. The stored latest numeric selection excludes non-rating reasons and uses the artifact's existing date/ID rule; API reads do not recalculate it. Null remains unknown and source zero/non-rating observations remain inspectable without becoming primary usable ratings.

`road_pavement_by_name` and `road_permits_by_name` are always filtered by exact road_id. Permit association requires the normalized **on-street** key; cross-street mentions do not assert work on that street. Distinct permit IDs remain distinct administrative records even when descriptions/dates coincide. Issue/validity dates never establish actual schedules. Original observation IDs, dates, ratings, geometry, source row keys/non-rating reasons and source revision references are retained; complete source checksums/lineage remain in the unchanged official APIs. Read-model associations never enter `road_conditions`, suitability, maintenance prioritization, screening, AI evidence or saved calculations. Original snapshot and reviewed-release verification remain separately available.

### M9 indicative map projection

The bulk map projection reuses the standardized Profile contract and its original numerical rating, category, date, counts, display basis and road source ID. Stable LION geometry locates the reference road only. A named-street observation may be shared by many segments; the line color never verifies any selected segment's condition. Null rating and Unclassified render Unknown/neutral while source values remain unchanged. No category thresholds, rounding, estimated measurements or road-wide evidence are created. This presentation-only projection and its cache are excluded from saved estimates, suitability, priorities, screenings, AI and planning evidence. Existing six field classifications, raw lineage, historical snapshots and M8 acceptance gates remain authoritative.

## M10 presentation-only planning drafts

M10 forms and drawn LineStrings map to the unchanged official-screen-v1 WorkInput/Location/Schedule/Basis/Alternative contracts. Coordinates are EPSG:4326; drawing commits approximate certainty and planning_assumption provenance. Shared author/date/rationale is explicitly inherited unless overridden per work. Geometry certainty declared remains a user declaration, not an official observation. Unknown excavation maps to null with no evidence basis, explicit Yes/No to boolean with attributed basis. No road centerline, indicative rating or administrative permit date populates these work declarations. Existing field classifications, lineage, saved snapshots and method/version semantics remain unchanged. Up to two works/two alternatives is a simplified editor limit, not a reduced API limit. Drafts/drawing are snapshot-scoped session memory; saved results keep their original immutable identities. [Implementation](M10_IMPLEMENTATION.md).
