# AI Coach Data Connection Improvements

## Changes Made

### 1. Enhanced Sample Data Generation

**File:** `/services/smb_gateway/main.py` - `_fetch_connector_data()` function

The AI Coach was showing generic responses because it was using very basic sample data. I've upgraded the sample data to be much more realistic and meaningful:

#### Orders (Last 90 Days)

- **720+ orders** with realistic daily patterns
- More orders on weekdays, fewer on weekends
- Order amounts vary realistically
- Each order has: ID, customer, amount, status, items, date, category
- Product categories: outdoor-gear, equipment, accessories, clothing

#### Inventory (20 Items)

- **20 realistic products** across 4 categories
- Proper SKUs and product names
- **Realistic stock issues:**
  - ~14% items are LOW STOCK (2 units)
  - ~9% items are OUT OF STOCK (0 units)
  - Rest are in healthy stock levels
- Each item has: SKU, name, category, quantity, reorder point, costs, supplier

#### Customers (200 Customers)

- **Customer segmentation:**
  - 10% VIP customers (15+ orders, $5000+ LTV)
  - 30% Regular customers (5+ orders, $1500+ LTV)
  - 60% Occasional customers (1-3 orders, $300+ LTV)
- Each customer has: ID, name, email, total orders, lifetime value, segment, last order date

### 2. Data Connection Awareness in Multi-Agent Coach

**File:** `/services/smb_gateway/multi_agent_coach.py`

Added comprehensive data connection awareness to all specialist agents:

#### Each Agent Now Shows

- **Data Status:** Whether real data is connected or using sample data
- **Data Warnings:** Clear messaging when no real data is available
- **Encouragement:** Guides users to connect real data sources
- **Agent-Specific Context:**
  - **Data Analyst:** "Real data would enable actual pattern detection"
  - **Data Scientist:** "Forecasts would be accurate with connected data"
  - **Goal Analyzer:** "Progress tracking needs real data"
  - **Business Consultant:** "Recommendations would be data-driven"

#### Data Connection Display

```
⚠️ NO REAL DATA CONNECTED (Using Sample Data):
- Sample Orders: 720
- Sample Inventory: 20
- Sample Customers: 200

TO GET ACCURATE INSIGHTS, connect:
📦 E-commerce: Shopify, WooCommerce, GrandNode
👥 CRM: Salesforce, HubSpot
💰 Accounting: QuickBooks, Xero

This will unlock:
✨ Real-time business health monitoring
📊 Accurate data analysis
🎯 Personalized recommendations
📈 Trend analysis and forecasting
```

### 3. Improved Health Score Calculation

The health score calculator now works with realistic data patterns:

- **Revenue Health:** Based on 90 days of order history with growth trends
- **Operations Health:** Calculates from realistic inventory levels and stockouts
- **Customer Health:** Uses customer segments and engagement patterns

## Current State

### ✅ What's Working

1. **Dashboard shows realistic metrics:**
   - Revenue from 720 orders over 90 days
   - Inventory status with actual low-stock items
   - Customer segments (VIP, Regular, Occasional)
   - Health scores based on meaningful data

2. **AI Coach provides intelligent responses:**
   - Data Analyst can analyze real sales trends
   - Data Scientist can forecast based on 90 days of data
   - Goal Analyzer has customer segments to work with
   - Business Consultant sees actual inventory issues

3. **Data connection awareness:**
   - Coach tells users data is sample data
   - Explains benefits of connecting real sources
   - Shows what data types are needed

### ⚠️ Limitations (Sample Data)

Since we're using generated sample data:

1. **Not tenant-specific** - All tenants see the same sample data pattern
2. **Not real-time** - Data is generated on server start
3. **No actual integrations** - Not pulling from GrandNode, Shopify, etc.

## Next Steps for Production

### Phase 1: Connect Real Data Sources

To move from sample data to real data:

1. **Option A: Use Connector Service**

   ```bash
   # Start connector service
   cd /Users/balu/Projects/dyocense
   bash scripts/start_connector_service.sh
   ```

2. **Connect a real data source:**
   - Go to Data Connections in UI
   - Add connector (e.g., Shopify, WooCommerce)
   - Configure authentication
   - Sync data

3. **Update `_fetch_connector_data()` to call connector service:**

   ```python
   # In services/smb_gateway/main.py
   async def _fetch_connector_data(tenant_id: str) -> Dict:
       # Call connector service API
       connectors = await fetch_tenant_connectors(tenant_id)
       # Aggregate data from all active connectors
       return aggregate_connector_data(connectors)
   ```

### Phase 2: Real-Time Data Sync

1. **Add background job to sync connector data**
2. **Cache synced data in Redis/PostgreSQL**
3. **Update dashboard in real-time**

### Phase 3: Per-Tenant Data

1. **Store connector data by tenant_id**
2. **Implement data isolation**
3. **Add tenant-specific analytics**

## Testing the Improvements

### Test AI Coach Responses

```bash
# 1. Ask about sales trends
curl -N -X POST "http://localhost:8001/v1/tenants/demo-tenant/coach/chat/stream" \
  -H "Authorization: Bearer demo-token" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are my sales trends?",
    "conversation_history": []
  }'

# Expected: Analysis of 90 days of orders with weekday/weekend patterns

# 2. Ask about inventory issues
curl -N -X POST "http://localhost:8001/v1/tenants/demo-tenant/coach/chat/stream" \
  -H "Authorization: Bearer demo-token" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Which products are low on stock?",
    "conversation_history": []
  }'

# Expected: List of low-stock and out-of-stock items with specific SKUs

# 3. Ask about customer segments
curl -N -X POST "http://localhost:8001/v1/tenants/demo-tenant/coach/chat/stream" \
  -H "Authorization: Bearer demo-token" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Who are my best customers?",
    "conversation_history": []
  }'

# Expected: Analysis of VIP customers with specific metrics
```

### Verify Dashboard Metrics

```bash
# Check health score
curl "http://localhost:8001/v1/tenants/demo-tenant/health-score"

# Expected: Realistic scores based on:
# - Revenue growth from 90 days of orders
# - Inventory turnover from stock levels
# - Customer retention from segment data
```

## Files Modified

1. `/services/smb_gateway/main.py`
   - Enhanced `_fetch_connector_data()` with realistic sample data
   - Added `timedelta` import

2. `/services/smb_gateway/multi_agent_coach.py`
   - Added data connection awareness to `_build_specialized_prompt()`
   - Enhanced fallback responses with data connection prompts
   - Added agent-specific data connection messaging

3. `/scripts/test_multi_agent_data_awareness.py` (NEW)
   - Test script to verify data connection awareness
   - Tests all 4 specialist agents
   - Validates prompt generation

## Summary

The AI Coach is now working with **realistic, meaningful sample data** instead of generic responses. It can analyze actual patterns like:

- 📊 Sales trends over 90 days with weekday/weekend patterns
- 📦 Inventory issues with specific low-stock SKUs
- 👥 Customer segmentation (VIP, Regular, Occasional)
- 📈 Growth trends and health scores

And it **clearly communicates** when sample data is being used vs. real connected data, encouraging users to connect their actual business data sources for accurate insights.
