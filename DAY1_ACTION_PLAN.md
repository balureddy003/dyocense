# 🚀 IMMEDIATE ACTION PLAN - Day 1

**Date:** November 7, 2025  
**Goal:** Get UI + Backend running end-to-end  
**Time Estimate:** 4-6 hours

---

## ✅ COMPLETED (Already Done)

1. ✅ **Created E2E_FUNCTIONAL_GAPS.md** - Comprehensive gap analysis
2. ✅ **Created apps/ui/.env** - Frontend configuration
3. ✅ **Pinned langchain versions** - Fixed dependency hell
4. ✅ **Verified CORS middleware** - Already configured in kernel
5. ✅ **Found .env.smb** - Backend config template exists

---

## 🔴 CRITICAL PATH - Do These in Order

### STEP 1: Fix Backend Dependencies (30 minutes)

**Current Issue:** Pip install hangs on langchain version resolution

**Action:**

```bash
cd /Users/balu/Projects/dyocense

# Activate virtual environment
source .venv/bin/activate

# Install with pinned versions (should be fast now)
pip install -r requirements-dev.txt

# Verify installation
python -c "import langgraph; import langchain; import fastapi; print('✅ All imports successful')"
```

**Expected Output:** All packages install in <5 minutes

---

### STEP 2: Configure Backend Environment (15 minutes)

**Action:**

```bash
# Copy SMB environment file
cp .env.smb .env

# Edit .env with your settings
nano .env  # or use VSCode
```

**Required Changes in .env:**

```bash
# Line 16: Update MongoDB URI
# For local testing, use:
MONGO_URI=mongodb://localhost:27017/dyocense_smb

# Or keep Atlas URI and update with your credentials:
# MONGO_URI=mongodb+srv://YOUR_USER:YOUR_PASSWORD@cluster.mongodb.net/dyocense?retryWrites=true&w=majority

# Line 22: Enable anonymous access for testing
ALLOW_ANONYMOUS=true

# Line 40: Add your OpenAI API key (if using OpenAI)
OPENAI_API_KEY=sk-your-key-here

# Or use Ollama (free, local)
# LLM_PROVIDER=ollama
# OLLAMA_BASE_URL=http://localhost:11434
# OLLAMA_MODEL=llama3.1
```

**Deploy MongoDB locally (if needed):**

```bash
# Option 1: Docker (recommended)
docker run -d --name dyocense-mongo -p 27017:27017 mongo:7

# Option 2: MongoDB Atlas (free tier)
# Sign up at https://www.mongodb.com/cloud/atlas
# Create cluster, get connection string
```

---

### STEP 3: Start Backend Service (5 minutes)

**Action:**

```bash
cd /Users/balu/Projects/dyocense
source .venv/bin/activate

# Set Python path and start kernel
PYTHONPATH=. uvicorn services.kernel.main:app --reload --port 8001
```

**Expected Output:**

```
INFO:     Will watch for changes in these directories: ['/Users/balu/Projects/dyocense']
INFO:     Uvicorn running on http://127.0.0.1:8001 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using StatReload
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Verify:**

```bash
# In another terminal:
curl http://localhost:8001/healthz
# Expected: {"status":"ok"}

curl http://localhost:8001/health/detailed
# Expected: JSON with service health checks
```

**Keep this terminal running!**

---

### STEP 4: Start Frontend Service (10 minutes)

**Action:**

```bash
# New terminal
cd /Users/balu/Projects/dyocense/apps/ui

# Install dependencies (if not already done)
npm install

# Start dev server
npm run dev
```

**Expected Output:**

```
  VITE v5.x.x  ready in 1234 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```

**Verify:**

- Open browser to <http://localhost:5173>
- Should see Dyocense UI
- Check browser console for errors

---

### STEP 5: Test End-to-End Connection (15 minutes)

**Action:**

1. Open browser to <http://localhost:5173>
2. Open browser console (F12)
3. Run test API call:

```javascript
// In browser console:
fetch('http://localhost:8001/healthz')
  .then(r => r.json())
  .then(d => console.log('✅ Backend connected:', d))
  .catch(e => console.error('❌ Connection failed:', e))
```

**Expected:** `✅ Backend connected: {status: "ok"}`

**If CORS error:** Check that backend .env has:

```bash
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

---

### STEP 6: Test Multi-Agent Endpoint (20 minutes)

**Action:**

```javascript
// In browser console (with backend running):
const testGoal = {
  goal: "I want to reduce my restaurant inventory costs by 15% while maintaining 95% service level",
  context: {
    industry: "restaurant",
    location: "San Francisco",
    size: "single_location"
  },
  llm_config: {
    provider: "openai",
    model: "gpt-4o-mini"
  }
};

fetch('http://localhost:8001/v1/chat/multi-agent', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(testGoal)
})
  .then(r => r.json())
  .then(d => {
    console.log('✅ Multi-agent response:', d);
    console.log('Goal Analysis:', d.goal_analysis);
    console.log('Data Analysis:', d.data_analysis);
    console.log('Model Results:', d.model_results);
    console.log('Recommendations:', d.recommendations);
  })
  .catch(e => console.error('❌ Multi-agent failed:', e));
```

**Expected:**

