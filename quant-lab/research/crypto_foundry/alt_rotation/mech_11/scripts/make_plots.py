#!/usr/bin/env python
"""MECH-11 plots - temporal field physics visual summary."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "plots"
OUT.mkdir(exist_ok=True)
plt.rcParams.update({"figure.dpi": 110, "font.size": 9})

HORIZONS = [1, 2, 3, 5, 7, 10, 14, 21, 30]


def p1_delivery_lattice():
    d = pd.read_csv(ROOT / "02_MULTI_SCALE_DELIVERY_LATTICE.csv")
    fig, ax = plt.subplots(2, 2, figsize=(11, 7))
    cells = ["HIGH_BREADTH_HIGH_DISP", "HIGH_BREADTH_LOW_DISP",
             "LOW_BREADTH_HIGH_DISP", "LOW_BREADTH_LOW_DISP"]
    short = {"HIGH_BREADTH_HIGH_DISP": "HH", "HIGH_BREADTH_LOW_DISP": "HL",
             "LOW_BREADTH_HIGH_DISP": "LH", "LOW_BREADTH_LOW_DISP": "LL"}
    for k, cell in enumerate(cells):
        a = ax[k // 2][k % 2]
        sub = d[d["cell"] == cell]
        for clock in ["STATE_EXIT", "PROPAGATION", "REENTRY"]:
            s = sub[sub["clock"] == clock]
            if not len(s):
                continue
            y = [s[f"p_by_{h}d"].mean() for h in HORIZONS]
            a.plot(HORIZONS, y, marker="o", ms=3, label=clock)
        a.set_title(short[cell])
        a.set_xlabel("horizon (d)")
        a.set_ylim(0, 1.05)
        a.legend(fontsize=7)
    fig.suptitle("Multi-scale delivery lattice: P(event within h) by cell")
    fig.tight_layout()
    fig.savefig(OUT / "01_delivery_lattice.png")
    plt.close(fig)


def p2_sequence_grammar():
    d = pd.read_csv(ROOT / "03_SEQUENCE_GRAMMAR.csv").head(12)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.barh(range(len(d)), d["count"], color="#4C72B0")
    ax.set_yticks(range(len(d)))
    ax.set_yticklabels([s.replace("->", "→") for s in d["sequence"]],
                       fontsize=6.5)
    ax.invert_yaxis()
    ax.set_xlabel("count")
    ax.set_title("Sequence grammar: atom ordering before 7D propagation")
    fig.tight_layout()
    fig.savefig(OUT / "02_sequence_grammar.png")
    plt.close(fig)


def p3_competing_risk():
    d = pd.read_csv(ROOT / "05_COMPETING_RISK_CLOCKS.csv")
    hh = d[d["cell"] == "HIGH_BREADTH_HIGH_DISP"].copy()
    fig, ax = plt.subplots(figsize=(8, 5))
    order = ["AGE_1", "AGE_2_3", "AGE_4_7", "AGE_8_14", "AGE_15_PLUS"]
    hh["age_band"] = pd.Categorical(hh["age_band"], order, ordered=True)
    hh = hh.sort_values("age_band")
    ax.plot(range(len(hh)), hh["ci_PROPAGATION_30d"], marker="o",
            label="propagation CI 30d")
    ax.plot(range(len(hh)), hh["ci_REENTRY_30d"], marker="o",
            label="reentry CI 30d")
    ax.set_xticks(range(len(hh)))
    ax.set_xticklabels(hh["age_band"], fontsize=7)
    ax.legend()
    ax.set_title("HH competing-risk: probability mass migrates reentry → prop")
    fig.tight_layout()
    fig.savefig(OUT / "03_competing_risk.png")
    plt.close(fig)


def p4_perturbation_amplitude():
    d = pd.read_csv(ROOT / "06_PERTURBATION_AMPLITUDE.csv")
    fig, ax = plt.subplots(figsize=(9, 5))
    for p in d["perturbation"].unique():
        s = d[d["perturbation"] == p].sort_values("amplitude")
        ax.plot([0, 1, 2], s["p_fwd7_prop"], marker="o", label=p, ms=4)
    ax.set_xticks([0, 1, 2])
    ax.set_xticklabels(["SMALL", "MEDIUM", "LARGE"])
    ax.set_ylabel("P(fwd7 propagation)")
    ax.legend(fontsize=7)
    ax.set_title("Perturbation amplitude vs propagation response")
    fig.tight_layout()
    fig.savefig(OUT / "04_perturbation_amplitude.png")
    plt.close(fig)


def p5_propagation_radius():
    d = pd.read_csv(ROOT / "07_PROPAGATION_RADIUS.csv")
    fig, ax = plt.subplots(figsize=(7, 4))
    for _, r in d.iterrows():
        ax.bar([r["event_type"]], [r["n_bands_affected_d7"]],
               label=f"{r['event_type']} → {r['verdict']}")
    ax.set_ylabel("bands affected by +7d")
    ax.set_title("Propagation radius (rank bands, +7d)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "05_propagation_radius.png")
    plt.close(fig)


def p6_loner_context():
    d = pd.read_csv(ROOT / "11_TRUE_FALSE_LONER_FIELD_CONTEXT.csv")
    fig, ax = plt.subplots(1, 3, figsize=(11, 3.5))
    for k, c in enumerate(["med_top500_breadth_30d",
                           "med_top500_dispersion_30d", "p_cell_HH"]):
        ax[k].bar(d["loner_class"], d[c], color=["#C44E52", "#55A868"])
        ax[k].set_title(c.replace("med_", ""))
        ax[k].tick_params(axis="x", rotation=15)
    fig.suptitle("True vs false loner field context")
    fig.tight_layout()
    fig.savefig(OUT / "06_loner_context.png")
    plt.close(fig)


def p7_health_transitions():
    d = pd.read_csv(ROOT / "14_HEALTH_TRANSITION_LATTICE.csv")
    prd = d[d["t0_state"] == "PRICE_RECOVERY_RANK_DECAY"]
    fig, ax = plt.subplots(figsize=(8, 5))
    for dest in ["p_PRICE_UP_RANK_UP", "p_PRICE_UP_RANK_DOWN",
                 "p_PRICE_DOWN_RANK_DOWN"]:
        ax.plot(prd["horizon_d"], prd[dest], marker="o", ms=4, label=dest)
    ax.set_xlabel("horizon (d)")
    ax.set_ylabel("transition probability")
    ax.legend(fontsize=7)
    ax.set_title("PRICE_RECOVERY_RANK_DECAY forward paths")
    fig.tight_layout()
    fig.savefig(OUT / "07_health_transitions.png")
    plt.close(fig)


if __name__ == "__main__":
    p1_delivery_lattice()
    p2_sequence_grammar()
    p3_competing_risk()
    p4_perturbation_amplitude()
    p5_propagation_radius()
    p6_loner_context()
    p7_health_transitions()
    print("[plots] done", flush=True)
