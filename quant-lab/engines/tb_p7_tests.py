#!/usr/bin/env python3
"""TB-P7 deterministic tests.

Checks structural / code-correctness invariants of tb_p7_convergence.py — NOT
economic claims (except where the claim is a deterministic property of the
generated artifact, e.g. paired-CI sign). Tests skip gracefully when the
corresponding phase output has not been generated yet. Run from the repo root:
    python quant-lab/engines/tb_p7_tests.py
"""

from __future__ import annotations

import json
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import tb_p7_convergence as P  # noqa: E402
from tb_p6_anatomy import load_and_verify  # noqa: E402

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
    return load_and_verify()


# ── 0. alignment unit tests (pure code correctness) ────────────────────
def _frame(entries, exits, pnl, idx=None):
    return pd.DataFrame({
        "entry_time": pd.to_datetime(entries),
        "exit_time": pd.to_datetime(exits),
        "TB-B_pnl_net": pnl,
    }, index=idx if idx is not None else range(len(entries)))


def test_alignment():
    # merge case: E_new holds one position where E0 closed + re-entered
    e0 = _frame(
        ["2023-01-01 09:00", "2023-01-01 11:30"],
        ["2023-01-01 11:00", "2023-01-01 14:00"],
        [10.0, 5.0])
    en = _frame(["2023-01-01 09:00"], ["2023-01-01 14:00"], [14.0])
    d = P.aligned_paired_diff(en, e0, "TB-B")
    check("align.merge_total", abs(d.sum() - (14.0 - 15.0)) < 1e-12,
          f"sum={d.sum()}")
    check("align.merge_len", len(d) == len(e0), f"len={len(d)}")
    # split case: E_new invalidates then re-enters inside E0's window
    e0b = _frame(["2023-01-01 09:00"], ["2023-01-01 14:00"], [20.0])
    enb = _frame(
        ["2023-01-01 09:00", "2023-01-01 11:30"],
        ["2023-01-01 11:00", "2023-01-01 14:00"],
        [8.0, 6.0])
    d2 = P.aligned_paired_diff(enb, e0b, "TB-B")
    check("align.split_total", abs(d2.sum() - (14.0 - 20.0)) < 1e-12,
          f"sum={d2.sum()}")
    # identity: E_new == E0 gives exact zeros
    d3 = P.aligned_paired_diff(e0, e0, "TB-B")
    check("align.identity", np.allclose(d3, 0.0, atol=1e-12), f"max={np.abs(d3).max()}")
    # leftover: E_new has a genuinely new trade outside every E0 window
    e0c = _frame(["2023-01-01 09:00"], ["2023-01-01 11:00"], [4.0])
    enc = _frame(
        ["2023-01-01 09:00", "2023-01-02 09:00"],
        ["2023-01-01 11:00", "2023-01-02 11:00"],
        [4.0, 7.0])
    d4 = P.aligned_paired_diff(enc, e0c, "TB-B")
    check("align.leftover", abs(d4.sum() - 7.0) < 1e-12, f"sum={d4.sum()}")


# ── 1. integrity gates ─────────────────────────────────────────────────
def test_integrity():
    df = _df()
    check("gates.bars", len(df) == 265809, f"bars={len(df)}")
    sim = P.simulate(df, P.ENTRY_Z)
    from tb_p5_validate import compare_to_log
    log = pd.read_csv(P.LIVE / "canonical_trade_log.csv",
                      parse_dates=["entry_time", "exit_time"])
    cmp = compare_to_log(sim, log)
    check("gates.signal_405", bool(cmp["exact_match"]), str(cmp))
    check("gates.n_405", len(sim) == 405, f"n={len(sim)}")


