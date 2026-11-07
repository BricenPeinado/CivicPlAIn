"""M4 contracts, independent arithmetic oracles, persistence and replay tests."""
import copy
import json
import sqlite3
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.core.config import ROOT, Settings
from app.core.scenario_repository import ScenarioRepository
from app.main import create_app
from app.models.database import connection, initialize
from app.seed import seed
from app.seed_m2 import seed_m2
from app.seed_m3 import seed_m3
from app.seed_m4 import seed_m4
from app.schemas.scenarios import ScenarioDraft
from app.schemas.planning import RepairOption
from app.services.scenarios import replay
from app.services.estimates import canonical_hash, cost_scenarios


@pytest.fixture
def db(tmp_path):
    p = tmp_path / 'm4.sqlite3'
    seed(p); seed_m2(p); seed_m3(p)
    return p


@pytest.fixture
def client(db):
    with TestClient(create_app(Settings(database_path=db))) as c:
        yield c


def draft(index=0):
    return copy.deepcopy(json.loads((ROOT / 'data/demo/scenarios.json').read_text())[index]['draft'])


def create(c, body=None):
    r = c.post('/api/v1/scenarios', json=body or draft())
    assert r.status_code == 201, r.text
    return r.json()['data']


def run(c, s):
    r = c.post(f'/api/v1/scenarios/{s["id"]}/evaluate', json={'expected_revision': s['revision']})
    assert r.status_code == 200, r.text
    return r.json()['data']


def patch(c, s, body):
    return c.patch(f'/api/v1/scenarios/{s["id"]}', json={'expected_revision': s['revision'], 'draft': body})


@pytest.mark.parametrize('field,value', [('budget_usd', '-1'), ('budget_usd', 'NaN'), ('budget_usd', '1.001'),
    ('currency', 'EUR'), ('name', ' '), ('planning_end', '2027-04-01'), ('mobilization_groups', [{'id': 'unsupported'}])])
def test_invalid_scenario(client, field, value):
    b = draft(); b[field] = value
    assert client.post('/api/v1/scenarios', json=b).status_code == 422


@pytest.mark.parametrize('path,value,status', [('road_segment_id','missing',404), ('repair_option_id','missing',404),
    ('related_project_ids',['missing'],404), ('repair_category','invalid',422), ('repair_category','preventive',422)])
def test_reference_validation(client, path, value, status):
    b = draft(); b['actions'][0][path] = value
    if path == 'related_project_ids': b['project_overrides'] = []
    assert client.post('/api/v1/scenarios', json=b).status_code == status


@pytest.mark.parametrize('q', [dict(derivation='explicit_area', value='0'), dict(derivation='explicit_area', value='-1'),
    dict(derivation='explicit_area', value='NaN'), dict(derivation='explicit_area', value='1', unit='m'),
    dict(derivation='explicit_rectangle', length_m='1', width_m='101'),
    dict(derivation='explicit_rectangle', length_m='1.001', width_m='1', value='2'),
    dict(derivation='road_dimensions', value='799')])
def test_quantity_validation(client, q):
    b = draft(); a = b['actions'][0]; a['quantity'] = q
    if q['derivation'] == 'explicit_area':
        a['scope']['extent'] = 'partial_area'
    assert client.post('/api/v1/scenarios', json=b).status_code == 422


@pytest.mark.parametrize('change', ['dates', 'horizon', 'geometry', 'closure_overlap', 'cycle', 'duplicate', 'bad_override', 'provenance', 'assumption'])
def test_cross_validation(client, change):
    b = draft(); a = b['actions'][0]
    if change == 'dates': a['schedule']['end_date'] = '2027-03-31'
    if change == 'horizon': a['schedule']['start_date'] = '2027-03-01'
    if change == 'geometry': a['scope']['geometry']['coordinates'][0][0] = [0,0]
    if change == 'closure_overlap': a['schedule']['closure_intervals'] *= 2
    if change == 'cycle': a['constraints'] = {'must_follow_action_ids': [a['id']]}
    if change == 'duplicate':
        b['actions'].append(copy.deepcopy(a)); b['actions'][1]['id'] = 'duplicate'
    if change == 'bad_override': b['project_overrides'][0]['replacement_action_ids'] = ['missing']
    if change == 'provenance': a['input_provenance']['scope.geometry']['record_field'] = 'description'
    if change == 'assumption': b['assumptions'][0]['field_paths'] = ['budget_usd']
    assert client.post('/api/v1/scenarios', json=b).status_code == 422


