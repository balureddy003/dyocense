# Multi-Agent Business Planning System

## Overview

A sophisticated multi-agent orchestration system built with **LangGraph** that decomposes complex business goals into actionable plans through specialized agent collaboration.

## Architecture

### Orchestrator Agent

Central coordinator that manages the workflow and agent handoffs.

### Specialized Agents

#### 1. **Goal Analyzer Agent**

- Breaks down vague business goals into SMART objectives
- Identifies key metrics and success criteria
- Defines data requirements and constraints
- Outputs: Refined goal, KPIs, target values, timeline

#### 2. **Data Analyst Agent**

- Assesses data availability and quality
- Identifies missing data sources
- Recommends connectors (CRM, ERP, spreadsheets)
- Prepares datasets for modeling
- Uses markers: `[SHOW_CONNECTORS: ...]`, `[SHOW_UPLOADER: ...]`

#### 3. **Data Scientist Agent**

- Builds forecasting models (time series, regression)
- Creates optimization algorithms (linear programming)
- Validates models with accuracy metrics
- Generates predictions with confidence intervals
- Outputs: Model results, accuracy, insights

#### 4. **Business Consultant Agent**

- Synthesizes all agent analyses
- Creates strategic recommendations
- Develops phased implementation plans
- Assesses risks and ROI
- Outputs: Executive summary, action plan, success metrics

## Deep Research Pattern

The system implements iterative refinement:

1. **Initial Analysis**: Goal Analyzer breaks down the goal
2. **Data Assessment**: Data Analyst checks available data
3. **Modeling**: Data Scientist builds solutions (if data is ready)
4. **Strategic Planning**: Business Consultant creates action plan
5. **Refinement Loop**: Agents can request help from each other

## State Management

Using LangGraph's state graph:

```python
AgentState:
  - messages: Conversation history
  - user_goal: Original business goal
  - current_agent: Active agent name
  - goal_analysis: Goal breakdown results
  - data_analysis: Data availability assessment
  - model_results: Predictions and forecasts
  - recommendations: Strategic action plan
  - next_agent: Where to route next
  - iteration_count: Prevent infinite loops
```

## Agent Workflow

```
User Goal → Goal Analyzer → Data Analyst → Data Scientist → Business Consultant → Final Plan
                ↓              ↓              ↓                    ↓
            SMART Goals    Data Needs     Forecasts         Action Plan
```

### Conditional Routing

- **Goal Analyzer** → Data Analyst (if data needed) OR Business Consultant (if strategic only)
- **Data Analyst** → Data Scientist (if data ready) OR loop back (if waiting for data)
- **Data Scientist** → Business Consultant
- **Business Consultant** → END (terminal agent)

## API Integration

### Endpoint: `/v1/chat/multi-agent`

**Request:**

```json
{
  "goal": "Increase sales by 20% in Q2",
  "context": {
    "data_sources": ["CRM", "Historical sales"],
    "constraints": {
      "budget": 50000,
      "timeline": "Q2 2024"
    }
  },
  "llm_config": {
    "provider": "azure",
    "endpoint": "https://your-endpoint.openai.azure.com/",
    "api_key": "your-key",
    "deployment": "gpt-4o-mini"
  }
}
```

**Response:**

```json
{
  "response": "Strategic plan for sales growth...",
  "goal_analysis": {
    "refined_goal": "Achieve 20% sales growth...",
    "primary_metric": "Revenue",
    "target_value": "+20%",
    "timeframe": "Q2 2024"
  },
  "data_analysis": {
    "available_data": ["CRM contacts", "Sales history"],
    "missing_data": ["Customer segmentation"],
    "ready_for_modeling": true
  },
  "model_results": {
    "forecast": "Expected growth: 18-22%",
    "confidence": "High",
    "assumptions": [...]
  },
  "recommendations": {
    "quick_wins": ["Upsell to existing customers"],
    "implementation_plan": [...],
    "estimated_roi": "3.5x"
  },
  "conversation": [
    "Analyzing goal: Increase sales by 20%...",
    "Data analysis: CRM data available...",
    "Forecast model: Linear regression...",
    "Strategic recommendations..."
  ]
}
```

## Installation

### Dependencies

```bash
pip install langgraph langchain-openai langchain-core
```

Or add to `requirements-dev.txt`:

```
langgraph>=0.0.40
langchain>=0.1.0,<0.2
langchain-openai>=0.0.5
langchain-core>=0.1.0,<0.2
```

### Configuration

Set environment variables in `.env.dev`:

```bash
LLM_PROVIDER=azure  # or "openai"

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini

# OR OpenAI
OPENAI_API_KEY=your-openai-key
```

## Usage

### Python API

```python
from packages.agents.multi_agent_system import OrchestratorAgent

# Create orchestrator
orchestrator = OrchestratorAgent()

# Configure LLM
orchestrator.configure_llm(
    provider="azure",
    azure_endpoint="https://your-endpoint.openai.azure.com/",
    api_key="your-key",
    deployment_name="gpt-4o-mini"
)

# Build agent graph
orchestrator.build_graph()

# Process goal
result = await orchestrator.process_goal(
    user_goal="Increase sales by 20% in Q2",
    context={"data_sources": ["CRM", "Sales history"]}
)

print(result["response"])
```

### HTTP API

```bash
curl -X POST http://localhost:8001/v1/chat/multi-agent \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-token" \
  -d '{
    "goal": "Increase sales by 20% in Q2",
    "context": {
      "data_sources": ["CRM"]
    }
  }'
```

### Test Script

```bash
# Test with custom goal
python scripts/test_multi_agent.py "Increase sales by 20%"

# Run interactive scenarios
python scripts/test_multi_agent.py
```

## Agent Prompts

### Goal Analyzer System Prompt

