"""MongoDB persistence helpers with credential-aware fallbacks."""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

_mongo_client = None


class InMemoryCollection:
    """Fallback collection that mimics a subset of pymongo API."""

    def __init__(self) -> None:
        self._documents: list[Dict[str, Any]] = []

    def insert_one(self, document: Dict[str, Any]) -> None:
        self._documents.append(json.loads(json.dumps(document)))

    def find_one(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for doc in self._documents:
            if all(doc.get(k) == v for k, v in query.items()):
                return json.loads(json.dumps(doc))
        return None

    def find_many(self, query: Dict[str, Any], limit: int) -> list[Dict[str, Any]]:
        results: list[Dict[str, Any]] = []
        for doc in reversed(self._documents):  # latest first
            if all(doc.get(k) == v for k, v in query.items()):
                results.append(json.loads(json.dumps(doc)))
            if len(results) >= limit:
                break
        return results

    def find(self, query: Dict[str, Any]):
        for doc in self._documents:
            if all(doc.get(k) == v for k, v in query.items()):
                yield json.loads(json.dumps(doc))

    def replace_one(self, query: Dict[str, Any], replacement: Dict[str, Any], upsert: bool = False) -> None:
        for idx, doc in enumerate(self._documents):
            if all(doc.get(k) == v for k, v in query.items()):
                self._documents[idx] = json.loads(json.dumps(replacement))
                return
        if upsert:
            self.insert_one(replacement)


def _build_mongo_uri() -> str:
    explicit_uri = os.getenv("MONGO_URI")
    if explicit_uri:
        return explicit_uri

    host = os.getenv("MONGO_HOST", "localhost")
    port = os.getenv("MONGO_PORT", "27017")
    username = os.getenv("MONGO_USERNAME")
    password = os.getenv("MONGO_PASSWORD")
    auth_db = os.getenv("MONGO_AUTH_DB", "admin")

    if username and password:
        return f"mongodb://{username}:{password}@{host}:{port}/?authSource={auth_db}"
    return f"mongodb://{host}:{port}"


def _get_database_name() -> str:
    return os.getenv("MONGO_DB_NAME", "dyocense")


def _get_mongo_client():
    global _mongo_client
    if _mongo_client is not None:
        return _mongo_client

    try:
        from pymongo import MongoClient  # type: ignore

        uri = _build_mongo_uri()
        _mongo_client = MongoClient(uri, serverSelectionTimeoutMS=1000)
        # Trigger a lightweight command to validate connectivity/auth
        _mongo_client.admin.command("ping")
        logger.info("Connected to MongoDB at %s", uri.split("@")[-1] if "@" in uri else uri)
        return _mongo_client
    except Exception as exc:  # pragma: no cover - depends on external service
        logger.warning("Mongo client initialisation failed (%s); using in-memory fallback.", exc)
        _mongo_client = None
        return None


def get_collection(name: str):
    """Return a MongoDB collection or an in-memory fallback if pymongo/unavailable."""

    client = _get_mongo_client()
    if client is None:
        return InMemoryCollection()

    try:
        database = client.get_database(_get_database_name())
        return database.get_collection(name)
    except Exception as exc:  # pragma: no cover
        logger.warning("Failed to obtain Mongo collection '%s' (%s); using fallback.", name, exc)
        return InMemoryCollection()


__all__ = ["get_collection", "InMemoryCollection"]
