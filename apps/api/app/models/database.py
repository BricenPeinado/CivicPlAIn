"""One SQLite connection per operation, with transactional writes."""
import sqlite3
from contextlib import contextmanager
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS dataset (
    id TEXT PRIMARY KEY, manifest_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS evidence (
    id TEXT PRIMARY KEY, dataset_id TEXT NOT NULL REFERENCES dataset(id), payload TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS roads (
    id TEXT PRIMARY KEY, dataset_id TEXT NOT NULL REFERENCES dataset(id), payload TEXT NOT NULL
);
"""


@contextmanager
def connection(path: Path):
    conn = sqlite3.connect(path)
    try:
        with conn:
            conn.execute("PRAGMA foreign_keys = ON")
            yield conn
    finally:
        conn.close()


def initialize(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with connection(path) as conn:
        conn.executescript(SCHEMA)
        # Additive, repeatable M1→M2 migration; existing JSON payloads stay untouched.
        conn.execute("BEGIN IMMEDIATE")
        for statement in M2_SCHEMA:
            conn.execute(statement)
        conn.execute("INSERT OR IGNORE INTO schema_migrations VALUES (2, 'm2-additive-v1')")
        for statement in M3_SCHEMA:
            conn.execute(statement)
        conn.execute("INSERT OR IGNORE INTO schema_migrations VALUES (3, 'm3-additive-v1')")
        for statement in M4_SCHEMA:
            conn.execute(statement)
        conn.execute("INSERT OR IGNORE INTO schema_migrations VALUES (4, 'm4-additive-v1')")
        for statement in M5_SCHEMA:
            conn.execute(statement)
        conn.execute("INSERT OR IGNORE INTO schema_migrations VALUES (5, 'm5-additive-v1')")


M2_SCHEMA = [
    "CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY, name TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS fixture_imports (id TEXT PRIMARY KEY, dataset_id TEXT NOT NULL REFERENCES dataset(id), manifest_json TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS maintenance_assets (road_id TEXT PRIMARY KEY REFERENCES roads(id), payload TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS assessments (id TEXT PRIMARY KEY, road_id TEXT NOT NULL REFERENCES roads(id), assessed_on TEXT, payload TEXT NOT NULL)",
    "CREATE INDEX IF NOT EXISTS assessments_by_road ON assessments(road_id, assessed_on, id)",
    "CREATE TABLE IF NOT EXISTS repair_options (id TEXT PRIMARY KEY, dataset_id TEXT NOT NULL REFERENCES dataset(id), payload TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS estimates (id TEXT PRIMARY KEY, road_id TEXT NOT NULL REFERENCES roads(id), dataset_id TEXT NOT NULL REFERENCES dataset(id), payload TEXT NOT NULL, low_cents INTEGER NOT NULL CHECK(low_cents>=0), base_cents INTEGER NOT NULL CHECK(base_cents>=low_cents), high_cents INTEGER NOT NULL CHECK(high_cents>=base_cents))",
    "CREATE TRIGGER IF NOT EXISTS estimates_no_update BEFORE UPDATE ON estimates BEGIN SELECT RAISE(ABORT, 'estimates are immutable'); END",
    "CREATE TRIGGER IF NOT EXISTS estimates_no_delete BEFORE DELETE ON estimates BEGIN SELECT RAISE(ABORT, 'estimates are immutable'); END",
]

M3_SCHEMA = [
    "CREATE TABLE IF NOT EXISTS work_projects (id TEXT PRIMARY KEY, dataset_id TEXT NOT NULL REFERENCES dataset(id), payload TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS project_roads (project_id TEXT NOT NULL REFERENCES work_projects(id), road_id TEXT NOT NULL REFERENCES roads(id), PRIMARY KEY(project_id, road_id))",
    "CREATE INDEX IF NOT EXISTS project_roads_by_road ON project_roads(road_id, project_id)",
    "CREATE TABLE IF NOT EXISTS conflict_analyses (id TEXT PRIMARY KEY, dataset_id TEXT NOT NULL REFERENCES dataset(id), payload TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS conflict_findings (id TEXT PRIMARY KEY, analysis_id TEXT NOT NULL REFERENCES conflict_analyses(id), payload TEXT NOT NULL)",
    "CREATE INDEX IF NOT EXISTS findings_by_analysis ON conflict_findings(analysis_id, id)",
    "CREATE TRIGGER IF NOT EXISTS analyses_no_update BEFORE UPDATE ON conflict_analyses BEGIN SELECT RAISE(ABORT, 'analyses are immutable'); END",
    "CREATE TRIGGER IF NOT EXISTS analyses_no_delete BEFORE DELETE ON conflict_analyses BEGIN SELECT RAISE(ABORT, 'analyses are immutable'); END",
    "CREATE TRIGGER IF NOT EXISTS findings_no_update BEFORE UPDATE ON conflict_findings BEGIN SELECT RAISE(ABORT, 'findings are immutable'); END",
    "CREATE TRIGGER IF NOT EXISTS findings_no_delete BEFORE DELETE ON conflict_findings BEGIN SELECT RAISE(ABORT, 'findings are immutable'); END",
]

M4_SCHEMA = [
    "CREATE TABLE IF NOT EXISTS scenarios (id TEXT PRIMARY KEY, dataset_id TEXT NOT NULL REFERENCES dataset(id), revision INTEGER NOT NULL CHECK(revision>0), payload TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS scenario_actions (scenario_id TEXT NOT NULL REFERENCES scenarios(id), id TEXT NOT NULL, road_id TEXT NOT NULL REFERENCES roads(id), option_id TEXT REFERENCES repair_options(id), payload TEXT NOT NULL, PRIMARY KEY(scenario_id,id))",
    "CREATE TABLE IF NOT EXISTS scenario_projects (scenario_id TEXT NOT NULL REFERENCES scenarios(id), project_id TEXT NOT NULL REFERENCES work_projects(id), PRIMARY KEY(scenario_id, project_id))",
    "CREATE TABLE IF NOT EXISTS scenario_evaluations (id TEXT PRIMARY KEY, scenario_id TEXT NOT NULL REFERENCES scenarios(id), revision INTEGER NOT NULL, payload TEXT NOT NULL)",
    "CREATE INDEX IF NOT EXISTS evaluations_by_scenario ON scenario_evaluations(scenario_id,revision)",
    "CREATE TRIGGER IF NOT EXISTS evaluations_no_update BEFORE UPDATE ON scenario_evaluations BEGIN SELECT RAISE(ABORT, 'evaluations are immutable'); END",
    "CREATE TRIGGER IF NOT EXISTS evaluations_no_delete BEFORE DELETE ON scenario_evaluations BEGIN SELECT RAISE(ABORT, 'evaluations are immutable'); END",
]

M5_SCHEMA = [
    "CREATE TABLE IF NOT EXISTS review_events (id TEXT PRIMARY KEY, evaluation_id TEXT NOT NULL REFERENCES scenario_evaluations(id), payload TEXT NOT NULL)",
    "CREATE TRIGGER IF NOT EXISTS review_events_no_update BEFORE UPDATE ON review_events BEGIN SELECT RAISE(ABORT, 'Review events are immutable'); END",
    "CREATE TRIGGER IF NOT EXISTS review_events_no_delete BEFORE DELETE ON review_events BEGIN SELECT RAISE(ABORT, 'Review events are immutable'); END",
    "CREATE TABLE IF NOT EXISTS ai_evidence (hash TEXT PRIMARY KEY, payload TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS ai_interactions (id TEXT PRIMARY KEY, evidence_hash TEXT NOT NULL REFERENCES ai_evidence(hash), payload TEXT NOT NULL)",
    "CREATE TRIGGER IF NOT EXISTS ai_evidence_no_update BEFORE UPDATE ON ai_evidence BEGIN SELECT RAISE(ABORT, 'AI evidence is immutable'); END",
    "CREATE TRIGGER IF NOT EXISTS ai_evidence_no_delete BEFORE DELETE ON ai_evidence BEGIN SELECT RAISE(ABORT, 'AI evidence is immutable'); END",
    "CREATE TRIGGER IF NOT EXISTS ai_interactions_no_update BEFORE UPDATE ON ai_interactions BEGIN SELECT RAISE(ABORT, 'AI audit is immutable'); END",
    "CREATE TRIGGER IF NOT EXISTS ai_interactions_no_delete BEFORE DELETE ON ai_interactions BEGIN SELECT RAISE(ABORT, 'AI audit is immutable'); END",
]
