# Coach V4 - Troubleshooting "Not Answering" Issue

## Quick Diagnosis Steps

### Step 1: Check Browser Console

1. Open DevTools (F12 or Cmd+Option+I)
2. Go to **Console** tab
3. Look for these log messages when page loads:

```
[CoachV4] Auth state: { tenantId: "...", hasApiToken: true, user: "your@email.com" }
```

**Problem Signs:**

- ❌ `tenantId: undefined` → Not logged in properly
- ❌ `hasApiToken: false` → No authentication token
- ❌ `user: 'Not logged in'` → User not authenticated

**Fix:** Log in again or check localStorage for `apiToken` and `tenantId`

---

### Step 2: Check Backend Connection

When you send a message, look for:

```
[CoachV4] Sending message to backend: {
    endpoint: "http://localhost:8001/v1/tenants/.../coach/chat/stream",
    tenantId: "...",
    agent: "business_analyst",
    messagePreview: "..."
}
[CoachV4] Backend response status: 200
[CoachV4] SSE data received: { delta: "I can help...", metadata: {...} }
```

**Problem Signs:**

- ❌ No logs appear → Frontend not calling backend
- ❌ `Backend response status: 404` → Endpoint doesn't exist
- ❌ `Backend response status: 401` → Authentication failed
- ❌ `Backend response status: 500` → Backend error
- ❌ No SSE data logs → Backend not streaming

---

### Step 3: Check Network Tab

1. DevTools → **Network** tab
2. Send a message
3. Look for request to `/coach/chat/stream`

**Click on the request and check:**

**Request Headers:**

```
POST /v1/tenants/{YOUR_TENANT_ID}/coach/chat/stream
Authorization: Bearer {YOUR_TOKEN}
Content-Type: application/json
```

**Request Payload:**

```json
{
  "message": "Your question",
  "conversation_history": [...],
  "persona": "business_analyst",
  "include_evidence": true,
  "include_forecast": false,
  "data_sources": []
}
```

**Response (EventStream):**

```
data: {"delta":"I","metadata":{}}
data: {"delta":" can","metadata":{}}
data: {"delta":" help","metadata":{}}
...
data: {"done":true,"metadata":{"run_url":"..."}}
```

**Problem Signs:**

- ❌ Request shows status `(failed)` → Network issue or backend not running
- ❌ Response is JSON error → Backend returned error instead of streaming
- ❌ Response is empty → Backend not sending data

---

## Common Issues & Fixes

### Issue 1: "Missing authentication! tenantId or apiToken is undefined"

**Cause:** User not logged in or auth state lost

**Fix:**

```javascript
// Check localStorage in Console
localStorage.getItem('apiToken')
localStorage.getItem('tenantId')

// If missing, log in again or manually set (for testing):
localStorage.setItem('apiToken', 'your-test-token')
localStorage.setItem('tenantId', 'test-tenant-123')
location.reload()
```

---

### Issue 2: "Backend response status: 404"

**Cause:** Backend not running or wrong port

**Fix:**

```bash
# Check if backend is running
curl http://localhost:8001/health

# If not running, start backend:
cd /Users/balu/Projects/dyocense
source .venv/bin/activate
python services/smb_gateway/main.py

# Or using make:
make run-smb
```

---

### Issue 3: "Backend response status: 500"

**Cause:** Backend error (check backend logs)

**Fix:**

1. Check backend terminal for error logs
2. Look for Python stack trace
3. Common causes:
   - Database connection failed
   - Missing environment variables
   - LangGraph/OpenAI API key missing

---

### Issue 4: Backend returns JSON error instead of streaming

**Cause:** Request validation failed or backend exception before streaming starts

**Example Error:**

```json
{
  "detail": "Coach streaming error: ..."
}
```

**Fix:**

1. Check the error message
2. Look at backend logs for full stack trace
3. Verify request payload matches expected schema

---

### Issue 5: SSE data never appears (blank response)

**Cause:** Backend streaming but data not reaching frontend

**Debug Steps:**

1. **Check if data is sent:**

```bash
# Test backend directly with curl
curl -X POST http://localhost:8001/v1/tenants/test-tenant-123/coach/chat/stream \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-token" \
  -d '{"message":"Hello","conversation_history":[],"persona":"business_analyst"}'
```

Expected output:

```
data: {"delta":"I","metadata":{}}
data: {"delta":" can","metadata":{}}
...
```

2. **Check CORS headers:**

- Backend must allow `localhost:5173` (Vite dev server)
- Check for `Access-Control-Allow-Origin` in response headers

3. **Check nginx/proxy buffering:**

- SSE requires `X-Accel-Buffering: no` header
- Backend already sends this, but check if proxy strips it

