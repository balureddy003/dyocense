# Scalable Multi-Business Architecture

## Problem

Previously, business-specific analysis methods like `_analyze_inventory_data()` were hardcoded into `MultiAgentCoach` and `CoachService`. This creates tight coupling and doesn't scale across different business domains:

- ❌ SMB Retail: Hardcoded inventory analysis
- ❌ Healthcare: Would need to hardcode patient/supply analysis
- ❌ Manufacturing: Would need to hardcode production analysis
- ❌ Restaurant: Would need to hardcode ingredient/menu analysis
- ❌ Every new business vertical = modify coach code

## Solution: Plugin-Based Tool Architecture

### Architecture Components

```
┌─────────────────────────────────────────────────────────────┐
│                      MultiAgentCoach                         │
│                      CoachService                            │
│  (Business-agnostic - no domain logic)                      │
└────────────────┬────────────────────────────────────────────┘
                 │
                 │ Uses
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                   CoachOrchestrator                          │
│  • Detects user intent (inventory, revenue, forecast)       │
│  • Maps to generic tool names ("analyze_inventory")         │
│  • Creates execution plans                                   │
└────────────────┬────────────────────────────────────────────┘
                 │
                 │ Delegates to
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                     ToolExecutor                             │
│  • Maintains tool registry                                   │
│  • Routes tool_name → registered function                    │
│  • Executes tools dynamically                                │
│  • Returns results to coach                                  │
└────────────────┬────────────────────────────────────────────┘
                 │
                 │ Invokes
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                   Analysis Tools                             │
│  • analyze_inventory_data() - SMB retail                     │
│  • analyze_revenue_data() - SMB retail                       │
│  • analyze_customer_data() - SMB retail                      │
│  • analyze_health_metrics() - Cross-industry                 │
│  • [Future] analyze_patient_care() - Healthcare              │
│  • [Future] analyze_production() - Manufacturing             │
└─────────────────────────────────────────────────────────────┘
```

### Key Files

**1. `tool_executor.py`** (NEW)

- `ToolExecutor` class: Manages tool registry and execution
- `get_tool_executor()`: Global singleton accessor
- `execute(tool_name, business_context)`: Dynamic tool invocation
- No business logic - pure routing and execution

**2. `analysis_tools.py`** (NEW)

- `analyze_inventory_data()`: SMB retail inventory analysis
- `analyze_revenue_data()`: Revenue trends and patterns
- `analyze_customer_data()`: Customer metrics and segments
- `analyze_health_metrics()`: Cross-industry health scoring
- Each function is independent, testable, swappable

**3. `multi_agent_coach.py`** (MODIFIED)

- Removed hardcoded `_analyze_inventory_data()` method
- Added `self.tool_executor = get_tool_executor()`
- Tool execution now uses `tool_executor.execute(tool_name, context)`
- Comment: "Business-specific analysis methods removed - now handled by ToolExecutor"

**4. `coach_service.py`** (MODIFIED)

- Added `self.tool_executor = get_tool_executor()`
- Changed `self._analyze_inventory_data()` → `self.tool_executor.execute("analyze_inventory", ...)`
- Decoupled from specific business domain

**5. `coach_orchestrator.py`** (UNCHANGED)

- Already used generic tool names like "analyze_inventory"
- No changes needed - designed for extensibility

## Benefits

### ✅ Scalability

Each business vertical can register its own tools:

```python
# SMB Retail
executor.register_tool("analyze_inventory", smb_inventory_analysis)

# Healthcare
executor.register_tool("analyze_inventory", medical_supplies_analysis)

# Restaurant
executor.register_tool("analyze_inventory", ingredient_stock_analysis)
```

### ✅ Decoupling

- **MultiAgentCoach**: Zero business logic, just orchestration
- **CoachOrchestrator**: Intent detection, task planning
- **ToolExecutor**: Tool registry and execution routing
- **Analysis Tools**: Isolated business logic functions

### ✅ Testability

Each analysis function can be tested independently:

```python
def test_inventory_analysis():
    context = {"metrics": {"total_inventory_items": 100, ...}}
    result = analyze_inventory_data(context)
    assert result["total_items"] == 100
```

### ✅ Extensibility

Add new tools without modifying coach:

```python
# New domain: Manufacturing
def analyze_production_line(context: Dict[str, Any]) -> Dict[str, Any]:
    # Production-specific logic
    pass

executor.register_tool("analyze_production", analyze_production_line)
```

