from fastapi import FastAPI, Body, Query, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Any, Dict, List, Optional
import os
from datetime import datetime, timezone
import datetime as py_dt
import uuid
import json

# Optional imports of internal packages (guarded so local dev still runs)
try:
	from packages.connectors.repository_postgres import ConnectorRepositoryPG  # type: ignore
	from packages.kernel_common.persistence_v2 import get_backend, PostgresBackend  # type: ignore
	CONNECTORS_AVAILABLE = True
except Exception:
	ConnectorRepositoryPG = None  # type: ignore
	PostgresBackend = None  # type: ignore
	def get_backend():  # type: ignore
		return None
	CONNECTORS_AVAILABLE = False
try:
	from packages.connectors.marketplace import ConnectorMarketplace  # type: ignore
	MARKETPLACE_AVAILABLE = True
except Exception:
	ConnectorMarketplace = None  # type: ignore
	MARKETPLACE_AVAILABLE = False
try:
	from packages.connectors.testing import ConnectorTester  # type: ignore
	TESTING_AVAILABLE = True
except Exception:
	ConnectorTester = None  # type: ignore
	TESTING_AVAILABLE = False
try:
	from backend.repositories.goals_repository import GoalsRepositoryPG  # type: ignore
	GOALS_REPO_AVAILABLE = True
except Exception:
	GoalsRepositoryPG = None  # type: ignore
	GOALS_REPO_AVAILABLE = False


