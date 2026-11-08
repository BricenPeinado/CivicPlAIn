"""Pure bounded official-context screening, never an excavation/safety decision."""
from itertools import combinations
from decimal import Decimal,localcontext
import shapely,pyproj
from shapely.geometry import shape
from app.schemas.official_screening import ScreeningRequest
from app.services.conflicts import PROJECT,NUMERICAL_EPSILON_M
from app.services.screening_math import overlap_bounds
from app.services.cost_math import money
from app.services.municipal_data import digest

VERSION='official-screen-v1'
WARNINGS=[
 'No finding is not clearance. Utility inventory, excavation depth, actual schedules and physical work coverage may be missing.',
 'Permit issue/effective/expiration/status fields are administrative facts only; they never populate work schedules or footprints.',
 'Supplied documents are attributed declarations, not independently verified government facts. Planner geometry/schedules remain assumptions.',
 'Projected overlap verifies only the supplied 2D shapes. Grade, actual excavation and field accuracy require human review.',
 'Thresholds and rework horizon are explicit planning policy assumptions; no optimized schedule, automatic approval or work order.']
LIBRARIES={'shapely':shapely.__version__,'geos':shapely.geos_version_string,'pyproj':pyproj.__version__,'proj':pyproj.proj_version_str}

def projected(geom):
    return shapely.transform(shape(geom),PROJECT.transform,interleaved=False)

