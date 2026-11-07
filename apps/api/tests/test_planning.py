import copy
import hashlib
import json
import sqlite3
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import ROOT, Settings
from app.core.planning_repository import PlanningRepository, ordered_assessments
from app.core.repository import RoadRepository
from app.main import create_app
from app.models.database import connection, initialize
from app.schemas.planning import Assessment, AssetAttributes, CostRates, EstimateRequest, PlanningAssumptions, RepairOption
from app.schemas.roads import Road
from app.seed import seed
from app.seed_m2 import seed_m2
from app.services.estimates import MissingInputs, calculate, canonical_hash, duration, money


@pytest.fixture
def db(tmp_path):
    path = tmp_path / 'm2.sqlite3'
    seed(path)
    seed_m2(path)
    return path


@pytest.fixture
def client(db):
    with TestClient(create_app(Settings(database_path=db))) as client:
        yield client


def inputs(db, option_id='demo-resurface', road_id='demo-r-001'):
    repo = PlanningRepository(db)
    return RoadRepository(db).get(road_id), repo.latest(road_id), next(o for o in repo.options() if o.id == option_id)


@pytest.mark.parametrize('field,value', [('length_m', '-1'), ('width_m', '0'), ('width_m', 'NaN'), ('surface_material', 'wood'), ('width_m', 'Infinity')])
def test_asset_validation(field, value):
    payload = json.loads((ROOT / 'data/demo/maintenance.json').read_text())['assets'][0]
    payload[field] = value
    with pytest.raises(ValidationError):
        AssetAttributes.model_validate(payload)


def test_assessment_scale_validation_and_provenance(db):
    road, assessment, _ = inputs(db)
    assert road.condition_summary.assessed_on.isoformat() == '2026-10-01'
    assert assessment.evidence_ids == ['demo-maintenance-assumptions-v1']
    assert road.dimension_basis['width_m'] == 'synthetic_planning_assumption'
    assert road.repairable_area_m2 == Decimal('800')
    for invalid in ['-1', '0', '11', 'NaN']:
        payload = assessment.model_dump(mode='json')
        payload['rating'] = invalid
        with pytest.raises(ValidationError):
            Assessment.model_validate(payload)
    for area in ['-1', '0', '801']:
        payload = road.model_dump(mode='json')
        payload['repairable_area_m2'] = area
        with pytest.raises(ValidationError):
            Road.model_validate(payload)


def test_latest_order_stable_ties_and_undated(db):
    _, original, _ = inputs(db)
    records = [original.model_copy(update={'id': i}) for i in ['z', 'a']]
    records += [original.model_copy(update={'id': 'undated', 'assessed_on': None})]
    assert [a.id for a in ordered_assessments(records)] == ['a', 'z', 'undated']
    assert ordered_assessments(list(reversed(records))) == ordered_assessments(records)


def test_exact_components_contingency_ordering_and_no_double_counting(db):
    result = calculate(*inputs(db))
    assert result.quantity == 800
    base = result.scenarios['base']
    assert [item.amount_usd for item in base.line_items] == ['36000.00', '6000.00', '2500.00']
    assert base.subtotal_usd == '44500.00'
    assert base.contingency_usd == '8900.00'
    assert base.total_usd == '53400.00'
    assert result.scenarios['low'].total_usd == '44760.00'
    assert result.scenarios['high'].total_usd == '66360.00'
    assert len(base.line_items) == 3  # bundled materials, labor, equipment charged only once
    assert base.line_items[0].unit == 'm2'
    assert base.line_items[1].unit == 'allowance'
    assert result.dimension_provenance['length_m']['unit'] == 'm'
    assert result.synthetic_input and result.data_kind == 'derived'
    assert calculate(*inputs(db)).model_dump_json() == result.model_dump_json()


def test_rounding_and_rate_validation(db):
    assert money(Decimal('1.005')) == '1.01'
    assert money(Decimal('1.004')) == '1.00'
    road, assessment, option = inputs(db)
    assumptions = PlanningAssumptions(length_m='.333', width_m='1', note='Explicit synthetic decimal test')
    option = RepairOption.model_validate({**option.model_dump(), 'unit_rates_usd': {'low': '1.005', 'base': '1.005', 'high': '1.005'},
        'mobilization_usd': '0', 'traffic_management_usd': '0', 'contingency_fraction': '.5'})
    base = calculate(road, assessment, option, assumptions).scenarios['base']
    assert base.line_items[0].amount_usd == '0.33'
    assert base.contingency_usd == '0.17' and base.total_usd == '0.50'
    for change in [{'productivity_per_day': '0'}, {'productivity_per_day': '-1'}, {'quantity_unit': 'm'},
                   {'productivity_unit': 'm/day'}, {'contingency_fraction': '1.1'}, {'mobilization_usd': '-1'}]:
        with pytest.raises(ValidationError):
            RepairOption.model_validate({**option.model_dump(), **change})
    with pytest.raises(ValidationError):
        CostRates(low=2, base=1, high=3)
    with pytest.raises(ValidationError):
        CostRates(low=-1, base=1, high=3)


