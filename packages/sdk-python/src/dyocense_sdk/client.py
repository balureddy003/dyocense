from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx

DEFAULT_BASE_URL = "http://localhost:8001"
DEFAULT_SERVICE_URLS = {
    "compile": DEFAULT_BASE_URL,
    "forecast": DEFAULT_BASE_URL,
    "policy": DEFAULT_BASE_URL,
    "optimise": DEFAULT_BASE_URL,
    "diagnose": DEFAULT_BASE_URL,
    "explain": DEFAULT_BASE_URL,
    "evidence": DEFAULT_BASE_URL,
    "orchestrator": DEFAULT_BASE_URL,
}


@dataclass
class DecisionResult:
    ops: Dict[str, Any]
    forecasts: Dict[str, Any]
    policy: Dict[str, Any]
    solution: Dict[str, Any]
    diagnostics: Dict[str, Any]
    explanation: Dict[str, Any]
    evidence_receipt: Dict[str, Any]


class DyocenseClient:
    """Thin wrapper around the Dyocense Decision Kernel HTTP endpoints."""

    def __init__(
        self,
        token: str,
        service_urls: Optional[Dict[str, str]] = None,
        timeout: float = 30.0,
        base_url: Optional[str] = None,
    ) -> None:
        base_map = {
            service: base_url or DEFAULT_SERVICE_URLS[service]
            for service in DEFAULT_SERVICE_URLS
        }
        self._service_urls = {**base_map, **(service_urls or {})}
        self._timeout = timeout
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def compile(self, goal: str, tenant_id: Optional[str] = None, project_id: str = "sdk-run") -> Dict[str, Any]:
        payload = {
            "goal": goal,
            "tenant_id": tenant_id or "sdk-tenant",
            "project_id": project_id,
        }
        return self._post("compile", "/v1/compile", payload)["ops"]

    def forecast(self, ops: Dict[str, Any], horizon: int = 2) -> Dict[str, Any]:
        demand = ops.get("parameters", {}).get("demand", {})
        series = [
            {"name": name, "values": [value]}
            for name, value in demand.items()
        ]
        payload = {"horizon": horizon, "series": series}
        return self._post("forecast", "/v1/forecast", payload)

    def policy(self, ops: Dict[str, Any], tenant_id: Optional[str] = None) -> Dict[str, Any]:
        payload = {"ops": ops}
        if tenant_id:
            payload["tenant_id"] = tenant_id
        return self._post("policy", "/v1/policy/evaluate", payload)

    def optimise(self, ops: Dict[str, Any]) -> Dict[str, Any]:
        return self._post("optimise", "/v1/optimise", {"ops": ops})["solution"]

    def diagnose(self, ops: Dict[str, Any], solution: Dict[str, Any]) -> Dict[str, Any]:
        return self._post("diagnose", "/v1/diagnose", {"ops": ops, "solution": solution})

    def explain(
        self,
        goal: str,
        solution: Dict[str, Any],
        forecasts: Dict[str, Any],
        policy: Dict[str, Any],
        diagnostics: Dict[str, Any],
    ) -> Dict[str, Any]:
        payload = {
            "goal": goal,
            "solution": solution,
            "forecasts": forecasts.get("forecasts", []),
            "policy": policy,
            "diagnostics": diagnostics,
        }
        return self._post("explain", "/v1/explain", payload)

    def evidence(
        self,
        run_id: str,
        tenant_id: str,
        ops: Dict[str, Any],
        solution: Dict[str, Any],
        explanation: Dict[str, Any],
    ) -> Dict[str, Any]:
        payload = {
            "run_id": run_id,
            "tenant_id": tenant_id,
            "ops": ops,
            "solution": solution,
            "explanation": explanation,
        }
        return self._post("evidence", "/v1/evidence/log", payload)

    def submit_run(
        self,
        goal: str,
        tenant_id: str = "sdk-tenant",
        project_id: Optional[str] = None,
        horizon: int = 2,
        series: Optional[list] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "goal": goal,
            "project_id": project_id,
            "horizon": horizon,
            "series": series,
        }
        return self._post("orchestrator", "/v1/runs", payload)

    def get_run(self, run_id: str) -> Dict[str, Any]:
        return self._get("orchestrator", f"/v1/runs/{run_id}")

    def run_decision_flow(
        self,
        goal: str,
        tenant_id: str = "sdk-tenant",
        project_id: str = "sdk-run",
        horizon: int = 2,
    ) -> DecisionResult:
        ops = self.compile(goal=goal, tenant_id=tenant_id, project_id=project_id)
        forecasts = self.forecast(ops, horizon=horizon)
        policy_result = self.policy(ops, tenant_id=tenant_id)
        solution = self.optimise(ops)
        diagnostics = self.diagnose(ops, solution)
        explanation = self.explain(goal, solution, forecasts, policy_result, diagnostics)
        receipt = self.evidence(
            run_id=solution["metadata"]["run_id"],
            tenant_id=tenant_id,
            ops=ops,
            solution=solution,
            explanation=explanation,
        )
        return DecisionResult(
            ops=ops,
            forecasts=forecasts,
            policy=policy_result,
            solution=solution,
            diagnostics=diagnostics,
            explanation=explanation,
            evidence_receipt=receipt,
        )

    def _post(self, service: str, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self._service_urls[service]}{path}"
        with httpx.Client(timeout=self._timeout) as client:
            response = client.post(url, json=payload, headers=self._headers)
            response.raise_for_status()
            return response.json()

    def _get(self, service: str, path: str) -> Dict[str, Any]:
        url = f"{self._service_urls[service]}{path}"
        with httpx.Client(timeout=self._timeout) as client:
            response = client.get(url, headers=self._headers)
            response.raise_for_status()
            return response.json()