def screen(works,permits,roads,parameters):
    """At most 60 entries; complete pair enumeration preserves unknown-location checks."""
    activities=[];issues=[]
    for work in sorted(works,key=lambda w:w['id']):
        w=dict(work);w['origin']='supplied_work';w['activity_id']='work:'+w['id'];w['location_issue']=None
        if w['location'] and w['road_ids']:
            g=projected(w['location']['geometry'])
            if any(g.distance(projected(roads[r]['geometry']))>parameters['proximity_m']+NUMERICAL_EPSILON_M for r in w['road_ids']):
                w['location_issue']='DECLARED_GEOMETRY_DISAGREES_WITH_ROAD_REFERENCE'
        activities.append(w)
    for record in sorted(permits,key=lambda p:p['record']['id']):
        r=record['record'];location=record['location']
        activities.append({'id':r['id'],'activity_id':'permit:'+r['id'],'origin':'administrative_permit','title':r['source_record_key'],
            'work_type':'unknown','road_ids':location['accepted_road_ids'],'permit_ids':[r['id']], 'location':None,'location_issue':'PERMIT_IS_NOT_WORK_FOOTPRINT',
            'schedule':None,'grade':'unknown','excavation_required':None,'excavation_depth_m':None,'closure':None,'source_record_hash':digest(r),'permit_location':location,
            'administrative_dates':{k:r['values'].get(k) for k in ['issued_at','valid_from','valid_to','permit_status']}})
    findings=[];checks=[]
    geoms={w['activity_id']:projected(w['location']['geometry']) for w in activities if w['location'] and not w['location_issue']}
    for w in activities:
        missing=[]
        for key in ['location','schedule','excavation_depth_m']:
            if w.get(key) is None:missing.append(key)
        if w['location_issue']:missing.append(w['location_issue'])
        if w['grade']=='unknown':missing.append('grade')
        if missing:issues.append({'activity_id':w['activity_id'],'missing':missing,'actual_work_confirmation':'unverified'})
    for a,b in combinations(activities,2):
        ids=[a['activity_id'],b['activity_id']];ga,gb=geoms.get(ids[0]),geoms.get(ids[1])
        distance=ga.distance(gb) if ga is not None and gb is not None else None
        intersects=ga.intersects(gb) if distance is not None else None
        overlap=ga.geom_type==gb.geom_type=='Polygon' and ga.intersection(gb).area>0 if distance is not None else None
        shared=sorted(set(a['road_ids'])&set(b['road_ids']))
        near=distance is not None and distance<=parameters['proximity_m']+NUMERICAL_EPSILON_M
        grade='unknown' if 'unknown' in [a['grade'],b['grade']] else 'same_declared_level' if a['grade']==b['grade'] else 'different_declared_levels'
        spatial={'distance_m':round(distance,6) if distance is not None else None,'geometry_intersects':intersects,'positive_area_overlap':overlap,
            'shared_road_ids':shared,'grade_relation':grade,'crs':'EPSG:32618','basis':'Computed supplied geometry only; road references are not footprints',
            'approximate':any(w['location'] and w['location']['certainty']=='approximate' for w in [a,b])}
        missing=[]
        if distance is None:missing.append('work_footprint')
        if grade=='unknown':missing.append('grade_separation')
        sa,sb=a['schedule'],b['schedule'];temporal={'relation':'unknown','intervals':{ids[i]:w['schedule'] for i,w in enumerate([a,b])},'gap_days':None}
        if sa and sb:
            from datetime import date
            da=[date.fromisoformat(sa[k]) for k in ['start','end']];db=[date.fromisoformat(sb[k]) for k in ['start','end']]
            start,end=overlap_bounds(da,db)
            temporal['relation']='overlap' if start<end else 'adjacent' if start==end else 'separate'
            first,second,d1,d2=(a,b,da,db) if da[1]<=db[0] else (b,a,db,da)
            if start>=end:temporal['gap_days']=(d2[0]-d1[1]).days
        else:missing.append('work_schedule')
        status='indeterminate' if missing else 'grade_separated' if grade=='different_declared_levels' else 'related' if near else 'not_spatially_related'
        if grade=='different_declared_levels':status='grade_separated'
        check={'activity_ids':ids,'status':status,'spatial':spatial,'temporal':temporal,'missing_fields':missing,
            'location_issues':[w['location_issue'] for w in [a,b] if w['location_issue']], 'depth_relation':'unknown','physical_interference':'unverified'}
        checks.append(check)
        # Shared identifiers alone, unknown footprints, and separate grades never establish conflict.
        if not near or distance is None or not sa or not sb or grade=='different_declared_levels':continue
        kinds=[]
        if temporal['relation']=='overlap':
            kinds.append(('concurrent_work','Supported overlap of supplied work intervals and related 2D geometries; coordinate scopes.'))
            ca,cb=a['closure'],b['closure']
            if ca and cb and max(ca['start'],cb['start'])<min(ca['end'],cb['end']):
                kinds.append(('multiple_closure_plans','Explicit closure intervals overlap near supplied work zones; actual closure/access impact is unverified.'))
            if a['work_type']=='resurfacing' or b['work_type']=='resurfacing':kinds.append(('resurfacing_coordination','Resurfacing and another supplied work plan overlap; inspect actual restoration and access requirements.'))
        elif temporal['gap_days'] is not None and 0<=temporal['gap_days']<=parameters['reopening_horizon_days']:
            if first['work_type']=='resurfacing' and second['excavation_required'] is True:
                kinds.append(('potential_pavement_rework','Supplied resurfacing precedes explicitly declared excavation within the review horizon; pavement damage and loss are not established.'))
            else:kinds.append(('adjacent_work_coordination','Spatially related work lies within the explicit sequencing window; shared mobilization or savings are not inferred.'))
        for kind,explanation in kinds:
            supported=grade=='same_declared_level' and not spatial['approximate'] and bool(intersects)
            finding={'activity_ids':ids,'finding_type':kind,'category':'supported_conflict_finding' if supported and kind in ['concurrent_work','multiple_closure_plans','potential_pavement_rework'] else 'potential_coordination_opportunity',
                'spatial':spatial,'temporal':temporal,'explanation':explanation,'qualified_by':missing,
                'evidence_hashes':{w['activity_id']:digest(w) for w in [a,b]},'contains_planning_assumptions':any('planning_assumption' in str(w) for w in [a,b]),
                'evidence_status':'supplied_evidence_only_not_independently_verified','human_review_required':True,
                'required_review':['Confirm work footprint, grade, depth and schedule with responsible organizations.','Review assumed/documentary declarations; no approval, utility clearance or safe-deferral conclusion.']}
            finding['id']='finding-'+digest({'method':VERSION,'parameters':parameters,'finding':finding});findings.append(finding)
    return {'activities':activities,'findings':sorted(findings,key=lambda f:f['id']),'pair_checks':checks,'activity_unknowns':issues,
        'possible_pair_count':len(activities)*(len(activities)-1)//2,'checked_pair_count':len(checks),
        'indeterminate_pair_count':sum(c['status']=='indeterminate' for c in checks)}

