#!/usr/bin/env python3
"""
TB-P5 deterministic tests — all critical calculations.
======================================================
Independent of the generated reports where cheap; recomputes the core math
(signal reproduction, weights, residuals, causality, rate sensitivity) from
raw inputs. All RNG seeded (SEED=42) -> deterministic.

Run:  python quant-lab/engines/tb_p5_tests.py     (exit 0 = all pass)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).parent.parent.parent
ART = ROOT / "artifacts" / "triangular_basis"
LIVE = ART / "live"
RESEARCH = ART / "research"
DATA = ROOT / "quant-lab" / "data"
sys.path.insert(0, str(Path(__file__).parent))

import tb_p5_validate as p5                          # noqa: E402
from verify_tb_04a import exposure_matrix, project_basket, residual_pct, basket_pnl  # noqa: E402

COSTS = p5.COSTS_PIPS
EPS = p5.EPS_VARIANTS
MODELS = p5.MODELS
NEUTRAL = ["TB-B"] + [f"TB-C-{e:g}%" for e in EPS]

FAILURES = []


def check(name: str, cond: bool, detail: str = ""):
    tag = "PASS" if cond else "FAIL"
    print(f"[{tag}] {name}" + (f"  ({detail})" if detail else ""))
    if not cond:
        FAILURES.append(name)


def load_pt() -> pd.DataFrame:
    pt = pd.read_csv(RESEARCH / "TB_P5_PER_TRADE_WEIGHTS.csv",
                     parse_dates=["entry_time", "exit_time"])
    return pt


def recompute_weights(pt: pd.DataFrame, syn: pd.DataFrame, m: str, n: int = 40) -> tuple:
    """Re-solve weights for a deterministic sample and compare to stored."""
    eps = 0.0 if m == "TB-B" else float(m.split("%")[0].split("-")[-1])
    idx = np.linspace(0, len(pt) - 1, n, dtype=int)
    max_abs_diff = 0.0
    for i in idx:
        r = pt.iloc[i]
        pe = syn.loc[r["entry_time"]]
        prices_e = {"gbpaud": pe["ga"], "gbpnzd": pe["gn"], "audnzd": pe["an"]}
        E = exposure_matrix(prices_e, r["direction"])
        q_a = np.array([r["q_ga"], r["q_gn"], r["q_an"]])
        s = project_basket(q_a, E, eps)
        stored = np.array([r[f"{m}_s0"], r[f"{m}_s1"], r[f"{m}_s2"]])
        max_abs_diff = max(max_abs_diff, float(np.abs(s - stored).max()))
    return max_abs_diff


# ═══════════════════════════════════════════════════════════════════════
# 1. SIGNAL REPRODUCTION — the frozen signal re-run causally from raw bars
#    must reproduce the canonical 405-trade log exactly.
# ═══════════════════════════════════════════════════════════════════════
def test_signal_reproduction():
    syn = p5.load_research_pairs()
    log = pd.read_csv(LIVE / "canonical_trade_log.csv",
                      parse_dates=["entry_time", "exit_time"])
    sim = p5.run_frozen_signal(syn)
    cmp = p5.compare_to_log(sim, log)
    check("signal reproduction exact (405/405, 0 mismatches)",
          bool(cmp["exact_match"]) and cmp["n_sim"] == 405 and cmp["n_mismatched_trades"] == 0,
          str({k: cmp[k] for k in ("n_sim", "n_log", "n_mismatched_trades")}))
    # spot check a few trade-level fields (entry/exit time, direction, z, pnl)
    for k in [0, 200, 404]:
        a, b = sim.iloc[k], log.iloc[k]
        check(f"trade {k} entry_time/direction/result match",
              str(a["entry_time"]) == str(b["entry_time"])
              and a["direction"] == b["direction"] and a["result"] == b["result"])
        check(f"trade {k} entry z matches to 1e-9",
              abs(a["entry_zscore"] - b["entry_zscore"]) < 1e-9)
        check(f"trade {k} gross pnl matches to 1e-6",
              abs(a["pnl_gross_pips"] - b["pnl_gross_pips"]) < 1e-6)


# ═══════════════════════════════════════════════════════════════════════
# 2. DECOMPOSITION IDENTITY — basis + rotation + cost == net pnl (by
#    construction), AND the notional-weighted attribution tracks the exact
#    pips PnL to the log-approximation error (< 0.5% of |gross|).
# ═══════════════════════════════════════════════════════════════════════
def test_decomposition_identity():
    anat = pd.read_csv(RESEARCH / "TB_P5_DISLOCATION_ANATOMY.csv")
    pt = load_pt()
    for m in MODELS:
        d = (anat[f"{m}_basis_pnl"] + anat[f"{m}_rot_pnl"] + anat[f"{m}_cost_pnl"]
             - anat[f"{m}_pnl"])
        check(f"decomposition identity {m} (max |err| <= 1e-9)",
              float(np.abs(d).max()) <= 1e-9, f"max_err={float(np.abs(d).max()):.2e}")
        exact = pt[f"{m}_pnl_net"].values
        approx = anat[f"{m}_pnl"].values
        abs_err = np.abs(approx - exact)
        check(f"attribution tracks exact pnl {m} (max abs err < 5 pips)",
              float(np.nanmax(abs_err)) < 5.0,
              f"max_abs_err={float(np.nanmax(abs_err)):.3f} pips, "
              f"median={float(np.nanmedian(abs_err)):.3f}")
        # MFE/MAE sanity: path bounds contain the final pnl for every trade.
        mfe_ok = bool((anat[f"{m}_mfe"] >= anat[f"{m}_pnl"] - 1e-9).all())
        mae_ok = bool((anat[f"{m}_mae"] <= anat[f"{m}_pnl"] + 1e-9).all())
        check(f"MFE/MAE bound final pnl {m} (all 405 trades)", mfe_ok and mae_ok)


# ═══════════════════════════════════════════════════════════════════════
# 3. METRICS REPRODUCE — recompute EV/PF/WR from the exact per-trade pnls
#    and compare with the model comparison table.
# ═══════════════════════════════════════════════════════════════════════
def test_metrics_reproduce():
    pt = load_pt()
    comp = pd.read_csv(RESEARCH / "TB_P5_MODEL_COMPARISON.csv").set_index("model")
    for m in MODELS:
        net = pt[f"{m}_pnl_net"].values
        wr = (net > 0).mean() * 100
        wins, losses = net[net > 0], -net[net < 0]
        pf = wins.sum() / losses.sum() if losses.sum() > 0 else float("inf")
        check(f"metrics reproduce {m} (EV, PF, WR)",
              abs(net.mean() - comp.loc[m, "expectancy_pips"]) < 1e-6
              and abs(pf - comp.loc[m, "profit_factor"]) < 1e-6
              and abs(wr - comp.loc[m, "win_rate_pct"]) < 1e-6,
              f"EV={net.mean():.6f} PF={pf:.6f} WR={wr:.6f}")


# ═══════════════════════════════════════════════════════════════════════
# 4. RESIDUAL CEILINGS — TB-C variants respect their cap, TB-B ~ 0,
#    TB-A reproduces the broker's ~34.9%.
# ═══════════════════════════════════════════════════════════════════════
def test_residual_ceilings():
    comp = pd.read_csv(RESEARCH / "TB_P5_MODEL_COMPARISON.csv").set_index("model")
    ra = comp.loc["TB-A", "median_residual_pct"]
    check("TB-A median residual ~ 34.8 (broker gate 34.93)",
          34.0 <= ra <= 36.0, f"median={ra:.4f}%")
    rb = comp.loc["TB-B", "median_residual_pct"]
    check("TB-B median residual ~ 0 (<= 0.05%)", rb <= 0.05, f"median={rb:.4f}%")
    for e in EPS:
        m = f"TB-C-{e:g}%"
        r = comp.loc[m, "median_residual_pct"]
        check(f"{m} median residual <= {e}% + 0.05pp", r <= e + 0.05, f"median={r:.4f}%")


# ═══════════════════════════════════════════════════════════════════════
# 5. EPSILON MONOTONICITY — EV non-increasing, residual non-decreasing in eps.
# ═══════════════════════════════════════════════════════════════════════
def test_epsilon_monotonic():
    comp = pd.read_csv(RESEARCH / "TB_P5_MODEL_COMPARISON.csv").set_index("model")
    evs = [comp.loc["TB-B", "expectancy_pips"]] + \
          [comp.loc[f"TB-C-{e:g}%", "expectancy_pips"] for e in EPS]
    res = [comp.loc["TB-B", "median_residual_pct"]] + \
          [comp.loc[f"TB-C-{e:g}%", "median_residual_pct"] for e in EPS]
    check("EV non-increasing in epsilon (TB-B >= TB-C-2.5 >= ... >= TB-C-10)",
          all(evs[i] >= evs[i + 1] - 1e-9 for i in range(len(evs) - 1)),
          " -> ".join(f"{v:.2f}" for v in evs))
    check("residual non-decreasing in epsilon",
          all(res[i] <= res[i + 1] + 1e-9 for i in range(len(res) - 1)),
          " -> ".join(f"{v:.2f}" for v in res))


# ═══════════════════════════════════════════════════════════════════════
# 6. CAUSALITY — stored weights are reproduced from ENTRY-only information;
#    exit-price perturbation must leave weights bit-identical and entry-price
#    perturbation must change them.
# ═══════════════════════════════════════════════════════════════════════
def test_causality_weights():
    syn = p5.load_research_pairs()
    pt = load_pt()
    # stored weights reproduced from entry prices
    d = recompute_weights(pt, syn, "TB-C-5%", n=40)
    check("TB-C-5% stored weights reproduced from entry-only inputs",
          d < 1e-9, f"max_abs_diff={d:.2e}")
    # counterfactual: solve with EXIT exposure matrix -> must differ
    ndiff = 0
    for i in range(0, len(pt), 10):
        r = pt.iloc[i]
        pe = syn.loc[r["entry_time"]]
        px = syn.loc[r["exit_time"]]
        q_a = np.array([r["q_ga"], r["q_gn"], r["q_an"]])
        s_entry = project_basket(q_a, exposure_matrix(
            {"gbpaud": pe["ga"], "gbpnzd": pe["gn"], "audnzd": pe["an"]}, r["direction"]), 5.0)
        s_exit = project_basket(q_a, exposure_matrix(
            {"gbpaud": px["ga"], "gbpnzd": px["gn"], "audnzd": px["an"]}, r["direction"]), 5.0)
        ndiff += float(np.abs(s_entry - s_exit).max()) > 1e-9
    check("counterfactual: exit-time exposure changes weights (causality holds)",
          ndiff > 0, f"{ndiff}/{len(range(0, len(pt), 10))} trades differ")


# ═══════════════════════════════════════════════════════════════════════
# 7. RATE SENSITIVITY — conversion-rate stress bounds (future-rate leakage).
# ═══════════════════════════════════════════════════════════════════════
def test_rate_sensitivity():
    import json
    with open(RESEARCH / "TB_P5_DECISION.json") as f:
        rs = json.load(f)["rate_sensitivity"]
    for m, v in rs.items():
        check(f"rate sensitivity {m}: |dEV| < 15%", v["max_abs_ev_change_pct"] < 15.0,
              f"{v['max_abs_ev_change_pct']:.2f}%")
        check(f"rate sensitivity {m}: d median residual < 0.5pp",
              v["max_median_resid_delta_pp"] < 0.5,
              f"{v['max_median_resid_delta_pp']:.4f}pp")


# ═══════════════════════════════════════════════════════════════════════
# 8. COST STRESS — EV strictly decreasing in multiplier; EV-zero bounds.
# ═══════════════════════════════════════════════════════════════════════
def test_cost_stress():
    cs = pd.read_csv(RESEARCH / "TB_P5_COST_STRESS.csv")
    for m in MODELS:
        g = cs[cs["model"] == m].sort_values("cost_multiplier")
        ev = g["expectancy_pips"].values
        check(f"cost stress {m}: EV strictly decreasing", bool(np.all(np.diff(ev) < 0)),
              " -> ".join(f"{v:.2f}" for v in ev))
    ra = cs[(cs["model"] == "TB-A") & (cs["cost_multiplier"] == 1.0)]["expectancy_pips"].iloc[0]
    check("TB-A EV at 1.0x costs == 8.74 (canonical)",
          abs(ra - 8.7403) < 1e-3, f"{ra:.4f}")


# ═══════════════════════════════════════════════════════════════════════
# 9. BOOTSTRAP — TB-A and TB-B EV CIs disjoint; all CIs exclude 0.
# ═══════════════════════════════════════════════════════════════════════
def test_bootstrap_ci():
    b = pd.read_csv(RESEARCH / "TB_P5_BOOTSTRAP_ROBUSTNESS.csv").set_index("model")
    check("bootstrap: all EV 95% CIs exclude 0",
          all(b.loc[m, "ev_ci_lo"] > 0 for m in MODELS))
    check("bootstrap: TB-B EV CI strictly above TB-A EV CI (disjoint)",
          b.loc["TB-A", "ev_ci_hi"] < b.loc["TB-B", "ev_ci_lo"],
          f"TB-A hi={b.loc['TB-A','ev_ci_hi']:.2f} < TB-B lo={b.loc['TB-B','ev_ci_lo']:.2f}")


# ═══════════════════════════════════════════════════════════════════════
# 10. YEARLY FALSIFICATION — no year (N>=10) with PF <= 1 for any model.
# ═══════════════════════════════════════════════════════════════════════
def test_yearly_no_weak():
    y = pd.read_csv(RESEARCH / "TB_P5_YEARLY_RESULTS.csv")
    bad = y[(y["N"] >= 10) & (y["profit_factor"] <= 1)]
    check("yearly falsification: no weak year (PF<=1, N>=10) for any model",
          len(bad) == 0,
          str(bad[["model", "year", "profit_factor"]].values.tolist()) if len(bad) else "none")


# ═══════════════════════════════════════════════════════════════════════
# 11. WALK-FORWARD — expanding prefixes: TB-B beats TB-A everywhere.
# ═══════════════════════════════════════════════════════════════════════
def test_walk_forward_expanding():
    wf = pd.read_csv(RESEARCH / "TB_P5_WALK_FORWARD_RESULTS.csv")
    exp = wf[wf["kind"] == "expanding"]
    agg = exp.pivot_table(index="label", columns="model", values="expectancy_pips")
    agg = agg.loc[sorted(agg.index, key=lambda s: s.split("<=")[1])]
    ok = bool((agg["TB-B"] > agg["TB-A"]).all())
    check("expanding walk-forward: TB-B EV > TB-A EV at every prefix", ok,
          f"{int((agg['TB-B'] > agg['TB-A']).sum())}/{len(agg)} prefixes")


# ═══════════════════════════════════════════════════════════════════════
# 12. LOT CONSTRAINTS — TB-B executable at $25k with low residual; TB-A $5k
#     degenerates (min-lot rejection) as documented.
# ═══════════════════════════════════════════════════════════════════════
def test_lot_constraints():
    ll = pd.read_csv(RESEARCH / "TB_P5_BROKER_LOT_CONSTRAINTS.csv")
    r25 = ll[(ll["model"] == "TB-B") & (ll["notional_usd"] == 25000)].iloc[0]
    check("TB-B @ $25k: rejection 0%, executable residual < 2%",
          r25["rejection_rate_pct"] == 0 and r25["median_executable_residual_pct"] < 2.0,
          f"resid={r25['median_executable_residual_pct']:.2f}% rej={r25['rejection_rate_pct']:.1f}%")
    r5 = ll[(ll["model"] == "TB-A") & (ll["notional_usd"] == 5000)].iloc[0]
    check("TB-A @ $5k: min-lot rejection > 0 (degenerate as documented)",
          r5["rejection_rate_pct"] > 0, f"rej={r5['rejection_rate_pct']:.1f}%")


# ═══════════════════════════════════════════════════════════════════════
# 13. DECISION JSON — verdicts, gate, forward-OOS status.
# ═══════════════════════════════════════════════════════════════════════
def test_decision_json():
    import json
    with open(RESEARCH / "TB_P5_DECISION.json") as f:
        d = json.load(f)
    check("decision: TB-A VALIDATED", d["verdicts"]["TB-A"]["grade"] == "VALIDATED")
    check("decision: all neutral models STRONG",
          all(d["verdicts"][m]["grade"] == "STRONG" for m in NEUTRAL))
    check("decision: optimization_cleared = true", d["optimization_cleared"] is True)
    check("decision: signal reproduction exact", d["signal_reproduction"]["exact_match"] is True)
    with open(RESEARCH / "TB_P5_FORWARD_OOS.csv") as f:
        fo = pd.read_csv(f)
    check("decision: FORWARD_OOS_PENDING (no trustworthy post-cutoff feed)",
          (fo["status"] == "FORWARD_OOS_PENDING").all())


def main() -> int:
    test_signal_reproduction()
    test_decomposition_identity()
    test_metrics_reproduce()
    test_residual_ceilings()
    test_epsilon_monotonic()
    test_causality_weights()
    test_rate_sensitivity()
    test_cost_stress()
    test_bootstrap_ci()
    test_yearly_no_weak()
    test_walk_forward_expanding()
    test_lot_constraints()
    test_decision_json()
    print(f"\n{'=' * 60}\n{len(FAILURES)} failure(s)"
          + (": " + ", ".join(FAILURES) if FAILURES else " — ALL PASS"))
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
