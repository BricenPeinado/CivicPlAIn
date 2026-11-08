"""M7 read boundary. Explicit snapshot context; no official mutation/calculation routes."""
from threading import RLock
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from shapely.geometry import box, shape

from app.core.municipal_repository import paginate
from app.core.repository import InvalidQuery
from app.routes.roads import parse_bbox

router=APIRouter(prefix='/api/v2')
Limit=Annotated[int,Query(ge=1,le=100)]
PERMIT_CONTEXT_LOCK=RLock()


def repo(request):
    return request.app.state.municipal


def strict(request,allowed):
    if set(request.query_params)-set(allowed) or any(len(request.query_params.getlist(k))!=1 for k in request.query_params):
        raise InvalidQuery('Unknown or repeated query parameter')


def envelope(request,data,sid=None,cursor=None,total=None,**extras):
    manifest=repo(request).snapshot(sid) if sid else None
    return {'data':data,'meta':{'request_id':request.state.request_id,'contract_version':'municipal-record-v2',
        'snapshot_id':sid,'mode':'official','coverage':manifest['coverage'] if manifest else None,
        'capabilities':manifest['capabilities'] if manifest else None,'warnings':manifest['warnings'] if manifest else [],
        'returned_count':len(data) if isinstance(data,list) else 1,'total_matching':total,
        'next_cursor':cursor,**extras}}


def listing(request,values,sid,limit,cursor,**extras):
    binding={'endpoint':request.url.path,'contract':'municipal-record-v2','snapshot':sid,
        'filters':sorted((k,v) for k,v in request.query_params.items() if k not in {'cursor','limit'})}
    page,next_cursor=paginate(values,limit,cursor,binding)
    return envelope(request,page,sid,next_cursor,len(values),**extras)


def filters(values,q):
    if q is None:
        return values
    q=q.strip()
    if not q or len(q)>100:
        raise InvalidQuery('q must contain 1–100 characters')
    return [r for r in values if q.casefold() in str(r['values'].get('name',r['values'].get('on_street','')) or '').casefold()
            or q.casefold() in r['source_record_key'].casefold()]


@router.get('/workspace')
def workspace(request:Request):
    strict(request,[])
    settings=request.app.state.settings
    if settings.data_mode=='official':
        manifest=repo(request).snapshot(settings.official_snapshot_id)
        return {'data':{'mode':'official','snapshot_id':manifest['id'],'capabilities':manifest['capabilities']},
            'meta':{'request_id':request.state.request_id}}
    return {'data':{'mode':'synthetic','snapshot_id':request.app.state.repository.snapshot()},
        'meta':{'request_id':request.state.request_id}}


@router.get('/data-snapshots')
def snapshots(request:Request,limit:Limit=100,cursor:str|None=None):
    strict(request,['limit','cursor'])
    return listing(request,repo(request).snapshots(),None,limit,cursor)


@router.get('/data-snapshots/{snapshot_id}')
def snapshot(request:Request,snapshot_id:str):
    strict(request,[])
    return envelope(request,repo(request).snapshot(snapshot_id),snapshot_id)


@router.get('/road-segments')
@router.get('/road-segments/geojson')
def roads(request:Request,snapshot_id:str,bbox:str|None=None,q:str|None=None,
          condition:str|None=None,limit:Annotated[int,Query(ge=1,le=2000)]=100,cursor:str|None=None,
          release_id:str|None=None,as_of_date:str|None=None,policy_id:str|None=None):
    strict(request,['snapshot_id','bbox','q','condition','limit','cursor','release_id','as_of_date','policy_id'])
    validate_policy_context(policy_id,snapshot_id,release_id)
    if (release_id or policy_id) and not as_of_date:
        raise InvalidQuery('Explicit as_of_date required for intelligence road context')
    if as_of_date: validate_as_of(as_of_date)
    if condition is not None and condition not in {'good','fair','poor','unknown'}:
        raise InvalidQuery('Invalid condition')
    bounds=parse_bbox(bbox)
    geo=request.url.path.endswith('/geojson')
    if geo and bounds is None:
        raise InvalidQuery('bbox is required for GeoJSON')
    records=filters(repo(request).records(snapshot_id,'road',bounds),q)
    records=repo(request).enrich(snapshot_id,records)
    if release_id:
        groups=accepted_groups(request,snapshot_id,release_id)
        inputs={key:repo(request).get(snapshot_id,'condition',key) for matches in groups.values() for key in matches}
        from app.services.road_conditions import summarize
        for r in records:
            matches=groups.get(r['id'],{})
            r['condition_summary']=summarize([inputs[key] for key in matches],matches,r['id'],snapshot_id,as_of_date,
                release_id=release_id,policy_id=policy_id)
    if condition:
        records=[r for r in records if r['condition_summary']['category']==condition]
    if (geo or bounds is not None and limit > 100) and len(records)>2000:
        raise HTTPException(422,'VIEWPORT_TOO_BROAD: refine viewport to at most 2000 features')
    result=listing(request,records,snapshot_id,limit,cursor)
    if geo:
        return as_geojson(result)
    # Records are already validated/dumped in JSON mode by the repository. Avoid
    # FastAPI's second recursive conversion of complete provenance on every pan.
    return JSONResponse(result)


