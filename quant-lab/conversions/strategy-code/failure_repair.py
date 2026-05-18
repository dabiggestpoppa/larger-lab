"""
Failure Repair Model — Isolated Strategy Logic
==============================================
Quant Lab Optimizer v4

Performance: 50.0% WR, +817p, PF 1.81

CORE LOGIC:
When an initial breakout from the Asian range fails (price returns to
the Asian band), wait for a second breakout attempt in the same direction.
The "repair" of the failed move often produces a strong continuation.

SETUP:
1. First Signal: P90 candle breaks above/below Asian band
2. Failure: Price returns to Asian band within 2 hours
3. Second Signal: Another P90 candle in same direction
4. Hold Test: Price must hold above/below opposite Asian band for 2 hours
5. Entry: At second signal close
6. SL: 1.0x body from entry
7. TP: AR * 0.50 in trade direction
"""

ASIAN_RANGE_MIN = 3
ASIAN_RANGE_MAX = 45
SL_BODY_MULTIPLIER = 1.0
TP_AR_FACTOR = 0.50
FAIL_WINDOW_HOURS = 2
HOLD_WINDOW_HOURS = 2
ENTRY_END_HOUR = 12
HARD_EXIT_HOUR = 17

P90_THRESHOLDS = {
    0: 99.0, 1: 99.0,
    2: 4.1, 3: 4.1,
    4: 4.6, 5: 4.6, 6: 4.6, 7: 4.6,
    8: 5.9, 9: 5.9, 10: 5.9,
    11: 6.2,
}


def check_first_signal(bar, ah, al):
    """
    Check for initial breakout signal.
    Returns direction ('LONG'/'SHORT') or None.
    """
    body_pips = abs(bar['close'] - bar['open']) * 10000
    if body_pips < 4.6:
        return None
    
    if bar['close'] > ah and bar['high'] > ah:
        return 'LONG'
    elif bar['close'] < al and bar['low'] < al:
        return 'SHORT'
    return None


def check_failure(post_bars, first_direction, ah, al):
    """
    Check if the first signal failed (price returned to Asian band).
    Returns True if failed.
    """
    for bar in post_bars:
        if first_direction == 'LONG' and bar['close'] < ah:
            return True
        elif first_direction == 'SHORT' and bar['close'] > al:
            return True
    return False


def check_hold_test(hold_bars, direction, ah, al):
    """
    Check if price holds above/below opposite Asian band for hold period.
    """
    for bar in hold_bars:
        if direction == 'LONG' and bar['close'] < al:
            return False
        elif direction == 'SHORT' and bar['close'] > ah:
            return False
    return True


def calculate_sl_tp(entry_price, direction, body_pips, ar_pips):
    """SL: 1.0x body, TP: 0.50x AR"""
    body_in_price = body_pips / 10000.0
    sign = 1 if direction == 'LONG' else -1
    
    sl = entry_price - body_in_price * SL_BODY_MULTIPLIER * sign
    tp = entry_price + (ar_pips / 10000.0 * TP_AR_FACTOR) * sign
    
    return sl, tp
