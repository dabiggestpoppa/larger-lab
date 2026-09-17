"""LOWER-FIELD-1 — 17 LOCAL_SEQUENCE_MAP.

Detects recurring local sequences (streaks of a binary band-state atom followed
by a downstream outcome) and requires reproducibility: >=30 instances across >=2
MECH-4 subperiods. Only surviving motifs are recorded.

Atoms (from prereg sec 14):
  VOL_EXPANSION        : band daily dispersion above its trailing (annual) median
  BAND_RISK_ON         : band median_ret > 0 for >=1 day (risk-on drift)
  LOWER_DISPERSION     : band dispersion in top decile of trailing year
  TOP500_BREADTH_HIGH  : top500 breadth high
  RANK_DETERIORATION   : band rank_migration more negative than trailing median

Streaks: consecutive-day runs where each atom's binary state == 1.

Outcomes measured after each streak:
  - P(2sigma tail day in next 7d)     (TAIL_AFTER)
  - P(sign reversal of band median)    (REVERSION)
  - streak duration distribution

Only atom->outcome edges with >=30 streak instances in >=2 subperiods are kept.

Output: RESULTS/17_LOCAL_SEQUENCE_MAP.csv
"""
import numpy as np
import pandas as pd

import lf1_common as C

SUBPERIODS = {
    "2020-2021": ("2020-09-01", "2021-12-31"),
    "2022": ("2022-01-01", "2022-12-31"),
    "2023": ("2023-01-01", "2023-12-31"),
    "2024": ("2024-01-01", "2024-12-31"),
    "2025-2026": ("2025-01-01", "2026-08-31"),
}


def streaks(mask):
    """Return list of (start_idx, length) for True runs in a boolean array of index."""
    out = []
    run = 0
    start = None
    for i, v in enumerate(mask.to_numpy()):
        if v:
            if run == 0:
                start = i
            run += 1
        else:
            if run > 0:
                out.append((start, run))
            run = 0
    if run > 0:
        out.append((start, run))
    return out


def main():
    # band-level daily state (from handoff artifact: has dispersion, median_ret,
    # rt rank_migration_7d, breadth already)
    h = pd.read_parquet(C.HANDBF).copy()
    h["date"] = pd.to_datetime(h["date"])
    h = h.dropna(subset=["dispersion", "median_ret"])

    records = []
    for band in C.PRIMARY_BANDS:
        b = h[h["rank_band"] == band].sort_values("date").set_index("date")
        # trailing baselines
        disp_base = b["dispersion"].rolling(252, min_periods=120).median()
        vol_high = b["dispersion"] > disp_base
        # lower dispersion = top decile of trailing 252
        disp_decile = b["dispersion"].rolling(252, min_periods=120).quantile(0.90)
        lower_disp = b["dispersion"] > disp_decile
        risk_on = b["median_ret"] > 0
        rank_det = b["rank_migration_7d"] if "rank_migration_7d" in b else pd.Series(np.nan, index=b.index)
        rm_base = rank_det.rolling(252, min_periods=120).median()
        rank_deteriorate = rank_det < rm_base
        breadth_high = b.get("breadth") if "breadth" in h.columns else None

        atoms = {
            "VOL_EXPANSION": vol_high.fillna(False),
            "BAND_RISK_ON": risk_on.fillna(False),
            "LOWER_DISPERSION": lower_disp.fillna(False),
            "RANK_DETERIORATION": rank_deteriorate.fillna(False),
        }
        # subperiod label per row
        sp = pd.Series(pd.NaT, index=b.index, dtype="str")
        for name, (s, e) in SUBPERIODS.items():
            sp[(b.index >= s) & (b.index <= e)] = name

        for atom, mask in atoms.items():
            for (start_idx, length) in streaks(mask):
                if length < 2:
                    continue
                d0 = b.index[start_idx]
                spd = sp.loc[d0]
                if pd.isna(spd):
                    continue
                # first day AFTER streak end
                end_i = start_idx + length
                # outcome: any day in next 7d where dispersion > 2x trailing-60d median (real tail expansion)
                tail_after = np.nan
                if end_i < len(b) - 7:
                    d60 = b["dispersion"].iloc[max(0, end_i - 60):end_i].median()
                    tail_after = bool((b["dispersion"].iloc[end_i:end_i + 7] > 2 * d60).any()) if d60 > 0 else np.nan
                revert = np.nan
                if end_i < len(b) - 1:
                    before = b["median_ret"].iloc[end_i - 1]
                    after = b["median_ret"].iloc[end_i] if end_i < len(b) else np.nan
                    if np.isfinite(before) and np.isfinite(after):
                        revert = bool((before > 0) != (after > 0)) if before != 0 else np.nan
                records.append({
                    "band": band, "atom": atom, "streak_len": length, "date": d0,
                    "subperiod": spd, "tail_after": tail_after, "revert": revert,
                })

    df = pd.DataFrame(records)
    df.to_csv(C.RESULTS / "17_LOCAL_SEQUENCE_MAP_RAW.csv", index=False)
    print("raw streaks", len(df))

    # reproducibility filter: atom x band x outcome cell must have >=30 streaks across >=2 subperiods
    rows = []
    for band in C.PRIMARY_BANDS:
        for atom in ["VOL_EXPANSION", "BAND_RISK_ON", "LOWER_DISPERSION", "RANK_DETERIORATION"]:
            sub = df[(df["band"] == band) & (df["atom"] == atom)]
            if len(sub) == 0:
                continue
            nsp = sub["subperiod"].nunique()
            if len(sub) >= 30 and nsp >= 2:
                p_tail = sub["tail_after"].dropna()
                p_rev = sub["revert"].dropna()
                rows.append({
                    "band": band, "atom": atom, "n_streaks": int(len(sub)),
                    "n_subperiods": int(nsp),
                    "median_streak_len": round(float(np.median(sub["streak_len"])), 2),
                    "max_streak_len": int(sub["streak_len"].max()),
                    "P_tail_after": round(float(p_tail.mean()) if len(p_tail) else np.nan, 4),
                    "P_revert_after": round(float(p_rev.mean()) if len(p_rev) else np.nan, 4),
                })
    d17 = pd.DataFrame(rows)
    d17.to_csv(C.RESULTS / "17_LOCAL_SEQUENCE_MAP.csv", index=False)
    print("\n=== 17 reproducible local sequences (>=30 streaks, >=2 subperiods) ===")
    print(d17.to_string(index=False))
    print("\nwrote 17")


if __name__ == "__main__":
    main()