"""Pydantic schemas for Plan service endpoints."""
from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from services.common import dto

if True:  # type-checker hint without runtime import cycle
    from .storage import PlanRecord  # pragma: no cover


class PlanCreateRequest(BaseModel):
    goal_id: Optional[str] = Field(default=None, description="Optional goal identifier")
    variant: Optional[str] = Field(default=None, description="Goal variant or scenario tag")
    kernel_payload: Dict[str, Any] = Field(default_factory=dict, description="Payload forwarded to kernel pipeline")


class PlanResponse(BaseModel):
    plan_id: str
    goal_id: Optional[str]
    variant: Optional[str]
    evidence_ref: str
    solution: Dict[str, Any]
    diagnostics: Dict[str, Any]
    policy: Optional[Dict[str, Any]]
    created_at: datetime

    @classmethod
    def from_record(cls, record: "PlanRecord") -> "PlanResponse":
        result = record.result
        solution_payload = _solution_to_dict(result.solution)
        diagnostics_payload = result.diagnostics.raw or asdict(result.diagnostics)
        policy_payload = asdict(result.policy) if result.policy else None
        return cls(
            plan_id=record.plan_id,
            goal_id=record.goal_id,
            variant=record.variant,
            evidence_ref=result.evidence_ref,
            solution=solution_payload,
            diagnostics=diagnostics_payload,
            policy=policy_payload,
            created_at=record.created_at,
        )


class PlanListItem(BaseModel):
    plan_id: str
    goal_id: Optional[str]
    variant: Optional[str]
    evidence_ref: str
    created_at: datetime
    allow: Optional[bool]

    @classmethod
    def from_record(cls, record: "PlanRecord") -> "PlanListItem":
        return cls(
            plan_id=record.plan_id,
            goal_id=record.goal_id,
            variant=record.variant,
            evidence_ref=record.result.evidence_ref,
            created_at=record.created_at,
            allow=record.result.policy.allow if record.result.policy else None,
        )


class PlanStep(BaseModel):
    sku: str
    supplier: str
    period: str
    quantity: float
    price: Optional[float]

    @classmethod
    def from_dto(cls, step: dto.SolutionStep) -> "PlanStep":
        return cls(
            sku=step.sku,
            supplier=step.supplier,
            period=step.period,
            quantity=step.quantity,
            price=step.price,
        )


class PlanStepsResponse(BaseModel):
    plan_id: str
    steps: List[PlanStep]

    @classmethod
    def from_record(cls, record: "PlanRecord") -> "PlanStepsResponse":
        steps = [PlanStep.from_dto(step) for step in record.result.solution.steps]
        return cls(plan_id=record.plan_id, steps=steps)


class PlanEvidenceResponse(BaseModel):
    plan_id: str
    evidence_ref: str

    @classmethod
    def from_record(cls, record: "PlanRecord") -> "PlanEvidenceResponse":
        return cls(plan_id=record.plan_id, evidence_ref=record.result.evidence_ref)


def _solution_to_dict(solution: dto.Solution) -> Dict[str, Any]:
    payload = asdict(solution)
    payload["steps"] = [asdict(step) for step in solution.steps]
    return payload
