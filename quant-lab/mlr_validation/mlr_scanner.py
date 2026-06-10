"""
MLR SCANNER — Lightweight Real-Time Market Tracker
===================================================
Runs alongside the live bridge. At London open (03:00 EST):
1. Scans all configured pairs
2. Calculates Asian Range + Tier
3. Computes MLR extension levels (-25%, -50%, -100%, 132% rekey)
4. Sends tier alert to Telegram via signals JSONL
5. Continuously scans during activation window (03:00-12:00 EST)
6. Sends alerts when key levels are hit

Integrates with signal_bot.py as a 3rd engine (MLR).
"""

import csv
import json
import os
import sys
import time
import logging
from collections import defaultdict
from datetime import datetime, timedelta, time, date
from pathlib import Path

# ─── CONFIG ─────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = REPO_ROOT / "quant-lab" / "data"
SIGNALS_FILE = REPO_ROOT / "quant-lab" / "mt5" / "live_logs" / "mlr_signals.jsonl"
LOG_FILE = REPO_ROOT / "quant-lab" / "mlr_validation" / "mlr_scanner.log"

# Pairs to scan — EURUSD + USDCHF + BTCUSD (MAD directive)
PAIRS = [
    "EURUSD", "USDCHF", "BTCUSD",
]

# MT5 symbol mapping
MT5_SYMBOLS = {p: p for p in PAIRS}

# Session times (EST)
ASIAN_START = 19    # 19:00 EST
ASIAN_END = 3       # 03:00 EST
LONDON_START = 3    # 03:00 EST
ACTIVATION_END = 12 # 12:00 EST

# Extension levels
EXTENSIONS = {"ext_25": 0.25, "ext_50": 0.50, "ext_100": 1.00}
REKEY_PCT = 1.32

# Tier config — per-pair native tiers (from asset_configs.py / sweep data)
# AU is ALWAYS per-pair, never universal.
PAIR_TIER_CONFIG = {
    "EURUSD": {
        "T1": {"ar_max": 60.0, "au": 10.0, "trigger": 12.0},
        "T2": {"ar_max": 60.0, "au": 12.0, "trigger": 15.0},
        "T3": {"ar_max": 60.0, "au": 15.0, "trigger": 19.0},
    },
    "USDCHF": {
        "T1": {"ar_max": 60.0, "au": 11.0, "trigger": 11.0},
        "T2": {"ar_max": 60.0, "au": 15.0, "trigger": 15.0},
        "T3": {"ar_max": 60.0, "au": 20.0, "trigger": 20.0},
    },
    "BTCUSD": {
        "T1": {"ar_max": 400.0, "au": 205.0, "trigger": 246.0},
        "T2": {"ar_max": 800.0, "au": 545.0, "trigger": 654.0},
        "T3": {"ar_max": 1500.0, "au": 1160.0, "trigger": 1392.0},
    },
}

# Default fallback
TIER_CONFIG = PAIR_TIER_CONFIG["EURUSD"]

# Pip sizes
def get_pip_size(symbol):
    s = symbol.upper().replace(".PRO", "")
    if "BTC" in s:
        return 1.0
    if "JPY" in s:
        return 0.01
    if any(x in s for x in ["XAU", "XAG", "LCO", "OIL"]):
        return 0.01  # Adjust for metals/oil
    return 0.0001