- Goal analyzed into SMART objectives
- Data requirements identified
- Model recommendations provided
- Strategic action plan generated

**If 503 error:** LangGraph not available, check dependencies installed

---

### STEP 7: Test UI Chat Flow (30 minutes)

**Actions:**

1. Navigate to chat page in UI
2. Type a complex goal:

   ```
   I want to reduce my restaurant inventory costs by 15% while maintaining 95% service level
   ```

3. Click send
4. Observe:
   - Loading state appears
   - Multi-agent endpoint called (check Network tab)
   - Response parsed and displayed
   - Markers like [SHOW_CONNECTORS:] rendered as components

**Expected Flow:**

```
User Input → Frontend → /v1/chat/multi-agent → 4 Agents Execute
→ Structured Response → UI Parses Markers → Shows Components
```

---

## 🟡 KNOWN ISSUES & WORKAROUNDS

### Issue 1: MongoDB Connection Fails

**Symptom:** Backend starts but crashes on first DB operation  
**Workaround:**

```bash
# Option 1: Start local MongoDB
docker run -d -p 27017:27017 mongo:7

# Option 2: Use in-memory fallback
# In .env:
USE_MONGODB=false  # Falls back to dict storage
```

### Issue 2: OpenAI API Key Missing

**Symptom:** Multi-agent returns "LLM not configured"  
**Workaround:**

```bash
# In .env, use free Ollama:
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1

# Then start Ollama:
ollama serve
ollama pull llama3.1
```

### Issue 3: Port 8001 Already in Use

**Symptom:** Backend won't start  
**Workaround:**

```bash
# Find and kill process
lsof -ti:8001 | xargs kill -9

# Or use different port
uvicorn services.kernel.main:app --port 8002

# Update UI .env:
VITE_DYOCENSE_BASE_URL=http://localhost:8002
```

### Issue 4: UI Shows Blank Page

**Symptom:** White screen, no errors  
**Workaround:**

```bash
# Clear cache and rebuild
cd apps/ui
rm -rf node_modules/.vite
npm run dev
```

### Issue 5: Dependencies Still Hang

**Symptom:** Pip install takes >10 minutes  
**Nuclear Option:**

```bash
# Delete venv and start fresh
rm -rf .venv
python3.11 -m venv .venv
source .venv/bin/activate

# Install in two passes (avoid backtracking)
pip install --upgrade pip
pip install fastapi uvicorn pydantic httpx pytest

# Then install rest
pip install -r requirements-dev.txt
```

---

## 📊 SUCCESS CRITERIA

After completing all steps, you should have:

- [ ] Backend running on <http://localhost:8001>
- [ ] Frontend running on <http://localhost:5173>
- [ ] `/healthz` endpoint returns `{"status": "ok"}`
- [ ] No CORS errors in browser console
- [ ] Multi-agent endpoint returns structured response
- [ ] UI chat interface sends requests to backend
- [ ] Responses displayed in UI (even if formatting needs work)

---

## 🎯 NEXT STEPS (After Day 1)

Once basic connection is working:

1. **Day 2:** Add sample data integration
   - Create `/v1/samples` endpoint
   - Add "Try Sample Data" button in UI
   - Pre-fill with restaurant inventory scenario

2. **Day 3:** Build onboarding wizard
   - Industry selection
   - Template library
   - First optimization with sample data

3. **Day 4:** Simplify dashboard
   - Business-friendly summaries
   - Hide technical details
   - Add visualizations

4. **Day 5:** Polish and test
   - Error handling
   - Loading states
   - End-to-end testing with real users

---

## 🆘 ESCALATION

**If stuck >1 hour:**

1. Check this checklist for known issues
2. Look at terminal logs for specific errors
3. Test each component in isolation:
   - Backend: `curl http://localhost:8001/healthz`
   - Frontend: Check browser console
   - MongoDB: `mongosh mongodb://localhost:27017`
4. Take a screenshot of error and document

**Common Error Patterns:**

- `ModuleNotFoundError`: Dependency not installed → `pip install <package>`
- `Connection refused`: Service not running → Check process
- `CORS error`: Origins not configured → Update .env
- `401 Unauthorized`: Auth required → Set `ALLOW_ANONYMOUS=true`
- `500 Internal Server Error`: Backend crash → Check backend logs

---

## ✅ COMPLETION CHECKLIST

When you finish Day 1, verify:

```bash
# Backend health
curl http://localhost:8001/healthz
# ✅ {"status":"ok"}

# Multi-agent endpoint
curl -X POST http://localhost:8001/v1/chat/multi-agent \
  -H "Content-Type: application/json" \
  -d '{"goal":"test","context":{},"llm_config":{"provider":"openai"}}'
# ✅ Returns JSON with goal_analysis, data_analysis, etc.

# Frontend loads
curl http://localhost:5173
# ✅ Returns HTML

# No console errors
# Open http://localhost:5173 in browser
# F12 → Console
# ✅ No red errors related to API calls
```

**Document any issues encountered and solutions found for future reference.**

---

**END OF DAY 1 PLAN**

*Total estimated time: 4-6 hours (including troubleshooting)*  
*Priority: Get it working, not perfect. Optimization comes later.*
