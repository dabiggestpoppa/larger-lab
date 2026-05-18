"""
P90P Distribution Tracker — Isolated Strategy Logic
====================================================
Quant Lab Optimizer v4

Performance: 20.0% WR, +150p, PF 1.14

CORE LOGIC:
Tracks the distribution of P90 breakouts. Enters in the direction of
the P90 candle with targets based on Asian Range multiples. Uses regime
detection to filter out low-probability days.

SETUP:
1. P90 candle: First candle with body >= threshold during 2-11 AM EST
2. Must close outside Asian band
3. Regime detection at 9 AM EST:
   - CONFIRMED: Daily range so far >= 1.50x AR → use 70% of target
   - NEUTRAL: Otherwise → use 55% of target
   - FAILED: Daily range < 1.45x AR → SKIP the trade
4. Target factors by tier: T1=1.80x, T2=1.50x, T3=1.20x
5. SL: 0.80x body from entry
6. TP: AR * tier_factor * regime_fraction in P90 direction
"""

ASIAN_RANGE_MIN = 3
ASIAN_RANGE_MAX = 45
SL_BODY_MULTIPLIER = 0.80

# Target factors by tier
TIER_FACTORS = {'T1': 1.80, 'T2': 1.50, 'T3': 1.20}

# Regime detection
CONFIRMED_THRESHOLD = 1.50
FAILED_THRESHOLD = 1.45
CONFIRMED_FRACTION = 0.70
NEUTRAL_FRACTION = 0.55

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
    Detect market regime based on daily range vs Asian range.
    Returns: 'CONFIRMED', 'NEUTRAL', or 'FAILED'
    """
    if ar_pips <= 0:
        return 'NEUTRAL'
    ratio = day_range_so_far_pips / ar_pips
    if ratio >= CONFIRMED_THRESHOLD:
        return 'CONFIRMED'
    elif ratio < FAILED_THRESHOLD:
        return 'FAILED'
    return 'NEUTRAL'


def calculate_sl_tp(entry_price, direction, body_pips, ar_pips, tier, regime):
    """
    SL: 0.80x body from entry
    TP: AR * tier_factor * regime_fraction in direction
    """
    body_in_price = body_pips / 10000.0
    sign = 1 if direction == 'LONG' else -1
    
    sl = entry_price - body_in_price * SL_BODY_MULTIPLIER * sign
    
    base_factor = TIER_FACTORS.get(tier, 1.20)
    if regime == 'CONFIRMED':
        fraction = CONFIRMED_FRACTION
    else:
        fraction = NEUTRAL_FRACTION
    
    target_pips = ar_pips * base_factor * fraction
    tp = entry_price + (target_pips / 10000.0) * sign
    
    return sl, tp
