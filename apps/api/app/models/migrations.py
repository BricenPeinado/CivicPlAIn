"""Explicit additive schema 7 migration with SQLite backup and preservation checks."""
import hashlib
import json
import sqlite3
from pathlib import Path

from app.models.database import SCHEMA, M2_SCHEMA, M3_SCHEMA, M4_SCHEMA, M5_SCHEMA

TABLES = [
    'CREATE TABLE source_revisions(id TEXT PRIMARY KEY, source_id TEXT NOT NULL, raw_sha256 TEXT NOT NULL, payload TEXT NOT NULL)',
    "CREATE TABLE import_runs(id TEXT PRIMARY KEY, status TEXT NOT NULL CHECK(status IN ('validated','rejected','published','failed')), report_json TEXT NOT NULL)",
    'CREATE TABLE data_snapshots(id TEXT PRIMARY KEY, study_area_id TEXT NOT NULL, manifest_hash TEXT NOT NULL UNIQUE, manifest_json TEXT NOT NULL, published_at TEXT NOT NULL)',
    'CREATE TABLE snapshot_sources(snapshot_id TEXT NOT NULL REFERENCES data_snapshots(id), source_revision_id TEXT NOT NULL REFERENCES source_revisions(id), PRIMARY KEY(snapshot_id,source_revision_id))',
    '''CREATE TABLE import_records(snapshot_id TEXT NOT NULL, kind TEXT NOT NULL CHECK(kind IN ('road','condition','permit','context')), id TEXT NOT NULL,
       source_revision_id TEXT NOT NULL, source_record_key TEXT NOT NULL, west REAL, south REAL, east REAL, north REAL, payload TEXT NOT NULL,
       PRIMARY KEY(snapshot_id,kind,id), UNIQUE(snapshot_id,kind,source_revision_id,source_record_key),
       FOREIGN KEY(snapshot_id,source_revision_id) REFERENCES snapshot_sources(snapshot_id,source_revision_id))''',
    'CREATE INDEX municipal_bbox ON import_records(snapshot_id,kind,west,east,south,north)',
    '''CREATE TABLE geographic_matches(snapshot_id TEXT NOT NULL, id TEXT NOT NULL, source_kind TEXT NOT NULL, source_record_id TEXT NOT NULL,
       target_kind TEXT NOT NULL CHECK(target_kind='road'), target_road_id TEXT, status TEXT NOT NULL CHECK(status IN ('matched','ambiguous','unmatched')), payload TEXT NOT NULL,
       PRIMARY KEY(snapshot_id,id), UNIQUE(snapshot_id,source_kind,source_record_id),
       FOREIGN KEY(snapshot_id,source_kind,source_record_id) REFERENCES import_records(snapshot_id,kind,id),
       FOREIGN KEY(snapshot_id,target_kind,target_road_id) REFERENCES import_records(snapshot_id,kind,id))''',
]
for table in ['source_revisions','data_snapshots','snapshot_sources','import_records','geographic_matches']:
    for action in ['UPDATE','DELETE']:
        TABLES.append(f"CREATE TRIGGER {table}_no_{action.lower()} BEFORE {action} ON {table} BEGIN SELECT RAISE(ABORT,'Official snapshots are immutable'); END")


def fingerprint(conn):
    """All preexisting complete rows, including JSON bytes, plus schema/triggers."""
    definitions = conn.execute("SELECT type,name,tbl_name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name").fetchall()
    rows = {}
    for (name,) in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"):
        values = conn.execute('SELECT * FROM "'+name.replace('"','""')+'"').fetchall()
        rows[name] = sorted([repr(row) for row in values])
    return {'schema':definitions,'rows':rows}


def check(conn):
    if conn.execute('PRAGMA integrity_check').fetchone()[0] != 'ok' or conn.execute('PRAGMA foreign_key_check').fetchall():
        raise ValueError('Database integrity check failed')


