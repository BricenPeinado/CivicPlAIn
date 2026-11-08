"""Synthetic policy/transport tests; actual pilot evidence is reported separately."""
import copy
import sqlite3
import pytest
from fastapi.testclient import TestClient

from app.services.pavement_policy import POLICY_ID, POLICY_HASH, classify
from app.services.road_conditions import summarize
from app.services.road_intelligence import build_overlay
from app.services.municipal_data import digest
from app.core.municipal_repository import MunicipalRepository
from app.core.intelligence_repository import IntelligenceRepository
from app.core.config import Settings
from app.main import create_app
from app.ingestion.pipeline import publish
from app.models.migrations import migrate, fingerprint
from test_m7_ingestion import staged, fixture_bundle
from test_m8_intelligence import review
from test_m8_conditions import inputs


@pytest.mark.parametrize('raw,rounded,category', [('0.01',0,'unknown'),('0.49',0,'unknown'),
    ('0.5',1,'poor'),('1',1,'poor'),('2.4',2,'poor'),('2.5',3,'poor'),('3',3,'poor'),
    ('3.499999',3,'poor'),('3.5',4,'fair'),('3.999',4,'fair'),('4',4,'fair'),
    ('6.8',7,'fair'),('7.0',7,'fair'),('7.4',7,'fair'),('7.499999',7,'fair'),
    ('7.5',8,'good'),('7.9',8,'good'),('8.0',8,'good'),('9.6',10,'good'),('10',10,'good')])
def test_half_up_boundaries_preserve_exact_raw_input(raw, rounded, category):
    result=classify(raw)
    assert result['raw_rating']==raw and result['rounded_rating']==rounded and result['category']==category
    assert result['policy_id']==POLICY_ID and result['policy_hash']==POLICY_HASH
    assert result['official_nyc_dot_policy'] is False and result['policy_classification']=='planning_assumption'


@pytest.mark.parametrize('raw,reason', [(None,'MISSING_RATING'),('','MISSING_RATING'),
    ('0','ZERO_RATING'),('-0','ZERO_RATING'),('-0.01','OUT_OF_RANGE_RATING'),('10.001','OUT_OF_RANGE_RATING'),
    ('abc','NONNUMERIC_RATING'),('NaN','NONFINITE_RATING'),('Infinity','NONFINITE_RATING'),
    ('-Infinity','NONFINITE_RATING'),(True,'NONNUMERIC_RATING')])
def test_unknown_reasons(raw,reason):
    result=classify(raw)
    assert result['category']=='unknown' and result['rounded_rating'] is None and result['reason']==reason


@pytest.mark.parametrize('raw',['0','7.5','10',None,'bad'])
def test_nonrating_reason_always_wins_and_is_preserved(raw):
    result=classify(raw,'Road Identification')
    assert result['category']=='unknown' and result['reason']=='NON_RATING_REASON'
    assert result['raw_rating']==raw and result['non_rating_reason']=='Road Identification'


def test_explicit_policy_keeps_v1_replay_and_eligibility_checks():
    r,m=inputs();original=copy.deepcopy(r)
    old=summarize([r],m,'road','snapshot','2026-01-11',10)
    new=summarize([r],m,'road','snapshot','2026-01-11',10,policy_id=POLICY_ID)
    assert old==summarize([r],m,'road','snapshot','2026-01-11',10)
    assert new['category']=='good' and new['rounded_rating']==8 and new['rating']=='7.52'
    assert new['method_version']=='road-condition-v2-pilot' and new['policy']['hash']==POLICY_HASH
    assert new['input_hash']!=old['input_hash'] and r==original
    assert new['stale'] is False
    m[r['id']]['status']='ambiguous'
    assert summarize([r],m,'road','snapshot','2026-01-11',policy_id=POLICY_ID)['category']=='unknown'
    m[r['id']]['status']='matched';m[r['id']]['decision']['scope']='partial'
    partial=summarize([r],m,'road','snapshot','2026-01-11',policy_id=POLICY_ID)
    assert partial['category']=='unknown' and partial['rating'] is None
    assert partial['history'][0]['grading']['category']=='good'
    assert partial['history'][0]['reason']=='PARTIAL_OR_UNREVIEWED_SCOPE'
    m[r['id']]['decision']['scope']='whole_road';r['lineage']['raw_fields']['ismultipass']='1'
    assert summarize([r],m,'road','snapshot','2026-01-11',policy_id=POLICY_ID)['category']=='unknown'
    r,m=inputs();r['values']['direction']=None
    assert summarize([r],m,'road','snapshot','2026-01-11',policy_id=POLICY_ID)['category']=='unknown'
    r,m=inputs();r['values']['rating']='0'
    zero=summarize([r],m,'road','snapshot','2026-01-11',policy_id=POLICY_ID)
    assert zero['category']=='unknown' and zero['history'][0]['grading']['raw_rating']=='0'


