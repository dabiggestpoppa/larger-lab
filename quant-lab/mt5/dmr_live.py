#!/usr/bin/env python3
"""
DMR (Deep Mean Reversion) — LIVE TRADING
Account: 650898 | Server: OxSecurities-Live
Symbol: EURUSD.PRO | Lot: 0.01
"""
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
from pathlib import Path
import json
import time
import sys
import csv

LOGIN = 650898
PASSWORD = "Teflondon1718!"
SERVER = "OxSecurities-Live"
SYMBOL = "EURUSD.PRO"
LOT_SIZE = 0.01
MAGIC_NUMBER = 20260520
HARD_EXIT_EST = 17

RESULTS_DIR = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5")
LOG_FILE = RESULTS_DIR / "dmr_live_log.csv"
STATE_FILE = RESULTS_DIR / "dmr_live_state.json"

def p90_threshold(est_h):
    if est_h < 2 or est_h >= 11: return 99.0
    if est_h < 4: return 4.1
    if est_h < 6: return 4.6
    if est_h < 8: return 4.6
    if est_h < 10: return 5.9
    if est_h < 11: return 6.2
    return 99.0

def to_pips(price_diff):
    return price_diff * 10000.0

def to_price(pips):
    return pips / 10000.0

def est_now():
    utc_now = datetime.now(timezone.utc)
    est_h = (utc_now.hour - 5 + 24) % 24
    return est_h, utc_now

def connect():
    if not mt5.initialize():
        print("MT5 init failed:", mt5.last_error())
        return False
    auth = mt5.login(login=LOGIN, password=PASSWORD, server=SERVER)
    if not auth:
        print("Login failed:", mt5.last_error())
        mt5.shutdown()
        return False
    acct = mt5.account_info()
    print("Connected:", acct.login, "|", acct.server, "| Balance:", acct.balance)
    sym = mt5.symbol_info(SYMBOL)
    if not sym:
        print("Symbol", SYMBOL, "not found")
        return False
    if not sym.visible:
        mt5.symbol_select(SYMBOL, True)
        time.sleep(0.5)
    tick = mt5.symbol_info_tick(SYMBOL)
    print("Symbol:", SYMBOL, "| Bid:", tick.bid, "| Ask:", tick.ask, "| Spread:", round(to_pips(tick.ask-tick.bid),1), "pips")
    return True

def get_today_bars(count=500):
    rates = mt5.copy_rates_from_pos(SYMBOL, mt5.TIMEFRAME_M5, 0, count)
    if not rates: return []
    bars = []
    for r in rates:
        ts = datetime.fromtimestamp(r['time'], tz=timezone.utc)
        bars.append({'time': ts, 'est_h': (ts.hour - 5 + 24) % 24, 'date': ts.date(),
                     'open': r['open'], 'high': r['high'], 'low': r['low'], 'close': r['close']})
    return bars

def find_p90(bars, already_found_times=None):
    """Find P90 candles. Returns list of all P90s found (not just first)."""
    if already_found_times is None:
        already_found_times = set()
    results = []
    for bar in bars:
        eh = bar['est_h']
        if eh < 2 or eh >= 11: continue
        body = to_pips(abs(bar['close'] - bar['open']))
        if body >= p90_threshold(eh):
            bar_time_str = bar['time'].strftime('%H:%M')
            if bar_time_str not in already_found_times:
                direction = 'LONG' if bar['close'] > bar['open'] else 'SHORT'
                results.append((direction, bar))
                already_found_times.add(bar_time_str)
    return results, already_found_times

def check_ds_touch(bars_after, direction, ds):
    for bar in bars_after:
        if direction == 'LONG' and bar['low'] <= ds: return True, bar
        if direction == 'SHORT' and bar['high'] >= ds: return True, bar
    return False, None