@pytest.mark.parametrize('budget,status,headroom', [('60000','within_budget','6600.00'), ('53400','within_budget','0.00'),
    ('50000','over_budget','-3400.00'), ('0','over_budget','-53400.00')])
def test_budget_and_component_math(client, budget, status, headroom):
    b = draft(); b['budget_usd'] = budget
    e = run(client, create(client,b))
    assert e['cost_total_usd'] == dict(low='44760.00',base='53400.00',high='66360.00')
    assert e['budget_status'] == status and e['budget_headroom_usd']['base'] == headroom
    assert e['upper_bound_within_budget'] is False
    c = e['action_costs'][0]
    assert c['costs']['base']['contingency_usd'] == '8900.00'
    assert c['duration']['total_preliminary_days'] == 5
    assert e['elapsed_days'] == 7 and e['lane_closure_days'] == 7
    assert e['budget_headroom_usd']['high'] == format(Decimal(budget)-Decimal('66360'),'.2f')


def test_multi_action_partial_area_decimal(client):
    b = draft(); a = copy.deepcopy(b['actions'][0]); a['id'] = 'second'; a['road_segment_id'] = 'demo-r-002'
    a['scope'].update(extent='partial_area', geometry=None, location_status='unknown')
    a['input_provenance'].pop('scope.geometry'); a['unknown_reasons']['scope.geometry'] = 'Not surveyed'
    a['quantity'] = dict(derivation='explicit_area', value='0.000111')
    b['actions'].append(a)
    e = run(client,create(client,b))
    # 0.000111*45 -> .00, allowances 8500; 20% contingency 1700 => 10200.
    assert e['cost_total_usd']['base'] == '63600.00'
    assert e['action_costs'][1]['costs']['base']['line_items'][0]['amount_usd'] == '0.00'
    assert e['action_costs'][1]['quantity_m2'] == '0.000111'
    assert e['scheduled_road_workdays'] == 14


def test_half_cent_rounding_single_helper():
    o = json.loads((ROOT/'data/demo/maintenance.json').read_text())['repair_options'][0]
    o.update(unit_rates_usd={'low':'1','base':'1','high':'1'}, mobilization_usd='0', traffic_management_usd='0', contingency_fraction='0.5')
    c = cost_scenarios(Decimal('.005'),RepairOption.model_validate(o))['base']
    assert c.line_items[0].amount_usd == '0.01'
    assert c.contingency_usd == '0.01' and c.total_usd == '0.02'


def test_unpriced_action_unknown_feasibility(client):
    b = draft(); a = b['actions'][0]
    a.update(repair_category='trench_restoration', repair_option_id=None)
    a['scope']['extent'] = 'utility_trench'; a['quantity'] = dict(derivation='unknown')
    a['unknown_reasons'].update(repair_option_id='No reviewed restoration catalog method', quantity='Restoration scope unknown')
    e = run(client, create(client,b))
    assert e['cost_total_usd'] is None and e['budget_status'] == 'indeterminate'
    assert e['budget_headroom_usd'] is None and e['upper_bound_within_budget'] is None
    assert any('UNCLASSIFIED_REOPENING_RULE' in c for c in e['indeterminate_checks'])


def test_unknown_road_dimensions_and_schedule(client):
    b = draft(); a=b['actions'][0]; a['road_segment_id']='demo-r-006'
    a['scope'].update(geometry=None,location_status='unknown'); a['schedule']=None
    a['input_provenance'].pop('scope.geometry'); a['input_provenance'].pop('schedule')
    a['unknown_reasons'].update({'scope.geometry':'Unknown footprint','schedule':'Not scheduled'})
    b['project_overrides']=[]
    e=run(client,create(client,b))
    assert e['cost_total_usd'] is None and e['elapsed_days'] is None and e['lane_closure_days'] is None
    assert e['conflict_screen']['analysis']['indeterminate_checks']


