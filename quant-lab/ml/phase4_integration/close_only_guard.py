"""
Phase 4.2: Close-Only Invalidation Enforcer
=============================================
Ensures the live engine does not trigger a stop-loss on a wick.
Strictly adheres to the CEREBUS FX v4 Manual rule:
  Only M5 CLOSE triggers invalidation. Wicks are ignored.

This is the +82% expectancy lift mechanism.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PositionState:
    """Current state of an open position."""
    direction: int          # 1=LONG, -1=SHORT
    entry_price: float
    sl_price: float         # OCC Extreme (zero buffer)
    tp_price: float         # 1 AU (or gear-shifted AU)
    au_target: float        # Target in price units
    tier: str               # T1/T2/T3
    entry_time: str         # ISO timestamp


def check_close_only_invalidation(
    direction: int,
    current_close: float,
    sl_price: float,
) -> tuple[bool, str]:
    """
    Phase 4 Execution Rule: Only M5 CLOSE triggers invalidation. Wicks are ignored.

    Parameters
    ----------
    direction : int
        1 for LONG, -1 for SHORT.
    current_close : float
        Current bar's CLOSE price.
    sl_price : float
        Stop loss price (OCC extreme).

    Returns
    -------
    (invalidated, reason) : tuple[bool, str]
    """
    if direction == 1:  # LONG
        if current_close < sl_price:
            return True, f"INVALIDATION: M5 Close {current_close:.5f} below SL {sl_price:.5f}"
    elif direction == -1:  # SHORT
        if current_close > sl_price:
            return True, f"INVALIDATION: M5 Close {current_close:.5f} above SL {sl_price:.5f}"

    return False, "HOLD: Close within structural bounds (wick ignored)"


def check_tp_hit(direction: int, current_high: float, current_low: float, tp_price: float) -> bool:
    """
    TP check: triggers on wick OR close (asymmetric to SL).
    """
    if direction == 1:  # LONG
        return current_high >= tp_price
    else:  # SHORT
        return current_low <= tp_price


def check_812_rule(direction: int, current_close: float, asian_high: float, asian_low: float) -> tuple[bool, str]:
    """
    81.2% Rule Kill Switch: If M5 closes back inside Asian band, exit immediately.
    Overrides SL and TP.
    """
    if direction == 1:  # LONG — price closed below Asian low
        if current_close < asian_low:
            return True, f"81.2% RULE: Close {current_close:.5f} back inside Asian band (low={asian_low:.5f})"
    elif direction == -1:  # SHORT — price closed above Asian high
        if current_close > asian_high:
            return True, f"81.2% RULE: Close {current_close:.5f} back inside Asian band (high={asian_high:.5f})"

    return False, "CONTINUE: Price outside Asian band"


def check_12pm_hard_exit(current_hour: int, current_minute: int) -> tuple[bool, str]:
    """
    12PM Hard Exit: All positions close at 12:00 PM EST. No exceptions.
    """
    if current_hour >= 12:
        return True, f"HARD EXIT: {current_hour}:{current_minute:02d} EST — 12:00 PM hard exit"
    return False, "CONTINUE: Within trading window"


def manage_open_position(
    state: PositionState,
    current_bar: dict,
    current_hour: int,
    current_minute: int,
    asian_high: float,
    asian_low: float,
) -> tuple[str, str]:
    """
    Complete position management for one bar.
    Returns (action, reason).
    Actions: HOLD, TP_HIT, SL_HIT, KILL_812, HARD_EXIT_12PM
    """
    close = current_bar["close"]
    high = current_bar["high"]
    low = current_bar["low"]

    # 1. 12PM Hard Exit (absolute priority)
    triggered, reason = check_12pm_hard_exit(current_hour, current_minute)
    if triggered:
        return "HARD_EXIT_12PM", reason

    # 2. TP check (wick or close)
    if check_tp_hit(state.direction, high, low, state.tp_price):
        return "TP_HIT", f"TP touched at {state.tp_price:.5f}"

    # 3. Close-only SL check
    invalidated, reason = check_close_only_invalidation(state.direction, close, state.sl_price)
    if invalidated:
        return "SL_HIT", reason

    # 4. 81.2% Rule kill switch
    triggered, reason = check_812_rule(state.direction, close, asian_high, asian_low)
    if triggered:
        return "KILL_812", reason

    return "HOLD", "All checks passed"


if __name__ == "__main__":
    # Demo: LONG position
    state = PositionState(
        direction=1, entry_price=1.08500, sl_price=1.08300,
        tp_price=1.08620, au_target=0.00120, tier="T2",
        entry_time="2024-01-15T09:30:00"
    )

    # Test: wick below SL but close above
    bar = {"open": 1.08450, "high": 1.08500, "low": 1.08250, "close": 1.08420}
    action, reason = manage_open_position(state, bar, 10, 0, 1.08600, 1.08200)
    print(f"Wick below SL, close above: {action} — {reason}")

    # Test: close below SL
    bar2 = {"open": 1.08350, "high": 1.08380, "low": 1.08250, "close": 1.08280}
    action, reason = manage_open_position(state, bar2, 10, 0, 1.08600, 1.08200)
    print(f"Close below SL: {action} — {reason}")
