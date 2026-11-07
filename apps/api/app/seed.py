"""Explicit, checksum-verified, transactional demo import. python -m app.seed"""
import hashlib
import json

from shapely.geometry import box, shape

from app.core.config import ROOT, Settings
from app.models.database import connection, initialize
from app.schemas.roads import Evidence, Road


def seed(path, fixture_dir=ROOT / "data/demo"):
    manifest = json.loads((fixture_dir / "manifest.json").read_text())
    raw = (fixture_dir / "roads.geojson").read_bytes()
    if hashlib.sha256(raw).hexdigest() != manifest["files"]["roads.geojson"]["checksum_sha256"]:
        raise ValueError("fixture checksum mismatch")
    collection = json.loads(raw)
    roads = [Road.model_validate({**feature["properties"], "geometry": feature["geometry"]})
             for feature in collection["features"]]
    ids = [road.id for road in roads]
    if (len(ids) != len(set(ids)) or ids != manifest["road_ids"] or
            len(ids) != manifest["record_count"] or not 0 < len(ids) <= 30):
        raise ValueError("fixture identifiers/count do not match manifest")
    if manifest["bbox"] != [-74.012, 40.710, -74.000, 40.720]:
        raise ValueError("study window does not match contract")
    evidence = Evidence.model_validate(manifest["evidence_source"])
    if evidence.checksum_sha256 != hashlib.sha256(raw).hexdigest():
        raise ValueError("evidence checksum mismatch")
    window = box(*manifest["bbox"])
    for road in roads:
        if (road.dataset_snapshot_id != manifest["dataset_snapshot_id"] or
                road.study_area_id != manifest["study_area_id"] or
                set(road.evidence_ids) != {evidence.id} or
                not window.intersects(shape(road.geometry.model_dump()))):
            raise ValueError("fixture snapshot, evidence, or study bounds mismatch")
    initialize(path)
    with connection(path) as conn:
        snapshots = conn.execute("SELECT id FROM dataset").fetchall()
        if any(row[0] != manifest["dataset_snapshot_id"] for row in snapshots):
            raise ValueError("M1 supports one snapshot per database; use a new database path")
        existing = conn.execute("SELECT manifest_json FROM dataset WHERE id = ?",
                                (manifest["dataset_snapshot_id"],)).fetchone()
        canonical = json.dumps(manifest, sort_keys=True)
        if existing and existing[0] != canonical:
            raise ValueError("snapshot is immutable; use a new snapshot ID/database")
        conn.execute("INSERT OR IGNORE INTO dataset VALUES (?, ?)",
                     (manifest["dataset_snapshot_id"], canonical))
        conn.execute("INSERT OR IGNORE INTO evidence VALUES (?, ?, ?)",
                     (evidence.id, manifest["dataset_snapshot_id"], evidence.model_dump_json()))
        for road in roads:
            conn.execute("INSERT OR IGNORE INTO roads VALUES (?, ?, ?)",
                         (road.id, road.dataset_snapshot_id, road.model_dump_json()))
    return len(roads)


if __name__ == "__main__":
    from app.seed_m2 import seed_m2
    path = Settings().database_path
    print(f"Demo fixture ready: {seed(path)} synthetic road segments; M2 counts {seed_m2(path)}.")
