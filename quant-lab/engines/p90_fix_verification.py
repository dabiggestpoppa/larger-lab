"""
P90 Multi-Asset Fix Verification Backtest
===========================================
Runs P90 backtest across 10 assets using the updated engine with:
  - Asset-specific MIN_P90_BODY thresholds
  - RR >= 1.0 gate
  - Band-edge TP calculation
  - Cascade 90min hard cutoff + 3-filter requirement

Fetches M5 data from MT5 (.PRO symbols) for all assets.
Outputs:
  - quant-lab/reports/p90_fix_verification.json
  - quant-lab/reports/p90_fix_verification.md
"""

from __future__ import annotations

import csv
import json
import os
import sys
import logging
from datetime import datetime, timedelta, time
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

# ── Path Setup ────────────────────────────────────────────────────────────
REPO_ROOT = Path(r"C:\Users\wifik\Desktop\projects\larger-lab")
QUANT_LAB = REPO_ROOT / "quant-lab"
DATA_DIR = QUANT_LAB / "data"
REPORTS_DIR = QUANT_LAB / "reports"
CONFIGS_DIR = QUANT_LAB / "configs"
ENGINES_DIR = QUANT_LAB / "engines"

sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(CONFIGS_DIR))
sys.path.insert(0, str(ENGINES_DIR))

REPORTS_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [P90-VERIFY] %(levelname)s: %(message)s",
)
logger = logging.getLogger("p90_verify")

# ── Imports ───────────────────────────────────────────────────────────────
from p90_engine import (
    P90Engine,
    P90Variant,
    P90Signal,
    Bar,
    TradeDirection,
    MIN_P90_BODY,
    DEFAULT_P90_THRESHOLDS,
)

# ── Target assets ─────────────────────────────────────────────────────────
TARGET_ASSETS = [
    "EURUSD", "USDCHF", "NZDUSD", "GBPJPY", "CHFJPY",
    "GBPAUD", "GBPUSD", "GBPNZD", "GBPCHF", "USDJPY",
]

# ── Commission per lot (approximate, in USD) ─────────────────────────────
# Standard forex commission: ~7 USD round-turn per lot
COMMISSION_PER_LOT_USD = 7.0

# ── Pip value per lot (approximate USD per pip) ──────────────────────────
PIP_VALUE_PER_LOT = {
    "EURUSD": 10.0, "GBPUSD": 10.0, "USDCHF": 10.0, "NZDUSD": 10.0,
    "USDJPY": 9.0, "GBPJPY": 9.0, "CHFJPY": 9.0,
    "GBPAUD": 10.0, "GBPNZD": 10.0, "GBPCHF": 10.0,
}


# ── Timestamp parsing ────────────────────────────────────────────────────
_TIMESTAMP_FORMATS = [
    "%Y.%m.%d %H:%M:%S",
    "%Y.%m.%d %H:%M",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%d",
    "%m/%d/%Y %H:%M:%S",
    "%m/%d/%Y %H:%M",
    "%d.%m.%Y %H:%M:%S",
    "%d.%m.%Y %H:%M",
    "%Y%m%d %H:%M:%S",
]


def parse_timestamp(raw: str) -> datetime:
    raw = raw.strip()
    # Try Unix timestamp
    try:
        return datetime.utcfromtimestamp(int(raw))
    except (ValueError, OSError):
        pass
    for fmt in _TIMESTAMP_FORMATS:
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    raise ValueError(f"Cannot parse timestamp '{raw}'. Tried: {_TIMESTAMP_FORMATS}")


