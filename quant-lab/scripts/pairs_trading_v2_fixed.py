"""
Pairs Trading EUR/USD-GBP/USD v2 - Fixed Cost Model
=====================================================
Key fix: Position sizing calibrated to spread volatility, not individual pair volatility.

For pairs trading, the "risk unit" is the spread itself. We need to:
1. Measure spread volatility in pips
2. Size positions based on spread pip movement risk
3. Apply costs per leg properly

Position sizing approach:
- Risk $500 per trade
- Stop = z-score stop (3.5) - z-score entry (~2.0) = 1.5 z-units
- 1 z-unit in pips = ratio_std / PIP_SIZE * PIP_VALUE
- But simpler: calibrate from historical spread pip movement

Alternative simpler approach:
- Fixed fractional: risk 5% of equity per trade
- Measure historical spread volatility (std of ratio changes in pips)
- Position size = risk_amount / (stop_pips * pip_value)
"""
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict

import pandas as pd
import numpy as np

# Config
ACCOUNT_EQUITY = 10000.0
RISK_PER_POSITION = 0.05
RISK_AMOUNT = ACCOUNT_EQUITY * RISK_PER_POSITION
COMMISSION_PER_LOT = 7.0
PIP_SIZE = 0.0001
PIP_VALUE_PER_STANDARD_LOT = 10.0

EURUSD_PATH = r"C:\Users\wifik\Downloads\EURUSD!_M5_202301020000_202605061250.csv"
GBPUSD_PATH = r"C:\Users\wifik\Downloads\GBPUSD!_M5_202301020000_202605061250.csv"

RESULTS_DIR = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\results")
RESULTS_DIR.mkdir(exist_ok=True)


def load_m5_data(path: str) -> pd.DataFrame:
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
    return df


