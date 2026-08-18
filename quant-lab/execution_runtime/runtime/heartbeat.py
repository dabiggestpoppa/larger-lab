"""QL-EXEC-R3 — heartbeat + read-only telemetry snapshot.

The heartbeat is a lightweight durable liveness/state record (no secrets). The
telemetry snapshot is a read-only status object for a future read-only
dashboard; it exposes identity, authority, reconciliation, and blocker truth,
but carries NO control surface (no execution buttons here).
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Heartbeat:
    """Durable heartbeat record (lightweight, no sensitive secrets)."""

    runtime_id: str
    state: str
    desired_state: str
    observed_at: str
    broker_connected: bool = False
    last_reconciliation_state: str = ""
    last_strategy_event_id: str = ""
    blocking_reason: str = ""

    def to_dict(self) -> dict:
        return {
            "runtime_id": self.runtime_id,
            "state": self.state,
            "desired_state": self.desired_state,
            "observed_at": self.observed_at,
            "broker_connected": self.broker_connected,
            "last_reconciliation_state": self.last_reconciliation_state,
            "last_strategy_event_id": self.last_strategy_event_id,
            "blocking_reason": self.blocking_reason,
        }


@dataclass(frozen=True)
class TelemetrySnapshot:
    """Read-only status object exposed by ``GenericRuntime.telemetry()``."""

    runtime_id: str
    account_id: str
    strategy_id: str
    runtime_state: str
    desired_state: str
    broker_connected: bool = False
    identity_match: bool = False
    reconciliation_state: str = ""
    reconciliation_clean: bool = False
    new_risk_authorized: bool = False
    owned_positions_count: int = 0
    foreign_positions_count: int = 0
    unresolved_intents: int = 0
    last_heartbeat: str = ""
    last_error: str = ""
    blocking_reason: str = ""
    blockers: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict:
        return {
            "runtime_id": self.runtime_id,
            "account_id": self.account_id,
            "strategy_id": self.strategy_id,
            "runtime_state": self.runtime_state,
            "desired_state": self.desired_state,
            "broker_connected": self.broker_connected,
            "identity_match": self.identity_match,
            "reconciliation_state": self.reconciliation_state,
            "reconciliation_clean": self.reconciliation_clean,
            "new_risk_authorized": self.new_risk_authorized,
            "owned_positions_count": self.owned_positions_count,
            "foreign_positions_count": self.foreign_positions_count,
            "unresolved_intents": self.unresolved_intents,
            "last_heartbeat": self.last_heartbeat,
            "last_error": self.last_error,
            "blocking_reason": self.blocking_reason,
            "blockers": list(self.blockers),
        }
