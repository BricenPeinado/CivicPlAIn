import json
import sqlite3
from datetime import date, datetime, timezone, timedelta

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from pyproj import Transformer
from shapely.geometry import box, mapping
from shapely import transform

from app.core.config import ROOT, Settings
from app.core.conflict_repository import ConflictRepository
from app.core.repository import RoadRepository
from app.main import create_app
from app.models.database import connection, initialize
from app.schemas.conflicts import WorkProject, WorkPolygon, AnalysisParameters
from app.schemas.roads import Road, Evidence
from app.seed import seed
from app.seed_m2 import seed_m2
from app.seed_m3 import seed_m3
from app.services.conflicts import analyze, projected


@pytest.fixture
def db(tmp_path):
    path = tmp_path / 'm3.sqlite3'
    seed(path)
    seed_m2(path)
    seed_m3(path)
    return path


@pytest.fixture
def client(db):
    with TestClient(create_app(Settings(database_path=db))) as c:
        yield c


def revise(project, **changes):
    raw = project.model_dump(mode='json')
    raw.update(changes)
    for key in ['geometry', 'start_date', 'end_date', 'actual_start_date', 'actual_end_date', 'lanes_closed', 'excavation_required', 'estimated_cost_usd']:
        if raw[key] is None:
            raw['unknown_reasons'][key] = 'test_explicit_unknown'
        else:
            raw['field_evidence'][key] = raw['evidence_ids']
    return WorkProject.model_validate(raw)


def pair(db):
    repo = ConflictRepository(db)
    return repo.project('demo-road-project'), repo.project('demo-utility-project')


def run(db, projects, **params):
    repo = RoadRepository(db)
    roads, _ = repo.list(100, None, None)
    refs = sorted({s for p in projects for s in p.evidence_ids} | {s for r in roads for s in r.evidence_ids})
    return analyze(projects, roads, AnalysisParameters(**params), [repo.evidence(s) for s in refs], datetime(2026, 11, 7, tzinfo=timezone.utc))


def types(result):
    return {f.finding_type for f in result.findings}


def test_fixture_reopening_and_source_preservation(db):
    result = run(db, list(pair(db)))
    assert types(result) == {'reopening_risk'}
    f = result.findings[0]
    assert f.temporal_evidence.gap_days == 2
    assert f.spatial_evidence.polygon_overlap
    assert f.spatial_evidence.shared_road_ids == ['demo-r-001']
    assert 'demo-project-assumptions-v1' in f.evidence_ids
    assert 'demo-roads-assumptions-v1' in f.evidence_ids or len(f.evidence_ids) >= 2
    assert f.synthetic_input and f.priority == 'coordination_review'
    assert 'financial loss' in f.explanation
    assert result.input_snapshot['sources'] and result.utility_coverage == 'unknown'


def test_same_road_without_geometry_retains_known_findings_and_unknown(db):
    a, b = pair(db)
    b = revise(b, geometry=None, location_status='unknown')
    result = run(db, [a, b])
    assert types(result) == {'reopening_risk'}
    assert result.findings[0].spatial_evidence.distance_m is None
    assert result.indeterminate_checks[0].missing_fields == [b.id + '.geometry']
    b = revise(b, road_segment_ids=[])
    result = run(db, [a, b])
    assert not result.findings and result.indeterminate_checks


def test_overlapping_polygons_without_road_links(db):
    a, b = pair(db)
    a = revise(a, road_segment_ids=[], location_status='source_reported')
    b = revise(b, road_segment_ids=[], location_status='source_reported', start_date='2027-04-05')
    result = run(db, [a, b])
    assert 'concurrent_work' in types(result)
    assert 'confirmed_geometric_overlap' in result.findings[0].spatial_evidence.classifications
    assert result.findings[0].temporal_evidence.overlap_end == date(2027, 4, 8)


def metric_polygon(x, y, width=10, height=5):
    inverse = Transformer.from_crs(32618, 4326, always_xy=True)
    return mapping(transform(box(x, y, x + width, y + height), inverse.transform, interleaved=False))


def test_distance_threshold_in_meters_and_unrelated(db):
    a, b = pair(db)
    # Offset away from road corridors; independent, non-overlapping rectangles.
    x, y = projected(a.geometry).centroid.coords[0]
    a = revise(a, geometry=metric_polygon(x, y + 80), road_segment_ids=[])
    b = revise(b, geometry=metric_polygon(x + 15, y + 80), road_segment_ids=[], start_date='2027-04-03')
    assert projected(a.geometry).distance(projected(b.geometry)) == pytest.approx(5, abs=1e-7)
    assert 'concurrent_work' in types(run(db, [a, b], proximity_m=5, corridor_m=0))
    assert not run(db, [a, b], proximity_m=4.999999, corridor_m=0).findings
    b = revise(b, geometry=metric_polygon(x + 100, y + 80))
    result = run(db, [a, b], corridor_m=0)
    assert not result.findings and result.checked_pair_count == 0


