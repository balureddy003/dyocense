# Coach Contextual Responses Fix

## Problem

The coach UI was including irrelevant metrics in responses:

- **Inventory analysis** showed "$0 revenue" and "0 customers"
- Responses were plain text instead of rich HTML formatting
- Generic terminology ("inventory") instead of industry-specific terms ("stock", "products")

## Root Cause

1. **Unconditional metric calculation**: All metrics (revenue, inventory, customers) were calculated regardless of the query type
2. **No prompt filtering**: Even when metrics were conditionally calculated, the LLM prompt included ALL metrics
3. **No HTML formatting instructions**: The system prompt didn't instruct the LLM to generate structured HTML
4. **Generic terminology**: No use of industry-specific terms in prompts

## Solution Implemented

### 1. Conditional Metric Calculation (main.py)

**Location**: `services/smb_gateway/main.py` lines 1053-1120

```python
# Only calculate metrics relevant to the task type
if "orders" in data_requirements or "revenue" in data_requirements:
    # Calculate revenue metrics
    metrics["revenue_last_30_days"] = ...
    metrics["orders_last_30_days"] = ...

if "inventory" in data_requirements:
    # Calculate inventory metrics
    metrics["total_inventory_value"] = ...
    metrics["low_stock_items"] = ...

if "customers" in data_requirements:
    # Calculate customer metrics
    metrics["total_customers"] = ...
    metrics["repeat_customer_rate"] = ...
```

**Result**: Only relevant metrics are calculated and added to business_context

### 2. Dynamic Business Profiling (business_profiler.py)

**Location**: `services/smb_gateway/business_profiler.py`

**Features**:

- Detects industry from tenant metadata (retail, ecommerce, saas, restaurant, healthcare, manufacturing, services)
- Maps industry-specific terminology:
  - Retail: "products", "customers", "orders"
  - Healthcare: "patients", "appointments", "supplies"
  - Restaurant: "menu items", "guests", "orders"
- Provides recommended analyses per industry

**Usage**:

```python
business_profile = BusinessProfiler.get_profile(
    tenant_metadata=tenant_metadata,
    data_samples=data_samples
)
# Returns: BusinessProfile(industry="retail", terminology={"items": "products"})
```

### 3. Prompt Filtering (multi_agent_coach.py)

**Location**: `services/smb_gateway/multi_agent_coach.py`

#### A. Specialized Agent Prompt (`_build_specialized_prompt`)

**Lines**: 332-540

**Changes**:

```python
# 🎯 Filter metrics based on task type
task_type = business_context.get("task_type", "general")
all_metrics = business_context.get("metrics", {})

if task_type == "inventory_analysis":
    # Only include inventory metrics in prompt
    relevant_metrics = {k: v for k, v in all_metrics.items() 
                       if "inventory" in k.lower() or "stock" in k.lower()}
elif task_type == "revenue_analysis":
    relevant_metrics = {k: v for k, v in all_metrics.items() 
                       if "revenue" in k.lower() or "sales" in k.lower()}
elif task_type == "customer_analysis":
    relevant_metrics = {k: v for k, v in all_metrics.items() 
                       if "customer" in k.lower()}
else:
    relevant_metrics = all_metrics
```

**Context Sections** (conditionally included):

- **Inventory analysis**: Shows only inventory data, excludes revenue/customer sections
- **Revenue analysis**: Shows only order/revenue data, excludes inventory/customer sections
- **Customer analysis**: Shows only customer data, excludes inventory/revenue sections

#### B. General Agent Prompt (`_build_general_prompt`)

**Lines**: 907-1040

**Same filtering logic** applied to general conversation path

### 4. HTML Formatting Instructions

**Location**: Both `_build_specialized_prompt` and `_build_general_prompt`

**Added to system prompts**:

```python
prompt += f"""

RESPONSE FORMAT (CRITICAL):
Your response MUST be formatted as rich HTML with proper structure:

1. Use semantic HTML elements:
   - <h2> for main sections
   - <h3> for subsections
   - <p> for paragraphs
   - <ul> and <li> for lists
   - <strong> for emphasis
   - <table> for structured data

2. Example structure:
   <div class="analysis-report">
     <h2>📊 {terminology.get('items', 'Products').capitalize()} Analysis</h2>
     
     <h3>Key Findings</h3>
     <ul>
       <li><strong>Finding 1:</strong> Description with numbers</li>
     </ul>
     
     <h3>Recommendations</h3>
     <ol>
       <li>Action with guidance</li>
     </ol>
   </div>

3. Use terminology: "{items_term}" not generic terms
4. Reference specific numbers from the data

CRITICAL: Do NOT include metrics outside the scope of {task_type}.
"""
```

