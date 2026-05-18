"""
Blind Structural Chain — Isolated Strategy Logic
=================================================
Quant Lab Optimizer v4

Performance: 43.1% WR, +2248p, PF 1.14

CORE LOGIC:
Detects impulse moves from a baseline, then enters on 32-50% pullbacks
in the direction of the impulse. Supports up to 3 cycle repetitions.

SETUP:
1. Baseline: 3 AM EST price level
2. Impulse: Price moves >= threshold from baseline (12p T1, 16p T2, 20p T3)
3. Pullback: Price retraces 32-50% of impulse
4. Entry: At close of pullback candle
5. SL: Pullback extreme - 5 pip buffer
6. TP: Entry + 0.80 x impulse size in impulse direction
7. Max 3 cycles per day
8. Invalidation: If pullback exceeds 80% of impulse range
"""

ASIAN_RANGE_MIN = 3
ASIAN_RANGE_MAX = 45
PULLBACK_MIN = 0.32
PULLBACK_MAX = 0.50
INVALIDATION_THRESHOLD = 0.80
SL_BUFFER_PIPS = 5.0
TP_IMPULSE_FACTOR = 0.80
MAX_CYCLES = 3

IMPULSE_THRESHOLDS = {
    'T1': 12.0,
    'T2': 16.0,
    'T3': 20.0,
}


def classify_tier(ar_pips):
    if ar_pips < 20: return 'T1'
    elif ar_pips < 30: return 'T2'
    elif ar_pips < 45: return 'T3'
    return 'NO_GO'


def get_impulse_threshold(tier):
    return IMPULSE_THRESHOLDS.get(tier, 999.0)


def check_impulse(price, baseline, tier):
    threshold = get_impulse_threshold(tier)
    move_pips = (price - baseline) * 10000
    if abs(move_pips) >= threshold:
        direction = 'LONG' if move_pips > 0 else 'SHORT'
        return True, direction, abs(move_pips)
    return False, None, 0


def check_pullback_entry(current_price, impulse_high, impulse_low, impulse_size, impulse_direction):
    if impulse_direction == 'LONG':
        retrace = (impulse_high - current_price) * 10000
    else:
        retrace = (current_price - impulse_low) * 10000
    if impulse_size > 0:
        retrace_pct = retrace / impulse_size
    else:
        return False, 0
    return PULLBACK_MIN <= retrace_pct <= PULLBACK_MAX, retrace_pct


def check_invalidation(pullback_low, pullback_high, impulse_extreme, baseline, impulse_direction):
    if impulse_direction == 'LONG':
        impulse_range = (impulse_extreme - baseline) * 10000
        if impulse_range > 0:
            return (impulse_extreme - pullback_low) * 10000 / impulse_range > INVALIDATION_THRESHOLD
    else:
        impulse_range = (baseline - impulse_extreme) * 10000
        if impulse_range > 0:
            return (pullback_high - impulse_extreme) * 10000 / impulse_range > INVALIDATION_THRESHOLD
    return False


def calculate_sl_tp(entry_price, pullback_low, pullback_high, impulse_size, direction):
    buffer = 5.0 / 10000.0
    impulse_in_price = impulse_size / 10000.0
    if direction == 'LONG':
        sl = pullback_low - buffer
        tp = entry_price + impulse_in_price * TP_IMPULSE_FACTOR
    else:
        sl = pullback_high + buffer
        tp = entry_price - impulse_in_price * TP_IMPULSE_FACTOR
    return sl, tp
