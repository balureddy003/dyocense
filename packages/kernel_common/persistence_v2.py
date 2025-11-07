"""Multi-backend persistence layer for Dyocense platform.

Supports both MongoDB (enterprise microservices) and PostgreSQL (SMB-optimized)
with a unified interface and seamless backend switching via environment variables.

Backend Selection:
    - Set PERSISTENCE_BACKEND=postgres for SMB-optimized deployments
    - Set PERSISTENCE_BACKEND=mongodb for enterprise deployments (default)
    - Fallback to in-memory mode if database connection fails

Architecture:
    - Abstract base classes define common interface
    - Backend-specific implementations handle details
    - Factory pattern for backend instantiation
    - Plugin-based design for future database support
"""

from __future__ import annotations

import json
import logging
import os
from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Iterator

logger = logging.getLogger(__name__)

# Global backend instance
_backend: Optional[PersistenceBackend] = None


# =====================================================================
# Abstract Base Classes
# =====================================================================

class PersistenceBackend(ABC):
    """Abstract base class for persistence backends."""
    
    @abstractmethod
    def connect(self) -> bool:
        """Establish connection to backend. Returns True if successful."""
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Close connection to backend."""
        pass
    
    @abstractmethod
    def get_collection(self, name: str) -> Collection:
        """Get a collection/table by name."""
        pass
    
    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """Return backend health status."""
        pass


class Collection(ABC):
    """Abstract base class for collection/table operations."""
    
    @abstractmethod
    def insert_one(self, document: Dict[str, Any]) -> str:
        """Insert a single document. Returns document ID."""
        pass
    
    @abstractmethod
    def find_one(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find a single document matching query."""
        pass
    
    @abstractmethod
    def find(self, query: Dict[str, Any], limit: Optional[int] = None) -> Iterator[Dict[str, Any]]:
        """Find multiple documents matching query."""
        pass
    
    @abstractmethod
    def update_one(self, query: Dict[str, Any], update: Dict[str, Any], upsert: bool = False) -> int:
        """Update a single document. Returns number of documents modified."""
        pass
    
    @abstractmethod
    def delete_one(self, query: Dict[str, Any]) -> int:
        """Delete a single document. Returns number of documents deleted."""
        pass
    
    @abstractmethod
    def count(self, query: Dict[str, Any]) -> int:
        """Count documents matching query."""
        pass


# =====================================================================
# PostgreSQL Backend (SMB-Optimized)
# =====================================================================

