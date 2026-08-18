"""QL-EXEC-R3 — durable execution intent + deterministic intent identity.

An ``ExecutionIntent`` is the write-ahead record persisted BEFORE any broker
submission. Its id is deterministic over immutable execution-semantic inputs
(runtime_id, account_id, strategy_id, deployment_generation, event_id,
economic-target id, instrument, side, broker quantity) — NEVER a random UUID,
NEVER wall-clock time. Re-processing the same upstream event re-derives the
same id, which is the idempotency backbone (duplicate event -> no duplicate
intended exposure).
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum


class IntentState(str, Enum):
    """Frozen R3 durable execution-intent lifecycle."""

    INTENT_CREATED = "INTENT_CREATED"       # write-ahead committed, not submitted
    INTENT_SUBMITTED = "INTENT_SUBMITTED"   # broker accepted (order id known)
    INTENT_FILLED = "INTENT_FILLED"         # owned position verified at broker
    INTENT_PARTIALLY_FILLED = "INTENT_PARTIALLY_FILLED"
    INTENT_REJECTED = "INTENT_REJECTED"     # broker rejected
    INTENT_TRANSPORT_ERROR = "INTENT_TRANSPORT_ERROR"
    INTENT_CLOSED = "INTENT_CLOSED"         # exit verified
    INTENT_ABORTED = "INTENT_ABORTED"       # flat, never reached broker


class PositionState(str, Enum):
    """Frozen R3 durable owned-position lifecycle."""

    REQUESTED = "REQUESTED"   # intent accepted; fill not yet verified
    FILLED = "FILLED"         # broker position verified (OPEN_VERIFIED)
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    CLOSE_PENDING = "CLOSE_PENDING"  # durable exit intent written, close in flight
    CLOSED = "CLOSED"         # exit verified flat
    ABORTED = "ABORTED"       # zero fill / never reached broker


def execution_intent_id(
    *,
    runtime_id: str,
    account_id: str,
    strategy_id: str,
    deployment_generation: str,
    event_id: str,
    economic_target_id: str,
    instrument: str,
    side: str,
    broker_quantity: float,
) -> str:
    """Deterministic, collision-resistant, versioned execution-intent id."""
    canonical = {
        "v": "EI1",
        "runtime_id": runtime_id,
        "account_id": account_id,
        "strategy_id": strategy_id,
        "deployment_generation": deployment_generation,
        "event_id": event_id,
        "economic_target_id": economic_target_id,
        "instrument": instrument,
        "side": side,
        "broker_quantity": str(broker_quantity),
    }
    payload = json.dumps(canonical, sort_keys=True, separators=(",", ":"))
    return "EI1_" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


@dataclass(frozen=True)
class ExecutionIntent:
    """Durable record of intended exposure (write-ahead before broker call)."""

    intent_id: str
    runtime_id: str
    account_id: str
    strategy_id: str
    deployment_generation: str
    event_id: str
    economic_target_id: str
    instrument: str
    broker_symbol: str
    side: str  # BUY / SELL
    broker_quantity: float
    logical_ownership_id: str
    ownership_tag: str
    broker_magic: int
    state: IntentState = IntentState.INTENT_CREATED
    broker_order_id: str = ""
    broker_position_id: str = ""
    filled_quantity: float = 0.0
    fill_price: float | None = None
    reason: str = ""
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "intent_id": self.intent_id,
            "runtime_id": self.runtime_id,
            "account_id": self.account_id,
            "strategy_id": self.strategy_id,
            "deployment_generation": self.deployment_generation,
            "event_id": self.event_id,
            "economic_target_id": self.economic_target_id,
            "instrument": self.instrument,
            "broker_symbol": self.broker_symbol,
            "side": self.side,
            "broker_quantity": self.broker_quantity,
            "logical_ownership_id": self.logical_ownership_id,
            "ownership_tag": self.ownership_tag,
            "broker_magic": self.broker_magic,
            "state": self.state.value,
            "broker_order_id": self.broker_order_id,
            "broker_position_id": self.broker_position_id,
            "filled_quantity": self.filled_quantity,
            "fill_price": self.fill_price,
            "reason": self.reason,
            "metadata": self.metadata,
        }
