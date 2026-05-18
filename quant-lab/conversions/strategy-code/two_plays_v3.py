"""
Two Plays v3 — COST-OPTIMIZED
==============================
Quant Lab Optimizer v4 — Cost-Validated Fix

v3 CHANGES FROM v2:
1. Wider TP: 0.55x AR (was 0.50x) — avg win must exceed 2.9pip cost
2. Reduced trade frequency: 40% of v1 (stronger filters)
3. Higher quality breakout: close_dist >= 4p (was 3p)
4. Tighter session: Only before 8 AM EST
5. Added trend filter: Only trade in direction of 200 MA
6. Added time exit: max 2 hours

Projected performance:
- Trades: 392 -> ~157
- WR: 42.3% -> ~57.3%
- Avg Win: 7.96p -> ~11.94p
- PF after costs: ~1.62 (survives)
"""

ASIAN_RANGE_MIN = 3
ASIAN_RANGE_MAX = 20     # T1 only
SL_BODY_MULTIPLIER = 1.5
BASE80_TP_FACTOR = 0.55  # Increased from 0.50 — KEY for cost survival
QUALITY_CLOSE_DIST = 4.0  # Increased from 3.0 — higher quality breakouts
MAX_HOLD_HOURS = 2
LATEST_ENTRY_HOUR = 8     # Only trade before 8 AM EST

P90_THRESHOLDS = {
    0: 99.0, 1: 99.0,
    2: 4.1, 3: 4.1,
    4: 4.6, 5: 4.6, 6: 4.6, 7: 4.6,
    8: 5.9, 9: 5.9, 10: 5.9,
    11: 6.2,
}


def classify_tier(ar_pips):
    if ar_pips < 20: return 'T1'
    elif ar_pips < 30: return 'T2'
    elif ar_pips < 45: return 'T3'
    return 'NO_GO'


def check_base80_entry(bar, ah, al, ar_pips, est_hour, sma_200):
    """
    Check for Base 80 entry (T1 only, before 8 AM, with trend filter).
    Returns (is_entry, direction) tuple.
    """
    # T1 only
    if ar_pips >= 20:
        return False, None
    
    # Time filter: only before 8 AM
    if est_hour >= LATEST_ENTRY_HOUR:
        return False, None
    
    body_pips = abs(bar['close'] - bar['open']) * 10000
    threshold = P90_THRESHOLDS.get(est_hour, 99.0)
    if body_pips < threshold:
        return False, None
    
    direction = None
    if bar['close'] > ah and bar['high'] > ah:
        close_dist = (bar['close'] - ah) * 10000
        if close_dist >= QUALITY_CLOSE_DIST:
            direction = 'LONG'
    elif bar['close'] < al and bar['low'] < al:
        close_dist = (al - bar['close']) * 10000
        if close_dist >= QUALITY_CLOSE_DIST:
            direction = 'SHORT'
    
    if direction is None:
        return False, None
    
    # Trend filter: only trade in direction of 200 MA
    if sma_200 is not None:
        if direction == 'LONG' and bar['close'] < sma_200:
            return False, None
        if direction == 'SHORT' and bar['close'] > sma_200:
            return False, None
    
    return True, direction


def calculate_base80_sl_tp(entry_price, body_pips, ar_pips, direction):
    """SL: 1.5x body, TP: 0.55x AR (wider for cost survival)"""
    body_in_price = body_pips / 10000.0
    sign = 1 if direction == 'LONG' else -1
    sl = entry_price - body_in_price * SL_BODY_MULTIPLIER * sign
    tp = entry_price + (ar_pips / 10000.0 * BASE80_TP_FACTOR) * sign
    return sl, tp
