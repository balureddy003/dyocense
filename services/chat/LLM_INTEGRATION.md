# Chat Service - LLM Integration Guide

## Overview

The chat service now supports **real LLM integration** with multiple providers:

- **OpenAI** (GPT-4, GPT-3.5-turbo)
- **Azure OpenAI**
- **Ollama** (local models)

It also includes intelligent **fallback responses** when LLMs are unavailable.

## Features

### ✅ Real LLM Integration

- Connects to OpenAI, Azure OpenAI, or Ollama based on configuration
- Supports function calling for inline UI components
- Passes conversation context and history to LLM

### ✅ Function Calling Support

The service handles function calls from LLMs:

- `show_connector_options(connectors, reason)` - Suggests data connectors
- `show_data_uploader(format, expectedColumns)` - Triggers file upload

When function calling is detected, the backend converts it to text markers:

- `[SHOW_CONNECTORS: salesforce, xero, shopify]`
- `[SHOW_UPLOADER: csv]` or `[SHOW_UPLOADER: excel]`

The frontend parses these markers and displays inline components.

### ✅ Intelligent Fallbacks

When LLMs are unavailable, the service uses smart fallback responses with data connection prompts.

---

## Configuration

### Option 1: OpenAI

1. **Install dependencies:**

   ```bash
   pip install openai
   ```

2. **Set environment variables:**

   ```bash
   export LLM_PROVIDER=openai
   export OPENAI_API_KEY=sk-...your-key...
   export OPENAI_MODEL=gpt-4o-mini  # or gpt-4, gpt-3.5-turbo
   ```

3. **Restart the chat service:**

   ```bash
   cd services/chat
   uvicorn main:app --reload --port 8003
   ```

### Option 2: Azure OpenAI

1. **Install dependencies:**

   ```bash
   pip install openai
   ```

2. **Set environment variables:**

   ```bash
   export LLM_PROVIDER=azure
   export AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
   export AZURE_OPENAI_API_KEY=your-key
   export AZURE_OPENAI_DEPLOYMENT=your-deployment-name
   ```

3. **Restart the chat service**

### Option 3: Ollama (Local)

1. **Install Ollama:**

   ```bash
   # macOS/Linux
   curl -fsSL https://ollama.com/install.sh | sh
   
   # Or download from https://ollama.com
   ```

2. **Pull a model:**

   ```bash
   ollama pull llama3.1
   # or
   ollama pull mistral
   ollama pull phi3
   ```

3. **Set environment variables:**

   ```bash
   export LLM_PROVIDER=ollama
   export OLLAMA_BASE_URL=http://localhost:11434
   export OLLAMA_MODEL=llama3.1
   ```

4. **Start Ollama (if not running):**

   ```bash
   ollama serve
   ```

5. **Restart the chat service**

### Option 4: No LLM (Fallback Mode)

If you don't set `LLM_PROVIDER`, the service uses intelligent fallback responses:

```bash
# No configuration needed - fallback mode is default
```

---

## Testing

### 1. Check Health

```bash
curl http://localhost:8003/health
```

### 2. Test Chat Endpoint

```bash
curl -X POST http://localhost:8003/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "model": "dyocense-chat-mini",
    "messages": [
      {"role": "user", "content": "Help me forecast sales"}
    ],
    "context": {
      "tenant_id": "test-tenant"
    }
  }'
```

### 3. Expected Response (OpenAI with function calling)

```json
{
  "id": "chatcmpl_...",
  "object": "chat.completion",
  "created": 1699401234,
  "model": "gpt-4o-mini",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "To create accurate sales forecasts, I'll need historical sales data. Do you use a CRM like Salesforce or HubSpot?\n\n[SHOW_CONNECTORS: salesforce, hubspot, pipedrive]"
    },
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 45,
    "completion_tokens": 32,
    "total_tokens": 77
  }
}
```

### 4. Frontend Integration

The frontend automatically:

1. Parses `[SHOW_CONNECTORS: ...]` markers
2. Creates inline connector selection UI
3. Parses `[SHOW_UPLOADER: ...]` markers
4. Creates inline file upload UI

---

## Function Calling Support

### Tools Schema

The service sends this schema to OpenAI/Azure when function calling is available:

```json
{
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "show_connector_options",
        "description": "Display inline connector selection UI",
        "parameters": {
          "type": "object",
          "properties": {
            "connectors": {
              "type": "array",
              "items": {"type": "string"},
              "description": "List of connector IDs (e.g., ['salesforce', 'xero'])"
            },
            "reason": {
              "type": "string",
              "description": "Why these connectors would help"
            }
          },
          "required": ["connectors", "reason"]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "show_data_uploader",
        "description": "Display inline file upload UI",
        "parameters": {
          "type": "object",
          "properties": {
            "format": {
              "type": "string",
              "enum": ["csv", "excel", "json"]
            },
            "expectedColumns": {
              "type": "array",
              "items": {"type": "string"}
            }
          },
          "required": ["format"]
        }
      }
    }
  ]
}
```

