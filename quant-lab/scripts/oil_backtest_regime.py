"""
CEREBUS Backtest — Oil (LCOUSD + OILUSD) with Regime-Aware Tier Config
Compares: (A) static default tiers vs (B) regime-fitted tiers
"""
import sys
sys.path.insert(0, "quant-lab")

import pandas as pd
import numpy as np
import json
from datetime import datetime, timezone
from engines.symmetry_trap import SymmetryTrapEngine, Bar, TradeDirection, classify_tier

# ─── Regime-specific tier configs (from atomic structure analysis) ───
REGIME_TIERS = {
    "LCOUSD": {
        "PRE_WAR":      {"T1": {"ar_max": 31.2, "au": 15.6, "trigger": 18.7}, "T2": {"ar_max": 64.5, "au": 25.8, "trigger": 31.0}, "T3": {"ar_max": 96.7, "au": 31.9, "trigger": 38.3}},
        "WAR_ONSET":    {"T1": {"ar_max": 40.8, "au": 20.4, "trigger": 24.5}, "T2": {"ar_max": 69.4, "au": 27.8, "trigger": 33.4}, "T3": {"ar_max": 104.2, "au": 34.4, "trigger": 41.3}},
        "WAR_SPIKE":    {"T1": {"ar_max": 28.8, "au": 14.4, "trigger": 17.3}, "T2": {"ar_max": 43.5, "au": 17.4, "trigger": 20.9}, "T3": {"ar_max": 65.3, "au": 21.5, "trigger": 25.8}},
        "NORMALIZATION":{"T1": {"ar_max": 34.4, "au": 17.2, "trigger": 20.6}, "T2": {"ar_max": 63.7, "au": 25.5, "trigger": 30.6}, "T3": {"ar_max": 95.5, "au": 31.5, "trigger": 37.8}},
        "CURRENT":      {"T1": {"ar_max": 31.2, "au": 15.6, "trigger": 18.7}, "T2": {"ar_max": 64.5, "au": 25.8, "trigger": 31.0}, "T3": {"ar_max": 96.7, "au": 31.9, "trigger": 38.3}},
    },
    "OILUSD": {
        "PRE_WAR":      {"T1": {"ar_max": 16.0, "au": 8.0, "trigger": 9.6}, "T2": {"ar_max": 39.9, "au": 16.0, "trigger": 19.2}, "T3": {"ar_max": 59.9, "au": 19.8, "trigger": 23.8}},
        "WAR_ONSET":    {"T1": {"ar_max": 18.4, "au": 9.2, "trigger": 11.0}, "T2": {"ar_max": 45.5, "au": 18.2, "trigger": 21.8}, "T3": {"ar_max": 68.3, "au": 22.5, "trigger": 27.0}},
        "WAR_SPIKE":    {"T1": {"ar_max": 14.4, "au": 7.2, "trigger": 8.6}, "T2": {"ar_max": 29.6, "au": 11.8, "trigger": 14.2}, "T3": {"ar_max": 44.4, "au": 14.7, "trigger": 17.6}},
        "NORMALIZATION":{"T1": {"ar_max": 16.0, "au": 8.0, "trigger": 9.6}, "T2": {"ar_max": 38.4, "au": 15.4, "trigger": 18.5}, "T3": {"ar_max": 57.6, "au": 19.0, "trigger": 22.8}},
        "CURRENT":      {"T1": {"ar_max": 21.6, "au": 10.8, "trigger": 13.0}, "T2": {"ar_max": 101.7, "au": 40.7, "trigger": 48.8}, "T3": {"ar_max": 152.5, "au": 50.3, "trigger": 60.4}},
    },
}

REGIME_DATES = {
    "PRE_WAR":       (pd.Timestamp("2023-01-01"), pd.Timestamp("2023-10-06")),
    "WAR_ONSET":     (pd.Timestamp("2023-10-07"), pd.Timestamp("2024-03-31")),
    "WAR_SPIKE":     (pd.Timestamp("2024-04-01"), pd.Timestamp("2024-06-30")),
    "NORMALIZATION": (pd.Timestamp("2024-07-01"), pd.Timestamp("2025-03-31")),
    "CURRENT":       (pd.Timestamp("2025-04-01"), pd.Timestamp("2026-12-31")),
}

