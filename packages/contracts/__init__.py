"""Contracts package: canonical schemas and API definitions."""

from importlib.resources import files


def schema_path(name: str):
    """Return importlib resources path for a schema file."""
    return files("packages.contracts.schemas") / name


__all__ = ["schema_path"]
