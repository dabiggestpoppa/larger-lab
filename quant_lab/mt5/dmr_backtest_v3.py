"""
DMR Backtest Engine v3 - MT5 EA Faithful Simulation
=====================================================
Fixes over v2 (which was dangerously optimistic):
1. SL/TP PnL at FIXED broker levels, NOT bar extremes
2. Spread-aware (subtracts spread from all PnL)
3. Conservative SL-first checking within same bar
4. Entry at DS-touch bar close

This engine is designed to produce results that match what the MT5 EA
(DMR_FULL_BACKTEST.mq5) would produce when running live or in Strategy Tester.

The key insight: MT5 EA sets real SL/TP at the broker. When price touches
the level, the broker fills at that level. The PnL is the fixed distance
from entry to the TP/SL level — NOT the bar extreme.
"""
import sys, os, time, json
from datetime import datetime, timedelta

sys.stdout.reconfigure(encoding='utf-8')

import MetaTrader5 as mt5

SYMBOL = "EURUSD.PRO"

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
    'SpreadPips':     0.0,
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

def fetch_bars(from_dt, to_dt, tf=mt5.TIMEFRAME_M5):
    rates = mt5.copy_rates_range(SYMBOL, tf, from_dt, to_dt)
    if rates is None or len(rates) == 0:
        return None
    return rates


def run_dmr_v3(bars, params):
    """
    MT5 EA faithful simulation.
    Matches DMR_FULL_BACKTEST.mq5 OnTick() logic exactly.
    """
    trades = []
    total_pnl = 0.0
    wins = 0
    losses = 0
    
    spread_pips = params.get('SpreadPips', 0.0)
    
    # Group bars by EST date
    days = {}
    for bar in bars:
        dt = datetime.fromtimestamp(bar['time'])
        est_hour = get_est_hour(dt, params['ESTOffset'])
        est_dt = dt + timedelta(hours=params['ESTOffset'])
        date_key = est_dt.date()
        
        if date_key not in days:
            days[date_key] = []
        
        days[date_key].append({
            'time':  bar['time'],
            'dt':    dt,
            'est_h': est_hour,
            'open':  bar['open'],
            'high':  bar['high'],
            'low':   bar['low'],
            'close': bar['close'],
        })
    
    for date_key in sorted(days.keys()):
        day_bars = sorted(days[date_key], key=lambda b: b['time'])
        if len(day_bars) < 5:
            continue
        
        # ── Asian Range (7PM-3AM EST) ──
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
        
        # ── Trading window 2AM-11AM ──
        trading_bars = [b for b in day_bars if 2 <= b['est_h'] < 11]
        
        # ── P90 scan ──
        p90_found = False
        p90_dir = 0
        activation = 0.0
        deep_state = 0.0
        kill_switch = 0.0
        body_pips = 0.0
        p90_idx = -1
        
        for i, b in enumerate(trading_bars):
            body = abs(b['close'] - b['open'])
            bp = price_to_pips(body)
            if bp >= get_p90_threshold(b['est_h']):
                p90_found = True
                p90_dir = 1 if b['close'] > b['open'] else -1
                activation = b['close']
                body_pips = bp
                deep_state = activation + pips_to_price(bp * params['DeepMult']) * p90_dir
                kill_switch = activation + pips_to_price(bp * params['KillMult']) * p90_dir
                p90_idx = i
                break
        
        if not p90_found:
            continue
        
        # ── Deep State touch (before noon) ──
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
        
        # ── Entry at DS-touch bar close ──
        is_short = (p90_dir == 1)
        entry_price = ds_bar['close']
        
        # ── Validate TP/SL placement (MT5 would reject invalid orders) ──
        if is_short:
            if activation >= entry_price or kill_switch <= entry_price:
                continue  # MT5 rejects: SHORT needs TP < entry < SL
        else:
            if activation <= entry_price or kill_switch >= entry_price:
                continue  # MT5 rejects: BUY needs SL < entry < TP
        
        # ── Simulate trade ──
        pnl_pips = 0.0
        result = 'UNKNOWN'
        
        for tb in trading_bars:
            if tb['time'] <= ds_bar['time']:
                continue
            
            # Hard exit at bar close
            if tb['est_h'] >= params['HardExitHour']:
                if is_short:
                    pnl_pips = price_to_pips(entry_price - tb['close']) - spread_pips
                else:
                    pnl_pips = price_to_pips(tb['close'] - entry_price) - spread_pips
                result = 'HARD_EXIT'
                break
            
            if is_short:
                # SL check first (conservative)
                if tb['high'] >= kill_switch:
                    pnl_pips = price_to_pips(entry_price - kill_switch) - spread_pips
                    result = 'SL'
                    break
                if tb['low'] <= activation:
                    pnl_pips = price_to_pips(entry_price - activation) - spread_pips
                    result = 'TP'
                    break
            else:
                if tb['low'] <= kill_switch:
                    pnl_pips = price_to_pips(kill_switch - entry_price) - spread_pips
                    result = 'SL'
                    break
                if tb['high'] >= activation:
                    pnl_pips = price_to_pips(activation - entry_price) - spread_pips
                    result = 'TP'
                    break
        else:
            last = trading_bars[-1] if trading_bars else ds_bar
            if is_short:
                pnl_pips = price_to_pips(entry_price - last['close']) - spread_pips
            else:
                pnl_pips = price_to_pips(last['close'] - entry_price) - spread_pips
            result = 'EOD'
        
        pnl_pips = round(pnl_pips, 1)
        total_pnl += pnl_pips
        if pnl_pips > 0:
            wins += 1
        elif pnl_pips < 0:
            losses += 1
        
        trades.append({
            'date':       str(date_key),
            'direction':  'SHORT' if is_short else 'BUY',
            'p90_dir':    'BULL' if p90_dir == 1 else 'BEAR',
            'body_pips':  round(body_pips, 1),
            'entry':      round(entry_price, 5),
            'ds':         round(deep_state, 5),
            'ks':         round(kill_switch, 5),
            'activation': round(activation, 5),
            'pnl_pips':   pnl_pips,
            'result':     result,
        })
    
    total = wins + losses
    return trades, {
        'total_trades':   total,
        'wins':           wins,
        'losses':         losses,
        'win_rate':       round(wins / total * 100, 1) if total > 0 else 0.0,
        'total_pnl_pips': round(total_pnl, 2),
        'avg_pnl_pips':   round(total_pnl / total, 2) if total > 0 else 0.0,
    }


