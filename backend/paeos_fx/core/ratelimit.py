"""Fixed-window rate limiter (Phase 12) — additive hardening.

A small, deterministic in-memory fixed-window counter. It is a defense-in-depth
throttle, not a security boundary: it never touches authentication or tenant
isolation, and it is disabled unless explicitly enabled in settings. Production
deployments should front this with a distributed limiter (e.g. Redis); see
``docs/PRODUCTION_HARDENING.md``.
"""

from __future__ import annotations

import threading


class FixedWindowRateLimiter:
    """Allow at most ``limit`` hits per ``window_seconds`` per key."""

    def __init__(self, limit: int, window_seconds: int = 60):
        if limit <= 0:
            raise ValueError("limit must be positive.")
        if window_seconds <= 0:
            raise ValueError("window_seconds must be positive.")
        self.limit = limit
        self.window_seconds = window_seconds
        self._counts: dict[tuple[str, int], int] = {}
        self._lock = threading.Lock()

    def allow(self, key: str, now: float) -> bool:
        """Return True if a hit for ``key`` is within the limit for its window."""
        window = int(now // self.window_seconds)
        bucket = (key, window)
        with self._lock:
            # Drop stale windows for this key to bound memory.
            for k in [k for k in self._counts if k[0] == key and k[1] != window]:
                del self._counts[k]
            current = self._counts.get(bucket, 0)
            if current >= self.limit:
                return False
            self._counts[bucket] = current + 1
            return True
