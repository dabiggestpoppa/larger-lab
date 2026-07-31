"""
CEREBUS Tier Discovery — Symmetry Trap Calibration
Based on manual Code Appendix (Code 6) from MAD.
Uses K-Means clustering on Asian Range to find optimal tier cutoffs, AU, and Trigger.

Usage:
    python discover_tiers.py --csv EURGBP_PRO_M5.csv --pip 0.0001 --name EURGBP
    python discover_tiers.py --all  (runs all 17 new pairs)
"""

import pandas as pd
import numpy as np
import json
import argparse
import os
from pathlib import Path
from sklearn.cluster import KMeans

REPO_ROOT = Path(r"C:\Users\wifik\Desktop\projects\larger-lab")
DATA_DIR = REPO_ROOT / "quant-lab" / "data"
REPORTS_DIR = REPO_ROOT / "quant-lab" / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# ─── All 17 new pairs with their pip sizes ───
NEW_PAIRS = {
    "EURGBP": {"pip": 0.0001, "csv": "EURGBP_PRO_M5.csv"},
    "EURJPY": {"pip": 0.01, "csv": "EURJPY_PRO_M5.csv"},
    "EURAUD": {"pip": 0.0001, "csv": "EURAUD_PRO_M5.csv"},
    "EURNZD": {"pip": 0.0001, "csv": "EURNZD_PRO_M5.csv"},
    "EURCHF": {"pip": 0.0001, "csv": "EURCHF_PRO_M5.csv"},
    "EURCAD": {"pip": 0.0001, "csv": "EURCAD_PRO_M5.csv"},
    "USDCAD": {"pip": 0.0001, "csv": "USDCAD_PRO_M5.csv"},
    "AUDJPY": {"pip": 0.01, "csv": "AUDJPY_PRO_M5.csv"},
    "AUDNZD": {"pip": 0.0001, "csv": "AUDNZD_PRO_M5.csv"},
    "AUDCHF": {"pip": 0.0001, "csv": "AUDCHF_PRO_M5.csv"},
    "AUDCAD": {"pip": 0.0001, "csv": "AUDCAD_PRO_M5.csv"},
    "NZDJPY": {"pip": 0.01, "csv": "NZDJPY_PRO_M5.csv"},
    "NZDCHF": {"pip": 0.0001, "csv": "NZDCHF_PRO_M5.csv"},
    "NZDCAD": {"pip": 0.0001, "csv": "NZDCAD_PRO_M5.csv"},
    "CADJPY": {"pip": 0.01, "csv": "CADJPY_PRO_M5.csv"},
    "CADCHF": {"pip": 0.0001, "csv": "CADCHF_PRO_M5.csv"},
    "GBPCAD": {"pip": 0.0001, "csv": "GBPCAD_PRO_M5.csv"},
}


def discover_tiers(csv_path, pip_size=0.0001, name=""):
    """K-Means tier discovery from MAD's manual Code 6."""
    print(f"\n{'='*60}")
    print(f"  TIER DISCOVERY: {name}")
    print(f"  CSV: {csv_path} | pip_size: {pip_size}")
    print(f"{'='*60}")

    # 1. Load data
    df = pd.read_csv(csv_path, header=0)
    # Map columns: time -> dt, volume -> vol
    df = df.rename(columns={"time": "dt", "volume": "vol"})
    df["dt"] = pd.to_datetime(df["dt"])
    df = df.set_index("dt").sort_index()

    # Force UTC then convert to EST
    if df.index.tz is None:
        df = df.tz_localize("UTC")
    df = df.tz_convert("America/New_York")

    # Group by session (shifted by 3 hours to align with 3AM EST start)
    shifted = df.index - pd.Timedelta(hours=3)
    df["session"] = shifted.floor("D")

    ranges = []
    for day, data in df.groupby("session"):
        # Asian session: 19:00 to 03:00 EST
        asian = data[(data.index.hour >= 19) | (data.index.hour < 3)]
        if len(asian) >= 10:
            ar = (asian["high"].max() - asian["low"].min()) / pip_size
            ranges.append(ar)

    ranges = np.array(ranges).reshape(-1, 1)
    print(f"  Sessions analyzed: {len(ranges)}")
    print(f"  AR mean: {ranges.mean():.1f}p | std: {ranges.std():.1f}p")
    print(f"  AR p50: {np.percentile(ranges, 50):.1f}p | p90: {np.percentile(ranges, 90):.1f}p")

    # 2. K-Means Clustering (k=3)
    km = KMeans(n_clusters=3, random_state=42, n_init=10).fit(ranges)
    c = sorted(km.cluster_centers_.flatten())

    # 3. Calculate Cutoffs and Parameters
    # Arch fix v2: Percentile boundaries (33rd/66th) to ensure balanced tier distribution
    # K-Means midpoints are skewed by dead clusters — percentiles guarantee T1/T2/T3
    # each capture ~33% of trading days regardless of distribution shape.
    # AU and Trigger still use K-Means centroids (true core volatility of each cluster).
    cutoff1 = np.percentile(ranges, 33.3)
    cutoff2 = np.percentile(ranges, 66.6)

    results = {
        "T1": {
            "range_max": round(cutoff1, 2),
            "au": int(round(c[0] * 0.5)),
            "trig": int(round(c[0] * 0.5 * 1.2)),
        },
        "T2": {
            "range_min": round(cutoff1, 2),
            "range_max": round(cutoff2, 2),
            "au": int(round(c[1] * 0.5)),
            "trig": int(round(c[1] * 0.5 * 1.2)),
        },
        "T3": {
            "range_min": round(cutoff2, 2),
            "au": int(round(c[2] * 0.5)),
            "trig": int(round(c[2] * 0.5 * 1.2)),
        },
    }

    print(f"\n  === TIER CONFIG FOR {name} ===")
    print(f"  T1: Range < {results['T1']['range_max']} | AU = {results['T1']['au']} | Trigger = {results['T1']['trig']}")
    print(f"  T2: Range {results['T2']['range_min']} - {results['T2']['range_max']} | AU = {results['T2']['au']} | Trigger = {results['T2']['trig']}")
    print(f"  T3: Range > {results['T3']['range_min']} | AU = {results['T3']['au']} | Trigger = {results['T3']['trig']}")
    print(f"  ============================================================\n")

    return results


