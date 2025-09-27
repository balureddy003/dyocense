"""FastAPI application for Goal service."""
from __future__ import annotations

import logging
from functools import lru_cache
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
    tracing,
)

from .config import get_settings
from .plan_client import PlanClient, PlanClientConfig, PlanClientError
from .schemas import (
    GoalCreateRequest,
    GoalFeedbackRequest,
    GoalListItem,
    GoalResponse,
    GoalStatusRequest,
    GoalUpdateRequest,
    GoalValidationRequest,
    GoalValidationResponse,
    GoalVariantRequest,
)
from .storage import GoalRecord, GoalRepository

logger = logging.getLogger(__name__)

app = FastAPI(title="Dyocense Goal Service", version="0.1.0")
app.add_middleware(BearerAuthMiddleware, decoder=noop_decoder)

_repository_singleton: Optional[GoalRepository] = None
_kernel_client_singleton: Optional[KernelClient] = None
_plan_client_singleton: Optional[PlanClient] = None


def get_repository() -> GoalRepository:
    global _repository_singleton
    if _repository_singleton:
        return _repository_singleton
    settings = get_settings()
    if not settings.mongo_uri:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="GOAL_MONGO_URI missing")
    collection = get_mongo_collection(settings.mongo_uri, settings.mongo_db, settings.mongo_collection)
    _repository_singleton = GoalRepository(collection)
    return _repository_singleton


@lru_cache()
def get_kernel_client() -> KernelClient:
    settings = get_settings()
    if not settings.kernel_base_url:
        raise RuntimeError("GOAL_KERNEL_BASE_URL is not configured")
    config = KernelClientConfig(
        base_url=str(settings.kernel_base_url),
        timeout=settings.kernel_timeout,
        api_key=settings.kernel_api_key,
    )
    return KernelClient(config)


def get_plan_client() -> Optional[PlanClient]:
    settings = get_settings()
    if not settings.plan_service_url:
        return None
    return PlanClient(PlanClientConfig(base_url=str(settings.plan_service_url), timeout=settings.plan_timeout))


@app.get("/health", tags=["health"])
def health() -> Dict[str, object]:
    settings = get_settings()
    return {
        "status": "ok",
        "mongo": settings.mongo_uri,
        "kernel": settings.kernel_base_url,
        "plan_service": settings.plan_service_url,
    }


@app.post("/goals", response_model=GoalResponse, status_code=status.HTTP_201_CREATED, tags=["goals"])
async def create_goal(
    request: GoalCreateRequest,
    repository: GoalRepository = Depends(get_repository),
) -> GoalResponse:
    tenant = _ensure_tenant()
    with tracing.start_span("goal.create", {"tenant_id": tenant.tenant_id}):
        record = repository.create(
            tenant_id=tenant.tenant_id,
            name=request.name,
            goaldsl=request.goaldsl,
            context=request.context,
            variants=request.variants,
        )
    return _goal_response(record)


@app.get("/goals", response_model=List[GoalListItem], tags=["goals"])
async def list_goals(
    repository: GoalRepository = Depends(get_repository),
) -> List[GoalListItem]:
    tenant = _ensure_tenant()
    records = repository.list(tenant.tenant_id)
    return [GoalListItem(
        goal_id=record.goal_id,
        name=record.name,
        status=record.status,
        created_at=record.created_at,
        updated_at=record.updated_at,
    ) for record in records]


