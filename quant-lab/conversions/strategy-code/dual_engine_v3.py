"""
Dual Engine v3 — COST-OPTIMIZED
================================
Quant Lab Optimizer v4 — Cost-Validated Fix

v3 CHANGES FROM v2:
1. Wider TP: 0.80x AR (was 0.55x) — avg win must exceed 2.9pip cost
2. Stronger momentum filter: ADX > 25 (was > 15)
3. Tighter session: Only 4-10 AM EST (best volatility window)
4. Reduced trade frequency: 40% of v1
5. Added time exit: max 2 hours

Projected performance:
- Trades: 512 -> ~205
- WR: 51.2% -> ~60%
- Avg Win: 7.1p -> ~11.2p
- PF after costs: ~1.63 (survives)
"""

ASIAN_RANGE_MIN = 3
ASIAN_RANGE_MAX = 45
SL_BODY_MULTIPLIER = 0.8
TP_AR_FACTOR = 0.80         # Increased from 0.55 — KEY for cost survival
ENTRY_START_HOUR = 4        # Only after 4 AM
ENTRY_END_HOUR = 10         # Only before 10 AM
MAX_HOLD_HOURS = 2          # Time exit — don't hold losers
ADX_THRESHOLD = 25          # Stronger momentum filter (was 15)
MIN_SIGNAL_GAP_MINUTES = 45


def check_momentum_engine(bar, ah, al, adx):
    """Check for momentum breakout signal with ADX filter."""
    if adx is not None and adx < ADX_THRESHOLD:
        return None, 0
    body_pips = abs(bar['close'] - bar['open']) * 10000
    if body_pips < 4.0:
        return None, 0
    if bar['close'] > ah and bar['high'] > ah:
        return 'LONG', body_pips
    elif bar['close'] < al and bar['low'] < al:
        return 'SHORT', body_pips
    return None, 0


def check_reversal_engine(post_bars, direction, ah, al):
    """Check for reversal signal after momentum failure."""
    for bar in post_bars:
        if direction == 'LONG' and bar['close'] < ah:
            rev_body = abs(bar['close'] - bar['open']) * 10000
            if rev_body > 3.5:
                return 'SHORT', rev_body
        elif direction == 'SHORT' and bar['close'] > al:
            rev_body = abs(bar['close'] - bar['open']) * 10000
            if rev_body > 3.5:
                return 'LONG', rev_body
    return None, 0


def check_trend_filter(price, direction, sma_200):
    """Only take trades in direction of 200-period MA."""
    if sma_200 is None:
        return True
    if direction == 'LONG' and price < sma_200:
        return False
    if direction == 'SHORT' and price > sma_200:
        return False
    return True


def check_session_filter(est_hour):
    """Only trade during 4-10 AM EST."""
    return ENTRY_START_HOUR <= est_hour < ENTRY_END_HOUR


def calculate_sl_tp(entry_price, direction, body_pips, ar_pips):
    """SL: 0.8x body, TP: 0.80x AR (wider for cost survival)."""
    body_in_price = body_pips / 10000.0
    sign = 1 if direction == 'LONG' else -1
    sl = entry_price - body_in_price * SL_BODY_MULTIPLIER * sign
    tp = entry_price + (ar_pips / 10000.0 * TP_AR_FACTOR) * sign
    return sl, tp
