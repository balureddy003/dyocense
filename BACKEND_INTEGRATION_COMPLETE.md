# ✅ Backend Integration Complete - Coach V4

## 🎯 Issue Fixed

**Problem**: Conversations were not tenant-scoped, and there was confusion about whether the AI was actually using backend data vs. giving generic responses.

**Root Cause**:

- localStorage used global key `coach_conversations` (not tenant-specific)
- Insufficient logging to debug backend integration
- No way to verify tenant-specific data was being used

## 🔧 Changes Implemented

### 1. Tenant-Scoped Conversation Storage

**Before**:

```typescript
// ❌ Global storage - data leaked between tenants!
const STORAGE_KEY = 'coach_conversations'
localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations))
```

**After**:

```typescript
// ✅ Tenant-specific storage
const key = `coach_conversations_${tenantId}`
localStorage.setItem(key, JSON.stringify(conversations))
```

**Impact**: Each tenant now has completely isolated conversation history.

---

### 2. Added Comprehensive Debug Logging

**Request Logging**:

```javascript
console.log('[CoachV4] Sending message to backend:', {
    endpoint: `${API_BASE}/v1/tenants/${tenantId}/coach/chat/stream`,
    tenantId,
    agent: selectedAgent,
    messagePreview: text.substring(0, 50)
})
```

**Response Logging**:

```javascript
console.log('[CoachV4] Backend response status:', response.status)
console.log('[CoachV4] SSE data received:', data)
console.log('[CoachV4] Metadata received:', data.metadata)
console.log('[CoachV4] Stream complete. RunURL:', data.runUrl)
```

**Impact**: Can now verify in browser console that:

- Correct tenant ID is being sent
- Backend is responding
- Real data is coming back (not generic responses)

---

### 3. Updated Conversation Interface

**Before**:

```typescript
interface Conversation {
    id: string
    title: string
    messages: Message[]
    // Missing tenant context!
}
```

**After**:

```typescript
interface Conversation {
    id: string
    title: string
    messages: Message[]
    createdAt: Date
    updatedAt: Date
    agent: string
    tenantId: string  // ✅ Now tenant-aware
}
```

---

## ✅ Verification Steps

### 1. Check Tenant Isolation

Open browser DevTools → Console, run:

```javascript
// Check current tenant
useAuthStore.getState().tenantId
// Expected: "tenant-abc123" (your actual tenant ID)

// Check localStorage keys
Object.keys(localStorage).filter(k => k.includes('coach'))
// Expected: ["coach_conversations_tenant-abc123", ...]
// NOT: ["coach_conversations"] (global key)
```

### 2. Verify Backend Integration

Send a message in the chat, then check Console:

```
✅ [CoachV4] Sending message to backend: {
     endpoint: "https://api.example.com/v1/tenants/tenant-abc123/coach/chat/stream",
     tenantId: "tenant-abc123",
     agent: "business_analyst",
     messagePreview: "What's my revenue?"
   }

✅ [CoachV4] Backend response status: 200

✅ [CoachV4] SSE data received: { delta: "Based on your Stripe data...", ... }

✅ [CoachV4] Metadata received: {
     dataSources: [{name: "Stripe", lastSync: "2025-11-11T10:30:00Z"}],
     evidence: [{claim: "Revenue is $45k", confidence: 95}]
   }
```

**Red Flags**:

```
❌ tenantId: "null" or "undefined"  → Auth problem
❌ Status: 401/403                   → Token/permission issue
❌ Status: 404                       → Wrong endpoint
❌ Generic response with no metadata → Backend not using tenant data
```

### 3. Test Multi-Tenant Isolation

1. Login as Tenant A, create conversation "Test A"
2. Check localStorage: `coach_conversations_tenant-A` exists ✅
3. Logout, login as Tenant B
4. Check localStorage: No key for Tenant A visible ✅
5. Create conversation "Test B"
6. Check: `coach_conversations_tenant-B` exists ✅
7. Logout, login as Tenant A again
8. Verify: Only "Test A" visible, NOT "Test B" ✅