def test_hypothetical_reuse_replacement_no_writes_and_replay(client,db):
    with connection(db) as c:
        tables=['roads','work_projects','project_roads','estimates','conflict_analyses','conflict_findings']
        before={t:c.execute('SELECT * FROM '+t+' ORDER BY rowid').fetchall() for t in tables}
    s=create(client); e=run(client,s)
    assert run(client,s)==e
    screen=e['conflict_screen']; analysis=screen['analysis']
    assert analysis['method_version']=='conflict-screen-v1'
    assert 'reopening_risk' in [f['finding_type'] for f in analysis['findings']]
    assert 'demo-road-project' not in screen['project_origins']
    assert len(screen['original_projects'])==2 and screen['overrides'][0]['operation']=='replace'
    assert set(screen['finding_contexts'].values())=={'hypothetical'}
    assert analysis['input_snapshot']['calculation_crs']=='EPSG:32618'
    assert len(analysis['input_snapshot']['roads']) == 24
    saved=ScenarioRepository(db).evaluation(e['id']); again=replay(saved)
    assert again.input_hash==saved.input_hash and again.result_hash==saved.result_hash
    with connection(db) as c:
        assert {t:c.execute('SELECT * FROM '+t+' ORDER BY rowid').fetchall() for t in tables}==before
        assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        assert not c.execute('PRAGMA foreign_key_check').fetchall()
        for operation in ['UPDATE scenario_evaluations SET revision=999','DELETE FROM scenario_evaluations']:
            with pytest.raises(sqlite3.IntegrityError): c.execute(operation)
    with TestClient(create_app(Settings(database_path=db))) as restarted:
        assert restarted.get('/api/v1/scenario-evaluations/'+e['id']).json()['data']==e


def test_revisions_crud_and_snapshot_immutability(client):
    s=create(client); e=run(client,s)
    b=draft(); b['name']='Edited'; b['budget_usd']='1'
    r=patch(client,s,b); assert r.status_code==200
    s2=r.json()['data']; assert s2['revision']==2 and s2['revision_hash']!=s['revision_hash']
    assert patch(client,s,b).status_code==409
    assert client.post('/api/v1/scenarios/'+s['id']+'/evaluate',json={'expected_revision':1}).status_code==409
    assert run(client,s2)['budget_status']=='over_budget'
    assert client.get('/api/v1/scenario-evaluations/'+e['id']).json()['data']==e
    assert len(client.get('/api/v1/scenarios/'+s['id']+'/evaluations').json()['data'])==2
    a=copy.deepcopy(b['actions'][0]); a.update(id='second',road_segment_id='demo-r-002')
    r=client.post('/api/v1/scenarios/'+s['id']+'/actions',json={'expected_revision':2,'action':a})
    assert r.status_code==201; assert r.json()['data']['revision']==3
    a['scope']['description']='Changed scope description'
    r=client.patch('/api/v1/scenarios/'+s['id']+'/actions/second',json={'expected_revision':3,'action':a})
    assert r.status_code==200 and r.json()['data']['revision']==4
    r=client.delete('/api/v1/scenarios/'+s['id']+'/actions/second?expected_revision=4')
    assert r.status_code==200 and len(r.json()['data']['actions'])==1


def test_empty_draft_and_pagination(client):
    b=draft(); b.update(actions=[],project_overrides=[],external_project_ids=[])
    s=create(client,b); e=run(client,s)
    assert e['budget_status']=='indeterminate' and e['cost_total_usd'] is None
    assert e['conflict_screen']['not_run_reason'].startswith('EMPTY_SCOPE')
    create(client)
    page=client.get('/api/v1/scenarios?limit=1').json()
    assert len(page['data'])==1 and page['meta']['next_cursor']
    assert len(client.get('/api/v1/scenarios?limit=1&after='+page['meta']['next_cursor']).json()['data'])==1


def test_demo_seeding_comparison_and_no_manufactured_savings(client,db):
    seed_m4(db); seed_m4(db)
    repo=ScenarioRepository(db)
    es=[repo.evaluations(f'demo-scenario-{k}')[0] for k in 'abc']
    assert [len(e.conflict_screen.analysis.findings) for e in es]==[1,1,2]
    assert [e.cost_total_usd['base'] for e in es]==['53400.00']*3
    r=client.post('/api/v1/scenario-comparisons',json={'evaluation_ids':[e.id for e in es]})
    assert r.status_code==200,r.text
    result=r.json()['data']
    assert all(d['base_cost_difference_usd']=='0.00' for d in result['deltas'])
    assert result['dominance']==[]
    assert any('later supplied completion' in t for t in result['tradeoffs'])
    with connection(db) as c:
        assert c.execute('SELECT count(*) FROM scenarios').fetchone()[0]==3
        assert c.execute('SELECT count(*) FROM scenario_evaluations').fetchone()[0]==3
    b=draft(); b['name']='Retain local edits'
    s=repo.get('demo-scenario-a'); repo.save(ScenarioDraft.model_validate(b),s.id,s.revision)
    seed_m4(db)
    assert repo.get(s.id).name=='Retain local edits'


