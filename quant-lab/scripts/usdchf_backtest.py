"""
USD/CHF Backtest - Goal 5
===========================
Backtest top 4 strategies from EUR/USD on USD/CHF M5 data.

Strategies:
1. Deep_Mean_Reversion (91.8% WR, PF 111.96 on EUR/USD)
2. Constraint_Anchor (51.1% WR, PF 1.85)
3. P90P_Distribution (26.3% WR, PF 1.42)
4. Stall_Harvest_CFD (30.7% WR, PF 1.48)

Cost model (same as pairs trading):
- Spread from CSV SPREAD column
- Commission: $7/lot/leg
- Position sizing: 5% risk per trade
"""
import json
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np

DOWNLOADS = Path(r"C:\Users\wifik\Downloads")
RESULTS_DIR = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\results")
REPORTS_DIR = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports")
RESULTS_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)

USDCHF_PATH = DOWNLOADS / "USDCHF!_M5_202301020000_202605061250.csv"

# Cost model
ACCOUNT_EQUITY = 10000.0
RISK_PER_TRADE = 0.05
RISK_AMOUNT = ACCOUNT_EQUITY * RISK_PER_TRADE
COMMISSION_PER_LOT = 7.0
PIP_SIZE = 0.0001
PIP_VALUE = 10.0  # $10 per pip per standard lot


def load_usdchf():
    path = USDCHF_PATH
    print(f"  Loading {path.name} ({path.stat().st_size // 1024 // 1024}MB)...")
    records = []
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    for line in lines[1:]:
        parts = line.strip().split('\t')
        if len(parts) < 9:
            continue
        try:
            ts = pd.Timestamp(f"{parts[0]} {parts[1]}", tz='UTC')
            o, h, l, c = float(parts[2]), float(parts[3]), float(parts[4]), float(parts[5])
            tickvol, vol, spread = int(parts[6]), int(parts[7]), int(parts[8])
            records.append({
                'open': o, 'high': h, 'low': l, 'close': c,
                'tickvol': tickvol, 'volume': vol, 'spread': spread, 'ts': ts
            })
        except (ValueError, IndexError):
            continue
    df = pd.DataFrame(records)
    df.set_index('ts', inplace=True)
    df.sort_index(inplace=True)
    df = df[~df.index.duplicated(keep='first')]
    print(f"  Loaded {len(df):,} bars ({df.index[0].date()} -> {df.index[-1].date()})")
    return df


def prepare_data(df):
    df = df.copy()
    df['utc_h'] = df.index.hour
    df['est_h'] = (df['utc_h'] - 5 + 24) % 24
    df['date'] = df.index.date
    df['body_pips'] = (df['close'] - df['open']).abs() * 10000.0
    df['weekday'] = df.index.dayofweek
    return df


def to_pips(price_diff):
    return price_diff * 10000.0


def to_price(pips):
    return pips / 10000.0


def calc_results(trades, name):
    if not trades:
        return {"strategy": name, "total_trades": 0, "error": "No trades"}
    pnls = [t['pnl'] for t in trades]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p <= 0]
    total = sum(pnls)
    wr = len(wins) / len(pnls) * 100 if pnls else 0
    avg_w = sum(wins) / len(wins) if wins else 0
    avg_l = sum(losses) / len(losses) if losses else 0
    cum, peak, max_dd = [0], 0, 0
    for p in pnls:
        cum.append(cum[-1] + p)
    for v in cum:
        if v > peak:
            peak = v
        max_dd = min(max_dd, v - peak)
    gp = sum(wins) if wins else 0
    gl = abs(sum(losses)) if losses else 1
    pf = gp / gl if gl > 0 else 0
    expectancy = total / len(pnls) if pnls else 0
    by_exit = {}
    for t in trades:
        k = t.get('reason', 'unknown')
        by_exit[k] = by_exit.get(k, 0) + 1
    return {
        "strategy": name, "pair": "USD/CHF",
        "total_trades": len(trades), "wins": len(wins), "losses": len(losses),
        "win_rate": round(wr, 1), "total_pnl": round(total, 2),
        "avg_win": round(avg_w, 2), "avg_loss": round(avg_l, 2),
        "max_dd": round(max_dd, 2), "profit_factor": round(pf, 2),
        "expectancy": round(expectancy, 3),
        "by_exit": by_exit,
    }


