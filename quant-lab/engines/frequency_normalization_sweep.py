"""
CEREBUS FX v4.0 — Frequency Normalization Sweep
================================================
MAD Directive 2026-06-04: Calibrate trigger parameters for sub-2.5 tr/day
EUR pairs to hit 2.5-3.0 tr/day floor while maintaining WR>80% and PF>10.0.

Deficit pairs: EURGBP, EURCHF, EURCAD, EURNZD, EURAUD, EURJPY

Method: Descending trigger sweep (0.75x, 0.65x, 0.55x, 0.45x of native T1 trigger).
Guardrail: PF >= 10.0 AND WR >= 80%. Halt sweep when breached.

Outputs:
  - quant-lab/reports/frequency_normalization_sweep.json
  - quant-lab/reports/frequency_normalization_sweep_report.md
"""

from __future__ import annotations

import json
import logging
import sys
import io
from datetime import datetime

# Force UTF-8 output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ── Path Setup ────────────────────────────────────────────────────────────
REPO_ROOT = Path(r"C:\Users\wifik\Desktop\projects\larger-lab")
QUANT_LAB = REPO_ROOT / "quant-lab"
DATA_DIR = QUANT_LAB / "data"
REPORTS_DIR = QUANT_LAB / "reports"
CONFIGS_DIR = QUANT_LAB / "configs"
ENGINES_DIR = QUANT_LAB / "engines"

sys.path.insert(0, str(CONFIGS_DIR))
sys.path.insert(0, str(ENGINES_DIR))

REPORTS_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [SWEEP] %(levelname)s: %(message)s",
)
logger = logging.getLogger("frequency_sweep")
logging.getLogger("cerebus.symmetry_trap").setLevel(logging.WARNING)
logging.getLogger("cerebus.symmetry_trap_backtest").setLevel(logging.WARNING)

from asset_configs import ASSET_CONFIGS
from symmetry_trap_backtest import SymmetryTrapBacktest, BacktestResult, load_m5_csv

# ── Configuration ─────────────────────────────────────────────────────────

DEFICIT_PAIRS = ["EURGBP", "EURCHF", "EURCAD", "EURNZD", "EURAUD", "EURJPY"]

# Trigger multipliers to test (descending from baseline)
MULTIPLIERS = [1.0, 0.75, 0.65, 0.55, 0.45]

# Guardrail thresholds
MIN_PF = 10.0
MIN_WR = 80.0

# Target trades/day
TARGET_TPD = 2.5
TARGET_TPD_MAX = 3.0


def get_csv_path(asset_key: str) -> Optional[Path]:
    """Find CSV data file for asset."""
    # Pattern 1: {ASSET_KEY}_M5.csv
    p1 = DATA_DIR / f"{asset_key}_M5.csv"
    if p1.exists():
        return p1

    # Pattern 2: {asset_key}PRO_M5*.csv
    candidates = sorted(DATA_DIR.glob(f"{asset_key}PRO_M5*.csv"))
    if candidates:
        return max(candidates, key=lambda p: p.stat().st_size)

    # Pattern 3: {asset_key}m_M5*.csv
    candidates = sorted(DATA_DIR.glob(f"{asset_key}m_M5*.csv"))
    if candidates:
        return max(candidates, key=lambda p: p.stat().st_size)

    # Pattern 4: Generic
    candidates = sorted(DATA_DIR.glob(f"{asset_key}*M5*.csv"))
    if candidates:
        return max(candidates, key=lambda p: p.stat().st_size)

    return None


def build_swept_config(base_config: dict, multiplier: float) -> dict:
    """
    Create a modified config with trigger values scaled by the multiplier.
    AR gate set to 60.0 (or kept high) to avoid interfering with trigger sweep.
    AU values kept at baseline — only triggers change.
    """
    import copy
    cfg = copy.deepcopy(base_config)

    # Scale triggers for all tiers
    for tier_name in ["T1", "T2", "T3"]:
        if tier_name in cfg.get("tiers", {}):
            orig_trigger = cfg["tiers"][tier_name]["trigger"]
            cfg["tiers"][tier_name]["trigger"] = round(orig_trigger * multiplier, 2)
            # Set ar_max high to avoid AR gate interference
            cfg["tiers"][tier_name]["ar_max"] = 60.0

    return cfg


