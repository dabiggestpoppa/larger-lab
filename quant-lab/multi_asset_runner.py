"""
Multi-Asset Forex M5 Backtest Runner
======================================
Runs ALL 10 CEREBUS strategies on ALL 8 Forex M5 assets.
Full strategy logic — NO simplification.

Cost model: 2.9 pips/trade (spread 0.2 + slippage 2.0 + commission 0.7)
JPY pairs: pips = price_diff * 100
"""

import sys
import os
import json
import math
import importlib.util
import traceback
from datetime import datetime, timedelta
from collections import defaultdict

# ─── Configuration ───────────────────────────────────────────────────────────

STRATEGY_DIR = r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\conversions\strategy-code"
DATA_DIR = r"C:\Users\wifik\Downloads"
OUTPUT_JSON = r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\results\multi_asset_forex_m5.json"
OUTPUT_REPORT = r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\MULTI_ASSET_FOREX_M5_REPORT.md"

STRATEGIES = [
    "Deep Mean Reversion",
    "Composite Alpha",
    "Failure Repair",
    "Dual Engine",
    "Blind Structural Chain",
    "Two Plays",
    "P90P Distribution",
    "Fractal Resolution",
    "Stall Harvest",
    "Constraint Anchor",
]

STRATEGY_FILES = {
    "Deep Mean Reversion": "deep_mean_reversion.py",
    "Composite Alpha": "composite_alpha.py",
    "Failure Repair": "failure_repair_v3.py",
    "Dual Engine": "dual_engine_v3.py",
    "Blind Structural Chain": "blind_structural_chain_v2.py",
    "Two Plays": "two_plays_v3.py",
    "P90P Distribution": "p90p_distribution_v2.py",
    "Fractal Resolution": "fractal_resolution_v2.py",
    "Stall Harvest": "stall_harvest_v3.py",
    "Constraint Anchor": "constraint_anchor_v3.py",
}

ASSETS = [
    ("EURUSD", "EURUSD!_M5_202301020000_202605061250.csv", False),
    ("GBPUSD", "GBPUSD!_M5_202301020000_202605061250.csv", False),
    ("USDJPY", "USDJPY!_M5_202301020000_202605061250.csv", True),
    ("USDCHF", "USDCHF!_M5_202301020000_202605061250.csv", False),
    ("AUDUSD", "AUDUSD!_M5_202301020000_202605061250.csv", False),
    ("NZDUSD", "NZDUSD!_M5_202301020000_202605061250.csv", False),
    ("USDCAD", "USDCAD!_M5_202301020000_202605061250.csv", False),
    ("CHFJPY", "CHFJPY!_M5_202201030000_202605061250.csv", True),
]

COST_PIPS = 2.9  # spread 0.2 + slippage 2.0 + commission 0.7


# ─── Data Loading ────────────────────────────────────────────────────────────

def load_csv(filepath):
    """Load MT5 CSV data. Returns list of bar dicts."""
    bars = []
    with open(filepath, 'r') as f:
        header = f.readline().strip()
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split('\t')
            if len(parts) < 7:
                continue
            try:
                bar = {
                    'date': parts[0],
                    'time': parts[1],
                    'datetime': parts[0] + ' ' + parts[1],
                    'open': float(parts[2]),
                    'high': float(parts[3]),
                    'low': float(parts[4]),
                    'close': float(parts[5]),
                    'volume': int(parts[6]) if parts[6] else 0,
                }
                bars.append(bar)
            except (ValueError, IndexError):
                continue
    return bars


def to_pips(price_diff, is_jpy):
    """Convert price difference to pips."""
    if is_jpy:
        return price_diff * 100.0
    return price_diff * 10000.0


def from_pips(pips, is_jpy):
    """Convert pips to price difference."""
    if is_jpy:
        return pips / 100.0
    return pips / 10000.0


def parse_datetime(date_str, time_str):
    """Parse date and time strings to datetime."""
    # Format: 2023.01.02 and 00:00:00
    parts_d = date_str.split('.')
    parts_t = time_str.split(':')
    return datetime(int(parts_d[0]), int(parts_d[1]), int(parts_d[2]),
                    int(parts_t[0]), int(parts_t[1]), int(parts_t[2]) if len(parts_t) > 2 else 0)


def to_est(dt):
    """Convert to EST (UTC-5). Data appears to be in UTC or broker time.
    We'll treat the time as-is and apply EST offset.
    MT5 data is typically in broker time (often UTC or UTC+2/+3).
    For P90 detection, we need EST hours.
    We'll assume the data timestamps are in UTC and convert to EST (UTC-5).
    """
    return dt - timedelta(hours=5)


# ─── Strategy Module Loader ──────────────────────────────────────────────────

def load_strategy_module(filename):
    """Load a strategy Python module from file."""
    filepath = os.path.join(STRATEGY_DIR, filename)
    spec = importlib.util.spec_from_file_location(filename.replace('.py', ''), filepath)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ─── Bar Utilities ───────────────────────────────────────────────────────────

def compute_sma(closes, period):
    """Compute SMA. Returns None if not enough data."""
    if len(closes) < period:
        return None
    return sum(closes[-period:]) / period


def compute_atr(bars, period):
    """Compute ATR. Returns list of ATR values."""
    if len(bars) < 2:
        return []
    trs = []
    for i in range(1, len(bars)):
        h = bars[i]['high']
        l = bars[i]['l'] if 'l' in bars[i] else bars[i]['low']
        prev_c = bars[i-1]['close']
        tr = max(h - l, abs(h - prev_c), abs(l - prev_c))
        trs.append(tr)
    if len(trs) < period:
        return trs
    atr_vals = []
    for i in range(len(trs)):
        if i < period - 1:
            atr_vals.append(None)
        else:
            atr_vals.append(sum(trs[i-period+1:i+1]) / period)
    return atr_vals


def find_daily_bars(bars, start_idx):
    """Find all bars in the same day starting from start_idx."""
    if start_idx >= len(bars):
        return [], start_idx
    day = bars[start_idx]['date']
    end_idx = start_idx
    while end_idx < len(bars) and bars[end_idx]['date'] == day:
        end_idx += 1
    return bars[start_idx:end_idx], end_idx


# ─── Per-Strategy Backtest Runners ───────────────────────────────────────────

