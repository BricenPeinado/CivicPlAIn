"""Pure accepted-evidence projection; no category policy has passed applicability review."""
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from app.services.municipal_data import digest


def summarize(records, matches, road_id, snapshot_id, as_of_date, stale_after_days=None, release_id=None, policy_id=None):
    from app.services.pavement_policy import POLICY_ID, POLICY, POLICY_HASH, classify
    if policy_id not in {None, POLICY_ID}:
        raise ValueError('Unsupported classification policy')
    reference = date.fromisoformat(as_of_date)
    if reference.isoformat() != as_of_date:
        raise ValueError('as_of_date must be YYYY-MM-DD')
    if stale_after_days is not None and (type(stale_after_days) is not int or not 0 <= stale_after_days <= 36500):
        raise ValueError('stale_after_days must be an integer from 0 through 36500')
    unique = {}
    for record in records:
        if record['id'] in unique and unique[record['id']] != record:
            raise ValueError('Conflicting duplicate assessment identifier')
        unique[record['id']] = record
    records = list(unique.values())
    inputs = []
    history = []
    for r in records:
        m = matches.get(r['id'])
        if not m or m['status'] != 'matched' or m['target_road_id'] != road_id:
            continue
        inputs.append({'record_hash': digest(r), 'association_hash': digest(m)})
        v = r['values']; reason = None; day = None
        try:
            inspection = datetime.fromisoformat(v['inspection_at']) if v.get('inspection_at') else None
            if inspection and inspection.tzinfo is not None:
                raise ValueError('Source floating timestamp cannot acquire a timezone')
            day = inspection.date() if inspection else None
            rating = Decimal(v['rating']) if v.get('rating') is not None else None
            if rating is None or not rating.is_finite() or not 0 <= rating <= 10:
                reason = 'UNRATED'
            elif v.get('non_rating_reason'):
                reason = 'NON_RATING_REASON_UNRESOLVED'
            elif rating < 1 and policy_id is None:
                reason = 'RATING_VALIDITY_UNRESOLVED'
            elif rating == 0:
                reason = 'ZERO_RATING'
            elif day is None:
                reason = 'UNDATED'
            elif day > reference:
                reason = 'AFTER_AS_OF_DATE'
            elif m.get('method') != 'reviewed-candidates-v2' or (m.get('decision') or {}).get('scope') != 'whole_road':
                reason = 'PARTIAL_OR_UNREVIEWED_SCOPE'
            elif not v.get('direction') or not v.get('road_type'):
                reason = 'UNKNOWN_DIRECTION_OR_ROADBED'
            elif str(r.get('lineage', {}).get('raw_fields', {}).get('ismultipass')) != '0':
                reason = 'MULTIPASS_SELECTION_UNRESOLVED'
        except (ValueError, TypeError, InvalidOperation):
            reason = 'INVALID_RATING_OR_DATE'
        history.append({'id': r['id'], 'rating': v.get('rating'), 'inspection_at': v.get('inspection_at'),
            'direction': v.get('direction'), 'road_type': v.get('road_type'),
            'non_rating_reason': v.get('non_rating_reason'),
            'multipass': r.get('lineage', {}).get('raw_fields', {}).get('ismultipass'),
            'source_revision_id': r['source_revision_id'], 'eligible': reason is None, 'reason': reason,
            'field_classifications': {key: r.get('field_classifications', {}).get(key, 'unknown')
                for key in ['rating','inspection_at','direction','road_type','non_rating_reason']},
            'record_hash': digest(r), 'association_id': m['id'], 'association_hash': digest(m)})
        if policy_id:
            history[-1]['grading'] = classify(v.get('rating'), v.get('non_rating_reason'))
            history[-1]['association_review'] = m.get('decision')
    history.sort(key=lambda r: r['id'])
    def timestamp_key(record):
        try:
            value = datetime.fromisoformat(record['inspection_at']) if record['inspection_at'] else datetime.min
            return value if value.tzinfo is None else datetime.min
        except (ValueError, TypeError):
            return datetime.min
    history.sort(key=timestamp_key, reverse=True)
    eligible = [r for r in history if r['eligible']]
    streams = {(r['direction'], r['road_type']) for r in eligible}
    reason = 'NO_ACCEPTED_ELIGIBLE_ASSESSMENT'; selected = None
    if len(streams) > 1:
        reason = 'MULTIPLE_DIRECTION_OR_ROADBED_STREAMS'
    elif eligible:
        newest = timestamp_key(eligible[0])
        latest = [r for r in eligible if timestamp_key(r) == newest]
        if len({Decimal(r['rating']) for r in latest}) > 1:
            reason = 'CONFLICTING_LATEST_RATINGS'
        else:
            selected = latest[0]; reason = None
    age = (reference - datetime.fromisoformat(selected['inspection_at']).date()).days if selected else None
    result = dict(method_version='road-condition-v1', intelligence_release_id=release_id, snapshot_id=snapshot_id, road_id=road_id,
        classification='derived_calculation', category='unknown', category_reason='OFFICIAL_POLICY_APPLICABILITY_UNRESOLVED',
        rating=selected['rating'] if selected else None, inspection_at=selected['inspection_at'] if selected else None,
        source_revision_id=selected['source_revision_id'] if selected else None,
        latest_usable_id=selected['id'] if selected else None, as_of_date=as_of_date,
        age_days=age, stale_after_days=stale_after_days,
        stale=None if age is None or stale_after_days is None else age > stale_after_days,
        recency_basis='Explicit application planning threshold; not agency freshness or safety policy',
        reason=reason, history=history, utility_coverage='unknown')
    result['field_classifications'] = {
        'rating': selected['field_classifications']['rating'] if selected else 'unknown',
        'inspection_at': selected['field_classifications']['inspection_at'] if selected else 'unknown',
        'category': 'unknown', 'as_of_date': 'planning_assumption',
        'stale_after_days': 'planning_assumption' if stale_after_days is not None else 'unknown',
        'age_days': 'derived_calculation' if age is not None else 'unknown',
        'stale': 'derived_calculation' if result['stale'] is not None else 'unknown'}
    result['input_hash'] = digest({'method_version': result['method_version'], 'snapshot_id': snapshot_id,
        'road_id': road_id, 'intelligence_release_id': release_id, 'as_of_date': as_of_date, 'stale_after_days': stale_after_days,
        'evidence': sorted(inputs, key=lambda r: (r['record_hash'], r['association_hash']))})
    if policy_id:
        grade = selected['grading'] if selected else None
        result.update(method_version='road-condition-v2-pilot', policy=POLICY | {'hash': POLICY_HASH},
                      rounded_rating=grade['rounded_rating'] if grade else None,
                      category=grade['category'] if grade else 'unknown',
                      category_reason=grade['reason'] if grade else reason)
        result['field_classifications']['category'] = 'derived_calculation' if grade else 'unknown'
        result['field_classifications']['rounded_rating'] = 'derived_calculation' if grade else 'unknown'
        result['field_classifications']['policy'] = 'planning_assumption'
        result['input_hash'] = digest({'legacy_input_hash': result['input_hash'], 'method_version': result['method_version'],
                                       'policy_id': policy_id, 'policy_hash': POLICY_HASH})
    result['result_hash'] = digest(result)
    return result
