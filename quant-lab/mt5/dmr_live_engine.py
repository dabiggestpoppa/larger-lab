"""
DMR Live Engine — 1:1 Parity with Backtest
===========================================
Uses the SAME P90Engine from backtest, only swaps data source from CSV to MT5 live.
"""
import sys, time, json, os
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(r"C:\Users\wifik\Desktop\projects\larger-lab")))
sys.path.insert(0, str(Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines")))
sys.path.insert(0, str(Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\configs")))

from p90_engine_dmr import P90Engine, Bar, TradeDirection, P90Variant, EngineState, DEFAULT_P90_THRESHOLDS
from asset_configs import ASSET_CONFIGS
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
signaled_windows = {}

# Per-pair engine instances
engines = {}

# Track last processed bar time per pair to avoid reprocessing
last_processed_bar = {}

# Track session initialization date per pair to avoid re-initializing every minute
session_init_date = {}

# Track pairs that are NO_GO for the day to skip them entirely
no_go_pairs = set()

# ─── Pair Configuration with per-pair tier configs ───
PAIRS = {
    "NZDCHF": {"symbol": "NZDCHF.PRO", "pip_mult": 10000, "magic": 20260601, "pip_size": 0.0001, "tier_config": ASSET_CONFIGS.get("NZDCHF", {}).get("tiers", {})},
    "GBPJPY": {"symbol": "GBPJPY.PRO", "pip_mult": 100,   "magic": 20260602, "pip_size": 0.01, "tier_config": ASSET_CONFIGS.get("GBPJPY", {}).get("tiers", {})},
    "EURGBP": {"symbol": "EURGBP.PRO", "pip_mult": 10000, "magic": 20260603, "pip_size": 0.0001, "tier_config": ASSET_CONFIGS.get("EURGBP", {}).get("tiers", {})},
    "AUDUSD": {"symbol": "AUDUSD.PRO", "pip_mult": 10000, "magic": 20260604, "pip_size": 0.0001, "tier_config": ASSET_CONFIGS.get("AUDUSD", {}).get("tiers", {})},
    "USDCAD": {"symbol": "USDCAD.PRO", "pip_mult": 10000, "magic": 20260605, "pip_size": 0.0001, "tier_config": ASSET_CONFIGS.get("USDCAD", {}).get("tiers", {})},
    "EURAUD": {"symbol": "EURAUD.PRO", "pip_mult": 10000, "magic": 20260606, "pip_size": 0.0001, "tier_config": ASSET_CONFIGS.get("EURAUD", {}).get("tiers", {})},
    "GBPNZD": {"symbol": "GBPNZD.PRO", "pip_mult": 10000, "magic": 20260607, "pip_size": 0.0001, "tier_config": ASSET_CONFIGS.get("GBPNZD", {}).get("tiers", {})},
    "EURUSD": {"symbol": "EURUSD.PRO", "pip_mult": 10000, "magic": 20260608, "pip_size": 0.0001, "tier_config": ASSET_CONFIGS.get("EURUSD", {}).get("tiers", {})},
    "USDCHF": {"symbol": "USDCHF.PRO", "pip_mult": 10000, "magic": 20260609, "pip_size": 0.0001, "tier_config": ASSET_CONFIGS.get("USDCHF", {}).get("tiers", {})},
    "CHFJPY": {"symbol": "CHFJPY.PRO", "pip_mult": 100,   "magic": 20260610, "pip_size": 0.01, "tier_config": ASSET_CONFIGS.get("CHFJPY", {}).get("tiers", {})},
}

PARAMS = {
    'LotSize':        0.01,
    'DeepMult':       2.0,
    'KillMult':       2.2,
    'ESTOffset':      -5,
    'HardExitHour':   17,
    'MaxDailyTrades': 999,
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


def get_est_hour(dt):
    return (dt.hour + PARAMS['ESTOffset']) % 24


def log(msg):
    ts = datetime.now(EST).strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(LOG_DIR / "dmr_live.log", "a", encoding="utf-8") as f:
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
                if d.ticket in reported_deals:
                    continue
                reported_deals.add(d.ticket)
                
                symbol_name = d.symbol.replace(".PRO", "")
                pnl_pips = d.profit * 10000  # Approximate
                
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
    """Cancel pending orders outside trading hours (after 5 PM EST)."""
    est_hour = get_est_hour(datetime.utcnow())
    if est_hour < 17:
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


def get_or_create_engine(pair_name, cfg):
    """Get or create P90Engine instance for a pair."""
    if pair_name not in engines:
        engines[pair_name] = P90Engine(
            pip_size=cfg["pip_size"],
            p90_config=DEFAULT_P90_THRESHOLDS.copy(),
            tier_config=cfg.get("tier_config", {}).copy(),
            symbol=pair_name,
            target_mode="both",
        )
    return engines[pair_name]


def fetch_m5_bars(symbol, count=500):
    """Fetch M5 bars from MT5."""
    bars = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, count)
    if bars is None or len(bars) < 50:
        return None
    
    result = []
    for bar in bars:
        dt = datetime.fromtimestamp(bar['time'])
        result.append(Bar(
            timestamp=dt.replace(tzinfo=timezone.utc),
            open=bar['open'],
            high=bar['high'],
            low=bar['low'],
            close=bar['close'],
        ))
    return result


def initialize_session(engine, pair_name, cfg, today_est):
    """Initialize session with Asian range from MT5 data."""
    # Check if already initialized for today
    if pair_name in session_init_date and session_init_date[pair_name] == today_est:
        return True
    
    bars = fetch_m5_bars(cfg["symbol"], 500)
    if not bars:
        return False
    
    # Calculate Asian range (19:00-03:00 EST previous day)
    asian_high, asian_low = 0.0, 99999.0
    for bar in bars:
        est_dt = bar.timestamp + timedelta(hours=PARAMS['ESTOffset'])
        est_h = get_est_hour(bar.timestamp)
        bar_date = est_dt.date()
        
        # Asian session: previous day 19:00-23:59 and today 00:00-03:00
        if bar_date == today_est - timedelta(days=1) and est_h >= 19:
            asian_high = max(asian_high, bar.high)
            asian_low = min(asian_low, bar.low)
        elif bar_date == today_est and est_h < 3:
            asian_high = max(asian_high, bar.high)
            asian_low = min(asian_low, bar.low)
    
    if asian_high == 0.0 or asian_low == 99999.0:
        return False
    
    engine.initialize_session(asian_high, asian_low)
    log(f"SESSION INIT: {pair_name} AR={engine.asian_range_pips:.1f}p tier={engine.tier_name}")
    
    # Track initialization date
    session_init_date[pair_name] = today_est
    return True


def process_live_bars(engine, pair_name, cfg, today_est):
    """Process latest bar through the engine."""
    bars = fetch_m5_bars(cfg["symbol"], 200)
    if not bars:
        return None
    
    # Filter to today's trading session (2-11 AM EST)
    today_bars = []
    for bar in bars:
        est_dt = bar.timestamp + timedelta(hours=PARAMS['ESTOffset'])
        est_h = get_est_hour(bar.timestamp)
        bar_date = est_dt.date()
        
        if bar_date == today_est and 2 <= est_h < 11:
            today_bars.append(bar)
    
    if not today_bars:
        return None
    
    # Only process the LATEST bar to avoid reprocessing historical bars
    latest_bar = today_bars[-1]
    bar_time = latest_bar.timestamp
    
    # Check if we've already processed this bar
    if pair_name in last_processed_bar and last_processed_bar[pair_name] == bar_time:
        return None
    
    # Update last processed bar time
    last_processed_bar[pair_name] = bar_time
    
    # Process only the latest bar through the engine
    sig = engine.process_bar(latest_bar)
    if sig:
        return [sig]
    
    return None


def place_dmr_order(symbol, is_short, sl_price, tp_price, entry_price, magic, pip_mult, pip_size):
    """Place DMR limit order on MT5."""
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

    # Ensure SL/TP meet broker minimum distance (2 pips minimum + spread)
    tick = mt5.symbol_info_tick(symbol)
    spread_pips = (tick.ask - tick.bid) * pip_mult if tick else 0
    min_distance = (2 + spread_pips) * pip_size
    
    if is_short:
        sl_dist = sl_r - entry_r
        tp_dist = entry_r - tp_r
        if sl_dist < min_distance:
            sl_r = round(entry_r + min_distance, digits)
        if tp_dist < min_distance:
            tp_r = round(entry_r - min_distance, digits)
    else:
        sl_dist = entry_r - sl_r
        tp_dist = tp_r - entry_r
        if sl_dist < min_distance:
            sl_r = round(entry_r - min_distance, digits)
        if tp_dist < min_distance:
            tp_r = round(entry_r + min_distance, digits)
    
    # Verify entry is within reasonable distance of current market
    tick = mt5.symbol_info_tick(symbol)
    if tick:
        max_entry_distance = 50 * pip_size
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


def handle_dmr_signal(engine, pair_name, cfg, sig, today_est):
    """Handle DMR signal from engine and place order."""
    if sig.event != "DMR_TRIGGERED":
        return None
    
    # Check if window already signaled
    date_str = today_est.isoformat()
    # Determine window from signal timestamp
    sig_time = datetime.fromisoformat(sig.timestamp.replace('Z', '+00:00')) if isinstance(sig.timestamp, str) else sig.timestamp
    est_h = get_est_hour(sig_time)
    window_start = None
    for start, end, _ in P90_WINDOWS:
        if start <= est_h < end:
            window_start = start
            break
    
    if window_start and is_window_signaled(pair_name, window_start, date_str):
        return None
    
    # Place the order
    result = place_dmr_order(
        cfg["symbol"],
        sig.direction == TradeDirection.SHORT,
        sig.sl_price,
        sig.tp_price,
        sig.entry_price,
        cfg["magic"],
        cfg["pip_mult"],
        cfg["pip_size"]
    )
    
    if result:
        daily_stats["signals_detected"] += 1
        if window_start:
            mark_window_signaled(pair_name, window_start, date_str)
        
        # Send Discord alert
        alert = {
            "symbol": pair_name,
            "direction": sig.direction.name,
            "confidence": 0.92,
            "pathway": "DMR_200DS",
            "regime": "DMR",
            "regime_ratio": 0.0,
            "asian_range_pips": round(engine.asian_range_pips, 1),
            "entry_price": round(sig.entry_price, 5),
            "sl_price": round(sig.sl_price, 5),
            "tp_price": round(sig.tp_price, 5),
            "body_pips": round(sig.p90_body_pips, 1),
            "ds_level": round(sig.entry_price, 5),
            "timestamp": datetime.now(EST).strftime("%Y-%m-%d %H:%M:%S"),
        }
        log_signal("DMR_ENTRY", pair_name, alert)
        send_discord_alert(alert)
        log(f"ORDER PLACED: {pair_name} {sig.direction.name} @ {sig.entry_price:.5f} | DS={sig.entry_price:.5f} | Body={sig.p90_body_pips:.1f}p")
        return alert
    else:
        if window_start:
            mark_window_signaled(pair_name, window_start, date_str)
        log(f"ORDER FAILED (no alert sent): {pair_name} {sig.direction.name} @ {sig.entry_price:.5f}")
        return None


def scan_pair(pair_name, cfg):
    """Scan a single pair for DMR signals using the backtest engine."""
    # Skip NO_GO pairs for the day
    if pair_name in no_go_pairs:
        return None
    
    engine = get_or_create_engine(pair_name, cfg)
    
    now = datetime.utcnow()
    today_est = (now + timedelta(hours=PARAMS['ESTOffset'])).date()
    
    # Initialize session if not already done
    if not engine.session_active:
        if not initialize_session(engine, pair_name, cfg, today_est):
            # If initialization failed or tier is NO_GO, mark as NO_GO for the day
            no_go_pairs.add(pair_name)
            return None
    
    # Check hard exit (5 PM EST)
    est_hour = get_est_hour(datetime.utcnow())
    if est_hour >= PARAMS['HardExitHour']:
        # Engine will handle hard exit via process_bar
        pass
    
    # Process live bars
    signals = process_live_bars(engine, pair_name, cfg, today_est)
    if not signals:
        return None
    
    # Handle all signals - log to JSONL and send Discord alerts
    for sig in signals:
        # Log all signals to JSONL for Discord bot
        alert = {
            "symbol": pair_name,
            "direction": sig.direction.name if hasattr(sig.direction, 'name') else str(sig.direction),
            "confidence": 0.92,
            "pathway": "DMR_200DS",
            "regime": "DMR",
            "regime_ratio": 0.0,
            "asian_range_pips": round(engine.asian_range_pips, 1),
            "entry_price": round(sig.entry_price, 5) if sig.entry_price else None,
            "sl_price": round(sig.sl_price, 5) if sig.sl_price else None,
            "tp_price": round(sig.tp_price, 5) if sig.tp_price else None,
            "body_pips": round(sig.p90_body_pips, 1),
            "ds_level": round(sig.entry_price, 5) if sig.event == "DMR_TRIGGERED" else None,
            "timestamp": datetime.now(EST).strftime("%Y-%m-%d %H:%M:%S"),
            "event": sig.event,
            "variant": sig.variant.value if hasattr(sig.variant, 'value') else str(sig.variant),
            "reason": sig.reason,
        }
        
        # Log to JSONL for Discord bot
        log_signal(sig.event, pair_name, alert)
        
        # Send Discord alert for all signal types
        send_discord_alert(alert)
        
        # Handle DMR_TRIGGERED specifically for order placement
        if sig.event == "DMR_TRIGGERED":
            handle_dmr_signal(engine, pair_name, cfg, sig, today_est)
        elif sig.event in ("DMR_TP_HIT", "DMR_SL_HIT", "TP_HIT", "SL_HIT", "EWS_EXIT", "HARD_EXIT"):
            log(f"{sig.event}: {pair_name} {sig.direction.name if hasattr(sig.direction, 'name') else sig.direction} @ {sig.entry_price}")
    
    return signals


def run_once():
    """Single scan cycle across all pairs."""
    signals = []
    for name, cfg in PAIRS.items():
        try:
            sigs = scan_pair(name, cfg)
            if sigs:
                signals.extend(sigs)
        except Exception as e:
            log(f"ERROR scanning {name}: {e}")
    return signals


def is_trading_hours():
    """Check if current time is within DMR trading window (2-11 AM EST)."""
    est_hour = get_est_hour(datetime.utcnow())
    return 2 <= est_hour < 11


def main():
    log("=" * 60)
    log("DMR LIVE ENGINE — 1:1 Parity with Backtest")
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

    try:
        while True:
            check_closed_trades()
            cancel_stale_orders()
            
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