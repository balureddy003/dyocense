"""MongoDB persistence helpers with credential-aware fallbacks."""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)

_mongo_client = None
_inmem_collections: dict[str, "InMemoryCollection"] = {}
_connection_pool_config: dict[str, Any] = {
    "maxPoolSize": 50,
    "minPoolSize": 10,
    "maxIdleTimeMS": 45000,
    "waitQueueTimeoutMS": 5000,
}
_retry_writes = True
_use_fallback_mode = False  # Feature flag to force in-memory mode


def _mongo_disabled_by_env() -> bool:
    """Determine if MongoDB should be disabled based on environment.

    Rules:
    - If PERSISTENCE_BACKEND is set to 'postgres' or 'in-memory' or 'unified' -> disable Mongo
    - If USE_MONGODB is explicitly set to a falsy value -> disable Mongo
    - If DEPLOYMENT_MODE is 'unified' or 'smb' and USE_MONGODB is not explicitly true -> disable Mongo
    """
    # Explicit override: if MONGO_URI is provided, always attempt a Mongo path.
    # This lets tests or power users force the Mongo branch even in unified/postgres modes.
    if os.getenv("MONGO_URI"):
        return False
    backend = os.getenv("PERSISTENCE_BACKEND", "").lower()
    if backend in ("postgres", "postgre", "pg", "in-memory", "unified"):
        return True

    use_mongodb = os.getenv("USE_MONGODB")
    if use_mongodb is not None and use_mongodb.lower() not in ("1", "true", "yes", "on"):
        return True

    deployment_mode = os.getenv("DEPLOYMENT_MODE", "").lower()
    if deployment_mode in ("unified", "smb") and (use_mongodb is None or use_mongodb.lower() not in ("1", "true", "yes", "on")):
        return True

    return False


class InMemoryCollection:
    """Fallback collection that mimics a subset of pymongo API."""

    class _DeleteResult:
        def __init__(self, deleted_count: int) -> None:
            self.deleted_count = deleted_count

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

    def delete_one(self, query: Dict[str, Any]):
        for idx, doc in enumerate(self._documents):
            if all(doc.get(k) == v for k, v in query.items()):
                del self._documents[idx]
                return InMemoryCollection._DeleteResult(1)
        return InMemoryCollection._DeleteResult(0)


def _build_mongo_uri() -> str:
    """Build MongoDB connection URI from environment variables.
    
    Supports both explicit MONGO_URI and component-based configuration.
    Validates credentials and constructs proper connection string.
    """
    explicit_uri = os.getenv("MONGO_URI")
    if explicit_uri:
        return explicit_uri

    host = os.getenv("MONGO_HOST", "localhost")
    port = os.getenv("MONGO_PORT", "27017")
    username = os.getenv("MONGO_USERNAME")
    password = os.getenv("MONGO_PASSWORD")
    auth_db = os.getenv("MONGO_AUTH_DB", "admin")
    
    # Support replica sets
    replica_set = os.getenv("MONGO_REPLICA_SET")
    
    # Support TLS/SSL
    use_tls = os.getenv("MONGO_TLS", "false").lower() == "true"
    tls_ca_file = os.getenv("MONGO_TLS_CA_FILE")

    base_uri = ""
    if username and password:
        base_uri = f"mongodb://{username}:{password}@{host}:{port}/?authSource={auth_db}"
    else:
        base_uri = f"mongodb://{host}:{port}"
    
    # Add connection options
    options = []
    if replica_set:
        options.append(f"replicaSet={replica_set}")
    if use_tls:
        options.append("tls=true")
        if tls_ca_file:
            options.append(f"tlsCAFile={tls_ca_file}")
    
    if options:
        separator = "&" if "?" in base_uri else "?"
        base_uri += separator + "&".join(options)
    
    return base_uri


def _get_database_name() -> str:
    return os.getenv("MONGO_DB_NAME", "dyocense")


def _get_mongo_client():
    """Initialize MongoDB client with connection pooling and retry logic.
    
    Returns:
        MongoClient instance or None if connection fails.
    
    Configuration:
        - Connection pooling with 10-50 connections
        - 1 second server selection timeout for fast failover
        - Automatic retry for write operations
        - TLS/SSL support for secure connections
        - Replica set support for high availability
    """
    global _mongo_client, _use_fallback_mode
    
    # Respect environment to disable Mongo in SMB/unified/Postgres-only mode.
    # Additionally, if PERSISTENCE_BACKEND=postgres we hard-skip any attempt (no log spam).
    if _mongo_disabled_by_env() or os.getenv("PERSISTENCE_BACKEND", "").lower() in ("postgres", "postgre", "pg"):
        _use_fallback_mode = True
        return None

    # Check feature flag to force in-memory mode
    if os.getenv("FORCE_INMEMORY_MODE", "false").lower() == "true":
        logger.info("FORCE_INMEMORY_MODE enabled; skipping MongoDB connection")
        _use_fallback_mode = True
        return None
    
    if _mongo_client is not None:
        return _mongo_client

    try:
        from pymongo import MongoClient  # type: ignore
        from pymongo.errors import (
            ConnectionFailure,
            OperationFailure,
            ConfigurationError,
        )  # type: ignore

        uri = _build_mongo_uri()
        
        # Create client with production-ready configuration
        _mongo_client = MongoClient(
            uri,
            serverSelectionTimeoutMS=1000,  # Fast failover
            connectTimeoutMS=2000,
            socketTimeoutMS=5000,
            retryWrites=_retry_writes,
            retryReads=True,
            **_connection_pool_config
        )
        
        # Validate connectivity with ping command
        _mongo_client.admin.command("ping")
        
        # Get server info for logging
        server_info = _mongo_client.server_info()
        mongo_version = server_info.get("version", "unknown")
        
        # Mask credentials in URI for logging
        safe_uri = uri.split("@")[-1] if "@" in uri else uri
        logger.info(
            "Connected to MongoDB %s at %s (pool: %d-%d connections)",
            mongo_version,
            safe_uri,
            _connection_pool_config["minPoolSize"],
            _connection_pool_config["maxPoolSize"]
        )
        
        return _mongo_client
        
    except ImportError:
        logger.debug("pymongo not installed; skipping Mongo and using in-memory")
        _mongo_client = None
        _use_fallback_mode = True
        return None
    except (ConnectionFailure, OperationFailure, ConfigurationError):
        if os.getenv("PERSISTENCE_BACKEND", "").lower() not in ("postgres", "postgre", "pg"):
            logger.warning("MongoDB connection failed; falling back to in-memory")
        _mongo_client = None
        _use_fallback_mode = True
        return None
    except Exception as exc:  # pragma: no cover
        logger.debug(f"Unexpected Mongo init error '{exc}'; fallback to in-memory")
        _mongo_client = None
        _use_fallback_mode = True
        return None


