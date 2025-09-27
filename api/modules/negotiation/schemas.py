"""Schemas for negotiation proposals."""
from __future__ import annotations

from typing import Dict, List

from pydantic import BaseModel, Field


class ProposalRequest(BaseModel):
    plan_id: str
    supplier_id: str
    adjustments: Dict[str, float] = Field(default_factory=dict)
    rationale: str


class ProposalResponse(BaseModel):
    proposal_id: str
    plan_id: str
    supplier_id: str
    adjustments: Dict[str, float]
    counterfactual_plan_id: str
