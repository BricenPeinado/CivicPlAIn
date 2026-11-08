"""Explicitly synthetic source-shaped examples; no network or real municipal claims."""
import copy
import json
from pathlib import Path

import pytest
from pyproj import Transformer
from shapely.geometry import shape

from app.ingestion.adapters import adapt, normalize
from app.ingestion.acquire import fetch, json_fetch, paged_socrata
from app.ingestion.pipeline import stage, publish, CAPABILITIES
from app.ingestion.registry import SOURCES, PILOT, CONTEXT, SCHEMAS, STUDY_AREA
from app.models.migrations import migrate
from app.models.database import connection
from app.schemas.municipal import MunicipalRecord
from app.services.municipal_data import canonical, candidate_matches, digest


def lion():
    project=Transformer.from_crs(4326,2263,always_xy=True)
    return {'attributes':{'OBJECTID':1,'SegmentID':'0000001','Street':'SYNTHETIC TEST STREET',
        'StreetCode':'100001','FeatureTyp':'0','LBoro':1,'RBoro':1,'NodeIDFrom':'001','NodeIDTo':'002'},
        'geometry':{'paths':[[list(project.transform(-74.01,40.712)),list(project.transform(-74.009,40.712))]]}}


def pavement():
    return {'source_row_id':'synthetic-row-1','oftcode':'100001100002100003','boroughname':'Manhattan','onstreetna':'SYNTHETIC TEST STREET',
        'fromstreet':'SYNTHETIC FROM','tostreet':'SYNTHETIC TO','direction':'East','road_type':'Main',
        'ismultipass':'0','systemrating':'7.52','inspection':'2026-01-01T12:30:00.000',
        'the_geom':{'type':'MultiLineString','coordinates':[[[-74.01,40.712],[-74.009,40.712]]]}}


def permit():
    return {'permitnumber':'SYNTHETIC-0001','boroughname':'Manhattan','oftcode':'100001100002100003',
        'onstreetname':'SYNTHETIC TEST STREET','issuedworkstartdate':'2026-01-01T00:00:00.000',
        'issuedworkenddate':'2026-02-01T23:59:59.000','permitstatusshortdesc':'ISSUED',
        'wkt':'POINT(999999 200000)','locationgeometry':'Point'}


def context():
    return {'source_id':'0001','the_geom':{'type':'MultiLineString','coordinates':[[[-74.01,40.71],[-74.009,40.71]]]}}


def fixture_bundle(tmp_path):
    """Mocks downloaded bytes. Never used for the real import or tracked as official extract."""
    folder=tmp_path/'raw'
    folder.mkdir()
    bundle={'format':'civicplain-nyc-acquisition-1','bbox':PILOT,'context_bbox':CONTEXT,
        'permit_since':'2026-01-01','retrieved_at':'2026-01-02T00:00:00+00:00','terms':{},'sources':{}}
    for kind,row in [('lion',lion()),('pavement',pavement()),('permits',permit()),('context',context())]:
        p=folder/kind
        p.mkdir()
        payload={'features':[row]} if kind=='lion' else [row]
        raw=canonical(payload).encode()
        (p/'page-000000.json').write_bytes(raw)
        meta={'fields':[{'name':n,'type':t} for n,t in SCHEMAS[kind]]} if kind=='lion' else {'columns':[{'fieldName':n,'dataTypeName':t} for n,t in SCHEMAS[kind]]}
        import hashlib
        bundle['sources'][kind]={'rows':[row],'metadata':meta,'source':SOURCES[kind],
            'files':{'page-000000.json':hashlib.sha256(raw).hexdigest()},'source_updated_at':1,
            'query':{'synthetic_fixture':True},'schema_fingerprint':digest(SCHEMAS[kind]),
            'dictionary_sha256':'synthetic-test-only','license':{'identifier':None,'terms':{}}}
    path=folder/'acquisition.json'
    path.write_text(canonical(bundle))
    return path


@pytest.fixture
def staged(tmp_path):
    return stage(fixture_bundle(tmp_path))


