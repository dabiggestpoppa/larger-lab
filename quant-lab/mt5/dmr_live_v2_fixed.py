#!/usr/bin/env python3
"""
DMR Live v2.3 - PAIR-SPECIFIC P90 THRESHOLDS
This is a clean copy with verified pair-specific thresholds.
"""
import MetaTrader5 as mt5
import sqlite3
import json
import os
import time
from datetime import datetime, timezone, timedelta

# === PAIR-SPECIFIC P90 THRESHOLDS ===
# Calculated from MT5 90th percentile of 5-min candle body sizes (90 days)
# Bands: [2-4AM, 4-6AM, 6-8AM, 8-10AM, 10-11AM] EST
P90_THRESHOLDS = {
    "EURUSD.PRO": [4.1, 4.6, 4.6, 5.9, 6.2],
    "USDCHF.PRO": [2.0, 3.8, 3.8, 3.6, 4.6],
    "CHFJPY.PRO": [5.2, 8.6, 8.6, 7.2, 9.2],
    "XAUUSD.PRO": [8.4, 14.7, 15.0, 14.1, 17.4],
}

def p90_threshold(est_h, symbol=""):
    thresholds = P90_THRESHOLDS.get(symbol, P90_THRESHOLDS.get("EURUSD.PRO"))
    if est_h < 2 or est_h >= 11: return 99.0
    if est_h < 4: return thresholds[0]
    if est_h < 6: return thresholds[1]
    if est_h < 8: return thresholds[2]
    if est_h < 10: return thresholds[3]
    if est_h < 11: return thresholds[4]
    return 99.0

def to_pips(price_diff, symbol=""):
    if "JPY" in symbol.upper(): return price_diff * 100.0
    if "XAU" in symbol.upper(): return price_diff * 10.0
    return price_diff * 10000.0

def to_price(pips, symbol=""):
    if "JPY" in symbol.upper(): return pips / 100.0
    if "XAU" in symbol.upper(): return pips / 10.0
    return pips / 10000.0

def est_now():
    utc_now = datetime.now(timezone.utc)
    est_h = (utc_now.hour - 5 + 24) % 24
    return est_h, utc_now

def connect_mt5(cfg):
    mt5.initialize()
    auth = mt5.login(login=cfg['login'], password=cfg['password'], server=cfg['server'])
    if not auth:
        err = mt5.last_error()
        mt5.shutdown()
        return False, err
    return True, None

def get_today_bars(symbol, count=500):
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, count)
    if rates is None or len(rates) == 0:
        return []
    bars = []
    for r in rates:
        ts = datetime.fromtimestamp(r['time'], tz=timezone.utc)
        est_h = (ts.hour - 5 + 24) % 24
        bars.append({
            'time': ts, 'est_h': est_h, 'date': ts.date(),
            'open': r['open'], 'high': r['high'], 'low': r['low'], 'close': r['close']
        })
    return bars

def find_new_p90s(today_bars, symbol, known_p90_ids):
    new_p90s = []
    for i, bar in enumerate(today_bars):
        eh = bar['est_h']
        if eh < 2 or eh >= 11:
            continue
        body = to_pips(abs(bar['close'] - bar['open']), symbol)
        thresh = p90_threshold(eh, symbol)
        if body >= thresh:
            ah = max(b['high'] for b in today_bars[:i+1])
            al = min(b['low'] for b in today_bars[:i+1])
            direction = 'LONG' if bar['close'] > bar['open'] else 'SHORT'
            if direction == 'LONG' and bar['close'] <= ah:
                continue
            if direction == 'SHORT' and bar['close'] >= al:
                continue
            bar_id = bar['time'].strftime('%H:%M')
            if bar_id not in known_p90_ids:
                new_p90s.append((direction, bar, body, thresh))
                known_p90_ids.add(bar_id)
    return new_p90s, known_p90_ids

# === MAIN ===
if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    cfg_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dmr_config.json')
    with open(cfg_file) as f:
        cfg = json.load(f)
    
    print(f"[DMR v2.3] Starting with pair-specific thresholds")
    print(f"[DMR v2.3] Thresholds: {json.dumps(P90_THRESHOLDS, indent=2)}")
    
    ok, err = connect_mt5(cfg)
    if not ok:
        print(f"[DMR v2.3] MT5 connect failed: {err}")
        sys.exit(1)
    
    acct = mt5.account_info()
    print(f"[DMR v2.3] Connected. Balance: {acct.balance}")
    
    # Simple test: scan each symbol for P90s
    for symbol in cfg['symbols']:
        bars = get_today_bars(symbol)
        if not bars:
            print(f"[DMR v2.3] {symbol}: no bars")
            continue
        today_bars = [b for b in bars if b['est_h'] >= 2 and b['est_h'] < 11]
        known = set()
        new_p90s, known = find_new_p90s(today_bars, symbol, known)
        print(f"[DMR v2.3] {symbol}: {len(new_p90s)} P90s found")
        for direction, bar, body, thresh in new_p90s[-3:]:
            print(f"  {bar['time'].strftime('%H:%M')} {direction} body={body:.1f}p thresh={thresh:.1f}p")
    
    mt5.shutdown()
    print("[DMR v2.3] Test complete")
