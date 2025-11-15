# 🤖 AI & Analytics Stack

**Version:** 4.0 (Hybrid Intelligence)  
**Last Updated:** November 14, 2025  
**Status:** Active Development

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Hybrid LLM Architecture](#hybrid-llm-architecture)
3. [Optimization Layer](#optimization-layer)
4. [Forecasting Layer](#forecasting-layer)
5. [Causal Inference Layer](#causal-inference-layer)
6. [Cost Analysis](#cost-analysis)

---

## 🎯 Overview

### **Key Innovation**

> **"LLMs for language, optimization for decisions, statistics for proof"**

Dyocense combines **3 types of AI**:

1. **Large Language Models (LLMs)** → Natural language understanding, explanations
2. **Mathematical Optimization** → Provably optimal decisions (inventory, staffing, budget)
3. **Causal Inference** → Explain "why" metrics changed (not just correlation)

**Why Hybrid?**

- ✅ **Mathematically Rigorous:** Optimization produces provably optimal solutions
- ✅ **Explainable:** Causal AI explains reasoning (not black-box)
- ✅ **Cost-Effective:** 70% local LLMs = 80% cost savings
- ✅ **Patentable IP:** Unique approach vs. "ChatGPT wrappers"

---

## 🧠 Hybrid LLM Architecture

### **70% Local, 30% Cloud Strategy**

| Metric | Local (Llama 3 8B) | Cloud (GPT-4o) | Savings |
|--------|-------------------|----------------|---------|
| **Cost** | $0.00/query | $0.05/query | 80% |
| **Latency** | 300-500ms | 1-2 seconds | 50-70% faster |
| **Privacy** | 100% local | Data sent to OpenAI | ✅ Local wins |
| **Accuracy** | 85% (good) | 95% (excellent) | Cloud better |

**Routing Logic:**

```python
def route_llm_query(query: str, context: dict) -> LLMProvider:
    # Estimate complexity
    complexity = estimate_query_complexity(query)
    
    if complexity < 0.3:  # Simple queries
        return LocalLlama3_8B()  # 70% of queries
    else:  # Complex reasoning
        return OpenAIGPT4o()  # 30% of queries
```

---

### **Local LLM Setup (Llama 3 8B)**

**Deployment Options:**

1. **Development:** Ollama (easiest setup)

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Download Llama 3 8B
ollama pull llama3

# Run inference
ollama run llama3 "What's my revenue trend?"
```

2. **Production:** vLLM (optimized inference)

```bash
# Install vLLM
pip install vllm

# Start server
python -m vllm.entrypoints.openai.api_server \
  --model meta-llama/Llama-3-8B-Instruct \
  --host 0.0.0.0 --port 8000
```

**Hardware Requirements:**

- **CPU:** 8+ cores
- **RAM:** 16GB+ (8B model needs ~6GB)
- **GPU:** Optional (RTX 3090 speeds up 5-10x)

---

### **Cloud LLMs (OpenAI GPT-4o, Anthropic Claude)**

**When to Use:**

- ✅ Complex multi-step reasoning
- ✅ Creative tasks (marketing copy generation)
- ✅ Ambiguous queries (need clarification)

**Cost Optimization:**

```python
# Cache LLM responses (Redis, 24-hour TTL)
@cache(ttl=86400)
async def get_llm_response(query: str) -> str:
    if query in cache:
        return cache[query]  # Free (cache hit)
    
    response = await openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": query}]
    )
    
    cache[query] = response.choices[0].message.content
    return response.choices[0].message.content
```

---

### **Embeddings (Sentence Transformers)**

**Model:** `all-MiniLM-L6-v2` (384 dimensions, free, local)

**Usage:**

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')

# Embed user query
query_embedding = model.encode("How do I reduce inventory costs?")

# Store in PostgreSQL (pgvector)
await db.execute(
    "INSERT INTO coaching_sessions (query_embedding) VALUES ($1)",
    query_embedding.tolist()
)
```

---

## 🧮 Optimization Layer

### **Mathematical Optimization (OR-Tools, PuLP)**

**Purpose:** Find **provably optimal** decisions (not heuristics)

**Techniques:**

1. **Linear Programming (LP):** Continuous decisions (order 150.5 units)
2. **Mixed-Integer Programming (MILP):** Discrete decisions (hire 3 staff, not 3.2)
3. **Constraint Programming (CP):** Complex scheduling, routing

---

### **Use Case 1: Inventory Optimization**

**Problem:** Minimize total cost (holding + stockouts)

**Formulation:**

```python
from ortools.linear_solver import pywraplp

solver = pywraplp.Solver.CreateSolver('SCIP')

# Decision variables: order quantity for each product
order_qty = {p: solver.NumVar(0, solver.infinity(), f'order_{p}') 
             for p in products}

# Objective: minimize total cost
solver.Minimize(
    sum(holding_cost[p] * order_qty[p] for p in products) +
    sum(stockout_penalty[p] * solver.Max(0, demand[p] - order_qty[p]) 
        for p in products)
)

# Constraints
solver.Add(
    sum(order_qty[p] * volume[p] for p in products) <= warehouse_capacity
)

# Solve
status = solver.Solve()
if status == pywraplp.Solver.OPTIMAL:
    for p in products:
        print(f"Order {order_qty[p].solution_value()} units of {p}")
```

---

### **Use Case 2: Staff Scheduling**

**Problem:** Minimize labor cost while meeting service levels

**Formulation:**

```python
# Decision variables: binary (1 = assign shift, 0 = don't assign)
shifts = {}
for emp in employees:
    for day in days:
        for time_slot in time_slots:
            shifts[(emp, day, time_slot)] = solver.BoolVar(f'{emp}_{day}_{time_slot}')

# Objective: minimize total labor cost
solver.Minimize(
    sum(shifts[(e, d, t)] * hourly_rate[e] for e in employees 
        for d in days for t in time_slots)
)

# Constraints
# 1. Meet demand (at least N employees per time slot)
for d in days:
    for t in time_slots:
        solver.Add(
            sum(shifts[(e, d, t)] for e in employees) >= demand[d][t]
        )

# 2. Max hours per employee (40 hours/week)
for e in employees:
    solver.Add(
        sum(shifts[(e, d, t)] for d in days for t in time_slots) <= 40
        )
```

---

### **Use Case 3: Budget Allocation**

**Problem:** Maximize ROI across marketing channels

```python
# Decision variables: spend per channel
spend = {c: solver.NumVar(0, solver.infinity(), f'spend_{c}') 
         for c in channels}

# Objective: maximize total revenue (diminishing returns model)
solver.Maximize(
    sum(roi_function(c, spend[c]) for c in channels)
)

# Constraints
solver.Add(sum(spend[c] for c in channels) <= total_budget)
```

---

## 📈 Forecasting Layer

### **Time-Series Prediction with Uncertainty**

**Goal:** Predict future metrics + confidence intervals

**Models:**

1. **Auto-ARIMA** (Automatic Parameter Selection)

```python
from pmdarima import auto_arima

model = auto_arima(sales_data, seasonal=True, m=12)
forecast = model.predict(n_periods=30)
```

2. **Prophet** (Seasonality, Holidays, Trend Detection)

```python
from prophet import Prophet

df = pd.DataFrame({'ds': dates, 'y': sales})
model = Prophet(yearly_seasonality=True, weekly_seasonality=True)
model.fit(df)

future = model.make_future_dataframe(periods=30)
forecast = model.predict(future)  # Returns yhat, yhat_lower, yhat_upper
```

3. **XGBoost** (Feature-Based Forecasting)

```python
from xgboost import XGBRegressor

# Create lag features
X = create_lag_features(sales_data, lags=[1, 7, 14, 30])
y = sales_data['revenue']

model = XGBRegressor(n_estimators=100)
model.fit(X_train, y_train)
forecast = model.predict(X_test)
```

4. **Ensemble** (Weighted Average)

```python
# Combine all models (typically 70% accuracy improvement)
ensemble_forecast = (
    0.3 * arima_forecast +
    0.4 * prophet_forecast +
    0.3 * xgboost_forecast
)
```

---

### **Uncertainty Quantification**

**Confidence Intervals:**

```python
# Prophet provides built-in intervals
forecast['yhat']  # Point estimate
forecast['yhat_lower']  # 95% lower bound
forecast['yhat_upper']  # 95% upper bound

# Coach explains to user:
# "Revenue forecast: $50,000 (range: $45,000 - $55,000)"
```

---

## 🔍 Causal Inference Layer

### **Explain "Why" Metrics Changed**

**Goal:** Not just correlation, but **causation**

**Techniques:**

1. **Granger Causality** (Time-Lagged Relationships)

```python
from statsmodels.tsa.stattools import grangercausalitytests

# Test: Does marketing spend cause revenue changes?
data = pd.DataFrame({
    'marketing_spend': [...],
    'revenue': [...]
})

results = grangercausalitytests(data[['revenue', 'marketing_spend']], maxlag=5)

# If p-value < 0.05, marketing spend Granger-causes revenue
```

2. **Bayesian Networks** (Structure Learning)

```python
from pgmpy.estimators import HillClimbSearch, BicScore
from pgmpy.models import BayesianNetwork

# Learn causal structure from data
hc = HillClimbSearch(data)
best_model = hc.estimate(scoring_method=BicScore(data))

# Result: DAG showing relationships
# marketing_spend → website_traffic → leads → revenue
```

3. **DoWhy** (Causal Effect Estimation)

```python
from dowhy import CausalModel

model = CausalModel(
    data=business_data,
    treatment='marketing_spend',
    outcome='revenue',
    common_causes=['seasonality', 'competitor_activity']
)

identified_estimand = model.identify_effect()
estimate = model.estimate_effect(identified_estimand)

print(f"Causal effect: ${estimate.value} revenue per $1 marketing")
# Example output: "$3.50 revenue per $1 marketing spend"
```

4. **Counterfactual Analysis**

```python
# Question: "What if we had spent $10K on marketing instead of $5K?"
counterfactual = model.do(marketing_spend=10000)
predicted_revenue = counterfactual.predict(df)

print(f"Actual revenue: ${actual_revenue}")
print(f"Counterfactual revenue: ${predicted_revenue}")
print(f"Missed opportunity: ${predicted_revenue - actual_revenue}")
```

---

## 💰 Cost Analysis

### **LLM Costs (Per 1000 Queries)**

| Approach | Cost | Latency | Accuracy |
|----------|------|---------|----------|
| **100% Cloud (GPT-4o)** | $50 | 1-2s | 95% |
| **100% Local (Llama 3 8B)** | $0 | 300-500ms | 85% |
| **Hybrid (70% local, 30% cloud)** | $15 | 400ms avg | 90% |

**Annual Savings (for 500 SMBs, 100 queries/SMB/month):**

- Cloud-only: 500 × 100 × 12 × $0.05 = **$30,000/year**
- Hybrid: 500 × 100 × 12 × $0.015 = **$9,000/year**
- **Savings: $21,000/year (70%)**

---

### **Infrastructure Costs**

| Component | Cost (Monthly) | Notes |
|-----------|---------------|-------|
| **Local LLM (Llama 3 8B)** | $0 (included in VM) | Runs on same server as backend |
| **Local LLM (GPU accelerated)** | $80 (GPU droplet) | Optional: 5-10x faster |
| **Cloud LLM (30% of queries)** | $30 | For 500 SMBs |
| **Total AI Costs** | **$30-110/month** | <$1/SMB/month |

---

## 🎯 Next Steps

1. **Review [Multi-Agent System Design](./Multi-Agent System Design.md)** for agent architecture
2. **Review [Design Document](./Design-Document.md)** for overall system
3. **Start Phase 1** of [Implementation Roadmap](./Implementation-Roadmap.md)

**Ready to build hybrid intelligence! 🚀**