def synthetic_test_stage(staged):
    """Keep isolated SQL/API harness records explicitly classified synthetic_fixture."""
    result=copy.deepcopy(staged)
    for r in result['records']:
        r['classification']='synthetic_fixture'
        r['contains_synthetic']=True
        r['field_classifications']={k:'synthetic_fixture' if v is not None else 'unknown' for k,v in r['values'].items()}
    result['manifest']['content_hash']=digest({'records':result['records'],'matches':result['matches']})
    result['manifest_hash']=digest(result['manifest'])
    result['snapshot_id']='nyc-'+result['manifest_hash'][:32]
    result['report']['snapshot_id']=result['snapshot_id']
    result['report']['manifest_hash']=result['manifest_hash']
    result['report']['report_hash']=digest({k:v for k,v in result['report'].items() if k!='report_hash'})
    return result


@pytest.fixture
def municipal_db(tmp_path,staged):
    path=tmp_path/'test.sqlite3'
    migrate(path,tmp_path/'backup.sqlite3')
    staged=synthetic_test_stage(staged)
    publish(path,staged,staged['report']['report_hash'])
    return path,staged


def test_native_feet_crs_and_leading_zero_ids():
    road=adapt('lion',lion(),'dcp-lion-arcgis:test')
    point=shape(road['geometry']).geoms[0].coords[0]
    assert point==pytest.approx((-74.01,40.712),abs=1e-8)
    assert road['source_record_key']=='0000001:1'
    assert road['raw_identifiers']['segment_id']=='0000001'
    assert road['lineage']['raw_geometry']==lion()['geometry']
    assert road['values']['utility_depth_m'] is None


def test_decimal_rating_inspection_no_invented_category():
    r=adapt('pavement',pavement(),'6yyb-pb25:test')
    assert r['values']['rating']=='7.52'
    assert r['values']['inspection_at']=='2026-01-01T12:30:00.000'
    assert r['values']['official_category'] is None
    assert r['field_classifications']['official_category']=='unknown'
    assert r['raw_identifiers']['oftcode']=='100001100002100003'


def test_permit_unknown_crs_missing_dates_and_not_work_schedule():
    row=permit()
    del row['issuedworkstartdate']
    r=adapt('permits',row,'tqtj-sjs8:test')
    assert r['geometry'] is None and r['bbox'] is None
    assert r['values']['valid_from'] is None
    assert r['values']['work_started'] is None
    assert r['lineage']['raw_wkt']==row['wkt']
    assert r['classification']=='imported_administrative_record'


@pytest.mark.parametrize('change',[{'oftcode':'123'},{'issuedworkenddate':'2025-01-01T00:00:00'}, {'permitnumber':None}, {'oftcode':123}])
def test_bad_identifiers_and_intervals_quarantined(change):
    rows,rejects,_,_=normalize('permits',[permit()|change],'tqtj-sjs8:test')
    assert not rows and len(rejects)==1


@pytest.mark.parametrize('g',[
    {'type':'LineString','coordinates':[[-74.01,40.712],[-74.01,40.712]]},
    {'type':'LineString','coordinates':[[40.712,-74.01],[40.713,-74.01]]},
    {'type':'LineString','coordinates':[[float('nan'),40.712],[-74.01,40.713]]},
    {'type':'Polygon','coordinates':[[[-74.01,40.71],[-74,40.72],[-74.01,40.72],[-74,40.71],[-74.01,40.71]]]},
])
def test_invalid_geometry_quarantined(g):
    rows,rejects,_,_=normalize('pavement',[pavement()|{'the_geom':g}],'6yyb-pb25:test')
    assert not rows and rejects


def test_duplicate_exact_and_conflicting_records():
    rows,rejects,duplicates,_=normalize('pavement',[pavement(),pavement()],'6yyb-pb25:test')
    assert len(rows)==1 and not rejects and duplicates==1
    rows,rejects,duplicates,_=normalize('pavement',[pavement(),pavement()|{'systemrating':'8.1'}],'6yyb-pb25:test')
    assert len(rows)==1 and len(rejects)==1