def calculate(snapshot):
    if snapshot['method_version']!=VERSION or snapshot['libraries']!=LIBRARIES:raise ValueError('Unsupported method or GIS runtime; replay in pinned environment')
    body=ScreeningRequest.model_validate(snapshot['request']);request=body.model_dump(mode='json')
    roads={r['id']:r for r in snapshot['roads']};parameters={k:request[k] for k in ['proximity_m','reopening_horizon_days']}
    base=screen(request['works'],snapshot['permits'],roads,parameters);alternatives=[]
    for alternative in request['alternatives']:
        overrides={o['work_id']:o for o in alternative['overrides']}
        works=[w|{k:overrides[w['id']][k] for k in ['schedule','closure']} if w['id'] in overrides else w for w in request['works']]
        value=screen(works,snapshot['permits'],roads,parameters)
        alternatives.append({'id':alternative['id'],'evidence':alternative['evidence'],'screen':value,'result_hash':digest(value),
            'interpretation':'Changed supplied schedules only. Finding-count changes do not establish benefit, safety or optimality.'})
    cost={'status':'unavailable','reason':'No complete explicit same-scope estimate and schedule-cost assumptions supplied','comparisons':[]}
    if body.cost_comparison:
        c=body.cost_comparison;saved=snapshot['estimate']
        if saved is None:raise ValueError('Selected estimate missing')
        alt=next(a for a in saved['result']['alternatives'] if a['treatment']==c.treatment)
        with localcontext() as ctx:
            ctx.prec=40
            common=Decimal(alt['cases']['base']['total_usd']);addition=Decimal(money(c.base_schedule_addition.number));total=common+addition
            cost={'status':'declared_comparable_scope','estimate_id':saved['id'],'treatment':c.treatment,'scope':alt['scope'],'quantity_m2':alt['quantity_m2'],
                'common_estimate_usd':money(common),'base_explicit_addition_usd':money(addition),'base_total_usd':money(total),
                'comparisons':[{'alternative_id':key,'explicit_addition_usd':money(value.number),'total_usd':money(common+Decimal(money(value.number))),
                    'difference_from_base_usd':money(Decimal(money(value.number))-addition)} for key,value in sorted(c.alternative_schedule_additions.items())],
                'basis':'Same frozen estimate scope in every schedule; differences are exclusively attributed explicit nonoverlapping additions. Not predicted savings, actual expenditure or bid.',
                'unknowns':alt['unknowns'],'exclusions':alt['exclusions'],'evidence':c.model_dump(mode='json')}
    return {'method_version':VERSION,'snapshot_id':body.snapshot_id,'base':base,'alternatives':alternatives,'cost_comparison':cost,
        'coverage':{'selected_work_declarations':len(body.works),'selected_administrative_records':len(snapshot['permits']),
            'snapshot_coverage':snapshot['base']['coverage'],'selection':'Explicit bounded selection, not a complete construction or utility inventory',
            'utilities':'unknown','actual_work_inventory':'unknown','excavation_clearance':False},
        'warnings':WARNINGS,'classification':'derived_calculation','contains_synthetic':False,'human_review_required':True}
