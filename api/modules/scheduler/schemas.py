"""Pydantic schemas for Scheduler service."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class EnqueueRequest(BaseModel):
    tenant_id: str
    tier: str = "standard"
    job_type: str = "kernel_run"
    cost_estimate: Dict[str, float] = Field(default_factory=dict)
    payload: Dict[str, Any]
    priority: Optional[int] = None


class EnqueueResponse(BaseModel):
    job_id: str
    lease_expires_at: Optional[datetime]


class LeaseRequest(BaseModel):
    worker_id: str
    max_jobs: int = 1


class LeaseResponse(BaseModel):
    jobs: list[Dict[str, Any]]


class HeartbeatRequest(BaseModel):
    worker_id: str
    lease_extension_seconds: int = 30


class CompleteRequest(BaseModel):
    worker_id: str
    result: Optional[Dict[str, Any]] = None


class TenantBudgetUpdate(BaseModel):
    tier: Optional[str] = None
    solver_sec_limit: Optional[float] = None
    gpu_sec_limit: Optional[float] = None
    llm_tokens_limit: Optional[float] = None


class TenantBudgetResponse(BaseModel):
    tenant_id: str
    tier: str
    remaining: Dict[str, float]
    limits: Dict[str, Optional[float]]
    rate_limit_per_minute: Optional[int]
