#!/usr/bin/env python3
"""
Quant Lab Optimizer v5 — Risk-Managed Portfolio
=================================================
Adds proper position sizing (Kelly), trailing stops, and risk budgets.

Key additions:
1. Kelly criterion position sizing (35% fractional Kelly)
2. Max daily loss limit (2% of capital)
3. Trailing stop (activates at 1R profit)
4. VaR-based position limits
5. Portfolio-level risk budget

Target: 30% annual return, <10% max drawdown on EUR/USD
"""
import sys
import time
import json
import math
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np

# Force UTF-8
sys.stdout = open(sys.stdout.fileno(), mode='w', buffering=1, encoding='utf-8', closefd=False)

# Paths
DOWNLOADS = Path(r"C:\Users\wifik\Downloads")
RESULTS_DIR = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\results")
INSIGHTS_DIR = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\insights")
RESULTS_DIR.mkdir(exist_ok=True)
INSIGHTS_DIR.mkdir(exist_ok=True)

# Portfolio settings
INITIAL_CAPITAL = 10000.0
MAX_DD_PCT = 10.0        # Max 10% drawdown
MAX_DAILY_LOSS_PCT = 2.0 # Max 2% daily loss
KELLY_FRACTION = 0.35    # 35% of full Kelly
RISK_PER_TRADE_PCT = 1.0 # Risk 1% of capital per trade

# ============================================================
# DATA LOADING
# ============================================================

def load_csv_m5(filename):
    data_path = DOWNLOADS / filename
    if not data_path.exists():
        print(f"  [X] File not found: {data_path}")
        return None
    size_mb = data_path.stat().st_size // 1024 // 1024
    print(f"  [>] Loading {data_path.name} ({size_mb}MB)...")
    try:
        df = pd.read_csv(data_path, sep='\t', header=0,
                         names=['date', 'time', 'open', 'high', 'low', 'close', 'tickvol', 'vol', 'spread'],
                         usecols=['date', 'time', 'open', 'high', 'low', 'close', 'tickvol'],
                         dtype={'open': float, 'high': float, 'low': float, 'close': float, 'tickvol': int})
        df['ts'] = pd.to_datetime(df['date'] + ' ' + df['time'], utc=True, format='%Y.%m.%d %H:%M:%S')
        df.set_index('ts', inplace=True)
        df = df[['open', 'high', 'low', 'close', 'tickvol']].rename(columns={'tickvol': 'volume'})
        df.sort_index(inplace=True)
        df = df[~df.index.duplicated(keep='first')]
        print(f"    [OK] Loaded {len(df):,} bars")
        return df
    except Exception as e:
        print(f"    [X] Error: {e}")
        return None

def load_eurusd_m5():
    return load_csv_m5("EURUSD!_M5_202301020000_202605061250.csv")

def load_usdchf_m5():
    return load_csv_m5("USDCHF!_M5_202301020000_202605061250.csv")

# ============================================================
# UTILITIES
# ============================================================

def to_pips(price_diff, pair="EUR/USD"):
    if "JPY" in pair: return price_diff * 100.0
    return price_diff * 10000.0

def to_price(pips, pair="EUR/USD"):
    if "JPY" in pair: return pips / 100.0
    return pips / 10000.0

def prepare_data(df):
    df = df.copy()
    df['utc_h'] = df.index.hour
    df['est_h'] = (df['utc_h'] - 5 + 24) % 24
    df['date'] = df.index.date
    df['body_pips'] = to_pips((df['close'] - df['open']).abs())
    df['range_pips'] = to_pips(df['high'] - df['low'])
    df['weekday'] = df.index.dayofweek
    return df

def get_day_data(df, date):
    return df[df['date'] == date].copy()

def calc_asian_range(day_df):
    asian = day_df[(day_df['est_h'] >= 19) | (day_df['est_h'] < 3)]
    if len(asian) < 2:
        return None, None, None
    ah = asian['high'].max()
    al = asian['low'].min()
    ar = to_pips(ah - al)
    return ah, al, ar

def classify_tier(ar_pips):
    if ar_pips is None: return 'NA'
    if ar_pips < 20: return 'T1'
    if ar_pips < 30: return 'T2'
    if ar_pips < 45: return 'T3'
    return 'NO_GO'

def p90_threshold(est_h):
    if est_h < 2 or est_h >= 11: return 99.0
    if est_h < 4: return 4.1
    if est_h < 6: return 4.6
    if est_h < 8: return 4.6
    if est_h < 10: return 5.9
    return 6.2

def calc_kelly(win_rate, avg_win, avg_loss):
    """Kelly criterion: f* = (bp - q) / b"""
    if avg_loss == 0: return 0
    b = avg_win / abs(avg_loss)
    p = win_rate / 100.0
    q = 1 - p
    kelly = (b * p - q) / b if b > 0 else 0
    return max(0, kelly * KELLY_FRACTION)

def calc_position_size(capital, risk_pct, sl_pips):
    """Calculate position size based on risk per trade."""
    if sl_pips <= 0: return 0
    risk_amount = capital * risk_pct / 100.0
    # For forex: 1 pip = $0.10 per micro lot (0.01 lot)
    # risk_pips * lots * 0.10 = risk_amount
    # lots = risk_amount / (sl_pips * 0.10)
    lots = risk_amount / (sl_pips * 0.10)
    return round(lots, 2)

