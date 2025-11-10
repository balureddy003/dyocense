# Conversational AI Coach Setup Guide

This guide covers setting up the enhanced conversational AI Coach with LangGraph and Server-Sent Events (SSE) streaming.

## Overview

The conversational AI Coach provides:

- **Intent-based routing**: Understands user intent (greetings, goals, tasks, analysis, advice)
- **Context enrichment**: Pulls relevant business data (health scores, goals, tasks)
- **Action planning**: Generates specific, actionable recommendations
- **Streaming responses**: Word-by-word delivery like GitHub Copilot
- **Conversational personality**: Warm, encouraging, uses emojis
- **State management**: Remembers conversation context per tenant

## Architecture

```
Frontend (React + Fetch API + SSE)
  ↓
Backend API (/v1/tenants/{id}/coach/chat/stream)
  ↓
ConversationalCoachAgent (LangGraph workflow)
  ↓ analyze_intent → gather_context → suggest_actions → generate_response
  ↓
LLM Integration (packages/llm)
  ↓
OpenAI / Azure OpenAI / Ollama
```

## Installation

### 1. Install LangGraph Dependencies

```bash
cd /Users/balu/Projects/dyocense
pip install langgraph langchain-openai
```

### 2. Configure LLM Provider

Choose one of the following:

#### Option A: OpenAI (Recommended for Production)

```bash
export LLM_PROVIDER=openai
export OPENAI_API_KEY=sk-your-api-key-here
export OPENAI_MODEL=gpt-4  # or gpt-3.5-turbo for faster/cheaper
```

#### Option B: Azure OpenAI

```bash
export LLM_PROVIDER=azure
export AZURE_OPENAI_API_KEY=your-azure-key
export AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
export AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
export AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

#### Option C: Ollama (Development/Testing)

```bash
# Install Ollama
brew install ollama  # macOS
# or download from https://ollama.ai

# Start Ollama service
ollama serve

# Pull a model
ollama pull llama2

# Configure
export LLM_PROVIDER=ollama
export OLLAMA_BASE_URL=http://localhost:11434
export OLLAMA_MODEL=llama2
```

### 3. Start Backend Service

```bash
cd services/smb_gateway
uvicorn main:app --reload --port 8000
```

### 4. Start Frontend

```bash
cd apps/smb
npm run dev
```

## Testing

### Test Streaming Endpoint (cURL)

```bash
# Replace with your tenant ID and token
TENANT_ID="your-tenant-id"
API_TOKEN="your-api-token"

curl -N -X POST "http://localhost:8000/v1/tenants/${TENANT_ID}/coach/chat/stream" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${API_TOKEN}" \
  -d '{
    "message": "How is my business doing today?",
    "conversation_history": []
  }'
```

Expected output (streaming):

```
data: {"delta":"Hi ","done":false,"metadata":{"intent":"greeting","conversation_stage":"greeting"}}

data: {"delta":"there! ","done":false,"metadata":{"intent":"greeting","conversation_stage":"greeting"}}

data: {"delta":"👋 ","done":false,"metadata":{"intent":"greeting","conversation_stage":"greeting"}}

...

data: {"delta":"perform. ","done":true,"metadata":{"intent":"greeting","conversation_stage":"understanding"}}
```

### Test in Browser

1. Navigate to home page at `http://localhost:3000`
2. Find the "AI Coach" section
3. Type a message like:
   - "Hello!" (greeting)
   - "What are my current goals?" (goal discussion)
   - "How can I improve revenue?" (seeking advice)
   - "Show me my tasks" (task management)
4. Watch the response stream in word-by-word

### Verify Intent Detection

Check backend logs for intent classification:

```bash
# Watch logs
tail -f logs/smb_gateway.log

# Look for:
# [INFO] Detected intent: greeting
# [INFO] Conversation stage: understanding
# [INFO] Generated action plan: ['Review pricing strategy', 'Optimize inventory']
```

## Features

### Intent Types

The coach understands these intents:

| Intent | Examples | Response Style |
|--------|----------|----------------|
| `greeting` | "Hi", "Hello", "Hey there" | Warm welcome, ask how to help |
| `goal_discussion` | "What are my goals?", "Show my targets" | List goals, discuss progress |
| `task_management` | "My tasks", "What should I do?" | Prioritize tasks, suggest actions |
| `performance_analysis` | "How am I doing?", "Revenue trends" | Analyze health score, trends |
| `seeking_advice` | "How to improve?", "Need help with..." | Actionable advice, encouragement |
| `general_inquiry` | Everything else | Helpful general response |