def as_geojson(result):
    features=[{'type':'Feature','id':r['id'],'geometry':r['geometry'],
        'properties':{k:r[k] for k in ['id','kind','source_revision_id','source_record_key','classification','values','field_classifications']}
            | ({'condition_summary':r['condition_summary']} if 'condition_summary' in r else {})}
        for r in result['data']]
    return JSONResponse({'type':'FeatureCollection','features':features,'meta':result['meta']},media_type='application/geo+json')


@router.get('/road-segments/{road_id}/conditions')
def conditions(request:Request,road_id:str,snapshot_id:str,limit:Limit=100,cursor:str|None=None):
    strict(request,['snapshot_id','limit','cursor'])
    repo(request).get(snapshot_id,'road',road_id)
    matches=repo(request).matches(snapshot_id)
    records=[repo(request).get(snapshot_id,'condition',key) for key,m in sorted(matches.items())
             if m['source_kind']=='condition' and m['target_road_id']==road_id]
    # Stable descending source date, ascending ID for ties, nulls last.
    records.sort(key=lambda r:r['id'])
    records.sort(key=lambda r:r['values']['inspection_at'] or '',reverse=True)
    latest=next((r['id'] for r in records if r['values']['inspection_at'] and r['values']['rating']),None)
    newest=next((r['values']['inspection_at'] for r in records if r['values']['inspection_at'] and r['values']['rating']),None)
    conflicting=bool(newest and len({r['values']['rating'] for r in records if r['values']['inspection_at']==newest and r['values']['rating'] is not None})>1)
    return listing(request,repo(request).enrich(snapshot_id,records),snapshot_id,limit,cursor,
        latest_usable_id=None if conflicting else latest,conflicting_latest_ratings=conflicting)


@router.get('/road-segments/{road_id}')
def road(request:Request,road_id:str,snapshot_id:str):
    strict(request,['snapshot_id'])
    return envelope(request,repo(request).enrich(snapshot_id,[repo(request).get(snapshot_id,'road',road_id)])[0],snapshot_id)


@router.get('/conditions')
def all_conditions(request:Request,snapshot_id:str,bbox:str|None=None,limit:Limit=100,cursor:str|None=None,
                   release_id:str|None=None,assessment_scope:str='all',as_of_date:str|None=None,policy_id:str|None=None):
    strict(request,['snapshot_id','bbox','limit','cursor','release_id','assessment_scope','as_of_date','policy_id'])
    validate_policy_context(policy_id,snapshot_id,release_id)
    if assessment_scope not in {'all','current','historical','unaccepted'}:
        raise InvalidQuery('Unsupported assessment scope')
    if as_of_date is not None:
        validate_as_of(as_of_date)
    if assessment_scope in {'current','historical'} and as_of_date is None:
        raise InvalidQuery('Explicit as_of_date required for current/historical assessments')
    records=repo(request).records(snapshot_id,'condition',parse_bbox(bbox))
    accepted=set();current=set()
    if assessment_scope!='all' or release_id is not None:
        from app.services.road_conditions import summarize
        groups={}
        if release_id is not None:
            associations=intelligence_repo(request).associations(snapshot_id,release_id,status='accepted')
            for a in associations:
                groups.setdefault(a['target_road_id'],{})[a['source_record_id']]=association_match(a,release_id)
        else:
            for key,m in repo(request).matches(snapshot_id).items():
                if m['source_kind']=='condition' and m['status']=='matched':
                    groups.setdefault(m['target_road_id'],{})[key]=m
        accepted={key for matches in groups.values() for key in matches}
        if assessment_scope in {'current','historical'}:
            inputs={key:repo(request).get(snapshot_id,'condition',key) for key in sorted(accepted)}
            for road_id,matches in groups.items():
                summary=summarize([inputs[key] for key in sorted(matches)],matches,road_id,snapshot_id,as_of_date,release_id=release_id,policy_id=policy_id)
                if summary['latest_usable_id']:current.add(summary['latest_usable_id'])
        if assessment_scope=='unaccepted':records=[r for r in records if r['id'] not in accepted]
        elif assessment_scope=='current':records=[r for r in records if r['id'] in current]
        elif assessment_scope=='historical':
            records=[r for r in records if r['id'] in accepted-current and r['values'].get('inspection_at') and r['values']['inspection_at'][:10]<=as_of_date]
    return listing(request,repo(request).enrich(snapshot_id,records),snapshot_id,limit,cursor,
                   intelligence_release_id=release_id,assessment_scope=assessment_scope,as_of_date=as_of_date)


