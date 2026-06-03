"""
CEREBUS Atomic Structure Calibration â€” FX Pairs
Runs Asian Range analysis on M5 CSV data to determine:
- AR mean, std, p50, p90, p95 per pair
- Tier distribution (how many days fall in T1/T2/T3/NO_GO)
- Recommended tier configs (ar_max, au, trigger) based on actual AR

Usage:
    python calibrate_fx_atomic.py
"""

import pandas as pd
import numpy as np
import json
import os
from pathlib import Path

REPO_ROOT = Path(r"C:\Users\wifik\Desktop\projects\larger-lab")
DATA_DIR = REPO_ROOT / "quant-lab" / "data"
REPORTS_DIR = REPO_ROOT / "quant-lab" / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# â”€â”€â”€ Reference Tier Config (from existing calibrated pairs) â”€â”€â”€
# These are the WORKING configs from Phase 0 ground truth pairs
REF_TIER_CONFIGS = {
    "EURUSD": {"ar_max": 20.0, "au": 10.0, "trigger": 12.0, "pip_size": 0.0001},
    "GBPJPY": {"ar_max": 35.0, "au": 18.0, "trigger": 21.0, "pip_size": 0.01},
    "GBPCHF": {"ar_max": 35.0, "au": 18.0, "trigger": 21.0, "pip_size": 0.0001},
    "GBPAUD": {"ar_max": 35.0, "au": 18.0, "trigger": 21.0, "pip_size": 0.0001},
    "GBPNZD": {"ar_max": 35.0, "au": 18.0, "trigger": 21.0, "pip_size": 0.0001},
    "NZDUSD": {"ar_max": 20.0, "au": 10.0, "trigger": 12.0, "pip_size": 0.0001},
    "USDCHF": {"ar_max": 18.0, "au": 9.0, "trigger": 11.0, "pip_size": 0.0001},
    "USDJPY": {"ar_max": 30.0, "au": 15.0, "trigger": 18.0, "pip_size": 0.01},
    "AUDUSD": {"ar_max": 18.0, "au": 9.0, "trigger": 11.0, "pip_size": 0.0001},
    "CHFJPY": {"ar_max": 30.0, "au": 15.0, "trigger": 18.0, "pip_size": 0.01},
}

# â”€â”€â”€ All 17 NEW pairs to calibrate â”€â”€â”€
NEW_PAIRS = [
    "EURGBP", "EURJPY", "EURAUD", "EURNZD", "EURCHF", "EURCAD",
    "USDCAD", "AUDJPY", "AUDNZD", "AUDCHF", "AUDCAD",
    "NZDJPY", "NZDCHF", "NZDCAD", "CADJPY", "CADCHF", "GBPCAD",
]

# â”€â”€â”€ JPY pairs need pip_size=0.01, others 0.0001 â”€â”€â”€
JPY_PAIRS = {"EURJPY", "AUDJPY", "NZDJPY", "CADJPY", "CHFJPY", "GBPJPY", "USDJPY"}


def find_csv(asset_key):
    """Find CSV file for an asset key."""
    patterns = [
        DATA_DIR / f"{asset_key}_M5.csv",
        DATA_DIR / f"{asset_key}_PRO_M5.csv",
        DATA_DIR / f"{asset_key}PRO_M5.csv",
    ]
    for p in patterns:
        if p.exists():
            return p
    # Generic glob
    candidates = sorted(DATA_DIR.glob(f"{asset_key}*M5*.csv"))
    if candidates:
        return max(candidates, key=lambda p: p.stat().st_size)
    return None


def classify_tier(ar_pips, tier_config):
    """Classify AR into tier based on config."""
    for tn in ("T1", "T2", "T3"):
        if ar_pips <= tier_config[tn]["ar_max"]:
            return tn, tier_config[tn]["au"], tier_config[tn]["trigger"]
    return "NO_GO", 0.0, 0.0


