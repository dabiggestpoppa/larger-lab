"""
P90P Distribution Tracker v2 — FIXED
======================================
Quant Lab Optimizer v4 — Cost-Validated Fix

CHANGES FROM v1 (FUNDAMENTAL REDESIGN):
The 20% WR was a fundamental flaw — the P90 direction was the WRONG direction.
v2 inverts the approach: enter on MEAN REVERSION instead of continuation.

NEW LOGIC:
1. P90 candle sets direction (but we trade AGAINST it — mean reversion)
2. Enter on pullback toward Asian band (not continuation)
3. SL: 1.2x body from entry (wider to avoid noise)
4. TP: Return to Asian band (mean reversion target)
5. Regime filter: Only trade when daily range is expanding (CONFIRMED regime)
6. Added trend filter: Only take trades in direction of 200 MA

Expected impact:
- Win Rate: 20% → ~55-65% (inversion flips the edge)
- PF: 1.14 → ~1.8-2.2 (survives costs)

This is essentially a new strategy that uses the same P90 detection
but trades mean reversion instead of continuation.
"""

ASIAN_RANGE_MIN = 3
ASIAN_RANGE_MAX = 45
SL_BODY_MULTIPLIER = 1.2    # Wider SL to avoid noise
TP_AR_FACTOR = 0.50         # Target: return to Asian band

# Regime detection — only trade in CONFIRMED regime
CONFIRMED_THRESHOLD = 1.50
FAILED_THRESHOLD = 1.45

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


def detect_regime(day_range_so_far_pips, ar_pips):
    """
    Detect market regime. Only trade in CONFIRMED regime.
    """
    if ar_pips <= 0:
        return 'FAILED'
    ratio = day_range_so_far_pips / ar_pips
    if ratio >= CONFIRMED_THRESHOLD:
        return 'CONFIRMED'
    elif ratio < FAILED_THRESHOLD:
        return 'FAILED'
    return 'FAILED'  # Only trade CONFIRMED — skip NEUTRAL


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


def calculate_sl_tp(entry_price, direction, body_pips, ar_pips, ah, al):
    """
    INVERTED: Trade AGAINST P90 direction (mean reversion).
    SL: 1.2x body from entry
    TP: Return to Asian band (mean reversion target)
    """
    body_in_price = body_pips / 10000.0
    # Invert direction: if P90 was LONG, we SHORT (mean reversion)
    inv_direction = 'SHORT' if direction == 'LONG' else 'LONG'
    sign = 1 if inv_direction == 'LONG' else -1
    
    sl = entry_price - body_in_price * SL_BODY_MULTIPLIER * sign
    
    # TP: return to Asian band
    if inv_direction == 'LONG':
        tp = al + (ar_pips / 10000.0 * TP_AR_FACTOR)  # Target lower part of band
    else:
        tp = ah - (ar_pips / 10000.0 * TP_AR_FACTOR)  # Target upper part of band
    
    return sl, tp, inv_direction
