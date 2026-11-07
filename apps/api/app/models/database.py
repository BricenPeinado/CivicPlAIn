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
