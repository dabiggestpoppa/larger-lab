"""
DMR Multi-Pair Backtest v2 — Full Statistical Suite
===================================================
- Max available history per pair
- Per-hour P90 calibration (not just single threshold)
- Full stats: Sharpe, Max Drawdown, Kelly, PF, etc.
"""
import sys, os, json
from datetime import datetime, timedelta

sys.stdout.reconfigure(encoding='utf-8')

import MetaTrader5 as mt5
import numpy as np

PAIRS = {
    'EURUSD': {'symbol': 'EURUSD', 'pip_mult': 10000},
    'GBPUSD': {'symbol': 'GBPUSD', 'pip_mult': 10000},
    'USDJPY': {'symbol': 'USDJPY', 'pip_mult': 100},
    'AUDUSD': {'symbol': 'AUDUSD', 'pip_mult': 10000},
    'USDCAD': {'symbol': 'USDCAD', 'pip_mult': 10000},
    'NZDUSD': {'symbol': 'NZDUSD', 'pip_mult': 10000},
}

PARAMS = {
    'DeepMult': 2.0, 'KillMult': 2.2,
    'MinAR': 3, 'MaxAR': 45,
    'ESTOffset': -5, 'HardExitHour': 17,
}

def get_est_hour(dt, offset=-5):
    return (dt.hour + offset) % 24

def compute_p90_per_hour(bars, pip_mult):
    """Compute P90 threshold for each EST hour in activation window."""
    hourly_p90 = {}
    for h in range(2, 11):
        hour_bars = []
        for bar in bars:
            dt = datetime.fromtimestamp(bar['time'])
            est_h = get_est_hour(dt)
            if est_h == h:
                body = abs(bar['close'] - bar['open'])
                hour_bars.append(body * pip_mult)
        if len(hour_bars) >= 20:
            hourly_p90[h] = round(np.percentile(hour_bars, 90), 1)
        else:
            hourly_p90[h] = None
    return hourly_p90

def get_p90_threshold(est_hour, hourly_p90, fallback):
    """Get P90 for specific hour, with fallback chain."""
    if est_hour in hourly_p90 and hourly_p90[est_hour] is not None:
        return hourly_p90[est_hour]
    # Use nearest hour with data
    for offset in range(1, 9):
        for candidate in [est_hour - offset, est_hour + offset]:
            if candidate in hourly_p90 and hourly_p90[candidate] is not None:
                return hourly_p90[candidate]
    return fallback

