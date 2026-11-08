"""Explicitly synthetic permit evidence. Actual coverage is verified separately."""
import copy
import sqlite3
import pytest
from fastapi.testclient import TestClient
from app.core.config import Settings
from app.main import create_app
from app.core.municipal_repository import MunicipalRepository
from app.core.intelligence_repository import IntelligenceRepository
from app.models.migrations import migrate,fingerprint,inspect_version
from app.ingestion.pipeline import publish
from app.ingestion.acquire import permit_window_query
from app.services.municipal_data import digest
from app.services.permit_intelligence import build_overlay,locations,candidates,coordination,PARAMETERS
from test_m7_ingestion import staged
from test_m8_intelligence import review


def setup(s):
    return ([r for r in s['records'] if r['kind']=='road'],[r for r in s['records'] if r['kind']=='permit'],
            {r['id']:r for r in s['revisions']})


def decision(b):
    d=review(b);d['scope']='partial'
    matches=[a['candidate'] for a in b['associations'] if a['source_record_id']==d['source_record_id'] and a['candidate']]
    d['candidate_set_hash']=digest(sorted(matches,key=lambda c:c['road_id']))
    return d


def test_names_oft_duplicates_topology_never_auto_accept(staged):
    roads,permits,sources=setup(staged)
    p=permits[0];p['values']['on_street']='  test---street  '
    p['raw_identifiers']['oftcode']=None
    r=roads[0];r['values']['name']='TEST STREET'
    twin=copy.deepcopy(r);twin['id']='duplicate-segment-export-row'
    found=candidates([r,twin],permits,sources,staged['manifest']['coverage']['bbox'])[0]
    assert len(found['candidates'])==2 and found['evidence_status']=='candidate'
    assert all(c['distance_m'] is None for c in found['candidates'])
    b=build_overlay(staged['snapshot_id'],staged['manifest'],[r,twin],permits,[],sources)
    assert b['report']['counts']['accepted_links']==0
    d=decision(b);approved=build_overlay(staged['snapshot_id'],staged['manifest'],[r,twin],permits,[d],sources)
    assert approved['report']['counts']['accepted_links']==1
    assert approved==build_overlay(staged['snapshot_id'],staged['manifest'],[twin,r],permits,[d],sources)
    for field in ['source_record_hash','target_record_hash','candidate_hash','candidate_set_hash','parameter_hash']:
        bad=copy.deepcopy(d);bad[field]='0'*64
        with pytest.raises(ValueError):build_overlay(staged['snapshot_id'],staged['manifest'],[r,twin],permits,[bad],sources)
    with pytest.raises(ValueError):build_overlay(staged['snapshot_id'],staged['manifest'],[r,twin],permits,[d,d],sources)


def test_crs_unknown_outside_and_invalid_not_guessed(staged):
    roads,permits,sources=setup(staged);p=permits[0]
    p['values']['on_street']='NO KNOWN NAME';p['raw_identifiers']['oftcode']=None
    p['geometry']=None;p['bbox']=None;p['lineage']['raw_wkt']='POINT (999999 111111)'
    assert candidates(roads,permits,sources,staged['manifest']['coverage']['bbox'])[0]['evidence_status']=='invalid_evidence'
    p['lineage']['raw_wkt']=None
    assert candidates(roads,permits,sources,staged['manifest']['coverage']['bbox'])[0]['evidence_status']=='unlocated'
    p['geometry']={'type':'Point','coordinates':[-73.9,40.8]};p['bbox']=[-73.9,40.8,-73.9,40.8]
    sources[p['source_revision_id']]['source_crs']='EPSG:4326'
    assert candidates(roads,permits,sources,staged['manifest']['coverage']['bbox'])[0]['evidence_status']=='outside_coverage'
    sources[p['source_revision_id']]['source_crs']='unknown'
    assert candidates(roads,permits,sources,staged['manifest']['coverage']['bbox'])[0]['evidence_status']=='invalid_evidence'


def test_oft_endpoint_nodes_and_crossing_parallel_roads_remain_candidates(staged):
    roads,permits,sources=setup(staged);r=roads[0];p=permits[0]
    r['raw_identifiers']['street_code']='001234';r['lineage']['raw_attributes'].update(NodeIDFrom='01',NodeIDTo='02')
    cross=copy.deepcopy(r);cross['id']='cross';cross['values']['name']='CROSS STREET';cross['raw_identifiers']['street_code']='005678'
    cross['lineage']['raw_attributes'].update(NodeIDFrom='02',NodeIDTo='03')
    p['raw_identifiers']['oftcode']='001234005678005678';p['values']['from_street']='CROSS STREET';p['values']['to_street']='CROSS STREET'
    c=candidates([r,cross],permits,sources,staged['manifest']['coverage']['bbox'])[0]['candidates']
    own=next(x for x in c if x['road_id']==r['id']);assert own['from_endpoint_road_ids']==['cross']
    assert own['to_endpoint_road_ids']==['cross'] and own['grade_agreement']=='unknown'
    assert own['street_code_agrees'] and own['distance_m'] is None


