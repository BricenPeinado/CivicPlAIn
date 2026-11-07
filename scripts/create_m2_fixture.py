"""Reproduce reviewed synthetic M2 planning assumptions without altering M1."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'demo-maintenance-assumptions-v1'
assets = []
for number, length, width in [(1, '100', '8'), (2, '120', '7'), (3, '150', '8'), (4, None, None), (5, '900', '12')]:
    assets.append(dict(road_segment_id=f'demo-r-{number:03}', length_m=length, width_m=width,
        surface_material='unknown' if number == 4 else 'asphalt', functional_class='unknown' if number == 4 else 'local',
        dimension_basis='synthetic_planning_assumption', evidence_ids=[SOURCE], data_kind='synthetic', synthetic_input=True,
        notes='Authored rectangular repair scope, unrelated to measured geometry; not actual pavement dimensions.'))
options = []
for treatment, label, rates, mobil, traffic, contingency, productivity, setup, curing, description, scope, materials, activities in [
    ('preventive', 'Preventive maintenance', ['4.80', '6.00', '7.80'], '1500', '500', '.20', '1200', 1, 0,
     'Surface preservation for the good-condition demonstration case.', 'Clean, seal and apply a thin surface treatment.', 'Demo asphalt-compatible seal treatment.', ['Surface cleaning', 'Crack sealing', 'Surface treatment']),
    ('resurface', 'Resurfacing or rehabilitation', ['36.00', '45.00', '58.50'], '6000', '2500', '.20', '600', 2, 1,
     'Surface rehabilitation for the fair-condition demonstration case.', 'Mill and replace an assumed shallow asphalt surface layer.', 'Demo asphalt overlay; thickness included in bundled rate, not measured.', ['Milling', 'Surface preparation', 'Asphalt placement', 'Compaction']),
    ('reconstruct', 'Full-depth reconstruction', ['112.00', '140.00', '182.00'], '20000', '6000', '.25', '200', 3, 3,
     'Potential structural replacement for the poor-condition demonstration case.', 'Remove pavement and replace an assumed pavement/base structure.', 'Demo asphalt and aggregate base; structure requires design review.', ['Pavement removal', 'Base preparation', 'Pavement replacement', 'Compaction']),
]:
    options.append(dict(id=f'demo-{treatment}', treatment=treatment, label=label, description=description, scope_of_work=scope,
        suitability_conditions='Dated synthetic 1–10 scale: good >=8 screens preventive, fair >=5 screens resurface, poor <5 screens reconstruct; asphalt only. All require engineering review.',
        material_assumptions=materials, work_activities=activities, quantity_unit='m2',
        unit_rates_usd=dict(zip(['low', 'base', 'high'], rates)),
        rate_inclusions='materials, labor and equipment bundled; do not add them again',
        mobilization_usd=mobil, traffic_management_usd=traffic, contingency_fraction=contingency,
        productivity_per_day=productivity, productivity_unit='m2/active_workday', setup_days=setup, curing_days=curing,
        price_basis_date='2026-11-07', sensitivity_basis='Synthetic rate sensitivity: low bundled rate = base −20%; high = base +30%. Quantity, allowances and productivity fixed. Scenarios are assumptions, not probabilities.',
        exclusions=['Utility relocation, drainage redesign, permits, taxes and design fees excluded.'],
        limitations=['No verified subsurface, structural or drainage investigation.', 'Single assumed crew; no weather, weekends, traffic phasing or contractor schedule.'],
        evidence_ids=[SOURCE], data_kind='synthetic', synthetic_input=True))
assessments = []
# Preserve M1 scale, categories and evidence as undated historical records for all roads.
roads = json.loads((ROOT / 'data/demo/roads.geojson').read_text())['features']
for feature in roads:
    road = feature['properties']
    if road['condition_summary']['rating'] is not None:
        assessments.append(dict(**road['condition_summary'], id=f"{road['id']}-assessment-m1", road_segment_id=road['id'],
            dataset_snapshot_id='demo-m1-v1', assessment_method='synthetic_fixture', notes='Undated M1 authored condition, not an inspection.'))
for number, rating, category in [(1, '3', 'poor'), (2, '9', 'good'), (3, '6', 'fair'), (5, '3', 'poor')]:
    for stamp in ['2026-06-01', '2026-10-01']:
        assessments.append(dict(id=f'demo-r-{number:03}-assessment-{stamp}', road_segment_id=f'demo-r-{number:03}',
            dataset_snapshot_id='demo-m1-v1', category=category, rating=rating, rating_scale='synthetic-1-10-higher-better',
            assessed_on=stamp, evidence_ids=[SOURCE], data_kind='synthetic', synthetic_input=True,
            assessment_method='synthetic_fixture', notes='Invented demonstration date and condition; not a certified engineering inspection.'))
for assessment in assessments:
    assessment['created_at'] = '2026-11-07T00:00:00Z'
    assessment['field_evidence'] = {f: assessment['evidence_ids'] for f in ['rating', 'category', 'assessed_on'] if assessment.get(f) is not None}
    assessment['unknown_reasons'] = {f: 'not_supplied' for f in ['rating', 'assessed_on'] if assessment.get(f) is None}
    assessment['limitations'] = ['Authored synthetic condition scale and date; not an inspection or official PCI.']
payload = dict(fixture_id='demo-m2-v1', dataset_snapshot_id='demo-m1-v1', evidence_id=SOURCE,
    synthetic_input=True, assets=assets, assessments=assessments, repair_options=options)
raw = (json.dumps(payload, indent=2) + '\n').encode()
(ROOT / 'data/demo/maintenance.json').write_bytes(raw)
manifest = dict(fixture_id='demo-m2-v1', dataset_snapshot_id='demo-m1-v1', synthetic_input=True,
    file='maintenance.json', checksum_sha256=hashlib.sha256(raw).hexdigest(), generator='scripts/create_m2_fixture.py',
    asset_count=len(assets), assessment_count=len(assessments), repair_option_count=len(options),
    evidence_source=dict(id=SOURCE, title='CivicPlAIn M2 synthetic dimensions, assessments, rates and productivity',
        publisher='CivicPlAIn demo authors', source_kind='demo_assumption', verification_status='synthetic_demo',
        uri='data/demo/maintenance.json', retrieved_at=None, observed_on=None, version='demo-m2-v1',
        checksum_sha256=hashlib.sha256(raw).hexdigest(), original_crs='EPSG:4326',
        coverage_note='Five linked synthetic assets; 26 assessment records; three demonstration treatments. No municipal observations.',
        reliability_note='Every dimension, date, rate and productivity is invented for demonstration. Length is not computed from geometry.',
        license_note='Original CivicPlAIn synthetic assumptions; no third-party prices or data.',
        unknown_reasons={'observed_on': 'not_observed', 'retrieved_at': 'authored_fixture'}))
(ROOT / 'data/demo/maintenance-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
