"""
DMR Backtest Engine v2 - Faithful port of DMR_FULL_BACKTEST.mq5
Exact logic match: P90 per-bar scan → Deep State → Mean Reversion entry
"""
import sys, os, time, json
from datetime import datetime, timedelta

sys.stdout.reconfigure(encoding='utf-8')

import MetaTrader5 as mt5
import numpy as np

SYMBOL = "EURUSD.PRO"

# ── Parameters (matching EA defaults) ──────────────────────────────
PARAMS = {
    'LotSize':        0.01,
    'MagicNumber':    20260528,
    'DeepMult':       2.0,
    'KillMult':       2.2,
    'MinAR':          3,
    'MaxAR':          45,
    'ESTOffset':      -5,
    'HardExitHour':   17,
    'MaxDailyTrades': 1,
}

# ── P90 Thresholds by EST hour (exact from .mq5) ───────────────────
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
    est = (dt.hour + offset) % 24
    return est

# ── Data Fetch ─────────────────────────────────────────────────────
def fetch_bars(from_dt, to_dt, tf=mt5.TIMEFRAME_M5):
    rates = mt5.copy_rates_range(SYMBOL, tf, from_dt, to_dt)
    if rates is None or len(rates) == 0:
        return None
    return rates

# ── Main Simulation ────────────────────────────────────────────────
def run_dmr(bars, params):
    """
    Exact DMR logic from DMR_FULL_BACKTEST.mq5
    
    Per day:
    1. Track Asian Range (7PM-3AM EST), lock at 3AM
    2. Skip day if AR outside [MinAR, MaxAR]
    3. Trading window: 2AM-11AM EST
    4. Scan for P90: bar with body >= threshold for that EST hour
    5. Deep State = close ± body*DeepMult (same direction as bar)
    6. Wait for price to touch Deep State
    7. Enter MEAN REVERSAL (opposite direction of P90 bar)
       SL = close ± body*KillMult, TP = P90 bar close
    8. Hard exit at 5PM EST
    """
    trades = []
    total_pnl = 0.0
    wins = 0
    losses = 0
    
    # Group bars by date
    days = {}
    for bar in bars:
        dt = datetime.fromtimestamp(bar['time'])
        # Use the date in EST
        est_hour = get_est_hour(dt, params['ESTOffset'])
        est_dt = dt + timedelta(hours=params['ESTOffset'])
        date_key = est_dt.date()
        
        if date_key not in days:
            days[date_key] = []
        
        days[date_key].append({
            'time':    bar['time'],
            'dt':      dt,
            'est_h':   est_hour,
            'open':    bar['open'],
            'high':    bar['high'],
            'low':     bar['low'],
            'close':   bar['close'],
        })
    
    for date_key in sorted(days.keys()):
        day_bars = sorted(days[date_key], key=lambda b: b['time'])
        if len(day_bars) < 5:
            continue
        
        # ── Step 1: Track Asian Range (7PM-3AM EST) ──
        asian_high = 0.0
        asian_low  = 99999.0
        ar_locked  = False
        skip_day   = False
        
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
        
        # ── Step 2: Trading window 2AM-11AM ──
        trading_bars = [b for b in day_bars if 2 <= b['est_h'] < 11]
        
        # ── Step 3: Scan for P90 ──
        p90_found     = False
        p90_dir       = 0      # 1=bull, -1=bear
        activation    = 0.0    # P90 bar close
        deep_state    = 0.0    # Deep State level
        kill_switch   = 0.0    # Kill Switch level
        body_pips     = 0.0
        
        for i, b in enumerate(trading_bars):
            body = abs(b['close'] - b['open'])
            body_p = price_to_pips(body)
            threshold = get_p90_threshold(b['est_h'])
            
            if body_p >= threshold:
                p90_found  = True
                p90_dir    = 1 if b['close'] > b['open'] else -1
                activation = b['close']
                body_pips  = body_p
                
                # Deep State = close + body*DeepMult in bar direction
                deep_state  = activation + pips_to_price(body_p * params['DeepMult']) * p90_dir
                kill_switch = activation + pips_to_price(body_p * params['KillMult']) * p90_dir
                
                trading_bars = trading_bars[i+1:]  # Continue after P90 bar
                break
        
        if not p90_found:
            continue
        
        # ── Step 4: Check Deep State touch (before noon EST) ──
        ds_touched = False
        for b in trading_bars:
            if b['est_h'] >= 12:
                break
            
            if p90_dir == 1 and b['low'] <= deep_state:
                ds_touched = True
                break
            if p90_dir == -1 and b['high'] >= deep_state:
                ds_touched = True
                break
        
        if not ds_touched:
            continue
        
        # ── Step 5: Place mean reversion trade ──
        # If P90 was bullish (up bar), enter SHORT (mean reversion down)
        # If P90 was bearish (down bar), enter LONG (mean reversion up)
        is_short = (p90_dir == 1)
        entry_ds_bar = b  # Bar where DS was touched
        
        # ── Validate TP/SL (MT5 rejects orders with TP/SL on wrong side) ──
        if is_short:
            if activation >= entry_ds_bar['close'] or kill_switch <= entry_ds_bar['close']:
                continue
        else:
            if activation <= entry_ds_bar['close'] or kill_switch >= entry_ds_bar['close']:
                continue
        
        # ── Step 6: Simulate trade until TP/SL/hard exit ──
        pnl_pips = 0.0
        result = 'UNKNOWN'
        
        for tb in trading_bars:
            if tb['time'] <= entry_ds_bar['time']:
                continue
            
            # Hard exit
            if tb['est_h'] >= params['HardExitHour']:
                if is_short:
                    pnl_pips = price_to_pips(activation - tb['close'])
                else:
                    pnl_pips = price_to_pips(tb['close'] - activation)
                result = 'HARD_EXIT'
                break
            
            if is_short:
                # SHORT: SL above, TP below
                if tb['high'] >= kill_switch:
                    pnl_pips = price_to_pips(activation - kill_switch)
                    result = 'SL'
                    break
                if tb['low'] <= activation:
                    pnl_pips = price_to_pips(activation - tb['low'])
                    result = 'TP'
                    break
            else:
                # BUY: SL below, TP above
                if tb['low'] <= kill_switch:
                    pnl_pips = price_to_pips(kill_switch - activation)
                    result = 'SL'
                    break
                if tb['high'] >= activation:
                    pnl_pips = price_to_pips(tb['high'] - activation)
                    result = 'TP'
                    break
        else:
            # End of day
            last = trading_bars[-1] if trading_bars else entry_ds_bar
            if is_short:
                pnl_pips = price_to_pips(activation - last['close'])
            else:
                pnl_pips = price_to_pips(last['close'] - activation)
            result = 'EOD'
        
        pnl_pips = round(pnl_pips, 2)
        if is_short:
            pnl_pips = -abs(pnl_pips) if result == 'SL' else (abs(pnl_pips) if result == 'TP' else pnl_pips)
        else:
            pnl_pips = -abs(pnl_pips) if result == 'SL' else (abs(pnl_pips) if result == 'TP' else pnl_pips)
        
        trades.append({
            'date':        str(date_key),
            'direction':   'SHORT' if is_short else 'BUY',
            'p90_dir':     'BULL' if p90_dir == 1 else 'BEAR',
            'body_pips':   round(body_pips, 1),
            'ds':          round(deep_state, 5),
            'ks':          round(kill_switch, 5),
            'activation':  round(activation, 5),
            'pnl_pips':    pnl_pips,
            'result':      result,
        })
        
        total_pnl += pnl_pips
        if pnl_pips > 0:   wins += 1
        elif pnl_pips < 0: losses += 1
    
    total = wins + losses
    summary = {
        'total_trades':   total,
        'wins':           wins,
        'losses':         losses,
        'win_rate':       round(wins / total * 100, 1) if total > 0 else 0.0,
        'total_pnl_pips': round(total_pnl, 2),
        'avg_pnl_pips':   round(total_pnl / total, 2) if total > 0 else 0.0,
    }
    
    return trades, summary