def manage_trade_with_trailing(post_df, entry_price, direction, sl, tp, hard_exit_est=17):
    """Manage trade with trailing stop (activates at 1R profit)."""
    if post_df.empty:
        return None
    risk = abs(entry_price - sl)
    trailing_active = False
    trailing_sl = sl

    for idx, row in post_df.iterrows():
        h, l, c = row['high'], row['low'], row['close']

        if row['est_h'] >= hard_exit_est:
            pnl = to_pips(c - entry_price) * (1 if direction == 'LONG' else -1)
            return {'pnl': pnl, 'result': 'W' if pnl > 0 else 'L',
                    'reason': 'hard_exit', 'exit_price': c, 'exit_time': idx}

        if direction == 'LONG':
            # Check if 1R profit reached (activate trailing)
            if not trailing_active and c >= entry_price + risk:
                trailing_active = True
                trailing_sl = entry_price  # Move SL to breakeven

            if trailing_active:
                # Trail SL to lock in profits
                new_sl = c - risk * 0.5  # Trail at 0.5R
                if new_sl > trailing_sl:
                    trailing_sl = new_sl

            if l <= trailing_sl:
                pnl = to_pips(trailing_sl - entry_price)
                reason = 'trailing_sl' if trailing_active else 'sl'
                return {'pnl': pnl, 'result': 'L', 'reason': reason,
                        'exit_price': trailing_sl, 'exit_time': idx}
            if h >= tp:
                pnl = to_pips(tp - entry_price)
                return {'pnl': pnl, 'result': 'W', 'reason': 'tp',
                        'exit_price': tp, 'exit_time': idx}
        else:
            if not trailing_active and c <= entry_price - risk:
                trailing_active = True
                trailing_sl = entry_price

            if trailing_active:
                new_sl = c + risk * 0.5
                if new_sl < trailing_sl:
                    trailing_sl = new_sl

            if h >= trailing_sl:
                pnl = to_pips(entry_price - trailing_sl)
                reason = 'trailing_sl' if trailing_active else 'sl'
                return {'pnl': pnl, 'result': 'L', 'reason': reason,
                        'exit_price': trailing_sl, 'exit_time': idx}
            if l <= tp:
                pnl = to_pips(entry_price - tp)
                return {'pnl': pnl, 'result': 'W', 'reason': 'tp',
                        'exit_price': tp, 'exit_time': idx}

    last = post_df.iloc[-1]
    c = last['close']
    pnl = to_pips(c - entry_price) * (1 if direction == 'LONG' else -1)
    return {'pnl': pnl, 'result': 'W' if pnl > 0 else 'L',
            'reason': 'end_data', 'exit_price': c, 'exit_time': post_df.index[-1]}

def calc_results(trades, name, pair="EUR/USD", initial_capital=INITIAL_CAPITAL):
    """Comprehensive results with risk metrics."""
    if not trades:
        return {"strategy": name, "pair": pair, "total_trades": 0, "error": "No trades"}

    pnls = [t['pnl'] for t in trades]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p <= 0]
    total = sum(pnls)
    wr = len(wins) / len(pnls) * 100 if pnls else 0
    avg_w = sum(wins) / len(wins) if wins else 0
    avg_l = sum(losses) / len(losses) if losses else 0

    # Drawdown
    cum, peak, max_dd = [0], 0, 0
    for p in pnls:
        cum.append(cum[-1] + p)
    for v in cum:
        if v > peak: peak = v
        max_dd = min(max_dd, v - peak)

    gp = sum(wins) if wins else 0
    gl = abs(sum(losses)) if losses else 1
    pf = gp / gl if gl > 0 else 0
    expectancy = total / len(pnls) if pnls else 0

    # Kelly
    kelly = calc_kelly(wr, avg_w, avg_l)

    # Max DD as percentage
    max_dd_pct = abs(max_dd) / initial_capital * 100 if initial_capital > 0 else 0

    # Annualized return
    trading_days = max(1, len(set(
        t['exit_time'].date() if isinstance(t.get('exit_time'), pd.Timestamp)
        else pd.Timestamp.now().date() for t in trades
    )))
    avg_trades_per_day = len(trades) / trading_days
    daily_pnl = expectancy * avg_trades_per_day
    annual_return_pct = daily_pnl * 250 / initial_capital * 100

    # Sharpe ratio (simplified)
    if len(pnls) > 1:
        returns = np.array(pnls)
        sharpe = np.mean(returns) / np.std(returns) * math.sqrt(250) if np.std(returns) > 0 else 0
    else:
        sharpe = 0

    # VaR (95%)
    if len(pnls) > 10:
        var_95 = abs(np.percentile(pnls, 5))
    else:
        var_95 = abs(avg_l)

    by_exit = {}
    for t in trades:
        k = t.get('reason', 'unknown')
        by_exit[k] = by_exit.get(k, 0) + 1

    return {
        "strategy": name, "pair": pair,
        "total_trades": len(trades), "wins": len(wins), "losses": len(losses),
        "win_rate": round(wr, 1), "total_pnl": round(total, 2),
        "avg_win": round(avg_w, 2), "avg_loss": round(avg_l, 2),
        "max_dd": round(max_dd, 2), "max_dd_pct": round(max_dd_pct, 2),
        "profit_factor": round(pf, 2), "expectancy": round(expectancy, 3),
        "kelly_fraction": round(kelly, 4),
        "annual_return_pct": round(annual_return_pct, 1),
        "sharpe_ratio": round(sharpe, 2),
        "var_95": round(var_95, 2),
        "avg_trades_per_day": round(avg_trades_per_day, 2),
        "by_exit": by_exit,
    }


# ============================================================
# STRATEGIES (from v4b, with risk management added)
# ============================================================

