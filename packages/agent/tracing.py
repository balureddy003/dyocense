from __future__ import annotations

import json
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict

TRACE_DIR = Path("artifacts/plans")

ENABLE_TRACING = os.getenv("PLAN_ENABLE_TRACING", "1").lower() in ("1","true","yes")


def trace_event(plan_id: str, event: str, data: Dict[str, Any]) -> None:
    if not ENABLE_TRACING:
        return
    plan_dir = TRACE_DIR / plan_id
    plan_dir.mkdir(parents=True, exist_ok=True)
    line = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": event,
        **data,
    }
    log_path = plan_dir / "trace.jsonl"
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(line) + "\n")
