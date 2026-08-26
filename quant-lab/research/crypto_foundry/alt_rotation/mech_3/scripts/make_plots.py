#!/usr/bin/env python
"""MECH-3 plots: decomposition, routing flips, pivot anatomy, release routes,
plateaus, primitive audit, state transitions, network connectivity."""
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

plt.rcParams.update({"figure.dpi": 110, "font.size": 9, "axes.titlesize": 10})


def load(name):
    return pd.read_csv(ROOT / name)


# 1. chain-liquidity decomposition: pooled redundancy heatmap
red = load("05_CHAIN_LIQUIDITY_REDUNDANCY.csv")
vars_ = sorted(set(red.var_a) | set(red.var_b))
M = np.full((len(vars_), len(vars_)), np.nan)
for _, r in red.iterrows():
    i, j = vars_.index(r.var_a), vars_.index(r.var_b)
    M[i, j] = M[j, i] = r.median_abs_r
np.fill_diagonal(M, 1.0)
fig, ax = plt.subplots(figsize=(9, 7))
im = ax.imshow(np.nan_to_num(M, nan=0.5), cmap="RdBu_r", vmin=0, vmax=1)
ax.set_xticks(range(len(vars_))); ax.set_xticklabels(vars_, rotation=90)
ax.set_yticks(range(len(vars_))); ax.set_yticklabels(vars_)
for i in range(len(vars_)):
    for j in range(len(vars_)):
        if not np.isnan(M[i, j]):
            ax.text(j, i, f"{M[i, j]:.2f}", ha="center", va="center", fontsize=6)
ax.set_title("Chain-liquidity coordinate redundancy (median |Spearman r|, 12 chains)")
fig.colorbar(im, shrink=0.8)
fig.tight_layout(); fig.savefig(OUT / "1_chain_liquidity_decomposition.png")
plt.close(fig)

# 2. routing flips: flagship relationship across states
d = load("08_ROUTING_FLIP_MAP.csv")
fl = d[d.relationship == "VEL 51-100->101-200"].dropna(subset=["cond_corr"])
fl = fl.sort_values("cond_corr")
fig, ax = plt.subplots(figsize=(9, 5))
colors = ["#c0392b" if (c == "REVERSED" and fdr < 0.05) else
          "#e67e22" if (c == "GAINED" and fdr < 0.05) else "#95a5a6"
          for c, fdr in zip(fl.classification, fl.fdr_q)]
ax.barh(fl.state, fl.cond_corr, color=colors)
ax.axvline(0, color="k", lw=0.8)
ax.set_xlabel("conditional corr (51-100 leads 101-200, velocity)")
ax.set_title("Routing flip map: 51-100->101-200 velocity lead by state\n"
             "(uncond +0.13; red=REVERSED q<0.05, orange=GAINED q<0.05)")
fig.tight_layout(); fig.savefig(OUT / "2_routing_flips.png")
plt.close(fig)

# 3. concentration entry anatomy (event vs control, window 7)
e = load("11_CONCENTRATION_PIVOT_ANATOMY.csv")
for evt in ["ENTRY", "EXIT"]:
    g = e[(e.event == evt) & (e.window_d == 7) & (e.fdr_q < 0.05)]
    if len(g) == 0:
        g = e[(e.event == evt) & (e.fdr_q < 0.05)].head(8)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    y = np.arange(len(g))
    ax.barh(y + 0.2, g.control_median, height=0.4, label="control", color="#bdc3c7")
    ax.barh(y - 0.2, g.event_median, height=0.4, label="event", color="#2980b9")
    ax.set_yticks(y); ax.set_yticklabels(g.precursor)
    ax.axvline(0, color="k", lw=0.6)
    ax.legend()
    ax.set_title(f"Concentration {evt.lower()} precursors (event vs control, 7D window)")
    fig.tight_layout(); fig.savefig(OUT / f"3_concentration_{evt.lower()}.png")
    plt.close(fig)

# 4. release routes
g = load("12_RELEASE_ROUTE_MAP.csv")
vc = g.destination_state.value_counts()
fig, ax = plt.subplots(figsize=(7, 4.5))
ax.bar(vc.index, vc.values, color="#8e44ad")
ax.set_ylabel("exits")
ax.set_title(f"Release routes from BTC_CONCENTRATION (n={len(g)})")
plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
fig.tight_layout(); fig.savefig(OUT / "4_release_routes.png")
plt.close(fig)

