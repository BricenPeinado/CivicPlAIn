"""Explicit additive fixture import. No startup seeding or existing-row updates."""
import hashlib
import json

from app.core.config import ROOT
from app.models.database import connection, initialize
from app.schemas.planning import Assessment, AssetAttributes, RepairOption
from app.schemas.roads import Evidence


def seed_m2(path, fixture_dir=ROOT / 'data/demo'):
    manifest = json.loads((fixture_dir / 'maintenance-manifest.json').read_text())
    raw = (fixture_dir / 'maintenance.json').read_bytes()
    checksum = hashlib.sha256(raw).hexdigest()
    if checksum != manifest['checksum_sha256']:
        raise ValueError('M2 fixture checksum mismatch')
    payload = json.loads(raw)
    evidence = Evidence.model_validate(manifest['evidence_source'])
    if evidence.checksum_sha256 != checksum or evidence.id != payload['evidence_id']:
        raise ValueError('M2 evidence checksum/reference mismatch')
    assets = [AssetAttributes.model_validate(a) for a in payload['assets']]
    assessments = [Assessment.model_validate(a) for a in payload['assessments']]
    options = [RepairOption.model_validate(a) for a in payload['repair_options']]
    for records, count, key in [(assets, 'asset_count', 'road_segment_id'), (assessments, 'assessment_count', 'id'), (options, 'repair_option_count', 'id')]:
        if len(records) != manifest[count] or len({getattr(r, key) for r in records}) != len(records):
            raise ValueError('M2 fixture count/IDs mismatch')
    if manifest['fixture_id'] != payload['fixture_id'] or manifest['dataset_snapshot_id'] != payload['dataset_snapshot_id']:
        raise ValueError('M2 fixture manifest identity mismatch')
    initialize(path)
    canonical = json.dumps(manifest, sort_keys=True)
    with connection(path) as conn:
        if not conn.execute('SELECT 1 FROM dataset WHERE id=?', (payload['dataset_snapshot_id'],)).fetchone():
            raise ValueError('Seed the M1 snapshot before importing M2')
        existing = conn.execute('SELECT manifest_json FROM fixture_imports WHERE id=?', (payload['fixture_id'],)).fetchone()
        if existing and existing[0] != canonical:
            raise ValueError('M2 fixture manifest is immutable')
        roads = {row[0] for row in conn.execute('SELECT id FROM roads WHERE dataset_id=?', (payload['dataset_snapshot_id'],))}
        sources = {row[0] for row in conn.execute('SELECT id FROM evidence WHERE dataset_id=?', (payload['dataset_snapshot_id'],))} | {evidence.id}
        for record in [*assets, *assessments, *options]:
            if not set(record.evidence_ids) <= sources:
                raise ValueError('unresolved M2 evidence')
            if hasattr(record, 'road_segment_id') and record.road_segment_id not in roads:
                raise ValueError('unresolved M2 road')
            if isinstance(record, Assessment) and record.dataset_snapshot_id != payload['dataset_snapshot_id']:
                raise ValueError('assessment snapshot mismatch')
        conn.execute('INSERT OR IGNORE INTO fixture_imports VALUES (?, ?, ?)', (payload['fixture_id'], payload['dataset_snapshot_id'], canonical))
        conn.execute('INSERT OR IGNORE INTO evidence VALUES (?, ?, ?)', (evidence.id, payload['dataset_snapshot_id'], evidence.model_dump_json()))
        for asset in assets:
            conn.execute('INSERT OR IGNORE INTO maintenance_assets VALUES (?, ?)', (asset.road_segment_id, asset.model_dump_json()))
        for assessment in assessments:
            conn.execute('INSERT OR IGNORE INTO assessments VALUES (?, ?, ?, ?)', (assessment.id, assessment.road_segment_id,
                str(assessment.assessed_on) if assessment.assessed_on else None, assessment.model_dump_json()))
        for option in options:
            conn.execute('INSERT OR IGNORE INTO repair_options VALUES (?, ?, ?)', (option.id, payload['dataset_snapshot_id'], option.model_dump_json()))
    return len(assets), len(assessments), len(options)