# ── CSV loading ───────────────────────────────────────────────────────────
def load_bars_csv(csv_path: str) -> List[Bar]:
    bars: List[Bar] = []
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    with open(path, newline="", encoding="utf-8-sig") as f:
        first_line = f.readline()
        f.seek(0)
        delimiter = "\t" if "\t" in first_line else ","
        reader = csv.DictReader(f, delimiter=delimiter)
        for row_num, row in enumerate(reader, start=2):
            clean_row = {k.strip().strip("<").strip(">"): v for k, v in row.items()}

            ts_raw = (clean_row.get("timestamp") or clean_row.get("Timestamp")
                      or clean_row.get("TIMESTAMP") or clean_row.get("datetime")
                      or clean_row.get("Datetime") or clean_row.get("DATETIME")
                      or clean_row.get("time") or clean_row.get("Time") or clean_row.get("TIME"))

            if ts_raw is None:
                date_val = (clean_row.get("date") or clean_row.get("Date") or clean_row.get("DATE"))
                time_val = (clean_row.get("time") or clean_row.get("Time") or clean_row.get("TIME"))
                if date_val and time_val:
                    ts_raw = f"{date_val.strip()} {time_val.strip()}"

            if ts_raw is None or not ts_raw.strip():
                continue

            o = clean_row.get("OPEN") or clean_row.get("open")
            h = clean_row.get("HIGH") or clean_row.get("high")
            l = clean_row.get("LOW") or clean_row.get("low")
            c = clean_row.get("CLOSE") or clean_row.get("close")

            if any(v is None for v in (o, h, l, c)):
                continue

            try:
                bars.append(Bar(
                    timestamp=parse_timestamp(ts_raw),
                    open=float(o), high=float(h), low=float(l), close=float(c)
                ))
            except (ValueError, TypeError):
                continue

    bars.sort(key=lambda b: b.timestamp)
    return bars


# ── MT5 data fetch ────────────────────────────────────────────────────────
def fetch_mt5_data(symbol: str, mt5_symbol: str, start_date: datetime, end_date: datetime) -> List[Bar]:
    """Fetch M5 bars from MT5."""
    try:
        import MetaTrader5 as mt5
    except ImportError:
        logger.warning("MetaTrader5 not installed")
        return []

    if not mt5.initialize():
        logger.warning(f"MT5 init failed: {mt5.last_error()}")
        return []

    try:
        symbol_info = mt5.symbol_info(mt5_symbol)
        if symbol_info and not symbol_info.visible:
            mt5.symbol_select(mt5_symbol, True)

        rates = mt5.copy_rates_range(mt5_symbol, mt5.TIMEFRAME_M5, start_date, end_date)
        if rates is None or len(rates) == 0:
            logger.warning(f"No MT5 data for {symbol} ({mt5_symbol})")
            return []

        bars = []
        for r in rates:
            bars.append(Bar(
                timestamp=datetime.utcfromtimestamp(r['time']),
                open=r['open'], high=r['high'], low=r['low'], close=r['close']
            ))
        bars.sort(key=lambda b: b.timestamp)
        logger.info(f"MT5 {symbol}: fetched {len(bars):,} M5 bars")
        return bars
    except Exception as e:
        logger.warning(f"MT5 fetch error for {symbol}: {e}")
        return []
    finally:
        try:
            mt5.shutdown()
        except Exception:
            pass


# ── Session grouping ──────────────────────────────────────────────────────
ASIAN_START_H = 19
ASIAN_END_H = 3
TRADING_START_H = 3
TRADING_END_H = 12


def _est_hour(dt: datetime) -> int:
    return (dt.hour - 5) % 24


def _session_date(dt: datetime):
    h = _est_hour(dt)
    if h >= ASIAN_START_H:
        return (dt + timedelta(days=1)).date()
    return dt.date()


def group_by_session(bars: List[Bar]):
    sessions = defaultdict(lambda: {"asian": [], "trading": []})
    for bar in bars:
        sdate = _session_date(bar.timestamp)
        h = _est_hour(bar.timestamp)
        if h >= ASIAN_START_H or h < ASIAN_END_H:
            sessions[sdate]["asian"].append(bar)
        elif TRADING_START_H <= h < TRADING_END_H:
            sessions[sdate]["trading"].append(bar)
    for sdate in sessions:
        sessions[sdate]["asian"].sort(key=lambda b: b.timestamp)
        sessions[sdate]["trading"].sort(key=lambda b: b.timestamp)
    return dict(sorted(sessions.items()))


def calc_asian_range(asian_bars):
    if not asian_bars:
        return 0.0, 0.0
    return max(b.high for b in asian_bars), min(b.low for b in asian_bars)


