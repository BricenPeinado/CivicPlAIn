"""Deterministic review queues. No AI, SQL, network, safety or schedule optimization."""
from decimal import Decimal,localcontext
from app.schemas.prioritization import PriorityRequest,PriorityResult
from app.schemas.road_intelligence import ConditionSummary
from app.services.municipal_data import digest

VERSION='maintenance-priority-v1'
DEFINITIONS={
 'condition_need':'(10 - exact eligible raw rating) / 9 on the supported 1..10 scale. Application review-need normalization, NOT an official category, failure probability or treatment recommendation.',
 'inspection_age':'min(accepted assessment age_days / policy age_horizon_days, 1). Evidence review age, not predicted deterioration.',
 'evidence_gap':'1 when no eligible accepted road-wide assessment is available; 0 otherwise. Known absence of eligible evidence, NOT observed pavement condition or risk.'}
WARNINGS=['Decision-support review order only; not an optimal citywide schedule, funding allocation, safety rating or safe-deferral decision.',
 'Missing weighted factors leave a road unranked. No zero filling or per-road weight redistribution. Equal exact scores share competition rank; road ID only orders tied display.',
 'All weights/thresholds are attributed planning assumptions, not independently approved municipal policy. Human engineering and source review required.',
 'Functional road class, traffic/disruption and verified work opportunities are unavailable in the current pinned adapters. Permit references are administrative, not construction schedules.',
 'Cost is a separate declared-scope planning estimate, not maintenance need, an expenditure, bid or comparable benefit. No savings, lifespan, utilities or excavation clearance inferred.']


def evaluate(rows,policy,budget=None):
    output=[]
    with localcontext() as ctx:
        ctx.prec=40
        for row in sorted(rows,key=lambda r:r['road']['id']):
            road=row['road'];summary=ConditionSummary.model_validate(row['condition']).model_dump(mode='json')
            age=summary['age_days'];rating=summary['rating'];eligible=rating is not None and age is not None and summary['latest_usable_id'] is not None and summary['reason'] is None
            official=summary['field_classifications']['rating']=='official_observation' and summary['field_classifications']['inspection_at']=='official_observation'
            stale=age is not None and age>policy.max_condition_age_days
            values={'condition_need':None,'inspection_age':None,'evidence_gap':Decimal(0 if eligible and official else 1)}
            reasons={}
            if eligible and official:
                raw=Decimal(rating)
                if 1<=raw<=10:values['condition_need']=(10-raw)/9
                else:reasons['condition_need']='RAW_RATING_OUTSIDE_SUPPORTED_SCALE'
                values['inspection_age']=min(Decimal(age)/policy.age_horizon_days,Decimal(1))
                if stale and policy.stale_behavior=='exclude':values['condition_need']=None;reasons['condition_need']='STALE_CONDITION_EXCLUDED'
            else:
                reasons.update(condition_need=summary['reason'] or 'OFFICIAL_FIELD_PROVENANCE_UNAVAILABLE',inspection_age=summary['reason'] or 'OFFICIAL_FIELD_PROVENANCE_UNAVAILABLE')
            factors={}
            missing=[];score=Decimal(0)
            for key,weight in policy.weights.model_dump().items():
                w=Decimal(weight);value=values[key]
                contribution=value*w if value is not None else None
                if w>0 and value is None:missing.append(key)
                elif w>0:score+=contribution
                factors[key]={'value':format(value,'f') if value is not None else None,'unit':'dimensionless','weight':weight,
                    'contribution':format(contribution,'f') if contribution is not None else None,'reason':reasons.get(key),'definition':DEFINITIONS[key]}
            excluded=[]
            if policy.objective=='maintenance_review' and not (eligible and official):excluded.append('NO_ELIGIBLE_OFFICIAL_ROAD_CONDITION')
            if policy.objective=='maintenance_review' and stale and policy.stale_behavior=='exclude':excluded.append('STALE_CONDITION_EXCLUDED')
            cost=row['cost'];constraint='not_applied'
            if budget is not None:
                if cost is None:constraint='indeterminate';excluded.append('COST_CEILING_UNCHECKABLE')
                elif Decimal(cost['base_total_usd'])>budget:constraint='exceeds_declared_scope_ceiling';excluded.append('DECLARED_SCOPE_COST_ABOVE_CEILING')
                else:constraint='within_declared_scope_ceiling'
            ranked=not excluded and not missing
            unknown=['Functional road hierarchy unavailable; feature type is not a traffic/safety classification','Traffic/disruption evidence unavailable','Verified construction opportunity and actual schedule unknown','Utility coverage unknown']
            if cost is None:unknown.append('No explicit saved estimate selected; implementation cost unknown')
            if not eligible:unknown.append('No eligible road-wide assessment; maintenance need unknown')
            if stale:unknown.append('Assessment exceeds explicit age threshold; age does not predict deterioration')
            output.append({'road_id':road['id'],'name':road['values'].get('name') or road['source_record_key'],
                'rank':None,'score':format(score,'f') if ranked else None,'status':'ranked' if ranked else 'unranked',
                'objective':policy.objective,'missing_weighted_factors':missing,'ineligible_reasons':excluded,'factors':factors,
                'completeness':{'eligible_official_condition':bool(eligible and official),'selected_cost_available':cost is not None,
                    'weighted_factors_available':sum(Decimal(v['weight'])>0 and v['value'] is not None for v in factors.values()),
                    'weighted_factors_required':sum(Decimal(v['weight'])>0 for v in factors.values())},
                'maintenance_need':{'raw_rating':rating,'official_category':summary['category'],'category_reason':summary['category_reason'],'status':'supported_rating_only' if eligible and official else 'unknown'},
                'recency':{'inspection_at':summary['inspection_at'],'age_days':age,'stale':stale if age is not None else None,'max_condition_age_days':policy.max_condition_age_days,'as_of_date':summary['as_of_date']},
                'road_classification':{'feature_type':road['values'].get('feature_type'),'functional_class':None,'scoring':'unsupported'},
                'implementation_cost':cost,'cost_constraint':constraint,'coordination':row['coordination'],
                'traffic_disruption':{'status':'unavailable','value':None},'unknowns':unknown,'human_review_required':True,
                'why':'Earlier '+policy.objective.replace('_',' ')+' under the explicit weighted factors; no work is approved.' if ranked else 'Excluded from numerical order: missing/ineligible evidence; this is not low priority.',
                'lineage':{'road_hash':digest(road),'source_revision_id':road['source_revision_id'],'condition_input_hash':summary['input_hash'],'condition_result_hash':summary['result_hash']}})
        output.sort(key=lambda r:(r['score'] is None,-Decimal(r['score']) if r['score'] is not None else Decimal(0),r['road_id']))
        last=None;rank=None
        for position,row in enumerate([r for r in output if r['score'] is not None],1):
            score=Decimal(row['score'])
            if score!=last:rank=position
            row['rank']=rank;last=score
    return {'policy_id':policy.id,'policy_version':policy.version,'policy_hash':digest(policy.model_dump(mode='json')),
        'objective':policy.objective,'rows':output,'ranked':sum(r['rank'] is not None for r in output),'unranked':sum(r['rank'] is None for r in output)}


