"""Pydantic schemas for feedback service."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


class FeedbackActual(BaseModel):
    sku: str
    period: str
    quantity: float = Field(ge=0)
    lead_time_days: Optional[float] = Field(default=None, ge=0)


class FeedbackIngestRequest(BaseModel):
    goal_id: Optional[str] = None
    plan_id: Optional[str] = None
    actuals: List[FeedbackActual]

    @validator("actuals")
    def non_empty(cls, value: List[FeedbackActual]) -> List[FeedbackActual]:
        if not value:
            raise ValueError("actuals must not be empty")
        return value


class FeedbackIngestResponse(BaseModel):
    count: int
    triggered_replan: bool


class DriftItem(BaseModel):
    sku: str
    count: int
    avg_quantity: float
    last_period: str
    last_quantity: float


class DriftReport(BaseModel):
    tenant_id: str
    goal_id: Optional[str]
    generated_at: datetime
    items: List[DriftItem]


class SchedulerEvent(BaseModel):
    tenant_id: str
    tier: Optional[str]
    payload: Dict[str, Any]
