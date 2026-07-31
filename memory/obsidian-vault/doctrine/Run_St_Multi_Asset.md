# Run St Multi Asset

> Category: doctrine | Imported: 2026-06-02 01:13 UTC

Tags: #doctrine #python #engines

```python
"""
CEREBUS FX v4.0 — Symmetry Trap Multi-Asset Backtest Runner
============================================================
Runs Symmetry Trap backtest across ALL assets in ASSET_CONFIGS registry.
Uses per-asset config injection (tier config, pip_size, etc.).

Outputs:
  - quant-lab/reports/st_multi_asset_results.json  (detailed per-asset)
  - quant-lab/reports/st_multi_asset_report.md     (human-readable summary)
  - progress/st-multi-asset-progress.md            (progress log)
"""

from __future__ import annotations

import csv
import json
import os
import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ── Path Setup ────────────────────────────────────────────────────────────
REPO_ROOT = Path(r"C:\Users\wifik\Desktop\projects\larger-lab")
QUANT_LAB = REPO_ROOT / "quant-lab"
DATA_DIR = QUANT_LAB / "data"
REPORTS_DIR = QUANT_LAB / "reports"
PROGRESS_DIR = REPO_ROOT / "progress"
CONFIGS_DIR = QUANT_LAB / "configs"
ENGINES_DIR = QUANT_LAB / "engines"

sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(CONFIGS_DIR))
sys.path.insert(0, str(ENGINES_DIR))

REPORTS_DIR.mkdir(parents=True, exist_ok=True)
PROGRESS_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [ST-MULTI] %(levelname)s: %(message)s",
)
logger = logging.getLogger("st_multi_asset")
# Suppress engine-level INFO (too verbose for multi-asset)
logging.getLogger("cerebus.symmetry_trap").setLevel(logging.WARNING)
logging.getLogger("cerebus.symmetry_trap_backtest").setLevel(logging.WARNING)

# ── Imports ───────────────────────────────────────────────────────────────
from asset_configs import ASSET_CONFIGS
from symmetry_trap_backtest import SymmetryTrapBacktest, format_report, BacktestResult, load_m5_csv

PROGRESS_FILE = PROGRESS_DIR / "st-multi-asset-progress.md"


def log_progress(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(PROGRESS_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def init_progress():
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        f.write(f"# Symmetry Trap Multi-Asset Backtest Progress\n")
        f.write(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")


# ── STEP 1: Check existing CSV data ───────────────────────────────────────

def get_existing_data() -> Dict[str, Path]:
    """Scan DATA_DIR for M5 CSV files and map to asset keys."""
    data_map: Dict[str, Path] = {}

    # Known file patterns: {ASSETKEY}_M5.csv, {ASSETKEY}PRO_M5*.csv, etc.
    all_csvs = sorted(DATA_DIR.glob("*.csv"))

    for asset_key in ASSET_CONFIGS:
        # Pattern 1: {ASSET_KEY}_M5.csv  (e.g., EURUSD_M5.csv)
        p1 = DATA_DIR / f"{asset_key}_M5.csv"
        if p1.exists():
            data_map[asset_key] = p1
            continue

        # Pattern 2: {asset_key}PRO_M5*.csv  (e.g., EURUSDPRO_M5_2023_2025.csv)
        candidates = sorted(DATA_DIR.glob(f"{asset_key}PRO_M5*.csv"))
        if candidates:
            # Pick the largest file (most data)
            best = max(candidates, key=lambda p: p.stat().st_size)
            data_map[asset_key] = best
            continue

        # Pattern 3: {asset_key}m_M5*.csv  (e.g., EURUSDm_M5.csv)
        candidates = sorted(DATA_DIR.glob(f"{asset_key}m_M5*.csv"))
        if candidates:
            best = max(candidates, key=lambda p: p.stat().st_size)
            data_map[asset_key] = best
            continue

        # Pattern 4: Generic — any CSV starting with asset_key
        candidates = sorted(DATA_DIR.glob(f"{asset_key}*M5*.csv"))
        if candidates:
            best = max(candidates, key=lambda p: p.stat().st_size)
            data_map[asset_key] = best
            continue

    return data_map


# ── STEP 2: MT5 Data Fetching ─────────────────────────────────────────────

def try_fetch_mt5() -> Dict[str, Path]:
    """Try connecting to MT5 and fetching missing data. Returns newly fetched paths."""
    try:
        import MetaTrader5 as mt5
    except ImportError:
        logger.warning("MetaTrader5 not installed — skipping MT5 fetch")
        return {}

    if not mt5.initialize():
        err = mt5.last_error()
        logger.warning(f"MT5 init failed: {err} — skipping MT5 fetch")
        return {}

    try:
        account = mt5.account_info()
        if account:
            logger.info(f"MT5 Connected: {account.name} | {account.server}")
        else:
            logger.warning("MT5 initialized but no account info")
    except Exception:
        pass

    mt5_timeframe = mt5.TIMEFRAME_M5
    start_date = datetime(2022, 1, 1)
    end_date = datetime.now()
    newly_fetched: Dict[str, Path] = {}

    # Discover available symbols once
    all_symbols = []
    try:
        raw = mt5.symbols_get()
        if raw:
            all_symbols = [s.name for s in raw]
    except Exception:
        all_symbols = []

    suffixes = [".PRO", "m", ".", ".MICRO", ".RAW", ""]

    for asset_key in ASSET_CONFIGS:
        # Check if CSV data already exists (as standard {ASSET_KEY}_M5.csv)
        existing_csv = DATA_DIR / f"{asset_key}_M5.csv"
        if existing_csv.exists():
            continue

        # Try to find the right symbol name
        found_symbol = None
        for suffix in suffixes:
            candidate = f"{asset_key}{suffix}"
            if candidate in all_symbols:
                found_symbol = candidate
                break

        if found_symbol is None:
            # Try without suffix — check if asset_key matches directly
            if asset_key in all_symbols:
                found_symbol = asset_key
            elif f"{asset_key}.PRO" in all_symbols:
                found_symbol = f"{asset_key}.PRO"
            else:
                # Last resort: partial match
                for s in all_symbols:
                    if asset_key in s and "." not in s.replace(asset_key, ""):
                        found_symbol = s
                        break

        if found_symbol is None:
            log_progress(f"  [MT5] {asset_key}: symbol not found in MT5 — skipping")
            continue

        try:
            symbol_info = mt5.symbol_info(found_symbol)
            if symbol_info and not symbol_info.visible:
                mt5.symbol_select(found_symbol, True)

            rates = mt5.copy_rates_range(found_symbol, mt5_timeframe, start_date, end_date)
            if rates is None or len(rates) == 0:
                log_progress(f"  [MT5] {asset_key} ({found_symbol}): no data returned")
                continue

            # Convert to CSV with columns: timestamp,open,high,low,close,volume
            import pandas as pd
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df = df.rename(columns={
                'time': 'timestamp',
                'open': 'open', 'high': 'high', 'low': 'low', 'close': 'close',
                'tick_volume': 'volume',
            })
            df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
            df['timestamp'] = df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
            df = df[df['timestamp'].str.slice(0, 10).apply(
                lambda d: True
            )]  # keep all

            out_path = DATA_DIR / f"{asset_key}_M5.csv"
            df.to_csv(out_path, index=False)
            size_mb = out_path.stat().st_size / 1024 / 1024
            log_progress(f"  [MT5] {asset_key} ({found_symbol}): saved {len(df):,} bars ({size_mb:.1f}MB) -> {out_path.name}")
            newly_fetched[asset_key] = out_path

        except Exception as e:
            log_progress(f"  [MT5] {asset_key} ({found_symbol}): ERROR — {e}")

    try:
        mt5.shutdown()
    except Exception:
        pass

    return newly_fetched


# ── STEP 3: Run backtest per asset ────────────────────────────────────────

def run_asset_backtest(asset_key: str, csv_path: Path) -> Optional[dict]:
    """Run Symmetry Trap backtest for a single asset with config injection."""
    config = ASSET_CONFIGS[asset_key]
    pip_size = config["pip_value"]
    tier_config = config["tiers"]

    log_asset = f"{asset_key} ({config.get('name', asset_key)})"
    csv_size_mb = csv_path.stat().st_size / 1024 / 1024
    log_progress(f"  Running {log_asset} | pip_size={pip_size} | csv={csv_path.name} ({csv_size_mb:.1f}MB)")

    try:
        bt = SymmetryTrapBacktest(
            pip_size=pip_size,
            tier_config=tier_config,
            symbol=asset_key,
            config=config,
        )
        result: BacktestResult = bt.run_from_csv(str(csv_path))
    except Exception as e:
        log_progress(f"  ERROR {log_asset}: {e}")
        import traceback
        log_progress(traceback.format_exc())
        return None

    # Serialize results
    report_text = format_report(result)
    log_progress(f"  {log_asset}: {result.total_trades} trades | WR={result.win_rate:.1f}% | PnL={result.total_pnl_pips:+.1f}p | PF={result.profit_factor:.2f}")

    # Flags
    flags = []
    if result.total_trades == 0:
        flags.append("ZERO_TRADES")
    if result.win_rate < 50.0 and result.total_trades > 0:
        flags.append("LOW_WR")
    if result.win_rate > 99.0 and result.total_trades > 5:
        flags.append("SUSPICIOUS_HIGH_WR")

    entry = {
        "asset_key": asset_key,
        "name": config.get("name", asset_key),
        "config_used": {
            "pip_value": config["pip_value"],
            "k_factor": config["k_factor"],
            "sl_method": config.get("sl_method", "N/A"),
            "csv_file": csv_path.name,
        },
        "total_trades": result.total_trades,
        "wins": result.wins,
        "losses": result.losses,
        "win_rate": round(result.win_rate, 2),
        "pnl_pips": round(result.total_pnl_pips, 2),
        "profit_factor": round(result.profit_factor, 4) if result.profit_factor != float("inf") else 999.99,
        "sharpe": round(result.sharpe_ratio, 4),
        "max_drawdown_pips": round(result.max_drawdown_pips, 2),
        "max_drawdown_pct": round(result.max_drawdown_pct, 4),
        "expectancy_pips": round(result.expectancy_pips, 2),
        "avg_win_pips": round(result.avg_win_pips, 2),
        "avg_loss_pips": round(result.avg_loss_pips, 2),
        "long_trades": result.long_trades,
        "long_wr": round(result.long_wr, 2),
        "long_pnl_pips": round(result.long_pnl, 2),
        "short_trades": result.short_trades,
        "short_wr": round(result.short_wr, 2),
        "short_pnl_pips": round(result.short_pnl, 2),
        "tier_stats": result.tier_stats,
        "hourly_stats": result.hourly_stats,
        "loop_stats": result.loop_stats,
        "data_bars": result.data_bars,
        "data_days": result.data_days,
        "kelly": round(result.kelly_criterion, 4),
        "max_consec_wins": result.max_consec_wins,
        "max_consec_losses": result.max_consec_losses,
        "flags": flags,
        "report_text": report_text,
    }
    return entry


# ── STEP 4: Generate summary report ───────────────────────────────────────

def generate_summary(all_results: List[dict], skipped: List[str], no_data: List[str]) -> str:
    lines = []
    lines.append("# Symmetry Trap Multi-Asset Backtest Report")
    lines.append(f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    lines.append("## Summary Table\n")
    lines.append("| Asset | Trades | WR% | PnL (pips) | PF | Sharpe | MaxDD (pips) | T1 | T2 | T3 | Flags |")
    lines.append("|-------|--------|-----|------------|----|--------|--------------|----|----|----|-------|")

    total_pnl = 0.0
    total_trades = 0
    for r in sorted(all_results, key=lambda x: x["pnl_pips"], reverse=True):
        ts = r.get("tier_stats", {})
        t1 = ts.get("T1", {}).get("wr", "-")
        t2 = ts.get("T2", {}).get("wr", "-")
        t3 = ts.get("T3", {}).get("wr", "-")
        t1s = f"{t1}%" if isinstance(t1, (int, float)) else t1
        t2s = f"{t2}%" if isinstance(t2, (int, float)) else t2
        t3s = f"{t3}%" if isinstance(t3, (int, float)) else t3
        flags_str = ", ".join(r.get("flags", [])) or "OK"
        lines.append(
            f"| {r['asset_key']} | {r['total_trades']} | {r['win_rate']:.1f}% | "
            f"{r['pnl_pips']:+.1f} | {r['profit_factor']:.2f} | {r['sharpe']:.2f} | "
            f"{r['max_drawdown_pips']:.1f} | {t1s} | {t2s} | {t3s} | {flags_str} |"
        )
        total_pnl += r["pnl_pips"]
        total_trades += r["total_trades"]

    lines.append(f"\n**Total Trades:** {total_trades} | **Total PnL:** {total_pnl:+.1f} pips\n")

    # Aggregate tier stats
    lines.append("## Aggregate Tier Summary\n")
    lines.append("| Tier | Total Trades | Avg WR% | Total PnL |")
    lines.append("|------|-------------|---------|-----------|")
    for tier in ["T1", "T2", "T3"]:
        t_trades = sum(r["tier_stats"].get(tier, {}).get("trades", 0) for r in all_results if r.get("tier_stats"))
        t_pnl = sum(r["tier_stats"].get(tier, {}).get("pnl", 0) for r in all_results if r.get("tier_stats"))
        wrs = [r["tier_stats"][tier]["wr"] for r in all_results if r.get("tier_stats") and tier in r["tier_stats"]]
        avg_wr = sum(wrs) / len(wrs) if wrs else 0
        lines.append(f"| {tier} | {t_trades} | {avg_wr:.1f}% | {t_pnl:+.1f}p |")

    # Per-asset detailed reports
    lines.append("\n## Detailed Per-Asset Reports\n")
    for r in sorted(all_results, key=lambda x: x["pnl_pips"], reverse=True):
        lines.append(f"### {r['asset_key']} — {r['name']}\n")
        lines.append(f"```\n{r['report_text']}\n```\n")

    # Skipped / No data
    if skipped:
        lines.append("## Skipped (MT5 Not Available)\n")
        for s in skipped:
            lines.append(f"- {s}")
        lines.append("")
    if no_data:
        lines.append("## No Data Available\n")
        for n in no_data:
            lines.append(f"- {n}")
        lines.append("")

    lines.append(f"---\n*Report generated by run_st_multi_asset.py @ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    return "\n".join(lines)


# ── MAIN ──────────────────────────────────────────────────────────────────

def main():
    init_progress()
    log_progress("=" * 60)
    log_progress("SYMMETRY TRAP MULTI-ASSET BACKTEST")
    log_progress("=" * 60)
    log_progress(f"Total assets in registry: {len(ASSET_CONFIGS)}")
    log_progress(f"Assets: {', '.join(ASSET_CONFIGS.keys())}")

    # ── Step 1: Check existing data ──────────────────────────────────────
    log_progress("\n--- STEP 1: Checking existing CSV data ---")
    data_map = get_existing_data()
    log_progress(f"Found CSV data for {len(data_map)} assets: {', '.join(data_map.keys())}")

    missing = [k for k in ASSET_CONFIGS if k not in data_map]
    log_progress(f"Missing data for {len(missing)} assets: {', '.join(missing)}")

    # ── Step 2: Try MT5 fetch ────────────────────────────────────────────
    log_progress("\n--- STEP 2: Attempting MT5 data fetch ---")
    try:
        fetched = try_fetch_mt5()
        log_progress(f"Successfully fetched {len(fetched)} assets from MT5: {', '.join(fetched.keys())}")
        data_map.update(fetched)
    except Exception as e:
        log_progress(f"MT5 fetch failed entirely: {e}")

    still_missing = [k for k in ASSET_CONFIGS if k not in data_map]
    if still_missing:
        log_progress(f"Still missing data for {len(still_missing)} assets: {', '.join(still_missing)}")

    # ── Step 3: Run backtests ────────────────────────────────────────────
    log_progress("\n--- STEP 3: Running Symmetry Trap backtests ---")
    all_results: List[dict] = []
    run_errors: List[str] = []

    # Determine processing order: existing data first
    for asset_key in ASSET_CONFIGS:
        if asset_key not in data_map:
            continue

        csv_path = data_map[asset_key]
        log_progress(f"\n>>> {asset_key}: {csv_path.name}")

        entry = run_asset_backtest(asset_key, csv_path)
        if entry is not None:
            all_results.append(entry)
        else:
            run_errors.append(asset_key)

        # Append per-asset report to progress
        log_progress(f"--- Done: {asset_key} ---")

    # ── Step 4: Generate reports ─────────────────────────────────────────
    log_progress("\n--- STEP 4: Generating reports ---")

    # JSON results
    json_data = {
        "generated": datetime.now().isoformat(),
        "total_assets_in_registry": len(ASSET_CONFIGS),
        "assets_tested": len(all_results),
        "assets_missing_data": still_missing,
        "assets_with_errors": run_errors,
        "results": all_results,
    }
    json_path = REPORTS_DIR / "st_multi_asset_results.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2, default=str)
    log_progress(f"Saved JSON results to {json_path}")

    # Markdown summary
    md_report = generate_summary(all_results, run_errors, still_missing)
    md_path = REPORTS_DIR / "st_multi_asset_report.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_report)
    log_progress(f"Saved markdown report to {md_path}")

    # ── Final flags check ────────────────────────────────────────────────
    log_progress("\n--- Verification ---")
    for r in all_results:
        flags = r.get("flags", [])
        if flags:
            log_progress(f"  FLAG {r['asset_key']}: {', '.join(flags)}")
        else:
            log_progress(f"  OK   {r['asset_key']}: WR={r['win_rate']:.1f}% | Trades={r['total_trades']}")

    log_progress(f"\n=== COMPLETE: {len(all_results)}/{len(ASSET_CONFIGS)} assets backtested ===")

    # Print summary table to console
    print("\n\n" + "=" * 70)
    print("MULTI-ASSET BACKTEST SUMMARY")
    print("=" * 70)
    for r in sorted(all_results, key=lambda x: x["pnl_pips"], reverse=True):
        print(f"  {r['asset_key']:10s} | {r['total_trades']:5d} tr | WR {r['win_rate']:5.1f}% | "
              f"PnL {r['pnl_pips']:+8.1f}p | PF {r['profit_factor']:.2f} | "
              f"Sharpe {r['sharpe']:+.2f} | DD {r['max_drawdown_pips']:.1f}p")
    print(f"\n{'':10s}   {sum(r['total_trades'] for r in all_results):5d} tr | "
          f"Total PnL {sum(r['pnl_pips'] for r in all_results):+.1f} pips")


if __name__ == "__main__":
    main()

```

