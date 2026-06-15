"""
CEREBUS FX v4.0 — Symmetry Trap Engine (Simple SL)
=====================================================
Same ST logic as symmetry_trap.py but with SIMPLE stop loss:
  - SL = entry ± buffer_pips (buffer above/below entry)
  - No OCC extreme, no profit lock, no impulse extreme tracking
  - Just a fixed buffer distance from entry

This is the "regular stop loss" — simple and clean.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("cerebus.symmetry_trap_simple_sl")


# ─── CONSTANTS ──────────────────────────────────────────────────────────

ASIAN_SESSION_START = 19   # 19:00 EST
ASIAN_SESSION_END = 3      # 03:00 EST
HARD_RESET_HOUR = 12       # 12:00 EST
HARD_EXIT_HOUR = 17        # 17:00 EST
KILL_SWITCH_PCT = 0.80
MAX_LOOPS = 5
EST_OFFSET = -5

DEFAULT_TIER_CONFIG: Dict[str, Dict[str, float]] = {
    "T1": {"ar_max": 60.0, "au": 10.0, "trigger": 12.0},
    "T2": {"ar_max": 60.0, "au": 12.0, "trigger": 15.0},
    "T3": {"ar_max": 60.0, "au": 15.0, "trigger": 19.0},
}


# ─── ENUMS ──────────────────────────────────────────────────────────────

class EngineState(Enum):
    SEARCH = "SEARCH"
    WAIT_RETRACE = "WAIT_RETRACE"
    WAIT_OCC = "WAIT_OCC"
    IN_TRADE = "IN_TRADE"


class TradeDirection(Enum):
    LONG = 1
    SHORT = -1
    FLAT = 0


# ─── DATA ───────────────────────────────────────────────────────────────

@dataclass
class Bar:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float


@dataclass
class TradeSignal:
    event: str
    direction: Optional[TradeDirection]
    entry_price: Optional[float]
    sl_price: Optional[float]
    tp_price: Optional[float]
    au_used: Optional[float]
    timestamp: Optional[datetime]
    reason: str = ""
    loop_count: int = 1


# ─── TIER CLASSIFICATION ─────────────────────────────────────────────────

def classify_tier_by_impulse(
    impulse_size_pips: float,
    tier_config: Dict[str, Dict[str, float]] = DEFAULT_TIER_CONFIG
) -> Tuple[str, float, float]:
    """Classify tier by impulse leg size using tier_config trigger values."""
    t1_cfg = tier_config.get("T1", {})
    t2_cfg = tier_config.get("T2", {})
    t3_cfg = tier_config.get("T3", {})
    t2_trigger = t2_cfg.get("trigger", 30.0)
    t3_trigger = t3_cfg.get("trigger", 45.0)
    if impulse_size_pips < t2_trigger:
        tier_name = "T1"
    elif impulse_size_pips <= t3_trigger:
        tier_name = "T2"
    else:
        tier_name = "T3"
    cfg = tier_config.get(tier_name, t1_cfg)
    return tier_name, cfg["au"], cfg["trigger"]


# ─── CORE ENGINE ─────────────────────────────────────────────────────────

class SymmetryTrapEngineSimpleSL:
    """
    Symmetry Trap with Simple Buffer SL.
    
    SL = entry ± buffer_pips (no OCC extreme, no profit lock)
    TP = 1 AU from entry
    Same state machine: SEARCH → WAIT_RETRACE → WAIT_OCC → IN_TRADE
    """

    def __init__(
        self,
        pip_size: float = 0.0001,
        tier_config: Optional[Dict[str, Dict[str, float]]] = None,
        symbol: str = "EURUSD",
        config: Optional[Dict] = None,
    ):
        self.pip_size = config.get("pip_value", pip_size) if config else pip_size
        # Extract tier_config from config dict if not explicitly passed
        if tier_config is None and config is not None:
            tier_config = config.get("tiers")
        self.tier_config = tier_config or DEFAULT_TIER_CONFIG
        self.symbol = symbol

        # Session state
        self.asian_high = 0.0
        self.asian_low = 99999.0
        self.asian_range_pips = 0.0
        self.session_active = False

        # Tier
        self.tier_name = "T1"
        self.au_pips = 10.0
        self.trigger_pips = 12.0

        # State machine
        self.state = EngineState.SEARCH
        self.swing_origin: Optional[float] = None
        self.impulse_direction = TradeDirection.FLAT
        self.impulse_extreme = 0.0
        self.impulse_size_pips = 0.0
        self.kill_switch_level = 0.0

        # Trade management
        self.entry_price: Optional[float] = None
        self.sl_price: Optional[float] = None
        self.tp_price: Optional[float] = None
        self.trade_placed = False

        # Loop tracking
        self.loop_count = 1
        self.loop_start_ts: Optional[int] = None

        # Stats
        self.total_trades = 0
        self.wins = 0
        self.losses = 0
        self.total_pnl_pips = 0.0
        self.signal_log: List[TradeSignal] = []

    def initialize_session(self, asian_high: float, asian_low: float) -> None:
        """Initialize session at 3AM EST from Asian Range."""
        self.asian_high = asian_high
        self.asian_low = asian_low
        self.asian_range_pips = (asian_high - asian_low) / self.pip_size

        # AR gate: uses T1 ar_max as session filter
        ar_max = self.tier_config.get("T1", {}).get("ar_max", 60.0)
        if self.asian_range_pips > ar_max:
            self.tier_name = "NO_GO"
            self.au_pips = 0.0
            self.trigger_pips = 0.0
        else:
            self.tier_name = "T1"
            cfg = self.tier_config.get("T1", {"au": 10.0, "trigger": 12.0})
            self.au_pips = cfg["au"]
            self.trigger_pips = cfg["trigger"]

        self.active_au = self.au_pips * self.pip_size
        self.session_active = self.tier_name != "NO_GO"

        self.state = EngineState.SEARCH
        self.swing_origin = None
        self.impulse_direction = TradeDirection.FLAT
        self.impulse_extreme = 0.0
        self.impulse_size_pips = 0.0
        self.kill_switch_level = 0.0
        self.entry_price = None
        self.sl_price = None
        self.tp_price = None
        self.loop_count = 1
        self.loop_start_ts = None

    def _classify_tier_by_impulse(self) -> None:
        """Reclassify tier based on impulse leg size."""
        self.tier_name, self.au_pips, _ = classify_tier_by_impulse(
            self.impulse_size_pips, self.tier_config
        )
        self.active_au = self.au_pips * self.pip_size

    def _est_hour(self, bar: Bar) -> int:
        utc_hour = bar.timestamp.hour
        return (utc_hour + EST_OFFSET) % 24

    def _reset_state(self, new_origin: float):
        """Reset state machine after trade exit."""
        self.state = EngineState.SEARCH
        self.swing_origin = new_origin
        self.impulse_direction = TradeDirection.FLAT
        self.impulse_extreme = 0.0
        self.impulse_size_pips = 0.0
        self.kill_switch_level = 0.0
        self.entry_price = None
        self.sl_price = None
        self.tp_price = None
        self.trade_placed = False

    def _advance_loop(self):
        """Increment loop counter."""
        self.loop_count += 1
        if self.loop_count > MAX_LOOPS:
            self.session_active = False

    def _record_trade(self, result: str, pnl_pips: float):
        """Record trade result."""
        self.total_trades += 1
        self.total_pnl_pips += pnl_pips
        if pnl_pips > 0:
            self.wins += 1
        elif pnl_pips < 0:
            self.losses += 1

    def hard_exit(self):
        """12PM hard reset."""
        if self.session_active and self.state == EngineState.IN_TRADE:
            if self.entry_price and self.impulse_direction != TradeDirection.FLAT:
                last_close = self.entry_price  # approximate
                if self.impulse_direction == TradeDirection.LONG:
                    pnl = (last_close - self.entry_price) / self.pip_size
                else:
                    pnl = (self.entry_price - last_close) / self.pip_size
                self._record_trade("12PM_EXIT", pnl)
        self._reset_state(0.0)
        self.session_active = False

    def process_bar(self, bar: Bar) -> Optional[TradeSignal]:
        """Process each M5 bar through the state machine."""
        if not self.session_active:
            return None

        est_hour = self._est_hour(bar)

        # 12PM hard reset
        if est_hour >= HARD_RESET_HOUR:
            self.hard_exit()
            return None

        # 5PM hard exit
        if est_hour >= HARD_EXIT_HOUR:
            self.hard_exit()
            return None

        # Bootstrap swing origin
        if self.swing_origin is None:
            self.swing_origin = bar.close

        active_trig = self.trigger_pips * self.pip_size
        up_move = bar.high - self.swing_origin
        dn_move = self.swing_origin - bar.low

        signal = None

        # ── STATE: SEARCH ──────────────────────────────────────────────
        if self.state == EngineState.SEARCH:
            if up_move >= active_trig:
                self.impulse_direction = TradeDirection.LONG
                self.impulse_extreme = bar.high
                self.impulse_size_pips = up_move / self.pip_size
                self._classify_tier_by_impulse()
                self.kill_switch_level = self.impulse_extreme - up_move * KILL_SWITCH_PCT
                self.state = EngineState.WAIT_RETRACE

            elif dn_move >= active_trig:
                self.impulse_direction = TradeDirection.SHORT
                self.impulse_extreme = bar.low
                self.impulse_size_pips = dn_move / self.pip_size
                self._classify_tier_by_impulse()
                self.kill_switch_level = self.impulse_extreme + dn_move * KILL_SWITCH_PCT
                self.state = EngineState.WAIT_RETRACE

        # ── STATE: WAIT_RETRACE ────────────────────────────────────────
        elif self.state == EngineState.WAIT_RETRACE:
            # Kill switch check
            if self.impulse_direction == TradeDirection.LONG:
                if bar.close < self.kill_switch_level:
                    self._advance_loop()
                    self._reset_state(bar.close)
                    return None
                pullback = self.impulse_extreme - bar.low
            else:
                if bar.close > self.kill_switch_level:
                    self._advance_loop()
                    self._reset_state(bar.close)
                    return None
                pullback = bar.high - self.impulse_extreme

            pullback_pips = pullback / self.pip_size
            retrace_pct = pullback_pips / self.impulse_size_pips if self.impulse_size_pips > 0 else 0

            # DZ: 1 AU or 32-50% Fib
            au_penetrated = pullback_pips >= self.au_pips
            fib_penetrated = 0.32 <= retrace_pct <= 0.50

            if au_penetrated or fib_penetrated:
                self.state = EngineState.WAIT_OCC

        # ── STATE: WAIT_OCC ────────────────────────────────────────────
        elif self.state == EngineState.WAIT_OCC:
            # Kill switch re-verify
            if self.impulse_direction == TradeDirection.LONG:
                if bar.close < self.kill_switch_level:
                    self._advance_loop()
                    self._reset_state(bar.close)
                    return None
            else:
                if bar.close > self.kill_switch_level:
                    self._advance_loop()
                    self._reset_state(bar.close)
                    return None

            # OCC: candle closing in impulse direction
            occ = (
                (self.impulse_direction == TradeDirection.LONG and bar.close > bar.open) or
                (self.impulse_direction == TradeDirection.SHORT and bar.close < bar.open)
            )

            if occ:
                self.entry_price = bar.close
                # SIMPLE SL: entry ± buffer (no OCC extreme)
                if self.impulse_direction == TradeDirection.LONG:
                    self.sl_price = self.entry_price - (self.au_pips * self.pip_size)
                    self.tp_price = self.entry_price + (self.active_au * self.impulse_direction.value)
                else:
                    self.sl_price = self.entry_price + (self.au_pips * self.pip_size)
                    self.tp_price = self.entry_price + (self.active_au * self.impulse_direction.value)

                self.state = EngineState.IN_TRADE
                self.trade_placed = True

                signal = TradeSignal(
                    event="ENTRY",
                    direction=self.impulse_direction,
                    entry_price=self.entry_price,
                    sl_price=self.sl_price,
                    tp_price=self.tp_price,
                    au_used=self.au_pips,
                    timestamp=bar.timestamp,
                    reason=f"Simple SL: entry ± {self.au_pips}p buffer",
                    loop_count=self.loop_count,
                )
                self.signal_log.append(signal)

        # ── STATE: IN_TRADE ────────────────────────────────────────────
        elif self.state == EngineState.IN_TRADE:
            if self.impulse_direction == TradeDirection.LONG:
                # TP check: wick or close
                if bar.high >= self.tp_price:
                    pnl = (self.tp_price - self.entry_price) / self.pip_size
                    self._record_trade("TP", pnl)
                    signal = TradeSignal(event="TP_HIT", direction=TradeDirection.LONG,
                                        entry_price=self.entry_price, sl_price=self.sl_price,
                                        tp_price=self.tp_price, au_used=self.au_pips,
                                        timestamp=bar.timestamp, loop_count=self.loop_count)
                    self._advance_loop()
                    self._reset_state(self.entry_price)
                # SL check: close-only
                elif bar.close <= self.sl_price:
                    pnl = (self.sl_price - self.entry_price) / self.pip_size
                    self._record_trade("SL", pnl)
                    signal = TradeSignal(event="SL_HIT", direction=TradeDirection.LONG,
                                        entry_price=self.entry_price, sl_price=self.sl_price,
                                        tp_price=self.tp_price, au_used=self.au_pips,
                                        timestamp=bar.timestamp, loop_count=self.loop_count)
                    self._advance_loop()
                    self._reset_state(self.entry_price)

            else:  # SHORT
                if bar.low <= self.tp_price:
                    pnl = (self.entry_price - self.tp_price) / self.pip_size
                    self._record_trade("TP", pnl)
                    signal = TradeSignal(event="TP_HIT", direction=TradeDirection.SHORT,
                                        entry_price=self.entry_price, sl_price=self.sl_price,
                                        tp_price=self.tp_price, au_used=self.au_pips,
                                        timestamp=bar.timestamp, loop_count=self.loop_count)
                    self._advance_loop()
                    self._reset_state(self.entry_price)
                elif bar.close >= self.sl_price:
                    pnl = (self.entry_price - self.sl_price) / self.pip_size
                    self._record_trade("SL", pnl)
                    signal = TradeSignal(event="SL_HIT", direction=TradeDirection.SHORT,
                                        entry_price=self.entry_price, sl_price=self.sl_price,
                                        tp_price=self.tp_price, au_used=self.au_pips,
                                        timestamp=bar.timestamp, loop_count=self.loop_count)
                    self._advance_loop()
                    self._reset_state(self.entry_price)

        return signal
