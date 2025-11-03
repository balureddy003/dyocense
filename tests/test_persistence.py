from __future__ import annotations

import importlib
import sys
from types import SimpleNamespace


def _reload_module(monkeypatch):
    sys.modules.pop("packages.kernel_common.persistence", None)
    module = importlib.import_module("packages.kernel_common.persistence")
    module._mongo_client = None  # type: ignore[attr-defined]
    return module


def test_get_collection_uses_env_uri(monkeypatch):
    module = _reload_module(monkeypatch)

    class FakeCollection(dict):
        pass

    class FakeDatabase:
        def get_collection(self, name: str):
            return FakeCollection(name=name)

    class FakeClient:
        def __init__(self, uri: str, serverSelectionTimeoutMS: int):
            self.uri = uri
            self.timeout = serverSelectionTimeoutMS
            self.admin = self

        def command(self, cmd: str):
            assert cmd == "ping"

        def get_database(self, name: str):
            return FakeDatabase()

    state = {}

    def fake_mongo_client(uri, serverSelectionTimeoutMS=1000):
        state["uri"] = uri
        state["timeout"] = serverSelectionTimeoutMS
        return FakeClient(uri, serverSelectionTimeoutMS)

    monkeypatch.setitem(sys.modules, "pymongo", SimpleNamespace(MongoClient=fake_mongo_client))
    monkeypatch.setenv("MONGO_URI", "mongodb://user:pass@mongo:27017/?authSource=admin")
    monkeypatch.setenv("MONGO_DB_NAME", "dyocense")

    collection = module.get_collection("evidence")
    assert isinstance(collection, dict)
    assert collection["name"] == "evidence"
    assert state["uri"] == "mongodb://user:pass@mongo:27017/?authSource=admin"

    # Cleanup env
    monkeypatch.delenv("MONGO_URI", raising=False)
    monkeypatch.delenv("MONGO_DB_NAME", raising=False)


def test_get_collection_falls_back_on_failure(monkeypatch):
    module = _reload_module(monkeypatch)

    def fake_mongo_client(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setitem(sys.modules, "pymongo", SimpleNamespace(MongoClient=fake_mongo_client))
    collection = module.get_collection("runs")
    assert isinstance(collection, module.InMemoryCollection)
