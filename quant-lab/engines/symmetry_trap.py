"""
CEREBUS FX v4.0 — Symmetry Trap Engine (Base)
==============================================

Reconstructed from CEREBUS ontology per MAD directive (2026-05-29):
  - Base Symmetry Trap ONLY
  - TP = single 1 AU target (no extended ladder)
  - SL = Zero-Buffer Impulse Extreme (close-only)
  - No gear shift, no cross-pair, no Blind Chain extensions
  - Add layers later after base is validated

ONTOLOGY SOURCES:
  - cerebus_qa_recap.md          (Q4 impulse trigger, Q5 80% kill, Q8 OCC entry, Q9 DZ)
  - cerebus_dual_engine.md       (Engine B isolation, zero-buffer SL)
  - cerebus_unified_topology.md  (Model B: Atomic Structural Engine)
  - cerebus_resolution_engine.py (4-state FSM base)
  - manual_ontology.md           (55 Q&As, Computable Mechanics)

AXIOMS ENFORCED:
  1. Symmetry Trap = Engine B ONLY (Atomic Structural). Never mix P90 SL/TP.
  2. AU = 50% of K-Means centroid (NOT pips or Fibonacci).
  3. P90 = Kinetic Validation Threshold (NOT an indicator).
  4. 80% Close Invalidation Rule = absolute, close-only.
  5. Zero-Buffer OCC Extreme = SL at exact impulse extreme.
  6. TP = exactly 1 AU from entry. Single target. No ladder.
  7. 12 PM EST = full state reset (deficits terminate, no roll-forward).
  8. Deficit is NEVER abandoned — only reassigned.

STATE MACHINE (4 states):
  SEARCH → WAIT_RETRACE → WAIT_OCC → IN_TRADE → (reset to SEARCH)

Author: CEREBUS Ontology Reconstruction — MAD Directive 2026-05-29
Mode: Mechanical / Structural / Executable
Trader Language: PURGED
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, time, timezone
from enum import Enum
from typing import Dict, List, Optional, Tuple

# ─── CONSTANTS ────────────────────────────────────────────────────────────

# Time quantization boundaries (manual_ontology.md Section 2 Q5, Q7)
ASIAN_SESSION_START = time(19, 0)   # 19:00 EST — compression window
ASIAN_SESSION_END = time(3, 0)      # 03:00 EST — compression ends
ACTIVATION_END = time(12, 0)        # 12:00 PM EST — hard termination

# Hard structural law (manual_ontology.md Computable Mechanics Q11)
KILL_SWITCH_PCT = 0.80              # 80% of impulse leg — CLOSE ONLY

# Tier Configuration: discrete volatility quantization classes
# AU = 50% of K-Means cluster centroid (manual_ontology.md Computable Q1)
DEFAULT_TIER_CONFIG: Dict[str, Dict[str, float]] = {
    "T1": {"ar_max": 20.0, "au": 10.0, "trigger": 12.0},
    "T2": {"ar_max": 30.0, "au": 12.0, "trigger": 15.0},
    "T3": {"ar_max": 45.0, "au": 15.0, "trigger": 19.0},
    # AR > 45p → NO-GO: structural coherence collapses
}


# ─── ENUMS ────────────────────────────────────────────────────────────────

class EngineState(Enum):
    """
    Four expressions of the single Resolution Construction engine.
    NOT independent states — recursive expressions of one state.
    """
    SEARCH = "SEARCH"               # Impulse detection (temporal-spatial saturation)
    WAIT_RETRACE = "WAIT_RETRACE"   # Density Zone penetration (friction clearing)
    WAIT_OCC = "WAIT_OCC"           # Pathway validation (kinetic reloading)
    IN_TRADE = "IN_TRADE"           # Resolution execution (deficit satisfaction)


class TradeDirection(Enum):
    LONG = 1
    SHORT = -1
    FLAT = 0


# ─── DATA STRUCTURES ──────────────────────────────────────────────────────

@dataclass
class Bar:
    """
    M5 candle — observer compression artifact (manual_ontology.md Q19).
    Fundamental objects are structural events (Impulse, OCC, AU Target).
    """
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float

    @property
    def body(self) -> float:
        return self.close - self.open

    @property
    def body_abs(self) -> float:
        return abs(self.close - self.open)

    @property
    def is_bullish(self) -> bool:
        return self.close > self.open

    @property
    def is_bearish(self) -> bool:
        return self.close < self.open


@dataclass
class TradeSignal:
    """Structured output on engine events."""
    event: str                          # "ENTRY", "TP_HIT", "SL_HIT", "KILL_SWITCH", "NO_GO"
    direction: Optional[TradeDirection]
    entry_price: Optional[float]
    sl_price: Optional[float]
    tp_price: Optional[float]
    au_used: Optional[float]
    timestamp: Optional[datetime]
    reason: str = ""                    # Axiom citation for audit trail
    loop_count: int = 1                 # Which loop this signal belongs to (1-indexed)


# ─── TIER CLASSIFICATION ──────────────────────────────────────────────────

def classify_tier(
    asian_range_pips: float,
    tier_config: Dict[str, Dict[str, float]] = DEFAULT_TIER_CONFIG
) -> Tuple[str, float, float]:
    """
    Classify session volatility into discrete Tier.

    Tier is DISCRETE — field snaps into one of three quantized energy states.
    AR > T3 max → NO-GO (structural coherence collapses).

    Reference: manual_ontology.md Section 1 Q4, Computable Mechanics Q3

    Returns:
        (tier_name, au_pips, trigger_pips)
    """
    for tier_name in ("T1", "T2", "T3"):
        if tier_name in tier_config and asian_range_pips <= tier_config[tier_name]["ar_max"]:
            cfg = tier_config[tier_name]
            return tier_name, cfg["au"], cfg["trigger"]
    return "NO_GO", 0.0, 0.0


# ─── CORE ENGINE ──────────────────────────────────────────────────────────

class SymmetryTrapEngine:
    """
    CEREBUS Model B: Atomic Structural Engine — Symmetry Trap (Base)

    Entry Pipeline (all 3 steps mandatory):
      1. Impulse:   M5 close beyond Tier Trigger (AU x 1.20) from swing_origin
      2. Rebalance: Pullback >= 1 AU OR 38.2%-50% Fib retracement
      3. OCC:       M5 candle closes BACK in impulse direction

    Trade Management:
      Entry:  Close of OCC candle
      SL:     Zero-Buffer Impulse Extreme (CLOSE-ONLY invalidation)
      TP:     Exactly 1 AU from entry (SINGLE TARGET — no ladder)

    Invalidation:
      - 80% Kill Switch: M5 close past 80% of impulse leg = pathway VOID
      - SL hit (close only) = trade over, reset to SEARCH

    Engine Isolation:
      This engine NEVER uses P90 body data.
      SL is ALWAYS Zero-Buffer OCC/Impulse Extreme — never 80% P90 body.
      TP is ALWAYS 1 AU — never P90 targets.

    Reference: cerebus_dual_engine.md Section I (Great Demarcation)
    """

    def __init__(
        self,
        pip_size: float = 0.0001,
        tier_config: Optional[Dict[str, Dict[str, float]]] = None,
        symbol: str = "EURUSD",
    ):
        self.pip_size = pip_size
        self.tier_config = tier_config or DEFAULT_TIER_CONFIG.copy()
        self.symbol = symbol
        self.logger = logging.getLogger(f"cerebus.symmetry_trap.{symbol}")

        # ── State Machine ──────────────────────────────────────────────
        self.state: EngineState = EngineState.SEARCH
        self.swing_origin: Optional[float] = None
        self.impulse_direction: TradeDirection = TradeDirection.FLAT
        self.impulse_extreme: float = 0.0
        self.impulse_size_pips: float = 0.0
        self.kill_switch_level: float = 0.0
        self.active_au: float = 0.0    # AU in price units

        # ── Trade State ────────────────────────────────────────────────
        self.entry_price: Optional[float] = None
        self.sl_price: Optional[float] = None
        self.tp_price: Optional[float] = None

        # ── Loop Tracking (Option B: Continuous Loop) ──────────────────
        self.loop_count: int = 1            # Start at loop 1
        self.max_loops: int = 5             # Safety cap per manual
        self.loop_start_time = None          # When loop began
        self.cascade_bias = None             # P90 cascade direction

        # ── Session State ──────────────────────────────────────────────
        self.asian_high: float = 0.0
        self.asian_low: float = 0.0
        self.asian_range_pips: float = 0.0
        self.tier_name: str = "T1"
        self.au_pips: float = 10.0
        self.trigger_pips: float = 12.0
        self.session_active: bool = False

        # ── Logging ────────────────────────────────────────────────────
        self.signal_log: List[TradeSignal] = []

    # ── Session Initialization ────────────────────────────────────────

    def initialize_session(
        self,
        asian_high: float,
        asian_low: float,
    ) -> None:
        """
        Initialize session at 03:00 EST from Asian Range.

        Classify Tier → Lock AU → Lock Trigger.
        Called ONCE per session.

        Reference: cerebus_qa_recap.md Q1 (Tier session invariance)
        """
        self.asian_high = asian_high
        self.asian_low = asian_low
        self.asian_range_pips = (asian_high - asian_low) / self.pip_size

        self.tier_name, self.au_pips, self.trigger_pips = classify_tier(
            self.asian_range_pips, self.tier_config
        )

        self.active_au = self.au_pips * self.pip_size
        self.session_active = self.tier_name != "NO_GO"

        # Reset state machine
        self.state = EngineState.SEARCH
        self.swing_origin = None
        self.impulse_direction = TradeDirection.FLAT
        self.impulse_extreme = 0.0
        self.impulse_size_pips = 0.0
        self.kill_switch_level = 0.0
        self.entry_price = None
        self.sl_price = None
        self.tp_price = None

        # ── Option B: Reset loop tracking for new session ─────────────
        self.loop_count = 1
        self.loop_start_time = None
        self.cascade_bias = None

        self.logger.info(
            f"Session initialized: tier={self.tier_name}, "
            f"AU={self.au_pips}p, trigger={self.trigger_pips}p, "
            f"AR={self.asian_range_pips:.1f}p, loop=1 (max={self.max_loops})"
        )

    # ── Main Processing Loop ─────────────────────────────────────────

    def process_bar(self, bar: Bar) -> Optional[TradeSignal]:
        """
        Process each M5 bar through the state machine.

        Args:
            bar: M5 candle with OHLC data

        Returns:
            TradeSignal on state transitions (ENTRY, TP_HIT, SL_HIT, KILL_SWITCH)
            None if no event
        """
        if not self.session_active:
            return None

        # Set swing origin from first bar if not set
        if self.swing_origin is None:
            self.swing_origin = bar.close

        # ── Option B: Loop timeout — if 4 hours pass without entry, stop looping
        if self.loop_start_time is not None and self.loop_count > 1:
            if (bar.timestamp - self.loop_start_time).total_seconds() > 4 * 3600:
                self.loop_start_time = None
                self.session_active = False
                self.logger.debug(f"Loop {self.loop_count} expired (4h timeout)")
                return None

        active_trig = self.trigger_pips * self.pip_size

        up_move = bar.high - self.swing_origin
        dn_move = self.swing_origin - bar.low

        # ── STATE: SEARCH ──────────────────────────────────────────────
        # Wait for impulse breach >= Tier Trigger (AU x 1.20)
        # Reference: cerebus_qa_recap.md Q4, manual_ontology.md Computable Q1
        if self.state == EngineState.SEARCH:
            if up_move >= active_trig:
                self.impulse_direction = TradeDirection.LONG
                self.impulse_extreme = bar.high
                self.impulse_size_pips = up_move / self.pip_size
                self.kill_switch_level = (
                    self.impulse_extreme - up_move * KILL_SWITCH_PCT
                )
                self.state = EngineState.WAIT_RETRACE
                self.logger.debug(
                    f"Impulse LONG: extreme={self.impulse_extreme:.5f}, "
                    f"size={self.impulse_size_pips:.1f}p, "
                    f"kill={self.kill_switch_level:.5f}"
                )

            elif dn_move >= active_trig:
                self.impulse_direction = TradeDirection.SHORT
                self.impulse_extreme = bar.low
                self.impulse_size_pips = dn_move / self.pip_size
                self.kill_switch_level = (
                    self.impulse_extreme + dn_move * KILL_SWITCH_PCT
                )
                self.state = EngineState.WAIT_RETRACE
                self.logger.debug(
                    f"Impulse SHORT: extreme={self.impulse_extreme:.5f}, "
                    f"size={self.impulse_size_pips:.1f}p, "
                    f"kill={self.kill_switch_level:.5f}"
                )

        # ── STATE: WAIT_RETRACE ────────────────────────────────────────
        # Wait for pullback >= 1 AU OR 38.2%-50% Fib retracement
        # Monitor 80% Kill Switch (close-only invalidation)
        # Reference: cerebus_qa_recap.md Q5 (Kill), Q8 (DZ pullback), Q9 (DZ)
        elif self.state == EngineState.WAIT_RETRACE:
            # Kill Switch check (CLOSE-ONLY)
            if self.impulse_direction == TradeDirection.LONG:
                if bar.close < self.kill_switch_level:
                    _loop = self.loop_count
                    self._reset_state_keep_loop(bar.close)
                    self.loop_count = min(_loop + 1, self.max_loops)
                    self.loop_start_time = bar.timestamp
                    if self.loop_count >= self.max_loops:
                        self.session_active = False
                    sig = TradeSignal(
                        event="KILL_SWITCH",
                        direction=None, entry_price=None,
                        sl_price=None, tp_price=None,
                        au_used=self.au_pips, timestamp=bar.timestamp,
                        reason="Q5: M5 close past 80% of impulse leg = pathway void",
                        loop_count=_loop,
                    )
                    self.signal_log.append(sig)
                    return sig
            else:  # SHORT
                if bar.close > self.kill_switch_level:
                    _loop = self.loop_count
                    self._reset_state_keep_loop(bar.close)
                    self.loop_count = min(_loop + 1, self.max_loops)
                    self.loop_start_time = bar.timestamp
                    if self.loop_count >= self.max_loops:
                        self.session_active = False
                    sig = TradeSignal(
                        event="KILL_SWITCH",
                        direction=None, entry_price=None,
                        sl_price=None, tp_price=None,
                        au_used=self.au_pips, timestamp=bar.timestamp,
                        reason="Q5: M5 close past 80% of impulse leg = pathway void",
                        loop_count=_loop,
                    )
                    self.signal_log.append(sig)
                    return sig

            # ── Dynamic DZ Thresholds (Option B: Continuous Loop) ────────
            # Loop 1: strict Goldilocks zone (32%-50%)
            # Loop 2+: relaxed floor (20%-50% — shallow momentum pullbacks)
            if self.loop_count == 1:
                min_retrace_pct = 0.32
                max_retrace_pct = 0.50
            else:
                min_retrace_pct = 0.20
                max_retrace_pct = 0.50

            # Pullback measurement
            if self.impulse_direction == TradeDirection.LONG:
                pullback_px = self.impulse_extreme - bar.low
            else:
                pullback_px = bar.high - self.impulse_extreme

            pullback_pips = pullback_px / self.pip_size
            retrace_pct = (
                pullback_pips / self.impulse_size_pips
                if self.impulse_size_pips > 0 else 0
            )

            au_penetrated = pullback_pips >= self.au_pips
            # Dynamic fib zone: min_retrace_pct to max_retrace_pct
            fib_penetrated = min_retrace_pct <= retrace_pct <= max_retrace_pct

            # ── Cascade P90 Bypass (Loop 2+ only) ────────────────────
            cascade_bypass = False
            if (self.loop_count >= 2 and retrace_pct < min_retrace_pct
                    and self.cascade_bias is not None
                    and self.cascade_bias == self.impulse_direction):
                cascade_bypass = True

            if au_penetrated or fib_penetrated or cascade_bypass:
                self.state = EngineState.WAIT_OCC
                self.logger.debug(
                    f"DZ penetrated: pullback={pullback_pips:.1f}p, "
                    f"retrace={retrace_pct:.3f}, au_ok={au_penetrated}, "
                    f"fib_ok={fib_penetrated}, loop={self.loop_count}, "
                    f"min_ret={min_retrace_pct:.2f}"
                )

        # ── STATE: WAIT_OCC ────────────────────────────────────────────
        # Wait for Opposite Candle Close confirming impulse direction
        # Reference: cerebus_qa_recap.md Q8, manual_ontology.md Computable Q3
        elif self.state == EngineState.WAIT_OCC:
            # Re-verify Kill Switch
            if self.impulse_direction == TradeDirection.LONG:
                if bar.close < self.kill_switch_level:
                    _loop = self.loop_count
                    self._reset_state_keep_loop(bar.close)
                    self.loop_count = min(_loop + 1, self.max_loops)
                    self.loop_start_time = bar.timestamp
                    if self.loop_count >= self.max_loops:
                        self.session_active = False
                    sig = TradeSignal(
                        event="KILL_SWITCH",
                        direction=None, entry_price=None,
                        sl_price=None, tp_price=None,
                        au_used=self.au_pips, timestamp=bar.timestamp,
                        reason="Q5: Kill switch breached in WAIT_OCC",
                        loop_count=_loop,
                    )
                    self.signal_log.append(sig)
                    return sig
            else:
                if bar.close > self.kill_switch_level:
                    _loop = self.loop_count
                    self._reset_state_keep_loop(bar.close)
                    self.loop_count = min(_loop + 1, self.max_loops)
                    self.loop_start_time = bar.timestamp
                    if self.loop_count >= self.max_loops:
                        self.session_active = False
                    sig = TradeSignal(
                        event="KILL_SWITCH",
                        direction=None, entry_price=None,
                        sl_price=None, tp_price=None,
                        au_used=self.au_pips, timestamp=bar.timestamp,
                        reason="Q5: Kill switch breached in WAIT_OCC",
                        loop_count=_loop,
                    )
                    self.signal_log.append(sig)
                    return sig

            # OCC check: candle closing in impulse direction
            occ_confirmed = (
                (self.impulse_direction == TradeDirection.LONG and bar.is_bullish) or
                (self.impulse_direction == TradeDirection.SHORT and bar.is_bearish)
            )

            if occ_confirmed:
                self.entry_price = bar.close
                self.sl_price = self.impulse_extreme  # ZERO BUFFER
                self.tp_price = (
                    bar.close + self.active_au * self.impulse_direction.value
                )
                self.state = EngineState.IN_TRADE

                sig = TradeSignal(
                    event="ENTRY",
                    direction=self.impulse_direction,
                    entry_price=self.entry_price,
                    sl_price=self.sl_price,
                    tp_price=self.tp_price,
                    au_used=self.au_pips,
                    timestamp=bar.timestamp,
                    reason=f"Q8: OCC confirmed after DZ pullback — entry on close (loop {self.loop_count})",
                    loop_count=self.loop_count,
                )
                self.signal_log.append(sig)
                self.logger.info(
                    f"ENTRY {'LONG' if self.impulse_direction == TradeDirection.LONG else 'SHORT'} "
                    f"(loop {self.loop_count}): "
                    f"entry={self.entry_price:.5f}, sl={self.sl_price:.5f}, "
                    f"tp={self.tp_price:.5f} (1 AU = {self.au_pips}p)"
                )
                return sig

        # ── STATE: IN_TRADE ────────────────────────────────────────────
        # Monitor TP (wick or close) and SL (CLOSE-ONLY)
        # Reference: cerebus_dual_engine.md (Zero-Buffer SL, close-only)
        elif self.state == EngineState.IN_TRADE:
            if self.impulse_direction == TradeDirection.LONG:
                # TP check: wick OR close
                if bar.high >= self.tp_price:
                    exit_price = self.tp_price
                    _entry = self.entry_price
                    _sl = self.sl_price
                    _tp = self.tp_price
                    _dir = self.impulse_direction
                    _loop = self.loop_count
                    self._reset_state_keep_loop(exit_price)
                    self.loop_count = min(_loop + 1, self.max_loops)
                    self.loop_start_time = bar.timestamp
                    sig = TradeSignal(
                        event="TP_HIT",
                        direction=_dir,
                        entry_price=_entry,
                        sl_price=_sl,
                        tp_price=_tp,
                        au_used=self.au_pips,
                        timestamp=bar.timestamp,
                        reason=f"TP = 1 AU reached (wick or close) – loop {_loop} complete",
                        loop_count=_loop,
                    )
                    self.signal_log.append(sig)
                    self.logger.info(f"TP HIT: exit={exit_price:.5f} (loop {_loop} -> {self.loop_count})")
                    return sig

                # SL check: CLOSE-ONLY (wicks don't count)
                if bar.close <= self.sl_price:
                    exit_price = self.sl_price
                    _entry = self.entry_price
                    _sl = self.sl_price
                    _tp = self.tp_price
                    _dir = self.impulse_direction
                    _loop = self.loop_count
                    self._reset_state_keep_loop(exit_price)
                    self.loop_count = min(_loop + 1, self.max_loops)
                    self.loop_start_time = bar.timestamp
                    sig = TradeSignal(
                        event="SL_HIT",
                        direction=_dir,
                        entry_price=_entry,
                        sl_price=_sl,
                        tp_price=_tp,
                        au_used=self.au_pips,
                        timestamp=bar.timestamp,
                        reason=f"Zero-Buffer SL hit (close-only invalidation) – loop {_loop} complete",
                        loop_count=_loop,
                    )
                    self.signal_log.append(sig)
                    self.logger.info(f"SL HIT: exit={exit_price:.5f} (loop {_loop} -> {self.loop_count})")
                    return sig

            else:  # SHORT
                # TP check: wick OR close
                if bar.low <= self.tp_price:
                    exit_price = self.tp_price
                    _entry = self.entry_price
                    _sl = self.sl_price
                    _tp = self.tp_price
                    _dir = self.impulse_direction
                    _loop = self.loop_count
                    self._reset_state_keep_loop(exit_price)
                    self.loop_count = min(_loop + 1, self.max_loops)
                    self.loop_start_time = bar.timestamp
                    sig = TradeSignal(
                        event="TP_HIT",
                        direction=_dir,
                        entry_price=_entry,
                        sl_price=_sl,
                        tp_price=_tp,
                        au_used=self.au_pips,
                        timestamp=bar.timestamp,
                        reason=f"TP = 1 AU reached (wick or close) – loop {_loop} complete",
                        loop_count=_loop,
                    )
                    self.signal_log.append(sig)
                    self.logger.info(f"TP HIT: exit={exit_price:.5f} (loop {_loop} -> {self.loop_count})")
                    return sig

                # SL check: CLOSE-ONLY
                if bar.close >= self.sl_price:
                    exit_price = self.sl_price
                    _entry = self.entry_price
                    _sl = self.sl_price
                    _tp = self.tp_price
                    _dir = self.impulse_direction
                    _loop = self.loop_count
                    self._reset_state_keep_loop(exit_price)
                    self.loop_count = min(_loop + 1, self.max_loops)
                    self.loop_start_time = bar.timestamp
                    sig = TradeSignal(
                        event="SL_HIT",
                        direction=_dir,
                        entry_price=_entry,
                        sl_price=_sl,
                        tp_price=_tp,
                        au_used=self.au_pips,
                        timestamp=bar.timestamp,
                        reason=f"Zero-Buffer SL hit (close-only invalidation) – loop {_loop} complete",
                        loop_count=_loop,
                    )
                    self.signal_log.append(sig)
                    self.logger.info(f"SL HIT: exit={exit_price:.5f} (loop {_loop} -> {self.loop_count})")
                    return sig

        return None

    # ── State Reset ────────────────────────────────────────────────────

    def _reset_state(self, new_origin: float) -> None:
        """
        Reset state machine to SEARCH with new swing origin.

        Reference: cerebus_resolution_engine.py _reset_state
        """
        self.state = EngineState.SEARCH
        self.swing_origin = new_origin
        self.impulse_direction = TradeDirection.FLAT
        self.impulse_extreme = 0.0
        self.impulse_size_pips = 0.0
        self.kill_switch_level = 0.0
        self.entry_price = None
        self.sl_price = None
        self.tp_price = None

    def _reset_state_keep_loop(self, new_origin: float) -> None:
        """
        Reset state machine to SEARCH after trade exit (Option B).
        Keeps loop_count (incremented by caller), clears kill switch.
        swing_origin set to exit_price (NOT impulse_extreme).

        Reference: Option B — Continuous Loop, 3-5 loops per session
        """
        self.state = EngineState.SEARCH
        self.swing_origin = new_origin
        self.impulse_direction = TradeDirection.FLAT
        self.impulse_extreme = 0.0
        self.impulse_size_pips = 0.0
        self.kill_switch_level = 0.0
        self.entry_price = None
        self.sl_price = None
        self.tp_price = None

    def hard_exit(self) -> None:
        """
        12:00 PM EST forced termination.

        Reference: manual_ontology.md Computable Q7 (engine termination)
        """
        self.session_active = False
        self.state = EngineState.SEARCH
        self.swing_origin = None
        self.loop_count = 1
        self.loop_start_time = None
        self.cascade_bias = None
        self.logger.info("Hard exit: 12 PM EST — session terminated, loops reset")

    # ── Utility ───────────────────────────────────────────────────────

    def get_status(self) -> Dict:
        """Return current engine state for monitoring."""
        return {
            "state": self.state.value,
            "tier": self.tier_name,
            "au_pips": self.au_pips,
            "trigger_pips": self.trigger_pips,
            "asian_range_pips": round(self.asian_range_pips, 1),
            "swing_origin": self.swing_origin,
            "impulse_direction": self.impulse_direction.name,
            "impulse_extreme": self.impulse_extreme,
            "kill_switch_level": self.kill_switch_level,
            "active_trade": self.state == EngineState.IN_TRADE,
            "entry": self.entry_price,
            "sl": self.sl_price,
            "tp": self.tp_price,
        }
