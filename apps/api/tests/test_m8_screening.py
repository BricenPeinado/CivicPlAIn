"""Explicitly synthetic software tests, never evidence of official construction coverage."""
import copy,json,sqlite3
from datetime import date,timedelta
import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient
from pyproj import Transformer
from app.schemas.official_screening import ScreeningRequest,WorkInput
from app.services.official_screening import screen,calculate,LIBRARIES,VERSION
from app.services.municipal_data import digest
from app.models.migrations import migrate,fingerprint,inspect_version
from app.ingestion.pipeline import publish
from app.core.official_screening_repository import OfficialScreeningRepository
from app.core.config import Settings
from app.main import create_app
from test_m7_ingestion import staged
from test_m8_estimates import body as estimate_body,number
from app.core.municipal_planning_repository import MunicipalPlanningRepository
E={'classification':'planning_assumption','author':'SYNTHETIC TEST','entered_on':'2026-11-08','note':'Synthetic work and policy, not a municipal observation'}
G={'type':'Polygon','coordinates':[[[-74.01,40.712],[-74.0098,40.712],[-74.0098,40.7121],[-74.01,40.7121],[-74.01,40.712]]]}
P={'proximity_m':5.0,'reopening_horizon_days':30}
SID='nyc-'+'1'*32

def schedule(start='2026-01-01',end='2026-01-10'):return {'start':start,'end':end,'basis':copy.deepcopy(E)}
def work(id='a',**changes):
    return WorkInput.model_validate({'id':id,'title':'Synthetic '+id,'work_type':'resurfacing','basis':E,'location':{'geometry':G,'crs':'EPSG:4326','certainty':'declared','basis':E},'schedule':schedule(),'grade':'surface','grade_basis':E}|changes).model_dump(mode='json')
def request(sid=SID,works=None,**changes):
    return ScreeningRequest.model_validate({'contract_version':VERSION,'snapshot_id':sid,'works':works if works is not None else [work(),work('b')],'proximity_m':5.0,'reopening_horizon_days':30,'policy_evidence':E}|changes)
def run(works,parameters=None):return screen(works,[],{},parameters or P)
def kinds(result):return {f['finding_type'] for f in result['findings']}


def test_overlap_spatial_evidence_ties_and_duplicate_stability():
    works=[work(),work('b')];r=run(works)
    assert 'concurrent_work' in kinds(r) and r==run(works[::-1])
    assert len({f['id'] for f in r['findings']})==len(r['findings'])
    assert r['pair_checks'][0]['spatial']['positive_area_overlap'] is True
    assert all(f['human_review_required'] and f['evidence_status']=='supplied_evidence_only_not_independently_verified' for f in r['findings'])

@pytest.mark.parametrize('gap,expected',[(0,True),(30,True),(31,False)])
def test_rework_horizon_and_adjacent_not_overlap(gap,expected):
    start=date(2026,1,10)+timedelta(days=gap)
    r=run([work(),work('b',work_type='excavation',excavation_required=True,excavation_basis=E,schedule=schedule(start.isoformat(),(start+timedelta(days=3)).isoformat()))])
    assert ('potential_pavement_rework' in kinds(r))==expected
    assert 'concurrent_work' not in kinds(r)
    assert r['pair_checks'][0]['temporal']['gap_days']==gap

@pytest.mark.parametrize('distance,expected',[(4.999,True),(5,True),(5.001,False)])
def test_projected_threshold_boundary(distance,expected):
    forward=Transformer.from_crs(4326,32618,always_xy=True);back=Transformer.from_crs(32618,4326,always_xy=True)
    x,y=forward.transform(-74.01,40.712)
    geom=lambda offset:{'type':'LineString','coordinates':[back.transform(x+offset,y),back.transform(x+offset,y+20)]}
    works=[work('a',location={'geometry':geom(0),'crs':'EPSG:4326','certainty':'declared','basis':E}),work('b',location={'geometry':geom(distance),'crs':'EPSG:4326','certainty':'declared','basis':E})]
    assert ('concurrent_work' in kinds(run(works)))==expected
    if expected:assert all(f['category']=='potential_coordination_opportunity' for f in run(works)['findings'])

def test_grade_separated_crossing_and_unknown_grade_qualification():
    a=work();b=work('b',grade='elevated');r=run([a,b]);assert not r['findings'];assert r['pair_checks'][0]['status']=='grade_separated'
    b=work('b',grade='unknown',grade_basis=None);r=run([a,b]);assert r['indeterminate_pair_count']==1
    assert all(f['category']=='potential_coordination_opportunity' and 'grade_separation' in f['qualified_by'] for f in r['findings'])

