#!/usr/bin/env python
"""Generate MECH-9 plots (terrain visualization only)."""
import warnings
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

warnings.filterwarnings("ignore")
OUT = Path(__file__).resolve().parents[1]
FIG = OUT / "plots"
FIG.mkdir(exist_ok=True)

plt.rcParams.update({"figure.dpi": 110, "font.size": 9,
                     "axes.titlesize": 10, "axes.labelsize": 9})


def p1_state_age_surface():
    s = pd.read_csv(OUT / "02_STATE_AGE_CONTINUOUS_SURFACE.csv")
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    for ax, cell in zip(axes.flat, [
            "HIGH_BREADTH_HIGH_DISP", "HIGH_BREADTH_LOW_DISP",
            "LOW_BREADTH_HIGH_DISP", "LOW_BREADTH_LOW_DISP"]):
        sub = s[s["cell"] == cell].sort_values("age_d")
        ax.plot(sub["age_d"], sub["p_leave_next"], "o-", label="P(leave next)")
        ax.plot(sub["age_d"], sub["fwd7_prop"], "s--", label="fwd7 prop")
        ax.set_title(cell)
        ax.set_xlabel("state age (days)")
        ax.legend(fontsize=7)
    fig.suptitle("MECH-9 WS1: continuous state-age surfaces")
    fig.tight_layout()
    fig.savefig(FIG / "p1_state_age_surface.png")
    plt.close(fig)


def p2_landmark():
    surv = pd.read_csv(OUT / "03_STATE_AGE_SURVIVORSHIP_AUDIT.csv")
    lm = surv[surv["analysis"] == "landmark"].sort_values("landmark_d")
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(lm["landmark_d"], lm["fwd7_prop"], "o-", label="fwd7 prop (age>=lm)")
    ax.plot(lm["landmark_d"], lm["p_leave_next"], "s--", label="P(leave next)")
    ax.set_xlabel("landmark (age >= d)")
    ax.set_ylabel("rate")
    ax.set_title("MECH-9 WS2: HH landmark analysis (survivorship)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG / "p2_landmark.png")
    plt.close(fig)


def p3_birth_quality():
    u = pd.read_csv(OUT / "05c_HH_BIRTH_QUALITY_UNIVARIATE.csv")
    u = u.sort_values("diff", key=lambda s: s.abs(), ascending=False)
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.barh(u["var"], u["diff"], color=["#2a9d8f" if d >= 0 else "#e76f51"
                                        for d in u["diff"]])
    ax.set_xlabel("long-lived - short-lived median (entry day)")
    ax.set_title("MECH-9 WS4: HH birth quality - entry coordinate differences")
    fig.tight_layout()
    fig.savefig(FIG / "p3_birth_quality.png")
    plt.close(fig)


def p4_bifurcation():
    b = pd.read_csv(OUT / "08_LOCAL_BIFURCATION_SEARCH.csv")
    fig, ax = plt.subplots(figsize=(9, 4))
    cols = ["#e76f51" if v.startswith("BIFURCATION") else
            "#2a9d8f" if v.startswith("SHARP") else "#a9a9a9"
            for v in b["verdict"]]
    ax.barh(b["axis"], b["max_jump"], color=cols)
    for i, (_, r) in enumerate(b.iterrows()):
        ax.text(r["max_jump"] + 0.005, i, r["verdict"], va="center", fontsize=8)
    ax.set_xlabel("max adjacent-bin jump in P(prop7)")
    ax.set_title("MECH-9 WS7: local bifurcation search (raw-coordinate binned)")
    fig.tight_layout()
    fig.savefig(FIG / "p4_bifurcation.png")
    plt.close(fig)


def p5_health_matrix():
    h = pd.read_csv(OUT / "11_HEALTH_STATE_FIELD_MATRIX.csv")
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    states = ["PRICE_RECOVERY_RANK_RECOVERY", "PRICE_RECOVERY_RANK_DECAY",
              "PRICE_DECAY_RANK_RECOVERY", "PRICE_DECAY_RANK_DECAY"]
    for ax, hs in zip(axes.flat, states):
        sub = h[h["health_state"] == hs].sort_values("lag_d")
        ax.axvline(0, color="k", ls=":", lw=0.8)
        ax.plot(sub["lag_d"], sub["med_top500_breadth_30d"], "o-",
                label="breadth30")
        ax.plot(sub["lag_d"], sub["med_top500_dispersion_30d"], "s--",
                label="disp30")
        ax.set_title(hs.replace("_", " ")[:34])
        ax.set_xlabel("lag (days)")
        ax.legend(fontsize=7)
    fig.suptitle("MECH-9 WS10: health-state field context -14..+30")
    fig.tight_layout()
    fig.savefig(FIG / "p5_health_matrix.png")
    plt.close(fig)


def p6_stress_surface():
    s = pd.read_csv(OUT / "15_STRESS_RESPONSE_SURFACE.csv")
    fig, ax = plt.subplots(figsize=(7, 5))
    piv = s.pivot(index="imp_tile", columns="deter_tile", values="p_responds")
    im = ax.imshow(piv, cmap="RdYlGn", vmin=0.4, vmax=0.8)
    ax.set_xticks(range(len(piv.columns)))
    ax.set_xticklabels(piv.columns, rotation=30, ha="right")
    ax.set_yticks(range(len(piv.index)))
    ax.set_yticklabels(piv.index)
    ax.set_xlabel("prior rank deterioration")
    ax.set_ylabel("field improvement")
    for i in range(len(piv.index)):
        for j in range(len(piv.columns)):
            ax.text(j, i, f"{piv.iloc[i, j]:.2f}", ha="center", va="center",
                    fontsize=8)
    ax.set_title(f"MECH-9 WS13: P(RESPONDS) surface ({s['verdict'].iloc[0]})")
    fig.colorbar(im)
    fig.tight_layout()
    fig.savefig(FIG / "p6_stress_surface.png")
    plt.close(fig)


def p7_volatility_locality():
    v = pd.read_csv(OUT / "19_VOLATILITY_LOCALITY.csv")
    fig, ax = plt.subplots(figsize=(7, 4))
    x = np.arange(len(v))
    ax.bar(x - 0.2, v["HH_fwd7_prop"], 0.4, label="HH fwd7 prop")
    ax.bar(x + 0.2, v["HH_median_dwell"] / v["HH_median_dwell"].max(), 0.4,
           label="HH dwell (normalized)")
    ax.set_xticks(x)
    ax.set_xticklabels(v["vol_tile"])
    ax.set_ylabel("rate")
    ax.set_title("MECH-9 WS17: volatility locality in HH")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG / "p7_volatility_locality.png")
    plt.close(fig)


if __name__ == "__main__":
    p1_state_age_surface()
    p2_landmark()
    p3_birth_quality()
    p4_bifurcation()
    p5_health_matrix()
    p6_stress_surface()
    p7_volatility_locality()
    print("[plots] done - 7 figures")