@pytest.mark.parametrize('start',[0,1,2,3,4,5,7,8])
def test_additive_nine_preserves_all_old_rows_and_backup(staged,tmp_path,start):
    path=tmp_path/'db';backup=tmp_path/'backup'
    if start in {7,8}:migrate(path,tmp_path/'initial',target_version=start)
    elif start:
        from app.models.database import SCHEMA,M2_SCHEMA,M3_SCHEMA,M4_SCHEMA,M5_SCHEMA
        with sqlite3.connect(path) as c:
            c.executescript(SCHEMA)
            for v,ddl in [(2,M2_SCHEMA),(3,M3_SCHEMA),(4,M4_SCHEMA),(5,M5_SCHEMA)]:
                if v<=start:
                    for q in ddl:c.execute(q)
                    c.execute('INSERT INTO schema_migrations VALUES(?,?)',(v,f'm{v}-additive-v1'))
    with sqlite3.connect(path) as c:before=fingerprint(c)
    with pytest.raises(sqlite3.OperationalError):migrate(path,tmp_path/'failure',True,9)
    with sqlite3.connect(path) as c:assert fingerprint(c)==before
    migrate(path,backup,target_version=9)
    with sqlite3.connect(backup) as c:assert fingerprint(c)==before
    with sqlite3.connect(path) as c:
        assert inspect_version(c)==9;after=fingerprint(c)
        assert set(before['schema'])<=set(after['schema'])
        for table,rows in before['rows'].items():
            assert set(rows)<=set(after['rows'][table]) if table=='schema_migrations' else rows==after['rows'][table]
    assert migrate(path,tmp_path/'unused',target_version=9)['status']=='already_current'


def test_review_publication_api_context_coordination_read_only(staged,tmp_path,monkeypatch):
    path=tmp_path/'db';migrate(path,tmp_path/'backup',target_version=9);publish(path,staged,staged['report']['report_hash'])
    roads,permits,sources=setup(staged)
    # Pure synthetic builder is only substituted inside this disposable test.
    import app.services.permit_intelligence as service
    def stage(repo,sid,decisions):
        return build_overlay(sid,repo.snapshot(sid),repo.records(sid,'road'),repo.records(sid,'permit'),decisions,sources)
    monkeypatch.setattr(service,'stage_overlay',stage)
    r=MunicipalRepository(path);b=stage(r,staged['snapshot_id'],[]);d=decision(b);b=stage(r,staged['snapshot_id'],[d])
    i=IntelligenceRepository(path)
    with pytest.raises(ValueError):i.publish(b,'0'*64)
    with pytest.raises(ValueError):i.publish(b,b['report']['report_hash'],True)
    assert i.releases(staged['snapshot_id'],kind='permit')==[]
    assert i.publish(b,b['report']['report_hash'])['status']=='published'
    assert i.publish(b,b['report']['report_hash'])['status']=='unchanged'
    with sqlite3.connect(path) as c:before=fingerprint(c)
    with TestClient(create_app(Settings(database_path=path))) as client:
        sid=staged['snapshot_id'];params={'snapshot_id':sid,'permit_release_id':b['report']['release_id'],'evidence':'true'}
        data=client.get('/api/v2/permits',params=params).json()['data'];assert data[0]['permit_location']['status']=='located'
        pid=data[0]['id'];assert client.get('/api/v2/permits/'+pid,params=params).json()['data']['permit_location']['accepted_road_ids']==[d['target_road_id']]
        assert client.get('/api/v2/permits',params={**params,'road_id':d['target_road_id']}).json()['meta']['total_matching']==1
        assert client.get('/api/v2/permit-associations',params={'snapshot_id':sid,'release_id':b['report']['release_id'],'source_record_id':pid,'status':'accepted'}).json()['meta']['total_matching']==1
        params.pop('evidence');assert client.get('/api/v2/permit-location-coverage',params=params).json()['data']['status_counts']['located']==1
        assert client.get('/api/v2/permits/'+pid+'/coordination-candidates',params=params).json()['data']==[]
        assert client.get('/api/v2/permits',params={'snapshot_id':sid,'location_status':'bad'}).status_code==422
        assert client.get('/api/v2/permits',params={'snapshot_id':sid,'permit_release_id':'foreign'}).status_code==404
        assert client.get('/api/v2/road-associations',params={'snapshot_id':sid,'release_id':b['report']['release_id']}).status_code==404
    with sqlite3.connect(path) as c:
        assert fingerprint(c)==before
        with pytest.raises(sqlite3.IntegrityError):c.execute('DELETE FROM permit_associations')


