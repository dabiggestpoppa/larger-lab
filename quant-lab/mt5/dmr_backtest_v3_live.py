"""
DMR Backtest Engine v3-LIVE — Matches MT5 EA's ACTUAL live behavior
===================================================================
The MT5 EA (DMR_FULL_BACKTEST.mq5) places orders WITHOUT setting SL/TP
on the MqlTradeRequest. This means:

In STRATEGY TESTER:
- MT5 simulates SL/TP fills based on bar data
- Results match intermediate bar-by-bar SL/TP checking

In LIVE/DEMO trading:
- NO SL/TP is set on the broker
- Position stays open until hard exit at 5PM
- Anyone using v3 for backtesting is seeing OPTIMISTIC results
  (intraday SL/TP closes) that won't happen live

This engine matches LIVE behavior:
- Entry at DS-touch bar close (same as EA)
- NO intermediate SL/TP simulation
- Only exit: hard exit at 5PM bar close
- PnL = entry - hard_exit_close (for SHORT) or reverse (for BUY)
"""
import sys, os, time, json
from datetime import datetime, timedelta

sys.stdout.reconfigure(encoding='utf-8')

import MetaTrader5 as mt5

SYMBOL = "EURUSD.PRO"

PARAMS = {
    'LotSize':        0.01,
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


def run_dmr_live(bars, params):
    """
    Matches MT5 EA's actual live/demo behavior:
    - No SL/TP set on orders
    - Only hard exit at 5PM EST
    - Exit at bar close
    """
    trades = []
    total_pnl = 0.0
    wins = 0
    losses = 0
    spread_pips = params.get('SpreadPips', 0.0)
    
    days = {}
    for bar in bars:
        dt = datetime.fromtimestamp(bar['time'])
        est_hour = get_est_hour(dt, params['ESTOffset'])
        est_dt = dt + timedelta(hours=params['ESTOffset'])
        date_key = est_dt.date()
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
        
        # ── Asian Range ──
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
        
        # ── Trading window ──
        trading_bars = [b for b in day_bars if 2 <= b['est_h'] < 11]
        
        # ── P90 scan ──
        p90_found = False
        p90_dir = 0
        activation = 0.0
        deep_state = 0.0
        kill_switch = 0.0
        body_pips_val = 0.0
        p90_idx = -1
        
        for i, b in enumerate(trading_bars):
            body = abs(b['close'] - b['open'])
            bp = price_to_pips(body)
            if bp >= get_p90_threshold(b['est_h']):
                p90_found = True
                p90_dir = 1 if b['close'] > b['open'] else -1
                activation = b['close']
                body_pips_val = bp
                deep_state = activation + pips_to_price(bp * params['DeepMult']) * p90_dir
                kill_switch = activation + pips_to_price(bp * params['KillMult']) * p90_dir
                p90_idx = i
                break
        if not p90_found:
            continue
        
        # ── Deep State touch ──
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
        
        # ── Entry at bar close ──
        is_short = (p90_dir == 1)
        entry_price = ds_bar['close']
        
        # ── LIVE behavior: NO SL/TP, only hard exit at 5PM ──
        pnl_pips = 0.0
        result = 'UNKNOWN'
        exit_price = entry_price
        
        for b in day_bars:
            if b['time'] <= ds_bar['time']:
                continue
            if b['est_h'] >= params['HardExitHour']:
                exit_price = b['close']
                if is_short:
                    pnl_pips = price_to_pips(entry_price - exit_price)
                else:
                    pnl_pips = price_to_pips(exit_price - entry_price)
                result = 'HARD_EXIT'
                break
        else:
            # End of data
            last = day_bars[-1]
            exit_price = last['close']
            if is_short:
                pnl_pips = price_to_pips(entry_price - exit_price)
            else:
                pnl_pips = price_to_pips(exit_price - entry_price)
            result = 'EOD'
        
        pnl_pips = round(pnl_pips - spread_pips, 1)
        total_pnl += pnl_pips
        if pnl_pips > 0:   wins += 1
        elif pnl_pips < 0: losses += 1
        
        trades.append({
            'date': str(date_key),
            'direction': 'SHORT' if is_short else 'BUY',
            'p90_dir': 'BULL' if p90_dir == 1 else 'BEAR',
            'body_pips': round(body_pips_val, 1),
            'entry': round(entry_price, 5),
            'exit': round(exit_price, 5),
            'ds': round(deep_state, 5),
            'ks': round(kill_switch, 5),
            'activation': round(activation, 5),
            'pnl_pips': pnl_pips,
            'result': result,
        })
    
    total = wins + losses
    return trades, {
        'total_trades': total, 'wins': wins, 'losses': losses,
        'win_rate': round(wins / total * 100, 1) if total > 0 else 0.0,
        'total_pnl_pips': round(total_pnl, 2),
        'avg_pnl_pips': round(total_pnl / total, 2) if total > 0 else 0.0,
    }


def main():
    print("="*60)
    print("DMR v3-LIVE (matches MT5 EA actual live behavior)")
    print("NO SL/TP — only hard exit at 5PM")
    print("="*60)
    
    if not mt5.initialize():
        print("MT5 init failed"); sys.exit(1)
    
    info = mt5.symbol_info(SYMBOL)
    if info:
        PARAMS['SpreadPips'] = price_to_pips(info.spread * info.point)
        print(f"Spread: {PARAMS['SpreadPips']:.1f} pips")
    
    from dmr_backtest_v3 import run_dmr_v3
    
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
    
    print(f"\n{'Test':15s} | {'Tester(v3)':>22s} | {'LIVE(v3-live)':>22s}")
    print(f"{'':15s} | {'Tr':>4} {'WR':>6} {'PnL':>8} | {'Tr':>4} {'WR':>6} {'PnL':>8}")
    print(f"{'-'*15}-+-{'-'*4}-{'-'*6}-{'-'*8}-+-{'-'*4}-{'-'*6}-{'-'*8}")
    
    for label, from_dt, to_dt in TESTS:
        bars = fetch_bars(from_dt, to_dt)
        if bars is None:
            print(f"{label}: NO DATA")
            continue
        
        v3_t, v3_s = run_dmr_v3(bars, PARAMS)
        vl_t, vl_s = run_dmr_live(bars, PARAMS)
        
        print(f"{label:15s} | {v3_s['total_trades']:4d} {v3_s['win_rate']:5.1f}% {v3_s['total_pnl_pips']:+8.1f} | "
              f"{vl_s['total_trades']:4d} {vl_s['win_rate']:5.1f}% {vl_s['total_pnl_pips']:+8.1f}")
    
    mt5.shutdown()

if __name__ == '__main__':
    main()
