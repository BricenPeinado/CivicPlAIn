"""Synthetic source-shaped arithmetic harness; not real-world ranking coverage."""
import copy,json,sqlite3
from decimal import Decimal
import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient
from app.schemas.prioritization import PriorityPolicy,PriorityRequest
from app.services.prioritization import evaluate,calculate,VERSION,DEFINITIONS
from app.services.road_conditions import summarize
from app.core.prioritization_repository import PrioritizationRepository
from app.models.migrations import migrate,fingerprint,inspect_version
from app.main import create_app
from app.core.config import Settings
from app.ingestion.pipeline import publish
from test_m7_ingestion import staged

E={'classification':'planning_assumption','author':'SYNTHETIC TEST','entered_on':'2026-11-08','note':'Authored unit test policy, not an approved municipal decision'}
def policy(**changes):
    return PriorityPolicy.model_validate({'id':'test','version':'1','objective':'maintenance_review','weights':{'condition_need':'1','inspection_age':'0','evidence_gap':'0'},'age_horizon_days':365,'max_condition_age_days':365,'stale_behavior':'exclude','evidence':E}|changes)

def row(identifier='road-a',rating='4',inspection='2026-11-01T00:00:00',cost=None):
    # Deliberately synthetic source-shaped record; production origin checks reject it.
    road={'id':identifier,'source_record_key':identifier,'source_revision_id':'test-source','classification':'synthetic_fixture','contains_synthetic':True,'field_classifications':{},'values':{'name':identifier,'feature_type':'0'}}
    record={'id':'condition-'+identifier,'source_revision_id':'test-source','lineage':{'raw_fields':{'ismultipass':'0'}},'values':{'rating':rating,'inspection_at':inspection,'direction':'East','road_type':'Main','non_rating_reason':None},'field_classifications':{'rating':'official_observation','inspection_at':'official_observation'}}
    matches={record['id']:{'id':'synthetic-link','status':'matched','target_road_id':identifier,'method':'reviewed-candidates-v2','decision':{'scope':'whole_road'}}}
    summary=summarize([record],matches,identifier,'nyc-'+'1'*32,'2026-11-08',365)
    return {'road':road,'condition':summary,'cost':cost,'coordination':{'verified_opportunity':None,'status':'unknown'}}

def test_stable_ties_and_no_id_score_bonus():
    rows=[row('z','4'),row('a','4'),row('b','7')];p=policy()
    result=evaluate(rows,p);assert result==evaluate(rows[::-1],p)
    assert [(r['road_id'],r['rank']) for r in result['rows']]==[('a',1),('z',1),('b',3)]
    assert Decimal(result['rows'][0]['score'])==Decimal(2)/3 or result['rows'][0]['score'].startswith('0.666666')

@pytest.mark.parametrize('weights',[('0','0','0'),('1','1','0'),('-1','1','1'),('NaN','0','0'),('0.3333333','0.6666667','0'),('1e0','0','0'),('0.9','0','0')])
def test_invalid_extreme_weights(weights):
    with pytest.raises(ValidationError):policy(weights=dict(zip(['condition_need','inspection_age','evidence_gap'],weights)))

def test_unknowns_never_zero_filled_or_renormalized():
    p=policy(weights={'condition_need':'0.5','inspection_age':'0.5','evidence_gap':'0'})
    r=evaluate([row(rating=None)],p)['rows'][0]
    assert r['score'] is None and r['rank'] is None and r['status']=='unranked'
    assert set(r['missing_weighted_factors'])=={'condition_need','inspection_age'}
    assert r['factors']['condition_need']['contribution'] is None
    assert r['implementation_cost'] is None and r['traffic_disruption']['value'] is None


def test_conflicting_factors_and_changed_weights():
    rows=[row('bad-new','1'),row('better-old','7','2026-01-01T00:00:00')]
    assert evaluate(rows,policy())['rows'][0]['road_id']=='bad-new'
    p=policy(weights={'condition_need':'0','inspection_age':'1','evidence_gap':'0'})
    assert evaluate(rows,p)['rows'][0]['road_id']=='better-old'