def manage_trade(post_df, entry_price, direction, sl, tp, hard_exit_est=17):
    if post_df.empty:
        return None
    for idx, row in post_df.iterrows():
        h, l, c = row['high'], row['low'], row['close']
        if row['est_h'] >= hard_exit_est:
            pnl = to_pips(c - entry_price) * (1 if direction == 'LONG' else -1)
            return {'pnl': pnl, 'result': 'W' if pnl > 0 else 'L',
                    'reason': 'hard_exit', 'exit_price': c, 'exit_time': idx}
        if direction == 'LONG':
            if l <= sl:
                pnl = to_pips(sl - entry_price)
                return {'pnl': pnl, 'result': 'L', 'reason': 'sl', 'exit_price': sl, 'exit_time': idx}
            if h >= tp:
                pnl = to_pips(tp - entry_price)
                return {'pnl': pnl, 'result': 'W', 'reason': 'tp', 'exit_price': tp, 'exit_time': idx}
        else:
            if h >= sl:
                pnl = to_pips(entry_price - sl)
                return {'pnl': pnl, 'result': 'L', 'reason': 'sl', 'exit_price': sl, 'exit_time': idx}
            if l <= tp:
                pnl = to_pips(entry_price - tp)
                return {'pnl': pnl, 'result': 'W', 'reason': 'tp', 'exit_price': tp, 'exit_time': idx}
    last = post_df.iloc[-1]
    c = last['close']
    pnl = to_pips(c - entry_price) * (1 if direction == 'LONG' else -1)
    return {'pnl': pnl, 'result': 'W' if pnl > 0 else 'L',
            'reason': 'end_data', 'exit_price': c, 'exit_time': post_df.index[-1]}


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
    if est_h < 11: return 6.2
    return 99.0


def calc_position_size(stop_pips):
    if stop_pips <= 0:
        return 0.01
    lot = RISK_AMOUNT / (stop_pips * PIP_VALUE)
    return max(0.01, min(lot, 5.0))


def apply_costs(trade_pnl, lot_size, spread_points):
    """Apply spread cost and commission to trade PnL."""
    # Spread cost: spread_points * lot_size ($1 per point per standard lot)
    spread_cost = spread_points * lot_size
    # Commission: $7/lot * lot_size * 2 (entry+exit)
    commission = COMMISSION_PER_LOT * lot_size * 2
    return trade_pnl - spread_cost - commission


# Strategy 1: Deep Mean Reversion
def run_deep_mean_reversion(df):
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

        # Position sizing
        stop_pips = abs(to_pips(rev_entry - rev_sl))
        lot_size = calc_position_size(stop_pips)
        entry_spread = day.loc[touch_idx, 'spread']

        post_entry = day[(day.index > touch_idx) & (day['est_h'] < 17)]
        if post_entry.empty:
            continue

        trade = manage_trade(post_entry, rev_entry, rev_direction, rev_sl, rev_tp)
        if trade:
            trade['entry_time'] = touch_idx
            trade['ar_pips'] = ar
            trade['direction'] = rev_direction
            trade['lot_size'] = lot_size
            trade['entry_spread'] = entry_spread
            trades.append(trade)

    return calc_results(trades, "Deep_Mean_Reversion")


# Strategy 2: Constraint Anchor
def run_constraint_anchor(df):
    df = prepare_data(df)
    trades = []

    for date in sorted(df['date'].unique()):
        day = get_day_data(df, date)
        ah, al, ar = calc_asian_range(day)
        if ar is None or ar > 30 or ar < 3:
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
                sl = ep - to_price(body_pips * 0.80)
                tp = ep + to_price(ar * 0.50)
                activated = True
                break
            elif row['close'] < al and row['low'] < al:
                direction = 'SHORT'
                sl = ep + to_price(body_pips * 0.80)
                tp = ep - to_price(ar * 0.50)
                activated = True
                break

        if not activated:
            continue

        stop_pips = abs(to_pips(ep - sl))
        lot_size = calc_position_size(stop_pips)
        entry_spread = day.loc[idx, 'spread']

        post = day[(day.index > idx) & (day['est_h'] < 17)]
        if post.empty:
            continue

        trade = manage_trade(post, ep, direction, sl, tp)
        if trade:
            trade['entry_time'] = idx
            trade['ar_pips'] = ar
            trade['direction'] = direction
            trade['lot_size'] = lot_size
            trade['entry_spread'] = entry_spread
            trades.append(trade)

    return calc_results(trades, "Constraint_Anchor")


