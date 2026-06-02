"""
CEREBUS Atomic Structure Analysis — LCOUSD & OILUSD (Brent & WTI)
Maps regime changes, tier drift, and structural shifts across war period (March 2024+).
"""
import pandas as pd
import numpy as np
from datetime import datetime, timezone, time as dtime
import json
import os

# ─── CEREBUS Tier Config (from symmetry_trap.py) ───
TIER_CONFIG = {
    "T1": {"ar_max": 20.0, "au": 10.0, "trigger": 12.0},
    "T2": {"ar_max": 30.0, "au": 12.0, "trigger": 15.0},
    "T3": {"ar_max": 45.0, "au": 15.0, "trigger": 19.0},
}

def classify_tier(ar_pips):
    for tn in ("T1", "T2", "T3"):
        if ar_pips <= TIER_CONFIG[tn]["ar_max"]:
            return tn, TIER_CONFIG[tn]["au"], TIER_CONFIG[tn]["trigger"]
    return "NO_GO", 0.0, 0.0

# ─── Asian Range Calculation ───
# Asian session: 00:00-03:00 UTC (19:00-22:00 EST prev day) for oil
# Actually for oil: Asian session is roughly 00:00-03:00 UTC
# Using the same window as FX: midnight to 3AM UTC

def calc_asian_range_daily(day_bars, asian_start=0, asian_end=3):
    """Calculate Asian Range from bars within asian_start to asian_end UTC hours."""
    asian_bars = day_bars[
        (day_bars["hour"] >= asian_start) & (day_bars["hour"] < asian_end)
    ]
    if len(asian_bars) < 3:
        return None, None
    ah = asian_bars["high"].max()
    al = asian_bars["low"].min()
    return ah, al

