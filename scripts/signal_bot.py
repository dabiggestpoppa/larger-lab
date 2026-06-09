"""
SIGNAL BOT — Trading Engine -> Telegram Forwarder
===================================================
Watches multiple signal sources and forwards to Telegram:
  1. quant-lab/mt5/live_logs/signals.jsonl — ST engine (live trades)
  2. quant-lab/mt5/live_logs/signals.jsonl — OCC+Buffer engine
  3. quant-lab/mt5/live_logs/mlr_signals.jsonl — MLR scanner (tier + level alerts)

Uses HERMES_TELEGRAM_TOKEN from .env (independent of PO/OC2).
Auto-discovers chat_id on first message if not set.

Engines:
  - SymmetryTrap: Live ST signals (ENTRY, TP_HIT, SL_HIT, KILL_SWITCH)
  - OCCBuffer: OCC+Buffer signals
  - MLR: Monday London Range scanner (TIER_SCAN, LEVEL_HIT)

Usage:
    python scripts/signal_bot.py              # run continuously
    python scripts/signal_bot.py --once       # send latest signal and exit
    python scripts/signal_bot.py --test       # send test message and exit
"""
import os
import sys
import json
import time
import ctypes
import requests
from pathlib import Path
from datetime import datetime

REPO_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = REPO_ROOT / ".env"
SIGNALS_FILES = [
    REPO_ROOT / "quant-lab" / "mt5" / "live_logs" / "signals.jsonl",
    REPO_ROOT / "quant-lab" / "mt5" / "live_logs" / "mlr_signals.jsonl",
]

# ─── SINGLETON ENFORCEMENT ───────────────────────────────────────────────
PID_FILE = REPO_ROOT / ".signal_bot.pid"
MUTEX_NAME = "Global\\SignalBot_Singleton"

