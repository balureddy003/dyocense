"""Pydantic schemas for Goal service."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class GoalCreateRequest(BaseModel):
    name: str
    goaldsl: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)
    variants: List[Dict[str, Any]] = Field(default_factory=list)


class GoalUpdateRequest(BaseModel):
    name: Optional[str] = None
    goaldsl: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None


class GoalVariantRequest(BaseModel):
    name: str
    goaldsl: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None


class GoalResponse(BaseModel):
    goal_id: str
    name: str
    goaldsl: Dict[str, Any]
    context: Dict[str, Any]
    variants: List[Dict[str, Any]]
    status: str
    approvals: List[Dict[str, Any]]
    feedback: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime


class GoalListItem(BaseModel):
    goal_id: str
    name: str
    status: str
    created_at: datetime
    updated_at: datetime


class GoalStatusRequest(BaseModel):
    status: str
    note: Optional[str] = None


class GoalValidationRequest(BaseModel):
    goaldsl: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None
    scenarios: Optional[Dict[str, Any]] = None


class GoalValidationResponse(BaseModel):
    allow: bool
    policy_snapshot: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GoalFeedbackRequest(BaseModel):
    actuals: Dict[str, Any]
    note: Optional[str] = None
