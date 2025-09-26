"""Tenant-aware scheduler providing WFQ, rate limits, and budget enforcement."""
from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict, List, Optional


class RateLimitExceeded(Exception):
    """Raised when a tenant exceeds the allowed request rate."""


class BudgetExceeded(Exception):
    """Raised when a tenant exceeds allocated budget."""


@dataclass
class TenantBudget:
    solver_sec: float
    gpu_sec: float
    llm_tokens: float

    def subtract(self, cost: "CostEstimate") -> None:
        self.solver_sec -= cost.solver_sec
        self.gpu_sec -= cost.gpu_sec
        self.llm_tokens -= cost.llm_tokens

    def check(self) -> None:
        if self.solver_sec < 0 or self.gpu_sec < 0 or self.llm_tokens < 0:
            raise BudgetExceeded("Tenant budgets exhausted")


@dataclass
class TierConfig:
    name: str
    weight: int
    rate_limit_per_minute: int
    default_budget: TenantBudget


@dataclass
class CostEstimate:
    solver_sec: float = 0.0
    gpu_sec: float = 0.0
    llm_tokens: float = 0.0


@dataclass
class TenantRequest:
    tenant_id: str
    tier: str
    cost: CostEstimate
    timestamp: float = field(default_factory=time.time)


@dataclass
class RunLease:
    tenant_id: str
    tier: str
    scheduler: "TenantScheduler"
    estimate: CostEstimate
    acquired: float

    def complete(self, actual: Optional[CostEstimate] = None) -> None:
        self.scheduler.release(self, actual or self.estimate)


class TenantState:
    def __init__(self, budgets: TenantBudget) -> None:
        self.remaining = TenantBudget(**budgets.__dict__)
        self.rate_history: Deque[float] = deque()
        self.virtual_finish: float = 0.0


class TenantScheduler:
    """Simple WFQ scheduler with rate limit and budget tracking."""

    def __init__(self) -> None:
        self._tiers: Dict[str, TierConfig] = {}
        self._states: Dict[str, TenantState] = {}
        self._queue: Deque[TenantRequest] = deque()

    def register_tier(self, config: TierConfig) -> None:
        self._tiers[config.name] = config

    def acquire(self, tenant_id: str, tier_name: str, estimate: CostEstimate) -> RunLease:
        tier = self._tiers.get(tier_name)
        if tier is None:
            raise ValueError(f"Unknown tier: {tier_name}")
        state = self._states.setdefault(tenant_id, TenantState(tier.default_budget))
        self._enforce_rate_limit(tenant_id, tier, state)
        preview = CostEstimate(
            solver_sec=estimate.solver_sec,
            gpu_sec=estimate.gpu_sec,
            llm_tokens=estimate.llm_tokens,
        )
        state.remaining.subtract(preview)
        state.remaining.check()
        request = TenantRequest(tenant_id=tenant_id, tier=tier_name, cost=estimate)
        self._queue.append(request)
        chosen = self._select_next()
        lease = RunLease(
            tenant_id=chosen.tenant_id,
            tier=chosen.tier,
            scheduler=self,
            estimate=chosen.cost,
            acquired=time.time(),
        )
        return lease

    def release(self, lease: RunLease, actual: CostEstimate) -> None:
        state = self._states[lease.tenant_id]
        tier = self._tiers[lease.tier]
        # refund preview (already subtracted) and subtract actual cost
        state.remaining.solver_sec += lease.estimate.solver_sec - actual.solver_sec
        state.remaining.gpu_sec += lease.estimate.gpu_sec - actual.gpu_sec
        state.remaining.llm_tokens += lease.estimate.llm_tokens - actual.llm_tokens
        state.remaining.check()
        work = actual.solver_sec + 0.5 * actual.gpu_sec + actual.llm_tokens / 1000.0
        state.virtual_finish += work / max(tier.weight, 1)

    def _enforce_rate_limit(self, tenant_id: str, tier: TierConfig, state: TenantState) -> None:
        now = time.time()
        window = 60.0
        history = state.rate_history
        while history and now - history[0] > window:
            history.popleft()
        if len(history) >= tier.rate_limit_per_minute:
            raise RateLimitExceeded(f"Rate limit exceeded for tenant {tenant_id}")
        history.append(now)

    def _select_next(self) -> TenantRequest:
        if not self._queue:
            raise RuntimeError("No pending requests")
        best_idx = 0
        best_score = float("inf")
        for idx, request in enumerate(self._queue):
            state = self._states[request.tenant_id]
            tier = self._tiers[request.tier]
            score = state.virtual_finish + 1.0 / max(tier.weight, 1)
            if score < best_score:
                best_score = score
                best_idx = idx
        chosen = list(self._queue)[best_idx]
        del self._queue[best_idx]
        return chosen
