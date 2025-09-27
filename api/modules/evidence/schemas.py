"""Pydantic schemas for Evidence service."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class EvidenceListItem(BaseModel):
    evidence_ref: str
    plan_id: Optional[str]
    tenant_id: str
    goal_id: Optional[str]
    created_at: datetime
    status: Optional[str]
    allow: Optional[bool]
    summary: Dict[str, Any]


class EvidenceDetail(BaseModel):
    evidence_ref: str
    plan_id: Optional[str]
    tenant_id: str
    goal_id: Optional[str]
    created_at: datetime
    snapshot: Dict[str, Any]
    policy_snapshot: Optional[Dict[str, Any]]
    diagnostics: Dict[str, Any]
    solution: Dict[str, Any]
    redacted: bool = False


class SupplierExplanation(BaseModel):
    evidence_ref: str
    supplier_id: str
    path: List[str]
    alternative: Optional[Dict[str, Any]]


class ConstraintLineage(BaseModel):
    evidence_ref: str
    constraint: str
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]


class ScenarioReplayResponse(BaseModel):
    evidence_ref: str
    scenario_id: int
    demand: Dict[str, Dict[str, float]]
    lead_time_days: Dict[str, float]


class ShareLinkResponse(BaseModel):
    share_id: str
    expires_at: datetime
    url: str


class ShareLinkRequest(BaseModel):
    expires_in_minutes: int = 60
    redact_policy: bool = True
    redact_variants: bool = False
