"""
DMR Multi-Pair Live Executor — Demo Account
==============================================
5 pairs: EURUSD, GBPUSD, USDJPY, GBPJPY, CHFJPY
~5 trades/day combined
Sends signals to data/alerts_history.json for Discord bot

Strategy: Limit order at 200% Deep State, TP at activation, SL at 220%
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


def get_p90_threshold(symbol, est_hour):
    thresholds = P90_THRESHOLDS.get(symbol, {})
    if est_hour in thresholds:
        return thresholds[est_hour]
    # Fallback to nearest hour
    for offset in range(1, 9):
        for candidate in [est_hour - offset, est_hour + offset]:
            if candidate in thresholds:
                return thresholds[candidate]
    return 5.0  # Safe fallback


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
        log(f"ORDER PLACED: {symbol} {'SHORT' if is_short else 'LONG'} @ {entry_r} SL={sl_r} TP={tp_r}")
        return result
    else:
        log(f"ORDER FAILED: {symbol} retcode={result.retcode if result else 'None'}")
        return None


def check_position_result(symbol, magic, pip_mult):
    """Check if a position was closed (TP or SL hit). Log result."""
    # Get deals from last 24h
    deals = mt5.history_deals_get(
        datetime.utcnow() - timedelta(hours=24),
        datetime.utcnow()
    )
    if not deals:
        return None
    
    # Find close deals for this symbol+magic
    for deal in deals:
        if deal.magic == magic and deal.entry == 1:  # entry=1 means close
            pnl_pips = price_to_pips(deal.profit, pip_mult) if hasattr(deal, 'profit') else 0
            result_type = "TP" if deal.profit > 0 else "SL"
            result = {
                "symbol": symbol.replace(".PRO", ""),
                "type": result_type,
                "result": result_type,
                "pnl_pips": round(pnl_pips, 1),
                "entry_price": deal.price,  # Approximate
                "exit_price": deal.price,
                "timestamp": datetime.now(EST).isoformat(),
            }
            log(f"RESULT: {symbol} {result_type} PnL={pnl_pips:+.1f}p")
            log_signal(result_type, symbol.replace(".PRO", ""), result)
            return result
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
    
    # Check if a position was recently closed (TP/SL hit)
    check_position_result(symbol, magic, pip_mult)

    # Check pending orders
    if check_pending_orders(symbol, magic) > 0:
        return None

    # Fetch recent bars
    bars = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, 500)
    if bars is None or len(bars) < 50:
        return None

    now = datetime.utcnow()
    today_est = (now + timedelta(hours=PARAMS['ESTOffset'])).date()

    # Parse bars into today's session
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

    # Check if market has live price (not stale) — allow up to 2h stale
    tick = mt5.symbol_info_tick(symbol)
    if not tick or tick.time == 0:
        log(f"SKIP {symbol}: No tick data")
        return None
    tick_age = (datetime.utcnow() - datetime.fromtimestamp(tick.time)).total_seconds()
    if tick_age > 7200:  # 2 hours
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

    log("Scanning every 60 seconds... (Ctrl+C to stop)")

    try:
        while True:
            signals = run_once()
            if signals:
                log(f"[{datetime.now(EST).strftime('%H:%M:%S')}] {len(signals)} signal(s) fired")
            time.sleep(60)
    except KeyboardInterrupt:
        log("STOPPED by user")
    finally:
        mt5.shutdown()
        log("MT5 disconnected")


if __name__ == "__main__":
    main()
