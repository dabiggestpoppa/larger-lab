"""
DMR Multi-Pair Backtest Engine
================================
Runs DMR v3 logic across all major FX pairs using
CEREBUS-derived P90 thresholds per pair.

Uses MT5 live data (180 days M5) for each pair.
"""
import sys, os, json
from datetime import datetime, timedelta

sys.stdout.reconfigure(encoding='utf-8')

import MetaTrader5 as mt5
import numpy as np

# ── PAIR CONFIG ──
PAIRS = {
    'EURUSD': {'symbol': 'EURUSD',   'p90': 4.1, 'pip_mult': 10000, 'point': 0.00001},
    'GBPUSD': {'symbol': 'GBPUSD',   'p90': 5.6, 'pip_mult': 10000, 'point': 0.00001},
    'USDJPY': {'symbol': 'USDJPY',   'p90': 6.4, 'pip_mult': 100,   'point': 0.001},
    'AUDUSD': {'symbol': 'AUDUSD',   'p90': 3.7, 'pip_mult': 10000, 'point': 0.00001},
    'USDCAD': {'symbol': 'USDCAD',   'p90': 3.5, 'pip_mult': 10000, 'point': 0.00001},
    'NZDUSD': {'symbol': 'NZDUSD',   'p90': 3.0, 'pip_mult': 10000, 'point': 0.00001},
}

PARAMS = {
    'DeepMult': 2.0,
    'KillMult': 2.2,
    'MinAR': 3,
    'MaxAR': 45,
    'ESTOffset': -5,
    'HardExitHour': 17,
}

def get_est_hour(dt, offset=-5):
    return (dt.hour + offset) % 24

def fetch_bars(symbol, from_dt, to_dt):
    rates = mt5.copy_rates_range(symbol, mt5.TIMEFRAME_M5, from_dt, to_dt)
    if rates is None or len(rates) == 0:
        return None
    return rates

def run_dmr_pair(bars, cfg):
    """Run DMR v3 logic on a single pair's bars."""
    p90_threshold = cfg['p90']
    pip_mult = cfg['pip_mult']
    
    def pips_to_price(pips):
        return pips / pip_mult
    
    def price_to_pips(price):
        return price * pip_mult
    
    trades = []
    total_pnl = 0.0
    wins = 0
    losses = 0
    skip_ar = 0
    skip_p90 = 0
    skip_ds = 0
    
    # Group by EST date
    days = {}
    for bar in bars:
        dt = datetime.fromtimestamp(bar['time'])
        est_dt = dt + timedelta(hours=PARAMS['ESTOffset'])
        date_key = est_dt.date()
        est_hour = get_est_hour(dt, PARAMS['ESTOffset'])
        
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
        
        # Asian Range (7PM-3AM EST)
        asian_high = 0.0
        asian_low = 99999.0
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
                        skip_ar += 1
                break
        
        if skip_day:
            continue
        
        # Trading window 2AM-11AM
        trading_bars = [b for b in day_bars if 2 <= b['est_h'] < 11]
        
        # P90 scan
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
            if bp >= p90_threshold:
                p90_found = True
                p90_dir = 1 if b['close'] > b['open'] else -1
                activation = b['close']
                body_pips = bp
                deep_state = activation + pips_to_price(bp * PARAMS['DeepMult']) * p90_dir
                kill_switch = activation + pips_to_price(bp * PARAMS['KillMult']) * p90_dir
                p90_idx = i
                break
        
        if not p90_found:
            skip_p90 += 1
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
            skip_ds += 1
            continue
        
        # Entry
        is_short = (p90_dir == 1)
        entry_price = ds_bar['close']
        
        # Validate
        if is_short:
            if activation >= entry_price or kill_switch <= entry_price:
                continue
        else:
            if activation <= entry_price or kill_switch >= entry_price:
                continue
        
        # Simulate
        pnl_pips = 0.0
        result = 'UNKNOWN'
        
        for tb in trading_bars:
            if tb['time'] <= ds_bar['time']:
                continue
            if tb['est_h'] >= PARAMS['HardExitHour']:
                pnl_pips = price_to_pips(abs(entry_price - tb['close']))
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
            if is_short:
                pnl_pips = price_to_pips(entry_price - last['close'])
            else:
                pnl_pips = price_to_pips(last['close'] - entry_price)
            result = 'EOD'
        
        pnl_pips = round(pnl_pips, 1)
        total_pnl += pnl_pips
        if pnl_pips > 0: wins += 1
        elif pnl_pips < 0: losses += 1
        
        trades.append({
            'date': str(date_key), 'result': result, 'pnl': pnl_pips,
            'dir': 'SHORT' if is_short else 'LONG', 'body': round(body_pips, 1),
            'entry': entry_price, 'sl': kill_switch, 'tp': activation,
        })
    
    return {
        'trades': trades,
        'total_pnl': round(total_pnl, 1),
        'wins': wins,
        'losses': losses,
        'total': wins + losses,
        'skip_ar': skip_ar,
        'skip_p90': skip_p90,
        'skip_ds': skip_ds,
    }


