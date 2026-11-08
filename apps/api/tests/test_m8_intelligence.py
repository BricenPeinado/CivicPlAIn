"""Source-shaped SYNTHETIC test evidence in disposable DBs; never municipal review."""
import copy
import sqlite3
import pytest
from fastapi.testclient import TestClient
from app.core.config import Settings
from app.main import create_app
from app.core.municipal_repository import MunicipalRepository
from app.core.intelligence_repository import IntelligenceRepository
from app.models.migrations import migrate, fingerprint, inspect_version
from app.services.road_intelligence import build_overlay, stage_overlay
from app.services.municipal_data import digest
from app.ingestion.pipeline import publish
from test_m7_ingestion import staged, municipal_db
from test_m7_api import client


def build(s):
    return build_overlay(s['snapshot_id'],s['manifest'],[r for r in s['records'] if r['kind']=='road'],
                         [r for r in s['records'] if r['kind']=='condition'],[])


def review(bundle):
    a=next(a for a in bundle['associations'] if a['candidate'])
    return dict(base_snapshot_id=a['base_snapshot_id'],source_record_id=a['source_record_id'],
        target_road_id=a['target_road_id'],source_record_hash=a['candidate']['source_record_hash'],
        target_record_hash=a['candidate']['target_record_hash'],candidate_hash=a['candidate_hash'],
        parameter_hash=a['parameter_hash'],status='accepted',scope='whole_road',scope_reason='SYNTHETIC TEST equal scope',
        reviewer='SYNTHETIC TEST REVIEW',reason='SYNTHETIC TEST only',evidence_refs=['synthetic-test:equal-lines'])


def test_overlay_many_targets_and_stale_reviews(staged):
    roads=[r for r in staged['records'] if r['kind']=='road']
    conditions=[r for r in staged['records'] if r['kind']=='condition']
    extra=copy.deepcopy(roads[0]);extra['id']='synthetic-second-row';roads.append(extra)
    bundle=build_overlay(staged['snapshot_id'],staged['manifest'],roads,conditions,[])
    decisions=[]
    for a in bundle['associations']:
        d=review({'associations':[a]});decisions.append(d)
    accepted=build_overlay(staged['snapshot_id'],staged['manifest'],roads,conditions,decisions)
    assert accepted['report']['counts']['accepted_links']==2
    assert accepted['report']['counts']['accepted_observations']==1
    assert accepted['report']['counts']['accepted_road_rows']==2
    assert accepted==build_overlay(staged['snapshot_id'],staged['manifest'],roads[::-1],conditions,decisions[::-1])
    for field in ['source_record_hash','target_record_hash','candidate_hash','parameter_hash']:
        bad=copy.deepcopy(decisions);bad[0][field]='0'*64
        with pytest.raises(ValueError):
            build_overlay(staged['snapshot_id'],staged['manifest'],roads,conditions,bad)
    with pytest.raises(ValueError,match='Duplicate'):
        build_overlay(staged['snapshot_id'],staged['manifest'],roads,conditions,decisions+decisions)


