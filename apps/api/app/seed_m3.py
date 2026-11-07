"""Checksum-verified additive M3 seed; never overwrite local projects."""
import hashlib
import json

from app.core.config import ROOT
from app.models.database import connection, initialize
from app.schemas.conflicts import WorkProject
from app.schemas.roads import Evidence


def seed_m3(path, fixture_dir=ROOT / 'data/demo'):
    manifest = json.loads((fixture_dir / 'projects-manifest.json').read_text())
    raw = (fixture_dir / 'projects.json').read_bytes()
    checksum = hashlib.sha256(raw).hexdigest()
    payload = json.loads(raw)
    evidence = Evidence.model_validate(manifest['evidence_source'])
    if checksum != manifest['checksum_sha256'] or evidence.checksum_sha256 != checksum or evidence.id != payload['evidence_id']:
        raise ValueError('M3 fixture checksum/reference mismatch')
    projects = [WorkProject.model_validate(p) for p in payload['projects']]
    ids = [p.id for p in projects]
    if (len(ids) != len(set(ids)) or ids != manifest['project_ids'] or len(ids) != manifest['project_count'] or not 0 < len(ids) <= 50
            or manifest['fixture_id'] != payload['fixture_id'] or manifest['dataset_snapshot_id'] != payload['dataset_snapshot_id']
            or not payload['synthetic_input'] or not manifest['synthetic_input']):
        raise ValueError('M3 manifest identity/count mismatch')
    initialize(path)
    with connection(path) as conn:
        if not conn.execute('SELECT 1 FROM dataset WHERE id=?', (payload['dataset_snapshot_id'],)).fetchone():
            raise ValueError('Seed M1 before M3')
        canonical = json.dumps(manifest, sort_keys=True)
        existing = conn.execute('SELECT manifest_json FROM fixture_imports WHERE id=?', (payload['fixture_id'],)).fetchone()
        if existing and existing[0] != canonical:
            raise ValueError('M3 fixture manifest is immutable')
        roads = {r[0] for r in conn.execute('SELECT id FROM roads WHERE dataset_id=?', (payload['dataset_snapshot_id'],))}
        sources = {r[0] for r in conn.execute('SELECT id FROM evidence WHERE dataset_id=?', (payload['dataset_snapshot_id'],))} | {evidence.id}
        for p in projects:
            if p.dataset_snapshot_id != payload['dataset_snapshot_id'] or not set(p.road_segment_ids) <= roads or not set(p.evidence_ids) <= sources or p.data_kind != 'synthetic':
                raise ValueError('M3 unresolved road, source, snapshot or classification')
        conn.execute('INSERT OR IGNORE INTO fixture_imports VALUES (?, ?, ?)', (payload['fixture_id'], payload['dataset_snapshot_id'], canonical))
        conn.execute('INSERT OR IGNORE INTO evidence VALUES (?, ?, ?)', (evidence.id, payload['dataset_snapshot_id'], evidence.model_dump_json()))
        for p in projects:
            # Preserve both local payload and its linked roads on repeated seeding.
            inserted = conn.execute('INSERT OR IGNORE INTO work_projects VALUES (?, ?, ?)', (p.id, p.dataset_snapshot_id, p.model_dump_json())).rowcount
            if inserted:
                conn.executemany('INSERT INTO project_roads VALUES (?, ?)', [(p.id, rid) for rid in p.road_segment_ids])
    return len(projects)
