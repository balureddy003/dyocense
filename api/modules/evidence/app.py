"""FastAPI application exposing evidence queries."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException, status

from api.common import (
    BearerAuthMiddleware,
    context,
    get_mongo_collection,
    noop_decoder,
)

from .config import get_settings
from .schemas import (
    ConstraintLineage,
    EvidenceDetail,
    EvidenceListItem,
    ScenarioReplayResponse,
    ShareLinkRequest,
    ShareLinkResponse,
    SupplierExplanation,
)
from .services import EvidenceService
from .storage import EvidenceRecord, EvidenceRepository

logger = logging.getLogger(__name__)

app = FastAPI(title="Dyocense Evidence Service", version="0.1.0")
app.add_middleware(BearerAuthMiddleware, decoder=noop_decoder)

_repository_singleton: Optional[EvidenceRepository] = None
_service_singleton: Optional[EvidenceService] = None


def get_repository() -> EvidenceRepository:
    global _repository_singleton
    if _repository_singleton:
        return _repository_singleton
    settings = get_settings()
    if not settings.mongo_uri:
        raise RuntimeError("EVIDENCE_MONGO_URI missing")
    collection = get_mongo_collection(settings.mongo_uri, settings.mongo_db, settings.evidence_collection)
    _repository_singleton = EvidenceRepository(collection)
    return _repository_singleton


def get_service(repository: EvidenceRepository = Depends(get_repository)) -> EvidenceService:
    global _service_singleton
    if _service_singleton is None:
        _service_singleton = EvidenceService(repository)
    return _service_singleton


@app.get("/health", tags=["health"])
def health() -> Dict[str, object]:
    settings = get_settings()
    return {"status": "ok", "mongo": settings.mongo_uri}


@app.get("/evidence", response_model=List[EvidenceListItem], tags=["evidence"])
async def list_evidence(service: EvidenceService = Depends(get_service)) -> List[EvidenceListItem]:
    tenant = _require_tenant()
    records = service.list_evidence(tenant.tenant_id)
    return [
        EvidenceListItem(
            evidence_ref=record.evidence_ref,
            tenant_id=record.tenant_id,
            plan_id=record.plan_id,
            goal_id=record.goal_id,
            created_at=record.created_at,
            status=record.snapshot.get("solution", {}).get("status") if isinstance(record.snapshot.get("solution"), dict) else None,
            allow=record.snapshot.get("policy", {}).get("allow") if isinstance(record.snapshot.get("policy"), dict) else None,
            summary={
                "kpis": (record.snapshot.get("solution") or {}).get("kpis", {}),
                "diagnostics": record.snapshot.get("diagnostics", {}),
            },
        )
        for record in records
    ]


@app.get("/evidence/{evidence_ref}", response_model=EvidenceDetail, tags=["evidence"])
async def get_evidence_detail(
    evidence_ref: str,
    service: EvidenceService = Depends(get_service),
) -> EvidenceDetail:
    tenant = _require_tenant()
    record = service.get_evidence(tenant.tenant_id, evidence_ref)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")
    policy_snapshot = service.extract_policy_snapshot(record)
    diagnostics = record.snapshot.get("diagnostics", {})
    solution = record.snapshot.get("solution", {})
    redacted = _should_redact(tenant)
    return EvidenceDetail(
        evidence_ref=record.evidence_ref,
        plan_id=record.plan_id,
        tenant_id=record.tenant_id,
        goal_id=record.goal_id,
        created_at=record.created_at,
        snapshot=_redact_snapshot(record.snapshot) if redacted else record.snapshot,
        policy_snapshot=policy_snapshot,
        diagnostics=diagnostics,
        solution=solution,
        redacted=redacted,
    )


@app.get("/evidence/{evidence_ref}/suppliers/{supplier_id}", response_model=SupplierExplanation, tags=["evidence"])
async def supplier_explanation(
    evidence_ref: str,
    supplier_id: str,
    service: EvidenceService = Depends(get_service),
) -> SupplierExplanation:
    tenant = _require_tenant()
    record = service.get_evidence(tenant.tenant_id, evidence_ref)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")
    data = service.supplier_explanation(record, supplier_id)
    return SupplierExplanation(**data)


@app.get("/evidence/{evidence_ref}/constraints/{constraint}", response_model=ConstraintLineage, tags=["evidence"])
async def constraint_lineage(
    evidence_ref: str,
    constraint: str,
    service: EvidenceService = Depends(get_service),
) -> ConstraintLineage:
    tenant = _require_tenant()
    record = service.get_evidence(tenant.tenant_id, evidence_ref)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")
    data = service.constraint_lineage(record, constraint)
    return ConstraintLineage(**data)


@app.get("/evidence/{evidence_ref}/scenarios/{scenario_id}", response_model=ScenarioReplayResponse, tags=["evidence"])
async def scenario_replay(
    evidence_ref: str,
    scenario_id: int,
    service: EvidenceService = Depends(get_service),
) -> ScenarioReplayResponse:
    tenant = _require_tenant()
    record = service.get_evidence(tenant.tenant_id, evidence_ref)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")
    scenario = service.scenario_replay(record, scenario_id)
    if scenario is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scenario not found")
    return ScenarioReplayResponse(
        evidence_ref=evidence_ref,
        scenario_id=scenario_id,
        demand=scenario.get("demand", {}),
        lead_time_days=scenario.get("lead_time_days", {}),
    )


@app.post("/evidence/{evidence_ref}/share", response_model=ShareLinkResponse, tags=["sharing"])
async def create_share_link(
    evidence_ref: str,
    request: ShareLinkRequest,
    repository: EvidenceRepository = Depends(get_repository),
) -> ShareLinkResponse:
    tenant = _require_tenant()
    record = repository.get(tenant.tenant_id, evidence_ref)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")
    share_id = _generate_share_id()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=request.expires_in_minutes)
    payload = {
        "tenant_id": tenant.tenant_id,
        "evidence_ref": evidence_ref,
        "expires_at": expires_at,
        "redact_policy": request.redact_policy,
        "redact_variants": request.redact_variants,
    }
    repository.add_share_link(tenant.tenant_id, evidence_ref, share_id, payload)
    return ShareLinkResponse(
        share_id=share_id,
        expires_at=expires_at,
        url=f"/share/{share_id}",
    )


@app.get("/share/{share_id}", response_model=EvidenceDetail, tags=["sharing"])
async def open_share_link(
    share_id: str,
    repository: EvidenceRepository = Depends(get_repository),
) -> EvidenceDetail:
    link = repository.get_share_link(share_id)
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Share link not found")
    expires_at = link.get("expires_at")
    if isinstance(expires_at, datetime) and expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Share link expired")
    record = repository.get(link["tenant_id"], link["evidence_ref"])
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")
    snapshot = record.snapshot
    if link.get("redact_policy"):
        snapshot = _redact_policy(snapshot)
    if link.get("redact_variants"):
        snapshot = _redact_variants(snapshot)
    diagnostics = snapshot.get("diagnostics", {})
    solution = snapshot.get("solution", {})
    return EvidenceDetail(
        evidence_ref=record.evidence_ref,
        plan_id=record.plan_id,
        tenant_id=record.tenant_id,
        goal_id=record.goal_id,
        created_at=record.created_at,
        snapshot=snapshot,
        policy_snapshot=snapshot.get("policy"),
        diagnostics=diagnostics,
        solution=solution,
        redacted=True,
    )


def _require_tenant():
    tenant = context.get_tenant()
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing tenant context")
    return tenant


def _should_redact(tenant) -> bool:
    return False


def _redact_snapshot(snapshot: Dict[str, object]) -> Dict[str, object]:
    return snapshot


def _redact_policy(snapshot: Dict[str, object]) -> Dict[str, object]:
    snapshot = dict(snapshot)
    snapshot.pop("policy", None)
    metadata = snapshot.get("metadata")
    if isinstance(metadata, dict):
        metadata = dict(metadata)
        metadata.pop("policy_snapshot", None)
        snapshot["metadata"] = metadata
    return snapshot


def _redact_variants(snapshot: Dict[str, object]) -> Dict[str, object]:
    snapshot = dict(snapshot)
    solution = snapshot.get("solution")
    if isinstance(solution, dict):
        solution = dict(solution)
        steps = solution.get("steps")
        if isinstance(steps, list):
            solution["steps"] = [
                {
                    "sku": step.get("sku"),
                    "supplier": step.get("supplier"),
                    "period": step.get("period"),
                    "quantity": step.get("quantity"),
                }
                for step in steps
            ]
        snapshot["solution"] = solution
    return snapshot


def _generate_share_id() -> str:
    import secrets

    return secrets.token_urlsafe(8)