@router.get('/permits')
def permits(request:Request,snapshot_id:str,road_id:str|None=None,q:str|None=None,status:str|None=None,
            location:str='all',bbox:str|None=None,limit:Limit=100,cursor:str|None=None,
            location_status:str|None=None,permit_release_id:str|None=None,evidence:bool=False,include_candidates:bool=False):
    strict(request,['snapshot_id','road_id','q','status','location','bbox','limit','cursor','location_status','permit_release_id','evidence','include_candidates'])
    if include_candidates and not road_id:raise InvalidQuery('Candidate inclusion requires an explicit road_id')
    from app.services.permit_intelligence import STATUSES
    if location_status is not None and location_status not in STATUSES:raise InvalidQuery('Invalid evidence status')
    enhanced=evidence or include_candidates or location_status is not None or permit_release_id is not None
    projections=permit_context(request,snapshot_id,permit_release_id)[1] if enhanced else {}
    if location not in {'all','matched','ambiguous','unmatched','unlocated'}:
        raise InvalidQuery('Invalid location filter')
    if status is not None and (not status.strip() or len(status)>100):
        raise InvalidQuery('status must contain 1–100 characters')
    if road_id:
        repo(request).get(snapshot_id,'road',road_id)
    inputs=repo(request).records(snapshot_id,'permit')
    if enhanced and q is not None:
        filters([],q) # common strict length/blank validation
        needle=q.strip().casefold()
        inputs=[r for r in inputs if needle in str([r['source_record_key'],r['values'],r['raw_identifiers']]).casefold()]
    else:inputs=filters(inputs,q)
    records=repo(request).enrich(snapshot_id,inputs)
    excluded=0
    bounds=parse_bbox(bbox)
    viewport=box(*bounds) if bounds else None
    linked_roads={r['id']:r for r in repo(request).records(snapshot_id,'road')} if bounds else {}
    result=[]
    for r in records:
        m=r['match']
        if enhanced:
            r['permit_location']=projections[r['id']]
            if location_status and r['permit_location']['status']!=location_status:continue
        accepted=projections[r['id']]['accepted_road_ids'] if enhanced else ([m['target_road_id']] if m['target_road_id'] else [])
        road_candidates={c['road_id'] for c in projections[r['id']]['candidates']} if include_candidates else set()
        if road_id and road_id not in accepted and road_id not in road_candidates or status is not None and r['values']['permit_status']!=status:
            continue
        if location=='unlocated' and r['location_basis']!='unknown' or location not in {'all','unlocated'} and m['status']!=location:
            continue
        if bounds and not r['geometry'] and not accepted:
            excluded+=1
        usable_geometry=r['geometry'] if not enhanced or 'GEOMETRY_CRS_UNVERIFIED' not in projections[r['id']]['reasons'] else None
        geometries=[usable_geometry] if usable_geometry else [linked_roads[rid]['geometry'] for rid in accepted if rid in linked_roads]
        if viewport is not None and not any(shape(g).intersects(viewport) for g in geometries):
            continue
        result.append(r)
    return listing(request,result,snapshot_id,limit,cursor,unlocated_excluded_count=excluded if bounds else 0)


@router.get('/permits/{permit_id}')
def permit(request:Request,permit_id:str,snapshot_id:str,permit_release_id:str|None=None,evidence:bool=False):
    strict(request,['snapshot_id','permit_release_id','evidence'])
    record=repo(request).enrich(snapshot_id,[repo(request).get(snapshot_id,'permit',permit_id)])[0]
    if evidence or permit_release_id:record['permit_location']=permit_context(request,snapshot_id,permit_release_id)[1][permit_id]
    return envelope(request,record,snapshot_id)