def run_backtest() -> Dict:
    print("=" * 70)
    print("Pairs Trading EUR/USD-GBP/USD v2 - Fixed Cost Model")
    print("=" * 70)

    # Load data
    print("\n[1/4] Loading data...")
    eurusd = load_m5_data(EURUSD_PATH)
    gbpusd = load_m5_data(GBPUSD_PATH)
    print(f"  EUR/USD: {len(eurusd):,} bars")
    print(f"  GBP/USD: {len(gbpusd):,} bars")

    # Align and compute spread
    common_idx = eurusd.index.intersection(gbpusd.index)
    df = pd.DataFrame(index=common_idx)
    df['eur_close'] = eurusd.loc[common_idx, 'close'].values
    df['gbp_close'] = gbpusd.loc[common_idx, 'close'].values
    df['eur_spread'] = eurusd.loc[common_idx, 'spread'].values
    df['gbp_spread'] = gbpusd.loc[common_idx, 'spread'].values

    # Ratio and z-score
    df['ratio'] = df['eur_close'] / df['gbp_close']
    df['ratio_mean'] = df['ratio'].rolling(50).mean()
    df['ratio_std'] = df['ratio'].rolling(50).std()
    df['z_ratio'] = (df['ratio'] - df['ratio_mean']) / (df['ratio_std'] + 1e-10)
    df['correlation'] = df['eur_close'].rolling(50).corr(df['gbp_close'])

    # Compute spread volatility in pips
    # The spread (ratio) change in pips = (ratio_change / PIP_SIZE)
    df['ratio_pips'] = (df['ratio'] - df['ratio_mean']) / PIP_SIZE
    spread_vol = df['ratio_pips'].std()
    print(f"\n[2/4] Signal statistics:")
    print(f"  Aligned bars: {len(df):,}")
    print(f"  Avg correlation: {df['correlation'].mean():.3f}")
    print(f"  Spread vol (pips std): {spread_vol:.2f}")
    print(f"  Z-score range: [{df['z_ratio'].min():.2f}, {df['z_ratio'].max():.2f}]")
    print(f"  Avg EUR/USD spread: {df['eur_spread'].replace(0, np.nan).mean():.1f} points")
    print(f"  Avg GBP/USD spread: {df['gbp_spread'].replace(0, np.nan).mean():.1f} points")

    # Backtest parameters
    zscore_entry = 2.0
    zscore_exit = 0.5
    zscore_stop = 3.5
    min_correlation = 0.70
    time_stop_bars = 50

    # Position sizing:
    # Stop distance in z-units = zscore_stop - zscore_entry = 3.5 - 2.0 = 1.5
    # Convert to pips: 1 z-unit = ratio_std in price = ratio_std / PIP_SIZE pips
    # Average ratio_std
    avg_ratio_std = df['ratio_std'].mean()
    stop_z_distance = zscore_stop - zscore_entry  # 1.5
    stop_pips = stop_z_distance * avg_ratio_std / PIP_SIZE
    # Position size = risk / (stop_pips * pip_value)
    lot_size = RISK_AMOUNT / (stop_pips * PIP_VALUE_PER_STANDARD_LOT)
    lot_size = max(0.01, min(lot_size, 5.0))  # Cap between 0.01 and 5.0 lots

    print(f"\n[3/4] Backtest parameters:")
    print(f"  Avg ratio_std: {avg_ratio_std:.6f}")
    print(f"  Stop distance: {stop_z_distance} z-units = {stop_pips:.1f} pips")
    print(f"  Position size: {lot_size:.4f} lots (fixed for all trades)")
    print(f"  Risk per trade: ${RISK_AMOUNT:,.0f}")
    print(f"  Commission per trade: ${COMMISSION_PER_LOT * lot_size * 2:.2f} (2 legs)")

    # Backtest loop
    equity = ACCOUNT_EQUITY
    trades = []
    position_open = False
    bars_in_trade = 0

    for idx, bar in df.iterrows():
        if position_open:
            trade = trades[-1]
            bars_in_trade += 1

            current_z = bar['z_ratio']
            entry_z = trade['entry_z']
            direction = trade['direction']

            # P&L: mean-reversion of z-score
            # For SHORT spread (direction=-1, entered when z>0): profit when z decreases
            # For LONG spread (direction=1, entered when z<0): profit when z increases
            if direction == -1:
                z_improvement = entry_z - current_z
            else:
                z_improvement = current_z - entry_z

            # Convert z-improvement to dollars
            # 1 z-unit = ratio_std in price change
            # Dollar value = z_improvement * ratio_std * lot_size * contract_size / ratio
            # Simplified: each z-unit of ratio change = ratio_std * lot_size * 100000 / ratio dollars
            ratio_std = bar['ratio_std'] if not pd.isna(bar['ratio_std']) else avg_ratio_std
            dollar_per_z = ratio_std * lot_size * 100000.0 / bar['ratio']
            pnl = z_improvement * dollar_per_z

            if not np.isfinite(pnl):
                pnl = 0.0

            trade['current_pnl'] = pnl

            # Exit checks
            exit_reason = None
            if abs(current_z) < zscore_exit:
                exit_reason = 'mean_reversion'
            elif abs(current_z) > zscore_stop:
                exit_reason = 'stop_loss'
            elif bars_in_trade >= time_stop_bars:
                exit_reason = 'time_stop'
            elif bar['correlation'] < 0.60:
                exit_reason = 'correlation_breakdown'

            if exit_reason:
                # Costs
                eur_spr = bar['eur_spread']
                gbp_spr = bar['gbp_spread']

                # Spread cost per leg = spread_points * $1 per point per standard lot * lot_size
                # 1 point = 0.00001, for standard lot (100,000 units):
                # spread_cost = spread_points * 0.00001 * 100000 * lot_size = spread_points * lot_size
                exit_spread = (eur_spr + gbp_spr) * lot_size  # $ per point * lot_size
                entry_spread = trade['entry_spread_cost']
                total_spread = entry_spread + exit_spread

                # Commission: $7/lot * lot_size * 2 legs * 2 (entry+exit)
                total_commission = COMMISSION_PER_LOT * lot_size * 2 * 2

                net_pnl = pnl - total_spread - total_commission

                trade['exit_time'] = idx
                trade['exit_z'] = current_z
                trade['gross_pnl'] = round(pnl, 2)
                trade['total_spread_cost'] = round(total_spread, 2)
                trade['total_commission'] = round(total_commission, 2)
                trade['net_pnl'] = round(net_pnl, 2)
                trade['exit_reason'] = exit_reason
                trade['bars_held'] = bars_in_trade

                equity += net_pnl
                trade['equity_after'] = round(equity, 2)
                position_open = False
                bars_in_trade = 0

        else:
            # Entry
            if pd.isna(bar['z_ratio']) or pd.isna(bar['correlation']):
                continue
            if abs(bar['z_ratio']) < zscore_entry:
                continue
            if bar['correlation'] < min_correlation:
                continue

            z = bar['z_ratio']
            direction = -1 if z > 0 else 1

            # Entry spread cost
            eur_spr = bar['eur_spread']
            gbp_spr = bar['gbp_spread']
            entry_spread = (eur_spr + gbp_spr) * lot_size

            trade = {
                'entry_time': idx,
                'entry_z': z,
                'direction': direction,
                'direction_label': 'SHORT_SPREAD' if direction == -1 else 'LONG_SPREAD',
                'correlation': bar['correlation'],
                'lot_size': lot_size,
                'entry_spread_cost': entry_spread,
            }
            trades.append(trade)
            position_open = True
            bars_in_trade = 0

    # Close final
    if position_open and trades:
        last = trades[-1]
        if 'exit_time' not in last:
            last['exit_time'] = df.index[-1]
            last['exit_z'] = df.iloc[-1]['z_ratio']
            last['gross_pnl'] = 0.0
            last['total_spread_cost'] = last['entry_spread_cost']
            last['total_commission'] = COMMISSION_PER_LOT * lot_size * 2 * 2
            last['net_pnl'] = -last['total_spread_cost'] - last['total_commission']
            last['exit_reason'] = 'end_of_data'
            equity += last['net_pnl']
            last['equity_after'] = round(equity, 2)

    # Results
    completed = [t for t in trades if 'net_pnl' in t]
    if not completed:
        print("  No trades generated")
        return {"trades": 0}

    pnls = [t['net_pnl'] for t in completed]
    gross_pnls = [t['gross_pnl'] for t in completed]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p <= 0]
    total_pnl = sum(pnls)
    total_gross = sum(gross_pnls)
    total_commission = sum(t['total_commission'] for t in completed)
    total_spread = sum(t['total_spread_cost'] for t in completed)
    win_rate = len(wins) / len(pnls) * 100

    cumulative = np.cumsum(pnls)
    peak = np.maximum.accumulate(cumulative)
    max_dd = (peak - cumulative).max() if len(cumulative) > 0 else 0

    avg_win = sum(wins) / len(wins) if wins else 0
    avg_loss = sum(losses) / len(losses) if losses else 0
    gross_profit = sum(wins) if wins else 0
    gross_loss = abs(sum(losses)) if losses else 1
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
    expectancy = total_pnl / len(pnls) if pnls else 0

    exit_reasons = {}
    for t in completed:
        reason = t.get('exit_reason', 'unknown')
        exit_reasons[reason] = exit_reasons.get(reason, 0) + 1

    results = {
        'strategy': 'Pairs Trading EUR/USD-GBP/USD v2',
        'pair': 'EUR/USD-GBP/USD',
        'timeframe': 'M5',
        'data_bars': len(df),
        'date_range': f"{df.index[0]} to {df.index[-1]}",
        'cost_model': {
            'commission_per_lot': COMMISSION_PER_LOT,
            'spread_source': 'CSV SPREAD column (points)',
            'risk_per_position': RISK_PER_POSITION,
            'account_equity': ACCOUNT_EQUITY,
            'pip_size': PIP_SIZE,
            'pip_value_per_standard_lot': PIP_VALUE_PER_STANDARD_LOT,
            'fixed_lot_size': round(lot_size, 4),
            'stop_pips': round(stop_pips, 1),
        },
        'total_trades': len(completed),
        'wins': len(wins),
        'losses': len(losses),
        'win_rate': round(win_rate, 1),
        'gross_pnl': round(total_gross, 2),
        'total_commission': round(total_commission, 2),
        'total_spread_cost': round(total_spread, 2),
        'net_pnl': round(total_pnl, 2),
        'avg_win': round(avg_win, 2),
        'avg_loss': round(avg_loss, 2),
        'max_drawdown': round(max_dd, 2),
        'profit_factor': round(profit_factor, 2),
        'expectancy': round(expectancy, 2),
        'avg_lot_size': round(lot_size, 4),
        'final_equity': round(equity, 2),
        'by_exit': exit_reasons,
        'avg_correlation': round(df['correlation'].mean(), 3),
    }

    print(f"\n{'=' * 70}")
    print(f"RESULTS - Pairs Trading EUR/USD-GBP/USD v2 (Proper Cost Model)")
    print(f"{'=' * 70}")
    print(f"  Total trades:       {results['total_trades']}")
    print(f"  Win rate:           {win_rate:.1f}%")
    print(f"  Gross P&L:          ${total_gross:,.2f}")
    print(f"  Total commission:   -${total_commission:,.2f}")
    print(f"  Total spread cost:  -${total_spread:,.2f}")
    print(f"  ---------------------------------")
    print(f"  Net P&L:            ${total_pnl:,.2f}")
    print(f"  Avg win:            ${avg_win:,.2f}")
    print(f"  Avg loss:           ${avg_loss:,.2f}")
    print(f"  Max drawdown:       ${max_dd:,.2f}")
    print(f"  Profit factor:      {profit_factor:.2f}")
    print(f"  Expectancy:         ${expectancy:,.2f}/trade")
    print(f"  Lot size:           {lot_size:.4f} lots (fixed)")
    print(f"  Final equity:       ${equity:,.2f}")
    print(f"  Avg correlation:    {df['correlation'].mean():.3f}")
    print(f"\n  Exit reasons:")
    for reason, count in sorted(exit_reasons.items(), key=lambda x: -x[1]):
        print(f"    {reason}: {count}")

    return results


if __name__ == "__main__":
    results = run_backtest()
    output_path = RESULTS_DIR / "pairs_trading_v2_results.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n  [SAVE] Results saved to {output_path}")
