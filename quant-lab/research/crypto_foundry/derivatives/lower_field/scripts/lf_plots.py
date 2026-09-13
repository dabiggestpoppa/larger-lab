#!/usr/bin/env python3
"""LF — checkpoint plots (rank vs elasticity, surface, horizon map, decay)."""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "plots"
OUT.mkdir(exist_ok=True)

BANDS = ["1-25", "26-100", "101-250", "251-500", "501-750", "751-1000",
         "1001-1500", "1501-2000"]
BAND_X = np.arange(len(BANDS))


def main() -> int:
    elast = pd.read_csv(ROOT / "RESULTS" / "06_RANK_ELASTICITY.csv")
    asym = pd.read_csv(ROOT / "RESULTS" / "07_POS_NEG_ASYMMETRY.csv")
    surf = pd.read_parquet(ROOT / "RESULTS" / "08_RESPONSE_SURFACE.parquet")
    horiz = pd.read_csv(ROOT / "RESULTS" / "10_MOMENTUM_HORIZON_REDUNDANCY.csv")
    persist = pd.read_csv(ROOT / "RESULTS" / "12_PERSISTENCE_DECAY.csv")

    # 1. rank vs median response (pos/neg market days)
    fig, ax = plt.subplots(figsize=(9, 5))
    for imp, color in [("POSITIVE_MARKET", "tab:green"),
                       ("NEGATIVE_MARKET", "tab:red")]:
        d = elast[(elast["impulse"] == imp) & elast["tested"]]
        d = d.set_index("rank_band").reindex(BANDS).reset_index()
        ax.plot(BAND_X, d["median"] * 100, marker="o", color=color,
                label=imp)
        ax.fill_between(BAND_X,
                        (d["median"] - d["iqr"]) * 100,
                        (d["median"] + d["iqr"]) * 100, alpha=0.12,
                        color=color)
    ax.axvline(3.5, color="grey", ls="--", lw=1)
    ax.text(3.6, ax.get_ylim()[1], "rank 500 boundary", fontsize=8)
    ax.set_xticks(BAND_X)
    ax.set_xticklabels(BANDS, rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("median asset 1D return (%)")
    ax.set_title("Median lower-field response on extreme market days by rank band")
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUT / "rank_vs_median_response.png", dpi=130)
    plt.close(fig)

    # 2. rank vs asymmetry ratio
    fig, ax = plt.subplots(figsize=(9, 5))
    d = asym.set_index("rank_band").reindex(BANDS).reset_index()
    ax.plot(BAND_X, d["asymmetry_ratio"], marker="s", color="tab:purple",
            label="|neg el| / pos el")
    ax.fill_between(BAND_X, d["ci_ratio_lo"], d["ci_ratio_hi"], alpha=0.2,
                    color="tab:purple")
    ax.axhline(1.0, color="black", ls="--", lw=1)
    ax.set_xticks(BAND_X)
    ax.set_xticklabels(BANDS, rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("asymmetry ratio")
    ax.set_title("Up/down elasticity asymmetry by rank band (CI = block bootstrap)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUT / "rank_vs_asymmetry.png", dpi=130)
    plt.close(fig)

    # 3. response surface heatmap (median ret by band x impulse bin)
    pivot = surf.pivot(index="rank_band", columns="impulse_bin",
                       values="median").reindex(BANDS)
    order = ["<P2.5", "P2.5-10", "P10-25", "P25-50", "P50-75", "P75-90",
             "P90-97.5", ">P97.5"]
    pivot = pivot[order]
    fig, ax = plt.subplots(figsize=(11, 6))
    im = ax.imshow(pivot.values * 100, cmap="RdBu_r", aspect="auto",
                   vmin=-8, vmax=8)
    ax.set_xticks(range(len(order)))
    ax.set_xticklabels(order, fontsize=8)
    ax.set_yticks(range(len(BANDS)))
    ax.set_yticklabels(BANDS, fontsize=8)
    ax.set_xlabel("global market impulse bin (cap-weighted top-500 1D return)")
    ax.set_ylabel("rank band")
    ax.set_title("Median asset 1D return (%) by market impulse x rank band")
    fig.colorbar(im, label="median ret %")
    fig.tight_layout()
    fig.savefig(OUT / "response_surface.png", dpi=130)
    plt.close(fig)

    # 4. horizon redundancy map
    fig, ax = plt.subplots(figsize=(9, 6))
    for band in BANDS:
        d = horiz[horiz["rank_band"] == band]
        ax.plot([1, 3, 7, 14, 30, 60],
                [d[d["horizon"] == h]["corr_1d"].iloc[0] for h in
                 [1, 3, 7, 14, 30, 60]],
                marker="o", label=band, lw=1.2)
    ax.set_xscale("log")
    ax.set_xticks([1, 3, 7, 14, 30, 60])
    ax.set_xticklabels(["1D", "3D", "7D", "14D", "30D", "60D"])
    ax.set_ylabel("corr with 1D return")
    ax.set_title("Horizon correlation with 1D return by rank band")
    ax.legend(fontsize=7, ncol=2)
    fig.tight_layout()
    fig.savefig(OUT / "horizon_redundancy_map.png", dpi=130)
    plt.close(fig)

    # 5. persistence decay by rank band (down-events, chain-confirmed)
    fig, ax = plt.subplots(figsize=(9, 6))
    for band in ["251-500", "501-750", "751-1000", "1001-1500", "1501-2000"]:
        d = persist[(persist["rank_band"] == band)
                    & (persist["event_sign"] == "DOWN")
                    & (persist["chain_confirms"] == True)]
        if d.empty:
            continue
        row = d.iloc[0]
        hs = [1, 3, 7, 14, 30]
        ax.plot(hs, [row[f"median_fwd_{h}d"] * 100 for h in hs],
                marker="o", label=band)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks([1, 3, 7, 14, 30])
    ax.set_xticklabels(["1D", "3D", "7D", "14D", "30D"])
    ax.set_ylabel("median forward return (%) after extreme DOWN day")
    ax.set_title("Post-extreme-down persistence/decay by rank band (chain-confirmed)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "persistence_decay_by_rank.png", dpi=130)
    plt.close(fig)

    # 6. extreme-event state map: prior 3D vs 7D momentum at event time
    cat = pd.read_parquet(ROOT / "EVENTS" / "05_EXTREME_EVENT_CATALOG.parquet")
    fam = cat[cat["family"] == "P2.5"].dropna(subset=["ret_3d", "ret_7d"])
    fig, ax = plt.subplots(figsize=(8, 8))
    for sign, color in [("UP", "tab:green"), ("DOWN", "tab:red")]:
        sub = fam[fam["event_sign"] == sign].sample(
            min(20000, len(fam[fam["event_sign"] == sign])), random_state=1)
        ax.scatter(sub["ret_3d"] * 100, sub["ret_7d"] * 100, s=2, alpha=0.05,
                   color=color, label=f"extreme {sign} days")
    ax.axhline(0, color="grey", lw=0.6)
    ax.axvline(0, color="grey", lw=0.6)
    ax.set_xlabel("prior 3D return %")
    ax.set_ylabel("prior 7D return %")
    ax.set_title("Extreme-move prior momentum state map (P2.5 family)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUT / "extreme_event_state_map.png", dpi=130)
    plt.close(fig)

    print("plots written to", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
