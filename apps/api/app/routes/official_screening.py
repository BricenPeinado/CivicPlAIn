"""V2 explicit screening and human notes. GET/navigation are write-free."""
from fastapi import APIRouter,Request,Response,HTTPException
from app.routes.municipal import strict,envelope,listing,Limit
from app.schemas.official_screening import ScreeningRequest,ReviewNote
from app.core.official_screening_repository import OfficialScreeningRepository
router=APIRouter(prefix='/api/v2/planning/conflict-analyses')
def repo(request):return OfficialScreeningRepository(request.app.state.settings.database_path)

@router.post('/preview')
def preview(request:Request,body:ScreeningRequest):
    strict(request,[])
    try:return envelope(request,repo(request).preview(body),body.snapshot_id)
    except ValueError as exc:raise HTTPException(422,str(exc)) from None

@router.post('')
def save(request:Request,response:Response,body:ScreeningRequest):
    strict(request,[])
    try:record,created=repo(request).save(body)
    except ValueError as exc:raise HTTPException(422,str(exc)) from None
    response.status_code=201 if created else 200
    return envelope(request,record,body.snapshot_id)

@router.get('')
def history(request:Request,snapshot_id:str,limit:Limit=100,cursor:str|None=None):
    strict(request,['snapshot_id','limit','cursor']);return listing(request,repo(request).summaries(snapshot_id),snapshot_id,limit,cursor)

@router.get('/{identifier}')
def get(request:Request,identifier:str,snapshot_id:str):
    strict(request,['snapshot_id']);return envelope(request,repo(request).get(snapshot_id,identifier),snapshot_id)

@router.get('/{identifier}/notes')
def notes(request:Request,identifier:str,snapshot_id:str):
    strict(request,['snapshot_id']);return envelope(request,repo(request).notes(snapshot_id,identifier),snapshot_id)

@router.post('/{identifier}/notes')
def note(request:Request,response:Response,identifier:str,snapshot_id:str,body:ReviewNote):
    strict(request,['snapshot_id']);value,created=repo(request).add_note(snapshot_id,identifier,body);response.status_code=201 if created else 200
    return envelope(request,value,snapshot_id)
