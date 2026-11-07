# Data sources and study area

Status: source planning, reviewed 2026-11-07. No municipal source payload has been imported. M1 now includes 24 reviewed synthetic schematic roads and a checksum manifest in data/demo; source-register candidate status remains unchanged.

## Study area: lower-manhattan-window-v1

Use one rectangular Lower Manhattan demonstration window in EPSG:4326: west **-74.012**, south **40.710**, east **-74.000**, north **40.720**. These are chosen study bounds, not measured municipal boundaries. The identifier and exact bbox must be present in the future fixture manifest.

Target 20–30 street centerline segments, hard cap 30. Proposed selection after source validation: retain street-type features intersecting the bbox, order by stable source segment key, and take the first 30; retain original unclipped geometry and record intersection-based selection. Verify source street classification and IDs before applying that rule. Document actual count, rejected records, edge effects, and any manual exclusions. Do not imply full-area or citywide coverage.

If a usable public geometry extract cannot be prepared, author simplified synthetic line geometry inside this same window with `demo-` IDs, “Demo segment” names, and conspicuous labels. It is a schematic placed in NYC, not a survey of actual streets. Synthetic widths, condition, utility works, costs, and dates must never be described as official observations.

## Verification labels

- **Verified and accessible**: the stated resource was actually readable during review; the verification level is explicitly limited to that resource. A readable index is not a verified data payload.
- **Candidate, not yet verified**: proposed input requiring payload retrieval, schema/coverage/license review and validation before use. A search result or catalog shell is insufficient for ingestion readiness.
- **Synthetic/demo**: intentionally authored assumptions for demonstration; no real-world observation is asserted. M1 road fixtures exist; M2 maintenance, assessment and rate fixtures are implemented; M3 fictional utility/project fixtures are implemented; M4 scenario fixtures are implemented.

## Source register

