"""LLM helper utilities with graceful fallback."""

from __future__ import annotations

import json
import logging
import os
from typing import Dict, List, Optional, Sequence

import httpx


logger = logging.getLogger(__name__)


def generate_explanation_llm(
    goal: str,
    solution: dict,
    highlights: List[str],
    what_ifs: List[str],
) -> Dict[str, List[str] | str] | None:
    prompt = _build_prompt(goal, solution, highlights, what_ifs)
    content = _invoke_llm(prompt)
    if not content:
        return None
    return {"summary": content.strip(), "highlights": highlights, "what_ifs": what_ifs}


def generate_ops_llm(
    goal: str,
    base_ops: dict,
    data_inputs: Optional[dict] = None,
    retrieval_snippets: Optional[Sequence[Dict[str, str]]] = None,
    playbook_instructions: Optional[str] = None,
) -> Optional[dict]:
    base_json = json.dumps(base_ops, indent=2)
    data_json = json.dumps(data_inputs, indent=2) if data_inputs else "None"
    context_json = _format_retrieval_snippets(retrieval_snippets)
    playbook_text = playbook_instructions or "Follow best practices for optimisation modelling."
    prompt = (
        "You are an optimisation expert. Build a valid Optimization Problem Spec (OPS) JSON "
        "object compatible with the provided metadata. Do not return prose, only JSON.\n"
        f"Metadata template (preserve and extend as needed):\n{base_json}\n"
        f"Goal: {goal}\n"
        f"Optional data inputs (may include demand, costs, etc.):\n{data_json}\n"
        f"Retrieved knowledge snippets for context:\n{context_json}\n"
        f"Playbook guidance:\n{playbook_text}\n"
        "Populate the following sections: metadata (reuse provided values), objective, "
        "decision_variables, parameters, constraints, kpis, validation_notes. "
        "Ensure the JSON is parseable."
    )
    content = _invoke_llm(prompt)
    if not content:
        return None
    return _extract_json(content)


def _invoke_llm(prompt: str, temperature: Optional[float] = None, max_tokens: Optional[int] = None, model: Optional[str] = None) -> Optional[str]:
    provider = os.getenv("LLM_PROVIDER", "ollama").lower()
    if provider == "openai":
        return _invoke_openai(prompt, temperature=temperature, max_tokens=max_tokens, model=model)
    if provider == "ollama":
        return _invoke_ollama(prompt, temperature=temperature, max_tokens=max_tokens, model=model)
    if provider == "azure":
        return _invoke_azure_openai(prompt, temperature=temperature, max_tokens=max_tokens, model=model)
    return None


def _invoke_openai(prompt: str, temperature: Optional[float] = None, max_tokens: Optional[int] = None, model: Optional[str] = None) -> Optional[str]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    try:
        from openai import OpenAI  # type: ignore
    except ImportError:
        return None

    model_name = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    temp = temperature if temperature is not None else 0.7
    tokens = max_tokens if max_tokens is not None else 2048
    
    client = OpenAI(api_key=api_key)
    try:
        completion = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=temp,
            max_tokens=tokens,
        )
        if not completion.choices:
            return None
        return (completion.choices[0].message.content or "").strip()
    except Exception as exc:
        logger.warning("OpenAI invocation failed: %s", exc)
        return None


def _invoke_azure_openai(prompt: str, temperature: Optional[float] = None, max_tokens: Optional[int] = None, model: Optional[str] = None) -> Optional[str]:  # pragma: no cover - optional dependency
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    deployment = model or os.getenv("AZURE_OPENAI_DEPLOYMENT")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
    
    if not (endpoint and api_key and deployment):
        logger.warning("Azure OpenAI environment variables missing; skipping invocation")
        return None

    try:
        from openai import AzureOpenAI
    except ImportError:
        logger.warning("openai package not installed; cannot invoke Azure OpenAI")
        return None

    try:
        client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version=api_version,
        )
        
        temp = temperature if temperature is not None else float(os.getenv("AZURE_OPENAI_TEMPERATURE", "0.7"))
        tokens = max_tokens if max_tokens is not None else int(os.getenv("AZURE_OPENAI_MAX_TOKENS", "2048"))
        
        response = client.chat.completions.create(
            model=deployment,
            messages=[{"role": "user", "content": prompt}],
            temperature=temp,
            max_tokens=tokens,
        )
        
        if not response.choices:
            return None
        return (response.choices[0].message.content or "").strip()
    except Exception as exc:
        logger.warning("Azure OpenAI invocation failed: %s", exc)
        return None


def _invoke_ollama(prompt: str, temperature: Optional[float] = None, max_tokens: Optional[int] = None, model: Optional[str] = None) -> Optional[str]:
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    model_name = model or os.getenv("OLLAMA_MODEL", "llama3.1")
    stream_str = os.getenv("OLLAMA_STREAM", "false")
    stream = stream_str.strip().lower() in {"1", "true", "yes", "on"}
    timeout_env = os.getenv("OLLAMA_TIMEOUT")
    try:
        timeout_val = float(timeout_env) if timeout_env else 120.0
    except ValueError:
        logger.warning("Invalid OLLAMA_TIMEOUT '%s'; using default", timeout_env)
        timeout_val = 120.0

    timeout_cfg = httpx.Timeout(timeout_val, read=timeout_val, connect=30.0)

    payload = {"model": model_name, "prompt": prompt, "stream": stream}
    
    # Add optional parameters if provided
    options = {}
    if temperature is not None:
        options["temperature"] = temperature
    if max_tokens is not None:
        options["num_predict"] = max_tokens
    if options:
        payload["options"] = options
    
    curl_cmd = (
        f"curl -X POST '{base_url}/api/generate' "
        "-H 'Content-Type: application/json' "
        f"-d '{json.dumps(payload)}'"
    )
    logger.debug("Ollama request (curl): %s", curl_cmd)

    try:
        response = httpx.post(
            f"{base_url}/api/generate",
            json=payload,
            timeout=timeout_cfg,
        )
        response.raise_for_status()
        data = response.json()
        return (data.get("response") or "").strip()
    except httpx.TimeoutException:
        logger.warning("Ollama request timed out after %.1fs", timeout_val)
        return None
    except Exception as exc:
        logger.warning("Ollama invocation failed: %s", exc)
        return None


def _build_prompt(goal: str, solution: dict, highlights: List[str], what_ifs: List[str]) -> str:
    solver = solution.get("metadata", {}).get("solver", "unknown solver")
    objective_value = solution.get("kpis", {}).get("objective_value", "unknown")
    return (
        "You are an optimisation expert. Summarise the following optimisation run in plain English.\n"
        f"Goal: {goal}\n"
        f"Solver: {solver}\n"
        f"Objective value: {objective_value}\n"
        f"Key highlights: {', '.join(highlights)}\n"
        f"Suggested what-ifs: {', '.join(what_ifs)}\n"
        "Focus on actionable insights, within 6 sentences."
    )


def _extract_json(text: str) -> Optional[dict]:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        if start == -1:
            return None
        depth = 0
        for idx in range(start, len(text)):
            char = text[idx]
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    candidate = text[start : idx + 1]
                    try:
                        return json.loads(candidate)
                    except json.JSONDecodeError:
                        continue
        return None


def _format_retrieval_snippets(
    snippets: Optional[Sequence[Dict[str, str]]],
) -> str:
    if not snippets:
        return "None"
    formatted: List[str] = []
    for snippet in snippets:
        doc_id = snippet.get("document_id", "unknown")
        text = snippet.get("text", "")
        formatted.append(f"{doc_id}: {text}")
    return "\n".join(formatted) or "None"
