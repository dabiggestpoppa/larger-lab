#!/usr/bin/env python
"""Generate the 7 MECH-13 diagnostic plots."""
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

AGE_ORDER = ["AGE_1", "AGE_2_3", "AGE_4_7", "AGE_8_14", "AGE_15_PLUS"]


def _read(name):
    return pd.read_csv(ROOT / name)


# 1. HH lifecycle deep map: mass-migration / stage redistribution
def plot1():
    lc = _read("02_LIFECYCLE_DEEP_MAP.csv")
    hh = lc[(lc["cell"] == "HIGH_BREADTH_HIGH_DISP") &
            (lc["stage"].isin(["INITIATION", "STABILIZATION", "MID_LIFE",
                               "MATURE"]))].sort_values(
        "age", ascending=True).drop_duplicates("stage")
    fig, ax = plt.subplots(figsize=(8.5, 4.4))
    ax.plot(hh["age"], hh["fwd7_prop"], "-o", label="fwd7 propagation")
    ax.plot(hh["age"], hh["fwd7_reentry"], "-s", label="fwd7 reentry")
    ax2 = ax.twinx()
    ax2.plot(hh["age"], hh["dispersion"], "--^", color="gray",
             label="dispersion")
    ax2.set_ylabel("dispersion (gray)")
    ax.set_xlabel("mean state age (days)")
    ax.set_ylabel("forward 7d probability")
    ax.set_title("MECH-13: HH lifecycle — delivery back-loads, "
                 "dispersion collapses")
    ax.legend(loc="upper left", fontsize=8)
    ax2.legend(loc="lower right", fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "01_hh_lifecycle.png", bbox_inches="tight")
    plt.close(fig)


# 2. Initiation geometry: significant birth coordinates
def plot2():
    ig = _read("04_INITIATION_GEOMETRY.csv")
    sig = ig[ig["q"] <= 0.10].copy()
    sig = sig.sort_values("cohens_d", key=lambda s: s.abs())
    fig, ax = plt.subplots(figsize=(9, 6))
    tabs = sig["cell"] + ":" + sig["coord"]
    ax.barh(np.arange(len(sig)), sig["cohens_d"],
            color=["#c44e52" if v < 0 else "#55a868" for v in
                   sig["cohens_d"]])
    ax.set_yticks(np.arange(len(sig)))
    ax.set_yticklabels(tabs, fontsize=7)
    ax.axvline(0, color="k", lw=0.8)
    ax.set_xlabel("cohens d (success minus fail)")
    ax.set_title("MECH-13: significant birth coordinates (FDR q<=0.10) "
                 f"n={len(sig)}")
    fig.tight_layout()
    fig.savefig(OUT / "02_initiation_geometry.png", bbox_inches="tight")
    plt.close(fig)


# 3. Entropy deep map + primitive driver
def plot3():
    ed = _read("06_ENTROPY_DEEP_MAP.csv")
    hh = ed[(ed["group"] == "cell_age") &
            (ed["cell"] == "HIGH_BREADTH_HIGH_DISP")]
    hh = hh.set_index("age_band").reindex(AGE_ORDER).dropna()
    eprim = _read("07_ENTROPY_PRIMITIVE_AUDIT.csv").sort_values(
        "spearman_rho")
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.3))
    a1.plot(hh.index, hh["branch_entropy"], "-o")
    a1.plot(hh.index, hh["dominant_share"], "-s", color="crimson")
    a1.set_xticklabels(AGE_ORDER, rotation=30)
    a1.set_ylabel("bits / share")
    a1.set_title("HH branch entropy collapses with age")
    a2.barh(eprim["coord"], eprim["spearman_rho"],
            color=["#55a868" if v > 0 else "#c44e52" for v in
                   eprim["spearman_rho"]])
    a2.set_xlabel("spearman rho vs entropy-collapse")
    a2.set_title("entropy-collapse drivers")
    fig.tight_layout()
    fig.savefig(OUT / "03_entropy.png", bbox_inches="tight")
    plt.close(fig)


# 4. Spatial/temporal 2x2 constraint matrix
def plot4():
    s = _read("09_SPATIAL_TEMPORAL_CONSTRAINT_MATRIX.csv")
    s = s.sort_values(["spatial_ax", "temporal_ax"])
    x = np.arange(len(s))
    w = 0.38
    fig, ax = plt.subplots(figsize=(8, 4.4))
    ax.bar(x - w / 2, s["p_prop_7d"], w, label="P(prop 7d)")
    ax.bar(x + w / 2, s["p_reentry_7d"], w, color="#c44e52",
           label="P(reentry 7d)")
    ax.set_xticks(x)
    ax.set_xticklabels(s["constraint_cell"], rotation=20)
    ax.set_ylabel("probability")
    ax.set_title(f"MECH-13: spatial activation x temporal entropy "
                 f"(axis rho={s['axis_spearman'].iloc[0]:.2f})")
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUT / "04_spatial_temporal.png", bbox_inches="tight")
    plt.close(fig)


