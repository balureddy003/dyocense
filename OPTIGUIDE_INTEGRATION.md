# OptiGuide Integration for Dyocense

## Overview

We've integrated **OptiGuide-style** conversational AI for inventory optimization, based on Microsoft Research's [OptiGuide: Large Language Models for Supply Chain Optimization](https://arxiv.org/abs/2307.03875).

This implementation provides:

- **What-if analysis** for scenario planning
- **Root cause analysis** for "why" questions  
- **Multi-agent orchestration** using LangGraph
- **Natural language interface** to optimization problems

## Architecture

### Microsoft's OptiGuide Concept

OptiGuide enables business users to ask natural language questions about supply chain optimization problems and receive quantitative, solver-backed answers. Key innovations:

1. **Privacy-Preserving**: Optimization runs locally; no proprietary data sent to LLMs
2. **Code Generation**: LLM generates code snippets to modify optimization constraints
3. **Safeguard Agent**: Validates generated code before execution
4. **Quantitative Results**: Uses OR-Tools/Gurobi solvers for proven optimal solutions

### Our Implementation

```
┌─────────────────────────────────────────────────────────────────┐
│                    User Question                                │
│  "What if order costs increase by 20%?"                        │
└────────────────────┬────────────────────────────────────────────┘
                     │
          ┌──────────▼──────────┐
          │  OptiGuide Agent    │
          │  (optiguide_agent.py)│
          └──────────┬──────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
   ┌────▼─────┐            ┌─────▼──────┐
   │  Writer  │            │ Safeguard  │
   │  Agent   │            │   Agent    │
   └────┬─────┘            └─────┬──────┘
        │                         │
        │ Generate Code           │ Validate
        │ Modifications           │ Safety
        └────────────┬────────────┘
                     │
            ┌────────▼────────┐
            │  OR-Tools LP    │
            │   Optimizer     │
            └────────┬────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
   ┌────▼────┐              ┌─────▼──────┐
   │ Analyst │              │  Narrator  │
   │  Agent  │              │   Agent    │
   └────┬────┘              └─────┬──────┘
        │                         │
        │ Compare Results         │ Business
        │ Calculate Impact        │ Language
        └────────────┬────────────┘
                     │
              ┌──────▼───────┐
              │   Response   │
              │   Narrative  │
              └──────────────┘
```

## Agent Roles

### 1. Writer Agent

**Purpose**: Generates Python code to modify optimization parameters

**Input**: Natural language question  
**Output**: Python dictionary with parameter modifications

**Example**:

```python
# Question: "What if order costs increase by 20%?"
# Output:
{
    "order_cost_multiplier": 1.2,
    "holding_cost_multiplier": 1.0
}
```

### 2. Safeguard Agent

**Purpose**: Validates code safety before execution

**Checks**:

- No import statements
- No file/network operations
- Only allowed parameter names
- Numeric values within reasonable bounds

**Output**: "SAFE" or "DANGER"

### 3. Optimizer Agent

**Purpose**: Executes OR-Tools LP solver with modified constraints

**Process**:

1. Load baseline optimization result
2. Apply parameter modifications
3. Re-run LP solver
4. Return new optimal solution

### 4. Analyst Agent

**Purpose**: Compares original vs modified results

**Analysis**:

- Cost changes (absolute and percentage)
- Savings impact
- SKU-level changes
- Trade-offs identified

### 5. Narrator Agent

**Purpose**: Translates technical analysis into business language

**Output**:

```markdown
**What-If Analysis: What if order costs increase by 20%?**

📈 This scenario would **increase** total costs by $13.58 (20.0%)

💡 **Recommendation**: This scenario increases costs. 
Consider alternative approaches or negotiating with suppliers.
```

## API Endpoints

### 1. What-If Analysis

```bash
POST /v1/tenants/{tenant_id}/what-if
```

**Request**:

```json
{
  "question": "What if order costs increase by 20%?",
  "llm_config": {  // Optional
    "model": "gpt-4",
    "api_key": "sk-...",
    "temperature": 0
  }
}
```

**Response**:

```json
{
  "success": true,
  "question": "What if order costs increase by 20%?",
  "original_result": {
    "objective_value": 67.89,
    "total_potential_savings": 28.94,
    "recommendations": [...]
  },
  "modified_result": {
    "objective_value": 81.47,
    "total_potential_savings": 34.73,
    "recommendations": [...]
  },
  "modifications_applied": {
    "order_cost_multiplier": 1.2
  },
  "analysis": "Cost Impact Analysis: ...",
  "narrative": "This scenario would increase total costs by 20%..."
}
```

### 2. Why Analysis

```bash
POST /v1/tenants/{tenant_id}/why
```

**Request**:

```json
{
  "question": "Why are inventory costs high?"
}
```

**Response**:

```json
{
  "success": true,
  "question": "Why are inventory costs high?",
  "narrative": "**WIDGET-001** is overstocked because current inventory exceeds optimal levels, leading to high holding costs.",
  "supporting_data": {
    "recommendations": [...]
  }
}
```

### 3. LangGraph Chat

```bash
POST /v1/tenants/{tenant_id}/chat
```

**Request**:

```json
{
  "question": "What's the current state of my inventory?",
  "stream": false
}
```

**Response**:

```json
{
  "success": true,
  "question": "What's the current state of my inventory?",
  "intent": "overview",
  "narrative": "📊 Total inventory value: $25,175.50...",
  "supporting_data": {...}
}
```

## LangGraph Workflow

The `langgraph_coach.py` implements a stateful conversation system:

```python
# Workflow States
User Question → Goal Planner → Data Gatherer → [Agent Execution] → Narrator → Response

# Routing Logic
- forecast intent → Forecaster Agent
- optimize intent → Optimizer Agent  
- what_if intent → What-If Agent
- why intent → Evidence Agent
- overview intent → Direct to Narrator
```

**Intent Classification**:

```python
def _goal_planner_node(state):
    question = state["user_question"].lower()
    
    if "forecast" in question or "predict" in question:
        intent = "forecast"
    elif "what if" in question:
        intent = "what_if"
    elif "why" in question:
        intent = "why"
    elif "optimize" in question:
        intent = "optimize"
    else:
        intent = "overview"
    
    state["intent"] = intent
    return state
```

## Example Conversations

### Scenario Planning

```
User: "What if supplier costs increase 15%?"

OptiGuide:
📈 This scenario would increase total costs by $10.18 (15.0%)

💡 Recommendation: Negotiate with suppliers or source alternatives.
Consider locking in current rates with long-term contracts.

Supporting Data:
- Original cost: $67.89
- Modified cost: $78.07
- Cost increase: $10.18
```

### Root Cause Analysis

```
User: "Why is GADGET-002 overstocked?"

OptiGuide:
**GADGET-002** is overstocked because current inventory (320 units) 
exceeds optimal levels (240 units), leading to $7.22 in excess 
holding costs.

Recommendation: Reduce stock to 240 units through sales promotions 
or reduced ordering.
```

### Optimization Guidance

```
User: "How can I reduce inventory costs?"

OptiGuide:
💡 Optimization found $28.94 in potential savings:

1. WIDGET-001: Reduce stock from 450 to 290 units (Save $5.33)
2. GADGET-002: Reduce stock from 320 to 240 units (Save $7.22)
3. TOOL-003: Reduce stock from 180 to 135 units (Save $9.65)

Total annual savings: $28.94 (42.6% reduction)
```

## Comparison to Microsoft's OptiGuide

| Feature | Microsoft OptiGuide | Dyocense Implementation | Status |
|---------|--------------------|-----------------------|---------|
| Natural language interface | ✅ | ✅ | Complete |
| Code generation | ✅ LLM-powered | ✅ Rule-based (LLM optional) | Working |
| Safety validation | ✅ Safeguard agent | ✅ Parameter validation | Complete |
| Optimization solver | ✅ Gurobi | ✅ OR-Tools LP | Complete |
| What-if analysis | ✅ | ✅ | Complete |
| Multi-agent system | ✅ AutoGen | ✅ LangGraph | Complete |
| Privacy-preserving | ✅ Local execution | ✅ Local execution | Complete |
| Causal inference | ❌ | ⏳ Planned (DoWhy) | Future |
| Streaming responses | ❌ | ⏳ Planned | Future |

## Current Limitations & Future Work

### Limitations

1. **Rule-Based Fallback**: Without LLM configuration, uses pattern matching instead of true NLU
2. **Simple Modifications**: Currently supports basic parameter multipliers only
3. **No Code Execution**: Modifies numerical parameters rather than generating/executing Python code
4. **Limited What-If Patterns**: Recognizes common patterns but may miss complex scenarios

### Future Enhancements

1. **Full LLM Integration**: Connect to OpenAI/Azure OpenAI for advanced NLU
2. **Causal Inference**: Integrate DoWhy for "why" question analysis
3. **Streaming Responses**: Server-sent events for real-time feedback
4. **Complex Scenarios**: Support multiple simultaneous constraint modifications
5. **Historical Comparison**: "What if we had done X last month?"
6. **Automated Recommendations**: Proactive optimization suggestions

## Testing

Run the comprehensive test suite:

```bash
./scripts/test_optiguide.sh
```

**Test Coverage**:

- ✅ Capabilities detection
- ✅ What-if analysis (order costs)
- ✅ What-if analysis (holding costs)
- ✅ What-if analysis (safety stock)
- ✅ What-if analysis (service level)
- ✅ Why analysis (high costs)
- ✅ Why analysis (overstock)
- ✅ LangGraph chat (overview)
- ✅ LangGraph chat (forecast)
- ✅ LangGraph chat (optimize)
- ✅ Complex what-if scenarios

## Configuration

### Basic (No LLM)

Works out-of-the-box with rule-based pattern matching:

```python
# Uses fallback logic for common patterns
response = await optiguide.ask_what_if(
    tenant_id="demo",
    question="What if order costs increase 20%?"
)
```

### Advanced (With LLM)

Requires OpenAI/Azure OpenAI configuration:

```python
llm_config = {
    "model": "gpt-4",
    "api_key": "sk-...",
    "temperature": 0
}

agent = OptiGuideInventoryAgent(backend, llm_config)
response = await agent.ask_what_if(tenant_id, question)
```

## Performance

**Typical Response Times** (without LLM):

- What-if analysis: 500-800ms
- Why analysis: 300-500ms
- LangGraph chat: 400-600ms

**With LLM** (additional overhead):

- +1-3 seconds for LLM API calls
- Depends on model (GPT-4 vs GPT-3.5)
- Can be optimized with caching

## Security

### Safeguard Validation

All generated code passes through safety checks:

```python
def _validate_modifications(modifications):
    allowed_params = {
        'order_cost_multiplier',
        'holding_cost_multiplier',
        'stockout_cost_multiplier',
        'service_level',
        'capacity_constraint',
        'budget_constraint'
    }
    
    # Check keys
    for key in modifications.keys():
        if key not in allowed_params:
            return False
    
    # Check values
    for value in modifications.values():
        if not isinstance(value, (int, float)):
            return False
        if value < 0 or value > 100:
            return False
    
    return True
```

### Privacy

- ✅ All optimization runs locally
- ✅ No proprietary data sent to LLMs (when using rule-based mode)
- ✅ Optional LLM mode for advanced features
- ✅ User controls LLM configuration

## Integration with Existing Services

OptiGuide builds on top of existing Dyocense services:

```python
from backend.services.elt_pipeline import ELTPipeline
from backend.services.forecaster.prophet_forecaster import ProphetForecaster
from backend.services.optimizer.ortools_optimizer import ORToolsOptimizer
from backend.services.coach.optiguide_agent import OptiGuideInventoryAgent
from backend.services.coach.langgraph_coach import LangGraphInventoryCoach

# ELT Pipeline: Provides business metrics
elt = ELTPipeline(backend)
elt.run_full_pipeline(tenant_id)

# Forecaster: Provides demand predictions
forecaster = ProphetForecaster(backend)
forecasts = forecaster.generate_forecasts(tenant_id, "demand", 4)

# Optimizer: Provides optimal inventory levels
optimizer = ORToolsOptimizer(backend)
result = await optimizer.optimize_inventory_lp(tenant_id)

# OptiGuide: What-if analysis using all above
optiguide = OptiGuideInventoryAgent(backend)
what_if = await optiguide.ask_what_if(tenant_id, "What if costs increase 20%?")

# LangGraph: Orchestrates all agents
coach = LangGraphInventoryCoach(backend)
response = coach.chat(tenant_id, "Optimize my inventory")
```

## Deployment

### Development

```bash
# Install dependencies
pip install pyautogen langgraph langchain-openai

# Start backend
uvicorn backend.main:app --reload --port 8001

# Test
./scripts/test_optiguide.sh
```

### Production

```bash
# Set environment variables
export OPENAI_API_KEY="sk-..."
export OPENAI_MODEL="gpt-4"

# Run with production settings
uvicorn backend.main:app --workers 4 --port 8001

# Monitor
curl http://localhost:8001/v1/capabilities
```

## References

1. **Microsoft OptiGuide Paper**: [arXiv:2307.03875](https://arxiv.org/abs/2307.03875)
2. **AutoGen Framework**: [microsoft/autogen](https://github.com/microsoft/autogen)
3. **LangGraph**: [langchain-ai/langgraph](https://github.com/langchain-ai/langgraph)
4. **OR-Tools**: [google/or-tools](https://github.com/google/or-tools)
5. **Prophet**: [facebook/prophet](https://github.com/facebook/prophet)

## License

This implementation is part of the Dyocense project. OptiGuide concept © Microsoft Research.
