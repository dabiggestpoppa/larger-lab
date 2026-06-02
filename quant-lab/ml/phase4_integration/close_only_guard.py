"""
Phase 4.2: Close-Only Guard
=============================
Enforces the CEREBUS close-only invalidation rule.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class PositionState:
    direction: int
    entry_price: float
    sl_price: float
    tp_price: float
    au_target: float
    tier: str
    entry_time: str


def check_close_only_invalidation(direction: int, current_close: float, sl_price: float) -> tuple[bool, str]:
    """Check if M5 close beyond SL triggers invalidation."""
    if direction == 1 and current_close < sl_price:
        return True, "INVALIDATION: M5 Close below SL"
    if direction == -1 and current_close > sl_price:
        return True, "INVALIDATION: M5 Close above SL"
    return False, "HOLD: Close within structural bounds"


def check_812_rule(direction: int, current_close: float, origin_price: float) -> tuple[bool, str]:
    """Check 81.2% rule — close back inside Asian band."""
    if direction == 1 and current_close < origin_price:
        return True, "KILL_812"
    if direction == -1 and current_close > origin_price:
        return True, "KILL_812"
    return False, "SAFE"


def check_12pm_hard_exit(hour: int, minute: int) -> tuple[bool, str]:
    """Check if 12:00 PM hard exit triggered."""
    if hour >= 12:
        return True, "HARD_EXIT_12PM"
    return False, "SAFE"


def check_tp_hit(direction: int, bar_high: float, bar_low: float, tp_price: float) -> tuple[bool, str]:
    """Check if TP hit (wick or close)."""
    if direction == 1 and bar_high >= tp_price:
        return True, "TP_HIT"
    if direction == -1 and bar_low <= tp_price:
        return True, "TP_HIT"
    return False, "SAFE"


def manage_open_position(
    state: PositionState,
    bar: dict,
    hour: int,
    minute: int,
    asian_high: float,
    asian_low: float,
) -> tuple[str, str]:
    """
    Full position management — runs every bar.
    Returns (action, reason).
    """
    # 12PM hard exit
    if hour >= 12:
        return "HARD_EXIT_12PM", "12:00 PM EST hard exit"

    # TP hit (wick)
    if state.direction == 1 and bar["high"] >= state.tp_price:
        return "TP_HIT", "Take profit hit"
    if state.direction == -1 and bar["low"] <= state.tp_price:
        return "TP_HIT", "Take profit hit"

    # SL (close only)
    if state.direction == 1 and bar["close"] <= state.sl_price:
        return "SL_HIT", "M5 close below SL"
    if state.direction == -1 and bar["close"] >= state.sl_price:
        return "SL_HIT", "M5 close above SL"

    # 81.2% rule
    if state.direction == 1 and bar["close"] < asian_low:
        return "KILL_812", "81.2% rule — close back inside Asian band"
    if state.direction == -1 and bar["close"] > asian_high:
        return "KILL_812", "81.2% rule — close back inside Asian band"

    return "HOLD", "Position held"


class CloseOnlyGuard:
    """Stateful position guard."""

    def __init__(self):
        self.position = None

    def open_position(self, direction, entry_price, sl_price, tp_price, origin_price):
        self.position = {
            "direction": direction,
            "entry_price": entry_price,
            "sl_price": sl_price,
            "tp_price": tp_price,
            "origin_price": origin_price,
        }

    def check_exit(self, bar_close, bar_high, bar_low, current_time_est):
        if self.position is None:
            return False, "NO_POSITION"

        direction = self.position["direction"]
        sl_price = self.position["sl_price"]
        tp_price = self.position["tp_price"]
        origin_price = self.position["origin_price"]

        # 12PM hard exit
        if current_time_est.hour >= 12:
            return True, "HARD_EXIT_12PM"

        # TP hit (wick)
        if direction == 1 and bar_high >= tp_price:
            return True, "TP_HIT"
        if direction == -1 and bar_low <= tp_price:
            return True, "TP_HIT"

        # SL (close only)
        if direction == 1 and bar_close <= sl_price:
            return True, "SL_CLOSE_ONLY"
        if direction == -1 and bar_close >= sl_price:
            return True, "SL_CLOSE_ONLY"

        # 81.2% rule
        if direction == 1 and bar_close < origin_price:
            return True, "81PCT_RULE_KILL"
        if direction == -1 and bar_close > origin_price:
            return True, "81PCT_RULE_KILL"

        return False, "HOLD"
