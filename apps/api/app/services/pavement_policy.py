"""Project-owner approved pilot grading; never NYC DOT category semantics."""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from app.services.municipal_data import digest

PILOT_SNAPSHOT_ID = 'nyc-3947b35876a619b31067db96b1409ad8'
POLICY_ID = 'civicplain-pilot-pavement-v1.0'
POLICY = {
    'id': POLICY_ID, 'name': 'CivicPlAIn Pilot Policy v1.0', 'version': '1.0',
    'classification': 'planning_assumption', 'approval': 'Project owner; CivicPlAIn hackathon pilot only',
    'official_nyc_dot_policy': False, 'rounding': 'Decimal ROUND_HALF_UP to integer',
    'valid_input': '0 < SystemRating <= 10; populated NonRatingReason always Unknown',
    'rounded_categories': {'0': 'unknown', '1-3': 'poor', '4-7': 'fair', '8-10': 'good'},
    'limitations': 'No local-street exception, PCI conversion, averaging, association or eligibility inference',
    'evidence_ref': 'docs/verification/M8_1_OWNER_APPROVAL.md',
}
POLICY_HASH = digest(POLICY)


def validate_context(policy_id, snapshot_id, release_id):
    if policy_id is not None and (policy_id != POLICY_ID or snapshot_id != PILOT_SNAPSHOT_ID or not release_id):
        raise ValueError('Pilot policy requires its approved base snapshot and an explicit intelligence release')


def classify(raw_rating, non_rating_reason=None):
    """Exact source value retained; rounding only chooses a project-derived category."""
    category, rounded, reason = 'unknown', None, None
    if non_rating_reason is not None and str(non_rating_reason).strip():
        reason = 'NON_RATING_REASON'
    elif raw_rating is None or isinstance(raw_rating, str) and not raw_rating.strip():
        reason = 'MISSING_RATING'
    else:
        try:
            if isinstance(raw_rating, bool):
                raise ValueError()
            value = Decimal(str(raw_rating))
            if not value.is_finite():
                reason = 'NONFINITE_RATING'
            elif not 0 <= value <= 10:
                reason = 'OUT_OF_RANGE_RATING'
            elif value == 0:
                reason = 'ZERO_RATING'
            else:
                rounded = int(value.quantize(Decimal('1'), rounding=ROUND_HALF_UP))
                category = 'poor' if 1 <= rounded <= 3 else 'fair' if 4 <= rounded <= 7 else 'good' if 8 <= rounded <= 10 else 'unknown'
                reason = 'ROUNDED_TO_ZERO' if rounded == 0 else None
        except (ValueError, TypeError, InvalidOperation):
            reason = 'NONNUMERIC_RATING'
    return {'raw_rating': raw_rating, 'rounded_rating': rounded, 'category': category, 'reason': reason,
            'non_rating_reason': non_rating_reason, 'policy_id': POLICY_ID, 'policy_version': '1.0',
            'policy_hash': POLICY_HASH, 'classification': 'derived_calculation',
            'policy_classification': 'planning_assumption', 'official_nyc_dot_policy': False}