### ✅ Tenant-Specific Customization

Different tenants in same industry can have custom implementations:

```python
if tenant_industry == "healthcare":
    if tenant_type == "hospital":
        executor.register_tool("analyze_inventory", hospital_inventory)
    elif tenant_type == "clinic":
        executor.register_tool("analyze_inventory", clinic_inventory)
```

## Migration Path

### Phase 1: ✅ COMPLETE

- Created `ToolExecutor` and `analysis_tools.py`
- Registered default SMB retail tools
- Updated `MultiAgentCoach` and `CoachService` to use ToolExecutor
- Removed hardcoded business methods

### Phase 2: Future

- Add industry-specific tool modules:
  - `analysis_tools_healthcare.py`
  - `analysis_tools_manufacturing.py`
  - `analysis_tools_restaurant.py`
- Create tool loader based on tenant industry
- Add tool versioning for A/B testing

### Phase 3: Future

- MCP tool integration (CSV query tools)
- External agent tools (diagnostician, optimizer)
- Custom tenant tools (uploaded Python scripts)

## Usage Example

### Before (Hardcoded)

```python
# In MultiAgentCoach
def _analyze_inventory_data(self, context):
    # Hardcoded SMB retail logic
    metrics = context.get("metrics", {})
    total_items = metrics.get("total_inventory_items", 0)
    # ... 40 lines of business logic
    return result
```

### After (Pluggable)

```python
# In MultiAgentCoach - no business logic
result = self.tool_executor.execute("analyze_inventory", business_context)

# Business logic in separate file (analysis_tools.py)
def analyze_inventory_data(context: Dict[str, Any]) -> Dict[str, Any]:
    # Same logic, but decoupled and reusable
    return result
```

## Adding a New Business Domain

**Example: Restaurant Industry**

1. Create `analysis_tools_restaurant.py`:

```python
def analyze_ingredient_stock(context: Dict[str, Any]) -> Dict[str, Any]:
    """Restaurant-specific inventory analysis"""
    metrics = context.get("metrics", {})
    perishable_items = metrics.get("perishable_count", 0)
    shelf_life_warnings = metrics.get("expiring_soon", 0)
    # Restaurant-specific calculations
    return {
        "perishable_items": perishable_items,
        "expiring_soon": shelf_life_warnings,
        "recommendations": [...]
    }

def analyze_menu_performance(context: Dict[str, Any]) -> Dict[str, Any]:
    """Menu item popularity and profitability"""
    # Menu-specific logic
    pass
```

2. Register tools for restaurant tenants:

```python
if tenant_industry == "restaurant":
    executor = get_tool_executor()
    executor.register_tool("analyze_inventory", analyze_ingredient_stock)
    executor.register_tool("analyze_menu", analyze_menu_performance)
```

3. No changes needed to:

- ❌ `MultiAgentCoach` - stays business-agnostic
- ❌ `CoachService` - stays business-agnostic
- ❌ `CoachOrchestrator` - already uses generic names
- ✅ Just add new tool files and register them!

## Testing

### Unit Test Example

```python
def test_inventory_analysis_with_tool_executor():
    executor = ToolExecutor()
    
    context = {
        "metrics": {
            "total_inventory_items": 541909,
            "low_stock_items": 55000,
            "out_of_stock_items": 24500,
            "total_inventory_value": 1250000
        }
    }
    
    result = executor.execute("analyze_inventory", context)
    
    assert result["total_items"] == 541909
    assert "stock_health" in result
    assert result["stock_health"]["in_stock"]["percentage"] > 0
```

### Integration Test Example

```python
def test_multi_agent_coach_with_tool_executor():
    coach = MultiAgentCoach()
    
    # Simulate user request
    async for chunk in coach.stream_response(
        tenant_id="test",
        user_message="analyze my inventory",
        business_context={...}
    ):
        # Verify tool execution happened
        assert "inventory_analysis" in business_context.get("tool_results", {})
```

## Conclusion

This architecture enables **true multi-business scalability**:

- ✅ Add new industries without modifying coach
- ✅ Swap implementations per tenant
- ✅ Test business logic independently
- ✅ Version and A/B test analysis algorithms
- ✅ Support custom tenant-specific tools

The coach is now a **generic orchestration engine** that works across any business domain! 🎉