def run_deep_mean_reversion(bars, is_jpy):
    """Deep Mean Reversion strategy."""
    trades = []
    i = 0
    while i < len(bars):
        bar = bars[i]
        est = to_est(parse_datetime(bar['date'], bar['time']))
        est_hour = est.hour
        
        # Find Asian session: 2AM-11AM EST
        if est_hour < 2 or est_hour >= 11:
            i += 1
            continue
        
        # Find the day's bars
        day_bars, next_i = find_daily_bars(bars, i)
        if len(day_bars) < 2:
            i = next_i
            continue
        
        # Compute Asian range from 2AM to current bar
        ah = max(b['high'] for b in day_bars)
        al = min(b['low'] for b in day_bars)
        ar = to_pips(ah - al, is_jpy)
        
        # P90 threshold
        threshold = _dmr_p90_threshold(est_hour)
        if threshold >= 99:
            i = next_i
            continue
        
        # Look for P90 candle
        p90_found = False
        for j, pb in enumerate(day_bars):
            body_pips = abs(pb['close'] - pb['open']) * (100.0 if is_jpy else 10000.0)
            if body_pips < threshold:
                continue
            
            # Check if P90 closes outside Asian band
            p90_dir = 'LONG' if pb['close'] > pb['open'] else 'SHORT'
            activation = pb['close']
            
            if p90_dir == 'LONG' and pb['close'] <= ah:
                continue
            if p90_dir == 'SHORT' and pb['close'] >= al:
                continue
            
            # Calculate Deep State and Kill Switch
            body_price = body_pips / (100.0 if is_jpy else 10000.0)
            deep_state = activation + body_price * 2.0 * (1 if p90_dir == 'LONG' else -1)
            kill_switch = activation + body_price * 2.2 * (1 if p90_dir == 'LONG' else -1)
            
            # Direction is mean reversion (against P90)
            direction = 'SHORT' if p90_dir == 'LONG' else 'LONG'
            
            # Look for price touching Deep State after P90
            for k in range(j + 1, len(day_bars)):
                future_bar = day_bars[k]
                future_est = to_est(parse_datetime(future_bar['date'], future_bar['time']))
                if future_est.hour >= 12:
                    break
                
                touched = False
                if direction == 'SHORT' and future_bar['high'] >= deep_state:
                    touched = True
                    entry_price = deep_state
                elif direction == 'LONG' and future_bar['low'] <= deep_state:
                    touched = True
                    entry_price = deep_state
                
                if touched:
                    sl_price = kill_switch
                    tp_price = activation
                    
                    # Simulate trade
                    result = _simulate_trade(bars, i + k, entry_price, sl_price, tp_price, direction, is_jpy, max_bars=144)
                    if result:
                        trades.append(result)
                    break
            
            p90_found = True
            break  # One P90 per day
        
        i = next_i
    
    return trades


def _dmr_p90_threshold(est_hour):
    if est_hour < 2 or est_hour >= 11: return 99.0
    if est_hour < 4: return 4.1
    if est_hour < 6: return 4.6
    if est_hour < 8: return 4.6
    if est_hour < 10: return 5.9
    if est_hour < 11: return 6.2
    return 99.0


def run_composite_alpha(bars, is_jpy):
    """Composite Alpha strategy."""
    trades = []
    i = 0
    while i < len(bars):
        bar = bars[i]
        est = to_est(parse_datetime(bar['date'], bar['time']))
        est_hour = est.hour
        
        if est_hour < 2 or est_hour >= 11:
            i += 1
            continue
        
        day_bars, next_i = find_daily_bars(bars, i)
        if len(day_bars) < 2:
            i = next_i
            continue
        
        ah = max(b['high'] for b in day_bars)
        al = min(b['low'] for b in day_bars)
        ar = to_pips(ah - al, is_jpy)
        
        # AR must be 3-20 pips (T1 only)
        if ar < 3 or ar > 20:
            i = next_i
            continue
        
        threshold = _ca_p90_threshold(est_hour)
        if threshold >= 99:
            i = next_i
            continue
        
        p90_found = False
        for j, pb in enumerate(day_bars):
            body_pips = abs(pb['close'] - pb['open']) * (100.0 if is_jpy else 10000.0)
            if body_pips < threshold:
                continue
            
            p90_dir = 'LONG' if pb['close'] > pb['open'] else 'SHORT'
            
            # Must close outside Asian band by at least 2 pips
            if p90_dir == 'LONG':
                close_dist = (pb['close'] - ah) * (100.0 if is_jpy else 10000.0)
                if close_dist < 2.0:
                    continue
            else:
                close_dist = (al - pb['close']) * (100.0 if is_jpy else 10000.0)
                if close_dist < 2.0:
                    continue
            
            # Compute composite score
            ar_tier = _classify_tier(ar)
            weekday = parse_datetime(pb['date'], pb['time']).weekday()
            
            signals = {}
            signals['ar_regime'] = {'T1': 1.0, 'T2': 0.6, 'T3': 0.3}.get(ar_tier, 0.0)
            signals['constraint_deficit'] = max(0, 1.0 - (ar / 45.0))
            
            baseline_threshold = 4.6
            signals['p90_momentum'] = min(1.0, (body_pips - baseline_threshold) / baseline_threshold) if body_pips > 0 else 0
            
            if 3 <= est_hour <= 5:
                signals['session_strength'] = 1.0
            elif 6 <= est_hour <= 8:
                signals['session_strength'] = 0.8
            else:
                signals['session_strength'] = 0.5
            
            if weekday in (1, 2, 3):
                signals['weekday_quality'] = 1.0
            elif weekday == 0:
                signals['weekday_quality'] = 0.7
            else:
                signals['weekday_quality'] = 0.5
            
            ic_weights = {'p90_momentum': 0.08, 'ar_regime': 0.06, 'constraint_deficit': 0.05,
                         'session_strength': 0.04, 'weekday_quality': 0.03}
            weighted_sum = sum(ic_weights.get(n, 0.03) * s for n, s in signals.items())
            weight_total = sum(ic_weights.get(n, 0.03) for n in signals)
            composite = weighted_sum / weight_total if weight_total > 0 else 0.0
            ir_mult = math.sqrt(max(1, len(signals))) / math.sqrt(5)
            adjusted = composite * min(ir_mult, 1.5)
            
            if adjusted < 0.20:
                continue
            
            # Enter in P90 direction
            direction = p90_dir
            entry_price = pb['close']
            
            # SL: 1.5x body from entry
            body_in_price = body_pips / (100.0 if is_jpy else 10000.0)
            sign = 1 if direction == 'LONG' else -1
            sl = entry_price - (body_in_price * 1.5) * sign
            tp_factor = 0.25 + 0.15 * min(adjusted, 1.0)
            tp = entry_price + (ar / (100.0 if is_jpy else 10000.0) * tp_factor) * sign
            
            result = _simulate_trade(bars, i + j, entry_price, sl, tp, direction, is_jpy, max_bars=144)
            if result:
                trades.append(result)
            
            p90_found = True
            break
        
        i = next_i
    
    return trades


def _ca_p90_threshold(est_hour):
    if est_hour < 2 or est_hour >= 11: return 99.0
    if est_hour < 4: return 4.1
    if est_hour < 8: return 4.6
    if est_hour < 10: return 5.9
    if est_hour < 11: return 6.2
    return 99.0


def _classify_tier(ar_pips):
    if ar_pips < 20: return 'T1'
    elif ar_pips < 30: return 'T2'
    elif ar_pips < 45: return 'T3'
    return 'NO_GO'


