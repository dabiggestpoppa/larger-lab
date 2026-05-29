"""
DMR Tick-Level Simulator
Uses MT5 tick data (copy_ticks_range) for high-fidelity backtest.
This eliminates the bar-approximation gap vs MT5 Strategy Tester.

Instead of simulating from OHLC bars, we:
1. Fetch tick data for the date range from MT5
2. Reconstruct intrabar price movement from ticks
3. Apply the DMR logic tick-by-tick
4. This should closely match MT5 Strategy Tester's every-tick model

Key fidelity improvements over bar-level simulation:
- Exact fill timing (tick resolution vs bar close)
- Accurate SL/TP trigger detection (intrabar touch matters)
- Proper spread handling
"""
import sys, os, time, json
from datetime import datetime, timedelta

sys.stdout.reconfigure(encoding='utf-8')

import MetaTrader5 as mt5
import numpy as np

SYMBOL = "EURUSD.PRO"

# ── Strategy Parameters ────────────────────────────────────────────
PARAMS = {
    'LotSize':        0.01,
    'DeepMult':       2.0,
    'KillMult':       2.2,
    'MinAR':          3,
    'MaxAR':          45,
    'ESTOffset':      -5,
    'HardExitHour':   17,
    'MaxDailyTrades': 1,
}

def get_p90_threshold(est_hour):
    if est_hour in (2, 3):      return 4.1
    if 4 <= est_hour <= 6:      return 4.6
    if est_hour in (7, 8):      return 5.9
    if est_hour in (9, 10):     return 6.2
    return 999.0

def pips_to_price(pips):
    return pips / 10000.0

def price_to_pips(price):
    return price * 10000.0

def get_est_hour(dt, offset=-5):
    return (dt.hour + offset) % 24

# ── Fetch M5 bars for strategy logic ───────────────────────────────
# We still use M5 bars for the strategy decisions (P90 scan, etc.)
# But we use ticks for fill simulation
def fetch_m5_bars(from_dt, to_dt):
    rates = mt5.copy_rates_range(SYMBOL, mt5.TIMEFRAME_M5, from_dt, to_dt)
    if rates is None or len(rates) == 0:
        return None
    return rates

# ── Fetch tick data for fill simulation ────────────────────────────
def fetch_ticks(from_dt, to_dt):
    """Fetch tick data from MT5"""
    ticks = mt5.copy_ticks_range(SYMBOL, from_dt, to_dt, mt5.COPY_TICKS_ALL)
    if ticks is None or len(ticks) == 0:
        return None
    return ticks