def calc_daily_asian_range(day_bars, pip_size, asian_start=0, asian_end=3):
    """Calculate Asian Range from M5 bars. Asian session: 00:00-03:00 UTC."""
    asian_bars = day_bars[
        (day_bars["hour"] >= asian_start) & (day_bars["hour"] < asian_end)
    ]
    if len(asian_bars) < 3:
        return None
    ah = asian_bars["high"].max()
    al = asian_bars["low"].min()
    ar_pips = (ah - al) / pip_size
    return ar_pips


def calibrate_pair(asset_key, csv_path, pip_size):
    """Run atomic structure calibration for one pair."""
    print(f"\n{'='*60}")
    print(f"  CALIBRATING: {asset_key}")
    print(f"  CSV: {csv_path.name} | pip_size: {pip_size}")
    print(f"{'='*60}")

    df = pd.read_csv(csv_path, parse_dates=["time"])
    df = df.sort_values("time").reset_index(drop=True)
    df["hour"] = df["time"].dt.hour
    df["date"] = df["time"].dt.date

    # â”€â”€â”€ Daily AR calculation â”€â”€â”€
    daily_ar = []
    for date, day_df in df.groupby("date"):
        ar = calc_daily_asian_range(day_df, pip_size)
        if ar is not None:
            daily_ar.append({"date": date, "ar_pips": ar, "n_bars": len(day_df)})

    ddf = pd.DataFrame(daily_ar)
    if len(ddf) == 0:
        print(f"  WARNING: No valid Asian Range days found!")
        return None

    # â”€â”€â”€ AR Statistics â”€â”€â”€
    ar_mean = ddf["ar_pips"].mean()
    ar_std = ddf["ar_pips"].std()
    ar_min = ddf["ar_pips"].min()
    ar_max = ddf["ar_pips"].max()
    ar_p50 = ddf["ar_pips"].median()
    ar_p75 = ddf["ar_pips"].quantile(0.75)
    ar_p90 = ddf["ar_pips"].quantile(0.90)
    ar_p95 = ddf["ar_pips"].quantile(0.95)

    print(f"  Days analyzed: {len(ddf)}")
    print(f"  AR mean: {ar_mean:.1f}p | std: {ar_std:.1f}p")
    print(f"  AR p50: {ar_p50:.1f}p | p75: {ar_p75:.1f}p | p90: {ar_p90:.1f}p | p95: {ar_p95:.1f}p")
    print(f"  AR range: {ar_min:.1f}p â€” {ar_max:.1f}p")

    # â”€â”€â”€ Tier distribution using REFERENCE config (T1â‰¤20, T2â‰¤30, T3â‰¤45) â”€â”€â”€
    ref_config = {"T1": {"ar_max": 20.0}, "T2": {"ar_max": 30.0}, "T3": {"ar_max": 45.0}}

    def simple_tier(ar):
        if ar <= 20: return "T1"
        if ar <= 30: return "T2"
        if ar <= 45: return "T3"
        return "NO_GO"

    ddf["tier"] = ddf["ar_pips"].apply(simple_tier)
    tier_dist = ddf["tier"].value_counts().to_dict()
    print(f"  Tier dist (ref): {tier_dist}")

    # â”€â”€â”€ RECOMMENDED TIER CONFIG â”€â”€â”€
    # Strategy: Set T1 ar_max at p50, T2 at p75, T3 at p90
    # AU = ar_max * k_factor (0.48-0.50)
    # Trigger = AU * 1.2
    k_factor = 0.48

    rec_t1_ar = round(ar_p50 * 0.9, 1)  # Slightly below p50 for clean T1 capture
    rec_t2_ar = round(ar_p75 * 0.9, 1)  # At p75
    rec_t3_ar = round(ar_p90 * 0.95, 1)  # At p90

    # Ensure minimums
    rec_t1_ar = max(rec_t1_ar, 10.0)
    rec_t2_ar = max(rec_t2_ar, rec_t1_ar + 5.0)
    rec_t3_ar = max(rec_t3_ar, rec_t2_ar + 8.0)

    rec_t1_au = round(rec_t1_ar * k_factor, 1)
    rec_t2_au = round(rec_t2_ar * k_factor, 1)
    rec_t3_au = round(rec_t3_ar * k_factor, 1)

    rec_t1_trigger = round(rec_t1_au * 1.2, 1)
    rec_t2_trigger = round(rec_t2_au * 1.2, 1)
    rec_t3_trigger = round(rec_t3_au * 1.2, 1)

    print(f"\n  â”€â”€â”€ RECOMMENDED CONFIG â”€â”€â”€")
    print(f"  T1: ar_max={rec_t1_ar}p | au={rec_t1_au}p | trigger={rec_t1_trigger}p")
    print(f"  T2: ar_max={rec_t2_ar}p | au={rec_t2_au}p | trigger={rec_t2_trigger}p")
    print(f"  T3: ar_max={rec_t3_ar}p | au={rec_t3_au}p | trigger={rec_t3_trigger}p")
    print(f"  NO_GO: >{rec_t3_ar}p")

    # â”€â”€â”€ Tier distribution with RECOMMENDED config â”€â”€â”€
    def rec_tier(ar):
        if ar <= rec_t1_ar: return "T1"
        if ar <= rec_t2_ar: return "T2"
        if ar <= rec_t3_ar: return "T3"
        return "NO_GO"

    ddf["rec_tier"] = ddf["ar_pips"].apply(rec_tier)
    rec_tier_dist = ddf["rec_tier"].value_counts().to_dict()
    print(f"  Tier dist (rec): {rec_tier_dist}")

    # â”€â”€â”€ Impulse analysis â”€â”€â”€
    # Look at max impulse bar range (high-low) in the 3 bars after Asian session
    impulse_stats = []
    for date, day_df in df.groupby("date"):
        # Post-Asian bars (03:00-05:00 UTC)
        post_asian = day_df[(day_df["hour"] >= 3) & (day_df["hour"] < 5)]
        if len(post_asian) >= 3:
            for _, bar in post_asian.head(3).iterrows():
                impulse_stats.append((bar["high"] - bar["low"]) / pip_size)

    if impulse_stats:
        imp_mean = np.mean(impulse_stats)
        imp_p50 = np.median(impulse_stats)
        imp_p90 = np.percentile(impulse_stats, 90)
        print(f"\n  Impulse (post-Asian 3 bars):")
        print(f"  Mean: {imp_mean:.1f}p | p50: {imp_p50:.1f}p | p90: {imp_p90:.1f}p")
    else:
        imp_mean = imp_p50 = imp_p90 = 0
        print(f"\n  Impulse: no data")

    # â”€â”€â”€ Build output â”€â”€â”€
    result = {
        "symbol": asset_key,
        "pip_size": pip_size,
        "n_days": len(ddf),
        "ar_stats": {
            "mean": round(ar_mean, 1),
            "std": round(ar_std, 1),
            "min": round(ar_min, 1),
            "max": round(ar_max, 1),
            "p50": round(ar_p50, 1),
            "p75": round(ar_p75, 1),
            "p90": round(ar_p90, 1),
            "p95": round(ar_p95, 1),
        },
        "tier_dist_reference": tier_dist,
        "recommended_config": {
            "k_factor": k_factor,
            "T1": {"ar_max": rec_t1_ar, "au": rec_t1_au, "trigger": rec_t1_trigger},
            "T2": {"ar_max": rec_t2_ar, "au": rec_t2_au, "trigger": rec_t2_trigger},
            "T3": {"ar_max": rec_t3_ar, "au": rec_t3_au, "trigger": rec_t3_trigger},
        },
        "tier_dist_recommended": rec_tier_dist,
        "impulse_stats": {
            "mean": round(imp_mean, 1),
            "p50": round(imp_p50, 1),
            "p90": round(imp_p90, 1),
        },
    }

    # Save individual JSON
    out_path = REPORTS_DIR / f"{asset_key}_atomic_structure.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2, default=str)
    print(f"\n  Saved: {out_path}")

    return result


