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
    TRADELOCKER_FUTURE = "TRADELOCKER_FUTURE"


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
