"""Mongo-backed storage for plan runs."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional

import uuid

from pymongo import ASCENDING, DESCENDING
from pymongo.collection import Collection

from api.common import dto


@dataclass(slots=True)
class PlanRecord:
    plan_id: str
    tenant_id: str
    goal_id: Optional[str]
    variant: Optional[str]
    parent_plan_id: Optional[str]
    request_payload: Dict[str, object]
    result: dto.KernelRunResult
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class PlanRepository:
    """MongoDB-backed repository for plan executions."""

    def __init__(self, collection: Collection) -> None:
        self._collection = collection
        self._ensure_indexes()

    def create(
        self,
        tenant_id: str,
        goal_id: Optional[str],
        variant: Optional[str],
        parent_plan_id: Optional[str],
        request_payload: Dict[str, object],
        result: dto.KernelRunResult,
    ) -> PlanRecord:
        plan_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc)
        document = {
            "plan_id": plan_id,
            "tenant_id": tenant_id,
            "goal_id": goal_id,
            "variant": variant,
            "parent_plan_id": parent_plan_id,
            "request_payload": request_payload,
            "result": _kernel_result_to_dict(result),
            "created_at": created_at,
        }
        self._collection.insert_one(document)
        return _document_to_record(document)

    def get(self, tenant_id: str, plan_id: str) -> Optional[PlanRecord]:
        document = self._collection.find_one({"tenant_id": tenant_id, "plan_id": plan_id})
        if not document:
            return None
        return _document_to_record(document)

    def list(self, tenant_id: str) -> Iterable[PlanRecord]:
        cursor = self._collection.find({"tenant_id": tenant_id}).sort("created_at", DESCENDING)
        return [_document_to_record(doc) for doc in cursor]

    def _ensure_indexes(self) -> None:
        self._collection.create_index([("tenant_id", ASCENDING), ("plan_id", ASCENDING)], unique=True)
        self._collection.create_index([("tenant_id", ASCENDING), ("created_at", DESCENDING)])

@dataclass(slots=True)
class ChatTranscript:
    conversation_id: str
    tenant_id: str
    provider_id: str
    messages: List[Dict[str, object]]
    goal: str
    context: Optional[str]
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class ChatTranscriptRepository:
    """MongoDB repository storing conversational planning transcripts."""

    def __init__(self, collection: Collection) -> None:
        self._collection = collection
        self._ensure_indexes()

    def create(
        self,
        *,
        tenant_id: str,
        provider_id: str,
        goal: str,
        context: Optional[str],
        messages: List[Dict[str, object]],
    ) -> ChatTranscript:
        conversation_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc)
        document = {
            "conversation_id": conversation_id,
            "tenant_id": tenant_id,
            "provider_id": provider_id,
            "goal": goal,
            "context": context,
            "messages": messages,
            "created_at": created_at,
        }
        self._collection.insert_one(document)
        return _document_to_chat_transcript(document)

    def list(self, tenant_id: str) -> List[ChatTranscript]:
        cursor = self._collection.find({"tenant_id": tenant_id}).sort("created_at", DESCENDING)
        return [_document_to_chat_transcript(doc) for doc in cursor]

    def _ensure_indexes(self) -> None:
        self._collection.create_index([("tenant_id", ASCENDING), ("conversation_id", ASCENDING)], unique=True)
        self._collection.create_index([("tenant_id", ASCENDING), ("created_at", DESCENDING)])


def _document_to_record(document: Dict[str, object]) -> PlanRecord:
    created_at = document.get("created_at")
    if isinstance(created_at, datetime):
        created_dt = created_at if created_at.tzinfo else created_at.replace(tzinfo=timezone.utc)
    else:
        created_dt = datetime.fromtimestamp(float(created_at), tz=timezone.utc)
    result_payload = document.get("result", {})
    if not isinstance(result_payload, dict):
        result_payload = {}
    result = dto.KernelRunResult.from_dict(result_payload)
    return PlanRecord(
        plan_id=str(document.get("plan_id")),
        tenant_id=str(document.get("tenant_id")),
        goal_id=document.get("goal_id"),
        variant=document.get("variant"),
        parent_plan_id=document.get("parent_plan_id"),
        request_payload=dict(document.get("request_payload", {})),
        result=result,
        created_at=created_dt,
    )


def _kernel_result_to_dict(result: dto.KernelRunResult) -> Dict[str, object]:
    if result.raw:
        return dict(result.raw)
    solution = _solution_to_dict(result.solution)
    diagnostics = result.diagnostics.raw or asdict(result.diagnostics)
    policy = _policy_to_dict(result.policy)
    llm_summary = _llm_summary_to_dict(result.llm_summary)
    payload: Dict[str, object] = {
        "evidence_ref": result.evidence_ref,
        "solution": solution,
        "diagnostics": diagnostics,
    }
    if result.scenario_set:
        payload["forecast"] = _scenario_set_to_dict(result.scenario_set)
    if result.optimodel:
        payload["optimodel"] = asdict(result.optimodel)
    if policy:
        payload["policy"] = policy
    if llm_summary:
        payload["llm_summary"] = llm_summary
    return payload


def _policy_to_dict(policy: Optional[dto.PolicySnapshot]) -> Optional[Dict[str, object]]:
    if policy is None:
        return None
    return {
        "allow": policy.allow,
        "policy_id": policy.policy_id,
        "reasons": list(policy.reasons),
        "warnings": list(policy.warnings),
        "controls": dict(policy.controls),
    }


def _llm_summary_to_dict(summary: Optional[dto.LLMSummary]) -> Optional[Dict[str, object]]:
    if summary is None:
        return None
    return {
        "text": summary.text,
        "source": summary.source,
        "model": summary.model,
        "error": summary.error,
        "prompt_tokens": summary.prompt_tokens,
        "completion_tokens": summary.completion_tokens,
        "prompt": summary.prompt,
    }


def _solution_to_dict(solution: dto.Solution) -> Dict[str, object]:
    return {
        "status": solution.status,
        "gap": solution.gap,
        "kpis": dict(solution.kpis),
        "steps": [
            {
                "sku": step.sku,
                "supplier": step.supplier,
                "period": step.period,
                "quantity": step.quantity,
                "price": step.price,
            }
            for step in solution.steps
        ],
        "binding_constraints": list(solution.binding_constraints),
        "activities": dict(solution.activities),
        "shadow_prices": dict(solution.shadow_prices),
    }


def _scenario_set_to_dict(scenario_set: dto.ScenarioSet) -> Dict[str, object]:
    return {
        "horizon": scenario_set.horizon,
        "num_scenarios": scenario_set.num_scenarios,
        "skus": list(scenario_set.skus),
        "scenarios": [
            {
                "id": scenario.id,
                "demand": scenario.demand,
                "lead_time_days": scenario.lead_time_days,
            }
            for scenario in scenario_set.scenarios
        ],
        "stats": scenario_set.stats,
    }


def _document_to_chat_transcript(document: Dict[str, object]) -> ChatTranscript:
    created_at = document.get("created_at")
    if isinstance(created_at, datetime):
        created_dt = created_at if created_at.tzinfo else created_at.replace(tzinfo=timezone.utc)
    else:
        created_dt = datetime.fromtimestamp(float(created_at), tz=timezone.utc)
    return ChatTranscript(
        conversation_id=str(document.get("conversation_id")),
        tenant_id=str(document.get("tenant_id")),
        provider_id=str(document.get("provider_id", "unknown")),
        goal=str(document.get("goal", "")),
        context=document.get("context"),
        messages=list(document.get("messages", [])),
        created_at=created_dt,
    )
