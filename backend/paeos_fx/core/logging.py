"""Structured logging + observability hooks (section W).

Uses structlog to emit JSON logs enriched with correlation and tenant ids.
Metrics and tracing are exposed as thin interfaces so concrete backends
(Prometheus, OpenTelemetry) can be wired in later phases without code churn.
"""

from __future__ import annotations

import logging
from collections.abc import MutableMapping
from typing import Any, Protocol

import structlog

from paeos_fx.core.context import current_context


def _add_context(
    _logger: Any, _method: str, event_dict: MutableMapping[str, Any]
) -> MutableMapping[str, Any]:
    """structlog processor: enrich every event with context ids."""
    ctx = current_context()
    event_dict.setdefault("correlation_id", ctx.correlation_id)
    if ctx.tenant_id is not None:
        event_dict.setdefault("tenant_id", str(ctx.tenant_id))
    if ctx.user_id is not None:
        event_dict.setdefault("user_id", str(ctx.user_id))
    return event_dict


def configure_logging(level: str = "INFO", json_output: bool = True) -> None:
    """Configure structlog once at startup."""
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO))
    renderer = (
        structlog.processors.JSONRenderer()
        if json_output
        else structlog.dev.ConsoleRenderer()
    )
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            _add_context,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, level.upper(), logging.INFO)
        ),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None):
    return structlog.get_logger(name)


class MetricsSink(Protocol):
    """Minimum stable metrics interface (Prometheus adapter added later)."""

    def increment(self, name: str, value: float = 1.0, **labels: str) -> None: ...
    def observe(self, name: str, value: float, **labels: str) -> None: ...


class NullMetricsSink:
    """No-op metrics sink used until an exporter is configured."""

    def increment(self, name: str, value: float = 1.0, **labels: str) -> None:
        return None

    def observe(self, name: str, value: float, **labels: str) -> None:
        return None


_metrics: MetricsSink = NullMetricsSink()


def get_metrics() -> MetricsSink:
    return _metrics


def set_metrics(sink: MetricsSink) -> None:
    global _metrics
    _metrics = sink
