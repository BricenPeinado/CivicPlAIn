"""Explicit immutable overlay publication and snapshot-bound reads."""
import json
from datetime import datetime, timezone
from fastapi import HTTPException
from app.models.database import connection
from app.models.migrations import check, inspect_version
from app.services.municipal_data import canonical, digest


class IntelligenceRepository:
    def __init__(self, path):
        self.path = path

    def ready(self, minimum=8):
        if not self.path.exists():
            raise HTTPException(503, f'MIGRATION_REQUIRED: explicit schema {minimum} migration required')
        with connection(self.path) as conn:
            if inspect_version(conn) < minimum:
                raise HTTPException(503, f'MIGRATION_REQUIRED: explicit schema {minimum} migration required')

    def releases(self, snapshot_id, kind="condition"):
        self.ready()
        with connection(self.path) as conn:
            return [json.loads(r[0]) | {'id': r[1], 'published_at': r[2]} for r in conn.execute(
                'SELECT manifest_json,id,published_at FROM intelligence_releases WHERE base_snapshot_id=? ORDER BY id', (snapshot_id,)) if json.loads(r[0])['contract_version'] == ('permit-intelligence-v1' if kind=='permit' else 'road-intelligence-v1')]

    def get(self, snapshot_id, release_id):
        self.ready()
        with connection(self.path) as conn:
            row = conn.execute('SELECT manifest_json,published_at FROM intelligence_releases WHERE base_snapshot_id=? AND id=?', (snapshot_id, release_id)).fetchone()
        if row is None:
            raise HTTPException(404, 'Intelligence release not in snapshot')
        return json.loads(row[0]) | {'id': release_id, 'published_at': row[1]}

    def associations(self, snapshot_id, release_id, road_id=None, status=None, kind="condition"):
        manifest=self.get(snapshot_id, release_id)
        if manifest["contract_version"] != ("permit-intelligence-v1" if kind=="permit" else "road-intelligence-v1"):
            raise HTTPException(404, "Release kind differs from requested evidence")
        table="permit_associations" if kind=="permit" else "road_associations"
        self.ready(9 if kind=="permit" else 8)
        with connection(self.path) as conn:
            query = f'SELECT payload FROM {table} WHERE base_snapshot_id=? AND release_id=?'
            args = [snapshot_id, release_id]
            if road_id is not None:
                query += ' AND target_road_id=?'; args.append(road_id)
            if status is not None:
                query += ' AND status=?'; args.append(status)
            return [json.loads(r[0]) for r in conn.execute(query + ' ORDER BY id', args)]

    def publish(self, staged, approval, inject_failure=False):
        self.ready()
        report = staged['report']; manifest = staged['manifest']; rows = staged['associations']
        permit = manifest.get('contract_version') == 'permit-intelligence-v1'
        if permit: self.ready(9)
        table = 'permit_associations' if permit else 'road_associations'
        if (approval != report['report_hash'] or approval != digest({k:v for k,v in report.items() if k != 'report_hash'})
                or report['manifest_hash'] != digest(manifest) or report['release_id'] != 'intel-' + digest(manifest)[:32]
                or manifest['content_hash'] != digest(rows) or manifest['contains_synthetic']):
            raise ValueError('Unapproved, tampered or synthetic intelligence release')
        # Rebuild from immutable base and reviews; hashes alone cannot authorize fabricated links.
        from app.core.municipal_repository import MunicipalRepository
        from app.services.road_intelligence import stage_overlay
        if permit:
            from app.services.permit_intelligence import stage_overlay
        rebuilt = stage_overlay(MunicipalRepository(self.path), report['base_snapshot_id'], [r['decision'] for r in rows if r['decision']])
        if rebuilt != staged:
            raise ValueError('Intelligence inputs do not reproduce reviewed report')
        with connection(self.path) as conn:
            conn.execute('BEGIN IMMEDIATE')
            existing = conn.execute('SELECT manifest_hash FROM intelligence_releases WHERE id=?', (report['release_id'],)).fetchone()
            if existing:
                if existing[0] != report['manifest_hash']:
                    raise ValueError('Intelligence release collision')
                return {'status': 'unchanged', 'release_id': report['release_id']}
            conn.execute('INSERT INTO intelligence_releases VALUES(?,?,?,?,?)', (report['release_id'], report['base_snapshot_id'], report['manifest_hash'], canonical(manifest), datetime.now(timezone.utc).isoformat()))
            for row in rows:
                conn.execute(f'INSERT INTO {table} VALUES(?,?,?,?,?,?,?,?,?)', (report['release_id'], row['id'], row['base_snapshot_id'], row['source_kind'], row['source_record_id'], 'road', row['target_road_id'], row['status'], canonical(row)))
            if inject_failure:
                raise ValueError('Injected publication failure')
            check(conn)
        return {'status': 'published', 'release_id': report['release_id']}