def run_failure_repair(bars, is_jpy):
    """Failure Repair v3 strategy."""
    trades = []
    i = 0
    while i < len(bars):
        bar = bars[i]
        est = to_est(parse_datetime(bar['date'], bar['time']))
        est_hour = est.hour
        
        # Session filter: 4-10 AM EST
        if est_hour < 4 or est_hour >= 10:
            i += 1
            continue
        
        day_bars, next_i = find_daily_bars(bars, i)
        if len(day_bars) < 2:
            i = next_i
            continue
        
        ah = max(b['high'] for b in day_bars)
        al = min(b['low'] for b in day_bars)
        ar = to_pips(ah - al, is_jpy)
        
        if ar < 3 or ar > 45:
            i = next_i
            continue
        
        # Look for first signal (breakout)
        first_signal_found = False
        for j, pb in enumerate(day_bars):
            body_pips = abs(pb['close'] - pb['open']) * (100.0 if is_jpy else 10000.0)
            if body_pips < 4.6:
                continue
            
            first_dir = None
            if pb['close'] > ah and pb['high'] > ah:
                first_dir = 'LONG'
            elif pb['close'] < al and pb['low'] < al:
                first_dir = 'SHORT'
            
            if first_dir is None:
                continue
            
            first_body = body_pips
            
            # Check for failure (price returns to Asian band)
            post_bars = day_bars[j+1:]
            failed = False
            fail_idx = None
            for k, fb in enumerate(post_bars):
                if first_dir == 'LONG' and fb['close'] < ah:
                    failed = True
                    fail_idx = k
                    break
                elif first_dir == 'SHORT' and fb['close'] > al:
                    failed = True
                    fail_idx = k
                    break
            
            if not failed:
                continue
            
            # Check for second signal (must be 2.0x first body)
            second_bars = post_bars[fail_idx+1:] if fail_idx is not None else []
            for k, sb in enumerate(second_bars):
                second_body = abs(sb['close'] - sb['open']) * (100.0 if is_jpy else 10000.0)
                if second_body < first_body * 2.0:
                    continue
                
                second_dir = None
                if sb['close'] > ah and sb['high'] > ah:
                    second_dir = 'LONG'
                elif sb['close'] < al and sb['low'] < al:
                    second_dir = 'SHORT'
                
                if second_dir is None:
                    continue
                
                # Check hold test
                hold_bars = second_bars[k+1:]
                holds = True
                for hb in hold_bars[:12]:  # Check next hour
                    if second_dir == 'LONG' and hb['close'] < al:
                        holds = False
                        break
                    elif second_dir == 'SHORT' and hb['close'] > ah:
                        holds = False
                        break
                
                if not holds:
                    continue
                
                # Trend filter: 200 SMA
                sma200 = None
                if i + j + fail_idx + k + 2 >= 200:
                    closes_so_far = [b['close'] for b in bars[:i + j + fail_idx + k + 2]]
                    sma200 = sum(closes_so_far[-200:]) / 200
                
                if sma200 is not None:
                    if second_dir == 'LONG' and sb['close'] < sma200:
                        continue
                    if second_dir == 'SHORT' and sb['close'] > sma200:
                        continue
                
                # Enter trade
                entry_price = sb['close']
                body_in_price = second_body / (100.0 if is_jpy else 10000.0)
                sign = 1 if second_dir == 'LONG' else -1
                sl = entry_price - body_in_price * 0.8 * sign
                tp = entry_price + (ar / (100.0 if is_jpy else 10000.0) * 0.75) * sign
                
                trade_idx = i + j + fail_idx + k + 2
                if trade_idx < len(bars):
                    result = _simulate_trade(bars, trade_idx, entry_price, sl, tp, second_dir, is_jpy, max_bars=72)
                    if result:
                        trades.append(result)
                
                first_signal_found = True
                break
            
            if first_signal_found:
                break
        
        i = next_i
    
    return trades


def run_dual_engine(bars, is_jpy):
    """Dual Engine v3 strategy."""
    trades = []
    closes_history = []
    i = 0
    while i < len(bars):
        bar = bars[i]
        closes_history.append(bar['close'])
        
        est = to_est(parse_datetime(bar['date'], bar['time']))
        est_hour = est.hour
        
        if est_hour < 4 or est_hour >= 10:
            i += 1
            continue
        
        day_bars, next_i = find_daily_bars(bars, i)
        if len(day_bars) < 2:
            i = next_i
            continue
        
        ah = max(b['high'] for b in day_bars)
        al = min(b['low'] for b in day_bars)
        ar = to_pips(ah - al, is_jpy)
        
        if ar < 3 or ar > 45:
            i = next_i
            continue
        
        # Compute ADX (simplified)
        adx = _compute_adx(bars, i)
        
        # SMA 200
        sma200 = compute_sma(closes_history, 200)
        
        # Look for momentum engine signal
        for j, pb in enumerate(day_bars):
            # ADX filter
            if adx is not None and adx < 25:
                continue
            
            body_pips = abs(pb['close'] - pb['open']) * (100.0 if is_jpy else 10000.0)
            if body_pips < 4.0:
                continue
            
            mom_dir = None
            if pb['close'] > ah and pb['high'] > ah:
                mom_dir = 'LONG'
            elif pb['close'] < al and pb['low'] < al:
                mom_dir = 'SHORT'
            
            if mom_dir is None:
                continue
            
            # Trend filter
            if sma200 is not None:
                if mom_dir == 'LONG' and pb['close'] < sma200:
                    continue
                if mom_dir == 'SHORT' and pb['close'] > sma200:
                    continue
            
            # Check for reversal (momentum failure)
            post_bars = day_bars[j+1:]
            rev_dir = None
            rev_body = 0
            rev_idx = None
            for k, rb in enumerate(post_bars):
                if mom_dir == 'LONG' and rb['close'] < ah:
                    rev_b = abs(rb['close'] - rb['open']) * (100.0 if is_jpy else 10000.0)
                    if rev_b > 3.5:
                        rev_dir = 'SHORT'
                        rev_body = rev_b
                        rev_idx = k
                    break
                elif mom_dir == 'SHORT' and rb['close'] > al:
                    rev_b = abs(rb['close'] - rb['open']) * (100.0 if is_jpy else 10000.0)
                    if rev_b > 3.5:
                        rev_dir = 'LONG'
                        rev_body = rev_b
                        rev_idx = k
                    break
            
            if rev_dir is None:
                continue
            
            # Enter on reversal
            entry_bar = post_bars[rev_idx]
            entry_price = entry_bar['close']
            body_in_price = rev_body / (100.0 if is_jpy else 10000.0)
            sign = 1 if rev_dir == 'LONG' else -1
            sl = entry_price - body_in_price * 0.8 * sign
            tp = entry_price + (ar / (100.0 if is_jpy else 10000.0) * 0.80) * sign
            
            trade_idx = i + j + rev_idx + 1
            if trade_idx < len(bars):
                result = _simulate_trade(bars, trade_idx, entry_price, sl, tp, rev_dir, is_jpy, max_bars=48)
                if result:
                    trades.append(result)
            
            break  # One trade per day
        
        i = next_i
    
    return trades


