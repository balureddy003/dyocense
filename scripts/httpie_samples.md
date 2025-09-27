```bash
# Forecast Scenarios (standard tier)
http POST $KERNEL/forecast/scenarios \
  Authorization:"Bearer $JWT" \
  Idempotency-Key:idem_$(date +%s) \
  tenant_id=tenant_std tier=standard \
  skus:='["SKU1","SKU2"]' horizon:=4 num_scenarios:=40 seed:=2025

# OptiGuide Compile (DRO mode)
http POST $KERNEL/optiguide/compile \
  Authorization:"Bearer $JWT" \
  Idempotency-Key:idem_$(date +%s) \
  tenant_id=tenant_pro tier=pro \
  goal_dsl:='{"objective":{"cost":0.5,"service":0.2,"setup_cost":0.3},"constraints":{"budget_month":12000,"robust":{"mode":"dro_wasserstein"}}}' \
  context:=@context.json scenarios:=@scenarios.json

# Optimizer Solve with reduction + LNS
http POST $KERNEL/optimizer/solve \
  Authorization:"Bearer $JWT" \
  Idempotency-Key:idem_$(date +%s) \
  tenant_id=tenant_pro tier=pro \
  optimodel:=@optimodel.json scenario_reduction:='{"k":20}' lns_iterations:='{"iterations":3}'

# Evidence Write
http POST $KERNEL/evidence/write \
  Authorization:"Bearer $JWT" \
  Idempotency-Key:idem_$(date +%s) \
  tenant_id=tenant_std plan_id=plan_123 \
  solution:=@solution.json constraints:='["budget","service_min"]' diagnostics:=@diagnostics.json \
  metadata:='{"seed":2025,"optimodel_sha":"sha256:abc123","plan_dna":"sha256:def456"}'

# Backend — create baseline plan
http POST :8000/plans Authorization:"Bearer tenant_demo" \
  goal_id=goal_123 variant=baseline \
  kernel_payload:='{"goaldsl":{"objective":{"cost":1.0}},"seed":4242}'

# Backend — delta plan (tight budget)
http POST :8000/plans/$PLAN_ID/delta Authorization:"Bearer tenant_demo" \
  variant_suffix=tight \
  kernel_payload:='{"constraints":{"budget_month":8500}}'

# Backend — counterfactual (remove supplier)
http POST :8000/plans/$PLAN_ID/counterfactual Authorization:"Bearer tenant_demo" \
  variant_suffix=no-sup1 \
  kernel_payload:='{"context":{"remove_suppliers":{"SKU1":["SUP1"]}}}'

# Backend — create goal
http POST :8000/goals Authorization:"Bearer tenant_demo" \
  name="Inventory" \
  goaldsl:='{"objective":{"cost":1.0}}' \
  context:='{"skus":["SKU1"]}'

# Backend — validate goal
http POST :8000/goals/$GOAL_ID/validate Authorization:"Bearer tenant_demo" \
  scenarios:='{"horizon":0,"num_scenarios":0,"skus":[],"scenarios":[]}'

# Backend — approve goal (triggers plan)
http POST :8000/goals/$GOAL_ID/status Authorization:"Bearer tenant_demo" \
  status=READY_TO_PLAN
```