@pytest.mark.parametrize('start',[0,1,2,3,4,5,7])
def test_explicit_schema8_preservation_backup_failure_recovery(tmp_path,start):
    path=tmp_path/'db.sqlite3'
    if start==7:
        migrate(path,tmp_path/'initial.sqlite3')
    else:
        from app.models.database import SCHEMA, M2_SCHEMA, M3_SCHEMA, M4_SCHEMA, M5_SCHEMA
        with sqlite3.connect(path) as conn:
            if start:
                conn.executescript(SCHEMA)
                conn.execute("INSERT INTO dataset VALUES('synthetic-preservation','EXACT synthetic bytes')")
            for v,ddl in [(2,M2_SCHEMA),(3,M3_SCHEMA),(4,M4_SCHEMA),(5,M5_SCHEMA)]:
                if start>=v:
                    for statement in ddl:conn.execute(statement)
                    conn.execute('INSERT INTO schema_migrations VALUES(?,?)',(v,f'm{v}-additive-v1'))
    with sqlite3.connect(path) as conn:before=fingerprint(conn)
    with pytest.raises(sqlite3.OperationalError):
        migrate(path,tmp_path/'failed-backup.sqlite3',target_version=8,inject_failure=True)
    with sqlite3.connect(path) as conn:assert fingerprint(conn)==before
    with sqlite3.connect(tmp_path/'failed-backup.sqlite3') as conn:assert fingerprint(conn)==before
    backup=tmp_path/'good-backup.sqlite3'
    assert migrate(path,backup,target_version=8)['version']==8
    assert backup.stat().st_mode & 0o777 == 0o600
    with sqlite3.connect(path) as conn:
        assert inspect_version(conn)==8
        after=fingerprint(conn)
        assert set(before['schema']) <= set(after['schema'])
        for table,rows in before['rows'].items():
            assert set(rows) <= set(after['rows'][table])
    assert migrate(path,tmp_path/'unused',target_version=8)['status']=='already_current'
    assert migrate(path,tmp_path/'unused7')['version']==8  # no downgrade
    with sqlite3.connect(path) as conn:
        conn.execute('DROP TRIGGER road_associations_no_delete')
    with pytest.raises(ValueError,match='Malformed'):
        migrate(path,tmp_path/'bad-shape',target_version=8)


def test_production_overlay_rejects_synthetic_harness(municipal_db):
    path,s=municipal_db
    with pytest.raises(ValueError,match='Synthetic'):
        stage_overlay(MunicipalRepository(path),s['snapshot_id'],[])


def test_atomic_overlay_publication_and_read_api_preserve_base(tmp_path,staged,monkeypatch):
    # Tests the adapter's source-shaped DTO branch in isolation. Fixture metadata declares
    # synthetic_fixture=True; this DB/review is never shipped, activated or used as coverage.
    path=tmp_path/'synthetic-dto-harness.sqlite3'
    migrate(path,tmp_path/'backup',target_version=8)
    publish(path,staged,staged['report']['report_hash'])
    base=MunicipalRepository(path)
    # Production staging rejects the synthetic query marker. Inject only the pure
    # builder for this transaction/read-boundary component test; no CLI can do this.
    with pytest.raises(ValueError,match='Synthetic'):
        stage_overlay(base,staged['snapshot_id'],[])
    import app.services.road_intelligence as intelligence
    def synthetic_builder(repository,sid,decisions):
        return build_overlay(sid,repository.snapshot(sid),repository.records(sid,'road'),repository.records(sid,'condition'),decisions)
    monkeypatch.setattr(intelligence,'stage_overlay',synthetic_builder)
    bundle=synthetic_builder(base,staged['snapshot_id'],[])
    d=review(bundle)
    bundle=synthetic_builder(base,staged['snapshot_id'],[d])
    repository=IntelligenceRepository(path)
    with sqlite3.connect(path) as conn:before=fingerprint(conn)
    with pytest.raises(ValueError,match='Injected'):
        repository.publish(bundle,bundle['report']['report_hash'],inject_failure=True)
    with sqlite3.connect(path) as conn:assert fingerprint(conn)==before
    with pytest.raises(ValueError,match='Unapproved'):
        repository.publish(bundle,'0'*64)
    assert repository.publish(bundle,bundle['report']['report_hash'])['status']=='published'
    assert repository.publish(bundle,bundle['report']['report_hash'])['status']=='unchanged'
    with sqlite3.connect(path) as conn:
        after=fingerprint(conn)
        for table,rows in before['rows'].items():
            if table not in {'intelligence_releases','road_associations'}:assert after['rows'][table]==rows
        for table in ['intelligence_releases','road_associations']:
            for action in ['DELETE FROM','UPDATE']:
                with pytest.raises(sqlite3.IntegrityError):
                    conn.execute(f'{action} {table}' + (' SET id=id' if action=='UPDATE' else ''))
    sid=staged['snapshot_id'];rid=bundle['report']['release_id'];road=d['target_road_id']
    with TestClient(create_app(Settings(database_path=path))) as c:
        assert c.get('/api/v2/intelligence-releases',params={'snapshot_id':sid}).json()['data'][0]['id']==rid
        assert c.get(f'/api/v2/intelligence-releases/{rid}',params={'snapshot_id':sid}).status_code==200
        params={'snapshot_id':sid,'release_id':rid}
        assert c.get('/api/v2/road-associations',params=params|{'status':'accepted'}).json()['meta']['total_matching']==1
        url=f'/api/v2/road-segments/{road}/condition-summary'
        response=c.get(url,params=params|{'as_of_date':'2026-01-11','stale_after_days':5})
        result=response.json()['data'];assert response.status_code==200
        assert result['rating']=='7.52' and result['category']=='unknown' and result['stale']
        assert result['intelligence_release_id']==rid and result['history'][0]['association_id']
        assert c.get(url,params=params|{'as_of_date':'2026-01-11','release_id':'missing'}).status_code==404
        assert c.get('/api/v2/road-associations',params=params|{'status':'fake'}).status_code==422
        assert c.post('/api/v2/road-associations',json={}).status_code==405
        for scope,count in [('all',1),('current',1),('historical',0),('unaccepted',0)]:
            response=c.get('/api/v2/conditions',params=params|{'assessment_scope':scope,'as_of_date':'2026-01-11'})
            assert response.status_code==200 and response.json()['meta']['total_matching']==count
            assert response.json()['meta']['intelligence_release_id']==rid
        assert c.get('/api/v2/conditions',params=params|{'assessment_scope':'current','as_of_date':'2025-01-01'}).json()['data']==[]
        assert c.get('/api/v2/conditions',params=params|{'assessment_scope':'current'}).status_code==422
        assert c.get('/api/v2/conditions',params=params|{'assessment_scope':'invented'}).status_code==422
        assert c.get('/api/v2/conditions',params=params|{'release_id':'missing'}).status_code==404



