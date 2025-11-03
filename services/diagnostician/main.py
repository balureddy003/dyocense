from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from fastapi import Depends, FastAPI
from pydantic import BaseModel, Field

from packages.kernel_common.deps import require_auth
from packages.kernel_common.logging import configure_logging

logger = configure_logging("diagnostician-service")


class DiagnoseRequest(BaseModel):
    ops: dict = Field(..., description="OPS document analysed for feasibility issues.")
    solution: dict | None = Field(
        None,
        description="Optional SolutionPack for context if an optimisation attempt failed.",
    )


class RelaxationSuggestion(BaseModel):
    constraint: str
    action: str
    rationale: str


def diagnose_ops(ops: dict, solution: dict | None, tenant_id: str) -> DiagnoseResponse:
    analysed_at = datetime.now(tz=timezone.utc).isoformat()
    suggestions = [
        RelaxationSuggestion(
            constraint="demand_satisfaction",
            action="allow 5% demand shortfall",
            rationale="Typical relaxation to absorb forecast volatility in stub pipeline.",
        ),
        RelaxationSuggestion(
            constraint="capacity_limit",
            action="increase capacity by 10 units",
            rationale="Increase headroom if reason codes cite resource over-utilisation.",
        ),
    ]

    logger.info(
        "Returning %d relaxation suggestions (tenant=%s)",
        len(suggestions),
        tenant_id,
    )
    return DiagnoseResponse(
        analysed_at=analysed_at,
        feasibility="unknown",
        suggestions=suggestions,
    )


app = FastAPI(
    title="Dyocense Diagnostician Service",
    version="0.6.0",
    description="Phase 3 stub that returns relaxation recommendations when infeasibility is suspected.",
)


class DiagnoseResponse(BaseModel):
    analysed_at: str
    feasibility: str
    suggestions: List[RelaxationSuggestion]


@app.post("/v1/diagnose", response_model=DiagnoseResponse)
def diagnose(body: DiagnoseRequest, identity: dict = Depends(require_auth)) -> DiagnoseResponse:
    """Return canned relaxation suggestions."""
    return diagnose_ops(body.ops, body.solution, identity["tenant_id"])
