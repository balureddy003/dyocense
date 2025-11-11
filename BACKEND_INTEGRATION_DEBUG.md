# Backend Integration Fix - Coach V4

## 🔧 Changes Made

### Issue

Conversations were not tenant-scoped, causing data to leak between different users/tenants. All users were seeing the same conversation history stored in a global localStorage key.

### Solution

Made all conversation storage **tenant-specific** by:

1. **Updated `lib/conversations.ts`**:
   - Changed `STORAGE_KEY` from global to tenant-scoped: `coach_conversations_${tenantId}`
   - Added `tenantId` field to `Conversation` interface
   - All functions now require `tenantId` parameter:
     - `loadConversations(tenantId)`
     - `saveConversation(conversation, tenantId)`
     - `deleteConversation(id, tenantId)`
     - `getConversation(id, tenantId)`

2. **Updated `CoachV4.tsx`**:
   - Pass `tenantId` to all conversation functions
   - Added null checks to prevent errors when `tenantId` is not available
   - Added comprehensive logging to debug backend integration

3. **Added Debug Logging**:
   - Logs when message is sent to backend (endpoint, tenantId, agent, message preview)
   - Logs backend response status
   - Logs each SSE chunk received
   - Logs metadata and runUrl when available
   - Logs errors with full details

---

## ✅ Verification Checklist

### 1. Check localStorage is Tenant-Scoped

**Open DevTools → Application → Local Storage**

You should see keys like:

- `coach_conversations_tenant-123` ← Your tenant's conversations
- `coach_conversations_tenant-456` ← Different tenant's conversations

**NOT** a global key like:

- ~~`coach_conversations`~~ ← This would leak data!

### 2. Verify Backend API Calls

**Open DevTools → Console**

When you send a message, you should see:

```
[CoachV4] Sending message to backend: {
    endpoint: "https://api.dyocense.com/v1/tenants/your-tenant-id/coach/chat/stream",
    tenantId: "your-tenant-id",
    agent: "business_analyst",
    messagePreview: "What's my revenue?"
}
[CoachV4] Backend response status: 200
[CoachV4] SSE data received: { delta: "Based on your...", metadata: {...} }
```

### 3. Check Network Tab

**Open DevTools → Network → Filter: "stream"**

Request to: `/v1/tenants/{your-tenant-id}/coach/chat/stream`

- Method: POST
- Headers:
  - `Authorization: Bearer {your-token}`
  - `Content-Type: application/json`
- Payload:

  ```json
  {
    "message": "What's my revenue?",
    "conversation_history": [...],
    "persona": "business_analyst",
    "include_evidence": true,
    "include_forecast": false,
    "data_sources": []
  }
  ```

### 4. Verify Tenant Isolation

**Test with two different tenants:**

1. Login as Tenant A
2. Create conversation: "Test A"
3. Check localStorage → `coach_conversations_tenant-A` → Should see "Test A"
4. Logout
5. Login as Tenant B
6. Check localStorage → `coach_conversations_tenant-B` → Should be empty
7. Create conversation: "Test B"
8. Logout and login as Tenant A again
9. Should still see "Test A", NOT "Test B" ✅

---

## 🐛 Debugging "Random Answers"

If you're still seeing incorrect/random answers, check these:

### Issue 1: Backend Not Receiving Tenant Context

**Symptom**: AI gives generic answers not based on your business data

**Check Console Logs**:

```
[CoachV4] Sending message to backend: { tenantId: "null" }  ← BAD!
```

**Fix**: Ensure user is properly authenticated and `tenantId` is set in auth store

**Verify**:

```typescript
// In browser console:
localStorage.getItem('auth_store')
// Should contain: { tenantId: "...", apiToken: "..." }
```

### Issue 2: Backend Using Wrong Tenant Data

**Symptom**: Seeing another tenant's data

**Check Backend Logs**:

- Backend should log: `Processing request for tenant: {tenantId}`
- Verify it's querying correct tenant's data from database

**Frontend Check**:

```javascript
// In DevTools Console
useAuthStore.getState().tenantId  // Should match your actual tenant ID
```

### Issue 3: Backend Not Analyzing Real Data

**Symptom**: Answers are generic/"made up" even for logged-in user

**Possible Causes**:

1. Backend not connected to data sources (Stripe, QuickBooks, etc.)
2. Data sources not synced for this tenant
3. LangGraph agent not configured to query tenant's data

**Check**:

- Health score API: `/v1/tenants/{id}/health-score` → Should return real data
- Goals API: `/v1/tenants/{id}/goals` → Should return your goals
- If these return empty/mock data → Backend integration issue, not frontend

### Issue 4: Caching Old Responses

**Symptom**: Same answer for different questions

**Fix**:

1. Clear browser cache
2. Hard refresh (Cmd+Shift+R / Ctrl+Shift+F5)
3. Check if backend has response caching enabled

---

## 📊 Expected Backend Response Format