def place_order(direction, sl, tp):
    sym = mt5.symbol_info(SYMBOL)
    digits = sym.digits
    tick = mt5.symbol_info_tick(SYMBOL)
    price = tick.ask if direction == 'LONG' else tick.bid
    req = {
        "action": mt5.TRADE_ACTION_DEAL, "symbol": SYMBOL, "volume": LOT_SIZE,
        "type": mt5.ORDER_TYPE_BUY if direction == 'LONG' else mt5.ORDER_TYPE_SELL,
        "price": round(price, digits), "sl": round(sl, digits), "tp": round(tp, digits),
        "deviation": 10, "magic": MAGIC_NUMBER, "comment": "DMR_LIVE_" + direction,
        "type_time": mt5.ORDER_TIME_GTC, "type_filling": mt5.ORDER_FILLING_IOC,
    }
    res = mt5.order_send(req)
    if res and res.retcode == mt5.TRADE_RETCODE_DONE:
        print("OK:", direction, LOT_SIZE, "lots @", price, "| SL:", sl, "| TP:", tp, "| Ticket:", res.order)
        return {'ticket': res.order, 'price': price, 'sl': sl, 'tp': tp, 'direction': direction}
    else:
        print("FAIL:", res.retcode if res else "None")
        return None

def check_position():
    positions = mt5.positions_get(symbol=SYMBOL)
    if positions:
        for p in positions:
            if p.magic == MAGIC_NUMBER: return p
    return None

def close_position(pos):
    sym = mt5.symbol_info(SYMBOL)
    tick = mt5.symbol_info_tick(SYMBOL)
    price = tick.bid if pos.type == mt5.ORDER_TYPE_BUY else tick.ask
    otype = mt5.ORDER_TYPE_SELL if pos.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
    req = {"action": mt5.TRADE_ACTION_DEAL, "symbol": SYMBOL, "volume": pos.volume,
           "type": otype, "price": round(price, sym.digits), "deviation": 10,
           "magic": MAGIC_NUMBER, "comment": "DMR_HARD_EXIT", "type_time": mt5.ORDER_TIME_GTC,
           "type_filling": mt5.ORDER_FILLING_IOC, "position": pos.ticket}
    res = mt5.order_send(req)
    if res and res.retcode == mt5.TRADE_RETCODE_DONE:
        print("Closed ticket", pos.ticket, "| PnL:", round(pos.profit, 2))
        return True
    return False

def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE) as f: return json.load(f)
    return {'today': None, 'trade_placed': False, 'total_trades': 0, 'wins': 0, 'losses': 0, 'pnl': 0.0, 'found_p90s': []}

def save_state(s):
    with open(STATE_FILE, 'w') as f: json.dump(s, f, indent=2, default=str)

def log_trade(row):
    exists = LOG_FILE.exists()
    with open(LOG_FILE, 'a', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['date','time','direction','entry','sl','tp','lots','ticket','result','pnl_usd','notes'])
        if not exists: w.writeheader()
        w.writerow(row)

