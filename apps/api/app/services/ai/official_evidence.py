"""Only replayed result scalars reach the existing selection-only explanation service.

No source prose, work titles, geometry, review notes, citation content or user policy
names are projected. Full evidence remains in the separately accessible saved record.
"""
from app.schemas.ai import Context, EvidenceRecord, Fact, EvidencePackage
from app.services.municipal_data import digest
from app.services.ai.evidence import validate_context

LIMITS = [
    'Derived planning calculations use explicit assumptions, not contractor bids or actual expenditures.',
    'Condition, scope, prices, schedules and physical interference require qualified human review.',
    'Permit administrative dates and candidate locations do not confirm actual work.',
    'Utility locations and depth are unknown. No finding establishes excavation clearance.',
    'The assistant cannot approve work, authorize spending, fill missing measurements or optimize a citywide schedule.',
    'Original source text and review notes are untrusted and excluded from this explanation projection. Inspect the frozen record for citations and assumptions.',
]

def build(kind, record):
    result = record['result']
    entity = {'estimate':'estimate', 'priority':'evaluation', 'screening':'conflict'}[kind]
    eid = 'ev-' + digest([kind, record['id'], record['result_hash']])[:24]
    reference = EvidenceRecord(evidence_id=eid, entity_type=entity, record_id=record['id'],
        record_hash=record['result_hash'], input_hash=record['input_hash'],
        calculation_version=result['method_version'], dataset_snapshot_id=result['snapshot_id'],
        source_revisions={'frozen_input':record['input_hash'], 'projection_version':digest('official-scalar-projection-v1')}, synthetic_input=False, data_kind='derived')
    facts = []
    def fact(field, label, value, unit=None):
        facts.append(Fact(fact_id='fact-'+digest([eid,field])[:24], evidence_id=eid,
            field=field, label=label, value=value, unit=unit, classification='deterministic_calculation'))
    if kind == 'estimate':
        for index, alternative in enumerate(result['alternatives']):
            prefix = f'alternatives.{index}'
            fact(prefix+'.treatment', 'Declared treatment', alternative['treatment'])
            fact(prefix+'.quantity_m2', 'Declared planning quantity', alternative['quantity_m2'], 'm2')
            for case in ('base','low','high'):
                cost = (alternative['cases'] or {}).get(case)
                fact(prefix+f'.cases.{case}.total_usd', f'{case.capitalize()} assumption-based total', cost['total_usd'] if cost else None, 'USD')
            fact(prefix+'.duration', 'Preliminary days; not a work schedule', alternative['duration']['total_preliminary_days'] if alternative['duration'] else None, 'days')
    elif kind == 'priority':
        fact('base.ranked', 'Ranked roads in explicitly selected universe', result['base']['ranked'], 'road rows')
        fact('base.unranked', 'Unranked roads with insufficient eligible inputs', result['base']['unranked'], 'road rows')
        fact('as_of_date', 'Frozen policy reference date', result['as_of_date'], 'date')
        fact('sensitivity', 'Explicit alternative policies', len(result['sensitivity']), 'policies')
    else:
        for name, screen in [('base',result['base'])] + [(f'alternative.{i}',v['screen']) for i,v in enumerate(result['alternatives'])]:
            fact(name+'.findings', 'Supplied-plan screening findings; not verified actual conflicts', len(screen['findings']), 'findings')
            fact(name+'.indeterminate', 'Indeterminate pairs', screen['indeterminate_pair_count'], 'pairs')
            fact(name+'.possible', 'Possible selected pairs', screen['possible_pair_count'], 'pairs')
    fact('utilities', 'Verified utility coverage', None)
    raw = dict(version='ai-evidence-v1', context=Context(type=entity, record_ids=[record['id']]).model_dump(mode='json'),
        records=[reference.model_dump(mode='json')], facts=[f.model_dump(mode='json') for f in facts],
        missing_information=[f.label+' is unknown or unavailable.' for f in facts if f.value is None],
        limitations=LIMITS, truncated=False, omitted_fact_count=0)
    package = EvidencePackage(**raw, snapshot_hash=digest(raw))
    validate_context(package)
    return package