### Context Enrichment

For each conversation, the coach automatically pulls:

- **Business name** (from tenant settings)
- **Health score** (overall + breakdown: revenue, operations, customer)
- **Active goals** (current targets and progress)
- **Pending tasks** (top 10 TODO items)

### Conversational Personality

System prompt guides the coach to be:

- **Warm and encouraging**: "Great job!", "You're making progress!"
- **Personal**: Uses business name, remembers context
- **Concise**: 2-4 sentences per response
- **Emoji-friendly**: Strategic use of 💡 🎯 ✨ 📈 👍
- **Action-oriented**: Always suggests next steps
- **Conversational**: Asks follow-up questions

### Streaming Experience

- **Word-by-word delivery** (50ms delay between words)
- **Progressive UI updates** (message builds in real-time)
- **Typing indicator** while thinking
- **Error handling** with graceful fallback

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `openai` | LLM provider: `openai`, `azure`, `ollama` |
| `OPENAI_API_KEY` | (required) | OpenAI API key |
| `OPENAI_MODEL` | `gpt-4` | Model name |
| `STREAM_WORD_DELAY_MS` | `50` | Delay between words (ms) |
| `MAX_CONVERSATION_HISTORY` | `10` | Messages to keep in memory |

### Customization

Edit `/services/smb_gateway/conversational_coach.py`:

**Change personality:**

```python
def _build_conversational_prompt(self, ...):
    system_prompt = f"""
    You are a friendly and supportive business coach for {business_name}.
    
    Personality:
    - [Customize here: warm/formal, concise/verbose, etc.]
    """
```

**Adjust streaming speed:**

```python
async for chunk in coach.stream_response(...):
    # Change delay from 50ms to your preference
    await asyncio.sleep(0.05)  # 0.05 = 50ms
```

**Add custom intents:**

```python
def _analyze_intent(self, state: AgentState) -> AgentState:
    # Add new intent detection
    if 'inventory' in user_message.lower():
        state['current_intent'] = 'inventory_management'
```

## Troubleshooting

### Issue: LangGraph Not Available

**Symptom:** Backend logs show "LangGraph not available, using simple state machine"

**Solution:**

```bash
pip install langgraph langchain-openai
# Restart backend
```

### Issue: No Streaming (All-at-Once Response)

**Symptom:** Response appears instantly instead of word-by-word

**Possible causes:**

1. **Proxy buffering**: nginx/load balancer buffering SSE
   - Check `X-Accel-Buffering: no` header is set
   - Disable buffering in proxy config

2. **CORS issues**: Browser blocking SSE
   - Check browser console for CORS errors
   - Ensure backend CORS middleware allows streaming

3. **Fallback mode**: LangGraph not installed
   - Install LangGraph as above

### Issue: Generic Responses

**Symptom:** Coach gives template responses like "Let me help you with that"

**Possible causes:**

1. **LLM not configured**: Using fallback responses
   - Check environment variables
   - Verify LLM_PROVIDER is set correctly
   - Test LLM connection separately

2. **Context not enriched**: Business data not available
   - Check backend logs for context gathering
   - Verify tenant has health score, goals, tasks
   - Ensure connector data is available

3. **Prompt too generic**: Not enough specificity
   - Review `_build_conversational_prompt()` method
   - Add more business context to prompt
   - Enhance intent detection logic

### Issue: Slow Responses

**Symptom:** Long delay before streaming starts

**Solutions:**

1. **Use faster model**: Switch from gpt-4 to gpt-3.5-turbo

   ```bash
   export OPENAI_MODEL=gpt-3.5-turbo
   ```

2. **Reduce context**: Limit goals/tasks in prompt

   ```python
   goals = goals_service.get_goals(tenant_id, status=GoalStatus.ACTIVE)[:3]  # Top 3 only
   ```

3. **Cache business context**: Store context in session
   - Implement Redis caching for health score
   - Cache goals/tasks with TTL

### Issue: CORS Errors

**Symptom:** Browser console shows CORS policy errors