def test_candidate_ambiguity_never_auto_accepts_and_review_is_bound(staged):
    assert all(m['target_road_id'] is None for m in staged['matches'])
    assert all(m['status']=='ambiguous' for m in staged['matches'])
    road=next(r for r in staged['records'] if r['kind']=='road')
    source=next(r for r in staged['records'] if r['kind']=='condition')
    decisions={source['id']:{'road_id':road['id'],'record_hash':digest(source),'reviewer':'Synthetic test reviewer','reason':'Synthetic test decision'}}
    result=candidate_matches(staged['records'],decisions)
    assert next(m for m in result if m['source_record_id']==source['id'])['status']=='matched'
    source['values']['rating']='4'
    with pytest.raises(ValueError,match='Stale'):
        candidate_matches(staged['records'],decisions)


def test_unmatched_missing_keys_retained():
    row=permit()|{'oftcode':None}
    r=adapt('permits',row,'tqtj-sjs8:test')
    match=candidate_matches([r],{})[0]
    assert match['status']=='unmatched' and match['candidates']==[]


def test_offline_stage_reproducible_clock_independent_and_evidence_tamper(tmp_path):
    path=fixture_bundle(tmp_path)
    first=stage(path)
    bundle=json.loads(path.read_text())
    bundle['retrieved_at']='2026-06-01T00:00:00+00:00'
    path.write_text(canonical(bundle))
    assert stage(path)['snapshot_id']==first['snapshot_id']
    (path.parent/'lion/page-000000.json').write_text('[]')
    with pytest.raises(ValueError,match='checksum'):
        stage(path)


def test_idempotent_refresh_and_immutable_source_provenance(municipal_db):
    db,staged=municipal_db
    assert publish(db,staged,staged['report']['report_hash'])['status']=='unchanged'
    with connection(db) as conn:
        assert conn.execute('SELECT count(*) FROM import_records').fetchone()[0]==4
        assert conn.execute('SELECT count(*) FROM import_runs').fetchone()[0]==1
        source=json.loads(conn.execute('SELECT payload FROM source_revisions LIMIT 1').fetchone()[0])
        assert source['dictionary_sha256'] and source['source_url'] and source['retrieved_at']
        import sqlite3
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("UPDATE import_records SET payload='{}'")


def test_wrong_approval_and_tampered_stage_no_writes(municipal_db):
    db,staged=municipal_db
    with pytest.raises(ValueError,match='approval'):
        publish(db,staged,'wrong')
    staged['records'][0]['values']['cost']='123'
    with pytest.raises(ValueError):
        publish(db,staged,staged['report']['report_hash'])


def test_fetch_rejects_unapproved_urls_without_network(tmp_path):
    for url in ['http://data.cityofnewyork.us/a','https://example.com','https://data.cityofnewyork.us:9999/a','https://u:p@data.cityofnewyork.us/a']:
        with pytest.raises(ValueError,match='Unapproved'):
            fetch(url,tmp_path/'out')


def test_html_and_error_json_rejected(monkeypatch,tmp_path):
    import app.ingestion.acquire as module
    monkeypatch.setattr(module,'fetch',lambda *args:b'<html>not json</html>')
    with pytest.raises(ValueError,match='JSON'):
        json_fetch('unused',tmp_path/'out')
    monkeypatch.setattr(module,'fetch',lambda *args:b'{"error":true}')
    with pytest.raises(ValueError,match='API error'):
        json_fetch('unused',tmp_path/'out')


def test_truncated_page_and_cap_fail_closed(monkeypatch,tmp_path):
    import app.ingestion.acquire as module
    def fake(url,path):
        return [{'count':'2'}] if 'count' in url else [permit()]
    monkeypatch.setattr(module,'json_fetch',fake)
    with pytest.raises(ValueError,match='Truncated'):
        paged_socrata('permits','test',tmp_path,5)
    with pytest.raises(ValueError,match='cap'):
        paged_socrata('permits','test',tmp_path,1)


