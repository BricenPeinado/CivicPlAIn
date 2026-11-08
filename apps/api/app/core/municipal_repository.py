"""Read-only, snapshot-isolated access to immutable official data."""
import base64
import binascii
import json
import sqlite3

from fastapi import HTTPException
from shapely.geometry import box, shape

from app.core.repository import InvalidQuery
from app.models.database import connection
from app.schemas.municipal import MunicipalRecord
from app.services.municipal_data import canonical, digest


class MunicipalRepository:
    def __init__(self,path):
        self.path=path

    def ready(self):
        if not self.path.exists():
            raise HTTPException(503,'MIGRATION_REQUIRED: run explicit schema 7 migration')
        with connection(self.path) as conn:
            try:
                current=conn.execute('SELECT name FROM schema_migrations WHERE version=7').fetchone()
            except sqlite3.OperationalError:
                current=None
            if current!=('m7-official-snapshots-v1',):
                raise HTTPException(503,'MIGRATION_REQUIRED: run explicit schema 7 migration')

    def snapshots(self):
        self.ready()
        with connection(self.path) as conn:
            return [json.loads(r[0])|{'id':r[1],'published_at':r[2]} for r in conn.execute(
                'SELECT manifest_json,id,published_at FROM data_snapshots ORDER BY published_at DESC,id')]

    def snapshot(self,sid):
        self.ready()
        with connection(self.path) as conn:
            row=conn.execute('SELECT manifest_json,published_at FROM data_snapshots WHERE id=?',(sid,)).fetchone()
        if row is None:
            raise HTTPException(404,'Published snapshot not found')
        return json.loads(row[0])|{'id':sid,'published_at':row[1]}

    def source(self,sid,source_id):
        self.snapshot(sid)
        with connection(self.path) as conn:
            row=conn.execute('SELECT r.payload FROM source_revisions r JOIN snapshot_sources s ON r.id=s.source_revision_id WHERE s.snapshot_id=? AND r.id=?',(sid,source_id)).fetchone()
        if row is None:
            raise HTTPException(404,'Source revision not in snapshot')
        return json.loads(row[0])

    def matches(self,sid):
        with connection(self.path) as conn:
            return {r[0]:json.loads(r[1]) for r in conn.execute('SELECT source_record_id,payload FROM geographic_matches WHERE snapshot_id=?',(sid,))}

    def records(self,sid,kind,bounds=None):
        self.snapshot(sid)
        query='SELECT payload FROM import_records WHERE snapshot_id=? AND kind=?'
        params=[sid,kind]
        if bounds is not None:
            query+=' AND west<=? AND east>=? AND south<=? AND north>=?'
            params.extend([bounds[2],bounds[0],bounds[3],bounds[1]])
        with connection(self.path) as conn:
            values=[MunicipalRecord.model_validate_json(r[0]).model_dump(mode='json') for r in conn.execute(query+' ORDER BY id',params)]
        if bounds is not None:
            viewport=box(*bounds)
            values=[r for r in values if shape(r['geometry']).intersects(viewport)]
        return values

    def get(self,sid,kind,identifier):
        self.snapshot(sid)
        with connection(self.path) as conn:
            row=conn.execute('SELECT payload FROM import_records WHERE snapshot_id=? AND kind=? AND id=?',(sid,kind,identifier)).fetchone()
        if row is None:
            raise HTTPException(404,'Record not in selected snapshot')
        return MunicipalRecord.model_validate_json(row[0]).model_dump(mode='json')

    def enrich(self,sid,records):
        matches=self.matches(sid)
        manifest=self.snapshot(sid)
        groups=manifest['oft_location_groups']
        for r in records:
            match=matches.get(r['id'])
            r['match']=match
            r['location_basis']='source_geometry' if r['geometry'] else 'matched_road_reference' if match and match['target_road_id'] else 'unknown'
            r['scope_membership']='confirmed_geometry' if r['geometry'] else 'accepted_road_link' if match and match['target_road_id'] else 'unverified_candidate'
            oft=r['raw_identifiers'].get('oftcode')
            r['same_oft_records']=[v for v in groups.get(oft,[]) if v['id']!=r['id']]
            if r['kind']=='road':
                r['condition_summary']={'category':'unknown','rating':None,'inspection_at':None,
                    'reason':'No confirmed category mapping; inspect accepted condition history and original decimal ratings'}
        return records

    def dashboard(self,sid):
        manifest=self.snapshot(sid)
        records={k:self.records(sid,k) for k in ['road','condition','permit']}
        matches=self.matches(sid)
        def counts(kind):
            return {s:sum(matches[r['id']]['status']==s for r in records[kind]) for s in ['matched','ambiguous','unmatched']}
        permit_counts=counts('permit')
        unlocated=sum(r['geometry'] is None and not matches[r['id']]['target_road_id'] for r in records['permit'])
        dated=sum(r['values']['inspection_at'] is not None for r in records['condition'])
        totals={'roads':len(records['road']), 'condition':{'good':0,'fair':0,'poor':0,'unknown':len(records['road'])},
            'assessments':{'total':len(records['condition']),'dated':dated,'undated':len(records['condition'])-dated,
                **{('accepted' if k=='matched' else k):v for k,v in counts('condition').items()}},
            'permits':{'total':len(records['permit']),'confirmed_in_scope':len(records['permit'])-unlocated,
                'scope_candidates':unlocated,'unlocated':unlocated,**permit_counts}}
        revisions=[self.source(sid,s) for s in manifest['source_revision_ids']]
        dates=[r['values']['inspection_at'] for r in records['condition'] if r['values']['inspection_at']]
        usable={r['id'] for r in records['condition'] if r['values']['inspection_at'] and r['values']['rating'] is not None}
        return {'snapshot_id':sid,'coverage':manifest['coverage'],'source_status':manifest['coverage']['source_status'],
            'counts':totals,'capabilities':manifest['capabilities'],
            'observation_date_range':[min(dates),max(dates)] if dates else None,
            'latest_retrieved_at':max(r['retrieved_at'] for r in revisions),
            'method_version':'municipal-summary-1',
            'classification':'derived_calculation','source_revision_ids':manifest['source_revision_ids'],
            'dated_road_coverage':{'value':len({m['target_road_id'] for m in matches.values() if m['source_kind']=='condition' and m['status']=='matched' and m['source_record_id'] in usable}),
                'denominator':len(records['road']),'classification':'derived_calculation'},
            'limitations':manifest['warnings']}


def paginate(values,limit,cursor,binding,key=lambda r:r['id']):
    token=digest(binding)
    start=0
    if cursor:
        try:
            decoded=json.loads(base64.b64decode(cursor,altchars=b'-_',validate=True))
            if decoded['binding']!=token:
                raise ValueError
            indices=[i for i,r in enumerate(values) if key(r)==decoded['last']]
            if len(indices)!=1:
                raise ValueError
            start=indices[0]+1
        except (ValueError,KeyError,TypeError,UnicodeError,binascii.Error):
            raise InvalidQuery('Cursor does not match snapshot, endpoint or filters') from None
    page=values[start:start+limit]
    next_cursor=base64.urlsafe_b64encode(canonical({'binding':token,'last':key(page[-1])}).encode()).decode() if page and start+limit<len(values) else None
    return page,next_cursor
