#!/usr/bin/env python3
r"""
CEREBUS CLEAN BRIDGE — No Duplicates, No UV, No Bullshit
========================================================
Thin transport layer: MT5 bars -> SymmetryTrap engine -> MT5 orders

SINGLETON: Kills ALL other bridge processes on startup. No mutex needed.
The bridge is started by process_registry.py which also enforces singleton.

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

# --- FORCE UTF-8 ---
sys.stdout.reconfigure(encoding="utf-8")
os.environ["PYTHONIOENCODING"] = "utf-8"

# --- KILL DUPLICATES ON STARTUP ---
def _kill_other_bridges():
    """Kill ALL other clean_bridge.py processes (not self)."""
    my_pid = os.getpid()
    killed = 0
    try:
        result = __import__('subprocess').run(
            ["tasklist", "/FI", "IMAGENAME eq python.exe", "/FO", "CSV", "/NH"],
            capture_output=True, text=True, timeout=10)
        for line in result.stdout.strip().split('\n'):
            line = line.strip()
            if not line or 'python.exe' not in line.lower():
                continue
            parts = line.split(',')
            if len(parts) < 2:
                continue
            try:
                pid = int(parts[1].strip('"'))
                if pid == my_pid:
                    continue
                # Check command line for our script name
                cmd_result = __import__('subprocess').run(
                    ["wmic", "process", "where", f"ProcessId={pid}", "get", "CommandLine", "/FORMAT:CSV"],
                    capture_output=True, text=True, timeout=5)
                cmd_line = cmd_result.stdout.strip()
                if 'clean_bridge' in cmd_line or 'cerebus_live_bridge' in cmd_line:
                    handle = ctypes.windll.kernel32.OpenProcess(0x0001, False, pid)
                    if handle:
                        ctypes.windll.kernel32.TerminateProcess(handle, 1)
                        ctypes.windll.kernel32.CloseHandle(handle)
                        killed += 1
                        print(f"[CLEAN BRIDGE] Killed duplicate PID {pid}")
            except (ValueError, OSError, IndexError):
                pass
    except Exception:
        pass
    if killed > 0:
        time.sleep(3)
    return killed

try:
    _kill_other_bridges()
except Exception as _e:
    print(f"[CLEAN BRIDGE] Kill duplicates error: {_e}")

# --- LOGGING ---
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

# --- MT5 IMPORT ---
import pytz
import MetaTrader5 as mt5

EST = pytz.timezone("US/Eastern")

# --- ENGINE IMPORT ---
_qlab = str(Path(__file__).parent.parent)  # quant-lab/
if _qlab not in sys.path:
    sys.path.insert(0, _qlab)
from engines.symmetry_trap import SymmetryTrapEngine, Bar, TradeDirection
# deploy_config is in quant-lab/mt5/ (this script's directory), imported in run_live()

# --- CONFIG ---
TOP7_ST = ["EURJPY.PRO", "EURNZD.PRO", "GBPNZD.PRO",
           "EURAUD.PRO", "GBPAUD.PRO", "GBPCAD.PRO", "FR40.PRO"]

# --- MT5 HELPERS ---
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
        "open": float(r["open"]), "high": float(r["high"]),
        "low": float(r["low"]), "close": float(r["close"]),
        "volume": int(r["tick_volume"]), "spread": int(r["spread"]),
    } for r in rates]

def mt5_bar_to_engine_bar(mt5_bar: dict) -> Bar:
    return Bar(timestamp=mt5_bar["time"], open=mt5_bar["open"],
               high=mt5_bar["high"], low=mt5_bar["low"], close=mt5_bar["close"])

def pip_size(symbol: str) -> float:
    if "XAU" in symbol: return 0.01
    if "XAG" in symbol: return 0.001
    if "JPY" in symbol: return 0.01
    return 0.0001

def to_pips(price_diff: float, symbol: str) -> float:
    pip = pip_size(symbol)
    if pip == 0: return 0.0
    return round(price_diff / pip, 1)

def get_positions() -> list:
    positions = mt5.positions_get()
    if positions is None: return []
    return [{"ticket": p.ticket, "symbol": p.symbol,
             "type": "BUY" if p.type == mt5.ORDER_TYPE_BUY else "SELL",
             "volume": p.volume, "open_price": p.price_open,
             "current_price": p.price_current, "sl": p.sl, "tp": p.tp,
             "profit": p.profit, "magic": p.magic} for p in positions]

def check_autotrading() -> bool:
    info = mt5.terminal_info()
    return info is not None and info.trade_allowed

def send_order(symbol, direction, volume, sl, tp, comment, no_sl=False):
    if not check_autotrading():
        log.warning("MT5 AutoTrading DISABLED"); return False
    info = mt5.symbol_info(symbol)
    if info is None or not info.visible:
        mt5.symbol_select(symbol, True); time.sleep(1)
        info = mt5.symbol_info(symbol)
    if info is None: log.error("Symbol %s not found", symbol); return False
    tick = mt5.symbol_info_tick(symbol)
    if tick is None: log.error("No tick for %s", symbol); return False

    order_type = mt5.ORDER_TYPE_BUY if direction == "BUY" else mt5.ORDER_TYPE_SELL
    price = tick.ask if direction == "BUY" else tick.bid
    sl_pips = to_pips(abs(sl - price), symbol) if sl > 0 else 0.0
    tp_pips = to_pips(abs(tp - price), symbol)
    rr = round(tp_pips / sl_pips, 2) if sl_pips > 0 else 0.0

    if rr < 1.0:
        log.warning("RR GATE: REJECTED %s %s RR=%.2f", direction, symbol, rr); return False

    request = {
        "action": mt5.TRADE_ACTION_DEAL, "symbol": symbol, "volume": volume,
        "type": order_type, "price": price, "tp": round(tp, info.digits),
        "deviation": 10, "magic": 20260601, "comment": comment,
        "type_time": mt5.ORDER_TIME_GTC, "type_filling": mt5.ORDER_FILLING_IOC,
    }
    if not no_sl: request["sl"] = round(sl, info.digits)

    result = mt5.order_send(request)
    if result is None: log.error("order_send None: %s", mt5.last_error()); return False
    if result.retcode == mt5.TRADE_RETCODE_DONE:
        log.info("Order OK: %s %s ticket=%d", direction, symbol, result.order)
        return result.order
    log.error("Order FAILED: %s %s retcode=%d", direction, symbol, result.retcode)
    return False

def close_position(ticket):
    positions = mt5.positions_get()
    if positions is None: return False
    pos = next((p for p in positions if p.ticket == ticket), None)
    if pos is None: return False
    tick = mt5.symbol_info_tick(pos.symbol)
    if tick is None: return False
    close_price = tick.bid if pos.type == mt5.ORDER_TYPE_BUY else tick.ask
    request = {
        "action": mt5.TRADE_ACTION_DEAL, "symbol": pos.symbol,
        "volume": pos.volume,
        "type": mt5.ORDER_TYPE_SELL if pos.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY,
        "position": ticket, "price": close_price, "deviation": 10,
        "magic": 20260601, "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    result = mt5.order_send(request)
    if result and result.retcode == mt5.TRADE_RETCODE_DONE:
        log.info("Closed ticket %d", ticket); return True
    log.error("Close FAILED: ticket=%d", ticket); return False

def calc_asian_range(bars):
    if not bars: return (0.0, 0.0)
    now = datetime.now(EST)
    if now.hour >= 3:
        session_end = now.replace(hour=3, minute=0, second=0, microsecond=0)
    else:
        yesterday = now - timedelta(days=1)
        session_end = yesterday.replace(hour=3, minute=0, second=0, microsecond=0)
    session_start = session_end - timedelta(hours=8)
    asian = [b for b in bars if b["time"] >= session_start and b["time"] <= session_end]
    if not asian: return (0.0, 0.0)
    return (max(b["high"] for b in asian), min(b["low"] for b in asian))

SIGNAL_FILE = LOG_DIR / "signals.jsonl"

def emit_signal(sig):
    with open(SIGNAL_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(sig) + "\n")

# --- MAIN LOOP ---
def run_live(symbols, lot_size=0.01):
    log.info("=" * 60)
    log.info("  CEREBUS CLEAN BRIDGE")
    log.info("  Symbols: %s", symbols)
    log.info("  Lot: %.2f", lot_size)
    log.info("  Started: %s", datetime.now(EST).strftime("%Y-%m-%d %H:%M:%S EST"))
    log.info("=" * 60)

    log.info("Step 1: Connecting to MT5...")
    if not mt5_connect():
        log.error("MT5 connection failed — exiting"); return
    log.info("Step 2: MT5 connected OK")

    from deploy_config import DEPLOYMENT_CONFIGS
    st_engines = {}
    for sym in symbols:
        ps = pip_size(sym)
        cfg = DEPLOYMENT_CONFIGS.get(sym, {})
        st_engines[sym] = SymmetryTrapEngine(pip_size=ps, symbol=sym, config=cfg)

    now = datetime.now(EST)
    for sym in symbols:
        bars = get_bars(sym, 500)
        if not bars:
            log.warning("[%s] No bars for session init", sym); continue
        ah, al = calc_asian_range(bars)
        if ah > 0 and al < 99999:
            st_engines[sym].initialize_session(ah, al)
            ar_pips = (ah - al) / pip_size(sym)
            log.info("[%s] Session INIT: AR=%.1f pips | tier=%s", sym, ar_pips, st_engines[sym].tier_name)
        else:
            last_close = bars[-1]["close"]
            pip = pip_size(sym)
            st_engines[sym].initialize_session(last_close + 10 * pip, last_close - 10 * pip)
            log.warning("[%s] AR unavailable — defaulting to T1", sym)

    active_trades = {}
    daily_stats = {"date": now.strftime("%Y-%m-%d"), "entries": 0, "wins": 0, "losses": 0, "pips": 0.0, "rr_total": 0.0}
    scan_count = signal_count = exec_count = 0
    last_minute = -1

    try:
        while True:
            now = datetime.now(EST)
            if not (now.second < 5 and now.minute != last_minute):
                time.sleep(0.5); continue

            last_minute = now.minute
            scan_count += 1
            positions = get_positions()
            acct = mt5.account_info()
            equity = acct.equity if acct else 0
            avg_rr = round(daily_stats["rr_total"] / daily_stats["entries"], 2) if daily_stats["entries"] > 0 else 0.0

            log.info("[%s] Scan #%d | Equity: $%.2f | Pos: %d | Sig: %d | Exec: %d | W%d L%d %+.1fp AvgRR=%.2f",
                     now.strftime("%H:%M:%S"), scan_count, equity, len(positions),
                     signal_count, exec_count, daily_stats["wins"], daily_stats["losses"],
                     daily_stats["pips"], avg_rr)

            for sym in symbols:
                try:
                    bars = get_bars(sym, 500)
                    if not bars: continue
                    engine_bar = mt5_bar_to_engine_bar(bars[-1])
                    st = st_engines[sym]
                    st_sig = st.process_bar(engine_bar)

                    if st_sig:
                        signal_count += 1
                        direction = "BUY" if st_sig.direction == TradeDirection.LONG else "SELL"
                        emit_signal({"engine": "SymmetryTrap", "symbol": sym, "direction": direction,
                                     "entry": st_sig.entry_price, "sl": st_sig.sl_price, "tp": st_sig.tp_price,
                                     "event": st_sig.event, "loop": st_sig.loop_count,
                                     "time": now.strftime("%Y-%m-%d %H:%M:%S")})

                        if st_sig.event == "ENTRY":
                            for op in [p for p in get_positions() if p["symbol"] == sym and p["magic"] == 20260601]:
                                close_position(op["ticket"])
                            for sk in [k for k in active_trades if k[0] == sym]: del active_trades[sk]
                            sl_p = to_pips(abs(st_sig.sl_price - st_sig.entry_price), sym)
                            tp_p = to_pips(abs(st_sig.tp_price - st_sig.entry_price), sym)
                            rr = round(tp_p / sl_p, 2) if sl_p > 0 else 0.0
                            log.info("ST ENTRY: %s %s @ %.5f | SL=%.1fp TP=%.1fp RR=%.2f",
                                     direction, sym, st_sig.entry_price, sl_p, tp_p, rr)
                            ticket = send_order(sym, direction, lot_size, st_sig.sl_price, st_sig.tp_price,
                                                f"CEREBUS-ST-L{st_sig.loop_count}", no_sl=True)
                            if ticket:
                                exec_count += 1; daily_stats["entries"] += 1; daily_stats["rr_total"] += rr
                                active_trades[(sym, "ST")] = {"ticket": ticket, "direction": direction,
                                    "entry": st_sig.entry_price, "sl": st_sig.sl_price, "tp": st_sig.tp_price,
                                    "engine": "ST", "sl_moved": False}

                        elif st_sig.event in ("TP_HIT", "SL_HIT", "KILL_SWITCH"):
                            key = (sym, "ST")
                            if key in active_trades:
                                trade = active_trades[key]
                                tick = mt5.symbol_info_tick(sym)
                                if tick:
                                    cp = tick.bid if trade["direction"] == "BUY" else tick.ask
                                    pnl = to_pips(cp - trade["entry"], sym) if trade["direction"] == "BUY" else to_pips(trade["entry"] - cp, sym)
                                else: pnl = 0.0
                                won = st_sig.event == "TP_HIT"
                                daily_stats["pips"] += pnl
                                if won: daily_stats["wins"] += 1
                                else: daily_stats["losses"] += 1
                                log.info("ST CLOSE [%s]: %s %s | PnL: %+.1fp | W%d L%d %+.1fp",
                                         st_sig.event, trade["direction"], sym, pnl,
                                         daily_stats["wins"], daily_stats["losses"], daily_stats["pips"])
                                close_position(trade["ticket"])
                                del active_trades[key]
                except Exception as e:
                    log.error("[%s] Error: %s", sym, e)

            time.sleep(1)

    except KeyboardInterrupt:
        log.info("Stopped by user.")
    except Exception as e:
        log.error("FATAL: %s", e, exc_info=True)
    finally:
        try: mt5.shutdown()
        except: pass
        avg_rr = round(daily_stats["rr_total"] / daily_stats["entries"], 2) if daily_stats["entries"] > 0 else 0.0
        log.info("Shutdown. %d scans | %d signals | %d exec | W%d L%d %+.1fp AvgRR=%.2f",
                 scan_count, signal_count, exec_count,
                 daily_stats["wins"], daily_stats["losses"], daily_stats["pips"], avg_rr)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="CEREBUS Clean Bridge")
    parser.add_argument("--symbols", default=",".join(TOP7_ST))
    parser.add_argument("--lot-size", type=float, default=0.01)
    args = parser.parse_args()
    symbols = [s.strip() for s in args.symbols.split(",")]
    run_live(symbols, args.lot_size)