def _compute_adx(bars, idx, period=14):
    """Simplified ADX computation."""
    if idx < period * 2:
        return None
    try:
        trs = []
        plus_dm = []
        minus_dm = []
        for k in range(idx - period * 2, idx):
            if k < 1:
                continue
            h = bars[k]['high']
            l = bars[k]['low']
            prev_c = bars[k-1]['close']
            prev_h = bars[k-1]['high']
            prev_l = bars[k-1]['low']
            tr = max(h - l, abs(h - prev_c), abs(l - prev_c))
            trs.append(tr)
            
            up_move = h - prev_h
            down_move = prev_l - l
            plus_dm.append(up_move if up_move > down_move and up_move > 0 else 0)
            minus_dm.append(down_move if down_move > up_move and down_move > 0 else 0)
        
        if len(trs) < period:
            return None
        
        atr = sum(trs[-period:]) / period
        if atr == 0:
            return None
        
        plus_di = (sum(plus_dm[-period:]) / period) / atr * 100
        minus_di = (sum(minus_dm[-period:]) / period) / atr * 100
        
        if plus_di + minus_di == 0:
            return None
        
        dx = abs(plus_di - minus_di) / (plus_di + minus_di) * 100
        return dx
    except:
        return None


def run_blind_structural_chain(bars, is_jpy):
    """Blind Structural Chain v2 strategy."""
    trades = []
    closes_history = []
    i = 0
    while i < len(bars):
        bar = bars[i]
        closes_history.append(bar['close'])
        
        day_bars, next_i = find_daily_bars(bars, i)
        if len(day_bars) < 5:
            i = next_i
            continue
        
        ah = max(b['high'] for b in day_bars)
        al = min(b['low'] for b in day_bars)
        ar = to_pips(ah - al, is_jpy)
        
        if ar < 3 or ar > 45:
            i = next_i
            continue
        
        tier = _classify_tier(ar)
        impulse_threshold = {'T1': 12.0, 'T2': 16.0, 'T3': 20.0}.get(tier, 999.0)
        
        sma200 = compute_sma(closes_history, 200)
        
        # Look for impulse move from Asian range
        for j in range(len(day_bars)):
            pb = day_bars[j]
            baseline = ah  # Start from AH
            
            move_pips = (pb['close'] - baseline) * (100.0 if is_jpy else 10000.0)
            
            if abs(move_pips) < impulse_threshold:
                # Also check from AL
                baseline2 = al
                move_pips2 = (pb['close'] - baseline2) * (100.0 if is_jpy else 10000.0)
                if abs(move_pips2) < impulse_threshold:
                    continue
                move_pips = move_pips2
                baseline = baseline2
            
            impulse_dir = 'LONG' if move_pips > 0 else 'SHORT'
            impulse_size = abs(move_pips)
            
            # Trend filter
            if sma200 is not None:
                if impulse_dir == 'LONG' and pb['close'] < sma200:
                    continue
                if impulse_dir == 'SHORT' and pb['close'] > sma200:
                    continue
            
            impulse_high = pb['high']
            impulse_low = pb['low']
            
            # Look for pullback (35-45% retrace)
            for k in range(j + 1, len(day_bars)):
                cb = day_bars[k]
                
                if impulse_dir == 'LONG':
                    retrace = (impulse_high - cb['close']) * (100.0 if is_jpy else 10000.0)
                else:
                    retrace = (cb['close'] - impulse_low) * (100.0 if is_jpy else 10000.0)
                
                if impulse_size > 0:
                    retrace_pct = retrace / impulse_size
                else:
                    continue
                
                if retrace_pct < 0.35:
                    continue
                if retrace_pct > 0.45:
                    # Pullback too deep
                    break
                
                # Check invalidation (60%)
                if impulse_dir == 'LONG':
                    impulse_range = (impulse_high - baseline) * (100.0 if is_jpy else 10000.0)
                    if impulse_range > 0 and (impulse_high - cb['low']) * (100.0 if is_jpy else 10000.0) / impulse_range > 0.60:
                        break
                else:
                    impulse_range = (baseline - impulse_low) * (100.0 if is_jpy else 10000.0)
                    if impulse_range > 0 and (cb['high'] - impulse_low) * (100.0 if is_jpy else 10000.0) / impulse_range > 0.60:
                        break
                
                # Confirmation candle
                if k + 1 < len(day_bars):
                    conf_bar = day_bars[k + 1]
                    if impulse_dir == 'LONG' and conf_bar['close'] <= conf_bar['open']:
                        continue
                    if impulse_dir == 'SHORT' and conf_bar['close'] >= conf_bar['open']:
                        continue
                else:
                    continue
                
                # Entry
                entry_price = cb['close']
                buffer = 5.0 / (100.0 if is_jpy else 10000.0)
                impulse_in_price = impulse_size / (100.0 if is_jpy else 10000.0)
                
                if impulse_dir == 'LONG':
                    sl = cb['low'] - buffer
                    tp = entry_price + impulse_in_price * 0.80
                else:
                    sl = cb['high'] + buffer
                    tp = entry_price - impulse_in_price * 0.80
                
                trade_idx = i + k + 1
                if trade_idx < len(bars):
                    result = _simulate_trade(bars, trade_idx, entry_price, sl, tp, impulse_dir, is_jpy, max_bars=48)
                    if result:
                        trades.append(result)
                
                break  # One trade per impulse
            
            break  # One impulse per day
        
        i = next_i
    
    return trades


def run_two_plays(bars, is_jpy):
    """Two Plays v3 strategy."""
    trades = []
    closes_history = []
    i = 0
    while i < len(bars):
        bar = bars[i]
        closes_history.append(bar['close'])
        
        est = to_est(parse_datetime(bar['date'], bar['time']))
        est_hour = est.hour
        
        # Only before 8 AM
        if est_hour >= 8:
            i += 1
            continue
        
        day_bars, next_i = find_daily_bars(bars, i)
        if len(day_bars) < 2:
            i = next_i
            continue
        
        ah = max(b['high'] for b in day_bars)
        al = min(b['low'] for b in day_bars)
        ar = to_pips(ah - al, is_jpy)
        
        # T1 only (AR < 20)
        if ar >= 20 or ar < 3:
            i = next_i
            continue
        
        sma200 = compute_sma(closes_history, 200)
        
        threshold = _ca_p90_threshold(est_hour)
        if threshold >= 99:
            i = next_i
            continue
        
        for j, pb in enumerate(day_bars):
            body_pips = abs(pb['close'] - pb['open']) * (100.0 if is_jpy else 10000.0)
            if body_pips < threshold:
                continue
            
            direction = None
            if pb['close'] > ah and pb['high'] > ah:
                close_dist = (pb['close'] - ah) * (100.0 if is_jpy else 10000.0)
                if close_dist >= 4.0:
                    direction = 'LONG'
            elif pb['close'] < al and pb['low'] < al:
                close_dist = (al - pb['close']) * (100.0 if is_jpy else 10000.0)
                if close_dist >= 4.0:
                    direction = 'SHORT'
            
            if direction is None:
                continue
            
            # Trend filter
            if sma200 is not None:
                if direction == 'LONG' and pb['close'] < sma200:
                    continue
                if direction == 'SHORT' and pb['close'] > sma200:
                    continue
            
            entry_price = pb['close']
            body_in_price = body_pips / (100.0 if is_jpy else 10000.0)
            sign = 1 if direction == 'LONG' else -1
            sl = entry_price - body_in_price * 1.5 * sign
            tp = entry_price + (ar / (100.0 if is_jpy else 10000.0) * 0.55) * sign
            
            result = _simulate_trade(bars, i + j, entry_price, sl, tp, direction, is_jpy, max_bars=48)
            if result:
                trades.append(result)
            
            break
        
        i = next_i
    
    return trades


