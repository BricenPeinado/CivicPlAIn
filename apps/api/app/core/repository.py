"""Small explicit SQLite repository; no data literals in HTTP routes."""
import base64
import binascii
import json
from pathlib import Path

from shapely.geometry import box, shape

from app.models.database import connection
from app.schemas.roads import Evidence, Road, ConditionSummary
from app.core.planning_repository import PlanningRepository


class InvalidQuery(ValueError):
    pass


def decode_cursor(value: str | None, snapshot: str | None, bbox):
    if value is None:
        return ""
    try:
        payload = json.loads(base64.b64decode(value, altchars=b"-_", validate=True))
        if (set(payload) != {"after", "snapshot", "bbox"} or
                not isinstance(payload["after"], str) or not payload["after"] or
                payload["snapshot"] != snapshot or payload["bbox"] != bbox):
            raise ValueError
        return payload["after"]
    except (ValueError, TypeError, KeyError, binascii.Error):
        raise InvalidQuery("invalid cursor for this snapshot/filter") from None


class RoadRepository:
    def __init__(self, path: Path):
        self.path = path

    def snapshot(self):
        with connection(self.path) as conn:
            row = conn.execute("SELECT id FROM dataset ORDER BY id LIMIT 1").fetchone()
        return row[0] if row else None

    def count(self):
        with connection(self.path) as conn:
            return conn.execute("SELECT COUNT(*) FROM roads").fetchone()[0]

    def get(self, road_id: str):
        with connection(self.path) as conn:
            row = conn.execute("SELECT payload FROM roads WHERE id = ?", (road_id,)).fetchone()
        return self.enrich(Road.model_validate_json(row[0])) if row else None

    def evidence(self, evidence_id: str):
        with connection(self.path) as conn:
            row = conn.execute("SELECT payload FROM evidence WHERE id = ?", (evidence_id,)).fetchone()
        return Evidence.model_validate_json(row[0]) if row else None

    def enrich(self, road):
        planning = PlanningRepository(self.path)
        asset = planning.asset(road.id)
        latest = planning.latest(road.id)
        raw = road.model_dump(mode='json')
        refs = set(road.evidence_ids)
        if asset:
            refs.update(asset.evidence_ids)
            for field in ('length_m', 'width_m', 'surface_material', 'functional_class', 'notes'):
                value = getattr(asset, field)
                raw[field] = str(value) if field in ('length_m', 'width_m') and value is not None else value
                if value is not None and value != 'unknown':
                    raw['field_evidence'][field] = asset.evidence_ids
                    raw['unknown_reasons'].pop(field, None)
                else:
                    raw['unknown_reasons'][field] = 'not_supplied'
            raw['dimension_basis'] = {f: asset.dimension_basis for f in ('length_m', 'width_m') if getattr(asset, f) is not None}
            raw['repairable_area_m2'] = str(asset.length_m * asset.width_m) if asset.length_m and asset.width_m else None
            if raw['repairable_area_m2'] is not None:
                raw['field_evidence']['repairable_area_m2'] = asset.evidence_ids
            else:
                raw['unknown_reasons']['repairable_area_m2'] = 'missing_length_or_width'
        if latest:
            refs.update(latest.evidence_ids)
            raw['condition_summary'] = ConditionSummary.model_validate(latest.model_dump(include=set(ConditionSummary.model_fields))).model_dump(mode='json')
            for field in ('rating', 'category', 'rating_scale', 'assessed_on'):
                key = f'condition_summary.{field}'
                if getattr(latest, field) is not None:
                    raw['field_evidence'][key] = latest.evidence_ids
                    raw['unknown_reasons'].pop(key, None)
        raw['evidence_ids'] = sorted(refs)
        return Road.model_validate(raw)

    def list(self, limit: int, cursor: str | None, bbox: list[float] | None):
        snapshot = self.snapshot()
        after = decode_cursor(cursor, snapshot, bbox)
        with connection(self.path) as conn:
            rows = conn.execute("SELECT payload FROM roads WHERE id > ? ORDER BY id", (after,)).fetchall()
        roads = [self.enrich(Road.model_validate_json(row[0])) for row in rows]
        if bbox:
            bounds = box(*bbox)
            roads = [road for road in roads if shape(road.geometry.model_dump()).intersects(bounds)]
        page = roads[:limit]
        next_cursor = None
        if len(roads) > limit:
            next_cursor = base64.urlsafe_b64encode(json.dumps({
                "after": page[-1].id, "snapshot": snapshot, "bbox": bbox
            }, separators=(",", ":")).encode()).decode()
        return page, next_cursor