def test_summary_strict_boundary_and_schema7_compatibility(client):
    c,s=client;road=next(r for r in s['records'] if r['kind']=='road')
    url=f"/api/v2/road-segments/{road['id']}/condition-summary"
    params={'snapshot_id':s['snapshot_id'],'as_of_date':'2026-01-11'}
    a=c.get(url,params=params)
    assert a.status_code==200 and a.json()['data']['rating'] is None
    assert a.json()['data']['stale'] is None
    assert a.json()['data']==c.get(url,params=params).json()['data']
    for extra in [{'as_of_date':'20260111'},{'as_of_date':'2026-02-31'},{'stale_after_days':-1},{'stale_after_days':36501},{'stale_after_days':'1.5'},{'bogus':'x'}]:
        assert c.get(url,params=params|extra).status_code==422
    assert c.get(url,params={'snapshot_id':s['snapshot_id']}).status_code==422
    assert c.get(url,params=params|{'snapshot_id':'missing'}).status_code==404
    assert c.get('/api/v2/intelligence-releases',params={'snapshot_id':s['snapshot_id']}).status_code==503


def test_schema8_preserves_saved_v1_and_committed_wal_and_busy_writer(tmp_path):
    from app.seed import seed
    from app.seed_m2 import seed_m2
    from app.seed_m3 import seed_m3
    from app.seed_m4 import seed_m4
    path=tmp_path/'saved.sqlite3'
    seed(path);seed_m2(path);seed_m3(path);seed_m4(path)
    migrate(path,tmp_path/'schema7-backup')
    writer=sqlite3.connect(path)
    writer.execute('PRAGMA journal_mode=WAL')
    writer.execute("INSERT INTO dataset VALUES('synthetic-wal','EXACT synthetic committed WAL bytes')")
    writer.commit()
    before=fingerprint(writer)
    writer.execute('BEGIN IMMEDIATE')
    try:
        with pytest.raises(sqlite3.OperationalError,match='locked'):
            migrate(path,tmp_path/'busy-backup',target_version=8)
    finally:writer.rollback()
    assert fingerprint(writer)==before
    backup=tmp_path/'private-backup'
    migrate(path,backup,target_version=8)
    with sqlite3.connect(backup) as conn:assert fingerprint(conn)==before
    after=fingerprint(writer)
    for table,rows in before['rows'].items():
        if table!='schema_migrations':assert after['rows'][table]==rows
    writer.close()
    with pytest.raises(ValueError,match='new distinct'):
        migrate(path,backup,target_version=8)
