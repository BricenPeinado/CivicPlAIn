"""Small explicit SQLite repository; no data literals in HTTP routes."""
import base64
import binascii
import json
from pathlib import Path

from shapely.geometry import box, shape

from app.models.database import connection
from app.schemas.roads import Evidence, Road


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
        return Road.model_validate_json(row[0]) if row else None

    def evidence(self, evidence_id: str):
        with connection(self.path) as conn:
            row = conn.execute("SELECT payload FROM evidence WHERE id = ?", (evidence_id,)).fetchone()
        return Evidence.model_validate_json(row[0]) if row else None

    def list(self, limit: int, cursor: str | None, bbox: list[float] | None):
        snapshot = self.snapshot()
        after = decode_cursor(cursor, snapshot, bbox)
        with connection(self.path) as conn:
            rows = conn.execute("SELECT payload FROM roads WHERE id > ? ORDER BY id", (after,)).fetchall()
        roads = [Road.model_validate_json(row[0]) for row in rows]
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
