"""Explicit snapshot collection and append-only priority run storage."""
import json
from datetime import datetime,timezone
from fastapi import HTTPException
from app.core.municipal_repository import MunicipalRepository
from app.core.intelligence_repository import IntelligenceRepository
from app.core.municipal_planning_repository import MunicipalPlanningRepository
from app.models.database import connection
from app.models.migrations import inspect_version
from app.schemas.prioritization import PriorityRequest
from app.services.municipal_data import digest,canonical
from app.services.road_conditions import summarize
from app.services.prioritization import VERSION,DEFINITIONS,calculate


def check_origin(record,source):
    if record['contains_synthetic'] or record['classification']=='synthetic_fixture' or 'synthetic_fixture' in record['field_classifications'].values() or source.get('query',{}).get('synthetic_fixture'):
        raise ValueError('Synthetic records cannot enter an official priority run')


def projection(snapshot):
    """Replay frozen inputs without consulting current SQL, wall clock or catalogs."""
    request=PriorityRequest.model_validate(snapshot['request']);base=snapshot['base'];sources=snapshot['sources']
    if base['id']!=request.snapshot_id or any(k not in base['source_revision_ids'] or v['id']!=k for k,v in sources.items()):raise ValueError('Inconsistent base/source context')
    rows=[]
    for item in snapshot['roads']:
        road=item['road'];check_origin(road,sources[road['source_revision_id']])
        for r in item['condition_records']:check_origin(r,sources[r['source_revision_id']])
        summary=summarize(item['condition_records'],item['condition_matches'],road['id'],request.snapshot_id,request.as_of_date.isoformat(),request.policy.max_condition_age_days,request.condition_release_id)
        if summary!=item['condition']:raise ValueError('Condition projection does not replay')
        if item['estimate']:
            saved=MunicipalPlanningRepository(None).verify(item['estimate']);choice=next(c for c in request.estimates if c.road_id==road['id'])
            if saved['id']!=choice.estimate_id or saved['result']['road_id']!=road['id'] or saved['result']['snapshot_id']!=request.snapshot_id or saved['input_snapshot']['road']!=road:raise ValueError('Foreign estimate context')
            alternative=next(a for a in saved['result']['alternatives'] if a['treatment']==choice.treatment)
            cost={'estimate_id':saved['id'],'treatment':alternative['treatment'],'base_total_usd':alternative['cases']['base']['total_usd'],
                'scope':alternative['scope'],'quantity_m2':alternative['quantity_m2'],'price_basis_date':alternative['price_basis_date'],
                'geography':alternative['geography'],'inclusions':alternative['inclusions'],'exclusions':alternative['exclusions'],
                'input_hash':saved['input_hash'],'result_hash':saved['result_hash'],'classification':'derived_calculation',
                'basis':'Explicit selected M8.3 declared-scope estimate; unverified planning assumptions, not whole-road cost or equal-benefit comparison'}
        else:cost=None
        if cost!=item['cost']:raise ValueError('Cost projection does not replay')
        # Accepted permit references alone cannot become a verified physical opportunity.
        coordination={'verified_opportunity':None,'status':'unknown','accepted_administrative_references':len(item['permit_associations']),
            'permit_release_id':request.permit_release_id,'reason':'Administrative road references do not establish actual work footprint, dates or coordination benefit'}
        if coordination!=item['coordination']:raise ValueError('Coordination projection does not replay')
        rows.append(item)
    return calculate(snapshot)