```
You are a Goal Analyzer agent specializing in business objective analysis.

Responsibilities:
1. Analyze business goals for clarity and specificity
2. Break down vague goals into SMART objectives
3. Identify required data sources and metrics
4. Define success criteria and KPIs

Output: Structured goal analysis with refined_goal, primary_metric, 
target_value, timeframe, success_criteria, data_needed, assumptions
```

### Data Analyst System Prompt

```
You are a Data Analyst agent specializing in business data analysis.

Responsibilities:
1. Assess available data sources and relevance
2. Evaluate data quality (completeness, accuracy, timeliness)
3. Identify missing data and gaps
4. Recommend data connections

Use markers:
- [SHOW_CONNECTORS: crm, accounting] to suggest connectors
- [SHOW_UPLOADER: csv] to request file uploads
```

### Data Scientist System Prompt

```
You are a Data Scientist agent specializing in business analytics.

Responsibilities:
1. Select appropriate modeling techniques
2. Build forecasting models (time series, regression, ML)
3. Create optimization models
4. Validate models and assess accuracy

Output: Model type, accuracy metrics, predictions, confidence, 
assumptions, limitations, insights
```

### Business Consultant System Prompt

```
You are a Business Consultant agent specializing in strategic planning.

Responsibilities:
1. Synthesize analysis from all other agents
2. Create actionable strategic recommendations
3. Develop phased implementation plans
4. Assess risks and ROI

Output: Executive summary, key recommendations, implementation plan,
quick wins, timeline, ROI, risks, success metrics
```

## Fallback Mode

If LangGraph is not installed, the system runs in **fallback mode**:

- Sequential agent execution (no state graph)
- Simplified agent responses
- Basic goal decomposition
- Still provides useful planning guidance

## Testing

### Unit Tests

Test individual agents in isolation:

```python
from packages.agents.multi_agent_system import GoalAnalyzerAgent

agent = GoalAnalyzerAgent()
state = {
    "messages": [],
    "user_goal": "Increase sales by 20%",
    ...
}

result = agent.invoke(state)
assert "goal_analysis" in result
```

### Integration Tests

Test agent handoffs:

```python
# Test goal analyzer → data analyst handoff
orchestrator = OrchestratorAgent()
result = await orchestrator.process_goal("Increase sales")

assert result["goal_analysis"] is not None
assert result["data_analysis"] is not None
```

### End-to-End Tests

Test complete workflow:

```bash
pytest tests/test_multi_agent.py -v
```

## Example Scenarios

### Scenario 1: Sales Growth

**Goal**: Increase sales revenue by 20% in Q2 2024

**Agent Flow**:

1. Goal Analyzer: "Need 20% growth = $500K additional revenue, require CRM and sales data"
2. Data Analyst: "CRM connected, sales history available, forecast possible"
3. Data Scientist: "Linear regression shows 18-22% growth achievable with confidence"
4. Business Consultant: "Focus on top 20% customers, implement upsell strategy, ROI: 3.5x"

### Scenario 2: Cost Reduction

**Goal**: Reduce operational costs by 15%

**Agent Flow**:

1. Goal Analyzer: "15% reduction = $300K savings, need expense tracking data"
2. Data Analyst: "Accounting data available, expense categories identified"
3. Data Scientist: "Optimization model identifies redundant costs"
4. Business Consultant: "Consolidate vendors, automate processes, save $350K annually"

### Scenario 3: Customer Retention

**Goal**: Improve customer retention from 75% to 85%

**Agent Flow**:

1. Goal Analyzer: "10% retention increase, need customer behavior data"
2. Data Analyst: "Support tickets, feedback surveys available"
3. Data Scientist: "Churn prediction model identifies at-risk customers"
4. Business Consultant: "Proactive support program, estimated $200K revenue saved"

## Troubleshooting

### LangGraph Not Available

```
ImportError: No module named 'langgraph'
```

**Solution**: Install dependencies

```bash
pip install langgraph langchain-openai
```

### LLM API Errors

```
AuthenticationError: Invalid API key
```

**Solution**: Check environment variables

```bash
echo $AZURE_OPENAI_API_KEY
```

### Agent Loops

If agents keep handing off without progress:

- Check `iteration_count` and `max_iterations`
- Review agent routing logic in `router()` function
- Add more specific exit conditions

## Advanced Configuration

### Custom Agents

Create new specialized agents:

```python
class FinancialAnalystAgent(Agent):
    def __init__(self):
        super().__init__(
            name="financial_analyst",
            role="Financial Analyst",
            capabilities=["Financial modeling", "Budget analysis"],
            system_prompt="You are a financial analyst..."
        )
    
    def invoke(self, state: AgentState) -> Dict[str, Any]:
        # Custom logic
        pass
```

### Custom Routing

Modify orchestrator routing:

```python
def custom_router(state: AgentState) -> str:
    if "budget" in state.get("user_goal", ""):
        return "financial_analyst"
    return state.get("next_agent", END)
```

### Human-in-the-Loop

Add checkpoints for human review:

```python
workflow.add_conditional_edges(
    "data_scientist",
    lambda state: "human_review" if state.get("needs_review") else "business_consultant"
)
```

## Roadmap

- [ ] Tool calling for agents (web search, database queries)
- [ ] Memory persistence (save conversation state)
- [ ] Agent learning (improve from feedback)
- [ ] Parallel agent execution
- [ ] Streaming responses (real-time updates)
- [ ] Multi-modal inputs (PDFs, images)

## References

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [LangChain Agents](https://python.langchain.com/docs/modules/agents/)
- [Multi-Agent Research Paper](https://arxiv.org/abs/2308.08155)
- [Deep Research Pattern](https://blog.langchain.dev/research-agents/)

## License

MIT License - see LICENSE file for details.
