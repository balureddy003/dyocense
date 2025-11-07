from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone


PlanStatus = Literal["draft", "executing", "completed", "failed", "cancelled"]
StepStatus = Literal["pending", "running", "succeeded", "failed", "skipped"]
StepType = Literal[
    "collect_data",
    "forecast",
    "policy_eval",
    "optimise",
    "diagnostics",
    "explain",
    "persist",
    "notify",
]


class Step(BaseModel):
    step_id: str
    type: StepType
    tool: str
    inputs: Dict[str, Any] = Field(default_factory=dict)
    depends_on: List[str] = Field(default_factory=list)
    planned_start: Optional[str] = None
    planned_end: Optional[str] = None
    actual_start: Optional[str] = None
    actual_end: Optional[str] = None
    status: StepStatus = "pending"
    output_ref: Optional[str] = None
    retries: int = 0
    rationale: Optional[str] = None
    metrics: Dict[str, Any] = Field(default_factory=dict)
    trace_id: Optional[str] = None
    span_id: Optional[str] = None


class PlanPack(BaseModel):
    id: str
    goal: str
    context: Dict[str, Any] = Field(default_factory=dict)
    steps: List[Step] = Field(default_factory=list)
    dependencies: Dict[str, List[str]] = Field(default_factory=dict)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    risks: List[str] = Field(default_factory=list)
    alternatives: List[Dict[str, Any]] = Field(default_factory=list)
    evidence_links: List[Dict[str, Any]] = Field(default_factory=list)
    status: PlanStatus = "draft"
    audit: Dict[str, Any] = Field(
        default_factory=lambda: {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "revisions": [],
        }
    )
    trace_root_id: Optional[str] = None

    def build_dependency_index(self) -> Dict[str, List[str]]:
        if not self.dependencies:
            self.dependencies = {s.step_id: s.depends_on for s in self.steps}
        return self.dependencies
