"""
Symmetry Trap Strategy — Nautilus Trader Implementation
========================================================
CEREBUS FX v4.0 — Engine B: Atomic Structural Engine

NOT DMR. Does NOT use P90 for entry. Mean reversion is WRONG here.

State Machine (4 states):
  SEARCH → WAIT_RETRACE → WAIT_OCC → IN_TRADE → (reset to SEARCH, up to 5 loops)

Core Logic:
1. Asian Session (7PM-3AM EST): accumulation/compression, track high/low
2. 3AM EST: Lock Asian Range, classify tier (T1/T2/T3 or NO-GO)
3. After 3AM (SEARCH): Detect Impulse leg exceeding trigger threshold
4. WAIT_RETRACE: DZ pullback — price retraces toward Asian Range
5. WAIT_OCC: M5 bar closes in impulse direction
6. Entry on OCC confirmation — direction WITH impulse (momentum, NOT mean reversion)
   SL: Zero-Buffer Impulse Extreme (exact high/low of impulse bar)
   TP: 1 AU from entry (single target, no ladder)
7. 80% Kill Switch: price retraces 80% of impulse leg → close immediately
8. After TP/SL: re-enter same session (up to 5 loops)
9. 12PM EST: Hard reset — all state clears
10. 5PM EST: Hard exit all positions

Engine Isolation (cerebus_dual_engine.md):
  - NEVER uses P90 body for SL/TP
  - SL = Zero-Buffer Impulse Extreme (NOT 80% P90 body)
  - TP = 1 AU from entry (NOT -25% or -50% AR)
  - Direction = WITH impulse (NOT mean reversion)
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from nautilus_trader.common.enums import LogColor
from nautilus_trader.core.message import Event
from nautilus_trader.model.data import Bar, BarType
from nautilus_trader.model.enums import OrderSide, TimeInForce
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.objects import Price, Quantity
from nautilus_trader.trading.strategy import Strategy, StrategyConfig


# ─── MACHINE READABLE ───────────────────────────────────────────────────
# Default tier configuration — EUR/USD reference (Quick Reference Card Page 2)
# For per-symbol overrides see configs/asset_configs.py

DEFAULT_TIER_CONFIG = {
    "T1": {"ar_max": 20.0, "au": 10.0, "trigger": 12.0},
    "T2": {"ar_max": 30.0, "au": 12.0, "trigger": 15.0},
    "T3": {"ar_max": 45.0, "au": 15.0, "trigger": 19.0},
}

# Per-symbol pip divisors (price * pip_divisor = pips)
PIP_DIVISORS = {
    "EURUSD.PRO": 10000.0,
    "EURUSD": 10000.0,
    "USDCHF.PRO": 10000.0,
    "USDCHF": 10000.0,
}

# Per-symbol tier configs — override EUR/USD defaults
SYMBOL_TIER_CONFIGS = {
    "EURUSD.PRO": DEFAULT_TIER_CONFIG,
    "EURUSD": DEFAULT_TIER_CONFIG,
    "USDCHF.PRO": {
        "T1": {"ar_max": 19.0, "au": 11.0, "trigger": 11.0},
        "T2": {"ar_max": 29.0, "au": 15.0, "trigger": 15.0},
        "T3": {"ar_max": 50.0, "au": 20.0, "trigger": 20.0},
    },
    "USDCHF": {
        "T1": {"ar_max": 19.0, "au": 11.0, "trigger": 11.0},
        "T2": {"ar_max": 29.0, "au": 15.0, "trigger": 15.0},
        "T3": {"ar_max": 50.0, "au": 20.0, "trigger": 20.0},
    },
}

# Structural constants
KILL_SWITCH_PCT = 0.80         # 80% of impulse leg — close-only invalidation
ASIAN_START_EST = 19           # 7PM EST — Asian session begins
ASIAN_END_EST = 3              # 3AM EST — Asian session ends, range locked
HARD_RESET_HOUR_EST = 12       # 12PM EST — all state clears (NO-GO for session)
HARD_EXIT_HOUR_EST = 17        # 5PM EST — hard exit all positions
MAX_LOOPS = 5                  # Safety cap on re-entries per session
EST_OFFSET = -5                # EST = UTC - 5


def _classify_tier(
    asian_range_pips: float,
    tier_config: dict,
) -> tuple:
    """
    Classify session volatility into discrete Tier.
    AR > T3 max → NO-GO (structural coherence collapses).

    Returns:
        (tier_name, au_pips, trigger_pips)
    """
    for tier_name in ("T1", "T2", "T3"):
        if tier_name in tier_config and asian_range_pips <= tier_config[tier_name]["ar_max"]:
            cfg = tier_config[tier_name]
            return tier_name, cfg["au"], cfg["trigger"]
    return "NO_GO", 0.0, 0.0


class SymmetryTrapConfig(StrategyConfig, frozen=True):
    """Configuration for SymmetryTrapStrategy."""

    instrument_id: str = "EURUSD.PRO"
    bar_type: str = "EURUSD.PRO-5-MINUTE-LAST-EXTERNAL"
    lot_size: Decimal = Decimal("0.01")
    magic_number: int = 20260530
    max_loops: int = MAX_LOOPS
    est_offset: int = EST_OFFSET
    asian_start_hour: int = ASIAN_START_EST
    asian_end_hour: int = ASIAN_END_EST
    hard_reset_hour: int = HARD_RESET_HOUR_EST
    hard_exit_hour: int = HARD_EXIT_HOUR_EST
    kill_switch_pct: float = KILL_SWITCH_PCT
    # Optional: override tier config for exotic symbols
    tier_config_override: Optional[dict] = None


class SymmetryTrapStrategy(Strategy):
    """
    CEREBUS FX v4.0 — Symmetry Trap (Engine B: Atomic Structural)

    State machine: SEARCH → WAIT_RETRACE → WAIT_OCC → IN_TRADE

    Momentum direction (WITH impulse), NOT mean reversion.
    SL = Zero-Buffer Impulse Extreme. TP = 1 AU. 80% Kill Switch.
    """

    def __init__(self, config: SymmetryTrapConfig):
        super().__init__(config)
        self.instrument_id = InstrumentId.from_str(config.instrument_id)
        self.bar_type = BarType.from_str(config.bar_type)
        self.lot_size = config.lot_size
        self.magic = config.magic_number
        self.max_loops = config.max_loops
        self.est_offset = config.est_offset
        self.asian_start_hour = config.asian_start_hour
        self.asian_end_hour = config.asian_end_hour
        self.hard_reset_hour = config.hard_reset_hour
        self.hard_exit_hour = config.hard_exit_hour
        self.kill_switch_pct = config.kill_switch_pct

        # ── Per-symbol config ──────────────────────────────────────────
        sym_str = str(self.instrument_id.symbol)
        self.pip_divisor = PIP_DIVISORS.get(sym_str, 10000.0)
        if config.tier_config_override is not None:
            self.tier_config = config.tier_config_override
        else:
            self.tier_config = SYMBOL_TIER_CONFIGS.get(sym_str, DEFAULT_TIER_CONFIG)

        # ── Per-session state (resets each day) ────────────────────────
        self._reset_all_state()

        # ── Statistics ─────────────────────────────────────────────────
        self.total_trades = 0
        self.wins = 0
        self.losses = 0
        self.total_pnl_pips = 0.0

        self.log.info(
            f"SymmetryTrap initialized: {self.instrument_id}",
            color=LogColor.GREEN,
        )

    # ── State Reset ────────────────────────────────────────────────────

    def _reset_all_state(self):
        """Full reset — called on new day and on 12PM hard reset."""
        # Asian range tracking
        self.asian_high = 0.0
        self.asian_low = 99999.0
        self.asian_locked = False
        self.current_date = None

        # Tier classification
        self.tier_name = "T1"
        self.au_pips = 10.0
        self.trigger_pips = 12.0
        self.asian_range_pips = 0.0
        self.session_active = False

        # State machine
        self._strategy_state = "SEARCH"                   # SEARCH | WAIT_RETRACE | WAIT_OCC | IN_TRADE
        self.swing_origin = 0.0
        self.impulse_direction = 0              # +1 LONG, -1 SHORT, 0 FLAT
        self.impulse_extreme = 0.0
        self.impulse_size_pips = 0.0
        self.kill_switch_level = 0.0
        self.active_au_price = 0.0              # AU in price units

        # Trade management
        self.entry_price = 0.0
        self.sl_price = 0.0
        self.tp_price = 0.0
        self.trade_placed = False

        # Loop tracking
        self.loop_count = 1
        self.loop_start_ts = None               # UTC ns when loop started

    def _reset_state_keep_loop_fixed(self, new_origin: float):
        """Reset state machine after trade exit, preserving loop count."""
        self._strategy_state = "SEARCH"
        self.swing_origin = new_origin
        self.impulse_direction = 0
        self.impulse_extreme = 0.0
        self.impulse_size_pips = 0.0
        self.kill_switch_level = 0.0
        self.entry_price = 0.0
        self.sl_price = 0.0
        self.tp_price = 0.0
        self.trade_placed = False

    # ── Helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _est_hour_from_bar(bar: Bar, est_offset: int) -> int:
        """Extract hour from bar timestamp, convert to EST.

        Nautilus bar.ts_event is the bar OPEN time in UTC nanoseconds.
        """
        utc_hour = (bar.ts_event // 3_600_000_000_000) % 24
        return (utc_hour + est_offset) % 24

    def _price_to_pips(self, price_delta: float) -> float:
        return price_delta * self.pip_divisor

    def _pips_to_price(self, pips: float) -> float:
        return pips / self.pip_divisor

    def _close_all_positions(self, reason: str):
        if not self.portfolio.is_flat(self.instrument_id):
            self.close_all_positions(self.instrument_id)
            self.log.info(f"CLOSED ALL: reason={reason}")

    def _advance_loop(self, bar: Bar):
        """Increment loop counter, set loop start time, cap at max_loops."""
        self.loop_count += 1
        if self.loop_count > self.max_loops:
            self.session_active = False
            self.log.info(f"Max loops ({self.max_loops}) reached — session terminated")
        else:
            self.loop_start_ts = bar.ts_event
            self.log.info(f"Loop advanced: {self.loop_count}/{self.max_loops}")

    # ── Lifecycle ──────────────────────────────────────────────────────

    def on_start(self):
        self.subscribe_bars(self.bar_type)
        self.log.info(
            f"Subscribed to {self.bar_type} | "
            f"Symbol={self.instrument_id.symbol} | "
            f"PipDiv={self.pip_divisor}",
            color=LogColor.BLUE,
        )

    def on_bar(self, bar: Bar):
        """Main strategy logic — called on each new M5 bar."""
        est_hour = self._est_hour_from_bar(bar, self.est_offset)

        # ── 12PM EST: Hard reset ──────────────────────────────────────
        if est_hour >= self.hard_reset_hour:
            if self.session_active:
                self.log.info("12PM EST hard reset — session terminated")
                self._close_all_positions("12PM_hard_reset")
            self._reset_all_state()
            return

        # ── 5PM EST: Hard exit ────────────────────────────────────────
        if est_hour >= self.hard_exit_hour:
            self._close_all_positions("5PM_hard_exit")
            return

        # ── Detect new day ────────────────────────────────────────────
        bar_date = self._ts_to_date(bar.ts_event)
        if self.current_date is None:
            self.current_date = bar_date
        elif bar_date != self.current_date:
            self._reset_all_state()
            self.current_date = bar_date
            self._last_seen_date = None  # reset static cache from _is_new_day

        # ── Phase 1: Asian Session tracking (7PM-3AM EST) ────────────
        in_asian = (est_hour >= self.asian_start_hour or est_hour < self.asian_end_hour)
        if in_asian:
            if float(bar.high) > self.asian_high:
                self.asian_high = float(bar.high)
            if float(bar.low) < self.asian_low:
                self.asian_low = float(bar.low)
            return  # No impulse detection during Asian hours

        # ── Phase 2: Initialize session at 3AM EST ────────────────────
        if not self.asian_locked and est_hour >= self.asian_end_hour:
            self.asian_locked = True
            self.asian_range_pips = self._price_to_pips(self.asian_high - self.asian_low)
            self.tier_name, self.au_pips, self.trigger_pips = _classify_tier(
                self.asian_range_pips, self.tier_config
            )
            self.active_au_price = self.au_pips / self.pip_divisor
            self.session_active = self.tier_name != "NO_GO"

            if not self.session_active:
                self.log.info(
                    f"NO-GO: AR={self.asian_range_pips:.1f}p > max tier "
                    f"— skipping session",
                    color=LogColor.RED,
                )
                return

            self._strategy_state = "SEARCH"
            self.swing_origin = float(bar.close)
            self.log.info(
                f"Session INIT: tier={self.tier_name}, AR={self.asian_range_pips:.1f}p, "
                f"AU={self.au_pips}p, trigger={self.trigger_pips}p, "
                f"swing_origin={self.swing_origin:.5f}",
                color=LogColor.YELLOW,
            )
            return  # Don't process impulse on the same bar as session init

        # ── Skip if session not active ────────────────────────────────
        if not self.session_active:
            return

        # ── Loop timeout: 4 hours without entry kills session ─────────
        if self.loop_start_ts is not None and self.loop_count > 1:
            elapsed_s = (bar.ts_event - self.loop_start_ts) / 1_000_000_000
            if elapsed_s > 4 * 3600:
                self.session_active = False
                self.log.info(
                    f"Loop {self.loop_count} expired (4h timeout) — session ended"
                )
                return

        # ── Swing origin bootstrap ────────────────────────────────────
        if self.swing_origin == 0.0:
            self.swing_origin = float(bar.close)

        # ── Delegate to state machine ─────────────────────────────────
        self._process_state_machine(bar, est_hour)

    # ── State Machine ──────────────────────────────────────────────────

    def _process_state_machine(self, bar: Bar, est_hour: int):
        """Route to correct state handler."""
        bar_open = float(bar.open)
        bar_high = float(bar.high)
        bar_low = float(bar.low)
        bar_close = float(bar.close)

        if self._strategy_state == "SEARCH":
            self._state_search(bar, bar_open, bar_high, bar_low, bar_close)
        elif self._strategy_state == "WAIT_RETRACE":
            self._state_wait_retrace(bar, bar_open, bar_high, bar_low, bar_close)
        elif self._strategy_state == "WAIT_OCC":
            self._state_wait_occ(bar, bar_open, bar_high, bar_low, bar_close)
        elif self._strategy_state == "IN_TRADE":
            self._state_in_trade(bar, bar_open, bar_high, bar_low, bar_close)

    # ── STATE: SEARCH — Impulse detection ─────────────────────────────

    def _state_search(self, bar: Bar, o: float, h: float, lo: float, c: float):
        """
        Detect impulse leg: first significant move out of Asian range
        exceeding trigger threshold.

        Impulse trigger = trigger_pips (AU x 1.20) from swing_origin.
        Reference: cerebus_qa_recap.md Q4
        """
        active_trig = self.trigger_pips / self.pip_divisor
        up_move = h - self.swing_origin  # wick-based trigger (per backtest engine uses bar.high)
        dn_move = self.swing_origin - lo

        # Engine uses bar.high / bar.low for trigger check (consistent with engine process_bar)
        up_move_close = c - self.swing_origin
        dn_move_close = self.swing_origin - c

        # Match engine: up_move = bar.high - swing_origin, dn_move = swing_origin - bar.low
        if up_move >= active_trig:
            self.impulse_direction = 1   # LONG
            self.impulse_extreme = h     # exact high of impulse bar
            self.impulse_size_pips = up_move * self.pip_divisor
            # Kill switch: 80% retracement of impulse leg (from impulse extreme toward origin)
            self.kill_switch_level = self.impulse_extreme - up_move * self.kill_switch_pct
            self._strategy_state = "WAIT_RETRACE"
            self.log.info(
                f"Impulse LONG: extreme={self.impulse_extreme:.5f}, "
                f"size={self.impulse_size_pips:.1f}p, "
                f"kill={self.kill_switch_level:.5f}, loop={self.loop_count}",
                color=LogColor.CYAN,
            )

        elif dn_move >= active_trig:
            self.impulse_direction = -1  # SHORT
            self.impulse_extreme = lo    # exact low of impulse bar
            self.impulse_size_pips = dn_move * self.pip_divisor
            self.kill_switch_level = self.impulse_extreme + dn_move * self.kill_switch_pct
            self._strategy_state = "WAIT_RETRACE"
            self.log.info(
                f"Impulse SHORT: extreme={self.impulse_extreme:.5f}, "
                f"size={self.impulse_size_pips:.1f}p, "
                f"kill={self.kill_switch_level:.5f}, loop={self.loop_count}",
                color=LogColor.CYAN,
            )

    # ── STATE: WAIT_RETRACE — DZ pullback + 80% kill switch ──────────

    def _state_wait_retrace(self, bar: Bar, o: float, h: float, lo: float, c: float):
        """
        Wait for DZ (Demand Zone) pullback — price retraces back toward Asian Range.
        Monitor 80% kill switch (close-only invalidation).
        Reference: cerebus_qa_recap.md Q5, Q8, Q9
        """
        # ── Kill Switch (close-only) ──────────────────────────────────
        if self.impulse_direction == 1:  # LONG impulse
            if c < self.kill_switch_level:
                self._handle_kill_switch(bar, c)
                return
        else:  # SHORT impulse
            if c > self.kill_switch_level:
                self._handle_kill_switch(bar, c)
                return

        # ── Dynamic DZ thresholds (Option B: Continuous Loop) ─────────
        # Loop 1: strict Goldilocks zone (32%-50%)
        # Loop 2+: relaxed floor (20%-50% — shallow momentum pullbacks)
        if self.loop_count == 1:
            min_retrace_pct = 0.32
        else:
            min_retrace_pct = 0.20
        max_retrace_pct = 0.50

        # Pullback measurement
        if self.impulse_direction == 1:  # LONG impulse
            pullback_px = self.impulse_extreme - lo
        else:  # SHORT impulse
            pullback_px = h - self.impulse_extreme

        pullback_pips = pullback_px * self.pip_divisor
        retrace_pct = (
            pullback_pips / self.impulse_size_pips
            if self.impulse_size_pips > 0 else 0
        )

        au_penetrated = pullback_pips >= self.au_pips
        fib_penetrated = min_retrace_pct <= retrace_pct <= max_retrace_pct

        if au_penetrated or fib_penetrated:
            self._strategy_state = "WAIT_OCC"
            self.log.info(
                f"DZ penetrated: pullback={pullback_pips:.1f}p, "
                f"retrace={retrace_pct:.3f}, loop={self.loop_count}",
                color=LogColor.CYAN,
            )

    # ── STATE: WAIT_OCC — Open/Close Cross ────────────────────────────

    def _state_wait_occ(self, bar: Bar, o: float, h: float, lo: float, c: float):
        """
        Detect OCC: M5 bar closes in impulse direction (confirms momentum).
        Re-verify kill switch.
        Entry on OCC confirmation — direction WITH impulse (momentum).
        Reference: cerebus_qa_recap.md Q8
        """
        # ── Kill Switch re-verify ─────────────────────────────────────
        if self.impulse_direction == 1:  # LONG impulse
            if c < self.kill_switch_level:
                self._handle_kill_switch(bar, c)
                return
        else:  # SHORT impulse
            if c > self.kill_switch_level:
                self._handle_kill_switch(bar, c)
                return

        # ── OCC: candle closing in impulse direction ──────────────────
        occ_confirmed = (
            (self.impulse_direction == 1 and c > o) or   # bullish M5 close
            (self.impulse_direction == -1 and c < o)      # bearish M5 close
        )

        if occ_confirmed:
            self.entry_price = c
            self.sl_price = self.impulse_extreme  # ZERO-BUFFER: exact impulse extreme
            self.tp_price = (
                c + self.active_au_price * self.impulse_direction
            )
            self._strategy_state = "IN_TRADE"
            self.trade_placed = True

            dir_label = "LONG" if self.impulse_direction == 1 else "SHORT"
            self.log.info(
                f"ENTRY {dir_label} (loop {self.loop_count}): "
                f"entry={self.entry_price:.5f}, "
                f"SL={self.sl_price:.5f} (zero-buffer impulse extreme), "
                f"TP={self.tp_price:.5f} (1 AU = {self.au_pips}p)",
                color=LogColor.GREEN,
            )
            self._submit_entry_order()

    # ── STATE: IN_TRADE — TP / SL monitoring ──────────────────────────

    def _state_in_trade(self, bar: Bar, o: float, h: float, lo: float, c: float):
        """
        Monitor TP (wick or close) and SL (CLOSE-ONLY).
        Reference: cerebus_dual_engine.md (Zero-Buffer SL, close-only)
        """
        if self.impulse_direction == 1:  # LONG trade
            # TP check: wick OR close
            if h >= self.tp_price:
                pnl = self._price_to_pips(self.tp_price - self.entry_price)
                self._record_trade("TP", pnl)
                self.log.info(
                    f"TP HIT: exit={self.tp_price:.5f}, pnl={pnl:+.1f}p "
                    f"(loop {self.loop_count})",
                    color=LogColor.GREEN,
                )
                self._advance_loop(bar)
                self._reset_state_keep_loop_fixed(self.entry_price)
                return

            # SL check: CLOSE-ONLY (wicks don't count)
            if c <= self.sl_price:
                pnl = self._price_to_pips(self.sl_price - self.entry_price)
                self._record_trade("SL", pnl)
                self.log.info(
                    f"SL HIT (zero-buffer impulse extreme): exit={self.sl_price:.5f}, "
                    f"pnl={pnl:+.1f}p (loop {self.loop_count})",
                    color=LogColor.RED,
                )
                self._advance_loop(bar)
                self._reset_state_keep_loop_fixed(self.entry_price)
                return

        else:  # SHORT trade
            # TP check: wick OR close
            if lo <= self.tp_price:
                pnl = self._price_to_pips(self.entry_price - self.tp_price)
                self._record_trade("TP", pnl)
                self.log.info(
                    f"TP HIT: exit={self.tp_price:.5f}, pnl={pnl:+.1f}p "
                    f"(loop {self.loop_count})",
                    color=LogColor.GREEN,
                )
                self._advance_loop(bar)
                self._reset_state_keep_loop_fixed(self.entry_price)
                return

            # SL check: CLOSE-ONLY
            if c >= self.sl_price:
                pnl = self._price_to_pips(self.entry_price - self.sl_price)
                self._record_trade("SL", pnl)
                self.log.info(
                    f"SL HIT (zero-buffer impulse extreme): exit={self.sl_price:.5f}, "
                    f"pnl={pnl:+.1f}p (loop {self.loop_count})",
                    color=LogColor.RED,
                )
                self._advance_loop(bar)
                self._reset_state_keep_loop_fixed(self.entry_price)
                return

    # ── Trade helpers ─────────────────────────────────────────────────

    def _submit_entry_order(self):
        """Submit market order for entry."""
        if self.impulse_direction == 1:
            order_side = OrderSide.BUY
        elif self.impulse_direction == -1:
            order_side = OrderSide.SELL
        else:
            self.log.error("Cannot submit order: impulse_direction is FLAT")
            return

        qty = Quantity.from_str(str(self.lot_size))

        order = self.order_factory.market(
            instrument_id=self.instrument_id,
            order_side=order_side,
            quantity=qty,
            time_in_force=TimeInForce.IOC,
            reduce_only=False,
        )
        self.submit_order(order)

    def _handle_kill_switch(self, bar: Bar, close_price: float):
        """80% Kill Switch triggered — exit immediately if in trade, then loop."""
        self.log.info(
            f"KILL SWITCH (80% impulse retracement): close={close_price:.5f}, "
            f"level={self.kill_switch_level:.5f}, loop={self.loop_count}",
            color=LogColor.RED,
        )

        # If in a trade, close it immediately
        if self._strategy_state == "IN_TRADE":
            pnl = self._compute_live_pnl(close_price)
            self._record_trade("KILL_SWITCH", pnl)

        self._advance_loop(bar)
        self._reset_state_keep_loop_fixed(close_price)

    def _compute_live_pnl(self, current_close: float) -> float:
        """Compute PnL in pips for the active trade at the given close price."""
        if self.impulse_direction == 1:
            return self._price_to_pips(current_close - self.entry_price)
        elif self.impulse_direction == -1:
            return self._price_to_pips(self.entry_price - current_close)
        return 0.0

    def _record_trade(self, result: str, pnl_pips: float):
        """Record trade result for statistics."""
        self.total_trades += 1
        self.total_pnl_pips += pnl_pips
        if pnl_pips > 0:
            self.wins += 1
        elif pnl_pips < 0:
            self.losses += 1

    # ── Day boundary detection ────────────────────────────────────────

    @staticmethod
    def _ts_to_date(ts_ns: int):
        """Convert UTC nanosecond timestamp to a date object."""
        from datetime import datetime, timezone
        return datetime.fromtimestamp(ts_ns / 1e9, tz=timezone.utc).date()

    # ── / Lifecycle ────────────────────────────────────────────────────

    def on_stop(self):
        wr = (self.wins / self.total_trades * 100.0) if self.total_trades > 0 else 0.0
        self.log.info(
            f"FINAL STATS: Trades={self.total_trades} W={self.wins} L={self.losses} "
            f"WR={wr:.1f}% PnL={self.total_pnl_pips:+.1f}p",
            color=LogColor.MAGENTA,
        )

    # ── Event handler (order fills, position changes) ─────────────────

    def on_event(self, event: Event):
        super().on_event(event)