def calculate(snapshot):
    if snapshot['method_version']!=VERSION or snapshot['definitions']!=DEFINITIONS:raise ValueError('Unsupported priority method or definitions')
    request=PriorityRequest.model_validate(snapshot['request'])
    if sorted(r['road']['id'] for r in snapshot['roads'])!=sorted(request.road_ids):raise ValueError('Ranking universe differs from input request')
    budget=request.max_estimate_usd.number if request.max_estimate_usd else None
    base=evaluate(snapshot['roads'],request.policy,budget);ranks={r['road_id']:r['rank'] for r in base['rows']}
    sensitivity=[]
    for policy in request.sensitivity_policies:
        alternative=evaluate(snapshot['roads'],policy,budget)
        alternative['rank_changes']=[{'road_id':r['road_id'],'base_rank':ranks[r['road_id']],'alternative_rank':r['rank'],
            'delta':ranks[r['road_id']]-r['rank'] if r['rank'] is not None and ranks[r['road_id']] is not None else None} for r in alternative['rows']]
        alternative['result_hash']=digest(alternative);sensitivity.append(alternative)
    result={'method_version':VERSION,'snapshot_id':request.snapshot_id,'as_of_date':request.as_of_date.isoformat(),
        'base':base,'sensitivity':sensitivity,'coverage':{'scoped_road_rows':len(snapshot['roads']),'snapshot_road_rows':snapshot['snapshot_road_count'],
            'selection':'Explicit road-row ID set; not a citywide census','geographic_coverage':snapshot['base']['coverage']},
        'definitions':DEFINITIONS,'warnings':WARNINGS,'contains_synthetic':False,'classification':'derived_calculation','utility_coverage':'unknown'}
    PriorityResult.model_validate(result)
    return result
