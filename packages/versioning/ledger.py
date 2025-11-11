"""Goal version ledger with Postgres and fallback stores."""

from __future__ import annotations

import logging
import threading
from typing import Any, Dict, Iterable, List, Optional

from .models import GoalVersion

logger = logging.getLogger(__name__)


class _InMemoryGoalVersionRepository:
    """Simple in-memory storage for GoalVersion when Postgres is unavailable."""

    def __init__(self) -> None:
        self._store: dict[str, GoalVersion] = {}
        self._lock = threading.RLock()

    def _clone(self, version: GoalVersion) -> GoalVersion:
        return version.copy(deep=True)

    def upsert(self, version: GoalVersion) -> GoalVersion:
        with self._lock:
            self._store[version.version_id] = self._clone(version)
            return self._clone(self._store[version.version_id])

    def get(self, version_id: str) -> Optional[GoalVersion]:
        with self._lock:
            version = self._store.get(version_id)
            return self._clone(version) if version is not None else None

    def list_for_project(self, tenant_id: str, project_id: str) -> List[GoalVersion]:
        with self._lock:
            versions = [
                self._clone(v)
                for v in self._store.values()
                if v.tenant_id == tenant_id and v.project_id == project_id
            ]
        versions.sort(key=lambda v: v.created_at, reverse=True)
        return versions

    def list_for_tenant(self, tenant_id: str) -> List[GoalVersion]:
        with self._lock:
            versions = [self._clone(v) for v in self._store.values() if v.tenant_id == tenant_id]
        versions.sort(key=lambda v: v.created_at, reverse=True)
        return versions

    def iter_all(self) -> Iterable[GoalVersion]:
        with self._lock:
            versions = sorted(self._store.values(), key=lambda v: v.created_at, reverse=True)
            for version in versions:
                yield self._clone(version)

    def annotate(self, version_id: str, fields: Dict[str, Any]) -> Optional[GoalVersion]:
        with self._lock:
            current = self._store.get(version_id)
            if current is None:
                return None
            data = current.dict()
            for key, value in fields.items():
                data[key] = value
            updated = GoalVersion(**data)
            self._store[version_id] = updated
            return self._clone(updated)


def _build_repository() -> Any:
    try:
        from packages.versioning.repository_postgres import GoalVersionRepositoryPG
    except ImportError as exc:
        logger.warning("Postgres goal ledger disabled because dependency missing: %s", exc)
        return _InMemoryGoalVersionRepository()

    try:
        return GoalVersionRepositoryPG()
    except RuntimeError as exc:
        logger.warning("Postgres goal ledger disabled: %s", exc)
        return _InMemoryGoalVersionRepository()
    except Exception as exc:  # pragma: no cover - best effort so bucket errors
        logger.warning("Failed to initialize Postgres ledger, falling back to memory: %s", exc)
        return _InMemoryGoalVersionRepository()


class GoalVersionLedger:
    """Thin wrapper over the repository to preserve the legacy API."""

    def __init__(self, repository: Any | None = None) -> None:
        self._repository = repository or _build_repository()

    def record(self, version: GoalVersion) -> GoalVersion:
        return self._repository.upsert(version)

    def get(self, version_id: str) -> Optional[GoalVersion]:
        return self._repository.get(version_id)

    def list_for_project(self, tenant_id: str, project_id: str) -> List[GoalVersion]:
        return self._repository.list_for_project(tenant_id, project_id)

    def list_for_tenant(self, tenant_id: str) -> List[GoalVersion]:
        return self._repository.list_for_tenant(tenant_id)

    def iter_versions(self) -> Iterable[GoalVersion]:
        return self._repository.iter_all()

    def annotate(self, version_id: str, **fields) -> Optional[GoalVersion]:
        return self._repository.annotate(version_id, fields)


GLOBAL_LEDGER = GoalVersionLedger()
