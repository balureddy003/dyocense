# Report Generation Pipeline: Orchestration → Tools → Report

## How Optimizer & Forecasting Are Called Before Reports

### The Complete Flow

```
User Request: "Generate inventory optimization report with demand forecast"
       ↓
┌──────────────────────────────────────────────────────────────┐
│ 1. CoachOrchestrator.analyze_intent()                        │
│    • Detects: OPTIMIZATION + FORECAST task types             │
│    • Creates TaskPlan with required tools:                   │
│      - analyze_inventory                                     │
│      - forecast_demand                                       │
│      - optimize_inventory                                    │
│    • Determines execution order based on dependencies        │
└──────────────────┬───────────────────────────────────────────┘
                   ↓
┌──────────────────────────────────────────────────────────────┐
│ 2. ToolExecutor.execute() - Sequential Tool Execution        │
│                                                              │
│   Step 2a: Execute "analyze_inventory"                      │
│   ├─→ Calls: analysis_tools.analyze_inventory_data()        │
│   ├─→ Calculates: Stock health, valuations, ABC analysis    │
│   └─→ Returns: inventory_analysis = {                       │
│         "total_items": 541909,                              │
│         "stock_health": {...},                              │
│         "critical_issues": [...]                            │
│       }                                                      │
│                                                              │
│   Step 2b: Execute "forecast_demand"                        │
│   ├─→ Calls: forecast_tools.forecast_demand()              │
│   ├─→ Uses: Historical order data from inventory_analysis   │
│   ├─→ Runs: Time series forecasting model                  │
│   └─→ Returns: demand_forecast = {                         │
│         "horizon_days": 30,                                 │
│         "total_predicted_orders": 450,                      │
│         "forecasts": [{day, predicted_orders, ...}],        │
│         "recommendations": [...]                            │
│       }                                                      │
│                                                              │
│   Step 2c: Execute "optimize_inventory"                     │
│   ├─→ Calls: optimization_tools.optimize_inventory_levels() │
│   ├─→ Uses: Both inventory_analysis AND demand_forecast    │
│   ├─→ Runs: Optimization algorithm (EOQ, ML model)         │
│   └─→ Returns: optimization_result = {                     │
│         "recommendations": [{priority, action, impact}],    │
│         "optimal_parameters": {reorder_point, safety_stock},│
│         "expected_outcomes": {cost_savings, service_level}  │
│       }                                                      │
└──────────────────┬───────────────────────────────────────────┘
                   ↓
┌──────────────────────────────────────────────────────────────┐
│ 3. Results Aggregation                                       │
│    business_context["tool_results"] = {                     │
│      "inventory_analysis": {...},                           │
│      "demand_forecast": {...},                              │
│      "optimization": {...}                                   │
│    }                                                         │
└──────────────────┬───────────────────────────────────────────┘
                   ↓
┌──────────────────────────────────────────────────────────────┐
│ 4. Orchestrated Prompt Generation                           │
│    orchestrator.generate_system_prompt_for_plan(            │
│      task_plan=task_plan,                                   │
│      analysis_results=tool_results  ← ALL RESULTS HERE      │
│    )                                                         │
│                                                              │
│    Generated Prompt:                                        │
│    """                                                       │
│    # INVENTORY OPTIMIZATION REPORT                          │
│                                                              │
│    ## Current Inventory Status                              │
│    - Total Items: 541,909                                   │
│    - Stock Health: 85.2% in stock, 10.3% low, 4.5% out     │
│    - Total Value: $1,250,000                                │
│                                                              │
│    ## Demand Forecast (Next 30 Days)                        │
│    - Predicted Orders: 450                                  │
│    - Expected Revenue: $45,000                              │
│    - Growth Trend: +2% monthly                              │
│                                                              │
│    ## Optimization Recommendations                          │
│    1. [CRITICAL] Reorder 24,500 out-of-stock items          │
│       Impact: Prevent $122,500 in lost sales                │
│                                                              │
│    2. [HIGH] Replenish 55,000 low-stock items               │
│       Impact: Maintain 95%+ service level                   │
│                                                              │
│    3. [MEDIUM] Clear 81,286 slow-moving items               │
│       Impact: Free up $812,860 in capital                   │
│                                                              │
│    ## Optimal Parameters                                    │
│    - Reorder Point: 105 units                               │
│    - Safety Stock: 1.5x lead time demand                    │
│    - Expected Outcomes:                                     │
│      • 80% stockout reduction                               │
│      • $812,860 carrying cost savings                       │
│      • 95%+ service level                                   │
│                                                              │
│    Now write a comprehensive report using this data.        │
│    """                                                       │
└──────────────────┬───────────────────────────────────────────┘
                   ↓
┌──────────────────────────────────────────────────────────────┐
│ 5. LLM Report Generation                                     │
│    _invoke_llm(orchestrated_prompt)                         │
│    ↓                                                         │
│    LLM synthesizes all the data into human-readable report  │
│    with narrative, insights, and actionable recommendations │
└──────────────────┬───────────────────────────────────────────┘
                   ↓
┌──────────────────────────────────────────────────────────────┐
│ 6. Streaming Response to User                                │
│    """                                                       │
│    📊 Inventory Optimization Report                          │
│                                                              │
│    Based on analysis of your 541,909 inventory items,       │
│    here's your optimization strategy:                       │
│                                                              │
│    🚨 Immediate Actions Required:                            │
│    Your inventory shows 24,500 out-of-stock items (4.5%)    │
│    causing estimated lost sales of $122,500/month...        │
│    [continues with full narrative report]                   │
│    """                                                       │
└──────────────────────────────────────────────────────────────┘
```