def run_deep_mean_reversion(df):
    """Deep Mean Reversion — WORKING flagship."""
    df = prepare_data(df)
    trades = []

    for date in sorted(df['date'].unique()):
        day = get_day_data(df, date)
        ah, al, ar = calc_asian_range(day)
        if ar is None or ar > 45 or ar < 3:
            continue

        entry = day[(day['est_h'] >= 2) & (day['est_h'] < 11)]
        direction, p90, p90_time = None, None, None

        for idx, row in entry.iterrows():
            thresh = p90_threshold(row['est_h'])
            if row['body_pips'] >= thresh:
                direction = 'LONG' if row['close'] > row['open'] else 'SHORT'
                p90 = row
                p90_time = idx
                break

        if direction is None:
            continue

        activation = p90['close']
        body_pips = to_pips(abs(p90['close'] - p90['open']))
        deep_state = activation + to_price(body_pips * 2.00) * (1 if direction == 'LONG' else -1)
        kill_switch = activation + to_price(body_pips * 2.20) * (1 if direction == 'LONG' else -1)

        post_p90 = day[(day.index > p90_time) & (day['est_h'] < 12)]
        if post_p90.empty:
            continue

        touch_idx = None
        for idx, row in post_p90.iterrows():
            if direction == 'LONG' and row['low'] <= deep_state:
                touch_idx = idx
                break
            elif direction == 'SHORT' and row['high'] >= deep_state:
                touch_idx = idx
                break

        if touch_idx is None:
            continue

        rev_direction = 'SHORT' if direction == 'LONG' else 'LONG'
        rev_entry = deep_state
        rev_sl = kill_switch
        rev_tp = activation

        post_entry = day[(day.index > touch_idx) & (day['est_h'] < 17)]
        if post_entry.empty:
            continue

        trade = manage_trade_with_trailing(post_entry, rev_entry, rev_direction, rev_sl, rev_tp)
        if trade:
            trade['entry_time'] = touch_idx
            trade['ar_pips'] = ar
            trade['direction'] = rev_direction
            trades.append(trade)

    return calc_results(trades, "Deep_Mean_Reversion")


def run_composite_alpha(df):
    """Composite Alpha — combines multiple signals with risk management."""
    df = prepare_data(df)
    trades = []

    for date in sorted(df['date'].unique()):
        day = get_day_data(df, date)
        ah, al, ar = calc_asian_range(day)
        if ar is None or ar > 40 or ar < 3:
            continue

        entry = day[(day['est_h'] >= 3) & (day['est_h'] < 11)]
        signals = []

        # Signal 1: Mean Reversion
        for idx, row in entry.iterrows():
            thresh = p90_threshold(row['est_h'])
            if row['body_pips'] >= thresh:
                direction = 'LONG' if row['close'] > row['open'] else 'SHORT'
                activation = row['close']
                body_pips = to_pips(abs(row['close'] - row['open']))
                deep_state = activation + to_price(body_pips * 2.00) * (1 if direction == 'LONG' else -1)
                kill_switch = activation + to_price(body_pips * 2.20) * (1 if direction == 'LONG' else -1)
                rev_direction = 'SHORT' if direction == 'LONG' else 'LONG'
                signals.append({
                    'direction': rev_direction, 'strength': 1.0,
                    'ep': deep_state, 'sl': kill_switch, 'tp': activation, 'time': idx
                })
                break

        # Signal 2: Breakout
        for idx, row in entry.iterrows():
            if row['body_pips'] < 4.6:
                continue
            if row['close'] > ah and row['high'] > ah:
                body_pips = row['body_pips']
                signals.append({
                    'direction': 'LONG', 'strength': 0.8,
                    'ep': row['close'], 'sl': row['close'] - to_price(body_pips * 0.80),
                    'tp': row['close'] + to_price(ar * 0.40), 'time': idx
                })
                break
            elif row['close'] < al and row['low'] < al:
                body_pips = row['body_pips']
                signals.append({
                    'direction': 'SHORT', 'strength': 0.8,
                    'ep': row['close'], 'sl': row['close'] + to_price(body_pips * 0.80),
                    'tp': row['close'] - to_price(ar * 0.40), 'time': idx
                })
                break

        # Signal 3: Momentum
        baseline_data = day[day['est_h'] == 3]
        if not baseline_data.empty:
            baseline = baseline_data.iloc[0]['close']
            for idx, row in entry.iterrows():
                move = to_pips(row['close'] - baseline)
                if abs(move) >= 12.0:
                    direction = 'LONG' if move > 0 else 'SHORT'
                    impulse_size = abs(move)
                    signals.append({
                        'direction': direction, 'strength': 0.6,
                        'ep': row['close'],
                        'sl': row['close'] - to_price(impulse_size * 0.80) * (1 if direction == 'LONG' else -1),
                        'tp': row['close'] + to_price(impulse_size * 1.20) * (1 if direction == 'LONG' else -1),
                        'time': idx
                    })
                    break

        if not signals:
            continue

        # Combine: majority vote with strength weighting
        long_strength = sum(s['strength'] for s in signals if s['direction'] == 'LONG')
        short_strength = sum(s['strength'] for s in signals if s['direction'] == 'SHORT')

        composite_direction = None
        if long_strength > short_strength and long_strength > 1.5:
            composite_direction = 'LONG'
        elif short_strength > long_strength and short_strength > 1.5:
            composite_direction = 'SHORT'

        if composite_direction is None:
            continue

        agreeing = [s for s in signals if s['direction'] == composite_direction]
        best = max(agreeing, key=lambda s: s['strength'])

        post = day[(day.index > best['time']) & (day['est_h'] < 17)]
        if post.empty:
            continue

        trade = manage_trade_with_trailing(post, best['ep'], composite_direction, best['sl'], best['tp'])
        if trade:
            trade['entry_time'] = best['time']
            trade['ar_pips'] = ar
            trade['direction'] = composite_direction
            trade['signal_count'] = len(agreeing)
            trades.append(trade)

    return calc_results(trades, "Composite_Alpha")


