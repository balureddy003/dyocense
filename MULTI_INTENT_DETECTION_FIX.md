# Multi-Intent Detection Fix

## Problem Identified from Logs

**User Request**: "Generate inventory optimization report with demand forecast"

**Expected**: Detect 3 intents → inventory + optimization + forecast

**Actual**: Only detected 1 intent → inventory_analysis

**Root Cause**: Orchestrator stopped at first keyword match ("inventory") and never checked for "optimize" or "forecast"

## Solution Implemented

### 1. Added Optimization Intent Pattern

```python
"optimization": {
    "keywords": ["optimize", "optimiz", "improve", "efficiency", "reduce cost", "maximize"],
    "task_type": TaskType.OPTIMIZATION,
    "primary_tools": ["optimize_inventory"],
    "optional_tools": ["analyze_inventory", "forecast_demand"]
}
```

### 2. Multi-Intent Detection

Changed from "first match wins" to "detect all matches":

**Before**:

```python
for intent_name, config in self.intent_patterns.items():
    if keywords_found:
        detected_intent = intent_name
        break  # ❌ Stops at first match
```

**After**:

```python
matched_intents = []
for intent_name, config in self.intent_patterns.items():
    if keywords_found:
        matched_intents.append((intent_name, config, len(keywords_found)))
# ✅ Collects ALL matches
```

### 3. Compound Task Planning

Created `_create_compound_task_plan()` method that:

- Merges tools from all detected intents
- Orders execution by dependency: Analysis → Forecast → Optimization
- Creates single unified execution plan

**Example Flow**:

```
User: "Generate inventory optimization report with demand forecast"
      ↓
Matched Intents:
  - inventory_analysis (keywords: ['inventory'])
  - optimization (keywords: ['optimization'])  
  - forecast (keywords: ['forecast', 'demand'])
      ↓
Compound Plan:
  Tools: [analyze_inventory, forecast_demand, optimize_inventory]
  Order: Analysis first → Forecast second → Optimize last
      ↓
Execution:
  1. analyze_inventory → Current state (541,909 items)
  2. forecast_demand → Predictions (450 orders)
  3. optimize_inventory → Recommendations (reorder 24,500 items)
```

### 4. Tool Execution Priority

Tools ordered by dependency:

| Priority | Tools | Why |
|----------|-------|-----|
| 1 | analyze_inventory, analyze_revenue, analyze_customers | Must know current state first |
| 2 | forecast_demand, forecast_revenue | Needs historical data from #1 |
| 3 | optimize_inventory, optimize_pricing | Needs current state + forecast |

## Expected Logs After Fix

```
INFO [Orchestrator] Analyzing message: 'Generate inventory optimization report with demand forecast'
INFO [Orchestrator] Intent 'inventory_analysis' matched keywords: ['inventory']
INFO [Orchestrator] Intent 'optimization' matched keywords: ['optimiz']
INFO [Orchestrator] Intent 'forecast' matched keywords: ['forecast', 'demand']
INFO [Orchestrator] Multiple intents detected: ['inventory_analysis', 'optimization', 'forecast']
INFO [Orchestrator] Creating compound plan for: ['inventory_analysis', 'optimization', 'forecast']
INFO [Orchestrator] Compound plan tools: ['analyze_inventory', 'forecast_demand', 'optimize_inventory']
INFO [MultiAgentCoach] 🎯 Task Plan Generated:
  - Type: inventory_analysis
  - Tools: ['analyze_inventory', 'forecast_demand', 'optimize_inventory']
  - Execution Order: ['analyze_inventory', 'forecast_demand', 'optimize_inventory']
  - Can Execute: True
INFO [MultiAgentCoach] 🔧 Executing 3 tools for inventory_analysis
INFO [tool_executor] 🔧 Executing tool: analyze_inventory
INFO [tool_executor] ✅ Tool 'analyze_inventory' completed successfully
INFO [tool_executor] 🔧 Executing tool: forecast_demand
INFO [forecast_tools] 📈 Forecasted 30 days: 450 orders, $45,000 revenue
INFO [tool_executor] ✅ Tool 'forecast_demand' completed successfully
INFO [tool_executor] 🔧 Executing tool: optimize_inventory
INFO [optimization_tools] ⚙️ Generated 3 optimization recommendations
INFO [tool_executor] ✅ Tool 'optimize_inventory' completed successfully
INFO [MultiAgentCoach] 💾 Stored 3 tool results in business_context
```

## Testing Instructions

1. **Restart smb_gateway service** to load updated orchestrator

2. **Test compound request**:

   ```
   User: "Generate inventory optimization report with demand forecast"
   ```

3. **Verify logs show**:
   - ✅ Multiple intents detected
   - ✅ Compound plan created
   - ✅ All 3 tools execute (analyze → forecast → optimize)
   - ✅ All results in business_context

4. **Verify response contains**:
   - Current inventory state: "541,909 items, 4.5% out of stock"
   - Demand forecast: "Predicted 450 orders over next 30 days"
   - Optimization recommendations: "Reorder 24,500 items, expected savings $812,860"

## Files Modified

- `services/smb_gateway/coach_orchestrator.py`:
  - Added "optimization" intent pattern with keywords
  - Updated `analyze_intent()` to detect multiple intents
  - Added `_create_compound_task_plan()` method
  - Tool execution ordering by dependency priority

## Benefits

✅ **Handles complex requests**: "analyze X, forecast Y, and optimize Z"
✅ **Correct tool ordering**: Dependencies respected automatically
✅ **No duplicate tools**: Set-based merging prevents redundancy
✅ **Extensible**: Add more intents without changing detection logic
