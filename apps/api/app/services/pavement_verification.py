"""Offline M8.1 audit helpers. No importer, approval or active category policy.

The legacy interpretation below is a proposal for the 2015 Rating_B schema.
It must not be used to classify the 6yyb-pb25 SystemRating feed.
"""
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from datetime import date, datetime
import re

from app.services.municipal_data import digest


def segment_id(value):
    """Syntax normalization only; never evidence of release compatibility."""
    if not isinstance(value, str) or not re.fullmatch(r'[0-9]{1,7}', value.strip()):
        return None
    return value.strip().zfill(7)


def proposed_legacy_classification(rating, usage_class, source_category=None):
    """Literal documented intervals; decimal gaps and local-7 uncertainty stay unknown.

    Audit-only counterfactual, not authorized for any ingested source revision.
    Source labels are retained; a disagreement prevents a supported category.
    """
    category = 'unknown'
    reason = 'INVALID_OR_MISSING_RATING'
    try:
        if isinstance(rating, bool) or rating is None:
            raise ValueError()
        value = Decimal(str(rating))
        if value.is_finite() and 1 <= value <= 10:
            reason = 'UNSUPPORTED_FRACTIONAL_INTERVAL'
            if 1 <= value <= 3:
                category = 'poor'
            elif 4 <= value < 7:
                category = 'fair'
            elif value == 7:
                category = {'L': 'good', 'P': 'fair', 'S': 'fair'}.get(usage_class, 'unknown')
                reason = 'USAGE_CLASS_UNAVAILABLE_OR_UNSUPPORTED'
            elif 8 <= value <= 10:
                category = 'good'
    except (InvalidOperation, ValueError, TypeError):
        pass
    compared = category != 'unknown' and source_category in {'Good', 'Fair', 'Poor'}
    conflict = compared and source_category.lower() != category
    computed = category
    if conflict:
        category, reason = 'unknown', 'SOURCE_COMPUTED_CATEGORY_CONFLICT'
    elif source_category is not None and source_category not in {'Good', 'Fair', 'Poor'}:
        category, reason = 'unknown', 'UNSUPPORTED_SOURCE_CATEGORY'
    elif category != 'unknown':
        reason = None
    return {'policy_id': 'dot-2015-literal-intervals-proposal-v1', 'status': 'Proposed — Pending Review',
            'computed_category': computed, 'category': category, 'reason': reason,
            'source_category': source_category, 'compared': compared, 'conflict': conflict,
            'applicable_to_current_feed': False}


def metric(count, denominator):
    return {'count': count, 'denominator': denominator,
            'percent': str((Decimal(count) * 100 / denominator).quantize(Decimal('.01'), rounding=ROUND_HALF_UP))
            if denominator else None}


def observation_recency(observations, as_of_date, stale_after_days):
    """Source-observation ages, never current road-condition coverage."""
    reference = date.fromisoformat(as_of_date)
    if reference.isoformat() != as_of_date or type(stale_after_days) is not int or not 0 <= stale_after_days <= 36500:
        raise ValueError('Explicit ISO reference date and integer threshold 0..36500 required')
    counts = Counter({'dated_within_threshold': 0, 'dated_outside_threshold': 0,
                      'undated': 0, 'invalid_or_future': 0})
    for r in observations:
        raw = r['values'].get('inspection_at')
        if not raw:
            counts['undated'] += 1
            continue
        try:
            inspection = datetime.fromisoformat(raw)
            if inspection.tzinfo is not None or inspection.date() > reference:
                raise ValueError('Unsupported timestamp')
            age = (reference - inspection.date()).days
            counts['dated_outside_threshold' if age > stale_after_days else 'dated_within_threshold'] += 1
        except (ValueError, TypeError):
            counts['invalid_or_future'] += 1
    return {'as_of_date': as_of_date, 'stale_after_days': stale_after_days,
            'parameter_classification': 'planning_assumption', 'classification': 'derived_calculation',
            'basis': 'Source inspection calendar date; age > threshold. Includes unassociated and ineligible observations; not road-condition recency.',
            'metrics': {k: metric(v, len(observations)) for k, v in sorted(counts.items())}}


