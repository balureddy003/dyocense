"""Archetype registry and data-prep helpers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from services.compiler.main import build_ops_document


@dataclass
class Archetype:
    id: str
    name: str
    description: str
    data_inputs: List[Dict[str, str]]
    solver_hint: Optional[str] = None


REGISTRY: Dict[str, Archetype] = {}


def load_registry(path: Path) -> None:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    for item in data.get("items", []):
        archetype = Archetype(
            id=item["id"],
            name=item["name"],
            description=item.get("description", ""),
            data_inputs=item.get("data_inputs", []),
            solver_hint=item.get("solver_hint"),
        )
        REGISTRY[archetype.id] = archetype


def build_ops_from_archetype(archetype_id: str, goal: str, tenant_id: str, project_id: str, inputs: Dict[str, List[Dict[str, str]]]) -> dict:
    archetype = REGISTRY.get(archetype_id)
    if not archetype:
        raise ValueError(f"Unknown archetype '{archetype_id}'")

    ops = build_ops_document(
        goal,
        tenant_id,
        project_id,
        data_inputs=inputs,
        use_llm=False,
    )
    ops["metadata"]["archetype_id"] = archetype_id
    return ops


# Load default registry
DEFAULT_REGISTRY_PATH = Path(__file__).parent / "registry.json"
if DEFAULT_REGISTRY_PATH.exists():
    load_registry(DEFAULT_REGISTRY_PATH)
