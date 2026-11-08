"""Pinned official adapter and immutable screening/review storage; no project writes."""
import json
from datetime import datetime,timezone
from fastapi import HTTPException
from shapely.geometry import box,shape
from app.models.database import connection
from app.models.migrations import inspect_version
from app.core.municipal_repository import MunicipalRepository
from app.core.intelligence_repository import IntelligenceRepository
from app.core.municipal_planning_repository import MunicipalPlanningRepository
from app.core.prioritization_repository import check_origin
from app.schemas.official_screening import ScreeningRequest
from app.services.permit_intelligence import locations,PARAMETERS
from app.services.official_screening import calculate,VERSION,LIBRARIES
from app.services.municipal_data import canonical,digest


def projection(snapshot):
    body=ScreeningRequest.model_validate(snapshot['request']);sid=body.snapshot_id
    if snapshot['base']['id']!=sid or snapshot['permit_parameters']!=PARAMETERS:raise ValueError('Snapshot/permit method differs')
    sources=snapshot['sources'];roads=snapshot['roads'];base=snapshot['base']
    if set(sources)!=set(base['source_revision_ids']) or any(k!=s['id'] for k,s in sources.items()):raise ValueError('Source membership mismatch')
    if len({r['id'] for r in roads})!=len(roads):raise ValueError('Duplicate frozen roads')
    for r in roads:
        check_origin(r,sources[r['source_revision_id']])
        if r['kind']!='road':raise ValueError('Foreign road context')
    by_road={r['id']:r for r in roads}
    for work in body.works:
        if not set(work.road_ids)<=by_road.keys():raise ValueError('Unknown road reference')
        if work.location and not box(*base['coverage']['bbox']).covers(shape(work.location.geometry.model_dump())):raise ValueError('Work geometry outside verified snapshot coverage')
    ids=sorted(set(body.permit_ids)|{p for w in body.works for p in w.permit_ids})
    records=[p['record'] for p in snapshot['permits']]
    if sorted(r['id'] for r in records)!=ids:raise ValueError('Permit universe mismatch')
    for r in records:
        check_origin(r,sources[r['source_revision_id']])
        if r['kind']!='permit':raise ValueError('Foreign permit')
    release=snapshot['permit_release']
    if body.permit_release_id:
        if not release or release['id']!=body.permit_release_id or release['base_snapshot_id']!=sid or release['contract_version']!='permit-intelligence-v1':raise ValueError('Wrong release context')
    elif release is not None or snapshot['permit_associations']:raise ValueError('Unexpected release evidence')
    projected=locations(sid,base,roads,records,sources,snapshot['permit_associations'],body.permit_release_id) if records else {}
    if any(p['location']!=projected[p['record']['id']] for p in snapshot['permits']):raise ValueError('Permit reference projection differs')
    if body.cost_comparison:
        c=body.cost_comparison;saved=MunicipalPlanningRepository(None).verify(snapshot['estimate'])
        if saved['id']!=c.estimate_id or saved['result']['snapshot_id']!=sid or saved['result']['road_id'] not in next(w for w in body.works if w.id==c.work_id).road_ids or saved['input_snapshot']['road']!=by_road[saved['result']['road_id']]:raise ValueError('Foreign cost scope')
        alt=next((a for a in saved['result']['alternatives'] if a['treatment']==c.treatment),None)
        if alt is None:raise ValueError('Selected treatment absent from estimate')
        if alt['status']!='available':raise ValueError('Unavailable selected estimate')
        work=next(w for w in body.works if w.id==c.work_id)
        if (work.work_type=='resurfacing')!=(c.treatment=='resurface'):raise ValueError('Work/estimate treatment scope differs')
    elif snapshot['estimate'] is not None:raise ValueError('Unexpected estimate')
    return calculate(snapshot)


