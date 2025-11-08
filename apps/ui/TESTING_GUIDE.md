# Testing the Agent-Driven Flow

## Start the development server

```bash
cd apps/ui
npm run dev
```

The app will be available at <http://localhost:5173>

## Test Scenarios

### 1. Upload a CSV file

1. Create a test CSV file (or use existing restaurant_inventory.csv from examples):

   ```csv
   ingredient_name,unit_cost,current_stock_kg,min_stock_kg,max_stock_kg
   Tomatoes,2.5,50,20,100
   Cheese,8.0,30,15,75
   Flour,1.2,100,40,200
   Olive Oil,12.0,25,10,50
   ```

2. In the chat interface, click the "Upload" button (📤)
3. Select your CSV file
4. **Expected behavior**:
   - User message appears: "Uploaded file: [filename]"
   - Loading indicator shows
   - Agent responds with parsed info: "File uploaded with X rows, columns: [list]"
   - Action buttons appear: "Preview Data", "Analyze", "Remove"

### 2. Preview uploaded data

**Option A**: Click the "Preview Data" button

**Option B**: Type in chat: "preview [filename]"

**Expected behavior**:

- Preview message shows first 5 rows in formatted table
- Columns and data are properly aligned

### 3. Analyze data

1. Click "Analyze" button OR type "Analyze the data in [filename]"
2. **Expected behavior**:
   - Agent responds with analysis suggestions
   - May ask clarifying questions about what to analyze

### 4. Remove data source

**Option A**: Click "Remove" button

**Option B**: Type: "remove [filename]"

**Expected behavior**:

- Data source is removed from list
- Agent acknowledges and suggests next steps

### 5. Connect a data source

1. Click "Connectors" button in header
2. Select a connector (e.g., Square, Shopify)
3. Fill in configuration details
4. Complete setup
5. **Expected behavior**:
   - Agent responds with capabilities summary
   - No hardcoded "✓ Connected" message
   - Dynamic response based on connector type

### 6. Natural language commands

Try these in chat:

- "What can I do with this data?"
- "Show me a preview of the sales data"
- "Connect to my Shopify store"
- "I want to reduce inventory costs by 15%"

**Expected behavior**:

- Agent interprets intent
- Suggests relevant actions
- Opens appropriate UI (connector marketplace, preview, etc.)

## Verify Agent Mode is Active

Check the console for:

```
AGENT_DRIVEN_FLOW = true
```

If you see hardcoded responses like "Would you like to connect or preview?", the agent mode is off.

## Backend Requirements

Ensure these services are running:

```bash
# Terminal 1: Backend API
uvicorn services.kernel.main:app --host 127.0.0.1 --port 8001 --reload

# Terminal 2: Frontend dev server
cd apps/ui && npm run dev
```

## API Endpoints Used

- `POST /v1/chat/completions` - Main LLM endpoint
  - Receives: system prompt, chat history, context (tenant, data sources, connectors)
  - Returns: agent's natural language response

- `GET /v1/connectors` - List active connectors
- `POST /v1/connectors` - Create new connector
- `GET /v1/tenants/me` - Get tenant profile

## Troubleshooting

### "Agent couldn't be reached"

- Check backend is running on port 8001
- Verify `/v1/chat/completions` endpoint is accessible
- Check browser console for API errors

### Static responses instead of dynamic

- Verify `AGENT_DRIVEN_FLOW = true` in AgentAssistant.tsx
- Check that backend is returning valid OpenAI-compatible responses

### File upload doesn't parse data

- Check file format (CSV or JSON only)
- Verify file size < 50MB
- Look for parse errors in browser console

### Action buttons don't appear

- Verify file status is "ready" (not "uploading" or "error")
- Check that message has `actions` array in state
- Look for render errors in React DevTools

## Success Criteria

✅ File uploads trigger agent responses (not hardcoded text)
✅ Action buttons work (preview, analyze, remove)
✅ Natural language commands are understood
✅ Connector setup completion triggers agent acknowledgment
✅ Context is maintained across conversation
✅ No errors in browser console
✅ Build completes without TypeScript errors
