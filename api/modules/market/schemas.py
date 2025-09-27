"""Schemas for market intelligence ingestion."""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List

from pydantic import BaseModel, Field


class SupplierSnapshot(BaseModel):
    supplier_id: str
    cost: float = Field(ge=0)
    capacity: float = Field(ge=0)
    score: float = Field(ge=0, le=1)
    metadata: Dict[str, object] = Field(default_factory=dict)


class MarketIngestRequest(BaseModel):
    tenant_id: str
    source: str
    snapshots: List[SupplierSnapshot]


class MarketIngestResponse(BaseModel):
    count: int
    ingested_at: datetime
