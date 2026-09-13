"""LOWER-FIELD-1 — 03 AMPlitude distr & 04 sigma-normalized move distrs.

Outputs:
  RESULTS/03_AMPLITUDE_DISTRIBUTIONS.csv
  RESULTS/04_SIGMA_NORMALIZED_MOVE_DISTRIBUTIONS.csv
"""
import numpy as np
import pandas as pd

import lf1_common as C


def quant(group, q):
    return group.quantile(q)


def build(band_df):
    """Return amplitude table and sigma-normalized table for a band df (with sigma col)."""
    records = []
    sig_records = []
    for h, col in C.RET_COLS.items():
        r = band_df[col].dropna()
        if len(r) == 0:
            continue
        a = r.abs()
        up = r[r > 0]
        dn = r[r < 0].abs()
        row = {
            "horizon": h,
            "n": int(len(r)),
            "pct_nonzero": round(float((r != 0).mean()), 4),
            "median_abs": round(float(a.median()), 5),
            "p75_abs": round(float(a.quantile(0.75)), 5),
            "p90_abs": round(float(a.quantile(0.90)), 5),
            "p95_abs": round(float(a.quantile(0.95)), 5),
            "p99_abs": round(float(a.quantile(0.99)), 5),
            "median_up": round(float(up.median()) if len(up) else np.nan, 5),
            "p90_up": round(float(up.quantile(0.90)) if len(up) else np.nan, 5),
            "p99_up": round(float(up.quantile(0.99)) if len(up) else np.nan, 5),
            "median_dn": round(float(dn.median()) if len(dn) else np.nan, 5),
            "p90_dn": round(float(dn.quantile(0.90)) if len(dn) else np.nan, 5),
            "p99_dn": round(float(dn.quantile(0.99)) if len(dn) else np.nan, 5),
        }
        records.append(row)

        # sigma-normalized at t0: ret_h / sigma_t0, only where sigma valid
        sub = band_df[[col, "sigma_t0"]].dropna()
        if len(sub):
            z = (sub[col] / sub["sigma_t0"]).abs()
            rec = {
                "horizon": h,
                "n": int(len(z)),
                "P_ge_1sigma": round(float((z >= 1.0).mean()), 5),
                "P_ge_2sigma": round(float((z >= 2.0).mean()), 5),
                "P_ge_3sigma": round(float((z >= 3.0).mean()), 5),
                "P_ge_4sigma": round(float((z >= 4.0).mean()), 5),
                "median_sigma": round(float(z.median()), 4),
                "p95_sigma": round(float(z.quantile(0.95)), 4),
                "p99_sigma": round(float(z.quantile(0.99)), 4),
            }
            sig_records.append(rec)
    return pd.DataFrame(records), pd.DataFrame(sig_records)


def main():
    p = pd.read_parquet(C.PANEL)
    print("panel rows", len(p))

    # causal trailing-63d sigma as a column (sigma_t0 = sigma known before day t)
    p["sigma_t0"] = C.compute_sigma(p)

    amp_tables, sig_tables = [], []
    for band in C.PRIMARY_BANDS:
        bdf = p[p["rank_band"] == band]
        a, s = build(bdf)
        if not a.empty:
            a.insert(0, "rank_band", band)
        if not s.empty:
            s.insert(0, "rank_band", band)
        amp_tables.append(a)
        sig_tables.append(s)

    amp_all = pd.concat(amp_tables, ignore_index=True)
    sig_all = pd.concat(sig_tables, ignore_index=True)

    # add comparison upper bands from canonical
    can = C.canonical_upper_bands()
    can["sigma_t0"] = C.compute_sigma(can)
    for band in ["251-500", "101-250", "26-100"]:
        bdf = can[can["rank_band"] == band]
        a, s = build(bdf)
        if not a.empty:
            a.insert(0, "rank_band", band)
        if not s.empty:
            s.insert(0, "rank_band", band)
        amp_all = pd.concat([amp_all, a], ignore_index=True)
        sig_all = pd.concat([sig_all, s], ignore_index=True)

    amp_all.to_csv(C.RESULTS / "03_AMPLITUDE_DISTRIBUTIONS.csv", index=False)
    sig_all.to_csv(C.RESULTS / "04_SIGMA_NORMALIZED_MOVE_DISTRIBUTIONS.csv", index=False)
    pd.set_option("display.width", 200)
    print("=== AMPLITUDE (1D row per band) ===")
    print(amp_all[amp_all["horizon"] == "1D"][
        ["rank_band", "median_abs", "p75_abs", "p95_abs", "p99_abs", "median_up", "median_dn"]
    ].to_string(index=False))
    print("\n=== SIGMA-NORM (1D) ===")
    print(sig_all[sig_all["horizon"] == "1D"][
        ["rank_band", "P_ge_1sigma", "P_ge_2sigma", "P_ge_3sigma", "P_ge_4sigma"]
    ].to_string(index=False))
    print("\nwrote 03_AMPLITUDE_DISTRIBUTIONS.csv and 04_SIGMA_NORMALIZED_MOVE_DISTRIBUTIONS.csv")


if __name__ == "__main__":
    main()