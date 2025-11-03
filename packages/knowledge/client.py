"""Client utilities for interacting with a knowledge service."""

from __future__ import annotations

import logging
import os
from typing import Iterable, Optional

import httpx

from .models import (
    KnowledgeDocument,
    KnowledgeIngestResponse,
    KnowledgeRetrievalRequest,
    KnowledgeRetrievalResponse,
)
from .store import BaseKnowledgeStore, InMemoryKnowledgeStore

logger = logging.getLogger(__name__)


class KnowledgeClient:
    """Dual-mode client: HTTP when configured, local store otherwise."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        store: Optional[BaseKnowledgeStore] = None,
        timeout: float = 30.0,
    ) -> None:
        self._base_url = base_url or os.getenv("KNOWLEDGE_SERVICE_URL")
        self._store = store or InMemoryKnowledgeStore()
        self._timeout = timeout

    def ingest(self, document: KnowledgeDocument) -> KnowledgeIngestResponse:
        if self._base_url:
            return self._ingest_http(document)
        self._store.upsert(document)
        return KnowledgeIngestResponse(document_id=document.document_id)

    def batch_ingest(self, documents: Iterable[KnowledgeDocument]) -> None:
        if self._base_url:
            for doc in documents:
                self._ingest_http(doc)
            return
        self._store.batch_upsert(documents)

    def retrieve(self, request: KnowledgeRetrievalRequest) -> KnowledgeRetrievalResponse:
        if self._base_url:
            return self._retrieve_http(request)
        return self._store.retrieve(request)

    def _ingest_http(self, document: KnowledgeDocument) -> KnowledgeIngestResponse:
        url = f"{self._base_url.rstrip('/')}/v1/datasets/documents"
        try:
            response = httpx.post(url, json=document.model_dump(), timeout=self._timeout)
            response.raise_for_status()
            return KnowledgeIngestResponse(**response.json())
        except Exception as exc:
            logger.warning("Failed to ingest document via HTTP: %s", exc)
            raise

    def _retrieve_http(self, request: KnowledgeRetrievalRequest) -> KnowledgeRetrievalResponse:
        url = f"{self._base_url.rstrip('/')}/v1/retrieve"
        try:
            response = httpx.post(url, json=request.model_dump(), timeout=self._timeout)
            response.raise_for_status()
            return KnowledgeRetrievalResponse(**response.json())
        except Exception as exc:
            logger.warning("Knowledge retrieval over HTTP failed: %s", exc)
            raise