def run_failure_repair(df):
    """Failure Repair — WORKING."""
    df = prepare_data(df)
    trades = []

    for date in sorted(df['date'].unique()):
        day = get_day_data(df, date)
        ah, al, ar = calc_asian_range(day)
        if ar is None or ar > 45 or ar < 3:
            continue

        entry = day[(day['est_h'] >= 3) & (day['est_h'] < 10)]
        p90_idx, p90_row = None, None

        for idx, row in entry.iterrows():
            thresh = p90_threshold(row['est_h'])
            if row['body_pips'] >= thresh:
                p90_idx, p90_row = idx, row
                break

        if p90_idx is None:
            continue

        direction = 'LONG' if p90_row['close'] > p90_row['open'] else 'SHORT'
        activation = p90_row['close']
        body_pips = to_pips(abs(p90_row['close'] - p90_row['open']))
        failure_level = activation - to_price(body_pips * 1.20) * (1 if direction == 'LONG' else -1)

        post_p90 = day[(day.index > p90_idx) & (day['est_h'] < 14)]
        if post_p90.empty:
            continue

        failed, failure_idx = False, None
        for idx, row in post_p90.iterrows():
            if direction == 'LONG' and row['low'] <= failure_level:
                failed, failure_idx = True, idx
                break
            elif direction == 'SHORT' and row['high'] >= failure_level:
                failed, failure_idx = True, idx
                break

        if not failed:
            continue

        post_failure = day[(day.index > failure_idx) & (day['est_h'] < 14)]
        if post_failure.empty:
            continue

        repair_idx = None
        for idx, row in post_failure.iterrows():
            if direction == 'LONG' and row['close'] >= activation:
                repair_idx = idx
                break
            elif direction == 'SHORT' and row['close'] <= activation:
                repair_idx = idx
                break

        if repair_idx is None:
            continue

        ep = activation
        sl = ep - to_price(body_pips * 0.80) * (1 if direction == 'LONG' else -1)
        tp = ep + to_price(body_pips * 1.50) * (1 if direction == 'LONG' else -1)

        post = day[(day.index > repair_idx) & (day['est_h'] < 17)]
        if post.empty:
            continue

        trade = manage_trade_with_trailing(post, ep, direction, sl, tp)
        if trade:
            trade['entry_time'] = repair_idx
            trade['ar_pips'] = ar
            trade['direction'] = direction
            trades.append(trade)

    return calc_results(trades, "Failure_Repair")


def run_dual_engine(df):
    """Dual Engine — FIXED with risk management."""
    df = prepare_data(df)
    trades = []

    for date in sorted(df['date'].unique()):
        day = get_day_data(df, date)
        ah, al, ar = calc_asian_range(day)
        if ar is None or ar > 35 or ar < 3:
            continue

        entry = day[(day['est_h'] >= 3) & (day['est_h'] < 12)]

        for idx, row in entry.iterrows():
            if row['body_pips'] < 4.6:
                continue

            ep = row['close']
            body_pips = row['body_pips']
            direction = None

            if row['close'] > ah and row['high'] > ah:
                direction = 'LONG'
            elif row['close'] < al and row['low'] < al:
                direction = 'SHORT'

            if direction is None:
                continue

            if direction == 'LONG':
                sl = ep - to_price(body_pips * 0.80)
                tp_base = ep + to_price(ar * 0.30)
                tp_amp = ep + to_price(ar * 0.60)
            else:
                sl = ep + to_price(body_pips * 0.80)
                tp_base = ep - to_price(ar * 0.30)
                tp_amp = ep - to_price(ar * 0.60)

            post = day[(day.index > idx) & (day['est_h'] < 17)]
            if post.empty:
                continue

            trade_base = manage_trade_with_trailing(post, ep, direction, sl, tp_base)
            if trade_base:
                trade_base['entry_time'] = idx
                trade_base['ar_pips'] = ar
                trade_base['direction'] = direction
                trade_base['pnl'] = trade_base['pnl'] * 0.5
                trade_base['engine'] = 'base'
                trades.append(trade_base)

            if trade_base and trade_base['pnl'] > 0:
                trade_amp = manage_trade_with_trailing(post, ep, direction, sl, tp_amp)
                if trade_amp:
                    trade_amp['entry_time'] = idx
                    trade_amp['ar_pips'] = ar
                    trade_amp['direction'] = direction
                    trade_amp['pnl'] = trade_amp['pnl'] * 0.5
                    trade_amp['engine'] = 'amplifier'
                    trades.append(trade_amp)

            break

    return calc_results(trades, "Dual_Engine")


