"""Background jobs framework (section L).

A thin, dependency-light Celery integration. Celery/Redis are optional extras;
this module degrades gracefully (a no-op app) when they are not installed, so the
foundation and its tests do not hard-depend on a broker. Tasks are tenant-aware:
the tenant id travels in the task headers and rebinds the execution context.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from typing import Any

from paeos_fx.core.config import get_settings
from paeos_fx.core.context import ExecutionContext, set_context


def celery_available() -> bool:
    """Whether the optional Celery extra (see pyproject [jobs]) is installed."""
    try:
        import celery  # noqa: F401
    except Exception:  # pragma: no cover - exercised only without the extra
        return False
    return True


def build_celery_app(name: str = "paeos") -> Any:
    """Create a configured Celery app, or raise if the extra is not installed."""
    try:
        from celery import Celery
    except Exception as exc:  # pragma: no cover - exercised only without the extra
        raise RuntimeError(
            "Celery is not installed. Install the 'jobs' extra to enable "
            "background processing."
        ) from exc
    settings = get_settings()
    app = Celery(name, broker=settings.redis_url, backend=settings.redis_url)
    app.conf.update(
        task_acks_late=True,
        task_reject_on_worker_lost=True,
        worker_prefetch_multiplier=1,
    )
    return app


def with_tenant_context(
    func: Callable[..., Any], tenant_id: uuid.UUID
) -> Callable[..., Any]:
    """Wrap a callable so it runs bound to a tenant execution context."""

    def _runner(*args: Any, **kwargs: Any) -> Any:
        token = set_context(ExecutionContext().with_tenant(tenant_id))
        try:
            return func(*args, **kwargs)
        finally:
            from paeos_fx.core.context import reset_context

            reset_context(token)

    return _runner
