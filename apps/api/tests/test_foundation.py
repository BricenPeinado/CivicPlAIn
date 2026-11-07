import copy
import hashlib
import json
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import ROOT, Settings
from app.core.repository import RoadRepository
from app.main import create_app
from app.models.database import connection
from app.schemas.roads import Geometry, Road
from app.seed import seed


@pytest.fixture
def db(tmp_path):
    path = tmp_path / "roads.sqlite3"
    seed(path)
    return path


@pytest.fixture
def client(db):
    with TestClient(create_app(Settings(database_path=db))) as client:
        yield client


def test_health_and_empty_state(tmp_path):
    with TestClient(create_app(Settings(database_path=tmp_path / "empty.sqlite3"))) as client:
        health = client.get('/api/v1/health')
        assert health.status_code == 200
        assert health.json()['data'] == {'status': 'ok', 'api_version': 'v1', 'data_ready': False, 'ai_mode': 'deterministic'}
        assert health.json()['meta']['dataset_snapshot_id'] is None
        assert client.get('/api/v1/road-segments').json()['data'] == []
        assert client.get('/api/v1/road-segments/geojson').json()['features'] == []


def test_geojson_contract_and_counts(client):
    response = client.get('/api/v1/road-segments/geojson')
    assert response.status_code == 200
    assert response.headers['content-type'] == 'application/geo+json'
    body = response.json()
    assert body['type'] == 'FeatureCollection'
    assert len(body['features']) == 24
    assert body['meta']['warnings'] and body['meta']['dataset_snapshot_id'] == 'demo-m1-v1'
    assert response.headers['x-request-id'] == body['meta']['request_id']
    counts = dict.fromkeys(['good', 'fair', 'poor', 'unknown'], 0)
    for feature in body['features']:
        road = Road.model_validate({**feature['properties'], 'geometry': feature['geometry']})
        assert feature['id'] == road.id
        assert road.synthetic_input and road.data_kind == 'synthetic'
        assert road.condition_summary.assessed_on is None
        counts[road.condition_summary.category] += 1
    assert set(counts.values()) == {6}


def test_roads_detail_evidence_and_unknown(client):
    listed = client.get('/api/v1/road-segments').json()['data']
    assert [r['id'] for r in listed] == sorted(r['id'] for r in listed)
    detail = client.get('/api/v1/road-segments/demo-r-001').json()['data']
    assert detail == listed[0]
    assert detail['condition_summary']['rating'] == '3'
    assert detail['width_m'] is None and detail['unknown_reasons']['width_m']
    assert client.get('/api/v1/road-segments/not-found').status_code == 404
    assert client.get('/api/v1/evidence-sources/not-found').status_code == 404
    evidence = client.get('/api/v1/evidence-sources/demo-assumptions-v1').json()['data']
    assert evidence['verification_status'] == 'synthetic_demo'
    assert evidence['observed_on'] is None


def test_pagination_and_filters(client):
    first = client.get('/api/v1/road-segments?limit=5').json()
    cursor = first['meta']['next_cursor']
    second = client.get('/api/v1/road-segments', params={'limit': 5, 'cursor': cursor}).json()
    assert first['data'][-1]['id'] < second['data'][0]['id']
    assert client.get('/api/v1/road-segments', params={'bbox': '-1,1,1,2'}).json()['data'] == []
    assert len(client.get('/api/v1/road-segments', params={'bbox': '-74.012,40.710,-74,40.720'}).json()['data']) == 24
    assert client.get('/api/v1/road-segments', params={'cursor': cursor, 'bbox': '-1,1,1,2'}).status_code == 422


@pytest.mark.parametrize('query', ['limit=0', 'limit=101', 'cursor=bad', 'cursor=e30=', 'bbox=1,2,0,3', 'bbox=nan,0,1,1', 'bbox=0,0,1', 'bbox=0,0,1,91'])
def test_invalid_query_errors(client, query):
    response = client.get('/api/v1/road-segments?' + query)
    assert response.status_code == 422
    error = response.json()['error']
    assert error['code'] == 'VALIDATION_ERROR' and error['field_errors'] and error['request_id']


def test_seed_repeatability_restart_and_foreign_keys(db):
    before = RoadRepository(db).get('demo-r-001').model_dump_json()
    assert seed(db) == 24
    assert RoadRepository(db).count() == 24
    assert RoadRepository(db).get('demo-r-001').model_dump_json() == before
    with TestClient(create_app(Settings(database_path=db))) as client:
        assert client.get('/api/v1/health').json()['data']['data_ready'] is True
    with connection(db) as conn:
        assert conn.execute('PRAGMA foreign_keys').fetchone()[0] == 1
        assert conn.execute('SELECT COUNT(*) FROM evidence').fetchone()[0] == 1
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("INSERT INTO roads VALUES ('bad', 'missing', '{}')")


