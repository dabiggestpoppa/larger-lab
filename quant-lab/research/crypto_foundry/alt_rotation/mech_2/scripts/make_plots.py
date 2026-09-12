#!/usr/bin/env python
"""Generate the MECH-2 plot set from final artifacts. Read-only over artifacts."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "plots"
OUT.mkdir(exist_ok=True)


def save(fig, name):
    fig.tight_layout()
    fig.savefig(OUT / name, dpi=130, bbox_inches="tight")
    plt.close(fig)
    print("wrote", name)


# 1. Capital propagation: chain-flow lead-lag heatmap (E)
e = pd.read_csv(ROOT / "08_CHAIN_FLOW_PROPAGATION.csv")
piv = e.pivot_table(index="link", columns="chain", values="corr",
                    aggfunc="mean", fill_value=np.nan)
fig, ax = plt.subplots(figsize=(11, 4.5))
im = ax.imshow(piv.values, cmap="RdYlGn", vmin=-0.3, vmax=0.3, aspect="auto")
ax.set_xticks(range(len(piv.columns)), piv.columns, rotation=60, ha="right", fontsize=8)
ax.set_yticks(range(len(piv.index)), piv.index, fontsize=8)
ax.set_title("Chain-flow lead/lag: mean corr by link x chain (E)")
fig.colorbar(im, ax=ax, label="mean corr")
save(fig, "01_capital_propagation_chain_flow.png")

# 2. Hierarchy: variance decomposition (H)
h = pd.read_csv(ROOT / "10_HIERARCHY_MAP.csv")
h = h.sort_values("n_member_days", ascending=False).head(15)
fig, ax = plt.subplots(figsize=(9, 6))
x = np.arange(len(h))
b = np.zeros(len(h))
cols = ["share_global", "share_chain_incremental", "share_sector_incremental", "share_idio"]
labels = ["global", "chain+", "sector+", "idiosyncratic"]
colors = ["#c44e52", "#ddaa33", "#4c72b0", "#8c8c8c"]
for c, l, cl in zip(cols, labels, colors):
    ax.barh(x, h[c].fillna(0), left=b, label=l, color=cl, height=0.7)
    b += h[c].fillna(0).values
ax.set_yticks(x, h["name"].str[:24])
ax.invert_yaxis()
ax.set_xlabel("share of cluster variance")
ax.set_title("Reference-frame hierarchy: variance decomposition (H)")
ax.legend(loc="lower right", fontsize=8)
save(fig, "02_hierarchy.png")

# 3. Rank migration: precursor event-vs-control by band (C)
c = pd.read_csv(ROOT / "06_RANK_MIGRATION_PRECURSORS.csv")
g = c.groupby("from_band").agg(
    succ=("success_rate_14d", "mean"),
    ev=("ev_rank_velocity_7d_win7", "mean"),
    ctrl=("ctrl_rank_velocity_7d_win7", "mean")).reindex(
    ["11-25", "26-50", "51-100", "101-200", "201-300", "301-500"])
fig, ax = plt.subplots(figsize=(9, 4.5))
xx = np.arange(len(g))
ax.bar(xx - 0.18, g["ev"], 0.36, label="event (pre-migration)", color="#4c72b0")
ax.bar(xx + 0.18, g["ctrl"], 0.36, label="control", color="#d3d3d3")
ax.set_xticks(xx, g.index)
ax.axhline(0, color="k", lw=0.6)
ax.set_ylabel("median rank velocity 7d (win7)")
ax.set_title("Rank-migration precursors: event vs control velocity (C)")
ax.legend()
ax2 = ax.twinx()
ax2.plot(xx, g["succ"], "o-", color="#c44e52", label="success rate 14d")
ax2.set_ylabel("success rate", color="#c44e52")
ax2.tick_params(axis="y", labelcolor="#c44e52")
save(fig, "03_rank_migration_precursors.png")

# 4. Sector expansion: same-day vs delayed peer corr (D)
d = pd.read_csv(ROOT / "07_SECTOR_PROPAGATION.csv")
cols = ["same_day_corr", "delay1_corr", "delay3_corr", "delay7_corr", "delay14_corr"]
med = d[cols].median()
fig, ax = plt.subplots(figsize=(7.5, 4.5))
ax.bar(range(len(cols)), med.values, color="#4c72b0")
ax.set_xticks(range(len(cols)), ["same day", "+1d", "+3d", "+7d", "+14d"])
ax.axhline(0, color="k", lw=0.6)
ax.set_ylabel("median peer corr (leader leads)")
ax.set_title("Sector propagation: leader->peer confirmation timing (D)")
for i, v in enumerate(med.values):
    ax.text(i, v + 0.008, f"{v:.3f}", ha="center", fontsize=9)
save(fig, "04_sector_expansion_timing.png")

# 5. State transitions: transition matrix heatmap (15)
t = pd.read_csv(ROOT / "15_DYNAMICAL_STATE_TRANSITIONS.csv", index_col=0)
t = t.reindex(index=t.index, columns=t.index).fillna(0)
trow = t.div(t.sum(axis=1).replace(0, np.nan), axis=0)
fig, ax = plt.subplots(figsize=(9.5, 8))
im = ax.imshow(trow.values, cmap="viridis", aspect="auto")
ax.set_xticks(range(len(trow.columns)), [s[:12] for s in trow.columns], rotation=60, ha="right", fontsize=8)
ax.set_yticks(range(len(trow.index)), [s[:12] for s in trow.index], fontsize=8)
ax.set_title("Daily routing-state transition probabilities")
fig.colorbar(im, ax=ax, label="P(next | current)")
save(fig, "05_state_transitions.png")

# 6. Network topology: band + sector graph adjacency (14)
tp = json.load(open(ROOT / "14_TOPOLOGY_REPORT.json"))
fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
for ax, (title, data, thr) in zip(axes, [
    ("Band graph (|corr| >= 0.8)", tp["band_graph"], 0.8),
    ("Sector graph (|corr| >= 0.5)", tp["sector_graph"], 0.5)]):
    ax.set_title(f"{title}  density={data['density']}")
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_xlim(-0.05, 1.05); ax.set_ylim(-0.05, 1.05)
    n_comp = len(data.get("connected_components", [1]))
    n_nodes = data.get("n_sectors", len(data.get("nodes", [])))
    ax.text(0.5, 0.5, f"{n_comp} component(s)\n{n_nodes} nodes",
            ha="center", va="center", fontsize=12)
save(fig, "06_network_topology.png")

# 7. Recurring morphisms: top motifs by subperiod spread (G)
m = json.load(open(ROOT / "12_MORPHISM_CATALOG.json"))
top = [x for x in m["top_motifs"] if x["classification"] in ("RECURRING", "PARTIALLY_RECURRING")][:10]
fig, ax = plt.subplots(figsize=(10, 5))
labels = [f"{x['state_1'][:10]}->{x['state_2'][:10]}->{x['state_3'][:10]}" for x in top]
ax.barh(range(len(top)), [x["occurrences"] for x in top],
        color=["#4c72b0" if x["classification"] == "RECURRING" else "#ddaa33" for x in top])
ax.set_yticks(range(len(top)), labels)
ax.invert_yaxis()
ax.set_xlabel("occurrences")
ax.set_title("Top recurring state motifs (G): blue=RECURRING (>=4 subperiods)")
save(fig, "07_recurring_morphisms.png")

print("all plots written to", OUT)
