from packages.knowledge import (
    InMemoryKnowledgeStore,
    KnowledgeDocument,
    KnowledgeRetrievalRequest,
)


def test_retrieval_prioritises_matching_terms():
    store = InMemoryKnowledgeStore()
    store.upsert(
        KnowledgeDocument(
            tenant_id="tenant",
            project_id="proj",
            collection="ops_context",
            document_id="doc-1",
            text="Inventory planning for seasonal demand spikes",
            metadata={"schema_version": "1.0"},
        )
    )
    store.upsert(
        KnowledgeDocument(
            tenant_id="tenant",
            project_id="proj",
            collection="ops_context",
            document_id="doc-2",
            text="Unrelated marketing campaign details",
            metadata={"schema_version": "1.0"},
        )
    )

    request = KnowledgeRetrievalRequest(
        tenant_id="tenant",
        project_id="proj",
        goal="Plan inventory levels to handle demand spikes",
        limit=1,
        filters={"collection": "ops_context"},
    )

    response = store.retrieve(request)
    assert len(response.snippets) == 1
    assert response.snippets[0].document_id == "doc-1"