### How It Works

1. Frontend sends tools schema in request
2. LLM decides whether to call functions
3. Backend detects function calls
4. Converts to text markers (`[SHOW_CONNECTORS: ...]`)
5. Frontend parses markers and renders inline UI

---

## Architecture

```
Frontend (React)
    ↓ HTTP POST
Chat Service (FastAPI)
    ↓
Provider Router (invoke_llm_chat)
    ↓
┌──────────┬──────────┬──────────┐
│ OpenAI   │  Azure   │  Ollama  │
└──────────┴──────────┴──────────┘
    ↓
Response with function calls or markers
    ↓
Frontend parses and renders inline components
```

---

## Environment Variables Reference

| Variable | Provider | Required | Default | Description |
|----------|----------|----------|---------|-------------|
| `LLM_PROVIDER` | All | No | `""` | `openai`, `azure`, `ollama`, or empty for fallback |
| `OPENAI_API_KEY` | OpenAI | Yes* | - | OpenAI API key |
| `OPENAI_MODEL` | OpenAI | No | `gpt-4o-mini` | Model to use |
| `AZURE_OPENAI_ENDPOINT` | Azure | Yes* | - | Azure OpenAI endpoint URL |
| `AZURE_OPENAI_API_KEY` | Azure | Yes* | - | Azure OpenAI API key |
| `AZURE_OPENAI_DEPLOYMENT` | Azure | Yes* | - | Deployment name |
| `OLLAMA_BASE_URL` | Ollama | No | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | Ollama | No | `llama3.1` | Ollama model name |

*Required when using that specific provider

---

## Troubleshooting

### LLM not responding

**Check logs:**

```bash
# Chat service logs
tail -f services/chat/logs/*.log
```

**Common issues:**

- API key not set or invalid
- Model doesn't exist or doesn't support function calling
- Ollama not running (`ollama serve`)
- Network/firewall issues

### Function calling not working

**Requirements:**

- OpenAI: Use `gpt-4o-mini`, `gpt-4-turbo`, or `gpt-3.5-turbo-1106+`
- Azure: Ensure deployment supports function calling
- Ollama: Function calling may not be supported (uses marker fallback)

**Test with fallback markers:**
Even without function calling, the service adds markers to responses:

- Fallback responses include `[SHOW_CONNECTORS: ...]` and `[SHOW_UPLOADER: ...]`
- Frontend parses these regardless of function calling support

### Markers not showing

**Check console:**

```javascript
// Browser console should show:
🤖 LLM Response: [full response text]
✅ Detected SHOW_CONNECTORS: salesforce, xero, shopify
```

**If not showing:**

- Check backend logs for LLM responses
- Verify regex patterns in frontend code
- Ensure response includes marker format exactly

---

## Development Tips

### Testing Locally with Ollama

```bash
# Quick setup
ollama pull llama3.1
export LLM_PROVIDER=ollama
cd services/chat
uvicorn main:app --reload --port 8003
```

### Testing with Mock Responses

```bash
# No LLM_PROVIDER = automatic fallback mode
cd services/chat
uvicorn main:app --reload --port 8003
```

### Adding New Functions

1. Update `AGENT_FUNCTION_TOOLS` in frontend (`AgentAssistant.tsx`)
2. Add handling in backend (`invoke_openai_chat`, `invoke_azure_chat`)
3. Add marker conversion for non-function-calling models
4. Add frontend parser for new marker
5. Create inline component for UI

---

## Next Steps

1. **Set up your preferred LLM provider** (see Configuration above)
2. **Restart services:**

   ```bash
   cd services/chat
   uvicorn main:app --reload --port 8003
   ```

3. **Test in browser:** Open the AI Assistant and try queries like:
   - "Help me forecast sales"
   - "I want to optimize inventory"
   - "Connect my accounting data"

4. **Monitor logs** to see LLM responses and function calls

---

## Production Recommendations

### Security

- Store API keys in secrets manager (AWS Secrets Manager, Azure Key Vault)
- Use environment-specific configurations
- Rotate keys regularly
- Monitor API usage and costs

### Performance

- Cache common responses
- Implement rate limiting
- Use streaming for long responses
- Monitor token usage

### Reliability

- Set up fallback chain: Primary LLM → Secondary LLM → Hardcoded responses
- Add retry logic with exponential backoff
- Monitor LLM availability
- Alert on high error rates

### Cost Optimization

- Use appropriate models (gpt-3.5-turbo for simple queries, gpt-4 for complex)
- Implement conversation length limits
- Cache system prompts
- Monitor per-tenant usage
