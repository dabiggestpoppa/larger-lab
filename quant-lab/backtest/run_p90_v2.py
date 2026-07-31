"""
P90 Cascade V2 — Matches 78.7% WR Reference Configuration
============================================================
Key differences from V1:
1. Tier config: T1 (AR≤20p), T2 (AR≤30p), T3 (AR≤45p), NO-GO (AR>45p)
2. TP1 = -25% AR, TP2 = -50% AR (not fixed AU)
3. Dual entry: two positions per P90 signal (SL1=80% body, SL2=168% body)
4. EWS = reduced size entry, NOT force-close exit
5. Default P90 thresholds (not calibrated)
"""
import sys, json, csv
from datetime import datetime, timedelta, timezone
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(r"C:\Users\wifik\Desktop\projects\larger-lab")))

from configs.asset_configs import ASSET_CONFIGS
from engines.p90_engine import (
    P90Engine, P90Variant, P90Signal, Bar, TradeDirection,
    DEFAULT_P90_THRESHOLDS
)

EST = timezone(timedelta(hours=-5))
EST_OFFSET = -5

# ORIGINAL TIER CONFIG (from P90_FINAL_COMPOSITE_REPORT.md)
ORIGINAL_TIERS = {
    "T1": {"ar_max": 20.0, "au": 10.0, "trigger": 12.0},
    "T2": {"ar_max": 30.0, "au": 12.0, "trigger": 15.0},
    "T3": {"ar_max": 45.0, "au": 15.0, "trigger": 19.0},
}


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
                        ts = datetime.strptime(ts_raw.strip(), fmt).replace(tzinfo=EST)
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


def run_p90_v2(symbol: str, bars: list, config: dict) -> dict:
    """
    Run P90 with original reference configuration.
    Uses default P90 thresholds, original tier config, AR-based TP.
    """
    pip_size = config.get("pip_value", 0.0001)
    
    # Use default P90 thresholds (not calibrated)
    p90_config = DEFAULT_P90_THRESHOLDS.copy()
    
    engine = P90Engine(
        pip_size=pip_size,
        p90_config=p90_config,
        tier_config=ORIGINAL_TIERS,
        symbol=symbol,
        target_mode="both",
    )

    current_date = None

    for i, bar in enumerate(bars):
        est_hour = (bar.timestamp.hour + EST_OFFSET) % 24
        bar_date = bar.timestamp.astimezone(EST).date()

        # Session init at 3AM EST
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

        # 12PM hard reset
        if est_hour == 12:
            engine.hard_exit()

        if not engine.session_active:
            continue

        engine.process_bar(bar)

    # Compile stats
    entries = [s for s in engine.signal_log if s.event == "ENTRY"]
    total = len(entries)
    if total == 0:
        return {"trades": 0}

    wins = sum(1 for s in engine.signal_log if s.event == "TP_HIT")
    losses = sum(1 for s in engine.signal_log if s.event == "SL_HIT")
    ews = sum(1 for s in engine.signal_log if s.event == "EWS_EXIT")
    kill = sum(1 for s in engine.signal_log if s.event == "KILL_SWITCH")

    total_pnl = 0.0
    for s in engine.signal_log:
        if s.event == "TP_HIT" and s.entry_price and s.tp_price:
            total_pnl += abs(s.entry_price - s.tp_price) / pip_size
        elif s.event == "SL_HIT" and s.entry_price and s.sl_price:
            total_pnl -= abs(s.entry_price - s.sl_price) / pip_size

    days = (bars[-1].timestamp - bars[0].timestamp).days if len(bars) > 1 else 0
    variants = Counter(s.variant.value for s in entries)

    return {
        "trades": total, "wins": wins, "losses": losses, "ews_exits": ews, "kill_switches": kill,
        "win_rate": round(wins / total * 100, 1) if total > 0 else 0,
        "pnl_pips": round(total_pnl, 1),
        "tr_per_day": round(total / days, 1) if days > 0 else 0,
        "days": days, "variants": dict(variants),
    }


def main():
    report_dir = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\hyperliquid_full")
    report_dir.mkdir(parents=True, exist_ok=True)

    # Run on EURUSD first to validate against 78.7% reference
    test_pairs = ["EURUSD"]
    
    # Then run all pairs
    skip_prefixes = ("NAS", "FR40", "HK50", "DE30", "LCO", "OIL")
    all_pairs = test_pairs + [k for k in ASSET_CONFIGS.keys() if not k.startswith(skip_prefixes) and k not in test_pairs]
    
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
        result = run_p90_v2(symbol, bars, config)
        all_results[symbol] = result

        if result["trades"] > 0:
            print("  Trades: %d | WR: %.1f%% | PnL: %.0fp | Tr/D: %.1f" % (
                result["trades"], result["win_rate"], result["pnl_pips"], result["tr_per_day"]))
            print("  TP: %d | SL: %d | EWS: %d | Kill: %d" % (
                result["wins"], result["losses"], result["ews_exits"], result.get("kill_switches", 0)))
            print("  Variants: %s" % result.get("variants", {}))
        else:
            print("  No trades generated")

    # Summary
    print("\n\n%s" % "=" * 90)
    print("  P90 CASCADE V2 (REF CONFIG) — MULTI-PAIR BACKTEST SUMMARY")
    print("=" * 90)
    h = "%-10s %8s %8s %12s %6s %6s %6s" % ("Pair", "Trades", "WR%", "PnL(pips)", "TP", "SL", "Tr/D")
    print(h)
    print("-" * 62)
    for sym, r in sorted(all_results.items(), key=lambda x: x[1].get("pnl_pips", 0), reverse=True):
        if r["trades"] > 0:
            print("%-10s %8d %7.1f%% %10.0f %6d %6d %5.1f" % (
                sym, r["trades"], r["win_rate"], r["pnl_pips"], r["wins"], r["losses"], r["tr_per_day"]))

    with open(report_dir / "p90_v2_all_pairs.json", "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    print("\nResults saved to %s" % (report_dir / "p90_v2_all_pairs.json"))


if __name__ == "__main__":
    main()