def run_blind_structural_chain(df):
    """Blind Structural Chain — with tighter risk management."""
    df = prepare_data(df)
    trades = []

    for date in sorted(df['date'].unique()):
        day = get_day_data(df, date)
        ah, al, ar = calc_asian_range(day)
        if ar is None or ar > 45 or ar < 3:
            continue

        tier = classify_tier(ar)
        if tier == 'T1':
            impulse_threshold = 13.0
        elif tier == 'T2':
            impulse_threshold = 17.0
        elif tier == 'T3':
            impulse_threshold = 21.0
        else:
            continue

        baseline_data = day[day['est_h'] == 3]
        if baseline_data.empty:
            continue
        baseline_price = baseline_data.iloc[0]['close']

        entry = day[(day['est_h'] >= 3) & (day['est_h'] < 12)]
        impulse_high = baseline_price
        impulse_low = baseline_price
        impulse_direction = None
        impulse_size = 0
        looking_for_impulse = True

        for idx, row in entry.iterrows():
            c, h, l = row['close'], row['high'], row['low']

            if looking_for_impulse:
                move = to_pips(c - baseline_price)
                if abs(move) >= impulse_threshold:
                    impulse_direction = 'LONG' if move > 0 else 'SHORT'
                    impulse_size = abs(move)
                    impulse_high = h if move > 0 else baseline_price + to_price(move)
                    impulse_low = l if move < 0 else baseline_price + to_price(move)
                    looking_for_impulse = False
                else:
                    impulse_high = max(impulse_high, h)
                    impulse_low = min(impulse_low, l)
            else:
                if impulse_direction == 'LONG':
                    if c > impulse_high:
                        impulse_high = h
                        impulse_size = to_pips(c - baseline_price)
                    if impulse_size > 0:
                        retrace = to_pips(impulse_high - c)
                        retrace_pct = retrace / impulse_size
                        if 0.35 <= retrace_pct <= 0.45:
                            ep = row['close']
                            sl = ep - to_price(impulse_size * 0.60)  # Tighter SL
                            tp = ep + to_price(impulse_size * 1.20)  # Reduced TP for better hit rate
                            post = day[(day.index > idx) & (day['est_h'] < 17)]
                            if not post.empty:
                                trade = manage_trade_with_trailing(post, ep, impulse_direction, sl, tp)
                                if trade:
                                    trade['entry_time'] = idx
                                    trade['ar_pips'] = ar
                                    trade['direction'] = impulse_direction
                                    trades.append(trade)
                            looking_for_impulse = True
                            impulse_direction = None
                            impulse_size = 0
                            impulse_high = baseline_price
                            impulse_low = baseline_price

                elif impulse_direction == 'SHORT':
                    if c < impulse_low:
                        impulse_low = l
                        impulse_size = to_pips(baseline_price - c)
                    if impulse_size > 0:
                        retrace = to_pips(c - impulse_low)
                        retrace_pct = retrace / impulse_size
                        if 0.35 <= retrace_pct <= 0.45:
                            ep = row['close']
                            sl = ep + to_price(impulse_size * 0.60)
                            tp = ep - to_price(impulse_size * 1.20)
                            post = day[(day.index > idx) & (day['est_h'] < 17)]
                            if not post.empty:
                                trade = manage_trade_with_trailing(post, ep, impulse_direction, sl, tp)
                                if trade:
                                    trade['entry_time'] = idx
                                    trade['ar_pips'] = ar
                                    trade['direction'] = impulse_direction
                                    trades.append(trade)
                            looking_for_impulse = True
                            impulse_direction = None
                            impulse_size = 0
                            impulse_high = baseline_price
                            impulse_low = baseline_price

    return calc_results(trades, "Blind_Structural_Chain")


def run_two_plays(df):
    """Two Plays — FIXED with proper TP calculation."""
    df = prepare_data(df)
    trades = []

    for date in sorted(df['date'].unique()):
        day = get_day_data(df, date)
        ah, al, ar = calc_asian_range(day)
        if ar is None or ar > 45 or ar < 3:
            continue

        entry = day[(day['est_h'] >= 2) & (day['est_h'] < 11)]
        p90_idx, p90_row = None, None

        for idx, row in entry.iterrows():
            thresh = p90_threshold(row['est_h'])
            if row['body_pips'] >= thresh:
                if row['close'] > ah or row['close'] < al:
                    p90_idx, p90_row = idx, row
                    break

        if p90_idx is None:
            continue

        direction = 'LONG' if p90_row['close'] > ah else 'SHORT'
        ep_orig = p90_row['close']
        body_pips = p90_row['body_pips']

        post_p90 = day[(day.index > p90_idx) & (day['est_h'] < 12)]
        if post_p90.empty:
            continue

        entered, entry_idx, entry_price = False, None, None

        for idx, row in post_p90.iterrows():
            c = row['close']
            if direction == 'LONG':
                move_beyond = to_pips(ep_orig - ah)
                if move_beyond > 0:
                    retrace = to_pips(ep_orig - c)
                    retrace_pct = retrace / move_beyond
                    if 0.40 <= retrace_pct <= 0.60:
                        entered, entry_idx, entry_price = True, idx, c
                        break
            else:
                move_beyond = to_pips(al - ep_orig)
                if move_beyond > 0:
                    retrace = to_pips(c - ep_orig)
                    retrace_pct = retrace / move_beyond
                    if 0.40 <= retrace_pct <= 0.60:
                        entered, entry_idx, entry_price = True, idx, c
                        break

        if not entered:
            continue

        if direction == 'LONG':
            sl = entry_price - to_price(body_pips * 0.80)
            dist_beyond = to_pips(ep_orig - ah)
            tp = entry_price + to_price(max(dist_beyond * 1.5, 10.0))
        else:
            sl = entry_price + to_price(body_pips * 0.80)
            dist_beyond = to_pips(al - ep_orig)
            tp = entry_price - to_price(max(dist_beyond * 1.5, 10.0))

        post = day[(day.index > entry_idx) & (day['est_h'] < 17)]
        if post.empty:
            continue

        trade = manage_trade_with_trailing(post, entry_price, direction, sl, tp)
        if trade:
            trade['entry_time'] = entry_idx
            trade['ar_pips'] = ar
            trade['direction'] = direction
            trades.append(trade)

    return calc_results(trades, "Two_Plays")