@pytest.mark.parametrize('gap,expected', [(0, True), (30, True), (31, False)])
def test_sequential_horizon_boundary(db, gap, expected):
    a, b = pair(db)
    start = a.end_date + timedelta(days=gap)
    b = revise(b, start_date=start, end_date=start + timedelta(days=2))
    result = run(db, [a, b])
    assert ('reopening_risk' in types(result)) is expected
    assert 'concurrent_work' not in types(result)


def test_concurrent_and_multiple_closures_and_multi_road(db):
    a, b = pair(db)
    c = ConflictRepository(db).project('demo-concurrent-project')
    result = run(db, [a, b, c])
    assert result.possible_pair_count == 3
    assert {'concurrent_work', 'multiple_closures', 'reopening_risk'} <= types(result)
    assert len({(tuple(f.project_ids), f.finding_type) for f in result.findings}) == len(result.findings)
    assert any('demo-r-002' in f.affected_road_ids for f in result.findings)


def test_shared_corridor_even_distant_workzones(db):
    a, b = pair(db)
    # Disjoint footprints at different portions of the same schematic road.
    road = RoadRepository(db).get('demo-r-001')
    coords = projected(road.geometry).coords
    from shapely.geometry import Point
    inverse = Transformer.from_crs(32618, 4326, always_xy=True)
    a = revise(a, geometry=mapping(transform(Point(coords[0]).buffer(2).envelope, inverse.transform, interleaved=False)), road_segment_ids=[])
    b = revise(b, geometry=mapping(transform(Point(coords[-1]).buffer(2).envelope, inverse.transform, interleaved=False)), road_segment_ids=[], start_date='2027-04-04')
    f = run(db, [a, b]).findings[0]
    assert f.spatial_evidence.shared_corridor_ids == ['demo-r-001']
    assert f.spatial_evidence.distance_m > 5
    assert not f.spatial_evidence.polygon_overlap
    assert any('grade' in w for w in f.data_quality_warnings)


def test_line_crossing_is_potential_not_confirmed_excavation(db):
    a, b = pair(db)
    a = revise(a, geometry={'type':'LineString', 'coordinates':[[-74.010,40.7115],[-74.0098,40.7117]]}, road_segment_ids=[])
    b = revise(b, geometry={'type':'LineString', 'coordinates':[[-74.010,40.7117],[-74.0098,40.7115]]}, road_segment_ids=[])
    f = run(db, [a, b]).findings[0]
    assert f.spatial_evidence.geometry_intersects and not f.spatial_evidence.polygon_overlap
    assert 'confirmed_geometric_overlap' not in f.spatial_evidence.classifications


def test_missing_dates_and_location_and_cancelled(db):
    a, b = pair(db)
    b = revise(b, start_date=None)
    result = run(db, [a, b])
    assert not result.findings and result.indeterminate_checks
    assert any('.planned_start_date' in f for f in result.indeterminate_checks[0].missing_fields)
    result = run(db, [a, revise(b, schedule_status='cancelled')])
    assert result.excluded_project_ids == [b.id] and result.possible_pair_count == 0
    assert any('Fewer' in w for w in result.warnings)


def test_completed_uses_actual_dates_and_no_future_destruction_claim(db):
    a, b = pair(db)
    a = revise(a, schedule_status='completed')
    assert not run(db, [a, b]).findings
    a = revise(a, actual_start_date='2027-04-01', actual_end_date='2027-04-08')
    assert 'reopening_risk' in types(run(db, [a, b]))
    b = revise(b, excavation_required=False)
    assert types(run(db, [a, b])) == {'sequencing_review'}


@pytest.mark.parametrize('changes', [
    {'end_date':'2027-03-01'}, {'schedule_status':'approved'}, {'estimated_cost_usd':'-1'},
    {'currency':'EUR'}, {'location_status':'unknown'}, {'lanes_closed':-1}, {'infrastructure_category':'gas'},
    {'geometry':{'type':'Polygon','coordinates':[[[-74.01,40.711],[-74.009,40.712],[-74.01,40.712],[-74.009,40.711],[-74.01,40.711]]]}},
    {'geometry':{'type':'Polygon','coordinates':[[[-74.01,40.711],[-74.009,40.711],[-74.009,40.712],[-74.01,40.712]]]}},
    {'geometry':{'type':'LineString','coordinates':[[0,0],[0.1,0.1]]}},
    {'geometry':{'type':'LineString','coordinates':[[float('nan'),40.71],[-74.01,40.72]]}},
])
def test_project_validation(db, changes):
    with pytest.raises(ValidationError):
        revise(pair(db)[0], **changes)