DEFAULT_TIERS = {
    "T1": {"ar_max": 20.0, "au": 10.0, "trigger": 12.0},
    "T2": {"ar_max": 30.0, "au": 12.0, "trigger": 15.0},
    "T3": {"ar_max": 45.0, "au": 15.0, "trigger": 19.0},
}

def get_regime(dt):
    for regime, (start, end) in REGIME_DATES.items():
        if start <= dt <= end:
            return regime
    return "CURRENT"

def backtest_symbol(sym_name, csv_path, pip_size, tier_config, label, use_regime_tiers=False):
    """Run ST backtest with given tier config."""
    df = pd.read_csv(csv_path, parse_dates=["time"])
    df = df.sort_values("time").reset_index(drop=True)
    
    engine = SymmetryTrapEngine(pip_size=pip_size, symbol=sym_name, tier_config=tier_config.copy())
    
    trades = []
    current_regime = None
    
    # Process bars day by day
    df["date"] = df["time"].dt.date
    for date, day_df in df.groupby("date"):
        dt = pd.Timestamp(date)
        regime = get_regime(dt)
        
        # If regime changed and using regime tiers, re-init engine with new config
        if use_regime_tiers and regime != current_regime:
            current_regime = regime
            regime_tiers = REGIME_TIERS.get(sym_name, {}).get(regime, tier_config)
            engine = SymmetryTrapEngine(pip_size=pip_size, symbol=sym_name, tier_config=regime_tiers.copy())
        
        # Calculate Asian Range from 00:00-03:00 UTC bars
        asian_bars = day_df[(day_df["time"].dt.hour >= 0) & (day_df["time"].dt.hour < 3)]
        if len(asian_bars) < 3:
            continue
        ah = asian_bars["high"].max()
        al = asian_bars["low"].min()
        if ah == al:
            continue
        
        engine.initialize_session(ah, al)
        if not engine.session_active:
            continue
        
        # Process remaining bars
        remaining = day_df[day_df["time"].dt.hour >= 3]
        for _, row in remaining.iterrows():
            bar = Bar(
                timestamp=row["time"],
                open=row["open"],
                high=row["high"],
                low=row["low"],
                close=row["close"],
            )
            sig = engine.process_bar(bar)
            if sig and sig.event == "ENTRY":
                trades.append({
                    "date": date,
                    "regime": regime,
                    "tier": engine.tier_name,
                    "direction": sig.direction.name,
                    "entry": sig.entry_price,
                    "sl": sig.sl_price,
                    "tp": sig.tp_price,
                    "loop": sig.loop_count,
                })
    
    # Calculate basic stats
    n_trades = len(trades)
    if n_trades == 0:
        print(f"  [{label}] {sym_name}: 0 trades")
        return {"label": label, "n_trades": 0}
    
    # Per-regime breakdown
    tdf = pd.DataFrame(trades)
    regime_stats = {}
    for regime in tdf["regime"].unique():
        rdf = tdf[tdf["regime"] == regime]
        regime_stats[regime] = len(rdf)
    
    tier_stats = tdf["tier"].value_counts().to_dict()
    
    print(f"  [{label}] {sym_name}: {n_trades} trades | Tiers: {tier_stats} | Per-regime: {regime_stats}")
    return {"label": label, "n_trades": n_trades, "tiers": tier_stats, "regimes": regime_stats}


# ─── RUN BACKTESTS ───
results = {}
for sym_name, csv_path, pip_size in [
    ("LCOUSD", "quant-lab/data/LCOUSDPRO_M5.csv", 0.01),
    ("OILUSD", "quant-lab/data/OILUSDPRO_M5.csv", 0.01),
]:
    print(f"\n{'='*60}")
    print(f"  BACKTEST: {sym_name}")
    print(f"{'='*60}")
    
    # A: Static default tiers
    r_default = backtest_symbol(sym_name, csv_path, pip_size, DEFAULT_TIERS, "STATIC_DEFAULT")
    
    # B: Regime-aware tiers
    r_regime = backtest_symbol(sym_name, csv_path, pip_size, DEFAULT_TIERS, "REGIME_ADAPTIVE", use_regime_tiers=True)
    
    results[sym_name] = {"static": r_default, "regime_adaptive": r_regime}

# Save
with open("quant-lab/reports/oil_backtest_regime_comparison.json", "w") as f:
    json.dump(results, f, indent=2, default=str)

print(f"\nSaved: quant-lab/reports/oil_backtest_regime_comparison.json")
