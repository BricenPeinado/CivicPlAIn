"""Read the supplied, already standardized artifact; never ingest or modify it."""
import json
import sqlite3
from contextlib import contextmanager, closing

from fastapi import HTTPException
from pydantic import ValidationError


class StandardizedRepository:
    def __init__(self, path):
        self.path = path

    @contextmanager
    def connection(self, snapshot):
        if not self.path.is_file():
            raise HTTPException(503, 'STANDARDIZED_DATABASE_MISSING: configure the supplied standardized database')
        try:
            with closing(sqlite3.connect(self.path.resolve().as_uri() + '?mode=ro', uri=True)) as conn:
                conn.row_factory = sqlite3.Row
                conn.execute('PRAGMA query_only=ON')
                # Validate the actual read contract, including views, before any lookup.
                for sql in [
                    'SELECT road_id,street_key,street_name,segment_id,object_id,geometry_json,street_observation_count,permits_on_street,latest_rating,latest_inspection_at,display_condition,display_basis FROM road_profiles LIMIT 0',
                    'SELECT road_id,observation_id,on_street,from_street,to_street,rating,display_condition,inspection_at,geometry_json,association_basis FROM road_pavement_by_name LIMIT 0',
                    'SELECT road_id,permit_id,permit_number,permit_type,permit_status,on_street,from_street,to_street,issue_date,valid_from,valid_to,association_basis FROM road_permits_by_name LIMIT 0',
                    'SELECT road_id,source_revision_id FROM roads LIMIT 0',
                    'SELECT observation_id,source_revision_id,source_row_key,non_rating_reason FROM pavement_observations LIMIT 0',
                    'SELECT permit_id,source_revision_id FROM permits LIMIT 0',
                ]:
                    conn.execute(sql)
                metadata = {r['key']: json.loads(r['value']) for r in conn.execute('SELECT key,value FROM metadata')}
                if metadata.get('dataset_kind') != 'derived_read_only_road_lookup' or not metadata.get('source_snapshot'):
                    raise ValueError('Unsupported metadata')
                if metadata['source_snapshot'] != snapshot:
                    raise HTTPException(409, 'STANDARDIZED_SNAPSHOT_MISMATCH: select the standardized source snapshot')
                yield conn
        except (sqlite3.Error, ValueError, TypeError, ValidationError) as exc:
            raise HTTPException(503, 'STANDARDIZED_DATABASE_INCOMPATIBLE: supplied database does not satisfy standardized-read-v1') from exc

    def profile(self, conn, road):
        row = conn.execute('SELECT p.*,r.source_revision_id FROM road_profiles p JOIN roads r USING(road_id) WHERE p.road_id=?', (road,)).fetchone()
        if row is None:
            raise HTTPException(404, 'Standardized road not found')
        result = dict(row)
        result['geometry'] = json.loads(result.pop('geometry_json'))
        return result

    def page(self, conn, road, kind, limit, offset):
        self.profile(conn, road)
        if kind == 'pavement':
            source = 'road_pavement_by_name v JOIN pavement_observations s USING(observation_id)'
            fields = 'v.*,s.source_revision_id,s.source_row_key,s.non_rating_reason'
            order = 'v.inspection_at DESC,v.observation_id'
        else:
            source = 'road_permits_by_name v JOIN permits s USING(permit_id)'
            fields = 'v.*,s.source_revision_id'
            order = 'v.issue_date DESC,v.permit_id'
        total = conn.execute(f'SELECT count(*) FROM {source} WHERE v.road_id=?', (road,)).fetchone()[0]
        rows = conn.execute(f'SELECT {fields} FROM {source} WHERE v.road_id=? ORDER BY {order} LIMIT ? OFFSET ?', (road, limit, offset))
        data = []
        for row in rows:
            value = dict(row)
            if 'geometry_json' in value:
                geometry = value.pop('geometry_json')
                value['geometry'] = json.loads(geometry) if geometry else None
            data.append(value)
        return data, total, offset + len(data) if offset + len(data) < total else None
