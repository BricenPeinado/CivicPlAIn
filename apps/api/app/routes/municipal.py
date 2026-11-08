"""M7 read boundary. Explicit snapshot context; no official mutation/calculation routes."""
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from shapely.geometry import box, shape

from app.core.municipal_repository import paginate
from app.core.repository import InvalidQuery
from app.routes.roads import parse_bbox

router=APIRouter(prefix='/api/v2')
Limit=Annotated[int,Query(ge=1,le=100)]


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
          condition:str|None=None,limit:Limit=100,cursor:str|None=None):
    strict(request,['snapshot_id','bbox','q','condition','limit','cursor'])
    if condition is not None and condition not in {'good','fair','poor','unknown'}:
        raise InvalidQuery('Invalid condition')
    bounds=parse_bbox(bbox)
    geo=request.url.path.endswith('/geojson')
    if geo and bounds is None:
        raise InvalidQuery('bbox is required for GeoJSON')
    records=filters(repo(request).records(snapshot_id,'road',bounds),q)
    if condition and condition!='unknown':
        records=[]
    if geo and len(records)>2000:
        raise HTTPException(422,'VIEWPORT_TOO_BROAD: refine viewport to at most 2000 features')
    records=repo(request).enrich(snapshot_id,records)
    result=listing(request,records,snapshot_id,limit,cursor)
    if geo:
        return as_geojson(result)
    return result


def as_geojson(result):
    features=[{'type':'Feature','id':r['id'],'geometry':r['geometry'],
        'properties':{k:r[k] for k in ['id','kind','source_revision_id','source_record_key','classification','values','field_classifications']}}
        for r in result['data']]
    return JSONResponse({'type':'FeatureCollection','features':features,'meta':result['meta']},media_type='application/geo+json')


@router.get('/road-segments/{road_id}/conditions')
def conditions(request:Request,road_id:str,snapshot_id:str,limit:Limit=100,cursor:str|None=None):
    strict(request,['snapshot_id','limit','cursor'])
    repo(request).get(snapshot_id,'road',road_id)
    matches=repo(request).matches(snapshot_id)
    records=[r for r in repo(request).records(snapshot_id,'condition') if matches[r['id']]['target_road_id']==road_id]
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
def all_conditions(request:Request,snapshot_id:str,bbox:str|None=None,limit:Limit=100,cursor:str|None=None):
    strict(request,['snapshot_id','bbox','limit','cursor'])
    return listing(request,repo(request).enrich(snapshot_id,repo(request).records(snapshot_id,'condition',parse_bbox(bbox))),snapshot_id,limit,cursor)


@router.get('/permits')
def permits(request:Request,snapshot_id:str,road_id:str|None=None,q:str|None=None,status:str|None=None,
            location:str='all',bbox:str|None=None,limit:Limit=100,cursor:str|None=None):
    strict(request,['snapshot_id','road_id','q','status','location','bbox','limit','cursor'])
    if location not in {'all','matched','ambiguous','unmatched','unlocated'}:
        raise InvalidQuery('Invalid location filter')
    if status is not None and (not status.strip() or len(status)>100):
        raise InvalidQuery('status must contain 1–100 characters')
    if road_id:
        repo(request).get(snapshot_id,'road',road_id)
    records=repo(request).enrich(snapshot_id,filters(repo(request).records(snapshot_id,'permit'),q))
    excluded=0
    bounds=parse_bbox(bbox)
    viewport=box(*bounds) if bounds else None
    linked_roads={r['id']:r for r in repo(request).records(snapshot_id,'road')} if bounds else {}
    result=[]
    for r in records:
        m=r['match']
        if road_id and m['target_road_id']!=road_id or status is not None and r['values']['permit_status']!=status:
            continue
        if location=='unlocated' and r['location_basis']!='unknown' or location not in {'all','unlocated'} and m['status']!=location:
            continue
        if bounds and r['location_basis']=='unknown':
            excluded+=1
        g=r['geometry'] or (linked_roads.get(m['target_road_id'],{}).get('geometry') if bounds else None)
        if viewport is not None and (g is None or not shape(g).intersects(viewport)):
            continue
        result.append(r)
    return listing(request,result,snapshot_id,limit,cursor,unlocated_excluded_count=excluded if bounds else 0)


@router.get('/permits/{permit_id}')
def permit(request:Request,permit_id:str,snapshot_id:str):
    strict(request,['snapshot_id'])
    return envelope(request,repo(request).enrich(snapshot_id,[repo(request).get(snapshot_id,'permit',permit_id)])[0],snapshot_id)


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
