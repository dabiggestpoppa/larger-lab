#!/usr/bin/env python3
"""
ALT-DATA-1.1 -- Benchmark Return Truth Seal & V2 Feature Build
"""
import hashlib, json, math, sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]  # alt_rotation/
DATA1 = ROOT / "data_1"
OUT = ROOT / "data_1_1"

WINDOWS = [1, 3, 7, 14, 30, 60, 90]
BTC_ID = 1
ETH_ID = 1027
COVERAGE_FLOOR = 0.8
MIN_OBS_BETA = 30

def write_parquet(df, name):
    p = OUT / name
    df.to_parquet(p, index=False)
    return p

print("=" * 70)
print("ALT-DATA-1.1 -- Benchmark Return Truth Seal")
print("=" * 70)

print("\nLoading V1 data...")
uni = pd.read_parquet(DATA1 / "ALT_DATA_1_PIT_UNIVERSE.parquet")
feat_v1 = pd.read_parquet(DATA1 / "ALT_DATA_1_ASSET_MULTISCALE_FEATURES.parquet")
terrain_v1 = pd.read_parquet(DATA1 / "ALT_DATA_1_MARKET_TERRAIN_FEATURES.parquet")
print(f"  PIT universe: {len(uni)} rows, {uni['historical_date'].nunique()} dates")
print(f"  V1 features: {len(feat_v1)} rows, {feat_v1.shape[1]} cols")

# Extract BTC/ETH returns from V1 features (already calendar-day correct)
btc_feat = feat_v1[feat_v1["cmc_id"] == BTC_ID].set_index("historical_date")
eth_feat = feat_v1[feat_v1["cmc_id"] == ETH_ID].set_index("historical_date")
btc_returns = {w: btc_feat[f"return_{w}d"] for w in WINDOWS}
eth_returns = {w: eth_feat[f"return_{w}d"] for w in WINDOWS}

# Pre-repair identity test
print("\nPre-repair identity test (should show large errors):")
for w in WINDOWS:
    vals = btc_feat[f"relative_return_vs_BTC_{w}d"].dropna()
    print(f"  BTC self-relative {w}D: max_abs={np.abs(vals).max():.6e}")

v1_hash = "12655965882ffe6ab1083e96a65dd06c299b6425c39660fa733e00506fa15189"

# Rebuild features with corrected benchmark returns
print("\nRebuilding V2 asset features with corrected benchmark returns...")
feat = feat_v1.copy()
max_abs_diff_btc = 0.0
max_abs_diff_eth = 0.0
changed_rows = 0

for w in WINDOWS:
    ret_col = f"return_{w}d"
    btc_r = btc_returns[w].reindex(feat["historical_date"].values).values
    eth_r = eth_returns[w].reindex(feat["historical_date"].values).values
    asset_r = feat[ret_col].values
    new_rel_btc = asset_r - btc_r
    new_rel_eth = asset_r - eth_r
    old_rel_btc = feat[f"relative_return_vs_BTC_{w}d"].values
    old_rel_eth = feat[f"relative_return_vs_ETH_{w}d"].values
    mask_btc = ~np.isnan(old_rel_btc) & ~np.isnan(new_rel_btc)
    mask_eth = ~np.isnan(old_rel_eth) & ~np.isnan(new_rel_eth)
    if mask_btc.any():
        diff_btc = np.abs(old_rel_btc[mask_btc] - new_rel_btc[mask_btc])
        max_abs_diff_btc = max(max_abs_diff_btc, float(np.max(diff_btc)))
        changed_rows += int(np.sum(diff_btc > 1e-15))
    if mask_eth.any():
        diff_eth = np.abs(old_rel_eth[mask_eth] - new_rel_eth[mask_eth])
        max_abs_diff_eth = max(max_abs_diff_eth, float(np.max(diff_eth)))
    feat[f"relative_return_vs_BTC_{w}d"] = new_rel_btc
    feat[f"relative_return_vs_ETH_{w}d"] = new_rel_eth

print(f"  Max abs diff relative_return_vs_BTC: {max_abs_diff_btc:.6e}")
print(f"  Max abs diff relative_return_vs_ETH: {max_abs_diff_eth:.6e}")
print(f"  Rows with changes: {changed_rows}")