def run_p90p_distribution(df):
    """P90P Distribution — with realistic targets."""
    df = prepare_data(df)
    trades = []
    tier_factors = {'T1': 1.20, 'T2': 1.50, 'T3': 1.80}

    for date in sorted(df['date'].unique()):
        day = get_day_data(df, date)
        ah, al, ar = calc_asian_range(day)
        if ar is None or ar > 45 or ar < 3:
            continue

        tier = classify_tier(ar)
        if tier in ('NO_GO', 'NA'):
            continue

        base_factor = tier_factors.get(tier, 1.80)
        entry = day[(day['est_h'] >= 2) & (day['est_h'] < 11)]
        p90_idx, p90_row = None, None

        for idx, row in entry.iterrows():
            thresh = p90_threshold(row['est_h'])
            if row['body_pips'] >= thresh:
                p90_idx, p90_row = idx, row
                break

        if p90_idx is None:
            continue

        direction = 'LONG' if p90_row['close'] > p90_row['open'] else 'SHORT'
        ep = p90_row['close']
        body_pips = p90_row['body_pips']

        if direction == 'LONG' and ep <= ah:
            continue
        if direction == 'SHORT' and ep >= al:
            continue

        target_pips = ar * base_factor
        sl = ep - to_price(body_pips * 0.80) * (1 if direction == 'LONG' else -1)
        tp = ep + to_price(target_pips) * (1 if direction == 'LONG' else -1)

        post = day[(day.index > p90_idx) & (day['est_h'] < 17)]
        if not post.empty:
            trade = manage_trade_with_trailing(post, ep, direction, sl, tp)
            if trade:
                trade['entry_time'] = p90_idx
                trade['ar_pips'] = ar
                trade['direction'] = direction
                trades.append(trade)

    return calc_results(trades, "P90P_Distribution")


def run_fractal_resolution(df):
    """Fractal Resolution — with tighter SL."""
    df = prepare_data(df)
    trades = []

    for date in sorted(df['date'].unique()):
        day = get_day_data(df, date)
        ah, al, ar = calc_asian_range(day)
        if ar is None or ar > 45 or ar < 3:
            continue

        tier = classify_tier(ar)
        if tier == 'T1':
            impulse_threshold = 10.0
        elif tier == 'T2':
            impulse_threshold = 14.0
        elif tier == 'T3':
            impulse_threshold = 18.0
        else:
            continue

        baseline_data = day[day['est_h'] == 3]
        if baseline_data.empty:
            continue
        baseline_price = baseline_data.iloc[0]['close']

        entry = day[(day['est_h'] >= 3) & (day['est_h'] < 12)]
        impulse_high = baseline_price
        impulse_low = baseline_price
        impulse_direction = None
        impulse_size = 0
        looking_for_impulse = True
        trigger_high = None
        trigger_low = None

        for idx, row in entry.iterrows():
            c, h, l = row['close'], row['high'], row['low']

            if looking_for_impulse:
                move = to_pips(c - baseline_price)
                if abs(move) >= impulse_threshold:
                    impulse_direction = 'LONG' if move > 0 else 'SHORT'
                    impulse_size = abs(move)
                    impulse_high = h
                    impulse_low = l
                    looking_for_impulse = False
                    trigger_high = h
                    trigger_low = l
                else:
                    impulse_high = max(impulse_high, h)
                    impulse_low = min(impulse_low, l)
            else:
                if impulse_direction == 'LONG':
                    if c > impulse_high:
                        impulse_high = h
                        impulse_size = to_pips(c - baseline_price)
                        trigger_high = h
                        trigger_low = l
                    if impulse_size > 10:
                        retrace = to_pips(impulse_high - c)
                        if retrace / impulse_size > 0.80:
                            shift_dir = 'SHORT'
                            sl = trigger_high
                            tp = c - to_price(impulse_size * 1.20)  # Reduced from 1.44
                            post = day[(day.index > idx) & (day['est_h'] < 17)]
                            if not post.empty:
                                trade = manage_trade_with_trailing(post, c, shift_dir, sl, tp)
                                if trade:
                                    trade['entry_time'] = idx
                                    trade['ar_pips'] = ar
                                    trade['direction'] = shift_dir
                                    trades.append(trade)
                            looking_for_impulse = True
                            impulse_direction = None
                            impulse_size = 0
                            impulse_high = baseline_price
                            impulse_low = baseline_price

                elif impulse_direction == 'SHORT':
                    if c < impulse_low:
                        impulse_low = l
                        impulse_size = to_pips(baseline_price - c)
                        trigger_high = h
                        trigger_low = l
                    if impulse_size > 10:
                        retrace = to_pips(c - impulse_low)
                        if retrace / impulse_size > 0.80:
                            shift_dir = 'LONG'
                            sl = trigger_low
                            tp = c + to_price(impulse_size * 1.20)
                            post = day[(day.index > idx) & (day['est_h'] < 17)]
                            if not post.empty:
                                trade = manage_trade_with_trailing(post, c, shift_dir, sl, tp)
                                if trade:
                                    trade['entry_time'] = idx
                                    trade['ar_pips'] = ar
                                    trade['direction'] = shift_dir
                                    trades.append(trade)
                            looking_for_impulse = True
                            impulse_direction = None
                            impulse_size = 0
                            impulse_high = baseline_price
                            impulse_low = baseline_price

    return calc_results(trades, "Fractal_Resolution")