def compute_stats(trades, initial_balance=289.17):
    """Compute full statistical suite from trade list."""
    if not trades:
        return {'error': 'No trades'}
    
    pnls = [t['pnl'] for t in trades]
    n = len(pnls)
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]
    
    total_pnl = sum(pnls)
    gross_profit = sum(wins) if wins else 0
    gross_loss = abs(sum(losses)) if losses else 0.001  # avoid div by zero
    
    win_rate = len(wins) / n * 100 if n > 0 else 0
    avg_win = sum(wins) / len(wins) if wins else 0
    avg_loss = sum(losses) / len(losses) if losses else 0
    
    # Profit Factor
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
    
    # Expectancy
    expectancy = total_pnl / n if n > 0 else 0
    
    # Sharpe Ratio (simplified — per-trade returns)
    returns = pnls  # already in pips
    mean_ret = np.mean(returns)
    std_ret = np.std(returns)
    sharpe = (mean_ret / std_ret * np.sqrt(252)) if std_ret > 0 else 0
    
    # Max Drawdown (pip-based equity curve)
    equity = initial_balance
    peak = equity
    max_dd = 0
    dd_series = []
    for p in pnls:
        equity += p * 0.01  # ~0.01 lots = ~$1/pip for most pairs
        if equity > peak:
            peak = equity
        dd = peak - equity
        if dd > max_dd:
            max_dd = dd
        dd_series.append(dd)
    
    # Max Drawdown percentage
    max_dd_pct = (max_dd / initial_balance * 100) if initial_balance > 0 else 0
    
    # Kelly Criterion
    if gross_loss > 0 and gross_profit > 0:
        w = len(wins) / n
        r = avg_win / abs(avg_loss) if avg_loss != 0 else 1
        kelly = (w * r - (1 - w)) / r if r > 0 else 0
    else:
        kelly = 0
    
    # Half Kelly (practical)
    half_kelly = kelly / 2
    
    # Consecutive wins/losses
    max_consec_wins = 0
    max_consec_losses = 0
    curr_wins = 0
    curr_losses = 0
    for p in pnls:
        if p > 0:
            curr_wins += 1
            curr_losses = 0
            max_consec_wins = max(max_consec_wins, curr_wins)
        elif p < 0:
            curr_losses += 1
            curr_wins = 0
            max_consec_losses = max(max_consec_losses, curr_losses)
    
    # Long/Short breakdown
    long_trades = [t for t in trades if t['dir'] == 'LONG']
    short_trades = [t for t in trades if t['dir'] == 'SHORT']
    long_wr = sum(1 for t in long_trades if t['pnl'] > 0) / len(long_trades) * 100 if long_trades else 0
    short_wr = sum(1 for t in short_trades if t['pnl'] > 0) / len(short_trades) * 100 if short_trades else 0
    long_pnl = sum(t['pnl'] for t in long_trades)
    short_pnl = sum(t['pnl'] for t in short_trades)
    
    # Hourly distribution
    hourly_stats = {}
    for h in range(2, 11):
        h_trades = [t for t in trades if t.get('est_hour') == h]
        if h_trades:
            h_wins = sum(1 for t in h_trades if t['pnl'] > 0)
            hourly_stats[str(h)] = {
                'trades': len(h_trades),
                'wr': round(h_wins / len(h_trades) * 100, 1),
                'pnl': round(sum(t['pnl'] for t in h_trades), 1),
            }
    
    return {
        'total_trades': n,
        'wins': len(wins),
        'losses': len(losses),
        'win_rate': round(win_rate, 1),
        'total_pnl_pips': round(total_pnl, 1),
        'gross_profit': round(gross_profit, 1),
        'gross_loss': round(-gross_loss, 1),
        'profit_factor': round(profit_factor, 2),
        'expectancy_pips': round(expectancy, 2),
        'avg_win_pips': round(avg_win, 1),
        'avg_loss_pips': round(avg_loss, 1),
        'sharpe_ratio': round(sharpe, 2),
        'max_drawdown_$': round(max_dd, 2),
        'max_drawdown_%': round(max_dd_pct, 2),
        'kelly_criterion': round(kelly, 3),
        'half_kelly': round(half_kelly, 3),
        'max_consec_wins': max_consec_wins,
        'max_consec_losses': max_consec_losses,
        'long_trades': len(long_trades),
        'long_wr': round(long_wr, 1),
        'long_pnl': round(long_pnl, 1),
        'short_trades': len(short_trades),
        'short_wr': round(short_wr, 1),
        'short_pnl': round(short_pnl, 1),
        'hourly': hourly_stats,
    }