def get_collection(name: str):
    """Return a MongoDB collection or an in-memory fallback if pymongo/unavailable.

    For the in-memory fallback, collections are cached by name so multiple services
    in the same process share data (important for the Kernel API).
    
    Args:
        name: Collection name
    
    Returns:
        MongoDB Collection or InMemoryCollection instance
    
    Usage:
        collection = get_collection("tenants")
        collection.insert_one({"tenant_id": "abc", "name": "Acme Corp"})
    """

    client = _get_mongo_client()
    if client is None:
        coll = _inmem_collections.get(name)
        if coll is None:
            coll = InMemoryCollection()
            _inmem_collections[name] = coll
            logger.debug("Created in-memory collection: %s", name)
        return coll

    try:
        database = client.get_database(_get_database_name())
        return database.get_collection(name)
    except Exception as exc:  # pragma: no cover
        logger.warning("Failed to obtain Mongo collection '%s' (%s); using fallback.", name, exc)
        coll = _inmem_collections.get(name)
        if coll is None:
            coll = InMemoryCollection()
            _inmem_collections[name] = coll
        return coll


@contextmanager
def mongo_transaction():
    """Context manager for MongoDB transactions (requires replica set).
    
    Usage:
        with mongo_transaction() as session:
            collection.insert_one(doc, session=session)
            another_collection.update_one(query, update, session=session)
    
    Falls back to no transaction if MongoDB unavailable or not replica set.
    """
    client = _get_mongo_client()
    if client is None or _use_fallback_mode:
        # No transaction support in fallback mode
        yield None
        return
    
    try:
        with client.start_session() as session:
            with session.start_transaction():
                yield session
    except Exception as exc:
        logger.warning("Transaction failed (%s); operations may be partially applied", exc)
        raise


def create_indexes(collection_name: str, indexes: list[tuple[str, int]]):
    """Create indexes on a MongoDB collection for query performance.
    
    Args:
        collection_name: Name of collection
        indexes: List of (field_name, direction) tuples. Direction: 1 for ascending, -1 for descending
    
    Example:
        create_indexes("tenants", [("tenant_id", 1), ("created_at", -1)])
    """
    client = _get_mongo_client()
    if client is None:
        logger.debug("Skipping index creation in in-memory mode")
        return
    
    try:
        from pymongo import IndexModel  # type: ignore
        
        database = client.get_database(_get_database_name())
        collection = database.get_collection(collection_name)
        
        index_models = [
            IndexModel([(field, direction)]) 
            for field, direction in indexes
        ]
        
        result = collection.create_indexes(index_models)
        logger.info("Created %d indexes on collection '%s': %s", len(result), collection_name, result)
        
    except Exception as exc:
        logger.warning("Failed to create indexes on '%s': %s", collection_name, exc)


def health_check() -> dict[str, Any]:
    """Check MongoDB connection health.
    
    Returns:
        dict with status, mode, and details
    
    Example:
        {
            "status": "healthy",
            "mode": "mongodb",
            "mongodb_version": "6.0.3",
            "database": "dyocense",
            "connection_pool": {"min": 10, "max": 50}
        }
    """
    client = _get_mongo_client()
    
    if client is None or _use_fallback_mode:
        return {
            "status": "degraded",
            "mode": "in-memory",
            "message": "Using in-memory fallback; data will not persist",
            "collections": list(_inmem_collections.keys())
        }
    
    try:
        server_info = client.server_info()
        db_name = _get_database_name()
        
        return {
            "status": "healthy",
            "mode": "mongodb",
            "mongodb_version": server_info.get("version"),
            "database": db_name,
            "connection_pool": {
                "min": _connection_pool_config["minPoolSize"],
                "max": _connection_pool_config["maxPoolSize"]
            }
        }
    except Exception as exc:
        return {
            "status": "unhealthy",
            "mode": "mongodb",
            "error": str(exc)
        }


__all__ = [
    "get_collection", 
    "InMemoryCollection", 
    "mongo_transaction", 
    "create_indexes",
    "health_check"
]