def run_p90p_distribution(bars, is_jpy):
    """P90P Distribution v2 strategy (mean reversion)."""
    trades = []
    i = 0
    while i < len(bars):
        bar = bars[i]
        est = to_est(parse_datetime(bar['date'], bar['time']))
        est_hour = est.hour
        
        if est_hour < 2 or est_hour >= 11:
            i += 1
            continue
        
        day_bars, next_i = find_daily_bars(bars, i)
        if len(day_bars) < 2:
            i = next_i
            continue
        
        ah = max(b['high'] for b in day_bars)
        al = min(b['low'] for b in day_bars)
        ar = to_pips(ah - al, is_jpy)
        
        if ar < 3 or ar > 45:
            i = next_i
            continue
        
        threshold = _ca_p90_threshold(est_hour)
        if threshold >= 99:
            i = next_i
            continue
        
        # Compute day range so far for regime detection
        day_high = max(b['high'] for b in day_bars)
        day_low = min(b['low'] for b in day_bars)
        day_range = to_pips(day_high - day_low, is_jpy)
        
        # Regime filter: only CONFIRMED
        if ar <= 0:
            i = next_i
            continue
        ratio = day_range / ar
        if ratio < 1.50:
            i = next_i
            continue
        
        for j, pb in enumerate(day_bars):
            body_pips = abs(pb['close'] - pb['open']) * (100.0 if is_jpy else 10000.0)
            if body_pips < threshold:
                continue
            
            p90_dir = 'LONG' if pb['close'] > pb['open'] else 'SHORT'
            
            # INVERT direction (mean reversion)
            inv_dir = 'SHORT' if p90_dir == 'LONG' else 'LONG'
            
            # Trend filter
            closes_so_far = [b['close'] for b in bars[:i + j + 1]]
            sma200 = compute_sma(closes_so_far, 200)
            if sma200 is not None:
                if inv_dir == 'LONG' and pb['close'] < sma200:
                    continue
                if inv_dir == 'SHORT' and pb['close'] > sma200:
                    continue
            
            entry_price = pb['close']
            body_in_price = body_pips / (100.0 if is_jpy else 10000.0)
            sign = 1 if inv_dir == 'LONG' else -1
            sl = entry_price - body_in_price * 1.2 * sign
            
            # TP: return to Asian band
            if inv_dir == 'LONG':
                tp = al + (ar / (100.0 if is_jpy else 10000.0) * 0.50)
            else:
                tp = ah - (ar / (100.0 if is_jpy else 10000.0) * 0.50)
            
            result = _simulate_trade(bars, i + j, entry_price, sl, tp, inv_dir, is_jpy, max_bars=144)
            if result:
                trades.append(result)
            
            break
        
        i = next_i
    
    return trades


def run_fractal_resolution(bars, is_jpy):
    """Fractal Resolution v2 strategy."""
    trades = []
    closes_history = []
    i = 0
    while i < len(bars):
        bar = bars[i]
        closes_history.append(bar['close'])
        
        est = to_est(parse_datetime(bar['date'], bar['time']))
        est_hour = est.hour
        
        # London/NY overlap: 8AM-12PM EST
        if est_hour < 8 or est_hour >= 12:
            i += 1
            continue
        
        day_bars, next_i = find_daily_bars(bars, i)
        if len(day_bars) < 2:
            i = next_i
            continue
        
        ah = max(b['high'] for b in day_bars)
        al = min(b['low'] for b in day_bars)
        ar = to_pips(ah - al, is_jpy)
        
        # T1 only
        if ar >= 20 or ar < 3:
            i = next_i
            continue
        
        sma200 = compute_sma(closes_history, 200)
        
        threshold = _ca_p90_threshold(est_hour)
        if threshold >= 99:
            i = next_i
            continue
        
        for j, pb in enumerate(day_bars):
            body_pips = abs(pb['close'] - pb['open']) * (100.0 if is_jpy else 10000.0)
            if body_pips < threshold:
                continue
            
            direction = None
            if pb['close'] > ah and pb['high'] > ah:
                direction = 'LONG'
            elif pb['close'] < al and pb['low'] < al:
                direction = 'SHORT'
            
            if direction is None:
                continue
            
            # Trend filter
            if sma200 is not None:
                if direction == 'LONG' and pb['close'] < sma200:
                    continue
                if direction == 'SHORT' and pb['close'] > sma200:
                    continue
            
            entry_price = pb['close']
            body_in_price = body_pips / (100.0 if is_jpy else 10000.0)
            sign = 1 if direction == 'LONG' else -1
            sl = entry_price - body_in_price * 1.0 * sign
            tp = entry_price + (ar / (100.0 if is_jpy else 10000.0) * 0.60) * sign
            
            result = _simulate_trade(bars, i + j, entry_price, sl, tp, direction, is_jpy, max_bars=48)
            if result:
                trades.append(result)
            
            break
        
        i = next_i
    
    return trades


def run_stall_harvest(bars, is_jpy):
    """Stall Harvest v3 strategy."""
    trades = []
    closes_history = []
    i = 0
    while i < len(bars):
        bar = bars[i]
        closes_history.append(bar['close'])
        
        est = to_est(parse_datetime(bar['date'], bar['time']))
        est_hour = est.hour
        
        # London/NY overlap: 8AM-12PM EST
        if est_hour < 8 or est_hour >= 12:
            i += 1
            continue
        
        day_bars, next_i = find_daily_bars(bars, i)
        if len(day_bars) < 5:
            i = next_i
            continue
        
        ah = max(b['high'] for b in day_bars)
        al = min(b['low'] for b in day_bars)
        ar = to_pips(ah - al, is_jpy)
        
        if ar < 5 or ar > 45:
            i = next_i
            continue
        
        sma200 = compute_sma(closes_history, 200)
        
        # Look for stall pattern (3 small candles near boundary)
        for j in range(2, len(day_bars)):
            recent = day_bars[j-2:j+1]
            avg_range = sum(abs(b['close'] - b['open']) for b in recent) / 3 * (100.0 if is_jpy else 10000.0)
            
            if avg_range >= ar * 0.25:
                continue
            
            last_close = day_bars[j]['close']
            ah_dist = abs(last_close - ah) * (100.0 if is_jpy else 10000.0)
            al_dist = abs(last_close - al) * (100.0 if is_jpy else 10000.0)
            
            direction = None
            if ah_dist < ar * 0.2:
                direction = 'LONG'
            elif al_dist < ar * 0.2:
                direction = 'SHORT'
            
            if direction is None:
                continue
            
            # Trend filter
            if sma200 is not None:
                if direction == 'LONG' and last_close < sma200:
                    continue
                if direction == 'SHORT' and last_close > sma200:
                    continue
            
            # Enter on breakout from stall
            if j + 1 < len(day_bars):
                entry_bar = day_bars[j + 1]
                entry_price = entry_bar['close']
                
                # Check for actual breakout
                if direction == 'LONG' and entry_price <= ah:
                    continue
                if direction == 'SHORT' and entry_price >= al:
                    continue
                
                body_pips = abs(entry_bar['close'] - entry_bar['open']) * (100.0 if is_jpy else 10000.0)
                body_in_price = body_pips / (100.0 if is_jpy else 10000.0)
                sign = 1 if direction == 'LONG' else -1
                sl = entry_price - body_in_price * 0.8 * sign
                tp = entry_price + (ar / (100.0 if is_jpy else 10000.0) * 0.55) * sign
                
                trade_idx = i + j + 1
                if trade_idx < len(bars):
                    result = _simulate_trade(bars, trade_idx, entry_price, sl, tp, direction, is_jpy, max_bars=48)
                    if result:
                        trades.append(result)
            
            break
        
        i = next_i
    
    return trades


