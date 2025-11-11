"""PostgreSQL repository for goal versions."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from psycopg2.extras import Json, RealDictCursor

from packages.kernel_common.persistence_v2 import get_backend, PostgresBackend

from .models import GoalVersion


class GoalVersionRepositoryPG:
    """CRUD operations for versioning.goal_versions."""

    def __init__(self) -> None:
        backend = get_backend()
        if not isinstance(backend, PostgresBackend):
            raise RuntimeError("GoalVersionRepositoryPG requires Postgres backend")
        self._backend = backend

    def _row_to_model(self, row: Dict[str, Any]) -> GoalVersion:
        data_inputs = row.get("data_inputs") if row.get("data_inputs") is not None else None
        knowledge_snippets = row.get("knowledge_snippets") or []
        retrieval = row.get("retrieval") or {}
        provenance = row.get("provenance") or {}
        return GoalVersion(
            version_id=row["version_id"],
            tenant_id=row["tenant_id"],
            project_id=row["project_id"],
            goal=row["goal"],
            ops=row["ops"],
            data_inputs=data_inputs,
            playbook_id=row.get("playbook_id"),
            knowledge_snippets=knowledge_snippets,
            parent_version_id=row.get("parent_version_id"),
            label=row.get("label"),
            created_at=row["created_at"],
            goal_hash=row["goal_hash"],
            retrieval=retrieval,
            provenance=provenance,
        )

    def upsert(self, version: GoalVersion) -> GoalVersion:
        sql = """
            INSERT INTO versioning.goal_versions (
                version_id, tenant_id, project_id, goal, ops,
                data_inputs, playbook_id, knowledge_snippets,
                parent_version_id, label, created_at, goal_hash,
                retrieval, provenance
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (version_id) DO UPDATE SET
                tenant_id = EXCLUDED.tenant_id,
                project_id = EXCLUDED.project_id,
                goal = EXCLUDED.goal,
                ops = EXCLUDED.ops,
                data_inputs = EXCLUDED.data_inputs,
                playbook_id = EXCLUDED.playbook_id,
                knowledge_snippets = EXCLUDED.knowledge_snippets,
                parent_version_id = EXCLUDED.parent_version_id,
                label = EXCLUDED.label,
                goal_hash = EXCLUDED.goal_hash,
                retrieval = EXCLUDED.retrieval,
                provenance = EXCLUDED.provenance,
                created_at = EXCLUDED.created_at
            RETURNING *
        """
        params = [
            version.version_id,
            version.tenant_id,
            version.project_id,
            version.goal,
            Json(version.ops),
            Json(version.data_inputs) if version.data_inputs is not None else None,
            version.playbook_id,
            version.knowledge_snippets,
            version.parent_version_id,
            version.label,
            version.created_at,
            version.goal_hash,
            Json(version.retrieval),
            Json(version.provenance),
        ]
        with self._backend.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, params)
                row = cur.fetchone()
            conn.commit()
        return self._row_to_model(row)

    def get(self, version_id: str) -> Optional[GoalVersion]:
        sql = "SELECT * FROM versioning.goal_versions WHERE version_id = %s"
        with self._backend.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, [version_id])
                row = cur.fetchone()
        if not row:
            return None
        return self._row_to_model(row)

    def list_for_project(self, tenant_id: str, project_id: str) -> List[GoalVersion]:
        sql = """
            SELECT * FROM versioning.goal_versions
             WHERE tenant_id = %s AND project_id = %s
             ORDER BY created_at DESC
        """
        with self._backend.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, [tenant_id, project_id])
                rows = cur.fetchall()
        return [self._row_to_model(row) for row in rows]

    def list_for_tenant(self, tenant_id: str) -> List[GoalVersion]:
        sql = """
            SELECT * FROM versioning.goal_versions
             WHERE tenant_id = %s
             ORDER BY created_at DESC
        """
        with self._backend.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, [tenant_id])
                rows = cur.fetchall()
        return [self._row_to_model(row) for row in rows]

    def annotate(self, version_id: str, fields: Dict[str, Any]) -> Optional[GoalVersion]:
        if not fields:
            return self.get(version_id)
        columns = []
        params: List[Any] = []
        for key, value in fields.items():
            if key in {"ops", "retrieval", "provenance", "data_inputs"} and value is not None:
                columns.append(f"{key} = %s")
                params.append(Json(value))
            elif key == "knowledge_snippets" and value is not None:
                columns.append("knowledge_snippets = %s")
                params.append(value)
            else:
                columns.append(f"{key} = %s")
                params.append(value)
        params.append(version_id)
        sql = f"""
            UPDATE versioning.goal_versions
               SET {', '.join(columns)}
             WHERE version_id = %s
            RETURNING *
        """
        with self._backend.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, params)
                row = cur.fetchone()
            conn.commit()
        if not row:
            return None
        return self._row_to_model(row)

    def iter_all(self) -> Iterable[GoalVersion]:
        sql = "SELECT * FROM versioning.goal_versions ORDER BY created_at DESC"
        with self._backend.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql)
                for row in cur:
                    yield self._row_to_model(dict(row))