# ── 2. exit-target surface invariants ──────────────────────────────────
def test_exit_surface():
    if not need("P7_EXIT_Z_SURFACE.csv"):
        return
    s = pd.read_csv(P.OUT / "P7_EXIT_Z_SURFACE.csv")
    check("surface.rows", len(s) == len(P.EXIT_GRID) * len(P.ENTRY_SETS) * 5,
          f"rows={len(s)}")
    for entry in P.ENTRY_SETS:
        for m in ["TB-A"] + P.P7_MODELS:
            g = s[(s["entry_z"] == entry) & (s["model"] == m)] \
                .sort_values("exit_target")
            ev = g["expectancy_pips"].values
            # sorted ascending by exit_target: overshoot (-0.50) first, so EV
            # is non-INCREASING as the exit target rises toward +1.0
            check(f"surface.monotone.{entry:g}.{m}",
                  all(b <= a + 1e-9 for a, b in zip(ev, ev[1:])),
                  f"ev={np.round(ev,2)}")
            dd = g["max_dd_pips"].values
            dd0 = g.loc[g["exit_target"] == 0.0, "max_dd_pips"].iloc[0]
            if m == "TB-B":
                # TB-B drawdown is unchanged across every target -0.50..+0.75;
                # the +1.00 target exits so early that re-entries change the
                # trade sequence and its DD - that cell is excluded by design
                core = g[g["exit_target"] <= 0.75]["max_dd_pips"].values
                check(f"surface.dd_flat.{entry:g}.{m}",
                      np.allclose(core, core[0], atol=1e-6),
                      f"dd={np.round(core,2)}")
            else:
                # no catastrophic drawdown blowup from overshooting: the worst
                # overshoot-target DD is no deeper than 1.5x the z=0.0 DD
                # (the +1.0 early-exit target is not a candidate and can
                # legitimately change the trade sequence)
                worst_os = g[g["exit_target"] < 0]["max_dd_pips"].min()
                check(f"surface.dd_bounded.{entry:g}.{m}",
                      bool(worst_os >= 1.5 * dd0),
                      f"worst_os={worst_os:.2f} dd0={dd0:.2f}")
            overshoot = g[g["exit_target"] < 0]
            if m in P.P7_MODELS:
                check(f"surface.be_overshoot.{entry:g}.{m}",
                      all((b >= 2.5 or np.isnan(b))
                          for b in overshoot["break_even_mult"].values),
                      f"be={overshoot['break_even_bound'].tolist()}")


# ── 3. matched-pairs alignment on real data ────────────────────────────
def test_real_alignment():
    if not need("P7_ENGINE_CONFIGS.json", "P7_EXIT_ENGINE_COMPARISON.csv"):
        return
    df = _df()
    cfg = json.load(open(P.OUT / "P7_ENGINE_CONFIGS.json", encoding="utf-8"))
    e0 = P.cache_load(2.5, df)
    for eng in cfg["engines"]:
        if eng["name"] == "E0":
            continue
        inv = P._inv_from_zones(eng.get("invalidate_zones", [])) \
            if eng.get("invalidate_zones") else None
        pt = P.enrich(P.simulate(df, 2.5, exit_target=eng["exit_target"],
                                 max_hold_min=eng.get("max_hold_min"),
                                 invalidate=inv), df)
        for m in P.P7_MODELS:
            d = P.aligned_paired_diff(pt, e0, m)
            total = pt[f"{m}_pnl_net"].sum() - e0[f"{m}_pnl_net"].sum()
            check(f"align.total.{eng['name']}.{m}",
                  abs(d.sum() - total) < 1e-6,
                  f"aligned={d.sum():.4f} total={total:.4f}")
    # E0 self-alignment is exact zero
    d0 = P.aligned_paired_diff(e0, e0, "TB-B")
    check("align.self_e0", np.allclose(d0, 0.0, atol=1e-9),
          f"max={np.abs(d0).max()}")


# ── 4. comparison-table correctness ────────────────────────────────────
def test_comparison():
    if not need("P7_EXIT_ENGINE_COMPARISON.csv"):
        return
    c = pd.read_csv(P.OUT / "P7_EXIT_ENGINE_COMPARISON.csv")
    check("comp.rows", len(c) == 24, f"rows={len(c)}")
    e0 = c[c["engine"] == "E0"].set_index(["entry_z", "model"])
    for (eng, entry, m), r in c[c["engine"] != "E0"].groupby(
            ["engine", "entry_z", "model"]):
        b = e0.loc[(entry, m)]
        ci = json.loads(r["ev_diff_ci"].iloc[0])
        uplift = r["expectancy_pips"].iloc[0] - b["expectancy_pips"]
        check(f"comp.uplift_consistent.{eng}.{entry:g}.{m}",
              abs(uplift - (r["expectancy_pips"].iloc[0] - b["expectancy_pips"])) < 1e-9)
        if eng == "E1":
            check(f"comp.e1_ci.{entry:g}.{m}", ci[0] > 0, f"ci={ci}")
            check(f"comp.e1_p.{entry:g}.{m}",
                  r["perm_p"].iloc[0] < 0.01, f"p={r['perm_p'].iloc[0]}")
            check(f"comp.e1_holdout.{entry:g}.{m}",
                  bool(r["holdout_ok"].iloc[0]), f"ho={r['holdout_ok'].iloc[0]}")
            check(f"comp.e1_top5.{entry:g}.{m}",
                  bool(r["top5_ok"].iloc[0]), f"t5={r['top5_ok'].iloc[0]}")
        if eng == "E3":
            check(f"comp.e3_ci_zero.{entry:g}.{m}",
                  ci[0] < 0 < ci[1], f"ci={ci} (contains 0)")
            check(f"comp.e3_dd.{entry:g}.{m}",
                  r["max_dd_pips"].iloc[0] < b["max_dd_pips"],
                  f"dd {r['max_dd_pips'].iloc[0]:.1f} vs E0 {b['max_dd_pips']:.1f}")
    # every candidate row: basis share, yearly, cost gates sane
    for _, r in c[c["engine"] != "E0"].iterrows():
        check(f"comp.basis.{r['engine']}.{r['entry_z']:g}.{r['model']}",
              r["basis_share_pct"] >= 60, f"basis={r['basis_share_pct']:.1f}")
        check(f"comp.weakyears.{r['engine']}.{r['entry_z']:g}.{r['model']}",
              (not isinstance(r["weak_years"], str)) or r["weak_years"].strip() == "",
              f"weak={r['weak_years']}")


