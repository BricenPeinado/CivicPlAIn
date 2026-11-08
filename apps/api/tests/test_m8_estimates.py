"""Authored arithmetic harness only. Synthetic tests never establish municipal prices/measurements."""
import copy
import json
import sqlite3
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from app.main import create_app
from app.core.config import Settings
from app.models.migrations import migrate,fingerprint,inspect_version
from app.schemas.municipal_planning import EstimateRequest
from app.services.municipal_estimates import calculate,quantity,VERSION,ARITHMETIC,METHODS,frozen_inputs
from app.services.municipal_data import digest
from app.core.municipal_planning_repository import MunicipalPlanningRepository
from app.ingestion.pipeline import publish
from test_m7_ingestion import staged

E={'classification':'planning_assumption','author':'SYNTHETIC TEST AUTHOR','entered_on':'2026-11-08','note':'SYNTHETIC arithmetic test, not a real measurement/market price'}
def number(value,unit):return {'value':str(value),'unit':unit,'evidence':copy.deepcopy(E)}
def alternative():
    return {'treatment':'resurface','cost_overlap_review':'declared_nonoverlapping','scope':{'description':'SYNTHETIC test rectangle','extent':'partial','length':number('10','m'),'width':number('2','m')},
        'rate':number('1.005','USD/m2'),'price_basis_date':'2026-11-08','geography':'SYNTHETIC test scope',
        'inclusions':'Bundled labor, materials and equipment, SYNTHETIC TEST ONLY','exclusions':['Utilities, design and permits not priced'],
        'allowances':[{'key':k,'label':k,'disposition':'priced','amount':number('0.005','USD'),'evidence':copy.deepcopy(E)} for k in ['mobilization','traffic_control']],
        'contingency':number('0.1','fraction'),'sensitivity':{'low':number('0.5','USD/m2'),'high':number('2','USD/m2'),'evidence':copy.deepcopy(E)},
        'productivity':number('10','m2/active_workday'),'setup_days':number('0','days'),'curing_days':number('1','days')}

def body(sid='nyc-'+'1'*32,rid='road-test'):
    return EstimateRequest.model_validate({'contract_version':'municipal-estimate-v1','snapshot_id':sid,'road_id':rid,'alternatives':[alternative()]})

def math_snapshot(request):
    # Source-neutral pure math tests have no claim to be an imported official origin.
    from app.services.municipal_estimates import AREA,LENGTH
    return {'request':request.model_dump(mode='json'),'method_version':VERSION,'arithmetic_version':ARITHMETIC,
        'conversions':{'area_to_m2':{k:str(v) for k,v in AREA.items()},'length_to_m':{k:str(v) for k,v in LENGTH.items()}},'methods':copy.deepcopy(METHODS)}

def test_cents_line_rounding_contingency_duration_and_sensitivity():
    snap=math_snapshot(body());r=calculate(snap)['alternatives'][0]
    assert r['quantity_m2']=='20' and r['cases']['base']['subtotal_usd']=='20.12'
    assert r['cases']['base']['contingency_usd']=='2.01' and r['cases']['base']['total_cents']==2213
    assert [r['cases'][c]['total_usd'] for c in ['low','base','high']]==['11.02','22.13','44.02']
    assert r['duration']['active_workdays']==2 and r['duration']['total_preliminary_days']==3
    assert calculate(json.loads(json.dumps(snap)))==calculate(snap)

@pytest.mark.parametrize('unit,expected',[('ft2','0.92903040'),('yd2','8.36127360'),('m2','10')])
def test_exact_area_conversion(unit,expected):
    b=body().model_dump(mode='json');b['alternatives'][0]['scope']={'description':'SYNTHETIC supplied area','extent':'partial','area':number('10',unit)}
    r=calculate(math_snapshot(EstimateRequest.model_validate(b)))['alternatives'][0];assert r['quantity_m2']==expected
    b['alternatives'][0].pop('sensitivity');b['alternatives'][0]['rate']=number('1',f'USD/{unit}');assert calculate(math_snapshot(EstimateRequest.model_validate(b)))['alternatives'][0]['cases']['base']['line_items'][0]['quantity']=='10'