@app.get("/goals/{goal_id}", response_model=GoalResponse, tags=["goals"])
async def get_goal(goal_id: str, repository: GoalRepository = Depends(get_repository)) -> GoalResponse:
    tenant = _ensure_tenant()
    record = repository.get(tenant.tenant_id, goal_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
    return _goal_response(record)


@app.patch("/goals/{goal_id}", response_model=GoalResponse, tags=["goals"])
async def update_goal(
    goal_id: str,
    request: GoalUpdateRequest,
    repository: GoalRepository = Depends(get_repository),
) -> GoalResponse:
    tenant = _ensure_tenant()
    record = repository.update(
        tenant_id=tenant.tenant_id,
        goal_id=goal_id,
        name=request.name,
        goaldsl=request.goaldsl,
        context=request.context,
    )
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
    return _goal_response(record)


@app.post("/goals/{goal_id}/variants", response_model=GoalResponse, tags=["goals"])
async def add_variant(
    goal_id: str,
    request: GoalVariantRequest,
    repository: GoalRepository = Depends(get_repository),
) -> GoalResponse:
    tenant = _ensure_tenant()
    variant = {
        "name": request.name,
        "goaldsl": request.goaldsl or {},
        "context": request.context or {},
    }
    record = repository.add_variant(tenant.tenant_id, goal_id, variant)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
    return _goal_response(record)


@app.post("/goals/{goal_id}/validate", response_model=GoalValidationResponse, tags=["validation"])
async def validate_goal(
    goal_id: str,
    request: GoalValidationRequest,
    repository: GoalRepository = Depends(get_repository),
) -> GoalValidationResponse:
    tenant = _ensure_tenant()
    record = repository.get(tenant.tenant_id, goal_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
    goaldsl = request.goaldsl or record.goaldsl
    context_payload = request.context or record.context
    scenarios = request.scenarios or {"horizon": 0, "num_scenarios": 0, "skus": [], "scenarios": []}
    payload = {
        "tenant_id": tenant.tenant_id,
        "tier": tenant.tier,
        "goal_dsl": goaldsl,
        "context": context_payload,
        "scenarios": scenarios,
    }
    client = get_kernel_client()
    try:
        response = client.compile_model(payload)
    except KernelClientError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    policy_snapshot = response.get("policy_snapshot") or response.get("metadata", {}).get("policy_snapshot")
    allow = not policy_snapshot or policy_snapshot.get("allow", True)
    return GoalValidationResponse(allow=allow, policy_snapshot=policy_snapshot, metadata=response.get("metadata", {}))


@app.post("/goals/{goal_id}/status", response_model=GoalResponse, tags=["workflow"])
async def update_goal_status(
    goal_id: str,
    request: GoalStatusRequest,
    repository: GoalRepository = Depends(get_repository),
) -> GoalResponse:
    tenant = _ensure_tenant()
    record = repository.update_status(tenant.tenant_id, goal_id, request.status, note=request.note)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
    if request.status.upper() == "READY_TO_PLAN":
        _trigger_plan_creation(record, tenant_token=tenant.tenant_id)
    return _goal_response(record)


@app.post("/goals/{goal_id}/feedback", response_model=GoalResponse, tags=["feedback"])
async def add_feedback(
    goal_id: str,
    request: GoalFeedbackRequest,
    repository: GoalRepository = Depends(get_repository),
) -> GoalResponse:
    tenant = _ensure_tenant()
    record = repository.add_feedback(
        tenant_id=tenant.tenant_id,
        goal_id=goal_id,
        feedback={"actuals": request.actuals, "note": request.note},
    )
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
    _trigger_plan_creation(record, tenant_token=tenant.tenant_id)
    return _goal_response(record)


def _goal_response(record: GoalRecord) -> GoalResponse:
    return GoalResponse(
        goal_id=record.goal_id,
        name=record.name,
        goaldsl=record.goaldsl,
        context=record.context,
        variants=record.variants,
        status=record.status,
        approvals=record.approvals,
        feedback=record.feedback,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def _trigger_plan_creation(record: GoalRecord, tenant_token: str) -> None:
    plan_client = get_plan_client()
    if not plan_client:
        logger.info("Plan service URL not configured; skipping plan creation for goal %s", record.goal_id)
        return
    payload = {
        "goal_id": record.goal_id,
        "variant": "auto",
        "kernel_payload": {
            "goaldsl": record.goaldsl,
            "context": record.context,
        },
    }
    try:
        plan_client.create_plan(payload, token=tenant_token)
    except PlanClientError as exc:
        logger.exception("Failed to trigger plan for goal %s", record.goal_id)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc


def _ensure_tenant():
    tenant = context.get_tenant()
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing tenant context")
    return tenant
