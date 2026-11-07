"""Read-only SQLite integrity and frozen evaluation replay verification.

Usage: PYTHONPATH=apps/api .venv/bin/python scripts/verify_m4.py [database_path]
"""
import sys
from pathlib import Path

from app.core.config import Settings
from app.core.scenario_repository import ScenarioRepository
from app.models.database import connection
from app.schemas.scenarios import ScenarioEvaluation
from app.services.scenarios import replay


def verify(path):
    with connection(path) as c:
        assert c.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        assert c.execute('PRAGMA foreign_key_check').fetchall() == []
        rows = c.execute('SELECT payload FROM scenario_evaluations ORDER BY id').fetchall()
    for row in rows:
        saved = ScenarioEvaluation.model_validate_json(row[0])
        result = replay(saved)
        assert (result.input_hash, result.result_hash) == (saved.input_hash, saved.result_hash), saved.id
        assert ScenarioRepository(path).evaluation(saved.id) == saved
    print(f'SQLite integrity ok; no foreign-key violations; {len(rows)} immutable evaluations replayed with matching hashes.')


if __name__ == '__main__':
    verify(Path(sys.argv[1]) if len(sys.argv) > 1 else Settings().database_path)