## Code Examples

### Example 1: Forecast-Only Request

**User**: "Predict my sales for next month"

**Orchestrator detects**: `TaskType.FORECAST`

**Execution sequence**:

```python
# In MultiAgentCoach.stream_response()
task_plan = orchestrator.analyze_intent("predict my sales for next month", available_data)
# → task_plan.task_type = FORECAST
# → task_plan.required_tools = ["forecast_demand", "forecast_revenue"]

tool_results = {}
for tool_req in task_plan.required_tools:
    if tool_req.tool_name == "forecast_demand":
        result = tool_executor.execute("forecast_demand", business_context, horizon=30)
        tool_results["forecast_demand"] = result
    
    if tool_req.tool_name == "forecast_revenue":
        result = tool_executor.execute("forecast_revenue", business_context, horizon=30)
        tool_results["forecast_revenue"] = result

# Results now available:
# tool_results = {
#   "forecast_demand": {"total_predicted_orders": 450, "forecasts": [...]},
#   "forecast_revenue": {"total_predicted_revenue": 45000, ...}
# }

# Generate prompt with forecast data
prompt = orchestrator.generate_system_prompt_for_plan(
    task_plan=task_plan,
    available_data=available_data,
    analysis_results=tool_results  # ← Forecast results injected here
)

# LLM generates report using the forecast data
response = _invoke_llm(prompt)
```

### Example 2: Optimization-Only Request

**User**: "How can I optimize my inventory?"

**Orchestrator detects**: `TaskType.OPTIMIZATION`

**Execution sequence**:

```python
task_plan = orchestrator.analyze_intent("optimize my inventory", available_data)
# → task_plan.task_type = OPTIMIZATION
# → task_plan.required_tools = ["analyze_inventory", "optimize_inventory"]
# → task_plan.execution_order = ["analyze_inventory", "optimize_inventory"]

# Execute in dependency order
results = {}

# Step 1: Analyze current state
inventory_analysis = tool_executor.execute("analyze_inventory", business_context)
results["inventory_analysis"] = inventory_analysis

# Step 2: Run optimization using analysis results
business_context["inventory_analysis"] = inventory_analysis  # Pass to optimizer
optimization = tool_executor.execute("optimize_inventory", business_context)
results["optimization"] = optimization

# optimization = {
#   "recommendations": [
#     {"priority": "critical", "action": "Reorder 24,500 items", ...},
#     {"priority": "high", "action": "Replenish 55,000 items", ...}
#   ],
#   "expected_outcomes": {"cost_savings": "$812,860", ...}
# }
```

### Example 3: Complex Multi-Tool Request

**User**: "Generate complete business analysis with forecasting and optimization"

**Orchestrator detects**: Multiple task types

**Execution sequence**:

```python
task_plan = orchestrator.analyze_intent("complete business analysis", available_data)
# → Detects keywords: analysis, forecast, optimize
# → Creates compound task plan

# Execution order (respects dependencies):
execution_order = [
    "analyze_inventory",    # 1. Current state
    "analyze_revenue",      # 2. Historical trends
    "analyze_customers",    # 3. Customer behavior
    "forecast_demand",      # 4. Future predictions (needs historical data)
    "forecast_revenue",     # 5. Revenue projections
    "optimize_inventory",   # 6. Optimization (needs current + forecast)
    "optimize_pricing"      # 7. Pricing strategy
]

results = {}
for tool_name in execution_order:
    # Each tool can access previous results from business_context
    result = tool_executor.execute(tool_name, business_context)
    results[tool_name] = result
    business_context["tool_results"][tool_name] = result  # Available to next tools

# Now LLM has ALL analysis, forecasts, and optimization results
prompt = orchestrator.generate_system_prompt_for_plan(
    task_plan=task_plan,
    analysis_results=results  # ← Complete dataset
)
```

