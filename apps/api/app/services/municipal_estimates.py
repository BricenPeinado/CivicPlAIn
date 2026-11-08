"""Deterministic official-road planning. No catalog defaults, AI, network or suitability inference."""
from decimal import Decimal,localcontext
from app.schemas.municipal_planning import EstimateRequest
from app.schemas.municipal import MunicipalRecord
from app.services.cost_math import assemble,workdays,VERSION as ARITHMETIC
from app.services.municipal_data import digest

VERSION='municipal-area-cost-v1'
AREA={'m2':Decimal(1),'yd2':Decimal('0.83612736'),'ft2':Decimal('0.09290304')}
LENGTH={'m':Decimal(1),'ft':Decimal('0.3048')}
METHODS={
 'patch':{'label':'Localized pavement patching','scope':'Planner-declared localized area; no defect depth or material quantity inferred',
    'source':'https://www.fhwa.dot.gov/preservation/memos/160225.cfm'},
 'resurface':{'label':'Pavement resurfacing','scope':'Planner-declared surface treatment; milling/layers/markings included only as explicitly priced',
    'source':'https://www.nyc.gov/html/dot/html/infrastructure/construction.shtml'}}
WARNINGS=[
 'Planning estimate for the declared scope, not actual expenditure, a contractor bid or municipal approval.',
 'All entered numeric values and source citations are planner-declared assumptions; citations are not independently verified.',
 'No synthetic catalog prices, inferred road dimensions, lifespan, savings, construction dates or closure duration.',
 'Condition/structural suitability, actual work footprint and utility coverage remain unknown; human engineering review required. No excavation clearance.',
 'Low/high are supplied rate sensitivities, not confidence limits; different treatment scopes are not equivalent benefits.']

def frozen_inputs(body,road,source,base):
    MunicipalRecord.model_validate(road)
    if (road['kind']!='road' or road['id']!=body.road_id or base['id']!=body.snapshot_id
        or road['source_revision_id']!=source['id'] or source['id'] not in base['source_revision_ids']):raise ValueError('Inconsistent road/base/source context')
    if road['contains_synthetic'] or road['classification']=='synthetic_fixture' or 'synthetic_fixture' in road['field_classifications'].values() or source.get('query',{}).get('synthetic_fixture'):
        raise ValueError('Synthetic evidence cannot price an official road')
    return {'request':body.model_dump(mode='json'),'road':road,'road_source':source,'base':base,
        'method_version':VERSION,'arithmetic_version':ARITHMETIC,
        'conversions':{'area_to_m2':{k:str(v) for k,v in AREA.items()},'length_to_m':{k:str(v) for k,v in LENGTH.items()}},
        'methods':METHODS}

def quantity(scope):
    if scope is None:return None,['scope']
    if scope.area:area=scope.area.number*AREA[scope.area.unit]
    else:
        missing=[key for key in ['length','width'] if not getattr(scope,key)]
        if missing:return None,missing
        area=scope.length.number*LENGTH[scope.length.unit]*scope.width.number*LENGTH[scope.width.unit]
    if area<=0 or area>10000000:raise ValueError('Treatment area must be positive and at most 10,000,000 m2')
    return area,[]