@pytest.mark.parametrize('coordinates', [[], [[0, 0]], [[1, 2], [1, 2]], [[181, 0], [0, 1]], [[0, float('inf')], [1, 2]], [[0, 0, 1], [1, 1, 1]]])
def test_geometry_rejects_invalid(coordinates):
    with pytest.raises(ValidationError):
        Geometry(type='LineString', coordinates=coordinates)


def test_boundary_provenance_and_condition_validation(db):
    road = RoadRepository(db).get('demo-r-001').model_dump(mode='json')
    for mutate in [lambda r: r.update(width_m='-1'), lambda r: r.update(field_evidence={}),
                   lambda r: r['condition_summary'].update(category='good'),
                   lambda r: r['unknown_reasons'].pop('width_m')]:
        invalid = copy.deepcopy(road)
        mutate(invalid)
        with pytest.raises(ValidationError):
            Road.model_validate(invalid)


def test_checksum_and_outside_geometry_are_rejected_atomically(tmp_path):
    fixture = tmp_path / 'fixture'
    fixture.mkdir()
    raw = (ROOT / 'data/demo/roads.geojson').read_bytes()
    manifest = json.loads((ROOT / 'data/demo/manifest.json').read_text())
    (fixture / 'manifest.json').write_text(json.dumps(manifest))
    (fixture / 'roads.geojson').write_bytes(raw + b' ')
    with pytest.raises(ValueError, match='checksum'):
        seed(tmp_path / 'bad.sqlite3', fixture)
    collection = json.loads(raw)
    collection['features'][0]['geometry']['coordinates'] = [[1, 1], [2, 2]]
    changed = json.dumps(collection).encode()
    checksum = hashlib.sha256(changed).hexdigest()
    manifest['files']['roads.geojson']['checksum_sha256'] = checksum
    manifest['evidence_source']['checksum_sha256'] = checksum
    (fixture / 'roads.geojson').write_bytes(changed)
    (fixture / 'manifest.json').write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match='bounds'):
        seed(tmp_path / 'bad.sqlite3', fixture)
    assert not (tmp_path / 'bad.sqlite3').exists()


def test_local_cors_and_errors(client, tmp_path):
    allowed = client.get('/api/v1/health', headers={'Origin': 'http://localhost:5173'})
    assert allowed.headers['access-control-allow-origin'] == 'http://localhost:5173'
    denied = client.get('/api/v1/health', headers={'Origin': 'https://untrusted.example'})
    assert 'access-control-allow-origin' not in denied.headers
    assert client.post('/api/v1/road-segments').status_code == 405
    with pytest.raises(ValueError, match='local HTTP'):
        Settings(allowed_origins=('https://untrusted.example',))
    # A directory cannot serve as a SQLite file; no filesystem details escape.
    with TestClient(create_app(Settings(database_path=tmp_path))) as broken:
        response = broken.get('/api/v1/health')
        assert response.status_code == 503
        assert response.json()['error']['message'] == 'Local storage is unavailable'
        assert str(tmp_path) not in response.text


def test_blank_environment_defaults_and_local_origin_validation(monkeypatch):
    monkeypatch.setenv('CIVICPLAIN_DATABASE_PATH', '')
    monkeypatch.setenv('CIVICPLAIN_ALLOWED_ORIGINS', '')
    settings = Settings()
    assert settings.database_path == ROOT / 'data/tmp/civicplain.sqlite3'
    assert settings.allowed_origins == ('http://127.0.0.1:5173', 'http://localhost:5173')
    for origin in ['*', 'http://localhost:5173/path', 'http://localhost:5173?query', 'http://localhost']:
        with pytest.raises(ValueError):
            Settings(allowed_origins=(origin,))


def test_snapshot_manifest_cannot_change_in_place(db, tmp_path):
    fixture = tmp_path / 'changed'
    fixture.mkdir()
    (fixture / 'roads.geojson').write_bytes((ROOT / 'data/demo/roads.geojson').read_bytes())
    manifest = json.loads((ROOT / 'data/demo/manifest.json').read_text())
    manifest['coverage_note'] = 'changed in place'
    (fixture / 'manifest.json').write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match='immutable'):
        seed(db, fixture)
    assert RoadRepository(db).count() == 24
