# Open Decision Spec (ODS)
Version: ops.v1 / pack.v1 (JSON-Schema 2020-12)

## OPS Minimal Example
```json
{
  "metadata": {"ops_version":"1.0.0","problem_type":"inventory","tenant_id":"t_abc","project_id":"p1","run_tags":["demo"]},
  "objective": {"sense":"min","expression":"sum(h[i]*x[i] + p[i]*b[i] for i in I)"},
  "decision_variables": [
    {"name":"x[i]","type":"integer","lb":0,"ub":100000,"index_sets":["I"]},
    {"name":"b[i]","type":"integer","lb":0,"ub":100000,"index_sets":["I"]}
  ],
  "parameters": {
    "I":["SKU1","SKU2"],
    "d":{"SKU1":120,"SKU2":80},
    "stock":{"SKU1":50,"SKU2":10},
    "h":{"SKU1":0.2,"SKU2":0.3},
    "p":{"SKU1":5.0,"SKU2":6.0},
    "_units":{"x":"units","b":"units","h":"£/unit/wk","p":"£/unit"}
  },
  "constraints":[{"name":"balance[i]","for_all":"I","expression":"stock[i] + x[i] - b[i] >= d[i]"}],
  "kpis":[{"name":"fill_rate","expression":"1 - sum(b[i] for i in I)/sum(d[i] for i in I)"}],
  "validation_notes":[]
}
```

## SolutionPack Minimal Example
```json
{"status":"optimal","objective_value":243.7,"decisions":{"x":{"SKU1":70,"SKU2":90},"b":{"SKU1":0,"SKU2":0}},
 "kpis":{"fill_rate":0.99},"diagnostics":{"gap":0.0,"runtime_ms":183,"solver":"ortools-cpsat"},
 "explanation_hints":{"binding":"balance[SKU2]","cost_drivers":["p","h"]},
 "artifacts":{"ops_ref":"s3://bucket/runs/123/ops.json"}}
```
