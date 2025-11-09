"""Lightweight Keystone GraphQL client and health helper.

This module provides a small helper to call the Keystone GraphQL endpoint configured
via the KEYSTONE_GRAPHQL environment variable. It supports an optional proxy API key
via PROXY_API_KEY which will be sent as x-api-key header when present.

Designed to be a low-risk integration used by the kernel health check and by services
that need to read tenant/workspace/project data from Keystone.
"""

from __future__ import annotations

import os
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

try:
    import httpx  # type: ignore
except Exception:
    httpx = None  # type: ignore


KEYSTONE_GRAPHQL = os.getenv("KEYSTONE_GRAPHQL", "http://localhost:3001/api/graphql")
PROXY_API_KEY = os.getenv("PROXY_API_KEY")


def _default_headers() -> Dict[str, str]:
    headers: Dict[str, str] = {"Content-Type": "application/json"}
    if PROXY_API_KEY:
        headers["x-api-key"] = PROXY_API_KEY
    return headers


def run_graphql_sync(query: str, variables: Optional[Dict[str, Any]] = None, timeout: float = 5.0) -> Dict[str, Any]:
    """Synchronous GraphQL call to Keystone. Raises RuntimeError on failure."""
    if httpx is None:
        raise RuntimeError("httpx is not installed; cannot call Keystone GraphQL")
    try:
        resp = httpx.post(KEYSTONE_GRAPHQL, json={"query": query, "variables": variables}, headers=_default_headers(), timeout=timeout)
    except Exception as exc:
        logger.exception("Keystone GraphQL request failed")
        raise RuntimeError("Keystone unreachable") from exc

    if resp.status_code != 200:
        logger.error("Keystone GraphQL returned %s: %s", resp.status_code, resp.text)
        raise RuntimeError(f"Keystone returned {resp.status_code}")
    body = resp.json()
    if body.get("errors"):
        logger.error("Keystone GraphQL errors: %s", body.get("errors"))
        raise RuntimeError("GraphQL errors: %s" % body.get("errors"))
    return body.get("data", {})


async def run_graphql(query: str, variables: Optional[Dict[str, Any]] = None, timeout: float = 5.0) -> Dict[str, Any]:
    """Async GraphQL call using httpx.AsyncClient."""
    if httpx is None:
        raise RuntimeError("httpx is not installed; cannot call Keystone GraphQL")
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(KEYSTONE_GRAPHQL, json={"query": query, "variables": variables}, headers=_default_headers(), timeout=timeout)
        except Exception as exc:
            logger.exception("Keystone GraphQL request failed")
            raise RuntimeError("Keystone unreachable") from exc

        if resp.status_code != 200:
            logger.error("Keystone GraphQL returned %s: %s", resp.status_code, resp.text)
            raise RuntimeError(f"Keystone returned {resp.status_code}")
        body = resp.json()
        if body.get("errors"):
            logger.error("Keystone GraphQL errors: %s", body.get("errors"))
            raise RuntimeError("GraphQL errors: %s" % body.get("errors"))
        return body.get("data", {})


def health_check() -> Dict[str, Any]:
    """Quick health check for Keystone: performs an introspection query or a simple tenants query.

    Returns a dict with 'status' (healthy|degraded|unhealthy) and extra details.
    """
    sample_q = """query { __typename: __typename }"""
    try:
        data = run_graphql_sync(sample_q, timeout=3.0)
        # If we get a dict back, assume healthy
        return {"status": "healthy", "details": "connected"}
    except Exception as exc:
        logger.warning("Keystone health check failed: %s", exc)
        return {"status": "degraded", "error": str(exc)}


__all__ = ["run_graphql", "run_graphql_sync", "health_check"]
