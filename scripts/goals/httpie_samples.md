```bash
# Create goal
http POST :8000/goals Authorization:"Bearer tenant_demo" \
  name="Inventory" \
  goaldsl:='{"objective":{"cost":1.0}}' \
  context:='{"skus":["SKU1"],"horizon":4}'

# Validate goal
http POST :8000/goals/$GOAL_ID/validate Authorization:"Bearer tenant_demo" \
  scenarios:='{"horizon":0,"num_scenarios":0,"skus":[],"scenarios":[]}'

# Approve goal (triggers plan creation)
http POST :8000/goals/$GOAL_ID/status Authorization:"Bearer tenant_demo" status=READY_TO_PLAN

# Add feedback (actuals)
http POST :8000/goals/$GOAL_ID/feedback Authorization:"Bearer tenant_demo" \
  actuals:='{"SKU1":{"2025-09-01":120}}'
```