def run_all():
    """Run tier discovery for all 17 new pairs."""
    all_configs = {}
    errors = []

    for pair, info in NEW_PAIRS.items():
        csv_path = DATA_DIR / info["csv"]
        if not csv_path.exists():
            print(f"  MISSING: {csv_path}")
            errors.append(pair)
            continue

        try:
            config = discover_tiers(str(csv_path), info["pip"], pair)
            all_configs[pair] = config
        except Exception as e:
            print(f"  ERROR {pair}: {e}")
            errors.append(pair)

    # Save all configs
    out_path = REPORTS_DIR / "tier_discovery_all.json"
    with open(out_path, "w") as f:
        json.dump(all_configs, f, indent=2)

    # Generate markdown summary
    md_path = REPORTS_DIR / "tier_discovery_summary.md"
    with open(md_path, "w") as f:
        f.write("# CEREBUS ST — Tier Discovery Summary\n\n")
        f.write("**Method:** K-Means Clustering (k=3) on Asian Range (Code 6 from manual)\n\n")
        f.write("---\n\n")
        f.write("## Tier Configs (Copy-Paste Ready)\n\n")
        f.write("| Pair | T1 Range | T1 AU | T1 Trig | T2 Range | T2 AU | T2 Trig | T3 Range | T3 AU | T3 Trig |\n")
        f.write("|------|----------|-------|---------|----------|-------|---------|----------|-------|----------|\n")
        for pair, cfg in all_configs.items():
            t1 = cfg["T1"]
            t2 = cfg["T2"]
            t3 = cfg["T3"]
            f.write(f"| {pair} | <{t1['range_max']} | {t1['au']} | {t1['trig']} | {t2['range_min']}-{t2['range_max']} | {t2['au']} | {t2['trig']} | >{t3['range_min']} | {t3['au']} | {t3['trig']} |\n")

        f.write("\n---\n\n")
        f.write("## Python Config Snippets\n\n")
        for pair, cfg in all_configs.items():
            t1 = cfg["T1"]
            t2 = cfg["T2"]
            t3 = cfg["T3"]
            f.write(f"```python  # {pair}\n")
            f.write(f'"{pair}": {{\n')
            f.write(f'    "tiers": {{\n')
            f.write(f'        "T1": {{"ar_max": {t1["range_max"]}, "au": {t1["au"]}, "trigger": {t1["trig"]}}},\n')
            f.write(f'        "T2": {{"ar_max": {t2["range_max"]}, "au": {t2["au"]}, "trigger": {t2["trig"]}}},\n')
            f.write(f'        "T3": {{"ar_max": {t3["range_min"]}, "au": {t3["au"]}, "trigger": {t3["trig"]}}},\n')
            f.write(f'    }},\n')
            f.write(f'    "gear_shifts": {{\n')
            f.write(f'        "T1": [({t2["range_max"]}, "T2"), ({t3["range_min"]}, "T3")],\n')
            f.write(f'        "T2": [({t3["range_min"]}, "T3")],\n')
            f.write(f'    }},\n'),
            f.write(f"}}\n```\n\n")

        if errors:
            f.write(f"\n---\n\n## Errors / Missing\n\n")
            for e in errors:
                f.write(f"- {e}\n")

    print(f"\n{'#'*60}")
    print(f"  TIER DISCOVERY COMPLETE")
    print(f"  Calibrated: {len(all_configs)}/17")
    print(f"  Errors: {errors}")
    print(f"  JSON: {out_path}")
    print(f"  Report: {md_path}")
    print(f"{'#'*60}\n")

    return all_configs


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CEREBUS Tier Discovery")
    parser.add_argument("--csv", help="CSV file path")
    parser.add_argument("--pip", type=float, default=0.0001, help="Pip size")
    parser.add_argument("--name", default="", help="Asset name")
    parser.add_argument("--all", action="store_true", help="Run all 17 new pairs")
    args = parser.parse_args()

    if args.all:
        run_all()
    elif args.csv:
        discover_tiers(args.csv, args.pip, args.name)
    else:
        print("Usage: python discover_tiers.py --all  OR  --csv FILE --pip 0.0001 --name EURGBP")
