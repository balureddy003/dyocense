"""Pydantic schemas for Policy service."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class PolicyRule(BaseModel):
    name: str
    definition: Dict[str, Any]


class PolicyCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    rules: List[PolicyRule]
    thresholds: Dict[str, Any] = Field(default_factory=dict)


class PolicyUpdateRequest(BaseModel):
    description: Optional[str] = None
    rules: Optional[List[PolicyRule]] = None
    thresholds: Optional[Dict[str, Any]] = None


class PolicyVersionResponse(BaseModel):
    version_id: str
    created_at: datetime
    created_by: str
    status: str
    name: str
    description: Optional[str]
    rules: List[PolicyRule]
    thresholds: Dict[str, Any]


class PolicyListItem(BaseModel):
    policy_id: str
    tenant_id: str
    active_version_id: Optional[str]
    updated_at: datetime


class PolicyActivateRequest(BaseModel):
    version_id: str
    note: Optional[str] = None


class PolicyAuditEntry(BaseModel):
    audit_id: str
    tenant_id: str
    policy_id: str
    version_id: str
    decision: Dict[str, Any]
    created_at: datetime
    source: Optional[str]


class ThresholdUpdateRequest(BaseModel):
    thresholds: Dict[str, Any]
