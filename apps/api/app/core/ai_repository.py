"""Append-only, minimal interaction metadata and bounded immutable evidence projections."""
import json
from app.models.database import connection
from app.services.estimates import canonical_hash


class AIInteractionAuditRepository:
    def __init__(self, path): self.path = path

    def save(self, result, request_id):
        metadata = dict(interaction_id=result.explanation_id, task_type=result.task_type,
            source_record_ids=result.evidence.context.record_ids, context_type=result.evidence.context.type,
            evidence_snapshot_hash=result.evidence_snapshot_hash, provider='openai' if result.model_label else None,
            model_label=result.model_label, output_mode=result.provider_status,
            validation_outcome=result.validation_status, error_category=result.fallback_reason,
            generated_at=result.generated_at.isoformat(), request_correlation_id=request_id,
            contract_version='ai-explanation-v1', output_hash=canonical_hash(result.model_dump(mode='json')))
        with connection(self.path) as c:
            c.execute('INSERT OR IGNORE INTO ai_evidence VALUES (?, ?)', (result.evidence_snapshot_hash, result.evidence.model_dump_json()))
            c.execute('INSERT INTO ai_interactions VALUES (?, ?, ?)', (result.explanation_id, result.evidence_snapshot_hash, json.dumps(metadata, sort_keys=True)))

    def get(self, interaction_id):
        with connection(self.path) as c:
            row = c.execute('SELECT payload FROM ai_interactions WHERE id=?', (interaction_id,)).fetchone()
        return json.loads(row[0]) if row else None

    def review(self, evaluation_id, body, request_id):
        from datetime import datetime, timezone
        from uuid import uuid4
        event = dict(id=str(uuid4()), action='review_note', evaluation_id=evaluation_id,
            **body.model_dump(), created_at=datetime.now(timezone.utc).isoformat(), request_correlation_id=request_id,
            authorizes_work=False)
        with connection(self.path) as c:
            c.execute('INSERT INTO review_events VALUES (?, ?, ?)', (event['id'], evaluation_id, json.dumps(event, sort_keys=True)))
        return event
