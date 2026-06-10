"""
CEREBUS OCC BUFFER SIGNAL ENGINE — Signal-Only (No Execution)
==============================================================
MAD Directive 2026-06-10: ST+OCC buffer engine, signals only.

Reads MT5 bars → SymmetryTrapOCCBufferEngine → writes signals to JSONL.
Separate signal file from ST bridge for clean traceability.

Engine: SymmetryTrapOCCBufferEngine (symmetry_trap_occ_buffer.py)
  - Same ST logic but with regular SL (impulse extreme + buffer)
  - No order placement — signal output only

Usage:
    python occ_buffer_signal.py --symbols EURUSD.PRO,USDCHF.PRO
    python occ_buffer_signal.py --symbols EURUSD.PRO,USDCHF.PRO --lot-size 0.01
"""
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
os.environ["PYTHONIOENCODING"] = "utf-8"

import pytz
import MetaTrader5 as mt5

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from engines.symmetry_trap_occ_buffer import (
    SymmetryTrapOCCBufferEngine,
    Bar,
    TradeDirection,
)

EST = pytz.timezone("US/Eastern")

# ─── CONFIG ────────────────────────────────────────────────────────
SYMBOLS = ["EURUSD.PRO", "USDCHF.PRO"]
LOT_SIZE = 0.01
MAGIC = 20260610

LOG_DIR = REPO_ROOT / "quant-lab" / "mt5" / "live_logs"
SIGNAL_FILE = LOG_DIR / "occ_buffer_signals.jsonl"
ACCOUNT_PATH = REPO_ROOT / "quant-lab" / "mt5" / "live_account.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_DIR / "occ_buffer.log"),
    ],
)
log = logging.getLogger("occ_buffer.signal")


# ─── MT5 HELPERS ──────────────────────────────────────────────────

def get_pip_size(symbol: str) -> float:
    info = mt5.symbol_info(symbol)
    if info is None:
        return 0.0001
    if info.point >= 0.001:
        return 0.01
    return 0.0001


def mt5_connect() -> bool:
    try:
        with open(ACCOUNT_PATH, "r") as f:
            account = json.load(f)
        login = account.get("login")
        server = account.get("server")
        password = account.get("password")
        if not mt5.initialize():
            log.error("MT5 init failed: %s", mt5.last_error())
            return False
        authorized = mt5.login(login=login, password=password, server=server)
        if not authorized:
            log.error("MT5 login failed: %s", mt5.last_error())
            mt5.shutdown()
            return False
        info = mt5.account_info()
        log.info("MT5 connected: %s @ %s | Balance: $%.2f",
                 info.login, info.server, info.balance)
        return True
    except Exception as e:
        log.error("MT5 connect error: %s", e)
        return False


def get_bars(symbol: str, count: int = 500) -> list:
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, count)
    if rates is None or len(rates) == 0:
        return []
    result = []
    for r in rates:
        result.append({
            "time": datetime.fromtimestamp(int(r["time"]), tz=EST),
            "open": float(r["open"]),
            "high": float(r["high"]),
            "low": float(r["low"]),
            "close": float(r["close"]),
        })
    return result


def mt5_bar_to_engine_bar(mt5_bar: dict) -> Bar:
    return Bar(
        timestamp=mt5_bar["time"],
        open=mt5_bar["open"],
        high=mt5_bar["high"],
        low=mt5_bar["low"],
        close=mt5_bar["close"],
    )


def calc_asian_range(bars: list) -> tuple:
    if not bars:
        return (0.0, 0.0)
    now = datetime.now(EST)
    if now.hour >= 3:
        session_end = now.replace(hour=3, minute=0, second=0, microsecond=0)
    else:
        yesterday = now - timedelta(days=1)
        session_end = yesterday.replace(hour=3, minute=0, second=0, microsecond=0)
    session_start = session_end - timedelta(hours=8)
    asian = [b for b in bars if b["time"] >= session_start and b["time"] <= session_end]
    if not asian:
        return (0.0, 0.0)
    return (max(b["high"] for b in asian), min(b["low"] for b in asian))


def to_pips(price_diff: float, symbol: str) -> float:
    pip = get_pip_size(symbol)
    if pip == 0:
        return 0.0
    return round(price_diff / pip, 1)


# ─── SIGNAL OUTPUT ────────────────────────────────────────────────

def emit_signal(sig: dict):
    """Write OCC Buffer signal to separate JSONL file."""
    SIGNAL_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SIGNAL_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(sig, default=str) + "\n")
    log.info("SIGNAL: %s %s %s", sig.get("event"), sig.get("symbol"), sig.get("direction"))


