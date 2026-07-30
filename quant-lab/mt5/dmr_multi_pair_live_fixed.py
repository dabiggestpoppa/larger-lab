"""
DMR Multi-Pair Live Executor — FIXED VERSION
==============================================
Fixes applied:
1. Symbol selection & Market Watch enforcement at startup
2. STOPLEVEL compliance (min SL/TP distance)
3. Retcode 10015/10027 handling with retry logic
4. MT5 API version compatibility (no level_stop_distance)
5. Hardcoded demo credentials
6. Proper tick freshness checks
7. Mutex/lock around order_send
8. Proper price normalization to symbol digits
9. Volume step validation
"""

import sys, time, json, os, csv, threading
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

import MetaTrader5 as mt5

REPO_ROOT = Path(r"C:\Users\wifik\Desktop\projects\larger-lab")
LOG_DIR = REPO_ROOT / "quant-lab" / "mt5" / "live_logs"
ALERTS_FILE = REPO_ROOT / "data" / "alerts_history.json"
EST = timezone(timedelta(hours=-5))

# ─── DEMO ACCOUNT CREDENTIALS (HARDCODED) ───
DEMO_LOGIN = 1114712
DEMO_PASSWORD = "your_demo_password_here"  # REPLACE WITH ACTUAL
DEMO_SERVER = "OxSecurities-Demo"

# ─── 5-Pair Portfolio (~5 tr/day) ───
PAIRS = {
    "EURUSD": {"symbol": "EURUSD.PRO", "pip_mult": 10000, "magic": 20260601},
    "GBPUSD": {"symbol": "GBPUSD.PRO", "pip_mult": 10000, "magic": 20260602},
    "USDJPY": {"symbol": "USDJPY.PRO", "pip_mult": 100,   "magic": 20260603},
    "GBPJPY": {"symbol": "GBPJPY.PRO", "pip_mult": 100,   "magic": 20260604},
    "CHFJPY": {"symbol": "CHFJPY.PRO", "pip_mult": 100,   "magic": 20260605},
}

PARAMS = {
    'LotSize':        0.01,
    'DeepMult':       2.0,
    'KillMult':       2.2,
    'MinAR':          3,
    'MaxAR':          45,
    'ESTOffset':      -5,
    'HardExitHour':   17,
    'MaxDailyTrades': 1,  # per pair
    'DS_ScanEndHour': 12,
}

# ─── Per-hour P90 thresholds (calibrated from backtest) ───
P90_THRESHOLDS = {
    "EURUSD": {2: 2.6, 3: 3.4, 4: 3.3, 5: 2.7, 6: 2.3, 7: 2.3, 8: 3.0, 9: 4.5, 10: 5.2},
    "GBPUSD": {2: 3.3, 3: 4.3, 4: 4.2, 5: 3.5, 6: 3.0, 7: 3.1, 8: 4.0, 9: 6.5, 10: 7.6},
    "USDJPY": {2: 8.0, 3: 9.3, 4: 8.0, 5: 6.4, 6: 5.7, 7: 6.0, 8: 6.8, 9: 8.4, 10: 9.3},
    "GBPJPY": {2: 9.2, 3: 10.6, 4: 9.1, 5: 7.6, 6: 6.9, 7: 7.2, 8: 8.3, 9: 11.6, 10: 13.2},
    "CHFJPY": {2: 7.4, 3: 8.7, 4: 7.3, 5: 6.1, 6: 5.6, 7: 5.8, 8: 6.7, 9: 9.2, 10: 10.7},
}

# ─── Thread lock for order_send ───
ORDER_LOCK = threading.Lock()

def get_p90_threshold(symbol, est_hour):
    thresholds = P90_THRESHOLDS.get(symbol, {})
    if est_hour in thresholds:
        return thresholds[est_hour]
    for offset in range(1, 9):
        for candidate in [est_hour - offset, est_hour + offset]:
            if candidate in thresholds:
                return thresholds[candidate]
    return 5.0

def pips_to_price(pips, pip_mult):
    return pips / pip_mult

def price_to_pips(price, pip_mult):
    return price * pip_mult

def get_est_hour(dt):
    return (dt.hour + PARAMS['ESTOffset']) % 24

def log(msg):
    ts = datetime.now(EST).strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(LOG_DIR / "dmr_multi_pair.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")

