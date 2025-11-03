# Forecast Service

Forecast service exposing `/v1/forecast` via FastAPI. Uses Holt-Winters exponential smoothing (statsmodels) when available, falling back to a naive forecast otherwise. Install `numpy`, `pandas`, and `statsmodels` (included in `requirements-dev.txt`) to enable advanced forecasting.

## Run locally

```bash
source .venv/bin/activate
PYTHONPATH=. uvicorn services.forecast.main:app --reload --port 8003
```

Sample request:

```bash
curl -X POST http://localhost:8003/v1/forecast \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer demo-tenant" \
  -d '{
        "horizon": 3,
        "series": [
          {"name": "widget", "values": [100, 110, 120]},
          {"name": "gadget", "values": [80, 90, 95]}
        ]
      }'
```
