"""
CEREBUS FX v4.0 — P90 Kinetic Engine with DMR (Deep Mean Reversion)
====================================================================

DMR is a nested sub-routine inside the P90 IN_TRADE state — NOT a separate
strategy or independent state machine. It has no standalone existence.

ONTOLOGY SOURCES:
  - cerebus_p90.md               (P90 kinetic threshold)
  - cerebus_dual_engine.md       (Model A table, engine isolation)
  - manual_ontology.md           (55 Q&As)

DMR SUB-ROUTINE DESCRIPTION:
  When P90 enters IN_TRADE, a conditional limit order is placed immediately
  at the Deep State (DS) coordinate — 200% of the P90 body beyond the
  activation boundary, in the OPPOSITE direction of the P90 trade.

  The DMR limit sits passively. If price reverses sharply enough to reach DS,
  the limit fills, creating a counter-trend position that profits from mean
  reversion back toward the P90 TP2 coordinate (-50% AR).

  The DMR shares the P90's exact SL boundary. One boundary governs both.

  If P90 SL or TP is hit first, the DMR limit is cancelled immediately.

AXIOMS ENFORCED:
  1. DMR = conditional limit order inside P90 IN_TRADE. Not a strategy.
  2. DMR limit placed IMMEDIATELY on P90 entry.
  3. DMR entry = limit order at DS (NOT market).
  4. DMR direction = OPPOSITE of P90 direction.
  5. DMR SL = SAME boundary as P90 SL (one boundary, both positions).
  6. DMR TP = -50% AR (the P90 TP2 coordinate).
  7. DMR has NO standalone bias filter or state machine.
  8. P90 exit always cancels/clears DMR.

RECONSTRUCTED FROM CEREBUS ONTOLOGY per MAD Directive (2026-05-29)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, time, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum

# ─── CONSTANTS ────────────────────────────────────────────────────────────

ASIAN_SESSION_START = time(19, 0)
ASIAN_SESSION_END = time(3, 0)
ACTIVATION_START = time(3, 0)
ACTIVATION_END = time(12, 0)

# P90 minimum body as fraction of AU
DEFAULT_P90_THRESHOLDS = {
    2: 4.1, 3: 4.1,
    4: 4.6, 5: 4.6, 6: 4.6,
    7: 5.9, 8: 5.9,
    9: 6.2, 10: 6.2,
    11: 999.0,
}

DEFAULT_TIER_CONFIG = {
    "T1": {"ar_max": 20.0, "au": 10.0, "trigger": 12.0},
    "T2": {"ar_max": 30.0, "au": 12.0, "trigger": 15.0},
    "T3": {"ar_max": 45.0, "au": 15.0, "trigger": 19.0},
}

CASCADE_WINDOW_MINUTES = 120


# ─── ENUMS ────────────────────────────────────────────────────────────────

class P90Variant(Enum):
    INITIAL = "INITIAL"
    CASCADE = "CASCADE"
    EWS = "EWS"


class EngineState(Enum):
    SEARCH = "SEARCH"
    IN_TRADE = "IN_TRADE"


class TradeDirection(Enum):
    LONG = 1
    SHORT = -1
    FLAT = 0


# ─── DATA STRUCTURES ──────────────────────────────────────────────────────

@dataclass
class Bar:
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


@dataclass
class P90Signal:
    event: str
    variant: P90Variant
    direction: TradeDirection
    entry_price: Optional[float]
    sl_price: Optional[float]
    tp_price: Optional[float]
    tp2_price: Optional[float] = None
    p90_body_pips: float = 0.0
    timestamp: Optional[datetime] = None
    reason: str = ""


# ─── TIER CLASSIFICATION ──────────────────────────────────────────────────

def classify_tier(
    asian_range_pips: float,
    tier_config: Dict = DEFAULT_TIER_CONFIG
) -> Tuple[str, float, float]:
    for tier_name in ("T1", "T2", "T3"):
        if tier_name in tier_config and asian_range_pips <= tier_config[tier_name]["ar_max"]:
            cfg = tier_config[tier_name]
            return tier_name, cfg["au"], cfg["trigger"]
    return "NO_GO", 0.0, 0.0


# ─── P90 THRESHOLD CALIBRATION ───────────────────────────────────────────

def get_p90_threshold(est_hour: int, p90_config: Dict[int, float] = None) -> float:
    cfg = p90_config or DEFAULT_P90_THRESHOLDS
    return cfg.get(est_hour, 999.0)


def calibrate_p90(
    all_m5_bars: List[Bar],
    est_hours: Tuple = (3, 4, 5, 6, 7, 8, 9, 10, 11),
    lookback_months: int = 3
) -> Dict[int, float]:
    body_by_hour: Dict[int, List[float]] = {h: [] for h in est_hours}
    for bar in all_m5_bars:
        est_hour = (bar.timestamp.hour - 5) % 24
        if est_hour in body_by_hour:
            body_by_hour[est_hour].append(bar.body_abs)

    result = {}
    for hour in est_hours:
        bodies = body_by_hour[hour]
        if len(bodies) >= 10:
            sorted_bodies = sorted(bodies)
            idx = int(len(sorted_bodies) * 0.9)
            result[hour] = sorted_bodies[min(idx, len(sorted_bodies) - 1)]
        else:
            result[hour] = DEFAULT_P90_THRESHOLDS.get(hour, 4.6)
    return result


# ─── DMR SUB-ROUTINE ─────────────────────────────────────────────────────

def calc_deep_state(
    activation_boundary: float,
    p90_body_price: float,
    p90_direction: TradeDirection,
) -> float:
    """
    Calculate the Deep State (DS) coordinate — the DMR limit entry price.

    Deep State = 200% of P90 body from the activation boundary (NOT from entry).

    Bull P90: DS = asian_high + 2.0 * body   (above the band)
    Bear P90: DS = asian_low  - 2.0 * body   (below the band)

    This is the 200% extension — the Deep State terminal coordinate per
    cerebus_qa_recap.md Q6 / manual_ontology.md Q6+Q9.
    """
    if p90_direction == TradeDirection.LONG:
        return activation_boundary + 2.0 * p90_body_price
    elif p90_direction == TradeDirection.SHORT:
        return activation_boundary - 2.0 * p90_body_price
    return activation_boundary


def check_dmr_triggered(
    bar: Bar,
    deep_state: float,
    p90_direction: TradeDirection,
) -> bool:
    """
    Check if price has reached the Deep State coordinate.

    CORRECTED DIRECTIONAL CHECK:
      Bull P90 (DS above) → bar['high'] >= DS  (price must RISE to 200%)
      Bear P90 (DS below) → bar['low']  <= DS  (price must FALL to 200%)

    NOTE: For a LONG P90, DS is ABOVE asian_high (wicks must reach it).
    The OPPOSITE side check (bar['low']) is WRONG — that would mean price
    reversed below the mean reversion target instead of reaching it.
    """
    if p90_direction == TradeDirection.LONG:
        # DS is above the band — price must rise to reach it
        return bar.high >= deep_state
    elif p90_direction == TradeDirection.SHORT:
        # DS is below the band — price must fall to reach it
        return bar.low <= deep_state
    return False


# ─── CORE P90 + DMR ENGINE ────────────────────────────────────────────────

class P90Engine:
    """
    CEREBUS Model A: P90 Kinetic Engine with DMR Nested Sub-Routine

    DMR is NOT a separate strategy. It is a conditional limit order that
    lives INSIDE the P90 IN_TRADE state. It has no independent existence.

    DMR SUB-ROUTINE FLOW:
      1. P90 enters IN_TRADE → DMR limit placed at DS immediately
      2. Each bar: check if price reaches DS (limit fill)
      3. If DMR fills → monitor DMR TP and shared SL
      4. If P90 SL hit → cancel DMR limit, close P90, full reset
      5. If P90 TP hit → cancel DMR limit, close P90, full reset
      6. If DMR TP hit → close DMR, P90 runner continues
      7. If DMR SL hit (= P90 SL) → close both, full reset
    """

    def __init__(
        self,
        pip_size: float = 0.0001,
        p90_config: Optional[Dict[int, float]] = None,
        tier_config: Optional[Dict] = None,
        symbol: str = "EURUSD",
        target_mode: str = "both",
    ):
        self.pip_size = pip_size
        self.p90_config = p90_config or DEFAULT_P90_THRESHOLDS.copy()
        self.tier_config = tier_config or DEFAULT_TIER_CONFIG.copy()
        self.symbol = symbol
        self.target_mode = target_mode
        self.logger = logging.getLogger(f"cerebus.p90_dmr.{symbol}")

        # ── State Machine ──────────────────────────────────────────────
        self.state = EngineState.SEARCH
        self.active_variant = P90Variant.INITIAL

        # ── Trade State ────────────────────────────────────────────────
        self.direction = TradeDirection.FLAT
        self.entry_price: Optional[float] = None
        self.sl_price: Optional[float] = None
        self.tp1_price: Optional[float] = None
        self.tp2_price: Optional[float] = None
        self.p90_body_pips: float = 0.0
        self.p90_body_price: float = 0.0

        # ── Session State ──────────────────────────────────────────────
        self.asian_high: float = 0.0
        self.asian_low: float = 0.0
        self.asian_range_pips: float = 0.0
        self.ar_price: float = 0.0
        self.tier_name: str = "T1"
        self.session_active: bool = False

        # ── Cascade State ──────────────────────────────────────────────
        self.p90_count: int = 0
        self.last_p90_exit_time: Optional[datetime] = None

        # ── Timing ─────────────────────────────────────────────────────
        self.last_bar_time: Optional[datetime] = None

        # ── Logging ────────────────────────────────────────────────────
        self.signal_log: List[P90Signal] = []

        # ════════════════════════════════════════════════════════════════
        # DMR SUB-ROUTINE STATE (nested inside P90 IN_TRADE)
        # ════════════════════════════════════════════════════════════════
        self.dmr_limit_placed: bool = False    # Is the limit order sitting at DS?
        self.dmr_active: bool = False           # Has the limit been filled?
        self.dmr_entry_price: Optional[float] = None   # DS price (limit fill)
        self.dmr_sl_price: Optional[float] = None      # = P90 SL (shared boundary)
        self.dmr_tp_price: Optional[float] = None      # -50% AR (P90 TP2 coord)
        self.dmr_direction: TradeDirection = TradeDirection.FLAT  # Opposite of P90

    # ── Session Initialization ────────────────────────────────────────

    def initialize_session(self, asian_high: float, asian_low: float) -> None:
        self.asian_high = asian_high
        self.asian_low = asian_low
        self.ar_price = asian_high - asian_low
        self.asian_range_pips = self.ar_price / self.pip_size

        self.tier_name, au_pips, trigger_pips = classify_tier(
            self.asian_range_pips, self.tier_config
        )
        self.session_active = self.tier_name != "NO_GO"

        # Reset state machine
        self.state = EngineState.SEARCH
        self.active_variant = P90Variant.INITIAL
        self.direction = TradeDirection.FLAT
        self.entry_price = None
        self.sl_price = None
        self.tp1_price = None
        self.tp2_price = None
        self.p90_body_pips = 0.0
        self.p90_body_price = 0.0
        self.p90_count = 0
        self.last_p90_exit_time = None

        # Reset DMR sub-routine
        self._reset_dmr()

        self.logger.info(
            f"Session initialized: tier={self.tier_name}, "
            f"AR={self.asian_range_pips:.1f}p"
        )

    # ── DMR Sub-Routine: Reset ────────────────────────────────────────

    def _reset_dmr(self) -> None:
        """Clear all DMR state. Called on any P90 exit."""
        self.dmr_limit_placed = False
        self.dmr_active = False
        self.dmr_entry_price = None
        self.dmr_sl_price = None
        self.dmr_tp_price = None
        self.dmr_direction = TradeDirection.FLAT

    # ── DMR Sub-Routine: Place Limit ─────────────────────────────────

    def _place_dmr_limit(self) -> None:
        """
        Place the DMR conditional limit order at Deep State.

        Called IMMEDIATELY when P90 enters IN_TRADE.

        DS calculation:
          Bull P90: DS = asian_high + 2.0 * p90_body_price
          Bear P90: DS = asian_low  - 2.0 * p90_body_price

        DMR direction = OPPOSITE of P90 direction.
        DMR SL = P90 SL (shared boundary — one boundary governs both).
        DMR TP = -50% AR (the P90 TP2 coordinate, mean reversion target).
        """
        if self.direction == TradeDirection.FLAT or self.p90_body_price == 0.0:
            return

        # Calculate Deep State from the activation boundary
        if self.direction == TradeDirection.LONG:
            activation_boundary = self.asian_high
        else:
            activation_boundary = self.asian_low

        deep_state = calc_deep_state(
            activation_boundary, self.p90_body_price, self.direction
        )

        self.dmr_limit_placed = True
        self.dmr_entry_price = deep_state
        self.dmr_direction = (
            TradeDirection.SHORT if self.direction == TradeDirection.LONG
            else TradeDirection.LONG
        )
        self.dmr_sl_price = self.sl_price  # SHARED boundary

        # DMR TP = -50% AR (the P90 TP2 coordinate — mean reversion target)
        if self.direction == TradeDirection.LONG:
            # P90 is LONG → DMR is SHORT → TP below entry
            self.dmr_tp_price = deep_state - (self.ar_price * 0.50)
        else:
            # P90 is SHORT → DMR is LONG → TP above entry
            self.dmr_tp_price = deep_state + (self.ar_price * 0.50)

        self.logger.info(
            f"DMR LIMIT PLACED: dir={self.dmr_direction.name} "
            f"@ DS={deep_state:.5f}, SL={self.dmr_sl_price:.5f}, "
            f"TP={self.dmr_tp_price:.5f}"
        )

    # ── DMR Sub-Routine: Cancel Limit ────────────────────────────────

    def _cancel_dmr_limit(self) -> None:
        """Cancel pending DMR limit order (if not yet filled)."""
        if self.dmr_limit_placed and not self.dmr_active:
            self.logger.info("DMR LIMIT CANCELLED: P90 exited before DMR trigger")
            self._reset_dmr()
            sig = P90Signal(
                event="DMR_CANCELLED",
                variant=self.active_variant,
                direction=self.direction,
                entry_price=self.entry_price,
                sl_price=self.sl_price,
                tp_price=self.tp1_price,
                p90_body_pips=self.p90_body_pips,
                timestamp=self.last_bar_time,
                reason="DMR limit cancelled: P90 exited before DS reached"
            )
            self.signal_log.append(sig)
            return sig
        return None

    # ── DMR Sub-Routine: Evaluate on Each Bar ────────────────────────

    def _evaluate_dmr(self, bar: Bar) -> Optional[P90Signal]:
        """
        Evaluate DMR sub-routine conditions on each bar during IN_TRADE.

        This is called from process_bar() inside the IN_TRADE state.
        It handles:
          1. DMR limit fill (price reaches DS)
          2. DMR TP hit (mean reversion profit)
          3. DMR SL hit (= P90 SL, shared boundary)
        """
        # ── Check 1: DMR limit fill ───────────────────────────────────
        if self.dmr_limit_placed and not self.dmr_active:
            if check_dmr_triggered(bar, self.dmr_entry_price, self.direction):
                self.dmr_active = True
                self.logger.info(
                    f"DMR TRIGGERED: {self.dmr_direction.name} filled "
                    f"@ {self.dmr_entry_price:.5f}"
                )
                sig = P90Signal(
                    event="DMR_TRIGGERED",
                    variant=self.active_variant,
                    direction=self.dmr_direction,
                    entry_price=self.dmr_entry_price,
                    sl_price=self.dmr_sl_price,
                    tp_price=self.dmr_tp_price,
                    p90_body_pips=self.p90_body_pips,
                    timestamp=bar.timestamp,
                    reason=(
                        f"DMR limit filled at DS={self.dmr_entry_price:.5f}, "
                        f"dir={self.dmr_direction.name} (opposite P90), "
                        f"SL(shared)={self.dmr_sl_price:.5f}, "
                        f"TP(-50%AR)={self.dmr_tp_price:.5f}"
                    )
                )
                self.signal_log.append(sig)
                return sig

        # ── Check 2: DMR active — monitor TP and SL ──────────────────
        if self.dmr_active:
            if self.dmr_direction == TradeDirection.LONG:
                # DMR LONG: TP above, SL below
                if self.dmr_tp_price and bar.high >= self.dmr_tp_price:
                    dmr_entry = self.dmr_entry_price
                    dmr_tp = self.dmr_tp_price
                    self.logger.info(
                        f"DMR TP HIT: LONG TP={dmr_tp:.5f}"
                    )
                    self._reset_dmr()
                    sig = P90Signal(
                        event="DMR_TP_HIT",
                        variant=self.active_variant,
                        direction=TradeDirection.LONG,
                        entry_price=dmr_entry,
                        sl_price=self.sl_price,
                        tp_price=dmr_tp,
                        p90_body_pips=self.p90_body_pips,
                        timestamp=bar.timestamp,
                        reason="DMR TP hit (-50% AR mean reversion target). P90 runner continues."
                    )
                    self.signal_log.append(sig)
                    return sig

                # DMR SL = P90 SL (shared boundary)
                if bar.close <= self.dmr_sl_price:
                    dmr_entry = self.dmr_entry_price
                    dmr_sl = self.dmr_sl_price
                    _p90_entry = self.entry_price
                    _p90_sl = self.sl_price
                    _p90_tp1 = self.tp1_price
                    _var = self.active_variant
                    _dir = self.direction
                    self._reset_state()
                    self._reset_dmr()
                    sig = P90Signal(
                        event="DMR_SL_HIT",
                        variant=_var,
                        direction=_dir,
                        entry_price=_p90_entry,
                        sl_price=_p90_sl,
                        tp_price=_p90_tp1,
                        p90_body_pips=self.p90_body_pips,
                        timestamp=bar.timestamp,
                        reason=(
                            f"DMR SL HIT (shared boundary={dmr_sl:.5f}). "
                            f"DMR entry={dmr_entry:.5f}. "
                            f"P90 runner also closed (same boundary)."
                        )
                    )
                    self.signal_log.append(sig)
                    return sig

            elif self.dmr_direction == TradeDirection.SHORT:
                # DMR SHORT: TP below, SL above
                if self.dmr_tp_price and bar.low <= self.dmr_tp_price:
                    dmr_entry = self.dmr_entry_price
                    dmr_tp = self.dmr_tp_price
                    self.logger.info(
                        f"DMR TP HIT: SHORT TP={dmr_tp:.5f}"
                    )
                    self._reset_dmr()
                    sig = P90Signal(
                        event="DMR_TP_HIT",
                        variant=self.active_variant,
                        direction=TradeDirection.SHORT,
                        entry_price=dmr_entry,
                        sl_price=self.sl_price,
                        tp_price=dmr_tp,
                        p90_body_pips=self.p90_body_pips,
                        timestamp=bar.timestamp,
                        reason="DMR TP hit (-50% AR mean reversion target). P90 runner continues."
                    )
                    self.signal_log.append(sig)
                    return sig

                # DMR SL = P90 SL (shared boundary)
                if bar.close >= self.dmr_sl_price:
                    dmr_entry = self.dmr_entry_price
                    dmr_sl = self.dmr_sl_price
                    _p90_entry = self.entry_price
                    _p90_sl = self.sl_price
                    _p90_tp1 = self.tp1_price
                    _var = self.active_variant
                    _dir = self.direction
                    self._reset_state()
                    self._reset_dmr()
                    sig = P90Signal(
                        event="DMR_SL_HIT",
                        variant=_var,
                        direction=_dir,
                        entry_price=_p90_entry,
                        sl_price=_p90_sl,
                        tp_price=_p90_tp1,
                        p90_body_pips=self.p90_body_pips,
                        timestamp=bar.timestamp,
                        reason=(
                            f"DMR SL HIT (shared boundary={dmr_sl:.5f}). "
                            f"DMR entry={dmr_entry:.5f}. "
                            f"P90 runner also closed (same boundary)."
                        )
                    )
                    self.signal_log.append(sig)
                    return sig

        return None

    # ── P90 Validation ───────────────────────────────────────────────

    def _is_p90(self, bar: Bar, est_hour: int) -> bool:
        body_pips = bar.body_abs / self.pip_size
        threshold = get_p90_threshold(est_hour, self.p90_config)
        return body_pips >= threshold

    def _is_boundary_breach(self, bar: Bar) -> bool:
        breach_up = bar.close > self.asian_high
        breach_down = bar.close < self.asian_low
        return breach_up or breach_down

    def _detect_variant(self, bar: Bar, est_hour: int) -> P90Variant:
        if (self.last_p90_exit_time is not None and
                self.p90_count > 0 and
                bar.timestamp - self.last_p90_exit_time <= timedelta(minutes=CASCADE_WINDOW_MINUTES)):
            self.logger.info(
                f"Cascade P90 detected: #{self.p90_count + 1}, "
                f"delta={bar.timestamp - self.last_p90_exit_time}"
            )
            return P90Variant.CASCADE
        return P90Variant.INITIAL

    # ── Trade Parameter Calculation ──────────────────────────────────

    def _calc_trade_params(
        self, bar: Bar, variant: P90Variant, direction: TradeDirection
    ) -> Tuple[float, float, Optional[float], Optional[float]]:
        body_price = bar.body_abs
        self.p90_body_price = body_price
        self.p90_body_pips = body_price / self.pip_size

        entry = bar.close

        if variant == P90Variant.INITIAL:
            sl_offset = body_price * 0.80
            ar_target_1 = self.ar_price * 0.25
            ar_target_2 = self.ar_price * 0.50

            if direction == TradeDirection.LONG:
                sl = entry - sl_offset
                tp1 = entry + ar_target_1
                tp2 = entry + ar_target_2
            else:
                sl = entry + sl_offset
                tp1 = entry - ar_target_1
                tp2 = entry - ar_target_2

        elif variant == P90Variant.CASCADE:
            sl_offset = body_price * 1.68
            ar_target_1 = self.ar_price * 0.25
            ar_target_2 = self.ar_price * 0.50

            if direction == TradeDirection.LONG:
                sl = entry - sl_offset
                tp1 = entry + ar_target_1
                tp2 = entry + ar_target_2
            else:
                sl = entry + sl_offset
                tp1 = entry - ar_target_1
                tp2 = entry - ar_target_2

        else:
            sl_offset = body_price * 0.80
            if direction == TradeDirection.LONG:
                sl = entry - sl_offset
                tp1 = entry + self.ar_price * 0.25
                tp2 = entry + self.ar_price * 0.50
            else:
                sl = entry + sl_offset
                tp1 = entry - self.ar_price * 0.25
                tp2 = entry - self.ar_price * 0.50

        return entry, sl, tp1, tp2

    # ── Main Processing Loop ─────────────────────────────────────────

    def process_bar(self, bar: Bar) -> Optional[P90Signal]:
        """
        Process each M5 bar through P90 + DMR engine.

        DMR sub-routine is evaluated INSIDE the IN_TRADE state block.
        """
        if not self.session_active:
            return None

        est_hour = (bar.timestamp.hour - 5) % 24
        self.last_bar_time = bar.timestamp

        # ── EWS Detection (can fire in SEARCH or IN_TRADE) ───────────
        if self.state == EngineState.IN_TRADE and self._is_p90(bar, est_hour):
            bar_dir = TradeDirection.LONG if bar.body > 0 else TradeDirection.SHORT
            if bar_dir != self.direction and self._is_boundary_breach(bar):
                _entry = self.entry_price
                _sl = self.sl_price
                _tp1 = self.tp1_price
                _var = self.active_variant
                _dir = self.direction
                # Cancel any pending DMR before EWS exit
                self._reset_dmr()
                self._reset_state()
                sig = P90Signal(
                    event="EWS_EXIT",
                    variant=P90Variant.EWS,
                    direction=_dir,
                    entry_price=_entry,
                    sl_price=_sl,
                    tp_price=_tp1,
                    p90_body_pips=self.p90_body_pips,
                    timestamp=bar.timestamp,
                    reason="EWS: Opposite P90 at target — force close, NOT reversal"
                )
                self.signal_log.append(sig)
                self.logger.info("EWS EXIT: opposite P90 detected, closing position")
                return sig

        # ── STATE: SEARCH ──────────────────────────────────────────────
        if self.state == EngineState.SEARCH:
            if self._is_p90(bar, est_hour) and self._is_boundary_breach(bar):
                direction = TradeDirection.LONG if bar.body > 0 else TradeDirection.SHORT
                variant = self._detect_variant(bar, est_hour)
                entry, sl, tp1, tp2 = self._calc_trade_params(bar, variant, direction)

                self.state = EngineState.IN_TRADE
                self.direction = direction
                self.active_variant = variant
                self.entry_price = entry
                self.sl_price = sl
                self.tp1_price = tp1
                self.tp2_price = tp2
                self.p90_count += 1

                # ── Place DMR limit immediately on P90 entry ──────────
                self._place_dmr_limit()

                dir_str = "LONG" if direction == TradeDirection.LONG else "SHORT"
                tp1_str = f"{tp1:.5f}" if tp1 is not None else "N/A"
                tp2_str = f"{tp2:.5f}" if tp2 is not None else "N/A"
                self.logger.info(
                    f"ENTRY [{variant.value}]: {dir_str} @ {entry:.5f}, "
                    f"SL={sl:.5f}, TP1={tp1_str}, TP2={tp2_str}"
                )

                sig = P90Signal(
                    event="ENTRY",
                    variant=variant,
                    direction=direction,
                    entry_price=entry,
                    sl_price=sl,
                    tp_price=tp1,
                    tp2_price=tp2,
                    p90_body_pips=self.p90_body_pips,
                    timestamp=bar.timestamp,
                    reason=f"P90 {variant.value}: body >= threshold, "
                           f"boundary breach, entry on close. DMR limit placed at DS."
                )
                self.signal_log.append(sig)
                return sig

        # ── STATE: IN_TRADE ────────────────────────────────────────────
        elif self.state == EngineState.IN_TRADE:

            # ── DMR sub-routine evaluation (nested inside IN_TRADE) ────
            dmr_sig = self._evaluate_dmr(bar)
            if dmr_sig is not None:
                # DMR_SL_HIT already resets state internally
                if dmr_sig.event == "DMR_SL_HIT":
                    return dmr_sig
                # DMR_TRIGGERED or DMR_TP_HIT — P90 runner continues
                # but we still return the DMR signal for logging
                # (caller gets one signal per bar; DMR signals take priority
                #  when they fire, P90 checks happen next bar)
                return dmr_sig

            if self.direction == TradeDirection.LONG:
                # TP2 check first (it's further out)
                if self.tp2_price and bar.high >= self.tp2_price:
                    _entry = self.entry_price; _sl = self.sl_price
                    _tp1 = self.tp1_price; _tp2 = self.tp2_price
                    _var = self.active_variant; _dir = self.direction
                    cancel_sig = self._cancel_dmr_limit()
                    self._reset_state()
                    sig = P90Signal(
                        event="TP_HIT",
                        variant=_var,
                        direction=_dir,
                        entry_price=_entry,
                        sl_price=_sl,
                        tp_price=_tp2,
                        p90_body_pips=self.p90_body_pips,
                        timestamp=bar.timestamp,
                        reason="TP2 (-50% AR) hit"
                    )
                    self.signal_log.append(sig)
                    self.logger.info("TP2 HIT (-50% AR)")
                    return sig

                # TP1 check
                if self.tp1_price and bar.high >= self.tp1_price:
                    _entry = self.entry_price; _sl = self.sl_price
                    _tp1 = self.tp1_price; _tp2 = self.tp2_price
                    _var = self.active_variant; _dir = self.direction
                    cancel_sig = self._cancel_dmr_limit()
                    self._reset_state()
                    sig = P90Signal(
                        event="TP_HIT",
                        variant=_var,
                        direction=_dir,
                        entry_price=_entry,
                        sl_price=_sl,
                        tp_price=_tp1,
                        tp2_price=_tp2,
                        p90_body_pips=self.p90_body_pips,
                        timestamp=bar.timestamp,
                        reason="TP1 (-25% AR) hit"
                    )
                    self.signal_log.append(sig)
                    self.logger.info("TP1 HIT (-25% AR)")
                    return sig

                # SL check (CLOSE ONLY)
                if bar.close <= self.sl_price:
                    _entry = self.entry_price; _sl = self.sl_price
                    _tp1 = self.tp1_price; _tp2 = self.tp2_price
                    _var = self.active_variant; _dir = self.direction
                    self._reset_dmr()
                    self._reset_state()
                    sig = P90Signal(
                        event="SL_HIT",
                        variant=_var,
                        direction=_dir,
                        entry_price=_entry,
                        sl_price=_sl,
                        tp_price=_tp1,
                        p90_body_pips=self.p90_body_pips,
                        timestamp=bar.timestamp,
                        reason="SL hit (80% P90 body, close-only). DMR limit cancelled."
                    )
                    self.signal_log.append(sig)
                    self.logger.info(f"SL HIT: exit={_sl}")
                    return sig

            else:  # SHORT
                # TP2 check
                if self.tp2_price and bar.low <= self.tp2_price:
                    _entry = self.entry_price; _sl = self.sl_price
                    _tp1 = self.tp1_price; _tp2 = self.tp2_price
                    _var = self.active_variant; _dir = self.direction
                    cancel_sig = self._cancel_dmr_limit()
                    self._reset_state()
                    sig = P90Signal(
                        event="TP_HIT",
                        variant=_var,
                        direction=_dir,
                        entry_price=_entry,
                        sl_price=_sl,
                        tp_price=_tp2,
                        p90_body_pips=self.p90_body_pips,
                        timestamp=bar.timestamp,
                        reason="TP2 (-50% AR) hit"
                    )
                    self.signal_log.append(sig)
                    self.logger.info("TP2 HIT (-50% AR)")
                    return sig

                # TP1 check
                if self.tp1_price and bar.low <= self.tp1_price:
                    _entry = self.entry_price; _sl = self.sl_price
                    _tp1 = self.tp1_price; _tp2 = self.tp2_price
                    _var = self.active_variant; _dir = self.direction
                    cancel_sig = self._cancel_dmr_limit()
                    self._reset_state()
                    sig = P90Signal(
                        event="TP_HIT",
                        variant=_var,
                        direction=_dir,
                        entry_price=_entry,
                        sl_price=_sl,
                        tp_price=_tp1,
                        tp2_price=_tp2,
                        p90_body_pips=self.p90_body_pips,
                        timestamp=bar.timestamp,
                        reason="TP1 (-25% AR) hit"
                    )
                    self.signal_log.append(sig)
                    self.logger.info("TP1 HIT (-25% AR)")
                    return sig

                # SL check (CLOSE ONLY)
                if bar.close >= self.sl_price:
                    _entry = self.entry_price; _sl = self.sl_price
                    _tp1 = self.tp1_price; _tp2 = self.tp2_price
                    _var = self.active_variant; _dir = self.direction
                    self._reset_dmr()
                    self._reset_state()
                    sig = P90Signal(
                        event="SL_HIT",
                        variant=_var,
                        direction=_dir,
                        entry_price=_entry,
                        sl_price=_sl,
                        tp_price=_tp1,
                        p90_body_pips=self.p90_body_pips,
                        timestamp=bar.timestamp,
                        reason="SL hit (80% P90 body, close-only). DMR limit cancelled."
                    )
                    self.signal_log.append(sig)
                    self.logger.info(f"SL HIT: exit={_sl}")
                    return sig

        return None

    # ── State Reset ────────────────────────────────────────────────────

    def _reset_state(self) -> None:
        """Reset to SEARCH, record cascade timing."""
        self.last_p90_exit_time = self.last_bar_time
        self.state = EngineState.SEARCH
        self.direction = TradeDirection.FLAT
        self.entry_price = None
        self.sl_price = None
        self.tp1_price = None
        self.tp2_price = None
        self.p90_body_pips = 0.0
        self.p90_body_price = 0.0

    def hard_exit(self) -> None:
        """12:00 PM EST forced termination."""
        self.session_active = False
        self.state = EngineState.SEARCH
        self._reset_dmr()
        self.logger.info("Hard exit: 12 PM EST — session terminated")

    def get_status(self) -> Dict:
        return {
            "state": self.state.value,
            "variant": self.active_variant.value,
            "direction": self.direction.name,
            "tier": self.tier_name,
            "asian_range_pips": round(self.asian_range_pips, 1),
            "p90_count": self.p90_count,
            "active_trade": self.state == EngineState.IN_TRADE,
            "entry": self.entry_price,
            "sl": self.sl_price,
            "tp1": self.tp1_price,
            "tp2": self.tp2_price,
            # DMR status
            "dmr_limit_placed": self.dmr_limit_placed,
            "dmr_active": self.dmr_active,
            "dmr_entry": self.dmr_entry_price,
            "dmr_direction": self.dmr_direction.name,
        }
