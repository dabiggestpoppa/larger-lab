"""
DMR Signal Engine v2 — Multi-Entry Signal Generator
====================================================
Scans MT5 for DMR setups across top 5 pairs ranked by accuracy.
Sends signals to Discord via dmr_signals.jsonl.
Tracks TP/SL hits and sends results.
EOD report at 5PM EST.

NO order placement — signal only. User executes manually.
"""
import sys, time, json, os
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

import MetaTrader5 as mt5

REPO_ROOT = Path(r"C:\Users\wifik\Desktop\projects\larger-lab")
LOG_DIR = REPO_ROOT / "quant-lab" / "mt5" / "live_logs"
EST = timezone(timedelta(hours=-5))

# ─── Top 5 Pairs Ranked by Accuracy (from backtest) ───
# GBPJPY 96.5%, CHFJPY 95.8%, EURAUD 94.4%, GBPNZD 94.7%, USDJPY 94.1%
PAIRS = {
    "GBPJPY": {"symbol": "GBPJPY.PRO", "pip_mult": 100, "magic": 20260604},
    "CHFJPY": {"symbol": "CHFJPY.PRO", "pip_mult": 100, "magic": 20260605},
    "GBPNZD": {"symbol": "GBPNZD.PRO", "pip_mult": 10000, "magic": 20260606},
    "EURAUD": {"symbol": "EURAUD.PRO", "pip_mult": 10000, "magic": 20260607},
    "USDJPY": {"symbol": "USDJPY.PRO", "pip_mult": 100, "magic": 20260603},
}

PARAMS = {
    'DeepMult':       2.0,
    'KillMult':       2.2,
    'MinAR':          3,
    'MaxAR':          45,
    'ESTOffset':      -5,
    'HardExitHour':   17,
    'DS_ScanEndHour': 12,
}

# Per-hour P90 thresholds (calibrated from backtest)
P90_THRESHOLDS = {
    "EURUSD":  {2: 2.6, 3: 3.4, 4: 3.3, 5: 2.7, 6: 2.3, 7: 2.3, 8: 3.0, 9: 4.5, 10: 5.2},
    "GBPUSD":  {2: 3.3, 3: 4.3, 4: 4.2, 5: 3.5, 6: 3.0, 7: 3.1, 8: 4.0, 9: 6.5, 10: 7.6},
    "USDJPY":  {2: 8.0, 3: 9.3, 4: 8.0, 5: 6.4, 6: 5.7, 7: 6.0, 8: 6.8, 9: 8.4, 10: 9.3},
    "GBPJPY":  {2: 9.2, 3: 10.6, 4: 9.1, 5: 7.6, 6: 6.9, 7: 7.2, 8: 8.3, 9: 11.6, 10: 13.2},
    "CHFJPY":  {2: 7.4, 3: 8.7, 4: 7.3, 5: 6.1, 6: 5.6, 7: 5.8, 8: 6.7, 9: 9.2, 10: 10.7},
    "GBPNZD":  {2: 7.9, 3: 9.6, 4: 9.9, 5: 8.9, 6: 7.6, 7: 7.1, 8: 7.8, 9: 10.8, 10: 11.4},
    "EURAUD":  {2: 6.2, 3: 6.1, 4: 7.2, 5: 8.5, 6: 8.7, 7: 7.5, 8: 6.9, 9: 6.7, 10: 7.6},
}

# Track open signals for TP/SL monitoring
open_signals = []
signal_log = []  # All signals for EOD report


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
    with open(LOG_DIR / "dmr_signal_engine.log", "a", encoding="utf-8") as f:
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


