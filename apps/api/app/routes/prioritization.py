"""Explicit POST ranking; GET only retrieves immutable previously computed facts."""
from fastapi import APIRouter,Request,Response,HTTPException
from app.routes.municipal import strict,envelope,listing,Limit
from app.schemas.prioritization import PriorityRequest
from app.core.prioritization_repository import PrioritizationRepository
router=APIRouter(prefix='/api/v2/planning/prioritization-runs')

def repo(request):return PrioritizationRepository(request.app.state.settings.database_path)

@router.post('/preview')
def preview(request:Request,body:PriorityRequest):
    strict(request,[])
    try:return envelope(request,repo(request).preview(body),body.snapshot_id)
    except ValueError as exc:raise HTTPException(422,str(exc)) from None

@router.post('')
def save(request:Request,response:Response,body:PriorityRequest):
    strict(request,[])
    try:result,created=repo(request).save(body)
    except ValueError as exc:raise HTTPException(422,str(exc)) from None
    response.status_code=201 if created else 200
    return envelope(request,result,body.snapshot_id)

@router.get('')
def runs(request:Request,snapshot_id:str,limit:Limit=100,cursor:str|None=None):
    strict(request,['snapshot_id','limit','cursor'])
    return listing(request,repo(request).summaries(snapshot_id),snapshot_id,limit,cursor)

@router.get('/{identifier}')
def run(request:Request,identifier:str,snapshot_id:str):
    strict(request,['snapshot_id']);return envelope(request,repo(request).get(snapshot_id,identifier),snapshot_id)

@router.get('/{identifier}/roads')
def roads(request:Request,identifier:str,snapshot_id:str,q:str|None=None,status:str|None=None,limit:Limit=100,cursor:str|None=None):
    strict(request,['snapshot_id','q','status','limit','cursor'])
    if q is not None and (not q.strip() or len(q)>100):raise HTTPException(422,'Invalid search')
    if status is not None and status not in {'ranked','unranked'}:raise HTTPException(422,'Invalid ranking status')
    rows=repo(request).get(snapshot_id,identifier)['result']['base']['rows']
    rows=[r for r in rows if (not q or q.casefold() in (r['name']+' '+r['road_id']).casefold()) and (not status or r['status']==status)]
    # Existing municipal pagination uses resource id; preserve score/rank order.
    return listing(request,[r|{'id':r['road_id']} for r in rows],snapshot_id,limit,cursor)

@router.get('/{identifier}/compare')
def compare(request:Request,identifier:str,snapshot_id:str,road_ids:str):
    strict(request,['snapshot_id','road_ids']);ids=road_ids.split(',')
    if not 2<=len(ids)<=5 or len(ids)!=len(set(ids)):raise HTTPException(422,'Compare 2–5 distinct road IDs')
    result=repo(request).get(snapshot_id,identifier)['result'];by_id={r['road_id']:r for r in result['base']['rows']}
    if any(r not in by_id for r in ids):raise HTTPException(404,'Compared road not in saved universe')
    return envelope(request,{'rows':[by_id[r] for r in ids],'basis':'Same saved universe and policy; costs/scopes may differ, no equal-benefit or optimal-schedule claim','sensitivity':result['sensitivity']},snapshot_id)