# 5. Waterfall subtype + activation surfaces
def plot5():
    w = _read("10_WATERFALL_SUBTYPE_MATRIX.csv")
    a = _read("11_ACTIVATION_THRESHOLD_SURFACES.csv")
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.3))
    a1.bar(np.arange(len(w)), w["n"],
           color=["#55a868" if v == "NAMED_SUBTYPE" else "#999" for v in
                  w["verdict"]])
    a1.set_xticks(np.arange(len(w)))
    a1.set_xticklabels(w["subtype"], rotation=20)
    a1.set_ylabel("n events")
    a1.set_title("waterfall subtypes (green=NAMED>=50)")
    mono = a[a["surface_type"] == "MONOTONIC_THRESHOLD_SURFACE"]
    a2.bar(np.arange(len(a)), a["spearman_rho"],
           color=["#55a868" if r == "MONOTONIC_THRESHOLD_SURFACE"
                  else "#999" for r in a["surface_type"]])
    a2.axhline(0, color="k", lw=0.8)
    a2.set_xticks(np.arange(len(a)))
    a2.set_xticklabels([f"{p}\n{c}" for p, c in
                        zip(a["patch"], a["coord"])], fontsize=6,
                       rotation=45)
    a2.set_ylabel("activation spearman rho")
    a2.set_title("activation threshold surfaces")
    fig.tight_layout()
    fig.savefig(OUT / "05_waterfall.png", bbox_inches="tight")
    plt.close(fig)


# 6. Patch response shape + homogeneity
def plot6():
    p = _read("12_PATCH_RESPONSE_CURVES.csv")
    shapes = p["response_shape"].value_counts()
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.2))
    a1.bar(shapes.index, shapes.values, color="#4c72b0")
    a1.set_ylabel("count")
    a1.set_title("patch response shape distribution")
    a1.tick_params(axis="x", rotation=20)
    # representative activation vs amplitude band for one perturbation
    rep = p[(p["perturbation"] == "brd_jump")].copy()
    band_order = ["Q1", "Q2", "Q3", "Q4"]
    for patch in rep["patch"].unique()[:5]:
        g = rep[rep["patch"] == patch].set_index("amp_band").reindex(
            band_order)
        a2.plot(band_order, g["activation_prob_3d"], "-o", label=patch,
                ms=4)
    a2.set_ylabel("activation prob (3d)")
    a2.set_xlabel("amplitude band")
    a2.set_title("activation by amplitude band (brd_jump)")
    a2.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(OUT / "06_patch_response.png", bbox_inches="tight")
    plt.close(fig)


# 7. Directional asymmetry atlas + absolute x sigma
def plot7():
    d = _read("17_DIRECTIONAL_ASYMMETRY_ATLAS.csv")
    a = _read("15_ABSOLUTE_SIGMA_SHOCK_GEOMETRY.csv")
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 4.4))
    colors = ["#c44e52" if s == "DOWN" else "#55a868" for s in d["sign"]]
    a1.bar(np.arange(len(d)), d["med_breadth"], 0.6, color=colors)
    a1.set_xticks(np.arange(len(d)))
    a1.set_xticklabels(d["family"], rotation=30, fontsize=8)
    a1.set_ylabel("median breadth at event")
    a1.set_title("directional asymmetry (red=down, green=up)")
    # abs vs sigma grid: reversal rate heat
    z_labels = ["<2", "2-3", "3-4", "4+"]
    a_labels = ["<2%", "2-5%", "5-10%", "10-20%", ">20%"]
    mat = np.full((len(a_labels), len(z_labels)), np.nan)
    for _, r in a.iterrows():
        zi = z_labels.index(r["sigma_class"]) if r["sigma_class"] in \
            z_labels else None
        ai = a_labels.index(r["abs_class"]) if r["abs_class"] in \
            a_labels else None
        if zi is None or ai is None:
            continue
        mat[ai, zi] = r["p_reversal"]
    im = a2.imshow(mat, cmap="RdYlGn_r", aspect="auto")
    a2.set_xticks(range(len(z_labels)))
    a2.set_xticklabels(z_labels)
    a2.set_yticks(range(len(a_labels)))
    a2.set_yticklabels(a_labels)
    a2.set_xlabel("sigma class")
    a2.set_ylabel("|abs move|")
    a2.set_title("P(reversal) by absolute x sigma")
    fig.colorbar(im, ax=a2)
    fig.tight_layout()
    fig.savefig(OUT / "07_directional_absigma.png", bbox_inches="tight")
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