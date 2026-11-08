"""Read-boundary integration against explicitly synthetic, isolated adapter records."""
import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from app.seed import seed
from test_m7_ingestion import staged, municipal_db


@pytest.fixture
def client(municipal_db):
    path,stage=municipal_db
    seed(path)
    with TestClient(create_app(Settings(database_path=path))) as client:
        yield client,stage


def test_discovery_workspace_and_v1_remains_synthetic(client):
    c,s=client
    assert c.get('/api/v2/workspace').json()['data']['mode']=='synthetic'
    snapshots=c.get('/api/v2/data-snapshots').json()
    assert snapshots['data'][0]['id']==s['snapshot_id']
    assert snapshots['meta']['snapshot_id'] is None
    assert c.get('/api/v1/health').json()['data']['data_ready']
    assert len(c.get('/api/v1/road-segments').json()['data'])==24
    r=next(r for r in s['records'] if r['kind']=='road')
    assert c.get('/api/v1/road-segments/'+r['id']).status_code==404
    assert c.post('/api/v2/permits',json={}).status_code==405


def test_official_requires_pinned_snapshot_and_no_fallback(municipal_db):
    path,s=municipal_db
    with pytest.raises(ValueError):
        Settings(database_path=path,data_mode='official')
    with pytest.raises(ValueError):
        Settings(data_mode='invalid')
    with TestClient(create_app(Settings(database_path=path,data_mode='official',official_snapshot_id=s['snapshot_id']))) as c:
        assert c.get('/api/v2/workspace').json()['data']['snapshot_id']==s['snapshot_id']
    with TestClient(create_app(Settings(database_path=path,data_mode='official',official_snapshot_id='nyc-'+'0'*32))) as c:
        assert c.get('/api/v2/workspace').status_code==404


def test_unmigrated_v2_readiness_v1_unchanged(tmp_path):
    with TestClient(create_app(Settings(database_path=tmp_path/'empty.sqlite3'))) as c:
        response=c.get('/api/v2/data-snapshots')
        assert response.status_code==503 and response.json()['error']['code']=='MIGRATION_REQUIRED'
        assert c.get('/api/v1/health').status_code==200


def test_bbox_geojson_exact_intersection_and_required_context(client):
    c,s=client
    sid=s['snapshot_id']
    params={'snapshot_id':sid}
    assert c.get('/api/v2/road-segments/geojson',params=params).status_code==422
    result=c.get('/api/v2/road-segments/geojson',params=params|{'bbox':'-74.011,40.711,-74.008,40.713'})
    assert result.status_code==200 and result.headers['content-type']=='application/geo+json'
    assert len(result.json()['features'])==1
    assert 'lineage' not in result.json()['features'][0]['properties']
    empty=c.get('/api/v2/road-segments',params=params|{'bbox':'-74.02,40.70,-74.015,40.705'})
    assert empty.json()['data']==[]
    assert c.get('/api/v2/context/geojson',params=params|{'bbox':'-75,40,-74,41'}).status_code==422
    assert c.get('/api/v2/context/geojson',params=params|{'bbox':'-74.02,40.70,-73.99,40.72'}).status_code==200


@pytest.mark.parametrize('extra',[{'bogus':'1'},{'limit':'0'},{'bbox':'NaN,1,2,3'},{'bbox':'2,1,1,3'},{'condition':'madeup'},{'cursor':'garbage'},{'q':' '*2}])
def test_strict_invalid_filters(client,extra):
    c,s=client
    assert c.get('/api/v2/road-segments',params={'snapshot_id':s['snapshot_id']}|extra).status_code==422


def test_detail_sources_all_conditions_and_unlocated_permits(client):
    c,s=client
    params={'snapshot_id':s['snapshot_id']}
    road=next(r for r in s['records'] if r['kind']=='road')
    assert c.get('/api/v2/road-segments/'+road['id'],params=params).json()['data']['condition_summary']['category']=='unknown'
    assert c.get('/api/v2/road-segments/'+road['id']+'/conditions',params=params).json()['data']==[]
    conditions=c.get('/api/v2/conditions',params=params).json()['data']
    assert len(conditions)==1 and conditions[0]['match']['status']=='ambiguous'
    p=c.get('/api/v2/permits',params=params|{'location':'unlocated'}).json()['data'][0]
    assert p['geometry'] is None and p['location_basis']=='unknown' and p['scope_membership']=='unverified_candidate'
    assert p['same_oft_records'][0]['kind']=='condition'
    assert c.get('/api/v2/permits/'+p['id'],params=params).status_code==200
    bbox=c.get('/api/v2/permits',params=params|{'bbox':'-74.02,40.70,-73.99,40.72'}).json()
    assert bbox['data']==[] and bbox['meta']['unlocated_excluded_count']==1
    filtered=c.get('/api/v2/permits',params=params|{'bbox':'-74.02,40.70,-73.99,40.72','location':'matched'}).json()
    assert filtered['data']==[] and filtered['meta']['unlocated_excluded_count']==0
    source_id=road['source_revision_id']
    assert c.get('/api/v2/source-revisions/'+source_id,params=params).status_code==200
    assert c.get('/api/v2/source-revisions/missing',params=params).status_code==404
    assert c.get('/api/v2/permits',params=params|{'road_id':'missing'}).status_code==404
    assert c.get('/api/v2/road-segments',params={'snapshot_id':'missing'}).status_code==404


