# VS Code Debugging Guide

## ✅ Setup Complete

Your VS Code is now configured with 6 debug configurations and optimal Python settings.

---

## 🎯 Quick Start

### 1. **Run the Kernel with Debugger**

1. Press `F5` or click "Run and Debug" in the sidebar
2. Select: **🚀 Kernel (Unified - Recommended)**
3. Set breakpoints by clicking left of line numbers
4. Service will start at `http://localhost:8001`

**Features enabled:**

- ✅ Auto-reload on code changes
- ✅ Anonymous auth (no tokens needed)
- ✅ Plan tracing enabled
- ✅ Debug logs visible
- ✅ Step through any code (including libraries)

---

## 🐛 Debug Configurations

### 1. 🚀 Kernel (Unified - Recommended)

**When to use:** Debug the main service

**What it does:**

- Starts unified kernel on port 8001
- Enables auto-reload
- Sets `ALLOW_ANONYMOUS=true` for easy testing
- Enables plan tracing

**How to test:**

```bash
# While debugging, open another terminal:
curl http://localhost:8001/healthz
curl http://localhost:8001/docs
```

---

### 2. 🧪 Run Current Test File

**When to use:** Debug the test file you're currently viewing

**How to use:**

1. Open any test file (e.g., `tests/test_plan_mode.py`)
2. Press `F5`
3. Select: **🧪 Run Current Test File**
4. Debugger will stop at breakpoints in test or code

**Example:**

```python
# tests/test_plan_mode.py
def test_planner_create_and_execute_basic_plan():
    resp = client.post(...)  # Set breakpoint here
    assert resp.status_code == 200
```

---

### 3. 🧪 Run All Tests

**When to use:** Debug entire test suite

**What it does:**

- Runs all tests in `tests/` directory
- Shows verbose output
- Stops at any breakpoint in any test

**Useful for:** Finding which test is failing and why

---

### 4. 🧪 Run Plan Mode Tests

**When to use:** Debug planner-specific tests

**What it does:**

- Runs only `tests/test_plan_mode.py`
- Shows output with `-s` flag (print statements visible)
- Perfect for debugging the new planner features

**Try this:**

1. Open `packages/agent/executor.py`
2. Set breakpoint in `execute()` method
3. Run this configuration
4. Watch execution flow through steps

---

### 5. 🔍 Debug Current Python File

**When to use:** Debug any standalone Python script

**How to use:**

1. Open any `.py` file
2. Press `F5`
3. Select: **🔍 Debug Current Python File**

**Good for:**

- Debugging utility scripts
- Testing individual modules
- Running examples

---

### 6. 📊 Evaluation Script

**When to use:** Debug plan evaluation

**What it does:**

- Runs `scripts/evaluate_plan_quality.py`
- Creates and executes a test plan
- Shows metrics and artifacts

**Perfect for:** Testing end-to-end plan execution

---

## 🎮 Debugger Controls

| Key | Action |
|-----|--------|
| `F5` | Continue / Start debugging |
| `F9` | Toggle breakpoint |
| `F10` | Step over (next line) |
| `F11` | Step into (enter function) |
| `Shift+F11` | Step out (exit function) |
| `Ctrl+Shift+F5` | Restart debugger |
| `Shift+F5` | Stop debugging |

---

## 🔍 Useful Debug Views

### Variables Panel

- Shows all local/global variables
- Expand objects to inspect
- Right-click → "Copy Value"

### Watch Panel

- Add expressions to monitor
- Example: `plan.status`, `step.metrics`

### Call Stack

- See the execution path
- Click frames to inspect state at each level

### Debug Console

- Run Python code in current context
- Example: `print(plan.model_dump_json(indent=2))`

---

## 💡 Pro Tips

### 1. **Conditional Breakpoints**

Right-click breakpoint → "Edit Breakpoint" → Add condition

```python
# Only break when this is true:
plan_id == "plan-abc123"
step.status == "failed"
```

### 2. **Log Points**

Right-click → "Add Logpoint" → Enter message

```
Plan {plan.id} status: {plan.status}
```

No code changes needed!

### 3. **Debug Specific Endpoint**

Set breakpoint in service, then test:

```bash
# In another terminal while debugging
curl -X POST http://localhost:8001/v1/plan \
  -H "Content-Type: application/json" \
  -d '{"goal": "test", "template_id": "inventory_basic"}'
```

### 4. **Inspect Plan Execution**

Set breakpoints in `packages/agent/executor.py`:

- Line ~85: Start of execute loop
- Line ~95: Before each step type
- Line ~165: Step success/failure

Watch variables:

