"""Knowledge store abstractions and simple in-memory fallback."""

from __future__ import annotations

import math
import threading
from collections import Counter, defaultdict
from typing import Dict, Iterable, List

from .models import (
    KnowledgeDocument,
    KnowledgeRetrievalRequest,
    KnowledgeRetrievalResponse,
    KnowledgeSnippet,
)


def _tokenize(text: str) -> List[str]:
    return [token for token in text.lower().split() if token]


class BaseKnowledgeStore:
    """Interface so other services can swap in remote/vector-backed stores."""

    def upsert(self, document: KnowledgeDocument) -> None:  # pragma: no cover - interface
        raise NotImplementedError

    def batch_upsert(self, documents: Iterable[KnowledgeDocument]) -> None:
        for doc in documents:
            self.upsert(doc)

    def retrieve(self, request: KnowledgeRetrievalRequest) -> KnowledgeRetrievalResponse:  # pragma: no cover - interface
        raise NotImplementedError


class InMemoryKnowledgeStore(BaseKnowledgeStore):
    """Naive token frequency ranking used for local development and tests."""

    def __init__(self) -> None:
        self._documents: Dict[str, KnowledgeDocument] = {}
        self._tenant_index: Dict[str, set[str]] = defaultdict(set)
        self._lock = threading.RLock()

    def upsert(self, document: KnowledgeDocument) -> None:
        key = f"{document.tenant_id}:{document.document_id}"
        with self._lock:
            self._documents[key] = document
            self._tenant_index[document.tenant_id].add(key)

    def retrieve(self, request: KnowledgeRetrievalRequest) -> KnowledgeRetrievalResponse:
        candidates = self._candidate_keys(request)
        if not candidates:
            return KnowledgeRetrievalResponse(goal=request.goal, snippets=[])

        query_tokens = _tokenize(request.goal)
        query_counts = Counter(query_tokens)
        query_norm = math.sqrt(sum(count ** 2 for count in query_counts.values())) or 1.0
        scored: List[KnowledgeSnippet] = []

        with self._lock:
            for key in candidates:
                document = self._documents.get(key)
                if not document:
                    continue
                tokens = _tokenize(document.text)
                token_counts = Counter(tokens)
                dot = sum(token_counts[token] * query_counts[token] for token in query_counts)
                doc_norm = math.sqrt(sum(count ** 2 for count in token_counts.values())) or 1.0
                score = dot / (doc_norm * query_norm)
                if score <= 0.0:
                    continue
                scored.append(
                    KnowledgeSnippet(
                        document_id=document.document_id,
                        text=document.text,
                        score=score,
                        metadata=document.metadata,
                    )
                )

        ranked = sorted(scored, key=lambda item: item.score, reverse=True)[: request.limit]
        return KnowledgeRetrievalResponse(goal=request.goal, snippets=ranked)

    def _candidate_keys(self, request: KnowledgeRetrievalRequest) -> List[str]:
        filter_collection = request.filters.get("collection")
        filter_schema = request.filters.get("schema_version")
        project = request.project_id

        with self._lock:
            keys = list(self._tenant_index.get(request.tenant_id, []))

        if not any([project, filter_collection, filter_schema]):
            return keys

        result: List[str] = []
        with self._lock:
            for key in keys:
                doc = self._documents.get(key)
                if not doc:
                    continue
                if project and doc.project_id != project:
                    continue
                if filter_collection and doc.collection != filter_collection:
                    continue
                if filter_schema and doc.metadata.get("schema_version") != filter_schema:
                    continue
                result.append(key)
        return result