def test_missing_inputs_never_use_defaults_and_partial_duration_unavailable():
    b=body().model_dump(mode='json');a=b['alternatives'][0]
    del a['scope']['width'];a.pop('rate');a.pop('sensitivity');a.pop('setup_days')
    r=calculate(math_snapshot(EstimateRequest.model_validate(b)))['alternatives'][0]
    assert r['cases'] is None and r['duration'] is None and {'width','rate'}<=set(r['missing_fields'])
    b=body().model_dump(mode='json');b['alternatives'][0].pop('sensitivity');b['alternatives'][0].pop('productivity')
    r=calculate(math_snapshot(EstimateRequest.model_validate(b)))['alternatives'][0]
    assert set(r['cases'])=={'base'} and r['duration'] is None

@pytest.mark.parametrize('value',['-1','NaN','Infinity','1e3','0.0000001','1,000',' 1','01',1.5,True])
def test_invalid_numeric_boundaries(value):
    b=body().model_dump(mode='json');b['alternatives'][0]['rate']['value']=value
    with pytest.raises(ValidationError):EstimateRequest.model_validate(b)

@pytest.mark.parametrize('change', ['reconstruct','zero_area','zero_rate','negative_days','reversed_rates','wrong_unit','duplicate_allowance','double_quantity','unprovenanced_zero'])
def test_reject_unsupported_inconsistent_or_unsafe_fields(change):
    b=body().model_dump(mode='json');a=b['alternatives'][0]
    if change=='reconstruct':a['treatment']='reconstruct'
    if change=='zero_area':a['scope']['length']=number(0,'m')
    if change=='zero_rate':a['rate']=number(0,'USD/m2')
    if change=='negative_days':a['curing_days']=number('-1','days')
    if change=='reversed_rates':a['sensitivity']['low']=number(9,'USD/m2')
    if change=='wrong_unit':a['rate']['unit']='USD'
    if change=='duplicate_allowance':a['allowances'].append(a['allowances'][0])
    if change=='double_quantity':a['scope']['area']=number(10,'m2')
    if change=='unprovenanced_zero':a['allowances'][0]['amount']['evidence']['note']=' '
    with pytest.raises(ValidationError):EstimateRequest.model_validate(b)


def test_area_cap_included_excluded_and_unknown_allowances():
    b=body().model_dump(mode='json');a=b['alternatives'][0];a['scope']={'description':'SYNTHETIC limit','extent':'partial','area':number('10000000','m2')}
    assert calculate(math_snapshot(EstimateRequest.model_validate(b)))['alternatives'][0]['status']=='available'
    a['scope']['area']=number('10000000.000001','m2')
    with pytest.raises(ValueError):calculate(math_snapshot(EstimateRequest.model_validate(b)))
    a['scope']['area']=number('1','m2')
    for row,disposition in zip(a['allowances'],['included','excluded']):row['disposition']=disposition;row.pop('amount')
    result=calculate(math_snapshot(EstimateRequest.model_validate(b)))['alternatives'][0]
    assert len(result['cases']['base']['line_items'])==1 and len(result['allowance_declarations'])==2
    a['allowances'][0]['disposition']='unknown'
    assert calculate(math_snapshot(EstimateRequest.model_validate(b)))['alternatives'][0]['cases'] is None


def test_reject_synthetic_origin(staged):
    road=next(r for r in staged['records'] if r['kind']=='road');source=next(s for s in staged['revisions'] if s['id']==road['source_revision_id'])
    with pytest.raises(ValueError,match='Synthetic'):frozen_inputs(body(staged['snapshot_id'],road['id']),road,source,{**staged['manifest'],'id':staged['snapshot_id']})

@pytest.mark.parametrize('start',[0,7,8,9])
def test_migration_ten_atomic_and_preserves(start,tmp_path):
    db=tmp_path/'db'
    if start:migrate(db,tmp_path/'initial',target_version=start)
    else:sqlite3.connect(db).close()
    with sqlite3.connect(db) as c:before=fingerprint(c)
    with pytest.raises(sqlite3.OperationalError):migrate(db,tmp_path/'failed',True,10)
    with sqlite3.connect(db) as c:assert fingerprint(c)==before
    migrate(db,tmp_path/'backup',target_version=10)
    with sqlite3.connect(tmp_path/'backup') as c:assert fingerprint(c)==before
    with sqlite3.connect(db) as c:
        assert inspect_version(c)==10;after=fingerprint(c)
        assert set(before['schema'])<=set(after['schema'])
        for table,rows in before['rows'].items():assert set(rows)<=set(after['rows'][table]) if table=='schema_migrations' else rows==after['rows'][table]
    assert migrate(db,tmp_path/'unused',target_version=10)['status']=='already_current'


