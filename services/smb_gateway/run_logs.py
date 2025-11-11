from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class RunEvent(BaseModel):
    type: str
    name: Optional[str] = None
    ts: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    latency_ms: Optional[int] = None
    data: Optional[Dict[str, Any]] = None


class RunLog(BaseModel):
    id: str
    tenant_id: str
    start_ts: str
    end_ts: Optional[str] = None
    persona: Optional[str] = None
    input: str
    output: str = ""
    tool_events: List[RunEvent] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


# In-memory store: tenant_id -> run_id -> RunLog
_RUN_LOGS: Dict[str, Dict[str, RunLog]] = {}


def create_run(tenant_id: str, input_text: str, persona: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> str:
    run_id = uuid.uuid4().hex
    log = RunLog(
        id=run_id,
        tenant_id=tenant_id,
        start_ts=datetime.utcnow().isoformat(),
        persona=persona,
        input=input_text,
        metadata=metadata or {},
    )
    _RUN_LOGS.setdefault(tenant_id, {})[run_id] = log
    return run_id


def append_event(tenant_id: str, run_id: str, event: Dict[str, Any]) -> None:
    log = _RUN_LOGS.get(tenant_id, {}).get(run_id)
    if not log:
        return
    try:
        log.tool_events.append(RunEvent(**event))
    except Exception:
        # Best-effort logging
        log.tool_events.append(RunEvent(type=event.get("type", "info"), name=event.get("name")))


def append_output(tenant_id: str, run_id: str, delta: str) -> None:
    log = _RUN_LOGS.get(tenant_id, {}).get(run_id)
    if not log:
        return
    log.output += delta


def finalize_run(tenant_id: str, run_id: str, metadata: Optional[Dict[str, Any]] = None) -> Optional[RunLog]:
    log = _RUN_LOGS.get(tenant_id, {}).get(run_id)
    if not log:
        return None
    log.end_ts = datetime.utcnow().isoformat()
    if metadata:
        log.metadata.update(metadata)
    return log


def list_runs(tenant_id: str, limit: int = 20) -> List[RunLog]:
    logs = list(_RUN_LOGS.get(tenant_id, {}).values())
    logs.sort(key=lambda x: x.start_ts, reverse=True)
    return logs[:limit]


def get_run(tenant_id: str, run_id: str) -> Optional[RunLog]:
    return _RUN_LOGS.get(tenant_id, {}).get(run_id)
