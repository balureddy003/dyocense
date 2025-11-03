"""Pydantic models representing goal versions and scenario metadata."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class GoalVersion(BaseModel):
    version_id: str = Field(..., description="Unique version identifier (UUID).")
    tenant_id: str = Field(..., description="Tenant associated with the goal.")
    project_id: str = Field(..., description="Project reference.")
    goal: str = Field(..., description="Raw goal text.")
    ops: Dict = Field(..., description="Compiled Optimization Problem Spec.")
    data_inputs: Dict | None = Field(default=None, description="Structured inputs used at compile time.")
    playbook_id: str | None = Field(default=None, description="Identifier of the playbook applied.")
    knowledge_snippets: list[str] = Field(default_factory=list, description="Snapshot of retrieval context IDs.")
    parent_version_id: Optional[str] = Field(
        default=None, description="If scenario, references the baseline version."
    )
    label: Optional[str] = Field(
        default=None,
        description="Friendly label capturing scenario name or checkpoint description.",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    goal_hash: str = Field(..., description="SHA256 hash of the goal text for deduplication.")
    retrieval: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata about knowledge snippets and dataset versions used during compile.",
    )
    provenance: Dict[str, Any] = Field(
        default_factory=dict,
        description="Provenance information including compiler source and model name.",
    )