def run_dmr_pair(bars, cfg, hourly_p90):
    """Run DMR logic on single pair."""
    pip_mult = cfg['pip_mult']
    fallback_p90 = cfg.get('p90_fallback', 4.0)
    
    def pips_to_price(pips):
        return pips / pip_mult
    def price_to_pips(price):
        return price * pip_mult
    
    trades = []
    
    # Group by EST date
    days = {}
    for bar in bars:
        dt = datetime.fromtimestamp(bar['time'])
        est_dt = dt + timedelta(hours=PARAMS['ESTOffset'])
        date_key = est_dt.date()
        est_hour = get_est_hour(dt)
        
        if date_key not in days:
            days[date_key] = []
        days[date_key].append({
            'time': bar['time'], 'dt': dt, 'est_h': est_hour,
            'open': bar['open'], 'high': bar['high'],
            'low': bar['low'], 'close': bar['close'],
        })
    
    for date_key in sorted(days.keys()):
        day_bars = sorted(days[date_key], key=lambda b: b['time'])
        if len(day_bars) < 5:
            continue
        
        # Asian Range
        asian_high, asian_low = 0.0, 99999.0
        ar_locked = False
        skip_day = False
        for b in day_bars:
            if b['est_h'] >= 19 or b['est_h'] < 3:
                asian_high = max(asian_high, b['high'])
                asian_low = min(asian_low, b['low'])
            if b['est_h'] == 3 and not ar_locked:
                ar_locked = True
                if asian_high > 0 and asian_low < 99999:
                    ar_pips = price_to_pips(asian_high - asian_low)
                    if ar_pips < PARAMS['MinAR'] or ar_pips > PARAMS['MaxAR']:
                        skip_day = True
                break
        if skip_day:
            continue
        
        # Trading window
        trading_bars = [b for b in day_bars if 2 <= b['est_h'] < 11]
        if not trading_bars:
            continue
        
        # P90 scan with per-hour calibration
        p90_found = False
        p90_dir = 0
        activation = deep_state = kill_switch = 0.0
        body_pips = 0.0
        p90_idx = -1
        p90_hour = -1
        
        for i, b in enumerate(trading_bars):
            body = abs(b['close'] - b['open'])
            bp = price_to_pips(body)
            threshold = get_p90_threshold(b['est_h'], hourly_p90, fallback_p90)
            if bp >= threshold:
                p90_found = True
                p90_dir = 1 if b['close'] > b['open'] else -1
                activation = b['close']
                body_pips = bp
                deep_state = activation + pips_to_price(bp * PARAMS['DeepMult']) * p90_dir
                kill_switch = activation + pips_to_price(bp * PARAMS['KillMult']) * p90_dir
                p90_idx = i
                p90_hour = b['est_h']
                break
        
        if not p90_found:
            continue
        
        # DS touch
        ds_touched = False
        ds_bar = None
        for b in trading_bars[p90_idx + 1:]:
            if b['est_h'] >= 12:
                break
            if p90_dir == 1 and b['low'] <= deep_state:
                ds_touched = True
                ds_bar = b
                break
            if p90_dir == -1 and b['high'] >= deep_state:
                ds_touched = True
                ds_bar = b
                break
        if not ds_touched:
            continue
        
        # Entry & validate
        is_short = (p90_dir == 1)
        entry_price = ds_bar['close']
        if is_short:
            if activation >= entry_price or kill_switch <= entry_price:
                continue
        else:
            if activation <= entry_price or kill_switch >= entry_price:
                continue
        
        # Simulate trade
        pnl_pips = 0.0
        result = 'UNKNOWN'
        for tb in trading_bars:
            if tb['time'] <= ds_bar['time']:
                continue
            if tb['est_h'] >= PARAMS['HardExitHour']:
                if is_short:
                    pnl_pips = price_to_pips(entry_price - tb['close'])
                else:
                    pnl_pips = price_to_pips(tb['close'] - entry_price)
                result = 'HARD_EXIT'
                break
            if is_short:
                if tb['high'] >= kill_switch:
                    pnl_pips = price_to_pips(entry_price - kill_switch)
                    result = 'SL'
                    break
                if tb['low'] <= activation:
                    pnl_pips = price_to_pips(entry_price - activation)
                    result = 'TP'
                    break
            else:
                if tb['low'] <= kill_switch:
                    pnl_pips = price_to_pips(kill_switch - entry_price)
                    result = 'SL'
                    break
                if tb['high'] >= activation:
                    pnl_pips = price_to_pips(activation - entry_price)
                    result = 'TP'
                    break
        else:
            last = trading_bars[-1] if trading_bars else ds_bar
            pnl_pips = price_to_pips(entry_price - last['close']) if is_short else price_to_pips(last['close'] - entry_price)
            result = 'EOD'
        
        pnl_pips = round(pnl_pips, 1)
        trades.append({
            'date': str(date_key), 'result': result, 'pnl': pnl_pips,
            'dir': 'SHORT' if is_short else 'LONG',
            'body': round(body_pips, 1), 'est_hour': p90_hour,
            'entry': round(entry_price, 5),
            'sl': round(kill_switch, 5), 'tp': round(activation, 5),
        })
    
    return trades