# ── Run P90 backtest for one asset ───────────────────────────────────────
def run_p90_asset(
    symbol: str,
    bars: List[Bar],
    pip_size: float,
    config: Optional[Dict] = None,
) -> Dict:
    """Run P90 engine on one asset's bars. Returns stats dict."""

    sessions = group_by_session(bars)
    logger.info(f"{symbol}: {len(bars):,} bars, {len(sessions)} sessions")

    engine = P90Engine(pip_size=pip_size, symbol=symbol, config=config)
    total_bars_processed = 0

    for sdate, session_bars in sessions.items():
        asian_bars = session_bars["asian"]
        trading_bars = session_bars["trading"]

        if not asian_bars or not trading_bars:
            continue

        asian_high, asian_low = calc_asian_range(asian_bars)
        if asian_high <= asian_low:
            continue

        engine.initialize_session(asian_high, asian_low)
        if not engine.session_active:
            continue

        for bar in trading_bars:
            engine.process_bar(bar)
            total_bars_processed += 1

    all_signals = engine.signal_log
    completed = [s for s in all_signals if s.event in ("TP_HIT", "SL_HIT", "EWS_EXIT")]

    # Compute per-trade PnL in pips
    trade_records = []
    for sig in completed:
        if sig.entry_price is None or sig.sl_price is None:
            continue

        sl_dist_price = abs(sig.sl_price - sig.entry_price)

        if sig.event == "TP_HIT":
            exit_price = sig.tp_price
        elif sig.event == "SL_HIT":
            exit_price = sig.sl_price
        elif sig.event == "EWS_EXIT":
            exit_price = sig.tp_price
        else:
            continue

        if exit_price is None:
            continue

        if sig.direction.name == "LONG":
            pnl_pips = (exit_price - sig.entry_price) / pip_size
        else:
            pnl_pips = (sig.entry_price - exit_price) / pip_size

        # Intended RR = TP1 distance / SL distance
        if sig.tp1_price is not None and sl_dist_price > 0:
            tp1_dist = abs(sig.tp1_price - sig.entry_price)
            intended_rr = tp1_dist / sl_dist_price
        else:
            intended_rr = 0.0

        # Actual RR = actual PnL / SL distance (in pips)
        sl_dist_pips = sl_dist_price / pip_size
        actual_rr = pnl_pips / sl_dist_pips if sl_dist_pips > 0 else 0.0

        trade_records.append({
            "event": sig.event,
            "variant": sig.variant.value,
            "direction": sig.direction.name,
            "entry": sig.entry_price,
            "sl": sig.sl_price,
            "tp1": sig.tp1_price,
            "exit_price": exit_price,
            "pnl_pips": round(pnl_pips, 2),
            "intended_rr": round(intended_rr, 3),
            "actual_rr": round(actual_rr, 3),
            "sl_dist_pips": round(sl_dist_pips, 2),
            "timestamp": sig.timestamp.isoformat() if sig.timestamp else None,
        })

    # Stats
    total_trades = len(trade_records)
    wins = [t for t in trade_records if t["pnl_pips"] > 0]
    losses = [t for t in trade_records if t["pnl_pips"] < 0]
    win_rate = len(wins) / total_trades * 100 if total_trades > 0 else 0.0

    gross_profit = sum(t["pnl_pips"] for t in wins)
    gross_loss = sum(t["pnl_pips"] for t in losses)
    net_pnl_pips = gross_profit + gross_loss

    # RR stats
    intended_rrs = [t["intended_rr"] for t in trade_records]
    min_rr = min(intended_rrs) if intended_rrs else 0.0
    max_rr = max(intended_rrs) if intended_rrs else 0.0
    avg_rr = sum(intended_rrs) / len(intended_rrs) if intended_rrs else 0.0

    # Sub-1.0 RR check
    sub_1_rr_trades = [t for t in trade_records if t["intended_rr"] < 1.0]

    # Commission estimate (assume 1 lot per trade)
    pip_val = PIP_VALUE_PER_LOT.get(symbol, 10.0)
    commission_per_trade = COMMISSION_PER_LOT_USD
    commission_pips = commission_per_trade / pip_val if pip_val > 0 else 0.0
    total_commission_pips = commission_pips * total_trades
    net_pnl_after_commission = net_pnl_pips - total_commission_pips

    # Profit factor
    gross_loss_abs = abs(gross_loss)
    profit_factor = gross_profit / gross_loss_abs if gross_loss_abs > 0 else float("inf")

    # Max drawdown
    cumulative = 0.0
    peak = 0.0
    max_dd = 0.0
    for t in trade_records:
        cumulative += t["pnl_pips"]
        if cumulative > peak:
            peak = cumulative
        dd = peak - cumulative
        if dd > max_dd:
            max_dd = dd

    # Per-variant breakdown
    per_variant = {}
    for variant_name in ["INITIAL", "CASCADE", "EWS"]:
        v_trades = [t for t in trade_records if t["variant"] == variant_name]
        if not v_trades:
            per_variant[variant_name] = {"trades": 0}
            continue
        v_wins = [t for t in v_trades if t["pnl_pips"] > 0]
        v_losses = [t for t in v_trades if t["pnl_pips"] < 0]
        v_pnl = sum(t["pnl_pips"] for t in v_trades)
        v_rrs = [t["intended_rr"] for t in v_trades]
        per_variant[variant_name] = {
            "trades": len(v_trades),
            "wins": len(v_wins),
            "losses": len(v_losses),
            "win_rate": round(len(v_wins) / len(v_trades) * 100, 1),
            "pnl_pips": round(v_pnl, 2),
            "avg_rr": round(sum(v_rrs) / len(v_rrs), 3),
            "min_rr": round(min(v_rrs), 3),
        }

    return {
        "symbol": symbol,
        "total_bars": len(bars),
        "total_sessions": len(sessions),
        "total_trades": total_trades,
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": round(win_rate, 2),
        "avg_intended_rr": round(avg_rr, 3),
        "min_intended_rr": round(min_rr, 3),
        "max_intended_rr": round(max_rr, 3),
        "sub_1_rr_count": len(sub_1_rr_trades),
        "sub_1_rr_trades": sub_1_rr_trades[:5],  # First 5 for inspection
        "gross_profit_pips": round(gross_profit, 2),
        "gross_loss_pips": round(gross_loss, 2),
        "net_pnl_pips": round(net_pnl_pips, 2),
        "commission_per_trade_pips": round(commission_pips, 4),
        "total_commission_pips": round(total_commission_pips, 2),
        "net_pnl_after_commission_pips": round(net_pnl_after_commission, 2),
        "profit_factor": round(profit_factor, 3) if profit_factor != float("inf") else 999.999,
        "max_drawdown_pips": round(max_dd, 2),
        "per_variant": per_variant,
        "trade_records": trade_records,
    }


