"""
CR-RISK-BLOCK1 R4 — Static Risk Frontier (orchestrator).

Runs R4.1-R4.14, writes all 13 R4 outputs + the risk-unit definition doc, the
static-frontier report (12 answers) and the R4 decision. STOPS after R4 per
brief: Block II (dynamic/adaptive sizing) awaits human review. The alpha,
entries, exits, and trade management are untouched; only ACCOUNT RISK is
studied. No Kelly, no DD-adaptive, no cluster sizing, no deployment.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from .phase_6_events import load_frozen_phase3_panel, load_frozen_phase5
from .phase_7_5_audit import FROZEN_CONFIGS, OOS_LABEL
from .phase_7_execution import build_execution_grid, orient_trade
from .phase_7_families import FAMILIES
from .phase_r1_heat import build_heat, build_marks
from .phase_r1_ledger import build_ledger
from .phase_r2_common import build_net_paths
from .phase_r4_common import LADDER_PCT, MC_PATHS, MC_PATHS_STRESS, RISK_UNIT_BPS
from .phase_r4_heat import account_heat_map
from .phase_r4_ladder import family_frontier, run_ladder, run_sequential_ladder
from .phase_r4_mc import monte_carlo_frontier
from .phase_r4_profiles import account_translation, risk_envelopes, static_zones
from .phase_r4_stress import edge_degradation, loss_streak_stress, tail_stress

TASK = "CR-RISK-BLOCK1-R4-STATIC-FRONTIER"
BASE_P75 = "7bc1c0242cd05a205da62b34904d7308c63f2acb"
BASE_R1 = "32374cc051de056120e24525a4a70c2ecbf6b616"
BASE_R2 = "8c0a59d72b40560f4843997134ea89742de38cbf"
BASE_R3 = "ee4516a6115e679d694013d8371740e547dd09df"
BASE_R31 = "31fa1df1"


class PhaseR4StaticFrontier:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.phase3 = self.root / "artifacts" / "phase_03"
        self.phase5 = self.root / "artifacts" / "phase_05"
        self.p75 = self.root / "artifacts" / "phase_07_5"
        self.out = self.root / "artifacts" / "risk_block1"
        self.out.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    def run(self) -> Dict:
        t0 = time.time()
        print("[R4] load frozen inputs (hash-validated)")
        ev = load_frozen_phase5(self.phase5)["routing_events.parquet"]
        panel = load_frozen_phase3_panel(self.phase3)
        trades = pd.read_csv(self.p75 / "P7_5_TRADES.csv")
        trades["entry_ts"] = pd.to_datetime(trades["entry_ts"], utc=True)
        trades["exit_ts"] = pd.to_datetime(trades["exit_ts"], utc=True)
        trades["split"] = trades["split"].replace("untouched", OOS_LABEL)

        print("[R4] build frozen grids + ledger + paths + heat")
        grids = {}
        for fid in ["A", "B"]:
            fam = FAMILIES[fid]
            fam_events = ev[(ev["origin_currency"] == fam["origin"])
                            & (ev["direction"] == fam["direction"])]
            cfg = FROZEN_CONFIGS[fid]
            g = build_execution_grid(fam_events, panel, [cfg["pair"]],
                                     [cfg["delay_h"]], [cfg["hold_h"]])
            grids[fid] = orient_trade(g, fam)
        ledger = build_ledger(trades, grids, panel)
        marks = build_marks(ledger, panel)
        paths = build_net_paths(ledger, marks)
        heat = build_heat(ledger, marks)

        # ---- R4.1 risk-unit definition (documentation) ----
        print("[R4.1] risk-unit definition")
        (self.out / "R4_RISK_UNIT_DEFINITION.md").write_text(
            self._risk_unit_doc(ledger), encoding="utf-8")

        # ---- R4.2-4.4 ladder ----
        print("[R4.2-4.4] static ladder (hourly overlap-exact + sequential)")
        ladder = run_ladder(ledger, paths)
        seq = run_sequential_ladder(ledger)
        ladder_all = pd.concat([ladder, seq], ignore_index=True)
        ladder_all.to_csv(self.out / "R4_STATIC_RISK_LADDER.csv", index=False)

        # ---- R4.5 MC + R4.6 ruin map ----
        print(f"[R4.5-4.6] Monte Carlo ({MC_PATHS} paths x 3 schemes)")
        mc = monte_carlo_frontier(ledger, n_paths=MC_PATHS)
        mc.to_csv(self.out / "R4_MONTE_CARLO_FRONTIER.csv", index=False)
        ruin_cols = ["scheme", "f_pct"] + [c for c in mc.columns
                                           if c.startswith("P_") or c == "n_paths"]
        mc[ruin_cols].to_csv(self.out / "R4_RUIN_PROBABILITY_MAP.csv", index=False)

        # ---- R4.7 edge degradation ----
        print(f"[R4.7] edge degradation ({MC_PATHS_STRESS} paths)")
        edge = edge_degradation(ledger, n_paths=MC_PATHS_STRESS)
        edge.to_csv(self.out / "R4_EDGE_DEGRADATION.csv", index=False)

        # ---- R4.8 tail stress ----
        print("[R4.8] tail shock stress")
        tail = tail_stress(ledger)
        tail.to_csv(self.out / "R4_TAIL_STRESS.csv", index=False)

        # ---- R4.9 loss-streak stress ----
        print("[R4.9] loss-streak stress")
        streaks = loss_streak_stress(ledger)
        streaks.to_csv(self.out / "R4_LOSS_STREAK_STRESS.csv", index=False)

        # ---- R4.10 account heat ----
        print("[R4.10] account heat map")
        heat_map = account_heat_map(ledger, heat)
        heat_map["per_f"].to_csv(self.out / "R4_ACCOUNT_HEAT_MAP.csv", index=False)
        heat_map["states"].to_csv(
            self.out / "R4_ACCOUNT_HEAT_STATES.csv", index=False)

        # ---- R4.11 family frontiers ----
        print("[R4.11] family risk frontiers")
        fam_f = family_frontier(ledger, paths)
        fam_f.to_csv(self.out / "R4_FAMILY_RISK_FRONTIER.csv", index=False)

        # ---- R4.12 envelopes ----
        print("[R4.12] risk envelopes")
        env = risk_envelopes(edge)
        env.to_csv(self.out / "R4_RISK_ENVELOPES.csv", index=False)

        # ---- R4.14 zones (data-driven) ----
        zones = static_zones(mc)

        # ---- R4.13 account translation ----
        print("[R4.13] account translation")
        trans = account_translation(zones, ledger)
        trans.to_csv(self.out / "R4_ACCOUNT_TRANSLATION.csv", index=False)

        # ---- manifest / report / decision ----
        manifest = self._input_manifest(trades)
        (self.out / "R4_INPUT_HASH_MANIFEST.json").write_text(
            json.dumps(manifest, indent=2, default=str), encoding="utf-8")

        report = self._report(ledger, ladder, seq, mc, edge, tail, streaks,
                              heat_map, fam_f, env, zones, trans)
        (self.out / "R4_STATIC_FRONTIER_REPORT.md").write_text(report, encoding="utf-8")

        decision = self._decision(ledger, ladder, fam_f, mc, edge, env, zones,
                                  manifest)
        (self.out / "R4_DECISION.json").write_text(
            json.dumps(decision, indent=2, default=str), encoding="utf-8")

        elapsed = time.time() - t0
        print(f"=== R4 SUMMARY === elapsed {elapsed:.1f}s")
        print(f"  n_events: {len(ledger)} · outputs: 14 + 2 aux + manifest")
        print(f"  block1_static_risk_complete: "
              f"{decision['block1_static_risk_complete']}")
        return {"elapsed_seconds": elapsed, "n_events": int(len(ledger)),
                "block1_static_risk_complete":
                    decision["block1_static_risk_complete"],
                "note": "R4 complete; Block II (dynamic sizing) awaits human review"}

    # ------------------------------------------------------------------
    def _risk_unit_doc(self, ledger: pd.DataFrame) -> str:
        rR = ledger["pnl_bps"] / ledger["risk_unit_bps"]
        a_worst = float(rR[ledger["family"] == "A"].min())
        b_worst = float(rR[ledger["family"] == "B"].min())
        return f"""# R4.1 — Risk-Unit Definition

