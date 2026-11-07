# Data sources and study area

Status: source planning, reviewed 2026-11-07. No source payload has been downloaded, imported, joined, or validated in M0. No fixtures exist yet.

## Study area: lower-manhattan-window-v1

Use one rectangular Lower Manhattan demonstration window in EPSG:4326: west **-74.012**, south **40.710**, east **-74.000**, north **40.720**. These are chosen study bounds, not measured municipal boundaries. The identifier and exact bbox must be present in the future fixture manifest.

Target 20–30 street centerline segments, hard cap 30. Proposed selection after source validation: retain street-type features intersecting the bbox, order by stable source segment key, and take the first 30; retain original unclipped geometry and record intersection-based selection. Verify source street classification and IDs before applying that rule. Document actual count, rejected records, edge effects, and any manual exclusions. Do not imply full-area or citywide coverage.

If a usable public geometry extract cannot be prepared, author simplified synthetic line geometry inside this same window with `demo-` IDs, “Demo segment” names, and conspicuous labels. It is a schematic placed in NYC, not a survey of actual streets. Synthetic widths, condition, utility works, costs, and dates must never be described as official observations.

## Verification labels

- **Verified and accessible**: the stated resource was actually readable during review; the verification level is explicitly limited to that resource. A readable index is not a verified data payload.
- **Candidate, not yet verified**: proposed input requiring payload retrieval, schema/coverage/license review and validation before use. A search result or catalog shell is insufficient for ingestion readiness.
- **Synthetic/demo**: intentionally authored assumptions for demonstration; no real-world observation is asserted. Planned fixtures remain uncreated until later milestones.

## Source register

| ID / source | Status and evidence | Planned use / limits |
| --- | --- | --- |
| NYC DOT data feeds index | **Verified and accessible**, index HTML readable on review date: [official index](https://www.nyc.gov/html/dot/html/about/datafeeds.shtml) | Lists pavement assessment and street-construction resources. Verification covers the listing only, not payload schemas, completeness, or availability. |
| DCP LION street network | **Candidate, not yet verified** for data use. [Official DCP page](https://www.nyc.gov/content/planning/pages/resources/datasets/lion) and [NYC Open Data catalog](https://data.cityofnewyork.us/City-Government/LION/2v4z-66xt) were located; live page extraction returned shells, not an inspected payload. | Candidate centerline geometry and segment identifiers. Confirm release, coordinate system, street classification, license/use limits and stable keys. Centerlines do not provide verified pavement widths or underground locations. |
| DOT Street Assessment / Pavement Ratings | **Candidate, not yet verified**. The readable [DOT index](https://www.nyc.gov/html/dot/html/about/datafeeds.shtml) links ratings resources; linked GeoJSON retrieval failed in this review. | Candidate condition observations. Validate actual scale semantics, assessment dates, geography and join keys from payload/metadata before use; do not assume every selected segment has a recent rating. No direct payload URL is promised here. |
| DOT Street Construction Permits (2022–Present) | **Candidate, not yet verified** for import. [Official catalog](https://data.cityofnewyork.us/Transportation/Street-Construction-Permits-2022-Present-/tqtj-sjs8/about_data) was located through official search metadata; live extraction returned a shell. | Candidate street-work and possible utility-work indicators. Inspect permit categories, location/schedule fields, statuses and revisions; permit windows are not confirmed construction schedules. No utility network or exhaustive future-work coverage is implied. |
| Utility-owner planned-work / subsurface information | **Candidate, not yet verified**; no public authoritative geometry/schedule dataset has been established for this MVP. No invented URL. | Use synthetic UtilityWork unless suitable public inputs are verified. Real integration requires owner coordination, permissions, sensitivity review, and coverage evidence. |
| CivicPlAIn fixture manifest, geometry and assumptions | **Synthetic/demo**, planned files under data/demo/; not yet created | Bounded map fallback, demo condition, utility project, repair options, cost/duration/lifespan assumptions, scenarios, and expected rule results. DEMO_PLAN defines proposed arithmetic. Not a municipal dataset. |

Publication/update cadence, field names, spatial completeness, and price accuracy are deliberately unasserted for unvalidated payloads. Capture the actual source version and retrieval date at import rather than promising freshness from a catalog title. Other DOT construction layers may be investigated later, but no source beyond this register is needed for MVP acceptance.

## Import and provenance procedure (M1–M3)

1. Retrieve only documented public source resources through a reviewed adapter; do not fetch arbitrary URLs supplied in records or prompts.
2. Record title, publisher, exact origin, retrieval time, source version if known, checksum, source CRS, license/use notes and coverage. Unknown metadata remains unknown.
3. Store original downloads in ignored data/raw/; inspect schema, geometry validity, dates, duplicates and stable keys. Confirm source terms before redistributing extracts.
4. Select the bounded study area with a reproducible rule. Retain source IDs and original observations; record transformations, spatial matching tolerances, and rejected/unmatched counts. Never silently join by a similar road name.
5. Normalize to DATA_MODEL with separate observed, synthetic and derived fields; transformed lengths are derived, not source measurements. Generated normalization outputs belong in ignored data/processed/.
6. Only reviewed, redistribution-appropriate small fixtures enter data/demo/. The manifest records fixture version, bbox, IDs, checksums, per-file origin, per-field assumptions, labels, expected counts, coverage notes, and deterministic method versions.

## Missing data and joins

Use null plus field-specific unknown reasons. Distinguish no assessment, undated assessment, old observation, unmapped permit, and missing utility coverage. A failed join never creates a fictional condition or project. If records refer to the same place ambiguously, keep candidate matches with limitations for review rather than choosing silently.

Map and asset panels show unknown coverage at all times. A conflict response with no positive findings still reports which projects and scope were checked and what is missing. No public source here can establish safe excavation, complete underground coverage, or permission to work.

TBD: actual source release, verified payload schemas and terms, join strategy, and usable count. Recommendation: ship the complete synthetic demonstrator first, then replace only validated fields with a small attributed public geometry/condition extract. Preserve synthetic utility work unless a defensible public schedule source is established.
