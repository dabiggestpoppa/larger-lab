"""
Phase 4.1: Friction Filters
=============================
Real-time pre-trade filters that prevent execution during toxic conditions.
"""
from __future__ import annotations

from typing import Optional

TIER_MAX_SPREAD = {
    "T1": 10.0,
    "T2": 15.0,
    "T3": 25.0,
}


def check_friction_filters(
    current_hour: int,
    current_minute: int,
    current_spread_pips: float,
    tier: str = "T2",
    symbol: str = "EURUSD",
    simulated_slippage_pips: float = 0.0,
) -> tuple[bool, str]:
    """
    Pre-trade friction gate.

    Returns
    -------
    (passed: bool, reason: str)
    """
    # Time gate: hard exit at 12:00 PM
    if current_hour >= 12:
        return False, "TIME_GATE: Past 12:00 PM EST hard exit"

    # Time gate: before session start (3:00 AM)
    if current_hour < 3:
        return False, "TIME_GATE: Before 3:00 AM EST session start"

    # Spread gate
    max_spread = TIER_MAX_SPREAD.get(tier, 15.0)
    if current_spread_pips > max_spread:
        return False, f"SPREAD_GATE: {current_spread_pips:.1f}p > max {max_spread:.1f}p for {tier}"

    # Slippage gate
    max_slippage = 3.0  # pips
    if simulated_slippage_pips > max_slippage:
        return False, f"SLIPPAGE_GATE: {simulated_slippage_pips:.1f}p > max {max_slippage:.1f}p"

    return True, "ALL_FILTERS_PASSED"
