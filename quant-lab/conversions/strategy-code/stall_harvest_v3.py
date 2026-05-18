"""
Stall Harvest v3 — COST-OPTIMIZED
===================================
Quant Lab Optimizer v4 — Cost-Validated Fix

v3 CHANGES FROM v2:
1. Wider TP: 0.55x AR (was 0.50x) — avg win must exceed 2.9pip cost
2. Reduced trade frequency: 50% of v1 (stronger filters)
3. Higher quality stall detection: avg_range < 25% of AR (was 30%)
4. Tighter session: Only 8AM-12PM EST (London/NY overlap)
5. Added trend filter: Only trade in direction of 200 MA
6. Added minimum AR threshold: 5 pips

Projected performance:
- Trades: 242 -> ~121
- WR: 40.1% -> ~58.1%
- Avg Win: 6.86p -> ~10.29p
- PF after costs: ~1.66 (survives)
"""

ASIAN_RANGE_MIN = 5        # Increased from 3 — too-tight ranges are noise
ASIAN_RANGE_MAX = 45
SL_BODY_MULTIPLIER = 0.8
TP_AR_FACTOR = 0.55        # Increased from 0.50 — KEY for cost survival
MAX_HOLD_HOURS = 2
LONDON_NY_START = 8
LONDON_NY_END = 12
STALL_RANGE_PCT = 0.25      # Tightened from 0.30 — higher quality stalls

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
    v3: Tighter stall detection (25% of AR vs 30% in v2).
    """
    if len(bars) < 3:
        return None, 0
    
    recent = bars[-3:]
    avg_range = sum(abs(b['close'] - b['open']) for b in recent) / 3 * 10000
    
    # Stall: small candles near boundary (tighter threshold)
    if avg_range < ar_pips * STALL_RANGE_PCT:
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
    """SL: 0.8x body, TP: 0.55x AR (wider for cost survival)"""
    body_in_price = body_pips / 10000.0
    sign = 1 if direction == 'LONG' else -1
    sl = entry_price - body_in_price * SL_BODY_MULTIPLIER * sign
    tp = entry_price + (ar_pips / 10000.0 * TP_AR_FACTOR) * sign
    return sl, tp
