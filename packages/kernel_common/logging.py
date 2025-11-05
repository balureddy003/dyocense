"""Logging helpers that also ensure environment variables (.env) are loaded."""

import logging
from typing import Optional

try:  # pragma: no cover - optional dependency
    from dotenv import load_dotenv

    # Ensure .env variables override any previously set environment values in dev shells
    # This avoids stale values (e.g., switching Keycloak URL) during reloads
    load_dotenv(override=True)
except ImportError:  # pragma: no cover
    pass


def configure_logging(name: str, level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s %(levelname)s [%(name)s] %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False
    return logger


__all__ = ["configure_logging"]
