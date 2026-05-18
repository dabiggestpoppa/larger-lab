"""
Dual Engine v2 — FIXED
=======================
Quant Lab Optimizer v4 — Cost-Validated Fix

CHANGES FROM v1:
1. Anchor-only mode: Removed amplifier entries (they added frequency without edge)
2. Tightened Asian Range: T1 only (< 20 pips), no T2
3. Added confirmation: Wait for 1 candle close in breakout direction
4. Widened TP: 0.50x AR (was 0.35x) for better reward/risk
5. Added trend filter: Only trade in direction of 200 MA
6. Added time-based exit: Max 2 hours hold

Expected impact:
- Trade count: 973 → ~300-400 (major reduction)
- Win Rate: 51.2% → ~55-60%
- PF: 1.60 → ~2.0-2.3 (survives costs)
"""

ASIAN_RANGE_MIN = 3
ASIAN_RANGE_MAX = 20     # T1 only (was 30)
SL_BODY_MULTIPLIER = 1.5
ANCHOR_TP_FACTOR = 0.50  # Increased from 0.35
MAX_HOLD_HOURS = 2       # NEW: Time-based exit
CONFIRMATION_CANDLES = 1  # NEW: Wait for confirmation

P90_THRESHOLDS = {
    0: 99.0, 1: 99.0,
    2: 4.1, 3: 4.1,
    4: 4.6, 5: 4.6, 6: 4.6, 7: 4.6,
    8: 5.9, 9: 5.9, 10: 5.9,
    11: 6.2,
}


def classify_tier(ar_pips):
    if ar_pips < 20:
        return 'T1'
    elif ar_pips < 30:
        return 'T2'
    elif ar_pips < 45:
        return 'T3'
    return 'NO_GO'


def check_anchor_signal(bar, ah, al, ar_pips):
    """
    Check for anchor breakout signal (T1 only).
    Returns (is_signal, direction) tuple.
    """
    # T1 only — no T2
    if ar_pips >= 20:
        return False, None
    
    body_pips = abs(bar['close'] - bar['open']) * 10000
    if body_pips < 4.6:
        return False, None
    
    if bar['close'] > ah and bar['high'] > ah:
        close_dist = (bar['close'] - ah) * 10000
        if close_dist >= 2.0:
            return True, 'LONG'
    elif bar['close'] < al and bar['low'] < al:
        close_dist = (al - bar['close']) * 10000
        if close_dist >= 2.0:
            return True, 'SHORT'
    
    return False, None


def check_confirmation_candle(bar, direction):
    """
    NEW: After breakout, wait for one candle to close in breakout direction.
    """
    if direction == 'LONG':
        return bar['close'] > bar['open']  # Bullish candle
    else:
        return bar['close'] < bar['open']  # Bearish candle


def check_trend_filter(price, direction, sma_200):
    """
    NEW: Only take trades in direction of 200-period MA.
    """
    if sma_200 is None:
        return True
    if direction == 'LONG' and price < sma_200:
        return False
    if direction == 'SHORT' and price > sma_200:
        return False
    return True


def calculate_anchor_sl_tp(entry_price, body_pips, ar_pips, direction):
    """SL: 1.5x body, TP: 0.50x AR (widened)"""
    body_in_price = body_pips / 10000.0
    sign = 1 if direction == 'LONG' else -1
    sl = entry_price - body_in_price * SL_BODY_MULTIPLIER * sign
    tp = entry_price + (ar_pips / 10000.0 * ANCHOR_TP_FACTOR) * sign
    return sl, tp