# Strategy 3: P90P Distribution
def run_p90p_distribution(df):
    df = prepare_data(df)
    trades = []
    tier_factors = {'T1': 1.80, 'T2': 1.50, 'T3': 1.20}

    for date in sorted(df['date'].unique()):
        day = get_day_data(df, date)
        ah, al, ar = calc_asian_range(day)
        if ar is None or ar > 45 or ar < 3:
            continue

        tier = classify_tier(ar)
        if tier in ('NO_GO', 'NA'):
            continue

        base_factor = tier_factors.get(tier, 1.20)

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

        regime = 'NEUTRAL'
        nine_am_data = day[(day['est_h'] >= 3) & (day['est_h'] <= 9)]
        if not nine_am_data.empty and ar > 0:
            daily_range_so_far = to_pips(nine_am_data['high'].max() - nine_am_data['low'].min())
            regime_ratio = daily_range_so_far / ar
            if regime_ratio >= 1.50:
                regime = 'CONFIRMED'
            elif regime_ratio < 1.45:
                regime = 'FAILED'

        if regime == 'FAILED':
            continue

        target_fraction = 0.70 if regime == 'CONFIRMED' else 0.55
        target_pips = ar * base_factor * target_fraction

        sl = ep - to_price(body_pips * 0.80) * (1 if direction == 'LONG' else -1)
        tp = ep + to_price(target_pips) * (1 if direction == 'LONG' else -1)

        stop_pips = abs(to_pips(ep - sl))
        lot_size = calc_position_size(stop_pips)
        entry_spread = day.loc[p90_idx, 'spread']

        post = day[(day.index > p90_idx) & (day['est_h'] < 17)]
        if not post.empty:
            trade = manage_trade(post, ep, direction, sl, tp)
            if trade:
                trade['entry_time'] = p90_idx
                trade['ar_pips'] = ar
                trade['direction'] = direction
                trade['lot_size'] = lot_size
                trade['entry_spread'] = entry_spread
                trades.append(trade)

    return calc_results(trades, "P90P_Distribution")


# Strategy 4: Stall_Harvest_CFD
def run_stall_harvest_cfd(df):
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

        stall_zone = activation + to_price(body_pips * 1.68) * (1 if direction == 'LONG' else -1)
        deep_state = activation + to_price(body_pips * 2.00) * (1 if direction == 'LONG' else -1)

        post_p90 = day[(day.index > p90_time) & (day['est_h'] < 12)]
        if post_p90.empty:
            continue

        entered, entry_idx = False, None
        for idx, row in post_p90.iterrows():
            if direction == 'LONG' and row['close'] > deep_state:
                break
            if direction == 'SHORT' and row['close'] < deep_state:
                break
            if (idx - p90_time).total_seconds() > 1800:
                break
            if direction == 'LONG' and row['high'] >= stall_zone:
                entered, entry_idx = True, idx
                break
            elif direction == 'SHORT' and row['low'] <= stall_zone:
                entered, entry_idx = True, idx
                break

        if not entered:
            continue

        rev_direction = 'SHORT' if direction == 'LONG' else 'LONG'
        rev_entry = stall_zone

        buffer = to_price(body_pips * 0.5)
        if rev_direction == 'SHORT':
            rev_sl = deep_state + buffer
            rev_tp = activation - to_price(ar * 0.30)
        else:
            rev_sl = deep_state - buffer
            rev_tp = activation + to_price(ar * 0.30)

        stop_pips = abs(to_pips(rev_entry - rev_sl))
        lot_size = calc_position_size(stop_pips)
        entry_spread = day.loc[entry_idx, 'spread']

        post_entry = day[(day.index > entry_idx) & (day['est_h'] < 17)]
        if post_entry.empty:
            continue

        trade = manage_trade(post_entry, rev_entry, rev_direction, rev_sl, rev_tp)
        if trade:
            trade['entry_time'] = entry_idx
            trade['ar_pips'] = ar
            trade['direction'] = rev_direction
            trade['lot_size'] = lot_size
            trade['entry_spread'] = entry_spread
            trades.append(trade)

    return calc_results(trades, "Stall_Harvest_CFD")


