# Multi-Agent Coach Orchestration System

## Overview

The coach now uses a **dynamic, multi-agent orchestration architecture** instead of hardcoded prompts. This allows the system to intelligently decide which tools/agents to invoke based on:

1. **User Intent** - What the user is asking for
2. **Available Data** - What data we have access to
3. **Tool Capabilities** - What analysis tools can do

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Request                              │
│          "do the inventory analysis and provide report"          │
└────────────────────────┬────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Coach Orchestrator                            │
│  - Analyzes intent (keywords → task type)                        │
│  - Checks available data (orders: 0, inventory: 541909)          │
│  - Creates execution plan with required tools                    │
└────────────────────────┬────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                       Task Plan                                  │
│  Type: INVENTORY_ANALYSIS                                        │
│  Tools: [list_csv_files, read_csv_file, analyze_inventory]      │
│  Execution Order: 1 → 2 → 3                                      │
│  Can Execute: true                                               │
└────────────────────────┬────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Tool Execution                                │
│  1. list_csv_files() → Find inventory CSVs                       │
│  2. read_csv_file(inventory.csv) → Load data                     │
│  3. analyze_inventory(data) → Calculate metrics                  │
└────────────────────────┬────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                Dynamic System Prompt                             │
│  "Execute tools in this order: list_csv_files → read_csv_file   │
│   → analyze_inventory. Generate report with sections:            │
│   Executive Summary, Stock Health, Recommendations"              │
└────────────────────────┬────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                      LLM Response                                │
│  Professional report with actual data from tool execution        │
└─────────────────────────────────────────────────────────────────┘
```

## How It Works

### 1. Intent Detection

The `CoachOrchestrator` analyzes the user message for keywords:

```python
intent_patterns = {
    "inventory_analysis": {
        "keywords": ["inventory", "stock", "sku", "product"],
        "task_type": TaskType.INVENTORY_ANALYSIS,
        "primary_tools": ["analyze_inventory", "read_csv_file"],
        "report_sections": ["executive_summary", "stock_health", "recommendations"]
    },
    "revenue_analysis": {
        "keywords": ["revenue", "sales", "order"],
        "task_type": TaskType.REVENUE_ANALYSIS,
        "primary_tools": ["analyze_revenue", "forecast_demand"],
        ...
    }
}
```

**User says**: "do the inventory analysis"  
**System detects**: `inventory_analysis` intent

### 2. Data Availability Check

Checks what data exists:

```python
available_data = {
    "orders": 0,        # ❌ No sales data
    "inventory": 541909, # ✅ Have inventory
    "customers": 0       # ❌ No customer data
}
```

### 3. Task Plan Creation

Creates a plan with required tools:

```python
TaskPlan {
    task_type: INVENTORY_ANALYSIS,
    required_tools: [
        ToolRequirement(tool_name="list_csv_files", tool_type="mcp_tool"),
        ToolRequirement(tool_name="read_csv_file", tool_type="mcp_tool"),
        ToolRequirement(tool_name="analyze_inventory", tool_type="internal_function")
    ],
    execution_order: ["list_csv_files", "read_csv_file", "analyze_inventory"],
    can_execute: true  // All required data is available
}
```

### 4. Dynamic Prompt Generation

Generates a context-aware prompt:

```
# Task: Inventory Analysis
# Persona: Business Analyst

## Execution Plan
You will perform inventory analysis using the following tools:

1. **list_csv_files** (mcp_tool) - REQUIRED
   Purpose: list_available_datasets
   Output: List of CSV files with metadata

2. **read_csv_file** (mcp_tool) - REQUIRED
   Purpose: load_raw_data
   Output: CSV data as JSON/records

3. **analyze_inventory** (internal_function) - REQUIRED
   Purpose: inventory_health_analysis
   Output: Stock levels, valuations, ABC analysis

## Workflow
Execute tools in this order:
1. list_csv_files
2. read_csv_file
3. analyze_inventory

## Report Structure
Generate your response with these sections:
- Executive Summary
- Stock Health
- Valuations
- Recommendations

