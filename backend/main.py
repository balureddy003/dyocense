from fastapi import FastAPI, Body
from fastapi.responses import JSONResponse
from typing import Any, Dict, List, Optional
import os
from datetime import datetime, timezone


def create_app() -> FastAPI:
	app = FastAPI(title="Dyocense Kernel (stub)", version="0.1.0")

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
		"""
		Return a minimal but realistic health score payload.
		This is a stub: in production, compute from metrics and goals.
		"""
		now = datetime.now(timezone.utc).isoformat()
		# Simple deterministic demo based on tenant_id length to avoid hardcoding
		base = 65 + (len(tenant_id) % 10)  # 65-74
		revenue = min(100, max(0, base + 5))
		operations = min(100, max(0, base - 10))
		customer = min(100, max(0, base + 2))
		trend = 2  # pretend it's up +2 vs prior period
		return {
			"score": round((revenue + operations + customer) / 3),
			"trend": trend,
			"breakdown": {
				"revenue": revenue,
				"operations": operations,
				"customer": customer,
				"revenue_available": True,
				"operations_available": True,
				"customer_available": True,
			},
			"last_updated": now,
			"period_days": 7,
		}

	@app.get("/v1/tenants/{tenant_id}/health-score/alerts")
	def get_health_alerts(tenant_id: str) -> List[Dict[str, Any]]:
		# Minimal illustrative alerts
		return [
			{
				"id": "alert-low-ops",
				"type": "critical",
				"title": "Operational efficiency is low",
				"description": "Order fulfillment times are trending above target.",
				"metric": "operations",
				"value": "SLA 92%",
				"threshold": ">= 95%",
			}
		]

	@app.get("/v1/tenants/{tenant_id}/health-score/signals")
	def get_health_signals(tenant_id: str) -> List[Dict[str, Any]]:
		# Minimal illustrative positive signals
		return [
			{
				"id": "signal-rev-growth",
				"type": "positive",
				"title": "Revenue up week-over-week",
				"description": "Last 7 days revenue grew +4% vs prior period.",
				"metric": "revenue",
				"value": "+4%",
			}
		]

	@app.get("/v1/tenants/{tenant_id}/metrics/snapshot")
	def get_metrics_snapshot(tenant_id: str) -> List[Dict[str, Any]]:
		"""
		Return a small set of metric snapshots for dashboard cards.
		The shape matches apps/smb/src/lib/api.ts MetricSnapshot.
		"""
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

	return app


app = create_app()


if __name__ == "__main__":
	import uvicorn

	host = os.getenv("HOST", "127.0.0.1")
	port = int(os.getenv("PORT", "8001"))
	uvicorn.run("backend.main:app", host=host, port=port, reload=False)
