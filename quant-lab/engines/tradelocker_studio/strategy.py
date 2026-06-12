"""
TradeLocker Studio Strategy — CEREBUS Symmetry Trap + DTB Target Prediction
=========================================================================
Runs inside TradeLocker Studio's backtrader engine.
Paste this code directly into Studio's Monaco editor.

Strategy Logic (from CEREBUS ontology):
  Model B: Atomic Structural Engine (Symmetry Trap)
    - Impulse: M5 close beyond Tier Trigger (AU x 1.20) from swing origin
    - Rebalance: Pullback >= 1 AU OR 38.2%-50% Fib retracement
    - OCC: M5 candle closes BACK in impulse direction
    - Entry: Close of OCC candle
    - SL: Zero-Buffer Impulse Extreme (close-only)
    - TP: 1 AU from entry (single target)

  DTB Overlay (Variance Compression Engine):
    - At T0 (3AM): Wide target cone from Asian Range + Tier
    - At T1 (6AM): Compress by 35% using loop velocity
    - At T2 (9AM): Compress by 40% using regime confirmation
    - At T3 (10:30AM): Crush to near-certainty

  This is a MECHANICAL system — no discretion, no indicators.
  All parameters derived from CEREBUS manual_ontology.md.
"""
import backtrader as bt
import numpy as np
from datetime import time, timedelta