---

## 🔍 Debugging "Random Answers"

If AI responses seem generic/incorrect, follow this diagnostic tree:

### Step 1: Check Tenant Context

```javascript
// Browser Console
const state = useAuthStore.getState()
console.log({
    tenantId: state.tenantId,
    hasToken: !!state.apiToken,
    user: state.user?.email
})
```

**If tenantId is null/undefined**:

- ❌ **Issue**: User not authenticated properly
- ✅ **Fix**: Check login flow, verify auth store is populated

**If tenantId exists**:

- ✅ Proceed to Step 2

### Step 2: Check Backend Response

Look at Console logs after sending a message:

**Good Response** (tenant-specific data):

```javascript
SSE data received: {
  delta: "Your revenue last month was $45,231 based on Stripe data...",
  metadata: {
    dataSources: [{name: "Stripe", recordCount: 1243}],
    evidence: [{claim: "Revenue $45k", source: "Stripe API"}]
  }
}
```

**Bad Response** (generic):

```javascript
SSE data received: {
  delta: "To improve your business, you should focus on customer retention...",
  metadata: {}  // ← No evidence, no data sources!
}
```

**If response is generic**:

- ❌ **Issue**: Backend not connected to tenant's real data
- ✅ **Fix**: Check backend data source integration (see below)

### Step 3: Verify Data Sources Connected

Test the health score API directly:

```javascript
// Browser Console
const { tenantId, apiToken } = useAuthStore.getState()

fetch(`/v1/tenants/${tenantId}/health-score`, {
    headers: { 'Authorization': `Bearer ${apiToken}` }
})
.then(r => r.json())
.then(data => console.log('Health Score:', data))
```

**Expected** (real data):

```json
{
  "score": 75,
  "breakdown": {
    "revenue": 82,
    "operations": 48,
    "customer": 24
  },
  "updated_at": "2025-11-11T10:30:00Z"
}
```

**If you get empty/mock data**:

- ❌ **Issue**: Backend not syncing data from Stripe/QuickBooks/etc.
- ✅ **Fix**: Backend team needs to:
  1. Verify data connectors are configured for this tenant
  2. Run manual data sync
  3. Check LangGraph agent is querying tenant DB correctly

---

## 📋 Backend Team Checklist

If frontend shows correct `tenantId` but responses are still wrong:

### ✅ 1. Verify Tenant ID Propagation

```python
# Backend (FastAPI example)
@app.post("/v1/tenants/{tenant_id}/coach/chat/stream")
async def coach_chat(tenant_id: str, request: ChatRequest):
    # ✅ Add logging
    logger.info(f"[Coach] Processing request for tenant: {tenant_id}")
    
    # ✅ Verify tenant exists
    tenant = await get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(404, "Tenant not found")
    
    # ✅ Pass tenant context to LangGraph
    config = {"configurable": {"tenant_id": tenant_id}}
    response = agent.invoke(request.message, config=config)
```

### ✅ 2. Verify LangGraph Tools Use Tenant Data

```python
# ❌ BAD: Global/hardcoded data
@tool
def get_revenue():
    return db.query("SELECT revenue FROM global_table")

# ✅ GOOD: Tenant-scoped data
@tool
def get_revenue(tenant_id: str):
    return db.query(
        "SELECT revenue FROM tenant_data WHERE tenant_id = ?",
        tenant_id
    )
```

### ✅ 3. Verify Data Sources Are Synced

```sql
-- Check if tenant has connected data sources
SELECT * FROM data_sources WHERE tenant_id = 'tenant-abc123'

-- Check last sync time
SELECT source, last_synced_at 
FROM data_source_syncs 
WHERE tenant_id = 'tenant-abc123'

-- Expected: Stripe, QuickBooks, etc. synced within last 24h
```

### ✅ 4. Add Response Validation