def coverage(roads, observations, associations):
    """Deterministic inventory; categories deliberately remain unknown for this feed.

    Caller verifies archive/snapshot/overlay integrity before using this as evidence.
    Repeated assessment grain is diagnostic, never an instruction to discard records.
    """
    road_by_id = {r['id']: r for r in roads}
    obs_by_id = {r['id']: r for r in observations}
    if len(road_by_id) != len(roads) or len(obs_by_id) != len(observations):
        raise ValueError('Duplicate record IDs')
    n, nr = len(observations), len(roads)
    ids = [segment_id(r['raw_identifiers'].get('segment_id')) for r in roads]
    id_counts = Counter(i for i in ids if i is not None)
    oft = Counter(r['raw_identifiers'].get('oftcode') for r in observations)
    grain = Counter()
    candidates, accepted = defaultdict(set), defaultdict(set)
    statuses = Counter()
    seen = set()
    for a in associations:
        source, target = a['source_record_id'], a['target_road_id']
        if source not in obs_by_id or (target is not None and target not in road_by_id):
            raise ValueError('Association outside snapshot')
        if (source, target) in seen:
            raise ValueError('Duplicate association pair')
        seen.add((source, target)); statuses[a['status']] += 1
        if a['status'] in {'candidate', 'accepted'}:
            if target is None:
                raise ValueError('Candidate/accepted association requires target')
            candidates[source].add(target)
        if a['status'] == 'accepted':
            accepted[source].add(target)
    # Every observation must be represented, including explicit unmatched rows.
    if {s for s, _ in seen} != set(obs_by_id):
        raise ValueError('Incomplete association inventory')
    for r in observations:
        v = r['values']
        grain[digest([r['raw_identifiers'].get('oftcode'), v.get('inspection_at'), v.get('direction'),
                      v.get('road_type'), r['lineage'].get('raw_fields', {}).get('ismultipass'),
                      v.get('rating'), v.get('non_rating_reason'), r.get('geometry')])] += 1
    source_categories = sum(r['values'].get('official_category') is not None for r in observations)
    counts = {
        'pavement_total': metric(n, n), 'road_rows': metric(nr, nr),
        'pavement_segment_id_syntax_valid': metric(sum(segment_id(r['raw_identifiers'].get('segment_id')) is not None for r in observations), n),
        'pavement_segment_id_missing': metric(sum(r['raw_identifiers'].get('segment_id') in (None, '') for r in observations), n),
        'pavement_oft_syntax_valid': metric(sum(isinstance(r['raw_identifiers'].get('oftcode'), str) and re.fullmatch(r'[0-9]{18}', r['raw_identifiers']['oftcode']) is not None for r in observations), n),
        'pavement_oft_missing': metric(sum(r['raw_identifiers'].get('oftcode') in (None, '') for r in observations), n),
        'pavement_repeated_oft_records': metric(sum(c for key, c in oft.items() if key and c > 1), n),
        'pavement_duplicate_assessment_grain_records': metric(sum(c for c in grain.values() if c > 1), n),
        'pavement_duplicate_assessment_grain_excess': metric(sum(c - 1 for c in grain.values()), n),
        'lion_segment_id_syntax_valid': metric(sum(i is not None for i in ids), nr),
        'lion_repeated_segment_id_values': metric(sum(c > 1 for c in id_counts.values()), len(id_counts)),
        'lion_rows_with_repeated_segment_id': metric(sum(c for c in id_counts.values() if c > 1), nr),
        'verified_matched_observations': metric(len(accepted), n),
        'verified_matched_roads': metric(len({t for ts in accepted.values() for t in ts}), nr),
        'unresolved_observations': metric(n - len(accepted), n),
        'no_candidate_observations': metric(sum(not candidates[r['id']] for r in observations), n),
        'multiple_candidate_observations': metric(sum(len(candidates[r['id']]) > 1 for r in observations), n),
        'single_candidate_observations': metric(sum(len(candidates[r['id']]) == 1 for r in observations), n),
        'missing_direction': metric(sum(not r['values'].get('direction') for r in observations), n),
        'missing_road_type': metric(sum(not r['values'].get('road_type') for r in observations), n),
        'non_rating_reason': metric(sum(bool(r['values'].get('non_rating_reason')) for r in observations), n),
        'multipass': metric(sum(str(r['lineage'].get('raw_fields', {}).get('ismultipass')) == '1' for r in observations), n),
        'source_category_present': metric(source_categories, n),
        'good': metric(0, n), 'fair': metric(0, n), 'poor': metric(0, n), 'unknown': metric(n, n),
        'source_computed_category_disagreements': metric(0, 0),
    }
    repeated = {i for i, c in id_counts.items() if c > 1}
    variants = defaultdict(set)
    for r in roads:
        i = segment_id(r['raw_identifiers'].get('segment_id'))
        if i in repeated:
            attrs = r['lineage'].get('raw_attributes', {})
            variants[i].add(digest([r.get('geometry'), attrs.get('NodeIDFrom'), attrs.get('NodeIDTo')]))
    counts['repeated_segment_ids_with_geometry_or_node_variants'] = metric(sum(len(v) > 1 for v in variants.values()), len(repeated))
    eligible = [a for a in associations if a['status'] == 'candidate' and a.get('candidate')
                and a['candidate'].get('street_code_agrees') and a['candidate'].get('on_street_name_agrees')]
    eligible.sort(key=lambda a: (-(a['candidate'].get('road_coverage_fraction') or 0),
                                 -(a['candidate'].get('observation_coverage_fraction') or 0), a['id']))
    shortlist, selected_sources, selected_roads = [], set(), set()
    for a in eligible:
        if a['source_record_id'] in selected_sources or a['target_road_id'] in selected_roads:
            continue
        source, road = obs_by_id[a['source_record_id']], road_by_id[a['target_road_id']]
        shortlist.append({'status': 'Proposed — Pending Review', 'association_id': a['id'],
            'source_record_id': source['id'], 'source_record_key': source['source_record_key'],
            'target_road_id': road['id'], 'target_record_key': road['source_record_key'],
            'street': road['values'].get('name'), 'oftcode': source['raw_identifiers'].get('oftcode'),
            'inspection_at': source['values'].get('inspection_at'), 'raw_rating': source['values'].get('rating'),
            'candidate_hash': a['candidate_hash'], 'candidate': a['candidate'],
            'competing_road_count': len(candidates[source['id']])})
        selected_sources.add(source['id']); selected_roads.add(road['id'])
        if len(shortlist) == 5:
            break
    return {'method_version': 'm81-coverage-audit-v1', 'metrics': counts,
            'association_status_counts': dict(sorted(statuses.items())),
            'distinct_oft_values': len(oft), 'distinct_lion_segment_ids': len(id_counts),
            'candidate_count_distribution': dict(sorted(Counter(len(candidates[r['id']]) for r in observations).items())),
            'suspected_release_mismatches': {'count': None, 'percent': None, 'denominator': n,
                'reason': 'No pavement SegmentID/referenced LION edition or compatible LDF chain; not measurable'},
            'classification_comparison': {'comparable_records': 0, 'reason': 'No source category or approved feed-specific computed policy'},
            'shortlist': shortlist}
