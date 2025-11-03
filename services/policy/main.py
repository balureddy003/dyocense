from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from fastapi import Depends, FastAPI
from pydantic import BaseModel, Field

from packages.kernel_common.deps import require_auth
from packages.kernel_common.logging import configure_logging

logger = configure_logging("policy-service")


class PolicyCheck(BaseModel):
    name: str
    status: str
    message: str


class PolicyRequest(BaseModel):
    ops: dict = Field(..., description="OPS document to evaluate.")
    tenant_id: str | None = Field(
        None, description="Tenant executing the policy checks (falls back to token)."
    )


def evaluate_ops_policy(ops: dict, tenant_id: str) -> PolicyResponse:
    evaluated_at = datetime.now(tz=timezone.utc).isoformat()
    checks = [
        PolicyCheck(
            name="tenant-quota",
            status="pass",
            message="Workload within tenant quota envelope.",
        ),
        PolicyCheck(
            name="mandatory-constraints",
            status="pass",
            message="Required constraints present for archetype inventory_planning.",
        ),
    ]

    logger.info(
        "Evaluated %d policies for tenant %s",
        len(checks),
        tenant_id,
    )
    return PolicyResponse(evaluated_at=evaluated_at, verdict="allow", checks=checks)


app = FastAPI(
    title="Dyocense Policy Service",
    version="0.6.0",
    description="Phase 3 stub that simulates policy evaluation results.",
)


class PolicyResponse(BaseModel):
    evaluated_at: str
    verdict: str
    checks: List[PolicyCheck]


@app.post("/v1/policy/evaluate", response_model=PolicyResponse)
def evaluate_policy(body: PolicyRequest, identity: dict = Depends(require_auth)) -> PolicyResponse:
    """
    Evaluate policies for an OPS document. Placeholder implementation.
    """
    tenant_id = body.tenant_id or identity["tenant_id"]
    return evaluate_ops_policy(body.ops, tenant_id)
