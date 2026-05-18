"""
Pairs Trading EUR/USD-GBP/USD v2
==================================
Proper cost model:
- Real spread from CSV SPREAD column (points)
- Commission: $7/lot/leg, 2 legs, entry+exit
- Position sizing: 5% risk per trade ($500 on $10K)

P&L model:
- Trade the ratio spread: ratio = EUR/USD / GBP/USD
- Enter when |z-score| > 2.0 (mean-reversion)
- Exit when |z| < 0.5 (TP) or |z| > 3.5 (SL)
- P&L = lot_size * 100000 * direction * (exit_ratio - entry_ratio) / avg_ratio
"""
import json
from pathlib import Path
from typing import Dict

import pandas as pd
import numpy as np

ACCOUNT_EQUITY = 10000.0
RISK_PER_POSITION = 0.05
RISK_AMOUNT = ACCOUNT_EQUITY * RISK_PER_POSITION
COMMISSION_PER_LOT = 7.0
PIP_SIZE = 0.0001

EURUSD_PATH = r"C:\Users\wifik\Downloads\EURUSD!_M5_202301020000_202605061250.csv"
GBPUSD_PATH = r"C:\Users\wifik\Downloads\GBPUSD!_M5_202301020000_202605061250.csv"
RESULTS_DIR = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\results")
RESULTS_DIR.mkdir(exist_ok=True)


def load_csv(path: str) -> pd.DataFrame:
    records = []
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    for line in lines[1:]:
        parts = line.strip().split('\t')
        if len(parts) < 9:
            continue
        try:
            ts = pd.Timestamp(f"{parts[0]} {parts[1]}", tz='UTC')
            records.append({
                'open': float(parts[2]), 'high': float(parts[3]),
                'low': float(parts[4]), 'close': float(parts[5]),
                'spread': int(parts[8]), 'ts': ts
            })
        except (ValueError, IndexError):
            continue
    df = pd.DataFrame(records)
    df.set_index('ts', inplace=True)
    df.sort_index(inplace=True)
    df = df[~df.index.duplicated(keep='first')]
    return df