def test_dashboard_denominators_do_not_depend_on_map(client):
    c,s=client
    params={'snapshot_id':s['snapshot_id']}
    before=c.get('/api/v2/dashboard',params=params).json()['data']
    assert before['counts']['roads']==1
    p=before['counts']['permits']
    assert p['matched']+p['ambiguous']+p['unmatched']==p['total']==1
    assert p['confirmed_in_scope']+p['scope_candidates']==p['total']
    assert p['unlocated']==1
    c.get('/api/v2/road-segments',params=params|{'bbox':'-74.02,40.70,-74.015,40.705','limit':1})
    assert c.get('/api/v2/dashboard',params=params).json()['data']==before


def test_cursor_snapshot_and_filter_isolation():
    from app.core.municipal_repository import paginate
    from app.core.repository import InvalidQuery
    values=[{'id':str(i)} for i in range(7)]
    first,cursor=paginate(values,3,None,{'snapshot':'one','q':''})
    second,last=paginate(values,4,cursor,{'snapshot':'one','q':''})
    assert len(first+second)==7 and len({r['id'] for r in first+second})==7 and last is None
    for binding in [{'snapshot':'two','q':''},{'snapshot':'one','q':'different'}]:
        with pytest.raises(InvalidQuery):
            paginate(values,3,cursor,binding)


def test_bbox_boundary_inclusion_and_outside_geometry(client):
    c,s=client
    from app.core.municipal_repository import MunicipalRepository
    path=c.app.state.settings.database_path
    repository=MunicipalRepository(path)
    r=repository.records(s['snapshot_id'],'road')[0]
    west,south,east,north=r['bbox']
    # Touching an endpoint remains an intersection, with bounds taken from the stored geometry.
    assert len(repository.records(s['snapshot_id'],'road',[east,south,east+.00001,north+.00001]))==1
    # The line has a nearly-horizontal envelope; querying below it must not select it.
    assert repository.records(s['snapshot_id'],'road',[west,south-.001,east,south-.00001])==[]


def test_viewport_cap_reports_error_without_truncation(client,monkeypatch):
    c,s=client
    original=c.app.state.municipal.records
    def dense(sid,kind,bounds=None):
        if kind=='road':
            return original(sid,kind,bounds)*2001
        return original(sid,kind,bounds)
    monkeypatch.setattr(c.app.state.municipal,'records',dense)
    r=c.get('/api/v2/road-segments/geojson',params={'snapshot_id':s['snapshot_id'],'bbox':'-74.02,40.7,-73.99,40.72'})
    assert r.status_code==422 and r.json()['error']['code']=='VIEWPORT_TOO_BROAD'


def test_dashboard_activity_and_freshness_preserve_source_meaning(client):
    c,s=client
    data=c.get('/api/v2/dashboard',params={'snapshot_id':s['snapshot_id']}).json()['data']
    assert data['method_version']=='municipal-summary-2'
    assert data['permit_status_counts']==[{'status':'ISSUED','count':1}]
    # Missing issue date cannot be replaced by the permit's known validity start.
    assert data['permit_issue_date_range'] is None
    assert len(data['source_freshness'])==4
    assert {r['id'] for r in data['source_freshness']}==set(data['source_revision_ids'])
    for item in data['source_freshness']:
        source=c.get('/api/v2/source-revisions/'+item['id'],params={'snapshot_id':s['snapshot_id']}).json()['data']
        assert item=={key:source[key] for key in ['id','source_id','retrieved_at','source_updated_at','cadence','release_note']}
    # Administrative status remains an exact source filter, never a construction-state inference.
    assert c.get('/api/v2/permits',params={'snapshot_id':s['snapshot_id'],'status':'ISSUED','location':'unlocated'}).json()['meta']['total_matching']==1
    assert c.get('/api/v2/permits',params={'snapshot_id':s['snapshot_id'],'status':'issued'}).json()['data']==[]


def test_large_map_page_preserves_full_records_and_rejects_oversize(client,monkeypatch):
    c,s=client
    params={'snapshot_id':s['snapshot_id'],'bbox':'-74.011,40.711,-74.008,40.713','limit':2000}
    response=c.get('/api/v2/road-segments',params=params)
    assert response.status_code==200
    assert response.json()['meta']['next_cursor'] is None
    assert len(response.json()['data'])==response.json()['meta']['total_matching']==1
    assert 'field_provenance' in response.json()['data'][0]
    assert c.get('/api/v2/road-segments',params=params|{'limit':2001}).status_code==422
    road=response.json()['data'][0]
    monkeypatch.setattr(c.app.state.municipal,'records',lambda *args: [road]*2001)
    monkeypatch.setattr(c.app.state.municipal,'enrich',lambda sid,records:records)
    oversized=c.get('/api/v2/road-segments',params=params)
    assert oversized.status_code==422 and oversized.json()['error']['code']=='VIEWPORT_TOO_BROAD'
    assert 'data' not in oversized.json()