def calculate(snapshot):
    if snapshot['method_version']!=VERSION or snapshot['arithmetic_version']!=ARITHMETIC:raise ValueError('Unsupported calculation version')
    expected={'area_to_m2':{k:str(v) for k,v in AREA.items()},'length_to_m':{k:str(v) for k,v in LENGTH.items()}}
    if snapshot['conversions']!=expected:raise ValueError('Unsupported conversion version')
    body=EstimateRequest.model_validate(snapshot['request'])
    results=[]
    with localcontext() as ctx:
        ctx.prec=40
        for option in sorted(body.alternatives,key=lambda a:a.treatment):
            path=f'request.alternatives.{body.alternatives.index(option)}'
            area,missing=quantity(option.scope)
            for key in ['rate','price_basis_date','geography','inclusions','contingency','exclusions','cost_overlap_review']:
                if not getattr(option,key):missing.append(key)
            for key in ['mobilization','traffic_control']:
                if not any(a.key==key for a in option.allowances):missing.append(key)
            missing.extend(a.label for a in option.allowances if a.disposition=='unknown')
            unknowns=['Treatment suitability and pavement structure unverified','Actual work footprint/schedule and utility locations unknown']
            if option.sensitivity is None:unknowns.append('Rate sensitivity bounds not supplied; cost range unavailable')
            duration=None
            if option.productivity and option.setup_days and option.curing_days and area is not None:
                active=workdays(area/AREA[option.productivity.unit.split('/')[0]],option.productivity.number)
                setup=int(option.setup_days.number);curing=int(option.curing_days.number)
                duration={'active_workdays':active,'setup_days':setup,'curing_days':curing,'total_preliminary_days':active+setup+curing,
                    'basis':'Sequential productivity + setup + curing assumptions; not calendar duration, closure time or contractor schedule'}
            else:unknowns.append('Duration unavailable: explicit quantity, productivity, setup and curing assumptions required')
            cases=None
            if not missing:
                cost_quantity=area/AREA[option.rate.unit.split('/')[1]]
                priced=[a for a in option.allowances if a.disposition=='priced']
                rates={'base':option.rate}
                if option.sensitivity:rates.update(low=option.sensitivity.low,high=option.sensitivity.high)
                cases={}
                for case,rate in rates.items():
                    cost=assemble(cost_quantity,rate.number,[a.amount.number for a in priced],option.contingency.number)
                    lines=[{'label':'Bundled treatment: '+snapshot['methods'][option.treatment]['label'],
                        'quantity':format(cost_quantity,'f'),'unit':rate.unit.split('/')[1],'rate_usd':rate.value,
                        'amount_usd':cost['amounts'][0],'amount_cents':int(Decimal(cost['amounts'][0])*100),'evidence_path':f'{path}.rate' if case=='base' else f'{path}.sensitivity.{case}'}]
                    lines.extend({'label':a.label,'quantity':'1','unit':'allowance','rate_usd':a.amount.value,
                        'amount_usd':amount,'amount_cents':int(Decimal(amount)*100),'evidence_path':f'{path}.allowances.{option.allowances.index(a)}.amount'} for a,amount in zip(priced,cost['amounts'][1:]))
                    cases[case]={'line_items':lines,**{k:v for k,v in cost.items() if k!='amounts'},
                        'contingency_fraction':option.contingency.value,'total_cents':int(Decimal(cost['total_usd'])*100)}
            results.append({'treatment':option.treatment,'status':'unavailable' if missing else 'available',
                'input_path':path,'missing_fields':sorted(set(missing)),'scope':option.scope.model_dump(mode='json') if option.scope else None,
                'quantity_m2':format(area,'f') if area is not None else None,'cases':cases,'duration':duration,
                'price_basis_date':str(option.price_basis_date) if option.price_basis_date else None,'geography':option.geography,
                'inclusions':option.inclusions,'exclusions':option.exclusions,
                'allowance_declarations':[a.model_dump(mode='json') for a in option.allowances],
                'unknowns':unknowns,'suitability':'requires_engineering_review','classification':'derived_calculation'})
    return {'contract_version':'municipal-estimate-v1','method_version':VERSION,'arithmetic_version':ARITHMETIC,
        'snapshot_id':body.snapshot_id,'road_id':body.road_id,'currency':'USD','alternatives':results,
        'warnings':WARNINGS,'utility_coverage':'unknown','classification':'derived_calculation',
        'contains_assumptions':True,'contains_synthetic':False,
        'comparison_basis':'Costs apply to independently declared scopes; no automatic ranking, savings or equal-benefit assertion'}