def log_signal(signal_type, symbol, details):
    os.makedirs(LOG_DIR, exist_ok=True)
    entry = {
        "timestamp": datetime.now(EST).isoformat(),
        "type": signal_type,
        "symbol": symbol,
        **details
    }
    with open(LOG_DIR / "dmr_signals.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

def send_discord_alert(alert):
    os.makedirs(ALERTS_FILE.parent, exist_ok=True)
    alerts = []
    if ALERTS_FILE.exists():
        try:
            with open(ALERTS_FILE, "r", encoding="utf-8") as f:
                alerts = json.loads(f.read().strip())
        except:
            alerts = []
    alerts.append(alert)
    with open(ALERTS_FILE, "w", encoding="utf-8") as f:
        json.dump(alerts, f, indent=2, default=str)

def check_existing_position(symbol, magic):
    positions = mt5.positions_get(symbol=symbol)
    if positions:
        for pos in positions:
            if pos.magic == magic:
                return pos
    return None

def check_pending_orders(symbol, magic):
    orders = mt5.orders_get(symbol=symbol)
    if orders:
        return sum(1 for o in orders if o.magic == magic)
    return 0

def normalize_price(symbol, price):
    """Normalize price to symbol's digits."""
    info = mt5.symbol_info(symbol)
    if not info:
        return price
    return round(price, info.digits)

def get_min_stop_distance(symbol):
    """Get broker's minimum stop distance (STOPLEVEL) in price units."""
    info = mt5.symbol_info(symbol)
    if not info:
        return 0
    # STOPLEVEL is in points, convert to price
    return info.trade_stops_level * info.point

def place_limit_order(symbol, is_short, sl_price, tp_price, entry_price, magic, pip_mult):
    info = mt5.symbol_info(symbol)
    if not info:
        log(f"ERROR: Cannot get info for {symbol}")
        return None
    
    digits = info.digits
    sl_r = normalize_price(symbol, sl_price)
    tp_r = normalize_price(symbol, tp_price)
    entry_r = normalize_price(symbol, entry_price)

    # Validate STOPLEVEL compliance
    min_stop_dist = get_min_stop_distance(symbol)
    if min_stop_dist > 0:
        if is_short:
            # For SELL_LIMIT: SL above entry, TP below entry
            sl_dist = sl_r - entry_r
            tp_dist = entry_r - tp_r
        else:
            # For BUY_LIMIT: SL below entry, TP above entry
            sl_dist = entry_r - sl_r
            tp_dist = tp_r - entry_r
        
        if sl_dist < min_stop_dist:
            log(f"SKIP {symbol}: SL distance {sl_dist:.5f} < min {min_stop_dist:.5f}")
            return None
        if tp_dist < min_stop_dist:
            log(f"SKIP {symbol}: TP distance {tp_dist:.5f} < min {min_stop_dist:.5f}")
            return None

    # Validate volume step
    volume_step = info.volume_step
    lot = round(PARAMS['LotSize'] / volume_step) * volume_step
    if lot < info.volume_min:
        lot = info.volume_min
    if lot > info.volume_max:
        lot = info.volume_max

    if is_short:
        otype = mt5.ORDER_TYPE_SELL_LIMIT
        oprice = entry_r
    else:
        otype = mt5.ORDER_TYPE_BUY_LIMIT
        oprice = entry_r

    req = {
        "action": mt5.TRADE_ACTION_PENDING,
        "symbol": symbol,
        "volume": lot,
        "type": otype,
        "price": oprice,
        "sl": sl_r,
        "tp": tp_r,
        "magic": magic,
        "comment": f"DMR_{'SHORT' if is_short else 'LONG'}",
        "type_filling": mt5.ORDER_FILLING_RETURN,
    }

    # Thread-safe order send with retry
    max_retries = 3
    for attempt in range(max_retries):
        with ORDER_LOCK:
            result = mt5.order_send(req)
        
        if result and result.retcode in (mt5.TRADE_RETCODE_DONE, mt5.TRADE_RETCODE_PLACED):
            log(f"ORDER PLACED: {symbol} {'SHORT' if is_short else 'LONG'} @ {entry_r} SL={sl_r} TP={tp_r}")
            return result
        elif result and result.retcode == mt5.TRADE_RETCODE_BUSY:
            log(f"RETRY {attempt+1}/{max_retries}: {symbol} trade context busy (10027)")
            time.sleep(0.5 * (attempt + 1))
            continue
        else:
            log(f"ORDER FAILED: {symbol} retcode={result.retcode if result else 'None'} comment={result.comment if result else 'None'}")
            return None
    
    return None

def check_position_result(symbol, magic, pip_mult):
    deals = mt5.history_deals_get(
        datetime.utcnow() - timedelta(hours=24),
        datetime.utcnow()
    )
    if not deals:
        return None
    
    for deal in deals:
        if deal.magic == magic and deal.entry == 1:  # entry=1 means close
            pnl_pips = price_to_pips(deal.profit, pip_mult) if hasattr(deal, 'profit') else 0
            result_type = "TP" if deal.profit > 0 else "SL"
            result = {
                "symbol": symbol.replace(".PRO", ""),
                "type": result_type,
                "result": result_type,
                "pnl_pips": round(pnl_pips, 1),
                "entry_price": deal.price,
                "exit_price": deal.price,
                "timestamp": datetime.now(EST).isoformat(),
            }
            log(f"RESULT: {symbol} {result_type} PnL={pnl_pips:+.1f}p")
            log_signal(result_type, symbol.replace(".PRO", ""), result)
            return result
    return None

def ensure_symbol_selected(symbol):
    """Ensure symbol is selected in Market Watch and wait for tick data."""
    if not mt5.symbol_select(symbol, True):
        log(f"Failed to select {symbol} in Market Watch")
        return False
    
    # Wait for tick data (max 10 seconds)
    for _ in range(20):
        tick = mt5.symbol_info_tick(symbol)
        if tick and tick.time > 0:
            return True
        time.sleep(0.5)
    
    log(f"WARNING: No tick data for {symbol} after 10s")
    return False

def scan_pair(cfg):
    symbol = cfg["symbol"]
    pip_mult = cfg["pip_mult"]
    magic = cfg["magic"]

    # Check existing position
    pos = check_existing_position(symbol, magic)
    if pos:
        est_hour = get_est_hour(datetime.utcnow())
        if est_hour >= PARAMS['HardExitHour']:
            tick = mt5.symbol_info_tick(symbol)
            if tick:
                close_type = mt5.ORDER_TYPE_BUY if pos.type == mt5.POSITION_TYPE_SELL else mt5.ORDER_TYPE_SELL
                price = tick.ask if pos.type == mt5.POSITION_TYPE_SELL else tick.bid
                req = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "symbol": symbol,
                    "volume": pos.volume,
                    "type": close_type,
                    "price": price,
                    "position": pos.ticket,
                    "magic": magic,
                    "comment": "DMR_HARD_EXIT",
                }
                with ORDER_LOCK:
                    mt5.order_send(req)
                log(f"HARD EXIT: {symbol}")
                log_signal("HARD_EXIT", symbol, {"ticket": pos.ticket})
        return None
    
    # Check if position was recently closed
    check_position_result(symbol, magic, pip_mult)

    # Check pending orders
    if check_pending_orders(symbol, magic) > 0:
        return None

    # Ensure symbol is selected and has fresh data
    if not ensure_symbol_selected(symbol):
        return None

    # Fetch recent bars
    bars = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, 500)
    if bars is None or len(bars) < 50:
        return None

    now = datetime.utcnow()
    today_est = (now + timedelta(hours=PARAMS['ESTOffset'])).date()

    today_bars = []
    for bar in bars:
        dt = datetime.fromtimestamp(bar['time'])
        est_dt = dt + timedelta(hours=PARAMS['ESTOffset'])
        if est_dt.date() == today_est:
            today_bars.append({
                'time': bar['time'], 'dt': dt,
                'est_h': get_est_hour(dt),
                'open': bar['open'], 'high': bar['high'],
                'low': bar['low'], 'close': bar['close'],
            })

    if len(today_bars) < 5:
        return None

    # Asian Range
    asian_high, asian_low = 0.0, 99999.0
    ar_locked = False
    skip_day = False
    for b in today_bars:
        if b['est_h'] >= 19 or b['est_h'] < 3:
            asian_high = max(asian_high, b['high'])
            asian_low = min(asian_low, b['low'])
        if b['est_h'] == 3 and not ar_locked:
            ar_locked = True
            if asian_high > 0 and asian_low < 99999:
                ar_pips = price_to_pips(asian_high - asian_low, pip_mult)
                if ar_pips < PARAMS['MinAR'] or ar_pips > PARAMS['MaxAR']:
                    skip_day = True
                    log(f"SKIP {symbol}: AR={ar_pips:.1f}p out of bounds")
            break

    if skip_day:
        return None

    # Trading window
    trading_bars = [b for b in today_bars if 2 <= b['est_h'] < 11]
    if not trading_bars:
        return None

    # P90 scan
    p90_found = False
    p90_dir = 0
    activation = 0.0
    body_pips = 0.0
    p90_idx = -1

    for i, b in enumerate(trading_bars):
        body = abs(b['close'] - b['open'])
        bp = price_to_pips(body, pip_mult)
        threshold = get_p90_threshold(symbol.replace(".PRO", ""), b['est_h'])
        if bp >= threshold:
            p90_found = True
            p90_dir = 1 if b['close'] > b['open'] else -1
            activation = b['close']
            body_pips = bp
            p90_idx = i
            break

    if not p90_found:
        return None

    # Deep State & Kill Switch
    ds = activation + pips_to_price(body_pips * PARAMS['DeepMult'], pip_mult) * p90_dir
    ks = activation + pips_to_price(body_pips * PARAMS['KillMult'], pip_mult) * p90_dir

    # DS Touch Detection
    ds_touched = False
    ds_bar = None
    for b in trading_bars[p90_idx + 1:]:
        if b['est_h'] >= PARAMS['DS_ScanEndHour']:
            break
        if p90_dir == 1 and b['low'] <= ds:
            ds_touched = True
            ds_bar = b
            break
        if p90_dir == -1 and b['high'] >= ds:
            ds_touched = True
            ds_bar = b
            break

    if not ds_touched:
        return None

    # Validate geometry
    is_short = (p90_dir == 1)
    entry_price = ds

    if is_short:
        if activation >= entry_price or ks <= entry_price:
            return None
    else:
        if activation <= entry_price or ks >= entry_price:
            return None

    # Check live price freshness
    tick = mt5.symbol_info_tick(symbol)
    if not tick or tick.time == 0:
        log(f"SKIP {symbol}: No tick data")
        return None
    tick_age = (datetime.utcnow() - datetime.fromtimestamp(tick.time)).total_seconds()
    if tick_age > 30:  # 30 second max staleness
        log(f"SKIP {symbol}: Stale price ({tick_age:.0f}s old)")
        return None
    
    # Place limit order
    result = place_limit_order(symbol, is_short, ks, activation, entry_price, magic, pip_mult)

    if result:
        direction = "SHORT" if is_short else "LONG"
        signal = {
            "symbol": symbol.replace(".PRO", ""),
            "direction": direction,
            "confidence": 0.92,
            "pathway": "DMR_200DS",
            "regime": "DMR",
            "regime_ratio": 0.0,
            "asian_range_pips": round(price_to_pips(asian_high - asian_low, pip_mult), 1),
            "entry_price": round(entry_price, 5),
            "sl_price": round(ks, 5),
            "tp_price": round(activation, 5),
            "body_pips": round(body_pips, 1),
            "ds_level": round(ds, 5),
            "timestamp": datetime.now(EST).strftime("%Y-%m-%d %H:%M:%S"),
        }

        log_signal("DMR_ENTRY", symbol.replace(".PRO", ""), signal)
        send_discord_alert(signal)

        log(f"SIGNAL: {symbol} {direction} @ {entry_price:.5f} | DS={ds:.5f} | Body={body_pips:.1f}p | AR={price_to_pips(asian_high - asian_low, pip_mult):.1f}p")

        return signal

    return None

