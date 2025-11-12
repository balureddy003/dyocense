# Research Agent Architecture - Schema-Aware Dynamic Analysis

## Overview

The Research Agent is a **self-adaptive system** that analyzes ANY SMB data structure without hardcoding. It works like GitHub Copilot for business data analysis.

## Key Features

### 1. **Dynamic Schema Discovery**

- Automatically detects field names, types, and semantics
- Identifies identifiers (ID, Code, SKU)
- Detects quantities, prices, dates, descriptions
- No hardcoded field names required

### 2. **Query Decomposition**

- Breaks complex queries into executable tasks
- Creates dependency chains
- Prioritizes tasks
- Generates execution plans

### 3. **Adaptive Code Generation**

- Generates Python code based on discovered schema
- Adapts aggregations to actual field names
- Creates trend analysis using detected date fields
- Builds segmentation using identified grouping fields

### 4. **Multi-Step Orchestration**

- Executes tasks in dependency order
- Collects results progressively
- Handles failures gracefully
- Streams results to frontend

## Architecture

```
User Query
    ↓
Research Agent
    ↓
┌─────────────────────────┐
│ 1. Schema Discovery     │ ← Inspect data structure
│    - Detect fields      │
│    - Identify semantics │
│    - Map data types     │
└─────────────────────────┘
    ↓
┌─────────────────────────┐
│ 2. Query Decomposition  │ ← Break down intent
│    - Identify sub-tasks │
│    - Build dependencies │
│    - Prioritize         │
└─────────────────────────┘
    ↓
┌─────────────────────────┐
│ 3. Code Generation      │ ← Generate analysis code
│    - Aggregations       │
│    - Trends             │
│    - Segmentations      │
└─────────────────────────┘
    ↓
┌─────────────────────────┐
│ 4. Execution            │ ← Run generated code
│    - Execute tasks      │
│    - Collect metrics    │
│    - Handle errors      │
└─────────────────────────┘
    ↓
Results → Coach LLM → Rich HTML Response
```

## Example Flow

### User Query

```
"Please do detailed product stock analysis"
```

### 1. Schema Discovery

```python
# Discovers your actual data structure
inventory_schema = {
    "data_type": "INVENTORY",
    "record_count": 541909,
    "fields": {
        "StockCode": SchemaField(is_identifier=True),
        "Description": SchemaField(is_descriptor=True),
        "Quantity": SchemaField(is_quantity=True, is_numeric=True),
        "UnitPrice": SchemaField(is_monetary=True, is_numeric=True),
        "InvoiceDate": SchemaField(is_temporal=True),
        "CustomerID": SchemaField(is_identifier=True),
        "Country": SchemaField(is_descriptor=True)
    },
    "semantic_fields": {
        "identifier": "StockCode",
        "descriptor": "Description",
        "quantity": "Quantity",
        "price": "UnitPrice",
        "date": "InvoiceDate",
        "customer": "CustomerID"
    }
}
```

### 2. Query Decomposition

```python
research_plan = ResearchPlan(
    tasks=[
        ResearchTask(
            task_id="task_001",
            description="Validate data schema",
            task_type="schema_discovery",
            dependencies=[]
        ),
        ResearchTask(
            task_id="task_002",
            description="Calculate key metrics from inventory",
            task_type="aggregation",
            dependencies=["task_001"],
            required_fields=["Quantity", "UnitPrice"]
        ),
        ResearchTask(
            task_id="task_003",
            description="Analyze trends over time",
            task_type="trend_analysis",
            dependencies=["task_001"],
            required_fields=["InvoiceDate"]
        ),
        ResearchTask(
            task_id="task_004",
            description="Segment inventory by stock code",
            task_type="segmentation",
            dependencies=["task_001"],
            required_fields=["StockCode"]
        )
    ],
    execution_order=["task_001", "task_002", "task_003", "task_004"]
)
```

### 3. Generated Code (Adaptive)

```python
# Task 002: Aggregation (generated dynamically)
total_quantity = sum(abs(item.get('Quantity', 0)) for item in data)
total_value = sum(
    abs(item.get('Quantity', 0)) * float(item.get('UnitPrice', 0)) 
    for item in data
)
result = {
    'total_quantity': total_quantity,
    'total_value': round(total_value, 2),
    'record_count': len(data)
}
```

### 4. Execution Results

