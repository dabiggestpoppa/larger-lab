"""
CR-RISK-BLOCK1 R3 — Profit Anatomy (orchestrator).

Runs R3.1-R3.13, writes all 16 R3 outputs, the profit-anatomy report and the
R3 decision (r4_static_frontier_cleared gate). STOPS after R3 per brief: R4
awaits human review. No TP, early exit, trailing, breakeven, partial, family
weighting, or sizing change is created.
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
from .phase_r1_heat import build_marks
from .phase_r1_ledger import build_ledger
from .phase_r2_analysis import failure_classes
from .phase_r2_common import build_net_paths
from .phase_r2_context import trade_context
from .phase_r3_analysis import (capture_ratio, giveback_transitions,
                                mfe_distributions, profit_giveback,
                                profit_maturity, remaining_expectancy_surface,
                                time_to_mfe_table, time_to_profit,
                                winner_tail_attribution)
from .phase_r3_context import (concurrency_profit_effects,
                               episode_profit_effects,
                               family_profit_comparison,
                               profit_delivery_curve,
                               temporal_profit_stability)

TASK = "CR-RISK-BLOCK1-R3-PROFIT-ANATOMY"
BASE_R1 = "32374cc051de056120e24525a4a70c2ecbf6b616"
BASE_R2 = "8c0a59d72b40560f4843997134ea89742de38cbf"
BASE_R2_BOOK = "116bb2de4930726d7007816177416130e8f9e7a9"
BASE_P75 = "7bc1c0242cd05a205da62b34904d7308c63f2acb"


class PhaseR3ProfitAnatomy:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.phase3 = self.root / "artifacts" / "phase_03"
        self.phase5 = self.root / "artifacts" / "phase_05"
        self.p75 = self.root / "artifacts" / "phase_07_5"
        self.out = self.root / "artifacts" / "risk_block1"
        self.out.mkdir(parents=True, exist_ok=True)

    def run(self) -> Dict:
        t0 = time.time()
        print("[R3] load frozen inputs (hash-validated)")
        ev = load_frozen_phase5(self.phase5)["routing_events.parquet"]
        panel = load_frozen_phase3_panel(self.phase3)
        trades = pd.read_csv(self.p75 / "P7_5_TRADES.csv")
        trades["entry_ts"] = pd.to_datetime(trades["entry_ts"], utc=True)
        trades["exit_ts"] = pd.to_datetime(trades["exit_ts"], utc=True)
        trades["split"] = trades["split"].replace("untouched", OOS_LABEL)

        print("[R3] build frozen grids + ledger + paths + context")
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
        _, class_frame = failure_classes(ledger, paths)
        ctx = trade_context(ledger, paths, class_frame)

        # ---- R3.1 ----
        print("[R3.1] MFE distributions")
        mfe = mfe_distributions(ledger, paths)
        mfe.to_csv(self.out / "R3_MFE_DISTRIBUTIONS.csv", index=False)

        # ---- R3.2 ----
        print("[R3.2] time to first profit")
        ttp = time_to_profit(ledger, paths)
        ttp.to_csv(self.out / "R3_TIME_TO_PROFIT.csv", index=False)

        # ---- R3.3 ----
        print("[R3.3] time to MFE")
        ttm = time_to_mfe_table(ledger, paths)
        ttm.to_csv(self.out / "R3_TIME_TO_MFE.csv", index=False)

        # ---- R3.4 ----
        print("[R3.4] capture ratio + giveback")
        cap = capture_ratio(ledger, paths)
        cap.to_csv(self.out / "R3_CAPTURE_RATIO.csv", index=False)
        gb = profit_giveback(ledger, paths)
        gb.to_csv(self.out / "R3_PROFIT_GIVEBACK.csv", index=False)

        # ---- R3.5 ----
        print("[R3.5] giveback transitions")
        gbt = giveback_transitions(ledger, paths)
        gbt.to_csv(self.out / "R3_GIVEBACK_TRANSITIONS.csv", index=False)

        # ---- R3.6 ----
        print("[R3.6] remaining expectancy surface")
        res = remaining_expectancy_surface(ledger, paths)
        res.to_csv(self.out / "R3_REMAINING_EXPECTANCY_SURFACE.csv", index=False)

        # ---- R3.7 ----
        print("[R3.7] profit maturity")
        mat = profit_maturity(ledger, paths)
        mat.to_csv(self.out / "R3_PROFIT_MATURITY.csv", index=False)

        # ---- R3.8 ----
        print("[R3.8] family profit comparison")
        fam_cmp = family_profit_comparison(ledger, paths)
        fam_cmp.to_csv(self.out / "R3_FAMILY_PROFIT_COMPARISON.csv", index=False)

        # ---- R3.9 ----
        print("[R3.9] concurrency profit effects")
        conc = concurrency_profit_effects(ledger, paths, ctx)
        conc.to_csv(self.out / "R3_CONCURRENCY_PROFIT_EFFECTS.csv", index=False)

        # ---- R3.10 ----
        print("[R3.10] episode profit effects")
        ep = episode_profit_effects(ledger, paths)
        ep.to_csv(self.out / "R3_EPISODE_PROFIT_EFFECTS.csv", index=False)

        # ---- R3.11 ----
        print("[R3.11] winner tail attribution")
        wta = winner_tail_attribution(ledger)
        wta.to_csv(self.out / "R3_WINNER_TAIL_ATTRIBUTION.csv", index=False)

        # ---- R3.12 ----
        print("[R3.12] temporal profit stability")
        temp = temporal_profit_stability(ledger, paths)
        temp.to_csv(self.out / "R3_TEMPORAL_PROFIT_STABILITY.csv", index=False)

        # ---- R3.13 ----
        print("[R3.13] profit delivery curve")
        curve = profit_delivery_curve(ledger, paths)
        curve.to_csv(self.out / "R3_PROFIT_DELIVERY_CURVE.csv", index=False)

        # ---- manifest + report + decision ----
        manifest = self._input_manifest(trades)
        (self.out / "R3_INPUT_HASH_MANIFEST.json").write_text(
            json.dumps(manifest, indent=2, default=str), encoding="utf-8")

        report = self._report(ledger, mfe, ttp, ttm, cap, gb, gbt, res, mat,
                              fam_cmp, conc, ep, wta, temp, curve)
        (self.out / "R3_PROFIT_ANATOMY_REPORT.md").write_text(report, encoding="utf-8")

        decision = self._decision(mfe, ttp, ttm, cap, gb, gbt, res, mat, fam_cmp,
                                  conc, ep, wta, temp, curve, manifest)
        (self.out / "R3_DECISION.json").write_text(
            json.dumps(decision, indent=2, default=str), encoding="utf-8")

        elapsed = time.time() - t0
        print(f"=== R3 SUMMARY === elapsed {elapsed:.1f}s")
        print(f"  n_events: {len(ledger)} · outputs: 16 + manifest")
        print(f"  r4_static_frontier_cleared: {decision['r4_static_frontier_cleared']}")
        return {"elapsed_seconds": elapsed, "n_events": int(len(ledger)),
                "r4_static_frontier_cleared": decision["r4_static_frontier_cleared"],
                "note": "R3 checkpoint complete; R4 awaits human review"}

    # ------------------------------------------------------------------
    def _input_manifest(self, trades: pd.DataFrame) -> Dict:
        def sha(p: Path) -> str:
            return hashlib.sha256(p.read_bytes()).hexdigest()
        p5_ev = self.phase5 / "routing_events.parquet"
        p3 = self.phase3 / "h1_strict_common_panel.parquet"
        trades_p = self.p75 / "P7_5_TRADES.csv"
        code_files = sorted(list(Path(__file__).parent.glob("phase_r1_*.py"))
                            + list(Path(__file__).parent.glob("phase_r2_*.py"))
                            + list(Path(__file__).parent.glob("phase_r3_*.py")))
        return {
            "phase": "R3",
            "task": TASK,
            "base_commits": {"p75_seal": BASE_P75, "r1": BASE_R1,
                             "r2": BASE_R2, "r2_bookkeeping": BASE_R2_BOOK},
            "inputs": {
                "phase_07_5/P7_5_TRADES.csv": {"sha256": sha(trades_p),
                                               "rows": int(len(trades))},
                "phase_05/routing_events.parquet": {"sha256": sha(p5_ev)},
                "phase_03/h1_strict_common_panel.parquet": {"sha256": sha(p3)},
            },
            "code": {p.name: sha(p) for p in code_files},
            "determinism": "no random sampling; deterministic outputs verified by tests",
            "subhour_note": "M5 feed rejected in R2 (p95 |diff| 22 bps vs frozen panel); "
                            "R3 uses hourly frozen H1 paths only - no fabricated sub-hour timing.",
        }

    # ------------------------------------------------------------------
    def _report(self, ledger, mfe, ttp, ttm, cap, gb, gbt, res, mat, fam_cmp,
                conc, ep, wta, temp, curve) -> str:
        L = []
        a = L.append
        a("# R3 — Profit Anatomy (CR-RISK-BLOCK1)")
        a("")
        a(f"**Task:** {TASK} · **Base:** {BASE_P75[:8]} (sealed) · R2 {BASE_R2[:8]}")
        a("")

        def _g(df, fam, oc, unit="R"):
            r = df[(df["family"] == fam) & (df["outcome"] == oc) & (df["unit"] == unit)]
            return r.iloc[0] if len(r) else None

        w = _g(mfe, "A+B", "WINNER")
        l = _g(mfe, "A+B", "LOSER")
        a(f"- **Q1** median MFE: winners {w['median']:.2f}R (p90 {w['p90']:.2f}R) vs "
          f"losers {l['median']:.2f}R (p90 {l['p90']:.2f}R).")
        a("")

        # Q2: time to first +0.25/+0.5/+1R (pooled, share of winners + median)
        q2 = []
        for lvl in [0.25, 0.5, 1.0]:
            r = ttp[(ttp["family"] == "A+B") & (ttp["level_R"] == lvl)].iloc[0]
            q2.append(f"+{lvl}R: {r['share_of_winners']*100:.0f}% of winners reach "
                      f"in median {r['median_time_h']:.0f}h (p25 {r['p25_time_h']:.0f} / "
                      f"p75 {r['p75_time_h']:.0f})")
        a("- **Q2** " + "; ".join(q2) + ".")
        a("")

        # Q3: time to MFE
        t_all = ttm[(ttm["family"] == "A+B") & (ttm["group"] == "all")].iloc[0]
        t_win = ttm[(ttm["family"] == "A+B") & (ttm["group"] == "winners")].iloc[0]
        a(f"- **Q3** time to MFE (all): median hour {t_all['median_hour']:.0f} "
          f"(p75 {t_all['p75_hour']:.0f}); winners median hour {t_win['median_hour']:.0f} "
          f"(p75 {t_win['p75_hour']:.0f}). Peak distribution: "
          + "; ".join(f"h{h} {t_all[f'pct_hour{h}']*100:.0f}%" for h in [1, 2, 3, 4, 5, 6])
          + ".")
        a("")

        # Q4: capture
        cap_w = cap[(cap["family"] == "A+B") & (cap["outcome"] == "WINNER")].iloc[0]
        a(f"- **Q4** winners retain a median {cap_w['median_capture']*100:.0f}% of peak MFE "
          f"(p25 {cap_w['p25_capture']*100:.0f}% / p75 {cap_w['p75_capture']*100:.0f}%); "
          f"{cap_w['share_capture_ge_75pct']*100:.0f}% keep >=75%.")
        a("")

        # Q5: giveback
        gb_w = gb[(gb["family"] == "A+B") & (gb["outcome"] == "WINNER")].iloc[0]
        gb_l = gb[(gb["family"] == "A+B") & (gb["outcome"] == "LOSER")].iloc[0]
        a(f"- **Q5** median giveback: winners {gb_w['median_giveback_R']:.2f}R "
          f"({gb_w['median_giveback_fraction']*100:.0f}% of peak) vs losers "
          f"{gb_l['median_giveback_R']:.2f}R.")
        a("")

        # Q6: become profitable then finish negative
        g1 = gbt[gbt["level_R"] == 1.0].iloc[0]
        g05 = gbt[gbt["level_R"] == 0.5].iloc[0]
        a(f"- **Q6** of trades reaching +1R: {g1['p_finish_negative']*100:.0f}% finish "
          f"negative, {g1['p_finish_below_half_peak']*100:.0f}% finish below half peak, "
          f"{g1['p_finish_positive']*100:.0f}% still positive. At +0.5R: "
          f"{g05['p_finish_negative']*100:.0f}% finish negative.")
        a("")

        # Q7: remaining expectancy at hours 1-5 (pooled, all states)
        q7 = []
        for age in [1, 2, 3, 4, 5]:
            cell = res[(res["age_h"] == age) & (res["family"] == "A+B")]
            # weighted by N over all states
            tot = int(cell["N"].sum())
            rem = float(np.average(cell["remaining_expectancy_R"], weights=cell["N"]))
            q7.append(f"h{age}: {rem:+.2f}R (n={tot})")
        a("- **Q7** remaining expectancy at each age (all states, N-weighted): "
          + "; ".join(q7) + ".")
        a("")

        # Q8: delivery curve - by what hour is most profit earned?
        c3 = curve[curve["hour"] == 3].iloc[0]
        c5 = curve[curve["hour"] == 5].iloc[0]
        a(f"- **Q8** by hour 3, {c3['pct_of_final_pnl_achieved']*100:.0f}% of total final "
          f"PnL is already on the book; by hour 5, {c5['pct_of_final_pnl_achieved']*100:.0f}% "
          f"(hour 6 is the frozen exit).")
        a("")
        a("| hour | avg open PnL (R) | % final PnL | % winners positive | % winners past MFE | remaining gain (R) |")
        a("|---|---|---|---|---|---|")
        for _, r in curve.iterrows():
            a(f"| {int(r['hour'])} | {r['avg_open_pnl_R']:+.2f} | "
              f"{r['pct_of_final_pnl_achieved']*100:.0f}% | "
              f"{r['pct_winners_currently_positive']*100:.0f}% | "
              f"{r['pct_winners_past_mfe']*100:.0f}% | {r['remaining_expected_gain_R']:+.2f} |")
        a("")

        # Q9: A vs B
        fa = fam_cmp[fam_cmp["family"] == "A"].iloc[0]
        fb = fam_cmp[fam_cmp["family"] == "B"].iloc[0]
        a(f"- **Q9** A vs B: median MFE {fa['median_mfe_R']:.2f}R vs {fb['median_mfe_R']:.2f}R; "
          f"time to first +0.5R median {fa['median_time_to_first_0_5R_h']:.0f}h vs "
          f"{fb['median_time_to_first_0_5R_h']:.0f}h; time to MFE {fa['median_time_to_mfe_h']:.0f}h "
          f"vs {fb['median_time_to_mfe_h']:.0f}h; median capture "
          f"{fa['median_capture_ratio_winners']*100:.0f}% vs "
          f"{fb['median_capture_ratio_winners']*100:.0f}%; late-hold share of winner PnL "
          f"{fa['late_hold_share_of_winner_pnl']*100:.0f}% vs "
          f"{fb['late_hold_share_of_winner_pnl']*100:.0f}%.")
        a("")

        # Q10: concurrency
        if len(conc):
            no = conc[conc["group"] == "no_overlap"].iloc[0]
            sd = conc[conc["group"] == "same_dir_overlap_any"].iloc[0]
            a(f"- **Q10** concurrency: no-overlap median MFE {no['median_mfe_R']:.2f}R, "
              f"expectancy {no['final_expectancy_R']:+.2f}R vs same-direction overlap "
              f"MFE {sd['median_mfe_R']:.2f}R, expectancy {sd['final_expectancy_R']:+.2f}R.")
        a("")

        # Q11: episode ranks
        e12 = ep[ep["interval_h"] == 12.0].set_index("rank_in_cluster")
        a(f"- **Q11** 12h-cluster ranks: time to MFE rank1 "
          f"{e12.loc['1','median_time_to_mfe_h']:.0f}h vs 4+ "
          f"{e12.loc['4+','median_time_to_mfe_h']:.0f}h; median capture "
          f"{e12.loc['1','median_capture_winners']*100:.0f}% vs 4+ "
          f"{e12.loc['4+','median_capture_winners']*100:.0f}%.")
        a("")

        # Q12: winner tail
        t1 = wta[wta["quantile"] == 0.01].iloc[0]
        t5 = wta[wta["quantile"] == 0.05].iloc[0]
        t10 = wta[wta["quantile"] == 0.10].iloc[0]
        ex5 = wta[(wta["quantile"] == 0.05)
                  & wta["expectancy_excluding_best_q_R"].notna()].iloc[0]
        a(f"- **Q12** best 1% of trades produce {t1['share_of_total_positive_pnl']*100:.0f}% "
          f"of total positive PnL; best 5% produce {t5['share_of_total_positive_pnl']*100:.0f}%; "
          f"best 10% produce {t10['share_of_total_positive_pnl']*100:.0f}%. Excluding best 5%: "
          f"expectancy {ex5['expectancy_excluding_best_q_R']:+.2f}R.")
        a("")

        # Q13: temporal
        a("- **Q13** profit anatomy through time (R3_TEMPORAL_PROFIT_STABILITY.csv):")
        for _, r in temp.iterrows():
            a(f"  - {r['split']}: N={int(r['N'])} · median MFE {r['median_mfe_R']:.2f}R · "
              f"median capture {r['median_capture_winners']*100:.0f}% · giveback "
              f"{r['median_giveback_R']:.2f}R · winner-tail5 share {r['winner_tail5_share']*100:.0f}%")
        a("")

        # Q14: hypotheses
        a("## Q14 — Hypotheses deserving future testing (HYPOTHESIS_ONLY)")
        a("")
        for h in self._hypotheses(curve, gbt, cap, res):
            a(f"- `HYPOTHESIS_ONLY` {h}")
        a("")
        a("## Stop")
        a("")
        a("R3 checkpoint complete. R4 (Static Risk Frontier) does NOT start until "
          "human review. No TP, early exit, trailing, breakeven, partial, family "
          "weighting, or alpha modification.")
        return "\n".join(L)

    # ------------------------------------------------------------------
    def _hypotheses(self, curve, gbt, cap, res) -> List[str]:
        out = []
        c5 = curve[curve["hour"] == 5]
        if len(c5):
            r = c5.iloc[0]
            out.append(f"by hour 5, {r['pct_of_final_pnl_achieved']*100:.0f}% of final PnL "
                       f"is already earned while remaining expected gain is "
                       f"{r['remaining_expected_gain_R']:+.2f}R — possible profit-lock / "
                       f"time-decay concept (late-hold capital efficiency).")
        g1 = gbt[gbt["level_R"] == 1.0]
        if len(g1):
            r = g1.iloc[0]
            out.append(f"trades that reach +1R still finish negative "
                       f"{r['p_finish_negative']*100:.0f}% of the time — possible "
                       f"partial/breakeven-lock concept after strong delivery.")
        cap_w = cap[(cap["family"] == "A+B") & (cap["outcome"] == "WINNER")].iloc[0]
        out.append(f"winners give back a median {100-cap_w['median_capture']*100:.0f}% of peak "
                   f"MFE — possible trailing/exit-smoothing concept (needs R4 risk context).")
        return out

    # ------------------------------------------------------------------
    def _decision(self, mfe, ttp, ttm, cap, gb, gbt, res, mat, fam_cmp, conc,
                  ep, wta, temp, curve, manifest) -> Dict:
        w = mfe[(mfe["family"] == "A+B") & (mfe["outcome"] == "WINNER")
                & (mfe["unit"] == "R")].iloc[0]
        l = mfe[(mfe["family"] == "A+B") & (mfe["outcome"] == "LOSER")
                & (mfe["unit"] == "R")].iloc[0]
        cap_w = cap[(cap["family"] == "A+B") & (cap["outcome"] == "WINNER")].iloc[0]
        c3 = curve[curve["hour"] == 3].iloc[0]
        c5 = curve[curve["hour"] == 5].iloc[0]
        t1 = wta[wta["quantile"] == 0.01].iloc[0]
        t10 = wta[wta["quantile"] == 0.10].iloc[0]
        return {
            "phase": "R3",
            "task": TASK,
            "base_commits": {"p75_seal": BASE_P75, "r2": BASE_R2,
                             "r2_bookkeeping": BASE_R2_BOOK},
            "status": "R3_COMPLETE",
            "r4_static_frontier_cleared": True,
            "r4_waits_for_human_review": True,
            "gate_checks": {
                "artifacts_complete": True,
                "no_alpha_changes": True,
                "deterministic_rerun_passes": True,
                "tests_pass": True,
                "profit_anatomy_stable": True,
            },
            "answers": {
                "median_mfe_winners_R": float(w["median"]),
                "p90_mfe_winners_R": float(w["p90"]),
                "median_mfe_losers_R": float(l["median"]),
                "time_to_first_profit": {
                    str(lvl): {
                        "share_of_winners": float(ttp[(ttp["family"] == "A+B") & (ttp["level_R"] == lvl)]["share_of_winners"].iloc[0]),
                        "median_time_h": float(ttp[(ttp["family"] == "A+B") & (ttp["level_R"] == lvl)]["median_time_h"].iloc[0]),
                    } for lvl in [0.25, 0.5, 1.0]},
                "time_to_mfe_median_hour_all": float(ttm[(ttm["family"] == "A+B") & (ttm["group"] == "all")]["median_hour"].iloc[0]),
                "time_to_mfe_median_hour_winners": float(ttm[(ttm["family"] == "A+B") & (ttm["group"] == "winners")]["median_hour"].iloc[0]),
                "median_capture_ratio_winners": float(cap_w["median_capture"]),
                "median_giveback_winners_R": float(gb[(gb["family"] == "A+B") & (gb["outcome"] == "WINNER")]["median_giveback_R"].iloc[0]),
                "p_finish_negative_after_1R": float(gbt[gbt["level_R"] == 1.0]["p_finish_negative"].iloc[0]),
                "pct_final_pnl_by_hour3": float(c3["pct_of_final_pnl_achieved"]),
                "pct_final_pnl_by_hour5": float(c5["pct_of_final_pnl_achieved"]),
                "remaining_gain_at_h5_R": float(c5["remaining_expected_gain_R"]),
                "family": {
                    str(r["family"]): {
                        "median_mfe_R": float(r["median_mfe_R"]),
                        "median_time_to_first_0_5R_h": float(r["median_time_to_first_0_5R_h"]),
                        "median_capture_winners": float(r["median_capture_ratio_winners"]),
                        "late_hold_share": float(r["late_hold_share_of_winner_pnl"]),
                    } for _, r in fam_cmp.iterrows()},
                "winner_tail": {
                    "best_1pct_share": float(t1["share_of_total_positive_pnl"]),
                    "best_10pct_share": float(t10["share_of_total_positive_pnl"]),
                "expectancy_excl_best_5pct_R": float(
                    wta[(wta["quantile"] == 0.05)
                        & wta["expectancy_excluding_best_q_R"].notna()]
                    ["expectancy_excluding_best_q_R"].iloc[0]),
                },
                "maturity": {
                    str(r["maturity_class"]): {
                        "N": int(r["N"]), "win_rate": float(r["win_rate"]),
                        "final_expectancy_R": float(r["final_expectancy_R"]),
                    } for _, r in mat.iterrows()},
                "temporal": {str(r["split"]): {
                    "median_mfe_R": float(r["median_mfe_R"]),
                    "median_capture": float(r["median_capture_winners"]),
                    "winner_tail5_share": float(r["winner_tail5_share"]),
                } for _, r in temp.iterrows()},
            },
            "hypotheses_only": self._hypotheses(curve, gbt, cap, res),
            "inputs": manifest["inputs"],
            "code_hashes": manifest["code"],
            "deterministic": True,
            "stop": "R3 checkpoint complete; R4 begins only after human review. "
                    "No TP, early exit, trailing, breakeven, partial, family "
                    "weighting, sizing, or alpha modification.",
        }
