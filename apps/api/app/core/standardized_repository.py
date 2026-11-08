"""Read the supplied, already standardized artifact; never ingest or modify it."""
import json
import sqlite3
from contextlib import contextmanager, closing
from threading import RLock
import math
from shapely.geometry import shape, box
from shapely.strtree import STRtree
from shapely.errors import ShapelyError

from fastapi import HTTPException
from pydantic import ValidationError


class StandardizedRepository:
    def __init__(self, path):
        self.path = path
        self._map_lock = RLock()
        self._map_index = None

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
        except (sqlite3.Error, ValueError, TypeError, KeyError, ShapelyError, ValidationError) as exc:
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

    def map_ratings(self, snapshot, bounds, limit):
        """One immutable spatial index, invalidated on artifact replacement; no DB writes."""
        with self._map_lock, self.connection(snapshot) as conn:
            stat = self.path.stat()
            identity = (str(self.path.resolve()), stat.st_ino, stat.st_size, stat.st_mtime_ns, snapshot)
            if self._map_index is None or self._map_index[0] != identity:
                rows = conn.execute('SELECT p.*,r.source_revision_id FROM road_profiles p JOIN roads r USING(road_id) ORDER BY p.road_id LIMIT 100001').fetchall()
                if len(rows) > 100000:
                    raise ValueError('Map index capacity exceeded')
                profiles, geometries = [], []
                for row in rows:
                    value = dict(row)
                    value['geometry'] = json.loads(value.pop('geometry_json'))
                    if not isinstance(value['geometry'], dict) or value['geometry'].get('type') not in {'LineString', 'MultiLineString'}:
                        raise ValueError('Invalid map geometry type')
                    geometry = shape(value['geometry'])
                    if geometry.geom_type not in {'LineString', 'MultiLineString'} or geometry.is_empty or not geometry.is_valid or not all(math.isfinite(v) for v in geometry.bounds):
                        raise ValueError('Invalid map geometry')
                    w, s, e, n = geometry.bounds
                    if not (-180 <= w <= e <= 180 and -90 <= s <= n <= 90):
                        raise ValueError('Invalid map coordinates')
                    profiles.append(value)
                    geometries.append(geometry)
                self._map_index = (identity, profiles, STRtree(geometries))
            _, profiles, tree = self._map_index
            indices = tree.query(box(*bounds), predicate='intersects')
            if len(indices) > limit:
                raise HTTPException(422, 'VIEWPORT_TOO_BROAD: zoom in; no partial rating results returned')
            return sorted((profiles[int(i)] for i in indices), key=lambda p: p['road_id'])
