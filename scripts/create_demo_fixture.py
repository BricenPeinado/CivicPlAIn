"""Reproduce reviewed M1 synthetic fixtures; never downloads municipal data."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "data/demo"
SOURCE = "demo-assumptions-v1"
roads = []
# A schematic 4 by 3 block lattice: 12 horizontal and 12 vertical segments.
for i in range(24):
    if i < 12:
        row, col = divmod(i, 3)
        x, y = -74.0108 + col * .0029, 40.7115 + row * .0022
        coordinates = [[round(x, 6), round(y, 6)], [round(x + .00145, 6), round(y + .00018, 6)],
                       [round(x + .0029, 6), round(y, 6)]]
    else:
        row, col = divmod(i - 12, 4)
        x, y = -74.0108 + col * .0029, 40.7115 + row * .0022
        coordinates = [[round(x, 6), round(y, 6)], [round(x, 6), round(y + .0022, 6)]]
    category, rating = [("poor", "3"), ("good", "8"), ("fair", "6"), ("unknown", None)][i % 4]
    unknown = {key: "not_supplied" for key in ["source_segment_key", "length_m", "width_m",
                                              "lane_count", "coverage_as_of", "condition_summary.assessed_on"]}
    field_evidence = {"geometry": [SOURCE], "name": [SOURCE]}
    if rating is None:
        unknown.update({"condition_summary.rating": "no_demo_assessment",
                        "condition_summary.rating_scale": "no_demo_assessment"})
    else:
        field_evidence.update({"condition_summary.rating": [SOURCE], "condition_summary.category": [SOURCE]})
    record = {"id": f"demo-r-{i+1:03}", "dataset_snapshot_id": "demo-m1-v1",
              "evidence_ids": [SOURCE], "data_kind": "synthetic", "synthetic_input": True,
              "field_evidence": field_evidence, "unknown_reasons": unknown,
              "limitations": ["Schematic demonstration geometry; does not trace actual streets.",
                              "Conditions are authored assumptions, not NYC observations.",
                              "Utility locations and schedules are unknown; no excavation clearance."],
              "created_at": "2026-11-07T00:00:00Z", "name": f"Demo segment R-{i+1:03}",
              "source_segment_key": None, "study_area_id": "lower-manhattan-window-v1",
              "length_m": None, "width_m": None, "lane_count": None,
              "utility_coverage": "unknown", "coverage_as_of": None,
              "condition_summary": {"category": category, "rating": rating,
                                    "rating_scale": "synthetic-1-10-higher-better" if rating else None,
                                    "assessed_on": None, "evidence_ids": [SOURCE],
                                    "data_kind": "synthetic", "synthetic_input": True}}
    roads.append({"type": "Feature", "id": record["id"],
                  "geometry": {"type": "LineString", "coordinates": coordinates}, "properties": record})
raw = (json.dumps({"type": "FeatureCollection", "features": roads}, indent=2) + "\n").encode()
checksum = hashlib.sha256(raw).hexdigest()
evidence = {"id": SOURCE, "title": "CivicPlAIn M1 schematic road and condition assumptions",
            "publisher": "CivicPlAIn demo authors", "source_kind": "demo_assumption",
            "verification_status": "synthetic_demo", "uri": "data/demo/roads.geojson",
            "retrieved_at": None, "observed_on": None, "version": "demo-m1-v1",
            "checksum_sha256": checksum, "original_crs": "EPSG:4326",
            "coverage_note": "24 schematic segments inside the chosen Lower Manhattan window; no actual street coverage.",
            "reliability_note": "Authored synthetic assumptions. No survey, assessment date, dimensions, or utility information.",
            "license_note": "Original CivicPlAIn synthetic fixture; no third-party geographic data incorporated.",
            "unknown_reasons": {"retrieved_at": "not_applicable_authored_fixture", "observed_on": "not_observed"}}
manifest = {"dataset_snapshot_id": "demo-m1-v1", "study_area_id": "lower-manhattan-window-v1",
            "bbox": [-74.012, 40.710, -74.000, 40.720], "record_count": 24,
            "road_ids": [f["id"] for f in roads], "synthetic_input": True,
            "selection_method": "schematic-lattice-v1: 12 bent horizontal and 12 vertical LineStrings; no municipal source",
            "category_rule": "synthetic-1-10-higher-better: good >=8, fair >=5 and <8, poor <5; unknown if rating absent",
            "expected_categories": {"good": 6, "fair": 6, "poor": 6, "unknown": 6},
            "field_assumptions": "All geometry, names and condition labels/ratings are synthetic. Dates and dimensions remain null.",
            "rejected_records": 0, "manual_exclusions": [],
            "coverage_note": "Schematic placed within NYC; not a street survey or representative sample.",
            "files": {"roads.geojson": {"checksum_sha256": checksum, "origin": "scripts/create_demo_fixture.py", "data_kind": "synthetic"}},
            "evidence_source": evidence}
TARGET.mkdir(parents=True, exist_ok=True)
(TARGET / "roads.geojson").write_bytes(raw)
(TARGET / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
print("Reproduced 24 synthetic fixtures and manifest.")
