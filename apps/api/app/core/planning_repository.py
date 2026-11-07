"""Append-only estimate storage and related planning records."""
from decimal import Decimal

from app.models.database import connection
from app.schemas.planning import Assessment, AssetAttributes, Estimate, RepairOption


def ordered_assessments(records):
    # Dated newest first, stable ID ascending ties; undated evidence remains last.
    return sorted(records, key=lambda a: (-(a.assessed_on.toordinal() if a.assessed_on else 0), a.id))


class PlanningRepository:
    def __init__(self, path):
        self.path = path

    def assessments(self, road_id):
        with connection(self.path) as conn:
            rows = conn.execute('SELECT payload FROM assessments WHERE road_id=?', (road_id,)).fetchall()
        return ordered_assessments([Assessment.model_validate_json(row[0]) for row in rows])

    def assessment(self, assessment_id):
        with connection(self.path) as conn:
            row = conn.execute('SELECT payload FROM assessments WHERE id=?', (assessment_id,)).fetchone()
        return Assessment.model_validate_json(row[0]) if row else None

    def latest(self, road_id):
        return next((a for a in self.assessments(road_id) if a.rating is not None), None)

    def asset(self, road_id):
        with connection(self.path) as conn:
            row = conn.execute('SELECT payload FROM maintenance_assets WHERE road_id=?', (road_id,)).fetchone()
        return AssetAttributes.model_validate_json(row[0]) if row else None

    def options(self):
        with connection(self.path) as conn:
            rows = conn.execute('SELECT payload FROM repair_options ORDER BY id').fetchall()
        return [RepairOption.model_validate_json(row[0]) for row in rows]

    def get_estimate(self, estimate_id):
        with connection(self.path) as conn:
            row = conn.execute('SELECT payload FROM estimates WHERE id=?', (estimate_id,)).fetchone()
        return Estimate.model_validate_json(row[0]) if row else None

    def save(self, estimate: Estimate):
        cents = [int(Decimal(estimate.scenarios[name].total_usd) * 100) for name in ('low', 'base', 'high')]
        with connection(self.path) as conn:
            conn.execute('INSERT INTO estimates VALUES (?, ?, ?, ?, ?, ?, ?)',
                (estimate.id, estimate.road_segment_id, estimate.dataset_snapshot_id, estimate.model_dump_json(), *cents))
