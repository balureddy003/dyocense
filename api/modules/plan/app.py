"""FastAPI application for the Plan service."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from functools import lru_cache
from typing import Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException, status

from api.common import (
    BearerAuthMiddleware,
    KernelClientError,
    context,
    tracing,
    noop_decoder,
    get_mongo_collection,
)

from api.modules.llm_router.service import router_service

from .config import get_settings
from .gateway import KernelGateway
from .schemas import (
    PlanChatRequest,
    PlanChatResponse,
    PlanCreateRequest,
    PlanCounterfactualRequest,
    PlanDeltaRequest,
    PlanEvidenceResponse,
    PlanListItem,
    PlanResponse,
    PlanStepsResponse,
)
from .storage import ChatTranscriptRepository, PlanRepository

logger = logging.getLogger(__name__)

app = FastAPI(title="Dyocense Plan Service", version="0.1.0")
app.add_middleware(BearerAuthMiddleware, decoder=noop_decoder)

_repository_singleton: Optional[PlanRepository] = None
_chat_repository_singleton: Optional[ChatTranscriptRepository] = None


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


def get_chat_repository() -> ChatTranscriptRepository:
    global _chat_repository_singleton
    if _chat_repository_singleton is not None:
        return _chat_repository_singleton
    settings = get_settings()
    if not settings.mongo_uri:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PLAN_MONGO_URI is not configured.",
        )
    collection = get_mongo_collection(
        settings.mongo_uri,
        settings.mongo_db,
        settings.chat_collection,
    )
    _chat_repository_singleton = ChatTranscriptRepository(collection)
    return _chat_repository_singleton


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
        parent_plan_id=None,
        request_payload=kernel_payload,
        result=result,
    )
    return PlanResponse.from_record(record)


@app.post("/plans/{plan_id}/delta", response_model=PlanResponse, status_code=status.HTTP_201_CREATED, tags=["plans"])
async def create_delta_plan(
    plan_id: str,
    request: PlanDeltaRequest,
    repository: PlanRepository = Depends(get_repository),
    gateway: KernelGateway = Depends(get_gateway),
) -> PlanResponse:
    tenant = context.get_tenant()
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing tenant context")

    baseline = repository.get(tenant.tenant_id, plan_id)
    if baseline is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Baseline plan not found")

    kernel_payload = _prepare_kernel_payload(baseline.request_payload, request.kernel_payload, tenant.tenant_id, tenant.tier)
    kernel_payload.setdefault("mode", "delta")

    with tracing.start_span("plan.delta", {"tenant_id": tenant.tenant_id, "parent_plan_id": plan_id}):
        try:
            result = gateway.run_pipeline(kernel_payload)
        except KernelClientError as exc:
            logger.exception("Kernel delta pipeline call failed")
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    variant = _compose_variant(baseline.variant, request.variant_suffix)
    record = repository.create(
        tenant_id=tenant.tenant_id,
        goal_id=request.goal_id or baseline.goal_id,
        variant=variant,
        parent_plan_id=baseline.plan_id,
        request_payload=kernel_payload,
        result=result,
    )
    return PlanResponse.from_record(record)


@app.post("/plans/{plan_id}/counterfactual", response_model=PlanResponse, status_code=status.HTTP_201_CREATED, tags=["plans"])
async def create_counterfactual_plan(
    plan_id: str,
    request: PlanCounterfactualRequest,
    repository: PlanRepository = Depends(get_repository),
    gateway: KernelGateway = Depends(get_gateway),
) -> PlanResponse:
    tenant = context.get_tenant()
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing tenant context")

    baseline = repository.get(tenant.tenant_id, plan_id)
    if baseline is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Baseline plan not found")

    kernel_payload = _prepare_kernel_payload(baseline.request_payload, request.kernel_payload, tenant.tenant_id, tenant.tier)
    kernel_payload.setdefault("mode", "counterfactual")

    with tracing.start_span("plan.counterfactual", {"tenant_id": tenant.tenant_id, "parent_plan_id": plan_id}):
        try:
            result = gateway.run_pipeline(kernel_payload)
        except KernelClientError as exc:
            logger.exception("Kernel counterfactual pipeline call failed")
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    variant = _compose_variant(baseline.variant, request.variant_suffix)
    record = repository.create(
        tenant_id=tenant.tenant_id,
        goal_id=request.goal_id or baseline.goal_id,
        variant=variant,
        parent_plan_id=baseline.plan_id,
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


@app.post("/chat/plan", response_model=PlanChatResponse, tags=["chat"])
async def chat_plan(
    request: PlanChatRequest,
    chat_repository: ChatTranscriptRepository = Depends(get_chat_repository),
) -> PlanChatResponse:
    tenant = context.get_tenant()
    tenant_id = tenant.tenant_id if tenant else request.tenant_id
    if tenant_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing tenant context")

    provider_id = request.provider_id or "openai"
    llm_payload = router_service.chat(provider_id=provider_id, prompt=request.goal)

    summary_prefix = (
        "Planning request captured. The assistant will translate this narrative goal"
        " into a Dyocense kernel payload (forecast → optiguide → optimizer → evidence)."
    )
    summary = f"{summary_prefix}\n\nGoal: {request.goal}\nContext: {request.context or 'n/a'}\nTenant: {tenant_id}"
    llm_response = llm_payload.get("message") or None

    timestamp = datetime.now(timezone.utc).isoformat()
    messages: List[Dict[str, object]] = [
        {
            "role": "user",
            "text": request.goal,
            "context": request.context,
            "timestamp": timestamp,
        },
        {
            "role": "assistant",
            "text": summary,
            "type": "plan_ack",
            "timestamp": timestamp,
        },
    ]
    if llm_response:
        messages.append(
            {
                "role": "assistant",
                "text": llm_response,
                "type": "llm_response",
                "provider_id": llm_payload.get("provider_id", provider_id),
                "timestamp": timestamp,
            }
        )

    transcript = chat_repository.create(
        tenant_id=tenant_id,
        provider_id=llm_payload.get("provider_id", provider_id),
        goal=request.goal,
        context=request.context,
        messages=messages,
    )

    return PlanChatResponse(
        summary=summary,
        llm_response=llm_response,
        provider_id=transcript.provider_id,
        conversation_id=transcript.conversation_id,
    )


def _prepare_kernel_payload(
    base_payload: Dict[str, object],
    overrides: Dict[str, object],
    tenant_id: str,
    tier: Optional[str],
) -> Dict[str, object]:
    payload: Dict[str, object] = dict(base_payload)
    payload.update(overrides)
    payload["tenant_id"] = tenant_id
    if tier:
        payload.setdefault("tier", tier)
    return payload


def _compose_variant(existing: Optional[str], suffix: Optional[str]) -> Optional[str]:
    if not suffix:
        return existing
    if existing:
        return f"{existing}-{suffix}"
    return suffix