def test_coordination_is_candidate_not_confirmed_and_handles_dates(staged):
    roads,permits,sources=setup(staged);p=permits[0];other=copy.deepcopy(p);other['id']='other';other['source_record_key']='OTHER'
    other['values'].update(valid_from='2026-01-02',valid_to='2026-01-03');p['values'].update(valid_from='2026-01-01',valid_to='2026-01-02')
    def screen():
        loc=locations(staged['snapshot_id'],staged['manifest'],roads,[p,other],sources)
        return coordination(p,[p,other],loc,staged['snapshot_id'])
    found=screen();assert len(found)==1
    assert found[0]['administrative_window_relation']=='possible_overlap' and found[0]['confirmed_conflict'] is False
    assert found[0]['spatial_basis']=='shared_candidate_road_reference' and found[0]['actual_work_overlap']=='unknown'
    other['values']['valid_from']='2026-01-03';assert screen()==[]
    other['values']['valid_from']=None;other['field_classifications']['valid_from']='unknown';other['unknown_reasons']['valid_from']='Synthetic missing date';assert screen()[0]['administrative_window_relation']=='unknown'
    other['values'].update(valid_from='2026-01-04',valid_to='2026-01-03');assert screen()[0]['administrative_window_relation']=='unknown'


def test_window_query_keeps_older_admin_records_and_no_street_name_filter():
    q=permit_window_query('2026-11-08','2026-11-09')
    assert 'issuedworkenddate' in q and 'OR (permitissuedate' in q and 'onstreetname' not in q
    for a,b in [('2026-01-02','2026-01-01'),('20260101','2026-01-02'),('2026-01-01','2026-03-01')]:
        with pytest.raises(ValueError):permit_window_query(a,b)


def test_rejected_candidates_are_visible_but_excluded_from_screening(staged):
    roads,permits,sources=setup(staged);p=permits[0]
    b=build_overlay(staged['snapshot_id'],staged['manifest'],roads,permits,[],sources)
    d=decision(b);d['status']='rejected'
    reviewed=build_overlay(staged['snapshot_id'],staged['manifest'],roads,permits,[d],sources)
    loc=locations(staged['snapshot_id'],staged['manifest'],roads,permits,sources,reviewed['associations'],reviewed['report']['release_id'])
    assert loc[p['id']]['rejected_associations'][0]['target_road_id']==d['target_road_id']
    assert all(c['road_id']!=d['target_road_id'] for c in loc[p['id']]['candidates'])
    assert loc[p['id']]['candidate_set_hash']==d['candidate_set_hash']


def test_aliases_not_invented_duplicate_permit_ids_rejected(staged):
    roads,permits,sources=setup(staged);p=permits[0]
    p['values']['on_street']='UNREVIEWED ALIAS';p['raw_identifiers']['oftcode']=None
    assert candidates(roads,permits,sources,staged['manifest']['coverage']['bbox'])[0]['candidates']==[]
    with pytest.raises(ValueError,match='Duplicate'):candidates(roads,permits+permits,sources,staged['manifest']['coverage']['bbox'])


def test_many_partial_references_and_verified_geometry_threshold(staged):
    from pyproj import Transformer
    roads,permits,sources=setup(staged);r=roads[0];p=permits[0]
    r['geometry']={'type':'LineString','coordinates':[[-74.005,40.71],[-74.005,40.711]]};r['bbox']=[-74.005,40.71,-74.005,40.711]
    twin=copy.deepcopy(r);twin['id']='parallel-test';roads=[r,twin]
    b=build_overlay(staged['snapshot_id'],staged['manifest'],roads,permits,[],sources)
    ds=[]
    for a in b['associations']:
        if a['candidate']:
            d=review({'associations':[a]});d['scope']='partial';d['candidate_set_hash']=digest(sorted([x['candidate'] for x in b['associations'] if x['candidate']],key=lambda c:c['road_id']));ds.append(d)
    accepted=build_overlay(staged['snapshot_id'],staged['manifest'],roads,permits,ds,sources)
    assert accepted['report']['counts']['accepted_links']==2
    assert accepted['report']['counts']['accepted_observations']==1
    p['values']['on_street']='NO NAME AGREEMENT';p['raw_identifiers']['oftcode']=None
    fwd=Transformer.from_crs(4326,32618,always_xy=True);inv=Transformer.from_crs(32618,4326,always_xy=True)
    x,y=fwd.transform(-74.005,40.7105);sources[p['source_revision_id']]['source_crs']='EPSG:4326'
    for offset,count in [(4.9,2),(5.1,0)]:
        lon,lat=inv.transform(x+offset,y);p['geometry']={'type':'Point','coordinates':[lon,lat]};p['bbox']=[lon,lat,lon,lat]
        assert len(candidates(roads,permits,sources,staged['manifest']['coverage']['bbox'])[0]['candidates'])==count