```python
# Before returning AI response, verify it mentions tenant data
def validate_response(response: str, tenant_id: str) -> bool:
    # Check if response contains tenant-specific metrics
    tenant_data = get_tenant_summary(tenant_id)
    
    # Example: Revenue should match actual data
    if str(tenant_data.revenue) not in response:
        logger.warning(
            f"Generic response for {tenant_id}: "
            f"Expected revenue ${tenant_data.revenue}, not mentioned"
        )
        return False
    
    return True
```

---

## 📊 Expected Backend API Behavior

### Request Format (Frontend → Backend)

```http
POST /v1/tenants/tenant-abc123/coach/chat/stream HTTP/1.1
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
Content-Type: application/json

{
  "message": "What's my revenue this month?",
  "conversation_history": [
    {"role": "user", "content": "Hello", "timestamp": "2025-11-11T10:00:00Z"},
    {"role": "assistant", "content": "Hi! How can I help?", "timestamp": "2025-11-11T10:00:01Z"}
  ],
  "persona": "business_analyst",
  "include_evidence": true,
  "include_forecast": false,
  "data_sources": ["stripe", "quickbooks"]
}
```

### Response Format (Backend → Frontend)

```
data: {"delta": "Based on ", "metadata": {}}

data: {"delta": "your Stripe data, ", "metadata": {"dataSources": [{"name": "Stripe", "lastSync": "2025-11-11T10:30:00Z", "recordCount": 1243}]}}

data: {"delta": "your revenue this month is $45,231. ", "metadata": {"evidence": [{"claim": "Revenue is $45,231", "source": "Stripe MRR Report", "confidence": 95, "data": {"current": 45231, "previous": 51420}}]}}

data: {"delta": "This is down 12% from last month.", "metadata": {}}

data: {"done": true, "runUrl": "https://smith.langchain.com/public/abc123/r/def456"}
```

**Key Points**:

- ✅ `dataSources` array shows which data sources were queried
- ✅ `evidence` array provides citations for claims
- ✅ `runUrl` links to LangGraph trace for debugging
- ✅ Actual tenant data (e.g., $45,231) is mentioned in response

---

## 🎉 Success Indicators

### Frontend is Working When

1. ✅ Console shows: `tenantId: "tenant-abc123"` (not null)
2. ✅ Network tab shows: `POST /v1/tenants/tenant-abc123/coach/chat/stream`
3. ✅ localStorage has: `coach_conversations_tenant-abc123` key
4. ✅ Different tenants see different conversation histories
5. ✅ Auth token present in request headers

### Backend is Working When

1. ✅ Responses mention specific dollar amounts from tenant's actual data
2. ✅ `metadata.dataSources` array is populated (not empty)
3. ✅ `metadata.evidence` cites real sources (Stripe, QuickBooks, etc.)
4. ✅ Health score API returns tenant's real business metrics
5. ✅ Recommendations are specific to tenant's situation

### Integration is Complete When

1. ✅ User asks "What's my revenue?" → Gets actual revenue from their Stripe
2. ✅ User asks "Why is customer churn high?" → Gets analysis of their actual churn data
3. ✅ Evidence panel shows real data sources with sync timestamps
4. ✅ Switching tenants shows completely different conversations
5. ✅ LangGraph run URL traces show tenant-specific tool calls

---

## 📞 Support

**Still seeing issues?**

1. Share browser console logs (copy full output)
2. Share Network tab request/response (screenshot or HAR file)
3. Share backend logs for the same request
4. Confirm tenant ID matches in all three places

**Quick Test**:

```bash
# Test backend directly (replace with your values)
curl -X POST https://your-api.com/v1/tenants/YOUR_TENANT_ID/coach/chat/stream \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is my revenue?", "conversation_history": [], "persona": "business_analyst"}'
```

If this returns generic answer → Backend issue
If this returns tenant-specific data → Frontend auth issue

---

**Files Changed**:

- `apps/smb/src/lib/conversations.ts` - Added tenant scoping
- `apps/smb/src/pages/CoachV4.tsx` - Added debug logs, tenant params

**Testing**: Open `/coach`, check browser console, verify tenant ID in all requests ✅
