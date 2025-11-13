"""
Goal Metabolism (Phase-1 outline)

Lightweight heuristic model to estimate 'fitness energy' capacity for achieving goals
based on current workload, recent activity, and health score context.

Outputs a snapshot that the coach can use to pace recommendations and scheduling.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta


@dataclass
class MetabolismSnapshot:
    energy_capacity: int              # 0-100 overall fitness energy to pursue goals
    fatigue: float                    # 0.0-1.0 fatigue factor (higher means more fatigued)
    recovery_rate: float              # 0.0-1.0 daily recovery factor
    workload_index: float             # 0.0-1.0 derived from active goals/tasks
    projected_weekly_capacity: int    # estimated tasks user can complete this week
    risks: List[str]                  # textual flags
    basis: Dict[str, Any]             # inputs used for transparency


def _safe_int(v: Optional[float], default: int) -> int:
    try:
        return int(v) if v is not None else default
    except Exception:
        return default


def compute_metabolism(
    health_score: Dict[str, Any],
    goals: List[Dict[str, Any]],
    tasks: List[Dict[str, Any]],
    recent_activity_days: int = 14,
) -> MetabolismSnapshot:
    """
    P1 heuristic:
    - Base energy from health score (60% overall, 20% operations, 20% customer if available)
    - Workload index from active goals and pending tasks
    - Fatigue increases with workload; recovery pegged to customer score and recent activity
    - Project weekly capacity from energy and workload
    """
    # Base energy from health score
    score = _safe_int(health_score.get("score"), 50)
    bkd = (health_score.get("breakdown") or {})
    ops_raw = bkd.get("operations")
    cust_raw = bkd.get("customer")
    ops = None if ops_raw is None else _safe_int(ops_raw, 50)
    cust = None if cust_raw is None else _safe_int(cust_raw, 50)

    # weighted base energy
    parts = [0.6 * score]
    if ops is not None:
        parts.append(0.2 * ops)
    if cust is not None:
        parts.append(0.2 * cust)
    base_energy = int(min(100, max(0, sum(parts))))

    # Workload index
    active_goals = [g for g in goals if (g.get("status") or "").lower() in ("active", "in_progress", "in progress")]
    todo_tasks = [t for t in tasks if (t.get("status") or "").lower() in ("todo", "pending", "not_started")]
    # Normalize: 5 goals and 20 tasks ≈ workload 1.0
    workload = min(1.0, (len(active_goals) / 5.0) * 0.5 + (len(todo_tasks) / 20.0) * 0.5)

    # Fatigue: grows with workload; reduced by good customer score (team/customer responsiveness)
    cust_score = cust if cust is not None else 50
    fatigue = min(1.0, max(0.0, 0.3 + 0.7 * workload - 0.002 * cust_score))

    # Recovery: influenced by operations/customer stability
    ops_score = ops if ops is not None else 50
    recovery = max(0.1, min(1.0, 0.2 + 0.003 * cust_score + 0.002 * ops_score))

    # Effective energy after fatigue
    effective_energy = int(max(0, min(100, base_energy * (1 - 0.5 * fatigue))))

    # Project weekly capacity (number of tasks achievable)
    # Scale with energy and inverse of workload. Minimum floor to avoid zero.
    base_capacity = 5 + int(0.15 * effective_energy)
    load_penalty = max(0.5, 1.2 - workload)  # more workload → smaller multiplier
    projected_weekly_capacity = max(3, int(base_capacity * load_penalty * (0.8 + 0.4 * recovery)))

    # Risk flags and recovery suggestions (Phase 2)
    risks: List[str] = []
    if workload > 0.85:
        risks.append("High workload; consider deferring or splitting goals")
    if effective_energy < 40:
        risks.append("Low energy; prioritize quick wins and recovery")
    if recovery < 0.25:
        risks.append("Slow recovery; improve operations/customer processes")
    
    # Phase 2: Fatigue-based recovery recommendations
    if fatigue > 0.7:
        risks.append("High fatigue detected; recommend recovery window (reduce new commitments for 3-5 days)")
    elif fatigue > 0.5:
        risks.append("Moderate fatigue; consider lighter tasks and focus on completion vs new starts")

    basis = {
        "health_score": {"score": score, "ops": ops, "cust": cust},
        "counts": {"active_goals": len(active_goals), "todo_tasks": len(todo_tasks)},
        "workload_index": round(workload, 3),
        "fatigue_level": round(fatigue, 3),
        "effective_energy": effective_energy,
    }

    return MetabolismSnapshot(
        energy_capacity=base_energy,
        fatigue=round(fatigue, 3),
        recovery_rate=round(recovery, 3),
        workload_index=round(workload, 3),
        projected_weekly_capacity=projected_weekly_capacity,
        risks=risks,
        basis=basis,
    )
