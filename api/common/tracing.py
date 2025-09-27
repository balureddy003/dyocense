"""Tracing helpers shared across services."""
from __future__ import annotations

import contextlib
from typing import Any, Dict, Iterator, Optional

try:  # pragma: no cover - optional dependency
    from opentelemetry import trace
except ImportError:  # pragma: no cover - best-effort fallback
    trace = None  # type: ignore


_TRACER_NAME = "dyocense.services"


@contextlib.contextmanager
def start_span(name: str, attributes: Optional[Dict[str, Any]] = None) -> Iterator[None]:
    """Start an OpenTelemetry span if OTEL is configured."""

    if trace is None:
        yield
        return
    tracer = trace.get_tracer(_TRACER_NAME)
    with tracer.start_as_current_span(name) as span:
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)
        yield