```python
metrics = {
    "total_quantity": 5176450,
    "total_value": 9747747.93,
    "average_value": 18.00,
    "record_count": 541909
}

analysis_results = {
    "task_001": {"schema": {...}},
    "task_002": {"total_quantity": 5176450, ...},
    "task_003": {"trends_by_month": {...}},
    "task_004": {"top_products": [...]}
}
```

## Benefits

### ✅ Zero Hardcoding

- Works with ANY data connector
- Adapts to ANY field names
- Handles ANY data structure

### ✅ Scalable

- Add new connectors → automatic schema discovery
- New data types → automatic detection
- New analysis types → generated code

### ✅ Intelligent

- Understands semantic meaning (ID, price, quantity)
- Decomposes complex queries
- Generates optimal execution plans

### ✅ Maintainable

- Single agent handles all data types
- No per-connector custom code
- Clear separation of concerns

## Integration Points

### 1. Main Coach Flow (main.py)

```python
# Replace hardcoded calculations with research agent
from .research_agent import get_research_agent

research_agent = get_research_agent()
research_plan = research_agent.research(user_query, available_data)

# Execute plan and collect metrics
for task in research_plan.tasks:
    result = execute_task(task)
    metrics.update(result)
```

### 2. Schema Discovery

```python
# Automatic schema detection
schema = SchemaDiscoveryAgent.discover_schema(data, "inventory")

# Access discovered fields
quantity_field = schema.quantity_field  # "Quantity" or "qty" or "amount"
price_field = schema.price_field        # "UnitPrice" or "price" or "cost"
```

### 3. Code Generation

```python
# Generate adaptive analysis code
task = ResearchTask(task_type="aggregation", ...)
code = research_agent._generate_aggregation_code(schema, task)

# Execute generated code
exec(code, {"data": inventory_data})
```

## Comparison with Old Approach

### Old (Hardcoded)

```python
# ❌ Fails if field names differ
total = sum(i.get("quantity", 0) * i.get("unit_cost", 0) for i in inventory)
low_stock = [i for i in inventory if i.get("status") == "low_stock"]
```

### New (Dynamic)

```python
# ✅ Adapts to actual field names
schema = discover_schema(inventory)
quantity_field = schema.quantity_field  # Discovered: "Quantity"
price_field = schema.price_field        # Discovered: "UnitPrice"

total = sum(
    i.get(quantity_field, 0) * i.get(price_field, 0) 
    for i in inventory
)
```

## Future Enhancements

1. **ML-Based Schema Learning**
   - Learn from user corrections
   - Improve field detection accuracy
   - Build industry-specific templates

2. **Query Optimization**
   - Cache discovered schemas
   - Reuse execution plans
   - Parallel task execution

3. **Advanced Analytics**
   - Anomaly detection
   - Predictive modeling
   - Correlation analysis

4. **Multi-Connector Joins**
   - Join data from multiple sources
   - Cross-reference analysis
   - Unified reporting

## Files

### Core Components

- `research_agent.py` - Main research agent and schema discovery
- `main.py` - Integration with coach flow
- `multi_agent_coach.py` - Prompt generation with research context

### Supporting Files

- `business_profiler.py` - Industry-specific terminology
- `coach_orchestrator.py` - Task planning (complementary)
- `analysis_tools.py` - Reusable analysis functions

## Testing

Test with different data structures:

```python
# E-commerce data
data_ecommerce = [
    {"sku": "ABC", "name": "Product", "qty": 10, "cost": 5.99}
]

# Healthcare data
data_healthcare = [
    {"item_id": "MED123", "supply_name": "Bandages", "stock_level": 50, "unit_price": 2.50}
]

# Restaurant data
data_restaurant = [
    {"ingredient_code": "ING001", "ingredient": "Flour", "amount": 100, "price_per_unit": 0.50}
]

# Research agent handles all automatically
for data in [data_ecommerce, data_healthcare, data_restaurant]:
    schema = discover_schema(data)
    plan = research_agent.research("analyze inventory", {"inventory": data})
    # Works with zero changes!
```

## Conclusion

The Research Agent transforms the coach from a **hardcoded** system to a **self-adaptive** platform that scales to ANY SMB and ANY data connector.

Like GitHub Copilot understands code context, the Research Agent understands data context and generates appropriate analysis code dynamically.
