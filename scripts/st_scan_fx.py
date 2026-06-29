"""
ST Engine scan — all forex pairs with native tier configs.
Sends signals to Discord.
"""
import sys, os, json, time, requests
os.environ["PYTHONIOENCODING"] = "utf-8"
sys.path.insert(0, "quant-lab/engines")
sys.path.insert(0, "quant-lab/configs")
sys.path.insert(0, "quant-lab/ml")

from symmetry_trap import SymmetryTrapEngine, Bar, TradeDirection
from asset_configs import ASSET_CONFIGS
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timezone, timedelta
from pathlib import Path

EST = timezone(timedelta(hours=-5))
REPO_ROOT = Path(__file__).parent.parent

# Discord webhook
ENV_PATH = REPO_ROOT / ".env"
DISCORD_WEBHOOK = ""
if ENV_PATH.exists():
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())
DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK_URL", "")


def send_discord(msg):
    if not DISCORD_WEBHOOK:
        return False
    try:
        resp = requests.post(DISCORD_WEBHOOK, json={"content": msg}, timeout=10)
        return resp.status_code in (200, 204)
    except Exception as e:
        print("[DISCORD] Error: %s" % e)
        return False


def scan_symbol(symbol):
    """Scan a single symbol with ST engine using native config."""
    try:
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, 500)
        if rates is None or len(rates) < 50:
            return None

        df = pd.DataFrame(rates)
        df["dt"] = pd.to_datetime(df["time"], unit="s", utc=True)
        df = df.set_index("dt").sort_index()
        df["est_hour"] = (df.index.hour - 5) % 24

        # Get per-asset config
        cfg = ASSET_CONFIGS.get(symbol, {})
        tier_cfg = cfg.get("tiers", None)
        pip_size = cfg.get("pip_value", 0.0001)

        # Compute Asian range from most recent complete session
        asian = df[(df["est_hour"] >= 19) | (df["est_hour"] < 3)]
        if len(asian) < 2:
            return None

        # Group by date and find most recent complete session
        asian_dates = {}
        for idx in asian.index:
            d = idx.date()
            if d not in asian_dates:
                asian_dates[d] = []
            asian_dates[d].append(idx)

        best_date = None
        best_count = 0
        for d in sorted(asian_dates.keys()):
            times_list = asian_dates[d]
            count = len(times_list)
            has_end_bar = any(t.hour >= 7 for t in times_list)
            if has_end_bar and count > best_count:
                best_date = d
                best_count = count

        if best_date is None:
            best_date = sorted(asian_dates.keys())[-1]

        recent_asian = asian.loc[asian_dates[best_date][0] : asian_dates[best_date][-1]]
        ah = recent_asian["high"].max()
        al = recent_asian["low"].min()

        # Create ST engine with native config
        st = SymmetryTrapEngine(tier_config=tier_cfg)
        st.initialize_session(ah, al)

        if not st.session_active:
            return {
                "symbol": symbol,
                "tier": st.tier_name,
                "ar_pips": round(st.asian_range_pips, 1),
                "active": False,
                "signal": None,
            }

        # Process post-Asian bars
        post_3am = df[df["est_hour"] >= 3]
        signals = []
        for idx, row in post_3am.iterrows():
            bar = Bar(
                timestamp=idx,
                open=row["open"],
                high=row["high"],
                low=row["low"],
                close=row["close"],
            )
            sig = st.process_bar(bar)
            if sig:
                signals.append(sig)

        latest = signals[-1] if signals else None
        return {
            "symbol": symbol,
            "tier": st.tier_name,
            "ar_pips": round(st.asian_range_pips, 1),
            "active": True,
            "signal": latest.event if latest else None,
            "direction": latest.direction.name if latest else None,
            "entry": latest.entry_price if latest else None,
            "sl": latest.sl_price if latest else None,
            "tp": latest.tp_price if latest else None,
            "signals_count": len(signals),
        }

    except Exception as e:
        print("ERROR %s: %s" % (symbol, e))
        return None


def main():
    if not mt5.initialize():
        print("MT5 not connected")
        return

    # All forex pairs with configs (no crypto/metals/indices)
    FX_PAIRS = [
        k
        for k in ASSET_CONFIGS.keys()
        if not any(
            x in k
            for x in ["BTC", "ETH", "SOL", "XAU", "XAG", "US500", "DE30", "FR40", "HK50", "NAS100", "XRP"]
        )
    ]

    print("=" * 70)
    print("ST ENGINE SCAN — ALL FOREX PAIRS (%d)" % len(FX_PAIRS))
    print("=" * 70)
    print()

    results = []
    for symbol in FX_PAIRS:
        result = scan_symbol(symbol)
        if result:
            results.append(result)

    # Sort: active with signals first
    active = [r for r in results if r["active"] and r["signal"]]
    inactive = [r for r in results if not r["active"] or not r["signal"]]

    # Send to Discord
    now = datetime.now(EST)
    header = "📊 **ST ENGINE SCAN** — %s EST\n" % now.strftime("%H:%M %A")
    header += "Pairs: %d | Active: %d | No Signal: %d\n" % (
        len(results),
        len(active),
        len(inactive),
    )

    if active:
        msg = header + "\n**ACTIVE SIGNALS:**\n"
        for r in active:
            msg += "  %s %s  entry=%.5f  sl=%.5f  tp=%.5f  tier=%s  AR=%.1fp\n" % (
                r["symbol"],
                r["direction"],
                r["entry"],
                r["sl"],
                r["tp"],
                r["tier"],
                r["ar_pips"],
            )
        send_discord(msg)
        print(msg)
    else:
        msg = header + "\nNo active signals right now."
        send_discord(msg)
        print(msg)

    # Also save to alerts file
    alerts_file = REPO_ROOT / "data" / "alerts_history.json"
    history = []
    if alerts_file.exists():
        with open(alerts_file, encoding="utf-8") as f:
            history = json.load(f)
    for r in active:
        history.append(
            {
                "symbol": r["symbol"],
                "direction": r["direction"],
                "entry": r["entry"],
                "sl": r["sl"],
                "tp": r["tp"],
                "tier": r["tier"],
                "asian_range_pips": r["ar_pips"],
                "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
            }
        )
    with open(alerts_file, "w", encoding="utf-8") as f:
        json.dump(history[-500:], f, indent=2)

    mt5.shutdown()


if __name__ == "__main__":
    main()