The backend `/v1/tenants/{id}/coach/chat/stream` endpoint should return **Server-Sent Events (SSE)**:

```
data: {"delta": "Based ", "metadata": {}}
data: {"delta": "on your ", "metadata": {}}
data: {"delta": "revenue data", "metadata": {"evidence": [...]}}
data: {"done": true, "runUrl": "https://smith.langchain.com/..."}
```

### Full Response Example

```json
// Chunk 1
{
  "delta": "Your revenue last month was $45,231. ",
  "metadata": {
    "dataSources": [
      {
        "name": "Stripe",
        "icon": "stripe",
        "lastSync": "2025-11-11T10:30:00Z",
        "recordCount": 1243
      }
    ]
  }
}

// Chunk 2
{
  "delta": "This is down 12% from October. ",
  "metadata": {
    "evidence": [
      {
        "claim": "Revenue down 12%",
        "source": "Stripe MRR Report",
        "confidence": 95,
        "data": { "oct": 51420, "nov": 45231 },
        "timestamp": "2025-11-11T10:30:00Z"
      }
    ]
  }
}

// Final chunk
{
  "done": true,
  "runUrl": "https://smith.langchain.com/public/abc123/r/def456"
}
```

---

## 🔍 Debugging Steps

### Step 1: Verify Auth State

```javascript
// Browser Console
const state = useAuthStore.getState()
console.log('User:', state.user)
console.log('Tenant ID:', state.tenantId)
console.log('Token:', state.apiToken ? 'Present' : 'Missing')
```

### Step 2: Test Backend Directly

```bash
# Using curl
curl -X POST https://your-api.com/v1/tenants/YOUR_TENANT_ID/coach/chat/stream \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is my revenue?",
    "conversation_history": [],
    "persona": "business_analyst"
  }'
```

**Expected**: Streaming response with actual business data
**If you get**: Generic/random answer → Backend issue, not frontend

### Step 3: Check Data Sources

```javascript
// Browser Console - Check if backend has data
fetch('/v1/tenants/' + useAuthStore.getState().tenantId + '/health-score', {
  headers: { 'Authorization': 'Bearer ' + useAuthStore.getState().apiToken }
})
.then(r => r.json())
.then(d => console.log('Health Score Data:', d))
```

**Expected**: Real health score from your data
**If empty/null**: Data sources not connected or synced

---

## 🎯 Action Items for Backend Team

If frontend logs show correct API calls but responses are still wrong:

### 1. Verify Tenant Context Propagation

```python
# Backend (FastAPI example)
@app.post("/v1/tenants/{tenant_id}/coach/chat/stream")
async def coach_chat(tenant_id: str, request: ChatRequest):
    # CRITICAL: Verify this tenant_id is used in all queries
    print(f"Processing for tenant: {tenant_id}")  # ← Add this log
    
    # BAD: Using global/hardcoded data
    # health_data = get_global_health_score()
    
    # GOOD: Using tenant-specific data
    health_data = get_health_score(tenant_id)  # ← Ensure this!
```

### 2. Verify LangGraph Agent Configuration

```python
# Ensure agent has access to tenant-specific tools
tools = [
    get_revenue_tool(tenant_id),      # ← NOT global!
    get_customer_tool(tenant_id),     # ← Tenant-specific
    get_inventory_tool(tenant_id),    # ← Tenant-scoped
]

agent = create_agent(llm, tools)
```

### 3. Add Response Validation

```python
# Before streaming response, verify it contains tenant data
response = agent.invoke({"input": message, "tenant_id": tenant_id})

# Validate response mentions tenant-specific data
if not contains_tenant_data(response, tenant_id):
    logger.warning(f"Generic response for tenant {tenant_id}")
    # Fallback or retry with more context
```

---

## ✅ Success Criteria

Frontend integration is correct when:

1. ✅ Console logs show correct `tenantId` in all API calls
2. ✅ Network tab shows requests to `/v1/tenants/{correct-id}/...`
3. ✅ Conversations are stored in `coach_conversations_{tenantId}` key
4. ✅ Different tenants see different conversation histories
5. ✅ Auth token is included in all requests

Backend integration is correct when:

1. ✅ Responses contain tenant-specific business data (revenue, customers, etc.)
2. ✅ Health score matches actual business metrics
3. ✅ Recommendations are based on real data, not generic advice
4. ✅ Evidence citations reference actual data sources (Stripe, QuickBooks, etc.)
5. ✅ Backend logs confirm tenant context is used in all queries

---

## 📞 Support

**Issue**: "Still seeing random answers"

**Questions to Ask**:

1. What does browser console show? (Share logs)
2. What does Network tab show? (Share request/response)
3. What does backend log show? (Share server logs)
4. Is user authenticated? (Check auth state)
5. Does health score API return real data? (Test endpoint)

**Next Steps**:

- If console shows correct tenantId → Backend issue
- If console shows null/undefined tenantId → Auth issue
- If backend returns generic data → Data source/LangGraph config issue
