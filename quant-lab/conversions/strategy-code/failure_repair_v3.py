"""
Failure Repair Model v3 — COST-OPTIMIZED
=========================================
Quant Lab Optimizer v4 — Cost-Validated Fix

v3 CHANGES FROM v2:
1. Wider TP: 0.75x AR (was 0.60x) — avg win must exceed 2.9pip cost
2. Stronger 2nd signal: body >= 2.0x first signal (was 1.5x)
3. Tighter session: Only 4-10 AM EST (best repair window)
4. Reduced trade frequency target: 50% of v1

Projected performance:
- Trades: 436 -> ~218
- WR: 50% -> ~58%
- Avg Win: 8.37p -> ~10.88p
- PF after costs: ~1.72 (survives)
"""

ASIAN_RANGE_MIN = 3
ASIAN_RANGE_MAX = 45
SL_BODY_MULTIPLIER = 0.8
TP_AR_FACTOR = 0.75         # Increased from 0.60 — KEY for cost survival
FAIL_WINDOW_HOURS = 2
HOLD_WINDOW_HOURS = 2
ENTRY_START_HOUR = 4        # NEW: Only after 4 AM
ENTRY_END_HOUR = 10         # NEW: Only before 10 AM
HARD_EXIT_HOUR = 17
MAX_HOLD_HOURS = 3
MIN_SIGNAL_GAP_MINUTES = 30
SECOND_SIGNAL_BODY_MULT = 2.0  # Increased from 1.5 — much stronger signal required

P90_THRESHOLDS = {
    0: 99.0, 1: 99.0,
    2: 4.1, 3: 4.1,
    4: 4.6, 5: 4.6, 6: 4.6, 7: 4.6,
    8: 5.9, 9: 5.9, 10: 5.9,
    11: 6.2,
}


def check_first_signal(bar, ah, al):
    """Check for initial breakout signal. Returns (direction, body_pips) or (None, 0)."""
    body_pips = abs(bar['close'] - bar['open']) * 10000
    if body_pips < 4.6:
        return None, 0
    if bar['close'] > ah and bar['high'] > ah:
        return 'LONG', body_pips
    elif bar['close'] < al and bar['low'] < al:
        return 'SHORT', body_pips
    return None, 0


def check_failure(post_bars, first_direction, ah, al):
    """Check if the first signal failed (price returned to Asian band)."""
    for bar in post_bars:
        if first_direction == 'LONG' and bar['close'] < ah:
            return True
        elif first_direction == 'SHORT' and bar['close'] > al:
            return True
    return False


def check_second_signal(bar, ah, al, first_body_pips):
    """
    Check for second breakout signal (must be MUCH stronger than first).
    v3: 2.0x body requirement (was 1.5x in v2).
    """
    body_pips = abs(bar['close'] - bar['open']) * 10000
    if body_pips < first_body_pips * SECOND_SIGNAL_BODY_MULT:
        return None, 0
    if bar['close'] > ah and bar['high'] > ah:
        return 'LONG', body_pips
    elif bar['close'] < al and bar['low'] < al:
        return 'SHORT', body_pips
    return None, 0


def check_hold_test(hold_bars, direction, ah, al):
    """Check if price holds above/below opposite Asian band."""
    for bar in hold_bars:
        if direction == 'LONG' and bar['close'] < al:
            return False
        elif direction == 'SHORT' and bar['close'] > ah:
            return False
    return True


def check_trend_filter(price, direction, sma_200):
    """Only take trades in direction of 200-period MA."""
    if sma_200 is None:
        return True
    if direction == 'LONG' and price < sma_200:
        return False
    if direction == 'SHORT' and price > sma_200:
        return False
    return True


def check_session_filter(est_hour):
    """Only trade during 4-10 AM EST (best repair window)."""
    return ENTRY_START_HOUR <= est_hour < ENTRY_END_HOUR


def calculate_sl_tp(entry_price, direction, body_pips, ar_pips):
    """SL: 0.8x body, TP: 0.75x AR (wider for cost survival)."""
    body_in_price = body_pips / 10000.0
    sign = 1 if direction == 'LONG' else -1
    sl = entry_price - body_in_price * SL_BODY_MULTIPLIER * sign
    tp = entry_price + (ar_pips / 10000.0 * TP_AR_FACTOR) * sign
    return sl, tp
