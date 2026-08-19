"""QL-EXEC-R5 — provider-aware rate limiter.

Enforces global + per-route limits from ``/config`` ``rateLimits`` truth,
honors ``Retry-After`` on 429, and applies bounded exponential backoff.
Never retries infinitely, and order POSTs are additionally protected by the
client's reconcile-before-retry policy (this limiter only gates WHEN a request
may be attempted, it never decides retry safety).
"""
from __future__ import annotations

import threading
import time
from typing import Callable, Optional

from .types import TradeLockerRateLimit

# Hard cap on backoff so a wedged route never stalls the session forever.
MAX_BACKOFF_SECONDS = 60.0


class TradeLockerRateLimiter:
    def __init__(
        self,
        limits: Optional[dict[str, TradeLockerRateLimit]] = None,
        clock: Optional[Callable[[], float]] = None,
    ) -> None:
        self._limits: dict[str, TradeLockerRateLimit] = dict(limits or {})
        self._hits: dict[str, list[float]] = {}
        self._retry_after_until: dict[str, float] = {}
        self._failure_backoff: dict[str, float] = {}
        self._lock = threading.Lock()
        self._clock = clock or time.time

    # ── configuration ────────────────────────────────────────────────────

    def update_from_config(self, rate_limits: tuple) -> None:
        """Adopt provider truth from ``/config`` ``rateLimits`` (idempotent)."""
        with self._lock:
            for rl in rate_limits:
                if isinstance(rl, TradeLockerRateLimit):
                    self._limits[rl.route_name] = rl

    def route_limits(self) -> dict:
        with self._lock:
            return dict(self._limits)

    # ── admission ────────────────────────────────────────────────────────

    def wait_seconds(self, route: str, now: Optional[float] = None) -> float:
        """Seconds the caller must wait before this route is allowed.

        0.0 means allowed now. The caller sleeps and calls again (bounded by
        the client's retry budget) — the limiter never blocks threads itself.
        """
        now = now if now is not None else self._clock()
        with self._lock:
            until = self._retry_after_until.get(route, 0.0)
            if until > now:
                return until - now
            limit = self._limits.get(route)
            if limit is None or limit.limit <= 0:
                backoff = self._failure_backoff.get(route, 0.0)
                return backoff if backoff > now else 0.0
            window = max(float(limit.seconds), 1.0)
            hits = [h for h in self._hits.get(route, []) if h > now - window]
            if len(hits) >= limit.limit:
                return (hits[0] + window) - now
            return 0.0

    def consume(self, route: str, now: Optional[float] = None) -> None:
        """Record a request attempt against the route window."""
        now = now if now is not None else self._clock()
        with self._lock:
            self._hits.setdefault(route, []).append(now)

    def note_retry_after(self, route: str, seconds: float, now: Optional[float] = None) -> None:
        """Provider asked us to wait (429 Retry-After)."""
        now = now if now is not None else self._clock()
        with self._lock:
            self._retry_after_until[route] = max(
                self._retry_after_until.get(route, 0.0), now + max(seconds, 0.0)
            )

    def note_failure(self, route: str, now: Optional[float] = None) -> None:
        """Bounded exponential backoff after a transport/5xx failure."""
        now = now if now is not None else self._clock()
        with self._lock:
            current = self._failure_backoff.get(route, 0.0)
            delay = 1.0 if current <= now else (current - now) * 2.0
            self._failure_backoff[route] = now + min(delay, MAX_BACKOFF_SECONDS)

    def reset_failure(self, route: str) -> None:
        with self._lock:
            self._failure_backoff.pop(route, None)
