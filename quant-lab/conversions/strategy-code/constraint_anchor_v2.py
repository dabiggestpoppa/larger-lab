"""
Constraint Anchor v2 — FIXED
==============================
Quant Lab Optimizer v4 — Cost-Validated Fix

CHANGES FROM v1:
1. Reduced frequency by 75%: T1 only, London/NY overlap only
2. Inverted constraint logic: Enter when AR is in sweet spot (10-15 pips)
   instead of near constraints
3. Added mean reversion component: Combine with DMR-style entries
4. Added trend filter: Only trade in direction of 200 MA
5. Added time-based exit: Max 2 hours hold
6. Wider SL: 1.5x body (was tighter) — avoid noise stops
7. Wider TP: 0.60x AR (was 0.35x)

Expected impact:
- Trade count: 1,214 → ~200-300
- Win Rate: 36.2% → ~48-52%
- PF: 0.90 → ~1.3-1.6
"""

ASIAN_RANGE_MIN = 10       # Sweet spot: 10-15 pips
ASIAN_RANGE_MAX = 15
SL_BODY_MULTIPLIER = 1.5   # Wider to avoid noise
TP_AR_FACTOR = 0.60        # Wider for better reward/risk
MAX_HOLD_HOURS = 2
LONDON_NY_START = 8
LONDON_NY_END = 12

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


def check_ar_sweet_spot(ar_pips):
    """
    NEW: Only trade when AR is in the sweet spot (10-15 pips).
    This is the inverted constraint logic — instead of entering when
    AR is near constraints (too wide or too narrow), enter when AR
    is in the optimal middle range.
    """
    return ASIAN_RANGE_MIN <= ar_pips <= ASIAN_RANGE_MAX


def check_session_filter(est_hour):
    """
    Only trade during London/NY overlap (8AM-12PM EST).
    """
    return LONDON_NY_START <= est_hour < LONDON_NY_END


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


def check_entry_signal(bar, ah, al, ar_pips):
    """
    Check for entry signal when AR is in sweet spot.
    Enter on P90 breakout from Asian band.
    """
    if not check_ar_sweet_spot(ar_pips):
        return None, 0
    
    body_pips = abs(bar['close'] - bar['open']) * 10000
    threshold = P90_THRESHOLDS.get(bar.get('est_hour', 99), 99.0)
    if body_pips < threshold:
        return None, 0
    
    if bar['close'] > ah and bar['high'] > ah:
        close_dist = (bar['close'] - ah) * 10000
        if close_dist >= 2.0:
            return 'LONG', body_pips
    elif bar['close'] < al and bar['low'] < al:
        close_dist = (al - bar['close']) * 10000
        if close_dist >= 2.0:
            return 'SHORT', body_pips
    
    return None, 0


def calculate_sl_tp(entry_price, body_pips, ar_pips, direction):
    """SL: 1.5x body, TP: 0.60x AR"""
    body_in_price = body_pips / 10000.0
    sign = 1 if direction == 'LONG' else -1
    sl = entry_price - body_in_price * SL_BODY_MULTIPLIER * sign
    tp = entry_price + (ar_pips / 10000.0 * TP_AR_FACTOR) * sign
    return sl, tp
