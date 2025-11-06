"""Template registry and data-prep helpers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from services.compiler.main import build_ops_document


@dataclass
class Template:
    """Represents a playbook template (formerly called archetype)."""
    id: str
    name: str
    description: str
    data_inputs: List[Dict[str, str]]
    solver_hint: Optional[str] = None


REGISTRY: Dict[str, Template] = {}


def load_registry(path: Path) -> None:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    for item in data.get("items", []):
        template = Template(
            id=item["id"],
            name=item["name"],
            description=item.get("description", ""),
            data_inputs=item.get("data_inputs", []),
            solver_hint=item.get("solver_hint"),
        )
        REGISTRY[template.id] = template


def build_ops_from_template(template_id: str, goal: str, tenant_id: str, project_id: str, inputs: Dict[str, List[Dict[str, str]]]) -> dict:
    """Build ops document from a template (formerly archetype)."""
    template = REGISTRY.get(template_id)
    if not template:
        raise ValueError(f"Unknown template '{template_id}'")

    ops, _goal_pack = build_ops_document(
        goal,
        tenant_id,
        project_id,
        data_inputs=inputs,
        use_llm=False,
    )
    ops["metadata"]["template_id"] = template_id
    return ops


# Load default registry
DEFAULT_REGISTRY_PATH = Path(__file__).parent / "registry.json"
if DEFAULT_REGISTRY_PATH.exists():
    load_registry(DEFAULT_REGISTRY_PATH)
