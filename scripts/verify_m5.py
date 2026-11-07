"""Repeatable synthetic M5 offline demonstration. Uses only a NEW temporary database.

PYTHONPATH=apps/api .venv/bin/python scripts/verify_m5.py
No key, network, fixture changes or existing database writes.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
from fastapi.testclient import TestClient
from app.core.config import Settings
from app.main import create_app
from app.models.database import connection
from app.seed import seed
from app.seed_m2 import seed_m2
from app.seed_m3 import seed_m3
from app.seed_m4 import seed_m4
from app.services.ai.providers import AISettings
from app.services.estimates import canonical_hash


def demonstrate():
    with TemporaryDirectory(prefix='civicplain-m5-') as temp:
        path = Path(temp)/'demo.sqlite3'
        seed(path); seed_m2(path); seed_m3(path); seed_m4(path)
        with TestClient(create_app(Settings(database_path=path), ai_settings=AISettings(provider='deterministic',api_key=''))) as c:
            def post(route, body):
                response = c.post('/api/v1/'+route, json=body)
                assert response.is_success, response.status_code
                return response.json()['data']
            road = c.get('/api/v1/road-segments/demo-r-001').json()['data']
            assert road['condition_summary']['category'] == 'poor'
            estimate = post('estimates', dict(road_segment_id=road['id'],repair_option_id='demo-resurface',dataset_snapshot_id='demo-m1-v1'))
            analysis = post('conflicts/analyze', dict(dataset_snapshot_id='demo-m1-v1',project_ids=['demo-road-project','demo-utility-project']))
            ids = [c.get(f'/api/v1/scenarios/demo-scenario-{s}/evaluations').json()['data'][0]['id'] for s in 'abc']
            with connection(path) as db:
                names = ['roads','estimates','work_projects','conflict_analyses','scenario_evaluations']
                before = {t:canonical_hash(db.execute(f'SELECT * FROM {t} ORDER BY id').fetchall()) for t in names}
            outputs = [post('ai/explain-estimate',dict(estimate_id=estimate['id'])),
                post('ai/explain-conflict',dict(conflict_id=analysis['findings'][0]['id'])),
                post('ai/explain-scenario-comparison',dict(evaluation_ids=ids,mode='ai')),
                post('ai/ask',dict(context=dict(type='road',record_ids=[road['id']]),question='Why is this road flagged?'))]
            assert outputs[2]['provider_status']=='fallback' and outputs[2]['fallback_reason']=='not_configured'
            assert all(o['citations'] and o['missing_information'] and o['human_review_required'] for o in outputs)
            insufficient=post('ai/ask',dict(context=dict(type='estimate',record_ids=[estimate['id']]),question='What happens if the city delays this repair?'))
            assert insufficient['validation_status']=='insufficient_evidence'
            with connection(path) as db:
                assert before == {t:canonical_hash(db.execute(f'SELECT * FROM {t} ORDER BY id').fetchall()) for t in names}
                assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
                assert not db.execute('PRAGMA foreign_key_check').fetchall()
                count = db.execute('SELECT COUNT(*) FROM ai_interactions').fetchone()[0]
            print('SYNTHETIC offline demo: road → saved estimate → potential conflict → three scenarios → grounded explanations.')
            print('Saved resurfacing base USD:',estimate['scenarios']['base']['total_usd'],'; preliminary days:',estimate['duration']['total_preliminary_days'])
            print('Potential rework gap:',analysis['findings'][0]['temporal_evidence']['gap_days'],'calendar days; no loss calculated.')
            print('AI request → deterministic fallback: not_configured. Future delay question → insufficient_evidence.')
            print(f'{count} audit records persisted; source tables unchanged; SQLite integrity and foreign keys passed.')


if __name__ == '__main__': demonstrate()
