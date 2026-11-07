"""Author repeatable M4 hypothetical fixtures; no rates or measured inputs are invented."""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/demo'


def build():
    projects = json.loads((OUT / 'projects.json').read_text())
    if isinstance(projects, dict):
        projects = projects['projects']
    original = next(p for p in projects if p['id'] == 'demo-road-project')
    scenarios = []
    dates = [('a', 'A — repair before utility work', '2027-04-01', '2027-04-08', 'Road repair precedes the supplied utility interval; potential rework is unpriced.'),
        ('b', 'B — repair after utility work', '2027-04-15', '2027-04-22', 'Road repair follows the utility interval. Deferral needs engineering review.'),
        ('c', 'C — explicitly coordinated work', '2027-04-10', '2027-04-17', 'Authored coordination assumption: roadwork and utility teams share an overlapping work window. This does not remove screening findings or produce savings.')]
    for key, name, start, end, note in dates:
        assumption = dict(id='planning', note='SYNTHETIC DEMO: $60,000 roadwork-only budget, approximate footprint, calendar dates and one-lane closure are authored planning assumptions. ' + note,
            field_paths=['repair_category', 'repair_option_id', 'scope', 'quantity', 'schedule', 'constraints', 'project_overrides', 'budget_usd'])
        prov = dict(basis='planning_assumption', evidence_ids=['assumption:planning'], note=assumption['note'])
        action = dict(id='road-repair', road_segment_id='demo-r-001', action_kind='repair', repair_category='resurface', repair_option_id='demo-resurface',
            scope=dict(extent='whole_segment', description='SYNTHETIC whole-road 100 m × 8 m authored repair scope; approximate project footprint only.', geometry=original['geometry'], location_status='approximate'),
            quantity=dict(value=None, unit='m2', derivation='road_dimensions', length_m=None, width_m=None),
            input_provenance={f: copy.deepcopy(prov) for f in ['repair_category', 'repair_option_id', 'scope', 'quantity', 'schedule', 'constraints']},
            unknown_reasons={}, related_project_ids=['demo-road-project', 'demo-utility-project'],
            schedule=dict(start_date=start, end_date=end, assumption_evidence_ids=['assumption:planning'], note=assumption['note'],
                closure_intervals=[dict(start_date=start, end_date=end, lanes_closed=1, evidence_ids=['assumption:planning'], note='SYNTHETIC one-lane closure includes setup/curing; independent of preliminary estimate days.')]))
        action['input_provenance']['scope.geometry'] = dict(basis='source_record', evidence_ids=original['field_evidence']['geometry'], record_id=original['id'], record_field='geometry')
        scenarios.append(dict(id=f'demo-scenario-{key}', draft=dict(name=name, description='SYNTHETIC HYPOTHETICAL DEMONSTRATION. ' + note,
            dataset_snapshot_id='demo-m1-v1', budget_usd='60000.00', planning_start='2027-04-01', planning_end='2027-05-01',
            actions=[action], assumptions=[assumption], external_project_ids=['demo-road-project', 'demo-utility-project'],
            project_overrides=[dict(project_id='demo-road-project', operation='replace', replacement_action_ids=['road-repair'],
                reason='SYNTHETIC alternative to original road schedule; original record remains untouched.', evidence_ids=['assumption:planning'])])))
    return scenarios


if __name__ == '__main__':
    raw = (json.dumps(build(), indent=2, ensure_ascii=False) + '\n').encode()
    (OUT / 'scenarios.json').write_bytes(raw)
    manifest = dict(id='demo-scenarios-v1', dataset_snapshot_id='demo-m1-v1', data_kind='synthetic', synthetic_input=True,
        file='scenarios.json', checksum_sha256=hashlib.sha256(raw).hexdigest(), scenario_ids=['demo-scenario-a', 'demo-scenario-b', 'demo-scenario-c'],
        limitations=['Hypothetical planning inputs, not municipal plans or measured quantities.',
            'No quantified shared mobilization, avoided restoration or savings. Utility costs excluded.',
            'B deferral and C coordinated overlap require human review. Existing catalog prices and sensitivity reused.'])
    (OUT / 'scenarios-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
