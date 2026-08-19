"""
TB-R6.3 — WEEKLY SIGNAL-COMPLETENESS AUDITOR · CORE
===================================================

Shared frozen constants, enums, and deterministic id helpers for the
read-only weekly auditor.

AUTHORITY: READ ONLY · DIAGNOSTIC ONLY · NO EXECUTION · NO CAPITAL ·
NO STRATEGY-MODIFICATION.

The strategy truth is imported from the sealed `engines.tb_forward_config`
module (the frozen PRIMARY / CONTROL contract). This module adds ONLY the
auditor's own frozen conventions:

  * outcome classes (exactly one per expected/live event)
  * decision types (ENTRY / EXIT)
  * deterministic expected_event_id derivation
  * canonical bar-key normalization (UTC minute precision)
  * frozen data-parity numeric tolerance

Nothing in this module (or the whole `audit` package) may influence
execution: it contains no broker calls, no runtime DB writes, and no
strategy parameter.
"""

from __future__ import annotations

import hashlib
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import List, Optional

# repo bootstrap: quant-lab on sys.path (engines live under it)
_QL = Path(__file__).resolve().parent.parent
for _p in (str(_QL), str(_QL / "engines"), str(_QL / "audit")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ─── Canonical frozen strategy truth (single source: sealed config) ──────
# Imported lazily-safe: the engines package is on sys.path at runtime.
try:
    from engines.tb_forward_config import (  # noqa: F401
        PRIMARY_CONFIG,
        CONTROL_CONFIG,
        LOOKBACK,
        STOP_Z,
        LONDON_START_H_EST,
        LONDON_END_H_EST,
        HARD_EXIT_H_EST,
        MIN_MINUTES_TO_EXIT,
        CANONICAL_RESEARCH_TIME_SEMANTICS,
    )
    from engines.triangular_basis_live import (  # noqa: F401
        BasketDecision,
    )
    _CONFIG_LOADED = True
except Exception:  # pragma: no cover - import fallback for partial envs
    _CONFIG_LOADED = False
    PRIMARY_CONFIG = CONTROL_CONFIG = None
    LOOKBACK = STOP_Z = 200  # placeholder; real import is authoritative


PRIMARY_STRATEGY_ID = "TB-FWD-V1"           # matches worker PRIMARY_STRATEGY_ID
CONTROL_STRATEGY_ID = "TB-FROZEN-CONTROL"   # matches worker CONTROL_STRATEGY_ID
STRATEGY_IDS = (PRIMARY_STRATEGY_ID, CONTROL_STRATEGY_ID)


class OutcomeClass(str, Enum):
    """Every expected/live event resolves to EXACTLY ONE of these."""
    MATCHED_TAKEN = "MATCHED_TAKEN"
    MATCHED_SHADOW = "MATCHED_SHADOW"
    VALID_RUNTIME_BLOCK = "VALID_RUNTIME_BLOCK"
    MISSED_SIGNAL = "MISSED_SIGNAL"
    RUNTIME_ONLY_SIGNAL = "RUNTIME_ONLY_SIGNAL"
    DATA_DIVERGENCE = "DATA_DIVERGENCE"
    NO_SIGNAL = "NO_SIGNAL"


class DecisionType(str, Enum):
    ENTRY = "ENTRY"
    EXIT = "EXIT"


class ParityStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"


# ─── Frozen data-parity numeric tolerance ────────────────────────────────
# Material divergence if abs(close_diff) exceeds max(ABS_TOL, REL_TOL * price)
# on ANY leg at a disputed bar key. Frozen; do not tune per audit.
PARITY_ABS_TOL = 0.0005        # 5 pips in the 0.0001 pip convention
PARITY_REL_TOL = 1e-4


# ─── Bar-key normalization ───────────────────────────────────────────────
def bar_key_minute(ts) -> str:
    """Canonical bar key: UTC minute precision, `YYYY-MM-DD HH:MM`.

    Live runtime writes `str(signal_bar_close_time)` (UTC-aware, possibly
    with microseconds). Replay bars are naive UTC broker open times. Both
    sides normalize to this form for exact matching.
    """
    if ts is None:
        return ""
    if isinstance(ts, str):
        ts = ts.strip()
        # tolerate "+00:00"/"Z" suffixes from str(aware datetime)
        if ts.endswith("Z"):
            ts = ts[:-1] + "+00:00"
        ts = datetime.fromisoformat(ts)
        if ts.tzinfo is not None:
            ts = ts.astimezone(timezone.utc)
    elif isinstance(ts, datetime):
        if ts.tzinfo is not None:
            ts = ts.astimezone(timezone.utc)
    else:  # pandas Timestamp etc.
        ts = datetime.fromtimestamp(float(ts) / 1e9, tz=timezone.utc)
    return ts.strftime("%Y-%m-%d %H:%M")


def direction_from_z(z: float) -> str:
    """Canonical direction convention: z>0 -> SHORT, z<0 -> LONG."""
    if z is None:
        return "FLAT"
    return "SHORT" if z > 0 else ("LONG" if z < 0 else "FLAT")


# ─── Deterministic expected event ids ────────────────────────────────────
def expected_event_id(strategy_id: str, bar_key: str, direction: str,
                      decision_type: str, generation: int) -> str:
    """Deterministic, content-addressed id for an expected signal.

    Based on: strategy, bar key, direction, generation (per spec). Identical
    inputs ALWAYS yield the identical id — replay-stable across runs.
    """
    raw = "|".join([strategy_id, bar_key, direction, decision_type,
                    str(generation)])
    return "EXP-" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


# ─── Domain records ──────────────────────────────────────────────────────
@dataclass
class ExpectedEvent:
    """One deterministic canonical expectation from the independent replay."""
    event_id: str
    strategy_id: str
    variant: str                 # "TB-B" model id
    decision_type: DecisionType
    bar_key: str
    timestamp_utc: str
    direction: str
    basis: float
    z: float
    generation: int              # 1-based entry ordinal per strategy/window
    basket_id: str = ""
    entry_eligible: bool = False
    entry_reason: str = ""
    exit_eligible: bool = False
    exit_reason: str = ""
    basket_state: str = "FLAT"
    block_reason: str = ""
    data_ok: bool = True         # whether the bar passed completeness gates

    def to_row(self) -> dict:
        return {
            "event_id": self.event_id,
            "strategy": self.strategy_id,
            "variant": self.variant,
            "decision_type": self.decision_type.value,
            "bar_key": self.bar_key,
            "timestamp_utc": self.timestamp_utc,
            "direction": self.direction,
            "basis": round(self.basis, 8),
            "z": round(self.z, 6),
            "generation": self.generation,
            "basket_id": self.basket_id,
            "entry_eligible": self.entry_eligible,
            "entry_reason": self.entry_reason,
            "exit_eligible": self.exit_eligible,
            "exit_reason": self.exit_reason,
            "basket_state": self.basket_state,
            "block_reason": self.block_reason,
        }


@dataclass
class LiveEvent:
    """One runtime artifact read READ-ONLY from the ledger."""
    seq: int
    event_type: str
    ts_utc: str
    strategy_id: str
    basket_id: str
    dedup_key: str
    payload: dict = field(default_factory=dict)
    reason: str = ""
    # derived audit fields
    bar_key: str = ""
    direction: str = "FLAT"
    z: float = 0.0

    def to_row(self) -> dict:
        return {
            "seq": self.seq,
            "event_type": self.event_type,
            "ts_utc": self.ts_utc,
            "strategy_id": self.strategy_id,
            "basket_id": self.basket_id,
            "bar_key": self.bar_key,
            "direction": self.direction,
            "z": round(self.z, 6),
            "reason": self.reason,
        }


@dataclass
class MatchRecord:
    """Detail-table row: expected vs runtime, one outcome class."""
    expected: Optional[ExpectedEvent]
    live: Optional[LiveEvent]
    outcome: OutcomeClass
    parity_status: ParityStatus = ParityStatus.UNKNOWN
    notes: str = ""

    def to_row(self) -> dict:
        e = self.expected.to_row() if self.expected else {
            "event_id": "", "strategy": self.live.strategy_id if self.live else "",
            "variant": "", "decision_type": "", "bar_key": self.live.bar_key if self.live else "",
            "timestamp_utc": self.live.ts_utc if self.live else "", "direction": self.live.direction if self.live else "",
            "basis": 0.0, "z": round(self.live.z, 6) if self.live else 0.0,
            "generation": 0, "basket_id": self.live.basket_id if self.live else "",
            "entry_eligible": False, "entry_reason": "", "exit_eligible": False,
            "exit_reason": "", "basket_state": "", "block_reason": "",
        }
        return {
            **e,
            "runtime_event": self.live.event_type if self.live else "",
            "runtime_seq": self.live.seq if self.live else "",
            "outcome": self.outcome.value,
            "parity_status": self.parity_status.value,
            "notes": self.notes,
        }


@dataclass
class AuditSummary:
    """Per-strategy week accounting (the end-of-week report numbers)."""
    strategy_id: str
    expected_entries: int = 0
    expected_exits: int = 0
    runtime_signals: int = 0
    taken: int = 0
    shadow: int = 0
    valid_blocks: int = 0
    missed: int = 0
    runtime_only: int = 0
    data_divergence: int = 0
    no_signal: bool = False
    unrecognized_expected: int = 0   # expected entries not recognized by runtime

    @property
    def signal_recognition_rate(self) -> float:
        valid = self.expected_entries - self.data_divergence
        if valid <= 0:
            return 1.0
        recognized = valid - self.missed - self.unrecognized_expected
        return max(0.0, recognized / valid)

    def to_dict(self) -> dict:
        return {
            "strategy": self.strategy_id,
            "expected_signals": self.expected_entries,
            "expected_exits": self.expected_exits,
            "runtime_signals": self.runtime_signals,
            "taken": self.taken,
            "shadow": self.shadow,
            "valid_blocks": self.valid_blocks,
            "missed": self.missed,
            "runtime_only": self.runtime_only,
            "data_divergence": self.data_divergence,
            "no_signal_week": self.no_signal,
            "signal_recognition_rate": round(self.signal_recognition_rate, 6),
        }