# 5. information plateau
h = load("13_INFORMATION_PLATEAU.csv")
cols = [c for c in h.columns if c.startswith("inc_r2_")]
fig, ax = plt.subplots(figsize=(7, 4.5))
for _, row in h.iterrows():
    vals = [row[c] for c in cols]
    ax.plot(range(1, len(vals) + 1), vals, marker="o", label=row.phenomenon)
ax.set_xticks(range(1, len(cols) + 1))
ax.set_xticklabels([c.replace("inc_r2_", "") for c in cols], rotation=45, ha="right")
ax.set_xlabel("variables added (fixed order)")
ax.set_ylabel("cumulative R2")
ax.set_title("Information plateau (incremental R2)")
ax.legend(fontsize=7)
fig.tight_layout(); fig.savefig(OUT / "5_information_plateau.png")
plt.close(fig)

# 6. field plateau triggers
i = load("14_FIELD_PLATEAU.csv")
fig, axes = plt.subplots(1, 3, figsize=(11, 3.6))
for ax, p in zip(axes, sorted(i.plateau.unique())):
    sub = i[i.plateau == p]
    vc = sub.release_trigger.value_counts().head(4)
    ax.bar(vc.index, vc.values, color="#16a085")
    ax.set_title(f"{p}\n(n={len(sub)}, med dur {sub.duration_d.median():.0f}d)")
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
fig.suptitle("Field plateau release triggers")
fig.tight_layout(); fig.savefig(OUT / "6_field_plateau.png")
plt.close(fig)

# 7. primitive audit
j = load("15_PRIMITIVE_CANDIDATE_AUDIT.csv")
fig, ax = plt.subplots(figsize=(8, 4))
x = np.arange(len(j))
ax.bar(x - 0.2, j.delta_r2_removed, width=0.4, label="removed", color="#c0392b")
ax.bar(x + 0.2, j.delta_r2_substituted, width=0.4, label="substituted", color="#2980b9")
ax.axhline(0.005, color="k", ls="--", lw=0.8, label="primitive bar")
ax.set_xticks(x); ax.set_xticklabels(j.candidate, rotation=30, ha="right")
ax.set_ylabel("delta R2 (concentration-exit reconstruction)")
ax.set_title("Primitive candidate audit (removal / substitution)")
ax.legend(fontsize=7)
fig.tight_layout(); fig.savefig(OUT / "7_primitive_audit.png")
plt.close(fig)

# 8. state transitions (basin focus) - routing self-transitions by subperiod
l = load("17_DYNAMICAL_SYSTEM_TRANSITIONS.csv")
fig, ax = plt.subplots(figsize=(7, 4))
ax.plot(l.subperiod, l.basin_self_transition, marker="o", color="#2c3e50")
ax.axhline(0.60, color="r", ls="--", lw=0.8, label="basin bar (0.60)")
ax.set_ylabel("basin self-transition")
ax.set_title("Concentration/mixed basin persistence by subperiod")
ax.legend()
fig.tight_layout(); fig.savefig(OUT / "8_state_transitions.png")
plt.close(fig)

# 9. network connectivity: velocity graph with articulation point
k = json.load(open(ROOT / "16_GRAPH_STRUCTURE.json"))
nodes = k["components"] if isinstance(k["components"], list) else []
flat = [n for c in nodes for n in c]
n = len(flat)
pos = {}
for i, name in enumerate(flat):
    ang = 2 * np.pi * i / max(n, 1)
    pos[name] = (np.cos(ang), np.sin(ang))
# edges from subperiod 2025-2026 (latest)
edges = set()
for sp in k["subperiods"]:
    if sp["subperiod"] == "2025-2026":
        for comp in sp["components"]:
            for a in comp:
                for b in comp:
                    if a != b:
                        edges.add((a, b))
fig, ax = plt.subplots(figsize=(8, 6))
for (a, b) in edges:
    x0, y0 = pos[a]; x1, y1 = pos[b]
    ax.plot([x0, x1], [y0, y1], color="#bdc3c7", lw=1.2, zorder=1)
for name in flat:
    x, y = pos[name]
    art = name in k.get("articulation_points", [])
    ax.scatter(x, y, s=420 if art else 220,
               color="#e74c3c" if art else "#3498db", zorder=2, edgecolor="k")
    ax.annotate(name, (x, y), ha="center", va="center", fontsize=7, color="white")
ax.set_title("Chain velocity graph (2025-26 edges; red = articulation point)")
ax.axis("off")
fig.tight_layout(); fig.savefig(OUT / "9_network_connectivity.png")
plt.close(fig)

print("plots written to", OUT)
