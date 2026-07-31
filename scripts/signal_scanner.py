"""
SIGNAL SCANNER — OCC Extreme + Buffer (Signal-Only, No Execution)
===================================================================
Scans MT5 live data using SymmetryTrapEngine with REGULAR stop loss
(OCC extreme + spread buffer on the LOSS side, not profit-lock).

Connects to MT5 for data only — does NOT place orders.
Signals forwarded to Telegram via @hermososabot.

SL LOGIC (regular stop loss):
  - For LONG:  SL = entry - (impulse_extreme_to_entry_distance + spread_buffer)
  - For SHORT: SL = entry + (entry_to_impulse_extreme_distance + spread_buffer)
  - This puts SL on the OPPOSITE side of entry = real stop loss

Usage:
    python scripts/signal_scanner.py              # run continuously
    python scripts/signal_scanner.py --once       # single scan, then exit
    python scripts/signal_scanner.py --test       # test Telegram, then exit
"""
import os
import sys
import json
import time
import requests
import logging
from pathlib import Path
from datetime import datetime, timezone

# ── Paths ──────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = REPO_ROOT / ".env"
SIGNALS_FILE = REPO_ROOT / "quant-lab" / "mt5" / "live_logs" / "signals.jsonl"

# ── Load .env ──────────────────────────────────────────────────────
if ENV_PATH.exists():
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

os.environ.setdefault("PYTHONIOENCODING", "utf-8")

# ── Config ─────────────────────────────────────────────────────────
TOKEN = os.environ.get("HERMES_TELEGRAM_TOKEN", "")
CHAT_ID = os.environ.get("HERMES_TELEGRAM_CHAT_ID", "")

# Symbols to scan (the ones you actually trade)
SYMBOLS = [
    "EURUSD.PRO",
    "USDCHF.PRO",
    "BTCUSD",
]

# OCC + Buffer SL config
SPREAD_BUFFER_PIPS = {
    "EURUSD.PRO": 1.5,
    "USDCHF.PRO": 2.0,
    "BTCUSD": 50.0,
}

# Per-pair tier config (from sweep data / asset_configs.py)
# AU is ALWAYS per-pair, never universal.
PAIR_TIER_CONFIG = {
    "EURUSD.PRO":  {"T1": {"au": 10, "ar_max": 20}, "T2": {"au": 12, "ar_max": 30}, "T3": {"au": 15, "ar_max": 45}},
    "USDCHF.PRO": {"T1": {"au": 11, "ar_max": 20}, "T2": {"au": 15, "ar_max": 30}, "T3": {"au": 20, "ar_max": 45}},
    "BTCUSD":     {"T1": {"au": 205, "ar_max": 400}, "T2": {"au": 545, "ar_max": 800}, "T3": {"au": 1160, "ar_max": 1500}},
}

SCAN_INTERVAL = 60  # seconds between scans

# ── Logging ────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("signal_scanner")


def discover_chat_id(token):
    try:
        r = requests.get(
            f"https://api.telegram.org/bot{token}/getUpdates?limit=1&timeout=5",
            timeout=10,
        )
        data = r.json()
        if data.get("ok") and data.get("result"):
            cid = str(data["result"][0]["message"]["chat"]["id"])
            log.info(f"Auto-discovered chat_id: {cid}")
            return cid
    except Exception as e:
        log.error(f"getUpdates error: {e}")
    return ""


def send_telegram(text):
    global CHAT_ID
    if not TOKEN:
        log.error("HERMES_TELEGRAM_TOKEN not set")
        return False
    if not CHAT_ID:
        CHAT_ID = discover_chat_id(TOKEN)
        if not CHAT_ID:
            log.error("No CHAT_ID — message the bot first")
            return False
    try:
        for chunk in [text[i:i+4096] for i in range(0, len(text), 4096)]:
            r = requests.post(
                f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                json={"chat_id": CHAT_ID, "text": chunk, "parse_mode": "HTML"},
                timeout=15,
            )
            if not r.json().get("ok"):
                log.error(f"Telegram error: {r.json()}")
                return False
        return True
    except Exception as e:
        log.error(f"Send error: {e}")
        return False


def get_pip_size(symbol):
    s = symbol.upper()
    if "BTC" in s:
        return 1.0
    if "JPY" in s:
        return 0.01
    return 0.0001


