"""Authored miniature synthetic read model; no redistributed official extracts."""
import hashlib
import json
import sqlite3
import pytest
from fastapi.testclient import TestClient
from app.core.config import Settings
from app.main import create_app

SID = 'nyc-' + 'a'*32

@pytest.fixture
def artifact(tmp_path):
    path=tmp_path/'standardized.sqlite3'
    with sqlite3.connect(path) as c:
        c.executescript('''
        CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT);
        CREATE TABLE roads(road_id TEXT PRIMARY KEY,street_key TEXT,street_name TEXT,segment_id TEXT,object_id TEXT,geometry_json TEXT,source_revision_id TEXT);
        CREATE TABLE streets(street_key TEXT PRIMARY KEY,observations INTEGER,permits_on_street INTEGER,latest_rating REAL,latest_inspection_at TEXT,display_condition TEXT,display_basis TEXT);
        CREATE TABLE pavement_observations(observation_id TEXT PRIMARY KEY,street_key TEXT,on_street TEXT,from_street TEXT,to_street TEXT,rating REAL,display_condition TEXT,inspection_at TEXT,geometry_json TEXT,source_revision_id TEXT,source_row_key TEXT,non_rating_reason TEXT);
        CREATE TABLE permits(permit_id TEXT PRIMARY KEY,on_street_key TEXT,on_street TEXT,from_street TEXT,to_street TEXT,permit_number TEXT,permit_type TEXT,permit_status TEXT,issue_date TEXT,valid_from TEXT,valid_to TEXT,source_revision_id TEXT);
        CREATE VIEW road_profiles AS SELECT r.*,s.observations AS street_observation_count,s.permits_on_street,s.latest_rating,s.latest_inspection_at,s.display_condition,s.display_basis FROM roads r JOIN streets s USING(street_key);
        CREATE VIEW road_pavement_by_name AS SELECT r.road_id,o.*, 'on_street_name' AS association_basis FROM roads r JOIN pavement_observations o USING(street_key);
        CREATE VIEW road_permits_by_name AS SELECT r.road_id,p.*, 'on_street_name' AS association_basis FROM roads r JOIN permits p ON p.on_street_key=r.street_key;
        ''')
        c.executemany('INSERT INTO metadata VALUES(?,?)', [('source_snapshot',json.dumps(SID)),('dataset_kind',json.dumps('derived_read_only_road_lookup'))])
        for road,key,count,permits,rating,band in [('road-a','TEST STREET',3,2,4.91,'Fair'),('road-b','EMPTY STREET',0,0,None,'Unknown')]:
            c.execute('INSERT INTO roads VALUES(?,?,?,?,?,?,?)',(road,key,key,'001','1',json.dumps({'type':'LineString','coordinates':[[-74,40.7],[-74,40.71]]}),'synthetic-source'))
            c.execute('INSERT INTO streets VALUES(?,?,?,?,?,?,?)',(key,count,permits,rating,'2026-01-01' if rating else None,band,'Synthetic fixture only'))
        for i in range(3):
            c.execute('INSERT INTO pavement_observations VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(f'obs-{i}','TEST STREET','TEST STREET','A','B',4.91,'Fair','2026-01-01',None,'synthetic-source',str(i),None))
        for i in range(3):
            c.execute('INSERT INTO permits VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(f'permit-{i}','TEST STREET' if i<2 else 'OTHER STREET','TEST STREET' if i<2 else 'OTHER STREET','TEST STREET','B',f'TEST-{i}','SYNTHETIC','TEST','2026-01-01',None,None,'synthetic-source'))
    return path


def client(tmp_path,path):
    return TestClient(create_app(Settings(database_path=tmp_path/'app.sqlite3',standardized_database_path=path)))


def test_profile_pagination_cross_street_exclusion_and_readonly(artifact,tmp_path):
    before=hashlib.sha256(artifact.read_bytes()).hexdigest()
    with client(tmp_path,artifact) as c:
        root='/api/v2/standardized/roads/road-a';p={'snapshot_id':SID}
        profile=c.get(root,params=p).json()['data']
        assert (profile['latest_rating'],profile['display_condition'],profile['street_observation_count'],profile['permits_on_street'])==(4.91,'Fair',3,2)
        ids=[]
        for offset in range(3):
            r=c.get(root+'/pavement',params=p|{'limit':1,'offset':offset});assert r.status_code==200,r.text
            body=r.json();ids.extend(row['observation_id'] for row in body['data'])
            assert body['meta']['next_offset']==(offset+1 if offset<2 else None)
            assert body['meta']['verified_segment_condition'] is False
        assert ids==['obs-0','obs-1','obs-2']
        permits=c.get(root+'/permits',params=p).json()
        assert permits['meta']['total_matching']==2
        assert {v['permit_id'] for v in permits['data']}=={'permit-0','permit-1'}
        assert all(v['road_id']=='road-a' for v in permits['data'])
        empty=c.get('/api/v2/standardized/roads/road-b/pavement',params=p).json()
        assert empty['data']==[] and empty['meta']['total_matching']==0
        assert c.get('/api/v2/standardized/roads/missing',params=p).status_code==404
        assert c.get(root,params={'snapshot_id':'nyc-'+'b'*32}).status_code==409
        for invalid in [{'limit':101},{'limit':0},{'offset':-1},{'unrecognized':'x'}]:
            assert c.get(root+'/permits',params=p|invalid).status_code==422
        assert c.get(root+'?snapshot_id='+SID+'&snapshot_id='+SID).status_code==422
        assert c.post(root,params=p).status_code==405
    assert hashlib.sha256(artifact.read_bytes()).hexdigest()==before


def test_missing_and_incompatible(tmp_path,artifact):
    missing=tmp_path/'missing.sqlite3'
    with client(tmp_path,missing) as c:
        r=c.get('/api/v2/standardized/roads/road-a',params={'snapshot_id':SID})
        assert r.status_code==503 and r.json()['error']['code']=='STANDARDIZED_DATABASE_MISSING'
    assert not missing.exists()
    with sqlite3.connect(artifact) as db: db.execute('DROP VIEW road_profiles')
    with client(tmp_path,artifact) as c:
        r=c.get('/api/v2/standardized/roads/road-a',params={'snapshot_id':SID})
        assert r.status_code==503 and r.json()['error']['code']=='STANDARDIZED_DATABASE_INCOMPATIBLE'


def test_invalid_profile_data_is_explicitly_incompatible(artifact,tmp_path):
    with sqlite3.connect(artifact) as db:
        db.execute("UPDATE streets SET display_condition='unsupported' WHERE street_key='TEST STREET'")
    with client(tmp_path,artifact) as c:
        r=c.get('/api/v2/standardized/roads/road-a',params={'snapshot_id':SID})
        assert r.status_code==503 and r.json()['error']['code']=='STANDARDIZED_DATABASE_INCOMPATIBLE'


def test_map_ratings_complete_bounded_indexed_and_readonly(artifact,tmp_path):
    before=hashlib.sha256(artifact.read_bytes()).hexdigest()
    p={'snapshot_id':SID,'bbox':'-74.01,40.69,-73.99,40.72'}
    with client(tmp_path,artifact) as c:
        r=c.get('/api/v2/standardized/map-ratings',params=p)
        assert r.status_code==200,r.text
        body=r.json()
        assert [v['road_id'] for v in body['data']]==['road-a','road-b']
        assert body['data'][0]['latest_rating']==4.91
        assert body['data'][1]['latest_rating'] is None
        assert body['meta']['complete'] is True
        assert body['meta']['verified_segment_condition'] is False
        assert body['meta']['association_basis']=='on_street_name'
        assert body['meta']['map_contract']=='indicative-map-v1'
        index=c.app.state.standardized._map_index
        assert c.get('/api/v2/standardized/map-ratings',params=p).json()==body
        assert c.app.state.standardized._map_index is index
        # Boundary intersection is included; no matching geometry means a real empty result.
        assert len(c.get('/api/v2/standardized/map-ratings',params=p|{'bbox':'-74,40.71,-73.99,40.72'}).json()['data'])==2
        assert c.get('/api/v2/standardized/map-ratings',params=p|{'bbox':'-74.02,40.72,-74.01,40.73'}).json()['data']==[]
        too_many=c.get('/api/v2/standardized/map-ratings',params=p|{'limit':1})
        assert too_many.status_code==422 and too_many.json()['error']['code']=='VIEWPORT_TOO_BROAD'
        assert 'data' not in too_many.json()
        for invalid in [{'bbox':'nan,40,-73,41'},{'bbox':'-74,41,-75,40'},{'bbox':'-180,-90,180,90'},{'limit':2001},{'limit':0},{'cursor':'x'}]:
            assert c.get('/api/v2/standardized/map-ratings',params=p|invalid).status_code==422
        assert c.get('/api/v2/standardized/map-ratings',params={'snapshot_id':SID}).status_code==422
        assert c.get('/api/v2/standardized/map-ratings',params=p|{'snapshot_id':'other'}).status_code==409
        assert c.post('/api/v2/standardized/map-ratings',params=p).status_code==405
    assert hashlib.sha256(artifact.read_bytes()).hexdigest()==before


def test_map_index_replacement_and_invalid_artifacts(artifact,tmp_path):
    p={'snapshot_id':SID,'bbox':'-74.01,40.69,-73.99,40.72'}
    with client(tmp_path,artifact) as c:
        assert c.get('/api/v2/standardized/map-ratings',params=p).status_code==200
        old=c.app.state.standardized._map_index
        # Only this authored disposable test artifact is modified.
        with sqlite3.connect(artifact) as db:
            db.execute("UPDATE streets SET latest_rating=8.0,display_condition='Good'")
        r=c.get('/api/v2/standardized/map-ratings',params=p)
        assert r.json()['data'][0]['display_condition']=='Good'
        assert c.app.state.standardized._map_index is not old
        with sqlite3.connect(artifact) as db:
            db.execute("UPDATE roads SET geometry_json='{}'")
        assert c.get('/api/v2/standardized/map-ratings',params=p).status_code==503
    with client(tmp_path,tmp_path/'absent.sqlite3') as c:
        assert c.get('/api/v2/standardized/map-ratings',params=p).status_code==503
