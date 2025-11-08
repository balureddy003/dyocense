# Multi-Agent System - Quick Start Guide

## What Was Built

A **LangGraph-based multi-agent orchestration system** that decomposes complex business goals into actionable plans through specialized agent collaboration.

### 4 Specialized Agents

1. **Goal Analyzer** - Refines vague goals into SMART objectives
2. **Data Analyst** - Assesses data availability and quality  
3. **Data Scientist** - Builds forecasting and optimization models
4. **Business Consultant** - Creates strategic action plans

### Deep Research Pattern

Agents collaborate through iterative refinement with handoffs, maintaining conversation history and structured insights.

## Files Created

```
packages/agents/
  ├── multi_agent_system.py       # Core multi-agent implementation
  └── README.md                    # Full documentation

services/chat/
  └── main.py                      # Added /v1/chat/multi-agent endpoint

scripts/
  └── test_multi_agent.py         # Test script with scenarios

requirements-dev.txt               # Added langgraph dependencies
```

## Quick Test

### 1. Configure LLM (Required)

Edit `.env.dev` with your API keys:

```bash
# Azure OpenAI (recommended)
LLM_PROVIDER=azure
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_OPENAI_API_KEY=your-actual-key
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini

# OR OpenAI
# LLM_PROVIDER=openai
# OPENAI_API_KEY=your-openai-key
```

### 2. Run Test Script

```bash
# Test with a business goal
python scripts/test_multi_agent.py "Increase sales by 20% in Q2"

# Interactive mode with scenarios
python scripts/test_multi_agent.py
```

### 3. Start Backend Service

```bash
# Start the kernel service (includes chat service)
uvicorn services.kernel.main:app --reload --port 8001
```

### 4. Test API Endpoint

```bash
curl -X POST http://localhost:8001/v1/chat/multi-agent \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dev-token" \
  -d '{
    "goal": "Increase sales by 20% in Q2",
    "context": {
      "data_sources": ["CRM", "Historical sales"]
    }
  }'
```

## Expected Flow

**Input**: "Increase sales by 20% in Q2"

**Agent Workflow**:

1. **Goal Analyzer**:
   - Refined goal: "Achieve 20% sales revenue growth ($500K) by end of Q2 2024"
   - Primary metric: Revenue
   - Data needed: CRM contacts, historical sales

2. **Data Analyst**:
   - Assessment: CRM connected, sales data available
   - Response includes: `[SHOW_CONNECTORS: salesforce, hubspot]` if data missing
   - Ready for modeling: Yes

3. **Data Scientist**:
   - Model: Time series forecast
   - Prediction: 18-22% growth achievable
   - Confidence: High (based on historical patterns)

4. **Business Consultant**:
   - Recommendations: Focus on top 20% customers, implement upsell strategy
   - Implementation: 3-phase plan (Months 1-3)
   - ROI: 3.5x estimated return

**Output**: Complete strategic plan with action items, timelines, and success metrics.

## Integration with Frontend

The multi-agent responses work seamlessly with the inline component system:

```typescript
// Frontend: AgentAssistant.tsx handles responses
if (response.includes('[SHOW_CONNECTORS:')) {
  // Data Analyst suggested connectors
  // Displays InlineConnectorSelector component
}

if (response.includes('[SHOW_UPLOADER:')) {
  // Data Analyst needs data upload
  // Displays InlineDataUploader component  
}
```

## Fallback Mode

If LangGraph is not available (dependencies not installed), the system runs in **fallback mode**:

- Sequential agent execution (no state graph)
- Simplified responses with basic planning
- Still provides useful guidance

## Test Scenarios

The test script includes 4 pre-built scenarios:

1. **Sales Growth**: "Increase sales revenue by 20% in Q2 2024"
2. **Cost Reduction**: "Reduce operational costs by 15%"
3. **Customer Retention**: "Improve retention rate from 75% to 85%"
4. **Market Expansion**: "Launch new product line in European market"

Each scenario demonstrates different agent capabilities and data requirements.

## Troubleshooting

### Issue: "Multi-agent system not available"

**Cause**: LangGraph not installed

**Fix**:

```bash
pip install langgraph langchain-openai langchain-core
```

### Issue: "AuthenticationError: Invalid API key"

**Cause**: LLM credentials not configured

**Fix**: Add real API keys to `.env.dev` (see step 1 above)

### Issue: Agents loop without progress

**Cause**: Missing data or unclear goal

**Fix**: Check agent responses for data requests, provide context in API call

## Next Steps

### 1. Add Real LLM Keys

Replace placeholder keys in `.env.dev` with your actual credentials.

### 2. Test End-to-End

```bash
# Start backend
uvicorn services.kernel.main:app --reload --port 8001

# In another terminal, test multi-agent endpoint
python scripts/test_multi_agent.py "Your business goal"
```

### 3. Integrate with Frontend

Update `AgentAssistant.tsx` to call the multi-agent endpoint for complex goals:

```typescript
// When user provides a complex goal
const response = await fetch('/v1/chat/multi-agent', {
  method: 'POST',
  body: JSON.stringify({
    goal: userMessage,
    context: { data_sources: connectedDataSources }
  })
});

const result = await response.json();
// Display result.response with inline components
```

