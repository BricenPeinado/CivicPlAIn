"""Append-only v2 calculation snapshots. No synthetic catalogs or v1 writes."""
import json
from datetime import datetime,timezone
from fastapi import HTTPException
from app.models.database import connection
from app.models.migrations import inspect_version
from app.core.municipal_repository import MunicipalRepository
from app.schemas.municipal_planning import EstimateResult
from app.services.municipal_estimates import frozen_inputs,calculate
from app.services.municipal_data import canonical,digest

class MunicipalPlanningRepository:
    def __init__(self,path):self.path=path

    def ready(self):
        if not self.path.exists():raise HTTPException(503,'MIGRATION_REQUIRED: explicit schema 10 migration required')
        with connection(self.path) as conn:
            if inspect_version(conn)<10:raise HTTPException(503,'MIGRATION_REQUIRED: explicit schema 10 migration required')

    def preview(self,body):
        repository=MunicipalRepository(self.path);base=repository.snapshot(body.snapshot_id)
        road=repository.get(body.snapshot_id,'road',body.road_id)
        source=repository.source(body.snapshot_id,road['source_revision_id'])
        inputs=frozen_inputs(body,road,source,base)
        result=calculate(inputs);EstimateResult.model_validate(result)
        return {'input_snapshot':inputs,'input_hash':digest(inputs),'result':result,'result_hash':digest(result)}

    def save(self,body,inject_failure=False):
        self.ready();values=self.preview(body)
        if any(a['status']=='unavailable' for a in values['result']['alternatives']):
            raise HTTPException(422,'MISSING_PLANNING_INPUTS: every saved alternative requires complete declared scope and costs')
        identifier='estimate-'+values['input_hash']
        record={**values,'id':identifier,'created_at':datetime.now(timezone.utc).isoformat()}
        with connection(self.path) as conn:
            conn.execute('BEGIN IMMEDIATE')
            row=conn.execute('SELECT payload FROM municipal_estimates WHERE id=?',(identifier,)).fetchone()
            if row:
                saved=self.verify(json.loads(row[0]))
                if saved['result_hash']!=values['result_hash']:raise HTTPException(409,'Calculation identity collision')
                return saved,False
            conn.execute('INSERT INTO municipal_estimates VALUES(?,?,?,?,?,?,?,?)',
                (identifier,body.snapshot_id,'road',body.road_id,values['input_hash'],values['result_hash'],canonical(record),record['created_at']))
            if inject_failure:raise ValueError('Injected estimate publication failure')
        return record,True

    def verify(self,record):
        try:
            if digest(record['input_snapshot'])!=record['input_hash'] or record['id']!='estimate-'+record['input_hash'] or digest(record['result'])!=record['result_hash']:
                raise ValueError('Hash mismatch')
            from app.schemas.municipal_planning import EstimateRequest
            snap=record['input_snapshot'];body=EstimateRequest.model_validate(snap['request'])
            rebuilt=frozen_inputs(body,snap['road'],snap['road_source'],snap['base'])
            # Method descriptions are frozen source guidance, not a live catalog lookup.
            rebuilt['methods']=snap['methods']
            if rebuilt!=snap or calculate(snap)!=record['result']:raise ValueError('Replay mismatch')
            EstimateResult.model_validate(record['result'])
        except (ValueError,KeyError,TypeError):raise HTTPException(409,'Estimate integrity/replay check failed') from None
        return record

    def get(self,snapshot_id,identifier):
        self.ready();MunicipalRepository(self.path).snapshot(snapshot_id)
        with connection(self.path) as conn:
            row=conn.execute('SELECT payload FROM municipal_estimates WHERE id=? AND snapshot_id=?',(identifier,snapshot_id)).fetchone()
        if not row:raise HTTPException(404,'Estimate not in selected snapshot')
        return self.verify(json.loads(row[0]))

    def summaries(self,snapshot_id,road_id=None):
        self.ready();repository=MunicipalRepository(self.path);repository.snapshot(snapshot_id)
        if road_id:repository.get(snapshot_id,'road',road_id)
        with connection(self.path) as conn:
            rows=conn.execute('SELECT id,road_id,input_hash,result_hash,created_at FROM municipal_estimates WHERE snapshot_id=?'+(' AND road_id=?' if road_id else '')+' ORDER BY id',([snapshot_id,road_id] if road_id else [snapshot_id])).fetchall()
        return [dict(zip(['id','road_id','input_hash','result_hash','created_at'],r)) for r in rows]