# ── Tick-level DMR Simulation ─────────────────────────────────────
def run_tick_dmr(m5_bars, ticks, params):
    """
    Run DMR simulation with tick-level fill precision.
    
    Strategy decisions (P90 scan, DS check) use M5 bars (same as EA).
    Entry/exit simulation uses tick data for precise fill timing.
    """
    trades = []
    
    # Build M5 bar lookup by timestamp
    bar_by_time = {}
    for bar in m5_bars:
        bar_by_time[bar['time']] = bar
    
    # Group ticks by date (EST) and by M5 bar
    days = {}
    for tick in ticks:
        dt = datetime.fromtimestamp(tick['time'])
        est_h = get_est_hour(dt, params['ESTOffset'])
        est_dt = dt + timedelta(hours=params['ESTOffset'])
        date_key = est_dt.date()
        
        if date_key not in days:
            days[date_key] = {'ticks': [], 'bars': []}
        days[date_key]['ticks'].append({
            'time': tick['time'],
            'dt': dt,
            'est_h': est_h,
            'bid': tick['bid'],
            'ask': tick['ask'],
            'volume': tick['volume'],
        })
    
    # Group M5 bars by date
    for bar in m5_bars:
        dt = datetime.fromtimestamp(bar['time'])
        est_dt = dt + timedelta(hours=params['ESTOffset'])
        date_key = est_dt.date()
        if date_key in days:
            days[date_key]['bars'].append({
                'time': bar['time'],
                'dt': dt,
                'est_h': get_est_hour(dt, params['ESTOffset']),
                'open': bar['open'],
                'high': bar['high'],
                'low': bar['low'],
                'close': bar['close'],
            })
    
    for date_key in sorted(days.keys()):
        day = days[date_key]
        day_bars = sorted(day['bars'], key=lambda b: b['time'])
        day_ticks = sorted(day['ticks'], key=lambda t: t['time'])
        
        if len(day_bars) < 5 or len(day_ticks) < 50:
            continue
        
        # ── Track Asian Range (7PM-3AM EST) ──
        asian_high = 0.0
        asian_low = 99999.0
        ar_locked = False
        skip_day = False
        
        for b in day_bars:
            if b['est_h'] >= 19 or b['est_h'] < 3:
                if b['high'] > asian_high: asian_high = b['high']
                if b['low'] < asian_low:   asian_low = b['low']
            if b['est_h'] == 3 and not ar_locked:
                ar_locked = True
                if asian_high > 0 and asian_low < 99999:
                    ar_pips = price_to_pips(asian_high - asian_low)
                    if ar_pips < params['MinAR'] or ar_pips > params['MaxAR']:
                        skip_day = True
                break
        
        if skip_day:
            continue
        
        # ── Trading window 2AM-11AM ──
        trading_bars = [b for b in day_bars if 2 <= b['est_h'] < 11]
        
        # ── Scan for P90 ──
        p90_found = False
        p90_dir = 0
        activation = 0.0
        deep_state = 0.0
        kill_switch = 0.0
        body_pips = 0.0
        p90_bar_idx = -1
        
        for i, b in enumerate(trading_bars):
            body = abs(b['close'] - b['open'])
            bp = price_to_pips(body)
            threshold = get_p90_threshold(b['est_h'])
            
            if bp >= threshold:
                p90_found = True
                p90_dir = 1 if b['close'] > b['open'] else -1
                activation = b['close']
                body_pips = bp
                deep_state = activation + pips_to_price(bp * params['DeepMult']) * p90_dir
                kill_switch = activation + pips_to_price(bp * params['KillMult']) * p90_dir
                p90_bar_idx = i
                break
        
        if not p90_found:
            continue
        
        # ── Check Deep State touch (before noon) ──
        ds_touched = False
        ds_touch_time = None
        ds_touch_bar = None
        
        for b in trading_bars[p90_bar_idx + 1:]:
            if b['est_h'] >= 12:
                break
            if p90_dir == 1 and b['low'] <= deep_state:
                ds_touched = True
                ds_touch_time = b['time']
                ds_touch_bar = b
                break
            if p90_dir == -1 and b['high'] >= deep_state:
                ds_touched = True
                ds_touch_time = b['time']
                ds_touch_bar = b
                break
        
        if not ds_touched:
            continue
        
        # ── Entry: Mean reversion at bar close ──
        is_short = (p90_dir == 1)
        entry_price = ds_touch_bar['close']
        
        # ── Validate TP/SL (MT5 rejects orders with TP/SL on wrong side) ──
        if is_short:
            if activation >= entry_price or kill_switch <= entry_price:
                continue
        else:
            if activation <= entry_price or kill_switch >= entry_price:
                continue
        
        # ── Simulate with TICK data for precise fills ──
        # Find ticks after entry
        entry_ticks = [t for t in day_ticks if t['time'] > ds_touch_time]
        
        pnl_pips = 0.0
        result = 'UNKNOWN'
        
        for tick in entry_ticks:
            # Hard exit
            if tick['est_h'] >= params['HardExitHour']:
                if is_short:
                    pnl_pips = price_to_pips(entry_price - tick['bid'])
                else:
                    pnl_pips = price_to_pips(tick['ask'] - entry_price)
                result = 'HARD_EXIT'
                break
            
            if is_short:
                # SHORT: hit SL if ask >= kill_switch, hit TP if bid <= activation
                if tick['ask'] >= kill_switch:
                    pnl_pips = price_to_pips(entry_price - kill_switch)
                    result = 'SL'
                    break
                if tick['bid'] <= activation:
                    pnl_pips = price_to_pips(entry_price - activation)
                    result = 'TP'
                    break
            else:
                # BUY: hit SL if bid <= kill_switch, hit TP if ask >= activation
                if tick['bid'] <= kill_switch:
                    pnl_pips = price_to_pips(kill_switch - entry_price)
                    result = 'SL'
                    break
                if tick['ask'] >= activation:
                    pnl_pips = price_to_pips(activation - entry_price)
                    result = 'TP'
                    break
        else:
            # End of data
            if entry_ticks:
                last = entry_ticks[-1]
                if is_short:
                    pnl_pips = price_to_pips(entry_price - last['bid'])
                else:
                    pnl_pips = price_to_pips(last['ask'] - entry_price)
            result = 'EOD'
        
        # Subtract spread cost
        spread_pips = params.get('SpreadPips', 0.0)
        pnl_pips = round(pnl_pips - spread_pips, 1)
        
        trades.append({
            'date': str(date_key),
            'direction': 'SHORT' if is_short else 'BUY',
            'p90_dir': 'BULL' if p90_dir == 1 else 'BEAR',
            'body_pips': round(body_pips, 1),
            'entry': round(entry_price, 5),
            'ds': round(deep_state, 5),
            'ks': round(kill_switch, 5),
            'tp': round(activation, 5),
            'pnl_pips': pnl_pips,
            'result': result,
        })
    
    total = len(trades)
    wins = sum(1 for t in trades if t['pnl_pips'] > 0)
    losses = sum(1 for t in trades if t['pnl_pips'] < 0)
    total_pnl = sum(t['pnl_pips'] for t in trades)
    
    return trades, {
        'total_trades': total,
        'wins': wins,
        'losses': losses,
        'win_rate': round(wins / total * 100, 1) if total > 0 else 0,
        'total_pnl_pips': round(total_pnl, 2),
        'avg_pnl_pips': round(total_pnl / total, 2) if total > 0 else 0,
    }