def _kill_all_signal_bot_processes():
    """Kill ALL other signal_bot.py processes (except self)."""
    kernel32 = ctypes.windll.kernel32
    PROCESS_TERMINATE = 0x0001
    my_pid = os.getpid()
    killed = 0
    try:
        result = __import__('subprocess').run(
            ["powershell", "-Command",
             "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
             "Where-Object { $_.CommandLine -like '*signal_bot*' -and $_.ProcessId -ne " + str(my_pid) + " } | "
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
                    log(f"Killed duplicate signal_bot PID {pid}")
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

    # Step 1: Kill ALL other signal_bot processes first
    _kill_all_signal_bot_processes()

    # Step 2: Create Windows named mutex (true OS-level singleton)
    mutex = kernel32.CreateMutexW(None, False, MUTEX_NAME)
    last_error = kernel32.GetLastError()

    if last_error == 183:  # ERROR_ALREADY_EXISTS
        if mutex:
            kernel32.CloseHandle(mutex)
        log("[FATAL] Another signal_bot instance holds the mutex. Exiting.")
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

if ENV_PATH.exists():
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

os.environ.setdefault("PYTHONIOENCODING", "utf-8")

TOKEN = os.environ.get("HERMES_TELEGRAM_TOKEN", "")
CHAT_ID = os.environ.get("HERMES_TELEGRAM_CHAT_ID", "")


def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def discover_chat_id(token):
    try:
        r = requests.get(
            f"https://api.telegram.org/bot{token}/getUpdates?limit=1&timeout=5",
            timeout=10,
        )
        data = r.json()
        if data.get("ok") and data.get("result"):
            cid = str(data["result"][0]["message"]["chat"]["id"])
            log(f"Auto-discovered chat_id: {cid}")
            return cid
    except Exception as e:
        log(f"getUpdates error: {e}")
    return ""


def send_telegram(text):
    global CHAT_ID
    if not TOKEN:
        log("ERROR: HERMES_TELEGRAM_TOKEN not set")
        return False
    if not CHAT_ID:
        CHAT_ID = discover_chat_id(TOKEN)
        if not CHAT_ID:
            log("ERROR: No CHAT_ID")
            return False
    try:
        for chunk in [text[i:i+4096] for i in range(0, len(text), 4096)]:
            r = requests.post(
                f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                json={"chat_id": CHAT_ID, "text": chunk, "parse_mode": "HTML"},
                timeout=15,
            )
            if not r.json().get("ok"):
                log(f"Telegram error: {r.json()}")
                return False
        return True
    except Exception as e:
        log(f"Send error: {e}")
        return False


def format_signal(sig):
    event = sig.get("event", "?")
    symbol = sig.get("symbol", "?").replace(".PRO", "")
    direction = sig.get("direction", "?")
    entry = sig.get("entry", 0)
    sl = sig.get("sl", 0)
    tp = sig.get("tp", 0)
    ts = sig.get("time", "?")
    engine = sig.get("engine", "?")
    pnl_pips = sig.get("pnl_pips", None)
    pnl_usd = sig.get("pnl_usd", None)

    if event == "ENTRY":
        emoji = "BUY" if direction == "BUY" else "SELL"
        label = f"ENTRY {direction}"
    elif event == "TP_HIT":
        emoji = "TP"
        label = "TAKE PROFIT"
    elif event == "SL_HIT":
        emoji = "SL"
        label = "STOP HIT"
    elif event == "KILL_SWITCH":
        emoji = "KS"
        label = "KILL SWITCH"
    else:
        emoji = "SIG"
        label = event

    def calc_pips(a, b, sym):
        pip = 0.01 if "JPY" in sym else 0.0001
        return round(abs(a - b) / pip, 1) if pip else 0

    sl_pips = calc_pips(entry, sl, symbol) if sl else 0
    tp_pips = calc_pips(entry, tp, symbol) if tp else 0
    rr = round(tp_pips / sl_pips, 2) if sl_pips > 0 else 0

    # ST engine: SL is profit-lock (SL_HIT = profit taken at impulse extreme)
    is_profit_lock = engine == "SymmetryTrap" and event == "SL_HIT"

    lines = [
        f"<b>{label}</b> — {symbol}",
        f"",
        f"Engine: {engine}",
        f"Direction: <b>{direction}</b>",
        f"Entry: {entry}",
        f"SL: {sl} ({sl_pips}p){' [PROFIT-LOCK]' if is_profit_lock else ''}",
        f"TP: {tp} ({tp_pips}p)",
        f"RR: {rr}",
    ]

    if event in ("TP_HIT", "SL_HIT", "KILL_SWITCH"):
        if pnl_pips is not None:
            sign = "+" if pnl_pips >= 0 else ""
            lines.append(f"PnL: {sign}{pnl_pips}p")
        if pnl_usd is not None:
            sign = "+" if pnl_usd >= 0 else ""
            lines.append(f"PnL: {sign}${pnl_usd:.2f}")
        if is_profit_lock and pnl_pips is not None and pnl_pips > 0:
            lines.append(f"Profit lock triggered")

    lines.append(f"")
    lines.append(f"{ts}")

    if event == "ENTRY":
        loop = sig.get("loop", "?")
        lines.insert(3, f"Loop: {loop}")

    return "\n".join(lines)


def tail_signals(filepath, last_pos=0):
    if not filepath.exists():
        return last_pos, []
    with open(filepath, "r", encoding="utf-8") as f:
        f.seek(last_pos)
        lines = f.readlines()
        new_pos = f.tell()
    signals = []
    for line in lines:
        line = line.strip()
        if line:
            try:
                signals.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return new_pos, signals


def format_mlr_signal(sig):
    """Format MLR scanner signals for Telegram."""
    event = sig.get("event", "?")
    msg = sig.get("message", "")

    if event == "MLR_TIER_SCAN":
        # Tier scan is already formatted as pre-formatted text
        return msg
    elif event == "MLR_LEVEL_HIT":
        # Level hit is also pre-formatted
        return msg
    else:
        return f"MLR: {json.dumps(sig, default=str)}"


def run_once():
    """Send latest signal from any source."""
    latest = None
    for sf in SIGNALS_FILES:
        if not sf.exists():
            continue
        with open(sf, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]
        if lines:
            try:
                sig = json.loads(lines[-1])
                if latest is None or sig.get("time", "") > latest.get("time", ""):
                    latest = sig
            except json.JSONDecodeError:
                pass
    if latest is None:
        log("No signals found")
        return False
    engine = latest.get("engine", "?")
    if engine == "MLR":
        msg = format_mlr_signal(latest)
    else:
        msg = format_signal(latest)
    log(f"Sending: {latest.get('event')} {latest.get('symbol', '')} [{engine}]")
    return send_telegram(msg)


def run_daemon():
    log("=" * 50)
    log("SIGNAL BOT — Multi-Engine Telegram Forwarder")
    log(f"Token: {TOKEN[:10]}...{TOKEN[-5:]}")
    for sf in SIGNALS_FILES:
        log(f"Watching: {sf.name}")
    log("=" * 50)

    if not TOKEN:
        log("FATAL: HERMES_TELEGRAM_TOKEN not set")
        sys.exit(1)

    # Track position and last signal per file
    positions = {}
    last_keys = {}
    for sf in SIGNALS_FILES:
        pos = 0
        if sf.exists():
            with open(sf, "r", encoding="utf-8") as f:
                f.seek(0, 2)
                pos = f.tell()
        positions[sf] = pos
        last_keys[sf] = None

    send_telegram(
        "Signal Bot Started\n\n"
        "Engines:\n"
        "  1. SymmetryTrap (live trades)\n"
        "  2. OCC+Buffer\n"
        "  3. MLR Scanner (tier + level alerts)\n\n"
        "New signals will appear here in real-time."
    )

    log("Watching for new signals...")
    try:
        while True:
            for sf in SIGNALS_FILES:
                if not sf.exists():
                    continue

                positions[sf], signals = tail_signals(sf, positions[sf])

                for sig in signals:
                    engine = sig.get("engine", "?")
                    sig_key = (sig.get("symbol", ""), sig.get("event", ""), sig.get("time", ""), engine)
                    if sig_key == last_keys[sf]:
                        continue
                    last_keys[sf] = sig_key

                    # Format based on engine
                    if engine == "MLR":
                        msg = format_mlr_signal(sig)
                    else:
                        msg = format_signal(sig)

                    event = sig.get("event", "?")
                    symbol = sig.get("symbol", "")
                    log(f"Signal: {event} {symbol} [{engine}]")
                    send_telegram(msg)

            time.sleep(5)

    except KeyboardInterrupt:
        log("Stopped.")
        _release_singleton()


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--test" in args:
        log("Sending test message...")
        ok = send_telegram(
            "Signal Bot Test\n\n"
            "Signal forwarder is working!"
        )
        log(f"Test: {'OK' if ok else 'FAILED'}")
    elif "--once" in args:
        run_once()
    else:
        # SINGLETON CHECK — MUST RUN BEFORE DAEMON
        if not _acquire_singleton():
            sys.exit(1)
        try:
            run_daemon()
        finally:
            _release_singleton()