| ID / source | Status and evidence | Planned use / limits |
| --- | --- | --- |
| NYC DOT data feeds index | **Verified and accessible**, index HTML readable on review date: [official index](https://www.nyc.gov/html/dot/html/about/datafeeds.shtml) | Lists pavement assessment and street-construction resources. Verification covers the listing only, not payload schemas, completeness, or availability. |
| DCP LION street network | **Candidate, not yet verified** for data use. [Official DCP page](https://www.nyc.gov/content/planning/pages/resources/datasets/lion) and [NYC Open Data catalog](https://data.cityofnewyork.us/City-Government/LION/2v4z-66xt) were located; live page extraction returned shells, not an inspected payload. | Candidate centerline geometry and segment identifiers. Confirm release, coordinate system, street classification, license/use limits and stable keys. Centerlines do not provide verified pavement widths or underground locations. |
| DOT Street Assessment / Pavement Ratings | **Candidate, not yet verified**. The readable [DOT index](https://www.nyc.gov/html/dot/html/about/datafeeds.shtml) links ratings resources; linked GeoJSON retrieval failed in this review. | Candidate condition observations. Validate actual scale semantics, assessment dates, geography and join keys from payload/metadata before use; do not assume every selected segment has a recent rating. No direct payload URL is promised here. |
| DOT Street Construction Permits (2022–Present) | **Candidate, not yet verified** for import. [Official catalog](https://data.cityofnewyork.us/Transportation/Street-Construction-Permits-2022-Present-/tqtj-sjs8/about_data) was located through official search metadata; live extraction returned a shell. | Candidate street-work and possible utility-work indicators. Inspect permit categories, location/schedule fields, statuses and revisions; permit windows are not confirmed construction schedules. No utility network or exhaustive future-work coverage is implied. |
| Utility-owner planned-work / subsurface information | **Candidate, not yet verified**; no public authoritative geometry/schedule dataset has been established for this MVP. No invented URL. | Use synthetic UtilityWork unless suitable public inputs are verified. Real integration requires owner coordination, permissions, sensitivity review, and coverage evidence. |
| CivicPlAIn fixture manifest, geometry and assumptions | **Synthetic/demo**, M1 roads.geojson and manifest.json under data/demo/ now implemented; M2 maintenance, assessment and rate fixtures are implemented; M3 fictional utility/project fixtures are implemented; M4 scenario fixtures are implemented | M1 includes bounded schematic geometry and synthetic condition labels/ratings. M2 adds synthetic dimensions, assessment history, repair options, cost rates and productivity. M3 adds seven fictional projects and saved deterministic conflict results. Lifespan stays unknown; reviewed scenarios reuse the same catalog and preserve explicit supplied schedule assumptions. HACKATHON_DEMO records verified arithmetic. Not a municipal dataset. |

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

## M1 fixture coverage

`demo-m1-v1` contains 24 stable `demo-r-001`…`demo-r-024` records: a 4×3 schematic lattice of 12 horizontal and 12 vertical segments, all inside the specified window. It meets the 20–30 target with no rejected records or manual exclusions. It is unrelated to actual street centerlines, does not imply full-area coverage, and redistributes no third-party geographic data. All condition assessment dates, dimensions and lane counts remain null with reasons. Six records per category exercise good/fair/poor/unknown styling. The manifest contains the synthetic rating thresholds, per-file checksum, source record, field assumptions and generator version. `scripts/create_demo_fixture.py` reproduces exact fixture bytes; it does not download data.

## M2 synthetic planning catalog (`demo-m2-v1`)

`data/demo/maintenance.json` and `maintenance-manifest.json` add five related road assets, 26 assessment records (18 undated M1 summaries plus eight dated demo records), and three repair options to the unchanged `demo-m1-v1` geometry snapshot. Stable road IDs: R-001 poor 100×8 m; R-002 good 120×7 m; R-003 fair 150×8 m; R-004 unknown dimensions/surface/assessment; R-005 poor 900×12 m. Every number/date is synthetic and each source is `demo-maintenance-assumptions-v1` or the original M1 source. No geometric distance is calculated. The 10,800 m² case illustrates large cost differences and cannot establish which treatment is feasible.

| Demo treatment | Bundled base USD/m² | Low/high USD/m² | Mobilization / traffic USD | Contingency | Productivity m²/active_workday | Setup / curing days |
| --- | --- | --- | --- | --- | --- | --- |
| Preventive | 6.00 | 4.80 / 7.80 | 1,500 / 500 | 20% | 1,200 | 1 / 0 |
| Resurface | 45.00 | 36.00 / 58.50 | 6,000 / 2,500 | 20% | 600 | 2 / 1 |
| Reconstruct | 140.00 | 112.00 / 182.00 | 20,000 / 6,000 | 25% | 200 | 3 / 3 |

Bundled rates include materials/labor/equipment; mobilization and traffic allowances are additional and no crew/resource costs are added again. Utility relocation, drainage redesign, permits, taxes and design fees are excluded. Quantities assume full rectangular scope; structural condition, layer design, actual resources, traffic phasing, weekends/weather and subsurface information are unverified. Low/high vary only the bundled unit rate by −20%/+30%; this is an authored sensitivity assumption, not calibrated uncertainty. Curing/setup/productivity are illustrative, not a contractor schedule. Basis date 2026-11-07 identifies an authored rate version, not market research.

No reviewed external construction-price payload was available in the repository. M2 intentionally uses no official price claim or inferred accuracy. `scripts/create_m2_fixture.py` reproduces exact JSON and SHA-256 manifest bytes; seed verifies counts, IDs, references and checksums before transactional insert. A changed manifest cannot overwrite an imported fixture. The prior DEMO_PLAN's scenario rates/arithmetic remain illustrative future M4 fixtures, not this M2 catalog. Future scenarios must select and freeze an explicit consistent rate/scope basis rather than assume that earlier narrative is implemented.

## M3 fictional work-project source

`projects.json` / `projects-manifest.json` add seven authored work projects under fixture ID `demo-m3-v1`, linked to the unchanged `demo-m1-v1` road snapshot. Source `demo-project-assumptions-v1` records the exact SHA-256, EPSG:4326, generator, synthetic status, expected pairs and missing-data examples. Footprints, dates, lane closures, organizations and excavation scope are invented and labeled at field/record/screen level. Geometry is approximate or unknown; there is no actual subsurface map or positional accuracy. No outside project/permit payload was retrieved. Existing maintenance and road manifests remain unchanged. Repeated seeding validates identity/checksum and preserves local rows. M4 scenario assumption sources are frozen inside evaluations; see HACKATHON_DEMO for exact IDs and results.