def test_comparison_basis_mismatch_and_scope_disclosure(client):
    a=run(client,create(client))
    b=draft(1); b['budget_usd']='60001'; b['actions'][0]['scope']['extent']='partial_area'
    b['actions'][0]['quantity']=dict(derivation='explicit_area',value='100')
    be=run(client,create(client,b))
    r=client.post('/api/v1/scenario-comparisons',json={'evaluation_ids':[a['id'],be['id']]})
    assert r.status_code==200
    assert any('different road/repair' in w for w in r.json()['data']['warnings'])
    b['planning_end']='2027-06-01'; ce=run(client,create(client,b))
    assert client.post('/api/v1/scenario-comparisons',json={'evaluation_ids':[a['id'],ce['id']]}).status_code==409
    assert client.post('/api/v1/scenario-comparisons',json={'evaluation_ids':[a['id'],a['id']]}).status_code==422
    assert client.post('/api/v1/scenario-comparisons',json={'evaluation_ids':[a['id'],'missing']}).status_code==404


def test_source_changes_new_evaluation_old_replays(client,db):
    s=create(client); e=run(client,s)
    with connection(db) as c:
        raw=json.loads(c.execute("SELECT payload FROM repair_options WHERE id='demo-resurface'").fetchone()[0])
        raw['unit_rates_usd']['base']='46'
        c.execute("UPDATE repair_options SET payload=? WHERE id='demo-resurface'",(json.dumps(raw),))
    new=run(client,s)
    assert new['id']!=e['id'] and new['baseline_source_hash']!=e['baseline_source_hash']
    old=ScenarioRepository(db).evaluation(e['id'])
    assert replay(old).result_hash==old.result_hash
    assert client.post('/api/v1/scenario-comparisons',json={'evaluation_ids':[e['id'],new['id']]}).status_code==409


def test_pareto_dominance_and_non_dominance(client):
    a=draft(1); a['name']='Shorter closure'
    # Same stated assumptions, service and envelope; only explicitly supplied closure interval differs.
    a['actions'][0]['schedule']['closure_intervals'][0]['end_date']='2027-04-16'
    b=copy.deepcopy(a); b['name']='Longer closure'
    b['actions'][0]['schedule']['closure_intervals'][0]['end_date']='2027-04-17'
    ea=run(client,create(client,a)); eb=run(client,create(client,b))
    r=client.post('/api/v1/scenario-comparisons',json={'evaluation_ids':[ea['id'],eb['id']]}).json()['data']
    assert len(r['dominance'])==1
    assert r['dominance'][0]['dominant_evaluation_id']==ea['id']
    assert r['dominance'][0]['dominated_evaluation_id']==eb['id']
    # Same closure totals cannot yield a strict dominance relationship.
    b['name']='Equivalent numeric plan'; b['actions'][0]['schedule']['closure_intervals'][0]['end_date']='2027-04-16'
    ec=run(client,create(client,b))
    r=client.post('/api/v1/scenario-comparisons',json={'evaluation_ids':[ea['id'],ec['id']]}).json()['data']
    assert r['dominance']==[]


def test_mixed_existing_hypothetical_context_and_exclusion(client):
    b=draft(); b['project_overrides']=[]
    b['external_project_ids'].append('demo-concurrent-project')
    e=run(client,create(client,b))
    assert set(e['conflict_screen']['finding_contexts'].values())=={'hypothetical','existing_project_screen'}
    b['project_overrides']=[dict(project_id='demo-concurrent-project',operation='exclude',replacement_action_ids=[],reason='Explicit evaluation exclusion',evidence_ids=['assumption:planning'])]
    e=run(client,create(client,b))
    assert 'demo-concurrent-project' not in e['conflict_screen']['project_origins']
    assert any(p['id']=='demo-concurrent-project' for p in e['conflict_screen']['original_projects'])


