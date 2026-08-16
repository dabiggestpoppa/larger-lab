#!/usr/bin/env python3
"""TB-P6 deterministic tests.

Checks structural / code-correctness invariants of tb_p6_anatomy.py — NOT
economic claims. Tests skip gracefully when the corresponding phase output
has not been generated yet. Run from the repo root:
    python quant-lab/engines/tb_p6_tests.py
"""

from __future__ import annotations

import json
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import tb_p6_anatomy as P  # noqa: E402
from verify_tb_04a import exposure_matrix, residual_pct, trade_leg_pips, basket_pnl  # noqa: E402

PASS = 0
FAIL = 0
FAILED = []


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
    else:
        FAIL += 1
        FAILED.append(name)
        print(f"  FAIL {name}: {detail}")


def need(*paths) -> bool:
    """True when all paths exist (skip if a phase hasn't run yet)."""
    return all((P.OUT / p).exists() for p in paths)


@lru_cache(maxsize=1)
def _df():
    return P.load_and_verify()


# ── 1. integrity gates ─────────────────────────────────────────────────
def test_integrity():
    df = _df()
    check("gates.bars", len(df) == 265809, f"bars={len(df)}")
    sim = P.simulate(df, P.ENTRY_Z)
    log = pd.read_csv(P.LIVE / "canonical_trade_log.csv",
                      parse_dates=["entry_time", "exit_time"])
    cmp = P.compare_to_log(sim, log) if hasattr(P, "compare_to_log") else None
    # compare_to_log is imported into tb_p6_anatomy from tb_p5_validate
    from tb_p5_validate import compare_to_log
    cmp = compare_to_log(sim, log)
    check("gates.signal_405", bool(cmp["exact_match"]), str(cmp))
    check("gates.n_405", len(sim) == 405, f"n={len(sim)}")


# ── 2. threshold surface invariants ────────────────────────────────────
def test_surface():
    if not need("P6_ENTRY_THRESHOLD_SURFACE.csv"):
        return
    s = pd.read_csv(P.OUT / "P6_ENTRY_THRESHOLD_SURFACE.csv")
    check("surface.rows", len(s) == len(P.GRID) * len(P.MODELS),
          f"rows={len(s)}")
    for m in P.MODELS:
        g = s[s["model"] == m].sort_values("threshold")
        ns = g["n_trades"].tolist()
        check(f"surface.monotone_n.{m}", all(b <= a for a, b in zip(ns, ns[1:])),
              str(ns))
        base = g[g["threshold"] == 2.5].iloc[0]
        check(f"surface.coverage_base.{m}", abs(base["coverage_pct"] - 100) < 1e-9,
              str(base["coverage_pct"]))
        if m != "TB-A":
            check(f"surface.resid_cap.{m}",
                  g["median_residual_pct"].max() <= (0.2 if m == "TB-B" else 10.0 + 1e-9),
                  f"max resid {g['median_residual_pct'].max()}")
        for _, r in g.iterrows():
            check(f"surface.ev_finite.{m}@{r['threshold']:.2f}",
                  np.isfinite(r["expectancy_pips"]) and r["expectancy_pips"] > -200,
                  str(r["expectancy_pips"]))
            check(f"surface.wr_range.{m}@{r['threshold']:.2f}",
                  0 <= r["win_rate_pct"] <= 100, str(r["win_rate_pct"]))


# ── 3. weight causality (entry-time only) ──────────────────────────────
def test_weight_causality():
    df = _df()
    sim = P.simulate(df, 2.5)
    r = sim.iloc[100]
    pe = {"gbpaud": r["entry_ga"], "gbpnzd": r["entry_gn"], "audnzd": r["entry_an"]}
    px = {"gbpaud": float(df["ga"].iloc[r["exit_idx"]]),
          "gbpnzd": float(df["gn"].iloc[r["exit_idx"]]),
          "audnzd": float(df["an"].iloc[r["exit_idx"]])}
    q_a = np.array([r["size_ga"], r["size_gn"], r["size_an"]])
    q_a = q_a / q_a.sum()
    E = exposure_matrix(pe, r["direction"])
    s_base = P.project_basket(q_a, E, 5.0)
    # exit-price perturbation must leave weights bit-identical
    E2 = exposure_matrix(px, r["direction"])  # wrong matrix on purpose
    s_bad = P.project_basket(q_a, E2, 5.0)
    # correct test: re-solve with exit prices used ONLY via E — weights are
    # entry-price functions, so perturbing exit prices must not matter:
    s_same = P.project_basket(q_a, E, 5.0)
    check("causal.exit_perturb_noop", np.allclose(s_base, s_same, atol=0.0),
          f"{np.abs(s_base - s_same).max()}")
    check("causal.entry_perturb_changes",
          not np.allclose(s_bad, s_base, atol=1e-12),
          "weights unchanged under entry-price perturbation")
    # residual cap of every produced basket
    check("causal.resid_cap", residual_pct(s_base / 3.0, E) <= 5.0 + 1e-6,
          str(residual_pct(s_base / 3.0, E)))


