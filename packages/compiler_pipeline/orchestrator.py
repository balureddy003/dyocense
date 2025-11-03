from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from packages.kernel_common.logging import configure_logging
from packages.llm import generate_ops_llm
from packages.knowledge import KnowledgeClient, KnowledgeRetrievalRequest
from packages.playbooks import DecisionPlaybook, PlaybookRegistry

logger = configure_logging("compiler-pipeline")


@dataclass
class CompileRequestContext:
    goal: str
    tenant_id: str
    project_id: str
    data_inputs: Dict[str, Any] | None = None
    use_llm: bool = True


@dataclass
class CompileTelemetry:
    events: list[dict[str, Any]] = field(default_factory=list)

    def record(self, event_type: str, **payload: Any) -> None:
        entry = {"event": event_type, **payload}
        self.events.append(entry)
        logger.info("compiler_event=%s", entry)


@dataclass
class CompileArtifacts:
    snippets: list[dict]
    playbook: DecisionPlaybook | None
    llm_ops: dict | None


class CompileOrchestrator:
    """Coordinates knowledge retrieval, playbook selection, and LLM synthesis."""

    def __init__(
        self,
        knowledge_client: KnowledgeClient,
        playbook_registry: PlaybookRegistry,
        telemetry: Optional[CompileTelemetry] = None,
    ) -> None:
        self._knowledge_client = knowledge_client
        self._playbooks = playbook_registry
        self._telemetry = telemetry or CompileTelemetry()

    def generate_ops(self, context: CompileRequestContext, base_ops: dict) -> CompileArtifacts:
        snippets = self._retrieve_context(context, base_ops)
        playbook = self._select_playbook(context.goal)

        if snippets:
            base_ops.setdefault("metadata", {})["knowledge_snippets"] = [
                snippet["document_id"] for snippet in snippets
            ]
        if playbook:
            base_ops.setdefault("metadata", {})["playbook_id"] = playbook.id
            base_ops["metadata"]["playbook_version"] = playbook.version

        if not context.use_llm:
            self._telemetry.record("llm_disabled", goal=context.goal)
            return CompileArtifacts(snippets=snippets, playbook=playbook, llm_ops=None)

        prompt_start = time.perf_counter()
        llm_ops = generate_ops_llm(
            context.goal,
            base_ops,
            context.data_inputs,
            retrieval_snippets=snippets,
            playbook_instructions=playbook.prompt_guidelines if playbook else None,
        )
        duration = time.perf_counter() - prompt_start
        model = os.getenv("OLLAMA_MODEL") or os.getenv("OPENAI_MODEL") or "unknown"
        self._telemetry.record(
            "llm_compile_attempt",
            goal=context.goal,
            playbook_id=getattr(playbook, "id", None),
            snippet_count=len(snippets),
            duration_seconds=duration,
            model=model,
        )
        if llm_ops:
            return CompileArtifacts(snippets=snippets, playbook=playbook, llm_ops=llm_ops)
        self._telemetry.record("llm_compile_failed", goal=context.goal)
        return CompileArtifacts(snippets=snippets, playbook=playbook, llm_ops=None)

    def _retrieve_context(self, context: CompileRequestContext, base_ops: dict) -> list[dict]:
        request = KnowledgeRetrievalRequest(
            tenant_id=context.tenant_id,
            project_id=context.project_id,
            goal=context.goal,
            limit=7,
            filters={
                "collection": base_ops.get("metadata", {}).get("problem_type", "ops_context"),
                "schema_version": base_ops.get("metadata", {}).get("ops_version"),
            },
        )
        try:
            response = self._knowledge_client.retrieve(request)
        except Exception as exc:  # pragma: no cover - remote failure path
            self._telemetry.record("knowledge_retrieval_failed", error=str(exc))
            logger.warning("Knowledge retrieval failed: %s", exc)
            return []
        snippets = [
            snippet.model_dump() if hasattr(snippet, "model_dump") else snippet for snippet in response.snippets
        ]
        self._telemetry.record("knowledge_retrieved", count=len(snippets))
        return snippets

    def _select_playbook(self, goal: str) -> DecisionPlaybook | None:
        playbook = self._playbooks.match(goal)
        if playbook:
            self._telemetry.record("playbook_selected", playbook_id=playbook.id, version=playbook.version)
        else:
            self._telemetry.record("playbook_not_found", goal=goal)
        return playbook