def test_missing_schedules_geometry_no_dates_or_shared_reference_guess():
    r=run([work(schedule=None),work('b')]);assert not r['findings'] and r['indeterminate_pair_count']==1
    a=work(location=None,road_ids=['r']);b=work('b',location=None,road_ids=['r'])
    r=screen([a,b],[],{'r':{'geometry':G}},P);assert not r['findings'];assert 'work_footprint' in r['pair_checks'][0]['missing_fields']

def test_conflicting_geometry_reference_is_not_promoted():
    a=work(road_ids=['r']);r=screen([a,work('b')],[],{'r':{'geometry':{'type':'LineString','coordinates':[[-74.001,40.719],[-74.002,40.719]]}}},P)
    assert not r['findings'];assert r['pair_checks'][0]['location_issues']==['DECLARED_GEOMETRY_DISAGREES_WITH_ROAD_REFERENCE']

def test_closures_use_exact_supplied_intervals_not_envelopes():
    a=work(closure=schedule('2026-01-01','2026-01-05'));b=work('b',closure=schedule('2026-01-05','2026-01-10'))
    assert 'concurrent_work' in kinds(run([a,b])) and 'multiple_closure_plans' not in kinds(run([a,b]))
    b=work('b',closure=schedule('2026-01-04','2026-01-10'));assert 'multiple_closure_plans' in kinds(run([a,b]))

def test_adjacent_nonexcavation_opportunity_and_approximate_qualification():
    b=work('b',work_type='inspection',schedule=schedule('2026-01-10','2026-01-12'))
    assert 'adjacent_work_coordination' in kinds(run([work(),b]))
    b['location']['certainty']='approximate';r=run([work(),b]);assert all(f['category']=='potential_coordination_opportunity' for f in r['findings'])

@pytest.mark.parametrize('change',[
 {'schedule':schedule('2026-01-10','2026-01-01')},
 {'schedule':schedule('2026-01-01','2026-01-01')},
 {'schedule':schedule('2026-02-30','2026-03-03')},
 {'location':{'geometry':G,'crs':'EPSG:2263','certainty':'declared','basis':E}},
 {'grade_basis':None}, {'excavation_required':True}, {'excavation_depth_m':'3'},
 {'closure':schedule('2026-01-01','2026-01-12')}, {'road_ids':['a','a']},
 {'basis':E|{'classification':'supplied_document'}},
 {'location':{'geometry':{'type':'Polygon','coordinates':[[[0,0],[1,1],[1,0],[0,1],[0,0]]]},'crs':'EPSG:4326','certainty':'declared','basis':E}}
])
def test_invalid_work_evidence_rejected(change):
    with pytest.raises(ValidationError):work(**change)


def test_alternative_replay_changes_schedule_without_inventing_benefits():
    b=request(alternatives=[{'id':'later','overrides':[{'work_id':'b','schedule':schedule('2026-03-01','2026-03-10')}],'evidence':E}])
    snap={'method_version':VERSION,'libraries':LIBRARIES,'request':b.model_dump(mode='json'),'roads':[],'permits':[],'base':{'coverage':{}},'estimate':None}
    r=calculate(snap);assert r==calculate(json.loads(json.dumps(snap)));assert r['base']['findings'] and not r['alternatives'][0]['screen']['findings']
    assert r['coverage']['utilities']=='unknown' and r['coverage']['excavation_clearance'] is False
    snap['libraries']={}
    with pytest.raises(ValueError):calculate(snap)

@pytest.mark.parametrize('start',[0,7,8,9,10,11])
def test_schema_twelve_atomic_preservation(start,tmp_path):
    db=tmp_path/'db'
    if start:migrate(db,tmp_path/'before',target_version=start)
    else:sqlite3.connect(db).close()
    with sqlite3.connect(db) as conn:prior=fingerprint(conn)
    with pytest.raises(sqlite3.OperationalError):migrate(db,tmp_path/'failed',True,12)
    with sqlite3.connect(db) as conn:assert fingerprint(conn)==prior
    migrate(db,tmp_path/'backup',target_version=12)
    with sqlite3.connect(tmp_path/'backup') as conn:assert fingerprint(conn)==prior
    with sqlite3.connect(db) as conn:
        assert inspect_version(conn)==12
        after=fingerprint(conn)
        assert set(prior['schema'])<=set(after['schema'])
        for table,rows in prior['rows'].items():assert set(rows)<=set(after['rows'][table]) if table=='schema_migrations' else rows==after['rows'][table]
    assert migrate(db,tmp_path/'unused',target_version=12)['status']=='already_current'


