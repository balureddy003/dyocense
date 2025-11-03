from packages.versioning import GLOBAL_LEDGER, GoalVersion


def test_record_and_annotate_version():
    version = GoalVersion(
        version_id="ver-test",
        tenant_id="tenant",
        project_id="proj",
        goal="Goal",
        ops={"metadata": {"version_id": "ver-test"}},
        data_inputs={},
        playbook_id=None,
        knowledge_snippets=[],
    )

    GLOBAL_LEDGER.record(version)
    fetched = GLOBAL_LEDGER.get("ver-test")
    assert fetched is not None

    GLOBAL_LEDGER.annotate("ver-test", label="Baseline", parent_version_id="root")
    updated = GLOBAL_LEDGER.get("ver-test")
    assert updated.label == "Baseline"
    assert updated.parent_version_id == "root"
