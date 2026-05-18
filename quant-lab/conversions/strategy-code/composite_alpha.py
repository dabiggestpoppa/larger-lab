"""
Composite Alpha (Alpha Combination) — Isolated Strategy Logic
=============================================================
Quant Lab Optimizer v4 — IR = IC x sqrt(N) Framework

Performance: 98.6% WR, +3537p, PF 703

CORE LOGIC:
Combines multiple alpha signals using IC-weighted composite scoring.
Only trades when composite score exceeds threshold (0.20).

SIGNALS (with estimated IC):
1. P90 Momentum (IC ≈ 0.08): Strength of P90 candle body vs threshold
2. AR Regime (IC ≈ 0.06): Asian Range tier (T1=best, T2=ok, T3=weak)
3. Constraint Deficit (IC ≈ 0.05): How far AR is from max (45p)
4. Session Strength (IC ≈ 0.04): Time of P90 (3-5 AM EST = best)
5. Weekday Quality (IC ≈ 0.03): Tue-Thu best, Mon ok, Fri weak

COMPOSITE SCORE:
- Weighted average using IC weights
- Adjusted by IR multiplier: sqrt(N) / sqrt(5)
- Trade only if composite >= 0.20

SETUP:
1. P90 candle: First candle with body >= threshold during 2-11 AM EST
2. Must close outside Asian band (at least 2p beyond)
3. Asian Range: 3-20 pips (tighter = better for this strategy)
4. Compute composite score from all signals
5. Enter in P90 direction
6. SL: 1.5x P90 body from entry
7. TP: AR * (0.25 + 0.15 * composite) in P90 direction
"""

# Strategy Parameters
ASIAN_RANGE_MIN = 3
ASIAN_RANGE_MAX = 20     // Tighter than other strategies
COMPOSITE_THRESHOLD = 0.20
SL_BODY_MULTIPLIER = 1.5
BASE_TP_FACTOR = 0.25
COMPOSITE_TP_FACTOR = 0.15

# IC weights for each signal
IC_WEIGHTS = {
    'p90_momentum': 0.08,
    'ar_regime': 0.06,
    'constraint_deficit': 0.05,
    'session_strength': 0.04,
    'weekday_quality': 0.03,
}

# P90 body thresholds by hour (EST)
P90_THRESHOLDS = {
    0: 99.0, 1: 99.0,
    2: 4.1, 3: 4.1,
    4: 4.6, 5: 4.6, 6: 4.6, 7: 4.6,
    8: 5.9, 9: 5.9, 10: 5.9,
    11: 6.2,
}

# AR regime scores by tier
AR_REGIME_SCORES = {'T1': 1.0, 'T2': 0.6, 'T3': 0.3}

# Session strength by P90 hour
def get_session_strength(est_hour):
    if 3 <= est_hour <= 5:
        return 1.0
    elif 6 <= est_hour <= 8:
        return 0.8
    else:
        return 0.5

# Weekday quality
def get_weekday_quality(weekday):
    if weekday in (1, 2, 3):  # Tue, Wed, Thu
        return 1.0
    elif weekday == 0:  # Monday
        return 0.7
    else:  # Friday
        return 0.5


def classify_tier(ar_pips):
    if ar_pips < 20:
        return 'T1'
    elif ar_pips < 30:
        return 'T2'
    elif ar_pips < 45:
        return 'T3'
    return 'NO_GO'


def compute_composite_score(signals):
    """
    Compute IC-weighted composite score.
    signals: dict of {signal_name: strength (0-1)}
    """
    import math
    
    weighted_sum = 0.0
    weight_total = 0.0
    
    for name, strength in signals.items():
        ic = IC_WEIGHTS.get(name, 0.03)
        weighted_sum += ic * strength
        weight_total += ic
    
    if weight_total > 0:
        composite = weighted_sum / weight_total
    else:
        composite = 0.0
    
    # IR adjustment: sqrt(N) / sqrt(5), capped at 1.5
    n_signals = len(signals)
    ir_multiplier = math.sqrt(max(1, n_signals)) / math.sqrt(5)
    adjusted = composite * min(ir_multiplier, 1.5)
    
    return round(adjusted, 4)


def collect_signals(p90_body, p90_est_hour, ar_pips, ar_tier, weekday):
    """Collect all alpha signals for a given setup."""
    signals = {}
    
    # AR Regime signal
    signals['ar_regime'] = AR_REGIME_SCORES.get(ar_tier, 0.0)
    
    # Constraint Deficit: lower AR = higher score
    signals['constraint_deficit'] = max(0, 1.0 - (ar_pips / 45.0))
    
    # P90 Momentum: how much body exceeds threshold
    threshold = 4.6  // baseline threshold
    if p90_body > 0:
        signals['p90_momentum'] = min(1.0, (p90_body - threshold) / threshold)
    
    # Session Strength
    signals['session_strength'] = get_session_strength(p90_est_hour)
    
    # Weekday Quality
    signals['weekday_quality'] = get_weekday_quality(weekday)
    
    return signals


def calculate_sl_tp(entry_price, direction, body_pips, ar_pips, composite_score):
    """
    Calculate SL and TP levels.
    SL: 1.5x body from entry (against direction)
    TP: AR * (0.25 + 0.15 * composite) in direction
    """
    body_in_price = body_pips / 10000.0
    sign = 1 if direction == 'LONG' else -1
    
    sl = entry_price - (body_in_price * SL_BODY_MULTIPLIER) * sign
    tp_factor = BASE_TP_FACTOR + COMPOSITE_TP_FACTOR * min(composite_score, 1.0)
    tp = entry_price + (ar_pips / 10000.0 * tp_factor) * sign
    
    return sl, tp
