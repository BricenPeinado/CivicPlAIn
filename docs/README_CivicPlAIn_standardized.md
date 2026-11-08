# CivicPlAIn — standardized Lower Manhattan data

**Source:** Uploaded CivicPlAIn NYC official pilot (`nyc-4620b9e30c1c0bd5be4252fe27999c80`), transformed without external source fetching. Built 2026-11-08. This is a **derived application-read model**, not a replacement for CivicPlAIn's existing database or a NYC official condition classification.

## What is standardized

- **4,150 LION road rows** in `roads`, with immutable `road_id`, original `segment_id`, `object_id`, GeoJSON and `street_key`.
- **249 street names** in `streets`, with one row per normalized name, aggregated counts and a simple display condition.
- **8,726 actual pavement observations** in `pavement_observations`, including source rating, date, on/from/to street, geometry and source revision.
- **23,047 actual permits** in `permits`, including on/from/to streets, permit number/type/status and administrative dates.
- **66,895 original permit name mentions** in `permit_street_mentions` identifying the role: `on_street`, `from_cross_street`, `to_cross_street`.
- **85,905 legacy pavement spatial candidates** in `pavement_road_candidates`, retained to let developers refine the name-only display to individual road segments.

### Rules

`street_key` is the trimmed uppercase name with non-alphanumeric runs replaced by one space. **Any permit with an `on_street` value matching a LION street name is linked to that street** through `permits.on_street_key`. From/to streets are indexed separately as cross-street *mentions*; those do not assert that the permitted work occurs on that cross street. This rule is deliberately permissive at *street level*. It does not assert work on each individual LION segment of the street.

Pavement observations also link to a street through the normalized `on_street` field, regardless of geometry ambiguity. The street's `latest_rating` uses the newest named-street observation with a numeric rating and no non-rating reason, with a deterministic ID tie-break. `display_condition` uses **app-facing indicative bins**: 1–<4 Poor, 4–<8 Fair, 8–10 Good; numeric values outside 1–10 are Unclassified. These are **not NYC DOT's official category policy** and are not a verified whole-road or per-segment rating. The same street-level display is shown on each segment to support selection; the raw observation geometry/date is available for geographic refinement.

Source permits' `issue_date`, `valid_from`, `valid_to` are **administrative**; they do not mean actual construction began or finished. The dataset does not fabricate missing pricing, durations, or utility locations.

## Direct queries for the app

```sql
-- Find and draw roads, with an immediately usable indicative street condition:
SELECT road_id, street_name, geometry_json, latest_rating,
       latest_inspection_at, display_condition, display_basis,
       street_observation_count, permits_on_street
FROM road_profiles LIMIT 100;

-- Get a selected road's exact named-street pavement observations:
SELECT observation_id, on_street, from_street, to_street, rating,
       display_condition, inspection_at, geometry_json
FROM road_pavement_by_name
WHERE road_id = ?
ORDER BY inspection_at DESC LIMIT 100;

-- Get a selected road's permits by on-street name:
SELECT permit_id, permit_number, permit_type, permit_status,
       on_street, from_street, to_street, issue_date, valid_from, valid_to
FROM road_permits_by_name
WHERE road_id = ?
ORDER BY issue_date DESC LIMIT 100;

-- Find directly mentioned cross streets, if relevant to inspection:
SELECT p.*, m.role FROM permit_street_mentions m
JOIN permits p USING (permit_id)
WHERE m.street_key = ? AND m.role != 'on_street'
LIMIT 100;
```

**Performance note:** The views `road_permits_by_name` and `road_pavement_by_name` multiply street-level records across all matching LION rows when queried *without* a `WHERE road_id` filter. Always filter by a selected `road_id`, with pagination. The physical tables have indexed `street_key` fields.

## Quick checks

```bash
python3 - <<'PY'
import sqlite3
c=sqlite3.connect('data/processed/CivicPlAIn_standardized.sqlite3')
print('Integrity:', c.execute('PRAGMA integrity_check').fetchone()[0])
print('Roads:', c.execute('SELECT COUNT(*) FROM roads').fetchone()[0])
print('Ratings by street:', c.execute('SELECT display_condition,COUNT(*) FROM streets GROUP BY display_condition').fetchall())
print('White Street:',c.execute("SELECT display_condition,latest_rating,observations,permits_on_street FROM streets WHERE street_key='WHITE STREET'").fetchone())
PY
```

## Integrating into CivicPlAIn

Do **not** overwrite the original M8 source database. Add a read-only SQLite connection to this database (or copy its standardized tables into a new additive database explicitly) and connect Map's selected `road_id` to `road_profiles`, `road_pavement_by_name`, and `road_permits_by_name`. Keep original official endpoints available for complete source/provenance and all saved-planning replays. Use labels **"Latest street observation"**, **"Indicative pavement band"**, and **"Permits naming this street"** rather than claiming an authorized road-wide rating or actual construction. No active work schedule can be inferred from a permit issue/effectiveness/expiration date.

**Coverage:** 249 street names, of which 188 have one or more named pavement observations, 157 have one or more permits naming the street as `on_street`, and 156 have both. Counts cover the chosen Lower Manhattan LION names and were computed from the uploaded pilot database. Among the 249 names: 89 indicative Good, 83 indicative Fair, 5 indicative Poor, 72 Unknown. These are display bands for latest named-street observations, not a physical road-condition census.
