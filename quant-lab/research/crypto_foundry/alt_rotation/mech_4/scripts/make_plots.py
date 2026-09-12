#!/usr/bin/env python
"""Generate MECH-4 plots (plots/ dir). Terrain research only."""
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "plots"
OUT.mkdir(exist_ok=True)
sys.path.insert(0, str(ROOT / "scripts"))
import alt_mech_4_analysis as A

plt.rcParams.update({"font.size": 8, "axes.titlesize": 9, "figure.dpi": 110})


import pickle

def gsum():
    return pickle.load(open(ROOT / "_cache_daily.pkl", "rb"))[0]


daily = gsum()
ledger = pd.read_parquet(ROOT / "04_RELEASE_EVENT_LEDGER.parquet")

# ---- 1. Release destination / staged patterns (bar) ----
def p1():
    pc = ledger.staged_pattern.value_counts()
    fig, ax = plt.subplots(figsize=(5.5, 3.2))
    pc.plot.bar(ax=ax, color="#4C72B0")
    ax.set_title("Concentration release staged patterns (n=125)")
    ax.set_ylabel("n releases")
    ax.tick_params(axis="x", rotation=30)
    fig.tight_layout(); fig.savefig(OUT / "01_release_patterns.png"); plt.close(fig)

# ---- 2. Hierarchical gates: delta_logloss + AUC ----
def p2():
    g = pd.read_csv(ROOT / "06_ESCAPE_VS_SNAPBACK.csv")
    fig, ax = plt.subplots(figsize=(6, 3.2))
    x = np.arange(len(g))
    ax.bar(x - 0.2, g.delta_logloss, 0.35, label="delta log-loss vs base", color="#4878D0")
    ax2 = ax.twinx()
    ax2.plot(x, g.auc, "o-", color="#D65F5F", label="AUC")
    ax.axhline(0, color="k", lw=0.8)
    ax.set_xticks(x); ax.set_xticklabels(g.gate, rotation=20, ha="right")
    ax.set_ylabel("delta log-loss"); ax2.set_ylabel("AUC")
    ax2.set_ylim(0, 1)
    h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, fontsize=7, loc="best")
    ax.set_title("Hierarchical release gates")
    fig.tight_layout(); fig.savefig(OUT / "02_release_gates.png"); plt.close(fig)

# ---- 3. Duration-structured escape hazard ----
def p3():
    t1 = pd.read_csv(ROOT / "12b_ESCAPE_BY_AGE.csv")
    t1["lo"] = t1.age_bin.str.split("-", expand=True)[0].astype(int)
    t1 = t1.sort_values("lo")
    fig, ax = plt.subplots(figsize=(5.5, 3.2))
    ax.plot(np.arange(len(t1)), t1.p_exit_within7d, "o-", color="#099DD9")
    ax.set_xticks(np.arange(len(t1))); ax.set_xticklabels(t1.age_bin)
    ax.set_title("P(escape concentration within 7D) by episode age")
    ax.set_ylabel("P(exit within 7D)")
    fig.tight_layout(); fig.savefig(OUT / "03_duration_escape_hazard.png"); plt.close(fig)

# ---- 4. First-move vs delivery ----
def p4():
    d = pd.read_csv(ROOT / "33_FIRST_MOVE_TRUE_DELIVERY.csv")
    vc = d.classification.value_counts()
    cols = {"IMMEDIATE_DELIVERY": "#2E8B57", "RETEST_RELOAD": "#1E90FF",
            "FAILED_IGNITION": "#FFA500", "FULL_FAILURE": "#D65F5F"}
    fig, ax = plt.subplots(figsize=(5.5, 3.2))
    for k, c in cols.items():
        if k in vc:
            ax.bar(k, vc[k], color=c, label=k)
    ax.set_title("First move vs true delivery (n=125)")
    ax.set_ylabel("n releases")
    ax.tick_params(axis="x", rotation=20)
    fig.tight_layout(); fig.savefig(OUT / "04_first_move_delivery.png"); plt.close(fig)

# ---- 5. Second-order route map (TOP transitions) ----
def p5():
    m = pd.read_csv(ROOT / "35_SECOND_ORDER_ROUTE_MAP.csv")
    vc = m.state_sequence.value_counts().head(8)
    fig, ax = plt.subplots(figsize=(6, 3.4))
    vc.plot.barh(ax=ax, color="#8C6DB1")
    ax.set_title("Most common second-order route sequences")
    ax.set_xlabel("count")
    fig.tight_layout(); fig.savefig(OUT / "05_second_order_routes.png"); plt.close(fig)