def run_single_backtest(
    asset_key: str,
    csv_path: Path,
    config: dict,
    label: str = "",
) -> Optional[dict]:
    """Run a single backtest and return serialized results."""
    pip_size = config["pip_value"]
    tier_config = config["tiers"]

    try:
        bt = SymmetryTrapBacktest(
            pip_size=pip_size,
            tier_config=tier_config,
            symbol=asset_key,
            config=config,
        )
        result: BacktestResult = bt.run_from_csv(str(csv_path))
    except Exception as e:
        logger.error(f"  ERROR {asset_key} ({label}): {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

    days = result.data_days
    tpd = result.total_trades / days if days > 0 else 0.0

    entry = {
        "label": label,
        "total_trades": result.total_trades,
        "wins": result.wins,
        "losses": result.losses,
        "win_rate": round(result.win_rate, 2),
        "pnl_pips": round(result.total_pnl_pips, 2),
        "profit_factor": round(result.profit_factor, 4) if result.profit_factor != float("inf") else 999.99,
        "sharpe": round(result.sharpe_ratio, 4),
        "max_drawdown_pips": round(result.max_drawdown_pips, 2),
        "expectancy_pips": round(result.expectancy_pips, 2),
        "avg_win_pips": round(result.avg_win_pips, 2),
        "avg_loss_pips": round(result.avg_loss_pips, 2),
        "data_bars": result.data_bars,
        "data_days": days,
        "trades_per_day": round(tpd, 4),
        "tier_stats": result.tier_stats,
        "loop_stats": result.loop_stats,
        "config_used": {
            "pip_value": config["pip_value"],
            "tiers": config["tiers"],
        },
    }
    return entry


def run_sweep_for_asset(asset_key: str, csv_path: Path) -> dict:
    """Run the full descending trigger sweep for a single asset."""
    base_config = ASSET_CONFIGS[asset_key]
    base_t1_trigger = base_config["tiers"]["T1"]["trigger"]

    print(f"\n{'='*60}")
    print(f"SWEEP: {asset_key} | Base T1 trigger: {base_t1_trigger}p")
    print(f"CSV: {csv_path.name} ({csv_path.stat().st_size / 1024 / 1024:.1f}MB)")
    print(f"{'='*60}")

    sweep_results = []
    optimal = None
    guardrail_breached = False

    for mult in MULTIPLIERS:
        new_t1_trigger = round(base_t1_trigger * mult, 2)
        print(f"\n  [{asset_key}] mult={mult:.2f} -> T1 trigger={new_t1_trigger}p")

        swept_config = build_swept_config(base_config, mult)
        label = f"{mult:.2f}x (T1={new_t1_trigger}p)"

        result = run_single_backtest(asset_key, csv_path, swept_config, label)
        if result is None:
            print(f"    -> ERROR, skipping")
            continue

        tpd = result["trades_per_day"]
        wr = result["win_rate"]
        pf = result["profit_factor"]
        tr = result["total_trades"]

        print(f"    -> {tr} trades | {tpd:.2f} tr/day | WR={wr:.1f}% | PF={pf:.2f}")

        sweep_results.append(result)

        # Check guardrail
        if pf < MIN_PF or wr < MIN_WR:
            print(f"    ⚠️ GUARDRAIL BREACHED (PF<{MIN_PF} or WR<{MIN_WR}%) — HALTING SWEEP")
            guardrail_breached = True
            break

        # Track optimal (highest tr/day that meets target)
        if tpd >= TARGET_TPD:
            if optimal is None or tpd < TARGET_TPD_MAX:
                optimal = result
                print(f"    [OK] TARGET REACHED ({tpd:.2f} tr/day)")
            elif tpd > TARGET_TPD_MAX and optimal is not None:
                # Previous result was closer to target range
                pass
        else:
            # Below target but above guardrail — keep as fallback
            if optimal is None:
                optimal = result
                print(f"    [BEST] Best so far (below target but above guardrail)")

    # If no result hit the target, use the last one (highest tr/day above guardrail)
    if optimal is None and sweep_results:
        optimal = sweep_results[-1]

    return {
        "asset_key": asset_key,
        "base_t1_trigger": base_t1_trigger,
        "sweep_results": sweep_results,
        "optimal_result": optimal,
        "guardrail_breached": guardrail_breached,
    }


def generate_report(all_sweep_data: List[dict]) -> str:
    """Generate the final normalization report."""
    lines = []
    lines.append("# Frequency Normalization Sweep Report")
    lines.append(f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"\n**Objective:** Normalize deficit pairs to 2.5-3.0 tr/day")
    lines.append(f"**Guardrail:** PF >= {MIN_PF}, WR >= {MIN_WR}%")
    lines.append(f"**AR gate:** Fixed at 60p for all tests (no interference)\n")

    # ── Summary Matrix ─────────────────────────────────────────────────
    lines.append("## Optimization Matrix\n")
    lines.append("| Asset | Old Mult (1.0x) | Old Tr/Day | **New Mult** | **New Tr/Day** | **New WR%** | **New PF** | Status |")
    lines.append("|-------|-----------------|------------|--------------|----------------|-------------|------------|--------|")

    for sd in all_sweep_data:
        ak = sd["asset_key"]
        base_trig = sd["base_t1_trigger"]

        # Find baseline (1.0x) result
        baseline = None
        for sr in sd["sweep_results"]:
            if sr["label"].startswith("1.00"):
                baseline = sr
                break

        old_tpd = baseline["trades_per_day"] if baseline else "?"
        old_wr = baseline["win_rate"] if baseline else "?"
        old_pf = baseline["profit_factor"] if baseline else "?"

        opt = sd.get("optimal_result")
        if opt:
            # Extract multiplier from label
            new_mult = opt["label"].split("x")[0].strip() + "x"
            new_tpd = opt["trades_per_day"]
            new_wr = opt["win_rate"]
            new_pf = opt["profit_factor"]

            if new_tpd >= TARGET_TPD:
                status = "OK TARGET"
            elif sd.get("guardrail_breached"):
                status = "GUARDRAIL"
            else:
                status = "BEST"

            lines.append(
                f"| {ak} | 1.00x ({base_trig}p) | {old_tpd} | "
                f"**{new_mult}** | **{new_tpd:.2f}** | **{new_wr:.1f}%** | **{new_pf:.2f}** | {status} |"
            )
        else:
            lines.append(f"| {ak} | 1.00x ({base_trig}p) | {old_tpd} | N/A | N/A | N/A | N/A | NO RESULT |")

    # ── Frequency Coefficient Table ────────────────────────────────────
    lines.append("\n## Frequency Coefficient Lookup Table\n")
    lines.append("| Asset | Base T1 Trigger | Optimal Multiplier | Optimal T1 Trigger | Coefficient |")
    lines.append("|-------|----------------|-------------------|--------------------|-------------|")

    for sd in all_sweep_data:
        ak = sd["asset_key"]
        base_trig = sd["base_t1_trigger"]
        opt = sd.get("optimal_result")
        if opt:
            # Parse multiplier from label
            mult_str = opt["label"].split("x")[0].strip()
            mult_val = float(mult_str)
            opt_trig = round(base_trig * mult_val, 2)
            lines.append(f"| {ak} | {base_trig}p | {mult_str}x | {opt_trig}p | {mult_val:.4f} |")
        else:
            lines.append(f"| {ak} | {base_trig}p | N/A | N/A | N/A |")

    # ── Detailed Sweep Results ─────────────────────────────────────────
    lines.append("\n## Detailed Sweep Results\n")
    for sd in all_sweep_data:
        ak = sd["asset_key"]
        lines.append(f"### {ak}\n")
        lines.append(f"- Base T1 Trigger: {sd['base_t1_trigger']}p")
        lines.append(f"- Guardrail Breached: {sd.get('guardrail_breached', False)}\n")
        lines.append("| Multiplier | T1 Trigger | Trades | Tr/Day | WR% | PF | PnL (pips) |")
        lines.append("|------------|-----------|--------|--------|-----|----|-----------|")
        for sr in sd["sweep_results"]:
            lines.append(
                f"| {sr['label']} | {sr['config_used']['tiers']['T1']['trigger']}p | "
                f"{sr['total_trades']} | {sr['trades_per_day']:.2f} | "
                f"{sr['win_rate']:.1f}% | {sr['profit_factor']:.2f} | "
                f"{sr['pnl_pips']:+.1f} |"
            )
        lines.append("")

    # ── Normalization Formula ──────────────────────────────────────────
    lines.append("## Normalization Formula\n")
    lines.append("```")
    lines.append("Optimal_Trigger = Base_T1_Trigger × Frequency_Coefficient")
    lines.append("")
    lines.append("Where Frequency_Coefficient is pair-specific:")
    for sd in all_sweep_data:
        ak = sd["asset_key"]
        opt = sd.get("optimal_result")
        if opt:
            mult_str = opt["label"].split("x")[0].strip()
            mult_val = float(mult_str)
            lines.append(f"  {ak}: coefficient = {mult_val:.4f}")
    lines.append("```")

    lines.append(f"\n---\n*Generated by frequency_normalization_sweep.py @ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    return "\n".join(lines)


# ── MAIN ──────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("FREQUENCY NORMALIZATION SWEEP")
    print("MAD Directive 2026-06-04")
    print("=" * 60)
    print(f"Deficit pairs: {', '.join(DEFICIT_PAIRS)}")
    print(f"Multipliers: {MULTIPLIERS}")
    print(f"Guardrail: PF >= {MIN_PF}, WR >= {MIN_WR}%")
    print(f"Target: {TARGET_TPD}-{TARGET_TPD_MAX} tr/day")

    # Check data availability
    print("\n--- Data Check ---")
    data_map = {}
    for ak in DEFICIT_PAIRS:
        csv_path = get_csv_path(ak)
        if csv_path:
            data_map[ak] = csv_path
            print(f"  {ak}: {csv_path.name} ({csv_path.stat().st_size / 1024 / 1024:.1f}MB)")
        else:
            print(f"  {ak}: ❌ NO DATA")

    if not data_map:
        print("\n❌ No data files found for any deficit pair. Aborting.")
        return

    # Run sweeps
    all_sweep_data = []
    for ak in DEFICIT_PAIRS:
        if ak not in data_map:
            print(f"\n⏭️  Skipping {ak} — no data")
            continue
        sweep_data = run_sweep_for_asset(ak, data_map[ak])
        all_sweep_data.append(sweep_data)

    # Save JSON results
    json_path = REPORTS_DIR / "frequency_normalization_sweep.json"
    output = {
        "generated": datetime.now().isoformat(),
        "objective": f"Normalize to {TARGET_TPD}-{TARGET_TPD_MAX} tr/day",
        "guardrail": {"min_pf": MIN_PF, "min_wr": MIN_WR},
        "multipliers_tested": MULTIPLIERS,
        "results": all_sweep_data,
    }
    with open(json_path, "w") as f:
        json.dump(output, f, indent=2, default=str)
    print(f"\nSaved JSON: {json_path}")

    # Generate report
    report = generate_report(all_sweep_data)
    report_path = REPORTS_DIR / "frequency_normalization_sweep_report.md"
    with open(report_path, "w") as f:
        f.write(report)
    print(f"Saved report: {report_path}")

    # Print summary
    print("\n" + "=" * 60)
    print("SWEEP COMPLETE — SUMMARY")
    print("=" * 60)
    for sd in all_sweep_data:
        ak = sd["asset_key"]
        opt = sd.get("optimal_result")
        if opt:
            mult_str = opt["label"].split("x")[0].strip() + "x"
            print(f"  {ak:10s} | {mult_str:>8s} | {opt['trades_per_day']:.2f} tr/day | WR={opt['win_rate']:.1f}% | PF={opt['profit_factor']:.2f}")
        else:
            print(f"  {ak:10s} | NO RESULT")


if __name__ == "__main__":
    main()
