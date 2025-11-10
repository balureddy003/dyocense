# AI Coach LLM Integration Setup

The AI Coach now uses **real LLM integration** instead of template-based responses. This guide explains how to configure it.

## LLM Provider Options

The coach service supports three LLM providers:

### 1. **OpenAI** (Recommended for Production)

Set these environment variables:

```bash
export LLM_PROVIDER=openai
export OPENAI_API_KEY=sk-your-api-key-here
export OPENAI_MODEL=gpt-4o-mini  # or gpt-4, gpt-3.5-turbo
```

### 2. **Azure OpenAI**

Set these environment variables:

```bash
export LLM_PROVIDER=azure
export AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
export AZURE_OPENAI_API_KEY=your-azure-key
export AZURE_OPENAI_DEPLOYMENT=your-deployment-name
export AZURE_OPENAI_TEMPERATURE=0.7  # Optional, default 0.0
export AZURE_OPENAI_MAX_TOKENS=2048  # Optional, default 2048
```

### 3. **Ollama** (Free, Local LLM)

Run Ollama locally and set:

```bash
export LLM_PROVIDER=ollama
export OLLAMA_BASE_URL=http://localhost:11434  # Optional, default
export OLLAMA_MODEL=llama3.1  # or mistral, codellama, etc.
export OLLAMA_TIMEOUT=120  # Optional, default 120 seconds
```

**Install Ollama:**

```bash
# macOS
brew install ollama

# Or download from https://ollama.ai
ollama pull llama3.1
ollama serve
```

## Quick Start for Development

For quick testing with **Ollama** (no API keys needed):

```bash
# 1. Install and start Ollama
ollama pull llama3.1
ollama serve

# 2. Set environment variable
export LLM_PROVIDER=ollama

# 3. Start the SMB Gateway
cd /Users/balu/Projects/dyocense
uvicorn services.smb_gateway.main:app --reload --port 8001
```

## Features of LLM-Powered AI Coach

### Context-Aware Responses

The AI Coach has access to:

- **Business Health Score** (overall + breakdown by revenue/operations/customer)
- **Active Goals** (title, category, progress, current/target values)
- **Pending Tasks** (title, category, priority)
- **Business Name** (from tenant settings)
- **Conversation History** (last 10 messages for context)

### Smart Prompting

The system prompt includes:

- Current business performance metrics
- Goal progress and targets
- Task priorities
- Guidelines for actionable, data-driven advice

### Fallback Mechanism

If the LLM is unavailable, the coach falls back to intelligent template-based responses using the business context.

## Testing the Integration

1. **Start the backend:**

   ```bash
   cd /Users/balu/Projects/dyocense
   export LLM_PROVIDER=ollama  # or openai/azure
   uvicorn services.smb_gateway.main:app --reload --port 8001
   ```

2. **Start the frontend:**

   ```bash
   cd /Users/balu/Projects/dyocense/apps/smb
   npm run dev
   ```

3. **Test on the home page:**
   - Navigate to <http://localhost:5178/home>
   - Scroll to the AI Coach widget
   - Ask questions like:
     - "How can I improve my health score?"
     - "What should I focus on this week?"
     - "Help me with my goals"

4. **Test on the Coach page:**
   - Navigate to <http://localhost:5178/coach>
   - Have a full conversation with context

## Monitoring LLM Usage

Check the logs for LLM activity:

```bash
# Backend logs will show:
# - "Invoking LLM with prompt length: X characters"
# - "LLM response received: Y characters"
# - "LLM returned no response, using fallback" (if LLM unavailable)
# - "LLM invocation failed: error details" (on errors)
```

## Cost Considerations

- **Ollama**: Free, runs locally, but requires compute resources
- **OpenAI**: Pay per token (~$0.0001-0.002 per 1K tokens depending on model)
- **Azure OpenAI**: Similar pricing to OpenAI, but with enterprise features

For development: Use Ollama
For production: Use OpenAI (gpt-4o-mini) or Azure OpenAI

## Future Enhancements (LangGraph Agents)

To add agent-based reasoning with LangGraph:

1. Install LangGraph:

   ```bash
   pip install langgraph langchain-openai
   ```

2. Create agent workflow in `coach_service.py`:
   - Goal analysis agent
   - Task recommendation agent
   - Health score diagnostic agent
   - Multi-agent orchestration

3. Use state management for complex multi-turn conversations

This would enable the coach to:

- Break down complex problems into steps
- Use tools (calculators, data lookups)
- Maintain conversation state across sessions
- Provide structured action plans

## Troubleshooting

**"LLM returned no response"**

- Check if LLM provider is running (Ollama server, OpenAI API key valid)
- Check network connectivity
- Verify environment variables are set

**Slow responses**

- Reduce context (limit conversation history)
- Use faster model (gpt-3.5-turbo instead of gpt-4)
- Increase timeout for Ollama

**Generic responses**

- Check if business context is being passed correctly
- Verify goals, tasks, and health score data exists
- Review system prompt in coach_service.py
