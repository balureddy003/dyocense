# Coach V4 - Phase 2: Model Settings Implementation

## Overview

Implemented power-user model settings feature to allow fine-tuned control over LLM behavior (temperature, max tokens, model selection) without cluttering the interface for regular users.

## Implementation Summary

### 1. Frontend Components

#### ModelSettingsPopover Component (`apps/smb/src/components/ModelSettingsPopover.tsx`)

- **Purpose**: Collapsible settings panel for model parameters
- **Features**:
  - Model selection dropdown (provider-specific: Ollama, OpenAI, Azure)
  - Temperature slider (0.0-2.0) with semantic markers:
    - 0.0 = Focused (deterministic)
    - 1.0 = Balanced (default)
    - 2.0 = Creative (high variation)
  - Max tokens input (128-8192)
  - Reset to defaults button
  - Clean icon-based trigger (IconAdjustments)
- **Props**:

  ```typescript
  interface ModelSettingsPopoverProps {
    settings: { temperature: number; maxTokens: number; model: string }
    onChange: (settings: typeof settings) => void
    provider: 'ollama' | 'openai' | 'azure'
  }
  ```

#### CoachV3 Integration (`apps/smb/src/pages/CoachV3.tsx`)

- **State Management**:

  ```typescript
  const [modelSettings, setModelSettings] = useState(() => {
    const saved = localStorage.getItem('coach_model_settings')
    return saved ? JSON.parse(saved) : { temperature: 0.7, maxTokens: 2048, model: 'llama3.1' }
  })
  ```

- **Persistence**: Settings saved to localStorage on change
- **UI Integration**: Popover added to header button group (left of Context/Goals/Tasks buttons)
- **API Integration**: Settings passed in `basePayload` to both streaming and non-streaming endpoints

### 2. Backend API

#### ChatRequest Model Extension (`services/smb_gateway/coach_service.py`)

```python
class ChatRequest(BaseModel):
    message: str
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list)
    persona: Optional[str] = "coach"
    goal_context: Optional[Dict[str, Any]] = None
    goal_id: Optional[str] = None
    intent: Optional[str] = None
    include_evidence: bool = False
    
    # Phase 2: Power-user model settings
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=1, le=8192)
    model: Optional[str] = None
```

#### LLM Invocation (`services/smb_gateway/coach_service.py`)

- Updated `_invoke_llm` method signature to accept optional parameters:

  ```python
  async def _invoke_llm(
      self, 
      messages: List[Dict[str, str]], 
      context: Dict[str, Any],
      temperature: Optional[float] = None,
      max_tokens: Optional[int] = None,
      model: Optional[str] = None
  ) -> str:
  ```

- Parameters passed from ChatRequest to LLM package

### 3. LLM Package Updates (`packages/llm/__init__.py`)

#### Core Function

- Updated `_invoke_llm` to accept optional parameters:

  ```python
  def _invoke_llm(
      prompt: str, 
      temperature: Optional[float] = None, 
      max_tokens: Optional[int] = None, 
      model: Optional[str] = None
  ) -> Optional[str]:
  ```

#### Provider-Specific Implementations

##### Ollama (`_invoke_ollama`)

- Temperature passed in `options.temperature`
- Max tokens passed in `options.num_predict`
- Model name overrides `OLLAMA_MODEL` env var
- Example payload:

  ```json
  {
    "model": "llama3.1",
    "prompt": "...",
    "stream": false,
    "options": {
      "temperature": 0.7,
      "num_predict": 2048
    }
  }
  ```

##### OpenAI (`_invoke_openai`)

- Parameters passed directly to `client.chat.completions.create()`
- Model name overrides `OPENAI_MODEL` env var
- Defaults: temperature=0.7, max_tokens=2048

##### Azure OpenAI (`_invoke_azure_openai`)

- Parameters passed to `client.chat.completions.create()`
- Model/deployment name can be overridden (defaults to `AZURE_OPENAI_DEPLOYMENT`)
- Falls back to env vars `AZURE_OPENAI_TEMPERATURE` and `AZURE_OPENAI_MAX_TOKENS` if not provided

## User Experience

### Default Behavior

