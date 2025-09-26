"""FastAPI application for the Plan service."""
from __future__ import annotations

import logging
from functools import lru_cache
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, status

from services.common import (
    BearerAuthMiddleware,
    KernelClientError,
    context,
    tracing,
    noop_decoder,
    get_mongo_collection,
)

from .config import get_settings
from .gateway import KernelGateway
from .schemas import (
    PlanCreateRequest,
    PlanEvidenceResponse,
    PlanListItem,
    PlanResponse,
    PlanStepsResponse,
)
from .storage import PlanRepository

logger = logging.getLogger(__name__)

app = FastAPI(title="Dyocense Plan Service", version="0.1.0")
app.add_middleware(BearerAuthMiddleware, decoder=noop_decoder)

_repository_singleton: Optional[PlanRepository] = None


@lru_cache()
def _gateway_singleton() -> KernelGateway:
    return KernelGateway()


def get_repository() -> PlanRepository:
    global _repository_singleton
    if _repository_singleton is not None:
        return _repository_singleton
    settings = get_settings()
    if not settings.mongo_uri:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PLAN_MONGO_URI is not configured.",
        )
    try:
        collection = get_mongo_collection(
            settings.mongo_uri,
            settings.mongo_db,
            settings.mongo_collection,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    _repository_singleton = PlanRepository(collection)
    return _repository_singleton


def get_gateway() -> KernelGateway:
    try:
        return _gateway_singleton()
    except RuntimeError as exc:  # Missing configuration
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc


@app.get("/health", tags=["health"])
def health() -> dict:
    settings = get_settings()
    return {
        "status": "ok",
        "kernel_base_url": settings.kernel_base_url,
    }


@app.post("/plans", response_model=PlanResponse, status_code=status.HTTP_201_CREATED, tags=["plans"])
async def create_plan(
    request: PlanCreateRequest,
    repository: PlanRepository = Depends(get_repository),
    gateway: KernelGateway = Depends(get_gateway),
) -> PlanResponse:
    tenant = context.get_tenant()
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing tenant context")

    kernel_payload = dict(request.kernel_payload)
    kernel_payload.setdefault("tenant_id", tenant.tenant_id)
    if tenant.tier and "tier" not in kernel_payload:
        kernel_payload["tier"] = tenant.tier

    with tracing.start_span("plan.create", {"tenant_id": tenant.tenant_id}):
        try:
            result = gateway.run_pipeline(kernel_payload)
        except KernelClientError as exc:
            logger.exception("Kernel pipeline call failed")
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    record = repository.create(
        tenant_id=tenant.tenant_id,
        goal_id=request.goal_id,
        variant=request.variant,
        request_payload=kernel_payload,
        result=result,
    )
    return PlanResponse.from_record(record)


@app.get("/plans", response_model=List[PlanListItem], tags=["plans"])
async def list_plans(
    repository: PlanRepository = Depends(get_repository),
) -> List[PlanListItem]:
    tenant = context.get_tenant()
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing tenant context")
    records = list(repository.list(tenant.tenant_id))
    return [PlanListItem.from_record(record) for record in records]


@app.get("/plans/{plan_id}", response_model=PlanResponse, tags=["plans"])
async def get_plan(
    plan_id: str,
    repository: PlanRepository = Depends(get_repository),
) -> PlanResponse:
    tenant = context.get_tenant()
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing tenant context")
    record = repository.get(tenant.tenant_id, plan_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    return PlanResponse.from_record(record)


@app.get("/plans/{plan_id}/steps", response_model=PlanStepsResponse, tags=["plans"])
async def get_plan_steps(
    plan_id: str,
    repository: PlanRepository = Depends(get_repository),
) -> PlanStepsResponse:
    tenant = context.get_tenant()
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing tenant context")
    record = repository.get(tenant.tenant_id, plan_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    return PlanStepsResponse.from_record(record)


@app.get("/plans/{plan_id}/evidence", response_model=PlanEvidenceResponse, tags=["plans"])
async def get_plan_evidence(
    plan_id: str,
    repository: PlanRepository = Depends(get_repository),
) -> PlanEvidenceResponse:
    tenant = context.get_tenant()
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing tenant context")
    record = repository.get(tenant.tenant_id, plan_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    return PlanEvidenceResponse.from_record(record)
