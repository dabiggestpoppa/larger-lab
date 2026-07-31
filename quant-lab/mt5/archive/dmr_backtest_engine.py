"""
DMR Backtest Engine - Python-based MT5 backtest
Gets historical data from MT5 via Python API and simulates the DMR strategy.
This replicates the logic from DMR_FULL_BACKTEST.mq5 without needing the Strategy Tester GUI.
"""
import sys, os, time, json
from datetime import datetime, timedelta
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')

import MetaTrader5 as mt5
import math

# â”€â”€ Strategy Parameters (matching DMR_FULL_BACKTEST.mq5) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
PARAMS = {
    'LotSize':      0.01,
    'MagicNumber':  20260528,
    'DeepMult':     2.0,
    'KillMult':     2.2,
    'MinAR':        3,
    'MaxAR':        45,
    'ESTOffset':    -5,
    'HardExitHour': 17,
    'MaxDailyTrades': 1,
}

SYMBOL = "EURUSD.PRO"

# â”€â”€ Data Fetch â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def fetch_bars(from_dt, to_dt, timeframe=mt5.TIMEFRAME_M5):
    """Fetch historical bars from MT5"""
    rates = mt5.copy_rates_range(SYMBOL, timeframe, from_dt, to_dt)
    if rates is None or len(rates) == 0:
        print(f"  ERROR: Failed to fetch bars: {mt5.last_error()}")
        return []
    return rates

def fetch_tick_data(from_dt, to_dt):
    """Fetch tick data for more accurate backtesting"""
    ticks = mt5.copy_ticks_range(SYMBOL, from_dt, to_dt, mt5.COPY_TICKS_ALL)
    if ticks is None:
        return []
    return ticks

# â”€â”€ P90 Calculation (Asian Range) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def calc_asian_range(bars, est_offset=-5):
    """
    Calculate the Asian Range (P90) for each day.
    Asian session: 7 PM EST - 4 AM EST (with offset)
    P90 = 90th percentile of the daily range
    """
    daily_ranges = []
    daily_data = defaultdict(list)
    
    for bar in bars:
        dt = datetime.fromtimestamp(bar['time'])
        # Adjust for EST
        est_hour = (dt.hour + est_offset) % 24
        date_key = dt.date()
        
        daily_data[date_key].append({
            'high': bar['high'],
            'low': bar['low'],
            'open': bar['open'],
            'close': bar['close'],
            'volume': bar['tick_volume'],
            'dt': dt,
            'est_hour': est_hour,
        })
    
    return daily_data

def calc_p90(daily_bars):
    """Calculate P90 threshold for a day"""
    if len(daily_bars) < 2:
        return None, None
    
    daily_range = max(b['high'] for b in daily_bars) - min(b['low'] for b in daily_bars)
    daily_high = max(b['high'] for b in daily_bars)
    daily_low = min(b['low'] for b in daily_bars)
    
    # P90 = 90% of the daily range from the open
    day_open = daily_bars[0]['open']
    p90_up = day_open + daily_range * 0.9
    p90_dn = day_open - daily_range * 0.9
    
    return p90_up, p90_dn, daily_range

