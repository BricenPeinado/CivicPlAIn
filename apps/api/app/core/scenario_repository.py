"""Optimistic draft revisions and append-only evaluation snapshots."""
from datetime import datetime, timezone
from uuid import uuid4

from app.models.database import connection
from app.schemas.scenarios import Scenario, ScenarioDraft, ScenarioEvaluation
from app.services.estimates import canonical_hash
from app.services.scenario_identity import canonical_proposal


class RevisionConflict(ValueError):
    pass


class ScenarioRepository:
    def __init__(self, path):
        self.path = path

    def get(self, scenario_id):
        with connection(self.path) as c:
            row = c.execute('SELECT payload FROM scenarios WHERE id=?', (scenario_id,)).fetchone()
        return Scenario.model_validate_json(row[0]) if row else None

    def list(self, after='', limit=30):
        with connection(self.path) as c:
            rows = c.execute('SELECT payload FROM scenarios WHERE id>? ORDER BY id LIMIT ?', (after, limit + 1)).fetchall()
        return [Scenario.model_validate_json(r[0]) for r in rows]

    def save(self, draft, scenario_id=None, expected_revision=None):
        draft = ScenarioDraft.model_validate(canonical_proposal(draft.model_dump(mode="json")))
        now = datetime.now(timezone.utc).isoformat()
        with connection(self.path) as c:
            c.execute('BEGIN IMMEDIATE')
            row = c.execute('SELECT payload FROM scenarios WHERE id=?', (scenario_id,)).fetchone() if scenario_id else None
            old = Scenario.model_validate_json(row[0]) if row else None
            if expected_revision is not None and (not old or old.revision != expected_revision):
                raise RevisionConflict('Scenario changed; reload before saving or evaluating')
            if scenario_id and old and expected_revision is None:
                return old  # idempotent fixture insertion preserves user edits
            record = Scenario(**draft.model_dump(), id=scenario_id or str(uuid4()),
                revision=old.revision + 1 if old else 1, revision_hash=canonical_hash(draft.model_dump(mode='json')),
                created_at=old.created_at if old else now, updated_at=now)
            c.execute('INSERT INTO scenarios VALUES (?, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET revision=excluded.revision, payload=excluded.payload',
                (record.id, record.dataset_snapshot_id, record.revision, record.model_dump_json()))
            c.execute('DELETE FROM scenario_actions WHERE scenario_id=?', (record.id,))
            c.execute('DELETE FROM scenario_projects WHERE scenario_id=?', (record.id,))
            for a in record.actions:
                c.execute('INSERT INTO scenario_actions VALUES (?, ?, ?, ?, ?)',
                    (record.id, a.id, a.road_segment_id, a.repair_option_id, a.model_dump_json()))
            for pid in sorted(set(record.external_project_ids + [p for a in record.actions for p in a.related_project_ids])):
                c.execute('INSERT INTO scenario_projects VALUES (?, ?)', (record.id, pid))
        return record

    def evaluation(self, evaluation_id):
        with connection(self.path) as c:
            row = c.execute('SELECT payload FROM scenario_evaluations WHERE id=?', (evaluation_id,)).fetchone()
        return ScenarioEvaluation.model_validate_json(row[0]) if row else None

    def evaluations(self, scenario_id):
        with connection(self.path) as c:
            rows = c.execute('SELECT payload FROM scenario_evaluations WHERE scenario_id=? ORDER BY rowid DESC', (scenario_id,)).fetchall()
        return [ScenarioEvaluation.model_validate_json(r[0]) for r in rows]

    def save_evaluation(self, record):
        with connection(self.path) as c:
            c.execute('BEGIN IMMEDIATE')
            row = c.execute('SELECT revision FROM scenarios WHERE id=?', (record.scenario_id,)).fetchone()
            if not row or row[0] != record.scenario_revision:
                raise RevisionConflict('Scenario changed during evaluation; evaluate the current revision')
            c.execute('INSERT OR IGNORE INTO scenario_evaluations VALUES (?, ?, ?, ?)',
                (record.id, record.scenario_id, record.scenario_revision, record.model_dump_json()))
        return self.evaluation(record.id)
