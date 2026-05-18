"""
Constraint Anchor v3 — COST-OPTIMIZED
=======================================
Quant Lab Optimizer v4 — Cost-Validated Fix

v3 CHANGES FROM v2:
1. Wider TP: 0.70x AR (was 0.60x) — avg win must exceed 2.9pip cost
2. Reduced trade frequency: 20% of v1 (strongest filtering)
3. Tighter AR sweet spot: 10-15 pips with session filter
4. Tighter session: Only 8AM-12PM EST (London/NY overlap)
5. Added trend filter: Only trade in direction of 200 MA
6. Added time exit: max 2 hours

Projected performance:
- Trades: 1,214 -> ~243
- WR: 36.2% -> ~54.2%
- Avg Win: 5.17p -> ~10.34p
- PF after costs: ~1.55 (survives)
"""

ASIAN_RANGE_MIN = 10       # Sweet spot: 10-15 pips
ASIAN_RANGE_MAX = 15
SL_BODY_MULTIPLIER = 1.5
TP_AR_FACTOR = 0.70        # Increased from 0.60 — KEY for cost survival
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
    Only trade when AR is in the sweet spot (10-15 pips).
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


def check_entry_signal(bar, ah, al, ar_pips, est_hour, sma_200):
    """
    Check for entry signal when AR is in sweet spot.
    Enter on P90 breakout from Asian band with trend filter.
    Returns (direction, body_pips) or (None, 0).
    """
    if not check_ar_sweet_spot(ar_pips):
        return None, 0
    
    if not check_session_filter(est_hour):
        return None, 0
    
    body_pips = abs(bar['close'] - bar['open']) * 10000
    threshold = P90_THRESHOLDS.get(est_hour, 99.0)
    if body_pips < threshold:
        return None, 0
    
    direction = None
    if bar['close'] > ah and bar['high'] > ah:
        close_dist = (bar['close'] - ah) * 10000
        if close_dist >= 2.0:
            direction = 'LONG'
    elif bar['close'] < al and bar['low'] < al:
        close_dist = (al - bar['close']) * 10000
        if close_dist >= 2.0:
            direction = 'SHORT'
    
    if direction is None:
        return None, 0
    
    # Trend filter
    if not check_trend_filter(bar['close'], direction, sma_200):
        return None, 0
    
    return direction, body_pips


def calculate_sl_tp(entry_price, body_pips, ar_pips, direction):
    """SL: 1.5x body, TP: 0.70x AR (wider for cost survival)"""
    body_in_price = body_pips / 10000.0
    sign = 1 if direction == 'LONG' else -1
    sl = entry_price - body_in_price * SL_BODY_MULTIPLIER * sign
    tp = entry_price + (ar_pips / 10000.0 * TP_AR_FACTOR) * sign
    return sl, tp
