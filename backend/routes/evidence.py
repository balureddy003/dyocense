"""
Evidence/Causal Inference Routes

Provides endpoints to:
- compute correlations across metrics
- run Granger causality between two series
- explain a metric change with driver contributions

Instrumented with Prometheus metrics for observability.
"""

import time
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from backend.services.evidence.causal_engine import (
    CausalEngine,
    CorrelationResult,
    GrangerResult,
)
from backend.utils.metrics import (
    record_evidence_correlation,
    record_evidence_granger,
    record_evidence_whatif,
    record_evidence_drivers,
)

router = APIRouter()
engine = CausalEngine()


class CorrelationsRequest(BaseModel):
    series: Dict[str, List[float]] = Field(
        ..., description="Mapping of metric -> values (equal length)"
    )


class CorrelationsResponse(BaseModel):
    results: List[CorrelationResult]


@router.post("/correlations", response_model=CorrelationsResponse)
async def correlations(payload: CorrelationsRequest, request: Request) -> CorrelationsResponse:
    """Compute pairwise correlations across metrics with Prometheus tracking."""
    start_time = time.time()
    
    results = engine.detect_correlations(payload.series)
    
    # Record metrics
    duration = time.time() - start_time
    tenant_id = getattr(request.state, "tenant_id", "unknown")
    record_evidence_correlation(
        tenant_id=tenant_id,
        num_series=len(payload.series),
        duration=duration,
        results=results
    )
    
    return CorrelationsResponse(results=results)


class GrangerRequest(BaseModel):
    a_name: str = Field(..., description="Name of first series")
    b_name: str = Field(..., description="Name of second series")
    a: List[float]
    b: List[float]
    max_lag: int = 3
    alpha: float = 0.05


class GrangerResponse(BaseModel):
    results: List[GrangerResult]


@router.post("/granger", response_model=GrangerResponse)
async def granger(payload: GrangerRequest, request: Request) -> GrangerResponse:
    """Test Granger causality between two time series with Prometheus tracking."""
    start_time = time.time()
    
    series = {payload.a_name: payload.a, payload.b_name: payload.b}
    results = engine.granger_causality(series, payload.max_lag, payload.alpha)
    
    # Record metrics
    duration = time.time() - start_time
    tenant_id = getattr(request.state, "tenant_id", "unknown")
    record_evidence_granger(tenant_id=tenant_id, duration=duration)
    
    return GrangerResponse(results=results)


class ExplainRequest(BaseModel):
    metric: str
    before: float
    after: float
    drivers: Dict[str, float] = Field(default_factory=dict)


class ExplainResponse(BaseModel):
    explanation: str


@router.post("/explain", response_model=ExplainResponse)
async def explain_change(payload: ExplainRequest) -> ExplainResponse:
    explanation = engine.explain_change(payload.metric, payload.before, payload.after, payload.drivers)
    return ExplainResponse(explanation=explanation)


class WhatIfRequest(BaseModel):
    cause_name: str = Field(..., description="Name of the causal feature")
    effect_name: str = Field(..., description="Name of the effected metric")
    cause: List[float] = Field(..., description="Historical values of the cause")
    effect: List[float] = Field(..., description="Historical values of the effect")
    delta_cause: float = Field(..., description="Proposed change in the cause")


class WhatIfResponse(BaseModel):
    predicted_delta: float
    slope: float
    intercept: float
    r2: float


@router.post("/what-if", response_model=WhatIfResponse)
async def what_if(payload: WhatIfRequest, request: Request) -> WhatIfResponse:
    """Perform what-if analysis with linear regression and Prometheus tracking."""
    start_time = time.time()
    
    result = engine.what_if(payload.cause, payload.effect, payload.delta_cause)
    if not result:
        raise HTTPException(status_code=400, detail="Unable to fit model for what-if analysis")
    
    # Record metrics
    duration = time.time() - start_time
    tenant_id = getattr(request.state, "tenant_id", "unknown")
    record_evidence_whatif(tenant_id=tenant_id, duration=duration, r2=result.get("r2"))
    
    return WhatIfResponse(
        predicted_delta=result["predicted_delta"],
        slope=result["slope"],
        intercept=result["intercept"],
        r2=result["r2"],
    )


class DriverContribution(BaseModel):
    name: str
    beta: float


class DriversRequest(BaseModel):
    target_name: str
    target: List[float]
    drivers: Dict[str, List[float]]


class DriversResponse(BaseModel):
    drivers: List[DriverContribution]


@router.post("/drivers", response_model=DriversResponse)
async def drivers(payload: DriversRequest, request: Request) -> DriversResponse:
    """Infer driver importance via standardized linear regression with Prometheus tracking."""
    start_time = time.time()
    
    inferred = engine.infer_drivers(payload.target, payload.drivers)
    
    # Record metrics
    duration = time.time() - start_time
    tenant_id = getattr(request.state, "tenant_id", "unknown")
    record_evidence_drivers(
        tenant_id=tenant_id,
        num_drivers=len(payload.drivers),
        duration=duration
    )
    
    return DriversResponse(
        drivers=[
            DriverContribution(name=str(d.get("name")), beta=float(d.get("beta", 0.0)))
            for d in inferred
            if isinstance(d, dict)
        ]
    )
