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
import sys, json, csv
from datetime import datetime, timedelta, timezone
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(r"C:\Users\wifik\Desktop\projects\larger-lab")))
sys.path.insert(0, str(Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines")))
sys.path.insert(0, str(Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\configs")))

from asset_configs import ASSET_CONFIGS
from p90_engine_dmr import P90Engine, P90Variant, P90Signal, Bar, TradeDirection

EST = timezone(timedelta(hours=-5))
EST_OFFSET = -5


def find_csv(symbol: str):
    """Find CSV file for a symbol."""
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
    """Load bars from CSV file."""
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
    """Run P90 + DMR backtest for a single pair."""
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

        # Session init at 3AM EST
        if est_hour == 3 and bar_date != current_date:
            current_date = bar_date
            # Collect Asian session bars (19:00-03:00 EST)
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

    wins = sum(1 for s in engine.signal_log if s.event in ("TP1_HIT", "TP2_HIT", "DMR_TP_HIT"))
    losses = sum(1 for s in engine.signal_log if s.event in ("SL_HIT", "END_OF_SESSION"))
    ews_exits = sum(1 for s in engine.signal_log if s.event == "EWS_EXIT")

    total_pnl = 0.0
    for s in engine.signal_log:
        if s.event in ("TP1_HIT", "TP2_HIT") and s.entry_price and s.tp_price:
            total_pnl += abs(s.entry_price - s.tp_price) / engine.pip_size
        elif s.event == "SL_HIT" and s.entry_price and s.sl_price:
            total_pnl -= abs(s.entry_price - s.sl_price) / engine.pip_size

    days = (bars[-1].timestamp - bars[0].timestamp).days if len(bars) > 1 else 0
    tr_per_day = total / days if days > 0 else 0
    variants = Counter(s.variant.value for s in entries)

    return {
        "trades": total, "wins": wins, "losses": losses, "ews_exits": ews_exits,
        "win_rate": round(wins / total * 100, 1) if total > 0 else 0,
        "pnl_pips": round(total_pnl, 1),
        "tr_per_day": round(tr_per_day, 1), "days": days,
        "variants": dict(variants),
    }


def main():
    report_dir = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\hyperliquid_full")
    report_dir.mkdir(parents=True, exist_ok=True)

    # All pairs with configs
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

        print(f"\n{symbol} ({csv_path})...")
        bars = load_bars(csv_path)
        if not bars:
            print(f"  No bars loaded")
            continue

        print(f"  {len(bars)} bars, {bars[0].timestamp.date()} -> {bars[-1].timestamp.date()}")
        result = run_p90_backtest(symbol, bars, config)
        all_results[symbol] = result

        if result["trades"] > 0:
            print(f"  Trades: {result['trades']} | WR: {result['win_rate']}% | PnL: {result['pnl_pips']:.0f}p")
            print(f"  TP: {result['wins']} | SL: {result['losses']} | EWS: {result.get('ews_exits', 0)} | Tr/D: {result['tr_per_day']}")
            print(f"  Variants: {result.get('variants', {})}")
        else:
            print(f"  No trades generated")

    # Summary
    print(f"\n\n{'='*80}")
    print(f"  P90 CASCADE + DMR — MULTI-PAIR BACKTEST SUMMARY")
    print(f"{'='*80}")
    h = f"{'Pair':<10} {'Trades':>8} {'WR%':>8} {'PnL(pips)':>12} {'TP':>6} {'SL':>6} {'Tr/D':>6}"
    print(h)
    print("-" * 62)
    for sym, r in sorted(all_results.items(), key=lambda x: x[1].get("pnl_pips", 0), reverse=True):
        if r["trades"] > 0:
            print(f"{sym:<10} {r['trades']:>8} {r['win_rate']:>7.1f}% {r['pnl_pips']:>10.0f} {r['wins']:>6} {r['losses']:>6} {r['tr_per_day']:>5.1f}")

    with open(report_dir / "p90_dmr_all_pairs.json", "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\nResults saved.")


if __name__ == "__main__":
    main()