def test_stale_sensitivity_and_age_does_not_change_rating():
    rows=[row('old','1','2024-01-01T00:00:00'),row('new','7')]
    a=evaluate(rows,policy());assert a['unranked']==1
    b=evaluate(rows,policy(stale_behavior='allow_qualified'));assert b['rows'][0]['road_id']=='old'
    assert b['rows'][0]['maintenance_need']['raw_rating']=='1' and b['rows'][0]['recency']['stale']
    assert b['rows'][0]['factors']['inspection_age']['value']=='1'


def test_budget_missing_cost_and_separate_cost_dimension():
    a=row('missing');b=row('priced',cost={'base_total_usd':'100.01'})
    assert evaluate([a,b],policy())['ranked']==2
    result=evaluate([a,b],policy(),Decimal('100'))
    assert result['ranked']==0 and {r['cost_constraint'] for r in result['rows']}=={'indeterminate','exceeds_declared_scope_ceiling'}
    assert evaluate([b],policy(),Decimal('100.01'))['ranked']==1


def test_inspection_gap_queue_not_maintenance_need():
    p=policy(objective='inspection_review',weights={'condition_need':'0','inspection_age':'0','evidence_gap':'1'})
    result=evaluate([row('missing',rating=None),row('known')],p)
    assert result['rows'][0]['road_id']=='missing' and result['rows'][0]['score']=='1'
    assert result['rows'][0]['maintenance_need']['status']=='unknown'
    with pytest.raises(ValidationError):policy(weights={'condition_need':'0','inspection_age':'0','evidence_gap':'1'})


def request(sid='nyc-'+'1'*32,ids=None,p=None):
    return PriorityRequest.model_validate({'contract_version':VERSION,'snapshot_id':sid,'road_ids':ids or ['a','b'],'as_of_date':'2026-11-08','policy':(p or policy()).model_dump(mode='json')})


def test_snapshot_replay_and_sensitivity_hashes():
    b=request(ids=['a','b']);d=b.model_dump(mode='json');d['sensitivity_policies']=[policy(id='alternative',weights={'condition_need':'0','inspection_age':'1','evidence_gap':'0'}).model_dump(mode='json')]
    snap={'method_version':VERSION,'definitions':DEFINITIONS,'request':d,'roads':[row('a'),row('b','7','2026-01-01T00:00:00')],'snapshot_road_count':2,'base':{'coverage':{'selection':'SYNTHETIC TEST'}}}
    result=calculate(snap);assert result==calculate(json.loads(json.dumps(snap)))
    assert result['sensitivity'][0]['rank_changes'][0]['delta']==1
    assert result['sensitivity'][0]['result_hash']
    snap['method_version']='unknown'
    with pytest.raises(ValueError):calculate(snap)

@pytest.mark.parametrize('field,value',[('road_ids',['a','a']),('as_of_date','2026-02-30'),('max_estimate_usd',{'value':'-1','unit':'USD','evidence':E}),('estimates',[{'road_id':'foreign','estimate_id':'estimate-'+'a'*64,'treatment':'patch'}])])
def test_request_invalid_context(field,value):
    b=request().model_dump(mode='json');b[field]=value
    with pytest.raises(ValidationError):PriorityRequest.model_validate(b)

@pytest.mark.parametrize('start',[0,7,8,9,10])
def test_schema_eleven_preservation_failure_recovery(start,tmp_path):
    db=tmp_path/'db'
    if start:migrate(db,tmp_path/'initial',target_version=start)
    else:sqlite3.connect(db).close()
    with sqlite3.connect(db) as c:before=fingerprint(c)
    with pytest.raises(sqlite3.OperationalError):migrate(db,tmp_path/'failure',True,11)
    with sqlite3.connect(db) as c:assert fingerprint(c)==before
    migrate(db,tmp_path/'backup',target_version=11)
    with sqlite3.connect(tmp_path/'backup') as c:assert fingerprint(c)==before
    with sqlite3.connect(db) as c:
        assert inspect_version(c)==11;after=fingerprint(c)
        for table,values in before['rows'].items():assert set(values)<=set(after['rows'][table]) if table=='schema_migrations' else values==after['rows'][table]
    assert migrate(db,tmp_path/'unused',target_version=11)['status']=='already_current'