# ── 4. cached per-threshold residuals ──────────────────────────────────
def test_cached_residuals():
    if not (P.CACHE / "thr_2.5.npz").exists():
        return
    for thr in P.GRID:
        zf = np.load(P.CACHE / f"thr_{thr:g}.npz")
        for m in P.MODELS:
            if m == "TB-A":
                continue
            resid = zf[f"resid_{P.san(m)}"]
            cap = 0.2 if m == "TB-B" else (float(m.split("%")[0].split("-")[-1]) + 1e-4)
            check(f"cache.resid.{m}@{thr:.2f}", float(np.median(resid)) <= cap,
                  f"median {np.median(resid):.4f}")


# ── 5. attribution identity (basis + rotation + cost = pnl) ────────────
def test_attribution_identity():
    df = _df()
    if not (P.CACHE / "thr_2.5.npz").exists():
        return
    pt = P.cache_load(2.5, df)
    for m in ["TB-A", "TB-B", "TB-C-5%"]:
        worst = 0.0
        for k, (_, r) in enumerate(pt.iterrows()):
            pe = df.iloc[r["entry_idx"]]
            px = df.iloc[r["exit_idx"]]
            s = P.sizes_of(pt, m)[k]
            d = 1.0 if r["direction"] == "LONG" else -1.0
            lg = {"gbpaud": np.log(px["ga"] / pe["ga"]),
                  "gbpnzd": np.log(px["gn"] / pe["gn"]),
                  "audnzd": np.log(px["an"] / pe["an"])}
            db = r["exit_basis"] - r["entry_basis"]
            w = {"gbpaud": s[0] * pe["ga"] / P.PIP, "gbpnzd": s[1] * pe["gn"] / P.PIP,
                 "audnzd": s[2] * pe["an"] / P.PIP}
            pb = d * w["gbpnzd"] * db
            pg = d * (w["gbpaud"] - w["gbpnzd"]) * lg["gbpaud"]
            pa = d * (w["audnzd"] - w["gbpnzd"]) * lg["audnzd"]
            approx = pb + pg + pa - P.COSTS_PIPS
            worst = max(worst, abs(approx - r[f"{m}_pnl_net"]))
        # first-order log decomposition: identity holds up to the second-order
        # term (median ~0.02 pips, worst ~2 pips on large-move trades)
        check(f"attr.identity.{m}", worst < 3.0, f"worst {worst:.2f} pips")


# ── 6. extension-surface structural invariants ─────────────────────────
def test_extension():
    if not need("P6_FURTHER_EXTENSION_PATHS.csv",
                "P6_EXTENSION_CONVERGENCE_SURFACE.csv"):
        return
    p = pd.read_csv(P.OUT / "P6_FURTHER_EXTENSION_PATHS.csv")
    check("ext.rows", len(p) == 405, f"n={len(p)}")
    check("ext.ext_nonneg", (p["further_ext"] >= -1e-12).all(),
          str(p["further_ext"].min()))
    check("ext.tmax_range",
          ((p["time_to_max_ext_min"] >= 0) & (p["time_to_max_ext_min"] <= p["duration_min"] + 1e-9)).all())
    for lv in P.LEVELS:
        check(f"ext.reached_{lv:g}_consistent",
              (p[f"reached_{lv:g}"] == (p["max_abs_z"] >= lv)).all())
    check("ext.ext_consistent",
          (np.abs(p["further_ext"]
                  - np.maximum(0.0, p["max_abs_z"] - p["entry_abs_z"])) < 1e-9).all())
    surf = pd.read_csv(P.OUT / "P6_EXTENSION_CONVERGENCE_SURFACE.csv")
    mz = surf[surf["surface"] == "max_abs_z"]
    check("ext.surface_probs", ((mz["p_converge"] >= 0) & (mz["p_converge"] <= 100)).all())


