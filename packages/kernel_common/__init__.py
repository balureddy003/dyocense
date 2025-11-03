"""Shared utilities for Dyocense services (Phase 1)."""

from importlib.resources import files
from typing import Any, Dict


def load_schema(name: str) -> Dict[str, Any]:
    """
    Load a JSON schema from the contracts package.

    Args:
        name: Filename within packages/contracts/schemas/.
    """
    schema_path = files("packages.contracts.schemas") / name
    if not schema_path.is_file():
        raise FileNotFoundError(f"Schema '{name}' not found in contracts package.")
    import json

    with schema_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


__all__ = ["load_schema"]
