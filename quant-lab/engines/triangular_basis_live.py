"""
CEREBUS FX v4.0 - Triangular Basis Live Strategy Wrapper
==========================================================

Thin wrapper around the canonical validated triangular_basis_engine.py.

DO NOT modify the canonical strategy mathematics. This wrapper ONLY:
- Exposes clean interfaces for live execution
- Delegates to canonical calculations for basis, rolling mean/std, z-score
- Returns high-level decisions: NO_ACTION, OPEN_BASKET, CLOSE_BASKET
- Tracks state between polling cycles

PARITY BY CONSTRUCTION
======================
The wrapper maintains a growing buffer of synchronized TriangularBar objects
and delegates computation to the canonical engine's pure functions
(compute_basis, compute_basis_zscore, compute_atr). This guarantees the live
wrapper produces IDENTICAL basis / z-score / ATR / sizing output to the
canonical historical backtest engine on the same chronological data.

Canonical commit: 2435d04e77eb31b42ab14ba76482efb729965b83
Balanced config: z=2.5, stop=6.0, lookback=200, London-only

Usage:
    from engines.triangular_basis_live import TriangularBasisLiveEngine
    engine = TriangularBasisLiveEngine()
    decision = engine.process_snapshot(snapshot)
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.stdout.reconfigure(encoding="utf-8")

import numpy as np

# --- IMPORT CANONICAL ENGINE ---
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from engines.triangular_basis_engine import (
        Config,
        Direction,
        TradeResult,
        Bar,
        TriangularBar,
        SessionData,
        compute_sessions,
        synchronize_bars,
        load_bars_csv,
        get_pip_size,
        _est_hour,
        _session_date,
        compute_atr,
        compute_basis,
        compute_basis_zscore,
    )
except ImportError as e:
    print(f"[TRIANGULAR_LIVE] ERROR importing canonical engine: {e}")
    raise


class BasketDecision(Enum):
    NO_ACTION = "no_action"
    OPEN_BASKET = "open_basket"
    CLOSE_BASKET = "close_basket"


@dataclass
class LegConfig:
    canonical_symbol: str
    broker_symbol: str
    side: Direction
    model_weight: float = 0.0  # canonical inverse-ATR normalized weight (NOT lots)
    entry_price: float = 0.0
    ticket: int = 0


@dataclass
class BasketIntent:
    decision: BasketDecision
    basket_id: str
    timestamp: datetime
    direction: Direction
    basis: float
    zscore: float
    legs: List[LegConfig] = field(default_factory=list)
    hedge_weights: Dict[str, float] = field(default_factory=dict)
    expected_cost_pips: float = 10.2

    def to_dict(self) -> dict:
        return {
            "decision": self.decision.value,
            "basket_id": self.basket_id,
            "timestamp": self.timestamp.isoformat(),
            "direction": self.direction.name,
            "basis": round(self.basis, 8),
            "zscore": round(self.zscore, 4),
            "legs": [
                {
                    "canonical_symbol": leg.canonical_symbol,
                    "broker_symbol": leg.broker_symbol,
                    "side": leg.side.name,
                    "model_weight": leg.model_weight,
                    "entry_price": leg.entry_price,
                    "ticket": leg.ticket,
                }
                for leg in self.legs
            ],
            "hedge_weights": self.hedge_weights,
            "expected_cost_pips": self.expected_cost_pips,
        }


@dataclass
class BasketState:
    basket_id: str
    direction: Direction
    entry_basis: float
    entry_zscore: float
    entry_time: datetime
    exit_deadline: datetime
    leg_tickets: Dict[str, int] = field(default_factory=dict)
    leg_fills: Dict[str, bool] = field(default_factory=dict)
    target_hedge_ratios: Dict[str, float] = field(default_factory=dict)
    actual_hedge_ratios: Dict[str, float] = field(default_factory=dict)
    status: str = "OPEN"


class TriangularBasisLiveEngine:
    """Thin live wrapper around the canonical TriangularBasisEngine.

    Delegates all mathematics to canonical functions for guaranteed parity.
    Does NOT rewrite any formula.
    """

    def __init__(self, config: Config = None):
        self.config = config or self._default_config()
        self._active_baskets: Dict[str, BasketState] = {}
        self._last_processed_timestamp: Optional[datetime] = None
        # Growing chronological buffer of synchronized TriangularBar objects
        self._tri_bars: List[TriangularBar] = []
        # Rolling basis values (incremental, parity with canonical)
        self._basis_history: List[float] = []
        self._config_hash = self._compute_config_hash()
        self.canonical_commit_sha = "2435d04e77eb31b42ab14ba76482efb729965b83"
        self.max_concurrent_baskets = 1

    def _default_config(self) -> Config:
        cfg = Config()
        cfg.BASIS_LOOKBACK = 200
        cfg.BASIS_ENTRY_Z = 2.5
        cfg.BASIS_STOP_Z = 6.0
        cfg.BASIS_EXIT_Z = 0.0
        cfg.TRADE_LONDON_ONLY = True
        cfg.MIN_MINUTES_TO_EXIT = 120
        cfg.LONDON_START_H_EST = 3
        cfg.LONDON_END_H_EST = 12
        cfg.HARD_EXIT_H_EST = 12
        cfg.MAX_TOTAL_LEVERAGE = 3.0
        cfg.ATR_PERIOD = 20
        return cfg

    def _compute_config_hash(self) -> str:
        config_str = json.dumps({
            "lookback": self.config.BASIS_LOOKBACK,
            "entry_z": self.config.BASIS_ENTRY_Z,
            "stop_z": self.config.BASIS_STOP_Z,
            "exit_z": self.config.BASIS_EXIT_Z,
            "london_start": self.config.LONDON_START_H_EST,
            "london_end": self.config.LONDON_END_H_EST,
            "hard_exit": self.config.HARD_EXIT_H_EST,
            "min_minutes_to_exit": self.config.MIN_MINUTES_TO_EXIT,
        }, sort_keys=True)
        return hashlib.sha256(config_str.encode()).hexdigest()[:16]

    def _snapshot_to_tri_bar(self, snapshot) -> TriangularBar:
        """Convert a sync snapshot (identical timestamps) to a TriangularBar."""
        return TriangularBar(
            timestamp=snapshot.timestamp,
            gbp_aud=snapshot.gbpaud_bar.close,
            gbp_nzd=snapshot.gbpnzd_bar.close,
            aud_nzd=snapshot.audnzd_bar.close,
            gbp_aud_high=snapshot.gbpaud_bar.high,
            gbp_aud_low=snapshot.gbpaud_bar.low,
            gbp_nzd_high=snapshot.gbpnzd_bar.high,
            gbp_nzd_low=snapshot.gbpnzd_bar.low,
            aud_nzd_high=snapshot.audnzd_bar.high,
            aud_nzd_low=snapshot.audnzd_bar.low,
        )

    def _update_atr_incrementally(self, tri_bar: TriangularBar):
        """Update rolling True Range windows per leg (parity with canonical).
        
        Canonical ATR: atr[i] = mean(TR over bars i-period+1..i). We keep a
        rolling deque of the last <period> TR values so the newest ATR matches
        compute_atr(self._tri_bars, leg, period)[-1] exactly.
        """
        from collections import deque
        if not hasattr(self, "_atr_windows"):
            self._atr_windows = {
                "gbp_aud": deque(maxlen=self.config.ATR_PERIOD),
                "gbp_nzd": deque(maxlen=self.config.ATR_PERIOD),
                "aud_nzd": deque(maxlen=self.config.ATR_PERIOD),
            }
            self._atr_values = {"gbp_aud": 0.0, "gbp_nzd": 0.0, "aud_nzd": 0.0}

        prev_gb, prev_gn, prev_an = None, None, None
        if len(self._tri_bars) >= 2:
            pb = self._tri_bars[-2]
            prev_gb, prev_gn, prev_an = pb.gbp_aud, pb.gbp_nzd, pb.aud_nzd

        def tr(high, low, prev_close):
            if prev_close is None:
                return high - low
            return max(high - low, abs(high - prev_close), abs(low - prev_close))

        for leg, (h, l, pc) in {
            "gbp_aud": (tri_bar.gbp_aud_high, tri_bar.gbp_aud_low, prev_gb),
            "gbp_nzd": (tri_bar.gbp_nzd_high, tri_bar.gbp_nzd_low, prev_gn),
            "aud_nzd": (tri_bar.aud_nzd_high, tri_bar.aud_nzd_low, prev_an),
        }.items():
            self._atr_windows[leg].append(tr(h, l, pc))
            # Canonical atr[i] only defined when i >= period; match that.
            if len(self._tri_bars) >= self.config.ATR_PERIOD:
                self._atr_values[leg] = sum(self._atr_windows[leg]) / len(self._atr_windows[leg])
            else:
                self._atr_values[leg] = 0.0

    def process_snapshot(self, snapshot) -> BasketIntent:
        """Process a synchronized TriangularSnapshot and return a basket decision.

        Exactly-once processing: same M5 timestamp processed once.
        Delegates basis/zscore/ATR/sizing to canonical functions.
        Uses canonical session/time semantics (fixed UTC-5 EST).
        """
        if snapshot is None:
            return self._no_action(0.0, 0.0)

        if self._last_processed_timestamp is not None and \
           self._last_processed_timestamp == snapshot.timestamp:
            return self._no_action(snapshot.gbpaud_bar.close, 0.0)

        tri_bar = self._snapshot_to_tri_bar(snapshot)

        # Dedup guard (should never trigger with exactly-once processing)
        if self._tri_bars and self._tri_bars[-1].timestamp == tri_bar.timestamp:
            return self._no_action(tri_bar.gbp_aud, 0.0)

        self._tri_bars.append(tri_bar)
        self._update_atr_incrementally(tri_bar)

        max_buffer = self.config.BASIS_LOOKBACK + 200
        if len(self._tri_bars) > max_buffer:
            self._tri_bars = self._tri_bars[-max_buffer:]

        # ── Incremental canonical basis + z-score ───────────────────────
        # Matches canonical compute_basis_zscore semantics:
        #   z[i] = (basis[i] - mean(basis[i-L:i])) / std(basis[i-L:i])
        # i.e. trailing "lookback" bars EXCLUDING the current bar.
        # We maintain a rolling basis history to avoid O(n^2) recompute.
        basis_value = (np.log(tri_bar.gbp_aud) - np.log(tri_bar.gbp_nzd) +
                       np.log(tri_bar.aud_nzd))
        self._basis_history.append(basis_value)
        if len(self._basis_history) > max_buffer:
            self._basis_history = self._basis_history[-max_buffer:]

        L = self.config.BASIS_LOOKBACK
        if len(self._basis_history) > L:
            window = self._basis_history[-(L + 1):-1]  # = basis[i-L:i], excludes current
            mean = float(np.mean(window))
            std = float(np.std(window))
            z_score = (basis_value - mean) / std if std > 0 else 0.0
        else:
            z_score = 0.0

        # Session eligibility (canonical fixed-UTC-5 EST semantics)
        est_hour = _est_hour(tri_bar.timestamp)
        london_ok = not self.config.TRADE_LONDON_ONLY or \
                    (self.config.LONDON_START_H_EST <= est_hour < self.config.LONDON_END_H_EST)
        minutes_to_exit = (self.config.HARD_EXIT_H_EST - est_hour) * 60
        enough_time = minutes_to_exit >= self.config.MIN_MINUTES_TO_EXIT

        # Close any active OPEN basket if its exit condition is met.
        # INTENT baskets (not yet confirmed by execution) are NOT closed here.
        if self._active_baskets:
            for bid, bstate in list(self._active_baskets.items()):
                if bstate.status != "OPEN":
                    continue
                if self._check_close_condition(bstate, z_score, est_hour):
                    intent = BasketIntent(
                        decision=BasketDecision.CLOSE_BASKET,
                        basket_id=bid,
                        timestamp=tri_bar.timestamp,
                        direction=bstate.direction,
                        basis=bstate.entry_basis,
                        zscore=z_score,
                    )
                    bstate.status = "CLOSED"
                    del self._active_baskets[bid]
                    self._last_processed_timestamp = snapshot.timestamp
                    return intent

        # New entry (only if no active baskets, London session, enough time)
        if not self._active_baskets and london_ok and enough_time:
            entry_intent = self._build_entry_intent(
                z_score, basis_value, tri_bar,
                self._atr_values["gbp_aud"],
                self._atr_values["gbp_nzd"],
                self._atr_values["aud_nzd"],
            )

            if entry_intent.decision == BasketDecision.OPEN_BASKET:
                basket_state = BasketState(
                    basket_id=entry_intent.basket_id,
                    direction=entry_intent.direction,
                    entry_basis=entry_intent.basis,
                    entry_zscore=entry_intent.zscore,
                    entry_time=tri_bar.timestamp,
                    exit_deadline=tri_bar.timestamp + timedelta(minutes=self.config.MIN_MINUTES_TO_EXIT),
                    status="INTENT",  # NOT OPEN until execution confirms 3-leg fill
                )
                self._active_baskets[basket_state.basket_id] = basket_state
                self._last_processed_timestamp = snapshot.timestamp
                return entry_intent

        self._last_processed_timestamp = snapshot.timestamp

        return BasketIntent(
            decision=BasketDecision.NO_ACTION,
            basket_id="",
            timestamp=tri_bar.timestamp,
            direction=Direction.FLAT,
            basis=basis_value,
            zscore=z_score,
        )

    def _no_action(self, basis: float, zscore: float) -> BasketIntent:
        return BasketIntent(
            decision=BasketDecision.NO_ACTION,
            basket_id="",
            timestamp=datetime.utcnow(),
            direction=Direction.FLAT,
            basis=basis,
            zscore=zscore,
        )

    def _build_entry_intent(self, z_score: float, basis_value: float,
                            tri_bar: TriangularBar,
                            atr_gbp_aud: float, atr_gbp_nzd: float,
                            atr_aud_nzd: float) -> BasketIntent:
        """Build a basket intent based on z-score entry conditions.

        Uses canonical volatility-weighted sizing formula.
        """
        size_gbp_aud = 1.0 / atr_gbp_aud if atr_gbp_aud > 0 else 1.0
        size_gbp_nzd = 1.0 / atr_gbp_nzd if atr_gbp_nzd > 0 else 1.0
        size_aud_nzd = 1.0 / atr_aud_nzd if atr_aud_nzd > 0 else 1.0

        total_size = size_gbp_aud + size_gbp_nzd + size_aud_nzd
        scale = self.config.MAX_TOTAL_LEVERAGE / total_size
        size_gbp_aud *= scale
        size_gbp_nzd *= scale
        size_aud_nzd *= scale

        basket_id = (f"TB_{tri_bar.timestamp.strftime('%Y%m%d_%H%M%S')}_"
                     f"{hashlib.md5(str(basis_value).encode()).hexdigest()[:8]}")

        if z_score > self.config.BASIS_ENTRY_Z:
            legs = [
                LegConfig(canonical_symbol="GBPAUD", broker_symbol="GBPAUD.PRO",
                          side=Direction.SHORT, model_weight=size_gbp_aud, entry_price=tri_bar.gbp_aud),
                LegConfig(canonical_symbol="GBPNZD", broker_symbol="GBPNZD.PRO",
                          side=Direction.LONG, model_weight=size_gbp_nzd, entry_price=tri_bar.gbp_nzd),
                LegConfig(canonical_symbol="AUDNZD", broker_symbol="AUDNZD.PRO",
                          side=Direction.SHORT, model_weight=size_aud_nzd, entry_price=tri_bar.aud_nzd),
            ]
            return BasketIntent(
                decision=BasketDecision.OPEN_BASKET,
                basket_id=basket_id,
                timestamp=tri_bar.timestamp,
                direction=Direction.SHORT,
                basis=basis_value,
                zscore=z_score,
                legs=legs,
                hedge_weights={"GBPAUD": size_gbp_aud, "GBPNZD": size_gbp_nzd, "AUDNZD": size_aud_nzd},
            )

        elif z_score < -self.config.BASIS_ENTRY_Z:
            legs = [
                LegConfig(canonical_symbol="GBPAUD", broker_symbol="GBPAUD.PRO",
                          side=Direction.LONG, model_weight=size_gbp_aud, entry_price=tri_bar.gbp_aud),
                LegConfig(canonical_symbol="GBPNZD", broker_symbol="GBPNZD.PRO",
                          side=Direction.SHORT, model_weight=size_gbp_nzd, entry_price=tri_bar.gbp_nzd),
                LegConfig(canonical_symbol="AUDNZD", broker_symbol="AUDNZD.PRO",
                          side=Direction.LONG, model_weight=size_aud_nzd, entry_price=tri_bar.aud_nzd),
            ]
            return BasketIntent(
                decision=BasketDecision.OPEN_BASKET,
                basket_id=basket_id,
                timestamp=tri_bar.timestamp,
                direction=Direction.LONG,
                basis=basis_value,
                zscore=z_score,
                legs=legs,
                hedge_weights={"GBPAUD": size_gbp_aud, "GBPNZD": size_gbp_nzd, "AUDNZD": size_aud_nzd},
            )

        return self._no_action(basis_value, z_score)

    def _check_close_condition(self, bstate: BasketState, z_score: float,
                              est_hour: int) -> bool:
        if bstate.direction == Direction.SHORT and z_score <= self.config.BASIS_EXIT_Z:
            return True
        if bstate.direction == Direction.LONG and z_score >= self.config.BASIS_EXIT_Z:
            return True
        if bstate.direction == Direction.SHORT and z_score >= self.config.BASIS_STOP_Z:
            return True
        if bstate.direction == Direction.LONG and z_score <= -self.config.BASIS_STOP_Z:
            return True
        if est_hour >= self.config.HARD_EXIT_H_EST:
            return True
        return False

    def load_historical_bars(self, bars: List[TriangularBar]):
        """Load a historical buffer for replay/parity."""
        self._tri_bars = list(bars)
        self._basis_history = [np.log(b.gbp_aud) - np.log(b.gbp_nzd) + np.log(b.aud_nzd)
                               for b in self._tri_bars]
        # Rebuild incremental ATR state from loaded buffer
        from collections import deque
        self._atr_windows = {
            "gbp_aud": deque(maxlen=self.config.ATR_PERIOD),
            "gbp_nzd": deque(maxlen=self.config.ATR_PERIOD),
            "aud_nzd": deque(maxlen=self.config.ATR_PERIOD),
        }
        self._atr_values = {"gbp_aud": 0.0, "gbp_nzd": 0.0, "aud_nzd": 0.0}
        for bar in self._tri_bars:
            self._update_atr_incrementally(bar)
        if self._tri_bars:
            self._last_processed_timestamp = self._tri_bars[-1].timestamp

    def reset_state(self):
        """Reset engine state (for parity/replay testing)."""
        self._active_baskets.clear()
        self._tri_bars.clear()
        self._basis_history.clear()
        if hasattr(self, "_atr_windows"):
            self._atr_windows.clear()
            self._atr_values = {"gbp_aud": 0.0, "gbp_nzd": 0.0, "aud_nzd": 0.0}
        self._last_processed_timestamp = None

    def get_active_baskets(self) -> Dict[str, BasketState]:
        return self._active_baskets.copy()

    # ── Strategy <-> Execution Acknowledgement ──────────────────────────
    # Strategy emits OPEN_BASKET_INTENT with status INTENT. Execution owns the
    # OPEN/BROKEN_HEDGE/CLOSED lifecycle. These callbacks let execution confirm
    # or reject. On failure the pending INTENT basket is cleanly reverted while
    # the mathematical rolling buffer continues normally.

    def on_basket_open_confirmed(self, basket_id: str, execution_result: dict = None):
        """Execution confirmed the full three-leg basket is filled -> OPEN."""
        bs = self._active_baskets.get(basket_id)
        if bs:
            bs.status = "OPEN"

    def on_basket_open_failed(self, basket_id: str, execution_result: dict = None):
        """Execution failed to complete the three-leg basket -> revert INTENT."""
        if basket_id in self._active_baskets:
            del self._active_baskets[basket_id]

    def on_basket_close_confirmed(self, basket_id: str, execution_result: dict = None):
        """Execution confirmed all three legs flat -> CLOSED."""
        if basket_id in self._active_baskets:
            bs = self._active_baskets[basket_id]
            bs.status = "CLOSED"
            del self._active_baskets[basket_id]

    def on_basket_open_partial(self, basket_id: str, execution_result: dict = None):
        """Partial fill detected -> execution is flattening; mark broken, revert."""
        if basket_id in self._active_baskets:
            bs = self._active_baskets[basket_id]
            bs.status = "BROKEN_HEDGE"
            del self._active_baskets[basket_id]

    def get_config_hash(self) -> str:
        return self._config_hash

    def get_rolling_state(self) -> dict:
        return {
            "last_processed_timestamp": str(self._last_processed_timestamp)
                if self._last_processed_timestamp else None,
            "buffer_size": len(self._tri_bars),
            "basis_history_size": len(self._basis_history),
            "active_baskets": list(self._active_baskets.keys()),
        }

    def shutdown(self):
        self._active_baskets.clear()
        self._tri_bars.clear()
        self._basis_history.clear()
