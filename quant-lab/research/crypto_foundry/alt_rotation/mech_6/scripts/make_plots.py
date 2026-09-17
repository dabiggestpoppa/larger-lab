#!/usr/bin/env python
"""MECH-6 plots: breadth transmission, sequence lifts, competing-risk CIF,
state-conditioned hazards, termination signatures."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
PLOTS = ROOT / "plots"
PLOTS.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({"figure.dpi": 110, "font.size": 9,
                     "axes.titlesize": 10, "axes.labelsize": 9})


def plot_cif():
    c = pd.read_csv(ROOT / "13_CUMULATIVE_INCIDENCE.csv")
    fig, ax = plt.subplots(figsize=(7, 4))
    for cause, color in [("REENTRY", "crimson"), ("MIXED", "gray"),
                         ("PROPAGATION", "seagreen"), ("OTHER", "goldenrod")]:
        sub = c[c.cause == cause]
        ax.plot(sub.horizon_d, sub.cumulative_incidence, label=cause, color=color, lw=2)
    ax.set_xlabel("days after release")
    ax.set_ylabel("cumulative incidence")
    ax.set_title("MECH-6 WS5: competing-risk cumulative incidence (n=125 releases)")
    ax.legend(frameon=False)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(PLOTS / "ws5_cumulative_incidence.png")
    plt.close(fig)


def plot_conditioned_hazard():
    c14 = pd.read_csv(ROOT / "14_STATE_CONDITIONED_HAZARDS.csv")
    piv = c14[c14.cause.isin(["REENTRY", "PROPAGATION"])].pivot_table(
        index="condition", columns=["window_d", "cause"],
        values="p_cause_by_window")
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), sharey=True)
    for k, cause in enumerate(["REENTRY", "PROPAGATION"]):
        sub = piv.xs(cause, level="cause", axis=1)
        sub.T.plot(kind="bar", ax=axes[k], width=0.85, legend=False)
        axes[k].set_title(f"{cause} by window")
        axes[k].set_xlabel("window")
        axes[k].tick_params(axis="x", rotation=45)
    axes[0].set_ylabel("probability of resolution")
    fig.suptitle("MECH-6 WS5: state-conditioned release hazards", y=1.03)
    fig.tight_layout()
    fig.savefig(PLOTS / "ws5_conditioned_hazards.png", bbox_inches="tight")
    plt.close(fig)


def plot_breadth_signatures():
    lat = pd.read_csv(ROOT / "08_BREADTH_TRANSMISSION_LATTICE.csv")
    q7 = lat[lat.question == "Q7_class_signature"]
    piv = q7.pivot_table(index="coordinate", columns="statistic", values="value")
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    horizons = ["median_breadth_tp0", "median_breadth_tp1", "median_breadth_tp3",
                "median_breadth_tp7", "median_breadth_tp14"]
    for cls in piv.index:
        vals = [piv.loc[cls, h] for h in horizons]
        ax.plot([0, 1, 3, 7, 14], vals, marker="o", label=cls, lw=2)
    ax.set_xlabel("days after release")
    ax.set_ylabel("median Top-500 breadth (30D)")
    ax.set_title("MECH-6 WS3: breadth path by outcome class")
    ax.legend(frameon=False)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(PLOTS / "ws3_breadth_signatures.png")
    plt.close(fig)


def plot_breadth_auc():
    lat = pd.read_csv(ROOT / "08_BREADTH_TRANSMISSION_LATTICE.csv")
    q2 = lat[(lat.question == "Q2_best_discriminator") & (lat.statistic == "auc_tp0")]
    q2 = q2.sort_values("value", ascending=True)
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.barh(q2.coordinate, q2.value, color="steelblue")
    ax.axvline(0.5, color="gray", ls="--", lw=1)
    ax.set_xlabel("univariate AUC at release (success vs failure)")
    ax.set_title("MECH-6 WS3: breadth-coordinate discrimination")
    fig.tight_layout()
    fig.savefig(PLOTS / "ws3_breadth_auc.png")
    plt.close(fig)


def plot_sequence_lift():
    s6 = pd.read_csv(ROOT / "06_SEQUENCE_SUBPERIOD_STABILITY.csv")
    top = s6.sort_values("lift", ascending=False).head(10)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    y = np.arange(len(top))[::-1]
    ax.barh(y, top.lift, color="seagreen", alpha=0.85)
    ax.errorbar(top.lift, y, xerr=[top.lift - top.lift_ci5, top.lift_ci95 - top.lift],
                fmt="none", ecolor="black", capsize=3)
    ax.axvline(1.0, color="gray", ls="--", lw=1)
    ax.set_yticks(y)
    ax.set_yticklabels([s[:34] + "..." if len(s) > 34 else s for s in top.seq], fontsize=7)
    ax.set_xlabel("lift vs marginal-product baseline")
    ax.set_title("MECH-6 WS2: top panel micro-state sequences (95% bootstrap CI)")
    fig.tight_layout()
    fig.savefig(PLOTS / "ws2_sequence_lift.png", bbox_inches="tight")
    plt.close(fig)


def plot_termination():
    t15 = pd.read_csv(ROOT / "15_TERMINATION_MICROSEQUENCES.csv")
    cnt = t15.termination_signature.value_counts()
    fig, ax = plt.subplots(figsize=(6, 3.5))
    ax.bar(cnt.index, cnt.values, color="indianred")
    ax.set_ylabel("episodes (n=27 sustained)")
    ax.set_title("MECH-6 WS6: first-decline coordinate at propagation termination")
    ax.tick_params(axis="x", rotation=30)
    fig.tight_layout()
    fig.savefig(PLOTS / "ws6_termination_signatures.png")
    plt.close(fig)


def plot_conditional_heat():
    c16 = pd.read_csv(ROOT / "16_CONDITIONAL_LOCAL_RULE_AUDIT.csv")
    piv = c16.pivot_table(index="condition", columns="seq",
                          values="significant_fdr", aggfunc="max")
    fig, ax = plt.subplots(figsize=(9, 3.5))
    im = ax.imshow(piv.values.astype(float), cmap="Reds", aspect="auto")
    ax.set_xticks(range(len(piv.columns)))
    ax.set_xticklabels([s[:22] for s in piv.columns], rotation=90, fontsize=6)
    ax.set_yticks(range(len(piv.index)))
    ax.set_yticklabels(piv.index, fontsize=7)
    ax.set_title("MECH-6 WS7: sequence occurrence dependence on conditions (FDR sig)")
    fig.colorbar(im, shrink=0.6)
    fig.tight_layout()
    fig.savefig(PLOTS / "ws7_conditional_heat.png", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    plot_cif()
    plot_conditioned_hazard()
    plot_breadth_signatures()
    plot_breadth_auc()
    plot_sequence_lift()
    plot_termination()
    plot_conditional_heat()
    print("plots written:", sorted(p.name for p in PLOTS.glob("*.png")))
