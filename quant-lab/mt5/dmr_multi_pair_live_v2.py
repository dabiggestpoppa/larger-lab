"""
DMR Multi-Pair Live Executor — Demo Account
==============================================
10 pairs: NZDCHF, GBPJPY, EURGBP, AUDUSD, USDCAD, EURAUD, GBPNZD, EURUSD, USDCHF, CHFJPY
~5 trades/day combined
Sends signals to data/alerts_history.json for Discord bot

Strategy: Limit order at 200% Deep State, TP at -50% AR (mean reversion), SL at P90 SL (shared boundary)
Per-hour P90 calibration from each pair's own data
"""
import sys, time, json, os, csv, numpy as np
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

import MetaTrader5 as mt5

REPO_ROOT = Path(r"C:\Users\wifik\Desktop\projects\larger-lab")
LOG_DIR = REPO_ROOT / "quant-lab" / "mt5" / "live_logs"
ALERTS_FILE = REPO_ROOT / "data" / "alerts_history.json"
EST = timezone(timedelta(hours=-5))

# ─── Daily Stats Tracker ───
STATS_FILE = REPO_ROOT / "quant-lab" / "mt5" / "live_logs" / "dmr_daily_stats.json"

daily_stats = {
    "date": None,
    "signals_detected": 0,
    "orders_placed": 0,
    "tp_hits": 0,
    "sl_hits": 0,
    "skipped_stale": 0,
}

# Track which windows have been signaled to prevent spam
# Key: "SYMBOL|window_start|date" -> True
signaled_windows = {}