def calc_regular_sl(entry, impulse_extreme, direction, symbol):
    """
    Calculate REGULAR stop loss (on the LOSS side of entry).
    
    For LONG:  SL = entry - |entry - impulse_extreme| - spread_buffer
    For SHORT: SL = SL = entry + |impulse_extreme - entry| - spread_buffer
    
    This is the OCC extreme + buffer method — SL is on the opposite side
    of entry from the impulse, with a spread buffer.
    """
    pip = get_pip_size(symbol)
    buffer_pips = SPREAD_BUFFER_PIPS.get(symbol, 2.0)
    buffer_price = buffer_pips * pip
    
    if direction == "BUY":
        # SL below entry: entry - (entry - impulse_extreme) - buffer
        # = impulse_extreme - buffer
        sl = impulse_extreme - buffer_price
    else:
        # SL above entry: entry + (impulse_extreme - entry) + buffer
        # = impulse_extreme + buffer
        sl = impulse_extreme + buffer_price
    
    return round(sl, 5)


def format_signal(sig):
    """Format signal for Telegram."""
    symbol = sig.get("symbol", "?").replace(".PRO", "")
    direction = sig.get("direction", "?")
    entry = sig.get("entry", 0)
    sl = sig.get("sl", 0)
    tp = sig.get("tp", 0)
    ts = sig.get("time", "?")
    au = sig.get("au", 0)
    tier = sig.get("tier", "?")
    sl_type = sig.get("sl_type", "REGULAR")

    emoji = "🟢" if direction == "BUY" else "🔴"

    # Calculate distances
    pip = get_pip_size(sig.get("symbol", ""))
    sl_pips = round(abs(entry - sl) / pip, 1) if pip else 0
    tp_pips = round(abs(tp - entry) / pip, 1) if pip else 0
    rr = round(tp_pips / sl_pips, 2) if sl_pips > 0 else 0

    lines = [
        f"{emoji} <b>ENTRY {direction}</b> — {symbol}",
        f"",
        f"Tier: {tier} | AU: {au}p",
        f"Entry: {entry}",
        f"SL: {sl} ({sl_pips}p) [{sl_type}]",
        f"TP: {tp} ({tp_pips}p)",
        f"RR: {rr}",
        f"",
        f"⏰ {ts}",
    ]
    return "\n".join(lines)


def run_scan():
    """Run a single scan cycle using MT5 data."""
    try:
        import MetaTrader5 as mt5
    except ImportError:
        log.error("MetaTrader5 not installed")
        return []

    if not mt5.initialize():
        log.error(f"MT5 init failed: {mt5.last_error()}")
        return []

    signals = []
    now = datetime.now()

    for symbol in SYMBOLS:
        try:
            # Get recent bars
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, 500)
            if rates is None or len(rates) < 50:
                continue

            bars = []
            for r in rates:
                bars.append({
                    "time": datetime.fromtimestamp(int(r["time"])),
                    "open": float(r["open"]),
                    "high": float(r["high"]),
                    "low": float(r["low"]),
                    "close": float(r["close"]),
                })

            # Get symbol info for pip size
            info = mt5.symbol_info(symbol)
            if info is None:
                continue
            pip = get_pip_size(symbol)

            # Calculate Asian Range (7PM-3AM EST)
            # Simplified: use last 8 hours of bars
            recent = bars[-96:]  # ~8 hours of M5 bars
            if len(recent) < 10:
                continue

            ah = max(b["high"] for b in recent)
            al = min(b["low"] for b in recent)
            ar_pips = (ah - al) / pip

            # AR gate — per-pair max AR
            ar_gate_max = 1500 if "BTC" in symbol else 60
            if ar_pips > ar_gate_max or ar_pips < 3:
                continue

            # Classify tier — per-pair config
            pair_cfg = PAIR_TIER_CONFIG.get(symbol, PAIR_TIER_CONFIG["EURUSD.PRO"])
            if ar_pips < pair_cfg["T2"]["ar_max"]:
                tier = "T1"
                au = pair_cfg["T1"]["au"]
            elif ar_pips < pair_cfg["T3"]["ar_max"]:
                tier = "T2"
                au = pair_cfg["T2"]["au"]
            elif ar_pips <= 1500:
                tier = "T3"
                au = pair_cfg["T3"]["au"]
            else:
                continue

            # Find bias (first close outside Asian range after 3AM)
            bias = 0
            bias_bar = None
            for b in bars[-48:]:  # Last 4 hours
                if b["time"].hour >= 3 and b["time"].hour < 12:
                    if b["close"] > ah:
                        bias = 1
                        bias_bar = b
                        break
                    elif b["close"] < al:
                        bias = -1
                        bias_bar = b
                        break

            if bias == 0:
                continue

            # Find impulse in bias direction
            found_impulse = False
            impulse_bar = None
            start_idx = bars.index(bias_bar) if bias_bar else 0

            for i in range(start_idx + 1, len(bars)):
                b = bars[i]
                body_pips = abs(b["close"] - b["open"]) / pip

                if bias == 1 and b["close"] > b["open"] and body_pips >= au * 0.5:
                    # Check for opposite close (OCC)
                    if i + 1 < len(bars):
                        next_b = bars[i + 1]
                        if next_b["close"] < next_b["open"]:
                            found_impulse = True
                            impulse_bar = b
                            break
                elif bias == -1 and b["close"] < b["open"] and body_pips >= au * 0.5:
                    if i + 1 < len(bars):
                        next_b = bars[i + 1]
                        if next_b["close"] > next_b["open"]:
                            found_impulse = True
                            impulse_bar = b
                            break

            if not found_impulse:
                continue

            # Calculate entry, SL, TP
            entry = impulse_bar["close"]
            direction = "BUY" if bias == 1 else "SELL"

            # Impulse extreme (the far side of the impulse bar)
            if bias == 1:
                impulse_extreme = impulse_bar["high"]
            else:
                impulse_extreme = impulse_bar["low"]

            # REGULAR SL: OCC extreme + buffer on the LOSS side
            sl = calc_regular_sl(entry, impulse_extreme, direction, symbol)

            # TP: 1 AU in trade direction
            tp = entry + (au * pip * bias)

            sig = {
                "symbol": symbol,
                "direction": direction,
                "entry": round(entry, 5),
                "sl": round(sl, 5),
                "tp": round(tp, 5),
                "au": au,
                "tier": tier,
                "ar_pips": round(ar_pips, 1),
                "sl_type": "OCC+BUFFER",
                "time": now.strftime("%Y-%m-%d %H:%M:%S"),
            }
            signals.append(sig)
            log.info(f"Signal: {direction} {symbol} @ {entry} SL={sl} TP={tp}")

        except Exception as e:
            log.error(f"Error scanning {symbol}: {e}")

    mt5.shutdown()
    return signals