def create_app() -> FastAPI:
	app = FastAPI(title="Dyocense Kernel (stub)", version="0.1.0")

	# --- In-memory demo state (per-process; resets on restart) ---
	connectors_store: dict[str, list[dict]] = {}
	coach_dismissed_store: dict[str, set[str]] = {}

	# Instantiate reusable repositories/services when available
	connector_repo = None
	if CONNECTORS_AVAILABLE:
		try:
			connector_repo = ConnectorRepositoryPG()  # type: ignore
		except Exception:
			connector_repo = None
	marketplace = None
	if MARKETPLACE_AVAILABLE:
		try:
			marketplace = ConnectorMarketplace()  # type: ignore
		except Exception:
			marketplace = None
	connector_tester = None
	if TESTING_AVAILABLE:
		try:
			connector_tester = ConnectorTester()  # type: ignore
		except Exception:
			connector_tester = None
	goals_repo = None
	if GOALS_REPO_AVAILABLE and CONNECTORS_AVAILABLE:
		try:
			backend = get_backend()
			if backend is not None and PostgresBackend is not None and isinstance(backend, PostgresBackend):  # type: ignore
				goals_repo = GoalsRepositoryPG()  # type: ignore
		except Exception:
			goals_repo = None

	# --- CORS (enable preflight for browser clients) ---
	origins_env = os.getenv("CORS_ORIGINS", "*")
	# Support comma-separated list, trim whitespace
	origins = [o.strip() for o in origins_env.split(",") if o.strip()] if origins_env else ["*"]
	app.add_middleware(
		CORSMiddleware,
		allow_origins=origins,
		allow_credentials=True,
		allow_methods=["*"],
		allow_headers=["*"],
	)

	@app.get("/health")
	def health() -> Dict[str, str]:
		return {"status": "ok"}

	@app.post("/v1/compile")
	def compile_goal(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
		goal = payload.get("goal", "")
		tenant_id = payload.get("tenant_id", "")
		project_id = payload.get("project_id", "")
		# Minimal stub: return a single no-op that carries the goal metadata
		ops: List[Dict[str, Any]] = [
			{
				"id": "op-1",
				"type": "noop",
				"meta": {"goal": goal, "tenant_id": tenant_id, "project_id": project_id},
			}
		]
		return {"ops": ops}

	@app.post("/v1/optimise")
	def optimise(payload: Dict[str, Any] = Body(...)) -> JSONResponse:
		_ops = payload.get("ops", [])
		# Minimal stub: accept ops and report success
		return JSONResponse(status_code=200, content={"status": "ok", "ops_count": len(_ops)})

	@app.get("/v1/catalog")
	def catalog() -> Dict[str, Any]:
		# Minimal stub: example catalog
		return {"items": [
			{"id": "policy-001", "name": "Default Policy", "category": "policy"},
			{"id": "optimizer-default", "name": "Default Optimizer", "category": "optimizer"},
		]}

	# --- Minimal Health Score API for beta validation ---
	@app.get("/v1/tenants/{tenant_id}/health-score")
	def get_health_score(tenant_id: str) -> Dict[str, Any]:
		"""Compute a simple health score from available data counts in Postgres."""
		now = datetime.now(timezone.utc).isoformat()
		orders = 0
		inventory = 0
		customers = 0
		# Prefer direct Postgres reads when available (even if connector_repo package is missing)
		if PostgresBackend is not None:
			try:
				backend = get_backend()
				if backend is not None and isinstance(backend, PostgresBackend):  # type: ignore
					with backend.get_connection() as conn:  # type: ignore
						with conn.cursor() as cur:
							# Align with current schema: use data_sources.extra_data for totals and data types
							cur.execute(
								"""
								SELECT COALESCE(extra_data->>'data_types', '[]') AS data_types,
								       COALESCE((extra_data->>'total_records')::int, 0)    AS total
								  FROM data_sources
								 WHERE tenant_id = %s
								""",
								[tenant_id],
							)
							for row in cur.fetchall():
								try:
									dt = json.loads(row[0] or "[]")
								except Exception:
									dt = []
								total = int(row[1] or 0)
								if "orders" in dt:
									orders += total
								if "inventory" in dt:
									inventory += total
								if "customers" in dt:
									customers += total
			except Exception:
				pass
		# Scale naive subscores: present data boosts corresponding area
		revenue = min(100, 50 + min(50, orders // 100))
		operations = min(100, 50 + min(50, inventory // 100))
		customer = min(100, 50 + min(50, customers // 100))
		score = round((revenue + operations + customer) / 3)
		trend = 2 if score >= 60 else -1
		return {
			"score": score,
			"trend": trend,
			"breakdown": {
				"revenue": revenue,
				"operations": operations,
				"customer": customer,
				"revenue_available": orders > 0,
				"operations_available": inventory > 0,
				"customer_available": customers > 0,
			},
			"last_updated": now,
			"period_days": 7,
		}

	@app.get("/v1/tenants/{tenant_id}/metrics/snapshot")
	def get_metrics_snapshot(tenant_id: str) -> List[Dict[str, Any]]:
		"""
		Return a small set of metric snapshots for dashboard cards.
		Query business_metrics table when available, otherwise fallback.
		"""
		if CONNECTORS_AVAILABLE and PostgresBackend is not None:
			try:
				backend = get_backend()
				if backend is not None and isinstance(backend, PostgresBackend):  # type: ignore
					with backend.get_connection() as conn:  # type: ignore
						with conn.cursor() as cur:
							# Get latest health score from smart_goals table progress
							cur.execute(
								"""
								SELECT COALESCE(AVG((current_value / NULLIF(target_value, 0)) * 100), 0)::int AS avg_progress
								  FROM smart_goals
							 WHERE tenant_id = %s AND status = 'active'
							""",
							[tenant_id],
						)
						row = cur.fetchone()
						current_score = int(row[0]) if row else 72
						
						# Get revenue growth from business_metrics if available
						cur.execute(
							"""
							SELECT value FROM business_metrics
							 WHERE tenant_id = %s AND metric_name = 'revenue_growth'
							 ORDER BY timestamp DESC LIMIT 1
							""",
							[tenant_id],
						)
						row = cur.fetchone()
						revenue_growth = float(row[0]) if row else 4.2
						
						# Count completed tasks (if we had tasks table; for now, hardcode)
						tasks_completed = 27
						
					return [
						{
							"id": "current_score",
							"label": "Current Score",
							"value": str(current_score),
							"change": 4,
							"changeType": "absolute",
							"trend": "up" if current_score > 68 else "down",
							"period": "last_7_days",
						},
						{
							"id": "revenue_growth",
							"label": "Revenue Growth",
							"value": f"+{revenue_growth:.1f}%",
							"change": revenue_growth,
							"changeType": "percentage",
							"trend": "up" if revenue_growth > 0 else "down",
							"period": "vs_prev_7d",
						},
						{
							"id": "tasks_completed",
							"label": "Tasks Completed",
							"value": str(tasks_completed),
							"change": 17,
							"changeType": "percentage",
							"trend": "up",
							"period": "last_7_days",
						},
					]
			except Exception:
				pass
		# Fallback static
		return [
			{
				"id": "current_score",
				"label": "Current Score",
				"value": "72",
				"change": 4,
				"changeType": "absolute",
				"trend": "up",
				"period": "last_7_days",
			},
			{
				"id": "revenue_growth",
				"label": "Revenue Growth",
				"value": "+4.2%",
				"change": 4.2,
				"changeType": "percentage",
				"trend": "up",
				"period": "vs_prev_7d",
			},
			{
				"id": "tasks_completed",
				"label": "Tasks Completed",
				"value": "27",
				"change": 17,
				"changeType": "percentage",
				"trend": "up",
				"period": "last_7_days",
			},
		]

	@app.get("/v1/tenants/{tenant_id}/health-score/alerts")
	def get_health_alerts(tenant_id: str) -> List[Dict[str, Any]]:
		"""Generate alerts from goals that are off-track or metrics below threshold."""
		alerts: List[Dict[str, Any]] = []
		if goals_repo is not None:
			try:
				goals = goals_repo.list_by_tenant(tenant_id, status="active")  # type: ignore
				for goal in goals:
					current = goal.get("current", 0)
					target = goal.get("target", 1)
					progress = (current / target * 100) if target > 0 else 0
					if progress < 50:
						alerts.append({
							"id": f"alert-goal-{goal.get('id')}",
							"type": "critical",
							"title": f"Goal at risk: {goal.get('title')}",
							"description": f"Only {progress:.0f}% progress toward target.",
							"metric": goal.get("category", "custom"),
							"value": f"{current} / {target}",
							"threshold": "50% progress",
						})
			except Exception:
				pass
		# Fallback minimal alert if none from goals
		if not alerts:
			alerts.append({
				"id": "alert-low-ops",
				"type": "critical",
				"title": "Operational efficiency is low",
				"description": "Order fulfillment times are trending above target.",
				"metric": "operations",
				"value": "SLA 92%",
				"threshold": ">= 95%",
			})
		return alerts

	@app.get("/v1/tenants/{tenant_id}/health-score/signals")
	def get_health_signals(tenant_id: str) -> List[Dict[str, Any]]:
		"""Generate positive signals from goals on-track or metrics above baseline."""
		signals: List[Dict[str, Any]] = []
		if goals_repo is not None:
			try:
				goals = goals_repo.list_by_tenant(tenant_id, status="active")  # type: ignore
				for goal in goals:
					current = goal.get("current", 0)
					target = goal.get("target", 1)
					progress = (current / target * 100) if target > 0 else 0
					if progress >= 75:
						signals.append({
							"id": f"signal-goal-{goal.get('id')}",
							"type": "positive",
							"title": f"Strong progress: {goal.get('title')}",
							"description": f"Already at {progress:.0f}% of target.",
							"metric": goal.get("category", "custom"),
							"value": f"{progress:.0f}%",
						})
			except Exception:
				pass
		# Fallback minimal signal
		if not signals:
			signals.append({
				"id": "signal-rev-growth",
				"type": "positive",
				"title": "Revenue up week-over-week",
				"description": "Last 7 days revenue grew +4% vs prior period.",
				"metric": "revenue",
				"value": "+4%",
			})
		return signals

	# --- Minimal Goals & Tasks APIs (stubbed for UI integration) ---

	# Data source summary used by BusinessContext and onboarding
	@app.get("/v1/tenants/{tenant_id}/data-source")
	def get_data_source_summary(tenant_id: str) -> Dict[str, Any]:
		"""
		Return a tiny summary about connected data so UI can show sample vs real data messaging.
		Shape matches apps/smb/src/contexts/BusinessContext.tsx DataSource.
		"""
		# Attempt to compute from connectors metadata in Postgres
		if PostgresBackend is not None:
			try:
				backend = get_backend()
				if backend is not None and isinstance(backend, PostgresBackend):  # type: ignore
					orders = 0
					inventory = 0
					customers = 0
					has_real = False
					with backend.get_connection() as conn:  # type: ignore
						with conn.cursor() as cur:
							cur.execute(
								"""
								SELECT COALESCE(extra_data->>'data_types', '[]') AS data_types,
								       COALESCE((extra_data->>'total_records')::int, 0)    AS total
								  FROM data_sources
								 WHERE tenant_id = %s
								""",
								[tenant_id],
							)
							for row in cur.fetchall():
								try:
									dtypes = json.loads(row[0] or "[]")
								except Exception:
									dtypes = []
								total = int(row[1] or 0)
								if total > 0:
									has_real = True
								if "orders" in dtypes:
									orders += total
								if "inventory" in dtypes:
									inventory += total
								if "customers" in dtypes:
									customers += total
					return {"orders": orders, "inventory": inventory, "customers": customers, "hasRealData": has_real}
			except Exception:
				pass
		# Fallback demo values
		return {"orders": 0, "inventory": 0, "customers": 0, "hasRealData": False}

	@app.get("/v1/tenants/{tenant_id}/goals")
	def list_goals(tenant_id: str, status: Optional[str] = Query(default=None)) -> List[Dict[str, Any]]:
		"""List goals from Postgres smart_goals when available; fallback to static."""
		if goals_repo is not None:
			try:
				return goals_repo.list_by_tenant(tenant_id, status=status)  # type: ignore
			except Exception:
				pass
		# Fallback
		return [
			{"id": "goal-1", "title": "Increase weekly revenue by 5%", "current": 3.0, "target": 5.0, "unit": "%", "status": "active"},
			{"id": "goal-2", "title": "Reduce order cycle time to 24h", "current": 28, "target": 24, "unit": "hours", "status": "active"},
		]

	@app.post("/v1/tenants/{tenant_id}/goals")
	def create_goal(tenant_id: str, payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
		"""Create a goal in Postgres or echo back a stub."""
		if goals_repo is not None:
			try:
				return goals_repo.create(  # type: ignore
					tenant_id=tenant_id,
					title=payload.get("title", "Untitled Goal"),
					description=payload.get("description", ""),
					category=payload.get("category", "custom"),
					target_value=float(payload.get("target", 100)),
					current_value=float(payload.get("current", 0)),
					unit=payload.get("unit", "units"),
					deadline=payload.get("deadline"),
					status=payload.get("status", "active"),
				)
			except Exception:
				pass
		# Fallback
		return {
			"id": f"goal-{int(datetime.now().timestamp())}",
			"title": payload.get("title", "Untitled Goal"),
			"current": payload.get("current", 0),
			"target": payload.get("target", 100),
			"unit": payload.get("unit", "units"),
			"status": "active",
		}

	@app.put("/v1/tenants/{tenant_id}/goals/{goal_id}")
	def update_goal(tenant_id: str, goal_id: str, payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
		"""Update goal in Postgres or return unchanged stub."""
		if goals_repo is not None:
			try:
				updated = goals_repo.update(  # type: ignore
					goal_id=goal_id,
					tenant_id=tenant_id,
					title=payload.get("title"),
					description=payload.get("description"),
					current_value=payload.get("current"),
					target_value=payload.get("target"),
					status=payload.get("status"),
					deadline=payload.get("deadline"),
				)
				if updated:
					return updated
			except Exception:
				pass
		# Fallback
		return {"id": goal_id, **payload}

	@app.delete("/v1/tenants/{tenant_id}/goals/{goal_id}")
	def delete_goal(tenant_id: str, goal_id: str) -> Dict[str, Any]:
		"""Delete goal from Postgres or acknowledge stub deletion."""
		if goals_repo is not None:
			try:
				goals_repo.delete(goal_id, tenant_id)  # type: ignore
			except Exception:
				pass
		return {"success": True}

	@app.get("/v1/tenants/{tenant_id}/tasks")
	def list_tasks(tenant_id: str, status: Optional[str] = Query(default=None)) -> List[Dict[str, Any]]:
		# Simple static tasks; filter by status when provided
		tasks = [
			{"id": "task-1", "title": "Connect your POS data", "status": "todo"},
			{"id": "task-2", "title": "Upload last 3 months sales CSV", "status": "in_progress"},
			{"id": "task-3", "title": "Review weekly action plan", "status": "todo"},
		]
		if status:
			return [t for t in tasks if t.get("status") == status]
		return tasks

	@app.post("/v1/tenants/{tenant_id}/tasks")
	def create_task(tenant_id: str, payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
		return {
			"id": f"task-{int(datetime.now().timestamp())}",
			"title": payload.get("title", "Untitled Task"),
			"status": payload.get("status", "todo"),
		}

	@app.put("/v1/tenants/{tenant_id}/tasks/{task_id}")
	def update_task(tenant_id: str, task_id: str, payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
		# Echo back the updated task payload
		return {"id": task_id, **payload}

	# --- Minimal Connectors API (used by hooks/useConnectors) ---
	@app.get("/v1/tenants/{tenant_id}/connectors")
	def list_connectors(tenant_id: str, status_filter: Optional[str] = Query(default=None)) -> Dict[str, Any]:
		"""List connectors from Postgres when available; fallback to in-memory."""
		# Preferred path: repository (when package is available)
		if connector_repo is not None:
			status_enum = None
			if status_filter:
				try:
					from packages.connectors.models import ConnectorStatus  # type: ignore
				except Exception:
					ConnectorStatus = None  # type: ignore
				if ConnectorStatus is not None:
					try:
						status_enum = ConnectorStatus(status_filter)  # type: ignore
					except Exception:
						status_enum = None
			models = connector_repo.list_by_tenant(tenant_id, status_enum)  # type: ignore
			items = [m.model_dump() if hasattr(m, "model_dump") else m for m in models]
			return {"connectors": items, "total": len(items)}
		# Secondary path: direct SQL against data_sources when Postgres backend available
		if PostgresBackend is not None:
			try:
				backend = get_backend()
				if backend is not None and isinstance(backend, PostgresBackend):  # type: ignore
					with backend.get_connection() as conn:  # type: ignore
						with conn.cursor() as cur:
							cur.execute(
								"""
								SELECT source_id, tenant_id, connector_type, name, status, last_sync, sync_frequency, extra_data
								  FROM data_sources
								 WHERE tenant_id = %s
								""",
								[tenant_id],
							)
							rows = cur.fetchall()
							items: List[Dict[str, Any]] = []
							for r in rows:
								(src_id, t_id, ctype, name, status, last_sync, freq, extra) = r
								meta = extra or {}
								if isinstance(meta, str):
									try:
										meta = json.loads(meta)
									except Exception:
										meta = {}
								items.append({
									"connector_id": str(src_id),
									"connector_type": ctype,
									"connector_name": ctype,
									"display_name": name,
									"category": meta.get("category", "api"),
									"icon": meta.get("icon", "Plug"),
									"data_types": meta.get("data_types", []),
									"status": status or "inactive",
									"sync_frequency": freq or "manual",
									"last_sync": last_sync.isoformat() if last_sync else None,
									"created_at": None,
									"updated_at": None,
									"metadata": meta,
								})
					return {"connectors": items, "total": len(items)}
			except Exception:
				pass
		# Fallback (dev only)
		items = connectors_store.get(tenant_id, [])
		return {"connectors": items, "total": len(items)}

	@app.post("/v1/tenants/{tenant_id}/connectors")
	def create_connector(tenant_id: str, payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
		"""Create a connector backed by Postgres repository when available."""
		connector_type = payload.get("connector_type", "custom")
		display_name = payload.get("display_name") or connector_type.replace("_", " ").title()
		sync_frequency = payload.get("sync_frequency", "manual")
		enable_mcp = bool(payload.get("enable_mcp", False))
		config = payload.get("config", {})
		# Enrich from marketplace if possible
		category = "api"
		icon = "Plug"
		data_types: list[str] = ["orders"]
		if marketplace is not None:
			try:
				mp = marketplace.get_by_id(connector_type)
				if mp:
					category = (mp.get("category") or "api") if isinstance(mp.get("category"), str) else (mp.get("category").value if mp.get("category") else "api")
					icon = mp.get("icon") or icon
					data_types = mp.get("dataTypes") or mp.get("data_types") or data_types
			except Exception:
				pass
		# Repo-backed creation
		if connector_repo is not None:
			created = connector_repo.create(
				tenant_id=tenant_id,
				connector_type=connector_type,
				connector_name=connector_type,
				display_name=display_name,
				category=category,
				icon=icon,
				config=config,
				data_types=data_types,
				created_by="system",
				sync_frequency=sync_frequency,
			)
			# Set MCP flag if requested
			try:
				if enable_mcp:
					connector_repo.update_metadata_flag(created.connector_id, mcp_enabled=True)
			except Exception:
				pass
			return created.model_dump() if hasattr(created, "model_dump") else created  # type: ignore
		# Direct SQL-backed creation (no repository package, but Postgres is available)
		backend = get_backend()
		if PostgresBackend is not None and backend is not None and isinstance(backend, PostgresBackend):  # type: ignore
			try:
				source_id = str(uuid.uuid4())
				# Build datasets from data_types and initialize counts
				datasets = [dt.lower().replace(" ", "_") for dt in data_types]
				last_record_count = {ds: 0 for ds in datasets}
				extra = {
					"category": category,
					"icon": icon,
					"data_types": data_types,
					"datasets": datasets,
					"last_record_count": last_record_count,
					"total_records": 0,
					"mcp_enabled": enable_mcp,
				}
				with backend.get_connection() as conn:  # type: ignore
					with conn.cursor() as cur:
						cur.execute(
							"""
							INSERT INTO data_sources (source_id, tenant_id, connector_type, name, credentials, config, status, last_sync, sync_frequency, created_at, extra_data)
							VALUES (%s, %s, %s, %s, %s, %s, 'inactive', NULL, %s, NOW(), %s)
							""",
							[
								source_id,
								tenant_id,
								connector_type,
								display_name,
								json.dumps({}),
								json.dumps(config or {}),
								sync_frequency,
								json.dumps(extra),
							],
						)
					conn.commit()
				record = {
					"connector_id": source_id,
					"connector_type": connector_type,
					"connector_name": connector_type,
					"display_name": display_name,
					"category": category,
					"icon": icon,
					"data_types": data_types,
					"datasets": datasets,
					"status": "inactive",
					"sync_frequency": sync_frequency,
					"last_sync": None,
					"created_at": datetime.now(timezone.utc).isoformat(),
					"updated_at": datetime.now(timezone.utc).isoformat(),
					"metadata": extra,
				}
				return record
			except Exception:
				pass
		# Fallback to in-memory
		connector_id = f"conn-{int(datetime.now().timestamp()*1000)}"
		item = {
			"connector_id": connector_id,
			"connector_type": connector_type,
			"connector_name": connector_type,
			"display_name": display_name,
			"category": category,
			"icon": icon,
			"data_types": data_types,
			"status": "inactive",
			"sync_frequency": sync_frequency,
			"last_sync": None,
			"created_at": datetime.now(timezone.utc).isoformat(),
			"updated_at": datetime.now(timezone.utc).isoformat(),
			"metadata": {"mcp_enabled": enable_mcp},
		}
		connectors_store.setdefault(tenant_id, []).append(item)
		return item

	@app.put("/v1/tenants/{tenant_id}/connectors/{connector_id}")
	def update_connector(tenant_id: str, connector_id: str, payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
		"""Update connector metadata in Postgres; fallback to in-memory update."""
		if connector_repo is not None and isinstance(get_backend(), PostgresBackend):  # type: ignore
			# Apply MCP flag via repo
			if "enable_mcp" in payload:
				try:
					connector_repo.update_metadata_flag(connector_id, mcp_enabled=bool(payload.get("enable_mcp")))  # type: ignore
				except Exception:
					pass
			# Update simple fields via direct SQL against data_sources
			try:
				backend = get_backend()
				with backend.get_connection() as conn:  # type: ignore
					with conn.cursor() as cur:
						cur.execute(
							"""
							UPDATE data_sources
							   SET name = COALESCE(%s, name),
							       sync_frequency = COALESCE(%s, sync_frequency),
							       status = COALESCE(%s, status),
							       updated_at = NOW()
							 WHERE source_id = %s AND tenant_id = %s
							""",
							[
								payload.get("display_name"),
								payload.get("sync_frequency"),
								payload.get("status"),
								connector_id,
								tenant_id,
							],
						)
					conn.commit()
			except Exception:
				pass
			return {"success": True}
		# Direct SQL when repository is unavailable but Postgres exists
		backend = get_backend()
		if PostgresBackend is not None and backend is not None and isinstance(backend, PostgresBackend):  # type: ignore
			try:
				with backend.get_connection() as conn:  # type: ignore
					with conn.cursor() as cur:
						# Update name, sync_frequency, status
						cur.execute(
							"""
							UPDATE data_sources
							   SET name = COALESCE(%s, name),
							       sync_frequency = COALESCE(%s, sync_frequency),
							       status = COALESCE(%s, status),
							       extra_data = CASE WHEN %s IS NULL THEN extra_data ELSE jsonb_set(COALESCE(extra_data, '{}'::jsonb), '{mcp_enabled}', to_jsonb(%s::boolean), true) END,
							       updated_at = NOW()
							 WHERE source_id = %s AND tenant_id = %s
							""",
							[
								payload.get("display_name"),
								payload.get("sync_frequency"),
								payload.get("status"),
								None if "enable_mcp" not in payload else True,
								bool(payload.get("enable_mcp")) if "enable_mcp" in payload else False,
								connector_id,
								tenant_id,
							],
						)
					conn.commit()
				return {"success": True}
			except Exception:
				pass
		# Fallback
		items = connectors_store.get(tenant_id, [])
		for it in items:
			if it.get("connector_id") == connector_id:
				it["display_name"] = payload.get("display_name", it.get("display_name"))
				if payload.get("sync_frequency"):
					it["sync_frequency"] = payload["sync_frequency"]
				if payload.get("status"):
					it["status"] = payload["status"]
				meta = it.setdefault("metadata", {})
				if "enable_mcp" in payload:
					meta["mcp_enabled"] = bool(payload.get("enable_mcp"))
				it["updated_at"] = datetime.now(timezone.utc).isoformat()
				return it
		return {"detail": "not found"}

	@app.delete("/v1/tenants/{tenant_id}/connectors/{connector_id}")
	def delete_connector(tenant_id: str, connector_id: str) -> Dict[str, Any]:
		backend = get_backend()
		if PostgresBackend is not None and isinstance(backend, PostgresBackend):  # type: ignore
			try:
				with backend.get_connection() as conn:  # type: ignore
					with conn.cursor() as cur:
						cur.execute("DELETE FROM data_sources WHERE source_id=%s AND tenant_id=%s", [connector_id, tenant_id])
					conn.commit()
				return {"success": True}
			except Exception:
				pass
		# Fallback
		items = connectors_store.get(tenant_id, [])
		connectors_store[tenant_id] = [it for it in items if it.get("connector_id") != connector_id]
		return {"success": True}

	@app.post("/v1/tenants/{tenant_id}/connectors/{connector_id}/test")
	def test_connector(tenant_id: str, connector_id: str) -> Dict[str, Any]:
		# Basic availability check: ensure connector exists in Postgres
		if connector_repo is not None:
			try:
				conn = connector_repo.get_by_id(connector_id)  # type: ignore
				if conn and getattr(conn, "tenant_id", tenant_id) == tenant_id:
					return {"success": True, "message": "Connection verified"}
			except Exception as e:
				return {"success": False, "message": f"Lookup failed: {e}"}
		return {"success": True, "message": "Connection verified (dev)"}

	@app.post("/v1/tenants/{tenant_id}/connectors/{connector_id}/sync")
	def sync_connector(tenant_id: str, connector_id: str, payload: Dict[str, Any] = Body(default={})) -> Dict[str, Any]:
		"""Trigger a sync for a connector. Updates last_sync timestamp."""
		if connector_repo is not None:
			try:
				conn = connector_repo.get_by_id(connector_id)  # type: ignore
				if conn and getattr(conn, "tenant_id", tenant_id) == tenant_id:
					# Update sync timestamp
					from datetime import datetime
					connector_repo.update_sync_info(connector_id, total_records=0, duration=0.0)  # type: ignore
					return {"success": True, "message": "Sync completed", "synced_at": py_dt.datetime.now(py_dt.timezone.utc).isoformat()}
			except Exception as e:
				return {"success": False, "message": f"Sync failed: {e}"}
		# Direct SQL path updates last_sync on data_sources
		backend = get_backend()
		if PostgresBackend is not None and backend is not None and isinstance(backend, PostgresBackend):  # type: ignore
			try:
				with backend.get_connection() as conn:  # type: ignore
					with conn.cursor() as cur:
						cur.execute(
							"""
							UPDATE data_sources
							   SET last_sync = NOW(), status = 'active'
							 WHERE source_id = %s AND tenant_id = %s
							""",
							[connector_id, tenant_id],
						)
					conn.commit()
				return {"success": True, "message": "Sync completed", "synced_at": py_dt.datetime.now(py_dt.timezone.utc).isoformat()}
			except Exception as e:
				return {"success": False, "message": f"Sync failed: {e}"}
		return {"success": True, "message": "Sync initiated (dev mode)"}

	@app.post("/v1/tenants/{tenant_id}/connectors/test")
	async def test_connector_config(tenant_id: str, payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
		"""Test connector configuration before saving."""
		connector_type = payload.get("connector_type", "")
		config = payload.get("config", {})
		
		# Use connector tester if available
		if connector_tester is not None:
			try:
				result = await connector_tester.test(connector_type, config)
				return {
					"success": result.success,
					"message": result.message,
					"details": result.details,
					"error_code": result.error_code
				}
			except Exception as e:
				return {
					"success": False,
					"message": f"Test failed: {str(e)}",
					"error_code": "TEST_ERROR"
				}
		
		# Fallback: basic validation
		return {"success": True, "message": "Configuration appears valid (testing service unavailable)"}

	@app.get("/v1/tenants/{tenant_id}/connectors/recommendations")
	def connector_recommendations(tenant_id: str) -> Dict[str, Any]:
		if marketplace is not None:
			try:
				# Minimal: surface a CSV quickstart from marketplace if present
				csv = marketplace.get_by_id("csv_upload")
				recs = []
				if csv:
					recs.append({
						"id": csv.get("id"),
						"label": csv.get("displayName") or csv.get("name"),
						"description": csv.get("description"),
						"icon": csv.get("icon", "📊"),
						"category": (csv.get("category") or "files"),
						"priority": 1,
						"reason": "Quick start - upload your existing spreadsheets",
						"fields": [
							{"name": "uploaded_file", "label": "Upload file", "type": "file", "accept": ".csv,.xlsx,.xls", "helper": "Select a CSV or Excel file from your computer"},
							{"name": "file_url", "label": "Or provide a URL (optional)", "placeholder": "https://example.com/export.csv", "helper": "If you have a hosted file that updates regularly"},
						],
					})
				existing = []
				if connector_repo is not None:
					try:
						existing = [c.connector_type for c in connector_repo.list_by_tenant(tenant_id)]  # type: ignore
					except Exception:
						existing = []
				return {
					"recommendations": recs or [],
					"business_profile": {"industry": None, "business_type": None, "team_size": None},
					"data_status": {"has_orders": False, "has_inventory": False, "has_customers": False, "has_products": False},
					"existing_connectors": existing,
					"message": "OK",
				}
			except Exception:
				pass
		# Fallback minimal recs
		return {
			"recommendations": [
				{
					"id": "csv_upload",
					"label": "CSV/Excel Upload",
					"description": "Upload a CSV or Excel file from your device, or provide a URL to fetch data automatically.",
					"icon": "📊",
					"category": "files",
					"priority": 1,
					"reason": "Quick start - upload your existing spreadsheets",
					"fields": [
						{"name": "uploaded_file", "label": "Upload file", "type": "file", "accept": ".csv,.xlsx,.xls", "helper": "Select a CSV or Excel file from your computer"},
						{"name": "file_url", "label": "Or provide a URL (optional)", "placeholder": "https://example.com/export.csv", "helper": "If you have a hosted file that updates regularly"},
					],
				}
			],
			"business_profile": {"industry": None, "business_type": None, "team_size": None},
			"data_status": {"has_orders": False, "has_inventory": False, "has_customers": False, "has_products": False},
			"existing_connectors": [it.get("connector_type") for it in connectors_store.get(tenant_id, [])],
			"message": "OK",
		}


	@app.get("/v1/tenants/{tenant_id}/connectors/connected")
	def connectors_connected(tenant_id: str) -> Dict[str, Any]:
		# Try DB first
		backend = get_backend()
		if PostgresBackend is not None and backend is not None and isinstance(backend, PostgresBackend):  # type: ignore
			try:
				with backend.get_connection() as conn:  # type: ignore
					with conn.cursor() as cur:
						cur.execute(
							"""
							SELECT source_id, tenant_id, connector_type, name, status, last_sync, sync_frequency, extra_data
							  FROM data_sources
							 WHERE tenant_id = %s
							""",
							[tenant_id],
						)
						rows = cur.fetchall()
						items: List[Dict[str, Any]] = []
						for r in rows:
							(src_id, _t, ctype, name, status, last_sync, freq, extra) = r
							meta = extra or {}
							if isinstance(meta, str):
								try:
									meta = json.loads(meta)
								except Exception:
									meta = {}
							items.append({
								"connector_id": str(src_id),
								"connector_type": ctype,
								"connector_name": ctype,
								"display_name": name,
								"category": meta.get("category", "api"),
								"icon": meta.get("icon", "Plug"),
								"data_types": meta.get("data_types", []),
								"status": status or "inactive",
								"sync_frequency": freq or "manual",
								"last_sync": last_sync.isoformat() if last_sync else None,
								"metadata": meta,
							})
					return {"connectors": items, "total": len(items)}
			except Exception:
				pass
		# Fallback to in-memory
		items = connectors_store.get(tenant_id, [])
		return {"connectors": items, "total": len(items)}

	@app.get("/v1/tenants/{tenant_id}/connectors/readiness")
	def connector_readiness(tenant_id: str) -> Dict[str, Any]:
		"""Return connector data readiness for dashboards and narratives."""
		# Try DB first
		backend = get_backend()
		if PostgresBackend is not None and backend is not None and isinstance(backend, PostgresBackend):  # type: ignore
			try:
				with backend.get_connection() as conn:  # type: ignore
					with conn.cursor() as cur:
						cur.execute(
							"""
							SELECT source_id, name, last_sync, extra_data
							  FROM data_sources
							 WHERE tenant_id = %s
							""",
							[tenant_id],
						)
						rows = cur.fetchall()
						connectors: List[Dict[str, Any]] = []
						for r in rows:
							(src_id, name, last_sync, extra) = r
							meta = extra or {}
							if isinstance(meta, str):
								try:
									meta = json.loads(meta)
								except Exception:
									meta = {}
							connectors.append({
								"connector_id": str(src_id),
								"display_name": name,
								"datasets": meta.get("datasets", []),
								"last_refreshed": last_sync.isoformat() if last_sync else None,
								"counts": meta.get("last_record_count", {}),
								"total_records": meta.get("total_records", 0),
							})
					return {"connectors": connectors, "total": len(connectors)}
			except Exception:
				pass
		# Fallback to in-memory
		items = connectors_store.get(tenant_id, [])
		connectors = []
		for it in items:
			meta = it.get("metadata", {})
			connectors.append({
				"connector_id": it.get("connector_id"),
				"display_name": it.get("display_name"),
				"datasets": meta.get("datasets", []),
				"last_refreshed": it.get("last_sync"),
				"counts": meta.get("last_record_count", {}),
				"total_records": meta.get("total_records", 0),
			})
		return {"connectors": connectors, "total": len(connectors)}

	# Upload endpoint used by CSV quickstart
	@app.post("/api/connectors/upload_csv")
	async def upload_csv(
		file: UploadFile = File(...),
		connector_id: str = Form(...),
		tenant_id: str = Form(...),
	) -> Dict[str, Any]:
		import csv
		import io
		
		# Read file content
		content_bytes = b""
		record_count = 0
		headers: list[str] = []
		sample_rows: list[dict[str, Any]] = []
		
		try:
			content_bytes = await file.read()
			content_str = content_bytes.decode("utf-8")
			reader = csv.DictReader(io.StringIO(content_str))
			headers = list(reader.fieldnames or [])
			
			# Count rows and collect samples
			for i, row in enumerate(reader):
				record_count += 1
				if i < 3:  # Keep first 3 rows as samples
					sample_rows.append(dict(row))
		except Exception as e:
			# Fallback to simple byte-based estimate if CSV parsing fails
			record_count = max(1, len(content_bytes) // 200)
		
		file_size = len(content_bytes)
		datasets = [h.lower().replace(" ", "_") for h in headers] if headers else ["data"]
		
		# Update via repository when available
		if connector_repo is not None:
			try:
				connector_repo.update_sync_info(connector_id, total_records=record_count, duration=0.0)  # type: ignore
			except Exception:
				pass
		
		# Direct SQL: update data_sources.extra_data and insert raw ingestion record
		backend = get_backend()
		if PostgresBackend is not None and backend is not None and isinstance(backend, PostgresBackend):  # type: ignore
			try:
				with backend.get_connection() as conn:  # type: ignore
					with conn.cursor() as cur:
						# Update extra_data with datasets, counts, and timestamp
						cur.execute(
							"""
							UPDATE data_sources
							   SET last_sync = NOW(),
							       status = 'active',
							       extra_data = jsonb_set(
							           jsonb_set(
							               jsonb_set(
							                   COALESCE(extra_data, '{}'::jsonb),
							                   '{datasets}',
							                   %s::jsonb,
							                   true
							               ),
							               '{total_records}',
							               to_jsonb(COALESCE((extra_data->>'total_records')::int, 0) + %s),
							               true
							           ),
							           '{last_record_count}',
							           %s::jsonb,
							           true
							       )
							 WHERE source_id = %s AND tenant_id = %s
							""",
							[
								json.dumps(datasets),
								record_count,
								json.dumps({ds: record_count for ds in datasets}),
								connector_id,
								tenant_id,
							],
						)
						
						# Insert raw ingestion record
						raw_id = str(uuid.uuid4())
						event_payload = {
							"filename": file.filename or "upload.csv",
							"bytes": file_size,
							"record_count": record_count,
							"headers": headers,
							"sample_rows": sample_rows,
						}
						cur.execute(
							"""
							INSERT INTO raw_connector_data (raw_id, tenant_id, source_id, source_type, source_record_id, data, ingested_at, processed)
							VALUES (%s, %s, %s, 'csv_upload', %s, %s, NOW(), false)
							""",
							[
								raw_id,
								tenant_id,
								connector_id,
								f"upload_{py_dt.datetime.now(py_dt.timezone.utc).strftime('%Y%m%d_%H%M%S')}",
								json.dumps(event_payload),
							],
						)
					conn.commit()
				return {"success": True, "bytes": file_size, "records": record_count, "datasets": datasets}
			except Exception as e:
				return {"success": False, "error": str(e)}
		
		# Fallback: update in-memory if present
		for it in connectors_store.get(tenant_id, []):
			if it.get("connector_id") == connector_id:
				it["last_sync"] = datetime.now(timezone.utc).isoformat()
				it.setdefault("metadata", {})["total_records"] = (it.get("metadata", {}).get("total_records") or 0) + record_count
				break
		return {"success": True, "bytes": file_size, "records": record_count, "datasets": datasets}


	# --- Analytics events sink (no-op) ---
	@app.get("/v1/marketplace/connectors")
	def marketplace_connectors(category: Optional[str] = Query(default=None), tier: Optional[str] = Query(default=None), search: Optional[str] = Query(default=None)) -> Dict[str, Any]:
		"""Return marketplace catalog from package when available; otherwise fallback minimal list."""
		if marketplace is not None:
			try:
				items = marketplace.get_all()
				if category:
					items = [c for c in items if (c.get("category") == category) or (hasattr(c.get("category"), "value") and c.get("category").value == category)]
				if tier:
					items = [c for c in items if (c.get("tier") == tier) or (hasattr(c.get("tier"), "value") and c.get("tier").value == tier)]
				if search:
					s = search.lower()
					items = [c for c in items if s in (c.get("displayName", "") + " " + c.get("description", "")).lower()]
				return {"connectors": items, "total": len(items), "categories": [], "tiers": ["free", "standard", "premium", "enterprise"]}
			except Exception:
				pass
		# Fallback - comprehensive catalog
		catalog = [
			{
				"id": "csv_upload",
				"name": "csv_upload",
				"display_name": "CSV/Excel Upload",
				"category": "storage",
				"description": "Upload spreadsheet data to get started quickly.",
				"icon": "FileSpreadsheet",
				"data_types": ["orders", "inventory", "customers"],
				"auth_type": "none",
				"tier": "free",
				"popular": True,
				"verified": True,
				"region": "global",
				"documentation_url": None,
				"setup_complexity": "low",
				"sync_realtime": False,
				"supports_mcp": True,
				"features": ["Simple upload", "URL fetch"],
				"limitations": ["Manual updates unless URL is provided"],
				"config_fields": [],
			},
			{
				"id": "salesforce",
				"name": "salesforce",
				"display_name": "Salesforce",
				"category": "crm",
				"description": "World's #1 CRM. Sync leads, opportunities, accounts, and sales pipeline data.",
				"icon": "Users",
				"data_types": ["contacts", "deals", "customers", "analytics"],
				"auth_type": "oauth2",
				"tier": "premium",
				"popular": True,
				"verified": True,
				"region": "Global",
				"setup_complexity": "medium",
				"sync_realtime": True,
				"supports_mcp": True,
				"features": ["Lead tracking", "Sales forecasting", "Account management"],
				"limitations": ["API rate limits apply"],
				"config_fields": [
					{
						"name": "connection_name",
						"label": "Connection Name",
						"type": "text",
						"required": True,
						"placeholder": "e.g., Production Salesforce, Sales Team CRM",
						"helper": "A friendly name to identify this connection"
					},
					{
						"name": "instance_url",
						"label": "Salesforce Instance URL",
						"type": "text",
						"required": True,
						"placeholder": "https://yourcompany.my.salesforce.com",
						"helper": "Your Salesforce instance URL (including https://)"
					},
					{
						"name": "username",
						"label": "Username",
						"type": "text",
						"required": True,
						"placeholder": "user@company.com",
						"helper": "Your Salesforce username (email)"
					},
					{
						"name": "password",
						"label": "Password",
						"type": "password",
						"required": True,
						"placeholder": "Enter your Salesforce password",
						"helper": "Your Salesforce password"
					},
					{
						"name": "security_token",
						"label": "Security Token",
						"type": "password",
						"required": True,
						"placeholder": "Security token from email",
						"helper": "Reset your security token in Salesforce: Setup → Personal Setup → My Personal Information → Reset Security Token"
					},
					{
						"name": "client_id",
						"label": "Consumer Key (Client ID)",
						"type": "text",
						"required": True,
						"placeholder": "3MVG9...",
						"helper": "From your Salesforce Connected App"
					},
					{
						"name": "client_secret",
						"label": "Consumer Secret (Client Secret)",
						"type": "password",
						"required": True,
						"placeholder": "Enter consumer secret",
						"helper": "From your Salesforce Connected App"
					}
				],
			},
			{
				"id": "shopify",
				"name": "shopify",
				"display_name": "Shopify",
				"category": "ecommerce",
				"description": "Connect your Shopify store to sync orders, inventory, products, and customers.",
				"icon": "ShoppingCart",
				"data_types": ["orders", "inventory", "customers", "products", "sales"],
				"auth_type": "oauth2",
				"tier": "free",
				"popular": True,
				"verified": True,
				"region": "Global",
				"setup_complexity": "easy",
				"sync_realtime": True,
				"supports_mcp": False,
				"features": ["Real-time sync", "Multi-location", "Customer profiles"],
				"limitations": ["API rate limit: 2 req/sec"],
				"config_fields": [],
			},
			{
				"id": "quickbooks",
				"name": "quickbooks",
				"display_name": "QuickBooks Online",
				"category": "finance",
				"description": "Sync invoices, expenses, customers, and financial data from QuickBooks.",
				"icon": "FileText",
				"data_types": ["invoices", "expenses", "customers", "payments"],
				"auth_type": "oauth2",
				"tier": "free",
				"popular": True,
				"verified": True,
				"region": "Global",
				"setup_complexity": "easy",
				"sync_realtime": False,
				"supports_mcp": False,
				"features": ["Invoice sync", "Expense tracking", "Financial reports"],
				"limitations": [],
				"config_fields": [],
			},
			{
				"id": "stripe",
				"name": "stripe",
				"display_name": "Stripe",
				"category": "finance",
				"description": "Accept payments and manage subscriptions. Sync charges, payouts, customers.",
				"icon": "CreditCard",
				"data_types": ["payments", "payouts", "customers", "subscriptions"],
				"auth_type": "api_key",
				"tier": "free",
				"popular": True,
				"verified": True,
				"region": "Global",
				"setup_complexity": "easy",
				"sync_realtime": False,
				"supports_mcp": False,
				"features": ["Charges", "Payouts", "Customers"],
				"limitations": [],
				"config_fields": [
					{
						"name": "api_key",
						"label": "Secret API Key",
						"type": "password",
						"required": True,
						"placeholder": "sk_live_...",
						"helper": "Create a restricted API key in your Stripe Dashboard"
					}
				],
			},
			{
				"id": "hubspot",
				"name": "hubspot",
				"display_name": "HubSpot",
				"category": "crm",
				"description": "Popular CRM for SMB. Sync contacts, companies, deals, and activities.",
				"icon": "Users",
				"data_types": ["contacts", "companies", "deals", "activities"],
				"auth_type": "token",
				"tier": "free",
				"popular": True,
				"verified": True,
				"region": "Global",
				"setup_complexity": "easy",
				"sync_realtime": False,
				"supports_mcp": False,
				"features": ["Contacts", "Deals", "Companies"],
				"limitations": [],
				"config_fields": [
					{
						"name": "private_app_token",
						"label": "Private App Token",
						"type": "password",
						"required": True,
						"placeholder": "pat-xxx-...",
						"helper": "Create a Private App token in HubSpot and paste it here"
					}
				],
			},
			{
				"id": "woocommerce",
				"name": "woocommerce",
				"display_name": "WooCommerce",
				"category": "ecommerce",
				"description": "Connect your WooCommerce store. Sync orders, products, customers, inventory.",
				"icon": "ShoppingCart",
				"data_types": ["orders", "products", "customers", "inventory"],
				"auth_type": "api_key",
				"tier": "free",
				"popular": True,
				"verified": True,
				"region": "Global",
				"setup_complexity": "easy",
				"sync_realtime": False,
				"supports_mcp": False,
				"features": ["Orders", "Products", "Customers"],
				"limitations": ["Requires REST API enabled on site"],
				"config_fields": [
					{
						"name": "site_url",
						"label": "Site URL",
						"type": "text",
						"required": True,
						"placeholder": "https://shop.example.com",
						"helper": "Your WooCommerce site base URL"
					},
					{
						"name": "consumer_key",
						"label": "Consumer Key",
						"type": "text",
						"required": True,
						"placeholder": "ck_...",
						"helper": "Generate keys in WooCommerce → Settings → Advanced → REST API"
					},
					{
						"name": "consumer_secret",
						"label": "Consumer Secret",
						"type": "password",
						"required": True,
						"placeholder": "cs_...",
						"helper": "Generate keys in WooCommerce → Settings → Advanced → REST API"
					}
				],
			},
			{
				"id": "square",
				"name": "square",
				"display_name": "Square POS",
				"category": "pos",
				"description": "Modern point-of-sale system. Sync transactions, inventory, and customer data.",
				"icon": "CreditCard",
				"data_types": ["sales", "inventory", "customers", "payments"],
				"auth_type": "oauth2",
				"tier": "free",
				"popular": True,
				"verified": True,
				"region": "US, CA, UK",
				"setup_complexity": "easy",
				"sync_realtime": True,
				"features": ["Transaction tracking", "Inventory management", "Customer profiles"],
				"limitations": [],
				"config_fields": [],
			},
			{
				"id": "xero",
				"name": "xero",
				"display_name": "Xero Accounting",
				"category": "finance",
				"description": "UK-favourite accounting. Sync invoices, payments, contacts, chart of accounts.",
				"icon": "FileText",
				"data_types": ["invoices", "expenses", "contacts", "payments"],
				"auth_type": "oauth2",
				"tier": "standard",
				"popular": True,
				"verified": True,
				"region": "UK, AU, NZ",
				"setup_complexity": "medium",
				"sync_realtime": False,
				"supports_mcp": False,
				"features": ["Invoices", "Contacts", "Bank reconciliation"],
				"limitations": [],
				"config_fields": [
					{"name": "client_id", "label": "Client ID", "type": "text", "required": True},
					{"name": "client_secret", "label": "Client Secret", "type": "password", "required": True},
					{"name": "tenant_id", "label": "Tenant ID (optional)", "type": "text", "required": False}
				],
			},
			{
				"id": "sage_business_cloud",
				"name": "sage_business_cloud",
				"display_name": "Sage Business Cloud Accounting",
				"category": "finance",
				"description": "Accounting for UK SMBs. Sync invoices, products, and contacts.",
				"icon": "FileText",
				"data_types": ["invoices", "products", "contacts"],
				"auth_type": "token",
				"tier": "standard",
				"popular": True,
				"verified": True,
				"region": "UK",
				"setup_complexity": "medium",
				"sync_realtime": False,
				"supports_mcp": False,
				"features": ["Invoices", "Products", "Contacts"],
				"limitations": [],
				"config_fields": [
					{"name": "api_token", "label": "API Token", "type": "password", "required": True}
				],
			},
			{
				"id": "zettle",
				"name": "zettle",
				"display_name": "Zettle by PayPal",
				"category": "pos",
				"description": "Popular UK POS. Sync sales, products and inventory.",
				"icon": "CreditCard",
				"data_types": ["sales", "products", "inventory"],
				"auth_type": "token",
				"tier": "free",
				"popular": True,
				"verified": True,
				"region": "UK, EU",
				"setup_complexity": "easy",
				"sync_realtime": False,
				"supports_mcp": False,
				"features": ["Sales", "Products", "Inventory"],
				"limitations": [],
				"config_fields": [
					{"name": "access_token", "label": "Access Token", "type": "password", "required": True}
				],
			},
			{
				"id": "lightspeed",
				"name": "lightspeed",
				"display_name": "Lightspeed POS",
				"category": "pos",
				"description": "Retail/restaurant POS. Sync sales, products, and stock.",
				"icon": "CreditCard",
				"data_types": ["sales", "products", "inventory"],
				"auth_type": "oauth2",
				"tier": "standard",
				"popular": True,
				"verified": True,
				"region": "Global",
				"setup_complexity": "medium",
				"sync_realtime": False,
				"supports_mcp": False,
				"features": ["Sales", "Products", "Stock"],
				"limitations": [],
				"config_fields": [
					{"name": "client_id", "label": "Client ID", "type": "text", "required": True},
					{"name": "client_secret", "label": "Client Secret", "type": "password", "required": True}
				],
			},
			{
				"id": "deliveroo",
				"name": "deliveroo",
				"display_name": "Deliveroo",
				"category": "restaurants",
				"description": "Delivery platform. Sync orders and payouts.",
				"icon": "ShoppingCart",
				"data_types": ["orders", "payouts"],
				"auth_type": "token",
				"tier": "free",
				"popular": True,
				"verified": False,
				"region": "UK",
				"setup_complexity": "easy",
				"sync_realtime": False,
				"supports_mcp": False,
				"features": ["Orders", "Payouts"],
				"limitations": [],
				"config_fields": [
					{"name": "api_key", "label": "API Key", "type": "password", "required": True}
				],
			},
			{
				"id": "uber_eats",
				"name": "uber_eats",
				"display_name": "Uber Eats",
				"category": "restaurants",
				"description": "Food delivery. Sync orders and payments.",
				"icon": "ShoppingCart",
				"data_types": ["orders", "payments"],
				"auth_type": "token",
				"tier": "free",
				"popular": True,
				"verified": False,
				"region": "UK",
				"setup_complexity": "easy",
				"sync_realtime": False,
				"supports_mcp": False,
				"features": ["Orders", "Payments"],
				"limitations": [],
				"config_fields": [
					{"name": "api_key", "label": "API Key", "type": "password", "required": True}
				],
			},
			{
				"id": "just_eat",
				"name": "just_eat",
				"display_name": "Just Eat",
				"category": "restaurants",
				"description": "UK takeaway platform. Sync orders and payouts.",
				"icon": "ShoppingCart",
				"data_types": ["orders", "payouts"],
				"auth_type": "token",
				"tier": "free",
				"popular": True,
				"verified": False,
				"region": "UK",
				"setup_complexity": "easy",
				"sync_realtime": False,
				"supports_mcp": False,
				"features": ["Orders", "Payouts"],
				"limitations": [],
				"config_fields": [
					{"name": "api_key", "label": "API Key", "type": "password", "required": True}
				],
			},
			{
				"id": "bigcommerce",
				"name": "bigcommerce",
				"display_name": "BigCommerce",
				"category": "ecommerce",
				"description": "E-commerce platform. Sync orders, products, customers.",
				"icon": "ShoppingCart",
				"data_types": ["orders", "products", "customers"],
				"auth_type": "oauth2",
				"tier": "standard",
				"popular": True,
				"verified": True,
				"region": "Global",
				"setup_complexity": "medium",
				"sync_realtime": False,
				"supports_mcp": False,
				"features": ["Orders", "Products", "Customers"],
				"limitations": [],
				"config_fields": [
					{"name": "client_id", "label": "Client ID", "type": "text", "required": True},
					{"name": "client_secret", "label": "Client Secret", "type": "password", "required": True}
				],
			},
			{
				"id": "ebay",
				"name": "ebay",
				"display_name": "eBay Seller",
				"category": "ecommerce",
				"description": "Sell on eBay. Sync orders, listings, and payouts.",
				"icon": "ShoppingCart",
				"data_types": ["orders", "listings", "payouts"],
				"auth_type": "oauth2",
				"tier": "standard",
				"popular": True,
				"verified": True,
				"region": "Global",
				"setup_complexity": "medium",
				"sync_realtime": False,
				"supports_mcp": False,
				"features": ["Orders", "Listings", "Payouts"],
				"limitations": [],
				"config_fields": [
					{"name": "client_id", "label": "Client ID", "type": "text", "required": True},
					{"name": "client_secret", "label": "Client Secret", "type": "password", "required": True}
				],
			},
			{
				"id": "amazon_seller",
				"name": "amazon_seller",
				"display_name": "Amazon Seller Central",
				"category": "ecommerce",
				"description": "Marketplace sales. Sync orders, listings, and settlements.",
				"icon": "ShoppingCart",
				"data_types": ["orders", "listings", "settlements"],
				"auth_type": "token",
				"tier": "standard",
				"popular": True,
				"verified": True,
				"region": "Global",
				"setup_complexity": "medium",
				"sync_realtime": False,
				"supports_mcp": False,
				"features": ["Orders", "Listings", "Settlements"],
				"limitations": [],
				"config_fields": [
					{"name": "refresh_token", "label": "Refresh Token", "type": "password", "required": True}
				],
			},
			{
				"id": "mailchimp",
				"name": "mailchimp",
				"display_name": "Mailchimp",
				"category": "marketing",
				"description": "Email marketing. Sync audiences and campaign metrics.",
				"icon": "Mail",
				"data_types": ["audiences", "campaigns", "metrics"],
				"auth_type": "token",
				"tier": "free",
				"popular": True,
				"verified": True,
				"region": "Global",
				"setup_complexity": "easy",
				"sync_realtime": False,
				"supports_mcp": False,
				"features": ["Audiences", "Campaigns", "Metrics"],
				"limitations": [],
				"config_fields": [
					{"name": "api_key", "label": "API Key", "type": "password", "required": True}
				],
			},
			{
				"id": "pipedrive",
				"name": "pipedrive",
				"display_name": "Pipedrive",
				"category": "crm",
				"description": "SMB CRM. Sync contacts, deals, organizations.",
				"icon": "Users",
				"data_types": ["contacts", "deals", "organizations"],
				"auth_type": "token",
				"tier": "free",
				"popular": True,
				"verified": True,
				"region": "Global",
				"setup_complexity": "easy",
				"sync_realtime": False,
				"supports_mcp": False,
				"features": ["Contacts", "Deals", "Organizations"],
				"limitations": [],
				"config_fields": [
					{"name": "api_token", "label": "API Token", "type": "password", "required": True}
				],
			},
		]
		filtered = catalog
		if category:
			filtered = [c for c in filtered if c.get("category") == category]
		if tier:
			filtered = [c for c in filtered if c.get("tier") == tier]
		if search:
			s = search.lower()
			filtered = [c for c in filtered if s in (c.get("displayName", "") + " " + c.get("description", "")).lower()]
		return {"connectors": filtered, "total": len(filtered), "categories": ["storage"], "tiers": ["free", "standard", "premium", "enterprise"]}

	@app.get("/v1/marketplace/starter-packs")
	def marketplace_starter_packs() -> Dict[str, Any]:
		"""Return curated starter packs for quick setup flows."""
		packs = [
			{
				"id": "restaurants_starter",
				"title": "Restaurant Starter Pack",
				"description": "Core tools for UK restaurants: POS + delivery platforms + accounting.",
				"category": "restaurants",
				"connectors": [
					{"id": "lightspeed", "required": False},
					{"id": "square", "required": False},
					{"id": "deliveroo", "required": False},
					{"id": "uber_eats", "required": False},
					{"id": "just_eat", "required": False},
					{"id": "xero", "required": False},
					{"id": "sage_business_cloud", "required": False},
				],
				"notes": "Pick your POS and delivery partners; choose either Xero or Sage for accounting.",
			},
			{
				"id": "ecommerce_starter",
				"title": "E‑commerce Starter Pack",
				"description": "Online store essentials: storefront + marketplace + email + accounting.",
				"category": "ecommerce",
				"connectors": [
					{"id": "shopify", "required": False},
					{"id": "woocommerce", "required": False},
					{"id": "bigcommerce", "required": False},
					{"id": "ebay", "required": False},
					{"id": "amazon_seller", "required": False},
					{"id": "mailchimp", "required": False},
					{"id": "quickbooks", "required": False},
					{"id": "xero", "required": False},
				],
				"notes": "Pick one storefront; connect marketplaces you use; add email and accounting.",
			},
		]
		return {"packs": packs, "total": len(packs)}

	# --- Coach recommendations (for dashboard/coach pages) ---
	@app.get("/v1/tenants/{tenant_id}/coach/recommendations")
	def get_coach_recommendations(tenant_id: str) -> List[Dict[str, Any]]:
		dismissed = coach_dismissed_store.get(tenant_id, set())
		# Check data-source to decide if we should push a connect-data CTA
		ds = get_data_source_summary(tenant_id)
		recs: List[Dict[str, Any]] = []
		if not ds.get("hasRealData"):
			recs.append({
				"id": "rec-connect-data",
				"priority": "important",
				"title": "Connect your business data",
				"description": "Upload a recent CSV or connect a system to unlock insights.",
				"actions": [
					{"id": "go-connectors", "label": "Open connectors", "buttonText": "Connect now", "variant": "primary"},
				],
				"dismissible": True,
				"dismissed": False,
				"createdAt": datetime.now(timezone.utc).isoformat(),
				"generatedAt": datetime.now(timezone.utc).isoformat(),
				"metadata": {},
			})
		# Always include a goals review suggestion
		recs.append({
			"id": "rec-review-goals",
			"priority": "suggestion",
			"title": "Review weekly goal progression",
			"description": "Check on your revenue and inventory goals and adjust targets if needed.",
			"actions": [
				{"id": "open-goals", "label": "View goals", "buttonText": "Review", "variant": "subtle"},
			],
			"dismissible": True,
			"dismissed": False,
			"createdAt": datetime.now(timezone.utc).isoformat(),
			"generatedAt": datetime.now(timezone.utc).isoformat(),
			"metadata": {},
		})
		return [r for r in recs if r["id"] not in dismissed]

	@app.post("/v1/tenants/{tenant_id}/coach/recommendations/{rec_id}/dismiss")
	def dismiss_recommendation(tenant_id: str, rec_id: str) -> Dict[str, Any]:
		coach_dismissed_store.setdefault(tenant_id, set()).add(rec_id)
		return {"success": True}

	@app.post("/v1/tenants/{tenant_id}/coach/recommendations/{rec_id}/feedback")
	def recommendation_feedback(tenant_id: str, rec_id: str, payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
		_feedback_id = f"fb-{int(datetime.now().timestamp()*1000)}"
		return {"success": True, "feedback_id": _feedback_id}

	# --- Auth endpoints (guarded, minimal UX support) ---
	@app.get("/v1/auth/providers")
	def auth_providers() -> Dict[str, Any]:
		return {
			"enabled_providers": [],  # No OAuth providers enabled in stub mode
			"providers": {
				"google": {
					"name": "Google",
					"description": "Sign in with Google",
					"icon": "google",
					"color": "#4285F4"
				},
				"microsoft": {
					"name": "Microsoft",
					"description": "Sign in with Microsoft",
					"icon": "microsoft",
					"color": "#00A4EF"
				}
			}
		}

	@app.post("/v1/auth/signup")
	def auth_signup(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
		# Accept email/name and return a verification token the UI will exchange at /v1/auth/verify
		email = payload.get("email") or "demo@example.com"
		return {"token": f"verify-{int(datetime.now().timestamp()*1000)}", "email": email}

	@app.post("/v1/auth/login")
	def auth_login(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
		# For passwordless flows this mirrors signup
		email = payload.get("email") or "demo@example.com"
		return {"token": f"verify-{int(datetime.now().timestamp()*1000)}", "email": email}

	@app.post("/v1/auth/login-password")
	def auth_login_password(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
		# Minimal password login: issue a demo JWT; no password validation in stub
		email = payload.get("email") or "demo@example.com"
		full_name = payload.get("full_name") or payload.get("name") or "Demo User"
		tenant_id = payload.get("tenant_id") or "demo"
		try:
			import jwt as pyjwt  # type: ignore
			secret = os.getenv("ACCOUNTS_JWT_SECRET", "dyocense-dev-secret")
			claims = {"sub": email, "name": full_name, "tid": tenant_id, "iss": "dyocense-accounts"}
			jwt_token = pyjwt.encode(claims, secret, algorithm="HS256")  # type: ignore
			return {"jwt": jwt_token, "tenant_id": tenant_id, "user": {"user_id": "user-1", "email": email, "full_name": full_name, "name": full_name}}
		except Exception:
			return {"jwt": "demo-jwt", "tenant_id": tenant_id, "user": {"user_id": "user-1", "email": email, "full_name": full_name, "name": full_name}}

	@app.post("/v1/auth/verify")
	def auth_verify(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
		"""Exchange a magic-link token for a JWT and ensure a tenant exists.

		If the accounts repository and Postgres are available, create a FREE plan tenant
		for the provided email/name. Otherwise, return a demo JWT and demo tenant.
		"""
		email = payload.get("email") or "demo@example.com"
		full_name = payload.get("full_name") or payload.get("name") or "Demo User"
		business_name = payload.get("business_name") or "Demo SMB"
		tenant_id = "demo"
		jwt_token = "demo-jwt"
		
		print(f"[AUTH VERIFY] Starting auth verification for email={email}, business={business_name}")
		
		try:
			from packages.kernel_common.persistence_v2 import PostgresBackend as _PB  # type: ignore
			from packages.accounts.repository import register_tenant, PlanTier  # type: ignore
			backend = get_backend()
			
			print(f"[AUTH VERIFY] Backend type: {type(backend)}, is PostgresBackend: {isinstance(backend, _PB) if _PB and backend else False}")
			
			if backend is not None and _PB is not None and isinstance(backend, _PB):  # type: ignore
				print(f"[AUTH VERIFY] Registering tenant for {business_name}")
				tenant = register_tenant(business_name, email, PlanTier.FREE)  # type: ignore
				tenant_id = getattr(tenant, "tenant_id", "demo")  # type: ignore
				print(f"[AUTH VERIFY] Tenant registered successfully: {tenant_id}")
				
				import jwt as pyjwt  # type: ignore
				secret = os.getenv("ACCOUNTS_JWT_SECRET", "dyocense-dev-secret")
				claims = {"sub": email, "name": full_name, "tid": tenant_id, "iss": "dyocense-accounts"}
				jwt_token = pyjwt.encode(claims, secret, algorithm="HS256")  # type: ignore
				print(f"[AUTH VERIFY] JWT generated for tenant: {tenant_id}")
			else:
				print(f"[AUTH VERIFY] Falling back to demo tenant (backend not available or not Postgres)")
		except Exception as e:
			# Log the error for debugging
			print(f"[AUTH VERIFY] ERROR: {e}")
			import traceback
			traceback.print_exc()
			pass
		
		print(f"[AUTH VERIFY] Returning tenant_id={tenant_id}, jwt={jwt_token[:20]}...")
		return {"jwt": jwt_token, "tenant_id": tenant_id, "user": {"user_id": "user-1", "email": email, "full_name": full_name, "name": full_name}}

	@app.get("/v1/auth/{provider}/callback")
	def auth_callback(provider: str, code: Optional[str] = Query(default=None)) -> Dict[str, Any]:
		# OAuth callback stub
		return {"jwt": "demo-jwt", "tenant_id": "demo", "user": {"user_id": "user-1", "email": "demo@example.com", "full_name": "Demo User", "name": "Demo User"}}

	return app


app = create_app()


if __name__ == "__main__":
	import uvicorn

	host = os.getenv("HOST", "127.0.0.1")
	port = int(os.getenv("PORT", "8001"))
	uvicorn.run("backend.main:app", host=host, port=port, reload=False)
