#!/usr/bin/env python3
r"""
CEREBUS CLEAN BRIDGE — No Duplicates, No UV, No Bullshit
========================================================
Thin transport layer: MT5 bars → SymmetryTrap engine → MT5 orders

SINGLETON ENFORCEMENT:
1. Windows named mutex (OS-level guarantee)
2. PID file lock (fallback)
3. Kill ALL other bridge processes on startup
4. Explicit venv Python path (no UV interception)

USAGE:
    .venv\Scripts\python.exe quant-lab/mt5/clean_bridge.py --symbols EURJPY.PRO,EURNZD.PRO,GBPNZD.PRO,EURAUD.PRO,GBPAUD.PRO,GBPCAD.PRO,FR40.PRO
"""
import json
import logging
import os
import sys
import time
import ctypes
from datetime import datetime, timedelta
from pathlib import Path

# ─── FORCE UTF-8 ENCODING ───────────────────────────────────────────────
sys.stdout.reconfigure(encoding="utf-8")
os.environ["PYTHONIOENCODING"] = "utf-8"

# ─── SINGLETON ENFORCEMENT ───────────────────────────────────────────────
PID_FILE = Path(__file__).parent / ".clean_bridge.pid"
MUTEX_NAME = "Global\\CerebusCleanBridge_Singleton"

def _kill_all_bridge_processes():
    """Kill ALL other clean_bridge.py processes (except self)."""
    kernel32 = ctypes.windll.kernel32
    PROCESS_TERMINATE = 0x0001
    my_pid = os.getpid()
    killed = 0
    try:
        result = __import__('subprocess').run(
            ["powershell", "-Command",
             "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
             "Where-Object { $_.CommandLine -like '*clean_bridge*' -and $_.ProcessId -ne " + str(my_pid) + " } | "
             "Select-Object -ExpandProperty ProcessId"],
            capture_output=True, text=True, timeout=10
        )
        for line in result.stdout.strip().split('\n'):
            line = line.strip()
            if not line:
                continue
            try:
                pid = int(line)
                handle = kernel32.OpenProcess(PROCESS_TERMINATE, False, pid)
                if handle:
                    kernel32.TerminateProcess(handle, 1)
                    kernel32.CloseHandle(handle)
                    killed += 1
                    log(f"Killed duplicate bridge PID {pid}")
            except (ValueError, OSError):
                pass
    except Exception as e:
        log(f"Error scanning for duplicates: {e}")
    if killed > 0:
        time.sleep(2)
    return killed

def _acquire_singleton():
    """Acquire Windows named mutex + kill all duplicates. Returns True if we own the singleton."""
    kernel32 = ctypes.windll.kernel32

    # Step 1: Kill ALL other bridge processes first
    _kill_all_bridge_processes()

    # Step 2: Create Windows named mutex (true OS-level singleton)
    mutex = kernel32.CreateMutexW(None, False, MUTEX_NAME)
    last_error = kernel32.GetLastError()

    if last_error == 183:  # ERROR_ALREADY_EXISTS
        if mutex:
            kernel32.CloseHandle(mutex)
        log("[FATAL] Another bridge instance holds the mutex. Exiting.")
        return False

    # Step 3: Write PID file
    try:
        with open(PID_FILE, "w") as f:
            f.write(str(os.getpid()))
    except Exception:
        pass

    return True

def _release_singleton():
    """Release mutex and clean up PID file."""
    kernel32 = ctypes.windll.kernel32
    try:
        mutex = kernel32.OpenMutexW(0x00100000, False, MUTEX_NAME)
        if mutex:
            kernel32.ReleaseMutex(mutex)
            kernel32.CloseHandle(mutex)
    except:
        pass
    if PID_FILE.exists():
        try:
            PID_FILE.unlink()
        except OSError:
            pass

# ─── LOGGING ─────────────────────────────────────────────────────────────
LOG_DIR = Path(__file__).parent / "live_logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_DIR / "clean_bridge.log", encoding="utf-8"),
    ],
)
log = logging.getLogger("clean_bridge")

# ─── MT5 IMPORT ───────────────────────────────────────────────────────────
import pytz
import MetaTrader5 as mt5

EST = pytz.timezone("US/Eastern")

# ─── ENGINE IMPORT ───────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from engines.symmetry_trap import SymmetryTrapEngine, Bar, TradeDirection
from deploy_config import DEPLOYMENT_CONFIGS