---

### Issue 6: "Failed to parse SSE data"

**Cause:** Backend sending malformed SSE

**Example Console Warning:**

```
Failed to parse SSE data: SyntaxError: Unexpected token ...
Line: data: {malformed json}
```

**Fix:**

1. Check backend code at `services/smb_gateway/main.py:850`
2. Ensure all SSE lines are valid JSON:

```python
yield f"data: {json.dumps(payload)}\n\n"  # Correct
# NOT: yield f"data: {payload}\n\n"  # Wrong - payload is dict
```

---

## Step-by-Step Debugging Session

### 1. Verify Auth

```javascript
// In browser console:
const store = JSON.parse(localStorage.getItem('auth-storage') || '{}')
console.log('Auth:', store.state)
// Should show: { apiToken: "...", tenantId: "...", user: {...} }
```

### 2. Verify Backend

```bash
# Terminal:
curl -s http://localhost:8001/health | jq
# Should return: {"status":"healthy",...}
```

### 3. Test Chat Endpoint

```bash
# Terminal:
curl -X POST http://localhost:8001/v1/tenants/test-tenant/coach/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message":"test","conversation_history":[],"persona":"business_analyst"}' \
  --no-buffer
# Should stream: data: {"delta":"..."}
```

### 4. Check Frontend API Config

```javascript
// In browser console:
console.log('API_BASE:', import.meta.env.VITE_API_BASE || 'http://localhost:8001')
// Should match backend port
```

### 5. Test Full Flow

1. Open DevTools Console
2. Type a message in chat
3. Press Send
4. Watch for:
   - `[CoachV4] Sending message to backend`
   - `[CoachV4] Backend response status: 200`
   - `[CoachV4] SSE data received`
   - Message appears in chat

---

## Environment Checklist

- [ ] **.env file created** at `/Users/balu/Projects/dyocense/apps/smb/.env`
- [ ] **VITE_API_BASE** set to `http://localhost:8001`
- [ ] **Backend running** on port 8001
- [ ] **User logged in** (apiToken and tenantId in localStorage)
- [ ] **Browser console** shows auth state
- [ ] **Network tab** shows successful request to `/coach/chat/stream`

---

## Quick Fixes

### Fix 1: Create .env file

```bash
cd /Users/balu/Projects/dyocense/apps/smb
echo "VITE_API_BASE=http://localhost:8001" > .env
```

### Fix 2: Restart Vite dev server

```bash
cd /Users/balu/Projects/dyocense/apps/smb
npm run dev
```

*Note: Vite requires restart after creating .env file*

### Fix 3: Set test auth (for development)

```javascript
// Browser console:
localStorage.setItem('apiToken', 'test-token')
localStorage.setItem('tenantId', 'test-tenant-123')
location.reload()
```

### Fix 4: Check backend logs

```bash
# Backend terminal should show:
INFO:     POST /v1/tenants/test-tenant-123/coach/chat/stream
INFO:     Streaming coach response...
```

---

## Success Indicators

✅ **Everything Working:**

```
Console:
  [CoachV4] Auth state: { tenantId: "...", hasApiToken: true, user: "..." }
  [CoachV4] Sending message to backend: {...}
  [CoachV4] Backend response status: 200
  [CoachV4] SSE data received: { delta: "I", metadata: {} }
  [CoachV4] SSE data received: { delta: " can", metadata: {} }
  [CoachV4] SSE data received: { delta: " help", metadata: {} }
  [CoachV4] Stream complete. RunURL: /v1/tenants/.../runs/...

Network:
  POST /v1/tenants/.../coach/chat/stream
  Status: 200
  Type: text/event-stream
  Size: [streaming]

Chat UI:
  Message appears character by character
  Stop button appears during streaming
  Message saved to conversation history
```

---

## Still Not Working?

1. **Capture full console logs:**

```javascript
// Copy all console output and share
console.save = function(data, filename){
    const blob = new Blob([JSON.stringify(data)], {type: 'text/json'});
    const a = document.createElement('a');
    a.download = filename;
    a.href = window.URL.createObjectURL(blob);
    a.click();
}
// Then: console.save(console.history, 'console-logs.json')
```

2. **Capture network HAR:**

- Network tab → Right-click → "Save all as HAR with content"
- Share the .har file

3. **Check backend logs:**

```bash
# If using systemd/pm2:
journalctl -u dyocense-smb-gateway -n 100

# If running manually:
# Check terminal output where you ran `python services/smb_gateway/main.py`
```

---

## Contact Support

If issue persists after trying all above:

1. Share console logs (screenshot or .json export)
2. Share network HAR file
3. Share backend error logs
4. Describe exact steps to reproduce
