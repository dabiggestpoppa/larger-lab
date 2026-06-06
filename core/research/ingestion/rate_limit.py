"""
L1.8 — Token bucket rate limiter + exponential backoff retry.

One RateLimit instance per source. Thread-safe via asyncio.Lock.
Used by all source clients (OpenAlex, arXiv, S2) before every API call.

Usage:
    limiter = RateLimit(per_second=10, max_retries=3)
    async with limiter:
        response = await session.get(url)
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class RateLimit:
    """Token bucket rate limiter with exponential backoff on 429/5xx."""

    per_second: float = 10.0
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    _tokens: float = field(init=False)
    _last_refill: float = field(init=False)
    _lock: asyncio.Lock = field(init=False, default_factory=asyncio.Lock)

    def __post_init__(self):
        self._tokens = self.per_second
        self._last_refill = time.monotonic()

    async def acquire(self) -> None:
        """Block until a token is available, then consume it."""
        async with self._lock:
            self._refill()
            while self._tokens < 1.0:
                wait = (1.0 - self._tokens) / self.per_second
                logger.debug("rate_limit: waiting %.2fs for token", wait)
                await asyncio.sleep(wait)
                self._refill()
            self._tokens -= 1.0

    async def __aenter__(self):
        await self.acquire()
        return self

    async def __aexit__(self, *exc):
        return False

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self.per_second, self._tokens + elapsed * self.per_second)
        self._last_refill = now

    @property
    def available_tokens(self) -> float:
        self._refill()
        return self._tokens

    def backoff_delay(self, attempt: int, retry_after: Optional[float] = None) -> float:
        """Compute delay before next retry. Honors Retry-After header if given."""
        if retry_after is not None:
            return min(retry_after, self.max_delay)
        delay = self.base_delay * (2 ** attempt)
        return min(delay, self.max_delay)

    async def execute_with_retry(self, coro_factory, *args, **kwargs):
        """
        Execute an async callable with rate limiting + retry.

        coro_factory: callable that returns a coroutine (rebuilt each retry)
        Returns: result of coro_factory(*args, **kwargs)
        Raises: last exception if all retries exhausted
        """
        last_exc: Optional[Exception] = None
        for attempt in range(self.max_retries + 1):
            await self.acquire()
            try:
                return await coro_factory(*args, **kwargs)
            except Exception as exc:
                last_exc = exc
                status = getattr(exc, "status", None)
                if status is not None and 400 <= status < 500 and status != 429:
                    # Non-retryable client error (except 429)
                    raise
                if attempt < self.max_retries:
                    delay = self.backoff_delay(attempt)
                    logger.warning(
                        "rate_limit: attempt %d/%d failed (%s), retrying in %.1fs",
                        attempt + 1, self.max_retries + 1, exc, delay,
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        "rate_limit: all %d retries exhausted", self.max_retries + 1
                    )
        raise last_exc