class PostgresBackend(PersistenceBackend):
    """PostgreSQL backend using psycopg2 with connection pooling."""
    
    def __init__(self):
        self.pool: Optional[Any] = None
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load PostgreSQL configuration from environment."""
        return {
            "host": os.getenv("POSTGRES_HOST", "localhost"),
            "port": int(os.getenv("POSTGRES_PORT", "5432")),
            "database": os.getenv("POSTGRES_DB", "dyocense"),
            "user": os.getenv("POSTGRES_USER", "dyocense"),
            "password": os.getenv("POSTGRES_PASSWORD", ""),
            "min_pool_size": int(os.getenv("POSTGRES_MIN_POOL_SIZE", "2")),
            "max_pool_size": int(os.getenv("POSTGRES_MAX_POOL_SIZE", "10")),
        }
    
    def connect(self) -> bool:
        """Establish PostgreSQL connection pool."""
        try:
            import psycopg2.pool
            from psycopg2 import OperationalError
            
            self.pool = psycopg2.pool.SimpleConnectionPool(
                minconn=self.config["min_pool_size"],
                maxconn=self.config["max_pool_size"],
                host=self.config["host"],
                port=self.config["port"],
                database=self.config["database"],
                user=self.config["user"],
                password=self.config["password"]
            )
            
            # Test connection
            conn = self.pool.getconn()
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT version()")
                    version = cur.fetchone()[0]
                    logger.info(f"Connected to PostgreSQL: {version}")
            finally:
                self.pool.putconn(conn)
            
            return True
            
        except (ImportError, OperationalError) as exc:
            logger.error(f"PostgreSQL connection failed: {exc}")
            return False
    
    def disconnect(self) -> None:
        """Close all connections in pool."""
        if self.pool:
            self.pool.closeall()
            self.pool = None
    
    def get_collection(self, name: str) -> Collection:
        """Get a PostgreSQL collection wrapper."""
        return PostgresCollection(self, name)
    
    def health_check(self) -> Dict[str, Any]:
        """Check PostgreSQL health."""
        if not self.pool:
            return {"status": "disconnected", "backend": "postgres"}
        
        try:
            conn = self.pool.getconn()
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    return {
                        "status": "healthy",
                        "backend": "postgres",
                        "pool_size": self.pool._used + self.pool._pool.qsize()
                    }
            finally:
                self.pool.putconn(conn)
        except Exception as exc:
            return {"status": "error", "backend": "postgres", "error": str(exc)}
    
    @contextmanager
    def get_connection(self):
        """Context manager for getting pooled connections."""
        conn = self.pool.getconn()
        try:
            yield conn
        finally:
            self.pool.putconn(conn)


class PostgresCollection(Collection):
    """PostgreSQL table wrapper with MongoDB-like interface."""
    
    # Mapping of collection names to schemas and tables
    COLLECTION_MAPPING = {
        "tenants": ("tenants", "tenants"),
        "users": ("tenants", "users"),
        "projects": ("tenants", "projects"),
        "runs": ("runs", "runs"),
        "run_steps": ("runs", "run_steps"),
        "connectors": ("connectors", "connectors"),
        "evidence_nodes": ("evidence", "evidence_nodes"),
        "evidence_edges": ("evidence", "evidence_edges"),
        "documents": ("knowledge", "documents"),
        "events": ("system", "event_queue"),
        "audit": ("system", "audit_log"),
        "jobs": ("system", "background_jobs"),
    }
    
    def __init__(self, backend: PostgresBackend, name: str):
        self.backend = backend
        self.name = name
        self.schema, self.table = self.COLLECTION_MAPPING.get(name, ("public", name))
        self.full_name = f"{self.schema}.{self.table}"
    
    def insert_one(self, document: Dict[str, Any]) -> str:
        """Insert document and return generated ID."""
        from psycopg2.extras import Json, RealDictCursor
        
        # Extract ID field (varies by table)
        id_field = self._get_id_field()
        doc_id = document.get(id_field)
        
        # Build insert query dynamically
        columns = list(document.keys())
        placeholders = ["%s"] * len(columns)
        values = [Json(v) if isinstance(v, (dict, list)) else v for v in document.values()]
        
        query = f"""
            INSERT INTO {self.full_name} ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
            RETURNING {id_field}
        """
        
        with self.backend.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, values)
                result = cur.fetchone()
                conn.commit()
                return result[id_field] if result else doc_id
    
    def find_one(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find single document matching query."""
        from psycopg2.extras import RealDictCursor
        
        where_clause, params = self._build_where(query)
        sql = f"SELECT * FROM {self.full_name} WHERE {where_clause} LIMIT 1"
        
        with self.backend.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, params)
                result = cur.fetchone()
                return dict(result) if result else None
    
    def find(self, query: Dict[str, Any], limit: Optional[int] = None) -> Iterator[Dict[str, Any]]:
        """Find multiple documents matching query."""
        from psycopg2.extras import RealDictCursor
        
        where_clause, params = self._build_where(query)
        sql = f"SELECT * FROM {self.full_name} WHERE {where_clause}"
        if limit:
            sql += f" LIMIT {limit}"
        
        with self.backend.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, params)
                for row in cur:
                    yield dict(row)
    
    def update_one(self, query: Dict[str, Any], update: Dict[str, Any], upsert: bool = False) -> int:
        """Update single document."""
        from psycopg2.extras import Json
        
        where_clause, where_params = self._build_where(query)
        
        # Handle MongoDB-style $set operator
        if "$set" in update:
            update = update["$set"]
        
        set_clause = ", ".join([f"{k} = %s" for k in update.keys()])
        set_values = [Json(v) if isinstance(v, (dict, list)) else v for v in update.values()]
        
        sql = f"UPDATE {self.full_name} SET {set_clause} WHERE {where_clause}"
        
        with self.backend.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, set_values + where_params)
                rows_updated = cur.rowcount
                
                # Handle upsert if no rows updated
                if rows_updated == 0 and upsert:
                    merged_doc = {**query, **update}
                    self.insert_one(merged_doc)
                    rows_updated = 1
                
                conn.commit()
                return rows_updated
    
    def delete_one(self, query: Dict[str, Any]) -> int:
        """Delete single document."""
        where_clause, params = self._build_where(query)
        sql = f"DELETE FROM {self.full_name} WHERE {where_clause}"
        
        with self.backend.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                rows_deleted = cur.rowcount
                conn.commit()
                return rows_deleted
    
    def count(self, query: Dict[str, Any]) -> int:
        """Count documents matching query."""
        where_clause, params = self._build_where(query)
        sql = f"SELECT COUNT(*) FROM {self.full_name} WHERE {where_clause}"
        
        with self.backend.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                return cur.fetchone()[0]
    
    def _build_where(self, query: Dict[str, Any]) -> tuple[str, List[Any]]:
        """Build WHERE clause from query dict."""
        if not query:
            return "TRUE", []
        
        conditions = []
        params = []
        
        for key, value in query.items():
            conditions.append(f"{key} = %s")
            params.append(value)
        
        return " AND ".join(conditions), params
    
    def _get_id_field(self) -> str:
        """Get primary key field name for this collection."""
        id_mapping = {
            "tenants": "tenant_id",
            "users": "user_id",
            "projects": "project_id",
            "runs": "run_id",
            "connectors": "connector_id",
            "evidence_nodes": "node_id",
            "evidence_edges": "edge_id",
            "documents": "document_id",
            "events": "event_id",
            "audit": "audit_id",
            "jobs": "job_id",
        }
        return id_mapping.get(self.name, "id")


