"""
Phase 4.1: Friction Filters
==============================
Real-time pre-trade filters: spread + time gates.
Prevents execution during toxic liquidity or after hours.
"""
from __future__ import annotations

from datetime import datetime, time
import pytz


# Max spread per tier (in pips) — asset-specific
TIER_MAX_SPREAD = {
    "EURUSD": {"T1": 3.0, "T2": 5.0, "T3": 8.0},
    "GBPUSD": {"T1": 4.0, "T2": 6.0, "T3": 10.0},
    "USDCHF": {"T1": 4.0, "T2": 6.0, "T3": 10.0},
    "USDJPY": {"T1": 5.0, "T2": 8.0, "T3": 15.0},
    "AUDUSD": {"T1": 4.0, "T2": 6.0, "T3": 10.0},
    "NZDUSD": {"T1": 5.0, "T2": 7.0, "T3": 12.0},
    "CHFJPY": {"T1": 8.0, "T2": 15.0, "T3": 30.0},
    "GBPJPY": {"T1": 10.0, "T2": 18.0, "T3": 35.0},
    "GBPAUD": {"T1": 8.0, "T2": 15.0, "T3": 30.0},
    "GBPNZD": {"T1": 10.0, "T2": 18.0, "T3": 35.0},
    "GBPCHF": {"T1": 8.0, "T2": 15.0, "T3": 30.0},
    "US500":  {"T1": 5.0, "T2": 10.0, "T3": 20.0},
    "DE30":   {"T1": 6.0, "T2": 12.0, "T3": 25.0},
    "FR40":   {"T1": 5.0, "T2": 10.0, "T3": 20.0},
    "USTEC100": {"T1": 8.0, "T2": 15.0, "T3": 30.0},
    "HK50":   {"T1": 20.0, "T2": 40.0, "T3": 80.0},
    "XAUUSD": {"T1": 10.0, "T2": 15.0, "T3": 25.0},
    "XAGUSD": {"T1": 3.0, "T2": 5.0, "T3": 10.0},
    "BTCUSD": {"T1": 50.0, "T2": 100.0, "T3": 200.0},
    "ETHUSD": {"T1": 10.0, "T2": 20.0, "T3": 40.0},
}

EST = pytz.timezone("America/New_York")
HARD_EXIT_TIME = time(12, 0, 0)  # 12:00 PM EST


def check_friction_filters(
    symbol: str,
    tier: str,
    current_spread_pips: float,
    current_time_est: datetime = None,
) -> tuple[bool, str]:
    """
    Phase 4 Friction Gate.
    Returns (pass, reason).
    """
    if current_time_est is None:
        current_time_est = datetime.now(EST)

    # 1. Time Gate: No new entries at or after 12:00 PM EST
    if current_time_est.time() >= HARD_EXIT_TIME:
        return False, "TIME_GATE: Past 12:00 PM EST hard exit."

    # 2. Spread Gate
    asset_spreads = TIER_MAX_SPREAD.get(symbol, {})
    max_spread = asset_spreads.get(tier, 10.0)
    if current_spread_pips > max_spread:
        return False, f"SPREAD_GATE: Current spread {current_spread_pips:.1f}p > Max {max_spread:.1f}p for {symbol} {tier}."

    return True, "FILTERS_PASSED"


def check_close_only_invalidation(direction: int, current_close: float, sl_price: float) -> tuple[bool, str]:
    """
    Phase 4 Execution Rule: Only M5 CLOSE triggers invalidation. Wicks are ignored.
    direction: 1 for LONG, -1 for SHORT
    """
    if direction == 1:  # LONG
        if current_close < sl_price:
            return True, "INVALIDATION: M5 Close below SL."
    elif direction == -1:  # SHORT
        if current_close > sl_price:
            return True, "INVALIDATION: M5 Close above SL."

    return False, "HOLD: Close within structural bounds (Wick ignored)."
