from __future__ import annotations

import importlib
import os
import sys
from typing import Any


def _reload_graph_module() -> Any:
    sys.modules.pop("packages.kernel_common.graph", None)
    return importlib.import_module("packages.kernel_common.graph")


def test_graph_store_disabled_without_uri(monkeypatch):
    monkeypatch.delenv("NEO4J_URI", raising=False)
    graph = _reload_graph_module()
    graph._graph_store = None  # type: ignore[attr-defined]
    store = graph.get_graph_store()
    assert isinstance(store, graph.NullGraphStore)


def test_graph_store_disabled_without_driver(monkeypatch):
    monkeypatch.setenv("NEO4J_URI", "bolt://localhost:7687")
    monkeypatch.setenv("NEO4J_USER", "neo4j")
    monkeypatch.setenv("NEO4J_PASSWORD", "test")
    graph = _reload_graph_module()
    graph._graph_store = None  # type: ignore[attr-defined]
    store = graph.get_graph_store()
    assert isinstance(store, graph.NullGraphStore)
    # cleanup for later imports
    monkeypatch.delenv("NEO4J_URI", raising=False)
    monkeypatch.delenv("NEO4J_USER", raising=False)
    monkeypatch.delenv("NEO4J_PASSWORD", raising=False)
