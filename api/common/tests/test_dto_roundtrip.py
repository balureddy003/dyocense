from api.common import dto


def test_kernel_run_result_roundtrip():
    payload = {
        "evidence_ref": "evidence://abc",
        "forecast": {
            "horizon": 2,
            "num_scenarios": 1,
            "skus": ["SKU1"],
            "scenarios": [
                {"id": 0, "demand": {"SKU1": {"t1": 10}}, "lead_time_days": {"SKU1": 2}}
            ],
            "stats": {"SKU1": {"mean": 10.0}},
        },
        "solution": {
            "status": "FEASIBLE",
            "gap": 0.0,
            "kpis": {"total_cost": 100.0},
            "steps": [
                {
                    "sku": "SKU1",
                    "supplier": "SUP1",
                    "period": "t1",
                    "quantity": 10,
                    "price": 10.0,
                }
            ],
            "binding_constraints": ["budget"],
            "activities": {"budget": 100.0},
            "shadow_prices": {},
        },
        "diagnostics": {"reduction": {"original_count": 1, "reduced_count": 1}},
        "policy": {
            "allow": True,
            "policy_id": "policy.guard.v1",
            "reasons": [],
            "warnings": [],
            "controls": {"tier": "pro"},
        },
        "llm_summary": {
            "text": "Plan looks good",
            "source": "fallback",
            "model": None,
        },
    }
    result = dto.KernelRunResult.from_dict(payload)
    assert result.evidence_ref == "evidence://abc"
    assert result.solution.status == "FEASIBLE"
    assert result.solution.steps[0].sku == "SKU1"
    assert result.diagnostics.reduction["original_count"] == 1
    assert result.policy and result.policy.allow
    assert result.llm_summary and result.llm_summary.source == "fallback"
