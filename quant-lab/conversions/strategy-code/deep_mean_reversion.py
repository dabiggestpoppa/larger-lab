"""
Deep Mean Reversion Strategy — Isolated Logic
==============================================
Source: optimizer_v4.py → run_deep_mean_reversion()
Win Rate: 91.8% | P&L: +8746p | PF: 112

CORE CONCEPT:
When price extends aggressively to the 200% Deep State level (measured from
P90 activation), enter mean reversion targeting return to activation level.

SETUP:
1. P90 candle sets direction and activation level (close price)
2. Deep State = activation + 200% of P90 body in P90 direction
3. Kill Switch = activation + 220% of P90 body in P90 direction
4. Wait for price to touch Deep State
5. Enter mean reversion (AGAINST P90 direction) at Deep State level
6. SL: Kill Switch level
7. TP: Return to activation level (0%)
8. Entry must occur before 12:00 PM EST

P90 THRESHOLDS (by EST hour):
- 2AM-4AM: 4.1 pips | 4AM-8AM: 4.6 pips | 8AM-10AM: 5.9 pips | 10AM-12PM: 6.2 pips
"""

DEEP_STATE_MULTIPLIER = 2.00  # 200% of P90 body
KILL_SWITCH_MULTIPLIER = 2.20  # 220% of P90 body
MAX_AR = 45  # pips
MIN_AR = 3   # pips
ENTRY_END_HOUR_EST = 12


def p90_threshold(est_hour):
    if est_hour < 2 or est_hour >= 11: return 99.0
    if est_hour < 4: return 4.1
    if est_hour < 6: return 4.6
    if est_hour < 8: return 4.6
    if est_hour < 10: return 5.9
    if est_hour < 11: return 6.2
    return 99.0


def should_entry(day_data, ah, al, ar, p90_row, p90_idx):
    """Determine if Deep Mean Reversion should enter."""
    if ar is None or ar > MAX_AR or ar < MIN_AR:
        return False, None

    body_pips = p90_row['body_pips']
    activation = p90_row['close']
    p90_direction = 'LONG' if p90_row['close'] > p90_row['open'] else 'SHORT'

    # Calculate Deep State and Kill Switch levels
    body_price = body_pips / 10000.0  # Convert pips to price for EUR/USD
    deep_state = activation + body_price * DEEP_STATE_MULTIPLIER * (1 if p90_direction == 'LONG' else -1)
    kill_switch = activation + body_price * KILL_SWITCH_MULTIPLIER * (1 if p90_direction == 'LONG' else -1)

    return True, {
        'direction': 'SHORT' if p90_direction == 'LONG' else 'LONG',  # Mean reversion
        'entry_price': deep_state,
        'sl_price': kill_switch,
        'tp_price': activation,
        'activation': activation,
        'deep_state': deep_state,
        'kill_switch': kill_switch,
    }
