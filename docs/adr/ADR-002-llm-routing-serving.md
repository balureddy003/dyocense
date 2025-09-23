# ADR-002: LLM Routing & Serving
## Status
Accepted
## Decision
Adopt LiteLLM router with local (Ollama/llama.cpp) + GPU (vLLM/TGI) + cloud fallback.
Guard with Guardrails/TypeChat; evaluate via Ragas/DeepEval/Promptfoo.