def test_unknown_source_and_category_scope(client):
    b=draft(); b['actions'][0]['input_provenance']['scope.geometry']['evidence_ids']=['missing-source']
    assert client.post('/api/v1/scenarios',json=b).status_code==404
    b=draft(); b['actions'][0]['scope']['extent']='utility_trench'; b['actions'][0]['quantity']={'derivation':'explicit_area','value':'10'}
    assert client.post('/api/v1/scenarios',json=b).status_code==422


def test_repeated_scope_and_constraints(client):
    b=draft(); a=copy.deepcopy(b['actions'][0]); a['id']='repeat';a['repair_category']='reconstruct';a['repair_option_id']='demo-reconstruct';b['actions'].append(a)
    assert client.post('/api/v1/scenarios',json=b).status_code==422
    a['action_kind']='repeat_restoration'; a['input_provenance']['repeat_justification']=a['input_provenance']['scope']
    b['assumptions'][0]['field_paths'].append('repeat_justification')
    a['schedule']['start_date']='2027-04-20';a['schedule']['end_date']='2027-04-27';a['schedule']['closure_intervals']=None
    a['unknown_reasons']['schedule.closure_intervals']='Not supplied'
    a['constraints']={'must_follow_action_ids':['road-repair']}
    s=create(client,b); assert len(run(client,s)['action_costs'])==2
    b['actions'][0]['constraints']={'must_follow_action_ids':['repeat']}
    assert client.post('/api/v1/scenarios',json=b).status_code==422


def test_adapter_bounds_and_canonical_action_order(client,db):
    from app.core.scenario_inputs import freeze
    from app.core.repository import RoadRepository
    from app.core.planning_repository import PlanningRepository
    from app.core.conflict_repository import ConflictRepository
    from app.schemas.scenarios import Scenario
    from app.schemas.conflicts import AnalysisParameters
    from app.services.hypothetical import screen
    from app.services.scenarios import evaluate
    b=draft(); s=create(client,b); scenario=Scenario.model_validate(s)
    ctx=freeze(scenario,RoadRepository(db),PlanningRepository(db),ConflictRepository(db),s['id'])
    # Adapter itself enforces project cap, independently of REST.
    base=scenario.actions[0]
    def generated(n):
        raw=scenario.model_dump(mode='json');raw['actions']=[]
        for i in range(n):
            a=base.model_dump(mode='json');a['id']=f'action-{i}';a['scope']['description']=f'Explicit independently supplied scope {i}'
            raw['actions'].append(a)
        raw['external_project_ids']=[];raw['project_overrides']=[]
        # This tests adapter cap only; full domain save rejects unresolved duplicate road scopes.
        return Scenario.model_validate(raw)
    assert screen(generated(0),ctx,AnalysisParameters()).not_run_reason.startswith('EMPTY_SCOPE')
    assert screen(generated(50),ctx,AnalysisParameters()).analysis is not None
    raw=generated(50).model_dump(mode='json');raw['external_project_ids']=['demo-utility-project']
    with pytest.raises(ValueError,match='at most 50'):screen(Scenario.model_validate(raw),ctx,AnalysisParameters())
    b=draft(); a=copy.deepcopy(b['actions'][0]);a['id']='second';a['road_segment_id']='demo-r-002';b['actions'].append(a)
    ss=create(client,b); obj=Scenario.model_validate(ss)
    ctx=freeze(obj,RoadRepository(db),PlanningRepository(db),ConflictRepository(db),ss['id'])
    first=evaluate(obj,ctx)
    raw=obj.model_dump(mode='json');raw['actions'].reverse();raw['external_project_ids'].reverse()
    second=evaluate(Scenario.model_validate(raw),ctx)
    assert (first.input_hash,first.result_hash)==(second.input_hash,second.result_hash)
    changed=evaluate(obj,ctx,AnalysisParameters(proximity_m=6))
    assert changed.input_hash!=first.input_hash


def test_unavailable_comparison_has_no_cost_delta(client):
    a=run(client,create(client))
    b=draft(1); b['actions'][0]['repair_option_id']=None
    b['actions'][0]['unknown_reasons']['repair_option_id']='No selected method'
    be=run(client,create(client,b))
    r=client.post('/api/v1/scenario-comparisons',json={'evaluation_ids':[a['id'],be['id']]}).json()['data']
    assert r['deltas'][0]['base_cost_difference_usd'] is None and r['dominance']==[]
    assert any('required costs are missing' in t for t in r['tradeoffs'])