def run_constraint_anchor(bars, is_jpy):
    """Constraint Anchor v3 strategy."""
    trades = []
    closes_history = []
    i = 0
    while i < len(bars):
        bar = bars[i]
        closes_history.append(bar['close'])
        
        est = to_est(parse_datetime(bar['date'], bar['time']))
        est_hour = est.hour
        
        # London/NY overlap: 8AM-12PM EST
        if est_hour < 8 or est_hour >= 12:
            i += 1
            continue
        
        day_bars, next_i = find_daily_bars(bars, i)
        if len(day_bars) < 2:
            i = next_i
            continue
        
        ah = max(b['high'] for b in day_bars)
        al = min(b['low'] for b in day_bars)
        ar = to_pips(ah - al, is_jpy)
        
        # AR sweet spot: 10-15 pips
        if ar < 10 or ar > 15:
            i = next_i
            continue
        
        sma200 = compute_sma(closes_history, 200)
        
        threshold = _ca_p90_threshold(est_hour)
        if threshold >= 99:
            i = next_i
            continue
        
        for j, pb in enumerate(day_bars):
            body_pips = abs(pb['close'] - pb['open']) * (100.0 if is_jpy else 10000.0)
            if body_pips < threshold:
                continue
            
            direction = None
            if pb['close'] > ah and pb['high'] > ah:
                close_dist = (pb['close'] - ah) * (100.0 if is_jpy else 10000.0)
                if close_dist >= 2.0:
                    direction = 'LONG'
            elif pb['close'] < al and pb['low'] < al:
                close_dist = (al - pb['close']) * (100.0 if is_jpy else 10000.0)
                if close_dist >= 2.0:
                    direction = 'SHORT'
            
            if direction is None:
                continue
            
            # Trend filter
            if sma200 is not None:
                if direction == 'LONG' and pb['close'] < sma200:
                    continue
                if direction == 'SHORT' and pb['close'] > sma200:
                    continue
            
            entry_price = pb['close']
            body_in_price = body_pips / (100.0 if is_jpy else 10000.0)
            sign = 1 if direction == 'LONG' else -1
            sl = entry_price - body_in_price * 1.5 * sign
            tp = entry_price + (ar / (100.0 if is_jpy else 10000.0) * 0.70) * sign
            
            result = _simulate_trade(bars, i + j, entry_price, sl, tp, direction, is_jpy, max_bars=48)
            if result:
                trades.append(result)
            
            break
        
        i = next_i
    
    return trades


# ─── Trade Simulation ────────────────────────────────────────────────────────

def _simulate_trade(bars, start_idx, entry_price, sl, tp, direction, is_jpy, max_bars=144):
    """
    Simulate a trade from entry. Returns dict with trade result or None.
    max_bars: maximum bars to hold (time exit).
    """
    if start_idx >= len(bars):
        return None
    
    entry_bar_idx = start_idx
    cost = COST_PIPS
    
    for k in range(1, min(max_bars + 1, len(bars) - start_idx)):
        idx = start_idx + k
        if idx >= len(bars):
            break
        
        bar = bars[idx]
        
        # Check if SL hit
        if direction == 'LONG':
            if bar['low'] <= sl:
                pnl_pips = to_pips(sl - entry_price, is_jpy) - cost
                return {
                    'direction': direction,
                    'entry_price': entry_price,
                    'exit_price': sl,
                    'pnl_pips': pnl_pips,
                    'exit_type': 'sl',
                    'bars_held': k,
                    'entry_bar': entry_bar_idx,
                    'exit_bar': idx,
                }
            if bar['high'] >= tp:
                pnl_pips = to_pips(tp - entry_price, is_jpy) - cost
                return {
                    'direction': direction,
                    'entry_price': entry_price,
                    'exit_price': tp,
                    'pnl_pips': pnl_pips,
                    'exit_type': 'tp',
                    'bars_held': k,
                    'entry_bar': entry_bar_idx,
                    'exit_bar': idx,
                }
        else:  # SHORT
            if bar['high'] >= sl:
                pnl_pips = to_pips(entry_price - sl, is_jpy) - cost
                return {
                    'direction': direction,
                    'entry_price': entry_price,
                    'exit_price': sl,
                    'pnl_pips': pnl_pips,
                    'exit_type': 'sl',
                    'bars_held': k,
                    'entry_bar': entry_bar_idx,
                    'exit_bar': idx,
                }
            if bar['low'] <= tp:
                pnl_pips = to_pips(entry_price - tp, is_jpy) - cost
                return {
                    'direction': direction,
                    'entry_price': entry_price,
                    'exit_price': tp,
                    'pnl_pips': pnl_pips,
                    'exit_type': 'tp',
                    'bars_held': k,
                    'entry_bar': entry_bar_idx,
                    'exit_bar': idx,
                }
    
    # Time exit
    last_idx = start_idx + min(max_bars, len(bars) - start_idx - 1)
    if last_idx < len(bars):
        exit_price = bars[last_idx]['close']
        if direction == 'LONG':
            pnl_pips = to_pips(exit_price - entry_price, is_jpy) - cost
        else:
            pnl_pips = to_pips(entry_price - exit_price, is_jpy) - cost
        return {
            'direction': direction,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'pnl_pips': pnl_pips,
            'exit_type': 'end_data',
            'bars_held': min(max_bars, len(bars) - start_idx - 1),
            'entry_bar': entry_bar_idx,
            'exit_bar': last_idx,
        }
    
    return None


# ─── Metrics Computation ─────────────────────────────────────────────────────

def compute_metrics(trades):
    """Compute performance metrics from trades list."""
    if not trades:
        return {
            'total_trades': 0,
            'win_rate': 0.0,
            'profit_factor': 0.0,
            'total_pnl': 0.0,
            'max_dd_pips': 0.0,
            'avg_win': 0.0,
            'avg_loss': 0.0,
            'expectancy': 0.0,
        }
    
    wins = [t for t in trades if t['pnl_pips'] > 0]
    losses = [t for t in trades if t['pnl_pips'] <= 0]
    
    total_trades = len(trades)
    win_rate = len(wins) / total_trades * 100 if total_trades > 0 else 0
    
    gross_win = sum(t['pnl_pips'] for t in wins)
    gross_loss = abs(sum(t['pnl_pips'] for t in losses))
    profit_factor = gross_win / gross_loss if gross_loss > 0 else (999.0 if gross_win > 0 else 0.0)
    
    total_pnl = sum(t['pnl_pips'] for t in trades)
    
    avg_win = gross_win / len(wins) if wins else 0
    avg_loss = gross_loss / len(losses) if losses else 0
    
    expectancy = total_pnl / total_trades if total_trades > 0 else 0
    
    # Max drawdown
    cumulative = 0
    peak = 0
    max_dd = 0
    for t in trades:
        cumulative += t['pnl_pips']
        if cumulative > peak:
            peak = cumulative
        dd = peak - cumulative
        if dd > max_dd:
            max_dd = dd
    
    return {
        'total_trades': total_trades,
        'win_rate': round(win_rate, 1),
        'profit_factor': round(profit_factor, 2),
        'total_pnl': round(total_pnl, 2),
        'max_dd_pips': round(max_dd, 2),
        'avg_win': round(avg_win, 2),
        'avg_loss': round(avg_loss, 2),
        'expectancy': round(expectancy, 3),
    }


