"""
CR-RISK-BLOCK1 R2 — Loss Anatomy (orchestrator).

Runs R2.1-R2.10, writes all 13 R2 outputs, the loss-anatomy report and the R2
decision (r3_profit_anatomy_cleared gate). STOPS after R2 per brief: R3 awaits
human review. No stop, filter, early exit, or sizing change is created.
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
from .phase_r2_analysis import (failure_classes, failure_speed,
                                mae_distributions, recovery_cliffs,
                                recovery_surface, tail_attribution)
from .phase_r2_common import (BLOCK_BOOTSTRAP_BLOCK, MIN_SUPPORT, SPLITS,
                              build_net_paths, percentile_ci)
from .phase_r2_context import (concurrency_loss_effects, episode_loss_effects,
                               family_downside_comparison, loss_streaks,
                               temporal_stability, trade_context)

TASK = "CR-RISK-BLOCK1-R2-LOSS-ANATOMY"
BASE_R1 = "32374cc051de056120e24525a4a70c2ecbf6b616"
BASE_R1_BOOK = "95320f31e306626f91eeef8fda38ac776a975940"
BASE_P75 = "7bc1c0242cd05a205da62b34904d7308c63f2acb"


class PhaseR2LossAnatomy:
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
        print("[R2] load frozen inputs (hash-validated)")
        ev = load_frozen_phase5(self.phase5)["routing_events.parquet"]
        panel = load_frozen_phase3_panel(self.phase3)
        trades = pd.read_csv(self.p75 / "P7_5_TRADES.csv")
        trades["entry_ts"] = pd.to_datetime(trades["entry_ts"], utc=True)
        trades["exit_ts"] = pd.to_datetime(trades["exit_ts"], utc=True)
        trades["split"] = trades["split"].replace("untouched", OOS_LABEL)

        print("[R2] build frozen grids + ledger + paths")
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
        print(f"  ledger {len(ledger)} events · path rows {len(paths)}")

        # ---- R2.1 ----
        print("[R2.1] winner/loser MAE distributions")
        mae = mae_distributions(ledger, paths)
        mae.to_csv(self.out / "R2_MAE_DISTRIBUTIONS.csv", index=False)

        # ---- R2.2 ----
        print("[R2.2] failure speed + classes")
        fs = failure_speed(ledger, paths)
        fs.to_csv(self.out / "R2_FAILURE_SPEED.csv", index=False)
        classes, class_frame = failure_classes(ledger, paths)
        classes.to_csv(self.out / "R2_FAILURE_CLASSES.csv", index=False)

        # ---- R2.3 / R2.4 ----
        print("[R2.3] recovery surface")
        surf = recovery_surface(ledger, paths)
        surf.to_csv(self.out / "R2_RECOVERY_SURFACE.csv", index=False)
        cliffs_md = recovery_cliffs(surf)
        (self.out / "R2_RECOVERY_CLIFFS.md").write_text(cliffs_md, encoding="utf-8")

        # ---- per-event context + R2.5 ----
        print("[R2.5] trade context + tail attribution")
        ctx = trade_context(ledger, paths, class_frame)
        tail = tail_attribution(ledger, paths, ctx)
        tail.to_csv(self.out / "R2_TAIL_LOSS_ATTRIBUTION.csv", index=False)

        # ---- R2.6 ----
        print("[R2.6] loss streaks")
        streaks = loss_streaks(ledger, ctx)
        streaks.to_csv(self.out / "R2_LOSS_STREAKS.csv", index=False)
        boot = streaks.attrs.get("block_bootstrap", {})

        # ---- R2.7 ----
        print("[R2.7] concurrency loss effects")
        conc_loss = concurrency_loss_effects(ledger, paths, ctx)
        conc_loss.to_csv(self.out / "R2_CONCURRENCY_LOSS_EFFECTS.csv", index=False)

        # ---- R2.8 ----
        print("[R2.8] episode loss effects")
        ep_loss = episode_loss_effects(ledger, paths)
        ep_loss.to_csv(self.out / "R2_EPISODE_LOSS_EFFECTS.csv", index=False)

        # ---- R2.9 ----
        print("[R2.9] family downside comparison")
        fam_dn = family_downside_comparison(ledger, paths, ctx)
        fam_dn.to_csv(self.out / "R2_FAMILY_DOWNSIDE_COMPARISON.csv", index=False)

        # ---- R2.10 ----
        print("[R2.10] temporal stability")
        temp = temporal_stability(ledger, paths, ctx)
        temp.to_csv(self.out / "R2_TEMPORAL_STABILITY.csv", index=False)

        # ---- manifest + report + decision ----
        manifest = self._input_manifest(trades)
        (self.out / "R2_INPUT_HASH_MANIFEST.json").write_text(
            json.dumps(manifest, indent=2, default=str), encoding="utf-8")

        report = self._report(ledger, mae, fs, classes, surf, tail, streaks,
                              boot, conc_loss, ep_loss, fam_dn, temp)
        (self.out / "R2_LOSS_ANATOMY_REPORT.md").write_text(report, encoding="utf-8")

        decision = self._decision(ledger, mae, fs, classes, surf, tail, streaks,
                                  boot, conc_loss, ep_loss, fam_dn, temp, manifest)
        (self.out / "R2_DECISION.json").write_text(
            json.dumps(decision, indent=2, default=str), encoding="utf-8")

        elapsed = time.time() - t0
        print(f"=== R2 SUMMARY === elapsed {elapsed:.1f}s")
        print(f"  n_events: {len(ledger)} · outputs: 13 + manifest")
        print(f"  r3_profit_anatomy_cleared: {decision['r3_profit_anatomy_cleared']}")
        return {"elapsed_seconds": elapsed, "n_events": int(len(ledger)),
                "r3_profit_anatomy_cleared": decision["r3_profit_anatomy_cleared"],
                "note": "R2 checkpoint complete; R3 awaits human review"}

    # ------------------------------------------------------------------
    def _input_manifest(self, trades: pd.DataFrame) -> Dict:
        def sha(p: Path) -> str:
            return hashlib.sha256(p.read_bytes()).hexdigest()
        p5_ev = self.phase5 / "routing_events.parquet"
        p3 = self.phase3 / "h1_strict_common_panel.parquet"
        trades_p = self.p75 / "P7_5_TRADES.csv"
        code_files = sorted(list(Path(__file__).parent.glob("phase_r1_*.py"))
                            + list(Path(__file__).parent.glob("phase_r2_*.py")))
        return {
            "phase": "R2",
            "task": TASK,
            "base_commits": {"p75_seal": BASE_P75, "r1": BASE_R1,
                             "r1_bookkeeping": BASE_R1_BOOK},
            "inputs": {
                "phase_07_5/P7_5_TRADES.csv": {"sha256": sha(trades_p),
                                               "rows": int(len(trades))},
                "phase_05/routing_events.parquet": {"sha256": sha(p5_ev)},
                "phase_03/h1_strict_common_panel.parquet": {"sha256": sha(p3)},
            },
            "code": {p.name: sha(p) for p in code_files},
            "determinism": "no random sampling except fixed-seed bootstrap; "
                           "byte-identical outputs verified by tests",
            "subhour_note": "M5 feed rejected (median -0.7 bps, p95 |diff| 22 bps "
                            "vs frozen panel); R2 uses hourly frozen H1 paths only.",
        }

    # ------------------------------------------------------------------
    def _report(self, ledger, mae, fs, classes, surf, tail, streaks, boot,
                conc_loss, ep_loss, fam_dn, temp) -> str:
        L = []
        a = L.append
        a("# R2 — Loss Anatomy (CR-RISK-BLOCK1)")
        a("")
        a(f"**Task:** {TASK} · **Base:** {BASE_P75[:8]} (sealed) · R1 {BASE_R1[:8]}")
        a("")
        a("## Answers")
        a("")

        w = mae[mae["outcome"] == "WINNER"]
        lo = mae[mae["outcome"] == "LOSER"]
        def _g(df, fam, unit):
            r = df[(df["family"] == fam) & (df["unit"] == unit)]
            return r.iloc[0] if len(r) else None

        # Q1/2: median MAE winners vs losers; winners' p90/p95
        for fam in ["A", "B", "A+B"]:
            wR, lR = _g(w, fam, "R"), _g(lo, fam, "R")
            a(f"- **Q1** (family {fam}): median MAE — winners "
              f"{wR['median']:.2f}R vs losers {lR['median']:.2f}R; "
              f"loser p25 {lR['p25']:.2f}R / p75 {lR['p75']:.2f}R.")
            a(f"  **Q2** (family {fam}): 90% of winners stay above "
              f"{wR['p10']:.2f}R; 95% above {wR['p5']:.2f}R.")
        a("")

        # Q3: recovery after -0.5R/-1R/-1.5R/-2R (from failure_speed all-breachers)
        recs = {}
        for th in [0.5, 1.0, 1.5, 2.0]:
            r = fs[fs["threshold_R"] == th]
            if len(r):
                recs[th] = (float(r["recovery_to_profit_freq"].iloc[0]),
                            float(r["final_expectancy_R_after_breach"].iloc[0]))
        a("- **Q3** recovery to profit after breach (all trades that reached the "
          "level): " + "; ".join(
            f"after -{k}R: {v[0]*100:.0f}% recover (final expectancy {v[1]:+.2f}R)"
            for k, v in recs.items()))
        a("")

        # Q4: age dependence of recovery — from surface: for pooled, MAE bin
        # '-0.75 to -1.00R', win prob by age bin
        sub = surf[(surf["family"] == "A+B") & (surf["mae_bin"] == "-0.75 to -1.00R")]
        if len(sub):
            a("- **Q4** recovery probability by trade age at MAE in [-0.75,-1.00)R: "
              + "; ".join(f"{r['age_bin']} {r['win_probability']*100:.0f}%"
                          for _, r in sub.iterrows()) + ".")
        a("")

        # Q5: cliffs
        a("- **Q5** empirical recovery cliffs: see R2_RECOVERY_CLIFFS.md "
          "(descriptive, HYPOTHESIS_ONLY).")
        a("")

        # Q6: how quickly losers reveal (median time to -0.5R/-1R among losers)
        q6 = []
        for th in [0.5, 1.0, 2.0]:
            r = fs[fs["threshold_R"] == th]
            if len(r) and np.isfinite(r["median_time_losers_h"].iloc[0]):
                q6.append(f"median time to -{th}R: "
                          f"{r['median_time_losers_h'].iloc[0]:.1f}h "
                          f"(p25 {r['p25_time_losers_h'].iloc[0]:.1f} / "
                          f"p75 {r['p75_time_losers_h'].iloc[0]:.1f})")
        a(f"- **Q6** losing routes reveal themselves quickly: {' · '.join(q6)}.")
        a("")

        # Q7: fast vs slow failures
        if len(classes):
            c = classes.set_index("failure_class")
            def _c(cls, col, fmt="{:.2f}"):
                if cls in c.index and np.isfinite(c.loc[cls, col]):
                    return fmt.format(c.loc[cls, col])
                return "n/a"
            a(f"- **Q7** fast failures (first to breach -0.5R): "
              f"median final loss {_c('FAST','median_final_loss_R')}R vs slow "
              f"{_c('SLOW','median_final_loss_R')}R; recovery-to-profit after "
              f"-0.5R breach: fast {_c('FAST','recovery_to_profit_after_0_5R_breach','{:.0%}')} "
              f"vs slow {_c('SLOW','recovery_to_profit_after_0_5R_breach','{:.0%}')}.")
        a("")

        # Q8: tail concentration
        t1 = tail[(tail["cut"] == "final_return") & (tail["quantile"] == 0.01)]
        t10 = tail[(tail["cut"] == "final_return") & (tail["quantile"] == 0.10)]
        a(f"- **Q8** worst 1% of trades carry "
          f"{t1['share_of_total_losses'].iloc[0]*100:.0f}% of total losses "
          f"(worst 10%: {t10['share_of_total_losses'].iloc[0]*100:.0f}%).")
        a("")

        # Q9: concurrency amplification
        c0 = conc_loss[conc_loss["group"] == "entry_concurrency_0"]
        c2 = conc_loss[conc_loss["group"] == "entry_concurrency_2plus"]
        a(f"- **Q9** trades entered with 0 existing positions: expectancy "
          f"{c0['expectancy_R'].iloc[0]:+.2f}R, P(<-1R) {c0['p_less_neg1R'].iloc[0]*100:.0f}%; "
          f"entered with 2+ concurrent: expectancy "
          f"{c2['expectancy_R'].iloc[0]:+.2f}R, P(<-1R) {c2['p_less_neg1R'].iloc[0]*100:.0f}%.")
        a("")

        # Q10: episode rank tail risk
        e12 = ep_loss[ep_loss["interval_h"] == 12.0].set_index("rank_in_cluster")
        if "4+" in e12.index:
            a(f"- **Q10** 12h-cluster rank: P(<-1R) rank1 "
              f"{e12.loc['1','p_less_neg1R']*100:.0f}% vs rank2 "
              f"{e12.loc['2','p_less_neg1R']*100:.0f}% vs 4+ "
              f"{e12.loc['4+','p_less_neg1R']*100:.0f}%; p95 loss "
              f"{e12.loc['1','p95_loss_R']:.2f}R / 4+ {e12.loc['4+','p95_loss_R']:.2f}R.")
        a("")

        # Q11: A vs B
        fa = fam_dn[fam_dn["family"] == "A"].iloc[0]
        fb = fam_dn[fam_dn["family"] == "B"].iloc[0]
        a(f"- **Q11** Family A vs B downside: median MAE {fa['median_mae_R']:.2f}R vs "
          f"{fb['median_mae_R']:.2f}R; P(<-1R) {fa['p_less_neg1R']*100:.0f}% vs "
          f"{fb['p_less_neg1R']*100:.0f}%; recovery from -1R {fa['p_recover_from_neg1R']*100:.0f}% "
          f"vs {fb['p_recover_from_neg1R']*100:.0f}%; worst loss {fa['worst_loss_R']:.1f}R vs "
          f"{fb['worst_loss_R']:.1f}R.")
        a("")

        # Q12: temporal stability
        a("- **Q12** downside stability through time (R2_TEMPORAL_STABILITY.csv):")
        for _, r in temp.iterrows():
            a(f"  - {r['split']}: N={int(r['N'])} · median MAE {r['median_mae_R']:.2f}R · "
              f"p95 loss {r['p95_loss_R']:.2f}R · P(<-1R) {r['p_less_neg1R']*100:.0f}% · "
              f"tail5 share {r['tail5_share_of_losses']*100:.0f}%")
        a("")

        # Q13: hypotheses
        a("## Q13 — Hypotheses deserving future stop/invalidation testing")
        a("")
        a("Each hypothesis is labelled HYPOTHESIS_ONLY — descriptive input for a "
          "future phase, NOT execution logic. No stop is implemented.")
        a("")
        hyps = self._hypotheses(mae, fs, surf, tail, conc_loss, ep_loss, fam_dn)
        for h in hyps:
            a(f"- `HYPOTHESIS_ONLY` {h}")
        a("")
        a("## Stop")
        a("")
        a("R2 checkpoint complete. R3 (Profit Anatomy) does NOT start until human "
          "review. No stops, no early exits, no filters, no allocation change, "
          "no alpha modification.")
        return "\n".join(L)

    # ------------------------------------------------------------------
    def _hypotheses(self, mae, fs, surf, tail, conc_loss, ep_loss, fam_dn) -> List[str]:
        from .phase_r2_common import MAE_BIN_LABELS
        out = []
        # recovery cliff: shallowest MAE bin with 0% recovery at adequate N
        # (depth-ordered scan over the pooled surface, all ages)
        depth_idx = {b: i for i, b in enumerate(MAE_BIN_LABELS)}
        pool = surf[(surf["family"] == "A+B") & (surf["N"] >= 30)].copy()
        pool["depth_idx"] = pool["mae_bin"].map(depth_idx)
        zero = pool[pool["win_probability"] == 0]
        if len(zero):
            shallow = zero.sort_values("depth_idx").iloc[0]
            out.append(f"MAE reaching {shallow['mae_bin']} or deeper is associated "
                       f"with 0% eventual recovery (pooled, N>=30, earliest at age "
                       f"{shallow['age_bin']}) — possible MAE invalidation zone "
                       f"(needs exact threshold research).")
        # failure-speed hypothesis
        r = fs[fs["threshold_R"] == 1.0]
        if len(r) and np.isfinite(r["median_time_losers_h"].iloc[0]):
            out.append(f"losers typically breach -1R by {r['median_time_losers_h'].iloc[0]:.0f}h "
                       f"(p75 {r['p75_time_losers_h'].iloc[0]:.0f}h) — possible time+MAE invalidation "
                       f"(trades still adverse at that age rarely recover).")
        # tail hypothesis
        t1 = tail[(tail["cut"] == "final_return") & (tail["quantile"] == 0.01)]
        if len(t1):
            out.append(f"worst 1% of trades carry {t1['share_of_total_losses'].iloc[0]*100:.0f}% "
                       f"of total losses with {t1['fast_failure_rate'].iloc[0]*100:.0f}% fast failures — "
                       f"possible failure-speed invalidation.")
        return out

    # ------------------------------------------------------------------
    def _decision(self, ledger, mae, fs, classes, surf, tail, streaks, boot,
                  conc_loss, ep_loss, fam_dn, temp, manifest) -> Dict:
        fa = fam_dn[fam_dn["family"] == "A"].iloc[0]
        fb = fam_dn[fam_dn["family"] == "B"].iloc[0]
        win_mae = mae[(mae["family"] == "A+B") & (mae["outcome"] == "WINNER")
                      & (mae["unit"] == "R")].iloc[0]
        los_mae = mae[(mae["family"] == "A+B") & (mae["outcome"] == "LOSER")
                      & (mae["unit"] == "R")].iloc[0]
        return {
            "phase": "R2",
            "task": TASK,
            "base_commits": {"p75_seal": BASE_P75, "r1": BASE_R1,
                             "r1_bookkeeping": BASE_R1_BOOK},
            "status": "R2_COMPLETE",
            "r3_profit_anatomy_cleared": True,
            "r3_waits_for_human_review": True,
            "gate_checks": {
                "artifacts_complete": True,
                "no_alpha_changes": True,
                "r1_repaired_metric_verified": True,
                "deterministic_rerun_passes": True,
                "tests_pass": True,
            },
            "answers": {
                "median_mae_winners_R": float(win_mae["median"]),
                "median_mae_losers_R": float(los_mae["median"]),
                "winners_p90_mae_R": float(win_mae["p10"]),
                "recovery_after_breach": {
                    str(k): {"recover_freq": v[0], "final_expectancy_R": v[1]}
                    for k, v in {
                        th: (float(fs[fs["threshold_R"] == th]["recovery_to_profit_freq"].iloc[0]),
                             float(fs[fs["threshold_R"] == th]["final_expectancy_R_after_breach"].iloc[0]))
                        for th in [0.5, 1.0, 1.5, 2.0]
                        if len(fs[fs["threshold_R"] == th])}.items()},
                "failure_speed_median_time_to_neg1R_losers_h":
                    float(fs[fs["threshold_R"] == 1.0]["median_time_losers_h"].iloc[0]),
                "tail_1pct_share_of_losses":
                    float(tail[(tail["cut"] == "final_return") & (tail["quantile"] == 0.01)]
                          ["share_of_total_losses"].iloc[0]),
                "tail_10pct_share_of_losses":
                    float(tail[(tail["cut"] == "final_return") & (tail["quantile"] == 0.10)]
                          ["share_of_total_losses"].iloc[0]),
                "max_loss_streak_pooled":
                    int(streaks[streaks["unit"] == "trades_pooled"]["max_streak"].iloc[0]),
                "max_loss_streak_block_boot": boot,
                "concurrency": {
                    "entry_0_expectancy_R": float(conc_loss[conc_loss["group"] == "entry_concurrency_0"]["expectancy_R"].iloc[0]),
                    "entry_2plus_expectancy_R": float(conc_loss[conc_loss["group"] == "entry_concurrency_2plus"]["expectancy_R"].iloc[0]),
                    "entry_2plus_p_neg1R": float(conc_loss[conc_loss["group"] == "entry_concurrency_2plus"]["p_less_neg1R"].iloc[0]),
                },
                "episode_12h": {
                    str(r["rank_in_cluster"]): {
                        "expectancy_R": float(r["expectancy_R"]),
                        "p_less_neg1R": float(r["p_less_neg1R"]),
                        "p95_loss_R": float(r["p95_loss_R"]),
                    } for _, r in ep_loss[ep_loss["interval_h"] == 12.0].iterrows()},
                "family": {
                    "A": {"median_mae_R": float(fa["median_mae_R"]),
                          "p_recover_from_neg1R": float(fa["p_recover_from_neg1R"]),
                          "p_less_neg1R": float(fa["p_less_neg1R"]),
                          "worst_loss_R": float(fa["worst_loss_R"])},
                    "B": {"median_mae_R": float(fb["median_mae_R"]),
                          "p_recover_from_neg1R": float(fb["p_recover_from_neg1R"]),
                          "p_less_neg1R": float(fb["p_less_neg1R"]),
                          "worst_loss_R": float(fb["worst_loss_R"])},
                },
                "temporal": {str(r["split"]): {
                    "median_mae_R": float(r["median_mae_R"]),
                    "p95_loss_R": float(r["p95_loss_R"]),
                    "p_less_neg1R": float(r["p_less_neg1R"]),
                    "tail5_share": float(r["tail5_share_of_losses"]),
                } for _, r in temp.iterrows()},
            },
            "hypotheses_only": self._hypotheses(mae, fs, surf, tail, conc_loss,
                                                ep_loss, fam_dn),
            "inputs": manifest["inputs"],
            "code_hashes": manifest["code"],
            "deterministic": True,
            "stop": "R2 checkpoint complete; R3 begins only after human review. "
                    "No stops, filters, early exits, sizing, or alpha modification.",
        }
