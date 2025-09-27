"""Mongo persistence for policies and audits."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional

from pymongo import ASCENDING, DESCENDING
from pymongo.collection import Collection

DEFAULT_POLICY_STATUS = "draft"


@dataclass(slots=True)
class PolicyVersion:
    version_id: str
    tenant_id: str
    policy_id: str
    name: str
    description: Optional[str]
    rules: List[Dict[str, object]]
    thresholds: Dict[str, object]
    status: str
    created_at: datetime
    created_by: str


@dataclass(slots=True)
class PolicyRecord:
    policy_id: str
    tenant_id: str
    active_version_id: Optional[str]
    updated_at: datetime


@dataclass(slots=True)
class AuditRecord:
    audit_id: str
    tenant_id: str
    policy_id: str
    version_id: str
    decision: Dict[str, object]
    source: Optional[str]
    created_at: datetime


class PolicyRepository:
    def __init__(self, policies: Collection, audits: Collection) -> None:
        self._policies = policies
        self._audits = audits
        self._ensure_indexes()

    def create_policy(
        self,
        tenant_id: str,
        name: str,
        description: Optional[str],
        rules: List[Dict[str, object]],
        thresholds: Dict[str, object],
        created_by: str,
    ) -> PolicyVersion:
        now = datetime.now(timezone.utc)
        policy_id = _uuid()
        version_id = _uuid()
        document = {
            "tenant_id": tenant_id,
            "policy_id": policy_id,
            "active_version_id": None,
            "versions": [
                {
                    "version_id": version_id,
                    "name": name,
                    "description": description,
                    "rules": rules,
                    "thresholds": thresholds,
                    "status": DEFAULT_POLICY_STATUS,
                    "created_at": now,
                    "created_by": created_by,
                }
            ],
            "updated_at": now,
        }
        self._policies.insert_one(document)
        return _version_from_doc(document["versions"][0], tenant_id, policy_id)

    def add_version(
        self,
        tenant_id: str,
        policy_id: str,
        name: str,
        description: Optional[str],
        rules: Optional[List[Dict[str, object]]],
        thresholds: Optional[Dict[str, object]],
        created_by: str,
    ) -> Optional[PolicyVersion]:
        now = datetime.now(timezone.utc)
        document = self._policies.find_one({"tenant_id": tenant_id, "policy_id": policy_id})
        if not document:
            return None
        existing_versions: List[Dict[str, object]] = document.get("versions", [])
        base_rules: List[Dict[str, object]] = rules if rules is not None else (existing_versions[-1].get("rules", []) if existing_versions else [])
        base_thresholds: Dict[str, object] = thresholds if thresholds is not None else (existing_versions[-1].get("thresholds", {}) if existing_versions else {})
        version = {
            "version_id": _uuid(),
            "name": name,
            "description": description,
            "rules": base_rules,
            "thresholds": base_thresholds,
            "status": DEFAULT_POLICY_STATUS,
            "created_at": now,
            "created_by": created_by,
        }
        self._policies.update_one(
            {"tenant_id": tenant_id, "policy_id": policy_id},
            {"$push": {"versions": version}, "$set": {"updated_at": now}},
        )
        return _version_from_doc(version, tenant_id, policy_id)

    def activate_version(
        self,
        tenant_id: str,
        policy_id: str,
        version_id: str,
        note: Optional[str],
    ) -> Optional[PolicyVersion]:
        now = datetime.now(timezone.utc)
        document = self._policies.find_one_and_update(
            {
                "tenant_id": tenant_id,
                "policy_id": policy_id,
                "versions.version_id": version_id,
            },
            {
                "$set": {
                    "active_version_id": version_id,
                    "versions.$.status": "active",
                    "versions.$.activated_at": now,
                    "versions.$.activation_note": note,
                    "updated_at": now,
                }
            },
            return_document=True,
        )
        if not document:
            return None
        for version in document.get("versions", []):
            if version.get("version_id") == version_id:
                return _version_from_doc(version, tenant_id, policy_id)
        return None

    def get_policy(self, tenant_id: str, policy_id: str) -> Optional[PolicyRecord]:
        document = self._policies.find_one({"tenant_id": tenant_id, "policy_id": policy_id})
        if not document:
            return None
        return PolicyRecord(
            policy_id=str(document.get("policy_id")),
            tenant_id=str(document.get("tenant_id")),
            active_version_id=document.get("active_version_id"),
            updated_at=document.get("updated_at", datetime.now(timezone.utc)),
        )

    def list_policies(self, tenant_id: str) -> Iterable[PolicyRecord]:
        cursor = self._policies.find({"tenant_id": tenant_id}).sort("updated_at", DESCENDING)
        return [
            PolicyRecord(
                policy_id=str(doc.get("policy_id")),
                tenant_id=str(doc.get("tenant_id")),
                active_version_id=doc.get("active_version_id"),
                updated_at=doc.get("updated_at", datetime.now(timezone.utc)),
            )
            for doc in cursor
        ]

    def get_version(self, tenant_id: str, policy_id: str, version_id: str) -> Optional[PolicyVersion]:
        document = self._policies.find_one(
            {
                "tenant_id": tenant_id,
                "policy_id": policy_id,
                "versions.version_id": version_id,
            },
            {
                "versions.$": 1,
                "tenant_id": 1,
                "policy_id": 1,
            },
        )
        if not document:
            return None
        version_doc = document.get("versions", [])[0]
        return _version_from_doc(version_doc, tenant_id, policy_id)

    def log_audit(
        self,
        tenant_id: str,
        policy_id: str,
        version_id: str,
        decision: Dict[str, object],
        source: Optional[str],
    ) -> AuditRecord:
        now = datetime.now(timezone.utc)
        document = {
            "audit_id": _uuid(),
            "tenant_id": tenant_id,
            "policy_id": policy_id,
            "version_id": version_id,
            "decision": decision,
            "source": source,
            "created_at": now,
        }
        self._audits.insert_one(document)
        return AuditRecord(
            audit_id=document["audit_id"],
            tenant_id=tenant_id,
            policy_id=policy_id,
            version_id=version_id,
            decision=decision,
            source=source,
            created_at=now,
        )

    def list_audits(self, tenant_id: str, policy_id: Optional[str] = None) -> Iterable[AuditRecord]:
        query = {"tenant_id": tenant_id}
        if policy_id:
            query["policy_id"] = policy_id
        cursor = self._audits.find(query).sort("created_at", DESCENDING)
        return [
            AuditRecord(
                audit_id=str(doc.get("audit_id")),
                tenant_id=str(doc.get("tenant_id")),
                policy_id=str(doc.get("policy_id")),
                version_id=str(doc.get("version_id")),
                decision=dict(doc.get("decision", {})),
                source=doc.get("source"),
                created_at=doc.get("created_at", datetime.now(timezone.utc)),
            )
            for doc in cursor
        ]

    def _ensure_indexes(self) -> None:
        self._policies.create_index([("tenant_id", ASCENDING), ("policy_id", ASCENDING)], unique=True)
        self._audits.create_index([("tenant_id", ASCENDING), ("created_at", DESCENDING)])


def _version_from_doc(doc: Dict[str, object], tenant_id: str, policy_id: str) -> PolicyVersion:
    return PolicyVersion(
        version_id=str(doc.get("version_id")),
        tenant_id=tenant_id,
        policy_id=policy_id,
        name=str(doc.get("name", "")),
        description=doc.get("description"),
        rules=list(doc.get("rules", [])),
        thresholds=dict(doc.get("thresholds", {})),
        status=str(doc.get("status", DEFAULT_POLICY_STATUS)),
        created_at=doc.get("created_at", datetime.now(timezone.utc)),
        created_by=str(doc.get("created_by", "system")),
    )


def _uuid() -> str:
    import uuid

    return str(uuid.uuid4())
