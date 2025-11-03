"""In-memory compliance fact registry."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


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
    def __init__(self) -> None:
        self._facts: Dict[str, ComplianceFact] = {}
        self._by_run: Dict[str, List[str]] = {}

    def record(self, fact: ComplianceFact) -> ComplianceFact:
        self._facts[fact.fact_id] = fact
        self._by_run.setdefault(fact.run_id, []).append(fact.fact_id)
        return fact

    def list_for_run(self, run_id: str) -> List[ComplianceFact]:
        return [self._facts[fid] for fid in self._by_run.get(run_id, [])]

    def get(self, fact_id: str) -> Optional[ComplianceFact]:
        return self._facts.get(fact_id)


GLOBAL_FACT_REGISTRY = FactRegistry()