# â”€â”€ DMR Strategy Simulation â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def run_dmr_backtest(bars, params=None):
    """
    Simulate the DMR (Deep Mean Reversion) strategy.
    
    Logic (from DMR_FULL_BACKTEST.mq5):
    1. Each day, calculate P90 (90th percentile of expected range)
    2. If price touches P90 level â†’ mark as "Deep State"
    3. If price reverses from Deep State â†’ place trade against the move
    4. SL at KillMult * distance from entry to P90
    5. TP at mean reversion (activation level)
    6. Max 1 trade per day
    7. Hard exit at HardExitHour EST
    """
    if params is None:
        params = PARAMS
    
    results = {
        'trades': [],
        'daily_stats': [],
        'summary': {}
    }
    
    # Group bars by day
    daily_bars = defaultdict(list)
    for bar in bars:
        dt = datetime.fromtimestamp(bar['time'])
        date_key = dt.date()
        est_hour = (dt.hour + params['ESTOffset']) % 24
        daily_bars[date_key].append({
            'time': bar['time'],
            'dt': dt,
            'est_hour': est_hour,
            'open': bar['open'],
            'high': bar['high'],
            'low': bar['low'],
            'close': bar['close'],
            'volume': bar['tick_volume'],
        })
    
    total_pnl = 0
    wins = 0
    losses = 0
    total_trades = 0
    
    for date_key in sorted(daily_bars.keys()):
        day_bars = sorted(daily_bars[date_key], key=lambda x: x['time'])
        if len(day_bars) < 10:
            continue
        
        # Calculate daily range and P90
        day_high = max(b['high'] for b in day_bars)
        day_low = min(b['low'] for b in day_bars)
        day_open = day_bars[0]['open']
        day_range = day_high - day_low
        
        # Asian Range filter
        if day_range < params['MinAR'] * 0.0001 or day_range > params['MaxAR'] * 0.0001:
            continue
        
        p90_up = day_open + day_range * 0.9
        p90_dn = day_open - day_range * 0.9
        
        # DMR Logic
        deep_state_touched = False
        trade_placed = False
        p90_direction = 0  # 1 = up, -1 = down
        activation_level = 0
        
        for bar in day_bars:
            # Hard exit check
            if bar['est_hour'] >= params['HardExitHour']:
                break
            
            if not deep_state_touched:
                # Check if P90 is touched
                if bar['high'] >= p90_up:
                    deep_state_touched = True
                    p90_direction = 1
                    activation_level = p90_up
                elif bar['low'] <= p90_dn:
                    deep_state_touched = True
                    p90_direction = -1
                    activation_level = p90_dn
            else:
                if not trade_placed:
                    # Check for reversal (Deep State â†’ Mean Reversion)
                    if p90_direction == 1:  # Was up, now reversing down
                        if bar['close'] < activation_level:
                            # SHORT entry
                            entry_price = bar['close']
                            sl_distance = (activation_level - entry_price) * params['KillMult']
                            sl_price = entry_price + sl_distance  # SL above for short
                            tp_price = day_open  # TP at mean (day open)
                            
                            trade = simulate_trade(
                                entry_price, sl_price, tp_price,
                                day_bars, bar, SELL=True
                            )
                            if trade:
                                trade['date'] = str(date_key)
                                trade['direction'] = 'SELL'
                                results['trades'].append(trade)
                                total_pnl += trade['pnl_pips']
                                if trade['pnl_pips'] > 0:
                                    wins += 1
                                else:
                                    losses += 1
                                total_trades += 1
                            trade_placed = True
                    
                    elif p90_direction == -1:  # Was down, now reversing up
                        if bar['close'] > activation_level:
                            # BUY entry
                            entry_price = bar['close']
                            sl_distance = (entry_price - activation_level) * params['KillMult']
                            sl_price = entry_price - sl_distance  # SL below for buy
                            tp_price = day_open  # TP at mean
                            
                            trade = simulate_trade(
                                entry_price, sl_price, tp_price,
                                day_bars, bar, SELL=False
                            )
                            if trade:
                                trade['date'] = str(date_key)
                                trade['direction'] = 'BUY'
                                results['trades'].append(trade)
                                total_pnl += trade['pnl_pips']
                                if trade['pnl_pips'] > 0:
                                    wins += 1
                                else:
                                    losses += 1
                                total_trades += 1
                            trade_placed = True
    
    # Summary
    wr = (wins / total_trades * 100) if total_trades > 0 else 0
    results['summary'] = {
        'total_trades': total_trades,
        'wins': wins,
        'losses': losses,
        'win_rate': wr,
        'total_pnl_pips': round(total_pnl, 2),
        'avg_pnl_pips': round(total_pnl / total_trades, 2) if total_trades > 0 else 0,
        'params': params,
        'symbol': SYMBOL,
    }
    
    return results

def simulate_trade(entry, sl, tp, remaining_bars, entry_bar, SELL=False):
    """Simulate a single trade through remaining bars"""
    entry_idx = None
    for i, b in enumerate(remaining_bars):
        if b['time'] >= entry_bar['time']:
            entry_idx = i
            break
    
    if entry_idx is None:
        return None
    
    for bar in remaining_bars[entry_idx:]:
        if SELL:
            # SELL: SL above, TP below
            if bar['high'] >= sl:
                pnl_pips = round((entry - sl) / 0.0001, 2)
                return {'pnl_pips': -abs(pnl_pips), 'result': 'SL', 'bar_time': str(bar['dt'])}
            if bar['low'] <= tp:
                pnl_pips = round((entry - tp) / 0.0001, 2)
                return {'pnl_pips': abs(pnl_pips), 'result': 'TP', 'bar_time': str(bar['dt'])}
        else:
            # BUY: SL below, TP above
            if bar['low'] <= sl:
                pnl_pips = round((sl - entry) / 0.0001, 2)
                return {'pnl_pips': -abs(pnl_pips), 'result': 'SL', 'bar_time': str(bar['dt'])}
            if bar['high'] >= tp:
                pnl_pips = round((tp - entry) / 0.0001, 2)
                return {'pnl_pips': abs(pnl_pips), 'result': 'TP', 'bar_time': str(bar['dt'])}
    
    # Trade still open at end of day â€” close at last bar's close
    last_bar = remaining_bars[-1]
    if SELL:
        pnl_pips = round((entry - last_bar['close']) / 0.0001, 2)
    else:
        pnl_pips = round((last_bar['close'] - entry) / 0.0001, 2)
    
    return {'pnl_pips': pnl_pips, 'result': 'EOD', 'bar_time': str(last_bar['dt'])}

