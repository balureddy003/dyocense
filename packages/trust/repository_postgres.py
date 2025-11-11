"""PostgreSQL repository for compliance facts."""

from __future__ import annotations

from typing import Any, Iterable, List, Optional

from psycopg2.extras import Json, RealDictCursor

from packages.kernel_common.persistence_v2 import get_backend, PostgresBackend
from .facts import ComplianceFact


class ComplianceFactRepositoryPG:
    """CRUD helpers for trust.compliance_facts."""

    def __init__(self) -> None:
        backend = get_backend()
        if not isinstance(backend, PostgresBackend):
            raise RuntimeError("ComplianceFactRepositoryPG requires Postgres backend")
        self._backend = backend

    def _row_to_fact(self, row: dict[str, Any]) -> ComplianceFact:
        metadata = row.get("metadata") or {}
        return ComplianceFact(
            fact_id=row["fact_id"],
            run_id=row["run_id"],
            tenant_id=row["tenant_id"],
            category=row["category"],
            statement=row["statement"],
            status=row["status"],
            source=row.get("source"),
            metadata=metadata,
            recorded_at=row.get("recorded_at"),
        )

    def record(self, fact: ComplianceFact) -> ComplianceFact:
        sql = """
            INSERT INTO trust.compliance_facts (
                fact_id, run_id, tenant_id, category, statement,
                status, source, metadata, recorded_at
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (fact_id) DO UPDATE SET
                category = EXCLUDED.category,
                statement = EXCLUDED.statement,
                status = EXCLUDED.status,
                source = EXCLUDED.source,
                metadata = EXCLUDED.metadata,
                recorded_at = EXCLUDED.recorded_at
            RETURNING *
        """
        params = [
            fact.fact_id,
            fact.run_id,
            fact.tenant_id,
            fact.category,
            fact.statement,
            fact.status,
            fact.source,
            Json(fact.metadata),
            fact.recorded_at,
        ]
        with self._backend.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, params)
                row = cur.fetchone()
            conn.commit()
        return self._row_to_fact(row)

    def record_many(self, facts: Iterable[ComplianceFact]) -> None:
        sql = """
            INSERT INTO trust.compliance_facts (
                fact_id, run_id, tenant_id, category, statement,
                status, source, metadata, recorded_at
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (fact_id) DO NOTHING
        """
        rows = [
            (
                fact.fact_id,
                fact.run_id,
                fact.tenant_id,
                fact.category,
                fact.statement,
                fact.status,
                fact.source,
                Json(fact.metadata),
                fact.recorded_at,
            )
            for fact in facts
        ]
        if not rows:
            return
        with self._backend.get_connection() as conn:
            with conn.cursor() as cur:
                cur.executemany(sql, rows)
            conn.commit()

    def list_for_run(self, run_id: str) -> List[ComplianceFact]:
        sql = """
            SELECT * FROM trust.compliance_facts
             WHERE run_id = %s
             ORDER BY recorded_at ASC
        """
        with self._backend.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, [run_id])
                rows = cur.fetchall()
        return [self._row_to_fact(row) for row in rows]

    def list_for_tenant(self, tenant_id: str, limit: int = 50) -> List[ComplianceFact]:
        sql = """
            SELECT * FROM trust.compliance_facts
             WHERE tenant_id = %s
             ORDER BY recorded_at DESC
             LIMIT %s
        """
        with self._backend.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, [tenant_id, limit])
                rows = cur.fetchall()
        return [self._row_to_fact(row) for row in rows]

    def get(self, fact_id: str) -> Optional[ComplianceFact]:
        sql = "SELECT * FROM trust.compliance_facts WHERE fact_id = %s"
        with self._backend.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, [fact_id])
                row = cur.fetchone()
        if not row:
            return None
        return self._row_to_fact(row)
