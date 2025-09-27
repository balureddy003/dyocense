"""Feedback service API."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException, status

from api.common import (
    BearerAuthMiddleware,
    KernelClient,
    KernelClientConfig,
    KernelClientError,
    context,
    get_mongo_collection,
    noop_decoder,
)

from .config import get_settings
from .scheduler_client import SchedulerClient, SchedulerClientConfig, SchedulerClientError
from .schemas import (
    DriftItem,
    DriftReport,
    FeedbackIngestRequest,
    FeedbackIngestResponse,
)
from .storage import FeedbackRepository

logger = logging.getLogger(__name__)

app = FastAPI(title="Dyocense Feedback Service", version="0.1.0")
app.add_middleware(BearerAuthMiddleware, decoder=noop_decoder)

_repository_singleton: Optional[FeedbackRepository] = None
_kernel_client_singleton: Optional[KernelClient] = None
_scheduler_client_singleton: Optional[SchedulerClient] = None


def get_repository() -> FeedbackRepository:
    global _repository_singleton
    if _repository_singleton:
        return _repository_singleton
    settings = get_settings()
    if not settings.mongo_uri:
        raise RuntimeError("FEEDBACK_MONGO_URI missing")
    collection = get_mongo_collection(settings.mongo_uri, settings.mongo_db, settings.collection)
    _repository_singleton = FeedbackRepository(collection)
    return _repository_singleton


def get_kernel_client() -> KernelClient:
    global _kernel_client_singleton
    if _kernel_client_singleton:
        return _kernel_client_singleton
    settings = get_settings()
    if not settings.kernel_base_url:
        raise RuntimeError("FEEDBACK_KERNEL_BASE_URL missing")
    config = KernelClientConfig(
        base_url=str(settings.kernel_base_url),
        timeout=settings.kernel_timeout,
        api_key=settings.kernel_api_key,
    )
    _kernel_client_singleton = KernelClient(config)
    return _kernel_client_singleton


def get_scheduler_client() -> Optional[SchedulerClient]:
    global _scheduler_client_singleton
    if _scheduler_client_singleton:
        return _scheduler_client_singleton
    settings = get_settings()
    if not settings.scheduler_url:
        return None
    _scheduler_client_singleton = SchedulerClient(
        SchedulerClientConfig(base_url=str(settings.scheduler_url), timeout=settings.scheduler_timeout)
    )
    return _scheduler_client_singleton


@app.get("/health", tags=["health"])
def health() -> Dict[str, object]:
    settings = get_settings()
    return {
        "status": "ok",
        "mongo": settings.mongo_uri,
        "kernel": settings.kernel_base_url,
        "scheduler": settings.scheduler_url,
    }


@app.post("/feedback/ingest", response_model=FeedbackIngestResponse, tags=["feedback"])
async def ingest_feedback(
    request: FeedbackIngestRequest,
    repository: FeedbackRepository = Depends(get_repository),
    kernel_client: KernelClient = Depends(get_kernel_client),
    scheduler_client: Optional[SchedulerClient] = Depends(get_scheduler_client),
) -> FeedbackIngestResponse:
    tenant = _require_tenant()
    actuals_payload = [actual.dict() for actual in request.actuals]

    # Persist actuals
    record = repository.insert_events(
        tenant_id=tenant.tenant_id,
        goal_id=request.goal_id,
        plan_id=request.plan_id,
        actuals=actuals_payload,
    )

    # Notify kernel forecast feedback endpoint
    feedback_payload = {
        "tenant_id": tenant.tenant_id,
        "goal_id": request.goal_id,
        "actuals": actuals_payload,
    }
    try:
        kernel_client.send_forecast_feedback(feedback_payload)
    except KernelClientError as exc:
        logger.exception("Failed to send forecast feedback to kernel")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    triggered_replan = False
    if scheduler_client:
        scheduler_payload = {
            "tenant_id": tenant.tenant_id,
            "tier": tenant.tier or "standard",
            "job_type": "replan",
            "payload": {
                "goal_id": request.goal_id,
                "plan_id": request.plan_id,
                "feedback_event_id": record.event_id,
            },
            "cost_estimate": {"solver_sec": 1.0},
        }
        try:
            scheduler_client.enqueue(scheduler_payload, token=tenant.tenant_id)
            triggered_replan = True
        except SchedulerClientError as exc:  # pragma: no cover - depends on scheduler availability
            logger.warning("Scheduler enqueue failed: %s", exc)

    return FeedbackIngestResponse(count=len(actuals_payload), triggered_replan=triggered_replan)


@app.get("/feedback/kpi-drift", response_model=DriftReport, tags=["feedback"])
async def kpi_drift(
    goal_id: Optional[str] = None,
    repository: FeedbackRepository = Depends(get_repository),
) -> DriftReport:
    tenant = _require_tenant()
    aggregates = repository.aggregate_drift(tenant.tenant_id, goal_id)
    items: List[DriftItem] = [
        DriftItem(
            sku=sku,
            count=data.get("count", 0),
            avg_quantity=data.get("avg_quantity", 0.0),
            last_period=data.get("last_period", ""),
            last_quantity=data.get("last_quantity", 0.0),
        )
        for sku, data in aggregates.items()
    ]
    return DriftReport(
        tenant_id=tenant.tenant_id,
        goal_id=goal_id,
        generated_at=datetime.now(timezone.utc),
        items=items,
    )


def _require_tenant():
    tenant = context.get_tenant()
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing tenant context")
    return tenant