def main():
    if not mt5.initialize():
        print("ERROR: MT5 init failed")
        return
    
    from_dt = datetime.utcnow() - timedelta(days=180)
    to_dt = datetime.utcnow()
    
    print("=" * 70)
    print("DMR MULTI-PAIR BACKTEST — CEREBUS P90 Thresholds")
    print(f"Data: Last 180 days M5 | DeepMult=2.0 | KillMult=2.2")
    print("=" * 70)
    
    all_results = {}
    grand_trades = 0
    grand_wins = 0
    grand_losses = 0
    grand_pnl = 0.0
    
    for pair, cfg in PAIRS.items():
        info = mt5.symbol_info(cfg['symbol'])
        if info is None:
            print(f"[FAIL] {pair}: Symbol {cfg['symbol']} not found")
            # Try .PRO
            cfg['symbol'] = cfg['symbol'].replace('.PRO', '') + '.PRO'
            info = mt5.symbol_info(cfg['symbol'])
            if info is None:
                print(f"[FAIL] {pair}: Also not found with .PRO suffix")
                continue
        
        bars = fetch_bars(cfg['symbol'], from_dt, to_dt)
        if bars is None:
            print(f"[FAIL] {pair}: No data")
            continue
        
        print(f"\n[{pair}] {cfg['symbol']} | P90={cfg['p90']}p | Bars: {len(bars)}")
        
        result = run_dmr_pair(bars, cfg)
        all_results[pair] = result
        
        t = result['total']
        wr = (result['wins'] / t * 100) if t > 0 else 0
        print(f"  Trades: {t} | W: {result['wins']} L: {result['losses']} | WR: {wr:.1f}%")
        print(f"  PnL: {result['total_pnl']:+.1f}p")
        print(f"  Skips: AR={result['skip_ar']} P90={result['skip_p90']} DS={result['skip_ds']}")
        
        grand_trades += t
        grand_wins += result['wins']
        grand_losses += result['losses']
        grand_pnl += result['total_pnl']
    
    # Grand summary
    print("\n" + "=" * 70)
    print("GRAND SUMMARY — ALL 6 PAIRS")
    print("=" * 70)
    print(f"{'Pair':<10} {'Trades':<8} {'W':<5} {'L':<5} {'WR':<8} {'PnL':<10}")
    print("-" * 46)
    for pair, res in all_results.items():
        t = res['total']
        wr = (res['wins'] / t * 100) if t > 0 else 0
        print(f"{pair:<10} {t:<8} {res['wins']:<5} {res['losses']:<5} {wr:<8.1f} {res['total_pnl']:<+10.1f}")
    
    print("-" * 46)
    gwr = (grand_wins / grand_trades * 100) if grand_trades > 0 else 0
    print(f"{'TOTAL':<10} {grand_trades:<8} {grand_wins:<5} {grand_losses:<5} {gwr:<8.1f} {grand_pnl:<+10.1f}")
    
    # Save
    outpath = r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\dmr_multi_pair.json"
    with open(outpath, 'w') as f:
        json.dump({
            'summary': {p: {k: v for k, v in r.items() if k != 'trades'} for p, r in all_results.items()},
            'grand': {'trades': grand_trades, 'wins': grand_wins, 'losses': grand_losses,
                      'pnl': round(grand_pnl, 1), 'wr': round(gwr, 1)},
            'trades': {p: r['trades'] for p, r in all_results.items()},
        }, f, indent=2, default=str)
    print(f"\nSaved to {outpath}")
    
    mt5.shutdown()

if __name__ == '__main__':
    main()
