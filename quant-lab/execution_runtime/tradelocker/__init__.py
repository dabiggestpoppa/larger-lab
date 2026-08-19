"""QL-EXEC-R5 — TradeLocker provider foundation.

First-class peer provider adapter for the generic Execution Runtime, NOT an
MT5-shaped wrapper. Everything in this package is provider-native truth:

- ``TradeLockerAuthProvider``  — JWT auth + refresh (singleflight), secrets via
  injected secret provider, never persisted plaintext.
- ``TradeLockerClient``        — REST client over an injectable transport
  (stdlib urllib by default; FakeTradeLocker in tests). Provider-native
  endpoints, dynamic column mapping via ``/config``, route-aware rate limiting.
- ``TradeLockerBrokerSession`` — implements the generic ``BrokerSession``
  protocol. orderId != positionId; accepted order != filled position; close
  request != closed truth.
- ``FakeTradeLocker``          — deterministic in-memory provider for offline
  tests (same injection pattern as ``brokers/fake_mt5.py``).

No live orders. No production authorization. R5 is offline/mock/demo-read
foundation only.
"""
from __future__ import annotations

from .auth import TradeLockerAuthError, TradeLockerAuthProvider
from .client import (
    TradeLockerApiError,
    TradeLockerClient,
    TradeLockerRateLimitExceeded,
)
from .config import TradeLockerConfigSnapshot, TradeLockerRateLimit
from .fake_server import FakeTradeLocker
from .ratelimit import TradeLockerRateLimiter
from .readonly import (
    DEMO_BASE_URL,
    DemoEnvironmentError,
    DemoReadOnlyAudit,
    ReadOnlyProviderWriteForbiddenError,
    ReadOnlyTradeLockerBrokerSession,
    ReadOnlyTransport,
    render_artifacts,
)
from .session import TradeLockerBrokerSession, TradeLockerProfile
from .transport import (
    AmbiguousSendError,
    HttpRequest,
    HttpResponse,
    TimeoutBeforeSendError,
    TransportError,
    UrllibTransport,
)
from .types import (
    TradeLockerAccount,
    TradeLockerInstrument,
    TradeLockerQuote,
    TradeLockerRoute,
    TradeLockerTokens,
)

__all__ = [
    "AmbiguousSendError",
    "DEMO_BASE_URL",
    "DemoEnvironmentError",
    "DemoReadOnlyAudit",
    "FakeTradeLocker",
    "HttpRequest",
    "HttpResponse",
    "TimeoutBeforeSendError",
    "TradeLockerAccount",
    "TradeLockerApiError",
    "TradeLockerAuthError",
    "TradeLockerAuthProvider",
    "TradeLockerBrokerSession",
    "TradeLockerClient",
    "TradeLockerConfigSnapshot",
    "TradeLockerInstrument",
    "TradeLockerProfile",
    "TradeLockerQuote",
    "TradeLockerRateLimit",
    "TradeLockerRateLimiter",
    "TradeLockerRateLimitExceeded",
    "TradeLockerRoute",
    "TradeLockerTokens",
    "ReadOnlyProviderWriteForbiddenError",
    "ReadOnlyTradeLockerBrokerSession",
    "ReadOnlyTransport",
    "TransportError",
    "UrllibTransport",
    "render_artifacts",
]
