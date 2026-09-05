#!/usr/bin/env python3
"""LF — Phase B (extreme events), C (rank elasticity), D (response surface),
I (up/down asymmetry).

All thresholds follow 02_PREREGISTRATION.md (frozen). Results written to:
  EVENTS/05_EXTREME_EVENT_CATALOG.parquet
  RESULTS/06_RANK_ELASTICITY.csv
  RESULTS/07_POS_NEG_ASYMMETRY.csv
  RESULTS/08_RESPONSE_SURFACE.parquet
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
PANEL = ROOT / "RESULTS" / "lower_field_panel.parquet"
CR = Path(__file__).resolve().parent.parent.parent.parent / "alt_rotation"
CANON_UNIVERSE = CR / "data_1_1" / "ALT_DATA_1_1_PIT_UNIVERSE.parquet"

BANDS = ["1-25", "26-100", "101-250", "251-500", "501-750", "751-1000",
         "1001-1500", "1501-2000"]
FAMILIES = {0.01: "P1", 0.025: "P2.5", 0.05: "P5"}
IMPULSE_ORDER = ["POSITIVE_MARKET", "NEGATIVE_MARKET", "CALM", "ALL"]
MIN_OBS_ASSET = 120
MIN_CELL_DAYS = 120
BOOT_N = 500
BOOT_BLOCK = 20
SEED = 20260826

CANON_BANDS = {"1-25", "26-100", "101-250", "251-500"}


def load_panels():
    lf = pd.read_parquet(PANEL)
    lf = lf.replace([np.inf, -np.inf], np.nan)
    can = pd.read_parquet(CANON_UNIVERSE,
                          columns=["historical_date", "cmc_id", "rank",
                                   "price_usd", "is_stablecoin"])
    can["rank_band"] = can["rank"].apply(
        lambda r: next((f"{lo}-{hi}" for lo, hi in
                        [(1, 25), (26, 100), (101, 250), (251, 500)]
                        if lo <= r <= hi), "OUT"))
    can = can[can["rank_band"].isin(CANON_BANDS)].copy()
    can["cmc_id"] = can["cmc_id"].astype(int)
    can = can.sort_values(["cmc_id", "historical_date"])
    g = can.groupby("cmc_id", sort=False)
    can["ret_1d"] = can["price_usd"] / g["price_usd"].shift(1) - 1.0
    can["ret_1d"] = can["ret_1d"].replace([np.inf, -np.inf], np.nan)
    # global context from canonical total mcap
    tot = pd.read_parquet(CANON_UNIVERSE,
                          columns=["historical_date", "total_mcap"]) \
        .drop_duplicates("historical_date").sort_values("historical_date")
    tot["historical_date_key"] = tot["historical_date"].dt.strftime("%Y-%m-%d")
    tot["mkt_ret_1d"] = tot["total_mcap"].pct_change()
    can["historical_date_key"] = can["historical_date"].dt.strftime("%Y-%m-%d")
    can = can.drop(columns=["market_cap_usd"], errors="ignore")
    can = can.merge(tot[["historical_date_key", "mkt_ret_1d"]],
                    on="historical_date_key", how="left")
    return lf, can


def impulse_class(s: pd.Series, q10: float, q40: float, q60: float,
                  q90: float) -> pd.Series:
    out = pd.Series("ALL", index=s.index)
    out[s >= q90] = "POSITIVE_MARKET"
    out[s <= q10] = "NEGATIVE_MARKET"
    out[(s >= q40) & (s <= q60)] = "CALM"
    return out


def block_boot_ci_date_median(date_medians: np.ndarray, alpha=0.05):
    """Block bootstrap CI for the median of a per-date-median series.
    Block length 20 days, 500 reps (frozen). Fast: operates on the
    date-median series (<= 2195 points), not pooled asset-days."""
    rng = np.random.default_rng(SEED)
    n = len(date_medians)
    if n < 2:
        return np.nan, np.nan
    stats = []
    for _ in range(BOOT_N):
        starts = rng.integers(0, n, size=int(np.ceil(n / BOOT_BLOCK)))
        idx = np.concatenate([np.arange(s, min(s + BOOT_BLOCK, n))
                              for s in starts])
        idx = idx[:n]
        stats.append(np.median(date_medians[idx]))
    stats = np.array(stats)
    return float(np.percentile(stats, 100 * alpha / 2)), \
        float(np.percentile(stats, 100 * (1 - alpha / 2)))


def main() -> int:
    lf, can = load_panels()

    # ---- global impulse percentiles from canonical panel only ----
    mkt = can["mkt_ret_1d"].dropna()
    q10, q40, q60, q90 = (np.percentile(mkt, [10, 40, 60, 90]))
    print(f"impulse percentiles P10={q10:.4f} P40={q40:.4f} "
          f"P60={q60:.4f} P90={q90:.4f}", flush=True)

    # ---- combine panels for band analysis ----
    comb = pd.concat([
        can[["historical_date", "cmc_id", "rank", "rank_band", "ret_1d",
             "mkt_ret_1d", "is_stablecoin"]],
        lf[["historical_date", "cmc_id", "rank", "rank_band", "ret_1d",
            "mkt_ret_1d", "is_stablecoin"]],
    ], ignore_index=True)
    comb["historical_date_key"] = comb["historical_date"].dt.strftime("%Y-%m-%d")
    comb["impulse"] = impulse_class(comb["mkt_ret_1d"], q10, q40, q60, q90)
    comb["clean"] = ~(comb["is_stablecoin"].astype(bool)
                      | comb["ret_1d"].isna())

    # =====================================================================
    # PHASE C — rank-dependent elasticity
    # =====================================================================
    rows = []
    for band in BANDS:
        bd = comb[(comb["rank_band"] == band) & comb["clean"]]
        for imp in IMPULSE_ORDER:
            sub = bd[bd["impulse"] == imp] if imp != "ALL" else bd
            r = sub["ret_1d"].dropna()
            m = sub["mkt_ret_1d"].dropna()
            n_days = sub["historical_date_key"].nunique()
            tested = n_days >= MIN_CELL_DAYS
            dm = sub.groupby("historical_date_key")["ret_1d"].median()
            if len(r) == 0 or not tested:
                rows.append({"rank_band": band, "impulse": imp,
                             "n_asset_days": int(len(r)),
                             "n_days": int(n_days), "tested": tested,
                             "median": np.nan, "mean": np.nan, "p75": np.nan,
                             "p90": np.nan, "p95": np.nan, "iqr": np.nan,
                             "mad": np.nan, "tail_up_5": np.nan,
                             "tail_dn_5": np.nan, "elasticity_ols": np.nan,
                             "amplification": np.nan,
                             "ci_amp_lo": np.nan, "ci_amp_hi": np.nan})
                continue
            med = float(dm.median())
            med_mkt = m.median() if len(m) else np.nan
            amp = med / med_mkt if med_mkt and np.isfinite(med_mkt) else np.nan
            ci = block_boot_ci_date_median(dm.values)
            mm = sub[["ret_1d", "mkt_ret_1d"]].dropna()
            slope = np.nan
            if len(mm) > 30 and mm["mkt_ret_1d"].std() > 0:
                slope = np.polyfit(mm["mkt_ret_1d"], mm["ret_1d"], 1)[0]
            rows.append({
                "rank_band": band, "impulse": imp,
                "n_asset_days": int(len(r)), "n_days": int(n_days),
                "tested": tested,
                "median": med, "mean": float(r.mean()),
                "p75": float(r.quantile(0.75)), "p90": float(r.quantile(0.90)),
                "p95": float(r.quantile(0.95)),
                "iqr": float(r.quantile(0.75) - r.quantile(0.25)),
                "mad": float((r - r.median()).abs().median()),
                "tail_up_5": float((r > 0.05).mean()),
                "tail_dn_5": float((r < -0.05).mean()),
                "elasticity_ols": float(slope) if np.isfinite(slope) else np.nan,
                "amplification": float(amp) if np.isfinite(amp) else np.nan,
                "ci_amp_lo": float(ci[0]), "ci_amp_hi": float(ci[1]),
            })
    elast = pd.DataFrame(rows)
    elast.to_csv(ROOT / "RESULTS" / "06_RANK_ELASTICITY.csv", index=False)
    print("phase C done:", elast.shape, flush=True)

    # =====================================================================
    # PHASE I — up/down asymmetry
    # =====================================================================
    arows = []
    for band in BANDS:
        bd = comb[(comb["rank_band"] == band) & comb["clean"]]
        pos = bd[bd["impulse"] == "POSITIVE_MARKET"]
        neg = bd[bd["impulse"] == "NEGATIVE_MARKET"]
        if (pos["historical_date_key"].nunique() < MIN_CELL_DAYS
                or neg["historical_date_key"].nunique() < MIN_CELL_DAYS):
            arows.append({"rank_band": band, "tested": False,
                          "pos_elasticity": np.nan, "neg_elasticity": np.nan,
                          "asymmetry_ratio": np.nan, "ci_ratio_lo": np.nan,
                          "ci_ratio_hi": np.nan,
                          "pos_p95": np.nan, "neg_abs_p5": np.nan,
                          "tail_asymmetry": np.nan})
            continue

        def slope_of(d):
            mm = d[["ret_1d", "mkt_ret_1d"]].dropna()
            if len(mm) < 30 or mm["mkt_ret_1d"].std() <= 0:
                return np.nan
            return np.polyfit(mm["mkt_ret_1d"], mm["ret_1d"], 1)[0]
        pe = slope_of(pos)
        ne = slope_of(neg)
        ratio = abs(ne) / pe if pe and np.isfinite(pe) and abs(pe) > 1e-9 \
            else np.nan
        # date-block bootstrap CI for the ratio (slopes on per-date median
        # series, resampled in 20d blocks)
        pos_dm = pos.groupby("historical_date_key")["ret_1d"].median()
        neg_dm = neg.groupby("historical_date_key")["ret_1d"].median()
        pos_mk = pos.groupby("historical_date_key")["mkt_ret_1d"].first()
        neg_mk = neg.groupby("historical_date_key")["mkt_ret_1d"].first()
        ratios = []
        rng = np.random.default_rng(SEED)
        npos, nneg = len(pos_dm), len(neg_dm)

        def slope_dm(dm, mk, n):
            starts = rng.integers(0, n, size=int(np.ceil(n / BOOT_BLOCK)))
            idx = np.concatenate([np.arange(x, min(x + BOOT_BLOCK, n))
                                  for x in starts])[:n]
            y, x = dm.values[idx], mk.values[idx]
            if np.std(x) <= 0:
                return np.nan
            return np.polyfit(x, y, 1)[0]
        for _ in range(BOOT_N):
            a = slope_dm(pos_dm, pos_mk, npos)
            b = slope_dm(neg_dm, neg_mk, nneg)
            if np.isfinite(a) and np.isfinite(b) and abs(a) > 1e-9:
                ratios.append(abs(b / a))
        ratios = np.array(ratios)
        ci_lo, ci_hi = (np.percentile(ratios, [2.5, 97.5])
                        if len(ratios) else (np.nan, np.nan))
        pos_p95 = pos["ret_1d"].quantile(0.95)
        neg_abs_p5 = abs(neg["ret_1d"].quantile(0.05))
        arows.append({
            "rank_band": band, "tested": True,
            "pos_elasticity": float(pe) if np.isfinite(pe) else np.nan,
            "neg_elasticity": float(ne) if np.isfinite(ne) else np.nan,
            "asymmetry_ratio": float(ratio) if np.isfinite(ratio) else np.nan,
            "ci_ratio_lo": float(ci_lo), "ci_ratio_hi": float(ci_hi),
            "pos_p95": float(pos_p95), "neg_abs_p5": float(neg_abs_p5),
            "tail_asymmetry": float(neg_abs_p5 / pos_p95)
            if pos_p95 > 0 else np.nan,
        })
    asym = pd.DataFrame(arows)
    asym.to_csv(ROOT / "RESULTS" / "07_POS_NEG_ASYMMETRY.csv", index=False)
    print("phase I done:", asym.shape, flush=True)

    # =====================================================================
    # PHASE D — response surface (impulse quantile bin x rank band)
    # =====================================================================
    edges = np.percentile(mkt, [2.5, 10, 25, 50, 75, 90, 97.5])
    bins = [-np.inf] + list(edges) + [np.inf]
    labels = ["<P2.5", "P2.5-10", "P10-25", "P25-50", "P50-75", "P75-90",
              "P90-97.5", ">P97.5"]
    comb["imp_bin"] = pd.cut(comb["mkt_ret_1d"], bins=bins, labels=labels)
    srows = []
    for band in BANDS:
        bd = comb[(comb["rank_band"] == band) & comb["clean"]]
        for lab in labels:
            sub = bd[bd["imp_bin"] == lab]
            r = sub["ret_1d"].dropna()
            srows.append({
                "rank_band": band, "impulse_bin": lab,
                "n_asset_days": int(len(r)),
                "n_days": int(sub["historical_date_key"].nunique()),
                "median": float(r.median()) if len(r) else np.nan,
                "mean": float(r.mean()) if len(r) else np.nan,
                "p25": float(r.quantile(0.25)) if len(r) else np.nan,
                "p75": float(r.quantile(0.75)) if len(r) else np.nan,
                "p95": float(r.quantile(0.95)) if len(r) else np.nan,
                "iqr": float(r.quantile(0.75) - r.quantile(0.25))
                if len(r) else np.nan,
                "dispersion_cv": float(r.std() / abs(r.mean()))
                if len(r) and r.mean() else np.nan,
            })
    surf = pd.DataFrame(srows)
    surf.to_parquet(ROOT / "RESULTS" / "08_RESPONSE_SURFACE.parquet", index=False)
    print("phase D done:", surf.shape, flush=True)

    # =====================================================================
    # PHASE B — extreme event catalog (lenses on every event)
    # =====================================================================
    lf2 = lf.copy()
    lf2 = lf2[~lf2["is_stablecoin"].astype(bool)].copy()
    obs_count = lf2.groupby("cmc_id")["ret_1d"].transform("count")
    lf2 = lf2[obs_count >= MIN_OBS_ASSET].copy()
    grp = lf2.groupby("cmc_id")["ret_1d"]
    ev_rows = []
    for fam_p, fam_name in FAMILIES.items():
        hi = grp.transform(lambda s: s.quantile(1 - fam_p))
        lo = grp.transform(lambda s: s.quantile(fam_p))
        ev = lf2[(lf2["ret_1d"] >= hi) | (lf2["ret_1d"] <= lo)].copy()
        ev["family"] = fam_name
        ev["event_sign"] = np.where(ev["ret_1d"] > 0, "UP", "DOWN")
        ev_rows.append(ev)
    catalog = pd.concat(ev_rows, ignore_index=True)
    catalog = catalog.drop_duplicates(["cmc_id", "historical_date", "family"])

    # liquidity quartile (dollar volume within date, cross-sectional)
    catalog["liq_q"] = catalog.groupby("historical_date")["volume_24h_usd"] \
        .transform(lambda s: pd.qcut(s.rank(method="first"), 4, labels=False))
    # concentration: top-3 mcap share of top-500 from canonical
    c3 = pd.read_parquet(CANON_UNIVERSE,
                         columns=["historical_date", "market_cap_usd"])
    c3 = c3.sort_values("market_cap_usd", ascending=False) \
        .groupby("historical_date").head(3)
    c3t = c3.groupby("historical_date")["market_cap_usd"].sum()
    tot = pd.read_parquet(CANON_UNIVERSE, columns=["historical_date",
                                                   "total_mcap"]) \
        .drop_duplicates("historical_date")
    conc = (c3t / tot.set_index("historical_date")["total_mcap"]) \
        .rename("conc_top3").reset_index()
    conc["historical_date_key"] = conc["historical_date"].dt.strftime("%Y-%m-%d")
    catalog["historical_date_key"] = catalog["historical_date"] \
        .dt.strftime("%Y-%m-%d")
    catalog = catalog.merge(conc[["historical_date_key", "conc_top3"]],
                            on="historical_date_key", how="left")

    out_cols = ["family", "event_sign", "historical_date", "cmc_id", "name",
                "symbol", "rank", "rank_band", "ret_1d", "mkt_ret_1d",
                "btc_ret_1d", "eth_ret_1d", "top500_breadth_30d",
                "mkt_vol_30d", "conc_top3", "tags", "platform_chain",
                "vol_accel", "rank_vel_3d", "rank_vel_7d", "ret_3d", "ret_7d",
                "ret_14d", "ret_30d", "ret_60d", "listing_age_days", "liq_q",
                "is_stablecoin", "flag_stale_price", "flag_zero_volume",
                "flag_missing_price", "flag_listing_day"]
    catalog = catalog[[c for c in out_cols if c in catalog.columns]]
    catalog.to_parquet(ROOT / "EVENTS" / "05_EXTREME_EVENT_CATALOG.parquet",
                       index=False)
    print("phase B done:", catalog.shape, flush=True)

    th = {"P10": float(q10), "P40": float(q40), "P60": float(q60),
          "P90": float(q90)}
    (ROOT / "RESULTS" / "impulse_thresholds.json").write_text(
        __import__("json").dumps(th, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
