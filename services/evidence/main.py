from __future__ import annotations

from datetime import datetime, timezone
import uuid

from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from packages.kernel_common.deps import require_auth
from packages.kernel_common.graph import get_graph_store
from packages.kernel_common.logging import configure_logging
from packages.evidence import EvidenceRepositoryPG
from packages.trust import GLOBAL_FACT_REGISTRY, ComplianceFact
from packages.trust.repository_postgres import ComplianceFactRepositoryPG

logger = configure_logging("evidence-service")
graph_store = get_graph_store()
evidence_repository = EvidenceRepositoryPG()
fact_repository = ComplianceFactRepositoryPG()

app = FastAPI(
    title="Dyocense Evidence Service",
    version="0.3.0",
    description="Phase 3 stub storing optimisation traces in MongoDB (or in-memory fallback).",
)


class EvidenceRecord(BaseModel):
    run_id: str = Field(..., description="Unique identifier for the decision run.")
    tenant_id: str | None = Field(
        None, description="Tenant submitting the run (falls back to token)."
    )
    ops: dict = Field(..., description="OPS payload associated with the run.")
    solution: dict = Field(..., description="SolutionPack output.")
    explanation: dict = Field(..., description="Explanation payload.")
    artifacts: dict | None = Field(
        default=None, description="Optional artifact metadata (e.g., file URIs)."
    )
    facts: list[dict] | None = Field(
        default=None,
        description="Optional compliance facts (category, statement, status, source, metadata).",
    )
    goal_pack: dict | None = Field(
        default=None,
        description="Optional GoalPack record associated with the run.",
    )


class EvidenceResponse(BaseModel):
    run_id: str
    stored_at: str


def persist_evidence_record(record: dict) -> EvidenceResponse:
    stored_at = datetime.now(tz=timezone.utc).isoformat()
    payload = {**record, "stored_at": stored_at}
    facts_payload = payload.pop("facts", None)
    saved = evidence_repository.create(payload)
    try:
        graph_store.ingest_evidence(saved)
    except Exception as exc:  # pragma: no cover - external graph store
        logger.warning("Graph ingest failed for run %s (%s)", record["run_id"], exc)
    if facts_payload:
        _record_facts(record["run_id"], record["tenant_id"], facts_payload)
    return EvidenceResponse(run_id=record["run_id"], stored_at=stored_at)


@app.post("/v1/evidence/log", response_model=EvidenceResponse)
def log_evidence(body: EvidenceRecord, identity: dict = Depends(require_auth)) -> EvidenceResponse:
    record = body.model_dump()
    record["tenant_id"] = identity["tenant_id"]
    response = persist_evidence_record(record)
    logger.info(
        "Stored evidence for run %s (tenant=%s)",
        body.run_id,
        identity["tenant_id"],
    )
    return response


@app.get("/v1/evidence/{run_id}")
def get_evidence(run_id: str) -> dict:
    document = evidence_repository.get(run_id)
    if not document:
        raise HTTPException(status_code=404, detail="Run not found")
    return document


@app.get("/v1/evidence")
def list_evidence(
    limit: int = Query(default=20, ge=1, le=100),
    identity: dict = Depends(require_auth),
) -> dict:
    items = evidence_repository.list_by_tenant(identity["tenant_id"], limit=limit)
    return {"items": items, "count": len(items)}


@app.get("/v1/evidence/{run_id}/facts")
def list_facts(run_id: str, identity: dict = Depends(require_auth)) -> dict:
    records = GLOBAL_FACT_REGISTRY.list_for_run(run_id)
    filtered = [fact for fact in records if fact.tenant_id == identity["tenant_id"]]
    return {"items": [fact.model_dump() for fact in filtered], "count": len(filtered)}


def _record_facts(run_id: str, tenant_id: str, facts_payload: list[dict]) -> None:
    for raw in facts_payload:
        fact = ComplianceFact(
            fact_id=raw.get("fact_id") or f"fact-{uuid.uuid4().hex[:12]}",
            run_id=run_id,
            tenant_id=tenant_id,
            category=raw.get("category", "unspecified"),
            statement=raw.get("statement", ""),
            status=raw.get("status", "pending"),
            source=raw.get("source"),
            metadata=raw.get("metadata", {}),
        )
        GLOBAL_FACT_REGISTRY.record(fact)