- `step.inputs` - What's being passed in
- `context_outputs` - In-memory artifacts
- `plan.risks` - Accumulated issues

### 5. **Debug Tests with Coverage**

Modify test config to see coverage:

```json
"args": ["tests/", "-v", "--cov=packages", "--cov=services"]
```

---

## 🐞 Common Debug Scenarios

### Scenario 1: Plan Step Failing

1. Set breakpoint in `packages/agent/executor.py` line ~165
2. Run: **🧪 Run Plan Mode Tests**
3. Inspect `step.metrics["error"]` to see what went wrong
4. Step back through call stack to find root cause

### Scenario 2: Reference Resolution Issues

1. Set breakpoint in `executor.py` at `resolve_inputs()` function
2. Run test that creates plan
3. Watch `context_outputs` dictionary populate
4. See how refs like `{"ref": "optimise_1"}` are resolved

### Scenario 3: Service Endpoint Not Working

1. Set breakpoint in service endpoint (e.g., `services/plan/main.py`)
2. Run: **🚀 Kernel (Unified - Recommended)**
3. Make request from terminal/Postman
4. Step through request handling

### Scenario 4: Test Assertion Failing

1. Open failing test file
2. Set breakpoint before assertion
3. Run: **🧪 Run Current Test File**
4. Inspect variables in Debug Console:

   ```python
   resp.json()
   resp.status_code
   plan_body
   ```

---

## 📁 Key Files to Set Breakpoints In

### Service Layer

- `services/kernel/main.py` - Main app router
- `services/plan/main.py` - Planner endpoints
- `services/orchestrator/main.py` - Run orchestration

### Business Logic

- `packages/agent/executor.py` - Plan execution (most important!)
- `packages/agent/schemas.py` - Data models
- `packages/agent/tracing.py` - Trace events

### Services

- `services/forecast/main.py` - Forecasting
- `services/optimiser/main.py` - Optimization
- `services/diagnostician/main.py` - Diagnostics

---

## 🧪 Testing Integration

VS Code settings also enable **Test Explorer**:

1. Click Testing icon in sidebar (beaker icon)
2. See all tests in tree view
3. Click play icon to run individual tests
4. Click debug icon to debug specific test

**Features:**

- ✅ Visual test results
- ✅ Run/debug individual tests
- ✅ See test output inline
- ✅ Auto-discover new tests

---

## 🔧 Settings Configured

The following VS Code settings are now active:

### Python

- ✅ Pytest as test framework
- ✅ Auto-activate virtual environment
- ✅ PYTHONPATH set automatically
- ✅ Type checking enabled (basic mode)
- ✅ Uses `.venv/bin/python` by default

### Editor

- ✅ Format on save
- ✅ Auto-organize imports
- ✅ Auto-save after 1 second
- ✅ Hide `__pycache__`, `.pyc` files

### Terminal

- ✅ PYTHONPATH set in integrated terminal
- ✅ Environment auto-activated

---

## 🚀 Quick Test

Try this right now:

1. Press `F5`
2. Select: **🚀 Kernel (Unified - Recommended)**
3. Wait for service to start (watch terminal)
4. Open browser: `http://localhost:8001/docs`
5. See the unified API documentation!

Then try:

1. Open `tests/test_plan_mode.py`
2. Set breakpoint on line 30 (in test function)
3. Press `F5`
4. Select: **🧪 Run Plan Mode Tests**
5. Debugger stops at your breakpoint!
6. Press `F10` to step through code

---

## 📚 Next Steps

1. **Explore the API**: Run kernel and visit `/docs`
2. **Set breakpoints**: Try debugging a test
3. **Inspect artifacts**: Check `artifacts/plans/` after running tests
4. **Read traces**: View `trace.jsonl` files to understand execution

---

## 🆘 Troubleshooting

### Debugger won't start

- Check Python extension is installed
- Verify `.venv/bin/python` exists
- Run: `pip install -r requirements-dev.txt`

### Can't hit breakpoints

- Ensure `"justMyCode": false` in config
- Check file is actually being executed
- Try "Restart Debugger" (`Ctrl+Shift+F5`)

### Tests not discovered

- Check Test Explorer icon in sidebar
- Click "Refresh Tests" button
- Verify PYTHONPATH is set correctly

### Import errors while debugging

- Ensure PYTHONPATH includes workspace folder
- Check terminal environment: `echo $PYTHONPATH`
- Restart VS Code if needed

---

**You're all set! Happy debugging! 🎉**

For more help, see:

- `RUNNING_SERVICES.md` - How to run services
- `tests/test_plan_mode.py` - Example tests
- `packages/agent/executor.py` - Plan execution logic
