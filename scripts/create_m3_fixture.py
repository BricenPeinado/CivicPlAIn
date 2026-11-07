"""Reproduce fictional M3 coordination records; never municipal observations."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'demo-project-assumptions-v1'


def polygon(w, s, e, n):
    return dict(type='Polygon', coordinates=[[[w, s], [e, s], [e, n], [w, n], [w, s]]])


footprint = polygon(-74.0106, 40.71148, -74.0094, 40.71172)
water = polygon(-74.0102, 40.71150, -74.0096, 40.71170)
records = []
for pid, title, category, work, roads, geom, start, end, excavation in [
    ('road-project', 'Fictional R-001 resurfacing', 'road_resurfacing', 'resurfacing', ['demo-r-001'], footprint, '2027-04-01', '2027-04-08', False),
    ('utility-project', 'Fictional water excavation after resurfacing', 'water', 'excavation', ['demo-r-001'], water, '2027-04-10', '2027-04-15', True),
    ('concurrent-project', 'Fictional sewer work during resurfacing', 'sewer', 'excavation', ['demo-r-001', 'demo-r-002'], water, '2027-04-05', '2027-04-11', True),
    ('unrelated-project', 'Fictional distant telecom inspection', 'telecommunications', 'inspection', ['demo-r-009'], polygon(-74.0030, 40.7158, -74.0026, 40.7160), '2027-04-02', '2027-04-06', False),
    ('unknown-location', 'Fictional gas project — location unknown', 'gas', 'excavation', [], None, '2027-04-03', '2027-04-10', None),
    ('unknown-schedule', 'Fictional electric work — schedule unknown', 'electric', 'maintenance', ['demo-r-001'], water, None, None, None),
    ('nearby-project', 'Fictional nearby water inspection', 'water', 'inspection', [], polygon(-74.0102, 40.711735, -74.0096, 40.711755), '2027-04-03', '2027-04-06', False),
]:
    record = dict(id='demo-' + pid, title=title, description='Entirely invented coordination example. No municipal project, utility route or actual schedule is asserted.',
        kind='road_repair' if category.startswith('road_') else 'utility', infrastructure_category=category, work_type=work,
        responsible_organization='Fictional CivicPlAIn demo organization', schedule_status='planned' if start else 'unknown',
        schedule_basis='assumed_demo' if start else 'unknown', start_date=start, end_date=end, actual_start_date=None, actual_end_date=None,
        geometry=geom, location_status='approximate' if geom else 'unknown', road_segment_ids=roads,
        excavation_required=excavation, lanes_closed=1 if roads else None, estimated_cost_usd=None, currency='USD',
        dataset_snapshot_id='demo-m1-v1', evidence_ids=[SOURCE], data_kind='synthetic', synthetic_input=True,
        created_at='2026-11-07T00:00:00Z', updated_at='2026-11-07T00:00:00Z',
        limitations=['Fictional schedules and approximate authored work zones; no observed utility location, depth or positional accuracy.'])
    fields = ['infrastructure_category', 'work_type', 'schedule_status', 'schedule_basis', 'location_status', 'road_segment_ids', 'geometry', 'start_date', 'end_date', 'actual_start_date', 'actual_end_date', 'responsible_organization', 'excavation_required', 'lanes_closed', 'estimated_cost_usd']
    record['field_evidence'] = {key: [SOURCE] for key in fields if record[key] is not None}
    record['unknown_reasons'] = {key: 'not_supplied_in_fictional_fixture' for key in fields if record[key] is None}
    records.append(record)
payload = dict(fixture_id='demo-m3-v1', dataset_snapshot_id='demo-m1-v1', evidence_id=SOURCE, synthetic_input=True, projects=records)
raw = (json.dumps(payload, indent=2) + '\n').encode()
(ROOT / 'data/demo/projects.json').write_bytes(raw)
checksum = hashlib.sha256(raw).hexdigest()
manifest = dict(fixture_id='demo-m3-v1', dataset_snapshot_id='demo-m1-v1', synthetic_input=True, file='projects.json',
    checksum_sha256=checksum, generator='scripts/create_m3_fixture.py', project_count=len(records), project_ids=[r['id'] for r in records],
    expected_examples=dict(reopening_pair=['demo-road-project', 'demo-utility-project'], reopening_gap_days=2,
        concurrent_pair=['demo-road-project', 'demo-concurrent-project'], overlap=['2027-04-05', '2027-04-08'],
        unrelated='demo-unrelated-project', unknown_location='demo-unknown-location', unknown_schedule='demo-unknown-schedule'),
    evidence_source=dict(id=SOURCE, title='CivicPlAIn fictional M3 work zones and coordination schedules', publisher='CivicPlAIn demo authors',
        source_kind='demo_assumption', verification_status='synthetic_demo', uri='data/demo/projects.json', retrieved_at=None, observed_on=None,
        version='demo-m3-v1', checksum_sha256=checksum, original_crs='EPSG:4326',
        coverage_note='Seven fictional projects inside the schematic study window; includes incomplete location and schedule.',
        reliability_note='Authored approximate polygons, categories, organizations, lane closures and dates; no observed utilities or real municipal schedules.',
        license_note='Original fictional CivicPlAIn demo records; no redistributed third-party utility data.',
        unknown_reasons=dict(observed_on='not_observed', retrieved_at='authored_fixture')))
(ROOT / 'data/demo/projects-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
