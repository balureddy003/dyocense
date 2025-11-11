"""Goal version ledger backed by PostgreSQL."""

from __future__ import annotations

from typing import Iterable, List, Optional

from packages.versioning.repository_postgres import GoalVersionRepositoryPG

from .models import GoalVersion


class GoalVersionLedger:
    """Thin wrapper over the Postgres repository to preserve the legacy API."""

    def __init__(self, repository: GoalVersionRepositoryPG | None = None) -> None:
        self._repository = repository or GoalVersionRepositoryPG()

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