def inspect_version(conn):
    names={r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if not names:
        return 0
    if not {'dataset','evidence','roads'} <= names:
        raise ValueError('Unrecognized database; refusing migration')
    if 'schema_migrations' not in names:
        if names != {'dataset','evidence','roads'}:
            raise ValueError('Malformed legacy schema')
        validate_shape(conn,1)
        return 1
    versions=dict(conn.execute('SELECT version,name FROM schema_migrations'))
    expected={2:'m2-additive-v1',3:'m3-additive-v1',4:'m4-additive-v1',5:'m5-additive-v1',7:'m7-official-snapshots-v1'}
    if not versions or any(expected.get(v)!=name for v,name in versions.items()):
        raise ValueError('Unknown migration version or name')
    if set(versions) != {v for v in expected if v <= max(versions)}:
        raise ValueError('Incomplete migration history')
    validate_shape(conn,max(versions))
    return max(versions)


def validate_shape(conn,version):
    """Known markers alone are insufficient: verify every required legacy/new DDL object."""
    with sqlite3.connect(':memory:') as expected:
        expected.executescript(SCHEMA)
        for v,statements in [(2,M2_SCHEMA),(3,M3_SCHEMA),(4,M4_SCHEMA),(5,M5_SCHEMA),(7,TABLES)]:
            if v<=version:
                for statement in statements:
                    expected.execute(statement)
        normalize=lambda value:' '.join(value.split()).casefold() if value else value
        actual={r[0]:normalize(r[1]) for r in conn.execute("SELECT name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'")}
        for name,sql in expected.execute("SELECT name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'"):
            if actual.get(name)!=normalize(sql):
                raise ValueError('Malformed schema or missing immutable constraint; refusing migration')


def migrate(path: Path, backup: Path, inject_failure=False):
    if path.resolve() == backup.resolve() or backup.exists():
        raise ValueError('Backup must be a new distinct file')
    if not path.exists():
        path.parent.mkdir(parents=True,exist_ok=True)
    conn=sqlite3.connect(path,timeout=2)
    try:
        conn.execute('PRAGMA foreign_keys=ON')
        version=inspect_version(conn)
        check(conn)
        if version==7:
            # Verify readiness even when marker exists.
            conn.execute('SELECT snapshot_id FROM import_records LIMIT 1')
            return {'status':'already_current','version':7}
        original=fingerprint(conn)
        backup.parent.mkdir(parents=True,exist_ok=True)
        # sqlite backup includes committed WAL pages. Caller must quiesce external writers.
        backup.touch(mode=0o600,exist_ok=False)
        with sqlite3.connect(backup) as target:
            conn.backup(target)
            check(target)
            if fingerprint(target)!=original:
                raise ValueError('Backup verification failed')
        conn.execute('BEGIN IMMEDIATE')
        baseline=fingerprint(conn)
        # Detect another writer between backup and the write lock.
        if baseline != original:
            raise ValueError('Database changed since backup')
        if version < 5:
            for statement in SCHEMA.split(';'):
                if statement.strip():
                    conn.execute(statement)
            for number, statements in [(2,M2_SCHEMA),(3,M3_SCHEMA),(4,M4_SCHEMA),(5,M5_SCHEMA)]:
                for statement in statements:
                    conn.execute(statement)
                conn.execute('INSERT OR IGNORE INTO schema_migrations VALUES (?,?)',(number,f'm{number}-additive-v1'))
        for statement in TABLES:
            conn.execute(statement)
        if inject_failure:
            raise sqlite3.OperationalError('Injected migration failure')
        conn.execute("INSERT INTO schema_migrations VALUES(7,'m7-official-snapshots-v1')")
        after=fingerprint(conn)
        for name,values in baseline['rows'].items():
            if name=='schema_migrations':
                if not set(values)<=set(after['rows'][name]):
                    raise ValueError('Legacy migration rows changed')
            elif values!=after['rows'][name]:
                raise ValueError('Legacy rows changed')
        if not set(baseline['schema'])<=set(after['schema']):
            raise ValueError('Legacy schema changed')
        check(conn)
        conn.commit()
        return {'status':'migrated','version':7,'backup':str(backup),
            'legacy_fingerprint':hashlib.sha256(json.dumps(original,sort_keys=True).encode()).hexdigest()}
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
