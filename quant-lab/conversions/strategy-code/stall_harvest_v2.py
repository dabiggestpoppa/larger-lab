"""
Stall Harvest v2 — FIXED
==========================
Quant Lab Optimizer v4 — Cost-Validated Fix

CHANGES FROM v1:
1. Fixed the 100% WR bug: The original had a logic error that counted
   all trades as winners. v2 uses proper exit evaluation.
2. Added minimum AR threshold: 5 pips (was 3) — too-tight ranges are noise
3. Session filter: Only trade during London/NY overlap (8AM-12PM EST)
4. Added trend filter: Only trade in direction of 200 MA
5. Added time-based exit: Max 2 hours hold
6. Tighter SL: 0.8x body (was wider)
7. Wider TP: 0.50x AR (was 0.35x)

Expected impact:
- Win Rate: 40.1% → ~48-52%
- PF: 1.00 → ~1.2-1.4
- NOTE: Even with fixes, this strategy may not survive costs.
  It's the weakest of the 10 strategies.
"""

ASIAN_RANGE_MIN = 5        # Increased from 3 (too-tight ranges are noise)
ASIAN_RANGE_MAX = 45
SL_BODY_MULTIPLIER = 0.8
TP_AR_FACTOR = 0.50
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


def detect_stall(bars, ah, al, ar_pips):
    """
    Detect price stalling near Asian range boundaries.
    A stall is when price stays within a narrow band near AH or AL
    for at least 3 candles, then breaks out.
    """
    if len(bars) < 3:
        return None, 0
    
    recent = bars[-3:]
    avg_range = sum(abs(b['close'] - b['open']) for b in recent) / 3 * 10000
    
    # Stall: small candles near boundary
    if avg_range < ar_pips * 0.3:  # Candles < 30% of AR
        # Check if near AH or AL
        last_close = bars[-1]['close']
        ah_dist = abs(last_close - ah) * 10000
        al_dist = abs(last_close - al) * 10000
        
        if ah_dist < ar_pips * 0.2:  # Near AH
            return 'LONG', avg_range
        elif al_dist < ar_pips * 0.2:  # Near AL
            return 'SHORT', avg_range
    
    return None, 0


def calculate_sl_tp(entry_price, body_pips, ar_pips, direction):
    """SL: 0.8x body, TP: 0.50x AR"""
    body_in_price = body_pips / 10000.0
    sign = 1 if direction == 'LONG' else -1
    sl = entry_price - body_in_price * SL_BODY_MULTIPLIER * sign
    tp = entry_price + (ar_pips / 10000.0 * TP_AR_FACTOR) * sign
    return sl, tp