def load_signaled_windows():
    global signaled_windows
    today = datetime.now(EST).date().isoformat()
    sw_file = LOG_DIR / "signaled_windows.json"
    if sw_file.exists():
        try:
            with open(sw_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data.get("date") == today:
                    signaled_windows = data.get("windows", {})
        except:
            pass

def save_signaled_windows():
    os.makedirs(LOG_DIR, exist_ok=True)
    sw_file = LOG_DIR / "signaled_windows.json"
    with open(sw_file, "w", encoding="utf-8") as f:
        json.dump({"date": datetime.now(EST).date().isoformat(), "windows": signaled_windows}, f)

def is_window_signaled(symbol, window_start, date_str):
    key = f"{symbol}|{window_start}|{date_str}"
    return key in signaled_windows

def mark_window_signaled(symbol, window_start, date_str):
    key = f"{symbol}|{window_start}|{date_str}"
    signaled_windows[key] = True
    save_signaled_windows()

def load_stats():
    global daily_stats
    today = datetime.now(EST).date().isoformat()
    if STATS_FILE.exists():
        try:
            with open(STATS_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                if saved.get("date") == today:
                    daily_stats = saved
        except:
            pass
    daily_stats["date"] = today

def save_stats():
    os.makedirs(STATS_FILE.parent, exist_ok=True)
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(daily_stats, f, indent=2)

# Track already-reported deal tickets to avoid duplicate alerts
reported_deals = set()

def check_closed_trades():
    """Check for TP/SL hits on DMR positions. Only alerts ONCE per deal."""
    global reported_deals
    deals = mt5.history_deals_get(timedelta(days=1))
    if deals is None:
        return
    for d in deals:
        if d.magic and 20260600 <= d.magic <= 20260610:
            if d.reason == mt5.DEAL_REASON_CLIENT and d.profit != 0:
                # Only report each deal ticket once
                if d.ticket in reported_deals:
                    continue
                reported_deals.add(d.ticket)
                
                # Get position details
                symbol_name = d.symbol.replace(".PRO", "")
                pnl_pips = price_to_pips(d.profit, 10000)  # Approximate
                
                if d.profit > 0:
                    daily_stats["tp_hits"] += 1
                    log_signal("TP_HIT", symbol_name, {
                        "profit": round(d.profit, 2),
                        "ticket": d.ticket,
                        "pnl_pips": round(pnl_pips, 1),
                        "entry_price": d.price,
                    })
                    send_discord_alert({"type": "TP_HIT", "symbol": symbol_name, "profit": round(d.profit, 2), "pnl_pips": round(pnl_pips, 1)})
                    log(f"TP HIT: {symbol_name} +${d.profit:.2f}")
                else:
                    daily_stats["sl_hits"] += 1
                    log_signal("SL_HIT", symbol_name, {
                        "profit": round(d.profit, 2),
                        "ticket": d.ticket,
                        "pnl_pips": round(pnl_pips, 1),
                        "entry_price": d.price,
                    })
                    send_discord_alert({"type": "SL_HIT", "symbol": symbol_name, "profit": round(d.profit, 2), "pnl_pips": round(pnl_pips, 1)})
                    log(f"SL HIT: {symbol_name} ${d.profit:.2f}")

def cancel_stale_orders():
    """Cancel pending orders outside trading hours or from previous day."""
    est_hour = get_est_hour(datetime.utcnow())
    if est_hour < 17:  # Still in trading session, don't cancel
        return
    
    orders = mt5.orders_get()
    if orders:
        for o in orders:
            if o.magic and 20260600 <= o.magic <= 20260610:
                result = mt5.order_send({
                    "action": mt5.TRADE_ACTION_REMOVE,
                    "order": o.ticket,
                    "magic": o.magic,
                })
                if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                    log(f"HARD EXIT: Cancelled stale order {o.symbol} ticket={o.ticket}")
                else:
                    log(f"HARD EXIT FAILED: {o.symbol} ticket={o.ticket} retcode={result.retcode if result else 'None'}")

# ─── Top 10 Pairs Ranked by PF x WR (v2 backtest) ───
PAIRS = {
    "NZDCHF": {"symbol": "NZDCHF.PRO", "pip_mult": 10000, "magic": 20260601},
    "GBPJPY": {"symbol": "GBPJPY.PRO", "pip_mult": 100,   "magic": 20260602},
    "EURGBP": {"symbol": "EURGBP.PRO", "pip_mult": 10000, "magic": 20260603},
    "AUDUSD": {"symbol": "AUDUSD.PRO", "pip_mult": 10000, "magic": 20260604},
    "USDCAD": {"symbol": "USDCAD.PRO", "pip_mult": 10000, "magic": 20260605},
    "EURAUD": {"symbol": "EURAUD.PRO", "pip_mult": 10000, "magic": 20260606},
    "GBPNZD": {"symbol": "GBPNZD.PRO", "pip_mult": 10000, "magic": 20260607},
    "EURUSD": {"symbol": "EURUSD.PRO", "pip_mult": 10000, "magic": 20260608},
    "USDCHF": {"symbol": "USDCHF.PRO", "pip_mult": 10000, "magic": 20260609},
    "CHFJPY": {"symbol": "CHFJPY.PRO", "pip_mult": 100,   "magic": 20260610},
}

PARAMS = {
    'LotSize':        0.01,
    'DeepMult':       2.0,
    'KillMult':       2.2,
    'ESTOffset':      -5,
    'HardExitHour':   17,
    'MaxDailyTrades': 999,  # No cap — multi-entry per window
    'DS_ScanEndHour': 12,
}

# ─── 2-Hour P90 Windows (from manual/backtest) ───
P90_WINDOWS = [
    (2, 4, 4.1),   # 2-4 AM >= 4.1 pips
    (4, 6, 4.6),   # 4-6 AM >= 4.6 pips
    (6, 8, 4.6),   # 6-8 AM >= 4.6 pips
    (8, 10, 5.9),  # 8-10 AM >= 5.9 pips
    (10, 11, 6.2), # 10-11 AM >= 6.2 pips
]


def get_p90_threshold(est_hour):
    """Get P90 threshold for a specific hour using 2-hour windows."""
    for start, end, threshold in P90_WINDOWS:
        if start <= est_hour < end:
            return threshold
    return 999.0  # No P90 allowed outside windows


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
    """Log signal to JSONL for Discord bot pickup."""
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
    """Write to alerts_history.json for Discord bot."""
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


def place_limit_order(symbol, is_short, sl_price, tp_price, entry_price, magic, pip_mult):
    info = mt5.symbol_info(symbol)
    if not info:
        log(f"ERROR: Cannot get info for {symbol}")
        return None
    digits = info.digits
    sl_r = round(sl_price, digits)
    tp_r = round(tp_price, digits)
    entry_r = round(entry_price, digits)

    if is_short:
        otype = mt5.ORDER_TYPE_SELL_LIMIT
        oprice = entry_r
    else:
        otype = mt5.ORDER_TYPE_BUY_LIMIT
        oprice = entry_r

    # Get spread in price units for SL adjustment
    tick = mt5.symbol_info_tick(symbol)
    spread_pips = (tick.ask - tick.bid) * pip_mult if tick else 0
    spread_buffer = max(0.00005, spread_pips / pip_mult)  # At least 0.5 pip spread buffer

    # Ensure SL/TP meet broker minimum distance (2 pips minimum + spread)
    if pip_mult >= 10000:
        pip_size = 0.0001  # FX majors
    elif pip_mult >= 100:
        pip_size = 0.01    # JPY pairs
    else:
        pip_size = 1.0     # Indices
    min_distance = (2 + spread_pips) * pip_size  # 2 pips + spread buffer
    
    if is_short:
        sl_dist = sl_r - entry_r
        tp_dist = entry_r - tp_r
        if sl_dist < min_distance:
            log(f"ADJUST {symbol}: SL {sl_r} too tight ({sl_dist/pip_size:.1f}p), adjusting to {round(entry_r + min_distance, digits)}")
            sl_r = round(entry_r + min_distance, digits)
        if tp_dist < min_distance:
            log(f"ADJUST {symbol}: TP {tp_r} too tight ({tp_dist/pip_size:.1f}p), adjusting to {round(entry_r - min_distance, digits)}")
            tp_r = round(entry_r - min_distance, digits)
    else:
        sl_dist = entry_r - sl_r
        tp_dist = tp_r - entry_r
        if sl_dist < min_distance:
            log(f"ADJUST {symbol}: SL {sl_r} too tight ({sl_dist/pip_size:.1f}p), adjusting to {round(entry_r - min_distance, digits)}")
            sl_r = round(entry_r - min_distance, digits)
        if tp_dist < min_distance:
            log(f"ADJUST {symbol}: TP {tp_r} too tight ({tp_dist/pip_size:.1f}p), adjusting to {round(entry_r + min_distance, digits)}")
            tp_r = round(entry_r + min_distance, digits)
    
    # Verify entry is within reasonable distance of current market
    # (reject stale signals from when market was closed)
    tick = mt5.symbol_info_tick(symbol)
    if tick:
        max_entry_distance = 50 * pip_size  # 50 pips max
        if abs(entry_r - tick.ask) > max_entry_distance:
            log(f"SKIP {symbol}: Entry {entry_r} too far from market {tick.ask} ({abs(entry_r - tick.ask)/pip_size:.0f}p)")
            return None
    
    req = {
        "action": mt5.TRADE_ACTION_PENDING,
        "symbol": symbol,
        "volume": PARAMS['LotSize'],
        "type": otype,
        "price": oprice,
        "sl": sl_r,
        "tp": tp_r,
        "magic": magic,
        "comment": f"DMR_{'SHORT' if is_short else 'LONG'}",
        "type_filling": mt5.ORDER_FILLING_RETURN,
    }

    result = mt5.order_send(req)
    if result and result.retcode in (mt5.TRADE_RETCODE_DONE, mt5.TRADE_RETCODE_PLACED):
        daily_stats["orders_placed"] += 1
        log(f"ORDER PLACED: {symbol} {'SHORT' if is_short else 'LONG'} @ {entry_r} SL={sl_r} TP={tp_r}")
        return result
    else:
        log(f"ORDER FAILED: {symbol} retcode={result.retcode if result else 'None'}")
        return None


def scan_pair(cfg):
    """Scan a single pair for DMR signal."""
    symbol = cfg["symbol"]
    pip_mult = cfg["pip_mult"]
    magic = cfg["magic"]

    # Check existing position
    pos = check_existing_position(symbol, magic)
    if pos:
        # Check hard exit
        est_hour = get_est_hour(datetime.utcnow())
        if est_hour >= PARAMS['HardExitHour']:
            # Close position
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
                mt5.order_send(req)
                log(f"HARD EXIT: {symbol}")
                log_signal("HARD_EXIT", symbol, {"ticket": pos.ticket})
        return None

    # Check pending orders
    if check_pending_orders(symbol, magic) > 0:
        return None

    # Fetch recent bars
    bars = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, 500)
    if bars is None or len(bars) < 50:
        return None

    now = datetime.utcnow()
    today_est = (now + timedelta(hours=PARAMS['ESTOffset'])).date()

    # Parse bars — only from current session (last 24h, excluding weekend stale data)
    # Asian session: previous day 19:00 EST → today 03:00 EST
    # Trading window: today 02:00 EST → 11:00 EST
    today_bars = []
    for bar in bars:
        dt = datetime.fromtimestamp(bar['time'])
        est_dt = dt + timedelta(hours=PARAMS['ESTOffset'])
        est_h = get_est_hour(dt)
        bar_date = est_dt.date()
        
        # Include Asian session bars from previous day (19:00-23:59 EST)
        if bar_date == today_est - timedelta(days=1) and est_h >= 19:
            today_bars.append({
                'time': bar['time'], 'dt': dt, 'est_h': est_h,
                'open': bar['open'], 'high': bar['high'],
                'low': bar['low'], 'close': bar['close'],
            })
        # Include today's bars (02:00-23:59 EST)
        elif bar_date == today_est and est_h >= 2:
            today_bars.append({
                'time': bar['time'], 'dt': dt, 'est_h': est_h,
                'open': bar['open'], 'high': bar['high'],
                'low': bar['low'], 'close': bar['close'],
            })

    if len(today_bars) < 5:
        return None

    # Asian Range (no filter - per v2 backtest)
    asian_high, asian_low = 0.0, 99999.0
    ar_locked = False
    for b in today_bars:
        if b['est_h'] >= 19 or b['est_h'] < 3:
            asian_high = max(asian_high, b['high'])
            asian_low = min(asian_low, b['low'])
        if b['est_h'] == 3 and not ar_locked:
            ar_locked = True
            break

    # Trading window
    trading_bars = [b for b in today_bars if 2 <= b['est_h'] < 11]
    if not trading_bars:
        return None

    # ─── Multi-Entry: Scan each 2-hour window for P90 ───
    # Track which windows have fired (check pending orders AND signaled history)
    windows_fired = set()
    
    # Check pending orders
    orders = mt5.orders_get(symbol=symbol)
    if orders:
        for o in orders:
            if o.magic and 20260600 <= o.magic <= 20260610:
                order_time = datetime.fromtimestamp(o.time)
                est_h = get_est_hour(order_time)
                for start, end, _ in P90_WINDOWS:
                    if start <= est_h < end:
                        windows_fired.add(start)
                        break
    
    # Check signaled windows history (prevents re-signaling if order failed)
    date_str = today_est.isoformat()
    for start, end, _ in P90_WINDOWS:
        if is_window_signaled(symbol.replace(".PRO", ""), start, date_str):
            windows_fired.add(start)

    # P90 scan - one per 2-hour window
    p90_found = False
    p90_dir = 0
    activation = 0.0
    body_pips = 0.0
    p90_idx = -1

    for window_start, window_end, window_threshold in P90_WINDOWS:
        if window_start in windows_fired:
            continue
        window_bars = [b for b in trading_bars if window_start <= b['est_h'] < window_end]
        if not window_bars:
            continue
        for i, b in enumerate(window_bars):
            body = abs(b['close'] - b['open'])
            bp = price_to_pips(body, pip_mult)
            if bp >= window_threshold:
                p90_found = True
                p90_dir = 1 if b['close'] > b['open'] else -1
                activation = b['close']
                body_pips = bp
                p90_idx = trading_bars.index(b)
                break
        if p90_found:
            break

    if not p90_found:
        return None

    # Deep State (DS) calculation - from Asian boundary, NOT bar close
    # Bull P90: DS = asian_high + 200% body (above the band)
    # Bear P90: DS = asian_low - 200% body (below the band)
    if p90_dir == 1:  # Bull P90
        ds = asian_high + pips_to_price(body_pips * PARAMS['DeepMult'], pip_mult)
    else:  # Bear P90
        ds = asian_low - pips_to_price(body_pips * PARAMS['DeepMult'], pip_mult)
    
    # Kill Switch (KS) - P90 SL at 80% body from activation
    # Used for P90 SL, but DMR uses P90 SL (shared boundary)
    ks = activation + pips_to_price(body_pips * PARAMS['KillMult'], pip_mult) * p90_dir

    # DS Touch Detection
    ds_touched = False
    ds_bar = None
    for b in trading_bars[p90_idx + 1:]:
        if b['est_h'] >= PARAMS['DS_ScanEndHour']:
            break
        # Bull P90: DS is ABOVE asian_high, need price to RISE to reach it
        if p90_dir == 1 and b['high'] >= ds:
            ds_touched = True
            ds_bar = b
            break
        # Bear P90: DS is BELOW asian_low, need price to FALL to reach it
        if p90_dir == -1 and b['low'] <= ds:
            ds_touched = True
            ds_bar = b
            break

    if not ds_touched:
        return None

    # Validate geometry
    is_short = (p90_dir == 1)
    entry_price = ds

    # P90 SL calculation (80% body from activation)
    p90_sl_distance = pips_to_price(body_pips * 0.80, pip_mult)
    if is_short:  # LONG P90
        p90_sl = activation - p90_sl_distance
    else:  # SHORT P90
        p90_sl = activation + p90_sl_distance
    
    # For DMR: SL must be on correct side of entry
    # LONG P90 → DMR SHORT → SL below entry
    # SHORT P90 → DMR LONG → SL above entry
    if is_short:  # DMR SHORT
        if p90_sl >= entry_price:
            return None
    else:  # DMR LONG
        if p90_sl <= entry_price:
            return None

    # Check if market has live price (not stale) — allow up to 2h stale
    tick = mt5.symbol_info_tick(symbol)
    if not tick or tick.time == 0:
        daily_stats["skipped_stale"] += 1
        log(f"SKIP {symbol}: No tick data")
        return None
    tick_age = (datetime.utcnow() - datetime.fromtimestamp(tick.time)).total_seconds()
    if tick_age > 7200:  # 2 hours
        daily_stats["skipped_stale"] += 1
        log(f"SKIP {symbol}: Stale price ({tick_age:.0f}s old)")
        return None
    
    # Calculate DMR TP/SL correctly
    # DMR TP = -50% AR (mean reversion target)
    # DMR SL = P90 SL (shared boundary, already calculated above)
    ar_price = asian_high - asian_low
    # DMR TP: mean reversion target (-50% AR from entry)
    # P90 LONG → DMR SHORT → TP below entry
    # P90 SHORT → DMR LONG → TP above entry
    if is_short:  # P90 LONG, DMR SHORT
        dmr_tp_price = entry_price - (ar_price * 0.50)
    else:  # P90 SHORT, DMR LONG
        dmr_tp_price = entry_price + (ar_price * 0.50)
    # DMR SL: use P90 SL (shared boundary)
    dmr_sl_price = p90_sl
    
    # Build signal data
    direction = "SHORT" if is_short else "LONG"
    date_str = today_est.isoformat()
    
    pre_signal = {
        "symbol": symbol.replace(".PRO", ""),
        "direction": direction,
        "confidence": 0.92,
        "pathway": "DMR_200DS",
        "regime": "DMR",
        "regime_ratio": 0.0,
        "asian_range_pips": round(price_to_pips(asian_high - asian_low, pip_mult), 1),
        "entry_price": round(entry_price, 5),
        "sl_price": round(dmr_sl_price, 5),
        "tp_price": round(dmr_tp_price, 5),
        "body_pips": round(body_pips, 1),
        "ds_level": round(ds, 5),
        "timestamp": datetime.now(EST).strftime("%Y-%m-%d %H:%M:%S"),
    }
    
    # Place the order FIRST
    result = place_limit_order(symbol, is_short, dmr_sl_price, dmr_tp_price, entry_price, magic, pip_mult)
    
    if result:
        # Order placed successfully - send alert ONCE
        daily_stats["signals_detected"] += 1
        mark_window_signaled(symbol.replace(".PRO", ""), window_start, date_str)
        log_signal("DMR_ENTRY", symbol.replace(".PRO", ""), pre_signal)
        send_discord_alert(pre_signal)
        log(f"ORDER PLACED: {symbol} {direction} @ {entry_price:.5f} | DS={ds:.5f} | Body={body_pips:.1f}p")
        return pre_signal
    else:
        # Order failed - log but DON'T send Discord alert
        # Still mark window as signaled to prevent retry spam
        mark_window_signaled(symbol.replace(".PRO", ""), window_start, date_str)
        log(f"ORDER FAILED (no alert sent): {symbol} {direction} @ {entry_price:.5f}")
        return None


def run_once():
    """Single scan cycle across all pairs."""
    signals = []
    for name, cfg in PAIRS.items():
        try:
            sig = scan_pair(cfg)
            if sig:
                signals.append(sig)
        except Exception as e:
            log(f"ERROR scanning {name}: {e}")
    return signals


def main():
    log("=" * 60)
    log("DMR MULTI-PAIR LIVE EXECUTOR — Demo Account")
    log(f"Pairs: {', '.join(PAIRS.keys())}")
    log(f"Expected: ~5 trades/day")
    log(f"Lot size: {PARAMS['LotSize']}")
    log("=" * 60)

    if not mt5.initialize():
        log("FATAL: MT5 init failed")
        sys.exit(1)

    acct = mt5.account_info()
    if acct:
        log(f"Account: {acct.login} | Balance: ${acct.balance:.2f} | Server: {acct.server}")
        log(f"Mode: {'DEMO' if acct.trade_mode == 0 else 'LIVE'}")

    load_stats()
    load_signaled_windows()
    log("Scanning every 60 seconds... (Ctrl+C to stop)")

    def is_trading_hours():
        """Check if current time is within DMR trading window (2-11 AM EST)."""
        est_hour = get_est_hour(datetime.utcnow())
        return 2 <= est_hour < 11

    try:
        while True:
            check_closed_trades()
            cancel_stale_orders()  # Cancel stale orders after 5 PM EST
            
            if is_trading_hours():
                signals = run_once()
                if signals:
                    log(f"[{datetime.now(EST).strftime('%H:%M:%S')}] {len(signals)} signal(s) fired")
            else:
                est_hour = get_est_hour(datetime.utcnow())
                log(f"[{datetime.now(EST).strftime('%H:%M:%S')}] Outside trading hours (EST: {est_hour}:00), skipping scan")
            
            save_stats()
            time.sleep(60)
    except KeyboardInterrupt:
        log("STOPPED by user")
    finally:
        save_stats()
        mt5.shutdown()
        log("MT5 disconnected")


if __name__ == "__main__":
    main()