# ─── LOGGING ────────────────────────────────────────────────────────
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(str(LOG_FILE), encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("mlr_scanner")


# ─── DATA LOADING ───────────────────────────────────────────────────

def find_data_file(pair):
    """Find the best M5 data file for a pair."""
    patterns = [
        f"{pair}_M5_fetched.csv",
        f"{pair}PRO_M5_2023_2026.csv",
        f"{pair}PRO_M5_2023_2025.csv",
        f"{pair}PRO_M5_MAD.csv",
        f"{pair}PRO_M5.csv",
        f"{pair}_M5.csv",
    ]
    for p in patterns:
        fp = DATA_DIR / p
        if fp.exists():
            return str(fp)
    return None


def load_recent_bars(filepath, lookback_days=3):
    """Load recent M5 bars (last N days for performance)."""
    bars = []
    cutoff = datetime.now() - timedelta(days=lookback_days)

    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                ts = None
                for col in ["timestamp", "time", "datetime"]:
                    if col in row and row[col].strip():
                        val = row[col].strip()
                        try:
                            ts = datetime.fromtimestamp(int(val))
                            break
                        except ValueError:
                            try:
                                ts = datetime.fromisoformat(val)
                                break
                            except ValueError:
                                continue
                if ts is None:
                    continue
                if ts < cutoff:
                    continue

                h = float(row["high"])
                l = float(row["low"])
                if h <= 0 or l <= 0:
                    continue

                bars.append({
                    "dt": ts,
                    "date": ts.date(),
                    "hour": ts.hour,
                    "open": float(row["open"]),
                    "high": h,
                    "low": l,
                    "close": float(row["close"]),
                })
            except:
                continue

    bars.sort(key=lambda x: x["dt"])
    return bars


# ─── SESSION CALCULATIONS ───────────────────────────────────────────

def calc_asian_range(bars, target_date):
    """Calculate Asian Range: 19:00 EST prev day → 03:00 EST target_date."""
    prev_date = target_date - timedelta(days=1)
    session_bars = []

    for b in bars:
        if b["date"] == prev_date and b["hour"] >= ASIAN_START:
            session_bars.append(b)
        elif b["date"] == target_date and b["hour"] < ASIAN_END:
            session_bars.append(b)

    if len(session_bars) < 2:
        return None

    high = max(b["high"] for b in session_bars)
    low = min(b["low"] for b in session_bars)
    range_val = high - low

    if range_val <= 0:
        return None

    t0 = session_bars[-1]["close"]

    return {
        "date": target_date,
        "high": high,
        "low": low,
        "range": range_val,
        "t0_anchor": t0,
    }


def classify_tier(range_pips, pair):
    """Classify session into Tier based on Asian Range. Uses per-pair config."""
    cfg = PAIR_TIER_CONFIG.get(pair, TIER_CONFIG)
    for tier_name in ("T1", "T2", "T3"):
        if tier_name in cfg and range_pips <= cfg[tier_name]["ar_max"]:
            tcfg = cfg[tier_name]
            return tier_name, tcfg["au"], tcfg["trigger"]
    return "NO_GO", 0.0, 0.0


def calc_mlr_levels(t0, ar):
    """Calculate MLR extension levels (bidirectional)."""
    levels = {"t0": t0, "range": ar}
    for name, pct in EXTENSIONS.items():
        levels["+" + name] = t0 + (ar * pct)
        levels["-" + name] = t0 - (ar * pct)
    levels["+rekey"] = t0 + (ar * REKEY_PCT)
    levels["-rekey"] = t0 - (ar * REKEY_PCT)
    return levels


# ─── SIGNAL OUTPUT ──────────────────────────────────────────────────

def write_signal(signal):
    """Write MLR signal to JSONL file for signal_bot to pick up."""
    SIGNALS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SIGNALS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(signal, default=str) + "\n")


# ─── MAIN SCANNER ──────────────────────────────────────────────────

