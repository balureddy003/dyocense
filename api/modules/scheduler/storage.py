"""Mongo persistence for scheduler jobs and tenant budgets."""
from __future__ import annotations

import math
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Dict, Iterable, Optional, Tuple

from pymongo import ASCENDING, DESCENDING
from pymongo.collection import Collection

DEFAULT_WEIGHT_BY_TIER = {
    "free": 1.0,
    "standard": 2.0,
    "pro": 3.0,
    "enterprise": 5.0,
}

DEFAULT_RATE_LIMITS = {
    "free": 1,
    "standard": 4,
    "pro": 8,
    "enterprise": 16,
}


@dataclass(slots=True)
class JobRecord:
    job_id: str
    tenant_id: str
    tier: str
    job_type: str
    payload: Dict[str, object]
    cost_estimate: Dict[str, float]
    priority: int
    status: str
    worker_id: Optional[str]
    lease_expires_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    virtual_finish: float


@dataclass(slots=True)
class TenantState:
    tenant_id: str
    tier: str
    weight: float
    remaining: Dict[str, float]
    limits: Dict[str, Optional[float]]
    rate_limit_per_minute: Optional[int]
    last_request_ts: float


class SchedulerRepository:
    def __init__(self, jobs: Collection, tenants: Collection) -> None:
        self._jobs = jobs
        self._tenants = tenants
        self._ensure_indexes()

    # ------------------------------------------------------------------
    # Tenant state
    # ------------------------------------------------------------------
    def ensure_tenant(self, tenant_id: str, tier: str) -> TenantState:
        weight = DEFAULT_WEIGHT_BY_TIER.get(tier, 1.0)
        rate_limit = DEFAULT_RATE_LIMITS.get(tier)
        now = time.time()
        document = self._tenants.find_one_and_update(
            {"tenant_id": tenant_id},
            {
                "$setOnInsert": {
                    "tier": tier,
                    "weight": weight,
                    "remaining": {"solver_sec": math.inf, "gpu_sec": math.inf, "llm_tokens": math.inf},
                    "limits": {"solver_sec": None, "gpu_sec": None, "llm_tokens": None},
                    "rate_limit_per_minute": rate_limit,
                    "last_request_ts": now,
                },
                "$set": {"tier": tier},
            },
            upsert=True,
            return_document=True,
        )
        return _tenant_document_to_state(document)

    def update_tenant_limits(
        self,
        tenant_id: str,
        tier: str,
        limits: Dict[str, Optional[float]],
    ) -> TenantState:
        weight = DEFAULT_WEIGHT_BY_TIER.get(tier, 1.0)
        document = self._tenants.find_one_and_update(
            {"tenant_id": tenant_id},
            {
                "$set": {
                    "tier": tier,
                    "weight": weight,
                    "limits": limits,
                }
            },
            upsert=True,
            return_document=True,
        )
        return _tenant_document_to_state(document)

    def get_tenant_state(self, tenant_id: str) -> Optional[TenantState]:
        document = self._tenants.find_one({"tenant_id": tenant_id})
        return _tenant_document_to_state(document)

    def decrement_usage(self, tenant_id: str, usage: Dict[str, float]) -> None:
        self._tenants.update_one(
            {"tenant_id": tenant_id},
            {
                "$inc": {
                    "remaining.solver_sec": -usage.get("solver_sec", 0.0),
                    "remaining.gpu_sec": -usage.get("gpu_sec", 0.0),
                    "remaining.llm_tokens": -usage.get("llm_tokens", 0.0),
                }
            },
        )

    # ------------------------------------------------------------------
    # Job queue operations
    # ------------------------------------------------------------------
    def enqueue_job(
        self,
        tenant_id: str,
        tier: str,
        job_type: str,
        payload: Dict[str, object],
        cost_estimate: Dict[str, float],
        priority: int,
        virtual_finish: float,
    ) -> JobRecord:
        now = datetime.now(timezone.utc)
        job_id = str(uuid.uuid4())
        document = {
            "job_id": job_id,
            "tenant_id": tenant_id,
            "tier": tier,
            "job_type": job_type,
            "payload": payload,
            "cost_estimate": cost_estimate,
            "priority": priority,
            "virtual_finish": virtual_finish,
            "status": "queued",
            "worker_id": None,
            "lease_expires_at": None,
            "created_at": now,
            "updated_at": now,
        }
        self._jobs.insert_one(document)
        return _job_document_to_record(document)

    def lease_jobs(
        self,
        worker_id: str,
        max_jobs: int,
        lease_seconds: int,
    ) -> Iterable[JobRecord]:
        now = datetime.now(timezone.utc)
        cursor = self._jobs.find(
            {
                "status": "queued",
                "$or": [
                    {"lease_expires_at": None},
                    {"lease_expires_at": {"$lte": now}},
                ],
            }
        ).sort([("priority", DESCENDING), ("virtual_finish", ASCENDING), ("created_at", ASCENDING)]).limit(max_jobs)
        jobs = []
        lease_expires = now + timedelta(seconds=lease_seconds)
        for doc in cursor:
            self._jobs.update_one({"_id": doc["_id"]}, {"$set": {"status": "leased", "worker_id": worker_id, "lease_expires_at": lease_expires, "updated_at": lease_expires}})
            doc["status"] = "leased"
            doc["worker_id"] = worker_id
            doc["lease_expires_at"] = lease_expires
            doc["updated_at"] = lease_expires
            jobs.append(_job_document_to_record(doc))
        return jobs

    def extend_lease(self, job_id: str, worker_id: str, lease_extension_seconds: int) -> Optional[JobRecord]:
        lease_expires = datetime.now(timezone.utc) + timedelta(seconds=lease_extension_seconds)
        document = self._jobs.find_one_and_update(
            {"job_id": job_id, "worker_id": worker_id, "status": "leased"},
            {"$set": {"lease_expires_at": lease_expires, "updated_at": lease_expires}},
            return_document=True,
        )
        return _job_document_to_record(document)

    def complete_job(self, job_id: str, worker_id: str, result: Optional[Dict[str, object]]) -> Optional[JobRecord]:
        document = self._jobs.find_one_and_update(
            {"job_id": job_id, "worker_id": worker_id},
            {"$set": {"status": "completed", "result": result, "updated_at": datetime.now(timezone.utc)}},
            return_document=True,
        )
        return _job_document_to_record(document)

    def rate_limit_allow(self, tenant_id: str, tier: str) -> bool:
        state = self.ensure_tenant(tenant_id, tier)
        rate_limit = state.rate_limit_per_minute
        if not rate_limit:
            return True
        now = time.time()
        if now - state.last_request_ts < 60 / rate_limit:
            return False
        self._tenants.update_one({"tenant_id": tenant_id}, {"$set": {"last_request_ts": now}})
        return True

    def _ensure_indexes(self) -> None:
        self._jobs.create_index([("status", ASCENDING), ("priority", DESCENDING), ("virtual_finish", ASCENDING)])
        self._jobs.create_index([("tenant_id", ASCENDING), ("created_at", DESCENDING)])
        self._tenants.create_index([("tenant_id", ASCENDING)], unique=True)