class CerebusSymmetryTrapStrategy(bt.Strategy):
    """
    CEREBUS Model B: Atomic Structural Engine for TradeLocker Studio.
    
    Uses backtrader's built-in indicators where possible.
    All state transitions are mechanical — no LLM calls, no discretion.
    """
    params = (
        # Tier config (AR gate decoupled from tier — June 4 optimization)
        ("ar_max", 60.0),           # AR gate: session filter only
        ("t1_au", 10.0),            # T1 AU in pips
        ("t1_trigger", 12.0),       # T1 trigger in pips
        ("t2_au", 12.0),
        ("t2_trigger", 15.0),
        ("t3_au", 15.0),
        ("t3_trigger", 19.0),
        # Session boundaries (EST)
        ("asian_start_h", 19),      # 7 PM EST — Asian session start
        ("asian_end_h", 3),         # 3 AM EST — Asian session end
        ("activation_start_h", 3),  # 3 AM EST — trading window opens
        ("activation_end_h", 16),   # 4 PM EST — hard cutoff (June 4 opt)
        ("sink_h", 12),             # 12 PM EST — temporal sink
        # DTB checkpoints
        ("t0_h", 8),                # 3 AM UTC = T0 checkpoint
        ("t1_h", 11),               # 6 AM UTC = T1 checkpoint
        ("t2_h", 14),               # 9 AM UTC = T2 checkpoint
        ("t3_h", 15),               # 10:30 UTC = T3 checkpoint
        # Risk
        ("lots_per_trade", 0.02),
        ("max_loops", 5),
        ("pip_size", 0.0001),       # 0.0001 for EURUSD, 0.01 for JPY pairs
        ("sl_min_buffer_pips", 8.0),
        ("spread_buffer_pips", 1.5),
    )

    def __init__(self):
        # ── Data ──
        self.close_price = self.datas[0].close
        self.high_price = self.datas[0].high
        self.low_price = self.datas[0].low
        self.open_price = self.datas[0].open

        # ── State Machine (4-state FSM from cerebus_resolution_engine.py) ──
        self.state = "SEARCH"           # SEARCH → WAIT_RETRACE → WAIT_OCC → IN_TRADE
        self.order = None

        # ── Impulse State ──
        self.swing_origin = None
        self.impulse_dir = 0            # 1=LONG, -1=SHORT, 0=FLAT
        self.impulse_extreme = 0.0
        self.impulse_size_pips = 0.0
        self.kill_switch_lvl = 0.0
        self.active_au = 0.0            # AU in price units

        # ── Trade State ──
        self.entry_price = None
        self.sl_price = None
        self.tp_price = None
        self.trade_direction = 0

        # ── Session State ──
        self.asian_high = 0.0
        self.asian_low = 99999.0
        self.asian_range_pips = 0.0
        self.tier_name = "T1"
        self.au_pips = 10.0
        self.trigger_pips = 12.0
        self.session_active = False
        self.current_date = None

        # ── Loop Tracking (Option B: Continuous Loop) ──
        self.loop_count = 1
        self.loop_start_time = None

        # ── DTB Tracking ──
        self.dtb_t0_target = None       # 3AM prediction
        self.dtb_t1_target = None       # 6AM update
        self.dtb_t2_target = None       # 9AM update
        self.dtb_t3_target = None       # 10:30AM update
        self.dtb_actual = 0.0           # Pips achieved so far
        self.dtb_checkpoint_log = []    # [(time, old_target, new_target)]
        self.regime_locked = False
        self.regime_ratio = 0.0

        # ── Bar Counter ──
        self.bar_count = 0

    def _est_hour(self, dt):
        """Convert datetime to EST hour (UTC-5)."""
        return (dt.hour - 5) % 24

    def _is_asian(self, est_h):
        """Check if EST hour falls in Asian session (19:00-03:00)."""
        return est_h >= 19 or est_h < 3

    def _classify_tier_by_impulse(self, impulse_size_pips):
        """Classify tier by impulse leg size (June 4 optimization)."""
        if impulse_size_pips < 20.0:
            self.tier_name = "T1"
            self.au_pips = self.p.t1_au
            self.trigger_pips = self.p.t1_trigger
        elif impulse_size_pips <= 30.0:
            self.tier_name = "T2"
            self.au_pips = self.p.t2_au
            self.trigger_pips = self.p.t2_trigger
        else:
            self.tier_name = "T3"
            self.au_pips = self.p.t3_au
            self.trigger_pips = self.p.t3_trigger
        self.active_au = self.au_pips * self.p.pip_size

    def _initialize_session(self, dt):
        """Initialize session at start of trading window (3AM EST)."""
        self.asian_high = 0.0
        self.asian_low = 99999.0
        self.current_date = dt.date()
        self.state = "SEARCH"
        self.swing_origin = None
        self.impulse_dir = 0
        self.entry_price = None
        self.sl_price = None
        self.tp_price = None
        self.loop_count = 1
        self.dtb_actual = 0.0
        self.dtb_checkpoint_log = []
        self.regime_locked = False
        self.regime_ratio = 0.0

    def _update_asian_range(self, est_h, bar_high, bar_low):
        """Update Asian Range during Asian session hours."""
        if self._is_asian(est_h):
            self.asian_high = max(self.asian_high, bar_high)
            self.asian_low = min(self.asian_low, bar_low)

    def _check_session_active(self):
        """Check if session is active based on AR gate."""
        if self.asian_high <= 0 or self.asian_low >= 99999:
            self.session_active = False
            return
        self.asian_range_pips = (self.asian_high - self.asian_low) / self.p.pip_size
        self.session_active = self.asian_range_pips <= self.p.ar_max
        if not self.session_active:
            self.tier_name = "NO_GO"

    def _update_dtb_checkpoints(self, est_h, dt):
        """
        DTB Variance Compression Engine.
        Updates target predictions at key temporal checkpoints.
        """
        if not self.session_active:
            return

        # Calculate current distribution achieved
        if self.swing_origin and self.entry_price:
            self.dtb_actual = abs(self.close_price[0] - self.swing_origin) / self.p.pip_size

        # T0: 3AM EST (8 UTC) — Initial prediction from Asian Range
        if est_h == self.p.t0_h and self.dtb_t0_target is None:
            if self.asian_range_pips > 0:
                # Base prediction: AR × tier multiplier
                tier_mult = {"T1": 0.65, "T2": 0.75, "T3": 0.85}.get(self.tier_name, 0.65)
                self.dtb_t0_target = self.asian_range_pips * tier_mult
                self.dtb_checkpoint_log.append(
                    (dt.time(), 0, self.dtb_t0_target)
                )

        # T1: 6AM EST (11 UTC) — Compress by 35% using loop velocity
        if est_h == self.p.t1_h and self.dtb_t1_target is None:
            if self.dtb_t0_target and self.dtb_actual > 0:
                velocity = self.dtb_actual / max(self.dtb_t0_target, 1)
                if velocity >= 1.0:
                    # Ahead of schedule — shift target up
                    self.dtb_t1_target = self.dtb_t0_target * 1.15
                elif velocity >= 0.65:
                    # On track — slight compression
                    self.dtb_t1_target = self.dtb_t0_target
                else:
                    # Behind — compress down
                    self.dtb_t1_target = self.dtb_t0_target * 0.80
                self.dtb_checkpoint_log.append(
                    (dt.time(), self.dtb_t0_target, self.dtb_t1_target)
                )

        # T2: 9AM EST (14 UTC) — Compress by 40% using regime
        if est_h == self.p.t2_h and self.dtb_t2_target is None:
            if self.dtb_t1_target:
                # Regime check: has price been trending or ranging?
                if self.dtb_actual > self.dtb_t1_target * 0.82:
                    # CONFIRMED regime — eliminate lower bound
                    self.dtb_t2_target = self.dtb_t1_target * 1.05
                    self.regime_locked = True
                    self.regime_ratio = 2.0
                elif self.dtb_actual > self.dtb_t1_target * 0.50:
                    # CAUTION — moderate compression
                    self.dtb_t2_target = self.dtb_t1_target * 0.95
                    self.regime_ratio = 1.0
                else:
                    # FAILED — compress significantly
                    self.dtb_t2_target = self.dtb_t1_target * 0.70
                    self.regime_ratio = 0.0
                self.dtb_checkpoint_log.append(
                    (dt.time(), self.dtb_t1_target, self.dtb_t2_target)
                )

        # T3: 10:30 EST (15:30 UTC) — Crush remaining variance
        if est_h == self.p.t3_h and self.dtb_t3_target is None:
            if self.dtb_t2_target:
                remaining_time = (self.p.sink_h - self.p.t3_h) * 60  # minutes
                max_additional_pips = remaining_time * 0.5  # ~0.5 pips/min ceiling
                self.dtb_t3_target = min(
                    self.dtb_t2_target,
                    self.dtb_actual + max_additional_pips
                )
                self.dtb_checkpoint_log.append(
                    (dt.time(), self.dtb_t2_target, self.dtb_t3_target)
                )

    def next(self):
        """
        Main strategy logic — called on each M5 candle close.
        Implements the 4-state FSM from cerebus_resolution_engine.py.
        """
        self.bar_count += 1
        dt = self.datas[0].datetime.datetime(0)
        est_h = self._est_hour(dt)

        # ── Session Management ──
        # Initialize new session at activation start (3AM EST)
        if est_h == self.p.activation_start_h and self.current_date != dt.date():
            self._initialize_session(dt)

        # Update Asian Range during Asian hours
        self._update_asian_range(est_h, self.high_price[0], self.low_price[0])

        # Check session activation at start of trading window
        if est_h == self.p.activation_start_h:
            self._check_session_active()

        # ── DTB Checkpoint Updates ──
        self._update_dtb_checkpoints(est_h, dt)

        # ── Hard Cutoff: 4PM EST ──
        if est_h >= self.p.activation_end_h and self.state == "SEARCH":
            return

        # ── Skip Asian Hours for Trading ──
        if self._is_asian(est_h):
            return

        # ── Set Swing Origin ──
        if self.swing_origin is None:
            self.swing_origin = self.close_price[0]

        if not self.session_active:
            return

        # ── Calculate distances from swing origin ──
        active_trig = self.trigger_pips * self.p.pip_size
        up_move = self.high_price[0] - self.swing_origin
        dn_move = self.swing_origin - self.low_price[0]

        # ═══════════════════════════════════════════════════════════════
        # STATE 1: SEARCH — Impulse Detection
        # ═══════════════════════════════════════════════════════════════
        if self.state == "SEARCH":
            if up_move >= active_trig:
                self.impulse_dir = 1
                self.impulse_extreme = self.high_price[0]
                self.impulse_size_pips = up_move / self.p.pip_size
                self.kill_switch_lvl = self.impulse_extreme - (up_move * 0.80)
                self._classify_tier_by_impulse(self.impulse_size_pips)
                self.state = "WAIT_RETRACE"
            elif dn_move >= active_trig:
                self.impulse_dir = -1
                self.impulse_extreme = self.low_price[0]
                self.impulse_size_pips = dn_move / self.p.pip_size
                self.kill_switch_lvl = self.impulse_extreme + (dn_move * 0.80)
                self._classify_tier_by_impulse(self.impulse_size_pips)
                self.state = "WAIT_RETRACE"

        # ═══════════════════════════════════════════════════════════════
        # STATE 2: WAIT_RETRACE — Density Zone Penetration
        # ═══════════════════════════════════════════════════════════════
        elif self.state == "WAIT_RETRACE":
            # 80% Kill Switch (close-only invalidation)
            if self.impulse_dir == 1 and self.close_price[0] < self.kill_switch_lvl:
                self._reset_to_search()
                return
            elif self.impulse_dir == -1 and self.close_price[0] > self.kill_switch_lvl:
                self._reset_to_search()
                return

            # Structural Penetration: 1 AU pullback OR 38.2-50% Fib retracement
            au_price = self.active_au
            if self.impulse_dir == 1:
                pullback = self.swing_origin - self.low_price[0]
                fib_retrace = (self.impulse_extreme - self.low_price[0]) / max(self.impulse_extreme - self.swing_origin, 0.0001)
                if pullback >= au_price or (0.382 <= fib_retrace <= 0.50):
                    self.state = "WAIT_OCC"
            elif self.impulse_dir == -1:
                pullback = self.high_price[0] - self.swing_origin
                fib_retrace = (self.high_price[0] - self.impulse_extreme) / max(self.swing_origin - self.impulse_extreme, 0.0001)
                if pullback >= au_price or (0.382 <= fib_retrace <= 0.50):
                    self.state = "WAIT_OCC"

        # ═══════════════════════════════════════════════════════════════
        # STATE 3: WAIT_OCC — Pathway Validation (Kinetic Reloading)
        # ═══════════════════════════════════════════════════════════════
        elif self.state == "WAIT_OCC":
            # 80% Kill Switch check
            if self.impulse_dir == 1 and self.close_price[0] < self.kill_switch_lvl:
                self._reset_to_search()
                return
            elif self.impulse_dir == -1 and self.close_price[0] > self.kill_switch_lvl:
                self._reset_to_search()
                return

            # OCC: candle closes BACK in impulse direction
            if self.impulse_dir == 1 and self.close_price[0] > self.open_price[0]:
                self._enter_trade("LONG")
            elif self.impulse_dir == -1 and self.close_price[0] < self.open_price[0]:
                self._enter_trade("SHORT")

        # ═══════════════════════════════════════════════════════════════
        # STATE 4: IN_TRADE — Resolution Execution
        # ═══════════════════════════════════════════════════════════════
        elif self.state == "IN_TRADE":
            if self.position:
                # Check SL (close-only)
                if self.trade_direction == 1:  # LONG
                    if self.low_price[0] <= self.sl_price:
                        self._exit_trade("SL_HIT")
                    elif self.high_price[0] >= self.tp_price:
                        self._exit_trade("TP_HIT")
                elif self.trade_direction == -1:  # SHORT
                    if self.high_price[0] >= self.sl_price:
                        self._exit_trade("SL_HIT")
                    elif self.low_price[0] <= self.tp_price:
                        self._exit_trade("TP_HIT")

    def _enter_trade(self, direction):
        """Enter trade at close of OCC candle."""
        self.entry_price = self.close_price[0]
        self.trade_direction = 1 if direction == "LONG" else -1

        # SL: Zero-Buffer Impulse Extreme (close-only)
        if direction == "LONG":
            raw_sl = self.impulse_extreme
            buffered_sl = raw_sl - (self.p.sl_min_buffer_pips * self.p.pip_size)
            self.sl_price = min(buffered_sl, raw_sl - (self.p.spread_buffer_pips * self.p.pip_size))
            # TP: 1 AU from entry
            self.tp_price = self.entry_price + self.active_au
        else:
            raw_sl = self.impulse_extreme
            buffered_sl = raw_sl + (self.p.sl_min_buffer_pips * self.p.pip_size)
            self.sl_price = max(buffered_sl, raw_sl + (self.p.spread_buffer_pips * self.p.pip_size))
            # TP: 1 AU from entry
            self.tp_price = self.entry_price - self.active_au

        # Execute order
        if direction == "LONG":
            self.order = self.buy(size=self.p.lots_per_trade)
        else:
            self.order = self.sell(size=self.p.lots_per_trade)

        self.state = "IN_TRADE"

    def _exit_trade(self, reason):
        """Exit trade and reset state."""
        if self.position:
            self.close()
        self.order = None
        self.entry_price = None
        self.sl_price = None
        self.tp_price = None
        self.trade_direction = 0

        # Option B: Continuous Loop — reset to SEARCH for next loop
        if self.loop_count < self.p.max_loops:
            self.loop_count += 1
            self.state = "SEARCH"
            self.swing_origin = self.close_price[0]
            self.impulse_dir = 0
        else:
            self.state = "SEARCH"
            self.impulse_dir = 0

    def _reset_to_search(self):
        """Reset to SEARCH state (kill switch or invalidation)."""
        self.state = "SEARCH"
        self.impulse_dir = 0
        self.swing_origin = self.close_price[0]
        self.entry_price = None
        self.sl_price = None
        self.tp_price = None

    def notify_order(self, order):
        """Handle order notifications."""
        if order.status in [order.Completed]:
            self.order = None
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.order = None
            self._reset_to_search()

    def notify_trade(self, trade):
        """Track completed trades for DTB actual calculation."""
        if trade.isclosed:
            pnl_pips = trade.pnl / self.p.pip_size
            self.dtb_actual = abs(pnl_pips)

    def stop(self):
        """Log final DTB checkpoint data."""
        if self.dtb_checkpoint_log:
            self.log("=== DTB VARIANCE COMPRESSION LOG ===")
            for check_time, old_target, new_target in self.dtb_checkpoint_log:
                self.log(
                    f"  {check_time} | {old_target:.1f} → {new_target:.1f} pips"
                )
            if self.dtb_t3_target:
                self.log(f"  FINAL TARGET: {self.dtb_t3_target:.1f} pips")
                self.log(f"  ACTUAL: {self.dtb_actual:.1f} pips")

    def log(self, msg):
        """Log message (visible in Studio's console)."""
        print(f"[{self.datas[0].datetime.datetime(0)}] {msg}")

    # ═══════════════════════════════════════════════════════════════════
    # params_metadata — Used by Studio's "Run Backtest/Bot" modal
    # ═══════════════════════════════════════════════════════════════════
    params_metadata = {
        "lots_per_trade": {
            "label": "Lots per Trade",
            "helper_text": "All trades will use this amount of lots",
            "value_type": "float",
        },
        "ar_max": {
            "label": "AR Max (pips)",
            "helper_text": "Asian Range gate — session filter only",
            "value_type": "float",
        },
        "t1_au": {
            "label": "T1 AU (pips)",
            "helper_text": "Tier 1 Atomic Unit in pips",
            "value_type": "float",
        },
        "t2_au": {
            "label": "T2 AU (pips)",
            "helper_text": "Tier 2 Atomic Unit in pips",
            "value_type": "float",
        },
        "t3_au": {
            "label": "T3 AU (pips)",
            "helper_text": "Tier 3 Atomic Unit in pips",
            "value_type": "float",
        },
    }