def test_duration_rounding_setup_curing_and_invalid(db):
    _, _, option = inputs(db)
    assert duration(Decimal('600'), option).active_workdays == 1
    d = duration(Decimal('600.001'), option)
    assert d.active_workdays == 2 and d.setup_days == 2 and d.curing_days == 1
    assert d.total_preliminary_days == 5
    for value in [Decimal('0'), Decimal('-1')]:
        with pytest.raises(ValueError):
            duration(value, option)


def test_missing_inputs_explicit_overrides_and_suitability(db):
    road, assessment, option = inputs(db, road_id='demo-r-004')
    assert road.length_m is None and road.width_m is None
    with pytest.raises(MissingInputs, match='length_m'):
        calculate(road, assessment, option)
    result = calculate(road, assessment, option, PlanningAssumptions(length_m='100', width_m='8', note='Hypothetical rectangular scope'))
    assert result.suitability.status == 'requires_review'
    assert result.dimension_provenance['width_m']['basis'] == 'user_planning_assumption'
    assert result.quantity == 800
    for rid, oid in [('demo-r-001', 'demo-reconstruct'), ('demo-r-002', 'demo-preventive'), ('demo-r-003', 'demo-resurface')]:
        assert calculate(*inputs(db, oid, rid)).suitability.status == 'candidate_requires_review'
    assert calculate(*inputs(db, 'demo-preventive')).suitability.status == 'not_indicated'
    for change in [{'length_m': '0'}, {'width_m': '-1'}, {'unit': 'ft'}, {'note': '  '}, {'length_m': None, 'width_m': None}]:
        with pytest.raises(ValidationError):
            PlanningAssumptions.model_validate({'length_m': '100', 'width_m': '8', 'note': 'Test', **change})


def test_api_conditions_options_and_unknowns(client):
    history = client.get('/api/v1/road-segments/demo-r-001/conditions').json()['data']
    assert len(history) == 3 and history[0]['assessed_on'] == '2026-10-01'
    assert history[-1]['assessed_on'] is None
    assert client.get('/api/v1/road-segments/demo-r-004/conditions').json()['data'] == []
    options = client.get('/api/v1/road-segments/demo-r-001/repair-options').json()['data']
    assert len(options) == 3 and all(o['preview']['synthetic_input'] for o in options)
    assert len(client.get('/api/v1/repair-options').json()['data']) == 3
    missing = client.get('/api/v1/road-segments/demo-r-004/repair-options').json()['data']
    assert all(o['preview'] is None and 'unknown' in o['unavailable_reason'] for o in missing)
    for path in ['/road-segments/missing/conditions', '/road-segments/missing/repair-options', '/estimates/missing']:
        assert client.get('/api/v1' + path).status_code == 404
    for path in ['/road-segments', '/road-segments/geojson', '/road-segments/demo-r-001', '/health', '/evidence-sources/demo-maintenance-assumptions-v1']:
        assert client.get('/api/v1' + path).status_code == 200


def request_body(**changes):
    return dict(road_segment_id='demo-r-001', repair_option_id='demo-resurface', dataset_snapshot_id='demo-m1-v1', **changes)


def test_save_retrieve_restart_immutable_snapshot_and_replay(client, db):
    response = client.post('/api/v1/estimates', json=request_body())
    assert response.status_code == 201, response.text
    record = response.json()['data']
    assert client.get('/api/v1/estimates/' + record['id']).json()['data'] == record
    snapshot = record['input_snapshot']
    assert canonical_hash(snapshot) == record['input_hash']
    replay = calculate(Road.model_validate(snapshot['road']), Assessment.model_validate(snapshot['assessment']), RepairOption.model_validate(snapshot['option']))
    assert canonical_hash(replay.model_dump(mode='json')) == record['result_hash']
    with connection(db) as conn:
        assert conn.execute('SELECT base_cents FROM estimates').fetchone()[0] == 5340000
        for sql in ['UPDATE estimates SET base_cents=0', 'DELETE FROM estimates']:
            with pytest.raises(sqlite3.IntegrityError, match='immutable'):
                conn.execute(sql)
        # Simulate future catalog changes; old snapshot must remain byte-equivalent.
        changed = copy.deepcopy(snapshot['option'])
        changed['unit_rates_usd'] = {'low': '1', 'base': '2', 'high': '3'}
        conn.execute('UPDATE repair_options SET payload=? WHERE id=?', (json.dumps(changed), changed['id']))
        conn.execute("DELETE FROM maintenance_assets WHERE road_id='demo-r-001'")
    with TestClient(create_app(Settings(database_path=db))) as restarted:
        assert restarted.get('/api/v1/estimates/' + record['id']).json()['data'] == record