def scan_pair(cfg):
    """Scan a single pair for DMR signal. Multi-entry: one P90 per 2hr window."""
    symbol = cfg["symbol"]
    pip_mult = cfg["pip_mult"]

    # Fetch recent bars
    bars = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, 500)
    if bars is None or len(bars) < 50:
        return []

    now = datetime.utcnow()
    today_est = (now + timedelta(hours=PARAMS['ESTOffset'])).date()

    # Parse bars into today's session
    today_bars = []
    for bar in bars:
        dt = datetime.fromtimestamp(bar['time'])
        est_dt = dt + timedelta(hours=PARAMS['ESTOffset'])
        if est_dt.date() == today_est:
            today_bars.append({
                'ts': bar['time'], 'dt': dt,
                'est_h': get_est_hour(dt),
                'o': bar['open'], 'h': bar['high'],
                'l': bar['low'], 'c': bar['close'],
            })

    if len(today_bars) < 5:
        return []

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
        return []

    # ─── Multi-Entry: Scan each 2-hour window for P90 ───
    p90_windows = [(2, 4), (4, 6), (6, 8), (8, 10), (10, 11)]
    signals = []

    for window_start, window_end in p90_windows:
        # Get bars in this window
        window_bars = [b for b in today_bars if window_start <= b['est_h'] < window_end]
        if not window_bars:
            continue

        # Find P90 in this window
        p90_found = False
        p90_dir = 0
        activation = 0.0
        body_pips = 0.0
        p90_idx = -1

        for i, b in enumerate(window_bars):
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
            continue

        # Deep State & Kill Switch
        ds = activation + pips_to_price(body_pips * PARAMS['DeepMult'], pip_mult) * p90_dir
        ks = activation + pips_to_price(body_pips * PARAMS['KillMult'], pip_mult) * p90_dir

        # DS Touch Detection
        ds_touched = False
        for b in today_bars:
            if b['ts'] <= window_bars[p90_idx]['ts']:
                continue
            if b['est_h'] >= PARAMS['DS_ScanEndHour']:
                break
            if p90_dir == 1 and b['l'] <= ds:
                ds_touched = True
                break
            if p90_dir == -1 and b['h'] >= ds:
                ds_touched = True
                break

        if not ds_touched:
            continue

        # Validate geometry
        is_short = (p90_dir == 1)
        entry_price = ds

        if is_short:
            if activation >= entry_price or ks <= entry_price:
                continue
        else:
            if activation <= entry_price or ks >= entry_price:
                continue

        # Check if we already have a signal for this window
        already_have = False
        for sig in open_signals:
            if sig['symbol'] == symbol.replace(".PRO", "") and sig['window'] == f"{window_start}-{window_end}h":
                already_have = True
                break
        if already_have:
            continue

        direction = "SHORT" if is_short else "LONG"
        ar_pips = price_to_pips(asian_high - asian_low, pip_mult)

        signal = {
            "symbol": symbol.replace(".PRO", ""),
            "direction": direction,
            "entry_price": round(entry_price, 5),
            "sl_price": round(ks, 5),
            "tp_price": round(activation, 5),
            "body_pips": round(body_pips, 1),
            "ds_level": round(ds, 5),
            "asian_range_pips": round(ar_pips, 1),
            "window": f"{window_start}-{window_end}h",
            "confidence": 0.92,
            "pathway": "DMR_200DS",
            "regime": "DMR",
            "timestamp": datetime.now(EST).strftime("%Y-%m-%d %H:%M:%S"),
        }

        signals.append(signal)
        open_signals.append(signal)
        signal_log.append(signal)

        log(f"SIGNAL: {symbol} {direction} @ {entry_price:.5f} | DS={ds:.5f} | Body={body_pips:.1f}p | AR={ar_pips:.1f}p | Window {window_start}-{window_end}h")
        log_signal("DMR_ENTRY", symbol.replace(".PRO", ""), signal)

    return signals