@router.get('/context/geojson')
def context(request:Request,snapshot_id:str,bbox:str,layer:str='shoreline',limit:Limit=100,cursor:str|None=None):
    strict(request,['snapshot_id','bbox','layer','limit','cursor'])
    if layer!='shoreline':
        raise InvalidQuery('Unsupported context layer')
    bounds=parse_bbox(bbox)
    extent=repo(request).snapshot(snapshot_id)['coverage']['context_bbox']
    if not box(*extent).covers(box(*bounds)):
        raise InvalidQuery('Context bbox exceeds approved extent')
    records=repo(request).records(snapshot_id,'context',bounds)
    if len(records)>2000:
        raise HTTPException(422,'VIEWPORT_TOO_BROAD: refine viewport')
    return as_geojson(listing(request,records,snapshot_id,limit,cursor))


@router.get('/source-revisions/{source_id}')
def source(request:Request,source_id:str,snapshot_id:str):
    strict(request,['snapshot_id'])
    return envelope(request,repo(request).source(snapshot_id,source_id),snapshot_id)


@router.get('/dashboard')
def dashboard(request:Request,snapshot_id:str):
    strict(request,['snapshot_id'])
    return envelope(request,repo(request).dashboard(snapshot_id),snapshot_id)


@router.get('/road-segments/{road_id}/condition-summary')
def condition_summary(request:Request,road_id:str,snapshot_id:str,as_of_date:str,
                      stale_after_days:Annotated[int|None,Query(ge=0,le=36500)]=None,release_id:str|None=None,policy_id:str|None=None):
    from datetime import date
    from app.services.road_conditions import summarize
    from app.schemas.road_intelligence import ConditionSummary
    strict(request,['snapshot_id','as_of_date','stale_after_days','release_id','policy_id'])
    validate_policy_context(policy_id,snapshot_id,release_id)
    validate_as_of(as_of_date)
    repo(request).get(snapshot_id,'road',road_id)
    matches={key:m for key,m in repo(request).matches(snapshot_id).items()
             if m['source_kind']=='condition' and m['status']=='matched' and m['target_road_id']==road_id}
    if release_id is not None:
        associations=intelligence_repo(request).associations(snapshot_id,release_id,road_id)
        matches={a['source_record_id']:association_match(a,release_id) for a in associations if a['status']=='accepted'}
    records=[repo(request).get(snapshot_id,'condition',key) for key in sorted(matches)]
    result=summarize(records,matches,
                     road_id,snapshot_id,as_of_date,stale_after_days,release_id,policy_id)
    return envelope(request,ConditionSummary.model_validate(result).model_dump(mode='json'),snapshot_id)


def intelligence_repo(request):
    from app.core.intelligence_repository import IntelligenceRepository
    return IntelligenceRepository(request.app.state.settings.database_path)


@router.get('/intelligence-releases')
def intelligence_releases(request:Request,snapshot_id:str,limit:Limit=100,cursor:str|None=None,kind:str='condition'):
    strict(request,['snapshot_id','limit','cursor','kind'])
    if kind not in {'condition','permit'}:raise InvalidQuery('Unsupported release kind')
    repo(request).snapshot(snapshot_id)
    return listing(request,intelligence_repo(request).releases(snapshot_id,kind),snapshot_id,limit,cursor)


@router.get('/intelligence-releases/{release_id}')
def intelligence_release(request:Request,release_id:str,snapshot_id:str):
    strict(request,['snapshot_id'])
    repo(request).snapshot(snapshot_id)
    return envelope(request,intelligence_repo(request).get(snapshot_id,release_id),snapshot_id)


@router.get('/road-associations')
def road_associations(request:Request,snapshot_id:str,release_id:str,road_id:str|None=None,
                      status:str|None=None,limit:Limit=100,cursor:str|None=None):
    strict(request,['snapshot_id','release_id','road_id','status','limit','cursor'])
    repo(request).snapshot(snapshot_id)
    if road_id:
        repo(request).get(snapshot_id,'road',road_id)
    if status is not None and status not in {'accepted','candidate','rejected','unmatched'}:
        raise InvalidQuery('Unsupported association status')
    values=intelligence_repo(request).associations(snapshot_id,release_id,road_id)
    if status:
        values=[a for a in values if a['status']==status]
    return listing(request,values,snapshot_id,limit,cursor)


def validate_as_of(value):
    from datetime import date
    try:
        if date.fromisoformat(value).isoformat()!=value:
            raise ValueError
    except ValueError:
        raise InvalidQuery('as_of_date must be YYYY-MM-DD') from None


def association_match(a,release_id):
    return {'id':a['id'],'source_kind':'condition','status':'matched',
        'target_road_id':a['target_road_id'],'method':'reviewed-candidates-v2','decision':a['decision'],
        'candidate_hash':a['candidate_hash'],'parameter_hash':a['parameter_hash'],'release_id':release_id}


