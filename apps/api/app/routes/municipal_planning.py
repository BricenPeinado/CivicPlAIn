"""V2 official-road planning; only explicit POST calculates or persists estimates."""
from fastapi import APIRouter,Request,HTTPException,Response
from app.routes.municipal import strict,envelope,listing,Limit
from app.schemas.municipal_planning import EstimateRequest
from app.core.municipal_planning_repository import MunicipalPlanningRepository
from app.services.municipal_estimates import METHODS,VERSION

router=APIRouter(prefix='/api/v2/planning')
def repository(request):return MunicipalPlanningRepository(request.app.state.settings.database_path)

@router.get('/capabilities')
def capabilities(request:Request,snapshot_id:str,road_id:str):
    strict(request,['snapshot_id','road_id'])
    request.app.state.municipal.get(snapshot_id,'road',road_id)
    persistence=True
    try:repository(request).ready()
    except HTTPException as exc:
        if exc.status_code!=503:raise
        persistence=False
    return envelope(request,{'snapshot_id':snapshot_id,'road_id':road_id,'contract_version':'municipal-estimate-v1',
        'method_version':VERSION,'treatments':METHODS,'persistence_available':persistence,
        'rate_catalog_available':False,'reason':'No reviewed NYC price/quantity catalog is activated. Enter explicit planning assumptions; missing inputs never use synthetic rates.',
        'utility_coverage':'unknown','reconstruction_available':False},snapshot_id)

@router.post('/estimates/preview')
def preview(request:Request,body:EstimateRequest):
    strict(request,[])
    try:values=repository(request).preview(body)
    except ValueError as exc:raise HTTPException(422,str(exc)) from None
    return envelope(request,values,body.snapshot_id)

@router.post('/estimates')
def save(request:Request,response:Response,body:EstimateRequest):
    strict(request,[])
    try:record,created=repository(request).save(body)
    except ValueError as exc:raise HTTPException(422,str(exc)) from None
    response.status_code=201 if created else 200
    return envelope(request,record,body.snapshot_id)

@router.get('/estimates')
def estimates(request:Request,snapshot_id:str,road_id:str|None=None,limit:Limit=100,cursor:str|None=None):
    strict(request,['snapshot_id','road_id','limit','cursor'])
    return listing(request,repository(request).summaries(snapshot_id,road_id),snapshot_id,limit,cursor)

@router.get('/estimates/{identifier}')
def estimate(request:Request,identifier:str,snapshot_id:str):
    strict(request,['snapshot_id'])
    return envelope(request,repository(request).get(snapshot_id,identifier),snapshot_id)