# ---- 6. Accumulation-like fingerprint ----
def p6():
    d = pd.read_csv(ROOT / "34_ACCUMULATION_LIKE_FINGERPRINT.csv")
    fig, ax = plt.subplots(figsize=(5.5, 3.2))
    stable = d[d.stable_outcome]
    unst = d[~d.stable_outcome]
    ax.scatter(unst.absorption_like_score, [0] * len(unst), alpha=0.35, marker="x",
               color="#D65F5F", label="not-propagation")
    ax.scatter(stable.absorption_like_score, [1] * len(stable), alpha=0.6,
               color="#2E8B57", label="propagation")
    ax.set_yticks([0, 1]); ax.set_yticklabels(["not-prop", "prop"])
    ax.set_xlabel("absorption-like score")
    ax.set_title("Absorption-like fingerprint vs propagation outcome")
    ax.legend(fontsize=7, loc="best")
    fig.tight_layout(); fig.savefig(OUT / "06_accumulation_like.png"); plt.close(fig)

# ---- 7. Volatility lifecycle ----
def p7():
    d = pd.read_csv(ROOT / "40_VOLATILITY_LIFECYCLE_ROLE.csv")
    fig, ax = plt.subplots(figsize=(6.5, 3.2))
    ordered = d.sort_values("pct_vol_high_day")
    ax.barh(ordered.stage, ordered.pct_vol_high_day, color="#4472C4")
    ax.axvline(0.5, color="k", ls="--", lw=0.8)
    ax.set_xlabel("share of days classified VOL_HIGH")
    ax.set_title("Volatility role by life-cycle stage")
    fig.tight_layout(); fig.savefig(OUT / "07_volatility_lifecycle.png"); plt.close(fig)

# ---- 8. Bifurcation boundary ----
def p8():
    d = pd.read_csv(ROOT / "39_BIFURCATION_STATE_SPACE_AUDIT.csv")
    fig, ax = plt.subplots(figsize=(5.5, 3.2))
    ax.plot(d.pred_prob_bin, d.outcome_rate, "o-", color="#D1495B")
    ax.set_xlabel("predicted-propagation bin (1=low..5=high)")
    ax.set_ylabel("observed propagation rate")
    ax.set_title("Bifurcation-style boundary in the G3 projection")
    for _, r in d.iterrows():
        if r.pred_prob_bin in (4, 5):
            ax.annotate(f"{r.outcome_rate:.2f}", (r.pred_prob_bin, r.outcome_rate),
                        textcoords="offset points", xytext=(0, 6), ha="center")
    fig.tight_layout(); fig.savefig(OUT / "08_bifurcation_boundary.png"); plt.close(fig)

# ---- 9. Temporal delivery lattice medians ----
def p9():
    t = pd.read_csv(ROOT / "31_TEMPORAL_DELIVERY_LATTICE.csv")
    tau_cols = ["tau_release_d", "tau_activate_d", "tau_broaden_d", "tau_peak_d",
                "tau_hold_d", "tau_decay_d", "tau_total_d"]
    med = t[tau_cols].median()
    fig, ax = plt.subplots(figsize=(6, 3.2))
    ax.bar(range(len(tau_cols)), med.values, color="#7A68A6")
    ax.set_xticks(range(len(tau_cols))); ax.set_xticklabels(tau_cols, rotation=25, ha="right")
    ax.set_ylabel("median days")
    ax.set_title("Temporal delivery lattice (median tau per release)")
    fig.tight_layout(); fig.savefig(OUT / "09_temporal_delivery.png"); plt.close(fig)

# ---- 10. Route latency matrix heat ----
def p10():
    m = pd.read_csv(ROOT / "36_ROUTE_LATENCY_MATRIX.csv").head(12)
    fig, ax = plt.subplots(figsize=(6.5, 4.0))
    piv = m.pivot_table(index="route1", columns="route2", values="prob", aggfunc="sum")
    im = ax.imshow(piv.values, cmap="Blues", aspect="auto")
    ax.set_xticks(range(piv.shape[1])); ax.set_xticklabels(piv.columns, rotation=40, ha="right", fontsize=6)
    ax.set_yticks(range(piv.shape[0])); ax.set_yticklabels(piv.index, fontsize=6)
    for i in range(piv.shape[0]):
        for j in range(piv.shape[1]):
            v = piv.values[i, j]
            if v > 0:
                ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=5)
    ax.set_title("Second-order route transition probability")
    fig.colorbar(im, fraction=0.03)
    fig.tight_layout(); fig.savefig(OUT / "10_route_latency.png"); plt.close(fig)


for f in [p1, p2, p3, p4, p5, p6, p7, p8, p9, p10]:
    f()
print("plots written to", OUT)