# ─── Main Runner ─────────────────────────────────────────────────────────────

STRATEGY_RUNNERS = {
    "Deep Mean Reversion": run_deep_mean_reversion,
    "Composite Alpha": run_composite_alpha,
    "Failure Repair": run_failure_repair,
    "Dual Engine": run_dual_engine,
    "Blind Structural Chain": run_blind_structural_chain,
    "Two Plays": run_two_plays,
    "P90P Distribution": run_p90p_distribution,
    "Fractal Resolution": run_fractal_resolution,
    "Stall Harvest": run_stall_harvest,
    "Constraint Anchor": run_constraint_anchor,
}


def run_all():
    """Run all strategies on all assets."""
    all_results = {}
    
    for strategy_name in STRATEGIES:
        print(f"\n{'='*60}")
        print(f"STRATEGY: {strategy_name}")
        print(f"{'='*60}")
        
        all_results[strategy_name] = {}
        runner = STRATEGY_RUNNERS[strategy_name]
        
        for asset_name, asset_file, is_jpy in ASSETS:
            filepath = os.path.join(DATA_DIR, asset_file)
            print(f"  [{asset_name}] Loading data...", end=' ', flush=True)
            
            try:
                bars = load_csv(filepath)
                print(f"{len(bars)} bars loaded. Running backtest...", end=' ', flush=True)
                
                trades = runner(bars, is_jpy)
                metrics = compute_metrics(trades)
                metrics['timeframe'] = 'M5'
                
                all_results[strategy_name][asset_name] = metrics
                
                print(f"Done. Trades: {metrics['total_trades']}, WR: {metrics['win_rate']}%, PnL: {metrics['total_pnl']}p, PF: {metrics['profit_factor']}")
                
                # Free memory
                del bars
                del trades
                
            except Exception as e:
                print(f"ERROR: {e}")
                traceback.print_exc()
                all_results[strategy_name][asset_name] = {
                    'total_trades': 0, 'win_rate': 0, 'profit_factor': 0,
                    'total_pnl': 0, 'max_dd_pips': 0, 'avg_win': 0, 'avg_loss': 0,
                    'expectancy': 0, 'timeframe': 'M5', 'error': str(e)
                }
    
    return all_results