# ─── CONFIG ───────────────────────────────────────────────────────────────
TOP7_ST = ["EURJPY.PRO", "EURNZD.PRO", "GBPNZD.PRO",
           "EURAUD.PRO", "GBPAUD.PRO", "GBPCAD.PRO", "FR40.PRO"]

# ─── MT5 HELPERS ─────────────────────────────────────────────────────────
def mt5_connect() -> bool:
    account_path = Path(__file__).parent / "live_account.json"
    try:
        with open(account_path, "r") as f:
            account = json.load(f)
    except Exception as e:
        log.error("Failed to load live_account.json: %s", e)
        return False

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
    log.info("MT5 connected: %s @ %s | Balance: $%.2f | Equity: $%.2f",
             info.login, info.server, info.balance, info.equity)
    return True

def get_bars(symbol: str, count: int = 500) -> list:
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, count)
    if rates is None or len(rates) == 0:
        return []
    return [{
        "time": datetime.fromtimestamp(int(r["time"]), tz=EST),
        "open": float(r["open"]),
        "high": float(r["high"]),
        "low": float(r["low"]),
        "close": float(r["close"]),
        "volume": int(r["tick_volume"]),
        "spread": int(r["spread"]),
    } for r in rates]

def mt5_bar_to_engine_bar(mt5_bar: dict) -> Bar:
    return Bar(
        timestamp=mt5_bar["time"],
        open=mt5_bar["open"],
        high=mt5_bar["high"],
        low=mt5_bar["low"],
        close=mt5_bar["close"],
    )

def pip_size(symbol: str) -> float:
    if "XAU" in symbol:
        return 0.01
    if "XAG" in symbol:
        return 0.001
    if "JPY" in symbol:
        return 0.01
    return 0.0001

def to_pips(price_diff: float, symbol: str) -> float:
    pip = pip_size(symbol)
    if pip == 0:
        return 0.0
    return round(price_diff / pip, 1)

def get_positions() -> list:
    positions = mt5.positions_get()
    if positions is None:
        return []
    return [{
        "ticket": p.ticket,
        "symbol": p.symbol,
        "type": "BUY" if p.type == mt5.ORDER_TYPE_BUY else "SELL",
        "volume": p.volume,
        "open_price": p.price_open,
        "current_price": p.price_current,
        "sl": p.sl,
        "tp": p.tp,
        "profit": p.profit,
        "magic": p.magic,
    } for p in positions]

def check_autotrading() -> bool:
    info = mt5.terminal_info()
    if info is None:
        return False
    return info.trade_allowed

def send_order(symbol: str, direction: str, volume: float,
               sl: float, tp: float, comment: str, no_sl: bool = False) -> int:
    if not check_autotrading():
        log.warning("MT5 AutoTrading DISABLED")
        return False

    info = mt5.symbol_info(symbol)
    if info is None or not info.visible:
        mt5.symbol_select(symbol, True)
        time.sleep(1)
        info = mt5.symbol_info(symbol)
    if info is None:
        log.error("Symbol %s not found", symbol)
        return False

    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        log.error("No tick for %s", symbol)
        return False

    order_type = mt5.ORDER_TYPE_BUY if direction == "BUY" else mt5.ORDER_TYPE_SELL
    price = tick.ask if direction == "BUY" else tick.bid

    sl_pips = to_pips(abs(sl - price), symbol) if sl > 0 else 0.0
    tp_pips = to_pips(abs(tp - price), symbol)
    rr = round(tp_pips / sl_pips, 2) if sl_pips > 0 else 0.0

    MIN_RR = 1.0
    if rr < MIN_RR:
        log.warning("BRIDGE RR GATE: REJECTED %s %s | RR=%.2f < %.1f | skipping",
                    direction, symbol, rr, MIN_RR)
        return False

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": order_type,
        "price": price,
        "tp": round(tp, info.digits),
        "deviation": 10,
        "magic": 20260601,
        "comment": comment,
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    if not no_sl:
        request["sl"] = round(sl, info.digits)

    result = mt5.order_send(request)
    if result is None:
        log.error("order_send returned None: %s", mt5.last_error())
        return False
    if result.retcode == mt5.TRADE_RETCODE_DONE:
        log.info("Order OK: %s %s ticket=%d", direction, symbol, result.order)
        return result.order
    log.error("Order FAILED: %s %s retcode=%d %s", direction, symbol, result.retcode, result.comment)
    return False

