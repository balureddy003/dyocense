"""PostgreSQL repository for evidence records."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from psycopg2.extras import Json, RealDictCursor

from packages.kernel_common.persistence_v2 import get_backend, PostgresBackend


class EvidenceRepositoryPG:
    """Store and retrieve evidence records from Postgres."""

    def __init__(self) -> None:
        backend = get_backend()
        if not isinstance(backend, PostgresBackend):
            raise RuntimeError("EvidenceRepositoryPG requires Postgres backend")
        self._backend = backend

    def _row_to_record(self, row: dict[str, Any]) -> dict[str, Any]:
        record = dict(row)
        if record.get("stored_at") and isinstance(record["stored_at"], datetime):
            record["stored_at"] = record["stored_at"].isoformat()
        if record.get("created_at") and isinstance(record["created_at"], datetime):
            record["created_at"] = record["created_at"].isoformat()
        if record.get("updated_at") and isinstance(record["updated_at"], datetime):
            record["updated_at"] = record["updated_at"].isoformat()
        return record

    def create(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Insert a new evidence record."""
        sql = """
            INSERT INTO evidence.records (
                run_id, tenant_id, ops, solution, explanation,
                artifacts, goal_pack, stored_at
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (run_id) DO UPDATE SET
                tenant_id = EXCLUDED.tenant_id,
                ops = EXCLUDED.ops,
                solution = EXCLUDED.solution,
                explanation = EXCLUDED.explanation,
                artifacts = EXCLUDED.artifacts,
                goal_pack = EXCLUDED.goal_pack,
                stored_at = EXCLUDED.stored_at,
                updated_at = NOW()
            RETURNING *
        """
        params = [
            payload["run_id"],
            payload["tenant_id"],
            Json(payload["ops"]),
            Json(payload["solution"]),
            Json(payload["explanation"]),
            Json(payload.get("artifacts")) if payload.get("artifacts") is not None else None,
            Json(payload.get("goal_pack")) if payload.get("goal_pack") is not None else None,
            payload.get("stored_at") or datetime.utcnow(),
        ]
        with self._backend.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, params)
                row = cur.fetchone()
            conn.commit()
        return self._row_to_record(row)

    def get(self, run_id: str) -> Optional[dict[str, Any]]:
        sql = "SELECT * FROM evidence.records WHERE run_id = %s"
        with self._backend.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, [run_id])
                row = cur.fetchone()
        if not row:
            return None
        return self._row_to_record(row)

    def list_by_tenant(self, tenant_id: str, limit: int = 20) -> list[dict[str, Any]]:
        sql = """
            SELECT * FROM evidence.records
             WHERE tenant_id = %s
             ORDER BY stored_at DESC
             LIMIT %s
        """
        with self._backend.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, [tenant_id, limit])
                rows = cur.fetchall()
        return [self._row_to_record(row) for row in rows]