def test_repository_adapter_permits_unknowns_notes_isolation_replay_and_atomicity(staged,tmp_path,monkeypatch):
    db=tmp_path/'db';migrate(db,tmp_path/'backup',target_version=12);publish(db,staged,staged['report']['report_hash'])
    sid=staged['snapshot_id'];permit=next(r for r in staged['records'] if r['kind']=='permit');rid=next(r['id'] for r in staged['records'] if r['kind']=='road')
    b=request(sid,[work(road_ids=[rid]),work('b',road_ids=[rid])],permit_ids=[permit['id']]);repo=OfficialScreeningRepository(db)
    with pytest.raises(ValueError,match='Synthetic'):repo.preview(b)
    import app.core.official_screening_repository as module
    monkeypatch.setattr(module,'check_origin',lambda *_:None)
    with pytest.raises(ValueError):repo.save(b,inject_failure=True)
    assert repo.summaries(sid)==[]
    with TestClient(create_app(Settings(database_path=db))) as client:
        url='/api/v2/planning/conflict-analyses';data=b.model_dump(mode='json')
        preview=client.post(url+'/preview',json=data);assert preview.status_code==200,preview.text
        assert repo.summaries(sid)==[]
        saved=client.post(url,json=data);assert saved.status_code==201,saved.text
        record=saved.json()['data'];id=record['id'];r=record['result'];assert r['base']['indeterminate_pair_count']==2
        p=next(a for a in r['base']['activities'] if a['origin']=='administrative_permit')
        assert p['schedule'] is None and p['location'] is None and p['administrative_dates']['valid_from']
        assert p['permit_location']['status']=='candidate'
        assert client.post(url,json=data).status_code==200
        data['works'].reverse();assert client.post(url,json=data).json()['data']['id']==id
        with sqlite3.connect(db) as c:before=fingerprint(c)
        assert client.get(url+'/'+id,params={'snapshot_id':sid}).json()['data']==record
        assert client.get(url,params={'snapshot_id':sid}).status_code==200
        assert client.get(url+'/'+id+'/notes',params={'snapshot_id':sid}).json()['data']==[]
        with sqlite3.connect(db) as c:assert fingerprint(c)==before
        assert client.get(url+'/'+id,params={'snapshot_id':'nyc-'+'f'*32}).status_code==404
        note={'author':'SYNTHETIC reviewer','note':'Synthetic review only, no approval','disposition':'needs_review','finding_id':r['base']['findings'][0]['id']}
        assert client.post(url+'/'+id+'/notes',params={'snapshot_id':sid},json=note).status_code==201
        assert client.post(url+'/'+id+'/notes',params={'snapshot_id':sid},json=note).status_code==200
        note['finding_id']='finding-'+'f'*64;assert client.post(url+'/'+id+'/notes',params={'snapshot_id':sid},json=note).status_code==404
        assert len(client.get(url+'/'+id+'/notes',params={'snapshot_id':sid}).json()['data'])==1
        with sqlite3.connect(db) as c:
            with pytest.raises(sqlite3.IntegrityError):c.execute('DELETE FROM official_screenings')
            with pytest.raises(sqlite3.IntegrityError):c.execute('UPDATE official_screening_notes SET payload=payload')
        damaged=copy.deepcopy(record);damaged['result']['base']['findings']=[]
        with pytest.raises(Exception) as exc:repo.verify(damaged)
        assert exc.value.status_code==409
        data['works'][0]['location']['geometry']={'type':'LineString','coordinates':[[-75,40],[-75.1,40.1]]}
        assert client.post(url+'/preview',json=data).status_code==422


def test_missing_schema_not_auto_migrated(staged,tmp_path):
    db=tmp_path/'db';migrate(db,tmp_path/'backup',target_version=7);publish(db,staged,staged['report']['report_hash']);repo=OfficialScreeningRepository(db)
    with pytest.raises(Exception) as exc:repo.save(request(staged['snapshot_id']))
    assert exc.value.status_code==503
    with sqlite3.connect(db) as c:assert inspect_version(c)==7