# ── Main ───────────────────────────────────────────────────────────
def main():
    print("="*60)
    print("DMR Backtest Engine v2 (MQ5-Exact Logic)")
    print(f"Symbol: {SYMBOL}")
    print("="*60)
    
    if not mt5.initialize():
        print(f"MT5 connection failed: {mt5.last_error()}")
        sys.exit(1)
    
    acc = mt5.account_info()
    if acc:
        print(f"Account: {acc.login} | Balance: {acc.balance} {acc.currency}")
    
    # ── Test Suite ─────────────────────────────────────────────────
    TESTS = [
        ("1M_Jan2024",   datetime(2024, 1, 1),  datetime(2024, 2, 1)),
        ("1M_Feb2024",   datetime(2024, 2, 1),  datetime(2024, 3, 1)),
        ("1M_Mar2024",   datetime(2024, 3, 1),  datetime(2024, 4, 1)),
        ("1M_Apr2024",   datetime(2024, 4, 1),  datetime(2024, 5, 1)),
        ("1M_May2024",   datetime(2024, 5, 1),  datetime(2024, 6, 1)),
        ("1M_Jun2024",   datetime(2024, 6, 1),  datetime(2024, 7, 1)),
        ("3M_Q1Q2_2024", datetime(2024, 1, 1),  datetime(2024, 7, 1)),
        ("1Y_2024",      datetime(2024, 1, 1),  datetime(2025, 1, 1)),
        ("1Y_2025",      datetime(2025, 1, 1),  datetime(2026, 1, 1)),
        ("Full_2024_25", datetime(2024, 1, 1),  datetime(2026, 1, 1)),
    ]
    
    all_results = {}
    all_trades = {}
    
    for label, from_dt, to_dt in TESTS:
        t0 = time.time()
        bars = fetch_bars(from_dt, to_dt)
        if bars is None:
            print(f"{label}: NO DATA")
            continue
        
        trades, summary = run_dmr(bars, PARAMS)
        elapsed = time.time() - t0
        
        s = summary
        print(f"{label:15s} | {s['total_trades']:3d} tr | WR: {s['win_rate']:5.1f}% | "
              f"P&L: {s['total_pnl_pips']:+8.1f}p | Avg: {s['avg_pnl_pips']:+6.2f}p | {elapsed:.1f}s")
        
        all_results[label] = s
        all_trades[label] = trades
    
    # ── Summary Table ──────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"{'TEST RESULTS SUMMARY':^70}")
    print(f"{'='*70}")
    print(f"{'Test':15s} | {'Trades':>6s} | {'WR%':>6s} | {'P&L pips':>10s} | {'Wins':>4s} | {'Loss':>4s} | {'Avg':>6s}")
    print(f"{'-'*15}-+-{'-'*6}-+-{'-'*6}-+-{'-'*10}-+-{'-'*4}-+-{'-'*4}-+-{'-'*6}")
    
    for label, s in all_results.items():
        print(f"{label:15s} | {s['total_trades']:6d} | {s['win_rate']:5.1f}% | "
              f"{s['total_pnl_pips']:+10.1f} | {s['wins']:4d} | {s['losses']:4d} | {s['avg_pnl_pips']:+6.2f}")
    
    # ── Detailed Trades for Full Period ────────────────────────────
    full_key = "Full_2024_25"
    if full_key in all_trades and all_trades[full_key]:
        print(f"\n── Detailed Trades: {full_key} ──")
        print(f"{'Date':12s} {'Dir':5s} {'P90':5s} {'Body':>6s} | {'DS':>10s} {'KS':>10s} {'TP':>10s} {'PnL':>7s} {'Result':>5s}")
        print(f"{'-'*12}-+-{'-'*5}-+-{'-'*5}-+-{'-'*6}-+-{'-'*10}-+-{'-'*10}-+-{'-'*10}-+-{'-'*7}-+-{'-'*10}")
        for t in all_trades[full_key][:20]:
            print(f"{t['date']:12s} {t['direction']:5s} {t['p90_dir']:5s} {t['body_pips']:5.1f}p "
                  f"  DS={t['ds']:10.5f} KS={t['ks']:10.5f} TP={t['activation']:10.5f} "
                  f"{t['pnl_pips']:+7.1f} {t['result']}")
        if len(all_trades[full_key]) > 20:
            print(f"  ... and {len(all_trades[full_key])-20} more trades")
    
    # ── Save Results ──────────────────────────────────────────────
    out_file = os.path.join(os.path.dirname(__file__), "backtest_v2_results.json")
    out = {}
    for label in all_results:
        out[label] = {
            'summary': all_results[label],
            'trades': all_trades.get(label, [])
        }
    
    with open(out_file, 'w') as f:
        json.dump(out, f, indent=2, default=str)
    print(f"\nResults saved: {out_file}")
    
    mt5.shutdown()
    print("\nBacktest complete.")

if __name__ == '__main__':
    main()
