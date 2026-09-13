#!/usr/bin/env python
"""Generate the 7 MECH-12 diagnostic plots."""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "plots"
OUT.mkdir(exist_ok=True)

plt.rcParams.update({"figure.dpi": 120, "font.size": 9,
                     "axes.grid": True, "grid.alpha": 0.3})


def _read(name):
    return pd.read_csv(ROOT / name)


# 1. Full lifecycle: HH vs LL propagation/reentry by age
def plot1():
    df = _read("02_FULL_STATE_LIFECYCLE.csv")
    order = ["AGE_1", "AGE_2_3", "AGE_4_7", "AGE_8_14", "AGE_15_PLUS"]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), sharey=True)
    for ax, cell, title in [
            (axes[0], "HIGH_BREADTH_HIGH_DISP", "HH lifecycle (7D)"),
            (axes[1], "LOW_BREADTH_LOW_DISP", "LL lifecycle (7D)")]:
        g = df[(df["cell"] == cell) & (df["horizon_d"] == 7)]
        g = g.set_index("age_band").reindex(order).dropna()
        x = np.arange(len(g))
        ax.plot(x, g["p_propagate"], "-o", label="propagate")
        ax.plot(x, g["p_reentry"], "-s", label="reentry")
        ax.plot(x, g["p_stay"], "--", label="stay")
        ax.plot(x, g["p_rank_recruitment"], ":", label="rank recruit")
        ax.set_xticks(x)
        ax.set_xticklabels(g.index, rotation=30)
        ax.set_title(title)
        ax.legend(fontsize=8)
    fig.suptitle("MECH-12: full state lifecycle by age", y=1.03)
    fig.tight_layout()
    fig.savefig(OUT / "01_full_lifecycle.png", bbox_inches="tight")
    plt.close(fig)


# 2. Constraint-resolution entropy collapse by age
def plot2():
    df = _read("08_CONSTRAINT_RESOLUTION_ENTROPY.csv")
    ca = df[df["scope"] == "cell_age"].copy()
    order = ["AGE_1", "AGE_2_3", "AGE_4_7", "AGE_8_14", "AGE_15_PLUS"]
    fig, ax = plt.subplots(figsize=(8, 4.2))
    for cell in ca["cell"].unique():
        g = ca[ca["cell"] == cell].set_index("age_band").reindex(order)
        ax.plot(g.index, g["branch_entropy"], "-o", label=cell)
    ax.set_xticklabels(order, rotation=30)
    ax.set_ylabel("branch entropy (bits)")
    ax.set_title("MECH-12: next-cell branch entropy collapses with state age")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "02_entropy_collapse.png", bbox_inches="tight")
    plt.close(fig)


# 3. Waterfall threshold hierarchy
def plot3():
    df = _read("09_WATERFALL_THRESHOLD_HIERARCHY.csv")
    df = df.sort_values("depth_idx")
    fig, ax = plt.subplots(figsize=(9, 4.2))
    x = np.arange(len(df))
    ax.plot(x, df["med_dispersion"], "-o", label="dispersion at activation")
    ax.plot(x, df["med_vol"], "-s", label="vol at activation")
    ax.plot(x, df["med_btc7"], "-^", label="BTC 7D at activation")
    ax2 = ax.twinx()
    ax2.plot(x, df["n_episodes"], "--", color="gray", alpha=0.7,
             label="n episodes")
    ax.set_xticks(x)
    ax.set_xticklabels(df["band"], rotation=60)
    ax.set_ylabel("field intensity at first activation")
    ax2.set_ylabel("n episodes")
    ax.set_title("MECH-12: waterfall as threshold hierarchy "
                 "(deeper bands need stronger field)")
    fig.tight_layout()
    fig.savefig(OUT / "03_waterfall_thresholds.png", bbox_inches="tight")
    plt.close(fig)


# 4. Metastability: dwell vs stationary share
def plot4():
    df = _read("14_METASTABILITY_AUDIT.csv")
    fig, ax = plt.subplots(figsize=(7, 5))
    for _, r in df.iterrows():
        ax.scatter(r["median_dwell_d"], r["stationary_share"], s=140,
                   label=r["cell"])
        ax.annotate(r["verdict"], (r["median_dwell_d"],
                                   r["stationary_share"]),
                    textcoords="offset points", xytext=(8, 6), fontsize=8)
    ax.set_xlabel("median dwell (days)")
    ax.set_ylabel("stationary share")
    ax.set_title("MECH-12: metastability audit")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "04_metastability.png", bbox_inches="tight")
    plt.close(fig)


# 5. Loner field placement
def plot5():
    df = _read("16_LONER_FIELD_PLACEMENT.csv")
    fig, ax = plt.subplots(figsize=(7, 4.2))
    x = np.arange(len(df))
    w = 0.35
    ax.bar(x - w / 2, df["p_HH"], w, label="p(HH)")
    ax.bar(x + w / 2, df["p_LL"], w, label="p(LL)")
    ax.set_xticks(x)
    ax.set_xticklabels(df["loner_class"])
    ax.set_ylabel("share")
    ax.set_title("MECH-12: loner field placement (2x2 cells)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUT / "05_loner_placement.png", bbox_inches="tight")
    plt.close(fig)


# 6. Absolute vs sigma amplitude
def plot6():
    df = _read("17_ABSOLUTE_VS_SIGMA_AMPLITUDE.csv")
    order = ["LOW_SIGMA_LOW_ABS", "LOW_SIGMA_HIGH_ABS",
             "HIGH_SIGMA_LOW_ABS", "HIGH_SIGMA_HIGH_ABS"]
    df = df.set_index("amplitude_cell").reindex(order).reset_index()
    fig, ax = plt.subplots(figsize=(8, 4.2))
    x = np.arange(len(df))
    ax.bar(x, df["p_fwd7_pos"], 0.55, label="P(fwd7>0)")
    ax.plot(x, df["p_reversal_7d"], "-o", color="red",
            label="P(reversal 7d)")
    ax.set_xticks(x)
    ax.set_xticklabels(df["amplitude_cell"], rotation=20)
    ax.set_ylabel("probability")
    ax.set_title("MECH-12: absolute vs sigma amplitude (extreme panel)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUT / "06_abs_vs_sigma.png", bbox_inches="tight")
    plt.close(fig)


# 7. Directional asymmetry
def plot7():
    df = _read("18_DIRECTIONAL_ASYMMETRY_FIELD.csv")
    fig, ax = plt.subplots(figsize=(8, 4.2))
    colors = ["#c44e52" if s == "DOWN" else "#55a868" for s in df["sign"]]
    ax.bar(np.arange(len(df)), df["med_breadth"], 0.6, color=colors)
    ax.set_xticks(np.arange(len(df)))
    ax.set_xticklabels(df["family"], rotation=30)
    ax.set_ylabel("median breadth at event")
    ax.set_title("MECH-12: field breadth by event family "
                 "(red=down, green=up)")
    fig.tight_layout()
    fig.savefig(OUT / "07_directional_asymmetry.png", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    plot1()
    plot2()
    plot3()
    plot4()
    plot5()
    plot6()
    plot7()
    print("[done] 7 plots written")
