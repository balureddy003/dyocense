from packages.compiler_pipeline import CompileOrchestrator, CompileRequestContext, CompileTelemetry
from packages.knowledge import KnowledgeClient, KnowledgeDocument, InMemoryKnowledgeStore
from packages.playbooks import PlaybookRegistry, load_default_playbooks


def test_orchestrator_retrieves_snippets_and_selects_playbook(monkeypatch):
    store = InMemoryKnowledgeStore()
    document = KnowledgeDocument(
        tenant_id="tenant",
        project_id="proj",
        collection="inventory_planning",
        document_id="doc-123",
        text="Consider safety stock when demand spikes for seasonal inventory.",
        metadata={"schema_version": "1.0.0"},
    )
    store.upsert(document)

    client = KnowledgeClient(store=store)
    registry = PlaybookRegistry(load_default_playbooks())
    telemetry = CompileTelemetry()

    orchestrator = CompileOrchestrator(client, registry, telemetry)

    context = CompileRequestContext(
        goal="Optimise inventory levels for winter season",
        tenant_id="tenant",
        project_id="proj",
        data_inputs=None,
        use_llm=False,
    )

    base_ops = {
        "metadata": {"ops_version": "1.0.0", "problem_type": "inventory_planning"},
    }

    artifacts = orchestrator.generate_ops(context, base_ops)

    assert len(artifacts.snippets) == 1
    assert artifacts.playbook is not None
    assert base_ops["metadata"]["knowledge_snippets"] == ["doc-123"]
    assert base_ops["metadata"]["playbook_id"] == "inventory_baseline"
    assert artifacts.llm_ops is None
    assert artifacts.source == "disabled"
    assert artifacts.duration_seconds == 0.0