def analyze_symbol(sym_name, csv_path, pip_size=0.01):
    """Full atomic structure analysis for one oil symbol."""
    print(f"\n{'='*70}")
    print(f"  ATOMIC STRUCTURE: {sym_name}")
    print(f"{'='*70}")
    
    df = pd.read_csv(csv_path, parse_dates=["time"])
    df = df.sort_values("time").reset_index(drop=True)
    df["hour"] = df["time"].dt.hour
    df["date"] = df["time"].dt.date
    
    # ─── DAILY ASIAN RANGE + TIER ───
    daily_stats = []
    for date, day_df in df.groupby("date"):
        ah, al = calc_asian_range_daily(day_df)
        if ah and al:
            ar_pips = (ah - al) / pip_size
            tier, au, trigger = classify_tier(ar_pips)
            daily_stats.append({
                "date": date,
                "asian_high": ah,
                "asian_low": al,
                "ar_pips": ar_pips,
                "tier": tier,
                "au": au,
                "trigger": trigger,
                "day_high": day_df["high"].max(),
                "day_low": day_df["low"].min(),
                "day_range_pips": (day_df["high"].max() - day_df["low"].min()) / pip_size,
                "n_bars": len(day_df),
            })
    
    ddf = pd.DataFrame(daily_stats)
    
    # ─── REGIME DETECTION ───
    # March 2024 = Russia-Ukraine escalation / Middle East tensions
    # Key dates:
    # - Oct 7, 2023: Hamas attack on Israel → Middle East war begins
    # - March 2024: Escalation spikes, oil jumps
    # - Mid 2024: Normalization begins
    # - Late 2024-2025: New normal regime
    
    regime_boundaries = {
        "PRE_WAR": (ddf["date"].min(), pd.Timestamp("2023-10-06").date()),
        "WAR_ONSET": (pd.Timestamp("2023-10-07").date(), pd.Timestamp("2024-03-31").date()),
        "WAR_SPIKE": (pd.Timestamp("2024-04-01").date(), pd.Timestamp("2024-06-30").date()),
        "NORMALIZATION": (pd.Timestamp("2024-07-01").date(), pd.Timestamp("2025-03-31").date()),
        "CURRENT": (pd.Timestamp("2025-04-01").date(), ddf["date"].max()),
    }
    
    # ─── PER-REGIME STATISTICS ───
    regime_results = {}
    for regime, (start, end) in regime_boundaries.items():
        mask = (ddf["date"] >= start) & (ddf["date"] <= end)
        rdf = ddf[mask]
        if len(rdf) == 0:
            continue
        
        tier_dist = rdf["tier"].value_counts().to_dict()
        ar_mean = rdf["ar_pips"].mean()
        ar_std = rdf["ar_pips"].std()
        ar_p50 = rdf["ar_pips"].median()
        ar_p90 = rdf["ar_pips"].quantile(0.90)
        ar_p95 = rdf["ar_pips"].quantile(0.95)
        
        regime_results[regime] = {
            "n_days": len(rdf),
            "ar_mean": round(ar_mean, 1),
            "ar_std": round(ar_std, 1),
            "ar_p50": round(ar_p50, 1),
            "ar_p90": round(ar_p90, 1),
            "ar_p95": round(ar_p95, 1),
            "ar_min": round(rdf["ar_pips"].min(), 1),
            "ar_max": round(rdf["ar_pips"].max(), 1),
            "tier_dist": tier_dist,
            "day_range_mean": round(rdf["day_range_pips"].mean(), 1),
            "day_range_p90": round(rdf["day_range_pips"].quantile(0.90), 1),
        }
        
        print(f"\n  ─── {regime} ({start} → {end}) ───")
        print(f"  Days: {len(rdf)}")
        print(f"  AR (pips):.mean={ar_mean:.1f} | std={ar_std:.1f} | p50={ar_p50:.1f} | p90={ar_p90:.1f} | p95={ar_p95:.1f}")
        print(f"  AR range: {rdf['ar_pips'].min():.1f} — {rdf['ar_pips'].max():.1f}")
        print(f"  Day range: mean={rdf['day_range_pips'].mean():.1f} | p90={rdf['day_range_pips'].quantile(0.90):.1f}")
        print(f"  Tier dist: {tier_dist}")
        
        # Dominant tier
        dom_tier = max(tier_dist, key=tier_dist.get)
        print(f"  Dominant tier: {dom_tier}")
    
    # ─── REGIME SHIFT ANALYSIS ───
    print(f"\n  ─── REGIME SHIFT ANALYSIS ───")
    pre = regime_results.get("PRE_WAR", {})
    current = regime_results.get("CURRENT", {})
    war_onset = regime_results.get("WAR_ONSET", {})
    war_spike = regime_results.get("WAR_SPIKE", {})
    
    if pre and current:
        ar_shift = current["ar_mean"] - pre["ar_mean"]
        print(f"  AR shift (PRE_WAR → CURRENT): {ar_shift:+.1f} pips")
        print(f"    PRE_WAR mean AR: {pre['ar_mean']} | CURRENT mean AR: {current['ar_mean']}")
        tier_shift = set(pre.get("tier_dist", {}).keys()) != set(current.get("tier_dist", {}).keys())
        print(f"  Tier distribution changed: {tier_shift}")
    
    if war_onset and war_spike:
        spike_ar = war_spike["ar_mean"]
        onset_ar = war_onset["ar_mean"]
        print(f"  AR shift (ONSET → SPIKE): {spike_ar - onset_ar:+.1f} pips")
    
    # ─── RECOMMENDED TIER CONFIGS PER REGIME ───
    print(f"\n  ─── RECOMMENDED TIER CONFIG PER REGIME ───")
    for regime, stats in regime_results.items():
        # Fit tier boundaries from AR distribution
        ar_p50 = stats["ar_p50"]
        ar_p90 = stats["ar_p90"]
        # T1: up to p50, T2: up to p90, T3: up to p90*1.5, NO_GO above
        rec_t1_ar = round(ar_p50 * 0.8, 1)
        rec_t2_ar = round(ar_p90 * 0.8, 1)
        rec_t3_ar = round(ar_p90 * 1.2, 1)
        print(f"  {regime}: T1≤{rec_t1_ar}p | T2≤{rec_t2_ar}p | T3≤{rec_t3_ar}p | NO_GO>{rec_t3_ar}p")
        
        # AU and trigger recommendations
        rec_t1_au = round(rec_t1_ar * 0.5, 1)
        rec_t2_au = round(rec_t2_ar * 0.4, 1)
        rec_t3_au = round(rec_t3_ar * 0.33, 1)
        print(f"          AU: T1={rec_t1_au}p | T2={rec_t2_au}p | T3={rec_t3_au}p")
        print(f"          Trigger: T1={round(rec_t1_au*1.2,1)}p | T2={round(rec_t2_au*1.2,1)}p | T3={round(rec_t3_au*1.2,1)}p")
    
    # ─── SAVE RESULTS ───
    output = {
        "symbol": sym_name,
        "pip_size": pip_size,
        "regimes": regime_results,
        "current_regime_ar_mean": current.get("ar_mean"),
        "current_regime_tier_dist": current.get("tier_dist"),
    }
    out_path = f"quant-lab/reports/{sym_name}_atomic_structure.json"
    os.makedirs("quant-lab/reports", exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2, default=str)
    print(f"\n  Saved: {out_path}")
    
    return ddf, regime_results

# ─── RUN BOTH ───
os.makedirs("quant-lab/reports", exist_ok=True)

lco_ddf, lco_regimes = analyze_symbol("LCOUSD", "quant-lab/data/LCOUSDPRO_M5.csv", pip_size=0.01)
oil_ddf, oil_regimes = analyze_symbol("OILUSD", "quant-lab/data/OILUSDPRO_M5.csv", pip_size=0.01)

# ─── CROSS-ASSET COMPARISON ───
print(f"\n{'='*70}")
print(f"  CROSS-ASSET: BRENT vs WTI REGIME COMPARISON")
print(f"{'='*70}")
for regime in set(lco_regimes.keys()) & set(oil_regimes.keys()):
    lco = lco_regimes[regime]
    oil = oil_regimes[regime]
    print(f"\n  {regime}:")
    print(f"    Brent AR mean: {lco['ar_mean']}p | WTI AR mean: {oil['ar_mean']}p | Δ = {lco['ar_mean']-oil['ar_mean']:+.1f}p")
    print(f"    Brent p90: {lco['ar_p90']}p | WTI p90: {oil['ar_p90']}p")
    print(f"    Brent tiers: {lco['tier_dist']}")
    print(f"    WTI tiers:   {oil['tier_dist']}")