# Rebuild rolling beta and residuals
print("\nRebuilding rolling beta and residual features...")
# Merge price from universe
prices = uni[["historical_date", "cmc_id", "price_usd"]]
feat = feat.merge(prices, on=["historical_date", "cmc_id"], how="left")
lb = np.log(feat["price_usd"])
lr = lb - lb.groupby(feat["cmc_id"]).shift(1)

btc_prices = btc_feat[["price_usd"]].copy() if "price_usd" in btc_feat.columns else uni[uni["cmc_id"]==BTC_ID][["historical_date","price_usd"]].set_index("historical_date")
eth_prices = eth_feat[["price_usd"]].copy() if "price_usd" in eth_feat.columns else uni[uni["cmc_id"]==ETH_ID][["historical_date","price_usd"]].set_index("historical_date")
btc_daily_lr = np.log(btc_prices["price_usd"]).diff()
eth_daily_lr = np.log(eth_prices["price_usd"]).diff()

for w in [30, 60, 90]:
    print(f"  Computing rolling beta {w}D...")
    # Build benchmark daily log return aligned to all dates
    btc_bench = btc_daily_lr.reindex(feat["historical_date"].values).values
    eth_bench = eth_daily_lr.reindex(feat["historical_date"].values).values

    tmp = pd.DataFrame({
        "cmc_id": feat["cmc_id"].values,
        "date": feat["historical_date"].values,
        "x": lr.values,
    })
    tmp["b_btc"] = btc_bench
    tmp["b_eth"] = eth_bench
    tmp["xb_btc"] = tmp["x"] * tmp["b_btc"]
    tmp["xb_eth"] = tmp["x"] * tmp["b_eth"]
    tmp["xx"] = tmp["x"] ** 2
    tmp = tmp.set_index("date")

    from pandas import MultiIndex
    key = MultiIndex.from_arrays([feat["cmc_id"].values, feat["historical_date"].values])
    sums_btc = {c: tmp.groupby("cmc_id")[c].rolling(f"{w}D", min_periods=1).sum()
                for c in ("x", "b_btc", "xb_btc", "xx")}
    sums_eth = {c: tmp.groupby("cmc_id")[c].rolling(f"{w}D", min_periods=1).sum()
                for c in ("x", "b_eth", "xb_eth", "xx")}
    n = tmp.groupby("cmc_id")["x"].rolling(f"{w}D", min_periods=1).count()

    nv = n.reindex(key).values
    sx = sums_btc["x"].reindex(key).values
    sxx = sums_btc["xx"].reindex(key).values

    # BTC beta
    sb = sums_btc["b_btc"].reindex(key).values
    sxb = sums_btc["xb_btc"].reindex(key).values
    denom = w * sxx - sx * sx
    safe_denom = np.where(np.abs(denom) > 1e-12, denom, np.nan)
    btc_beta = np.where(np.abs(denom) > 1e-12, (w * sxb - sx * sb) / safe_denom, np.nan)
    need = max(MIN_OBS_BETA, int(math.ceil(COVERAGE_FLOOR * w)))
    btc_beta[nv < need] = np.nan
    feat[f"rolling_beta_vs_BTC_{w}d"] = btc_beta

    # ETH beta
    sb_e = sums_eth["b_eth"].reindex(key).values
    sxb_e = sums_eth["xb_eth"].reindex(key).values
    eth_beta = np.where(np.abs(denom) > 1e-12, (w * sxb_e - sx * sb_e) / safe_denom, np.nan)
    eth_beta[nv < need] = np.nan
    feat[f"rolling_beta_vs_ETH_{w}d"] = eth_beta

    # Expected + residual
    btc_cum = btc_returns[w].reindex(feat["historical_date"].values).values
    eth_cum = eth_returns[w].reindex(feat["historical_date"].values).values
    actual = feat[f"return_{w}d"].values
    feat[f"expected_return_given_BTC_{w}d"] = btc_beta * btc_cum
    feat[f"expected_return_given_ETH_{w}d"] = eth_beta * eth_cum
    feat[f"residual_return_vs_BTC_{w}d"] = actual - btc_beta * btc_cum
    feat[f"residual_return_vs_ETH_{w}d"] = actual - eth_beta * eth_cum

# Post-repair identity test
print("\nPost-repair identity test (must be 0):")
btc_post = feat[feat["cmc_id"] == BTC_ID].set_index("historical_date")
eth_post = feat[feat["cmc_id"] == ETH_ID].set_index("historical_date")
identity_pass = True
for w in WINDOWS:
    max_abs = float(np.abs(btc_post[f"relative_return_vs_BTC_{w}d"].dropna()).max())
    status = "PASS" if max_abs < 1e-12 else "FAIL"
    if status == "FAIL": identity_pass = False
    print(f"  BTC self-relative {w}D: max_abs={max_abs:.2e} [{status}]")
