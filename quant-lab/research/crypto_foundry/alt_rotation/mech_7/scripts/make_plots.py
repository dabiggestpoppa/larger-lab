#!/usr/bin/env python
"""MECH-7 plots: 2x2 plane, family reversal geometry, lifecycle dwell,
first-divergence lags, rank bridge, sequence atlas lifts."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT
PLOTS = ROOT / "plots"
PLOTS.mkdir(exist_ok=True)

plt.rcParams.update({"figure.dpi": 110, "savefig.bbox": "tight"})


def p1_family_reversal():
    fam = pd.read_csv(OUT / "_FAMILY_SUMMARY.csv")
    fam = fam[fam["family"].isin([
        "ISOLATED_DOWNSIDE_EXTREME", "LOCAL_CLUSTER_DOWNSIDE",
        "BAND_BROAD_UPSIDE", "MULTI_BAND_UPSIDE", "ISOLATED_UPSIDE",
        "COORDINATED_DOWNSIDE"])].sort_values("reversal_rate")
    fig, ax = plt.subplots(figsize=(9, 5))
    x = np.arange(len(fam))
    ax.barh(x, fam["reversal_rate"], color="#4C72B0")
    ax.set_yticks(x)
    ax.set_yticklabels(fam["family"])
    ax.axvline(0.5, ls="--", c="grey", lw=1)
    ax.set_xlabel("7D reversal rate (sign flip)")
    ax.set_title("MECH-7 event families — 7D reversal geometry (LF2 parity)")
    for i, (n, r) in enumerate(zip(fam["n_events"], fam["reversal_rate"])):
        ax.text(r + 0.01, i, f"n={int(n):,}", va="center", fontsize=8)
    fig.savefig(PLOTS / "01_family_reversal_geometry.png")
    plt.close(fig)


def p2_2x2_plane():
    plane = pd.read_csv(OUT / "06_BREADTH_DISPERSION_2X2.csv")
    cells = ["LOW_BREADTH_LOW_DISP", "LOW_BREADTH_HIGH_DISP",
             "HIGH_BREADTH_LOW_DISP", "HIGH_BREADTH_HIGH_DISP"]
    plane = plane.set_index("cell").reindex(cells)
    fig, ax = plt.subplots(figsize=(8, 6))
    im = ax.imshow(plane[["prop7"]].values.reshape(2, 2),
                   cmap="RdYlBu", vmin=0, vmax=0.6, aspect="auto")
    ax.set_xticks([0, 1]); ax.set_xticklabels(["DISP_LO", "DISP_HI"])
    ax.set_yticks([0, 1]); ax.set_yticklabels(["BRD_HI", "BRD_LO"])
    ax.set_title("BREADTH x DISPERSION 2x2 — P(propagation within 7D)")
    for i in range(2):
        for j in range(2):
            cell = cells[i * 2 + j]
            row = plane.loc[cell]
            ax.text(j, i, f"{row['prop7']:.2f}\nn={int(row['n_days'])}\ndwell={int(row['n_episodes'])}",
                    ha="center", va="center", fontsize=10)
    plt.colorbar(im, ax=ax)
    fig.savefig(PLOTS / "02_breadth_dispersion_2x2.png")
    plt.close(fig)


def p3_lifecycle_dwell():
    life = pd.read_csv(OUT / "08_HIGH_BRD_HIGH_DISP_LIFECYCLE.csv")
    fig, ax = plt.subplots(figsize=(10, 4))
    ent = life[life["dimension"] == "entry_order"]
    ex = life[life["dimension"] == "exit_order"]
    ax.bar(np.arange(len(ent)) - 0.2, ent["median_dwell_d"], width=0.4,
           label="entry order", color="#55A868")
    ax.bar(np.arange(len(ex)) + 0.2, ex["median_dwell_d"], width=0.4,
           label="exit order", color="#C44E52")
    ax.set_xticks(np.arange(max(len(ent), len(ex))))
    labels = list(ent["path"]) + [""] * (max(len(ent), len(ex)) - len(ent))
    ax.set_xticklabels(labels, rotation=30, ha="right")
    ax.set_ylabel("median dwell (days)")
    ax.set_title("HIGH_BRD_HIGH_DISP lifecycle — median dwell by entry/exit order")
    ax.legend()
    fig.savefig(PLOTS / "03_hh_lifecycle_dwell.png")
    plt.close(fig)


def p4_first_divergence():
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    for ax, f, title in [
            (axes[0], "16_FIRST_DIVERGENCE_DOWN_REVERSE_VS_CONTINUE.csv",
             "Isolated downside — reversal vs continuation"),
            (axes[1], "15_FIRST_DIVERGENCE_UP_CONT_VS_GIVEBACK.csv",
             "Coordinated upside — continuation vs giveback")]:
        df = pd.read_csv(OUT / f)
        if len(df) == 0:
            continue
        df = df.sort_values("lag_d")
        for var in ["top500_breadth_30d", "top500_dispersion_30d", "btc_return_30d"]:
            sub = df[df["variable"] == var]
            if len(sub) == 0:
                continue
            ax.plot(sub["lag_d"], sub["diff"], marker="o", ms=4, label=var)
        ax.axhline(0, c="grey", lw=1)
        ax.axvline(0, c="grey", lw=0.8, ls="--")
        ax.set_xlabel("lag (days around event)")
        ax.set_ylabel("median difference (outcome A - outcome B)")
        ax.set_title(title)
        ax.legend(fontsize=8)
    fig.savefig(PLOTS / "04_first_divergence_lags.png")
    plt.close(fig)


def p5_rank_bridge():
    bridge = pd.read_csv(OUT / "14_RANK_DETERIORATION_SHOCK_BRIDGE.csv")
    fig, ax = plt.subplots(figsize=(8, 5))
    order = ["RANK_DETERIORATING", "RANK_STABLE", "RANK_IMPROVING"]
    bridge = bridge.set_index("rank_state").reindex(order).dropna(how="all")
    x = np.arange(len(bridge))
    ax.bar(x - 0.2, bridge["reversal_rate"], width=0.4, label="reversal rate", color="#55A868")
    ax.bar(x + 0.2, bridge["med_fwd7_sigma"], width=0.4, label="median fwd7 sigma", color="#4C72B0")
    ax.set_xticks(x); ax.set_xticklabels(bridge.index, rotation=15)
    ax.set_title("Isolated downside by pre-event rank state (WS9 bridge)")
    ax.legend()
    for i, n in enumerate(bridge["n_events"]):
        ax.text(i - 0.2, 0.02, f"n={int(n)}", fontsize=8, ha="center")
    fig.savefig(PLOTS / "05_rank_bridge.png")
    plt.close(fig)


def p6_sequence_lifts():
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    for f, title, ax in [("12_COORDINATED_UP_SEQUENCE_ATLAS.csv",
                          "Coordinated-up sequence atlas", axes[0]),
                         ("13_ISOLATED_DOWN_SEQUENCE_ATLAS.csv",
                          "Isolated-down sequence atlas", axes[1])]:
        df = pd.read_csv(OUT / f)
        if len(df) == 0:
            ax.text(0.5, 0.5, "no sequences ≥50 days", ha="center")
            ax.set_title(title)
            continue
        df = df.sort_values("lift").tail(10)
        ax.barh(np.arange(len(df)), df["lift"], color="#4C72B0")
        ax.set_yticks(np.arange(len(df)))
        ax.set_yticklabels(df["sequence"], fontsize=7)
        ax.axvline(1.0, ls="--", c="grey", lw=1)
        ax.set_xlabel("lift vs event-date baseline")
        ax.set_title(title)
    fig.savefig(PLOTS / "06_sequence_atlas_lifts.png")
    plt.close(fig)


def p7_breadth_composition():
    comp = pd.read_csv(OUT / "10_BREADTH_COMPOSITION.csv")
    fig, ax = plt.subplots(figsize=(8, 5))
    order = ["R1_25", "R26_100", "R101_250", "R251_500"]
    comp = comp.set_index("layer").reindex(order)
    x = np.arange(len(comp))
    ax.bar(x - 0.2, comp["med_breadth_7d"], width=0.4, label="median 7D breadth", color="#4C72B0")
    ax.bar(x + 0.2, comp["share_of_top500_breadth"], width=0.4, label="share of top500 breadth", color="#DD8452")
    ax.set_xticks(x); ax.set_xticklabels(comp.index)
    ax.set_title("Breadth internal composition by rank layer")
    ax.legend()
    fig.savefig(PLOTS / "07_breadth_composition.png")
    plt.close(fig)


if __name__ == "__main__":
    p1_family_reversal()
    p2_2x2_plane()
    p3_lifecycle_dwell()
    p4_first_divergence()
    p5_rank_bridge()
    p6_sequence_lifts()
    p7_breadth_composition()
    print("plots done:", sorted(p.name for p in PLOTS.glob("*.png")))