# ── Main ──────────────────────────────────────────────────────────────────
def main():
    print("=" * 70)
    print("P90 FIX VERIFICATION — MULTI-ASSET BACKTEST")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # Date range for MT5 fetch
    start_date = datetime(2022, 1, 1)
    end_date = datetime(2026, 6, 3)

    all_results = {}
    skipped = []

    for symbol in TARGET_ASSETS:
        print(f"\n{'─' * 50}")
        print(f">>> {symbol}")
        print(f"{'─' * 50}")

        # ── Try to get M5 data ────────────────────────────────────────
        bars = None

        # Strategy 1: Check for existing M5 CSV with actual M5 data
        for csv_name in [f"{symbol}PRO_M5_2023_2026.csv", f"{symbol}PRO_M5_2023_2025.csv", f"{symbol}PRO_M5_MAD.csv"]:
            csv_path = DATA_DIR / csv_name
            if csv_path.exists():
                test_bars = load_bars_csv(str(csv_path))
                if len(test_bars) > 100:
                    # Check if actually M5 (not daily)
                    if len(test_bars) > 1000:
                        bars = test_bars
                        print(f"  Loaded from CSV: {csv_name} ({len(bars):,} bars)")
                        break

        # Strategy 2: Fetch from MT5
        if bars is None:
            print(f"  Fetching M5 from MT5 ({symbol}.PRO)...")
            bars = fetch_mt5_data(symbol, f"{symbol}.PRO", start_date, end_date)
            if bars:
                print(f"  MT5 fetch: {len(bars):,} bars")

        # Strategy 3: Use whatever CSV we have (even if daily)
        if bars is None:
            csv_path = DATA_DIR / f"{symbol}_M5.csv"
            if csv_path.exists():
                bars = load_bars_csv(str(csv_path))
                print(f"  WARNING: Using daily data from {csv_path.name} ({len(bars):,} bars)")

        if not bars:
            print(f"  SKIP {symbol}: no data available")
            skipped.append(symbol)
            continue

        # ── Get pip size from config ──────────────────────────────────
        pip_size = 0.0001
        config = None
        try:
            from asset_configs import get_config
            config = get_config(symbol)
            pip_size = config["pip_value"]
            print(f"  Config: pip_size={pip_size}, tiers={list(config['tiers'].keys())}")
        except Exception as e:
            print(f"  Config load failed: {e}, using pip_size={pip_size}")

        # ── Run backtest ─────────────────────────────────────────────
        result = run_p90_asset(symbol, bars, pip_size, config)
        all_results[symbol] = result

        print(f"  RESULT: {result['total_trades']} trades | WR={result['win_rate']:.1f}% | "
              f"AvgRR={result['avg_intended_rr']:.2f} | MinRR={result['min_intended_rr']:.2f} | "
              f"Sub1RR={result['sub_1_rr_count']} | PnL={result['net_pnl_pips']:+.1f}p")

    # ── Generate reports ────────────────────────────────────────────────
    print(f"\n{'=' * 70}")
    print("GENERATING REPORTS")
    print(f"{'=' * 70}")

    # JSON report
    json_report = {
        "generated": datetime.now().isoformat(),
        "engine": "P90 Kinetic Engine v4.0",
        "fixes_applied": [
            "Asset-specific MIN_P90_BODY thresholds (MAD 2026-06-03)",
            "RR >= 1.0 gate (skip trades where TP1 < SL distance)",
            "Band-edge TP calculation (TP from Asian High/Low, not entry)",
            "Cascade 90min hard cutoff + 3-filter requirement (time/dir/body)",
        ],
        "assets_requested": TARGET_ASSETS,
        "assets_tested": list(all_results.keys()),
        "assets_skipped": skipped,
        "results": {sym: {k: v for k, v in r.items() if k != "trade_records"} for sym, r in all_results.items()},
    }

    json_path = REPORTS_DIR / "p90_fix_verification.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_report, f, indent=2, default=str)
    print(f"JSON report: {json_path}")

    # Markdown report
    md_lines = []
    md_lines.append("# P90 Fix Verification — Multi-Asset Backtest Report")
    md_lines.append(f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    md_lines.append("## Fixes Applied\n")
    md_lines.append("1. **Asset-specific MIN_P90_BODY thresholds** — JPY crosses require 8-12p body vs 4p for majors")
    md_lines.append("2. **RR >= 1.0 gate** — Skip trades where TP1 doesn't cover the SL risk")
    md_lines.append("3. **Band-edge TP calculation** — TP measured from Asian High/Low edge, not from entry price")
    md_lines.append("4. **Cascade 90min hard cutoff + 3-filter** — Cascade requires: 30-90min window, same direction, body >= minimum\n")

    md_lines.append("## Summary Table\n")
    md_lines.append("| Asset | Trades | WR% | Avg RR | Min RR | Max RR | Sub-1RR | Gross P&L | Net P&L | PF |")
    md_lines.append("|-------|--------|-----|--------|--------|--------|---------|-----------|---------|-----|")

    total_trades = 0
    total_pnl = 0.0
    total_sub1 = 0

    for sym in TARGET_ASSETS:
        if sym not in all_results:
            md_lines.append(f"| {sym} | — | — | — | — | — | — | — | — | SKIP |")
            continue
        r = all_results[sym]
        md_lines.append(
            f"| {sym} | {r['total_trades']} | {r['win_rate']:.1f}% | "
            f"{r['avg_intended_rr']:.2f} | {r['min_intended_rr']:.2f} | {r['max_intended_rr']:.2f} | "
            f"{r['sub_1_rr_count']} | {r['gross_profit_pips'] + r['gross_loss_pips']:+.1f}p | "
            f"{r['net_pnl_after_commission_pips']:+.1f}p | {r['profit_factor']:.2f} |"
        )
        total_trades += r['total_trades']
        total_pnl += r['net_pnl_pips']
        total_sub1 += r['sub_1_rr_count']

    md_lines.append(f"\n**Total Trades:** {total_trades} | **Total Net PnL:** {total_pnl:+.1f} pips | **Sub-1.0 RR trades:** {total_sub1}\n")

    # Key verification result
    md_lines.append("## 🎯 Key Verification: Did Fixes Eliminate Sub-1.0 RR Trades?\n")
    if total_sub1 == 0:
        md_lines.append("**✅ PASS: Zero sub-1.0 RR trades across all assets.** The RR gate and asset thresholds are working correctly.\n")
    else:
        md_lines.append(f"**⚠️ FAIL: {total_sub1} sub-1.0 RR trades still present.** Investigation needed.\n")
        for sym in TARGET_ASSETS:
            if sym not in all_results:
                continue
            r = all_results[sym]
            if r['sub_1_rr_count'] > 0:
                md_lines.append(f"  - {sym}: {r['sub_1_rr_count']} sub-1RR trades")
                for t in r.get('sub_1_rr_trades', []):
                    md_lines.append(f"    - {t['variant']} {t['direction']}: RR={t['intended_rr']:.3f}, PnL={t['pnl_pips']:+.1f}p, {t['timestamp']}")
                md_lines.append("")

    # Per-asset detail
    md_lines.append("\n## Per-Asset Detail\n")
    for sym in TARGET_ASSETS:
        if sym not in all_results:
            continue
        r = all_results[sym]
        md_lines.append(f"### {sym}\n")
        md_lines.append(f"- **Total Trades:** {r['total_trades']} (W:{r['wins']} L:{r['losses']})")
        md_lines.append(f"- **Win Rate:** {r['win_rate']:.1f}%")
        md_lines.append(f"- **Avg Intended RR:** {r['avg_intended_rr']:.2f}")
        md_lines.append(f"- **Min Intended RR:** {r['min_intended_rr']:.2f}")
        md_lines.append(f"- **Max Intended RR:** {r['max_intended_rr']:.2f}")
        md_lines.append(f"- **Sub-1.0 RR Trades:** {r['sub_1_rr_count']}")
        md_lines.append(f"- **Gross P&L:** {r['gross_profit_pips'] + r['gross_loss_pips']:+.1f} pips")
        md_lines.append(f"- **Net P&L (after commission):** {r['net_pnl_after_commission_pips']:+.1f} pips")
        md_lines.append(f"- **Profit Factor:** {r['profit_factor']:.2f}")
        md_lines.append(f"- **Max Drawdown:** {r['max_drawdown_pips']:.1f} pips")
        md_lines.append(f"- **Data:** {r['total_bars']:,} bars, {r['total_sessions']} sessions")

        pv = r.get('per_variant', {})
        if pv:
            md_lines.append("\n| Variant | Trades | WR% | Avg RR | Min RR | PnL |")
            md_lines.append("|---------|--------|-----|--------|--------|------|")
            for vn in ["INITIAL", "CASCADE", "EWS"]:
                vd = pv.get(vn, {})
                if vd.get('trades', 0) > 0:
                    md_lines.append(
                        f"| {vn} | {vd['trades']} | {vd.get('win_rate', 0):.1f}% | "
                        f"{vd.get('avg_rr', 0):.2f} | {vd.get('min_rr', 0):.2f} | {vd.get('pnl_pips', 0):+.1f}p |"
                    )
                else:
                    md_lines.append(f"| {vn} | 0 | — | — | — | — |")
        md_lines.append("")

    if skipped:
        md_lines.append("\n## Skipped (No Data)\n")
        for s in skipped:
            md_lines.append(f"- {s}")

    md_lines.append(f"\n---\n*Report generated by p90_fix_verification.py @ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

    md_path = REPORTS_DIR / "p90_fix_verification.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))
    print(f"Markdown report: {md_path}")

    # ── Console summary ────────────────────────────────────────────────
    print(f"\n{'=' * 70}")
    print("VERIFICATION SUMMARY")
    print(f"{'=' * 70}")
    print(f"{'Asset':<10} {'Trades':>6} {'WR%':>6} {'AvgRR':>7} {'MinRR':>7} {'MaxRR':>7} {'Sub1':>5} {'NetP&L':>9}")
    print(f"{'─'*10} {'─'*6} {'─'*6} {'─'*7} {'─'*7} {'─'*7} {'─'*5} {'─'*9}")
    for sym in TARGET_ASSETS:
        if sym not in all_results:
            print(f"{sym:<10} {'SKIP':>6}")
            continue
        r = all_results[sym]
        print(f"{sym:<10} {r['total_trades']:>6} {r['win_rate']:>5.1f}% {r['avg_intended_rr']:>7.2f} "
              f"{r['min_intended_rr']:>7.2f} {r['max_intended_rr']:>7.2f} {r['sub_1_rr_count']:>5} "
              f"{r['net_pnl_after_commission_pips']:>+9.1f}")
    print(f"\nSub-1.0 RR trades across ALL assets: {total_sub1}")
    if total_sub1 == 0:
        print("✅ ALL SUB-1.0 RR TRADES ELIMINATED — FIXES VERIFIED")
    else:
        print(f"⚠️  {total_sub1} sub-1.0 RR trades remain — needs investigation")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