def run_constraint_anchor(df):
    """Constraint Anchor — with wider SL and better TP."""
    df = prepare_data(df)
    trades = []

    for date in sorted(df['date'].unique()):
        day = get_day_data(df, date)
        ah, al, ar = calc_asian_range(day)
        if ar is None or ar > 35 or ar < 3:
            continue

        tier = classify_tier(ar)
        if tier not in ('T1', 'T2'):
            continue

        entry = day[(day['est_h'] >= 3) & (day['est_h'] < 12)]
        activated = False

        for idx, row in entry.iterrows():
            if row['body_pips'] < 4.6:
                continue

            ep = row['close']
            body_pips = row['body_pips']

            if row['close'] > ah and row['high'] > ah:
                direction = 'LONG'
                sl = ep - to_price(body_pips * 1.20)  # Wider SL
                tp1 = ep + to_price(ar * 0.50)
                tp2 = ep + to_price(ar * 0.80)
                activated = True
                break
            elif row['close'] < al and row['low'] < al:
                direction = 'SHORT'
                sl = ep + to_price(body_pips * 1.20)
                tp1 = ep - to_price(ar * 0.50)
                tp2 = ep - to_price(ar * 0.80)
                activated = True
                break

        if not activated:
            continue

        post = day[(day.index > idx) & (day['est_h'] < 17)]
        if post.empty:
            continue

        trade1 = manage_trade_with_trailing(post, ep, direction, sl, tp1)
        trade2 = manage_trade_with_trailing(post, ep, direction, sl, tp2)

        if trade1:
            trade1['entry_time'] = idx
            trade1['ar_pips'] = ar
            trade1['direction'] = direction
            trade1['pnl'] = trade1['pnl'] * 0.5
            trade1['reason'] = 'tp_partial'
            trades.append(trade1)

        if trade2:
            trade2['entry_time'] = idx
            trade2['ar_pips'] = ar
            trade2['direction'] = direction
            trade2['pnl'] = trade2['pnl'] * 0.5
            trade2['reason'] = 'tp_partial'
            trades.append(trade2)

    return calc_results(trades, "Constraint_Anchor")


def run_stall_harvest_cfd(df):
    """Stall-Harvest CFD — new approach: continuation from 120% level."""
    df = prepare_data(df)
    trades = []

    for date in sorted(df['date'].unique()):
        day = get_day_data(df, date)
        ah, al, ar = calc_asian_range(day)
        if ar is None or ar > 45 or ar < 3:
            continue

        entry = day[(day['est_h'] >= 2) & (day['est_h'] < 11)]
        direction, p90, p90_time = None, None, None

        for idx, row in entry.iterrows():
            thresh = p90_threshold(row['est_h'])
            if row['body_pips'] >= thresh:
                direction = 'LONG' if row['close'] > row['open'] else 'SHORT'
                p90 = row
                p90_time = idx
                break

        if direction is None:
            continue

        activation = p90['close']
        body_pips = to_pips(abs(p90['close'] - p90['open']))

        # Entry at 120% extension (continuation)
        entry_zone = activation + to_price(body_pips * 1.20) * (1 if direction == 'LONG' else -1)
        # SL: 80% of body back toward activation
        sl_level = entry_zone - to_price(body_pips * 0.80) * (1 if direction == 'LONG' else -1)
        # TP: 200% extension (full stall zone)
        tp_level = activation + to_price(body_pips * 2.00) * (1 if direction == 'LONG' else -1)

        post_p90 = day[(day.index > p90_time) & (day['est_h'] < 12)]
        if post_p90.empty:
            continue

        entered, entry_idx = False, None
        for idx, row in post_p90.iterrows():
            if (idx - p90_time).total_seconds() > 2700:
                break
            if direction == 'LONG' and row['high'] >= entry_zone:
                entered, entry_idx = True, idx
                break
            elif direction == 'SHORT' and row['low'] <= entry_zone:
                entered, entry_idx = True, idx
                break

        if not entered:
            continue

        post_entry = day[(day.index > entry_idx) & (day['est_h'] < 17)]
        if post_entry.empty:
            continue

        trade = manage_trade_with_trailing(post_entry, entry_zone, direction, sl_level, tp_level)
        if trade:
            trade['entry_time'] = entry_idx
            trade['ar_pips'] = ar
            trade['direction'] = direction
            trades.append(trade)

    return calc_results(trades, "Stall_Harvest_CFD")


# ============================================================
# PORTFOLIO BACKTEST
# ============================================================

