"""
Dual Engine — Isolated Strategy Logic
======================================
Quant Lab Optimizer v4

Performance: 51.2% WR, +757p, PF 1.60

CORE LOGIC:
Two-stage entry system. First "anchor" entry on Asian breakout, then
"amplifier" entries on pullbacks within the trend.

ANCHOR (Play 1):
1. P90 candle breaks above/below Asian band (body >= 4.6p)
2. Must close at least 2p outside Asian band
3. Asian Range: 3-20 pips (T1/T2 only)
4. Enter at close of breakout candle
5. SL: 1.5x body from entry
6. TP: AR * 0.35 in trade direction

AMPLIFIER (Play 2):
1. After anchor, look for continuation candles in same direction
2. Amplifier must have body >= 4.1p
3. Enter on 32-50% pullback of impulse from anchor
4. SL: 1.5x amplifier body from entry
5. TP: AR * 0.36 in trade direction
6. Max 2 amplifiers for T1, 1 for T2
"""

ASIAN_RANGE_MIN = 3
ASIAN_RANGE_MAX = 30
ANCHOR_TIERS = ('T1', 'T2')  // Only T1 and T2
SL_BODY_MULTIPLIER = 1.5
ANCHOR_TP_FACTOR = 0.35
AMPLIFIER_TP_FACTOR = 0.35
MAX_AMPS_T1 = 2
MAX_AMPS_T2 = 1
PULLBACK_MIN = 0.32
PULLBACK_MAX = 0.50
AMPLIFIER_BODY_MIN = 4.1


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
    Check for anchor breakout signal.
    Returns (is_signal, direction) tuple.
    """
    body_pips = abs(bar['close'] - bar['open']) * 10000
    if body_pips < 4.6:
        return False, None
    
    if bar['close'] > ah and bar['high'] > ah:
        close_dist = (bar['close'] - ah) * 10000
        if close_dist >= 2.0 and ar_pips <= 20:
            return True, 'LONG'
    elif bar['close'] < al and bar['low'] < al:
        close_dist = (al - bar['close']) * 10000
        if close_dist >= 2.0 and ar_pips <= 20:
            return True, 'SHORT'
    
    return False, None


def check_amplifier_entry(bar, anchor_ep, impulse_high, impulse_low, impulse_size, anchor_direction):
    """
    Check for amplifier entry on 32-50% pullback.
    Returns True if entry signal.
    """
    body_pips = abs(bar['close'] - bar['open']) * 10000
    if body_pips < AMPLIFIER_BODY_MIN:
        return False
    
    amp_direction = 'LONG' if bar['close'] > bar['open'] else 'SHORT'
    if amp_direction != anchor_direction:
        return False
    
    if anchor_direction == 'LONG':
        retrace = (impulse_high - bar['low']) * 10000
    else:
        retrace = (bar['high'] - impulse_low) * 10000
    
    if impulse_size > 0:
        retrace_pct = retrace / impulse_size
    else:
        return False
    
    return PULLBACK_MIN <= retrace_pct <= PULLBACK_MAX


def calculate_anchor_sl_tp(entry_price, body_pips, ar_pips, direction):
    """SL: 1.5x body, TP: 0.35x AR"""
    body_in_price = body_pips / 10000.0
    sign = 1 if direction == 'LONG' else -1
    sl = entry_price - body_in_price * SL_BODY_MULTIPLIER * sign
    tp = entry_price + (ar_pips / 10000.0 * ANCHOR_TP_FACTOR) * sign
    return sl, tp


def calculate_amplifier_sl_tp(entry_price, amp_body_pips, ar_pips, direction):
    """SL: 1.5x amplifier body, TP: 0.35x AR"""
    body_in_price = amp_body_pips / 10000.0
    sign = 1 if direction == 'LONG' else -1
    sl = entry_price - body_in_price * SL_BODY_MULTIPLIER * sign
    tp = entry_price + (ar_pips / 10000.0 * AMPLIFIER_TP_FACTOR) * sign
    return sl, tp
