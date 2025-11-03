"""Goal version ledger with persistence backends."""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, List, Optional

from packages.kernel_common.persistence import InMemoryCollection, get_collection

from .models import GoalVersion


class GoalVersionLedger:
    def __init__(self, collection=None) -> None:
        self._collection = collection or get_collection("goal_versions")
        self._is_fallback = isinstance(self._collection, InMemoryCollection)
        self._versions: Dict[str, GoalVersion] = {}
        self._by_tenant: Dict[str, List[str]] = defaultdict(list)
        self._by_project: Dict[str, List[str]] = defaultdict(list)
        self._load_existing()

    def record(self, version: GoalVersion) -> GoalVersion:
        self._versions[version.version_id] = version
        tenant_key = self._tenant_key(version.tenant_id)
        project_key = self._project_key(version.tenant_id, version.project_id)
        if version.version_id not in self._by_tenant[tenant_key]:
            self._by_tenant[tenant_key].append(version.version_id)
        if version.version_id not in self._by_project[project_key]:
            self._by_project[project_key].append(version.version_id)
        self._persist(version)
        return version

    def get(self, version_id: str) -> Optional[GoalVersion]:
        return self._versions.get(version_id)

    def list_for_project(self, tenant_id: str, project_id: str) -> List[GoalVersion]:
        project_key = self._project_key(tenant_id, project_id)
        return [self._versions[vid] for vid in self._by_project.get(project_key, [])]

    def list_for_tenant(self, tenant_id: str) -> List[GoalVersion]:
        tenant_key = self._tenant_key(tenant_id)
        return [self._versions[vid] for vid in self._by_tenant.get(tenant_key, [])]

    def iter_versions(self) -> Iterable[GoalVersion]:
        return self._versions.values()

    def annotate(self, version_id: str, **fields) -> Optional[GoalVersion]:
        version = self._versions.get(version_id)
        if not version:
            return None
        updated = version.model_copy(update=fields)
        self._versions[version_id] = updated
        self._persist(updated)
        return updated

    def _load_existing(self) -> None:
        try:
            if hasattr(self._collection, "find") and not self._is_fallback:
                for document in self._collection.find({}):  # type: ignore[attr-defined]
                    document.pop("_id", None)
                    self._hydrate(document)
            elif isinstance(self._collection, InMemoryCollection):
                for document in self._collection.find({}):
                    self._hydrate(document)
        except Exception:  # pragma: no cover - loading is best effort
            pass

    def _hydrate(self, document: dict) -> None:
        try:
            version = GoalVersion.model_validate(document)
        except Exception:  # pragma: no cover - malformed documents ignored
            return
        self._versions[version.version_id] = version
        tenant_key = self._tenant_key(version.tenant_id)
        project_key = self._project_key(version.tenant_id, version.project_id)
        if version.version_id not in self._by_tenant[tenant_key]:
            self._by_tenant[tenant_key].append(version.version_id)
        if version.version_id not in self._by_project[project_key]:
            self._by_project[project_key].append(version.version_id)

    def _persist(self, version: GoalVersion) -> None:
        document = version.model_dump()
        try:
            if hasattr(self._collection, "replace_one") and not self._is_fallback:
                self._collection.replace_one({"version_id": version.version_id}, document, upsert=True)  # type: ignore[attr-defined]
            elif isinstance(self._collection, InMemoryCollection):
                self._collection.replace_one({"version_id": version.version_id}, document, upsert=True)
        except Exception:  # pragma: no cover - persistence best effort
            pass

    @staticmethod
    def _tenant_key(tenant_id: str) -> str:
        return tenant_id

    @staticmethod
    def _project_key(tenant_id: str, project_id: str) -> str:
        return f"{tenant_id}:{project_id}"


GLOBAL_LEDGER = GoalVersionLedger()
