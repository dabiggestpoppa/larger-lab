"""
P90 Cascade Only — Multi-Pair Backtest
=======================================
Pure P90 engine (no DMR overlay) with INITIAL + CASCADE variants.
Uses the existing p90_engine.py (not DMR variant).

P90 Logic:
  - INITIAL: First P90 of day, SL = 0.80x body
  - CASCADE: 2nd/3rd P90 same direction within 120min, SL = 1.68x body
  - EWS: Opposite P90 at target = exit signal
  - TP1: -25% Asian Range, TP2: -50% Asian Range
"""
import sys, json, csv
from datetime import datetime, timedelta, timezone
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(r"C:\Users\wifik\Desktop\projects\larger-lab")))
sys.path.insert(0, str(Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines")))
sys.path.insert(0, str(Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\configs")))

from asset_configs import ASSET_CONFIGS
from p90_engine import P90Engine, P90Variant, P90Signal, Bar, TradeDirection

EST = timezone(timedelta(hours=-5))
EST_OFFSET = -5


def find_csv(symbol: str):
    patterns = [
        f"quant-lab/data/{symbol}_M5.csv",
        f"quant-lab/data/{symbol}_M5_fetched.csv",
        f"quant-lab/data/{symbol}PRO_M5_2023_2026.csv",
        f"quant-lab/data/{symbol}PRO_M5_2023_2025.csv",
        f"quant-lab/data/{symbol}PRO_M5.csv",
    ]
    for p in patterns:
        if Path(p).exists():
            return p
    return None


def load_bars(csv_path: str) -> list:
    bars = []
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                ts_raw = (row.get("timestamp") or row.get("time") or row.get("date") or row.get("datetime"))
                if not ts_raw:
                    continue
                ts = None
                for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M"]:
                    try:
                        ts = datetime.strptime(ts_raw.strip(), fmt)
                        ts = ts.replace(tzinfo=EST)
                        break
                    except ValueError:
                        continue
                if ts is None:
                    continue
                o = float(row.get("open") or row.get("Open"))
                h = float(row.get("high") or row.get("High"))
                lo = float(row.get("low") or row.get("Low"))
                cl = float(row.get("close") or row.get("Close"))
                bars.append(Bar(timestamp=ts, open=o, high=h, low=lo, close=cl))
            except (ValueError, KeyError):
                continue
    bars.sort(key=lambda b: b.timestamp)
    return bars


def run_p90_backtest(symbol: str, bars: list, config: dict) -> dict:
    engine = P90Engine(
        pip_size=config.get("pip_value", 0.0001),
        tier_config=config.get("tiers"),
        symbol=symbol,
        target_mode="both",
    )

    current_date = None

    for i, bar in enumerate(bars):
        est_hour = (bar.timestamp.hour + EST_OFFSET) % 24
        bar_date = bar.timestamp.astimezone(EST).date()

        if est_hour == 3 and bar_date != current_date:
            current_date = bar_date
            asian_high = bar.high
            asian_low = bar.low
            for j in range(i - 1, -1, -1):
                bj = bars[j]
                bj_hour = (bj.timestamp.hour + EST_OFFSET) % 24
                if bj_hour >= 19 or bj_hour < 3:
                    asian_high = max(asian_high, bj.high)
                    asian_low = min(asian_low, bj.low)
                else:
                    break
            engine.initialize_session(asian_high, asian_low)

        if est_hour == 12:
            engine.hard_exit()

        if not engine.session_active:
            continue

        engine.process_bar(bar)

    entries = [s for s in engine.signal_log if s.event == "ENTRY"]
    total = len(entries)
    if total == 0:
        return {"trades": 0}

    wins = sum(1 for s in engine.signal_log if s.event == "TP_HIT")
    losses = sum(1 for s in engine.signal_log if s.event == "SL_HIT")
    ews = sum(1 for s in engine.signal_log if s.event == "EWS_EXIT")

    total_pnl = 0.0
    for s in engine.signal_log:
        if s.event == "TP_HIT" and s.entry_price and s.tp_price:
            total_pnl += abs(s.entry_price - s.tp_price) / engine.pip_size
        elif s.event == "SL_HIT" and s.entry_price and s.sl_price:
            total_pnl -= abs(s.entry_price - s.sl_price) / engine.pip_size

    days = (bars[-1].timestamp - bars[0].timestamp).days if len(bars) > 1 else 0
    variants = Counter(s.variant.value for s in entries)

    return {
        "trades": total, "wins": wins, "losses": losses, "ews_exits": ews,
        "win_rate": round(wins / total * 100, 1) if total > 0 else 0,
        "pnl_pips": round(total_pnl, 1),
        "tr_per_day": round(total / days, 1) if days > 0 else 0,
        "days": days, "variants": dict(variants),
    }


def main():
    report_dir = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\hyperliquid_full")
    report_dir.mkdir(parents=True, exist_ok=True)

    skip_prefixes = ("NAS", "FR40", "HK50", "DE30", "LCO", "OIL")
    all_pairs = [k for k in ASSET_CONFIGS.keys() if not k.startswith(skip_prefixes)]
    all_results = {}

    for symbol in all_pairs:
        csv_path = find_csv(symbol)
        if not csv_path:
            continue
        config = ASSET_CONFIGS.get(symbol)
        if not config:
            continue

        print("\n%s (%s)..." % (symbol, csv_path))
        bars = load_bars(csv_path)
        if not bars:
            print("  No bars loaded")
            continue

        print("  %d bars, %s -> %s" % (len(bars), bars[0].timestamp.date(), bars[-1].timestamp.date()))
        result = run_p90_backtest(symbol, bars, config)
        all_results[symbol] = result

        if result["trades"] > 0:
            print("  Trades: %d | WR: %.1f%% | PnL: %.0fp | Tr/D: %.1f" % (
                result["trades"], result["win_rate"], result["pnl_pips"], result["tr_per_day"]))
            print("  TP: %d | SL: %d | EWS: %d" % (result["wins"], result["losses"], result.get("ews_exits", 0)))
            print("  Variants: %s" % result.get("variants", {}))
        else:
            print("  No trades generated")

    print("\n\n%s" % "=" * 80)
    print("  P90 CASCADE ONLY — MULTI-PAIR BACKTEST SUMMARY")
    print("=" * 80)
    h = "%-10s %8s %8s %12s %6s %6s %6s" % ("Pair", "Trades", "WR%", "PnL(pips)", "TP", "SL", "Tr/D")
    print(h)
    print("-" * 62)
    for sym, r in sorted(all_results.items(), key=lambda x: x[1].get("pnl_pips", 0), reverse=True):
        if r["trades"] > 0:
            print("%-10s %8d %7.1f%% %10.0f %6d %6d %5.1f" % (
                sym, r["trades"], r["win_rate"], r["pnl_pips"], r["wins"], r["losses"], r["tr_per_day"]))

    with open(report_dir / "p90_cascade_all_pairs.json", "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    print("\nResults saved.")


if __name__ == "__main__":
    main()