def test_source_change_creates_snapshot_old_is_retained(municipal_db,tmp_path):
    db,first=municipal_db
    second=copy.deepcopy(first)
    # A new reviewed decision is a new content snapshot, never an in-place refresh.
    second['matches'][0]['reason']='Synthetic revised review rationale'
    second['manifest']['content_hash']=digest({'records':second['records'],'matches':second['matches']})
    second['manifest_hash']=digest(second['manifest'])
    second['snapshot_id']='nyc-'+second['manifest_hash'][:32]
    second['report']['snapshot_id']=second['snapshot_id']
    second['report']['manifest_hash']=second['manifest_hash']
    second['report']['report_hash']=digest({k:v for k,v in second['report'].items() if k!='report_hash'})
    result=publish(db,second,second['report']['report_hash'])
    assert result['status']=='published' and result['snapshot_id']!=first['snapshot_id']
    with connection(db) as conn:
        assert conn.execute('SELECT count(*) FROM data_snapshots').fetchone()[0]==2
        assert conn.execute('SELECT count(*) FROM import_records WHERE snapshot_id=?',(first['snapshot_id'],)).fetchone()[0]==4


def test_atomic_publish_rolls_back_bad_match_reference(municipal_db):
    import sqlite3
    db,first=municipal_db
    second=copy.deepcopy(first)
    # Typed valid accepted link whose record reference is missing, to exercise SQL rollback.
    second['matches'][0].update(target_road_id='missing-road',status='matched',confidence='human_reviewed',
        candidates=[{'road_id':'missing-road'}],decision={'reviewer':'synthetic test'})
    second['manifest']['content_hash']=digest({'records':second['records'],'matches':second['matches']})
    second['manifest_hash']=digest(second['manifest'])
    second['snapshot_id']='nyc-'+second['manifest_hash'][:32]
    second['report']['snapshot_id']=second['snapshot_id']
    second['report']['manifest_hash']=second['manifest_hash']
    second['report']['report_hash']=digest({k:v for k,v in second['report'].items() if k!='report_hash'})
    with pytest.raises(sqlite3.IntegrityError):
        publish(db,second,second['report']['report_hash'])
    with connection(db) as conn:
        assert conn.execute('SELECT count(*) FROM data_snapshots').fetchone()[0]==1
        assert conn.execute('SELECT count(*) FROM import_records').fetchone()[0]==4


def test_schema_drift_blocks_stage_without_database_writes(tmp_path):
    path=fixture_bundle(tmp_path)
    bundle=json.loads(path.read_text())
    bundle['sources']['pavement']['metadata']['columns'].append({'fieldName':'unreviewed_new_field','dataTypeName':'text'})
    path.write_text(canonical(bundle))
    with pytest.raises(ValueError,match='Unreviewed'):
        stage(path)


def test_missing_rating_and_inspection_remain_unknown_not_retrieval_date():
    row=pavement()
    del row['systemrating']
    del row['inspection']
    row['nonratingreason']='Construction'
    r=adapt('pavement',row,'6yyb-pb25:test')
    assert r['values']['rating'] is None and r['values']['inspection_at'] is None
    assert r['values']['non_rating_reason']=='Construction'
    assert r['field_classifications']['rating']=='unknown' and r['unknown_reasons']['inspection_at']


def test_polygon_topology_and_coordinate_dimension_validation():
    r=adapt('permits',permit(),'tqtj-sjs8:test')
    r['geometry']={'type':'Polygon','coordinates':[[[-74.01,40.71],[-74,40.71],[-74,40.72],[-74.01,40.72],[-74.01,40.71]]]}
    r['bbox']=[-74.01,40.71,-74,40.72]
    assert MunicipalRecord.model_validate(r).geometry is not None
    r['geometry']['coordinates'][0]=[[-74.01,40.71],[-74,40.72],[-74.01,40.72],[-74,40.71],[-74.01,40.71]]
    with pytest.raises(ValueError,match='Invalid'):
        MunicipalRecord.model_validate(r)