def run_backtest() -> Dict:
    print("=" * 70)
    print("Pairs Trading EUR/USD-GBP/USD v2")
    print("=" * 70)

    print("\n[1] Loading data...")
    eurusd = load_csv(EURUSD_PATH)
    gbpusd = load_csv(GBPUSD_PATH)
    print(f"  EUR/USD: {len(eurusd):,} bars")
    print(f"  GBP/USD: {len(gbpusd):,} bars")

    # Align
    common = eurusd.index.intersection(gbpusd.index)
    df = pd.DataFrame(index=common)
    df['eur'] = eurusd.loc[common, 'close'].values
    df['gbp'] = gbpusd.loc[common, 'close'].values
    df['eur_spr'] = eurusd.loc[common, 'spread'].values
    df['gbp_spr'] = gbpusd.loc[common, 'spread'].values

    # Ratio and z-score
    df['ratio'] = df['eur'] / df['gbp']
    df['ratio_mean'] = df['ratio'].rolling(50).mean()
    df['ratio_std'] = df['ratio'].rolling(50).std()
    df['z'] = (df['ratio'] - df['ratio_mean']) / (df['ratio_std'] + 1e-10)
    df['corr'] = df['eur'].rolling(50).corr(df['gbp'])

    avg_ratio_std = df['ratio_std'].mean()
    avg_ratio = df['ratio'].mean()

    print(f"\n[2] Signal stats:")
    print(f"  Bars: {len(df):,} | Corr: {df['corr'].mean():.3f}")
    print(f"  Ratio: {avg_ratio:.6f} | Ratio_std: {avg_ratio_std:.6f}")
    print(f"  EUR spread: {df['eur_spr'].replace(0, np.nan).mean():.1f} pts")
    print(f"  GBP spread: {df['gbp_spr'].replace(0, np.nan).mean():.1f} pts")

    # Parameters
    Z_ENTRY = 2.0
    Z_EXIT = 0.5
    Z_STOP = 3.5
    MIN_CORR = 0.70
    TIME_STOP = 50

    # Position sizing:
    # Risk = stop_z * dollar_per_z * lot_size
    # dollar_per_z = ratio_std * 100000 / ratio (for 1 standard lot)
    # lot_size = RISK / (stop_z * ratio_std * 100000 / ratio)
    stop_z = Z_STOP - Z_ENTRY
    lot_size = RISK_AMOUNT * avg_ratio / (stop_z * avg_ratio_std * 100000.0)
    lot_size = max(0.01, min(lot_size, 5.0))

    dollar_per_z = avg_ratio_std * 100000.0 * lot_size / avg_ratio
    comm_per_trade = COMMISSION_PER_LOT * lot_size * 4  # 2 legs * entry+exit

    print(f"\n[3] Position sizing:")
    print(f"  Stop: {stop_z} z-units | Dollar/z: ${dollar_per_z:.2f}")
    print(f"  Lot size: {lot_size:.4f} | Comm/trade: ${comm_per_trade:.2f}")

    # Backtest
    equity = ACCOUNT_EQUITY
    trades = []
    in_trade = False
    bars_held = 0

    for idx, bar in df.iterrows():
        if in_trade:
            t = trades[-1]
            bars_held += 1
            direction = t['dir']
            entry_z = t['entry_z']
            cur_z = bar['z']

            # P&L: ratio change * scaling
            if direction == -1:  # SHORT spread (z was > 0)
                z_imp = entry_z - cur_z
            else:  # LONG spread (z was < 0)
                z_imp = cur_z - entry_z

            ratio_std = bar['ratio_std'] if not pd.isna(bar['ratio_std']) else avg_ratio_std
            ratio = bar['ratio']
            dpz = ratio_std * 100000.0 * lot_size / ratio
            pnl = z_imp * dpz
            if not np.isfinite(pnl):
                pnl = 0.0

            # Exit
            reason = None
            if abs(cur_z) < Z_EXIT:
                reason = 'mean_reversion'
            elif abs(cur_z) > Z_STOP:
                reason = 'stop_loss'
            elif bars_held >= TIME_STOP:
                reason = 'time_stop'
            elif bar['corr'] < 0.60:
                reason = 'correlation_breakdown'

            if reason:
                # Costs
                entry_spr = t['entry_spr_points'] * lot_size
                exit_spr = (bar['eur_spr'] + bar['gbp_spr']) * lot_size
                total_spr = entry_spr + exit_spr
                total_comm = comm_per_trade
                net = pnl - total_spr - total_comm

                t.update({
                    'exit_time': idx, 'exit_z': cur_z,
                    'gross_pnl': round(pnl, 2),
                    'spread_cost': round(total_spr, 2),
                    'commission': round(total_comm, 2),
                    'net_pnl': round(net, 2),
                    'exit_reason': reason, 'bars_held': bars_held
                })
                equity += net
                t['equity_after'] = round(equity, 2)
                in_trade = False
                bars_held = 0
        else:
            if pd.isna(bar['z']) or pd.isna(bar['corr']):
                continue
            if abs(bar['z']) < Z_ENTRY or bar['corr'] < MIN_CORR:
                continue

            z = bar['z']
            direction = -1 if z > 0 else 1
            spr_pts = bar['eur_spr'] + bar['gbp_spr']

            trades.append({
                'entry_time': idx, 'entry_z': z, 'dir': direction,
                'dir_label': 'SHORT_SPREAD' if direction == -1 else 'LONG_SPREAD',
                'corr': bar['corr'], 'lot_size': lot_size,
                'entry_spr_points': spr_pts
            })
            in_trade = True
            bars_held = 0

    # Close final
    if in_trade and trades:
        last = trades[-1]
        if 'exit_time' not in last:
            last.update({
                'exit_time': df.index[-1], 'exit_z': df.iloc[-1]['z'],
                'gross_pnl': 0.0,
                'spread_cost': last['entry_spr_points'] * lot_size,
                'commission': comm_per_trade,
                'net_pnl': -(last['entry_spr_points'] * lot_size) - comm_per_trade,
                'exit_reason': 'end_of_data'
            })
            equity += last['net_pnl']
            last['equity_after'] = round(equity, 2)

    # Results
    done = [t for t in trades if 'net_pnl' in t]
    if not done:
        return {"trades": 0}

    pnls = [t['net_pnl'] for t in done]
    gross = [t['gross_pnl'] for t in done]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p <= 0]
    total = sum(pnls)
    total_gross = sum(gross)
    total_comm = sum(t['commission'] for t in done)
    total_spr = sum(t['spread_cost'] for t in done)
    wr = len(wins) / len(pnls) * 100

    cum = np.cumsum(pnls)
    peak = np.maximum.accumulate(cum)
    max_dd = float((peak - cum).max()) if len(cum) > 0 else 0

    avg_w = sum(wins) / len(wins) if wins else 0
    avg_l = sum(losses) / len(losses) if losses else 0
    gp = sum(wins) if wins else 0
    gl = abs(sum(losses)) if losses else 1
    pf = gp / gl if gl > 0 else 0
    exp = total / len(pnls) if pnls else 0

    by_exit = {}
    for t in done:
        r = t.get('exit_reason', 'unknown')
        by_exit[r] = by_exit.get(r, 0) + 1

    results = {
        'strategy': 'Pairs Trading EUR/USD-GBP/USD v2',
        'pair': 'EUR/USD-GBP/USD', 'timeframe': 'M5',
        'data_bars': len(df),
        'date_range': f"{df.index[0]} to {df.index[-1]}",
        'cost_model': {
            'commission_per_lot_per_leg': COMMISSION_PER_LOT,
            'spread_source': 'CSV SPREAD column (points)',
            'risk_per_position': RISK_PER_POSITION,
            'account_equity': ACCOUNT_EQUITY,
            'lot_size': round(lot_size, 4),
        },
        'total_trades': len(done), 'wins': len(wins), 'losses': len(losses),
        'win_rate': round(wr, 1),
        'gross_pnl': round(total_gross, 2),
        'total_commission': round(total_comm, 2),
        'total_spread_cost': round(total_spr, 2),
        'net_pnl': round(total, 2),
        'avg_win': round(avg_w, 2), 'avg_loss': round(avg_l, 2),
        'max_drawdown': round(max_dd, 2),
        'profit_factor': round(pf, 2),
        'expectancy': round(exp, 2),
        'avg_lot_size': round(lot_size, 4),
        'final_equity': round(equity, 2),
        'by_exit': by_exit,
        'avg_correlation': round(float(df['corr'].mean()), 3),
    }

    print(f"\n{'=' * 70}")
    print(f"RESULTS")
    print(f"{'=' * 70}")
    print(f"  Trades: {len(done)} | WR: {wr:.1f}%")
    print(f"  Gross: ${total_gross:,.2f}")
    print(f"  Comm:  -${total_comm:,.2f}")
    print(f"  Sprd:  -${total_spr:,.2f}")
    print(f"  Net:   ${total:,.2f}")
    print(f"  AvgW: ${avg_w:,.2f} | AvgL: ${avg_l:,.2f}")
    print(f"  MaxDD: ${max_dd:,.2f} | PF: {pf:.2f} | Exp: ${exp:,.2f}")
    print(f"  Equity: ${equity:,.2f} | Corr: {df['corr'].mean():.3f}")
    print(f"  Exits: {by_exit}")

    return results


if __name__ == "__main__":
    results = run_backtest()
    out = RESULTS_DIR / "pairs_trading_v2_results.json"
    with open(out, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n  Saved to {out}")
