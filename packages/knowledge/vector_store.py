"""Vector-backed knowledge store using Qdrant (optional dependency)."""

from __future__ import annotations

import hashlib
import logging
from typing import Iterable, List, Optional

from .models import (
    KnowledgeDocument,
    KnowledgeRetrievalRequest,
    KnowledgeRetrievalResponse,
    KnowledgeSnippet,
)
from .store import BaseKnowledgeStore

logger = logging.getLogger(__name__)

try:  # pragma: no cover - optional dependency
    from qdrant_client import QdrantClient
    from qdrant_client.http.models import Distance, VectorParams
except Exception:  # pragma: no cover
    QdrantClient = None  # type: ignore
    Distance = None  # type: ignore
    VectorParams = None  # type: ignore

try:  # pragma: no cover - optional dependency
    from azure.ai.openai import OpenAIClient  # type: ignore
    from azure.core.credentials import AzureKeyCredential  # type: ignore
except Exception:  # pragma: no cover
    OpenAIClient = None  # type: ignore
    AzureKeyCredential = None  # type: ignore


class QdrantKnowledgeStore(BaseKnowledgeStore):
    def __init__(
        self,
        url: str,
        api_key: str | None = None,
        collection: str = "dyocense_ops_context",
        vector_size: Optional[int] = 64,
    ) -> None:
        if QdrantClient is None:
            raise ImportError("qdrant-client is required for QdrantKnowledgeStore")
        self._client = QdrantClient(url=url, api_key=api_key)
        self._collection = collection
        self._embedding_client = self._init_azure_embedding_client()
        self._embedding_deployment = None
        if self._embedding_client:
            self._embedding_deployment = self._get_env("AZURE_OPENAI_EMBED_DEPLOYMENT")
        self._vector_size = vector_size or 64
        if self._embedding_client and self._embedding_deployment:
            embed = self._azure_embed("dimension-probe")
            if embed:
                self._vector_size = len(embed)
        self._ensure_collection()

    def upsert(self, document: KnowledgeDocument) -> None:
        vector = self._vectorize(document.text)
        payload = {
            "tenant_id": document.tenant_id,
            "project_id": document.project_id,
            "collection": document.collection,
            "metadata": document.metadata,
        }
        self._client.upsert(
            collection_name=self._collection,
            points=[
                {
                    "id": f"{document.tenant_id}:{document.document_id}",
                    "vector": vector,
                    "payload": {
                        **payload,
                        "document_id": document.document_id,
                        "text": document.text,
                    },
                }
            ],
        )

    def batch_upsert(self, documents: Iterable[KnowledgeDocument]) -> None:
        points = []
        for document in documents:
            points.append(
                {
                    "id": f"{document.tenant_id}:{document.document_id}",
                    "vector": self._vectorize(document.text),
                    "payload": {
                        "tenant_id": document.tenant_id,
                        "project_id": document.project_id,
                        "collection": document.collection,
                        "metadata": document.metadata,
                        "document_id": document.document_id,
                        "text": document.text,
                    },
                }
            )
        if points:
            self._client.upsert(collection_name=self._collection, points=points)

    def retrieve(self, request: KnowledgeRetrievalRequest) -> KnowledgeRetrievalResponse:
        vector = self._vectorize(request.goal)
        filters = {
            "must": [
                {"key": "tenant_id", "match": {"value": request.tenant_id}},
            ]
        }
        if request.project_id:
            filters["must"].append({"key": "project_id", "match": {"value": request.project_id}})
        if request.filters.get("collection"):
            filters["must"].append({"key": "collection", "match": {"value": request.filters["collection"]}})

        results = self._client.search(
            collection_name=self._collection,
            query_vector=vector,
            limit=request.limit,
            query_filter=filters,
        )
        snippets: List[KnowledgeSnippet] = []
        for hit in results:
            payload = hit.payload or {}
            snippets.append(
                KnowledgeSnippet(
                    document_id=payload.get("document_id", "unknown"),
                    text=payload.get("text", ""),
                    score=float(hit.score or 0.0),
                    metadata=payload.get("metadata", {}),
                )
            )
        return KnowledgeRetrievalResponse(goal=request.goal, snippets=snippets)

    def _ensure_collection(self) -> None:
        try:
            self._client.get_collection(self._collection)
        except Exception:
            logger.info("Creating Qdrant collection '%s'", self._collection)
            self._client.recreate_collection(
                collection_name=self._collection,
                vectors_config=VectorParams(size=self._vector_size, distance=Distance.COSINE),
            )

    def _vectorize(self, text: str) -> List[float]:
        if self._embedding_client and self._embedding_deployment:
            vector = self._azure_embed(text)
            if vector:
                return vector
        tokens = text.lower().split()
        vector = [0.0] * self._vector_size
        if not tokens:
            return vector
        for token in tokens:
            hashed = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)
            index = hashed % self._vector_size
            vector[index] += 1.0
        norm = sum(value * value for value in vector) ** 0.5 or 1.0
        return [value / norm for value in vector]

    def _init_azure_embedding_client(self):
        endpoint = self._get_env("AZURE_OPENAI_ENDPOINT")
        api_key = self._get_env("AZURE_OPENAI_API_KEY")
        deployment = self._get_env("AZURE_OPENAI_EMBED_DEPLOYMENT")
        if not (endpoint and api_key and deployment):
            return None
        if OpenAIClient is None or AzureKeyCredential is None:
            logger.warning("Azure embeddings requested but azure-ai-openai is not installed")
            return None
        try:
            client = OpenAIClient(endpoint=endpoint, credential=AzureKeyCredential(api_key))
            self._embedding_deployment = deployment
            return client
        except Exception as exc:  # pragma: no cover
            logger.warning("Failed to initialise Azure embedding client: %s", exc)
            return None

    def _azure_embed(self, text: str) -> Optional[List[float]]:
        if not self._embedding_client or not self._embedding_deployment:
            return None
        try:
            response = self._embedding_client.get_embeddings(
                model=self._embedding_deployment,
                input=text,
            )
            if not response.data:
                return None
            vector = response.data[0].embedding
            norm = sum(value * value for value in vector) ** 0.5 or 1.0
            return [value / norm for value in vector]
        except Exception as exc:  # pragma: no cover
            logger.warning("Azure embedding request failed: %s", exc)
            return None

    @staticmethod
    def _get_env(name: str) -> Optional[str]:
        import os

        value = os.getenv(name)
        return value.strip() if value else None


__all__ = ["QdrantKnowledgeStore"]