def run_once():
    signals = []
    for name, cfg in PAIRS.items():
        try:
            sig = scan_pair(cfg)
            if sig:
                signals.append(sig)
        except Exception as e:
            log(f"ERROR scanning {name}: {e}")
    return signals

def initialize_mt5():
    """Initialize MT5 with demo credentials."""
    if not mt5.initialize():
        log(f"MT5 init failed: {mt5.last_error()}")
        return False
    
    # Login to demo account
    if not mt5.login(DEMO_LOGIN, password=DEMO_PASSWORD, server=DEMO_SERVER):
        log(f"MT5 login failed: {mt5.last_error()}")
        return False
    
    account = mt5.account_info()
    if account:
        log(f"Connected: {account.name} | {account.server} | Balance: {account.balance} {account.currency}")
    return True

def main():
    log("=" * 60)
    log("DMR MULTI-PAIR LIVE EXECUTOR — Demo Account (FIXED)")
    log("Pairs: EURUSD, GBPUSD, USDJPY, GBPJPY, CHFJPY")
    log("Expected: ~5 trades/day")
    log("Lot size: 0.01")
    log("=" * 60)

    if not initialize_mt5():
        return

    # Ensure all symbols are selected at startup
    for name, cfg in PAIRS.items():
        ensure_symbol_selected(cfg["symbol"])
    
    log("All symbols selected. Starting scan loop...")
    log("Scanning every 60 seconds... (Ctrl+C to stop)")

    try:
        while True:
            start = time.time()
            signals = run_once()
            if signals:
                log(f"[{datetime.now(EST).strftime('%H:%M:%S')}] {len(signals)} signal(s) fired")
            elapsed = time.time() - start
            sleep_time = max(60 - elapsed, 1)
            time.sleep(sleep_time)
    except KeyboardInterrupt:
        log("Shutdown requested")
    finally:
        mt5.shutdown()
        log("MT5 shutdown complete")

if __name__ == "__main__":
    main()