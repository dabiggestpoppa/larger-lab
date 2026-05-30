"""
CEREBUS Resolution Engine — Definitive Python Reference Implementation
Source: MAD Ontology Extraction (2026-05-29)
Mode: Mechanical / Structural / Executable
Trader Language: PURGED

Finite-state machine tracking recursive deficit resolution.
No indicators. No moving averages. No discretionary logic.
"""

import pandas as pd
import numpy as np


class CerebusResolutionEngine:
    def __init__(self, pip_size, tier_config):
        """
        tier_config example for EUR/USD:
        {
            'T1': {'max_ar': 20, 'au': 10, 'trig': 12},
            'T2': {'max_ar': 30, 'au': 12, 'trig': 15},
            'T3': {'max_ar': 45, 'au': 15, 'trig': 19}
        }
        """
        self.pip = pip_size
        self.tiers = tier_config

        # State Variables
        self.state = "SEARCH"
        self.swing_origin = None
        self.impulse_dir = 0  # 1 = Long, -1 = Short
        self.impulse_extreme = 0.0
        self.impulse_size_pips = 0.0
        self.kill_switch_lvl = 0.0
        self.active_au = 0.0

        # Trade Variables
        self.entry_px = 0.0
        self.sl_px = 0.0
        self.tp_px = 0.0

    def classify_tier(self, asian_range_pips):
        for tier, cfg in self.tiers.items():
            if asian_range_pips <= cfg['max_ar']:
                return tier, cfg['au'], cfg['trig']
        return "NO-GO", 0, 0

    def process_bar(self, bar, asian_hi, asian_lo):
        """
        Pass each new M5 bar (dict/Series with 'open', 'high', 'low', 'close')
        and the daily Asian Range bounds.
        """
        # Calculate current AU and Trigger based on daily Tier
        ar_pips = (asian_hi - asian_lo) / self.pip
        tier, au_pips, trig_pips = self.classify_tier(ar_pips)

        if tier == "NO-GO":
            return None  # Stand down

        self.active_au = au_pips * self.pip
        active_trig = trig_pips * self.pip

        # Calculate distances from swing origin
        if self.swing_origin is None:
            self.swing_origin = bar['close']

        up_move = bar['high'] - self.swing_origin
        dn_move = self.swing_origin - bar['low']

        # ─────────────────────────────────────────────────────────────
        # STATE 1: SEARCH (Impulse Detection)
        # ─────────────────────────────────────────────────────────────
        if self.state == "SEARCH":
            if up_move >= active_trig:
                self.impulse_dir = 1
                self.impulse_extreme = bar['high']
                self.impulse_size_pips = up_move / self.pip
                self.kill_switch_lvl = self.impulse_extreme - (up_move * 0.80)
                self.state = "WAIT_RETRACE"

            elif dn_move >= active_trig:
                self.impulse_dir = -1
                self.impulse_extreme = bar['low']
                self.impulse_size_pips = dn_move / self.pip
                self.kill_switch_lvl = self.impulse_extreme + (dn_move * 0.80)
                self.state = "WAIT_RETRACE"

        # ─────────────────────────────────────────────────────────────
        # STATE 2: WAIT_RETRACE (AU / Fib Penetration)
        # ─────────────────────────────────────────────────────────────
        elif self.state == "WAIT_RETRACE":
            # 1. Check 80% Kill Switch (Close-Only Invalidation)
            if self.impulse_dir == 1 and bar['close'] < self.kill_switch_lvl:
                self._reset_state(bar['close'])
                return None
            elif self.impulse_dir == -1 and bar['close'] > self.kill_switch_lvl:
                self._reset_state(bar['close'])
                return None

            # 2. Check Structural Penetration (1 AU OR 38.2%-50% Fib)
            pullback_px = abs(bar['low'] - self.impulse_extreme) if self.impulse_dir == 1 else abs(bar['high'] - self.impulse_extreme)
            pullback_pips = pullback_px / self.pip
            retrace_pct = pullback_pips / self.impulse_size_pips if self.impulse_size_pips > 0 else 0

            au_penetrated = pullback_pips >= au_pips
            fib_penetrated = 0.382 <= retrace_pct <= 0.500

            if au_penetrated or fib_penetrated:
                self.state = "WAIT_OCC"

        # ─────────────────────────────────────────────────────────────
        # STATE 3: WAIT_OCC (Pathway Acceptance)
        # ─────────────────────────────────────────────────────────────
        elif self.state == "WAIT_OCC":
            # Re-verify Kill Switch
            if self.impulse_dir == 1 and bar['close'] < self.kill_switch_lvl:
                self._reset_state(bar['close'])
                return None
            elif self.impulse_dir == -1 and bar['close'] > self.kill_switch_lvl:
                self._reset_state(bar['close'])
                return None

            # Check for Opposite Candle Close (OCC)
            is_bull_candle = bar['close'] > bar['open']
            is_bear_candle = bar['close'] < bar['open']

            occ_confirmed = (self.impulse_dir == 1 and is_bull_candle) or \
                            (self.impulse_dir == -1 and is_bear_candle)

            if occ_confirmed:
                self.entry_px = bar['close']
                self.sl_px = self.impulse_extreme  # ZERO BUFFER SL
                self.tp_px = self.entry_px + (self.active_au * self.impulse_dir)
                self.state = "IN_TRADE"
                return self._generate_signal("ENTRY")

        # ─────────────────────────────────────────────────────────────
        # STATE 4: IN_TRADE (Resolution & Loop Reset)
        # ─────────────────────────────────────────────────────────────
        elif self.state == "IN_TRADE":
            # TP Check (Wick or Close)
            tp_hit = (self.impulse_dir == 1 and bar['high'] >= self.tp_px) or \
                     (self.impulse_dir == -1 and bar['low'] <= self.tp_px)

            # SL Check (CLOSE-ONLY INVALIDATION)
            sl_hit = (self.impulse_dir == 1 and bar['close'] <= self.sl_px) or \
                     (self.impulse_dir == -1 and bar['close'] >= self.sl_px)

            if tp_hit:
                self._reset_state(self.tp_px)
                return self._generate_signal("TP_HIT")
            elif sl_hit:
                self._reset_state(self.sl_px)
                return self._generate_signal("SL_HIT")

        return None

    def _reset_state(self, new_origin):
        """Continuous Loop Reset: Option B Architecture"""
        self.state = "SEARCH"
        self.swing_origin = new_origin
        self.impulse_dir = 0
        self.impulse_extreme = 0.0
        self.impulse_size_pips = 0.0

    def _generate_signal(self, event_type):
        return {
            "event": event_type,
            "dir": "LONG" if self.impulse_dir == 1 else "SHORT",
            "entry": self.entry_px,
            "sl": self.sl_px,
            "tp": self.tp_px,
            "au_used": self.active_au / self.pip
        }