def main():
    print("="*60)
    print("DMR LIVE TRADING")
    print("Account:", LOGIN, "|", SERVER, "|", SYMBOL, "| Lot:", LOT_SIZE)
    print("="*60)
    if not connect(): sys.exit(1)
    state = load_state()
    found_p90s = set(state.get('found_p90s', []))
    print("State:", state)
    print("Already found P90s:", found_p90s)
    print("Scanning every 30s | Ctrl+C to stop")
    print("")
    try:
        while True:
            try:
                est_h, now = est_now()
                today = now.date().isoformat()
                if state.get('today') != today:
                    state = {'today': today, 'trade_placed': False, 'total_trades': state.get('total_trades',0),
                             'wins': state.get('wins',0), 'losses': state.get('losses',0), 'pnl': state.get('pnl',0.0),
                             'found_p90s': []}
                    found_p90s = set()
                    save_state(state)

                # Hard exit at 5PM EST
                if est_h >= HARD_EXIT_EST and state.get('trade_placed'):
                    pos = check_position()
                    if pos:
                        print("Hard exit", est_h, "EST — closing position")
                        if close_position(pos):
                            state['total_trades'] += 1
                            if pos.profit > 0: state['wins'] += 1
                            else: state['losses'] += 1
                            state['pnl'] += pos.profit
                            state['trade_placed'] = False
                            state['found_p90s'] = list(found_p90s)
                            save_state(state)
                            log_trade({'date':today,'time':now.isoformat(),'direction':'EXIT','entry':0,'sl':0,'tp':0,
                                       'lots':pos.volume,'ticket':pos.ticket,'result':'W' if pos.profit>0 else 'L',
                                       'pnl_usd':round(pos.profit,2),'notes':'Hard exit 5PM EST'})
                    time.sleep(60); continue

                # Only scan during P90 window (2-11 AM EST)
                if est_h < 2 or est_h >= 11:
                    if est_h >= 11 and not state.get('trade_placed') and found_p90s:
                        print(now.strftime('%H:%M'), "EST — P90 window closed. Found:", found_p90s, "No trades today.")
                    time.sleep(60); continue

                # Check existing position
                pos = check_position()
                if pos:
                    print(now.strftime('%H:%M'), "EST — Position open (ticket:", pos.ticket, "PnL:", round(pos.profit,2), ")")
                    time.sleep(30); continue

                # Already traded today
                if state.get('trade_placed'):
                    time.sleep(30); continue

                # Get today's bars and scan for P90
                bars = get_today_bars()
                if not bars: time.sleep(30); continue
                today_bars = [b for b in bars if b['date'] == now.date()]
                p90_results, found_p90s = find_p90(today_bars, found_p90s)
                
                if not p90_results:
                    print(now.strftime('%H:%M'), "EST — scanning, no new P90 yet | found so far:", found_p90s)
                    time.sleep(30); continue

                # Process the latest P90 found
                direction, p90 = p90_results[-1]
                print("")
                print("*** P90 SIGNAL:", direction, "@", p90['time'].strftime('%H:%M'), "EST ***")
                activation = p90['close']
                body = to_pips(abs(p90['close'] - p90['open']))
                ds = activation + to_price(body * 2.00) * (1 if direction == 'LONG' else -1)
                ks = activation + to_price(body * 2.20) * (1 if direction == 'LONG' else -1)
                rev = 'SHORT' if direction == 'LONG' else 'LONG'
                print("  Activation:", activation, "| DS:", ds, "| KS:", ks, "| Rev:", rev)

                # Wait for Deep State touch
                post = [b for b in today_bars if b['time'] > p90['time'] and b['est_h'] < 12]
                touched, tb = check_ds_touch(post, direction, ds)
                if not touched:
                    print("  Waiting for Deep State touch...")
                    time.sleep(30); continue

                print("  DS touched @", tb['time'].strftime('%H:%M'), "- Placing", rev, "order")
                order = place_order(rev, ks, activation)
                if order:
                    state['trade_placed'] = True
                    state['found_p90s'] = list(found_p90s)
                    save_state(state)
                    log_trade({'date':today,'time':now.isoformat(),'direction':rev,'entry':order['price'],
                               'sl':order['sl'],'tp':order['tp'],'lots':LOT_SIZE,'ticket':order['ticket'],
                               'result':'OPEN','pnl_usd':0,'notes':"P90@"+p90['time'].strftime('%H:%M')+"_DS@"+tb['time'].strftime('%H:%M')})
                    print("  *** TRADE LIVE:", rev, LOT_SIZE, "lots | Ticket:", order['ticket'], "***")
                print("")
                time.sleep(30)
            except KeyboardInterrupt:
                print("Stopped by user"); break
            except Exception as e:
                print("Error:", e); import traceback; traceback.print_exc(); time.sleep(30)
    finally:
        state = load_state()
        print("")
        print("FINAL: Trades:", state['total_trades'], "| W:", state['wins'], "| L:", state['losses'], "| PnL:", round(state['pnl'], 2))
        mt5.shutdown()

if __name__ == "__main__":
    main()
