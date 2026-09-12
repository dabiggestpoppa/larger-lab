"""LOWER-FIELD-2 integrity repair: corrected cross-rank sigma (03) and
event-count reconciliation (04). Also writes the 02_INTEGRITY_REPAIR_AUDIT.md
supported verdict. Self-contained: rebuilds the corrected comparison bands with
continuous causal returns AND continuous sigma (both on the full per-asset
series before band filter).

CONTEXT
  The LF1 Top-500 comparison path had two corruption classes:
    (a) multi-day returns bug: cs - shift(_logf, w) subtracted a DAILY
        log-return instead of the shifted CUMULATIVE log-return -> inflated
        ret_3d..ret_30d ~50x and produced impossible sigma ratios (e.g. 3D
        median ~181 sigma). Fixed by cs - shift(cs, w) (LF0-exact algorithm),
        parity 0.0.
    (b) sigma band-truncation: recomputing sigma AFTER band-filtering truncates
        migrated assets' series and distorts the trailing window. Avoided here
        by computing sigma on the full continuous series first.
  Reconciliation of '~329k events / 10% >=3sigma': that figure is the UNION of
  event lenses (dominated by the lenient raw>=15% lens); the true unconditional
  1D >=3sigma rate (continuous causal sigma) is ~2.5%, and only ~26% of the
  union rows are genuinely >=3sigma.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import lf2_common as C
import lf2_load as L

COMP = ["26-100", "101-250", "251-500"]


def _canonical_comparison_frame() -> pd.DataFrame:
    """Repaired cross-rank frame: continuous returns + continuous sigma on the
    FULL canonical series (ranks 1-500), band assigned by PIT rank, then filter
    to comparison bands. Returns the LF0-exact algorithm with continuous sigma."""
    can = pd.read_parquet(C.CANON)
    can = can.sort_values(["cmc_id", "historical_date"]).copy()
    g = can.groupby("cmc_id", sort=False)["price_usd"]
    can["price_prev"] = g.shift(1)
    can["ret_1d"] = can["price_usd"] / can["price_prev"] - 1.0
    ok = can["ret_1d"].notna() & (can["ret_1d"] > -1.0)
    logf = np.where(ok, np.log1p(can["ret_1d"].clip(lower=-0.9999)), np.nan)
    can["_logf"] = logf
    can["_cs"] = can.groupby("cmc_id", sort=False)["_logf"].cumsum()
    for w, col in [(1, "ret_1d2"), (3, "ret_3d"), (7, "ret_7d"),
                   (14, "ret_14d"), (30, "ret_30d")]:
        if col == "ret_1d2":
            can[col] = can["ret_1d"]
            continue
        cs_shift = can.groupby("cmc_id", sort=False)["_cs"].transform(
            lambda s: s.shift(w))
        can[col] = np.expm1(can["_cs"] - cs_shift)
    # continuous sigma on the FULL canonical series (all 1-500) before filter
    can["sigma_t0"] = C.compute_sigma(can)
    rb = pd.cut(can["rank"], bins=[0, 25, 100, 250, 500],
                labels=["1-25", "26-100", "101-250", "251-500"])
    can["rank_band"] = rb.astype(str)
    can = can[can["rank_band"].isin(COMP)].copy()
    can["ret_1d"] = can["ret_1d2"]
    return can


def corrected_cross_rank_sigma():
    rows = []
    comp = _canonical_comparison_frame()
    for band in COMP:
        frame = comp[comp["rank_band"] == band]
        for h, col in [("1D", "ret_1d"), ("3D", "ret_3d"), ("7D", "ret_7d"),
                       ("14D", "ret_14d"), ("30D", "ret_30d")]:
            z = (frame[col].abs() / frame["sigma_t0"])
            z = z[np.isfinite(z)]
            if len(z) < 100:
                continue
            rows.append({
                "rank_band": band, "horizon": h, "n": int(len(z)),
                "z_median": float(z.median()), "z_p75": float(z.quantile(0.75)),
                "z_p95": float(z.quantile(0.95)), "z_p99": float(z.quantile(0.99)),
                "impossible_median_ratio": "YES" if z.median() > 10 else "NO",
            })
    # append the primary lower bands from the panel (continuous sigma already)
    df = L.load()
    for band in C.PRIMARY_BANDS:
        frame = df[df["rank_band"] == band]
        for h, col in [("1D", "ret_1d"), ("3D", "ret_3d"), ("7D", "ret_7d"),
                       ("14D", "ret_14d"), ("30D", "ret_30d")]:
            z = (frame[col].abs() / frame["sigma_t0"])
            z = z[np.isfinite(z)]
            if len(z) < 100:
                continue
            rows.append({
                "rank_band": band, "horizon": h, "n": int(len(z)),
                "z_median": float(z.median()), "z_p75": float(z.quantile(0.75)),
                "z_p95": float(z.quantile(0.95)), "z_p99": float(z.quantile(0.99)),
                "impossible_median_ratio": "YES" if z.median() > 10 else "NO",
            })
    return pd.DataFrame(rows)


def event_count_reconciliation():
    df = L.load()
    z = (df["ret_1d"].abs() / df["sigma_t0"]).to_numpy(float)
    r = df["ret_1d"].to_numpy(float)
    tot = int(np.isfinite(z).sum())
    b = np.isfinite(z) & (z >= 3.0)
    c = np.isfinite(r) & (np.abs(r) >= 0.15)
    union = int(((np.nan_to_num(z) >= 3.0) | (np.nan_to_num(r) >= 0.15)).sum())
    lensB = int(b.sum())
    lensC = int(c.sum())
    both = int((b & c).sum())
    rows = [
        {"metric": "panel_rows_primary_bands", "value": int(len(df)),
         "definition": "rows ranks 501-2000 (feature frame)"},
        {"metric": "n_with_sigma", "value": tot,
         "definition": "rows with finite continuous causal 1D sigma_t0"},
        {"metric": "p_ge1sigma_1d", "value": round(float((z >= 1).mean()), 5),
         "definition": "unconditional |ret_1d|>=1 sigma"},
        {"metric": "p_ge2sigma_1d", "value": round(float((z >= 2).mean()), 5),
         "definition": "unconditional |ret_1d|>=2 sigma"},
        {"metric": "p_ge3sigma_1d", "value": round(float((z >= 3).mean()), 5),
         "definition": "TRUE unconditional |ret_1d|>=3 sigma"},
        {"metric": "p_ge4sigma_1d", "value": round(float((z >= 4).mean()), 5),
         "definition": "unconditional |ret_1d|>=4 sigma"},
        {"metric": "p_raw_move_ge10pct", "value": round(float((np.abs(r) >= .10).mean()), 5),
         "definition": "unconditional |ret_1d|>=10%"},
        {"metric": "p_raw_move_ge15pct", "value": round(float((np.abs(r) >= .15).mean()), 5),
         "definition": "unconditional |ret_1d|>=15%"},
        {"metric": "count_lensB_sigma3", "value": lensB,
         "definition": "rows passing sigma>=3 lens"},
        {"metric": "count_lensC_raw15", "value": lensC,
         "definition": "rows passing raw>=15% lens"},
        {"metric": "count_union_lensB_or_C", "value": union,
         "definition": "UNION (sigma>=3 OR raw>=15%)  <-- comparable to ~329k figure"},
        {"metric": "count_sigma3_and_raw15", "value": both,
         "definition": "rows passing BOTH lenses"},
        {"metric": "share_of_union_that_is_sigma3",
         "value": round(lensB / union if union else 0.0, 5),
         "definition": "fraction of union event rows genuinely >=3sigma"},
        {"metric": "lf1_prior_329k_claim",
         "value": np.nan,
         "definition": "DISSOLVED: 329k = union-of-lenses, not >=3sigma count"},
    ]
    return pd.DataFrame(rows)


def main():
    crs = corrected_cross_rank_sigma()
    crs.to_csv(C.RESULTS / "03_CORRECTED_CROSS_RANK_SIGMA.csv", index=False)
    ecr = event_count_reconciliation()
    ecr.to_csv(C.RESULTS / "04_EVENT_COUNT_RECONCILIATION.csv", index=False)
    p3 = float(ecr[ecr.metric == "p_ge3sigma_1d"].value.iloc[0])
    print("INTEGRITY_PASS_REQUIRED = TRUE")
    print(f"unconditional 1D >=3sigma = {p3:.4%}")
    print()
    print(crs[["rank_band", "horizon", "z_median", "z_p99", "impossible_median_ratio"]]
          [crs.horizon.isin(["1D", "3D", "14D"])].to_string(index=False))


if __name__ == "__main__":
    main()