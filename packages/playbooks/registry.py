"""In-memory playbook registry with simple keyword matching."""

from __future__ import annotations

import re
from typing import Iterable, List, Optional

from .models import DecisionPlaybook


class PlaybookRegistry:
    def __init__(self, playbooks: Iterable[DecisionPlaybook]):
        self._playbooks = list(playbooks)

    def match(self, goal: str) -> Optional[DecisionPlaybook]:
        goal_lower = goal.lower()
        for playbook in self._playbooks:
            if any(re.search(rf"\b{re.escape(keyword.lower())}\b", goal_lower) for keyword in playbook.keywords):
                return playbook
        return None

    def all(self) -> List[DecisionPlaybook]:
        return list(self._playbooks)


def load_default_playbooks() -> List[DecisionPlaybook]:
    return [
        DecisionPlaybook(
            id="inventory_baseline",
            name="Inventory Replenishment",
            description="Optimise stock levels with holding and shortage trade-offs.",
            version="1.0.0",
            prompt_guidelines=(
                "Use safety stock concepts when demand variability is described. "
                "Consider lead times if provided. Prioritise service level >= 95%. "
                "Emit KPIs for stockouts and carrying cost."
            ),
            keywords=["inventory", "stock", "sku", "warehouse"],
            tags=["supply_chain", "inventory"],
        ),
        DecisionPlaybook(
            id="staffing_shift",
            name="Shift Scheduling",
            description="Allocate staff to time slots respecting coverage targets.",
            version="1.0.0",
            prompt_guidelines=(
                "Model decision variables as headcount per shift. "
                "Enforce labour hour limits and required coverage. "
                "Expose KPIs for utilisation and overtime."
            ),
            keywords=["staffing", "rota", "schedule", "shift"],
            tags=["workforce"],
        ),
    ]