def test_api_origin_gate_storage_reads_and_cross_context(staged,tmp_path,monkeypatch):
    db=tmp_path/'db';migrate(db,tmp_path/'backup',target_version=11);publish(db,staged,staged['report']['report_hash'])
    rid=next(r['id'] for r in staged['records'] if r['kind']=='road');sid=staged['snapshot_id']
    b=request(sid,[rid],policy(objective='inspection_review',weights={'condition_need':'0','inspection_age':'0','evidence_gap':'1'}))
    repository=PrioritizationRepository(db)
    with pytest.raises(ValueError,match='Synthetic'):repository.preview(b)
    # Preserve fixture semantics, explicitly bypass origin for persistence harness only.
    import app.core.prioritization_repository as module
    monkeypatch.setattr(module,'check_origin',lambda *_:None)
    with pytest.raises(ValueError):repository.save(b,inject_failure=True)
    assert repository.summaries(sid)==[]
    with TestClient(create_app(Settings(database_path=db))) as client:
        url='/api/v2/planning/prioritization-runs';data=b.model_dump(mode='json')
        result=client.post(url,json=data);assert result.status_code==201,result.text
        saved=result.json()['data'];identifier=saved['id'];assert client.post(url,json=data).status_code==200
        with sqlite3.connect(db) as c:before=fingerprint(c)
        assert client.get(url+'/'+identifier,params={'snapshot_id':sid}).json()['data']==saved
        assert client.get(url+'/'+identifier,params={'snapshot_id':'nyc-'+'f'*32}).status_code==404
        assert client.get(url+'/'+identifier+'/roads',params={'snapshot_id':sid,'status':'ranked'}).json()['meta']['total_matching']==1
        assert client.get(url+'/'+identifier+'/roads',params={'snapshot_id':sid,'status':'missing'}).status_code==422
        assert client.get(url+'/'+identifier+'/compare',params={'snapshot_id':sid,'road_ids':rid+',foreign'}).status_code==404
        assert client.post(url+'/preview',json=data).status_code==200
        with sqlite3.connect(db) as c:
            assert fingerprint(c)==before
            for statement in ['DELETE FROM prioritization_runs',"UPDATE prioritization_runs SET result_hash='bad'"]:
                with pytest.raises(sqlite3.IntegrityError):c.execute(statement)
    altered=copy.deepcopy(saved);altered['result']['base']['rows'][0]['score']='999'
    with pytest.raises(Exception):repository.verify(altered)


def test_ranked_road_pagination_and_filter_bound_cursor(staged,tmp_path,monkeypatch):
    db=tmp_path/'db';migrate(db,tmp_path/'backup',target_version=11);publish(db,staged,staged['report']['report_hash'])
    # Isolated HTTP adapter test: source-shaped rows are synthetic, no official coverage claim.
    ranked=evaluate([row('a','1'),row('b','7')],policy())
    monkeypatch.setattr(PrioritizationRepository,'get',lambda *_:{'result':{'base':ranked}})
    with TestClient(create_app(Settings(database_path=db))) as c:
        url='/api/v2/planning/prioritization-runs/adapter-test/roads';params={'snapshot_id':staged['snapshot_id'],'limit':1}
        first=c.get(url,params=params);assert first.status_code==200
        data=first.json();assert data['data'][0]['id']=='a';cursor=data['meta']['next_cursor'];assert cursor
        second=c.get(url,params=params|{'cursor':cursor});assert second.status_code==200 and second.json()['data'][0]['id']=='b'
        assert c.get(url,params=params|{'cursor':cursor,'status':'ranked'}).status_code==422


def test_condition_boundaries_and_monotonicity():
    rows=[row('low','1'),row('decimal','7.52'),row('high','10')]
    result=evaluate(rows,policy())
    assert [r['road_id'] for r in result['rows']]==['low','decimal','high']
    assert result['rows'][0]['score']=='1' and result['rows'][-1]['score']=='0'
    assert result['rows'][1]['maintenance_need']['raw_rating']=='7.52'
    assert all(r['maintenance_need']['official_category']=='unknown' for r in result['rows'])