### 4. Monitor Agent Performance

Check logs for agent handoffs:

```bash
# View agent workflow
tail -f logs/chat.log | grep "current_agent"
```

### 5. Customize Agents

Edit agent system prompts in `multi_agent_system.py` to match your business domain:

```python
class GoalAnalyzerAgent(Agent):
    def __init__(self):
        super().__init__(
            system_prompt="You are a Goal Analyzer for [YOUR INDUSTRY]..."
        )
```

## Architecture Diagram

```
┌─────────────────────────────────────────────────┐
│           Frontend (AgentAssistant)            │
│  - User enters goal: "Increase sales 20%"      │
└────────────────────┬────────────────────────────┘
                     │ POST /v1/chat/multi-agent
                     ↓
┌─────────────────────────────────────────────────┐
│        Chat Service (FastAPI)                  │
│  - Route: /v1/chat/multi-agent                 │
│  - Creates OrchestratorAgent                   │
└────────────────────┬────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────┐
│       OrchestratorAgent (LangGraph)            │
│  - Builds state graph with conditional routing │
└────────────────────┬────────────────────────────┘
                     │
          ┌──────────┴──────────┐
          ↓                     ↓
┌──────────────────┐  ┌──────────────────┐
│  Goal Analyzer   │→ │  Data Analyst    │
│  SMART goals     │  │  Data quality    │
└──────────────────┘  └────────┬─────────┘
                              ↓
                     ┌──────────────────┐
                     │ Data Scientist   │
                     │ Forecasting      │
                     └────────┬─────────┘
                              ↓
                     ┌──────────────────┐
                     │ Business Consult │
                     │ Strategic plan   │
                     └────────┬─────────┘
                              ↓
┌─────────────────────────────────────────────────┐
│              Final Response                     │
│  - Goal analysis                                │
│  - Data assessment                              │
│  - Model results                                │
│  - Action plan                                  │
└─────────────────────────────────────────────────┘
```

## API Response Example

```json
{
  "response": "Strategic Plan for Sales Growth:\n\n**Goal**: Increase sales revenue by 20% ($500K) by Q2 2024...",
  
  "goal_analysis": {
    "refined_goal": "Achieve 20% sales revenue growth ($500K) by end of Q2 2024",
    "primary_metric": "Revenue",
    "target_value": "+20% ($500K)",
    "timeframe": "Q2 2024",
    "success_criteria": [
      "Monthly revenue tracking",
      "Customer acquisition rate",
      "Average deal size"
    ],
    "data_needed": ["CRM contacts", "Historical sales", "Product catalog"]
  },
  
  "data_analysis": {
    "available_data": ["CRM: 5000 contacts", "Sales history: 2 years"],
    "data_quality": "Good",
    "ready_for_modeling": true
  },
  
  "model_results": {
    "model_type": "Time series forecast",
    "accuracy_metrics": {"MAPE": "8.5%", "R2": 0.92},
    "predictions": "18-22% growth achievable",
    "confidence": "High"
  },
  
  "recommendations": {
    "executive_summary": "Focus on top 20% customers with upsell strategy...",
    "key_recommendations": [
      "Implement automated follow-up system",
      "Launch customer referral program",
      "Expand product bundles"
    ],
    "implementation_plan": {
      "phase_1": "Month 1: Setup automation",
      "phase_2": "Month 2: Launch referral program",
      "phase_3": "Month 3: Optimize and scale"
    },
    "estimated_roi": "3.5x",
    "estimated_timeline": "3 months"
  },
  
  "conversation": [
    "Analyzing goal: Increase sales by 20% in Q2...",
    "Data analysis: CRM data available, sales history sufficient...",
    "Forecast model shows 18-22% growth achievable...",
    "Strategic recommendations: Focus on top customers..."
  ]
}
```

## Production Checklist

Before deploying to production:

- [ ] Add real LLM API keys to environment variables
- [ ] Test all 4 agent scenarios
- [ ] Set up error monitoring for agent failures
- [ ] Configure rate limiting for API endpoint
- [ ] Add caching for repeated goal analyses
- [ ] Implement conversation persistence (database)
- [ ] Add human-in-the-loop checkpoints for critical decisions
- [ ] Test fallback mode behavior
- [ ] Document custom agent prompts for your domain
- [ ] Set up logging for agent handoff debugging

## Support

For issues or questions:

1. Check `packages/agents/README.md` for full documentation
2. Review test scenarios in `scripts/test_multi_agent.py`
3. Check logs: `tail -f logs/chat.log`
4. Verify LangGraph installation: `python -c "import langgraph; print('OK')"`

## Success Indicators

You've successfully set up the multi-agent system when:

✅ Test script runs without errors  
✅ All 4 agents execute in sequence  
✅ Goal analysis includes SMART objectives  
✅ Data analyst suggests relevant connectors  
✅ Data scientist provides forecasts  
✅ Business consultant delivers action plan  
✅ Frontend displays inline components for data upload/connectors  
✅ API returns structured JSON with all agent outputs  

**You're ready to use the multi-agent system for real business planning!**
