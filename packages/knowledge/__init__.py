"""
Knowledge plane abstractions used across services.

Phase 1 introduces a lightweight in-memory fallback alongside HTTP clients so
the system can scale toward external stores such as MinIO + Qdrant later.
"""

from .client import KnowledgeClient
from .store import InMemoryKnowledgeStore
from .vector_store import QdrantKnowledgeStore
from .models import (
    KnowledgeDocument,
    KnowledgeIngestResponse,
    KnowledgeRetrievalRequest,
    KnowledgeRetrievalResponse,
    KnowledgeSnippet,
)

__all__ = [
    "InMemoryKnowledgeStore",
    "KnowledgeClient",
    "KnowledgeDocument",
    "KnowledgeIngestResponse",
    "KnowledgeRetrievalRequest",
    "KnowledgeRetrievalResponse",
    "KnowledgeSnippet",
    "QdrantKnowledgeStore",
]