def test_snapshot_storage_isolation_idempotency_replay_and_read_only(staged,tmp_path,monkeypatch):
    db=tmp_path/'db';migrate(db,tmp_path/'backup',target_version=10);publish(db,staged,staged['report']['report_hash'])
    road=next(r for r in staged['records'] if r['kind']=='road');request=body(staged['snapshot_id'],road['id'])
    # Test-only source-neutral boundary substitution, preserving synthetic fixture semantics.
    # Actual official-origin calculation is verified separately against the pinned real local archive.
    import app.core.municipal_planning_repository as module
    def test_freeze(body,road,source,base):return {**math_snapshot(body),'road':road,'road_source':source,'base':base}
    monkeypatch.setattr(module,'frozen_inputs',test_freeze)
    repository=MunicipalPlanningRepository(db)
    with pytest.raises(ValueError):repository.save(request,inject_failure=True)
    assert repository.summaries(staged['snapshot_id'])==[]
    with TestClient(create_app(Settings(database_path=db))) as c:
        url='/api/v2/planning/estimates'
        result=c.post(url,json=request.model_dump(mode='json'));assert result.status_code==201,result.text
        saved=result.json()['data'];identifier=saved['id']
        assert c.post(url,json=request.model_dump(mode='json')).status_code==200
        with sqlite3.connect(db) as conn:before=fingerprint(conn)
        assert c.get(url+'/'+identifier,params={'snapshot_id':staged['snapshot_id']}).json()['data']==saved
        assert c.get(url+'/'+identifier,params={'snapshot_id':'nyc-'+'f'*32}).status_code==404
        assert c.get(url,params={'snapshot_id':staged['snapshot_id'],'road_id':road['id']}).json()['meta']['total_matching']==1
        assert c.get(url,params={'snapshot_id':staged['snapshot_id'],'limit':101}).status_code==422
        incomplete=request.model_dump(mode='json');incomplete['alternatives'][0]['scope']=None
        assert c.post(url+'/preview',json=incomplete).json()['data']['result']['alternatives'][0]['status']=='unavailable'
        invalid=c.post(url,json=incomplete)
        assert invalid.status_code==422 and invalid.json()['error']['code']=='MISSING_PLANNING_INPUTS'
        with sqlite3.connect(db) as conn:
            assert fingerprint(conn)==before
            for sql in ['DELETE FROM municipal_estimates','UPDATE municipal_estimates SET result_hash=\'bad\'']:
                with pytest.raises(sqlite3.IntegrityError):conn.execute(sql)
    altered=copy.deepcopy(saved);altered['result']['alternatives'][0]['quantity_m2']='999'
    with pytest.raises(Exception):repository.verify(altered)


def test_independent_patch_scope_zero_contingency_and_input_paths():
    data=body().model_dump(mode='json')
    patch=copy.deepcopy(data['alternatives'][0]);patch['treatment']='patch'
    patch['scope']={'description':'SYNTHETIC localized test only','extent':'partial','length':number('10','ft'),'width':number('2','ft')}
    patch['contingency']=number('0','fraction');patch.pop('sensitivity')
    patch['productivity']=number('10','ft2/active_workday')
    data['alternatives'].append(patch)
    snap=math_snapshot(EstimateRequest.model_validate(data));result=calculate(snap)
    p,r=result['alternatives']
    assert [p['treatment'],r['treatment']]==['patch','resurface']
    assert p['quantity_m2']=='1.85806080' and p['duration']['active_workdays']==2
    assert p['cases']['base']['contingency_usd']=='0.00'
    assert p['cases']['base']['line_items'][0]['evidence_path']=='request.alternatives.1.rate'
    assert r['cases']['base']['total_cents']==2213
    snap['arithmetic_version']='unsupported'
    with pytest.raises(ValueError,match='version'):calculate(snap)


def test_missing_overlap_review_and_contingency_block_costs():
    data=body().model_dump(mode='json');a=data['alternatives'][0]
    a.pop('cost_overlap_review');a.pop('contingency')
    r=calculate(math_snapshot(EstimateRequest.model_validate(data)))['alternatives'][0]
    assert r['status']=='unavailable' and r['cases'] is None
    assert {'cost_overlap_review','contingency'}<=set(r['missing_fields'])
