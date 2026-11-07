"""Validated M3 records; identical analyses reuse immutable snapshots."""
from app.models.database import connection
from app.schemas.conflicts import WorkProject, ConflictAnalysis, ConflictFinding


class ConflictRepository:
    def __init__(self, path):
        self.path = path

    def projects(self):
        with connection(self.path) as conn:
            rows = conn.execute('SELECT payload FROM work_projects ORDER BY id').fetchall()
        return [WorkProject.model_validate_json(row[0]) for row in rows]

    def project(self, project_id):
        with connection(self.path) as conn:
            row = conn.execute('SELECT payload FROM work_projects WHERE id=?', (project_id,)).fetchone()
        return WorkProject.model_validate_json(row[0]) if row else None

    def analysis(self, analysis_id):
        with connection(self.path) as conn:
            row = conn.execute('SELECT payload FROM conflict_analyses WHERE id=?', (analysis_id,)).fetchone()
        return ConflictAnalysis.model_validate_json(row[0]) if row else None

    def findings(self):
        with connection(self.path) as conn:
            rows = conn.execute('SELECT payload FROM conflict_findings ORDER BY id').fetchall()
        return [ConflictFinding.model_validate_json(row[0]) for row in rows]

    def finding(self, finding_id):
        with connection(self.path) as conn:
            row = conn.execute('SELECT payload FROM conflict_findings WHERE id=?', (finding_id,)).fetchone()
        return ConflictFinding.model_validate_json(row[0]) if row else None

    def save(self, result):
        with connection(self.path) as conn:
            conn.execute('INSERT OR IGNORE INTO conflict_analyses VALUES (?, ?, ?)',
                         (result.id, result.dataset_snapshot_id, result.model_dump_json()))
            for finding in result.findings:
                conn.execute('INSERT OR IGNORE INTO conflict_findings VALUES (?, ?, ?)',
                             (finding.id, result.id, finding.model_dump_json()))
        return self.analysis(result.id)