# â”€â”€ Main â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def main():
    print("="*60)
    print("DMR Backtest Engine (Python + MT5 Data)")
    print(f"Symbol: {SYMBOL}")
    print(f"Strategy: Deep Mean Reversion (v3.0)")
    print("="*60)
    
    if not mt5.initialize():
        print(f"Failed to connect to MT5: {mt5.last_error()}")
        sys.exit(1)
    
    print(f"Connected to MT5")
    acc = mt5.account_info()
    if acc:
        print(f"Account: {acc.login} | Balance: {acc.balance} {acc.currency}")
    
    # â”€â”€ Test Configurations â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    TESTS = [
        ("1M_Jan2024",  datetime(2024, 1, 1),  datetime(2024, 1, 31)),
        ("1M_Feb2024",  datetime(2024, 2, 1),  datetime(2024, 2, 29)),
        ("1M_Mar2024",  datetime(2024, 3, 1),  datetime(2024, 3, 31)),
        ("3M_Q1_2024",  datetime(2024, 1, 1),  datetime(2024, 3, 31)),
        ("6M_H1_2024",  datetime(2024, 1, 1),  datetime(2024, 6, 30)),
        ("1Y_2024",     datetime(2024, 1, 1),  datetime(2024, 12, 31)),
        ("1M_Jan2025",  datetime(2025, 1, 1),  datetime(2025, 1, 31)),
        ("3M_Q1_2025",  datetime(2025, 1, 1),  datetime(2025, 3, 31)),
        ("YTD_2025",    datetime(2025, 1, 1),  datetime(2025, 12, 31)),
        ("Full_2024_25",datetime(2024, 1, 1),  datetime(2025, 12, 31)),
    ]
    
    all_results = {}
    
    # Run quick validation first (1 month)
    print(f"\n{'â”€'*60}")
    print("Running validation test: Jan 2024")
    print(f"{'â”€'*60}")
    
    label, from_dt, to_dt = TESTS[0]
    t0 = time.time()
    bars = fetch_bars(from_dt, to_dt)
    fetch_time = time.time() - t0
    
    if bars is None or len(bars) == 0:
        print("No data fetched!")
        mt5.shutdown()
        sys.exit(1)
    
    print(f"Fetched {len(bars)} bars in {fetch_time:.1f}s")
    print(f"Date range: {datetime.fromtimestamp(bars[0]['time'])} â†’ {datetime.fromtimestamp(bars[-1]['time'])}")
    
    t0 = time.time()
    results = run_dmr_backtest(bars)
    sim_time = time.time() - t0
    
    print(f"\nSimulation complete in {sim_time:.2f}s")
    print(f"Total trades: {results['summary']['total_trades']}")
    print(f"Win rate: {results['summary']['win_rate']:.1f}%")
    print(f"Total P&L: {results['summary']['total_pnl_pips']:.1f} pips")
    print(f"Avg P&L: {results['summary']['avg_pnl_pips']:.2f} pips")
    
    # Show first few trades
    if results['trades']:
        print(f"\nFirst 5 trades:")
        for t in results['trades'][:5]:
            print(f"  {t['date']} {t['direction']:4s} â†’ {t['result']:3s}  {t['pnl_pips']:+.1f} pips")
    
    all_results[label] = results['summary']
    
    # â”€â”€ Run Full Suite â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    print(f"\n{'='*60}")
    print("FULL BACKTEST SUITE")
    print(f"{'='*60}")
    
    for label, from_dt, to_dt in TESTS:
        t0 = time.time()
        bars = fetch_bars(from_dt, to_dt)
        if bars is None or len(bars) == 0:
            print(f"\n{label}: NO DATA")
            continue
        
        results = run_dmr_backtest(bars)
        elapsed = time.time() - t0
        
        s = results['summary']
        print(f"\n{label:15s} | {s['total_trades']:3d} trades | WR: {s['win_rate']:5.1f}% | "
              f"P&L: {s['total_pnl_pips']:+8.1f} pips | {elapsed:.1f}s")
        
        all_results[label] = s
    
    # â”€â”€ Summary Table â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    print(f"\n{'='*60}")
    print("SUMMARY TABLE")
    print(f"{'='*60}")
    print(f"{'Test':15s} | {'Trades':>6s} | {'WR%':>6s} | {'P&L pips':>10s} | {'Wins':>4s} | {'Loss':>4s}")
    print(f"{'-'*15}-+-{'-'*6}-+-{'-'*6}-+-{'-'*10}-+-{'-'*4}-+-{'-'*4}")
    
    for label, s in all_results.items():
        print(f"{label:15s} | {s['total_trades']:6d} | {s['win_rate']:5.1f}% | "
              f"{s['total_pnl_pips']:+10.1f} | {s['wins']:4d} | {s['losses']:4d}")
    
    # â”€â”€ Save Results â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    out_file = os.path.join(os.path.dirname(__file__), "backtest_results.json")
    serializable = {}
    for label, s in all_results.items():
        serializable[label] = {k: v for k, v in s.items() if k != 'params'}
        serializable[label]['params'] = {k: v for k, v in s['params'].items()}
    
    with open(out_file, 'w') as f:
        json.dump(serializable, f, indent=2, default=str)
    print(f"\nResults saved: {out_file}")
    
    mt5.shutdown()
    print("\nBacktest pipeline complete.")

if __name__ == '__main__':
    main()

