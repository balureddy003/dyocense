from packages.playbooks import PlaybookRegistry, load_default_playbooks


def test_match_returns_inventory_playbook():
    registry = PlaybookRegistry(load_default_playbooks())
    playbook = registry.match("Need to optimise inventory levels across warehouses")
    assert playbook is not None
    assert playbook.id == "inventory_baseline"


def test_match_returns_none_for_unknown_goal():
    registry = PlaybookRegistry(load_default_playbooks())
    playbook = registry.match("Design marketing copy for new product launch")
    assert playbook is None
