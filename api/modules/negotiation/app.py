"""Negotiation assistant service."""
from __future__ import annotations

import logging
import uuid
from typing import Dict, Optional

from fastapi import Depends, FastAPI, HTTPException, status

from api.common import BearerAuthMiddleware, context, noop_decoder

from api.modules.plan.app import get_gateway as get_plan_gateway
from api.modules.plan.gateway import KernelGateway
from .schemas import ProposalRequest, ProposalResponse

logger = logging.getLogger(__name__)

app = FastAPI(title="Dyocense Negotiation Service", version="0.1.0")
app.add_middleware(BearerAuthMiddleware, decoder=noop_decoder)


@app.post("/negotiation/proposals", response_model=ProposalResponse, tags=["negotiation"])
async def propose_counterfactual(
    request: ProposalRequest,
    plan_gateway: KernelGateway = Depends(get_plan_gateway),
) -> ProposalResponse:
    tenant = _require_tenant()
    kernel_payload = {
        "tenant_id": tenant.tenant_id,
        "mode": "counterfactual",
        "context": {"adjustments": {request.supplier_id: request.adjustments}},
    }
    try:
        result = plan_gateway.run_pipeline(kernel_payload)
    except Exception as exc:  # pragma: no cover - reused gateway handles errors
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    proposal_id = str(uuid.uuid4())
    return ProposalResponse(
        proposal_id=proposal_id,
        plan_id=request.plan_id,
        supplier_id=request.supplier_id,
        adjustments=request.adjustments,
        counterfactual_plan_id=result.solution.kpis.get("plan_id", ""),
    )


def _require_tenant():
    tenant = context.get_tenant()
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing tenant context")
    return tenant
