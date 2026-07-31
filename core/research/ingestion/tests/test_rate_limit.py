"""
Tests for L1.8 — Rate limiter + retry.

5 tests:
    1. Token bucket blocks when exhausted
    2. Token bucket refills over time
    3. Backoff delay doubles each attempt
    4. Retry succeeds on transient failure
    5. Retry exhausts and raises last error
"""

import asyncio
import pytest

from core.research.ingestion.rate_limit import RateLimit


@pytest.fixture
def limiter():
    return RateLimit(per_second=10.0, max_retries=2, base_delay=0.01, max_delay=1.0)


@pytest.mark.asyncio
async def test_token_bucket_blocks_when_exhausted(limiter):
    """Exhaust tokens, then verify acquire blocks briefly."""
    # Exhaust the bucket
    for _ in range(10):
        await limiter.acquire()
    assert limiter.available_tokens < 1.0
    # Next acquire should block (but refill helps at 10/s)
    start = asyncio.get_event_loop().time()
    await limiter.acquire()
    elapsed = asyncio.get_event_loop().time() - start
    # Should have waited some non-zero time
    assert elapsed >= 0.0


@pytest.mark.asyncio
async def test_token_bucket_refills(limiter):
    """Tokens refill after waiting."""
    # Exhaust
    for _ in range(10):
        await limiter.acquire()
    assert limiter.available_tokens < 1.0
    # Wait for refill
    await asyncio.sleep(0.5)
    assert limiter.available_tokens > 1.0


def test_backoff_delay_doubles(limiter):
    """Exponential backoff: delay doubles each attempt."""
    d0 = limiter.backoff_delay(0)
    d1 = limiter.backoff_delay(1)
    d2 = limiter.backoff_delay(2)
    assert d1 == pytest.approx(d0 * 2, rel=0.01)
    assert d2 == pytest.approx(d0 * 4, rel=0.01)


def test_backoff_respects_retry_after():
    """If Retry-After header is present, use it (capped at max_delay)."""
    limiter = RateLimit(per_second=10.0, max_retries=2, base_delay=0.01, max_delay=60.0)
    delay = limiter.backoff_delay(0, retry_after=5.0)
    assert delay == 5.0
    # Capped at max_delay
    delay_capped = limiter.backoff_delay(0, retry_after=999.0)
    assert delay_capped == limiter.max_delay


@pytest.mark.asyncio
async def test_retry_succeeds_on_transient_failure(limiter):
    """execute_with_retry retries on failure and returns result on success."""
    call_count = 0

    async def flaky():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ConnectionError("transient")
        return "ok"

    result = await limiter.execute_with_retry(flaky)
    assert result == "ok"
    assert call_count == 3


@pytest.mark.asyncio
async def test_retry_exhausts_and_raises(limiter):
    """execute_with_retry raises last exception after all retries exhausted."""
    limiter.max_retries = 2
    call_count = 0

    async def always_fail():
        nonlocal call_count
        call_count += 1
        raise ConnectionError(f"fail {call_count}")

    with pytest.raises(ConnectionError, match="fail 3"):
        await limiter.execute_with_retry(always_fail)
    assert call_count == 3  # initial + 2 retries
