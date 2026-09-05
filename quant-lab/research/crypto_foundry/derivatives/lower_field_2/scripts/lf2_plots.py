"""LOWER-FIELD-2 plots (the .png's are gitignored per repo convention but kept
on disk for the record)."""
from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import lf2_common as C

PLOTS = C.ROOT / "plots"
PLOTS.mkdir(exist_ok=True)
BANDS = C.PRIMARY_BANDS


def _load(name):
    return pd.read_csv(C.RESULTS / name)


def plot_reversal_surface():
    srf = _load("08_CONTINUOUS_RANK_REVERSAL_SURFACE.csv")
    w = srf[srf["width"] == 100]
    fig, ax = plt.subplots(figsize=(9, 5))
    for sign, c in [("UP", "tab:green"), ("DOWN", "tab:red")]:
        d = w[w["sign"] == sign].sort_values("rank_lo")
        ax.plot((d["rank_lo"] + d["rank_hi"]) / 2, d["p_rev_7d"], "-o",
                color=c, label=f"{sign} P(rev7)")
    ax.axvspan(750, 1500, alpha=0.08, color="gray")
    ax.set_xlabel("PIT rank (width-100 window)")
    ax.set_ylabel("P(sign-reversal within 7D)")
    ax.set_title("Reversal by rank & sign (3-sigma extremes)")
    ax.legend()
    fig.tight_layout(); fig.savefig(PLOTS / "reversal_surface.png", dpi=110)


def plot_reversal_purged():
    pur = _load("07_REVERSAL_PURGED_ROBUSTNESS.csv")
    d = pur[(pur["sign"] == "DOWN") & (pur["horizon"] == "7D") &
            (pur["purge_d"].isin(["RAW", "30D"]))]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    x = np.arange(len(BANDS)); wdt = 0.35
    for i, pg in enumerate(["RAW", "30D"]):
        vals = d[d["purge_d"] == pg].set_index("rank_band")["p_rev"].reindex(BANDS)
        ax.bar(x + i * wdt, vals, wdt, label=pg)
    ax.set_xticks(x + wdt / 2); ax.set_xticklabels(BANDS)
    ax.set_ylabel("P(rev7) DOWN 3s"); ax.set_title("Deep downside reversal: purge-stable")
    ax.legend(); fig.tight_layout(); fig.savefig(PLOTS / "reversal_purged.png", dpi=110)


def plot_tail_depth_states():
    # reconstructed per-state depth tail table
    data = [
        ("S_COLD_M_COLD", .090, .109, .121, .157),
        ("S_COLD_M_HOT", .109, .121, .129, .151),
        ("S_HOT_M_COLD(SHMC)", .090, .107, .118, .145),
        ("S_HOT_M_HOT", .126, .141, .148, .158),
    ]
    fig, ax = plt.subplots(figsize=(8, 5))
    for lab, *vals in data:
        ax.plot(BANDS, vals, "-o", label=lab)
    ax.set_xlabel("rank band"); ax.set_ylabel("P(|fwd7|>2sigma)")
    ax.set_title("7D tail by momentum state & depth (SHMC is LOWEST)")
    ax.legend(fontsize=7); fig.tight_layout()
    fig.savefig(PLOTS / "tail_depth_states.png", dpi=110)


def plot_breadth_realization():
    s = _load("14_POTENTIAL_REALIZATION_EVENT_TIME.csv")
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for b, lab, c in [("HIGH", "HIGH breadth", "tab:blue"), ("LOW", "LOW breadth", "tab:orange")]:
        d = s[s["breadth"] == b].set_index("rank_band")["p_realized"].reindex(BANDS)
        ax.plot(BANDS, d, "-o", label=lab, color=c)
    ax.set_ylabel("P(potential -> delivery)"); ax.set_title("Realization by breadth & rank")
    ax.legend(); fig.tight_layout(); fig.savefig(PLOTS / "breadth_realization.png", dpi=110)


def plot_delivery_clock():
    dc = _load("15_DELIVERY_CLOCK_CONDITIONAL.csv")
    dd = dc[dc["metric"].isin(["t1s", "t2s", "t3s"])].groupby(
        ["rank_band", "metric"])["median"].median().unstack().reindex(BANDS)
    dd.plot(kind="bar", figsize=(8, 4.5))
    plt.title("Delivery clock (median days) by rank")
    plt.ylabel("days to k-sigma forward")
    plt.tight_layout(); plt.savefig(PLOTS / "delivery_clock.png", dpi=110)


def main():
    plot_reversal_surface(); plot_reversal_purged(); plot_tail_depth_states()
    plot_breadth_realization(); plot_delivery_clock()
    print("plots written to", PLOTS)


if __name__ == "__main__":
    main()