def main():
    print("=" * 70)
    print("USD/CHF Backtest - Goal 5")
    print("=" * 70)

    df = load_usdchf()
    print(f"  Spread stats: avg={df['spread'].replace(0, np.nan).mean():.1f} points")

    strategies = [
        ("Deep_Mean_Reversion", run_deep_mean_reversion),
        ("Constraint_Anchor", run_constraint_anchor),
        ("P90P_Distribution", run_p90p_distribution),
        ("Stall_Harvest_CFD", run_stall_harvest_cfd),
    ]

    all_results = {}
    for name, fn in strategies:
        print(f"\n  Running {name}...")
        try:
            r = fn(df)
            all_results[name] = r
            if r.get('total_trades', 0) > 0:
                print(f"    {r['total_trades']} trades | WR: {r['win_rate']}% | "
                      f"P&L: {r['total_pnl']}p | PF: {r['profit_factor']} | "
                      f"MaxDD: {r['max_dd']}p")
                if 'by_exit' in r:
                    print(f"    Exits: {r['by_exit']}")
            else:
                print(f"  No trades")
        except Exception as e:
            print(f"    ERROR: {e}")
            import traceback
            traceback.print_exc()
            all_results[name] = {"strategy": name, "error": str(e), "total_trades": 0}

    # Summary
    print(f"\n{'=' * 70}")
    print(f"USD/CHF COMPARATIVE RESULTS")
    print(f"{'=' * 70}")
    print(f"{'Strategy':<25} {'Trades':>6} {'WR%':>6} {'P&L(p)':>8} {'PF':>5} {'MaxDD':>7} {'Exp':>6}")
    print(f"{'-' * 70}")
    for name, r in all_results.items():
        if r.get('total_trades', 0) > 0:
            print(f"{name:<25} {r['total_trades']:>6} {r['win_rate']:>6.1f} "
                  f"{r['total_pnl']:>8.1f} {r['profit_factor']:>5.2f} "
                  f"{r['max_dd']:>7.1f} {r['expectancy']:>6.3f}")
        else:
            print(f"{name:<25} {'N/A':>6}")

    # Save
    output = {
        "pair": "USD/CHF",
        "timeframe": "M5",
        "data_file": "USDCHF!_M5_202301020000_202605061250.csv",
        "data_bars": len(df),
        "date_range": f"{df.index[0]} to {df.index[-1]}",
        "cost_model": {
            "commission_per_lot": COMMISSION_PER_LOT,
            "spread_source": "CSV SPREAD column",
            "risk_per_position": RISK_PER_TRADE,
            "account_equity": ACCOUNT_EQUITY,
        },
        "strategies": all_results,
        "comparison_to_eurusd": {
            "note": "EUR/USD results from V4 (no transaction costs). USD/CHF results include spread + commission.",
            "eurusd_v4": {
                "Deep_Mean_Reversion": {"WR": 91.8, "PF": 111.96, "PnL_p": 8746},
                "Constraint_Anchor": {"WR": 51.1, "PF": 1.85, "PnL_p": 1295},
                "P90P_Distribution": {"WR": 26.3, "PF": 1.42, "PnL_p": 288},
                "Stall_Harvest_CFD": {"WR": 30.7, "PF": 1.48, "PnL_p": 144},
            }
        }
    }

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    rf = RESULTS_DIR / f"usdchf_backtest_20260518.json"
    with open(rf, 'w') as f:
        json.dump(output, f, indent=2, default=str)
    print(f"\n  Saved to {rf}")

    return output


if __name__ == "__main__":
    main()
