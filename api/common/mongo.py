"""MongoDB helpers shared across services."""
from __future__ import annotations

from functools import lru_cache
from typing import Dict

try:  # pragma: no cover - optional dependency check
    from pymongo import MongoClient
except ImportError as exc:  # pragma: no cover - during import, raise informative error later
    MongoClient = None  # type: ignore
    _import_error = exc
else:
    _import_error = None

_client_cache: Dict[str, MongoClient] = {}


def get_client(uri: str) -> MongoClient:
    """Return (and cache) a MongoClient for the provided URI."""

    if MongoClient is None:  # pragma: no cover - runtime guard when dependency missing
        raise RuntimeError(
            "pymongo is required to use Mongo-backed repositories. Install it via `pip install pymongo`."
        ) from _import_error
    if uri not in _client_cache:
        _client_cache[uri] = MongoClient(uri)  # type: ignore[call-arg]
    return _client_cache[uri]


def get_collection(uri: str, db_name: str, collection_name: str):
    client = get_client(uri)
    return client[db_name][collection_name]
