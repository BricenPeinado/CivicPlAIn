"""Synthetic audit tests do not establish actual municipal match coverage."""
import copy
import json
from pathlib import Path
import runpy
import sqlite3

import pytest

from app.services.pavement_verification import coverage, metric, observation_recency, proposed_legacy_classification, segment_id
from app.services.road_intelligence import build_overlay
from test_m7_ingestion import staged, fixture_bundle


@pytest.mark.parametrize('raw,expected', [('123', '0000123'), (' 0000123 ', '0000123'),
    ('0000000', '0000000'), (None, None), ('', None), (123, None), ('123.0', None),
    ('12345678', None), ('１２３', None), ('1e3', None)])
def test_identifier_syntax_is_not_a_release_match(raw, expected):
    assert segment_id(raw) == expected


@pytest.mark.parametrize('rating,usage,expected', [('1', None, 'poor'), ('3', None, 'poor'),
    ('3.01', 'L', 'unknown'), ('3.99', 'P', 'unknown'), ('4', None, 'fair'),
    ('6', None, 'fair'), ('6.99', None, 'fair'), ('7', 'L', 'good'), ('7', 'P', 'fair'),
    ('7', 'S', 'fair'), ('7', None, 'unknown'), ('7', 'Main', 'unknown'),
    ('7.01', 'L', 'unknown'), ('7.99', 'L', 'unknown'), ('8', None, 'good'),
    ('10', None, 'good'), ('0', 'L', 'unknown'), ('10.01', None, 'unknown'),
    ('NaN', 'L', 'unknown'), (None, 'L', 'unknown'), (True, 'L', 'unknown')])
def test_proposed_legacy_policy_is_a_counterfactual(rating, usage, expected):
    result = proposed_legacy_classification(rating, usage)
    assert result['category'] == expected
    assert result['applicable_to_current_feed'] is False
    assert result['status'] == 'Proposed — Pending Review'


def test_source_category_conflict_is_visible_and_never_overridden():
    result = proposed_legacy_classification('7', 'L', 'Fair')
    assert result['category'] == 'unknown' and result['computed_category'] == 'good'
    assert result['source_category'] == 'Fair' and result['conflict']
    assert result['reason'] == 'SOURCE_COMPUTED_CATEGORY_CONFLICT'
    assert not proposed_legacy_classification('7', None, 'Fair')['compared']
    assert not proposed_legacy_classification('8', None, 'Good')['conflict']
    unsupported = proposed_legacy_classification('8', None, 'unrated')
    assert unsupported['category'] == 'unknown' and unsupported['source_category'] == 'unrated'
    assert metric(0, 0)['percent'] is None
    assert metric(1, 3)['percent'] == '33.33'


def test_inventory_repeated_ids_and_ambiguity_are_not_verified_matches(staged):
    roads = [r for r in staged['records'] if r['kind'] == 'road']
    obs = [r for r in staged['records'] if r['kind'] == 'condition']
    twin = copy.deepcopy(roads[0]); twin['id'] += '-alternate-export-row'; roads.append(twin)
    repeated = copy.deepcopy(obs[0]); repeated['id'] += '-repeated-assessment'; obs.append(repeated)
    overlay = build_overlay('test', staged['manifest'], roads, obs, [])
    report = coverage(roads, obs, overlay['associations'])
    assert report['metrics']['verified_matched_observations']['count'] == 0
    assert report['metrics']['pavement_segment_id_missing']['count'] == len(obs)
    assert report['metrics']['lion_rows_with_repeated_segment_id']['count'] == 2
    assert report['metrics']['pavement_duplicate_assessment_grain_records']['count'] == 2
    assert report['metrics']['multiple_candidate_observations']['count'] == len(obs)
    assert report['metrics']['unknown']['count'] == len(obs)
    assert report['suspected_release_mismatches']['count'] is None
    assert report == coverage(list(reversed(roads)), list(reversed(obs)), list(reversed(overlay['associations'])))
    with pytest.raises(ValueError, match='Duplicate record IDs'):
        coverage(roads, obs + [obs[0]], overlay['associations'])
    with pytest.raises(ValueError, match='Incomplete'):
        coverage(roads, obs, [])
    with pytest.raises(ValueError, match='Duplicate association'):
        coverage(roads, obs, overlay['associations'] + overlay['associations'][:1])
    bad = copy.deepcopy(overlay['associations']); bad[0]['target_road_id'] = 'outside'
    with pytest.raises(ValueError, match='outside snapshot'):
        coverage(roads, obs, bad)


def test_verifier_reads_are_query_only_and_archive_tampering_fails(tmp_path):
    script = runpy.run_path(str(Path(__file__).resolve().parents[3] / 'scripts/verify_m8_1.py'))
    db = tmp_path / 'audit.sqlite3'
    with sqlite3.connect(db) as conn:
        conn.execute('CREATE TABLE data_snapshots(id TEXT,manifest_json TEXT)')
        conn.execute('INSERT INTO data_snapshots VALUES(?,?)', ('snapshot', '{}'))
    evidence = script['ReadOnlyEvidence'](db, 'snapshot')
    try:
        with pytest.raises(sqlite3.OperationalError):
            evidence.conn.execute('INSERT INTO data_snapshots VALUES(?,?)', ('write', '{}'))
        with pytest.raises(ValueError, match='Wrong snapshot'):
            evidence.snapshot('wrong')
    finally:
        evidence.conn.close()
    archive = tmp_path / 'acquisition.json'
    archive.write_text(json.dumps({'sources': {'pavement': {'files': {'../outside': 'bad'}}}}))
    with pytest.raises(ValueError, match='basename'):
        script['verify_archive'](archive)
    (tmp_path / 'pavement').mkdir()
    (tmp_path / 'pavement' / 'page-000000.json').write_text('[]')
    archive.write_text(json.dumps({'sources': {'pavement': {'files': {'page-000000.json': 'bad'}}}}))
    with pytest.raises(ValueError, match='checksum'):
        script['verify_archive'](archive)


def test_observation_recency_is_explicit_and_not_road_coverage():
    obs = [{'values': {'inspection_at': value}} for value in
           ['2026-11-07T12:00:00', '2026-11-06', '2026-11-09', None, 'bad']]
    result = observation_recency(obs, '2026-11-08', 1)
    assert result['metrics']['dated_within_threshold']['count'] == 1
    assert result['metrics']['dated_outside_threshold']['count'] == 1
    assert result['metrics']['invalid_or_future']['count'] == 2
    assert result['metrics']['undated']['count'] == 1
    assert result['parameter_classification'] == 'planning_assumption'
    assert result == observation_recency(list(reversed(obs)), '2026-11-08', 1)
    with pytest.raises(ValueError):
        observation_recency(obs, '20261108', 1)
    with pytest.raises(ValueError):
        observation_recency(obs, '2026-11-08', -1)
