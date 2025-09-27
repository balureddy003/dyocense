```bash
# Ingest actuals
http POST :8000/feedback/ingest Authorization:"Bearer tenant_demo" \
  goal_id=goal_1 plan_id=plan_1 \
  actuals:='[{"sku":"SKU1","period":"2025-09-01","quantity":120}]'

# KPI drift report
http GET :8000/feedback/kpi-drift Authorization:"Bearer tenant_demo"
```