## Available Data
- Inventory: 541,909 records
```

## Adding New Capabilities

### 1. Add a New Task Type

In `coach_orchestrator.py`, add to `intent_patterns`:

```python
"competitor_analysis": {
    "keywords": ["competitor", "competition", "market", "benchmark"],
    "task_type": TaskType.COMPETITOR_ANALYSIS,
    "primary_tools": ["scrape_competitor_data", "compare_metrics"],
    "optional_tools": ["generate_swot"],
    "report_sections": ["market_position", "competitive_gaps", "strategies"]
}
```

### 2. Register a New Tool

In `tool_registry`:

```python
"scrape_competitor_data": {
    "type": "external_agent",
    "capability": "web_scraping_and_analysis",
    "required_data": ["company_name"],
    "output": "Competitor pricing, features, market position"
}
```

### 3. Connect External Agents

For tools like MCP servers or external agents:

```python
# In coach_service.py, add tool execution logic:
elif task_plan.task_type == TaskType.COMPETITOR_ANALYSIS:
    # Call external MCP server or agent
    result = await self._call_mcp_tool("scrape_competitor_data", {
        "company_name": business_ctx.get("business_name")
    })
    context["competitor_insights"] = result
```

## Benefits of This Architecture

### 1. **Dynamic Adaptation**

- No hardcoded prompts for every scenario
- System adapts to available data automatically
- New capabilities can be added without rewriting prompts

### 2. **Transparent Decision-Making**

```python
logger.info(
    f"Task Plan: {task_plan.task_type.value}, "
    f"Tools: {[t.tool_name for t in task_plan.required_tools]}, "
    f"Can Execute: {task_plan.can_execute}"
)
```

You can see exactly what the system plans to do.

### 3. **Graceful Degradation**

If required data is missing:

```python
if not task_plan.can_execute:
    return self._generate_missing_data_prompt(task_plan, available_data)
```

The coach explains what's missing and what it CAN do with available data.

### 4. **Multi-Agent Coordination**

Each tool can be:

- **MCP Tool** (CSV queries, external data)
- **Internal Function** (inventory analysis, forecasting)
- **External Agent** (diagnostician, optimizer, specialized AI agents)

### 5. **Evidence-Based Responses**

Every tool execution is tracked:

```python
evidence_tracker.add_evidence(
    conversation_id,
    f"Analyzed {inventory_analysis['total_items']} items",
    f"Inventory Data Analysis Tool",
    confidence="high"
)
```

## Example: How It Handles Different Requests

### Request: "do the inventory analysis"

1. **Intent**: `inventory_analysis`
2. **Tools**: `[list_csv_files, read_csv_file, analyze_inventory]`
3. **Prompt**: "Execute inventory analysis using these 3 tools..."
4. **Result**: Comprehensive inventory report with actual data

### Request: "forecast next month's revenue"

1. **Intent**: `forecast`
2. **Check Data**: orders: 0 ❌
3. **Can Execute**: false
4. **Prompt**: "Cannot forecast - no sales data. Explain what's needed."
5. **Result**: "To forecast revenue, I need historical sales data. You have inventory data, so I can analyze stock levels instead..."

### Request: "help me grow my business"

1. **Intent**: `general_advice` (no specific keywords)
2. **Tools**: [] (none needed)
3. **Prompt**: "Provide general business coaching"
4. **Result**: General advice based on available context

## Future Enhancements

### 1. Tool Chaining

```python
# Automatically chain tools based on dependencies
if "forecast" in task_plan:
    # First get historical data, then forecast
    execution_order = ["read_csv_file", "analyze_trends", "forecast_demand"]
```

### 2. Multi-Agent Collaboration

```python
# Route to specialist agents
if task_plan.complexity > THRESHOLD:
    results = await asyncio.gather(
        diagnostician_agent.analyze(context),
        optimizer_agent.optimize(context),
        forecaster_agent.predict(context)
    )
    context["multi_agent_insights"] = synthesize(results)
```

### 3. Learning from Feedback

```python
# Track which tool combinations work best
if user_feedback == "helpful":
    orchestrator.record_successful_plan(task_plan)
```

### 4. Real-time MCP Tool Discovery

```python
# Dynamically discover available MCP tools
mcp_tools = await mcp_client.list_tools()
orchestrator.update_tool_registry(mcp_tools)
```

## Summary

Instead of hardcoding prompts like:

```python
if "inventory" in message:
    prompt = "Do inventory analysis with these steps..."
```

The system now:

1. **Analyzes** what the user wants (intent detection)
2. **Plans** what tools to use (task planning)
3. **Generates** a dynamic prompt (prompt orchestration)
4. **Executes** the plan (tool invocation)
5. **Tracks** evidence (transparency)

This makes the coach **intelligent, extensible, and data-driven** rather than rule-based! 🚀
