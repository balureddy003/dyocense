"""Logging helpers that ensure environment variables (.env) are loaded and services share the same console output."""

from __future__ import annotations

import logging
import os
from typing import Any, Iterable, Mapping

try:  # pragma: no cover - optional dependency
    from dotenv import load_dotenv

    # Ensure .env overrides shell env values so developers can tweak during reloads.
    load_dotenv(override=True)
except ImportError:  # pragma: no cover
    pass


LOG_DEFAULT_LEVEL = logging.INFO
LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
LOG_DATEFMT = "%Y-%m-%dT%H:%M:%S"


def _parse_level(value: int | str | None) -> int:
    if value is None:
        return LOG_DEFAULT_LEVEL
    if isinstance(value, int):
        return value
    normalized = value.strip().upper()
    if normalized.isdigit():
        return int(normalized)
    return getattr(logging, normalized, LOG_DEFAULT_LEVEL)


def _effective_level(overrides: Iterable[int | str | None] | None = None) -> int:
    if overrides is None:
        overrides = ()
    for override in overrides:
        if override is not None:
            return _parse_level(override)
    return LOG_DEFAULT_LEVEL


def configure_logging(name: str, level: int | str | None = None) -> logging.Logger:
    """Configure a shared console handler and return a named logger."""
    env_level = os.getenv("LOG_LEVEL")
    resolved = _effective_level((level, env_level))

    root = logging.getLogger()
    if not root.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=LOG_DATEFMT))
        root.addHandler(handler)
    root.setLevel(resolved)

    logger = logging.getLogger(name)
    logger.setLevel(resolved)
    return logger


def log_flow_event(
    logger: logging.Logger,
    stage: str,
    source: str,
    target: str,
    message: str,
    metadata: Mapping[str, Any] | None = None,
    level: int | str | None = None,
) -> None:
    """Log a standardized flow transition between connected components."""
    resolved_level = _effective_level((level, None))
    prefix = f"[flow:{stage}] {source} -> {target}"
    meta_parts: list[str] = []
    if metadata:
        for key, value in metadata.items():
            meta_parts.append(f"{key}={value}")
    meta_str = ""
    if meta_parts:
        meta_str = " | " + ", ".join(meta_parts)
    logger.log(resolved_level, "%s %s%s", prefix, message, meta_str)


__all__ = ["configure_logging", "log_flow_event"]
