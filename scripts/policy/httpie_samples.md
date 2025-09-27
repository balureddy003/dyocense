```bash
# Create policy draft
http POST :8000/policies Authorization:"Bearer tenant_demo" \
  name="Budget Policy" \
  rules:='[{"name":"budget_cap","definition":{"max_budget":10000}}]' \
  thresholds:='{"scenario_cap":50}'

# Activate policy version
http POST :8000/policies/$POLICY_ID/activate Authorization:"Bearer tenant_demo" \
  version_id=$VERSION_ID note="Reviewed by Ops"

# Update thresholds
http POST :8000/policies/$POLICY_ID/thresholds Authorization:"Bearer tenant_demo" \
  thresholds:='{"scenario_cap":80}'

# List audits
http GET :8000/audits Authorization:"Bearer tenant_demo"
```
