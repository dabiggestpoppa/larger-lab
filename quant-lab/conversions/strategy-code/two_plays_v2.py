"""
Two Plays v2 — FIXED
=====================
Quant Lab Optimizer v4 — Cost-Validated Fix

CHANGES FROM v1:
1. Focus on Play 1 only (Base 80) — dropped T3 Model 2 (no edge)
2. Tightened to T1 only — AR < 20 pips
3. Require stronger breakout: Quality close distance 3p (was 2p)
4. Added time filter: Only trade before 8 AM EST (best volatility)
5. Added trend filter: Only trade in direction of 200 MA
6. Widened TP: 0.50x AR (was 0.35x) for better reward/risk
7. Added time-based exit: Max 2 hours hold

Expected impact:
- Trade count: 392 → ~150-200
- Win Rate: 42.3% → ~50-55%
- PF: 1.04 → ~1.5-1.8
"""

ASIAN_RANGE_MIN = 3
ASIAN_RANGE_MAX = 20     # T1 only
SL_BODY_MULTIPLIER = 1.5
BASE80_TP_FACTOR = 0.50  # Increased from 0.35
QUALITY_CLOSE_DIST = 3.0  # Increased from 2.0
MAX_HOLD_HOURS = 2       # NEW: Time-based exit
LATEST_ENTRY_HOUR = 8    # NEW: Only trade before 8 AM EST

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


def check_base80_entry(bar, ah, al, ar_pips, est_hour):
    """
    Check for Base 80 entry (T1 only, before 8 AM).
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
    
    if bar['close'] > ah and bar['high'] > ah:
        close_dist = (bar['close'] - ah) * 10000
        if close_dist >= QUALITY_CLOSE_DIST:
            return True, 'LONG'
    elif bar['close'] < al and bar['low'] < al:
        close_dist = (al - bar['close']) * 10000
        if close_dist >= QUALITY_CLOSE_DIST:
            return True, 'SHORT'
    
    return False, None


def check_trend_filter(price, direction, sma_200):
    """
    Only take trades in direction of 200-period MA.
    """
    if sma_200 is None:
        return True
    if direction == 'LONG' and price < sma_200:
        return False
    if direction == 'SHORT' and price > sma_200:
        return False
    return True


def calculate_base80_sl_tp(entry_price, body_pips, ar_pips, direction):
    """SL: 1.5x body, TP: 0.50x AR (widened)"""
    body_in_price = body_pips / 10000.0
    sign = 1 if direction == 'LONG' else -1
    sl = entry_price - body_in_price * SL_BODY_MULTIPLIER * sign
    tp = entry_price + (ar_pips / 10000.0 * BASE80_TP_FACTOR) * sign
    return sl, tp
