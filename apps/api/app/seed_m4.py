"""Checksum-verified idempotent M4 import; preserves edited drafts and old snapshots."""
import hashlib
import json

from app.core.config import ROOT
from app.core.repository import RoadRepository
from app.core.planning_repository import PlanningRepository
from app.core.conflict_repository import ConflictRepository
from app.core.scenario_repository import ScenarioRepository
from app.core.scenario_inputs import freeze
from app.models.database import connection, initialize
from app.schemas.scenarios import ScenarioDraft
from app.services.scenarios import evaluate


def seed_m4(path, fixture_dir=ROOT / 'data/demo'):
    raw = (fixture_dir / 'scenarios.json').read_bytes()
    manifest = json.loads((fixture_dir / 'scenarios-manifest.json').read_text())
    if hashlib.sha256(raw).hexdigest() != manifest['checksum_sha256']:
        raise ValueError('M4 fixture checksum mismatch')
    payload = json.loads(raw)
    if [p['id'] for p in payload] != manifest['scenario_ids']:
        raise ValueError('M4 fixture IDs do not match manifest')
    initialize(path)
    canonical = json.dumps(manifest, sort_keys=True)
    with connection(path) as c:
        prior = c.execute('SELECT manifest_json FROM fixture_imports WHERE id=?', (manifest['id'],)).fetchone()
        if prior and prior[0] != canonical:
            raise ValueError('M4 fixture import is immutable')
    repo = ScenarioRepository(path)
    for item in payload:
        draft = ScenarioDraft.model_validate(item['draft'])
        context = freeze(draft, RoadRepository(path), PlanningRepository(path), ConflictRepository(path), item['id'])
        # Existing drafts/evaluations are retained. Identical inputs reuse the saved
        # evaluation; changed source/method context appends a fresh current snapshot.
        scenario = repo.save(draft, item['id'])
        context = freeze(scenario, RoadRepository(path), PlanningRepository(path), ConflictRepository(path), scenario.id)
        repo.save_evaluation(evaluate(scenario, context))
    with connection(path) as c:
        c.execute('INSERT OR IGNORE INTO fixture_imports VALUES (?, ?, ?)', (manifest['id'], manifest['dataset_snapshot_id'], canonical))
    return len(payload)