def format_signal(sig, engine_sym: str, lot_size: float) -> dict:
    """Format engine signal dict for signal_bot consumption."""
    direction = "BUY" if sig.direction == TradeDirection.LONG else "SELL"
    entry = sig.entry_price
    sl = sig.sl_price
    tp = sig.tp_price

    sl_pips = to_pips(abs(entry - sl), engine_sym) if sl and entry else 0
    tp_pips = to_pips(abs(tp - entry), engine_sym) if tp and entry else 0
    rr = round(tp_pips / sl_pips, 2) if sl_pips > 0 else 0.0

    return {
        "engine": "OCCBuffer",
        "symbol": engine_sym,
        "direction": direction,
        "entry": entry,
        "sl": sl,
        "tp": tp,
        "event": sig.event,
        "loop": sig.loop_count,
        "time": datetime.now(EST).strftime("%Y-%m-%d %H:%M:%S"),
        "sl_pips": sl_pips,
        "tp_pips": tp_pips,
        "rr": rr,
        "lot_size": lot_size,
        "buffer_type": "regular_sl",
    }


# ─── MAIN LOOP ────────────────────────────────────────────────────

def run(symbols: list, lot_size: float):
    log.info("=" * 60)
    log.info("  OCC BUFFER SIGNAL ENGINE — Signal-Only (No Execution)")
    log.info("  Symbols: %s", symbols)
    log.info("  Lot: %.2f", lot_size)
    log.info("  Signal file: %s", SIGNAL_FILE)
    log.info("  Started: %s", datetime.now(EST).strftime("%Y-%m-%d %H:%M:%S EST"))
    log.info("=" * 60)

    if not mt5_connect():
        log.error("MT5 connection failed — exiting")
        return

    # Initialize engines per symbol
    engines = {}
    for sym in symbols:
        ps = get_pip_size(sym)
        engines[sym] = SymmetryTrapOCCBufferEngine(pip_size=ps, symbol=sym)

    # Initialize sessions
    now = datetime.now(EST)
    for sym in symbols:
        bars = get_bars(sym, 500)
        if not bars:
            log.warning("[%s] No bars for session init", sym)
            continue
        ah, al = calc_asian_range(bars)
        if ah > 0 and al < 99999:
            engines[sym].initialize_session(ah, al)
            ar_pips = (ah - al) / get_pip_size(sym)
            log.info("[%s] Session INIT: AR=%.1f pips | tier=%s",
                     sym, ar_pips, engines[sym].tier_name)
        else:
            last_close = bars[-1]["close"]
            pip = get_pip_size(sym)
            engines[sym].initialize_session(last_close + 10 * pip, last_close - 10 * pip)
            log.warning("[%s] Asian Range unavailable — defaulting to T1", sym)

    scan_count = 0
    signal_count = 0
    last_minute = -1

    try:
        while True:
            now = datetime.now(EST)

            scan_this_minute = (now.second < 5 and now.minute != last_minute)
            if scan_this_minute:
                last_minute = now.minute
                scan_count += 1

                if scan_count % 60 == 0:
                    acct = mt5.account_info()
                    equity = acct.equity if acct else 0
                    log.info("[%s] Scan #%d | Equity: $%.2f | Signals: %d",
                             now.strftime("%H:%M:%S"), scan_count, equity, signal_count)

                for sym in symbols:
                    try:
                        bars = get_bars(sym, 500)
                        if not bars:
                            continue

                        latest = bars[-1]
                        engine_bar = mt5_bar_to_engine_bar(latest)

                        engine = engines[sym]
                        sig = engine.process_bar(engine_bar)

                        if sig:
                            signal_count += 1
                            sig_dict = format_signal(sig, sym, lot_size)
                            emit_signal(sig_dict)

                            direction = sig_dict["direction"]
                            entry = sig.entry_price
                            sl = sig.sl_price
                            tp = sig.tp_price
                            sl_p = sig_dict["sl_pips"]
                            tp_p = sig_dict["tp_pips"]
                            rr = sig_dict["rr"]

                            if sig.event == "ENTRY":
                                log.info("ENTRY: %s %s @ %.5f | SL=%.5f (%.1fp) | TP=%.5f (%.1fp) | RR=%.2f",
                                         direction, sym, entry, sl, sl_p, tp, tp_p, rr)
                            elif sig.event == "TP_HIT":
                                log.info("TP HIT: %s %s @ %.5f | RR=%.2f", direction, sym, entry, rr)
                            elif sig.event == "SL_HIT":
                                log.info("SL HIT: %s %s @ %.5f | SL was %.5f (%.1fp buffer)",
                                         direction, sym, entry, sl, sl_p)

                    except Exception as sym_err:
                        log.error("[%s] Error: %s", sym, sym_err)

            time.sleep(1)

    except KeyboardInterrupt:
        log.info("Stopped by user.")
    except Exception as e:
        log.error("FATAL: %s", e, exc_info=True)
    finally:
        try:
            mt5.shutdown()
        except Exception:
            pass
        log.info("Shutdown. %d scans | %d signals emitted", scan_count, signal_count)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="OCC Buffer Signal Engine")
    parser.add_argument("--symbols", default=",".join(SYMBOLS))
    parser.add_argument("--lot-size", type=float, default=LOT_SIZE)
    args = parser.parse_args()
    symbols = [s.strip() for s in args.symbols.split(",")]
    run(symbols, args.lot_size)