def _job_document_to_record(document: Optional[Dict[str, object]]) -> Optional[JobRecord]:
    if not document:
        return None
    return JobRecord(
        job_id=str(document.get("job_id")),
        tenant_id=str(document.get("tenant_id")),
        tier=str(document.get("tier", "standard")),
        job_type=str(document.get("job_type", "kernel_run")),
        payload=dict(document.get("payload", {})),
        cost_estimate=dict(document.get("cost_estimate", {})),
        priority=int(document.get("priority", 0)),
        status=str(document.get("status", "queued")),
        worker_id=document.get("worker_id"),
        lease_expires_at=document.get("lease_expires_at"),
        created_at=document.get("created_at"),
        updated_at=document.get("updated_at"),
        virtual_finish=float(document.get("virtual_finish", 0.0)),
    )


def _tenant_document_to_state(document: Optional[Dict[str, object]]) -> Optional[TenantState]:
    if not document:
        return None
    remaining = document.get("remaining", {})
    limits = document.get("limits", {})
    return TenantState(
        tenant_id=str(document.get("tenant_id")),
        tier=str(document.get("tier", "standard")),
        weight=float(document.get("weight", 1.0)),
        remaining={
            "solver_sec": float(remaining.get("solver_sec", math.inf)),
            "gpu_sec": float(remaining.get("gpu_sec", math.inf)),
            "llm_tokens": float(remaining.get("llm_tokens", math.inf)),
        },
        limits={
            "solver_sec": limits.get("solver_sec"),
            "gpu_sec": limits.get("gpu_sec"),
            "llm_tokens": limits.get("llm_tokens"),
        },
        rate_limit_per_minute=document.get("rate_limit_per_minute"),
        last_request_ts=float(document.get("last_request_ts", time.time())),
    )