def test_estimate_comparable_scope_rounding_and_missing_alternative(staged,tmp_path,monkeypatch):
    db=tmp_path/'db';migrate(db,tmp_path/'backup',target_version=12);publish(db,staged,staged['report']['report_hash']);sid=staged['snapshot_id'];rid=next(r['id'] for r in staged['records'] if r['kind']=='road')
    import app.core.official_screening_repository as screening_module
    monkeypatch.setattr(screening_module,'check_origin',lambda *_:None)
    # M8.3 intentionally rejects synthetic origins; bypass only in this explicit synthetic storage harness.
    # Pure cost-comparison math; storage origin gates are independently tested above.
    from test_m8_estimates import math_snapshot
    from app.core.municipal_repository import MunicipalRepository
    from app.services.municipal_estimates import calculate as estimate_calculate
    repository=MunicipalRepository(db);eb=estimate_body(sid,rid);base=repository.snapshot(sid);road=repository.get(sid,'road',rid)
    snap=math_snapshot(eb)|{'road':road,'base':base,'source':repository.source(sid,road['source_revision_id'])}
    # Keep this test at the pure screening math boundary; real estimate replay is covered by M8.3 and actual isolated QA.
    result={'alternatives':estimate_calculate(snap)['alternatives']}
    choice={'work_id':'a','estimate_id':'estimate-'+'a'*64,'treatment':'resurface','base_schedule_addition':number('0.005','USD'),'alternative_schedule_additions':{'later':number('1.005','USD')},'comparable_scope_and_nonoverlap':'declared_same_scope_nonoverlapping_additions','evidence':E}
    b=request(sid,[work(road_ids=[rid]),work('b')],alternatives=[{'id':'later','overrides':[{'work_id':'a','schedule':schedule('2026-03-01','2026-03-03')}],'evidence':E}],cost_comparison=choice)
    snap={'method_version':VERSION,'libraries':LIBRARIES,'request':b.model_dump(mode='json'),'roads':[road],'permits':[],'base':base,'estimate':{'id':choice['estimate_id'],'result':result}}
    cost=calculate(snap)['cost_comparison'];assert cost['base_explicit_addition_usd']=='0.01';assert cost['comparisons'][0]['explicit_addition_usd']=='1.01';assert cost['comparisons'][0]['difference_from_base_usd']=='1.00'
    choice['alternative_schedule_additions']={}
    with pytest.raises(ValidationError):request(sid,cost_comparison=choice)


def test_unlocated_and_multiple_candidate_permits_never_become_work():
    permits=[]
    for i,candidates in enumerate([[],[{'road_id':'r1'},{'road_id':'r2'}]]):
        record={'id':'p'+str(i),'source_record_key':'SYNTHETIC ADMIN','values':{'valid_from':'2026-01-01','valid_to':'2026-01-10'}}
        permits.append({'record':record,'location':{'status':'candidate' if candidates else 'unlocated','accepted_road_ids':[], 'candidates':candidates}})
    r=screen([],permits,{},P)
    assert r['findings']==[] and r['indeterminate_pair_count']==1
    assert all(a['location'] is None and a['schedule'] is None for a in r['activities'])
    assert len(r['activities'][1]['permit_location']['candidates'])==2


def test_actual_crossing_lines_different_grade_and_horizon_zero():
    a=work(location={'geometry':{'type':'LineString','coordinates':[[-74.01,40.712],[-74.009,40.712]]},'crs':'EPSG:4326','certainty':'declared','basis':E})
    b=work('b',grade='elevated',location={'geometry':{'type':'LineString','coordinates':[[-74.0095,40.7115],[-74.0095,40.7125]]},'crs':'EPSG:4326','certainty':'declared','basis':E})
    r=run([a,b]);assert r['pair_checks'][0]['spatial']['geometry_intersects'] and not r['findings']
    c=work('c',schedule=schedule('2026-01-10','2026-01-12'),excavation_required=True,excavation_basis=E)
    assert 'potential_pavement_rework' in kinds(run([work(),c],P|{'reopening_horizon_days':0}))
    c['schedule']=schedule('2026-01-11','2026-01-12');assert not run([work(),c],P|{'reopening_horizon_days':0})['findings']


def test_same_long_road_does_not_override_known_footprint_separation():
    road={'geometry':{'type':'LineString','coordinates':[[-74.01,40.712],[-74.008,40.712]]}}
    shape_a={'type':'LineString','coordinates':[[-74.01,40.712],[-74.0099,40.712]]}
    shape_b={'type':'LineString','coordinates':[[-74.0081,40.712],[-74.008,40.712]]}
    works=[work('a',road_ids=['r'],location={'geometry':shape_a,'crs':'EPSG:4326','certainty':'declared','basis':E}),work('b',road_ids=['r'],location={'geometry':shape_b,'crs':'EPSG:4326','certainty':'declared','basis':E})]
    result=screen(works,[],{'r':road},P)
    assert result['pair_checks'][0]['spatial']['shared_road_ids']==['r']
    assert result['pair_checks'][0]['spatial']['distance_m']>5
    assert result['pair_checks'][0]['status']=='not_spatially_related'
    assert result['findings']==[]
