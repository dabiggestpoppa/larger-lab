"""
TB-R6.3 — WEEKLY SIGNAL-COMPLETENESS AUDITOR · REPLAY
=====================================================

TBWeeklyReplayEngine — the INDEPENDENT canonical replay.

It reconstructs expected signals from RAW COMPLETED M5 bars through the
frozen canonical pure strategy engine (`engines.triangular_basis_live`,
which delegates every formula to the sealed research engine). It is:

  * deterministic  — same bars, same records, byte-for-byte
  * execution-free — it emits decisions only; it never touches a broker
  * lifecycle-faithful — entries are confirmed OPEN (canonical fills
    confirmation) so exits, hard-exits and re-entries follow the frozen
    contract; this is what reproduces the sealed 405/194 reference counts
  * session-faithful — London 3-12 EST, fixed UTC-5, hard exit 12 EST,
    min 120 minutes to exit, all inside the canonical engine

Replay records carry: bar_key, timestamp, basis, z, strategy_variant,
entry_eligible, entry_direction, entry_reason, exit_eligible, exit_reason,
basket_state, block_reason — the deterministic ledger for matching.

The warmup requirement (>= 201 bars before Monday) is enforced by the data
loader; this engine never starts z cold.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Dict, List, Optional

_QL = Path(__file__).resolve().parent.parent
for _p in (str(_QL), str(_QL / "engines"), str(_QL / "audit")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pandas as pd

try:
    from engines.tb_forward_config import (
        PRIMARY_CONFIG, CONTROL_CONFIG, LOOKBACK,
        LONDON_START_H_EST, LONDON_END_H_EST, HARD_EXIT_H_EST,
        MIN_MINUTES_TO_EXIT,
    )
    from engines.triangular_basis_live import (
        TriangularBasisLiveEngine, BasketDecision, Direction,
    )
except Exception as e:  # pragma: no cover
    raise RuntimeError(f"TB-R6.3 replay requires the canonical engine: {e}")

from tb_audit_core import (
    DecisionType, ExpectedEvent, direction_from_z, expected_event_id,
)


@dataclass
class BarRecord:
    """One replayed bar (deterministic; the detail table backbone)."""
    bar_key: str
    timestamp_utc: str
    basis: float
    z: float
    strategy_id: str
    variant: str
    entry_eligible: bool
    entry_direction: str
    entry_reason: str
    exit_eligible: bool
    exit_reason: str
    basket_state: str
    block_reason: str


@dataclass
class ReplayResult:
    strategy_id: str
    records: List[BarRecord] = field(default_factory=list)
    expected_events: List[ExpectedEvent] = field(default_factory=list)
    entry_count: int = 0
    exit_count: int = 0


def make_snapshot(row, bar: "object") -> object:
    """Build the canonical snapshot object the live engine consumes."""
    b = SimpleNamespace
    return SimpleNamespace(
        timestamp=bar.ts,
        gbpaud_bar=b(close=float(row["GA"]), high=float(row["GA_h"]),
                     low=float(row["GA_l"])),
        gbpnzd_bar=b(close=float(row["GN"]), high=float(row["GN_h"]),
                     low=float(row["GN_l"])),
        audnzd_bar=b(close=float(row["AN"]), high=float(row["AN_h"]),
                     low=float(row["AN_l"])),
    )


def _est_hour(ts: datetime) -> int:
    """Fixed UTC-5 canonical EST hour (no DST, per sealed contract)."""
    return (ts.hour - 5) % 24


class TBWeeklyReplayEngine:
    """Independent deterministic replay of one strategy over one week."""

    def __init__(self, model_config=None):
        from engines.tb_forward_config import StrategyModelConfig  # noqa: PLC0415
        self.model_config = model_config or CONTROL_CONFIG
        self.strategy_id = self.model_config.strategy_id
        self.variant = self.model_config.model_id
        self.entry_z = self.model_config.entry_z
        self.short_exit_z = self.model_config.short_exit_z
        self.long_exit_z = self.model_config.long_exit_z
        self.stop_z = self.model_config.stop_z

    # ── replay ──────────────────────────────────────────────────────────
    def replay(self, data_window, collect_records: bool = True) -> ReplayResult:
        """Replay warmup (no records) + window (records + expected events).

        collect_records=False keeps only expected events (cheap pass used
        for the full historical cadence replay).
        """
        from tb_audit_data import CANONICAL_SYMBOLS  # noqa: PLC0415
        eng = TriangularBasisLiveEngine(model_config=self.model_config)
        res = ReplayResult(strategy_id=self.strategy_id)
        ws = data_window.week_start

        frames = {}
        for s in CANONICAL_SYMBOLS:
            bars = data_window.per_symbol[s]
            frames[s] = {
                b.ts: b for b in bars
            }
        # common timeline (already aligned by loader)
        timeline = sorted(frames[CANONICAL_SYMBOLS[0]].keys())

        state = "FLAT"          # FLAT | INTENT | OPEN
        open_basket_id = ""
        gen = 0                 # entry generation (1-based per window)
        last_entry: Optional[ExpectedEvent] = None

        def rec(bar, basis, z, entry_elig, entry_reason, exit_elig,
                exit_reason, block_reason):
            return BarRecord(
                bar_key=bar.ts.strftime("%Y-%m-%d %H:%M"),
                timestamp_utc=bar.ts.strftime("%Y-%m-%d %H:%M:%S"),
                basis=float(basis), z=float(z),
                strategy_id=self.strategy_id, variant=self.variant,
                entry_eligible=entry_elig, entry_direction=direction_from_z(z),
                entry_reason=entry_reason, exit_eligible=exit_elig,
                exit_reason=exit_reason, basket_state=state,
                block_reason=block_reason,
            )

        for ts in timeline:
            bars = {s: frames[s][ts] for s in CANONICAL_SYMBOLS}
            row = {
                "GA": bars["GBPAUD"].close, "GA_h": bars["GBPAUD"].high,
                "GA_l": bars["GBPAUD"].low,
                "GN": bars["GBPNZD"].close, "GN_h": bars["GBPNZD"].high,
                "GN_l": bars["GBPNZD"].low,
                "AN": bars["AUDNZD"].close, "AN_h": bars["AUDNZD"].high,
                "AN_l": bars["AUDNZD"].low,
            }
            snap = make_snapshot(row, bars["GBPAUD"])
            d = eng.process_snapshot(snap)
            z = float(d.zscore)
            basis = float(d.basis)
            est_hour = _est_hour(ts)
            in_window = ws <= ts < data_window.week_end

            if d.decision == BasketDecision.OPEN_BASKET:
                gen += 1
                open_basket_id = d.basket_id
                ev = ExpectedEvent(
                    event_id=expected_event_id(
                        self.strategy_id, ts.strftime("%Y-%m-%d %H:%M"),
                        d.direction.name, DecisionType.ENTRY.value, gen),
                    strategy_id=self.strategy_id, variant=self.variant,
                    decision_type=DecisionType.ENTRY,
                    bar_key=ts.strftime("%Y-%m-%d %H:%M"),
                    timestamp_utc=ts.strftime("%Y-%m-%d %H:%M:%S"),
                    direction=d.direction.name, basis=float(d.basis),
                    z=float(d.zscore), generation=gen,
                    basket_id=d.basket_id, entry_eligible=True,
                    entry_reason="Z_ENTRY", basket_state="OPEN",
                )
                if in_window:
                    res.expected_events.append(ev)
                    res.entry_count += 1
                last_entry = ev
                state = "OPEN"
                # canonical lifecycle: execution confirms 3-leg fill
                eng.on_basket_open_confirmed(d.basket_id)
                if in_window and collect_records:
                    res.records.append(rec(bars["GBPAUD"], basis, z,
                                           True, "Z_ENTRY", False, "",
                                           ""))
            elif d.decision == BasketDecision.CLOSE_BASKET:
                ev = ExpectedEvent(
                    event_id=expected_event_id(
                        self.strategy_id, ts.strftime("%Y-%m-%d %H:%M"),
                        d.direction.name, DecisionType.EXIT.value,
                        (last_entry.generation if last_entry else 0)),
                    strategy_id=self.strategy_id, variant=self.variant,
                    decision_type=DecisionType.EXIT,
                    bar_key=ts.strftime("%Y-%m-%d %H:%M"),
                    timestamp_utc=ts.strftime("%Y-%m-%d %H:%M:%S"),
                    direction=d.direction.name, basis=float(d.basis),
                    z=float(d.zscore),
                    generation=last_entry.generation if last_entry else 0,
                    basket_id=open_basket_id, exit_eligible=True,
                    exit_reason=d.exit_reason or "EXIT",
                    basket_state="FLAT",
                )
                if in_window:
                    res.expected_events.append(ev)
                    res.exit_count += 1
                state = "FLAT"
                open_basket_id = ""
                if in_window and collect_records:
                    res.records.append(rec(bars["GBPAUD"], basis, z,
                                           False, "", True,
                                           d.exit_reason or "EXIT", ""))
            else:
                if not in_window or not collect_records:
                    continue
                # block_reason: a would-be entry that the canonical contract
                # correctly refuses
                block = ""
                if abs(z) > self.entry_z and state != "FLAT":
                    block = "BASKET_ALREADY_OPEN"
                elif abs(z) > self.entry_z:
                    if not (LONDON_START_H_EST <= est_hour < LONDON_END_H_EST):
                        block = "OUTSIDE_LONDON_SESSION"
                    elif (HARD_EXIT_H_EST - est_hour) * 60 < MIN_MINUTES_TO_EXIT:
                        block = "NOT_ENOUGH_TIME_TO_EXIT"
                res.records.append(rec(bars["GBPAUD"], basis, z,
                                       abs(z) > self.entry_z,
                                       "Z_ENTRY" if abs(z) > self.entry_z else "",
                                       False, "", block))
        return res


def replay_historical(data_window, strategies=(PRIMARY_CONFIG, CONTROL_CONFIG),
                      collect_records: bool = False):
    """Replay a full history window (dev reference) once per strategy.

    Deterministic pure function of the data. Used for the frozen historical
    cadence distributions and the 405/194 reference anchoring.
    """
    return {cfg.strategy_id: TBWeeklyReplayEngine(model_config=cfg)
            .replay(data_window, collect_records=collect_records)
            for cfg in strategies}
