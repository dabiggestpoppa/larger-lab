"""
Two Plays — Isolated Strategy Logic
====================================
Quant Lab Optimizer v4

Performance: 42.3% WR, +53p, PF 1.04

CORE LOGIC:
Two distinct trading plays based on Asian Range tier:

PLAY 1 — Base 80 (T1/T2 only):
1. P90 candle breaks above/below Asian band
2. Must close at least 2p outside Asian band
3. Asian Range must be T1 (< 20p) for best edge
4. Enter at close
5. SL: 1.5x body from entry
6. TP: AR * 0.35 in trade direction

PLAY 2 — T3 Model 2 (T3 only, AR 30-45p):
1. Initial breakout from Asian band (P90, body >= 4.6p)
2. Hold test: Price stays above/below opposite Asian band for 2 hours
3. Wait for 32-50% pullback of impulse leg
4. Enter at close of pullback candle
5. SL: 0.80x impulse from entry
6. TP: AR * 1.0 in trade direction
"""

ASIAN_RANGE_MIN = 3
ASIAN_RANGE_MAX = 45
SL_BODY_MULTIPLIER = 1.5
BASE80_TP_FACTOR = 0.35
T3_TP_FACTOR = 1.0
T3_SL_IMPULSE_FACTOR = 0.80
PULLBACK_MIN = 0.32
PULLBACK_MAX = 0.50
QUALITY_CLOSE_DIST = 2.0  # Minimum pips outside Asian band

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


# === PLAY 1: Base 80 ===

def check_base80_entry(bar, ah, al, ar_pips):
    """
    Check for Base 80 entry (T1/T2 only).
    Returns (is_entry, direction) tuple.
    """
    if ar_pips >= 20:  # Only T1
        return False, None
    
    body_pips = abs(bar['close'] - bar['open']) * 10000
    threshold = P90_THRESHOLDS.get(bar['est_hour'], 99.0)
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


def calculate_base80_sl_tp(entry_price, body_pips, ar_pips, direction):
    """SL: 1.5x body, TP: 0.35x AR"""
    body_in_price = body_pips / 10000.0
    sign = 1 if direction == 'LONG' else -1
    sl = entry_price - body_in_price * SL_BODY_MULTIPLIER * sign
    tp = entry_price + (ar_pips / 10000.0 * BASE80_TP_FACTOR) * sign
    return sl, tp


# === PLAY 2: T3 Model 2 ===

def check_initial_breakout(bar, ah, al):
    """Check for initial Asian band breakout."""
    body_pips = abs(bar['close'] - bar['open']) * 10000
    if body_pips < 4.6:
        return False, None
    
    if bar['close'] > ah and bar['high'] > ah:
        return True, 'LONG'
    elif bar['close'] < al and bar['low'] < al:
        return True, 'SHORT'
    return False, None


def check_hold_test(hold_bars, direction, ah, al):
    """Check if price holds for 2 hours after breakout."""
    for bar in hold_bars:
        if direction == 'LONG' and bar['close'] < al:
            return False
        elif direction == 'SHORT' and bar['close'] > ah:
            return False
    return True


def check_t3_pullback(row, break_price, ah, al, impulse_leg, break_direction):
    """
    Check for 32-50% pullback entry in T3 Model 2.
    """
    if break_direction == 'LONG':
        retrace = (break_price - row['low']) * 10000
    else:
        retrace = (row['high'] - break_price) * 10000
    
    if impulse_leg > 0:
        retrace_pct = retrace / impulse_leg
    else:
        return False
    
    return PULLBACK_MIN <= retrace_pct <= PULLBACK_MAX


def calculate_t3_sl_tp(entry_price, impulse_leg, ar_pips, direction):
    """SL: 0.80x impulse, TP: 1.0x AR"""
    impulse_in_price = impulse_leg / 10000.0
    sign = 1 if direction == 'LONG' else -1
    sl = entry_price - impulse_in_price * T3_SL_IMPULSE_FACTOR * sign
    tp = entry_price + (ar_pips / 10000.0 * T3_TP_FACTOR) * sign
    return sl, tp