# =====================================================================
# MongoDB Backend (Enterprise Microservices)
# =====================================================================

class MongoBackend(PersistenceBackend):
    """MongoDB backend with connection pooling."""
    
    def __init__(self):
        self.client: Optional[Any] = None
        self.db: Optional[Any] = None
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load MongoDB configuration from environment."""
        return {
            "uri": os.getenv("MONGO_URI"),
            "host": os.getenv("MONGO_HOST", "localhost"),
            "port": int(os.getenv("MONGO_PORT", "27017")),
            "username": os.getenv("MONGO_USERNAME"),
            "password": os.getenv("MONGO_PASSWORD"),
            "auth_db": os.getenv("MONGO_AUTH_DB", "admin"),
            "database": os.getenv("MONGO_DB_NAME", "dyocense"),
            "replica_set": os.getenv("MONGO_REPLICA_SET"),
            "use_tls": os.getenv("MONGO_TLS", "false").lower() == "true",
        }
    
    def connect(self) -> bool:
        """Establish MongoDB connection."""
        try:
            from pymongo import MongoClient
            from pymongo.errors import ConnectionFailure
            
            uri = self._build_uri()
            
            self.client = MongoClient(
                uri,
                serverSelectionTimeoutMS=1000,
                connectTimeoutMS=2000,
                socketTimeoutMS=5000,
                retryWrites=True,
                maxPoolSize=50,
                minPoolSize=10
            )
            
            # Test connection
            self.client.admin.command("ping")
            self.db = self.client[self.config["database"]]
            
            logger.info(f"Connected to MongoDB at {self.config['host']}")
            return True
            
        except (ImportError, ConnectionFailure) as exc:
            logger.error(f"MongoDB connection failed: {exc}")
            return False
    
    def disconnect(self) -> None:
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            self.client = None
            self.db = None
    
    def get_collection(self, name: str) -> Collection:
        """Get MongoDB collection wrapper."""
        return MongoCollection(self.db[name])
    
    def health_check(self) -> Dict[str, Any]:
        """Check MongoDB health."""
        if not self.client:
            return {"status": "disconnected", "backend": "mongodb"}
        
        try:
            self.client.admin.command("ping")
            return {"status": "healthy", "backend": "mongodb"}
        except Exception as exc:
            return {"status": "error", "backend": "mongodb", "error": str(exc)}
    
    def _build_uri(self) -> str:
        """Build MongoDB connection URI."""
        if self.config["uri"]:
            return self.config["uri"]
        
        username = self.config["username"]
        password = self.config["password"]
        host = self.config["host"]
        port = self.config["port"]
        auth_db = self.config["auth_db"]
        
        if username and password:
            return f"mongodb://{username}:{password}@{host}:{port}/?authSource={auth_db}"
        return f"mongodb://{host}:{port}"


class MongoCollection(Collection):
    """Wrapper for MongoDB collection."""
    
    def __init__(self, collection):
        self.collection = collection
    
    def insert_one(self, document: Dict[str, Any]) -> str:
        """Insert document and return ID."""
        result = self.collection.insert_one(document)
        return str(result.inserted_id)
    
    def find_one(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find single document."""
        return self.collection.find_one(query)
    
    def find(self, query: Dict[str, Any], limit: Optional[int] = None) -> Iterator[Dict[str, Any]]:
        """Find multiple documents."""
        cursor = self.collection.find(query)
        if limit:
            cursor = cursor.limit(limit)
        return cursor
    
    def update_one(self, query: Dict[str, Any], update: Dict[str, Any], upsert: bool = False) -> int:
        """Update single document."""
        result = self.collection.update_one(query, update, upsert=upsert)
        return result.modified_count
    
    def delete_one(self, query: Dict[str, Any]) -> int:
        """Delete single document."""
        result = self.collection.delete_one(query)
        return result.deleted_count
    
    def count(self, query: Dict[str, Any]) -> int:
        """Count documents."""
        return self.collection.count_documents(query)


