"""QL-EXEC-R1 — domain enums.

Pure domain constants. No broker imports, no strategy math.
"""
from __future__ import annotations

from enum import Enum


class ExecutionTransport(str, Enum):
    """Execution transport/platform. NOT a broker company."""

    MT5 = "MT5"
    SIM = "SIM"
    REPLAY = "REPLAY"
    TRADELOCKER = "TRADELOCKER"
    TRADELOCKER_FUTURE = "TRADELOCKER_FUTURE"


class AuthenticationMode(str, Enum):
    """How a session authenticates. Secret requirement depends on THIS,

    never on transport type alone (R1.1 repair: authentication is separated
    from secret possession).
    """

    NONE = "NONE"
    EXTERNAL_SESSION = "EXTERNAL_SESSION"
    RUNTIME_CREDENTIALS = "RUNTIME_CREDENTIALS"


class AccountRole(str, Enum):
    """Frozen R0 account roles."""

    EXCLUSIVE_STRATEGY_MASTER = "EXCLUSIVE_STRATEGY_MASTER"
    PORTFOLIO_MASTER = "PORTFOLIO_MASTER"
    FOLLOWER = "FOLLOWER"
    MIRROR = "MIRROR"


class ExecutionMode(str, Enum):
    """Execution mode. LIVE in schema is NOT authorization."""

    SHADOW = "SHADOW"
    SIM = "SIM"
    DEMO = "DEMO"
    LIVE = "LIVE"


class Environment(str, Enum):
    """Broker-reported environment."""

    DEMO = "DEMO"
    CONTEST = "CONTEST"
    REAL = "REAL"
    SIM = "SIM"
    REPLAY = "REPLAY"
    UNKNOWN = "UNKNOWN"


class HedgingNetting(str, Enum):
    """Position-accounting model."""

    HEDGING = "HEDGING"
    NETTING = "NETTING"
    UNKNOWN = "UNKNOWN"


class ReservationState(str, Enum):
    """Durable heat reservation lifecycle (R0 frozen set)."""

    PROPOSED = "PROPOSED"
    ADMITTED_RESERVED = "ADMITTED_RESERVED"
    ORDER_SUBMITTED = "ORDER_SUBMITTED"
    FILLED_ACTIVE = "FILLED_ACTIVE"
    EXIT_PENDING = "EXIT_PENDING"
    CLOSED_RELEASED = "CLOSED_RELEASED"
    REJECTED = "REJECTED"
    RELEASED_ABORTED = "RELEASED_ABORTED"
    RESERVATION_UNRESOLVED = "RESERVATION_UNRESOLVED"


class CapabilityState(str, Enum):
    """Tri-state capability. UNKNOWN is NOT FALSE."""

    SUPPORTED = "SUPPORTED"
    UNSUPPORTED = "UNSUPPORTED"
    UNKNOWN = "UNKNOWN"


class DesiredState(str, Enum):
    """Per-runtime desired state."""

    RUNNING = "RUNNING"
    STOPPED_BY_USER = "STOPPED_BY_USER"


class MachineProfile(str, Enum):
    """Where a runtime process runs (not its identity)."""

    LOCAL_WINDOWS = "local_windows"
    WINDOWS_VPS = "windows_vps"


class OwnershipMode(str, Enum):
    """Portfolio group ownership topology."""

    SINGLE_RUNTIME_MULTI_ADAPTER = "SINGLE_RUNTIME_MULTI_ADAPTER"
    MULTI_PRODUCER_SINGLE_ROUTER = "MULTI_PRODUCER_SINGLE_ROUTER"


class MarketStatus(str, Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    UNKNOWN = "UNKNOWN"


class ClockStatus(str, Enum):
    """Broker/server clock health/status. Value is observed/calibrated."""

    CALIBRATED = "CALIBRATED"
    UNCALIBRATED = "UNCALIBRATED"
    STALE = "STALE"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"


class RuntimeHealth(str, Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    OFFLINE = "OFFLINE"
    BLOCKED = "BLOCKED"
    STOPPED = "STOPPED"
    UNKNOWN = "UNKNOWN"


class SecretKind(str, Enum):
    """Secret reference kinds. Never a credential value."""

    NONE = "NONE"
    ENV_VAR = "ENV_VAR"
    OS_KEYRING = "OS_KEYRING"
    SECRET_STORE = "SECRET_STORE"


class RoutingDecision(str, Enum):
    ROUTED = "ROUTED"
    REJECTED = "REJECTED"


class CompatibilityStatus(str, Enum):
    SUPPORTED = "SUPPORTED"
    SUPPORTABLE_WITH_WORK = "SUPPORTABLE_WITH_WORK"
    BLOCKED_PENDING_VIRTUAL_LEDGER = "BLOCKED_PENDING_VIRTUAL_LEDGER"
    FAIL_CLOSED = "FAIL_CLOSED"


class CapitalDecisionKind(str, Enum):
    ADMITTED = "ADMITTED"
    REJECTED = "REJECTED"


class OrderType(str, Enum):
    """Broker-neutral order type. R2 supports only what execution needs;

    R5 adds STOP as the provider-neutral stop-order concept (TradeLocker
    ``type=stop`` and the MT5 buy/sell stop variants share this semantic).
    """

    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"


class OrderSide(str, Enum):
    """Broker-neutral market side."""

    BUY = "BUY"
    SELL = "SELL"


class FillPolicy(str, Enum):
    """Broker-neutral fill semantics. MT5 enum integers never leak here."""

    FILL_OR_KILL = "FILL_OR_KILL"
    IMMEDIATE_OR_CANCEL = "IMMEDIATE_OR_CANCEL"
    RETURN_OR_PARTIAL = "RETURN_OR_PARTIAL"
    BROKER_DEFAULT = "BROKER_DEFAULT"
    UNKNOWN = "UNKNOWN"


class QuantityUnit(str, Enum):
    """Unit of OrderIntent.volume at the BrokerSession boundary."""

    LOT = "LOT"
    UNKNOWN = "UNKNOWN"


class SlippageUnit(str, Enum):
    """Unit of a slippage/deviation constraint. Never a naked number."""

    PRICE = "PRICE"
    POINTS = "POINTS"
    UNKNOWN = "UNKNOWN"


class BrokerErrorCategory(str, Enum):
    """Normalized broker result categories (no raw MT5 exceptions leak).

    ``NONE`` is the truthful success state: a result with ``ok == True``
    always carries ``NONE`` (never an error category).
    """

    NONE = "NONE"
    NOT_CONNECTED = "NOT_CONNECTED"
    AUTH_FAILED = "AUTH_FAILED"
    IDENTITY_UNAVAILABLE = "IDENTITY_UNAVAILABLE"
    SYMBOL_UNAVAILABLE = "SYMBOL_UNAVAILABLE"
    CLOCK_UNCALIBRATED = "CLOCK_UNCALIBRATED"
    INVALID_REQUEST = "INVALID_REQUEST"
    ORDER_CHECK_FAILED = "ORDER_CHECK_FAILED"
    ORDER_REJECTED = "ORDER_REJECTED"
    TRANSPORT_ERROR = "TRANSPORT_ERROR"
    UNSUPPORTED_CAPABILITY = "UNSUPPORTED_CAPABILITY"
    UNKNOWN_BROKER_ERROR = "UNKNOWN_BROKER_ERROR"
