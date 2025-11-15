# 🤖 Multi-Agent System Design

**Version:** 4.0 (LangGraph within Monolith)  
**Last Updated:** November 14, 2025  
**Status:** Active Development

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Agent Architecture](#agent-architecture)
3. [Agent Personas](#agent-personas)
4. [LangGraph State Machine](#langgraph-state-machine)
5. [Agent Coordination](#agent-coordination)
6. [Implementation](#implementation)

---

## 🎯 Overview

### **Multi-Agent Coach System**

The AI Coach is implemented as a **multi-agent system** where specialized agents collaborate to answer user queries:

- 🎯 **Goal Planner** → Decompose user intent into SMART goals
- 📈 **Forecaster** → Predict future metrics with confidence intervals
- 🧮 **Optimizer** → Recommend optimal actions (inventory, staffing, budget)
- 🔍 **Evidence Analyzer** → Explain why metrics changed (causal inference)
- 📊 **Data Analyst** → Query metrics, generate reports

**Key Innovation:**
> **"Each agent is an expert, coordinated by LangGraph state machine"**

---

### **Why Multi-Agent?**

| Approach | Pros | Cons |
|----------|------|------|
| **Single LLM** | Simple, fast | Lacks specialization, error-prone |
| **Multi-Agent (LangGraph)** | Expert agents, explainable, modular | More complex orchestration |

**Benefits:**

- ✅ **Specialization:** Each agent uses optimal tools (LLM vs. optimization vs. causal AI)
- ✅ **Explainability:** Trace which agent made each decision
- ✅ **Modularity:** Easy to add new agents (e.g., Compliance Agent)
- ✅ **Performance:** Parallel execution for independent tasks

---

## 🏗️ Agent Architecture

### **Framework: LangGraph**

**Why LangGraph?**

- ✅ **State Machines:** Explicit control flow (better than LangChain chains)
- ✅ **Streaming:** Real-time output (Server-Sent Events for frontend)
- ✅ **Debugging:** Visualize agent state transitions
- ✅ **Conditional Routing:** Dynamic agent selection based on query type

**Architecture Diagram:**

```
┌─────────────────────────────────────────────────────────┐
│                  User Query                              │
│  "How can I reduce my inventory costs by 20%?"          │
└────────────────────┬────────────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────────────┐
│            Intent Classifier (Router)                    │
│  - Analyze query complexity                              │
│  - Determine which agents to invoke                      │
└────────────────────┬────────────────────────────────────┘
                     ▼
       ┌─────────────┴──────────────┐
       ▼                            ▼
┌─────────────┐            ┌─────────────────┐
│  Optimizer  │            │  Evidence       │
│  Agent      │            │  Analyzer       │
│             │            │                 │
│ • OR-Tools  │            │ • Causal DAG    │
│ • PuLP      │            │ • DoWhy         │
└─────┬───────┘            └────────┬────────┘
      │                             │
      └─────────────┬───────────────┘
                    ▼
         ┌──────────────────────┐
         │  Response Generator  │
         │  - Synthesize results│
         │  - Natural language  │
         └──────────┬───────────┘
                    ▼
         ┌──────────────────────┐
         │  Streaming Output    │
         │  (Server-Sent Events)│
         └──────────────────────┘
```

---

## 👥 Agent Personas

### **1. Goal Planner Agent**

**Responsibility:** Generate SMART goals from user intent

**Tools:**

- `query_metrics(tenant_id, metric_name)` → Get historical data
- `get_benchmarks(industry, metric)` → Industry averages
- `calculate_feasibility(goal, resources)` → Assess achievability

**LLM:** GPT-4o (requires complex reasoning)

**Example:**

```python
from langchain_openai import ChatOpenAI
from langchain.tools import Tool

class GoalPlannerAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.3)
        self.tools = [
            Tool(name="query_metrics", func=self.query_metrics),
            Tool(name="get_benchmarks", func=self.get_benchmarks),
        ]
    
    async def plan_goal(self, user_query: str) -> dict:
        # Retrieve context
        context = await self.query_metrics("revenue", days=90)
        benchmarks = await self.get_benchmarks("restaurant", "revenue_growth")
        
        # Generate SMART goal
        prompt = f"""
        User query: {user_query}
        Current revenue: {context['current_value']}
        Industry avg growth: {benchmarks['avg_growth']}%
        
        Generate a SMART goal:
        - Specific: What exactly?
        - Measurable: How much?
        - Achievable: Given resources
        - Relevant: Business impact
        - Time-bound: By when?
        """
        
        response = await self.llm.ainvoke(prompt)
        return self.parse_smart_goal(response.content)
```

---

### **2. Forecaster Agent**

**Responsibility:** Predict future metrics with uncertainty

**Tools:**

- `run_arima(metric_data, horizon)` → ARIMA forecast
- `run_prophet(metric_data, horizon)` → Prophet forecast
- `run_xgboost(metric_data, features, horizon)` → XGBoost forecast
- `ensemble_forecast(forecasts)` → Weighted average

**Output:** Time-series predictions + confidence intervals

**Example:**

```python
class ForecasterAgent:
    async def forecast(self, metric_name: str, horizon: int = 30) -> dict:
        # Get historical data
        data = await self.get_metric_data(metric_name, days=365)
        
        # Run multiple models in parallel
        arima_forecast = await self.run_arima(data, horizon)
        prophet_forecast = await self.run_prophet(data, horizon)
        xgboost_forecast = await self.run_xgboost(data, horizon)
        
        # Ensemble (weighted average)
        ensemble = self.ensemble_forecast([
            (arima_forecast, 0.3),
            (prophet_forecast, 0.4),
            (xgboost_forecast, 0.3)
        ])
        
        return {
            "forecast": ensemble["values"],
            "confidence_lower": ensemble["lower_bound"],
            "confidence_upper": ensemble["upper_bound"],
            "horizon_days": horizon
        }
```

---

### **3. Optimizer Agent**

**Responsibility:** Solve resource allocation problems

**Tools:**

- `formulate_lp(problem_type, constraints)` → Linear programming model
- `solve_lp(model)` → Optimal solution
- `sensitivity_analysis(solution)` → What-if scenarios
- `pareto_frontier(objectives)` → Multi-objective trade-offs

**Solver:** OR-Tools, PuLP

**Example:**

```python
from ortools.linear_solver import pywraplp

class OptimizerAgent:
    async def optimize_inventory(self, products: list, constraints: dict) -> dict:
        solver = pywraplp.Solver.CreateSolver('SCIP')
        
        # Decision variables
        order_qty = {p: solver.NumVar(0, solver.infinity(), f'order_{p}') 
                     for p in products}
        
        # Objective: minimize total cost
        solver.Minimize(
            sum(constraints['holding_cost'][p] * order_qty[p] for p in products) +
            sum(constraints['stockout_penalty'][p] * 
                solver.Max(0, constraints['demand'][p] - order_qty[p]) 
                for p in products)
        )
        
        # Constraint: warehouse capacity
        solver.Add(
            sum(order_qty[p] * constraints['volume'][p] for p in products) 
            <= constraints['warehouse_capacity']
        )
        
        # Solve
        status = solver.Solve()
        
        if status == pywraplp.Solver.OPTIMAL:
            return {
                "optimal_orders": {p: order_qty[p].solution_value() for p in products},
                "total_cost": solver.Objective().Value(),
                "status": "optimal"
            }
        else:
            return {"status": "infeasible", "reason": "Constraints cannot be satisfied"}
```

---

### **4. Evidence Analyzer Agent**

**Responsibility:** Causal analysis and root cause diagnosis

**Tools:**

- `discover_dag(metrics)` → Learn causal graph from data
- `estimate_causal_effect(treatment, outcome)` → Quantify impact
- `granger_causality(metric_a, metric_b)` → Time-lagged causation
- `counterfactual_analysis(action, expected_impact)` → "What if?"

**Framework:** DoWhy, pgmpy

**Example:**

```python
from dowhy import CausalModel

class EvidenceAnalyzerAgent:
    async def explain_change(self, metric: str, time_range: tuple) -> dict:
        # Get data
        data = await self.get_metrics_data(time_range)
        
        # Build causal model
        model = CausalModel(
            data=data,
            treatment='marketing_spend',
            outcome=metric,
            common_causes=['seasonality', 'competitor_activity']
        )
        
        # Identify and estimate causal effect
        identified_estimand = model.identify_effect()
        estimate = model.estimate_effect(identified_estimand)
        
        # Generate explanation
        explanation = f"""
        {metric} changed due to:
        1. Marketing spend: ${estimate.value:.2f} per $1 spent (p-value: {estimate.p_value:.3f})
        2. Seasonality: {self.analyze_seasonality(data)}
        3. Competitor activity: {self.analyze_competitors(data)}
        """
        
        return {
            "causal_factors": self.parse_factors(explanation),
            "confidence": 1 - estimate.p_value,
            "evidence_graph": self.build_graph(model)
        }
```

---

### **5. Data Analyst Agent**

**Responsibility:** Query metrics, generate reports

**Tools:**

- `query_metrics(filters, aggregations)` → Flexible SQL generation
- `generate_visualization(data, chart_type)` → Chart configurations
- `export_data(query, format)` → CSV, Excel, JSON

**Example:**

```python
class DataAnalystAgent:
    async def answer_query(self, query: str) -> dict:
        # Parse query intent
        intent = await self.parse_intent(query)
        
        # Generate SQL
        sql = self.build_sql(intent['filters'], intent['aggregations'])
        
        # Execute
        results = await self.db.execute(sql)
        
        # Generate visualization
        chart_config = self.suggest_visualization(results, intent['metric_type'])
        
        return {
            "data": results,
            "visualization": chart_config,
            "summary": self.summarize_results(results)
        }
```

---

## 🔄 LangGraph State Machine

### **State Definition**

```python
from typing import TypedDict, List, Optional
from langgraph.graph import StateGraph, END

class CoachState(TypedDict):
    user_query: str
    conversation_history: List[dict]
    
    # Retrieved context
    retrieved_context: str
    relevant_metrics: dict
    
    # Agent outputs
    goal_plan: Optional[dict]
    forecast_result: Optional[dict]
    optimization_result: Optional[dict]
    evidence_result: Optional[dict]
    
    # Final response
    final_response: str
    response_confidence: float
```

---

### **Agent Nodes**

```python
# Define agent nodes
async def retrieve_context(state: CoachState) -> CoachState:
    """RAG: Retrieve similar conversations using pgvector"""
    embedding = embed_query(state["user_query"])
    similar = await db.vector_search(embedding, limit=5)
    state["retrieved_context"] = similar
    return state

async def route_to_agents(state: CoachState) -> str:
    """Decide which agents to invoke based on query"""
    intent = classify_intent(state["user_query"])
    
    if "goal" in intent:
        return "goal_planner"
    elif "forecast" in intent or "predict" in intent:
        return "forecaster"
    elif "optimize" in intent or "reduce cost" in intent:
        return "optimizer"
    elif "why" in intent or "explain" in intent:
        return "evidence"
    else:
        return "data_analyst"

async def goal_planner_node(state: CoachState) -> CoachState:
    agent = GoalPlannerAgent()
    state["goal_plan"] = await agent.plan_goal(state["user_query"])
    return state

async def forecaster_node(state: CoachState) -> CoachState:
    agent = ForecasterAgent()
    state["forecast_result"] = await agent.forecast("revenue", horizon=30)
    return state

async def optimizer_node(state: CoachState) -> CoachState:
    agent = OptimizerAgent()
    state["optimization_result"] = await agent.optimize_inventory(...)
    return state

async def evidence_node(state: CoachState) -> CoachState:
    agent = EvidenceAnalyzerAgent()
    state["evidence_result"] = await agent.explain_change("revenue", ...)
    return state

async def generate_response(state: CoachState) -> CoachState:
    """Synthesize all agent outputs into natural language"""
    response = synthesize_response(
        goal=state.get("goal_plan"),
        forecast=state.get("forecast_result"),
        optimization=state.get("optimization_result"),
        evidence=state.get("evidence_result")
    )
    state["final_response"] = response
    return state
```

---

### **Build Graph**

```python
# Create state graph
workflow = StateGraph(CoachState)

# Add nodes
workflow.add_node("retrieve", retrieve_context)
workflow.add_node("goal_planner", goal_planner_node)
workflow.add_node("forecaster", forecaster_node)
workflow.add_node("optimizer", optimizer_node)
workflow.add_node("evidence", evidence_node)
workflow.add_node("respond", generate_response)

# Define routing
workflow.set_entry_point("retrieve")
workflow.add_conditional_edges("retrieve", route_to_agents)

# All agents route to response generator
workflow.add_edge("goal_planner", "respond")
workflow.add_edge("forecaster", "respond")
workflow.add_edge("optimizer", "respond")
workflow.add_edge("evidence", "respond")
workflow.add_edge("respond", END)

# Compile
app = workflow.compile()
```

---

## 🤝 Agent Coordination

### **Coordination Patterns**

1. **Sequential** (for dependent tasks)

```
Goal Planner → Forecaster → Optimizer → Evidence → Response
```

2. **Parallel** (for independent tasks)

```python
async def parallel_agents(state):
    results = await asyncio.gather(
        forecaster_node(state),
        evidence_node(state),
        optimizer_node(state)
    )
    return merge_results(results)
```

3. **Human-in-the-Loop** (for critical decisions)

```python
async def optimizer_node(state):
    solution = await solve_optimization(state)
    
    if solution["impact"] == "high":  # e.g., "lay off 5 employees"
        # Request human approval
        state["requires_approval"] = True
        state["pending_action"] = solution
        return state
    else:
        # Auto-execute
        state["optimization_result"] = solution
        return state
```

---

## 💻 Implementation

### **FastAPI Integration**

```python
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/coach", tags=["coach"])

@router.post("/ask")
async def ask_coach(query: str, tenant_id: str):
    """Streaming coach response using Server-Sent Events"""
    
    async def event_stream():
        # Initialize state
        initial_state = {
            "user_query": query,
            "conversation_history": [],
            "retrieved_context": "",
            "final_response": ""
        }
        
        # Stream agent outputs
        async for chunk in app.astream(initial_state):
            if "goal_plan" in chunk:
                yield f"data: {json.dumps({'type': 'goal', 'data': chunk['goal_plan']})}\n\n"
            if "forecast_result" in chunk:
                yield f"data: {json.dumps({'type': 'forecast', 'data': chunk['forecast_result']})}\n\n"
            if "optimization_result" in chunk:
                yield f"data: {json.dumps({'type': 'optimization', 'data': chunk['optimization_result']})}\n\n"
            if "final_response" in chunk:
                yield f"data: {json.dumps({'type': 'response', 'data': chunk['final_response']})}\n\n"
        
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(event_stream(), media_type="text/event-stream")
```

---

## 🎯 Next Steps

1. **Review [AI & Analytics Stack](./AI & Analytics Stack.md)** for model details
2. **Review [Service Architecture](./Service-Architecture.md)** for modular design
3. **Start Phase 1** of [Implementation Roadmap](./Implementation-Roadmap.md)

**Ready to build multi-agent coach! 🚀**
