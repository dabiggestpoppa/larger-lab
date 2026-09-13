"""LOWER-FIELD-1 — diagnostic plots deck."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

import lf1_common as C

OUT = C.ROOT / "plots"
OUT.mkdir(exist_ok=True)
C.BANDS = ["501-750", "751-1000", "1001-1500", "1501-2000"]


def _mid(x):
    return float(x.split("-")[0]) + (float(x.split("-")[1]) - float(x.split("-")[0])) / 2


def main():
    # 03/04 amplitude + sigma-norm
    a3 = pd.read_csv(C.RESULTS / "03_AMPLITUDE_DISTRIBUTIONS.csv")
    a4 = pd.read_csv(C.RESULTS / "04_SIGMA_NORMALIZED_MOVE_DISTRIBUTIONS.csv")
    a1 = a3[(a3["horizon"] == "1D") & a3["rank_band"].isin(C.BANDS)].copy()
    a1["mid"] = a1["rank_band"].map(_mid)
    fig, ax = plt.subplots(1, 2, figsize=(12, 4))
    ax[0].plot(a1["mid"], a1["median_abs"], "-o", label="median")
    ax[0].plot(a1["mid"], a1["p95_abs"], "-o", label="p95")
    ax[0].plot(a1["mid"], a1["p99_abs"], "-o", label="p99")
    ax[0].set_title("1D |ret| amplitude vs rank depth")
    ax[0].set_xlabel("rank mid"); ax[0].legend()
    a4b = a4[(a4["horizon"] == "1D") & a4["rank_band"].isin(C.BANDS)].copy()
    a4b["mid"] = a4b["rank_band"].map(_mid)
    ax[1].plot(a4b["mid"], a4b["P_ge_2sigma"], "-o", label="P(>=2s)")
    ax[1].plot(a4b["mid"], a4b["P_ge_3sigma"], "-o", label="P(>=3s)")
    ax[1].plot(a4b["mid"], a4b["P_ge_4sigma"], "-o", label="P(>=4s)")
    ax[1].set_title("Sigma-norm tail freq vs depth (1D)")
    ax[1].set_xlabel("rank mid"); ax[1].legend()
    fig.tight_layout(); fig.savefig(OUT / "amplitude_sigma.png", dpi=120); plt.close(fig)

    # 05 time to delivery
    d5 = pd.read_csv(C.RESULTS / "05_TIME_TO_DELIVERY.csv")
    fig, ax = plt.subplots(figsize=(8, 5))
    for met in ["time_to_1sigma", "time_to_2sigma", "time_to_3sigma"]:
        s = d5[d5["metric"] == met].set_index("rank_band")["median_d"].get(C.BANDS)
        ax.plot([_mid(x) for x in s.index], s.values, "-o", label=met)
    ax.set_yscale("log")
    ax.set_title("Median time-to-delivery vs rank depth")
    ax.set_xlabel("rank mid"); ax.set_ylabel("days (log)"); ax.legend()
    fig.tight_layout(); fig.savefig(OUT / "time_to_delivery.png", dpi=120); plt.close(fig)

    # 07 tail activation gradient
    d7 = pd.read_csv(C.RESULTS / "07_TAIL_ACTIVATION_REVALIDATION.csv")
    sh = d7[d7["state"] == "SHORT_HOT_MEDIUM_COLD"].copy()
    sh["mid"] = sh["rank_band"].map(_mid)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(sh["mid"], sh["P_gt_2sigma"], "-o", label="P(>2s)")
    ax.plot(sh["mid"], sh["P_gt_3sigma"], "-o", label="P(>3s)")
    ax.fill_between(sh["mid"], sh["P_dn_extreme"], sh["P_up_extreme"], alpha=0.2)
    ax.plot(sh["mid"], sh["P_up_extreme"], "--o", label="P(up extr)")
    ax.plot(sh["mid"], sh["P_dn_extreme"], "--o", label="P(dn extr)")
    ax.set_title("SHORT_HOT_MEDIUM_COLD tail activation (fwd7) vs depth")
    ax.set_xlabel("rank mid"); ax.legend()
    fig.tight_layout(); fig.savefig(OUT / "tail_activation_gradient.png", dpi=120); plt.close(fig)

    # 09 breadth delivery discriminator
    d9 = pd.read_csv(C.RESULTS / "09_POTENTIAL_REALIZATION_DIVERGENCE.csv")
    br = d9[d9["feature"] == "top500_breadth_30d"].copy()
    br["mid"] = br["rank_band"].map(_mid)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(br["mid"], br["cohens_d"], "-o")
    ax.axhline(0, color="grey", lw=1)
    ax.set_title("top500_breadth delivery discriminator (cohens d) vs depth")
    ax.set_xlabel("rank mid"); ax.set_ylabel("cohens d")
    fig.tight_layout(); fig.savefig(OUT / "breadth_delivery_gate.png", dpi=120); plt.close(fig)

    # 13 reversal
    d13 = pd.read_csv(C.RESULTS / "13_REVERSAL_DECAY_GEOMETRY.csv")
    fig, ax = plt.subplots(figsize=(8, 5))
    for sgn, marker in [("UP", "o"), ("DOWN", "s")]:
        s = d13[d13["sign"] == sgn].copy()
        s["mid"] = s["rank_band"].map(_mid)
        ax.plot(s["mid"], s["P_rev_7d"], marker + "-", label=f"{sgn} P_rev")
    ax.set_title("P(reversal 7d) by sign vs rank depth")
    ax.set_xlabel("rank mid"); ax.legend()
    fig.tight_layout(); fig.savefig(OUT / "reversal_geometry.png", dpi=120); plt.close(fig)

    # 16 form change
    d16 = pd.read_csv(C.RESULTS / "16_FORM_CHANGE_BY_RANK.csv")
    fig, ax = plt.subplots(1, 2, figsize=(12, 4))
    ax[0].plot(d16["depth_rank_mid"], d16["mean_dispersion"], "-o")
    ax[0].set_title("band dispersion vs depth"); ax[0].set_xlabel("rank mid")
    ax[1].plot(d16["depth_rank_mid"], d16["corr_band_btc"], "-o")
    ax[1].set_title("band median-BTC corr vs depth"); ax[1].set_xlabel("rank mid")
    fig.tight_layout(); fig.savefig(OUT / "form_change.png", dpi=120); plt.close(fig)

    print("plots written to", OUT)


if __name__ == "__main__":
    main()