class PrioritizationRepository:
    def __init__(self,path):self.path=path

    def ready(self):
        if not self.path.exists():raise HTTPException(503,'MIGRATION_REQUIRED: explicit schema 11 migration required')
        with connection(self.path) as conn:
            if inspect_version(conn)<11:raise HTTPException(503,'MIGRATION_REQUIRED: explicit schema 11 migration required')

    def preview(self,body):
        repository=MunicipalRepository(self.path);base=repository.snapshot(body.snapshot_id);sid=body.snapshot_id
        sources={key:repository.source(sid,key) for key in base['source_revision_ids']}
        release=None;permit_release=None;groups={};permit_groups={}
        intelligence=IntelligenceRepository(self.path)
        if body.condition_release_id:
            release=intelligence.get(sid,body.condition_release_id)
            if release['contract_version']!='road-intelligence-v1':raise HTTPException(404,'Wrong condition release kind')
            for a in intelligence.associations(sid,body.condition_release_id,status='accepted'):
                if a['target_road_id'] in body.road_ids:
                    groups.setdefault(a['target_road_id'],{})[a['source_record_id']]={'id':a['id'],'source_kind':'condition','status':'matched','target_road_id':a['target_road_id'],
                        'method':'reviewed-candidates-v2','decision':a['decision'],'candidate_hash':a['candidate_hash'],'parameter_hash':a['parameter_hash'],'release_id':body.condition_release_id}
        else:
            for key,m in repository.matches(sid).items():
                if m['source_kind']=='condition' and m['status']=='matched' and m['target_road_id'] in body.road_ids:groups.setdefault(m['target_road_id'],{})[key]=m
        if body.permit_release_id:
            permit_release=intelligence.get(sid,body.permit_release_id)
            if permit_release['contract_version']!='permit-intelligence-v1':raise HTTPException(404,'Wrong permit release kind')
            for a in intelligence.associations(sid,body.permit_release_id,status='accepted',kind='permit'):
                if a['target_road_id'] in body.road_ids:permit_groups.setdefault(a['target_road_id'],[]).append(a)
        rows=[]
        for rid in sorted(body.road_ids):
            road=repository.get(sid,'road',rid);matches=groups.get(rid,{})
            records=[repository.get(sid,'condition',key) for key in sorted(matches)]
            summary=summarize(records,matches,rid,sid,body.as_of_date.isoformat(),body.policy.max_condition_age_days,body.condition_release_id)
            estimate_choice=next((c for c in body.estimates if c.road_id==rid),None)
            saved=MunicipalPlanningRepository(self.path).get(sid,estimate_choice.estimate_id) if estimate_choice else None
            if saved and saved['result']['road_id']!=rid:raise HTTPException(404,'Estimate does not belong to selected road')
            if saved and not any(a['treatment']==estimate_choice.treatment for a in saved['result']['alternatives']):raise ValueError('Selected treatment absent from estimate')
            links=permit_groups.get(rid,[])
            permits=[repository.get(sid,'permit',key) for key in sorted({a['source_record_id'] for a in links})]
            cost=None
            if saved:
                a=next(a for a in saved['result']['alternatives'] if a['treatment']==estimate_choice.treatment)
                cost={'estimate_id':saved['id'],'treatment':a['treatment'],'base_total_usd':a['cases']['base']['total_usd'],
                    'scope':a['scope'],'quantity_m2':a['quantity_m2'],'price_basis_date':a['price_basis_date'],'geography':a['geography'],
                    'inclusions':a['inclusions'],'exclusions':a['exclusions'],'input_hash':saved['input_hash'],'result_hash':saved['result_hash'],
                    'classification':'derived_calculation','basis':'Explicit selected M8.3 declared-scope estimate; unverified planning assumptions, not whole-road cost or equal-benefit comparison'}
            rows.append({'road':road,'condition_records':records,'condition_matches':matches,'condition':summary,'estimate':saved,'cost':cost,
                'permit_associations':links,'permit_records':permits,
                'coordination':{'verified_opportunity':None,'status':'unknown','accepted_administrative_references':len(links),'permit_release_id':body.permit_release_id,
                    'reason':'Administrative road references do not establish actual work footprint, dates or coordination benefit'}})
        with connection(self.path) as conn:count=conn.execute("SELECT count(*) FROM import_records WHERE snapshot_id=? AND kind='road'",(sid,)).fetchone()[0]
        request=body.model_dump(mode='json');request['road_ids']=sorted(body.road_ids);request['estimates']=sorted(request['estimates'],key=lambda c:c['road_id'])
        snapshot={'method_version':VERSION,'definitions':DEFINITIONS,'request':request,'base':base,'sources':sources,
            'condition_release':release,'permit_release':permit_release,'snapshot_road_count':count,'roads':rows}
        result=projection(snapshot)
        return {'input_snapshot':snapshot,'input_hash':digest(snapshot),'result':result,'result_hash':digest(result)}

    def save(self,body,inject_failure=False):
        self.ready();values=self.preview(body);identifier='priority-'+values['input_hash'];record=values|{'id':identifier,'created_at':datetime.now(timezone.utc).isoformat()}
        with connection(self.path) as conn:
            conn.execute('BEGIN IMMEDIATE');existing=conn.execute('SELECT payload FROM prioritization_runs WHERE id=?',(identifier,)).fetchone()
            if existing:return self.verify(json.loads(existing[0])),False
            conn.execute('INSERT INTO prioritization_runs VALUES(?,?,?,?,?,?)',(identifier,body.snapshot_id,values['input_hash'],values['result_hash'],canonical(record),record['created_at']))
            if inject_failure:raise ValueError('Injected priority save failure')
        return record,True

    def verify(self,record):
        try:
            if record['id']!='priority-'+record['input_hash'] or digest(record['input_snapshot'])!=record['input_hash'] or digest(record['result'])!=record['result_hash'] or projection(record['input_snapshot'])!=record['result']:raise ValueError('Replay mismatch')
        except (ValueError,KeyError,TypeError,StopIteration,HTTPException):raise HTTPException(409,'Priority integrity/replay check failed') from None
        return record

    def get(self,sid,identifier):
        self.ready();MunicipalRepository(self.path).snapshot(sid)
        with connection(self.path) as conn:row=conn.execute('SELECT payload FROM prioritization_runs WHERE id=? AND snapshot_id=?',(identifier,sid)).fetchone()
        if not row:raise HTTPException(404,'Priority run not in selected snapshot')
        return self.verify(json.loads(row[0]))

    def summaries(self,sid):
        self.ready();MunicipalRepository(self.path).snapshot(sid)
        with connection(self.path) as conn:return [dict(zip(['id','input_hash','result_hash','created_at'],r)) for r in conn.execute('SELECT id,input_hash,result_hash,created_at FROM prioritization_runs WHERE snapshot_id=? ORDER BY id',(sid,))]
