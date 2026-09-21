import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


def create_job_audit_run(
    db: Session,
    *,
    run_group_id: str,
    job_key: str,
    status: str,
    provider: str | None = None,
    target_type: str | None = None,
    target_id: str | None = None,
    target_name: str | None = None,
    processed: int = 0,
    inserted: int = 0,
    updated: int = 0,
    skipped: int = 0,
    error_message: str | None = None,
    metadata: dict[str, Any] | None = None,
    started_at: datetime | None = None,
    finished_at: datetime | None = None,
) -> int:
    now = datetime.now(timezone.utc)
    row = db.execute(
        text(
            """
            INSERT INTO job_audit_runs (
                run_group_id,
                job_key,
                provider,
                target_type,
                target_id,
                target_name,
                status,
                processed,
                inserted,
                updated,
                skipped,
                error_message,
                metadata,
                started_at,
                finished_at
            )
            VALUES (
                :run_group_id,
                :job_key,
                :provider,
                :target_type,
                :target_id,
                :target_name,
                :status,
                :processed,
                :inserted,
                :updated,
                :skipped,
                :error_message,
                CAST(:metadata AS JSONB),
                :started_at,
                :finished_at
            )
            RETURNING id
            """
        ),
        {
            "run_group_id": run_group_id,
            "job_key": job_key,
            "provider": provider,
            "target_type": target_type,
            "target_id": target_id,
            "target_name": target_name,
            "status": status,
            "processed": processed,
            "inserted": inserted,
            "updated": updated,
            "skipped": skipped,
            "error_message": error_message,
            "metadata": json.dumps(metadata or {}, ensure_ascii=False, default=str),
            "started_at": started_at or now,
            "finished_at": finished_at or now,
        },
    )
    return row.scalar_one()
