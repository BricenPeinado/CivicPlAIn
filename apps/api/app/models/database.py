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
    with sqlite3.connect(path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        yield conn


def initialize(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with connection(path) as conn:
        conn.executescript(SCHEMA)