def run_once():
    """Single scan cycle."""
    log.info("Running signal scan...")
    signals = run_scan()
    if not signals:
        log.info("No signals found")
        return

    for sig in signals:
        msg = format_signal(sig)
        log.info(f"Sending: {sig['direction']} {sig['symbol']}")
        send_telegram(msg)


def run_daemon():
    """Continuous scanning loop."""
    log.info("=" * 50)
    log.info("SIGNAL SCANNER — OCC Extreme + Buffer")
    log.info(f"Symbols: {', '.join(SYMBOLS)}")
    log.info(f"Interval: {SCAN_INTERVAL}s")
    log.info("=" * 50)

    if not TOKEN:
        log.fatal("HERMES_TELEGRAM_TOKEN not set")
        sys.exit(1)

    # Send startup message
    send_telegram(
        "📡 <b>Signal Scanner Started</b>\n\n"
        f"Symbols: {', '.join(s.replace('.PRO','') for s in SYMBOLS)}\n"
        f"SL: OCC Extreme + Buffer (regular stop loss)\n"
        f"Interval: {SCAN_INTERVAL}s\n\n"
        "Scanning for signals..."
    )

    last_signals = {}  # dedup: (symbol, direction) -> time

    while True:
        try:
            signals = run_scan()
            for sig in signals:
                key = (sig["symbol"], sig["direction"])
                last_time = last_signals.get(key)
                if last_time == sig["time"]:
                    continue
                last_signals[key] = sig["time"]

                msg = format_signal(sig)
                send_telegram(msg)

            time.sleep(SCAN_INTERVAL)

        except KeyboardInterrupt:
            log.info("Stopped.")
            break
        except Exception as e:
            log.error(f"Scan error: {e}")
            time.sleep(10)


if __name__ == "__main__":
    args = sys.argv[1:]

    if "--test" in args:
        log.info("Sending test message...")
        ok = send_telegram(
            "🧪 <b>Signal Scanner Test</b>\n\n"
            "OCC Extreme + Buffer signal scanner is ready.\n"
            "No MT5 execution — signals only."
        )
        sys.exit(0 if ok else 1)

    if "--once" in args:
        run_once()
    else:
        run_daemon()