def close_position(ticket: int) -> bool:
    positions = mt5.positions_get()
    if positions is None:
        return False
    pos = next((p for p in positions if p.ticket == ticket), None)
    if pos is None:
        return False

    tick = mt5.symbol_info_tick(pos.symbol)
    if tick is None:
        return False

    close_price = tick.bid if pos.type == mt5.ORDER_TYPE_BUY else tick.ask
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": pos.symbol,
        "volume": pos.volume,
        "type": mt5.ORDER_TYPE_SELL if pos.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY,
        "position": ticket,
        "price": close_price,
        "deviation": 10,
        "magic": 20260601,
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    result = mt5.order_send(request)
    if result and result.retcode == mt5.TRADE_RETCODE_DONE:
        log.info("Closed ticket %d", ticket)
        return True
    log.error("Close FAILED: ticket=%d retcode=%s", ticket, result.retcode if result else "None")
    return False

# ─── ASIAN RANGE ───────────────────────────────────────────────────────────
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

# ─── SIGNAL LOG ───────────────────────────────────────────────────────────
SIGNAL_FILE = LOG_DIR / "signals.jsonl"

def emit_signal(sig: dict):
    with open(SIGNAL_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(sig) + "\n")

# ─── MAIN LOOP ─────────────────────────────────────────────────────────────
def run_live(symbols: list, lot_size: float = 0.01):
    log.info("=" * 60)
    log.info("  CEREBUS CLEAN BRIDGE — No Duplicates")
    log.info("  Symbols: %s", symbols)
    log.info("  Lot: %.2f", lot_size)
    log.info("  Started: %s", datetime.now(EST).strftime("%Y-%m-%d %H:%M:%S EST"))
    log.info("=" * 60)

    if not mt5_connect():
        return

    # Initialize engines
    st_engines = {}
    for sym in symbols:
        ps = pip_size(sym)
        cfg = DEPLOYMENT_CONFIGS.get(sym, {})
        st_engines[sym] = SymmetryTrapEngine(pip_size=ps, symbol=sym, config=cfg)

    # Initialize sessions
    now = datetime.now(EST)
    for sym in symbols:
        bars = get_bars(sym, 500)
        if not bars:
            log.warning("[%s] No bars for session init", sym)
            continue
        ah, al = calc_asian_range(bars)
        if ah > 0 and al < 99999:
            st_engines[sym].initialize_session(ah, al)
            ar_pips = (ah - al) / pip_size(sym)
            log.info("[%s] Session INIT: AR=%.1f pips | tier=%s",
                     sym, ar_pips, st_engines[sym].tier_name)
        else:
            last_close = bars[-1]["close"]
            pip = pip_size(sym)
            st_engines[sym].initialize_session(last_close + 10 * pip, last_close - 10 * pip)
            log.warning("[%s] Asian Range unavailable — defaulting to T1 (synthetic AR=10p)", sym)

    active_trades = {}
    daily_stats = {"date": now.strftime("%Y-%m-%d"), "entries": 0, "wins": 0, "losses": 0, "pips": 0.0, "rr_total": 0.0}
    scan_count = 0
    signal_count = 0
    exec_count = 0
    last_minute = -1

    try:
        while True:
            now = datetime.now(EST)

            scan_this_minute = (now.second < 5 and now.minute != last_minute)
            if not scan_this_minute:
                time.sleep(0.5)
                continue

            last_minute = now.minute
            scan_count += 1

            positions = get_positions()
            acct = mt5.account_info()
            equity = acct.equity if acct else 0

            avg_rr = round(daily_stats["rr_total"] / daily_stats["entries"], 2) if daily_stats["entries"] > 0 else 0.0
            log.info("[%s] Scan #%d | Equity: $%.2f | Pos: %d | Sig: %d | Exec: %d | Daily: W%d L%d %+.1fp AvgRR=%.2f",
                     now.strftime("%H:%M:%S"), scan_count, equity, len(positions), signal_count, exec_count,
                     daily_stats["wins"], daily_stats["losses"], daily_stats["pips"], avg_rr)

            for sym in symbols:
                try:
                    bars = get_bars(sym, 500)
                    if not bars:
                        continue

                    latest = bars[-1]
                    engine_bar = mt5_bar_to_engine_bar(latest)
                    st = st_engines[sym]
                    st_sig = st.process_bar(engine_bar)

                    if st_sig:
                        signal_count += 1
                        direction = "BUY" if st_sig.direction == TradeDirection.LONG else "SELL"

                        sig_dict = {
                            "engine": "SymmetryTrap",
                            "symbol": sym,
                            "direction": direction,
                            "entry": st_sig.entry_price,
                            "sl": st_sig.sl_price,
                            "tp": st_sig.tp_price,
                            "event": st_sig.event,
                            "loop": st_sig.loop_count,
                            "time": now.strftime("%Y-%m-%d %H:%M:%S"),
                        }
                        emit_signal(sig_dict)

                        if st_sig.event == "ENTRY":
                            # Close pre-existing position
                            existing_pos = get_positions()
                            old_on_sym = [p for p in existing_pos if p["symbol"] == sym and p["magic"] == 20260601]
                            for op in old_on_sym:
                                log.info("[%s] Closing pre-existing position before new entry: #%s %s @ %.5f",
                                         sym, op["ticket"], op["type"], op["open_price"])
                                close_position(op["ticket"])
                            stale_keys = [k for k in active_trades if k[0] == sym]
                            for sk in stale_keys:
                                del active_trades[sk]

                            sl_p = to_pips(abs(st_sig.sl_price - st_sig.entry_price), sym)
                            tp_p = to_pips(abs(st_sig.tp_price - st_sig.entry_price), sym)
                            rr = round(tp_p / sl_p, 2) if sl_p > 0 else 0.0
                            log.info("ST ENTRY: %s %s @ %.5f | SL=%.1fp TP=%.1fp RR=%.2f",
                                     direction, sym, st_sig.entry_price, sl_p, tp_p, rr)

                            ticket = send_order(sym, direction, lot_size,
                                            st_sig.sl_price, st_sig.tp_price,
                                            f"CEREBUS-ST-L{st_sig.loop_count}",
                                            no_sl=True)
                            if ticket:
                                exec_count += 1
                                daily_stats["entries"] += 1
                                daily_stats["rr_total"] += rr
                                active_trades[(sym, "ST")] = {
                                    "ticket": ticket,
                                    "direction": direction,
                                    "entry": st_sig.entry_price,
                                    "sl": st_sig.sl_price,
                                    "tp": st_sig.tp_price,
                                    "engine": "ST",
                                    "sl_moved": False,
                                }

                        elif st_sig.event in ("TP_HIT", "SL_HIT", "KILL_SWITCH"):
                            key = (sym, "ST")
                            if key in active_trades:
                                trade = active_trades[key]
                                entry = trade["entry"]
                                direction = trade["direction"]
                                tick = mt5.symbol_info_tick(sym)
                                if tick:
                                    close_price = tick.bid if direction == "BUY" else tick.ask
                                    pnl_pips = to_pips(close_price - entry, sym) if direction == "BUY" else to_pips(entry - close_price, sym)
                                else:
                                    pnl_pips = 0.0
                                won = st_sig.event == "TP_HIT"
                                daily_stats["pips"] += pnl_pips
                                if won:
                                    daily_stats["wins"] += 1
                                else:
                                    daily_stats["losses"] += 1
                                log.info("ST CLOSE [%s]: %s %s | PnL: %+.1fp | Daily: W%d L%d %+.1fp",
                                         st_sig.event, direction, sym, pnl_pips,
                                         daily_stats["wins"], daily_stats["losses"], daily_stats["pips"])
                                close_position(trade["ticket"])
                                del active_trades[key]

                except Exception as sym_err:
                    log.error("[%s] Symbol error: %s — skipping", sym, sym_err)

            time.sleep(1)

    except KeyboardInterrupt:
        log.info("Stopped by user.")
    except Exception as e:
        log.error("FATAL: %s", e, exc_info=True)
        log.error("Exiting. Use process_registry.py to restart.")
    finally:
        try:
            mt5.shutdown()
        except Exception:
            pass
        _release_singleton()
        avg_rr = round(daily_stats["rr_total"] / daily_stats["entries"], 2) if daily_stats["entries"] > 0 else 0.0
        log.info("Shutdown. %d scans | %d signals | %d executed | Daily: W%d L%d %+.1fp AvgRR=%.2f",
                 scan_count, signal_count, exec_count,
                 daily_stats["wins"], daily_stats["losses"], daily_stats["pips"], avg_rr)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="CEREBUS Clean Bridge — No Duplicates")
    parser.add_argument("--symbols", default=",".join(TOP7_ST))
    parser.add_argument("--lot-size", type=float, default=0.01)
    args = parser.parse_args()

    symbols = [s.strip() for s in args.symbols.split(",")]

    # SINGLETON CHECK — MUST RUN BEFORE ANYTHING ELSE
    if not _acquire_singleton():
        sys.exit(1)

    run_live(symbols, args.lot_size)