LINKS:
[[Codemap]]
[[01 System Overview]]
[[02 Agent Workflow]]
[[03 Srra Topology]]
[[04 Data And Storage]]
[[Agents]]
[[Api Reference]]
[[Cg 1 Mermaid Specs]]
[[Cg 1 Revised]]
[[Cg 2 Mermaid Specs]]
[[Cg 2 World Model Activation]]
[[Cg 3 Openclaw Anchor]]
[[Cg 3 Relational Topology]]
[[Cg 4 Execution Intelligence]]
[[Cg 4 Mermaid Specs]]
[[Cg 5 Continuity Intelligence]]
[[Cg 6 Meta Cognition]]
[[Cg 7 Multi Scale Orchestration]]
[[Cg 8 Operator Coevolution]]
[[Cg 9 Autonomous Strategic Field]]
[[Chaos Scenarios]]
[[Chat Response Bug Diagram]]
[[Cleanup Report]]
[[Code Quality]]
[[Contributing]]
[[Debugging]]
[[Domain Micro Doctrines]]
[[Harness Engineering]]
[[Heartbeat]]
[[Identity]]
[[Master Plan 2026 05 18]]
[[Master Plan Observer Core]]
[[Master Prompt]]
[[Module Guide]]
[[Observer Core Workspace State]]
[[Oce Unified Frontend Plan]]
[[O 6 Implementation Plan]]
[[O 7 Persistent Field Doc]]
[[Phase10]]
[[Phase Breakdown]]
[[Principles]]
[[Project Progress Clean]]
[[Quality Review]]
[[Quality Review Feedback]]
[[Readme]]
[[Soul]]
[[Sub Agent Rules]]
[[Team Tasks]]
[[Telegram Bot Setup]]
[[Testing]]
[[Test Manual]]
[[Tools]]
[[Topological Cognition Architecture]]
[[User]]
[[Workspace State]]
[[Progress]]
[[Citation Workflow]]
[[Patterns]]
[[Server]]
[[Standard]]
[[Asset Configs]]
[[Convergence Indicator]]
[[Dmr Standalone Backtest]]
[[P90 Backtest]]
[[P90 Count Ews]]
[[P90 Dmr Backtest]]
[[P90 Dmr Combo Backtest]]
[[P90 Dmr Overlay Backtest]]
[[P90 Engine]]
[[P90 Engine Dmr]]
[[P90 Gap Check]]
[[P90 Trace Trades]]
[[P90 Usdchf Backtest]]
[[Run Majors Backtest]]
[[Run Top5 Backtest Mc]]
[[St Batch2 Runner]]
[[St Batch Runner]]
[[Symmetry Trap]]
[[Symmetry Trap Backtest]]
[[Symmetry Trap Monte Carlo]]
[[Memory]]
[[Atomic Sym Trap]]
[[Blind Chain Debug]]
[[Blind Chain Diag]]
[[Blind Chain Engine]]
[[Blind Chain Exact]]
[[Blind Chain V2 Debug]]
[[Blind Chain V2 Sl Calibrated]]
[[Blind Chain V3]]
[[Cerebus Resolution Engine]]
[[Constraint Anchor Engine]]
[[Debug Days]]
[[Debug One Day]]
[[Debug St]]
[[Debug Trace]]
[[Diag Option B]]
[[Diag V5]]
[[Dmr Strategy]]
[[Dual Engine]]
[[Naut Asset Config]]
[[P90 Cfd Expansion Engine]]
[[P90 Cfd Expansion Engine V2]]
[[P90 Cfd Expansion Engine V3]]
[[P90 Cfd Expansion Engine V4]]
[[P90 Cfd Expansion Engine V5]]
[[P90 Strategy]]
[[Shared]]
[[Stall Harvest Cfd Engine]]
[[Symmetry Trap Engine]]
[[Symmetry Trap Exact]]
[[Symmetry Trap Option B]]
[[Symmetry Trap Strategy]]
[[Symmetry Trap V4]]
[[Symmetry Trap V5]]
[[Symmetry Trap V6 Exact]]
[[Symmetry Trap V7B Sl Calibrated]]
[[Symmetry Trap V7 Sl Calibrated]]
[[Two Plays Engine]]
[[Adaptation Engine]]
[[Agent Lifecycle]]
[[Agent Spawner]]
[[Attractor Analysis]]
[[Autonomous Repair]]
[[Capability Matcher]]
[[Complexity Scorer]]
[[Consensus Memory]]
[[Consensus Replay]]
[[Context Injector]]
[[Continuity Preserver]]
[[Data Fetcher]]
[[Dormant State Manager]]
[[Environmental Monitor]]
[[Event Schema]]
[[Execution Boundary]]
[[Failure Analyzer]]
[[Indicators]]
[[Journal]]
[[Loader]]
[[Long Horizon Memory]]
[[Metrics]]
[[Model Selector]]
[[Multi Agent Coordinator]]
[[Observability Stress]]
[[Observer Consensus]]
[[Observer Evolution]]
[[Observer Persistence]]
[[Observer Registry]]
[[Observer Specialization]]
[[Openrouter Gateway]]
[[Operational Drift Detect]]
[[Operational Replay]]
[[Operational Scoring]]
[[Passive Awareness]]
[[Pattern Memory]]
[[Persistent Runtime]]
[[Persistent Scheduler]]
[[Recovery Persistence]]
[[Routing Consensus]]
[[Routing Learning]]
[[Runtime Heartbeat]]
[[Spawn Blueprint]]
[[Spawn Planner]]
[[Spawn Registry]]
[[Spawn Replay]]
[[Structural Anchor]]
[[Synthesizer]]
[[Task Classifier]]
[[Temporal Graph]]
[[Test Journal]]
[[Test Loader]]
[[Topology Learning]]
[[Trace Collector]]
[[Trace Feedback]]
[[Workflow Distiller]]
[[Workflow Memory]]
[[Autonomous Orchestrator]]
[[Chat Log]]
[[Command Router]]
[[Context Distiller]]
[[Continuity Memory]]
[[Event Awareness]]
[[Graph Traversal]]
[[Observer Conversation Runtime]]
[[Observer Lifecycle]]
[[Observer Session]]
[[Observer State]]
[[Pattern Distillation]]
[[Primary Observer]]
[[Report Return]]
[[Runtime Awareness]]
[[Semantic Retrieval]]
[[Task Executor]]
[[Task Intent Analyzer]]
[[Vault]]
[[Compressor]]
[[Error Intelligence]]
[[Knowledge Importer]]
[[Linker]]
[[Live Sync]]
[[Memory Distiller]]
[[Note Standard]]
[[Pattern Crystallizer]]
[[Taxonomy]]
[[Test Compressor]]
[[Test Context Injector]]
[[Test Error Intelligence]]
[[Test Linker]]
[[Test Memory Distiller]]
[[Test Note Standard]]
[[Test Pattern Crystallizer]]
[[Test Taxonomy]]
[[Test Vault Writer]]
[[Vault Writer]]
[[Interpreter]]
[[Semantic State]]
[[Telegram Gateway]]