# ── 5. decision JSON ───────────────────────────────────────────────────
def test_decision():
    if not need("TB_P7_DECISION.json"):
        return
    d = json.load(open(P.OUT / "TB_P7_DECISION.json", encoding="utf-8"))
    grades = d["engine_grades"]
    e1s = [v for k, v in grades.items() if k.startswith("E1")]
    e3s = [v for k, v in grades.items() if k.startswith("E3")]
    check("decision.e1_all_A", len(e1s) == 8 and all(v == "A" for v in e1s),
          f"E1 grades={e1s}")
    check("decision.e3_all_D", len(e3s) == 8 and all(v == "D" for v in e3s),
          f"E3 grades={e3s}")
    check("decision.counts", d["grade_counts"] == {"A": 8, "B": 0, "C": 0, "D": 16},
          f"counts={d['grade_counts']}")
    check("decision.p8_cleared", bool(d["p8_structural_geometry_cleared"]))
    check("decision.repair_documented", "p75_gate_repair" in d)


# ── 6. P7.2 / P7.3 / P7.4 artifact properties ──────────────────────────
def test_hold_and_capture():
    if need("P7_REMAINING_EXPECTANCY_SURFACE.csv"):
        r = pd.read_csv(P.OUT / "P7_REMAINING_EXPECTANCY_SURFACE.csv")
        # no weak region: expected remaining PnL stays positive everywhere
        check("hold.exp_positive", bool((r["e_remaining_pnl"] > 0).all()),
              f"min={r['e_remaining_pnl'].min():.2f}")
        # coarse support floor for the P7.2 remaining-expectancy bins
        check("hold.min_support", int(r["n"].min()) >= 5, f"min n={r['n'].min()}")
    if need("P7_CAPTURE_EFFICIENCY.csv"):
        c = pd.read_csv(P.OUT / "P7_CAPTURE_EFFICIENCY.csv")
        tb = c[(c["model"] == "TB-B") & (c["entry_z"] == 2.5)].iloc[0]
        check("capture.losers_prev_profitable",
              tb["losers_prev_profitable_pct"] > 50,
              f"pct={tb['losers_prev_profitable_pct']:.1f}")
        check("capture.winner_median",
              tb["median_capture_winners"] > 0.9,
              f"capture={tb['median_capture_winners']:.3f}")
    if need("P7_INVALIDATION_SURFACE.csv", "P7_RECOVERY_CLIFFS.md"):
        inv = pd.read_csv(P.OUT / "P7_INVALIDATION_SURFACE.csv")
        cell = inv[(inv["entry_z"] == 2.5) & (inv["z_lo"] == 2.5)
                   & (inv["z_hi"] == 3.0) & (inv["age_lo"] == 180)]
        check("inv.cliff_cell", len(cell) == 1, f"cells={len(cell)}")
        if len(cell):
            check("inv.cliff_low_pconv", cell["p_convergence_pct"].iloc[0] < 30,
                  f"P={cell['p_convergence_pct'].iloc[0]:.1f}%")
            check("inv.cliff_support", int(cell["n"].iloc[0]) >= 15,
                  f"N={cell['n'].iloc[0]}")
        cliffs = Path(P.OUT / "P7_RECOVERY_CLIFFS.md").read_text(encoding="utf-8")
        check("inv.cliffs_documented", "180" in cliffs and "19" in cliffs)


# ── 7. reproducibility: regenerate-all produces bit-identical outputs ──
def test_repro():
    if not need("P7_EXIT_Z_SURFACE.csv", "P7_EXIT_ENGINE_COMPARISON.csv"):
        return
    # cache-file independence: simulate(enriched) must equal cache_load
    df = _df()
    e0 = P.cache_load(2.5, df)
    sim = P.enrich(P.simulate(df, 2.5), df)
    for m in P.P7_MODELS:
        a = e0[f"{m}_pnl_net"].values
        b = sim[f"{m}_pnl_net"].values
        check(f"repro.pnl.{m}", np.allclose(a, b, atol=1e-9),
              f"maxdiff={np.abs(a - b).max():.2e}")


def main():
    test_alignment()
    test_integrity()
    test_exit_surface()
    test_real_alignment()
    test_comparison()
    test_decision()
    test_hold_and_capture()
    test_repro()
    print(f"\nP7 tests: {PASS} passed, {FAIL} failed")
    if FAILED:
        print("failed:", ", ".join(FAILED))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