@pytest.mark.parametrize('change,status', [({'road_segment_id': 'missing'}, 404), ({'repair_option_id': 'missing'}, 404),
    ({'dataset_snapshot_id': 'other'}, 409), ({'quantity': '-1'}, 422), ({'planning_assumptions': {'width_m': '0', 'note': 'test'}}, 422),
    ({'planning_assumptions': {'width_m': '8', 'unit': 'feet', 'note': 'test'}}, 422), ({'road_segment_id': 'demo-r-004'}, 422)])
def test_api_invalid_inputs(client, change, status):
    response = client.post('/api/v1/estimates', json={**request_body(), **change})
    assert response.status_code == status
    assert response.json()['error']['request_id']


def test_api_assumption_snapshot_and_cors(client):
    body = {**request_body(), 'road_segment_id': 'demo-r-004', 'planning_assumptions': {'length_m': '100', 'width_m': '8', 'note': 'Explicit hypothetical scope'}}
    response = client.post('/api/v1/estimates', json=body)
    assert response.status_code == 201
    record = response.json()['data']
    assert record['input_snapshot']['user-planning-assumption']['note'] == 'Explicit hypothetical scope'
    assert record['suitability']['status'] == 'requires_review'
    response = client.options('/api/v1/estimates', headers={'Origin': 'http://127.0.0.1:5173', 'Access-Control-Request-Method': 'POST', 'Access-Control-Request-Headers': 'content-type'})
    assert response.status_code == 200 and 'POST' in response.headers['access-control-allow-methods']


def test_migration_preserves_exact_m1_payloads_and_idempotent_seed(tmp_path):
    path = tmp_path / 'legacy.sqlite3'
    # Build an actual three-table M1 schema without initializing M2 first.
    conn = sqlite3.connect(path)
    conn.executescript('CREATE TABLE dataset(id TEXT PRIMARY KEY, manifest_json TEXT NOT NULL); CREATE TABLE evidence(id TEXT PRIMARY KEY,dataset_id TEXT NOT NULL REFERENCES dataset(id),payload TEXT NOT NULL); CREATE TABLE roads(id TEXT PRIMARY KEY,dataset_id TEXT NOT NULL REFERENCES dataset(id),payload TEXT NOT NULL);')
    manifest_payload = json.loads((ROOT / 'data/demo/manifest.json').read_text())
    conn.execute('INSERT INTO dataset VALUES (?,?)', ('demo-m1-v1', json.dumps(manifest_payload, sort_keys=True)))
    evidence = manifest_payload['evidence_source']
    conn.execute('INSERT INTO evidence VALUES (?,?,?)', (evidence['id'], 'demo-m1-v1', json.dumps(evidence)))
    for feature in json.loads((ROOT / 'data/demo/roads.geojson').read_text())['features']:
        payload = {**feature['properties'], 'geometry': feature['geometry']}
        conn.execute('INSERT INTO roads VALUES (?,?,?)', (payload['id'], 'demo-m1-v1', json.dumps(payload)))
    conn.commit()
    assert not conn.execute("SELECT name FROM sqlite_master WHERE name='schema_migrations'").fetchall()
    conn.close()
    with connection(path) as conn:
        before = conn.execute('SELECT * FROM roads ORDER BY id').fetchall()
        manifest = conn.execute('SELECT * FROM dataset').fetchall()
        # Re-run after additive migration and explicit fixture import.
    seed_m2(path)
    for _ in range(2):
        initialize(path)
        seed(path)
        assert seed_m2(path) == (5, 26, 3)
    with connection(path) as conn:
        assert before == conn.execute('SELECT * FROM roads ORDER BY id').fetchall()
        assert manifest == conn.execute('SELECT * FROM dataset').fetchall()
        assert conn.execute('SELECT COUNT(*) FROM assessments').fetchone()[0] == 26
        assert conn.execute('PRAGMA foreign_key_check').fetchall() == []
        assert conn.execute('SELECT * FROM schema_migrations').fetchall() == [(2, 'm2-additive-v1'), (3, 'm3-additive-v1'), (4, 'm4-additive-v1')]


