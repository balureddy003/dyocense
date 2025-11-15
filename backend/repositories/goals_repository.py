"""
Goals repository for Postgres smart_goals table.
Provides CRUD operations for goals persistence.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from uuid import UUID, uuid4
import json


class GoalsRepositoryPG:
	"""Repository for smart_goals table in Postgres."""

	def __init__(self, backend=None):
		from packages.kernel_common.persistence_v2 import get_backend
		self._backend = backend or get_backend()

	def create(
		self,
		tenant_id: str,
		title: str,
		description: str = "",
		category: str = "custom",
		target_value: float = 100.0,
		current_value: float = 0.0,
		unit: str = "units",
		deadline: Optional[str] = None,
		status: str = "active",
	) -> Dict[str, Any]:
		"""Create a new goal in smart_goals table."""
		goal_id = uuid4()
		now = datetime.now(timezone.utc)
		deadline_dt = datetime.fromisoformat(deadline.replace("Z", "+00:00")) if deadline else None
		
		sql = """
			INSERT INTO smart_goals (
				goal_id, tenant_id, title, description, category,
				target_value, current_value, unit, deadline, status,
				created_at, updated_at
			) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
			RETURNING goal_id, tenant_id, title, description, category,
			          target_value, current_value, unit, deadline, status,
			          created_at, updated_at, extra_data
		"""
		with self._backend.get_connection() as conn:
			with conn.cursor() as cur:
				cur.execute(
					sql,
					[
						str(goal_id),
						tenant_id,
						title,
						description,
						category,
						target_value,
						current_value,
						unit,
						deadline_dt,
						status,
						now,
						now,
					],
				)
				row = cur.fetchone()
			conn.commit()
		
		return self._row_to_dict(row) if row else {}

	def get(self, goal_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
		"""Get a goal by ID."""
		sql = """
			SELECT goal_id, tenant_id, title, description, category,
			       target_value, current_value, unit, deadline, status,
			       created_at, updated_at, extra_data
			  FROM smart_goals
			 WHERE goal_id = %s AND tenant_id = %s
		"""
		with self._backend.get_connection() as conn:
			with conn.cursor() as cur:
				cur.execute(sql, [goal_id, tenant_id])
				row = cur.fetchone()
		return self._row_to_dict(row) if row else None

	def list_by_tenant(self, tenant_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
		"""List all goals for a tenant, optionally filtered by status."""
		sql = """
			SELECT goal_id, tenant_id, title, description, category,
			       target_value, current_value, unit, deadline, status,
			       created_at, updated_at, extra_data
			  FROM smart_goals
			 WHERE tenant_id = %s
		"""
		params: List[Any] = [tenant_id]
		if status:
			sql += " AND status = %s"
			params.append(status)
		sql += " ORDER BY created_at DESC"
		
		with self._backend.get_connection() as conn:
			with conn.cursor() as cur:
				cur.execute(sql, params)
				rows = cur.fetchall()
		return [self._row_to_dict(row) for row in rows]

	def update(
		self,
		goal_id: str,
		tenant_id: str,
		title: Optional[str] = None,
		description: Optional[str] = None,
		current_value: Optional[float] = None,
		target_value: Optional[float] = None,
		status: Optional[str] = None,
		deadline: Optional[str] = None,
	) -> Optional[Dict[str, Any]]:
		"""Update goal fields."""
		updates = []
		params = []
		
		if title is not None:
			updates.append("title = %s")
			params.append(title)
		if description is not None:
			updates.append("description = %s")
			params.append(description)
		if current_value is not None:
			updates.append("current_value = %s")
			params.append(current_value)
		if target_value is not None:
			updates.append("target_value = %s")
			params.append(target_value)
		if status is not None:
			updates.append("status = %s")
			params.append(status)
		if deadline is not None:
			deadline_dt = datetime.fromisoformat(deadline.replace("Z", "+00:00")) if deadline else None
			updates.append("deadline = %s")
			params.append(deadline_dt)
		
		if not updates:
			return self.get(goal_id, tenant_id)
		
		updates.append("updated_at = %s")
		params.append(datetime.now(timezone.utc))
		params.extend([goal_id, tenant_id])
		
		sql = f"""
			UPDATE smart_goals
			   SET {", ".join(updates)}
			 WHERE goal_id = %s AND tenant_id = %s
			RETURNING goal_id, tenant_id, title, description, category,
			          target_value, current_value, unit, deadline, status,
			          created_at, updated_at, extra_data
		"""
		with self._backend.get_connection() as conn:
			with conn.cursor() as cur:
				cur.execute(sql, params)
				row = cur.fetchone()
			conn.commit()
		return self._row_to_dict(row) if row else None

	def delete(self, goal_id: str, tenant_id: str) -> bool:
		"""Delete a goal."""
		sql = "DELETE FROM smart_goals WHERE goal_id = %s AND tenant_id = %s"
		with self._backend.get_connection() as conn:
			with conn.cursor() as cur:
				cur.execute(sql, [goal_id, tenant_id])
				deleted = cur.rowcount > 0
			conn.commit()
		return deleted

	def _row_to_dict(self, row) -> Dict[str, Any]:
		"""Convert a DB row to a dict matching UI contract."""
		if not row:
			return {}
		(
			goal_id,
			tenant_id,
			title,
			description,
			category,
			target_value,
			current_value,
			unit,
			deadline,
			status,
			created_at,
			updated_at,
			extra_data,
		) = row
		return {
			"id": str(goal_id),
			"tenant_id": str(tenant_id),
			"title": title,
			"description": description or "",
			"category": category or "custom",
			"target": float(target_value or 0),
			"current": float(current_value or 0),
			"unit": unit or "units",
			"deadline": deadline.isoformat() if deadline else None,
			"status": status,
			"created_at": created_at.isoformat() if created_at else None,
			"updated_at": updated_at.isoformat() if updated_at else None,
			"auto_tracked": (extra_data or {}).get("auto_tracked", False) if extra_data else False,
			"connector_source": (extra_data or {}).get("connector_source") if extra_data else None,
		}
