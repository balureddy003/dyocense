"""Compliance fact registry with persistence support."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from packages.kernel_common.persistence import InMemoryCollection, get_collection


class ComplianceFact(BaseModel):
    fact_id: str = Field(..., description="Unique fact identifier.")
    run_id: str = Field(..., description="Associated decision run or version.")
    tenant_id: str = Field(..., description="Tenant that owns the fact.")
    category: str = Field(..., description="Category (e.g., policy, safety, audit).")
    statement: str = Field(..., description="Natural language description of the fact.")
    status: str = Field(..., description="State such as satisfied, violated, pending.")
    source: str | None = Field(default=None, description="Source system or policy pack.")
    metadata: Dict[str, str] = Field(
        default_factory=dict,
        description="Additional structured data (policy ids, evidence URIs, etc.).",
    )
    recorded_at: datetime = Field(default_factory=datetime.utcnow)


class FactRegistry:
    def __init__(self, collection=None) -> None:
        self._collection = collection or get_collection("compliance_facts")
        self._is_fallback = isinstance(self._collection, InMemoryCollection)
        self._facts: Dict[str, ComplianceFact] = {}
        self._by_run: Dict[str, List[str]] = {}
        self._load_existing()

    def record(self, fact: ComplianceFact) -> ComplianceFact:
        self._facts[fact.fact_id] = fact
        self._by_run.setdefault(fact.run_id, []).append(fact.fact_id)
        self._persist(fact)
        return fact

    def list_for_run(self, run_id: str) -> List[ComplianceFact]:
        return [self._facts[fid] for fid in self._by_run.get(run_id, [])]

    def get(self, fact_id: str) -> Optional[ComplianceFact]:
        return self._facts.get(fact_id)

    def _load_existing(self) -> None:
        try:
            if hasattr(self._collection, "find") and not self._is_fallback:
                for document in self._collection.find({}):  # type: ignore[attr-defined]
                    document.pop("_id", None)
                    self._hydrate(document)
            elif isinstance(self._collection, InMemoryCollection):
                for document in self._collection.find({}):
                    self._hydrate(document)
        except Exception:  # pragma: no cover
            pass

    def _persist(self, fact: ComplianceFact) -> None:
        document = fact.model_dump()
        try:
            if hasattr(self._collection, "replace_one") and not self._is_fallback:
                self._collection.replace_one({"fact_id": fact.fact_id}, document, upsert=True)  # type: ignore[attr-defined]
            elif isinstance(self._collection, InMemoryCollection):
                self._collection.replace_one({"fact_id": fact.fact_id}, document, upsert=True)
        except Exception:  # pragma: no cover
            pass

    def _hydrate(self, document: dict) -> None:
        try:
            fact = ComplianceFact.model_validate(document)
        except Exception:  # pragma: no cover
            return
        self._facts[fact.fact_id] = fact
        self._by_run.setdefault(fact.run_id, []).append(fact.fact_id)


GLOBAL_FACT_REGISTRY = FactRegistry()
