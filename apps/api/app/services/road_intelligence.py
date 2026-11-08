"""Deterministic read-derived pavement associations. No automatic acceptance."""
from app.ingestion.pipeline import runtime_versions
from app.schemas.road_intelligence import AssociationReview
from app.services.municipal_data import candidate_matches, digest

PARAMETERS = {'version': 'road-association-overlay-v1', 'candidate_method': 'reviewed-candidates-v2',
    'metric_crs': 'EPSG:32618', 'tolerance_m': 5, 'automatic_acceptance': False,
    'coverage_method': 'buffered intersection length fraction; candidate evidence only'}


def stage_overlay(repository, snapshot_id, decisions):
    base = repository.snapshot(snapshot_id)
    roads = repository.records(snapshot_id, 'road')
    observations = repository.records(snapshot_id, 'condition')
    if (any(r['contains_synthetic'] or r['classification']=='synthetic_fixture'
            or 'synthetic_fixture' in r['field_classifications'].values() for r in roads + observations)
            or any(repository.source(snapshot_id,source_id)['query'].get('synthetic_fixture')
                   for source_id in base['source_revision_ids'])):
        raise ValueError('Synthetic harness cannot be published as official intelligence')
    return build_overlay(snapshot_id, base, roads, observations, decisions)


def build_overlay(snapshot_id, base, roads, observations, decisions, *, source_kind="condition", parameters=None, matches=None, contract="road-intelligence-v1", warnings=None):
    parameters = PARAMETERS if parameters is None else parameters
    """Pure builder also used by explicitly synthetic tests (not production publication)."""
    matches = candidate_matches(roads + observations, {}, 'reviewed-candidates-v2') if matches is None else matches
    parameter_hash = digest(parameters)
    reviewed = {}
    for value in decisions:
        d = AssociationReview.model_validate(value).model_dump(exclude_none=True)
        key = (d['source_record_id'], d['target_road_id'])
        if key in reviewed or d['base_snapshot_id'] != snapshot_id or d['parameter_hash'] != parameter_hash:
            raise ValueError('Duplicate, wrong-snapshot or stale-parameter review')
        if any(not d[k].strip() for k in ['reviewer', 'reason', 'scope_reason']) or any(not ref.strip() for ref in d['evidence_refs']):
            raise ValueError('Review evidence and rationale cannot be blank')
        reviewed[key] = d
    associations = []
    for m in matches:
        candidate_set_hash = digest(m['candidates'])
        for c in m['candidates'] or [None]:
            target = c['road_id'] if c else None
            d = reviewed.pop((m['source_record_id'], target), None)
            if d and (d['source_record_hash'] != c['source_record_hash'] or
                      d['target_record_hash'] != c['target_record_hash'] or d['candidate_hash'] != digest(c)):
                raise ValueError('Stale source, target or candidate review')
            if d and d.get('candidate_set_hash', candidate_set_hash) != candidate_set_hash:
                raise ValueError('Stale candidate-set review')
            row = {'base_snapshot_id': snapshot_id, 'source_kind': source_kind, 'source_record_id': m['source_record_id'],
                'target_kind': 'road', 'target_road_id': target, 'status': d['status'] if d else 'candidate' if c else 'unmatched',
                'candidate': c, 'candidate_hash': digest(c), 'parameter_hash': parameter_hash,
                'method': parameters['version'], 'decision': d,
                'scope': d['scope'] if d else 'unknown'}
            row['id'] = 'assoc-' + digest(row)[:32]
            associations.append(row)
    if reviewed:
        raise ValueError('Review references an unknown or ineligible candidate')
    associations.sort(key=lambda a: a['id'])
    accepted = [a for a in associations if a['status'] == 'accepted']
    accepted_ids = {a['source_record_id'] for a in accepted}
    counts = {'observations': len(observations), 'road_rows': len(roads), 'association_rows': len(associations),
        'accepted_observations': len(accepted_ids), 'accepted_road_rows': len({a['target_road_id'] for a in accepted}),
        'accepted_links': len(accepted), 'partial_links': sum(a['scope'] == 'partial' for a in accepted),
        'unresolved_observations': len(observations) - len(accepted_ids),
        'no_candidate_observations': sum(not m['candidates'] for m in matches),
        'candidate_links': sum(a['status'] == 'candidate' for a in associations),
        'rejected_links': sum(a['status'] == 'rejected' for a in associations)}
    manifest = {'contract_version': contract, 'base_snapshot_id': snapshot_id,
        'base_content_hash': base['content_hash'], 'source_revision_ids': sorted(base['source_revision_ids']),
        'parameters': parameters, 'parameter_hash': parameter_hash, 'runtime_versions': runtime_versions(),
        'decision_hash': digest(sorted(decisions, key=lambda d: (d['source_record_id'], d['target_road_id']))),
        'content_hash': digest(associations), 'counts': counts,
        'contains_synthetic': any(r['contains_synthetic'] for r in roads + observations),
        'warnings': warnings if warnings is not None else ['Local human review is not verified municipal endorsement.',
            'Candidate overlap does not establish direction, grade, roadbed or assessment scope.',
            'Official category policy applicability unresolved; utilities and excavation safety unknown.']}
    manifest_hash = digest(manifest)
    report = {'release_id': 'intel-' + manifest_hash[:32], 'base_snapshot_id': snapshot_id,
        'manifest_hash': manifest_hash, 'counts': counts, 'parameter_hash': parameter_hash}
    report['report_hash'] = digest(report)
    return {'manifest': manifest, 'associations': associations, 'report': report}
