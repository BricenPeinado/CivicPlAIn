"""Offline, read-only M8.1 evidence verification. No fetch, import, migration or approval.

Run with PYTHONPATH=apps/api and existing project dependencies. Output is exclusive.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3

from app.services.municipal_data import canonical, digest
from app.services.pavement_verification import coverage, observation_recency
from app.services.road_intelligence import stage_overlay
from app.ingestion.pipeline import stage


class ReadOnlyEvidence:
    def __init__(self, database, snapshot_id):
        self.conn = sqlite3.connect(database.resolve().as_uri() + '?mode=ro', uri=True)
        self.conn.execute('PRAGMA query_only=ON')
        self.conn.execute('BEGIN')
        self.snapshot_id = snapshot_id
        row = self.conn.execute('SELECT manifest_json FROM data_snapshots WHERE id=?', (snapshot_id,)).fetchone()
        if row is None:
            raise ValueError('Snapshot not found')
        self.base = json.loads(row[0])

    def snapshot(self, sid):
        if sid != self.snapshot_id:
            raise ValueError('Wrong snapshot')
        return self.base

    def records(self, sid, kind):
        self.snapshot(sid)
        return [json.loads(r[0]) for r in self.conn.execute(
            'SELECT payload FROM import_records WHERE snapshot_id=? AND kind=? ORDER BY id', (sid, kind))]

    def source(self, sid, source_id):
        self.snapshot(sid)
        row = self.conn.execute('SELECT r.payload FROM source_revisions r JOIN snapshot_sources s '
            'ON r.id=s.source_revision_id WHERE s.snapshot_id=? AND r.id=?', (sid, source_id)).fetchone()
        if row is None:
            raise ValueError('Source not in snapshot')
        return json.loads(row[0])


def verify_archive(path):
    acquisition = json.loads(path.read_text())
    checked = {}
    for kind, source in sorted(acquisition['sources'].items()):
        pages = []
        for filename, expected in sorted(source['files'].items()):
            # Fixed local archived basenames only; never follow a supplied URL/path.
            if Path(filename).name != filename:
                raise ValueError('Archive filename must be a basename')
            p = path.parent / kind / filename
            actual = hashlib.sha256(p.read_bytes()).hexdigest()
            if actual != expected:
                raise ValueError(f'Archive checksum mismatch: {kind}/{filename}')
            checked[f'{kind}/{filename}'] = actual
            if filename.startswith('page-'):
                page = json.loads(p.read_text())
                pages.extend(page['features'] if kind == 'lion' else page)
        if pages != source['rows']:
            raise ValueError('Acquisition rows differ from archived pages')
    return acquisition, checked


def verify(database, snapshot_id, acquisition_path, bundle_path, as_of_date, stale_after_days, policy_id=None):
    acquisition, checked = verify_archive(acquisition_path)
    repository = ReadOnlyEvidence(database, snapshot_id)
    try:
        sources = {s: repository.source(snapshot_id, s) for s in repository.base['source_revision_ids']}
        baseline = stage(acquisition_path, {})
        if baseline['snapshot_id'] != snapshot_id or baseline['manifest'] != repository.base:
            raise ValueError('Acquisition does not reproduce the pinned M7 snapshot')
        stored = sorted([r for kind in ['road', 'condition', 'permit', 'context']
                         for r in repository.records(snapshot_id, kind)], key=lambda r: r['id'])
        if stored != sorted(baseline['records'], key=lambda r: r['id']):
            raise ValueError('Stored records differ from original adapter output')
        for kind in ['pavement', 'lion']:
            archived = acquisition['sources'][kind]
            revisions = [r for r in sources.values() if r['source_id'] == archived['source']['id']]
            if len(revisions) != 1 or revisions[0]['dictionary_sha256'] != archived['dictionary_sha256']:
                raise ValueError('Archive/source revision mismatch')
            revision = revisions[0]
            # Same raw-input checksum construction as the existing ingestion pipeline.
            if revision['raw_sha256'] != digest(sorted(archived['rows'], key=canonical)):
                raise ValueError('Archive files differ from pinned source revision')
        bundle = json.loads(bundle_path.read_text())
        rebuilt = stage_overlay(repository, snapshot_id, [r['decision'] for r in bundle['associations'] if r['decision']])
        if rebuilt != bundle:
            raise ValueError('Overlay does not reproduce from pinned source records and reviews')
        roads, observations = repository.records(snapshot_id, 'road'), repository.records(snapshot_id, 'condition')
        report = coverage(roads, observations, bundle['associations'])
        report['observation_recency'] = observation_recency(observations, as_of_date, stale_after_days)
        report.update(snapshot_id=snapshot_id, base_content_hash=repository.base['content_hash'],
            overlay_manifest_hash=bundle['report']['manifest_hash'], overlay_report_hash=bundle['report']['report_hash'],
            archive_files_verified=len(checked), archive_file_hashes=checked,
            source_revisions=sources, acquisition_sha256=hashlib.sha256(acquisition_path.read_bytes()).hexdigest(),
            overlay_bundle_sha256=hashlib.sha256(bundle_path.read_bytes()).hexdigest(),
            classification_policy_status='Proposed — Pending Review; current feed categories remain Unknown',
            release_compatibility_status='BLOCKED: pavement referenced LION release absent; ArcGIS edit revision is not a catalog edition')
        if policy_id:
            from collections import Counter, defaultdict
            from app.services.pavement_policy import validate_context, POLICY, POLICY_HASH, classify
            from app.services.road_conditions import summarize
            from app.routes.municipal import association_match
            release_id = bundle['report']['release_id']
            validate_context(policy_id, snapshot_id, release_id)
            by_id = {r['id']: r for r in observations}
            groups = defaultdict(dict)
            for a in bundle['associations']:
                if a['status'] == 'accepted':
                    groups[a['target_road_id']][a['source_record_id']] = association_match(a, release_id)
            summaries = [summarize([by_id[key] for key in sorted(matches)], matches, road_id,
                snapshot_id, as_of_date, stale_after_days, release_id, policy_id)
                for road_id, matches in sorted(groups.items())]
            grade_counts = Counter(classify(by_id[key]['values'].get('rating'),
                by_id[key]['values'].get('non_rating_reason'))['category'] for key in {key for matches in groups.values() for key in matches})
            road_counts = Counter(s['category'] for s in summaries)
            road_counts['unknown'] += len(roads) - len(summaries)
            report['approved_pilot'] = {'policy': POLICY | {'hash': POLICY_HASH}, 'road_summaries': summaries,
                'accepted_observation_grade_counts': {k: grade_counts[k] for k in ['good','fair','poor','unknown']},
                'road_category_counts': {k: road_counts[k] for k in ['good','fair','poor','unknown']},
                'classification': 'derived_calculation', 'policy_classification': 'planning_assumption'}
            report['classification_policy_status'] = 'Project-owner approved pilot policy; official NYC DOT category applicability unresolved'
        report['report_hash'] = digest(report)
        return report
    finally:
        repository.conn.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', type=Path, required=True)
    parser.add_argument('--snapshot', required=True)
    parser.add_argument('--acquisition', type=Path, required=True)
    parser.add_argument('--review-bundle', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--as-of-date', required=True)
    parser.add_argument('--stale-after-days', required=True, type=int)
    parser.add_argument('--policy-id', help='Explicit approved pilot projection; does not activate or approve a policy')
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Output exists; choose a new path')
    report = verify(args.database, args.snapshot, args.acquisition, args.review_bundle, args.as_of_date, args.stale_after_days, args.policy_id)
    with args.output.open('x') as stream:
        json.dump(report, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')
    print(json.dumps({'report_hash': report['report_hash'], 'output': str(args.output), 'metrics': report['metrics']}))


if __name__ == '__main__':
    main()
