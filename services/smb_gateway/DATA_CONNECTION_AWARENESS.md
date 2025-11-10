# Data Connection Awareness Feature

## Overview

The AI Coach now detects whether users have connected their business data sources and encourages them to connect data for better insights.

## How It Works

### 1. Data Detection

When a user interacts with the AI Coach, the system checks:

- Whether real connector data exists (`tenant_id in TENANT_CONNECTOR_DATA`)
- Total number of orders, inventory items, and customers
- If data appears to be sample/mock data

**Business Context includes:**

```json
{
  "has_data_connected": true/false,
  "data_sources": {
    "orders": 100,
    "inventory": 50,
    "customers": 150
  }
}
```

### 2. Intent Detection

New intent type added: **`data_connection`**

Triggered by keywords:

- connect, data, integrate, source
- connection, connector
- "How do I connect my data?"
- "What integrations are available?"

### 3. Conversational Responses

**When NO data is connected:**

The AI Coach will:

- ✨ Gently encourage data connection
- 📊 Explain benefits (real-time insights, accurate analytics, personalized recommendations)
- 🔌 Mention available integrations (Shopify, Salesforce, QuickBooks, etc.)
- 💡 Frame it as "unlocking better insights" (not pushy)

**Example responses:**

*For help/advice questions:*
> "I'd love to help you with personalized insights! 💡 To give you the most accurate advice, I recommend connecting your business data sources (like your e-commerce platform or CRM). This will help me understand your revenue trends, inventory levels, and customer behavior. Would you like to know more about connecting your data? 📊"

*For health score questions:*
> "Your current health score is 75/100 based on sample data. For real-time insights based on your actual business, I recommend connecting your data sources. This will give you accurate revenue tracking, inventory alerts, and customer insights! 📈"

*For general greetings (no data):*
> "I'm here to help with YourBusiness! 👋 For the best experience, I recommend connecting your business data sources first. This will unlock personalized insights, real-time analytics, and accurate recommendations. What would you like to explore - data integration, goals, or current insights? 💡"

**When data IS connected:**

The AI Coach will:

- ✅ Provide personalized insights based on real data
- 📈 Reference actual metrics (orders, inventory, customers)
- 🎯 Give specific, actionable recommendations
- 💪 Celebrate progress and patterns

## Available Integrations

The coach mentions these integration types:

**E-commerce:**

- Shopify
- WooCommerce
- GrandNode

**CRM:**

- Salesforce
- HubSpot

**Accounting:**

- QuickBooks
- Xero

## System Prompt Enhancements

The conversational prompt now includes a **DATA CONNECTION STATUS** section:

```
⚠️ NO REAL DATA CONNECTED
The user has not connected their business data sources yet.
- Orders: 0 (sample data)
- Inventory: 0 (sample data)
- Customers: 0 (sample data)

IMPORTANT: You should gently encourage them to connect their real business data to get personalized insights.
...

Will enable you to provide:
✨ Real-time business health monitoring
📊 Accurate revenue and sales analytics
🎯 Personalized recommendations based on their actual data
📈 Trend analysis and forecasting
💡 Proactive alerts about opportunities and issues
```

Or when connected:

```
✅ DATA CONNECTED
- Orders: 100
- Inventory: 50
- Customers: 150
```

## User Experience

### Scenario 1: New User, No Data

**User:** "Hello!"

**AI Coach:** "I'm here to help with your business! 👋 For the best experience, I recommend connecting your business data sources first. This will unlock personalized insights, real-time analytics, and accurate recommendations. What would you like to explore - data integration, goals, or current insights? 💡"

### Scenario 2: User Asks About Connecting Data

**User:** "How do I connect my data?"

**AI Coach:** "Great question! 🎯 You can connect various data sources to get personalized insights:

📦 E-commerce: Shopify, WooCommerce, GrandNode
👥 CRM: Salesforce, HubSpot
💰 Accounting: QuickBooks, Xero

Once connected, I can provide real-time analytics, trend analysis, and proactive recommendations based on your actual business data. Would you like help getting started?"

### Scenario 3: User Asks for Advice (No Data)

**User:** "How can I improve my revenue?"

**AI Coach:** "I'd love to help you with personalized insights! 💡 To give you the most accurate advice, I recommend connecting your business data sources (like your e-commerce platform or CRM). This will help me understand your revenue trends, inventory levels, and customer behavior. Would you like to know more about connecting your data? 📊"

### Scenario 4: User With Connected Data

**User:** "How's my revenue looking?"

**AI Coach:** "Your revenue is up 15% this month compared to last! 📈 You've processed 100 orders totaling $15,000. Your top-selling items are driving this growth. Want to explore opportunities to maintain this momentum? 💪"

## Implementation Details

### Backend Changes

**File: `/services/smb_gateway/main.py`**

Both coach endpoints now include:

```python
# Check if data is connected
has_real_data = tenant_id in TENANT_CONNECTOR_DATA
total_orders = len(connector_data.get("orders", []))
total_inventory = len(connector_data.get("inventory", []))
total_customers = len(connector_data.get("customers", []))
has_data_connected = has_real_data or (total_orders > 0 and total_inventory > 0)

# Add to business context
business_context = {
    "has_data_connected": has_data_connected,
    "data_sources": {
        "orders": total_orders,
        "inventory": total_inventory,
        "customers": total_customers,
    },
    ...
}
```

**File: `/services/smb_gateway/conversational_coach.py`**

Updates:

1. New intent: `data_connection`
2. Enhanced prompt with data connection status
3. Fallback responses prioritize data connection when not connected
4. Context-aware responses based on `has_data_connected` flag

### Testing

**Test without data:**

```bash
curl -N -X POST "http://localhost:8000/v1/tenants/test-tenant/coach/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{"message": "How can you help me?", "conversation_history": []}'
```

**Test with data:**

1. Add tenant to `TENANT_CONNECTOR_DATA` in main.py
2. Run same curl command
3. Observe different response style

**Frontend Testing:**

1. Navigate to home page
2. Open AI Coach
3. Try these messages:
   - "Hello!" (should mention data connection)
   - "How do I connect my data?" (should list integrations)
   - "What's my health score?" (should note it's sample data)

## Benefits

**For Users:**

- 🎯 Clear guidance on how to get better insights
- 📊 Understanding of why data connection matters
- 🔌 Knowledge of available integrations
- 💡 Motivation to connect real data

**For Business:**

- ⬆️ Increased data connection rate
- 📈 Better engagement with real data users
- 🎓 Educated users about platform capabilities
- 💪 More valuable insights when data is connected

## Future Enhancements

Potential improvements:

- [ ] Direct links to connector setup pages
- [ ] "Connect Data" button in chat responses
- [ ] Show which specific connectors are already connected
- [ ] Estimate improvement in insights after connecting data
- [ ] Onboarding wizard triggered from chat
- [ ] Track data connection conversions from AI Coach
- [ ] Personalized integration recommendations based on industry
- [ ] Show preview of insights available with connected data

## Configuration

No additional configuration needed. The feature works automatically by checking:

1. `TENANT_CONNECTOR_DATA` dictionary for real data
2. Connector data structure (orders, inventory, customers)
3. Business context passed to AI Coach

## Monitoring

Track these metrics:

- % of conversations with data_connection intent
- Data connection rate after AI Coach interaction
- User satisfaction when data is/isn't connected
- Most common questions about data connection

## Summary

The AI Coach now intelligently detects when users haven't connected their business data and encourages them to do so in a friendly, helpful way. This improves user engagement and increases the value of the platform by driving data connections.

**Key Principle:** Be helpful and encouraging, not pushy or annoying.
