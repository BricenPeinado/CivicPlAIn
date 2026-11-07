# Preliminary data model

Status: M1 implements RecordMeta/RoadSegment and EvidenceSource for synthetic fixtures, plus the limited condition_summary projection below. Other entities remain proposed. API_SPEC uses these shapes. M1 stores validated JSON in SQLite using sqlite3; normalization of assessments/assets/projects belongs to M2.

## Shared conventions

`!` means required and non-null; `?` means optional/nullable. Collections marked `!` must be present (empty allowed unless specified). IDs are stable opaque strings, unique by entity; demo IDs use `demo-` prefixes. Foreign keys must resolve in the same dataset snapshot. Dates are ISO `YYYY-MM-DD`; work intervals are `[start_date, end_date)` local to America/New_York. Instants are RFC3339 UTC. Money is a nonnegative two-decimal USD string over REST, integer cents in storage. Finite decimal quantities/rates use decimal strings; counts are integers.

All domain entities below except EvidenceSource and AuditEvent include this **RecordMeta**:

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
| coverage_as_of? | date; mandatory for verified_for_scope |

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

## ConditionAssessment

| Field | Type / validation |
| --- | --- |
| road_segment_id! | RoadSegment ID |
| asset_id? | InfrastructureAsset ID associated with the same segment |
| assessed_on? | date; null for undated evidence, which cannot be called current |
| rating? | finite decimal within rating_scale; null for missing assessment |
| rating_scale! | object: name, min, max, direction (`higher_better` or `lower_better`); min < max |
| condition_label? | string; source-specific categorization, no unsupported normalization |
| safety_note? | string; sourced observation or explicit demo assumption, never certification |
| assessment_method! | string; e.g. published survey or synthetic fixture |

Rating and assessed_on carry field evidence. Latest usable assessment is max assessed_on, tie-break by stable ID ascending; undated records remain visible but do not supersede dated ones. Freshness threshold is TBD with a recommendation to show age without asserting current safety.

## WorkProject

| Field | Type / validation |
| --- | --- |
| title! | nonempty string |
| kind! | enum road_repair, utility, other |
| road_segment_ids! | list of RoadSegment IDs; may be empty for unmatched permits |
| geometry? | GeoJSON LineString or Polygon, actual or explicitly assumed work footprint |
| start_date?, end_date? | dates; when both known, start < end |
| schedule_status! | enum planned, tentative, completed, cancelled, unknown |
| schedule_basis! | enum confirmed_source, permit_window, assumed_demo, unknown |
| lanes_closed? | nonnegative integer; if segment lane count known, cannot exceed it without documented multi-segment scope |
| review_status! | enum unreviewed, reviewed_with_notes; neither means approved |

Relationships: one optional UtilityWork subtype; scenarios reference source projects but propose their own action dates. Unknown geometry/dates allow storage but produce indeterminate checks. Permit validity is not a confirmed actual construction schedule. Cancelled projects are excluded with an explicit reason; completed historical work is considered only for relevant reopening comparisons.

## UtilityWork

| Field | Type / validation |
| --- | --- |
| work_project_id! | unique WorkProject ID with kind=utility |
| utility_type! | enum water, sewer, gas, electric, telecom, unknown |
| infrastructure_asset_ids! | list of InfrastructureAsset IDs, empty if unmapped |
| permit_reference? | string; source-specific, no fabricated official identifier |
| excavation_required? | bool; null means not established |
| location_confidence! | enum source_reported, assumed_demo, unknown; not numeric probability |
| scope_note? | string explaining what is and is not known |

Schedule/geometry live on WorkProject to prevent contradictory copies. A permit may imply potential utility work only with supporting classification evidence. No sensitive underground route data is required for MVP.

## RepairOption

| Field | Type / validation |
| --- | --- |
| label! | nonempty string |
| treatment! | enum patch, resurface, reconstruct, restoration |
| quantity_unit! | enum m2, m; compatible with chosen rate |
| unit_rate_usd! | decimal ≥0 per quantity_unit; assumed unless supported by a reviewed price source |
| mobilization_usd! | money |
| contingency_fraction! | decimal in [0,1]; explicit assumption |
| productivity_per_day? | decimal >0 in quantity_unit/day |
| setup_days! | integer ≥0 |
| assumed_duration_days? | integer >0; alternative to productivity-derived duration |
| lifespan_years? | Range in years |
| price_basis_date! | date; required even for a synthetic assumption |
| cost_scope! | nonempty string describing inclusions/exclusions |

At least productivity or assumed duration is required. If both exist, request must select a duration method explicitly. Applicability to real pavement requires engineering review; fixture options do not establish fitness.

## CostEstimate

| Field | Type / validation |
| --- | --- |
| road_segment_id!, repair_option_id! | corresponding entity IDs |
| quantity! | positive decimal with unit matching option |
| line_items! | nonempty list: label, quantity decimal, unit, unit_rate_usd decimal, amount_usd money, evidence_ids; amount obeys rounding contract |
| subtotal_usd!, contingency_usd! | money, derived exactly from items and option |
| total_usd! | Range in USD, values formatted as money; central=subtotal+contingency |
| duration_days! | integer >0, calendar days |
| duration_method! | enum assumed, productivity |
| lifespan_years? | Range in years; inherited assumption with evidence |
| cost_scope! | string, inherited or explicitly narrowed |
| method_version!, input_hash! | nonempty strings |

data_kind=derived. Quantity/duration overrides require evidence. No persisted CostEstimate is created for missing mandatory inputs; return 422 field errors. Scenario evaluation may report missing estimates as indeterminate. Uncertainty bounds need explicit multipliers or item ranges, saved in evidence; do not manufacture confidence.

## ConflictFinding

| Field | Type / validation |
| --- | --- |
| project_ids! | exactly two distinct WorkProject IDs, canonically sorted |
| finding_type! | enum concurrent_work, reopening_risk |
| spatial_distance_m! | decimal ≥0, from projected geometry |
| proximity_m! | decimal ≥0, rule input |
| overlap_start?, overlap_end? | dates; required with start < end for concurrent_work |
| gap_days? | integer ≥0; required for reopening_risk and ≤ reopening_horizon_days |
| reopening_horizon_days! | integer ≥0 |
| overlap_geometry? | GeoJSON for explanatory visualization; null when proximity has no geometric intersection |
| severity! | enum coordination_review, urgent_review; policy assumption, not predicted safety |
| rationale_code! | deterministic rule identifier |
| method_version!, input_hash! | strings |

data_kind=derived. `urgent_review` requires a separate sourced policy/safety flag; default is coordination_review. Findings are positive rule matches only. Indeterminate pair checks and coverage warnings live in the check/evaluation response, not as fake positive findings. References do not assert a physical underground collision.

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

## Implemented M1 storage and condition projection

SQLite tables: `dataset(id PRIMARY KEY, manifest_json)`, `evidence(id PRIMARY KEY, dataset_id REFERENCES dataset(id), payload)`, `roads(id PRIMARY KEY, dataset_id REFERENCES dataset(id), payload)`. Payloads are JSON validated through Pydantic on import and read, preserving nullable decimal strings, dates, geometry and per-field provenance. Only synthetic records are accepted by the M1 implementation; observed/derived entities above are future contracts, not working import types. M1 supports exactly one snapshot per database. Imports use stable IDs, checksum validation, foreign keys and a transaction. No mutation endpoint exists.

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

The projection carries no independently mutable assessment list. Full ConditionAssessment records, latest-dated selection and stable-ID tie-breaking remain M2, at which point the summary should be derived from those records. No costs, dimensions, observed dates, utility routes or schedules are inferred for M1.
