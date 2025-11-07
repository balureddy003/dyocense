# UI → Backend Connection Fix

## 🐛 Problem Identified

The UI was making requests to **port 63330** instead of **8001** because:

1. **Random Port Assignment**: When running uvicorn through the debugger without explicit `--host`, it can bind to a random port
2. **Missing Proxy**: The Vite dev server wasn't proxying API requests to the backend
3. **Absolute URLs**: The UI was using absolute URLs (`http://127.0.0.1:8001`) which didn't match the actual running port

## ✅ Solution Applied

### 1. Fixed Debug Configuration (`.vscode/launch.json`)

Added `--host 127.0.0.1` to ensure the service binds to the correct interface:

```json
"args": [
  "services.kernel.main:app",
  "--reload",
  "--host",
  "127.0.0.1",  // ← Added this
  "--port",
  "8001",
  "--log-level",
  "debug"
]
```

### 2. Added Vite Proxy (`apps/ui/vite.config.ts`)

Now all API requests are proxied to the backend:

```typescript
server: {
  port: 5173,
  proxy: {
    "/v1": {
      target: "http://127.0.0.1:8001",
      changeOrigin: true,
    },
    "/api": {
      target: "http://127.0.0.1:8001",
      changeOrigin: true,
    },
  },
}
```

### 3. Updated API Config (`apps/ui/src/lib/config.ts`)

Uses relative URLs in development (leverages proxy):

```typescript
export const API_BASE_URL = import.meta.env.DEV 
  ? "" // Use Vite proxy in development
  : "http://127.0.0.1:8001"; // Direct connection in production
```

## 🚀 How to Run Correctly

### Terminal 1: Start Backend (Debug Mode)

1. Press `F5` in VS Code
2. Select: **🚀 Kernel (Unified - Recommended)**
3. Wait for: `Application startup complete.`
4. Verify: Backend running at `http://127.0.0.1:8001`

### Terminal 2: Start Frontend

```bash
cd apps/ui
npm run dev
```

Frontend will run at `http://localhost:5177` (or 5173)

## 🧪 Testing the Connection

### Option 1: Check Backend Directly

```bash
# Should return {"status": "ok"}
curl http://127.0.0.1:8001/healthz

# Should return API docs (JSON)
curl http://127.0.0.1:8001/docs
```

### Option 2: Check Through Vite Proxy

```bash
# Should proxy to backend and return {"status": "ok"}
curl http://localhost:5177/healthz

# Test registration endpoint
curl -X POST http://localhost:5177/v1/users/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'
```

### Option 3: Check in Browser

1. Open: `http://localhost:5177`
2. Open DevTools → Network tab
3. Try to register/login
4. Check requests are going to `localhost:5177/v1/users/register`
5. Verify status is **200 OK** (not 404)

## 🔍 Understanding the Flow

### Development Mode (with Proxy)

```
Browser (localhost:5177)
    ↓ Request: /v1/users/register
Vite Dev Server (localhost:5177)
    ↓ Proxy to: http://127.0.0.1:8001/v1/users/register
Kernel Service (127.0.0.1:8001)
    ↓ Response
Browser
```

**Benefits:**
- ✅ No CORS issues
- ✅ Same-origin requests
- ✅ Hot reload works
- ✅ Easy debugging

### Production Mode (direct connection)

```
Browser (example.com)
    ↓ Request: http://api.example.com/v1/users/register
Kernel Service (api.example.com)
    ↓ Response
Browser
```

## 🐛 Troubleshooting

### Still seeing 404 errors?

1. **Check backend is running on correct port:**
   ```bash
   lsof -i :8001
   # Should show Python/uvicorn process
   ```

2. **Restart both services:**
   - Stop debugger (`Shift+F5`)
   - Stop Vite dev server (`Ctrl+C`)
   - Start backend first (F5)
   - Then start frontend (`npm run dev`)

3. **Clear browser cache:**
   - Hard refresh: `Cmd+Shift+R` (Mac) or `Ctrl+Shift+R` (Windows/Linux)

### Seeing CORS errors?

This means the proxy isn't working. Check:

```bash
# In apps/ui directory
npm run dev

# Should show:
# ➜  Local:   http://localhost:5173/
# ➜  Proxy:   /v1 -> http://127.0.0.1:8001
```

If proxy isn't shown, Vite config wasn't applied. Restart Vite.

### Backend on different port?

If you need to run backend on a different port:

1. Update debug config:
   ```json
   "args": ["...", "--port", "8002"]
   ```

2. Update Vite proxy:
   ```typescript
   target: "http://127.0.0.1:8002"
   ```

### Using environment variables

Create `apps/ui/.env.local`:

```bash
# For production builds
VITE_DYOCENSE_BASE_URL=http://your-api-server.com

# For development (optional, proxy is preferred)
# VITE_DYOCENSE_BASE_URL=http://127.0.0.1:8001
```

## 📚 Related Files

- `.vscode/launch.json` - Debug configurations
- `apps/ui/vite.config.ts` - Vite proxy setup
- `apps/ui/src/lib/config.ts` - API base URL configuration
- `apps/ui/src/lib/api.ts` - API client functions

## ✨ Summary

**Before:**
- ❌ UI calling random port (63330)
- ❌ 404 errors on all API calls
- ❌ CORS issues possible

**After:**
- ✅ Backend always on port 8001
- ✅ Vite proxy handles routing
- ✅ Relative URLs in development
- ✅ No CORS issues
- ✅ Easy debugging with breakpoints

---

**Now both services should communicate correctly!** 🎉
