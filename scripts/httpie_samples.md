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
```