### 5. Enhanced Logging

**Location**: `services/smb_gateway/main.py` and `multi_agent_coach.py`

**main.py logging**:

```python
logger.info(f"[coach_chat_stream] 🏢 Business Profile Detected:")
logger.info(f"[coach_chat_stream]   - Industry: {business_profile.industry}")
logger.info(f"[coach_chat_stream]   - Terminology: {business_profile.terminology}")
logger.info(f"[coach_chat_stream] 📋 Metrics calculated: {list(metrics.keys())}")
logger.info(f"[coach_chat_stream] 🚨 Alerts calculated: {list(alerts.keys())}")
```

**multi_agent_coach.py logging**:

```python
logger.info(f"[_build_specialized_prompt] 📊 Task type: {task_type}")
logger.info(f"[_build_specialized_prompt] 📋 Filtered metrics: {list(relevant_metrics.keys())}")
logger.info(f"[_build_specialized_prompt] 🚨 Filtered alerts: {list(relevant_alerts.keys())}")

# Before LLM invocation
logger.info(f"📝 Prompt length: {len(prompt)} chars")
logger.info(f"📝 Prompt preview (first 300 chars):\n{prompt[:300]}...")
logger.info(f"📝 Prompt preview (last 500 chars):\n...{prompt[-500:]}")
```

## Expected Behavior

### Example: "Analyze product stock"

**Before Fix**:

```
Response (plain text):
You have 541,909 products in stock.
Your revenue is $0 from 0 orders.
You have 0 customers.
```

**After Fix**:

```html
<div class="analysis-report">
  <h2>📊 Product Stock Analysis</h2>
  
  <h3>Key Findings</h3>
  <ul>
    <li><strong>Total Products:</strong> 541,909 items in your inventory</li>
    <li><strong>Low Stock Items:</strong> 45 products need reordering</li>
    <li><strong>Inventory Value:</strong> $2.3M total stock value</li>
  </ul>
  
  <h3>Recommendations</h3>
  <ol>
    <li><strong>Reorder Priority:</strong> Focus on the 45 low-stock items to avoid stockouts</li>
    <li><strong>Slow Movers:</strong> Consider discounting 120 products with zero sales in 90 days</li>
  </ol>
</div>
```

**Logs**:

```
[coach_chat_stream] 📋 Metrics calculated: ['total_inventory_value', 'low_stock_items']
[_build_specialized_prompt] 📊 Task type: inventory_analysis
[_build_specialized_prompt] 📋 Filtered metrics: ['total_inventory_value', 'low_stock_items']
```

## Testing Checklist

- [ ] Inventory analysis shows ONLY inventory metrics (no revenue/customers)
- [ ] Revenue analysis shows ONLY revenue metrics (no inventory)
- [ ] Customer analysis shows ONLY customer metrics (no inventory)
- [ ] Responses use HTML formatting (h2, h3, ul, li, strong, table)
- [ ] Industry-specific terminology is used ("products" for retail, not "inventory")
- [ ] Logs show filtered metrics matching task type
- [ ] Sample data warning appears when no real data connected
- [ ] Downloadable reports use correct terminology

## Files Changed

1. **services/smb_gateway/main.py**
   - Lines 1053-1120: Conditional metric calculation
   - Lines 1165-1200: Business profile integration and logging

2. **services/smb_gateway/multi_agent_coach.py**
   - Lines 332-540: Enhanced `_build_specialized_prompt` with filtering and HTML instructions
   - Lines 907-1040: Enhanced `_build_general_prompt` with filtering and HTML instructions
   - Lines 740-745: Improved logging for LLM invocation

3. **services/smb_gateway/business_profiler.py**
   - New file (238 lines): Dynamic industry detection and terminology mapping

4. **services/smb_gateway/report_generator.py**
   - New file (378 lines): Report generation with chart structures

## Next Steps

1. **Test the changes**: Run inventory, revenue, and customer analysis queries
2. **Verify logs**: Check that filtered metrics match task type
3. **Check HTML rendering**: Ensure frontend renders HTML properly
4. **Validate terminology**: Verify industry-specific terms are used
5. **Test report downloads**: Ensure downloadable reports work correctly

## Related Documents

- `COACH_UI_IMPROVEMENT_PLAN.md` - Original improvement plan
- `MULTI_INTENT_DETECTION_FIX.md` - Task orchestration implementation
- `ARCHITECTURE_SUMMARY.md` - Overall system architecture
