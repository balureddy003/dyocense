"""Neo4j graph helpers with graceful fallbacks."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

try:  # pragma: no cover - optional dependency
    from neo4j import GraphDatabase  # type: ignore
except Exception:  # pragma: no cover - driver missing
    GraphDatabase = None


@dataclass
class GraphConfig:
    uri: str
    user: str
    password: str
    database: Optional[str]


class NullGraphStore:
    """No-op graph store used when Neo4j is unavailable."""

    def ingest_evidence(self, payload: Dict[str, Any]) -> None:
        logger.debug("Graph store disabled; skipping evidence ingest.")

    def close(self) -> None:
        logger.debug("Graph store disabled; nothing to close.")


class Neo4jGraphStore:
    """Lightweight helper around neo4j driver."""

    def __init__(self, config: GraphConfig) -> None:
        if GraphDatabase is None:
            raise RuntimeError("neo4j driver not installed")
        self._config = config
        self._driver = GraphDatabase.driver(
            config.uri,
            auth=(config.user, config.password),
            max_connection_lifetime=120,
        )
        logger.info("Connected to Neo4j at %s", config.uri)

    def ingest_evidence(self, payload: Dict[str, Any]) -> None:
        """Persist run/evidence structure into Neo4j."""

        run_id = payload.get("run_id")
        tenant_id = payload.get("tenant_id")
        metadata = payload.get("ops", {}).get("metadata", {})

        def _work(tx):
            tx.run(
                """
                MERGE (t:Tenant {id: $tenant_id})
                MERGE (r:Run {id: $run_id})
                SET r += $run_props
                MERGE (t)-[:HAS_RUN]->(r)
                """,
                tenant_id=tenant_id,
                run_id=run_id,
                run_props={
                    "goal": metadata.get("goal") or payload.get("goal"),
                    "archetype_id": metadata.get("archetype_id"),
                    "stored_at": payload.get("stored_at"),
                },
            )

            tx.run(
                """
                MERGE (ops:OPS {run_id: $run_id})
                SET ops.payload = $ops_json
                MERGE (r:Run {id: $run_id})-[:HAS_OPS]->(ops)
                """,
                run_id=run_id,
                ops_json=json.dumps(payload.get("ops", {})),
            )

            tx.run(
                """
                MERGE (sol:Solution {run_id: $run_id})
                SET sol.payload = $solution_json
                MERGE (r:Run {id: $run_id})-[:HAS_SOLUTION]->(sol)
                """,
                run_id=run_id,
                solution_json=json.dumps(payload.get("solution", {})),
            )

            tx.run(
                """
                MERGE (exp:Explanation {run_id: $run_id})
                SET exp.payload = $explanation_json
                MERGE (r:Run {id: $run_id})-[:HAS_EXPLANATION]->(exp)
                """,
                run_id=run_id,
                explanation_json=json.dumps(payload.get("explanation", {})),
            )

        with self._driver.session(database=self._config.database) as session:
            session.execute_write(_work)
        logger.debug("Persisted run %s into Neo4j", run_id)

    def close(self) -> None:
        self._driver.close()
        logger.debug("Closed Neo4j driver.")


def _load_config_from_env() -> Optional[GraphConfig]:
    uri = os.getenv("NEO4J_URI")
    if not uri:
        return None
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "neo4j")
    database = os.getenv("NEO4J_DATABASE")
    return GraphConfig(uri=uri, user=user, password=password, database=database)


_graph_store: Optional[NullGraphStore | Neo4jGraphStore] = None


def get_graph_store() -> NullGraphStore | Neo4jGraphStore:
    global _graph_store
    if _graph_store is not None:
        return _graph_store

    config = _load_config_from_env()
    if not config:
        logger.info("NEO4J_URI not set; graph store disabled.")
        _graph_store = NullGraphStore()
        return _graph_store

    if GraphDatabase is None:
        logger.warning("neo4j driver missing; install neo4j to enable graph persistence.")
        _graph_store = NullGraphStore()
        return _graph_store

    try:
        _graph_store = Neo4jGraphStore(config)
    except Exception as exc:  # pragma: no cover - depends on external service
        logger.warning("Neo4j connection failed (%s); graph store disabled.", exc)
        _graph_store = NullGraphStore()
    return _graph_store


__all__ = ["get_graph_store", "Neo4jGraphStore", "NullGraphStore"]
