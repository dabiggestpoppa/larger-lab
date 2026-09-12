#!/usr/bin/env python
"""Generate MECH-10 plots (terrain visualization only)."""
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

CELLS = ["HIGH_BREADTH_HIGH_DISP", "HIGH_BREADTH_LOW_DISP",
         "LOW_BREADTH_HIGH_DISP", "LOW_BREADTH_LOW_DISP"]
SHORT = {"HIGH_BREADTH_HIGH_DISP": "HH", "HIGH_BREADTH_LOW_DISP": "HL",
         "LOW_BREADTH_HIGH_DISP": "LH", "LOW_BREADTH_LOW_DISP": "LL"}


def p1_decomposition():
    d = pd.read_csv(OUT / "02_STATE_AGE_MECHANISM_DECOMPOSITION.csv")
    fig, ax = plt.subplots(figsize=(7, 4))
    sub = d.dropna(subset=["diff"])
    ax.bar(sub["component"], sub["diff"], color="#4C72B0")
    ax.axhline(0, color="k", lw=0.8)
    ax.set_ylabel("long-lived - short-lived (effect)")
    ax.set_title("MECH-10 WS1: state-age mechanism decomposition")
    for i, r in sub.iterrows():
        ax.annotate(f"p={r['p']:.2g}", (i - 0.15, r["diff"]),
                    fontsize=7)
    fig.tight_layout()
    fig.savefig(FIG / "p1_decomposition.png")
    plt.close(fig)


def p2_landmarks():
    lm = pd.read_csv(OUT / "03_CONDITIONAL_LANDMARKS.csv")
    fig, ax = plt.subplots(figsize=(7, 4))
    for cell in ["HIGH_BREADTH_HIGH_DISP"]:
        sub = lm[lm["cell"] == cell].sort_values("landmark_age")
        ax.plot(sub["landmark_age"], sub["p_prop_7d"], "o-",
                label="P(prop within 7D)")
        ax.plot(sub["landmark_age"], sub["p_reentry_7d"], "s--",
                label="P(reentry within 7D)")
        ax.plot(sub["landmark_age"], sub["p_stay_7d"], "^:",
                label="P(stay 7D)")
        ax.set_xlabel("landmark age (days)")
        ax.set_ylabel("rate")
        ax.set_title("MECH-10 WS2: HH conditional landmarks")
        ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(FIG / "p2_landmarks.png")
    plt.close(fig)


def p3_delivery_clocks():
    d = pd.read_csv(OUT / "04_4STATE_TEMPORAL_DELIVERY.csv")
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    for ax, cell in zip(axes.flat, CELLS):
        sub = d[(d["cell"] == cell) &
                (d["clock"].isin(["PROPAGATION", "REENTRY"]))]
        pivot = sub.pivot_table(index="age_band", columns="clock",
                                values="p_by_7d", aggfunc="first")
        pivot.plot(ax=ax, marker="o")
        ax.set_title(SHORT[cell])
        ax.set_ylabel("P(event within 7D)")
        ax.tick_params(axis="x", rotation=30)
    fig.suptitle("MECH-10 WS3: 4-state temporal delivery clocks")
    fig.tight_layout()
    fig.savefig(FIG / "p3_delivery_clocks.png")
    plt.close(fig)


def p4_exit_hazards():
    h = pd.read_csv(OUT / "05_4STATE_EXIT_HAZARDS.csv")
    fig, ax = plt.subplots(figsize=(8, 4))
    for cell in CELLS:
        sub = h[h["cell"] == cell].sort_values("h_d")
        ax.plot(sub["h_d"], sub["hazard"], "o-",
                label=SHORT[cell])
    ax.set_xlabel("time since state entry (days)")
    ax.set_ylabel("P(exit next day)")
    ax.set_title("MECH-10 WS4: 4-state exit hazards")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG / "p4_exit_hazards.png")
    plt.close(fig)


def p5_prd_vs_pru():
    c = pd.read_csv(OUT / "09_PRICE_UP_RANK_DOWN_VS_RANK_UP.csv")
    fig, ax = plt.subplots(figsize=(9, 5))
    sig = c[c["p_fdr"] < 0.10]
    base = c[~c.index.isin(sig.index)]
    ax.scatter(base["axis"], base["diff"], alpha=0.5, s=30,
               label="not FDR-significant")
    ax.scatter(sig["axis"], sig["diff"], s=50, color="crimson",
               label="FDR q<0.10")
    ax.axhline(0, color="k", lw=0.8)
    ax.set_ylabel("PRD median - PRU median")
    ax.set_title("MECH-10 WS7: PRICE_RECOVERY_RANK_DECAY vs RANK_RECOVERY")
    ax.tick_params(axis="x", rotation=60)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(FIG / "p5_prd_vs_pru.png")
    plt.close(fig)


def p6_stress_process():
    p = pd.read_csv(OUT / "12_STRESS_RESPONSE_PROCESS.csv")
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    for ax, dim in zip(axes, ["breadth", "rank"]):
        sub = p[p["dimension"] == dim]
        if not len(sub):
            continue
        for cls, col in [("RESPONDS", "responds_med"),
                         ("NO_RESPONSE", "no_resp_med")]:
            ax.plot(sub["lag_d"], sub[col], "o-", label=cls)
        ax.set_xlabel("days from event")
        ax.set_title(f"{dim} response process")
        ax.legend(fontsize=8)
    fig.suptitle("MECH-10 WS10: stress-response process")
    fig.tight_layout()
    fig.savefig(FIG / "p6_stress_process.png")
    plt.close(fig)


def p7_perm_real():
    t = pd.read_csv(OUT / "16_PERMISSION_REALIZATION_TEST.csv")
    fig, ax = plt.subplots(figsize=(7, 4))
    x = np.arange(len(t))
    ax.bar(x, t["fwd7_prop"], color="#55A868",
           label="P(prop within 7D)")
    ax.bar(x, t["p_tail_by_7d"], color="#C44E52", alpha=0.7,
           label="P(tail within 7D)")
    ax.set_xticks(x)
    ax.set_xticklabels(t["move_type"], rotation=15)
    ax.set_ylabel("rate")
    ax.set_title("MECH-10 WS14: permission -> realization entry orders")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG / "p7_perm_real.png")
    plt.close(fig)


if __name__ == "__main__":
    for fn in [p1_decomposition, p2_landmarks, p3_delivery_clocks,
               p4_exit_hazards, p5_prd_vs_pru, p6_stress_process,
               p7_perm_real]:
        fn()
    print("plots done")
