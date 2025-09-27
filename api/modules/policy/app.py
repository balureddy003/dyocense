"""Policy service API."""
from __future__ import annotations

import logging
from typing import Dict, Iterable, List, Optional

from fastapi import Depends, FastAPI, HTTPException, status

from api.common import BearerAuthMiddleware, context, get_mongo_collection, noop_decoder

from .config import get_settings
from .schemas import (
    PolicyActivateRequest,
    PolicyAuditEntry,
    PolicyCreateRequest,
    PolicyListItem,
    PolicyUpdateRequest,
    PolicyVersionResponse,
    ThresholdUpdateRequest,
)
from .storage import PolicyRepository

logger = logging.getLogger(__name__)

app = FastAPI(title="Dyocense Policy Service", version="0.1.0")
app.add_middleware(BearerAuthMiddleware, decoder=noop_decoder)

_repository_singleton: Optional[PolicyRepository] = None


def get_repository() -> PolicyRepository:
    global _repository_singleton
    if _repository_singleton:
        return _repository_singleton
    settings = get_settings()
    if not settings.mongo_uri:
        raise RuntimeError("POLICY_MONGO_URI missing")
    policies = get_mongo_collection(settings.mongo_uri, settings.mongo_db, settings.policies_collection)
    audits = get_mongo_collection(settings.mongo_uri, settings.mongo_db, settings.audits_collection)
    _repository_singleton = PolicyRepository(policies, audits)
    return _repository_singleton


@app.get("/health", tags=["health"])
def health() -> Dict[str, object]:
    settings = get_settings()
    return {"status": "ok", "mongo": settings.mongo_uri}


@app.post("/policies", response_model=PolicyVersionResponse, status_code=status.HTTP_201_CREATED, tags=["policies"])
async def create_policy(
    request: PolicyCreateRequest,
    repository: PolicyRepository = Depends(get_repository),
) -> PolicyVersionResponse:
    tenant = _require_tenant()
    version = repository.create_policy(
        tenant_id=tenant.tenant_id,
        name=request.name,
        description=request.description,
        rules=[rule.dict() for rule in request.rules],
        thresholds=request.thresholds,
        created_by=tenant.user_id or tenant.tenant_id,
    )
    return _version_response(version)


@app.post("/policies/{policy_id}/versions", response_model=PolicyVersionResponse, tags=["policies"])
async def create_policy_version(
    policy_id: str,
    request: PolicyUpdateRequest,
    repository: PolicyRepository = Depends(get_repository),
) -> PolicyVersionResponse:
    tenant = _require_tenant()
    version = repository.add_version(
        tenant.tenant_id,
        policy_id,
        name=request.__dict__.get("name", "update"),
        description=request.description,
        rules=[rule.dict() for rule in request.rules] if request.rules is not None else None,
        thresholds=request.thresholds,
        created_by=tenant.user_id or tenant.tenant_id,
    )
    if not version:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")
    return _version_response(version)


@app.post("/policies/{policy_id}/activate", response_model=PolicyVersionResponse, tags=["policies"])
async def activate_policy(
    policy_id: str,
    request: PolicyActivateRequest,
    repository: PolicyRepository = Depends(get_repository),
) -> PolicyVersionResponse:
    tenant = _require_tenant()
    version = repository.activate_version(tenant.tenant_id, policy_id, request.version_id, note=request.note)
    if not version:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy/version not found")
    return _version_response(version)


@app.get("/policies", response_model=List[PolicyListItem], tags=["policies"])
async def list_policies(repository: PolicyRepository = Depends(get_repository)) -> List[PolicyListItem]:
    tenant = _require_tenant()
    records = repository.list_policies(tenant.tenant_id)
    return [
        PolicyListItem(
            policy_id=record.policy_id,
            tenant_id=record.tenant_id,
            active_version_id=record.active_version_id,
            updated_at=record.updated_at,
        )
        for record in records
    ]


@app.get("/policies/{policy_id}/versions/{version_id}", response_model=PolicyVersionResponse, tags=["policies"])
async def get_version(
    policy_id: str,
    version_id: str,
    repository: PolicyRepository = Depends(get_repository),
) -> PolicyVersionResponse:
    tenant = _require_tenant()
    version = repository.get_version(tenant.tenant_id, policy_id, version_id)
    if not version:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy/version not found")
    return _version_response(version)


@app.post("/policies/{policy_id}/thresholds", response_model=PolicyVersionResponse, tags=["policies"])
async def update_thresholds(
    policy_id: str,
    request: ThresholdUpdateRequest,
    repository: PolicyRepository = Depends(get_repository),
) -> PolicyVersionResponse:
    tenant = _require_tenant()
    version = repository.add_version(
        tenant.tenant_id,
        policy_id,
        name="threshold-update",
        description=None,
        rules=None,
        thresholds=request.thresholds,
        created_by=tenant.user_id or tenant.tenant_id,
    )
    if not version:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")
    return _version_response(version)


@app.get("/audits", response_model=List[PolicyAuditEntry], tags=["audits"])
async def list_audits(
    policy_id: Optional[str] = None,
    repository: PolicyRepository = Depends(get_repository),
) -> List[PolicyAuditEntry]:
    tenant = _require_tenant()
    audits = repository.list_audits(tenant.tenant_id, policy_id)
    return [
        PolicyAuditEntry(
            audit_id=record.audit_id,
            tenant_id=record.tenant_id,
            policy_id=record.policy_id,
            version_id=record.version_id,
            decision=record.decision,
            source=record.source,
            created_at=record.created_at,
        )
        for record in audits
    ]


def _version_response(version) -> PolicyVersionResponse:
    return PolicyVersionResponse(
        version_id=version.version_id,
        created_at=version.created_at,
        created_by=version.created_by,
        status=version.status,
        name=version.name,
        description=version.description,
        rules=version.rules,
        thresholds=version.thresholds,
    )


def _require_tenant():
    tenant = context.get_tenant()
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing tenant context")
    return tenant