# =====================================================================
# In-Memory Backend (Fallback/Testing)
# =====================================================================

class InMemoryBackend(PersistenceBackend):
    """In-memory fallback backend for testing or when databases unavailable."""
    
    def __init__(self):
        self.collections: Dict[str, InMemoryCollection] = {}
    
    def connect(self) -> bool:
        """Always succeeds for in-memory."""
        logger.warning("Using in-memory persistence backend (data not persisted)")
        return True
    
    def disconnect(self) -> None:
        """Clear all collections."""
        self.collections.clear()
    
    def get_collection(self, name: str) -> Collection:
        """Get or create in-memory collection."""
        if name not in self.collections:
            self.collections[name] = InMemoryCollection()
        return self.collections[name]
    
    def health_check(self) -> Dict[str, Any]:
        """Always healthy."""
        return {
            "status": "healthy",
            "backend": "in-memory",
            "collections": len(self.collections)
        }


class InMemoryCollection(Collection):
    """In-memory collection using Python list."""
    
    def __init__(self):
        self.documents: List[Dict[str, Any]] = []
    
    def insert_one(self, document: Dict[str, Any]) -> str:
        """Insert document."""
        import uuid
        doc_copy = json.loads(json.dumps(document))
        if "_id" not in doc_copy:
            doc_copy["_id"] = str(uuid.uuid4())
        self.documents.append(doc_copy)
        return doc_copy["_id"]
    
    def find_one(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find single document."""
        for doc in self.documents:
            if all(doc.get(k) == v for k, v in query.items()):
                return json.loads(json.dumps(doc))
        return None
    
    def find(self, query: Dict[str, Any], limit: Optional[int] = None) -> Iterator[Dict[str, Any]]:
        """Find multiple documents."""
        results = []
        for doc in self.documents:
            if all(doc.get(k) == v for k, v in query.items()):
                results.append(json.loads(json.dumps(doc)))
                if limit and len(results) >= limit:
                    break
        return iter(results)
    
    def update_one(self, query: Dict[str, Any], update: Dict[str, Any], upsert: bool = False) -> int:
        """Update single document."""
        # Handle MongoDB-style $set operator
        if "$set" in update:
            update = update["$set"]
        
        for doc in self.documents:
            if all(doc.get(k) == v for k, v in query.items()):
                doc.update(update)
                return 1
        
        if upsert:
            self.insert_one({**query, **update})
            return 1
        return 0
    
    def delete_one(self, query: Dict[str, Any]) -> int:
        """Delete single document."""
        for idx, doc in enumerate(self.documents):
            if all(doc.get(k) == v for k, v in query.items()):
                del self.documents[idx]
                return 1
        return 0
    
    def count(self, query: Dict[str, Any]) -> int:
        """Count documents."""
        count = 0
        for doc in self.documents:
            if all(doc.get(k) == v for k, v in query.items()):
                count += 1
        return count


# =====================================================================
# Factory & Public API
# =====================================================================

def get_backend() -> PersistenceBackend:
    """Get or create the configured persistence backend.
    
    Backend selection order:
        1. PERSISTENCE_BACKEND env var (postgres, mongodb, in-memory)
        2. Auto-detect based on available credentials
        3. Fallback to in-memory if all connections fail
    """
    global _backend
    
    if _backend is not None:
        return _backend
    
    backend_type = os.getenv("PERSISTENCE_BACKEND", "").lower()
    
    # Explicit backend selection
    if backend_type == "postgres":
        _backend = PostgresBackend()
    elif backend_type == "mongodb":
        _backend = MongoBackend()
    elif backend_type == "in-memory":
        _backend = InMemoryBackend()
    else:
        # Auto-detect: try Postgres first (SMB default), then MongoDB
        if os.getenv("POSTGRES_HOST") or os.getenv("POSTGRES_DB"):
            _backend = PostgresBackend()
        elif os.getenv("MONGO_URI") or os.getenv("MONGO_HOST"):
            _backend = MongoBackend()
        else:
            logger.warning("No database configuration found, using in-memory backend")
            _backend = InMemoryBackend()
    
    # Try to connect
    if not _backend.connect():
        logger.error(f"Failed to connect to {type(_backend).__name__}, falling back to in-memory")
        _backend = InMemoryBackend()
        _backend.connect()
    
    return _backend


def get_collection(name: str) -> Collection:
    """Get a collection/table by name.
    
    Args:
        name: Collection name (e.g., "tenants", "runs", "connectors")
    
    Returns:
        Collection instance for the configured backend
    """
    backend = get_backend()
    return backend.get_collection(name)


def health_check() -> Dict[str, Any]:
    """Check persistence backend health."""
    backend = get_backend()
    return backend.health_check()


def close_connections() -> None:
    """Close all database connections."""
    global _backend
    if _backend:
        _backend.disconnect()
        _backend = None


# Backwards compatibility helpers
def get_mongo_client():
    """Legacy function for MongoDB client access."""
    backend = get_backend()
    if isinstance(backend, MongoBackend):
        return backend.client
    logger.warning("get_mongo_client() called but backend is not MongoDB")
    return None


def get_database():
    """Legacy function for MongoDB database access."""
    backend = get_backend()
    if isinstance(backend, MongoBackend):
        return backend.db
    logger.warning("get_database() called but backend is not MongoDB")
    return None


# Context manager for transactions (where supported)
@contextmanager
def transaction():
    """Context manager for database transactions (Postgres only for now)."""
    backend = get_backend()
    if isinstance(backend, PostgresBackend):
        with backend.get_connection() as conn:
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
    else:
        # No-op for backends without transaction support
        yield None