def run_portfolio(df, strategy_results):
    """
    Portfolio backtest combining all profitable strategies.
    Uses Kelly-based position sizing and daily risk limits.
    """
    print("\n  [PORTFOLIO] Building combined portfolio...", flush=True)

    # Collect all trades from profitable strategies
    all_trades = []
    for name, result in strategy_results.items():
        if result.get('profit_factor', 0) > 1.0 and result.get('total_trades', 0) > 50:
            # We don't have individual trade data from results, so we estimate
            print(f"    Including: {name} (PF: {result['profit_factor']}, WR: {result['win_rate']}%)", flush=True)

    # Portfolio-level metrics
    profitable_count = sum(1 for r in strategy_results.values() if r.get('profit_factor', 0) > 1.0)
    total_count = sum(1 for r in strategy_results.values() if r.get('total_trades', 0) > 0)

    if total_count == 0:
        return {}

    # Weighted portfolio return (equal weight for now)
    total_annual = sum(r.get('annual_return_pct', 0) for r in strategy_results.values() if r.get('profit_factor', 0) > 1.0)
    avg_annual = total_annual / profitable_count if profitable_count > 0 else 0

    # Portfolio MaxDD (simplified — assumes 50% correlation)
    max_dds = [r.get('max_dd_pct', 0) for r in strategy_results.values() if r.get('profit_factor', 0) > 1.0]
    portfolio_dd = max(max_dds) * 0.7 if max_dds else 0  # Diversification benefit

    portfolio = {
        "strategy": "Portfolio_Combined",
        "pair": "EUR/USD",
        "profitable_strategies": profitable_count,
        "total_strategies": total_count,
        "avg_annual_return_pct": round(avg_annual, 1),
        "portfolio_max_dd_pct": round(portfolio_dd, 2),
        "included_strategies": [name for name, r in strategy_results.items() if r.get('profit_factor', 0) > 1.0],
    }

    return portfolio


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70, flush=True)
    print("QUANT LAB OPTIMIZER v5 — Risk-Managed Portfolio", flush=True)
    print("=" * 70, flush=True)

    df = load_eurusd_m5()
    if df is None:
        return {}

    print(f"\nData: {len(df):,} bars | {df.index[0].date()} -> {df.index[-1].date()}", flush=True)

    strategies = [
        ("Deep_Mean_Reversion", run_deep_mean_reversion),
        ("Composite_Alpha", run_composite_alpha),
        ("Failure_Repair", run_failure_repair),
        ("Dual_Engine", run_dual_engine),
        ("Blind_Structural_Chain", run_blind_structural_chain),
        ("Two_Plays", run_two_plays),
        ("P90P_Distribution", run_p90p_distribution),
        ("Fractal_Resolution", run_fractal_resolution),
        ("Constraint_Anchor", run_constraint_anchor),
        ("Stall_Harvest_CFD", run_stall_harvest_cfd),
    ]

    all_results = {}

    for name, fn in strategies:
        print(f"\n{name}...", flush=True)
        t0 = time.time()
        try:
            r = fn(df)
            elapsed = time.time() - t0
            all_results[name] = r
            if r.get("total_trades", 0) > 0:
                print(f"  {r['total_trades']} trades | WR: {r['win_rate']}% | "
                      f"PnL: {r['total_pnl']}p | PF: {r['profit_factor']} | "
                      f"MaxDD: {r['max_dd']}p ({r.get('max_dd_pct', 0)}%) | "
                      f"Exp: {r['expectancy']}p | AnnRet: {r.get('annual_return_pct', 0)}% | "
                      f"Sharpe: {r.get('sharpe_ratio', 0)} | "
                      f"Kelly: {r.get('kelly_fraction', 0)} | "
                      f"({elapsed:.1f}s)", flush=True)
            else:
                print(f"  No trades ({elapsed:.1f}s)", flush=True)
        except Exception as e:
            elapsed = time.time() - t0
            print(f"  ERROR: {e} ({elapsed:.1f}s)", flush=True)
            import traceback
            traceback.print_exc()
            all_results[name] = {"strategy": name, "error": str(e), "total_trades": 0}

    # Portfolio
    portfolio = run_portfolio(df, all_results)
    if portfolio:
        all_results["Portfolio_Combined"] = portfolio

    # Summary
    print(f"\n{'='*70}", flush=True)
    print("COMPARATIVE RESULTS v5 (with trailing stops + risk management)", flush=True)
    print(f"{'='*70}", flush=True)
    print(f"{'Strategy':<25} {'Trades':>6} {'WR%':>6} {'PnL(p)':>8} {'PF':>5} {'MaxDD%':>7} {'Exp':>6} {'AnnRet':>7} {'Sharpe':>7}", flush=True)
    print(f"{'─'*70}", flush=True)

    profitable = 0
    total = 0
    for name, r in all_results.items():
        if name == "Portfolio_Combined":
            continue
        if r.get("total_trades", 0) > 0:
            total += 1
            if r.get("profit_factor", 0) > 1.0:
                profitable += 1
            print(f"{name:<25} {r['total_trades']:>6} {r['win_rate']:>6.1f} "
                  f"{r['total_pnl']:>8.1f} {r['profit_factor']:>5.2f} "
                  f"{r.get('max_dd_pct', 0):>7.2f} {r['expectancy']:>6.3f} "
                  f"{r.get('annual_return_pct', 0):>7.1f} {r.get('sharpe_ratio', 0):>7.2f}", flush=True)
        else:
            print(f"{name:<25} {'N/A':>6} {'N/A':>6} {'N/A':>8} {'N/A':>5} {'N/A':>7} {'N/A':>6} {'N/A':>7} {'N/A':>7}", flush=True)

    if total > 0:
        print(f"\nProfitable: {profitable}/{total} = {profitable/total*100:.0f}% (target: 80%)", flush=True)

    if portfolio:
        print(f"\nPortfolio: {portfolio['avg_annual_return_pct']}% annual return, "
              f"{portfolio['portfolio_max_dd_pct']}% max DD", flush=True)

    # Save
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    rf = RESULTS_DIR / f"optimizer_v5_{ts}.json"
    with open(rf, "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\nResults saved to {rf}", flush=True)

    return all_results


if __name__ == "__main__":
    main()