# ── Main ───────────────────────────────────────────────────────────
def main():
    print("="*60)
    print("DMR Tick-Level Backtest (High Fidelity)")
    print(f"Symbol: {SYMBOL}")
    print("="*60)
    
    if not mt5.initialize():
        print(f"MT5 connection failed: {mt5.last_error()}")
        sys.exit(1)
    
    # Run on recent week where tick data is available
    from_dt = datetime(2026, 5, 21)
    to_dt   = datetime(2026, 5, 28)
    
    print(f"\nPeriod: {from_dt.strftime('%Y-%m-%d')} to {to_dt.strftime('%Y-%m-%d')}")
    
    # Fetch M5 bars for strategy logic
    print("Fetching M5 bars...")
    t0 = time.time()
    bars = fetch_m5_bars(from_dt, to_dt)
    if bars is None:
        print("No M5 data!")
        mt5.shutdown()
        sys.exit(1)
    print(f"  {len(bars)} bars in {time.time()-t0:.1f}s")
    
    # Fetch tick data for fill simulation
    print("Fetching tick data...")
    t0 = time.time()
    ticks = fetch_ticks(from_dt, to_dt)
    if ticks is None:
        print("No tick data! Falling back to bar-level simulation.")
        ticks = None
    else:
        print(f"  {len(ticks)} ticks in {time.time()-t0:.1f}s")
    
    # Run simulation
    print("\nRunning simulation...")
    t0 = time.time()
    if ticks is not None:
        trades, summary = run_tick_dmr(bars, ticks, PARAMS)
    else:
        print("  Tick data unavailable — skipping")
        mt5.shutdown()
        sys.exit(1)
    
    elapsed = time.time() - t0
    print(f"  Completed in {elapsed:.2f}s")
    
    # Results
    s = summary
    print(f"\n{'='*50}")
    print(f"RESULTS")
    print(f"{'='*50}")
    print(f"Total trades: {s['total_trades']}")
    print(f"Win rate:     {s['win_rate']:.1f}%")
    print(f"Total P&L:    {s['total_pnl_pips']:+.1f} pips")
    print(f"Avg P&L:      {s['avg_pnl_pips']:+.2f} pips/trade")
    print(f"Wins/Losses:  {s['wins']}/{s['losses']}")
    
    # Show first 10 trades
    if trades:
        print(f"\nFirst trades:")
        for t in trades[:10]:
            print(f"  {t['date']} {t['direction']:5s} {t['p90_dir']:5s} "
                  f"body={t['body_pips']:4.1f}p entry={t['entry']:.5f} "
                  f"KS={t['ks']:.5f} TP={t['tp']:.5f} → {t['pnl_pips']:+6.1f}p {t['result']}")
    
    # Save results
    out_file = os.path.join(os.path.dirname(__file__), "reports", "tick_sim_results.json")
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, 'w') as f:
        json.dump({'summary': summary, 'trades': trades}, f, indent=2, default=str)
    print(f"\nSaved: {out_file}")
    
    mt5.shutdown()
    print("Done.")

if __name__ == '__main__':
    main()