def test_latest_duplicate_history_and_conflict_are_not_averaged():
    r,m=inputs();older=copy.deepcopy(r);older['id']='older';older['values'].update(rating='2.4',inspection_at='2025-01-01')
    m[older['id']]=copy.deepcopy(m[r['id']])
    a=summarize([r,older],m,'road','snapshot','2026-01-11',policy_id=POLICY_ID)
    assert a['category']=='good' and a['history'][1]['grading']['category']=='poor'
    assert a==summarize([older,r,r],m,'road','snapshot','2026-01-11',policy_id=POLICY_ID)
    older['values']['inspection_at']=r['values']['inspection_at']
    assert summarize([r,older],m,'road','snapshot','2026-01-11',policy_id=POLICY_ID)['category']=='unknown'


def test_candidate_set_hash_rejects_competitor_changes(staged):
    roads=[r for r in staged['records'] if r['kind']=='road'];obs=[r for r in staged['records'] if r['kind']=='condition']
    b=build_overlay(staged['snapshot_id'],staged['manifest'],roads,obs,[])
    d=review(b);d['candidate_set_hash']=digest(sorted([a['candidate'] for a in b['associations']],key=lambda a:a['road_id']))
    accepted=build_overlay(staged['snapshot_id'],staged['manifest'],roads,obs,[d])
    assert accepted['report']['counts']['accepted_links']==1
    twin=copy.deepcopy(roads[0]);twin['id']='synthetic-duplicate-segment';roads.append(twin)
    with pytest.raises(ValueError,match='candidate-set'):
        build_overlay(staged['snapshot_id'],staged['manifest'],roads,obs,[d])


def test_explicit_policy_api_map_filters_and_cursor_context(tmp_path,staged,monkeypatch):
    path=tmp_path/'synthetic-pilot-policy.sqlite3';migrate(path,tmp_path/'backup',target_version=8)
    publish(path,staged,staged['report']['report_hash']);base=MunicipalRepository(path)
    import app.services.road_intelligence as intelligence
    import app.services.pavement_policy as policy
    # Disposable source-shaped synthetic test only, never actual pilot evidence.
    monkeypatch.setattr(policy,'PILOT_SNAPSHOT_ID',staged['snapshot_id'])
    def builder(repository,sid,decisions):
        return build_overlay(sid,repository.snapshot(sid),repository.records(sid,'road'),repository.records(sid,'condition'),decisions)
    monkeypatch.setattr(intelligence,'stage_overlay',builder)
    b=builder(base,staged['snapshot_id'],[]);d=review(b);b=builder(base,staged['snapshot_id'],[d])
    IntelligenceRepository(path).publish(b,b['report']['report_hash'])
    with sqlite3.connect(path) as conn:before=fingerprint(conn)
    sid=staged['snapshot_id'];rid=b['report']['release_id'];road=d['target_road_id']
    params={'snapshot_id':sid,'release_id':rid,'as_of_date':'2026-01-11','policy_id':POLICY_ID}
    with TestClient(create_app(Settings(database_path=path))) as c:
        response=c.get(f'/api/v2/road-segments/{road}/condition-summary',params=params)
        assert response.status_code==200,response.text
        summary=response.json()['data'];assert summary['category']=='good' and summary['rounded_rating']==8
        assert summary['rating']=='7.52' and summary['history'][0]['grading']['category']=='good'
        for category,count in [('good',1),('fair',0),('poor',0),('unknown',0)]:
            r=c.get('/api/v2/road-segments',params=params|{'condition':category})
            assert r.status_code==200 and r.json()['meta']['total_matching']==count
        r=c.get('/api/v2/road-segments/geojson',params=params|{'bbox':'-74.02,40.7,-73.985,40.725'})
        assert r.json()['features'][0]['properties']['condition_summary']['result_hash']==summary['result_hash']
        assert c.get('/api/v2/conditions',params=params|{'assessment_scope':'current'}).json()['meta']['total_matching']==1
        assert c.get('/api/v2/road-segments',params=params|{'policy_id':'invented'}).status_code==422
        assert c.get('/api/v2/road-segments',params={k:v for k,v in params.items() if k!='as_of_date'}).status_code==422
        assert c.get('/api/v2/road-segments',params={k:v for k,v in params.items() if k!='release_id'}).status_code==422
        assert c.get('/api/v2/road-segments',params=params|{'release_id':'missing'}).status_code==404
    with sqlite3.connect(path) as conn:assert fingerprint(conn)==before