def test_m2_bad_checksum_and_unresolved_references_atomic(db, tmp_path):
    fixture = tmp_path / 'fixture'
    fixture.mkdir()
    raw = (ROOT / 'data/demo/maintenance.json').read_bytes()
    manifest = json.loads((ROOT / 'data/demo/maintenance-manifest.json').read_text())
    (fixture / 'maintenance.json').write_bytes(raw + b' ')
    (fixture / 'maintenance-manifest.json').write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match='checksum'):
        seed_m2(db, fixture)
    payload = json.loads(raw)
    payload['assets'][0]['road_segment_id'] = 'missing'
    changed = json.dumps(payload).encode()
    manifest['checksum_sha256'] = manifest['evidence_source']['checksum_sha256'] = hashlib.sha256(changed).hexdigest()
    manifest['fixture_id'] = payload['fixture_id'] = 'new-fixture'
    (fixture / 'maintenance.json').write_bytes(changed)
    # Recompute after changing fixture id.
    changed = json.dumps(payload).encode()
    (fixture / 'maintenance.json').write_bytes(changed)
    manifest['checksum_sha256'] = manifest['evidence_source']['checksum_sha256'] = hashlib.sha256(changed).hexdigest()
    (fixture / 'maintenance-manifest.json').write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match='unresolved M2 road'):
        seed_m2(db, fixture)
    with connection(db) as conn:
        assert conn.execute('SELECT COUNT(*) FROM fixture_imports').fetchone()[0] == 1


def test_empty_m2_catalog_and_no_startup_seed(tmp_path):
    path = tmp_path / 'm1-only.sqlite3'
    seed(path)
    with TestClient(create_app(Settings(database_path=path))) as client:
        assert client.get('/api/v1/repair-options').json()['data'] == []
        assert client.get('/api/v1/road-segments/demo-r-001/conditions').json()['data'] == []
        assert client.get('/api/v1/road-segments/demo-r-001').json()['data']['length_m'] is None


def test_estimate_inputs_and_results_order_with_fractional_dimensions(db):
    road, assessment, option = inputs(db)
    for length, width in [('0.001', '0.001'), ('10.125', '7.875'), ('100000', '100')]:
        result = calculate(road, assessment, option, PlanningAssumptions(length_m=length, width_m=width, note='Synthetic sensitivity boundary'))
        totals = [Decimal(result.scenarios[name].total_usd) for name in ['low', 'base', 'high']]
        assert totals == sorted(totals)
        assert all(len(str(t).split('.')[-1]) == 2 for t in totals)
        assert result.quantity == Decimal(length) * Decimal(width)
    with pytest.raises(ValidationError):
        PlanningAssumptions(length_m='0.0001', note='Exceeds supported decimal precision')


def test_missing_dimension_basis_and_assessment_provenance_rejected(db):
    road, assessment, _ = inputs(db)
    with pytest.raises(ValidationError, match='dimension basis'):
        Road.model_validate({**road.model_dump(), 'dimension_basis': {}})
    with pytest.raises(ValidationError, match='provenance'):
        Assessment.model_validate({**assessment.model_dump(), 'field_evidence': {}})


def test_legacy_m1_dimensions_remain_readable_without_measurement_claims():
    feature = json.loads((ROOT / 'data/demo/roads.geojson').read_text())['features'][0]
    legacy = {**feature['properties'], 'geometry': feature['geometry'], 'length_m': '100', 'width_m': '8'}
    for field in ('length_m', 'width_m'):
        legacy['field_evidence'][field] = legacy['evidence_ids']
        legacy['unknown_reasons'].pop(field, None)
    road = Road.model_validate(legacy)
    assert road.repairable_area_m2 == 800
    assert road.dimension_basis == {'length_m': 'legacy_synthetic_basis_unknown', 'width_m': 'legacy_synthetic_basis_unknown'}


def test_seed_keeps_existing_asset_edits(db):
    with connection(db) as conn:
        raw = json.loads(conn.execute("SELECT payload FROM maintenance_assets WHERE road_id='demo-r-001'").fetchone()[0])
        raw['notes'] = 'Preserved local planning note'
        changed = json.dumps(raw)
        conn.execute("UPDATE maintenance_assets SET payload=? WHERE road_id='demo-r-001'", (changed,))
    seed_m2(db)
    with connection(db) as conn:
        assert conn.execute("SELECT payload FROM maintenance_assets WHERE road_id='demo-r-001'").fetchone()[0] == changed


def test_m2_manifest_immutable(db, tmp_path):
    fixture = tmp_path / 'changed-manifest'
    fixture.mkdir()
    (fixture / 'maintenance.json').write_bytes((ROOT / 'data/demo/maintenance.json').read_bytes())
    manifest = json.loads((ROOT / 'data/demo/maintenance-manifest.json').read_text())
    manifest['note'] = 'Changed source description under the same identity'
    (fixture / 'maintenance-manifest.json').write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match='immutable'):
        seed_m2(db, fixture)
