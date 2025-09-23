# Forecast — DESIGN (Detailed, Corrected)

Provides **demand** and **lead‑time** scenarios for robust planning. Combines classical models (Prophet/sktime/ARIMA) and **Darts** (RNN/TCN) with **Monte Carlo** sampling and returns distributional summaries used by OptiGuide.

---

## 1) Inputs & Outputs
**Inputs:** sales history (sku, period, qty), calendar/events, supplier lead‑time history, seasonality flags.  
**Outputs:** `scenarios[]` with `(demand_t, lead_time)` plus aggregates: mean, σ, p95 (per sku/period).

## 2) Pipeline
```mermaid
flowchart LR
  A[Raw History + Calendar] --> B(Preprocess: outliers, gaps, rolling features)
  B --> C(Model Select per SKU: Naive|Prophet|ARIMA|Darts)
  C --> D(Time CV & Fit)
  D --> E(Point Forecasts)
  E --> F(Residual Bootstrap + Lead‑time sampling)
  F --> G(Assemble N Scenarios)
  G --> H(Distribution Stats)
  H --> I[[OptiGuide]]
```

## 3) Sequence
```mermaid
sequenceDiagram
  participant OG as OptiGuide
  participant FC as Forecast
  OG->>FC: GET /scenarios {skus, horizon}
  FC->>FC: preprocess & features
  FC->>FC: fit models per sku; compute residuals
  FC->>FC: simulate N=50 scenarios
  FC-->>OG: scenarios[], stats (mean, σ, p95)
```

## 4) Modeling Notes
- **Prophet/ARIMA** for short or seasonal series; **Darts RNN/TCN** when history is long.
- Residual bootstrap for Monte Carlo; truncate negative demand to 0.
- Lead‑time sampling: empirical KDE or log‑normal; cap by SLA.
- Optionally blend models using CV weights.

## 5) Configuration
```json
{"horizon_periods": 4, "num_scenarios": 50, "model":"auto", "clip_negative": true}
```

## 6) Data Quality
- Great Expectations checks: non‑negative qty, monotonic dates, missingness thresholds.
- Warn on insufficient history; fall back to naive + wider variance.

---
## 7) Hierarchical, Intermittent & Reconciliation
- **Hierarchy**: fit per node and reconcile via **MinT** (covariance‑weighted) to keep sums consistent across SKU→category→location.
- **Intermittent demand**: **Croston/SBA/TSB**; switch automatically if %zeros > θ.
- **Group effects**: hierarchical Bayes priors by cuisine/segment to improve cold starts.

---
## 8) Conformal Prediction & Quantiles
- Produce **quantile forecasts** (τ = 0.1…0.9) and compute conformal **prediction intervals** with finite‑sample coverage.
- Export `{ lower, upper }` per period/sku for OptiGuide’s conformal mode.

---
## 9) Lead‑Time & Reliability Modeling
- Use **survival models** (CoxPH/AFT) or empirical KDE for lead‑time; emit hazard of delay.
- Supplier reliability score updated with feedback loop; feed as penalty in OptiGuide.

---
## 10) Scenario Generation Details
- **Sampling**: Latin Hypercube + antithetic pairs to cover tails.
- **Reduction hooks**: provide distance matrix for Optimizer’s k‑medoids/forward selection.
- **Caching key**: hash(sku, horizon, model_cfg, seed) → reuse across runs.

---
## 11) API Contract (Internal)
**POST** `/forecast/scenarios`  
**Request**: `{ tenant_id, tier, skus[], horizon, num_scenarios, model?, seed? }`  
**Response**: `ScenarioSet`

### 11.1 JSON Schema — `ScenarioSet`
```json
{
  "type":"object",
  "properties":{
    "horizon":{"type":"integer"},
    "num_scenarios":{"type":"integer"},
    "skus":{"type":"array","items":{"type":"string"}},
    "scenarios":{"type":"array","items":{"type":"object","properties":{
      "id":{"type":"integer"},
      "demand":{"type":"object","additionalProperties":{"type":"number"}},
      "lead_time_days":{"type":"number"}
    }}},
    "stats":{"type":"object","additionalProperties":{"type":"object"}}
  },
  "required":["horizon","num_scenarios","skus","scenarios"]
}
```

### 11.2 FastAPI Stub
```python
from fastapi import APIRouter, Header
from pydantic import BaseModel
router = APIRouter(prefix="/forecast", tags=["forecast"])

class Scenario(BaseModel):
    id: int
    demand: dict[str, float]
    lead_time_days: float
class ScenarioSet(BaseModel):
    horizon: int
    num_scenarios: int
    skus: list[str]
    scenarios: list[Scenario]
    stats: dict[str, dict] | None = None

@router.post("/scenarios")
def scenarios(body: dict, idempotency_key: str = Header(alias="Idempotency-Key")) -> ScenarioSet:
    # TODO: validate tenant_id, tier; generate or fetch cached scenarios
    return ScenarioSet(horizon=4, num_scenarios=2, skus=["DEMO"], scenarios=[
        Scenario(id=0, demand={"t1":100}, lead_time_days=2.0),
        Scenario(id=1, demand={"t1":120}, lead_time_days=3.0),
    ])
```
