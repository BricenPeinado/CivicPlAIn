import sqlite3

import pytest

from app.models.database import SCHEMA, M2_SCHEMA, M3_SCHEMA, M4_SCHEMA, M5_SCHEMA, connection
from app.models.migrations import migrate, fingerprint
from app.seed import seed
from app.seed_m4 import seed_m4
from app.seed_m2 import seed_m2
from app.seed_m3 import seed_m3


@pytest.mark.parametrize('version',[0,1,2,3,4,5])
def test_all_legacy_versions_preserve_rows_schema_and_private_backup(tmp_path,version):
    path=tmp_path/'source.sqlite3'
    with sqlite3.connect(path) as conn:
        if version:
            conn.executescript(SCHEMA)
            conn.execute("INSERT INTO dataset VALUES('legacy','raw JSON bytes preserved')")
        for v,ddl in [(2,M2_SCHEMA),(3,M3_SCHEMA),(4,M4_SCHEMA),(5,M5_SCHEMA)]:
            if version>=v:
                for statement in ddl:
                    conn.execute(statement)
                conn.execute('INSERT INTO schema_migrations VALUES(?,?)',(v,f'm{v}-additive-v1'))
        before=fingerprint(conn)
    backup=tmp_path/'private-backup.sqlite3'
    result=migrate(path,backup)
    assert result['version']==7 and backup.stat().st_mode&0o777==0o600
    with sqlite3.connect(backup) as conn:
        assert fingerprint(conn)==before
    with sqlite3.connect(path) as conn:
        after=fingerprint(conn)
        assert set(before['schema'])<=set(after['schema'])
        for table,rows in before['rows'].items():
            assert set(rows)<=set(after['rows'][table])
    assert migrate(path,tmp_path/'never-created.sqlite3')['status']=='already_current'
    assert not (tmp_path/'never-created.sqlite3').exists()


def test_complete_saved_synthetic_work_preserved_and_wal_backed_up(tmp_path):
    path=tmp_path/'saved.sqlite3'
    seed(path)
    seed_m2(path)
    seed_m3(path)
    seed_m4(path)
    writer=sqlite3.connect(path)
    writer.execute('PRAGMA journal_mode=WAL')
    writer.execute("INSERT INTO dataset VALUES ('wal-preservation','synthetic test committed WAL record')")
    writer.commit()
    before=fingerprint(writer)
    assert path.with_name(path.name+'-wal').exists()
    migrate(path,tmp_path/'backup.sqlite3')
    with sqlite3.connect(tmp_path/'backup.sqlite3') as backup:
        assert fingerprint(backup)==before
    writer.close()
    with sqlite3.connect(path) as conn:
        after=fingerprint(conn)
        for table,rows in before['rows'].items():
            if table!='schema_migrations':
                assert rows==after['rows'][table]
        assert set(before['schema'])<=set(after['schema'])


@pytest.mark.parametrize('version',[0,1,5])
def test_injected_failure_rolls_back_all_schema_changes(tmp_path,version):
    path=tmp_path/'source.sqlite3'
    if version==5:
        seed(path)
    else:
        with sqlite3.connect(path) as conn:
            if version==1:
                conn.executescript(SCHEMA)
    with sqlite3.connect(path) as conn:
        before=fingerprint(conn)
    with pytest.raises(sqlite3.OperationalError):
        migrate(path,tmp_path/'backup.sqlite3',inject_failure=True)
    with sqlite3.connect(path) as conn:
        assert fingerprint(conn)==before


def test_future_version_and_existing_backup_rejected(tmp_path):
    path=tmp_path/'source.sqlite3'
    seed(path)
    with sqlite3.connect(path) as conn:
        conn.execute("INSERT INTO schema_migrations VALUES(999,'future')")
    backup=tmp_path/'backup.sqlite3'
    with pytest.raises(ValueError,match='Unknown'):
        migrate(path,backup)
    assert not backup.exists()
    backup.touch()
    with pytest.raises(ValueError,match='new distinct'):
        migrate(path,backup)


def test_malformed_marker_schema_and_busy_writer_fail_closed(tmp_path):
    path=tmp_path/'db.sqlite3'
    seed(path)
    with sqlite3.connect(path) as conn:
        conn.execute('DROP TRIGGER estimates_no_delete')
    with pytest.raises(ValueError,match='Malformed'):
        migrate(path,tmp_path/'no-backup.sqlite3')
    assert not (tmp_path/'no-backup.sqlite3').exists()
    # Restore through the existing idempotent initializer; test only, never runtime repair.
    from app.models.database import initialize
    initialize(path)
    writer=sqlite3.connect(path)
    writer.execute('BEGIN IMMEDIATE')
    try:
        with pytest.raises(sqlite3.OperationalError,match='locked'):
            migrate(path,tmp_path/'busy-backup.sqlite3')
    finally:
        writer.rollback()
        writer.close()
    with sqlite3.connect(path) as conn:
        assert conn.execute('SELECT max(version) FROM schema_migrations').fetchone()[0]==5