def main():
    print(f"\n{'#'*60}")
    print(f"  CEREBUS FX ATOMIC STRUCTURE CALIBRATION")
    print(f"  Pairs: {len(NEW_PAIRS)}")
    print(f"{'#'*60}")

    all_results = {}
    missing = []

    for pair in NEW_PAIRS:
        csv_path = find_csv(pair)
        if csv_path is None:
            print(f"\n  MISSING DATA: {pair}")
            missing.append(pair)
            continue

        pip_size = 0.01 if pair in JPY_PAIRS else 0.0001
        result = calibrate_pair(pair, csv_path, pip_size)
        if result:
            all_results[pair] = result

    # â”€â”€â”€ Summary Report â”€â”€â”€
    summary_path = REPORTS_DIR / "fx_calibration_summary.json"
    with open(summary_path, "w") as f:
        json.dump({
            "calibrated": all_results,
            "missing": missing,
        }, f, indent=2, default=str)

    # â”€â”€â”€ Markdown Summary â”€â”€â”€
    md_path = REPORTS_DIR / "fx_calibration_summary.md"
    with open(md_path, "w") as f:
        f.write("# CEREBUS FX Atomic Structure Calibration\n\n")
        f.write(f"**Date:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"**Pairs calibrated:** {len(all_results)}/{len(NEW_PAIRS)}\n\n")

        f.write("---\n\n")
        f.write("## Recommended Tier Configs\n\n")
        f.write("| Pair | Pip | Days | AR mean | AR p50 | AR p90 | T1 ar_max | T2 ar_max | T3 ar_max | T1 AU | T2 AU | T3 AU |\n")
        f.write("|------|-----|------|---------|--------|--------|-----------|-----------|-----------|-------|-------|-------|\n")

        for pair in NEW_PAIRS:
            if pair in all_results:
                r = all_results[pair]
                cfg = r["recommended_config"]
                ar = r["ar_stats"]
                f.write(f"| {pair} | {r['pip_size']} | {r['n_days']} | {ar['mean']}p | {ar['p50']}p | {ar['p90']}p | {cfg['T1']['ar_max']}p | {cfg['T2']['ar_max']}p | {cfg['T3']['ar_max']}p | {cfg['T1']['au']}p | {cfg['T2']['au']}p | {cfg['T3']['au']}p |\n")

        f.write("\n---\n\n")
        f.write("## Tier Distribution (Recommended Config)\n\n")
        f.write("| Pair | T1 | T2 | T3 | NO_GO | Total |\n")
        f.write("|------|----|----|----|----|-------|\n")
        for pair in NEW_PAIRS:
            if pair in all_results:
                r = all_results[pair]
                td = r["tier_dist_recommended"]
                total = sum(td.values())
                t1 = td.get("T1", 0)
                t2 = td.get("T2", 0)
                t3 = td.get("T3", 0)
                nogo = td.get("NO_GO", 0)
                f.write(f"| {pair} | {t1} | {t2} | {t3} | {nogo} | {total} |\n")

        if missing:
            f.write(f"\n---\n\n")
            f.write("## Missing Data\n\n")
            for m in missing:
                f.write(f"- {m}\n")

    print(f"\n{'#'*60}")
    print(f"  CALIBRATION COMPLETE")
    print(f"  Calibrated: {len(all_results)}/{len(NEW_PAIRS)}")
    print(f"  Missing: {missing}")
    print(f"  Summary: {summary_path}")
    print(f"  Report: {md_path}")
    print(f"{'#'*60}\n")


if __name__ == "__main__":
    main()