class MLRScanner:
    def __init__(self):
        self.pair_data = {}      # pair -> bars
        self.pair_levels = {}    # pair -> levels for today
        self.hit_levels = {}     # pair -> set of already-hit levels (avoid dupes)
        self.last_scan_date = None
        self.tier_sent = False

    def load_all_pairs(self):
        """Load recent bars for all pairs."""
        logger.info("Loading pair data...")
        loaded = 0
        for pair in PAIRS:
            filepath = find_data_file(pair)
            if filepath is None:
                continue
            try:
                bars = load_recent_bars(filepath, lookback_days=3)
                if len(bars) > 10:
                    self.pair_data[pair] = bars
                    loaded += 1
            except Exception as e:
                logger.warning(f"  {pair}: load error: {e}")
        logger.info(f"Loaded {loaded}/{len(PAIRS)} pairs")

    def scan_tiers(self, scan_date):
        """Scan all pairs and calculate tiers + MLR levels for the day."""
        logger.info(f"Scanning tiers for {scan_date}...")
        tier_report = []

        for pair, bars in self.pair_data.items():
            ar = calc_asian_range(bars, scan_date)
            if ar is None:
                continue

            pip_size = get_pip_size(pair)
            ar_pips = ar["range"] / pip_size

            tier_name, au, trigger = classify_tier(ar_pips, pair)
            if tier_name == "NO_GO":
                continue

            levels = calc_mlr_levels(ar["t0_anchor"], ar["range"])

            self.pair_levels[pair] = {
                "ar": ar,
                "ar_pips": ar_pips,
                "tier": tier_name,
                "au": au,
                "levels": levels,
            }
            self.hit_levels[pair] = set()

            tier_report.append({
                "pair": pair,
                "tier": tier_name,
                "au": au,
                "ar_pips": round(ar_pips, 1),
                "t0": ar["t0_anchor"],
                "ext_25_up": levels["+ext_25"],
                "ext_25_dn": levels["-ext_25"],
                "ext_50_up": levels["+ext_50"],
                "ext_50_dn": levels["-ext_50"],
                "ext_100_up": levels["+ext_100"],
                "ext_100_dn": levels["-ext_100"],
                "rekey_up": levels["+rekey"],
                "rekey_dn": levels["-rekey"],
            })

        return tier_report

    def send_tier_alert(self, tier_report):
        """Send tier report as a signal."""
        if not tier_report:
            return

        # Sort by tier then by AR size
        tier_order = {"T1": 1, "T2": 2, "T3": 3}
        tier_report.sort(key=lambda x: (tier_order.get(x["tier"], 9), -x["ar_pips"]))

        lines = [
            "MLR SCAN — London Open",
            f"{datetime.now().strftime('%Y-%m-%d %H:%M')} EST",
            f"Pairs: {len(tier_report)}",
            "",
        ]

        for r in tier_report:
            pair = r["pair"]
            tier = r["tier"]
            ar = r["ar_pips"]
            t0 = r["t0"]

            # Format levels based on pair type
            if "BTC" in pair:
                fmt = lambda x: f"{x:.1f}"
            elif "JPY" in pair:
                fmt = lambda x: f"{x:.2f}"
            elif any(x in pair for x in ["XAU", "XAG"]):
                fmt = lambda x: f"{x:.1f}"
            else:
                fmt = lambda x: f"{x:.5f}"

            lines.append(
                f"<b>{pair}</b> | {tier} | AU={r['au']}p | AR={ar}p"
            )
            lines.append(
                f"  +25%: {fmt(r['ext_25_up'])}  -25%: {fmt(r['ext_25_dn'])}"
            )
            lines.append(
                f"  +50%: {fmt(r['ext_50_up'])}  -50%: {fmt(r['ext_50_dn'])}"
            )
            lines.append(
                f"  +100%: {fmt(r['ext_100_up'])}  -100%: {fmt(r['ext_100_dn'])}"
            )
            lines.append(
                f"  Rekey: {fmt(r['rekey_up'])} / {fmt(r['rekey_dn'])}"
            )
            lines.append("")

        msg = "\n".join(lines)

        signal = {
            "event": "MLR_TIER_SCAN",
            "engine": "MLR",
            "time": datetime.now().isoformat(),
            "message": msg,
            "pairs_scanned": len(tier_report),
        }
        write_signal(signal)
        logger.info(f"Tier alert sent: {len(tier_report)} pairs")

    def scan_levels(self, scan_date):
        """Scan for level hits during activation window."""
        alerts = []

        for pair, bars in self.pair_data.items():
            if pair not in self.pair_levels:
                continue

            info = self.pair_levels[pair]
            levels = info["levels"]
            hit = self.hit_levels.get(pair, set())

            # Get activation window bars for today
            act_bars = [
                b for b in bars
                if b["date"] == scan_date and ASIAN_END <= b["hour"] < ACTIVATION_END
            ]

            if not act_bars:
                continue

            act_high = max(b["high"] for b in act_bars)
            act_low = min(b["low"] for b in act_bars)

            # Check each level
            for level_name in ["ext_25", "ext_50", "ext_100"]:
                for direction in ["+", "-"]:
                    key = f"{direction}{level_name}"
                    if key in hit:
                        continue

                    level_val = levels[key]
                    hit_up = direction == "+" and act_high >= level_val
                    hit_dn = direction == "-" and act_low <= level_val

                    if hit_up or hit_dn:
                        hit.add(key)
                        pct = int(EXTENSIONS[level_name] * 100)
                        arrow = "↑" if direction == "+" else "↓"

                        alerts.append({
                            "pair": pair,
                            "tier": info["tier"],
                            "level": f"{arrow}{pct}%",
                            "price": level_val,
                            "direction": direction,
                        })

            # Check rekey
            for direction in ["+", "-"]:
                key = f"{direction}rekey"
                if key in hit:
                    continue

                level_val = levels[key]
                hit_up = direction == "+" and act_high >= level_val
                hit_dn = direction == "-" and act_low <= level_val

                if hit_up or hit_dn:
                    hit.add(key)
                    arrow = "↑" if direction == "+" else "↓"

                    alerts.append({
                        "pair": pair,
                        "tier": info["tier"],
                        "level": f"{arrow}REKEY",
                        "price": level_val,
                        "direction": direction,
                    })

        return alerts

    def send_hit_alert(self, alerts):
        """Send level hit alerts."""
        if not alerts:
            return

        for alert in alerts:
            pair = alert["pair"]
            tier = alert["tier"]
            level = alert["level"]
            price = alert["price"]

            if "JPY" in pair:
                price_str = f"{price:.2f}"
            elif any(x in pair for x in ["XAU", "XAG"]):
                price_str = f"{price:.1f}"
            else:
                price_str = f"{price:.5f}"

            msg = (
                f"<b>MLR HIT</b> — {pair}\n"
                f"Tier: {tier}\n"
                f"Level: <b>{level}</b>\n"
                f"Price: {price_str}\n"
                f"{datetime.now().strftime('%H:%M:%S')} EST"
            )

            signal = {
                "event": "MLR_LEVEL_HIT",
                "engine": "MLR",
                "symbol": pair,
                "time": datetime.now().isoformat(),
                "message": msg,
                "level": level,
                "price": price,
                "tier": tier,
            }
            write_signal(signal)
            logger.info(f"HIT: {pair} {level} @ {price_str}")

    def run(self):
        """Main scanner loop."""
        log("=" * 60)
        logger.info("MLR SCANNER — Starting")
        logger.info(f"Pairs: {len(PAIRS)}")
        logger.info(f"Signals file: {SIGNALS_FILE}")
        logger.info("=" * 60)

        self.load_all_pairs()

        while True:
            now = datetime.now()
            current_date = now.date()
            current_hour = now.hour

            # Reload data periodically (every 6 hours)
            if self.last_scan_date != current_date:
                self.load_all_pairs()
                self.last_scan_date = current_date
                self.tier_sent = False
                self.pair_levels = {}
                self.hit_levels = {}

            # At London open (03:00 EST): scan tiers and send alert
            if current_hour == ASIAN_END and not self.tier_sent:
                tier_report = self.scan_tiers(current_date)
                self.send_tier_alert(tier_report)
                self.tier_sent = True

            # During activation window (03:00-12:00 EST): scan for level hits
            if ASIAN_END <= current_hour < ACTIVATION_END and self.pair_levels:
                alerts = self.scan_levels(current_date)
                self.send_hit_alert(alerts)

            # After 12:00 EST: reset for next day
            if current_hour >= ACTIVATION_END:
                self.tier_sent = False

            # Scan every 60 seconds
            time.sleep(60)


def main():
    scanner = MLRScanner()
    try:
        scanner.run()
    except KeyboardInterrupt:
        logger.info("Stopped.")
    except Exception as e:
        logger.error(f"FATAL: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
