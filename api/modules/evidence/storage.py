"""MongoDB storage helpers for evidence snapshots."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Iterable, Optional

from pymongo import ASCENDING, DESCENDING
from pymongo.collection import Collection


@dataclass(slots=True)
class EvidenceRecord:
    evidence_ref: str
    tenant_id: str
    plan_id: Optional[str]
    goal_id: Optional[str]
    created_at: datetime
    snapshot: Dict[str, object]
    share_links: Dict[str, Dict[str, object]]


class EvidenceRepository:
    def __init__(self, collection: Collection) -> None:
        self._collection = collection
        self._ensure_indexes()

    def upsert_snapshot(
        self,
        tenant_id: str,
        evidence_ref: str,
        snapshot: Dict[str, object],
        plan_id: Optional[str] = None,
        goal_id: Optional[str] = None,
    ) -> EvidenceRecord:
        now = datetime.now(timezone.utc)
        document = self._collection.find_one_and_update(
            {"tenant_id": tenant_id, "evidence_ref": evidence_ref},
            {
                "$set": {
                    "snapshot": snapshot,
                    "plan_id": plan_id,
                    "goal_id": goal_id,
                    "updated_at": now,
                },
                "$setOnInsert": {
                    "created_at": now,
                    "share_links": {},
                },
            },
            upsert=True,
            return_document=True,
        )
        return _document_to_record(document)

    def get(self, tenant_id: str, evidence_ref: str) -> Optional[EvidenceRecord]:
        document = self._collection.find_one({"tenant_id": tenant_id, "evidence_ref": evidence_ref})
        return _document_to_record(document)

    def list(self, tenant_id: str) -> Iterable[EvidenceRecord]:
        cursor = self._collection.find({"tenant_id": tenant_id}).sort("created_at", DESCENDING)
        return [_document_to_record(doc) for doc in cursor]

    def add_share_link(self, tenant_id: str, evidence_ref: str, share_id: str, payload: Dict[str, object]) -> Optional[EvidenceRecord]:
        document = self._collection.find_one_and_update(
            {"tenant_id": tenant_id, "evidence_ref": evidence_ref},
            {
                "$set": {f"share_links.{share_id}": payload, "updated_at": datetime.now(timezone.utc)}
            },
            return_document=True,
        )
        return _document_to_record(document)

    def get_share_link(self, share_id: str) -> Optional[Dict[str, object]]:
        document = self._collection.find_one({f"share_links.{share_id}": {"$exists": True}})
        if not document:
            return None
        return document["share_links"][share_id]

    def _ensure_indexes(self) -> None:
        self._collection.create_index([("tenant_id", ASCENDING), ("evidence_ref", ASCENDING)], unique=True)
        self._collection.create_index([("share_links", ASCENDING)])


def _document_to_record(document: Optional[Dict[str, object]]) -> Optional[EvidenceRecord]:
    if not document:
        return None
    created_at = _to_datetime(document.get("created_at"))
    snapshot = dict(document.get("snapshot", {}))
    return EvidenceRecord(
        evidence_ref=str(document.get("evidence_ref")),
        tenant_id=str(document.get("tenant_id")),
        plan_id=document.get("plan_id"),
        goal_id=document.get("goal_id"),
        created_at=created_at,
        snapshot=snapshot,
        share_links=dict(document.get("share_links", {})),
    )


def _to_datetime(value: object) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return datetime.fromtimestamp(float(value), tz=timezone.utc)
