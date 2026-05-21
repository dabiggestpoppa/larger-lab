#!/usr/bin/env python3
"""
DMR (Deep Mean Reversion) — LIVE TRADING v2.2
- Multi-symbol support
- SQLite database for all operations logging
- P90 detection counting with proper state tracking
- Web dashboard integration via JSON state
- FIX: Proper P90 lifecycle — track found vs traded separately
- FIX: Only 1 active trade per symbol, new P90s can replace waiting ones
- FIX: Full MT5 error reporting
"""
import MetaTrader5 as mt5
import sqlite3
import json
import time
import sys
import traceback
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ── CONFIG ──────────────────────────────────────────────────────────────────
CONFIG_FILE = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_config.json")
DB_FILE = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_live.db")
STATE_FILE = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_live_state.json")

DEFAULT_CONFIG = {
    "login": 650898,
    "password": "Teflondon1718!",
    "server": "OxSecurities-Live",
    "symbols": ["EURUSD.PRO"],
    "lot_size": 0.02,
    "max_daily_trades_per_symbol": 1,
    "hard_exit_hour_est": 17,
    "deep_mult": 2.00,
    "kill_mult": 2.20,
    "magic_number": 20260520,
    "enabled": True
}

# ── DATABASE ────────────────────────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT, time TEXT, symbol TEXT, direction TEXT,
        entry_price REAL, sl_price REAL, tp_price REAL,
        lot_size REAL, ticket INTEGER, result TEXT,
        pnl_pips REAL, pnl_usd REAL, notes TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS p90_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT, time TEXT, symbol TEXT, direction TEXT,
        body_pips REAL, threshold REAL, activation REAL,
        deep_state REAL, kill_switch REAL,
        trade_triggered BOOLEAN, trade_ticket INTEGER, notes TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS system_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT, level TEXT, category TEXT,
        message TEXT, details TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS account_snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT, balance REAL, equity REAL,
        margin REAL, free_margin REAL, profit REAL,
        positions_count INTEGER
    )''')
    conn.commit()
    return conn

def log_trade(conn, row):
    c = conn.cursor()
    c.execute('''INSERT INTO trades (date, time, symbol, direction, entry_price, sl_price, tp_price, lot_size, ticket, result, pnl_pips, pnl_usd, notes)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''',
        (row.get('date'), row.get('time'), row.get('symbol'), row.get('direction'),
         row.get('entry'), row.get('sl'), row.get('tp'), row.get('lots'),
         row.get('ticket'), row.get('result'), row.get('pnl_pips'), row.get('pnl_usd'), row.get('notes')))
    conn.commit()

def log_p90(conn, row):
    c = conn.cursor()
    c.execute('''INSERT INTO p90_events (date, time, symbol, direction, body_pips, threshold, activation, deep_state, kill_switch, trade_triggered, trade_ticket, notes)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''',
        (row.get('date'), row.get('time'), row.get('symbol'), row.get('direction'),
         row.get('body_pips'), row.get('threshold'), row.get('activation'),
         row.get('deep_state'), row.get('kill_switch'), row.get('trade_triggered'),
         row.get('trade_ticket'), row.get('notes')))
    conn.commit()

def log_system(conn, level, category, message, details=None):
    c = conn.cursor()
    c.execute('''INSERT INTO system_log (timestamp, level, category, message, details)
        VALUES (?,?,?,?,?)''',
        (datetime.now(timezone.utc).isoformat(), level, category, message, details or ''))
    conn.commit()

def log_account(conn, acct_info, positions_count):
    c = conn.cursor()
    c.execute('''INSERT INTO account_snapshots (timestamp, balance, equity, margin, free_margin, profit, positions_count)
        VALUES (?,?,?,?,?,?,?)''',
        (datetime.now(timezone.utc).isoformat(), acct_info.balance, acct_info.equity,
         acct_info.margin, getattr(acct_info, 'free_margin', getattr(acct_info, 'margin_free', 0)), acct_info.profit, positions_count))
    conn.commit()

# ── CONFIG ──────────────────────────────────────────────────────────────────
def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            cfg = json.load(f)
        for k, v in DEFAULT_CONFIG.items():
            if k not in cfg:
                cfg[k] = v
        return cfg
    save_config(DEFAULT_CONFIG)
    return DEFAULT_CONFIG.copy()

def save_config(cfg):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(cfg, f, indent=2)

# ── STRATEGY ────────────────────────────────────────────────────────────────
# Pair-specific P90 thresholds: 90th percentile of 5-min body sizes (MT5, 90 days)
# Bands: [2-4AM, 4-6AM, 6-8AM, 8-10AM, 10-11AM] EST
_P90_THRESH = {
    "EURUSD.PRO": [4.1, 4.6, 4.6, 5.9, 6.2],
    "USDCHF.PRO": [2.0, 3.8, 3.8, 3.6, 4.6],
    "CHFJPY.PRO": [5.2, 8.6, 8.6, 7.2, 9.2],
    "XAUUSD.PRO": [8.4, 14.7, 15.0, 14.1, 17.4],
}

def p90_threshold(est_h, symbol=""):
    """Pair-specific P90 thresholds. Each pair has its own volatility profile."""
    t = _P90_THRESH.get(symbol, _P90_THRESH["EURUSD.PRO"])
    if est_h < 2 or est_h >= 11: return 99.0
    if est_h < 4: return t[0]
    if est_h < 6: return t[1]
    if est_h < 8: return t[2]
    if est_h < 10: return t[3]
    if est_h < 11: return t[4]
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
    """Find P90 candles we haven't seen before.
    known_p90_ids: set of 'HH:MM' strings already discovered.
    Returns list of new P90s and updated known set."""
    new_p90s = []
    for bar in today_bars:
        eh = bar['est_h']
        if eh < 2 or eh >= 11:
            continue
        body = to_pips(abs(bar['close'] - bar['open']), symbol)
        thresh = p90_threshold(eh, symbol)
        if body >= thresh:
            # Asian range filter: P90 must close OUTSIDE the Asian band
            ah = max(b['high'] for b in today_bars[:today_bars.index(bar)+1])
            al = min(b['low'] for b in today_bars[:today_bars.index(bar)+1])
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

def check_ds_touch(bars_after, direction, ds):
    for bar in bars_after:
        if direction == 'LONG' and bar['low'] <= ds:
            return True, bar
        if direction == 'SHORT' and bar['high'] >= ds:
            return True, bar
    return False, None

def place_order(cfg, direction, sl, tp, symbol):
    """Place market order with full error reporting. Returns (order_result, error_msg)."""
    sym = mt5.symbol_info(symbol)
    if not sym:
        return None, f"Symbol {symbol} not found"
    if not sym.visible:
        mt5.symbol_select(symbol, True)
        time.sleep(1)
        sym = mt5.symbol_info(symbol)
        if not sym or not sym.visible:
            return None, f"Cannot select {symbol} in Market Watch"
    tick = mt5.symbol_info_tick(symbol)
    if not tick:
        return None, f"No tick for {symbol}"
    if tick.ask <= 0 or tick.bid <= 0:
        return None, f"Invalid tick: ask={tick.ask} bid={tick.bid}"

    digits = sym.digits
    price = tick.ask if direction == 'LONG' else tick.bid

    req = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": cfg['lot_size'],
        "type": mt5.ORDER_TYPE_BUY if direction == 'LONG' else mt5.ORDER_TYPE_SELL,
        "price": round(price, digits),
        "sl": round(sl, digits),
        "tp": round(tp, digits),
        "deviation": 20,
        "magic": cfg['magic_number'],
        "comment": f"DMR_{direction}",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    res = mt5.order_send(req)
    if res is None:
        err = mt5.last_error()
        return None, f"order_send returned None, error: {err}"
    if res.retcode == mt5.TRADE_RETCODE_DONE:
        return {'ticket': res.order, 'price': price, 'sl': sl, 'tp': tp, 'direction': direction}, None

    retcode_map = {
        10004: "Requote", 10005: "Request rejected", 10006: "Request canceled",
        10010: "Invalid request", 10014: "Invalid volume", 10015: "Invalid price",
        10016: "Invalid stops", 10017: "Trade disabled", 10018: "Market closed",
        10019: "No funds", 10026: "Autotrading disabled", 10027: "Request locked",
    }
    err_name = retcode_map.get(res.retcode, f"Unknown({res.retcode})")
    return None, f"Retcode {res.retcode} ({err_name}): {res.comment}"

def get_positions(cfg, symbol=None):
    if symbol:
        positions = mt5.positions_get(symbol=symbol)
    else:
        positions = mt5.positions_get()
    if not positions:
        return []
    return [p for p in positions if p.magic == cfg['magic_number']]

def close_position(cfg, pos):
    sym = mt5.symbol_info(pos.symbol)
    tick = mt5.symbol_info_tick(pos.symbol)
    if not tick:
        return False
    price = tick.bid if pos.type == mt5.ORDER_TYPE_BUY else tick.ask
    otype = mt5.ORDER_TYPE_SELL if pos.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
    req = {
        "action": mt5.TRADE_ACTION_DEAL, "symbol": pos.symbol, "volume": pos.volume,
        "type": otype, "price": round(price, sym.digits), "deviation": 20,
        "magic": cfg['magic_number'], "comment": "DMR_HARD_EXIT",
        "type_time": mt5.ORDER_TIME_GTC, "type_filling": mt5.ORDER_FILLING_IOC,
        "position": pos.ticket
    }
    res = mt5.order_send(req)
    return res and res.retcode == mt5.TRADE_RETCODE_DONE

# ── STATE ───────────────────────────────────────────────────────────────────
def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {'today': None, 'symbols': {}}

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2, default=str)

def get_symbol_state(state, symbol):
    """Get or create symbol state, ensuring it's linked to parent state dict."""
    if 'symbols' not in state:
        state['symbols'] = {}
    if symbol not in state['symbols']:
        state['symbols'][symbol] = {
            'active_trade': False,          # Is there a live position?
            'current_ticket': None,         # Ticket of active position
            'trades_today': 0,              # Total trades placed today
            'wins': 0, 'losses': 0,
            'pnl': 0.0,
            'known_p90s': [],               # All P90 time IDs we've discovered
            'p90_count': 0,
            'last_p90_time': None,          # Time of most recent P90 found
            'last_trade_time': None,        # Time of last trade placed
        }
    return state['symbols'][symbol]

# ── MAIN ────────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("DMR LIVE TRADING v2.2")
    print("=" * 60)

    cfg = load_config()
    print(f"Account: {cfg['login']} | {cfg['server']}")
    print(f"Symbols: {cfg['symbols']} | Lot: {cfg['lot_size']}")

    conn = init_db()
    log_system(conn, 'INFO', 'SYSTEM', 'DMR Live v2.2 started', json.dumps(cfg))

    ok, err = connect_mt5(cfg)
    if not ok:
        log_system(conn, 'ERROR', 'MT5', 'Connection failed', str(err))
        print(f"MT5 connection failed: {err}")
        sys.exit(1)

    acct = mt5.account_info()
    print(f"Connected: {acct.login} | Balance: {acct.balance} | Equity: {acct.equity}")
    log_system(conn, 'INFO', 'MT5', f'Connected. Balance: {acct.balance}, Equity: {acct.equity}')

    term = mt5.terminal_info()
    if term:
        print(f"Terminal: trade_allowed={term.trade_allowed}")
        if not term.trade_allowed:
            log_system(conn, 'WARN', 'MT5', 'AutoTrading DISABLED in terminal!', '')
            print("⚠️  WARNING: AutoTrading is OFF in MT5 — orders will be rejected!")

    state = load_state()
    print(f"Scanning every 30s | Ctrl+C to stop\n")

    try:
        while True:
            try:
                cfg = load_config()
                if not cfg.get('enabled', True):
                    time.sleep(60)
                    continue

                est_h, now = est_now()
                today = now.date().isoformat()

                # Reset state for new day
                if state.get('today') != today:
                    state = {'today': today, 'symbols': {}}
                    save_state(state)
                    log_system(conn, 'INFO', 'SYSTEM', f'New trading day: {today}')
                    print(f"\n📅 New day: {today} — state reset")

                # Hard exit: close all positions at hard exit hour
                if est_h >= cfg['hard_exit_hour_est']:
                    all_positions = get_positions(cfg)
                    for pos in all_positions:
                        if close_position(cfg, pos):
                            log_system(conn, 'INFO', 'TRADE', f'Hard exit: closed ticket {pos.ticket} PnL: {pos.profit}')
                            ss = get_symbol_state(state, pos.symbol)
                            ss['active_trade'] = False
                            ss['current_ticket'] = None
                            ss['trades_today'] = ss.get('trades_today', 0) + 1
                            if pos.profit > 0:
                                ss['wins'] = ss.get('wins', 0) + 1
                            else:
                                ss['losses'] = ss.get('losses', 0) + 1
                            ss['pnl'] = ss.get('pnl', 0.0) + pos.profit
                            log_trade(conn, {
                                'date': today, 'time': now.isoformat(), 'symbol': pos.symbol,
                                'direction': 'EXIT', 'entry': 0, 'sl': 0, 'tp': 0,
                                'lots': pos.volume, 'ticket': pos.ticket,
                                'result': 'W' if pos.profit > 0 else 'L',
                                'pnl_pips': 0, 'pnl_usd': round(pos.profit, 2),
                                'notes': f'Hard exit {cfg["hard_exit_hour_est"]}PM EST'
                            })
                    if all_positions:
                        save_state(state)
                    time.sleep(60)
                    continue

                # Only scan during P90 window (2-11 AM EST)
                if est_h < 2 or est_h >= 11:
                    time.sleep(60)
                    continue

                # Account snapshot every 15 min
                if now.minute % 15 == 0 and now.second < 30:
                    acct = mt5.account_info()
                    if acct:
                        pos_count = len(get_positions(cfg))
                        log_account(conn, acct, pos_count)

                # Process each symbol
                for symbol in cfg['symbols']:
                    ss = get_symbol_state(state, symbol)

                    # Check existing position
                    positions = get_positions(cfg, symbol)
                    if positions:
                        p = positions[0]
                        if ss.get('current_ticket') != p.ticket:
                            ss['current_ticket'] = p.ticket
                            ss['active_trade'] = True
                        continue  # Already in a trade, skip to next symbol
                    else:
                        # Position closed (TP/SL hit or manual close)
                        if ss.get('active_trade'):
                            ss['active_trade'] = False
                            ss['current_ticket'] = None
                            save_state(state)

                    # Skip if max daily trades reached
                    if ss.get('trades_today', 0) >= cfg['max_daily_trades_per_symbol']:
                        continue

                    # Get bars and find NEW P90s
                    bars = get_today_bars(symbol)
                    if not bars:
                        continue

                    today_bars = [b for b in bars if b['date'] == now.date()]
                    known = set(ss.get('known_p90s', []))
                    new_p90s, known = find_new_p90s(today_bars, symbol, known)

                    # Always update known P90s in state
                    ss['known_p90s'] = sorted(known)
                    ss['p90_count'] = len(known)

                    if not new_p90s:
                        # No new P90s — just log status occasionally
                        if now.second < 30:
                            print(f"  {now.strftime('%H:%M')} {symbol} — scanning | P90s: {len(known)} | Trades: {ss.get('trades_today', 0)} | PnL: ${round(ss.get('pnl', 0), 2)}")
                        continue

                    # Process each NEW P90
                    for direction, p90_bar, body_pips, thresh in new_p90s:
                        p90_time_str = p90_bar['time'].strftime('%H:%M')
                        ss['last_p90_time'] = p90_time_str

                        activation = p90_bar['close']
                        ds = activation + to_price(body_pips * cfg['deep_mult'], symbol) * (1 if direction == 'LONG' else -1)
                        ks = activation + to_price(body_pips * cfg['kill_mult'], symbol) * (1 if direction == 'LONG' else -1)
                        rev = 'SHORT' if direction == 'LONG' else 'LONG'

                        print(f"\n  🔔 P90: {symbol} {direction} @ {p90_time_str} EST | Body: {body_pips:.1f}p | DS: {ds} | Trade: {rev}")

                        # Log P90 event
                        log_p90(conn, {
                            'date': today, 'time': p90_bar['time'].isoformat(),
                            'symbol': symbol, 'direction': direction,
                            'body_pips': body_pips, 'threshold': thresh,
                            'activation': activation, 'deep_state': ds,
                            'kill_switch': ks, 'trade_triggered': False,
                            'trade_ticket': None, 'notes': f'Rev: {rev}'
                        })

                        # Check if DS has been touched by bars after this P90
                        post_bars = [b for b in today_bars if b['time'] > p90_bar['time'] and b['est_h'] < 12]
                        touched, tb = check_ds_touch(post_bars, direction, ds)

                        if not touched:
                            print(f"    ⏳ DS not touched yet — waiting...")
                            continue

                        # DS touched — place market order
                        print(f"    ✅ DS touched @ {tb['time'].strftime('%H:%M')} — Placing {rev} market order...")

                        order, err_msg = place_order(cfg, rev, ks, activation, symbol)
                        if order:
                            ss['active_trade'] = True
                            ss['current_ticket'] = order['ticket']
                            ss['trades_today'] = ss.get('trades_today', 0) + 1
                            ss['last_trade_time'] = now.strftime('%H:%M')

                            log_system(conn, 'INFO', 'TRADE',
                                f'{symbol} {rev} LIVE @ {order["price"]} SL:{order["sl"]} TP:{order["tp"]} Ticket:{order["ticket"]}')
                            log_trade(conn, {
                                'date': today, 'time': now.isoformat(), 'symbol': symbol,
                                'direction': rev, 'entry': order['price'], 'sl': order['sl'],
                                'tp': order['tp'], 'lots': cfg['lot_size'], 'ticket': order['ticket'],
                                'result': 'OPEN', 'pnl_pips': 0, 'pnl_usd': 0,
                                'notes': f'P90@{p90_time_str}_DS@{tb["time"].strftime("%H:%M")}'
                            })
                            print(f"    ✅✅ TRADE LIVE: {symbol} {rev} {cfg['lot_size']} lots | Ticket: {order['ticket']} | Price: {order['price']}")
                        else:
                            log_system(conn, 'ERROR', 'TRADE', f'{symbol} order FAILED: {err_msg}', '')
                            print(f"    ❌ ORDER FAILED: {err_msg}")
                            # Don't increment trades_today — allow next P90 to try

                save_state(state)
                time.sleep(30)

            except KeyboardInterrupt:
                print("\nStopped by user")
                break
            except Exception as e:
                err = traceback.format_exc()
                log_system(conn, 'ERROR', 'RUNTIME', str(e), err)
                print(f"Error: {e}")
                time.sleep(30)
    finally:
        state = load_state()
        print(f"\n{'='*60}")
        print("DAILY SUMMARY")
        print(f"{'='*60}")
        for sym in cfg['symbols']:
            ss = get_symbol_state(state, sym)
            print(f"  {sym}: P90s: {ss.get('p90_count', 0)} | Trades: {ss.get('trades_today', 0)} | W: {ss.get('wins', 0)} | L: {ss.get('losses', 0)} | PnL: ${round(ss.get('pnl', 0), 2)}")
        log_system(conn, 'INFO', 'SYSTEM', 'DMR Live v2.2 stopped')
        mt5.shutdown()
        conn.close()

if __name__ == "__main__":
    main()