def main():
    if not mt5.initialize():
        print("ERROR: MT5 init failed")
        return
    
    # Fetch max available data for each pair
    # MT5 typically provides ~65K M5 bars max
    from_dt = datetime(2023, 6, 1)  # 2+ years
    to_dt = datetime.utcnow()
    
    print("=" * 80)
    print("DMR MULTI-PAIR BACKTEST v2 — Full Statistical Suite")
    print(f"Period: {from_dt.date()} to {to_dt.date()} | Max available M5")
    print(f"DeepMult={PARAMS['DeepMult']} | KillMult={PARAMS['KillMult']}")
    print(f"Per-hour P90 calibration | AR filter: {PARAMS['MinAR']}-{PARAMS['MaxAR']}p")
    print("=" * 80)
    
    all_results = {}
    all_trades_combined = []
    
    for pair, cfg in PAIRS.items():
        info = mt5.symbol_info(cfg['symbol'])
        if info is None:
            cfg['symbol'] = cfg['symbol'] + '.PRO'
            info = mt5.symbol_info(cfg['symbol'])
        if info is None:
            print(f"[FAIL] {pair}: not found")
            continue
        
        bars = mt5.copy_rates_range(cfg['symbol'], mt5.TIMEFRAME_M5, from_dt, to_dt)
        if bars is None or len(bars) == 0:
            print(f"[FAIL] {pair}: no data")
            continue
        
        span_days = (bars[-1]['time'] - bars[0]['time']) / 86400
        print(f"\n[{pair}] {cfg['symbol']} | {len(bars):,} bars | {span_days:.0f} days")
        
        # Compute per-hour P90
        hourly_p90 = compute_p90_per_hour(bars, cfg['pip_mult'])
        cfg['p90_fallback'] = np.median([v for v in hourly_p90.values() if v is not None]) if any(v for v in hourly_p90.values()) else 4.0
        
        print(f"  Per-hour P90:")
        for h in range(2, 11):
            val = hourly_p90.get(h)
            print(f"    {h:02d}:00 EST → {val:.1f}p" if val else f"    {h:02d}:00 EST → N/A (using fallback {cfg['p90_fallback']:.1f}p)")
        
        # Run DMR
        trades = run_dmr_pair(bars, cfg, hourly_p90)
        stats = compute_stats(trades)
        stats['hourly_p90'] = {str(k): v for k, v in hourly_p90.items() if v is not None}
        stats['data_bars'] = len(bars)
        stats['data_days'] = int(span_days)
        stats['symbol'] = cfg['symbol']
        
        all_results[pair] = stats
        all_trades_combined.extend(trades)
        
        if 'error' in stats:
            print(f"  No trades")
        else:
            print(f"\n  --- RESULTS ---")
            print(f"  Trades: {stats['total_trades']} | W: {stats['wins']} L: {stats['losses']} | WR: {stats['win_rate']}%")
            print(f"  PnL: {stats['total_pnl_pips']:+.1f} pips")
            print(f"  Profit Factor: {stats['profit_factor']}")
            print(f"  Expectancy: {stats['expectancy_pips']:+.2f} pips/trade")
            print(f"  Avg Win: {stats['avg_win_pips']:+.1f}p | Avg Loss: {stats['avg_loss_pips']:+.1f}p")
            print(f"  Sharpe (ann): {stats['sharpe_ratio']}")
            print(f"  Max Drawdown: ${stats['max_drawdown_$']:.2f} ({stats['max_drawdown_%']:.1f}%)")
            print(f"  Kelly: {stats['kelly_criterion']:.3f} | Half-Kelly: {stats['half_kelly']:.3f}")
            print(f"  Max Consec W/L: {stats['max_consec_wins']} / {stats['max_consec_losses']}")
            print(f"  Long: {stats['long_trades']} ({stats['long_wr']}% WR, {stats['long_pnl']:+.1f}p)")
            print(f"  Short: {stats['short_trades']} ({stats['short_wr']}% WR, {stats['short_pnl']:+.1f}p)")
    
    # Combined stats across all pairs
    print("\n" + "=" * 80)
    print("COMBINED — ALL 6 PAIRS")
    print("=" * 80)
    combined = compute_stats(all_trades_combined)
    for k, v in combined.items():
        if k != 'hourly':
            print(f"  {k}: {v}")
    
    # Save full results
    out = {
        'per_pair': {p: {k: v for k, v in s.items() if k != 'hourly'} for p, s in all_results.items()},
        'combined': {k: v for k, v in combined.items() if k != 'hourly'},
        'hourly_p90': {p: s.get('hourly_p90', {}) for p, s in all_results.items()},
        'combined_hourly': combined.get('hourly', {}),
        'trades_sample': {p: all_results[p].get('total_trades', 0) for p in all_results},
    }
    outpath = r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\dmr_multi_pair_v2.json"
    with open(outpath, 'w') as f:
        json.dump(out, f, indent=2, default=str)
    print(f"\nFull results saved to {outpath}")
    
    mt5.shutdown()

if __name__ == '__main__':
    main()