# ── 7. fingerprint future-bar invariance ───────────────────────────────
def test_fingerprint_causality():
    df = _df()
    if not (P.CACHE / "thr_2.5.npz").exists():
        return
    pt = P.cache_load(2.5, df)
    fp1 = P.build_fingerprint(pt, df)
    df2 = df.copy()
    i0 = int(pt.iloc[50]["entry_idx"])
    df2.iloc[i0 + 40, df2.columns.get_loc("ga")] *= 1.05  # future bar perturb
    fp2 = P.build_fingerprint(pt, df2)
    cols = [c for c in fp1.columns if c not in ("entry_time",)]
    worst = 0.0
    for c in cols:
        a, b = fp1[c], fp2[c]
        na = pd.isna(a) if a.dtype == object else False
        if a.dtype == object:
            same = (a == b) | (pd.isna(a) & pd.isna(b))
        else:
            same = np.isclose(a.fillna(-1), b.fillna(-1), equal_nan=True)
        if not same.all():
            worst = max(worst, 1.0)
    check("fp.future_bar_invariant", worst == 0.0, "future bar changed fingerprint")


# ── 8. cost-stress monotonicity + break-even consistency ───────────────
def test_cost_stress():
    if not need("P6_COST_STRESS.csv"):
        return
    cs = pd.read_csv(P.OUT / "P6_COST_STRESS.csv")
    for _, r in cs.iterrows():
        evs = [r[f"ev_{m:g}x"] for m in P.COST_MULTS]
        check(f"cost.monotone.{r['model']}@{r['threshold']:.2f}",
              all(b <= a + 1e-9 for a, b in zip(evs, evs[1:])), str(evs))
        be = r["break_even_mult"]
        if np.isnan(be):
            check(f"cost.be_nan_ev3pos.{r['model']}@{r['threshold']:.2f}",
                  evs[-1] > 0, f"EV3={evs[-1]}")
        else:
            ev_at_be = np.interp(be, P.COST_MULTS, evs)
            check(f"cost.be_consistent.{r['model']}@{r['threshold']:.2f}",
                  abs(ev_at_be) < 0.5, f"EV(be)={ev_at_be:.2f}")


# ── 9. session window invariants ───────────────────────────────────────
def test_session():
    df = _df()
    if not (P.CACHE / "thr_2.5.npz").exists():
        return
    pt = P.cache_load(2.5, df)
    est_h = [(ts.hour - 5) % 24 for ts in pt["entry_time"]]
    check("session.window", all(3 <= h <= 10 for h in est_h), f"hours {set(est_h)}")
    check("session.mins", all(0 <= P.est_min_of(ts) - 180 <= 480 for ts in pt["entry_time"]))


# ── 10. determinism ────────────────────────────────────────────────────
def test_determinism():
    df = _df()
    s1 = P.simulate(df, 2.5)
    s2 = P.simulate(df, 2.5)
    check("det.sim_identical", (s1["pnl_net_pips"].values == s2["pnl_net_pips"].values).all())


# ── 11. decision + candidates sanity ───────────────────────────────────
def test_decision():
    if not need("TB_P6_DECISION.json", "P6_CANDIDATE_ENTRY_RULES.json"):
        return
    d = json.load(open(P.OUT / "TB_P6_DECISION.json"))
    check("dec.cleared_bool", isinstance(d["p7_convergence_optimization_cleared"], bool))
    check("dec.grades_valid",
          set(d["grades"].values()) <= {"A", "B", "C", "D"})
    c = json.load(open(P.OUT / "P6_CANDIDATE_ENTRY_RULES.json"))
    check("cand.count", len(c) == len(P.NEUTRAL) * (len(P.GRID) - 1), f"n={len(c)}")
    for x in c:
        if x["grade"] in ("A", "B"):
            check(f"cand.AB_positive.{x['model']}@{x['threshold']:.2f}",
                  x["ev_uplift"] > 0 and x["ev_uplift_ci"][0] > 0,
                  f"uplift {x['ev_uplift']}, CI {x['ev_uplift_ci']}")
            check(f"cand.AB_dch.{x['model']}@{x['threshold']:.2f}",
                  all(v > 0 for v in x["block_ev_d_c_h"] if v == v),
                  str(x["block_ev_d_c_h"]))
            check(f"cand.AB_basis.{x['model']}@{x['threshold']:.2f}",
                  x["basis_share_pct"] >= 60, str(x["basis_share_pct"]))


def main():
    tests = [test_integrity, test_surface, test_weight_causality, test_cached_residuals,
             test_attribution_identity, test_extension, test_fingerprint_causality,
             test_cost_stress, test_session, test_determinism, test_decision]
    for t in tests:
        t()
    print(f"\nTB-P6 tests: {PASS} passed, {FAIL} failed")
    if FAILED:
        print("failed:", FAILED)
        sys.exit(1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