## External Agent Integration

### Calling Optimizer Agent Microservice

```python
# In optimization_tools.py
async def call_optimizer_agent(
    tenant_id: str,
    optimization_type: str,
    data: Dict[str, Any]
) -> Dict[str, Any]:
    """Call external optimizer microservice"""
    
    # Import optimizer client
    from services.optimiser.client import OptimizerClient
    
    client = OptimizerClient(base_url="http://optimiser:8005")
    
    # Send optimization request
    result = await client.optimize(
        tenant_id=tenant_id,
        optimization_type=optimization_type,  # "inventory", "pricing", "workforce"
        data={
            "current_inventory": data["inventory_analysis"],
            "demand_forecast": data["demand_forecast"],
            "constraints": {
                "budget": 50000,
                "storage_capacity": 100000,
                "service_level_target": 0.95
            }
        }
    )
    
    # result = {
    #   "optimized_inventory": {
    #     "sku": "ABC123",
    #     "current_level": 50,
    #     "optimal_level": 120,
    #     "reorder_point": 80,
    #     "order_quantity": 150,
    #     "expected_cost_savings": 450
    #   },
    #   ...
    # }
    
    return result

# Usage in optimize_inventory_levels():
optimization_result = await call_optimizer_agent(
    tenant_id=business_context["tenant_id"],
    optimization_type="inventory",
    data={
        "inventory_analysis": results["inventory_analysis"],
        "demand_forecast": results["demand_forecast"]
    }
)
```

### Calling Forecasting Service

```python
# In forecast_tools.py
async def call_forecasting_service(
    tenant_id: str,
    data_type: str,
    historical_data: List[Dict]
) -> Dict[str, Any]:
    """Call external forecasting microservice"""
    
    from services.forecast.client import ForecastClient
    
    client = ForecastClient(base_url="http://forecast:8006")
    
    # Send forecasting request
    result = await client.forecast(
        tenant_id=tenant_id,
        model_type="lstm",  # or "arima", "prophet", "xgboost"
        data={
            "time_series": historical_data,
            "horizon": 30,
            "frequency": "daily",
            "features": ["seasonality", "trend", "holidays"]
        }
    )
    
    # result = {
    #   "predictions": [
    #     {"date": "2025-11-13", "predicted_value": 45.2, "confidence_interval": [40.1, 50.3]},
    #     ...
    #   ],
    #   "model_metrics": {"mape": 8.5, "rmse": 3.2},
    #   "feature_importance": {"seasonality": 0.6, "trend": 0.3, "holidays": 0.1}
    # }
    
    return result
```

## Execution Order & Dependencies

### Dependency Graph

```
analyze_inventory ─┐
                   ├─→ optimize_inventory ─→ Report
forecast_demand ───┘

analyze_revenue ───┐
                   ├─→ optimize_pricing ─→ Report
forecast_revenue ──┘
```

**Rule**: Later tools can access results from earlier tools via `business_context["tool_results"]`

### Implementation in ToolExecutor

```python
# In multi_agent_coach.py
tool_results = {}

for tool_req in task_plan.required_tools:
    # Get tool name
    executor_tool_name = tool_mapping.get(tool_req.tool_name)
    
    # Execute tool (it can access business_context which includes previous results)
    result = self.tool_executor.execute(
        executor_tool_name,
        business_context,  # Contains previous tool_results
        **tool_req.parameters
    )
    
    if result:
        # Store result
        tool_results[tool_req.tool_name] = result
        
        # Make available to subsequent tools
        business_context["tool_results"][tool_req.tool_name] = result

# Now all results available for prompt generation
orchestrated_prompt = self.task_orchestrator.generate_system_prompt_for_plan(
    task_plan=task_plan,
    available_data=available_data,
    analysis_results=tool_results  # ← Complete result set
)
```

## Benefits of This Architecture

### ✅ Sequential Analysis Pipeline

Tools execute in order, each building on previous results

### ✅ Forecasting Before Optimization

Optimizer can use forecast data to make better recommendations

### ✅ All Results Available to LLM

Prompt includes complete analysis + forecast + optimization data

### ✅ Extensible

Add new tools without modifying orchestration logic

### ✅ External Service Integration

Easy to swap local tools with microservice calls

### ✅ Testable

Each tool can be tested independently with mock data

## Summary

**The key insight**: Tools execute **BEFORE** the LLM generates the report. The LLM receives:

1. ✅ Current state analysis (inventory, revenue, customers)
2. ✅ Future predictions (demand forecast, revenue projections)
3. ✅ Optimization recommendations (reorder points, pricing strategies)
4. ✅ Expected outcomes (cost savings, revenue lift)

Then the LLM **synthesizes** all this data into a coherent, narrative report with actionable insights! 🎯
