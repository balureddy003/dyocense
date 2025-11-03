"""Pydantic models describing knowledge ingestion and retrieval contracts."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class KnowledgeDocument(BaseModel):
    """Single chunk of knowledge text with metadata for filtering."""

    tenant_id: str = Field(..., description="Tenant the document belongs to.")
    project_id: Optional[str] = Field(None, description="Optional project scope.")
    collection: str = Field(
        "default",
        description="Logical collection (e.g., dataset or topic) the document is part of.",
    )
    document_id: str = Field(..., description="Stable identifier for the document chunk.")
    text: str = Field(..., description="Plaintext content eligible for embedding/RAG.")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Structured attributes (schema_version, source_uri, etc.).",
    )


class KnowledgeIngestResponse(BaseModel):
    document_id: str
    status: str = "stored"


class KnowledgeSnippet(BaseModel):
    document_id: str
    text: str
    score: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


class KnowledgeRetrievalRequest(BaseModel):
    tenant_id: str
    project_id: Optional[str] = None
    goal: str = Field(..., description="The goal or query string used for retrieval.")
    limit: int = Field(5, ge=1, le=20)
    filters: Dict[str, Any] = Field(default_factory=dict)


class KnowledgeRetrievalResponse(BaseModel):
    goal: str
    snippets: List[KnowledgeSnippet]

