"""Scheduler service API."""
from __future__ import annotations

import logging
from typing import Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException, status

from api.common import BearerAuthMiddleware, context, get_mongo_collection, noop_decoder

from .config import get_settings
from .schemas import (
    CompleteRequest,
    EnqueueRequest,
    EnqueueResponse,
    HeartbeatRequest,
    LeaseRequest,
    LeaseResponse,
    TenantBudgetResponse,
    TenantBudgetUpdate,
)
from .storage import DEFAULT_WEIGHT_BY_TIER, JobRecord, SchedulerRepository

logger = logging.getLogger(__name__)

app = FastAPI(title="Dyocense Scheduler Service", version="0.1.0")
app.add_middleware(BearerAuthMiddleware, decoder=noop_decoder)

_repository_singleton: Optional[SchedulerRepository] = None


def get_repository() -> SchedulerRepository:
    global _repository_singleton
    if _repository_singleton:
        return _repository_singleton
    settings = get_settings()
    if not settings.mongo_uri:
        raise RuntimeError("SCHEDULER_MONGO_URI missing")
    jobs = get_mongo_collection(settings.mongo_uri, settings.mongo_db, settings.jobs_collection)
    tenants = get_mongo_collection(settings.mongo_uri, settings.mongo_db, settings.tenants_collection)
    _repository_singleton = SchedulerRepository(jobs, tenants)
    return _repository_singleton


@app.get("/health", tags=["health"])
def health() -> Dict[str, object]:
    settings = get_settings()
    return {"status": "ok", "mongo": settings.mongo_uri}


@app.post("/queue/enqueue", response_model=EnqueueResponse, tags=["queue"])
async def enqueue_job(
    request: EnqueueRequest,
    repository: SchedulerRepository = Depends(get_repository),
) -> EnqueueResponse:
    tenant = context.get_tenant()
    tenant_id = tenant.tenant_id if tenant else request.tenant_id
    tier = request.tier
    if not repository.rate_limit_allow(tenant_id, tier):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")
    state = repository.ensure_tenant(tenant_id, tier)
    weight = state.weight or DEFAULT_WEIGHT_BY_TIER.get(tier, 1.0)
    priority = request.priority if request.priority is not None else int(weight)
    virtual_finish = state.last_request_ts + (sum(request.cost_estimate.values()) / max(weight, 0.0001))
    record = repository.enqueue_job(
        tenant_id=tenant_id,
        tier=tier,
        job_type=request.job_type,
        payload=request.payload,
        cost_estimate=request.cost_estimate,
        priority=priority,
        virtual_finish=virtual_finish,
    )
    return EnqueueResponse(job_id=record.job_id, lease_expires_at=record.lease_expires_at)


@app.post("/queue/lease", response_model=LeaseResponse, tags=["queue"])
async def lease_jobs(
    request: LeaseRequest,
    repository: SchedulerRepository = Depends(get_repository),
) -> LeaseResponse:
    jobs = repository.lease_jobs(request.worker_id, request.max_jobs, lease_seconds=get_settings().default_lease_seconds)
    return LeaseResponse(jobs=[_job_to_payload(job) for job in jobs])


@app.post("/queue/{job_id}/heartbeat", tags=["queue"])
async def heartbeat_job(
    job_id: str,
    request: HeartbeatRequest,
    repository: SchedulerRepository = Depends(get_repository),
) -> Dict[str, object]:
    record = repository.extend_lease(job_id, request.worker_id, request.lease_extension_seconds)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return {"job_id": record.job_id, "lease_expires_at": record.lease_expires_at}


@app.post("/queue/{job_id}/complete", tags=["queue"])
async def complete_job(
    job_id: str,
    request: CompleteRequest,
    repository: SchedulerRepository = Depends(get_repository),
) -> Dict[str, object]:
    record = repository.complete_job(job_id, request.worker_id, request.result)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return {"status": "completed"}


@app.get("/tenants/{tenant_id}/budget", response_model=TenantBudgetResponse, tags=["tenants"])
async def get_tenant_budget(
    tenant_id: str,
    repository: SchedulerRepository = Depends(get_repository),
) -> TenantBudgetResponse:
    state = repository.get_tenant_state(tenant_id)
    if not state:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    return TenantBudgetResponse(
        tenant_id=state.tenant_id,
        tier=state.tier,
        remaining=state.remaining,
        limits=state.limits,
        rate_limit_per_minute=state.rate_limit_per_minute,
    )


@app.post("/tenants/{tenant_id}/budget", response_model=TenantBudgetResponse, tags=["tenants"])
async def update_tenant_budget(
    tenant_id: str,
    request: TenantBudgetUpdate,
    repository: SchedulerRepository = Depends(get_repository),
) -> TenantBudgetResponse:
    tier = request.__dict__.get("tier", "standard")  # allow overrides if provided
    limits = {
        "solver_sec": request.solver_sec_limit,
        "gpu_sec": request.gpu_sec_limit,
        "llm_tokens": request.llm_tokens_limit,
    }
    state = repository.update_tenant_limits(tenant_id, tier, limits)
    return TenantBudgetResponse(
        tenant_id=state.tenant_id,
        tier=state.tier,
        remaining=state.remaining,
        limits=state.limits,
        rate_limit_per_minute=state.rate_limit_per_minute,
    )


def _job_to_payload(job: JobRecord) -> Dict[str, object]:
    return {
        "job_id": job.job_id,
        "tenant_id": job.tenant_id,
        "tier": job.tier,
        "job_type": job.job_type,
        "payload": job.payload,
        "cost_estimate": job.cost_estimate,
        "priority": job.priority,
        "lease_expires_at": job.lease_expires_at,
    }
