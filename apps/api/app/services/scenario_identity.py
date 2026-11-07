"""Canonicalize set-like proposal lists without dropping evidence or assumptions."""
import copy

SET_FIELDS = {'evidence_ids', 'assumption_evidence_ids', 'related_project_ids', 'external_project_ids',
    'replacement_action_ids', 'must_follow_action_ids', 'field_paths', 'working_weekdays', 'excluded_dates'}


def canonical_proposal(value):
    if isinstance(value, dict):
        result = {k: canonical_proposal(v) for k, v in value.items()}
        for key, val in result.items():
            if isinstance(val, list):
                if key in SET_FIELDS:
                    result[key] = sorted(val)
                elif key in {'actions', 'assumptions', 'project_overrides'}:
                    result[key] = sorted(val, key=lambda r: r.get('id', r.get('project_id', '')))
                elif key == 'closure_intervals':
                    result[key] = sorted(val, key=lambda r: (r['start_date'], r['end_date']))
        return result
    if isinstance(value, list):
        return [canonical_proposal(v) for v in value]
    return copy.deepcopy(value)
