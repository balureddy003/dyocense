```bash
# List configured LLM providers
http GET :8000/llm/providers Authorization:"Bearer tenant_demo"

# Invoke provider (mocked until external credentials provided)
http POST :8000/llm/chat Authorization:"Bearer tenant_demo" \
  provider_id=openai prompt='Summarize replenishment risk for SKU1.'
```