**Solution:** Add CORS middleware to main.py:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)
```

## Monitoring

### Check Conversation State

```python
# In conversational_coach.py, add logging
coach = get_conversational_coach()
state = coach.conversations.get(tenant_id)
logger.info(f"Conversation state: {state}")
```

### Monitor Streaming

```bash
# Watch network tab in browser DevTools
# Look for:
# - Request to /coach/chat/stream
# - Type: eventsource or fetch
# - Response: chunked transfer encoding
# - Content-Type: text/event-stream
```

### Log LLM Calls

```python
# In packages/llm/__init__.py
logger.info(f"LLM call: provider={provider}, prompt_length={len(prompt)}")
logger.info(f"LLM response: length={len(response)}, tokens={...}")
```

## Performance Optimization

### Caching

```python
# Add Redis cache for business context
from redis import Redis

cache = Redis(host='localhost', port=6379, db=0)

# Cache health score
cache_key = f"health_score:{tenant_id}"
cached = cache.get(cache_key)
if cached:
    health_score = json.loads(cached)
else:
    health_score = calculator.calculate_overall_health()
    cache.setex(cache_key, 300, json.dumps(health_score.dict()))  # 5 min TTL
```

### Rate Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/v1/tenants/{tenant_id}/coach/chat/stream")
@limiter.limit("10/minute")  # 10 requests per minute per IP
async def coach_chat_stream(...):
    ...
```

### Token Optimization

```python
# Limit conversation history
MAX_HISTORY_MESSAGES = 6  # Last 3 exchanges (user + assistant)

# Truncate long messages
MAX_MESSAGE_LENGTH = 1000

# Use cheaper model for simple intents
if intent == "greeting":
    model = "gpt-3.5-turbo"  # Fast & cheap
else:
    model = "gpt-4"  # Smart for complex queries
```

## Future Enhancements

### Planned Features

- [ ] **Conversation persistence**: Save to database instead of in-memory
- [ ] **Multi-turn context**: Remember full conversation history
- [ ] **Proactive suggestions**: Coach initiates conversations based on events
- [ ] **Rich media**: Return charts, tables, action buttons
- [ ] **Voice input/output**: Speech-to-text and text-to-speech
- [ ] **Multi-language**: Detect language, respond accordingly
- [ ] **Personalization**: Learn user preferences over time
- [ ] **Integration with tasks**: Create tasks directly from chat
- [ ] **Analytics dashboard**: Track coach usage, satisfaction
- [ ] **A/B testing**: Test different personalities, prompts

### Advanced LangGraph Features

```python
# Add memory persistence
from langgraph.checkpoint.sqlite import SqliteSaver

checkpointer = SqliteSaver.from_conn_string("coach_memory.db")
graph = workflow.compile(checkpointer=checkpointer)

# Use with thread_id for conversation continuity
result = await graph.ainvoke(
    state,
    config={"configurable": {"thread_id": tenant_id}}
)
```

## Cost Considerations

### OpenAI Pricing (as of 2024)

| Model | Input (per 1K tokens) | Output (per 1K tokens) |
|-------|----------------------|------------------------|
| gpt-4 | $0.03 | $0.06 |
| gpt-3.5-turbo | $0.0005 | $0.0015 |

### Example Costs

**Typical conversation:**

- Prompt: ~500 tokens (context + history)
- Response: ~200 tokens
- Cost per message (gpt-4): ~$0.027
- Cost per message (gpt-3.5-turbo): ~$0.0006

**Monthly estimate (100 users, 10 messages/day):**

- gpt-4: ~$810/month
- gpt-3.5-turbo: ~$18/month

**Recommendation:** Start with gpt-3.5-turbo, upgrade to gpt-4 for complex queries only.

## Support

For issues or questions:

1. Check logs: `services/smb_gateway/logs/`
2. Review backend errors: `uvicorn` console output
3. Test LLM separately: `python -c "from packages.llm import _invoke_llm; print(_invoke_llm('Hello'))"`
4. Verify environment variables: `env | grep LLM`
5. Check frontend console: Browser DevTools → Console

## References

- [LangGraph Documentation](https://python.langchain.com/docs/langgraph)
- [Server-Sent Events MDN](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [AI Coach LLM Setup](./AI_COACH_LLM_SETUP.md)