def validate_policy_context(policy_id,snapshot_id,release_id):
    from app.services.pavement_policy import validate_context
    try:
        validate_context(policy_id,snapshot_id,release_id)
    except ValueError as exc:
        raise InvalidQuery(str(exc)) from None


def accepted_groups(request,snapshot_id,release_id):
    groups={}
    for a in intelligence_repo(request).associations(snapshot_id,release_id,status='accepted'):
        groups.setdefault(a['target_road_id'],{})[a['source_record_id']]=association_match(a,release_id)
    return groups


def permit_context(request,snapshot_id,release_id=None):
    """Bounded two-context in-memory cache; no persisted GET products or refresh."""
    from collections import OrderedDict,Counter
    from app.services.permit_intelligence import locations,STATUSES,PARAMETERS
    from app.schemas.permit_intelligence import PermitLocation
    from app.services.municipal_data import digest
    base=repo(request).snapshot(snapshot_id)
    associations=None
    if release_id:
        associations=[a for status in ['accepted','rejected'] for a in intelligence_repo(request).associations(snapshot_id,release_id,status=status,kind='permit')]
    with PERMIT_CONTEXT_LOCK:
        key=(snapshot_id,release_id)
        cache=getattr(request.app.state,'permit_evidence_cache',None)
        if cache is None:cache=OrderedDict();request.app.state.permit_evidence_cache=cache
        if key not in cache:
            roads=repo(request).records(snapshot_id,'road');records=repo(request).records(snapshot_id,'permit')
            sources={sid:repo(request).source(snapshot_id,sid) for sid in base['source_revision_ids']}
            projections=locations(snapshot_id,base,roads,records,sources,associations,release_id)
            for value in projections.values():PermitLocation.model_validate(value)
            counts=Counter(p['status'] for p in projections.values())
            coverage={'snapshot_id':snapshot_id,'permit_release_id':release_id,'method_version':PARAMETERS['version'],
                'total_permits':len(records),'status_counts':{status:counts[status] for status in STATUSES},
                'accepted_road_rows':len({rid for p in projections.values() for rid in p['accepted_road_ids']}),
                'source_selection':base['coverage']['permit_selection'],'utility_coverage':'unknown',
                'precision':'No independently labeled permit matches; automatic acceptance disabled',
                'limitations':['Street-name/code candidates may span long streets or aliases; geographic membership unverified.',
                    'No inferred WKT CRS. Administrative validity is not a confirmed work schedule or closure.',
                    'No findings cannot establish completeness, absence of work or excavation safety.']}
            coverage['result_hash']=digest(coverage)
            cache[key]=(records,projections,coverage)
            while len(cache)>2:cache.popitem(last=False)
        cache.move_to_end(key)
        return cache[key]


@router.get('/permit-location-coverage')
def permit_location_coverage(request:Request,snapshot_id:str,permit_release_id:str|None=None):
    strict(request,['snapshot_id','permit_release_id'])
    return envelope(request,permit_context(request,snapshot_id,permit_release_id)[2],snapshot_id)


@router.get('/permits/{permit_id}/coordination-candidates')
def permit_coordination(request:Request,permit_id:str,snapshot_id:str,permit_release_id:str|None=None,
                        limit:Limit=30,cursor:str|None=None):
    from app.services.permit_intelligence import coordination
    strict(request,['snapshot_id','permit_release_id','limit','cursor'])
    selected=repo(request).get(snapshot_id,'permit',permit_id)
    records,projections,_=permit_context(request,snapshot_id,permit_release_id)
    return listing(request,coordination(selected,records,projections,snapshot_id,permit_release_id),snapshot_id,limit,cursor,
        permit_release_id=permit_release_id,actual_schedule='unknown',confirmed_conflicts_available=False)


@router.get('/permit-associations')
def permit_associations(request:Request,snapshot_id:str,release_id:str,road_id:str|None=None,
                        source_record_id:str|None=None,status:str|None=None,limit:Limit=100,cursor:str|None=None):
    strict(request,['snapshot_id','release_id','road_id','source_record_id','status','limit','cursor'])
    repo(request).snapshot(snapshot_id)
    if road_id:repo(request).get(snapshot_id,'road',road_id)
    if source_record_id:repo(request).get(snapshot_id,'permit',source_record_id)
    if status is not None and status not in {'accepted','candidate','rejected','unmatched'}:
        raise InvalidQuery('Unsupported association status')
    values=intelligence_repo(request).associations(snapshot_id,release_id,road_id,kind='permit')
    if source_record_id:values=[a for a in values if a['source_record_id']==source_record_id]
    if status:values=[a for a in values if a['status']==status]
    return listing(request,values,snapshot_id,limit,cursor)