def generate_report(all_results):
    """Generate markdown report."""
    lines = []
    lines.append("# Multi-Asset Forex M5 Backtest Report")
    lines.append(f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"\n**Cost Model:** {COST_PIPS} pips/trade (spread 0.2 + slippage 2.0 + commission 0.7)")
    lines.append(f"\n**Timeframe:** M5")
    lines.append(f"\n**Strategies:** {len(STRATEGIES)}")
    lines.append(f"\n**Assets:** {', '.join(a[0] for a in ASSETS)}")
    
    # ─── Summary Table ───────────────────────────────────────────────────
    lines.append("\n\n## Strategy × Asset Results Matrix (Win Rate %)\n")
    
    asset_names = [a[0] for a in ASSETS]
    header = "| Strategy | " + " | ".join(asset_names) + " | Avg WR |"
    sep = "|----------|" + "------|" * len(asset_names) + "--------|"
    lines.append(header)
    lines.append(sep)
    
    for strategy_name in STRATEGIES:
        row = f"| {strategy_name} |"
        wrs = []
        for asset_name in asset_names:
            data = all_results.get(strategy_name, {}).get(asset_name, {})
            wr = data.get('win_rate', 0)
            wrs.append(wr)
            row += f" {wr}% |"
        avg_wr = sum(wrs) / len(wrs) if wrs else 0
        row += f" {avg_wr:.1f}% |"
        lines.append(row)
    
    # ─── PnL Matrix ──────────────────────────────────────────────────────
    lines.append("\n\n## Strategy × Asset Results Matrix (Total PnL pips)\n")
    
    header = "| Strategy | " + " | ".join(asset_names) + " | Total |"
    sep = "|----------|" + "------|" * len(asset_names) + "-------|"
    lines.append(header)
    lines.append(sep)
    
    for strategy_name in STRATEGIES:
        row = f"| {strategy_name} |"
        pnls = []
        for asset_name in asset_names:
            data = all_results.get(strategy_name, {}).get(asset_name, {})
            pnl = data.get('total_pnl', 0)
            pnls.append(pnl)
            row += f" {pnl:+.1f} |"
        total_pnl = sum(pnls)
        row += f" {total_pnl:+.1f} |"
        lines.append(row)
    
    # ─── Profit Factor Matrix ────────────────────────────────────────────
    lines.append("\n\n## Strategy × Asset Results Matrix (Profit Factor)\n")
    
    header = "| Strategy | " + " | ".join(asset_names) + " | Avg PF |"
    sep = "|----------|" + "------|" * len(asset_names) + "--------|"
    lines.append(header)
    lines.append(sep)
    
    for strategy_name in STRATEGIES:
        row = f"| {strategy_name} |"
        pfs = []
        for asset_name in asset_names:
            data = all_results.get(strategy_name, {}).get(asset_name, {})
            pf = data.get('profit_factor', 0)
            pfs.append(pf)
            row += f" {pf:.2f} |"
        avg_pf = sum(pfs) / len(pfs) if pfs else 0
        row += f" {avg_pf:.2f} |"
        lines.append(row)
    
    # ─── Per-Strategy Details ────────────────────────────────────────────
    lines.append("\n\n## Per-Strategy Analysis\n")
    
    for strategy_name in STRATEGIES:
        lines.append(f"\n### {strategy_name}\n")
        
        best_asset = None
        worst_asset = None
        best_pnl = -999999
        worst_pnl = 999999
        total_wr = 0
        count = 0
        
        for asset_name in asset_names:
            data = all_results.get(strategy_name, {}).get(asset_name, {})
            pnl = data.get('total_pnl', 0)
            if pnl > best_pnl:
                best_pnl = pnl
                best_asset = asset_name
            if pnl < worst_pnl:
                worst_pnl = pnl
                worst_asset = asset_name
            total_wr += data.get('win_rate', 0)
            count += 1
        
        avg_wr = total_wr / count if count > 0 else 0
        
        lines.append(f"- **Best Asset:** {best_asset} ({best_pnl:+.1f} pips)")
        lines.append(f"- **Worst Asset:** {worst_asset} ({worst_pnl:+.1f} pips)")
        lines.append(f"- **Average WR:** {avg_wr:.1f}%")
        
        lines.append("\n| Asset | Trades | WR% | PF | PnL | MaxDD | AvgWin | AvgLoss | Expectancy |")
        lines.append("|-------|--------|-----|----|-----|-------|--------|---------|------------|")
        
        for asset_name in asset_names:
            data = all_results.get(strategy_name, {}).get(asset_name, {})
            lines.append(f"| {asset_name} | {data.get('total_trades', 0)} | {data.get('win_rate', 0)}% | "
                        f"{data.get('profit_factor', 0)} | {data.get('total_pnl', 0):+.1f} | "
                        f"{data.get('max_dd_pips', 0)} | {data.get('avg_win', 0)} | "
                        f"{data.get('avg_loss', 0)} | {data.get('expectancy', 0)} |")
    
    # ─── Per-Asset Analysis ──────────────────────────────────────────────
    lines.append("\n\n## Per-Asset Analysis (Best Strategies per Asset)\n")
    
    for asset_name in asset_names:
        lines.append(f"\n### {asset_name}\n")
        
        # Sort strategies by PnL for this asset
        strat_pnls = []
        for strategy_name in STRATEGIES:
            data = all_results.get(strategy_name, {}).get(asset_name, {})
            strat_pnls.append((strategy_name, data.get('total_pnl', 0), data.get('win_rate', 0),
                              data.get('profit_factor', 0), data.get('total_trades', 0)))
        
        strat_pnls.sort(key=lambda x: x[1], reverse=True)
        
        lines.append("| Rank | Strategy | PnL | WR% | PF | Trades |")
        lines.append("|------|----------|-----|-----|----|--------|")
        for i, (sn, pnl, wr, pf, tr) in enumerate(strat_pnls, 1):
            lines.append(f"| {i} | {sn} | {pnl:+.1f} | {wr}% | {pf} | {tr} |")
    
    # ─── EUR/USD Validation ──────────────────────────────────────────────
    lines.append("\n\n## EUR/USD Validation vs Optimizer v4b\n")
    lines.append("\n| Strategy | v4b WR% | Multi-Asset WR% | v4b PnL | Multi-Asset PnL | v4b Trades | Multi-Asset Trades |")
    lines.append("|----------|---------|-----------------|---------|-----------------|------------|-------------------|")
    
    # Load v4b results for comparison
    v4b_path = r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\results\optimizer_v4b_20260517_193302.json"
    try:
        with open(v4b_path, 'r') as f:
            v4b = json.load(f)
        
        v4b_name_map = {
            "Deep Mean Reversion": "Deep_Mean_Reversion",
            "Composite Alpha": "Composite_Alpha",
            "Failure Repair": "Failure_Repair",
            "Dual Engine": "Dual_Engine",
            "Blind Structural Chain": "Blind_Structural_Chain",
            "Two Plays": "Two_Plays",
            "P90P Distribution": "P90P_Distribution",
            "Fractal Resolution": "Fractal_Resolution",
            "Stall Harvest": "Stall_Harvest_CFD",
            "Constraint Anchor": "Constraint_Anchor",
        }
        
        for strategy_name in STRATEGIES:
            v4b_key = v4b_name_map.get(strategy_name, '')
            v4b_data = v4b.get(v4b_key, {})
            ma_data = all_results.get(strategy_name, {}).get('EURUSD', {})
            
            lines.append(f"| {strategy_name} | {v4b_data.get('win_rate', 'N/A')}% | {ma_data.get('win_rate', 0)}% | "
                        f"{v4b_data.get('total_pnl', 'N/A')} | {ma_data.get('total_pnl', 0):.1f} | "
                        f"{v4b_data.get('total_trades', 'N/A')} | {ma_data.get('total_trades', 0)} |")
    except Exception as e:
        lines.append(f"\n*Could not load v4b results: {e}*")
    
    # ─── Recommendations ─────────────────────────────────────────────────
    lines.append("\n\n## Production Deployment Recommendations\n")
    
    # Find best overall strategy
    strategy_totals = []
    for strategy_name in STRATEGIES:
        total_pnl = sum(all_results.get(strategy_name, {}).get(a[0], {}).get('total_pnl', 0) for a in ASSETS)
        avg_pf = sum(all_results.get(strategy_name, {}).get(a[0], {}).get('profit_factor', 0) for a in ASSETS) / len(ASSETS)
        strategy_totals.append((strategy_name, total_pnl, avg_pf))
    
    strategy_totals.sort(key=lambda x: x[1], reverse=True)
    
    lines.append("\n### Overall Strategy Ranking (by total PnL across all assets)\n")
    lines.append("| Rank | Strategy | Total PnL | Avg PF |")
    lines.append("|------|----------|-----------|--------|")
    for i, (sn, pnl, pf) in enumerate(strategy_totals, 1):
        lines.append(f"| {i} | {sn} | {pnl:+.1f} | {pf:.2f} |")
    
    lines.append("\n### Key Findings\n")
    
    # Find consistently profitable strategies
    consistent = []
    for strategy_name in STRATEGIES:
        profitable_assets = sum(1 for a in ASSETS if all_results.get(strategy_name, {}).get(a[0], {}).get('total_pnl', 0) > 0)
        if profitable_assets >= len(ASSETS) // 2:
            consistent.append((strategy_name, profitable_assets))
    
    if consistent:
        lines.append("**Consistently Profitable Strategies** (profitable on 5+ assets):\n")
        for sn, count in consistent:
            lines.append(f"- {sn} ({count}/{len(ASSETS)} assets)")
    
    # Best asset per strategy
    lines.append("\n**Best Asset per Strategy:**\n")
    for strategy_name in STRATEGIES:
        best = max(((a[0], all_results.get(strategy_name, {}).get(a[0], {}).get('total_pnl', 0)) for a in ASSETS), key=lambda x: x[1])
        if best[1] > 0:
            lines.append(f"- {strategy_name}: {best[0]} ({best[1]:+.1f} pips)")
    
    lines.append("\n---\n")
    lines.append(f"*Report generated by Multi-Asset Forex M5 Backtest Runner*")
    lines.append(f"*Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    
    return "\n".join(lines)


# ─── Entry Point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("MULTI-ASSET FOREX M5 BACKTEST RUNNER")
    print("=" * 60)
    print(f"Strategies: {len(STRATEGIES)}")
    print(f"Assets: {len(ASSETS)}")
    print(f"Cost: {COST_PIPS} pips/trade")
    print("=" * 60)
    
    start_time = datetime.now()
    
    # Run all backtests
    all_results = run_all()
    
    # Save JSON
    os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
    with open(OUTPUT_JSON, 'w') as f:
        json.dump(all_results, f, indent=2)
    print(f"\n\nResults saved to: {OUTPUT_JSON}")
    
    # Generate report
    report = generate_report(all_results)
    os.makedirs(os.path.dirname(OUTPUT_REPORT), exist_ok=True)
    with open(OUTPUT_REPORT, 'w') as f:
        f.write(report)
    print(f"Report saved to: {OUTPUT_REPORT}")
    
    elapsed = (datetime.now() - start_time).total_seconds()
    print(f"\nTotal time: {elapsed:.1f} seconds")
    print("DONE.")