class OfficialScreeningRepository:
    def __init__(self,path):self.path=path
    def ready(self):
        if not self.path.exists():raise HTTPException(503,'MIGRATION_REQUIRED: explicit schema 12 migration required')
        with connection(self.path) as conn:
            if inspect_version(conn)<12:raise HTTPException(503,'MIGRATION_REQUIRED: explicit schema 12 migration required')

    def preview(self,body):
        repo=MunicipalRepository(self.path);sid=body.snapshot_id;base=repo.snapshot(sid)
        sources={key:repo.source(sid,key) for key in base['source_revision_ids']}
        roads=repo.records(sid,'road')
        if any(rid not in {r['id'] for r in roads} for w in body.works for rid in w.road_ids):raise HTTPException(404,'Work road not in selected snapshot')
        ids=sorted(set(body.permit_ids)|{p for w in body.works for p in w.permit_ids})
        records=[repo.get(sid,'permit',key) for key in ids];associations=[];release=None
        if body.permit_release_id:
            intelligence=IntelligenceRepository(self.path);release=intelligence.get(sid,body.permit_release_id)
            if release['contract_version']!='permit-intelligence-v1':raise HTTPException(404,'Wrong permit release kind')
            associations=[a for status in ['accepted','rejected'] for a in intelligence.associations(sid,body.permit_release_id,status=status,kind='permit') if a['source_record_id'] in ids]
        located=locations(sid,base,roads,records,sources,associations,body.permit_release_id) if records else {}
        estimate=MunicipalPlanningRepository(self.path).get(sid,body.cost_comparison.estimate_id) if body.cost_comparison else None
        request=body.model_dump(mode='json');request['works']=sorted(request['works'],key=lambda w:w['id']);request['permit_ids']=sorted(request['permit_ids'])
        for w in request['works']:
            w['road_ids']=sorted(w['road_ids']);w['permit_ids']=sorted(w['permit_ids'])
        request['alternatives']=sorted(request['alternatives'],key=lambda a:a['id'])
        for a in request['alternatives']:a['overrides']=sorted(a['overrides'],key=lambda o:o['work_id'])
        snapshot={'method_version':VERSION,'libraries':LIBRARIES,'request':request,'base':base,'sources':sources,'roads':roads,
            'permits':[{'record':r,'location':located[r['id']]} for r in records],'permit_parameters':PARAMETERS,'permit_release':release,
            'permit_associations':sorted(associations,key=lambda a:a['id']),'estimate':estimate}
        result=projection(snapshot)
        return {'input_snapshot':snapshot,'input_hash':digest(snapshot),'result':result,'result_hash':digest(result)}

    def save(self,body,inject_failure=False):
        self.ready();values=self.preview(body);record=values|{'id':'screen-'+values['input_hash'],'created_at':datetime.now(timezone.utc).isoformat()}
        with connection(self.path) as conn:
            conn.execute('BEGIN IMMEDIATE');existing=conn.execute('SELECT payload FROM official_screenings WHERE id=?',(record['id'],)).fetchone()
            if existing:return self.verify(json.loads(existing[0])),False
            conn.execute('INSERT INTO official_screenings VALUES(?,?,?,?,?,?)',(record['id'],body.snapshot_id,values['input_hash'],values['result_hash'],canonical(record),record['created_at']))
            if inject_failure:raise ValueError('Injected screening save failure')
        return record,True

    def verify(self,record):
        try:
            if record['id']!='screen-'+record['input_hash'] or digest(record['input_snapshot'])!=record['input_hash'] or digest(record['result'])!=record['result_hash'] or projection(record['input_snapshot'])!=record['result']:raise ValueError('Replay mismatch')
        except (ValueError,KeyError,TypeError,StopIteration,HTTPException):raise HTTPException(409,'Screening integrity/replay check failed') from None
        return record

    def get(self,sid,identifier):
        self.ready();MunicipalRepository(self.path).snapshot(sid)
        with connection(self.path) as conn:row=conn.execute('SELECT payload FROM official_screenings WHERE snapshot_id=? AND id=?',(sid,identifier)).fetchone()
        if not row:raise HTTPException(404,'Screening not in selected snapshot')
        return self.verify(json.loads(row[0]))

    def summaries(self,sid):
        self.ready();MunicipalRepository(self.path).snapshot(sid)
        with connection(self.path) as conn:return [dict(zip(['id','input_hash','result_hash','created_at'],r)) for r in conn.execute('SELECT id,input_hash,result_hash,created_at FROM official_screenings WHERE snapshot_id=? ORDER BY id',(sid,))]

    def notes(self,sid,identifier):
        self.get(sid,identifier)
        with connection(self.path) as conn:return [json.loads(r[0]) for r in conn.execute('SELECT payload FROM official_screening_notes WHERE screening_id=? ORDER BY id',(identifier,))]

    def add_note(self,sid,identifier,body):
        record=self.get(sid,identifier)
        ids={f['id'] for f in record['result']['base']['findings']}|{f['id'] for a in record['result']['alternatives'] for f in a['screen']['findings']}
        if body.finding_id and body.finding_id not in ids:raise HTTPException(404,'Finding not in saved screening')
        values={'screening_id':identifier,'snapshot_id':sid,**body.model_dump(mode='json')};key='review-'+digest(values)
        note=values|{'id':key,'created_at':datetime.now(timezone.utc).isoformat(),'meaning':'Human planning note only; not work approval or excavation clearance'}
        with connection(self.path) as conn:
            conn.execute('BEGIN IMMEDIATE');prior=conn.execute('SELECT payload FROM official_screening_notes WHERE id=?',(key,)).fetchone()
            if prior:return json.loads(prior[0]),False
            conn.execute('INSERT INTO official_screening_notes VALUES(?,?,?)',(key,identifier,canonical(note)))
        return note,True