- Settings popover collapsed by default (clean UI)
- Default values provide balanced performance:
  - Temperature: 0.7 (balanced creativity/consistency)
  - Max tokens: 2048 (sufficient for detailed responses)
  - Model: llama3.1 (local Ollama default)

### Power User Flow

1. Click settings icon (IconAdjustments) in header
2. Adjust temperature slider for creativity level
3. Set max tokens for response length control
4. Select different model if needed (e.g., switch to gpt-4 for better reasoning)
5. Click "Reset to Defaults" to restore initial values
6. Settings persist across sessions via localStorage

### Model Selection Options

#### Ollama (default)

- llama3.1
- llama3.2
- mixtral
- codellama
- mistral

#### OpenAI

- gpt-4o
- gpt-4o-mini
- gpt-4-turbo
- gpt-3.5-turbo

#### Azure OpenAI

- Uses deployment names from Azure portal
- Default: from AZURE_OPENAI_DEPLOYMENT env var
- Can override per request

## Testing Checklist

- [ ] Settings popover opens/closes correctly
- [ ] Temperature slider updates state and saves to localStorage
- [ ] Max tokens input validates range (128-8192)
- [ ] Model dropdown shows provider-specific options
- [ ] Reset button restores defaults
- [ ] Settings persist across page refreshes
- [ ] Settings passed to backend in API requests (check network tab)
- [ ] Backend extracts temperature/max_tokens/model from ChatRequest
- [ ] LLM package receives and uses parameters (check logs)
- [ ] Ollama API receives options.temperature and options.num_predict
- [ ] Response behavior changes with different temperature values
- [ ] Response length respects max_tokens limit

## Next Steps (Remaining Phase 2)

### Source Citations (RAG Evidence)

- Check if ChatResponse already includes evidence array
- Create inline citation component with hover preview
- Link citations to evidence sources (databases, documents, APIs)
- Example: "Revenue forecast shows 15% growth [1]" → hover shows "Source: Historical sales data (last 12 months)"

### Dev Mode Links

- Add environment check for dev mode (import.meta.env.DEV or localStorage flag)
- Create "Open in Playground" button (if LangServe endpoint available)
- Create "Open in Studio" button (if LangGraph Studio running)
- Conditional rendering based on dev mode and service availability

## Files Modified

### Created

- `apps/smb/src/components/ModelSettingsPopover.tsx` (127 lines)
- `docs/COACH_V4_PHASE2_MODEL_SETTINGS.md` (this file)

### Modified

- `apps/smb/src/pages/CoachV3.tsx`
  - Added ModelSettingsPopover import
  - Added modelSettings state with localStorage persistence
  - Rendered ModelSettingsPopover in header
  - Passed settings in basePayload to API
- `services/smb_gateway/coach_service.py`
  - Extended ChatRequest with temperature, max_tokens, model fields
  - Updated _invoke_llm signature and call site
- `packages/llm/__init__.py`
  - Updated _invoke_llm to accept optional parameters
  - Updated _invoke_ollama to pass options.temperature and options.num_predict
  - Updated _invoke_openai to use parameters in API call
  - Updated _invoke_azure_openai to use parameters in API call

## Benefits

1. **Flexibility**: Power users can tune LLM behavior for specific use cases
2. **Cost Control**: Max tokens helps manage API costs
3. **Model Experimentation**: Easy switching between models/providers
4. **Clean UX**: Settings hidden by default, doesn't overwhelm regular users
5. **Persistence**: Settings saved across sessions
6. **Provider Agnostic**: Works with Ollama, OpenAI, and Azure OpenAI

## Known Limitations

- Model dropdown shows all provider options; invalid selections will fail at runtime
- No real-time validation of model availability
- Temperature slider semantic labels (Focused/Balanced/Creative) are approximate
- No per-conversation settings (global across all chats)
- Settings not synced across devices (localStorage only)

## Future Enhancements (Phase 3+)

- Per-conversation model settings
- Model availability detection (hide unavailable models)
- Advanced options (top_p, frequency_penalty, presence_penalty)
- Settings presets/profiles ("Code Assistant", "Creative Writer", etc.)
- Cloud sync of settings (per-user backend storage)
- Model cost/performance comparison UI