for w in WINDOWS:
    max_abs = float(np.abs(eth_post[f"relative_return_vs_ETH_{w}d"].dropna()).max())
    status = "PASS" if max_abs < 1e-12 else "FAIL"
    if status == "FAIL": identity_pass = False
    print(f"  ETH self-relative {w}D: max_abs={max_abs:.2e} [{status}]")
if not identity_pass:
    print("\n*** FAIL_BENCHMARK_RETURN_TRUTH_SEAL ***")
    sys.exit(1)
print("\n  Identity tests PASSED.")

# Rebuild terrain
print("\nRebuilding terrain with corrected benchmark returns...")
terrain = terrain_v1.copy()
for w in WINDOWS:
    terrain[f"btc_return_{w}d"] = terrain["historical_date"].map(btc_returns[w]).values
    terrain[f"eth_return_{w}d"] = terrain["historical_date"].map(eth_returns[w]).values
    terrain[f"eth_btc_relative_return_{w}d"] = terrain[f"eth_return_{w}d"] - terrain[f"btc_return_{w}d"]

# Write V2 artifacts
print("\nWriting V2 artifacts...")
write_parquet(feat, "ALT_DATA_1_1_ASSET_MULTISCALE_FEATURES_V2.parquet")
write_parquet(terrain, "ALT_DATA_1_1_MARKET_TERRAIN_V2.parquet")

import shutil
for name in ["ALT_DATA_1_PIT_UNIVERSE.parquet", "ALT_DATA_1_IDENTITY_MAP.parquet",
             "ALT_DATA_1_PERP_ELIGIBILITY.parquet", "ALT_DATA_1_RANK_BAND_FEATURES.parquet",
             "ALT_DATA_1_SECTOR_FEATURES.parquet", "ALT_DATA_1_SECTOR_MEMBERSHIP.parquet",
             "ALT_DATA_1_SURVIVORSHIP.parquet"]:
    src = DATA1 / name
    if src.exists():
        dst = OUT / name.replace("ALT_DATA_1_", "ALT_DATA_1_1_")
        if not dst.exists():
            shutil.copy2(src, dst)
            print(f"  Copied {name}")

# V2 hash
v2_columns = sorted(feat.columns.tolist())
v2_def = json.dumps({"version": "2.0.0", "columns": v2_columns}, sort_keys=True)
v2_hash = hashlib.sha256(v2_def.encode()).hexdigest()
print(f"  V2 feature hash: {v2_hash}")

# Feature change log
print("\nWriting feature change log...")
change_log = pd.DataFrame([{
    "feature": "relative_return_vs_BTC_*d",
    "v1_hash": v1_hash,
    "v2_hash": v2_hash,
    "changed_rows": changed_rows,
    "max_abs_diff": max_abs_diff_btc,
    "reason": "Calendar-day benchmark return alignment",
}, {
    "feature": "relative_return_vs_ETH_*d",
    "v1_hash": v1_hash,
    "v2_hash": v2_hash,
    "changed_rows": changed_rows,
    "max_abs_diff": max_abs_diff_eth,
    "reason": "Calendar-day benchmark return alignment",
}])
change_log.to_csv(OUT / "ALT_DATA_1_1_FEATURE_CHANGE_LOG.csv", index=False)

# Summary
summary = {
    "v1_feature_hash": v1_hash,
    "v2_feature_hash": v2_hash,
    "max_abs_diff_btc": max_abs_diff_btc,
    "max_abs_diff_eth": max_abs_diff_eth,
    "changed_rows": changed_rows,
    "identity_test_pass": identity_pass,
}
with open(OUT / "benchmark_repair_summary.json", "w") as f:
    json.dump(summary, f, indent=2)

print(f"\n{'=' * 70}")
print(f"BENCHMARK REPAIR COMPLETE")
print(f"  V2 feature hash: {v2_hash}")
print(f"  Max abs diff BTC: {max_abs_diff_btc:.6e}")
print(f"  Max abs diff ETH: {max_abs_diff_eth:.6e}")
print(f"  Changed rows: {changed_rows}")
print(f"  Identity test: {'PASS' if identity_pass else 'FAIL'}")
print(f"{'=' * 70}")