def test_stability_replay_unknown_references_and_dedup(db):
    projects = ConflictRepository(db).projects()
    first = run(db, projects)
    second = run(db, projects[::-1])
    assert first.model_dump_json() == second.model_dump_json()
    saved = first.input_snapshot
    replay = analyze([WorkProject.model_validate(p) for p in saved['projects']], [Road.model_validate(r) for r in saved['roads']],
        AnalysisParameters.model_validate(saved['parameters']), [Evidence.model_validate(e) for e in saved['sources']], first.detected_at)
    assert replay.result_hash == first.result_hash
    repo = ConflictRepository(db)
    assert repo.save(first) == repo.save(second)
    assert len(repo.findings()) == len(first.findings)
    a, b = pair(db)
    with pytest.raises(ValueError, match='unknown affected road'):
        run(db, [a, revise(b, road_segment_ids=['missing'])])
    with pytest.raises(ValueError, match='distinct'):
        run(db, [a, a])
    with pytest.raises(sqlite3.IntegrityError, match='immutable'):
        with connection(db) as conn:
            conn.execute('DELETE FROM conflict_analyses')


def body(client, **changes):
    projects = client.get('/api/v1/projects').json()['data']
    return dict(dataset_snapshot_id='demo-m1-v1', project_ids=[p['id'] for p in projects], **changes)


def test_api_analysis_retrieval_pagination_filters_and_regression(client, db):
    payload = body(client)
    response = client.post('/api/v1/conflicts/analyze', json=payload)
    assert response.status_code == 200, response.text
    analysis = response.json()['data']
    assert analysis['indeterminate_checks'] and analysis['utility_coverage'] == 'unknown'
    repeated = client.post('/api/v1/conflicts/analyze', json=payload).json()['data']
    assert repeated == analysis
    assert client.get('/api/v1/conflict-analyses/' + analysis['id']).json()['data'] == analysis
    page = client.get('/api/v1/conflicts?limit=1').json()
    assert page['meta']['next_cursor']
    assert client.get('/api/v1/conflicts', params={'cursor':page['meta']['next_cursor'], 'project_id':'demo-road-project'}).status_code == 422
    findings = client.get('/api/v1/conflicts', params={'analysis_id':analysis['id'], 'road_segment_id':'demo-r-001'}).json()['data']
    assert findings and all('demo-r-001' in f['affected_road_ids'] for f in findings)
    assert client.get('/api/v1/conflicts/' + findings[0]['id']).json()['data'] == findings[0]
    assert len(client.get('/api/v1/projects?road_segment_id=demo-r-002').json()['data']) == 1
    assert client.get('/api/v1/projects/demo-utility-project').status_code == 200
    assert client.get('/api/v1/projects?kind=bad').status_code == 422
    assert client.get('/api/v1/projects?road_segment_id=missing').status_code == 404
    for path in ['/projects/missing','/conflicts/missing','/conflict-analyses/missing']:
        assert client.get('/api/v1' + path).status_code == 404
    # Existing M2 estimate API must retain exact synthetic arithmetic.
    estimate = client.post('/api/v1/estimates', json=dict(road_segment_id='demo-r-001', repair_option_id='demo-resurface', dataset_snapshot_id='demo-m1-v1'))
    assert estimate.status_code == 201
    assert estimate.json()['data']['scenarios']['base']['total_usd'] == '53400.00'
    with TestClient(create_app(Settings(database_path=db))) as restarted:
        assert restarted.get('/api/v1/conflict-analyses/' + analysis['id']).json()['data'] == analysis


@pytest.mark.parametrize('change,status', [({'project_ids':[]},422), ({'project_ids':['demo-road-project']*2},422),
    ({'project_ids':['missing']},404), ({'proximity_m':-1},422), ({'proximity_m':101},422), ({'corridor_m':51},422),
    ({'reopening_horizon_days':31.5},422), ({'dataset_snapshot_id':'missing'},409), ({'unit':'degrees'},422)])
def test_api_errors(client, change, status):
    payload = body(client)
    payload.update(change)
    response = client.post('/api/v1/conflicts/analyze', json=payload)
    assert response.status_code == status, response.text
    assert response.json()['error']['request_id']


