"""Lightweight OpenTelemetry helpers (optional dependency)."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Dict, Iterator, Optional

try:  # pragma: no cover - optional
    from opentelemetry import trace

    _TRACER = trace.get_tracer("dyocense")
except Exception:  # pragma: no cover - dependency may not exist
    _TRACER = None


@contextmanager
def start_span(name: str, attributes: Optional[Dict[str, Any]] = None) -> Iterator[Any]:
    """Context manager that starts an OpenTelemetry span when tracing is available."""

    if _TRACER is None:
        yield None
        return

    with _TRACER.start_as_current_span(name) as span:
        if attributes:
            for key, value in attributes.items():
                try:
                    span.set_attribute(key, value)
                except Exception:
                    continue
        yield span


def set_span_attributes(span: Any, attributes: Dict[str, Any]) -> None:
    if span is None:
        return
    for key, value in attributes.items():
        try:
            span.set_attribute(key, value)
        except Exception:
            continue


__all__ = ["start_span", "set_span_attributes"]
