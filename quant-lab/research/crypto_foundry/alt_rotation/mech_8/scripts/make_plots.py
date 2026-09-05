#!/usr/bin/env python
"""MECH-8 plots."""
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


def _fmt(x):
    return f"{x:.3f}"


# P1: effect curves (reversal vs continuation) for key variables
e4 = pd.read_csv(ROOT / "04_ISOLATED_DOWN_EFFECT_CURVES.csv")
vars4 = ["top500_breadth_30d", "top500_dispersion_30d", "btc_return_30d",
         "rank_depth_rel", "med_ret30_201_500", "top3_share"]
fig, axes = plt.subplots(2, 3, figsize=(15, 8))
for ax, var in zip(axes.ravel(), vars4):
    g = e4[e4["variable"] == var].sort_values("lag_d")
    if len(g) == 0:
        ax.set_title(f"{var} (no data)")
        continue
    ax.axhline(0, color="grey", lw=0.6)
    ax.plot(g["lag_d"], g["diff"], "-o", ms=3, label="med(rev) - med(cont)")
    sig = g[g["p_fdr"] < 0.1]
    ax.scatter(sig["lag_d"], sig["diff"], s=40, facecolors="none",
               edgecolors="red", label="FDR q<0.1")
    ax.set_title(var)
    ax.axvline(0, color="black", lw=0.5, ls=":")
    ax.legend(fontsize=7)
fig.suptitle("MECH-8 WS2: reversal vs continuation effect curves (-30..+14D)")
fig.tight_layout()
fig.savefig(OUT / "p1_effect_curves.png")
plt.close(fig)

# P2: 4-state transition matrix heatmap
t6 = pd.read_csv(ROOT / "06_BRD_DISP_4STATE_TRANSITION_MATRIX.csv")
cells = ["LOW_BREADTH_LOW_DISP", "LOW_BREADTH_HIGH_DISP",
         "HIGH_BREADTH_LOW_DISP", "HIGH_BREADTH_HIGH_DISP"]
M = np.full((4, 4), np.nan)
for i, f in enumerate(cells):
    for j, t in enumerate(cells):
        row = t6[(t6["from"] == f) & (t6["to"] == t)]
        if len(row):
            M[i, j] = row["p"].iloc[0]
fig, ax = plt.subplots(figsize=(7, 6))
im = ax.imshow(M, cmap="Blues", vmin=0, vmax=1)
ax.set_xticks(range(4), [c.replace("_", " ") for c in cells], rotation=30, ha="right")
ax.set_yticks(range(4), [c.replace("_", " ") for c in cells])
for i in range(4):
    for j in range(4):
        if M[i, j] == M[i, j]:
            ax.text(j, i, _fmt(M[i, j]), ha="center", va="center",
                    color="white" if M[i, j] > 0.5 else "black")
ax.set_title("Breadth×dispersion 4-state daily transition probabilities")
fig.colorbar(im)
fig.tight_layout()
fig.savefig(OUT / "p2_transition_matrix.png")
plt.close(fig)

# P3: state age — P(leave) by cell and age bucket
a7 = pd.read_csv(ROOT / "07_BRD_DISP_STATE_AGE.csv")
order = {"DAY_1": 0, "DAY_2_3": 1, "DAY_4_7": 2, "DAY_8_14": 3, "DAY_15_PLUS": 4}
a7["_o"] = a7["age_bucket"].map(order)
fig, ax = plt.subplots(figsize=(10, 5))
for cell, g in a7.groupby("cell"):
    g = g.sort_values("_o")
    ax.plot(g["age_bucket"], g["p_leave"], "-o", ms=4, label=cell.replace("_", " "))
ax.set_xlabel("state age bucket")
ax.set_ylabel("P(leave state next day)")
ax.set_title("State age / maturity: probability of leaving by cell")
ax.legend(fontsize=8)
fig.tight_layout()
fig.savefig(OUT / "p3_state_age.png")
plt.close(fig)

# P4: HH lifecycle — dwell distribution + entry/exit orders
l8 = pd.read_csv(ROOT / "08_HH_FULL_LIFECYCLE.csv")
fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
for ax, dim in zip(axes, ["entry_order", "exit_order"]):
    sub = l8[l8["dimension"] == dim]
    if len(sub):
        sub = sub.sort_values("n_episodes", ascending=False)
        ax.bar(sub["path"], sub["n_episodes"], color="steelblue")
        ax.set_title(f"HH {dim}")
        ax.set_ylabel("n episodes")
        ax.tick_params(axis="x", rotation=30)
fig.suptitle("MECH-8 WS5: HH lifecycle entry/exit choreography")
fig.tight_layout()
fig.savefig(OUT / "p4_hh_lifecycle.png")
plt.close(fig)

# P5: price-rank health matrix (stacked)
m13 = pd.read_csv(ROOT / "13_PRICE_RANK_HEALTH_MATRIX.csv")
m13 = m13[m13["cross_state"] != "TOTAL"]
fig, ax = plt.subplots(figsize=(9, 5))
piv = m13.pivot(index="pre_rank_state", columns="cross_state", values="pct").fillna(0)
piv = piv[["PRICE_RECOVERY_RANK_RECOVERY", "PRICE_RECOVERY_RANK_DECAY",
           "PRICE_DECAY_RANK_RECOVERY", "PRICE_DECAY_RANK_DECAY"]]
piv.plot(kind="bar", stacked=True, ax=ax, color=["#2ca02c", "#98df8a", "#ff9896", "#d62728"])
ax.set_ylabel("share")
ax.set_title("Rank health × price recovery cross states (isolated downside)")
ax.legend(fontsize=7)
fig.tight_layout()
fig.savefig(OUT / "p5_price_rank_health.png")
plt.close(fig)

# P6: SHMC vs SHHM field context
s17 = pd.read_csv(ROOT / "17_SHMC_SHHM_FIELD_RECHECK.csv")
if len(s17) == 2:
    fig, axes = plt.subplots(1, 3, figsize=(13, 4))
    for ax, col, title in [(axes[0], "med_breadth30", "median breadth30"),
                           (axes[1], "med_disp30", "median dispersion30"),
                           (axes[2], "reversal_rate", "reversal rate")]:
        ax.bar(s17["group"], s17[col], color=["#d62728", "#2ca02c"])
        ax.set_title(title)
    fig.suptitle("MECH-8 WS11: SHMC vs SHHM field recheck")
    fig.tight_layout()
    fig.savefig(OUT / "p6_shmc_shhm.png")
    plt.close(fig)

# P7: breadth architecture day-level features (entropy vs breadth level)
a11 = pd.read_csv(ROOT / "11_BREADTH_ARCHITECTURE_DAILY_FEATURES.csv")
if len(a11):
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(a11["top500_breadth_30d"], a11["entropy_layers"], s=8, alpha=0.5)
    ax.set_xlabel("breadth30 level")
    ax.set_ylabel("layer entropy of positive movers")
    ax.set_title("Breadth architecture: layer entropy vs breadth level (high-breadth days)")
    fig.tight_layout()
    fig.savefig(OUT / "p7_breadth_architecture.png")
    plt.close(fig)

print("[plots] done")