def test_additive_migration_and_seed_preserve_existing(db):
    with connection(db) as conn:
        before = conn.execute('SELECT payload FROM roads ORDER BY id').fetchall()
        project = json.loads(conn.execute("SELECT payload FROM work_projects WHERE id='demo-road-project'").fetchone()[0])
        project['description'] = 'Preserve local authored changes'
        changed = json.dumps(project)
        conn.execute("UPDATE work_projects SET payload=? WHERE id='demo-road-project'", (changed,))
    initialize(db)
    assert seed_m3(db) == 7
    with connection(db) as conn:
        assert conn.execute('SELECT payload FROM roads ORDER BY id').fetchall() == before
        assert conn.execute("SELECT payload FROM work_projects WHERE id='demo-road-project'").fetchone()[0] == changed
        assert conn.execute('SELECT count(*) FROM project_roads').fetchone()[0] == 6
        assert conn.execute('SELECT max(version) FROM schema_migrations').fetchone()[0] == 5


def test_unseeded_api_no_auto_import(tmp_path):
    with TestClient(create_app(Settings(database_path=tmp_path / 'empty.sqlite'))) as c:
        assert c.get('/api/v1/projects').json()['data'] == []
        assert c.get('/api/v1/conflicts').json()['data'] == []


def test_saved_snapshot_survives_project_source_changes_and_new_parameters(db):
    repo = ConflictRepository(db)
    original = repo.save(run(db, list(pair(db))))
    a, b = pair(db)
    changed = repo.save(run(db, [a, revise(b, start_date='2027-04-12')]))
    assert changed.id != original.id and changed.findings[0].id != original.findings[0].id
    assert repo.analysis(original.id) == original
    assert original.findings[0].temporal_evidence.gap_days == 2
    assert changed.findings[0].temporal_evidence.gap_days == 4
    assert run(db, [a, b], proximity_m=6).input_hash != original.input_hash
    # Method source contents themselves are frozen and affect input identity.
    inputs = original.input_snapshot
    sources = [Evidence.model_validate(e) for e in inputs['sources']]
    sources[0] = sources[0].model_copy(update={'reliability_note': 'Updated explicit source limitation'})
    altered = analyze([a, b], [Road.model_validate(r) for r in inputs['roads']], sources=sources)
    assert altered.input_hash != original.input_hash
    assert repo.analysis(original.id).input_snapshot['sources'] == inputs['sources']


def test_fixture_checksum_and_immutable_manifest_rejection(db, tmp_path):
    fixtures = tmp_path / 'fixtures'
    fixtures.mkdir()
    raw = (ROOT / 'data/demo/projects.json').read_bytes()
    manifest = json.loads((ROOT / 'data/demo/projects-manifest.json').read_text())
    (fixtures / 'projects.json').write_bytes(raw + b' ')
    (fixtures / 'projects-manifest.json').write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match='checksum'):
        seed_m3(db, fixtures)
    (fixtures / 'projects.json').write_bytes(raw)
    manifest['note'] = 'Different manifest under same fixture ID'
    (fixtures / 'projects-manifest.json').write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match='immutable'):
        seed_m3(db, fixtures)


def test_project_pagination_and_cross_endpoint_cursor(client):
    page = client.get('/api/v1/projects?limit=2').json()
    cursor = page['meta']['next_cursor']
    second = client.get('/api/v1/projects', params={'limit':2,'cursor':cursor}).json()
    assert {p['id'] for p in page['data']}.isdisjoint(p['id'] for p in second['data'])
    assert client.get('/api/v1/conflicts', params={'cursor':cursor}).status_code == 422
    assert client.get('/api/v1/projects?road_segment_id=demo-r-024').json()['data'] == []


def test_synthetic_source_flag_propagates_even_if_project_classification_is_observed(db):
    a, b = pair(db)
    x, y = projected(a.geometry).centroid.coords[0]
    a = revise(a, id='source-reported-a', data_kind='observed', synthetic_input=False,
        geometry=metric_polygon(x, y + 80), road_segment_ids=[])
    b = revise(b, id='source-reported-b', data_kind='observed', synthetic_input=False,
        geometry=metric_polygon(x, y + 80), road_segment_ids=[])
    # Current EvidenceSource supports demo assumptions only; do not lose that
    # synthetic dependency just because a project classifier says observed.
    result = run(db, [a, b], corridor_m=0)
    assert result.findings and result.findings[0].affected_road_ids == []
    assert result.findings[0].synthetic_input is True
