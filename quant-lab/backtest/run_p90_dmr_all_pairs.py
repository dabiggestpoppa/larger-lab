"""
P90 Cascade + DMR — Multi-Pair Backtest
=========================================
Runs P90 Engine with Cascade variants and DMR sub-routine
across all available pairs using cached CSV data.

P90 Logic:
  - INITIAL: First P90 of day, SL = 0.80x body
  - CASCADE: 2nd/3rd P90 same direction within 120min, SL = 1.68x body
  - EWS: Opposite P90 at target = exit signal
  - TP1: -25% Asian Range, TP2: -50% Asian Range
  - DMR: Deep State limit at 200% body from activation boundary

Usage:
    python quant-lab/backtest/run_p90_dmr_all_pairs.py
"""
import sys, json, csv, time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(r"C:\Users\wifik\Desktop\projects\larger-lab")))
sys.path.insert(0, str(Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines")))
sys.path.insert(0, str(Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\configs")))

from asset_configs import ASSET_CONFIGS
from p90_engine_dmr import P90Engine, P90Variant, P90Signal, Bar, TradeDirection

EST = timezone(timedelta(hours=-5))

# Map asset keys to CSV files
PAIR_FILES = {
    "EURUSD": "quant-lab/data/EURUSD_M5.csv",
    "GBPUSD": "quant-lab/data/GBPUSD_M5.csv",
    "USDCHF": "quant-lab/data/USDCHF_M5.csv",
    "USDJPY": "quant-lab/data/USDJPY_M5.csv",
    "AUDUSD": "quant-lab/data/AUDUSD_M5.csv",
    "NZDUSD": "quant-lab/data/NZDUSD_M5.csv",
    "USDCAD": "quant-lab/data/USDCAD_PRO_M5.csv",
    "XAUUSD": "quant-lab/data/XAUUSD_M5.csv",
    "XAGUSD": "quant-lab/data/XAGUSD_M5.csv",
    "BTCUSD": "quant-lab/data/BTCUSD_M5.csv",
    "ETHUSD": "quant-lab/data/ETHUSD_M5.csv",
    "LTCUSD": "quant-lab/data/LTCUSD_M5.csv",
    "BCHUSD": "quant-lab/data/BCHUSD_M5.csv",
    "BNBUSD": "quant-lab/data/BNBUSD_M5.csv",
    "XLMUSD": "quant-lab/data/XLMUSD_M5.csv",
}


def load_bars(csv_path: str) -> list:
    """Load bars from CSV file."""
    bars = []
    path = Path(csv_path)
    if not path.exists():
        # Try alternative paths
        for alt in [csv_path.replace("_M5.csv", "_M5_fetched.csv"),
                     csv_path.replace("USD_M5", "USDPRO_M5_2023_2026")]:
            if Path(alt).exists():
                path = Path(alt)
                break
        else:
            return []

    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                ts_raw = (row.get("timestamp") or row.get("time") or row.get("date") or row.get("datetime"))
                if not ts_raw:
                    continue
                # Parse timestamp
                for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M"]:
                    try:
                        ts = datetime.strptime(ts_raw.strip(), fmt)
                        ts = ts.replace(tzinfo=EST)
                        break
                    except ValueError:
                        continue
                else:
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
    """Run P90 + DMR backtest for a single pair."""
    engine = P90Engine(
        pip_size=config.get("pip_value", 0.0001),
        tier_config=config.get("tiers"),
        symbol=symbol,
        target_mode="both",
    )

    for bar in bars:
        engine.process_bar(bar)

    # Compile stats from signal_log
    entries = [s for s in engine.signal_log if s.event == "ENTRY"]
    total = len(entries)
    if total == 0:
        return {"trades": 0}

    # Count wins/losses from exit signals
    wins = sum(1 for s in engine.signal_log if s.event in ("TP_HIT", "DMR_TP_HIT"))
    losses = sum(1 for s in engine.signal_log if s.event in ("SL_HIT", "END_OF_SESSION"))
    # EWS exits are neither win nor loss (just exit)
    ews_exits = sum(1 for s in engine.signal_log if s.event == "EWS_EXIT")

    wr = wins / total * 100.0 if total > 0 else 0.0

    # Variant breakdown
    variant_stats = {}
    for sig in entries:
        v = sig.variant.value
        variant_stats[v] = variant_stats.get(v, 0) + 1

    # DMR stats
    dmr_entries = [s for s in engine.signal_log if s.event == "DMR_ENTRY"]
    dmr_tp = [s for s in engine.signal_log if s.event == "DMR_TP_HIT"]

    return {
        "trades": total,
        "wins": wins,
        "losses": losses,
        "ews_exits": ews_exits,
        "win_rate": round(wr, 1),
        "variants": variant_stats,
        "dmr_entries": len(dmr_entries),
        "dmr_tp": len(dmr_tp),
        "bars_processed": len(bars),
    }


def main():
    print("=" * 70)
    print("  P90 CASCADE + DMR — MULTI-PAIR BACKTEST")
    print("=" * 70)

    all_results = {}

    for symbol, csv_path in PAIR_FILES.items():
        config = ASSET_CONFIGS.get(symbol)
        if not config:
            print(f"  {symbol}: No config, skipping")
            continue

        print(f"\n  {symbol}...")
        bars = load_bars(csv_path)
        if not bars:
            print(f"    No data found")
            continue

        print(f"    Loaded {len(bars)} bars")
        result = run_p90_backtest(symbol, bars, config)
        all_results[symbol] = result

        if result["trades"] > 0:
            print(f"    Trades: {result['trades']} | WR: {result['win_rate']}% | PnL: {result['pnl_pips']:.0f}p")
            print(f"    Variants: {result['variants']} | DMR: {result.get('dmr_trades', 0)}")
        else:
            print(f"    No trades generated")

    # Summary
    print(f"\n{'='*70}")
    print(f"  SUMMARY")
    print(f"{'='*70}")
    h = f"{'Pair':<10} {'Trades':>8} {'WR%':>8} {'PnL':>12} {'Variants'}"
    print(h)
    print("-" * 60)
    for sym, r in sorted(all_results.items(), key=lambda x: x[1].get("pnl_pips", 0), reverse=True):
        if r["trades"] > 0:
            print(f"{sym:<10} {r['trades']:>8} {r['win_rate']:>7.1f}% {r['pnl_pips']:>10.1f}  {r.get('variants', {})}")

    # Save
    report_dir = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\hyperliquid_full")
    report_dir.mkdir(parents=True, exist_ok=True)
    with open(report_dir / "p90_dmr_all_pairs.json", "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\nResults saved.")


if __name__ == "__main__":
    main()