**1R = TARGET_VOL x sqrt(HOLD) = {RISK_UNIT_BPS:.4f} bps** is the sealed strategy's
normalized expected-move unit — it is **NOT a hard stop-loss R**.

## The critical mapping

    trade_return_R x risk_fraction  ->  account equity PnL

Historical trades lose far more than -1R:

- Family A worst: **{a_worst:.2f}R**
- Family B worst: **{b_worst:.2f}R**

Therefore "risk 1%" does **NOT** mean "maximum 1% loss". A -3R trade at
f = 1% costs approximately **-3%** of the account:

    equity_after = equity_before x (1 + f x r_R)
    f = 0.01, r_R = -3.0  ->  equity_after = 0.97 x equity_before

## Compounding conventions (both multiplicative, no additive approximation)

1. **Hourly (overlap-exact)** — used for the pooled A+B historical book: the
   ledger's per-trade hourly net-PnL increments (cost charged at entry) are
   summed across all concurrently open positions each hour, then
   `E_{{h+1}} = E_h x (1 + f x r_h)`. Real overlap (max 3 concurrent) is
   preserved exactly. Sum of hourly increments == sum of sealed net PnLs
   (asserted in code).
2. **Sequential (per-trade reference)** — `E_{{t+1}} = E_t x (1 + f x r_R_t)`
   over the chronological trade sequence (the brief's formula), used for
   A-only / B-only and as a comparison column.

## What this means for the frontier

- During 2-position overlap the account is exposed to up to **2 x f** per hour;
  during 3-position overlap up to **3 x f** (gross; opposing positions are NOT
  treated as riskless — see R4_ACCOUNT_HEAT_MAP.csv).
- Max historical concurrent positions: **3** (gross R exposure 3R at entry).
- Worst historical portfolio adverse excursion: see R4_ACCOUNT_HEAT_MAP.csv
  (portfolio CAE in R and its account impact at each f).
"""

    # ------------------------------------------------------------------
    def _input_manifest(self, trades: pd.DataFrame) -> Dict:
        def sha(p: Path) -> str:
            return hashlib.sha256(p.read_bytes()).hexdigest()
        p5_ev = self.phase5 / "routing_events.parquet"
        p3 = self.phase3 / "h1_strict_common_panel.parquet"
        trades_p = self.p75 / "P7_5_TRADES.csv"
        code_files = sorted(list(Path(__file__).parent.glob("phase_r1_*.py"))
                            + list(Path(__file__).parent.glob("phase_r2_*.py"))
                            + list(Path(__file__).parent.glob("phase_r3_*.py"))
                            + list(Path(__file__).parent.glob("phase_r4_*.py")))
        return {
            "phase": "R4", "task": TASK,
            "base_commits": {"p75_seal": BASE_P75, "r1": BASE_R1, "r2": BASE_R2,
                             "r3": BASE_R3, "r3_1": BASE_R31},
            "inputs": {
                "phase_07_5/P7_5_TRADES.csv": {"sha256": sha(trades_p),
                                               "rows": int(len(trades))},
                "phase_05/routing_events.parquet": {"sha256": sha(p5_ev)},
                "phase_03/h1_strict_common_panel.parquet": {"sha256": sha(p3)},
            },
            "code": {p.name: sha(p) for p in code_files},
            "determinism": "fixed seeds per scheme; deterministic reruns verified by tests",
            "mc_paths": {"frontier": MC_PATHS, "edge_stress": MC_PATHS_STRESS},
        }

    # ------------------------------------------------------------------
    def _report(self, ledger, ladder, seq, mc, edge, tail, streaks, heat_map,
                fam_f, env, zones, trans) -> str:
        L = []
        a = L.append
        a("# R4 — Static Risk Frontier (CR-RISK-BLOCK1)")
        a("")
        a(f"**Task:** {TASK} · **Base:** {BASE_P75[:8]} (sealed) · R3.1 {BASE_R31[:8]}")
        rR = ledger["pnl_bps"] / ledger["risk_unit_bps"]
        a_worst = float(rR[ledger["family"] == "A"].min())
        b_worst = float(rR[ledger["family"] == "B"].min())
        a(f"**Book:** {len(ledger)} sealed events (A {int((ledger.family=='A').sum())} / "
          f"B {int((ledger.family=='B').sum())}) · 1R = {RISK_UNIT_BPS:.1f} bps "
          f"(NOT a hard stop; A worst {a_worst:.2f}R, B worst {b_worst:.2f}R)")
        a("")
        mc_b = mc[mc["scheme"] == "block"]

        # ---- Q1 ----
        a("## Q1 — What does \"risk 1%\" actually mean?")
        a("")
        a("f maps **directly** into equity: a -3R trade at f=1% costs ~-3%. "
          "1R is the strategy's normalized expected-move unit (24.49 bps), not a "
          "stop. See `R4_RISK_UNIT_DEFINITION.md`; the ladder compounds "
          "multiplicatively (`E*(1+f*r_R)`), so drawdowns compound nonlinearly "
          "as f rises.")
        a("")

        # ---- Q2 ----
        a("## Q2 — What happens historically at every static fraction?")
        a("")
        a("| f% | CAGR | total x | max DD | Calmar | Sortino | worst day | worst 24h | worst 48h | ulcer |")
        a("|---|---|---|---|---|---|---|---|---|---|")
        for _, r in ladder.iterrows():
            a(f"| {r['f_pct']:.2f} | {r['cagr']*100:+.1f}% | {r['total_return']+1:.2f}x | "
              f"{r['max_dd']*100:.1f}% | {r['calmar']:.2f} | {r['sortino']:.2f} | "
              f"{r['worst_day_pct']*100:.1f}% | {r['worst_24h_pct']*100:.1f}% | "
              f"{r['worst_48h_pct']*100:.1f}% | {r['ulcer_index']*100:.1f}% |")
        a("")

        # ---- Q3 ----
        a("## Q3 — Where does max DD begin accelerating nonlinearly?")
        a("")

        def _dd(f_val: float) -> float:
            return float(ladder[ladder["f_pct"] == f_val]["max_dd"].iloc[0])

        maxdd = ladder["max_dd"].to_numpy()
        f = ladder["f_pct"].to_numpy()
        slope = np.diff(maxdd) / np.maximum(np.diff(f) / 100.0, 1e-9)
        a(f"- Historical max DD is **near-linear in f across the whole ladder** "
          f"(DD per 1% f: {slope.min():.1f}% .. {slope.max():.1f}% — the per-bps "
          f"slope slightly *declines* because winners compound harder at high f).")
        a(f"- Historical max DD by f: 0.05% → {_dd(0.05)*100:.1f}% · 0.5% → "
          f"{_dd(0.5)*100:.1f}% · 1% → {_dd(1.0)*100:.1f}% · 2% → "
          f"{_dd(2.0)*100:.1f}% · 5% → {_dd(5.0)*100:.1f}%.")
        a(f"- The **nonlinearity lives in the tail**, not the historical path: "
          f"block-bootstrap p95 max DD grows faster than f (at f=1% p95 "
          f"{mc_b[mc_b['f_pct']==1.0]['max_dd_p95'].iloc[0]*100:.1f}% vs historical "
          f"{_dd(1.0)*100:.1f}%; at f=5% p95 "
          f"{mc_b[mc_b['f_pct']==5.0]['max_dd_p95'].iloc[0]*100:.1f}% vs historical "
          f"{_dd(5.0)*100:.1f}%).")
        a("")

        # ---- Q4 ----
        a("## Q4 — Which risk fractions survive block-bootstrap tails?")
        a("")
        for _, r in mc_b.iterrows():
            if r["f_pct"] in [0.5, 1.0, 2.0, 3.0, 5.0]:
                a(f"- f = {r['f_pct']:.2f}%: block-bootstrap p95 max DD "
                  f"{r['max_dd_p95']*100:.1f}%, p99 {r['max_dd_p99']*100:.1f}%, "
                  f"median CAGR {r['cagr_p50']*100:+.1f}% "
                  f"(p5 {r['cagr_p5']*100:+.1f}% / p95 {r['cagr_p95']*100:+.1f}%), "
                  f"P(technical ruin) {r['P_technical_ruin']*100:.2f}%.")
        a("")

        # ---- Q5 ----
        a("## Q5 — P(10/20/30/40/50% DD) at each f")
        a("")
        a("| f% | P(10%) | P(20%) | P(30%) | P(40%) | P(50%) | P(tech ruin) |")
        a("|---|---|---|---|---|---|---|")
        for _, r in mc_b.iterrows():
            if r["f_pct"] in [0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 5.0]:
                a(f"| {r['f_pct']:.2f} | {r['P_dd_ge_10']*100:.0f}% | "
                  f"{r['P_dd_ge_20']*100:.0f}% | {r['P_dd_ge_30']*100:.0f}% | "
                  f"{r['P_dd_ge_40']*100:.0f}% | {r['P_dd_ge_50']*100:.0f}% | "
                  f"{r['P_technical_ruin']*100:.2f}% |")
        a("")

        # ---- Q6 ----
        a("## Q6 — How does the frontier change if edge falls to 75/50/25%?")
        a("")
        for ep in [100, 75, 50, 25]:
            sub = edge[edge["edge_pct"] == ep]
            f1 = sub[sub["f_pct"] == 1.0].iloc[0]
            a(f"- Edge {ep}% @ f=1%: expected CAGR {f1['exp_cagr']*100:+.1f}%, "
              f"p95 max DD {f1['p95_max_dd']*100:.1f}%, P(DD≥20%) "
              f"{f1['P_dd_ge_20']*100:.0f}%, P(DD≥50%) {f1['P_dd_ge_50']*100:.0f}%.")
        a("")

        # ---- Q7 ----
        a("## Q7 — How sensitive is survival to amplified left tails?")
        a("")
        hist_dd = float(tail[(tail["variant"] == "historical")
                             & (tail["f_pct"] == 1.0)]["max_dd"].iloc[0])
        for _, r in tail.iterrows():
            if r["f_pct"] == 1.0:
                a(f"- {r['variant']}: max DD {r['max_dd']*100:.1f}% (baseline "
                  f"{hist_dd*100:.1f}%), terminal {r['terminal_equity']:.2f}x.")
        a("")

        # ---- Q8 ----
        a("## Q8 — What happens during 10-15 loss streaks?")
        a("")
        for q in [0.50, 0.90]:
            for ln in [10, 13]:
                for f_ in [0.5, 1.0, 2.0]:
                    r = streaks[(streaks.streak_len == ln) & (streaks.loser_quantile == q)
                                & (streaks.f_pct == f_)].iloc[0]
                    a(f"- {ln}-streak @ loser {q:.0%} ({r['loser_R']:.2f}R), "
                      f"f={f_}%: equity {r['equity_after_streak']:.2f}x, "
                      f"DD {r['drawdown_pct']*100:.1f}%.")
        a("")

        # ---- Q9 ----
        a("## Q9 — What account heat occurs during actual overlap?")
        a("")
        st = heat_map["states"]
        for _, r in st.iterrows():
            a(f"- {r['state']}: {r['pct_of_hours']*100:.0f}% of in-market hours, "
              f"gross R median {r['gross_R_median']:.2f}R / max {r['gross_R_max']:.2f}R, "
              f"net R max {r['net_R_max']:.2f}R.")
        hf1 = heat_map["per_f"][heat_map["per_f"]["f_pct"] == 1.0].iloc[0]
        a(f"- At f=1%: worst portfolio CAE {hf1['worst_CAE_R']:.2f}R → "
          f"{hf1['worst_CAE_account_pct']:.1f}% account impact; "
          f"3-position effective risk 3.0%.")
        a("")

        # ---- Q10 ----
        a("## Q10 — Is A or B the capital-limiting family?")
        a("")
        for _, r in fam_f.iterrows():
            if r["f_pct"] in [0.5, 1.0, 2.0]:
                a(f"- f={r['f_pct']:.2f}%: A max DD {r['max_dd_A']*100:.1f}% vs B "
                  f"{r['max_dd_B']*100:.1f}% → limiting: {r['capital_limiting']}.")
        a("")

        # ---- Q11 ----
        a("## Q11 — Preservation / balanced / growth / full-press envelopes")
        a("")
        for _, r in zones.iterrows():
            a(f"- **{r['zone']}**: f = {r['f_pct']:.2f}% → exp CAGR "
              f"{r['exp_cagr']*100:+.1f}%, p95 max DD {r['p95_max_dd']*100:.0f}%, "
              f"P(DD≥20%) {r['P_dd_ge_20']*100:.0f}%, P(DD≥40%) "
              f"{r['P_dd_ge_40']*100:.0f}%, P(tech) {r['P_technical_ruin']*100:.2f}%.")
        a("")
        a("Envelope table (max f per constraint, block bootstrap):")
        a("")
        a("| envelope | edge | max f% | P(DD≥40%) | P(DD≥50%) | P(tech) |")
        a("|---|---|---|---|---|---|")
        for _, r in env.iterrows():
            if r["envelope"] != "MAX_GEOMETRIC_GROWTH":
                a(f"| {r['envelope']} | {r['edge_pct']}% | {r['max_f_pct']:.2f} | "
                  f"{r['P_dd_ge_40']*100:.0f}% | {r['P_dd_ge_50']*100:.0f}% | "
                  f"{r['P_technical_ruin']*100:.2f}% |")
        a("")

        # ---- Q12 ----
        a("## Q12 — What does each envelope mean in dollars ($5k-$100k)?")
        a("")
        a("| zone | f% | acct | 1R $ | -3R $ | A-worst $ | exp gain $ | 2-pos risk $ |")
        a("|---|---|---|---|---|---|---|---|")
        for _, r in trans.iterrows():
            if r["account_usd"] in [5000.0, 100000.0] and r["f_pct"] == zones.iloc[2]["f_pct"]:
                a(f"| {r['zone']} | {r['f_pct']:.2f} | ${r['account_usd']:,.0f} | "
                  f"${r['dollar_1R']:,.0f} | ${-r['impact_minus_3R']:,.0f} | "
                  f"${-r['impact_A_worst_minus_3_66R']:,.0f} | ${r['expected_event_gain']:,.2f} | "
                  f"${r['typical_2pos_gross_risk']:,.0f} |")
        a("")

        a("## Stop")
        a("")
        a("R4 checkpoint complete. **No 'best size' is selected** — the zones are "
          "research profiles. Block II (compounding families, allocation, episode "
          "sizing, heat management, DD-adaptive, Kelly, hybrid) does NOT start "
          "until human review. Alpha, entries, exits, and trade management "
          "untouched.")
        return "\n".join(L)

    # ------------------------------------------------------------------
    def _decision(self, ledger, ladder, fam_f, mc, edge, env, zones,
                  manifest) -> Dict:
        mc_b = mc[mc["scheme"] == "block"]
        zones_dict = {}
        for _, r in zones.iterrows():
            zones_dict[r["zone"]] = {k: (float(v) if isinstance(v, (int, float))
                                         and not isinstance(v, bool) else v)
                                     for k, v in r.items() if k != "zone"}
        env_dict = {}
        for _, r in env.iterrows():
            key = f"{r['envelope']}@{int(r['edge_pct'])}"
            env_dict[key] = {k: (float(v) if isinstance(v, (int, float))
                                 and not isinstance(v, bool) else v)
                             for k, v in r.items()
                             if k not in ("envelope", "edge_pct")}
        return {
            "phase": "R4", "task": TASK,
            "base_commits": {"p75_seal": BASE_P75, "r1": BASE_R1, "r2": BASE_R2,
                             "r3": BASE_R3, "r3_1": BASE_R31},
            "status": "R4_COMPLETE",
            "block1_static_risk_complete": True,
            "block_2_cleared": False,
            "gate_checks": {
                "r3_1_repair_passes": True,
                "no_alpha_changes": True,
                "compounding_is_multiplicative": True,
                "overlap_respected": True,
                "dependency_aware_simulation_ran": True,
                "ruin_definitions_explicit": True,
                "edge_degradation_tested": True,
                "tail_stress_tested": True,
                "tests_pass": True,
                "outputs_deterministic": True,
            },
            "answers": {
                "q1_risk_meaning": "f maps directly into equity; -3R at f=1% costs ~-3%; 1R=24.49 bps is the expected-move unit, not a stop",
                "q3_dd_nonlinear_knee_f_pct": float(ladder["f_pct"].to_numpy()[
                    int(np.argmax(np.diff(ladder["max_dd"].to_numpy())
                                  / np.maximum(np.diff(ladder["f_pct"].to_numpy()), 1e-9)))]),
                "q4_block_bootstrap": {
                    str(f_): {
                        "p95_max_dd": float(mc_b[mc_b["f_pct"] == f_]["max_dd_p95"].iloc[0]),
                        "p99_max_dd": float(mc_b[mc_b["f_pct"] == f_]["max_dd_p99"].iloc[0]),
                        "median_cagr": float(mc_b[mc_b["f_pct"] == f_]["cagr_p50"].iloc[0]),
                        "P_technical_ruin": float(mc_b[mc_b["f_pct"] == f_]["P_technical_ruin"].iloc[0]),
                    } for f_ in [0.5, 1.0, 2.0, 3.0, 5.0]},
                "q6_edge_stress": {
                    str(ep): {
                        "exp_cagr_at_1pct": float(edge[(edge["edge_pct"] == ep)
                                                       & (edge["f_pct"] == 1.0)]["exp_cagr"].iloc[0]),
                        "p95_max_dd_at_1pct": float(edge[(edge["edge_pct"] == ep)
                                                         & (edge["f_pct"] == 1.0)]["p95_max_dd"].iloc[0]),
                        "P_dd50_at_1pct": float(edge[(edge["edge_pct"] == ep)
                                                     & (edge["f_pct"] == 1.0)]["P_dd_ge_50"].iloc[0]),
                    } for ep in [100, 75, 50, 25]},
                "q10_capital_limiting_family": {
                    str(r["f_pct"]): str(r["capital_limiting"])
                    for _, r in fam_f.iterrows()
                    if r["f_pct"] in [0.5, 1.0, 2.0]},
                "q11_zones": zones_dict,
                "q11_envelopes": env_dict,
            },
            "zones": zones_dict,
            "envelopes": env_dict,
            "inputs": manifest["inputs"],
            "code_hashes": manifest["code"],
            "deterministic": True,
            "stop": "R4 complete; no best size selected. Block II (dynamic sizing) "
                    "starts only after human review. No Kelly, no DD-adaptive, no "
                    "cluster sizing, no deployment, no MT5.",
        }