def main():
    print("="*60)
    print("DMR Backtest v3 (MT5 EA Faithful)")
    print(f"Symbol: {SYMBOL}")
    print("="*60)
    
    if not mt5.initialize():
        print(f"MT5 init failed: {mt5.last_error()}")
        sys.exit(1)
    
    info = mt5.symbol_info(SYMBOL)
    if info:
        spread_pips = price_to_pips(info.spread * info.point)
        print(f"Spread: {info.spread} pts ({spread_pips:.1f} pips)")
        PARAMS['SpreadPips'] = spread_pips
    
    from dmr_backtest_v2 import run_dmr as run_v2, fetch_bars as fetch_v2
    
    TESTS = [
        ("1M_Jan2024",   datetime(2024, 1, 1),  datetime(2024, 2, 1)),
        ("1M_Feb2024",   datetime(2024, 2, 1),  datetime(2024, 3, 1)),
        ("1M_Mar2024",   datetime(2024, 3, 1),  datetime(2024, 4, 1)),
        ("1M_Apr2024",   datetime(2024, 4, 1),  datetime(2024, 5, 1)),
        ("1M_May2024",   datetime(2024, 5, 1),  datetime(2024, 6, 1)),
        ("1M_Jun2024",   datetime(2024, 6, 1),  datetime(2024, 7, 1)),
        ("1Y_2024",      datetime(2024, 1, 1),  datetime(2025, 1, 1)),
        ("1Y_2025",      datetime(2025, 1, 1),  datetime(2026, 1, 1)),
        ("Full_2024_25", datetime(2024, 1, 1),  datetime(2026, 1, 1)),
    ]
    
    print(f"\n{'Test':15s} | {'v2 Tr':>5} {'v2 WR':>6} {'v2 PnL':>8} | {'v3 Tr':>5} {'v3 WR':>6} {'v3 PnL':>8} | {'Delta':>7}")
    print(f"{'-'*15}-+-{'-'*5}-{'-'*6}-{'-'*8}-+-{'-'*5}-{'-'*6}-{'-'*8}-+-{'-'*7}")
    
    all_v3 = {}
    for label, from_dt, to_dt in TESTS:
        bars = fetch_bars(from_dt, to_dt)
        if bars is None:
            print(f"{label}: NO DATA")
            continue
        
        v2_t, v2_s = run_v2(bars, PARAMS)
        v3_t, v3_s = run_dmr_v3(bars, PARAMS)
        delta = v3_s['total_pnl_pips'] - v2_s['total_pnl_pips']
        
        print(f"{label:15s} | {v2_s['total_trades']:5d} {v2_s['win_rate']:5.1f}% {v2_s['total_pnl_pips']:+8.1f} | "
              f"{v3_s['total_trades']:5d} {v3_s['win_rate']:5.1f}% {v3_s['total_pnl_pips']:+8.1f} | {delta:+7.1f}")
        
        all_v3[label] = {'summary': v3_s, 'trades': v3_t}
    
    # Sample trades
    fk = "Full_2024_25"
    if fk in all_v3:
        print(f"\n── v3 Trades (first 15) ──")
        for t in all_v3[fk]['trades'][:15]:
            print(f"  {t['date']:12s} {t['direction']:5s} {t['p90_dir']:5s} body={t['body_pips']:4.1f}p "
                  f"entry={t['entry']:.5f} KS={t['ks']:.5f} TP={t['activation']:.5f} "
                  f"→ {t['pnl_pips']:+6.1f}p {t['result']}")
    
    # Save
    out_file = os.path.join(os.path.dirname(__file__), "reports", "backtest_v3_results.json")
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, 'w') as f:
        json.dump(all_v3, f, indent=2, default=str)
    print(f"\nSaved: {out_file}")
    
    mt5.shutdown()

if __name__ == '__main__':
    main()