def check_tp_sl_hits():
    """Check if any open signals have hit TP or SL."""
    results = []
    for sig in open_signals[:]:
        symbol = sig['symbol']
        # Find the PRO symbol
        pro_symbol = symbol + ".PRO"
        tick = mt5.symbol_info_tick(pro_symbol)
        if not tick:
            continue

        current_price = tick.bid if sig['direction'] == "LONG" else tick.ask
        tp = sig['tp_price']
        sl = sig['sl_price']

        if sig['direction'] == "LONG":
            if current_price >= tp:
                result = {**sig, "result": "TP", "exit_price": round(current_price, 5), "pnl_pips": round(price_to_pips(current_price - sig['entry_price'], 100 if 'JPY' in symbol else 10000), 1)}
                results.append(result)
                open_signals.remove(sig)
                log(f"TP HIT: {symbol} @ {current_price:.5f} | PnL={result['pnl_pips']:+.1f}p")
                log_signal("TP", symbol, result)
            elif current_price <= sl:
                result = {**sig, "result": "SL", "exit_price": round(current_price, 5), "pnl_pips": round(price_to_pips(current_price - sig['entry_price'], 100 if 'JPY' in symbol else 10000), 1)}
                results.append(result)
                open_signals.remove(sig)
                log(f"SL HIT: {symbol} @ {current_price:.5f} | PnL={result['pnl_pips']:+.1f}p")
                log_signal("SL", symbol, result)
        else:  # SHORT
            if current_price <= tp:
                result = {**sig, "result": "TP", "exit_price": round(current_price, 5), "pnl_pips": round(price_to_pips(sig['entry_price'] - current_price, 100 if 'JPY' in symbol else 10000), 1)}
                results.append(result)
                open_signals.remove(sig)
                log(f"TP HIT: {symbol} @ {current_price:.5f} | PnL={result['pnl_pips']:+.1f}p")
                log_signal("TP", symbol, result)
            elif current_price >= sl:
                result = {**sig, "result": "SL", "exit_price": round(current_price, 5), "pnl_pips": round(price_to_pips(sig['entry_price'] - current_price, 100 if 'JPY' in symbol else 10000), 1)}
                results.append(result)
                open_signals.remove(sig)
                log(f"SL HIT: {symbol} @ {current_price:.5f} | PnL={result['pnl_pips']:+.1f}p")
                log_signal("SL", symbol, result)

    return results


def send_eod_report():
    """Send end-of-day summary."""
    now = datetime.now(EST)
    today = now.strftime("%Y-%m-%d")

    # Count today's signals
    today_signals = [s for s in signal_log if s.get("timestamp", "").startswith(today)]
    wins = sum(1 for s in today_signals if s.get("result") == "TP")
    losses = sum(1 for s in today_signals if s.get("result") == "SL")
    total = len(today_signals)
    wr = (wins / total * 100) if total > 0 else 0

    report = {
        "type": "EOD_REPORT",
        "date": today,
        "total_trades": total,
        "wins": wins,
        "losses": losses,
        "win_rate": round(wr, 1),
        "open_positions": len(open_signals),
        "timestamp": now.isoformat(),
    }

    log_signal("EOD", "ALL", report)
    log(f"EOD REPORT: {total} trades | {wins}W {losses}L | WR={wr:.1f}% | {len(open_signals)} open")


def main():
    log("=" * 60)
    log("DMR SIGNAL ENGINE v2 — Multi-Entry")
    log(f"Pairs: {', '.join(PAIRS.keys())}")
    log("Mode: SIGNAL ONLY (no order placement)")
    log("=" * 60)

    if not mt5.initialize():
        log("FATAL: MT5 init failed")
        sys.exit(1)

    acct = mt5.account_info()
    if acct:
        log(f"Account: {acct.login} | Balance: ${acct.balance:.2f} | Server: {acct.server}")

    log("Scanning every 60 seconds... (Ctrl+C to stop)")

    last_eod_date = None

    try:
        while True:
            # 1) Scan all pairs for new signals
            for name, cfg in PAIRS.items():
                try:
                    signals = scan_pair(cfg)
                    if signals:
                        log(f"[{datetime.now(EST).strftime('%H:%M:%S')}] {len(signals)} signal(s) for {name}")
                except Exception as e:
                    log(f"ERROR scanning {name}: {e}")

            # 2) Check TP/SL hits on open signals
            results = check_tp_sl_hits()
            if results:
                log(f"[{datetime.now(EST).strftime('%H:%M:%S')}] {len(results)} result(s) detected")

            # 3) EOD report at 5PM EST
            now = datetime.now(EST)
            if now.hour == 17 and now.minute == 0 and last_eod_date != now.date():
                last_eod_date = now.date()
                send_eod_report()

            time.sleep(60)
    except KeyboardInterrupt:
        log("STOPPED by user")
    finally:
        mt5.shutdown()
        log("MT5 disconnected")


if __name__ == "__main__":
    main()
