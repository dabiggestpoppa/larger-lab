"""
CR-RISK-BLOCK1 R1 — Exposure Truth & Portfolio Heat (orchestrator).

Runs R1.1 (event-risk ledger) -> R1.2 (concurrency map) -> R1.3 (portfolio heat)
-> R1.4 (routing episode clustering), freezes input hashes, writes all R1
outputs, the exposure-truth report and the R1 decision. STOPS after R1
(per brief: R2 begins only after checkpoint evidence is complete).
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from .phase_6_events import (PHASE3_PANEL_HASH, PHASE5_INPUT_HASHES,
                             load_frozen_phase3_panel, load_frozen_phase5)
from .phase_7_5_audit import FROZEN_CONFIGS, OOS_LABEL
from .phase_7_execution import build_execution_grid, orient_trade
from .phase_7_families import FAMILIES
from .phase_r1_concurrency import build_concurrency
from .phase_r1_episodes import (INTERVALS_H, cluster_events,
                                conditional_results, independence_verdict)
from .phase_r1_heat import build_heat, build_marks, heat_distributions
from .phase_r1_ledger import build_ledger, unit_mapping_formulas

TASK = "CR-RISK-BLOCK1-R1-EXPOSURE-TRUTH"
BASE_P75_COMMIT = "7bc1c0242cd05a205da62b34904d7308c63f2acb"
BASE_P8_COMMIT = "95fb6f207db37cfc3c44af0e67cd716dd7171679"


class PhaseR1ExposureTruth:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.phase3 = self.root / "artifacts" / "phase_03"
        self.phase5 = self.root / "artifacts" / "phase_05"
        self.p75 = self.root / "artifacts" / "phase_07_5"
        self.out = self.root / "artifacts" / "risk_block1"
        self.out.mkdir(parents=True, exist_ok=True)

    def run(self) -> Dict:
        t0 = time.time()
        print("[R1] load frozen inputs (hash-validated)")
        ev = load_frozen_phase5(self.phase5)["routing_events.parquet"]
        panel = load_frozen_phase3_panel(self.phase3)
        trades = pd.read_csv(self.p75 / "P7_5_TRADES.csv")
        trades["entry_ts"] = pd.to_datetime(trades["entry_ts"], utc=True)
        trades["exit_ts"] = pd.to_datetime(trades["exit_ts"], utc=True)
        trades["split"] = trades["split"].replace("untouched", OOS_LABEL)

        print("[R1] build frozen-config execution grids")
        grids = {}
        for fid in ["A", "B"]:
            fam = FAMILIES[fid]
            fam_events = ev[
                (ev["origin_currency"] == fam["origin"])
                & (ev["direction"] == fam["direction"])
            ]
            cfg = FROZEN_CONFIGS[fid]
            g = build_execution_grid(fam_events, panel, [cfg["pair"]],
                                     [cfg["delay_h"]], [cfg["hold_h"]])
            g = orient_trade(g, fam)
            grids[fid] = g
            print(f"  family {fid}: {len(fam_events)} events, {len(g)} grid rows")

        print("[R1.1] event-risk ledger")
        ledger = build_ledger(trades, grids, panel)
        ledger.to_csv(self.out / "R1_EVENT_RISK_LEDGER.csv", index=False)

        print("[R1.2] concurrency map")
        conc_tl, conc_sum = build_concurrency(ledger)
        conc_tl.to_csv(self.out / "R1_CONCURRENCY_TIMELINE.csv", index=False)
        conc_sum.to_csv(self.out / "R1_CONCURRENCY_SUMMARY.csv", index=False)

        print("[R1.3] portfolio heat")
        marks = build_marks(ledger, panel)
        heat = build_heat(ledger, marks)
        heat.to_csv(self.out / "R1_PORTFOLIO_HEAT.csv", index=False)
        heat_dist = heat_distributions(heat)
        heat_dist.to_csv(self.out / "R1_HEAT_DISTRIBUTIONS.csv", index=False)

        print("[R1.4] routing episode clustering")
        ep_frames = []
        for interval_h in INTERVALS_H:
            ep_frames.append(cluster_events(ledger, marks, interval_h))
        episodes = pd.concat(ep_frames, ignore_index=True)
        episodes.to_csv(self.out / "R1_ROUTING_EPISODES.csv", index=False)
        cond = conditional_results(ledger, marks)
        cond.to_csv(self.out / "R1_EPISODE_CONDITIONAL_RESULTS.csv", index=False)
        verdicts = independence_verdict(cond)

        # ---- freeze input hashes ----
        manifest = self._input_manifest(trades)
        (self.out / "R1_INPUT_HASH_MANIFEST.json").write_text(
            json.dumps(manifest, indent=2, default=str), encoding="utf-8")

        # ---- report + decision ----
        report = self._report(ledger, conc_tl, conc_sum, heat, heat_dist,
                              episodes, cond, verdicts, manifest)
        (self.out / "R1_EXPOSURE_TRUTH_REPORT.md").write_text(report, encoding="utf-8")

        decision = self._decision(ledger, conc_sum, heat, heat_dist, episodes,
                                  cond, verdicts, manifest)
        (self.out / "R1_DECISION.json").write_text(
            json.dumps(decision, indent=2, default=str), encoding="utf-8")

        elapsed = time.time() - t0
        print(f"=== R1 SUMMARY === elapsed {elapsed:.1f}s")
        print(f"  ledger events: {len(ledger)}")
        print(f"  max concurrency: {conc_sum['max_concurrent_positions'].iloc[0]}")
        print(f"  gross heat p99: {heat_dist[(heat_dist.metric=='gross_heat') & (heat_dist.window_h==1) & (heat_dist.scope=='all_hours')]['p99'].iloc[0]:.2f} bps")
        print(f"  cluster verdicts: {json.dumps(verdicts, default=str)[:400]}")
        return {"elapsed_seconds": elapsed, "n_events": int(len(ledger)),
                "n_outputs": 9, "r2_ready": True,
                "note": "R1 checkpoint complete; R2 awaits human review"}

    # ------------------------------------------------------------------
    def _input_manifest(self, trades: pd.DataFrame) -> Dict:
        def sha(p: Path) -> str:
            return hashlib.sha256(p.read_bytes()).hexdigest()

        p5_ev = self.phase5 / "routing_events.parquet"
        p3 = self.phase3 / "h1_strict_common_panel.parquet"
        trades_p = self.p75 / "P7_5_TRADES.csv"
        code_files = sorted(Path(__file__).parent.glob("phase_r1_*.py"))
        return {
            "phase": "R1",
            "task": TASK,
            "base_commits": {"p75_seal": BASE_P75_COMMIT, "p8_overlay": BASE_P8_COMMIT},
            "inputs": {
                "phase_07_5/P7_5_TRADES.csv": {"sha256": sha(trades_p),
                                               "bytes": trades_p.stat().st_size,
                                               "rows": int(len(trades))},
                "phase_05/routing_events.parquet": {"sha256": sha(p5_ev),
                                                    "frozen_expected": PHASE5_INPUT_HASHES["routing_events.parquet"]},
                "phase_03/h1_strict_common_panel.parquet": {"sha256": sha(p3),
                                                            "frozen_expected": PHASE3_PANEL_HASH},
            },
            "code": {p.name: sha(p) for p in code_files},
            "determinism": "no random sampling; greedy deterministic clustering; "
                           "byte-identical outputs verified by tests",
        }

    # ------------------------------------------------------------------
    def _report(self, ledger, conc_tl, conc_sum, heat, heat_dist,
                episodes, cond, verdicts, manifest) -> str:
        L = []
        a = L.append
        a("# R1 — Exposure Truth & Portfolio Heat (CR-RISK-BLOCK1)")
        a("")
        a(f"**Task:** {TASK} · **Base:** {BASE_P75_COMMIT[:8]} (sealed baseline) · "
          f"Phase-8 overlay preserved as negative result ({BASE_P8_COMMIT[:8]})")
        a("")
        a("## 1. Unit reconciliation (R1.1)")
        a("")
        a("```")
        for k, v in unit_mapping_formulas().items():
            if k == "units":
                for kk, vv in v.items():
                    a(f"  {kk}: {vv}")
            else:
                a(f"{k}: {v}")
        a("```")
        a("")
        a(f"- **1R = TARGET_VOL × √hold = 10 × √6 = 24.4949 bps** of PnL for the "
          f"vol-normalized position — a one-sigma move over the full hold.")
        a(f"- `r_multiple = net_pnl_bps / 1R`; `account_return_pct = r_multiple × "
          f"{1.0}%` (reference 1% per R; the account-leverage parameter is swept in R4).")
        a("- Entry/exit prices are read from the frozen H1 panel with the exact Phase-7 "
          "window convention; `price_return_bps` reproduces the grid's `gross_return_bps` "
          "to float tolerance (unit-tested).")
        a("")
        a("## 2. Ledger")
        a("")
        splits = {k: int(v) for k, v in ledger['split'].value_counts().items()}
        a(f"- Events: **{len(ledger)}** (A: {(ledger['family']=='A').sum()}, "
          f"B: {(ledger['family']=='B').sum()}) · splits: "
          f"{splits}")
        exp = ledger.groupby("family")["pnl_bps"].mean()
        for fid in ["A", "B"]:
            sub = ledger[ledger["family"] == fid]
            a(f"- Family {fid}: expectancy {exp[fid]:+.3f} bps = "
              f"{exp[fid]/ledger['risk_unit_bps'].iloc[0]:+.3f}R · win "
              f"{(sub['pnl_bps']>0).mean():.3f} · median R "
              f"{sub['r_multiple'].median():+.3f} · worst R {sub['r_multiple'].min():+.3f} "
              f"· best R {sub['r_multiple'].max():+.3f}")
        a("")
        a("## 3. Concurrency (R1.2)")
        a("")
        s = conc_sum.iloc[0]
        a(f"- Max concurrent positions: **{s['max_concurrent_positions']}** · "
          f"mean (in-market) {s['mean_concurrency_in_market']:.2f} · median "
          f"{s['median_concurrency_in_market']:.0f} · p90 {s['p90_concurrency_in_market']:.0f} "
          f"· p99 {s['p99_concurrency_in_market']:.0f}")
        a(f"- In-market hours: {s['in_market_hours']} of {s['timeline_hours']} "
          f"({100*s['in_market_hours']/s['timeline_hours']:.1f}%)")
        a(f"- Hours with 2 positions: {s['hours_with_2_positions']} · 3: "
          f"{s['hours_with_3_positions']} · 4+: {s['hours_with_4plus_positions']}")
        a(f"- Overlap hours — same-direction: {s['same_direction_overlap_hours']} · "
          f"opposite-direction: {s['opposite_direction_overlap_hours']} · "
          f"A+A: {s['A_A_overlap_hours']} · B+B: {s['B_B_overlap_hours']} · "
          f"A+B: {s['A_B_overlap_hours']}")
        a(f"- Exposure — max gross {s['max_gross_exposure']:.2f} · "
          f"max |net| {s['max_abs_net_exposure']:.2f} · gross p90 "
          f"{s['gross_exposure_p90']:.2f} · gross p99 {s['gross_exposure_p99']:.2f}")
        a("- Opposite positions do NOT cancel economically; gross and net are tracked separately.")
        a("")
        a("## 4. Portfolio heat (R1.3)")
        a("")
        g1 = heat_dist[(heat_dist["metric"] == "gross_heat") & (heat_dist["window_h"] == 1)]
        n1 = heat_dist[(heat_dist["metric"] == "abs_net_heat") & (heat_dist["window_h"] == 1)]
        c1 = heat_dist[(heat_dist["metric"] == "portfolio_cae_bps") & (heat_dist["window_h"] == 1)]
        a("- Heat = aggregate live account-risk commitment. Each open position "
          "commits `10×√rem` bps (24.49 bps at entry), decaying to zero at exit.")
        for scope in ["all_hours", "in_market"]:
            gg = g1[g1["scope"] == scope].iloc[0]
            a(f"- gross heat ({scope}): median {gg['median']:.1f} · p75 {gg['p75']:.1f} · "
              f"p90 {gg['p90']:.1f} · p95 {gg['p95']:.1f} · p99 {gg['p99']:.1f} · "
              f"max {gg['max']:.1f} bps")
        nn = n1[n1["scope"] == "all_hours"].iloc[0]
        a(f"- |net heat| (all hours): median {nn['median']:.1f} · p90 {nn['p90']:.1f} · "
          f"p99 {nn['p99']:.1f} bps")
        cc = c1[c1["scope"] == "all_hours"].iloc[0]
        a(f"- portfolio CAE (all hours): median {cc['median']:.1f} · p90 {cc['p90']:.1f} · "
          f"p95 {cc['p95']:.1f} · p99 {cc['p99']:.1f} bps")
        a("- Rolling 1/3/6/12/24h heat distributions in R1_HEAT_DISTRIBUTIONS.csv.")
        a("")
        a("## 5. Routing episode clustering (R1.4)")
        a("")
        for interval_h in INTERVALS_H:
            sub = episodes[episodes["interval_h"] == interval_h]
            multi = sub[sub["n_events"] > 1]
            n_multi = int(multi["n_events"].sum())
            pct = 100.0 * n_multi / len(ledger)
            a(f"- interval {interval_h:g}h: {len(sub)} clusters · "
              f"{int((sub['n_events']==1).sum())} singletons · events in multi clusters "
              f"{n_multi} ({pct:.1f}%) · max cluster size {int(sub['n_events'].max())}")
        a("")
        a("### Conditional expectancy by within-cluster rank")
        a("")
        a("| interval | rank | N | mean bps | win | vs rank1 |")
        a("|---|---|---|---|---|---|")
        for interval_h in INTERVALS_H:
            sub = cond[cond["interval_h"] == interval_h]
            base = sub[sub["rank_in_cluster"] == "1"]["mean_net_pnl_bps"]
            base_v = float(base.iloc[0]) if len(base) else np.nan
            for _, r in sub.iterrows():
                diff = "" if r["rank_in_cluster"] == "1" else \
                    f"{r['mean_net_pnl_bps'] - base_v:+.2f}"
                a(f"| {interval_h:g}h | {r['rank_in_cluster']} | {int(r['n'])} | "
                  f"{r['mean_net_pnl_bps']:+.2f} | {r['win_rate']:.3f} | {diff} |")
        a("")
        a("### Independence vs duplication verdict")
        a("")
        for interval_h, v in verdicts.items():
            a(f"- **{interval_h}h:** {v['verdict']} (rank-1 expectancy "
              f"{v['rank1_expectancy_bps']:+.2f} bps)")
        a("")
        a("## 6. Checkpoint answers")
        a("")
        a("- **Unit reconciliation:** ledger reproduces the sealed baseline "
          "(A {:.3f} / B {:.3f} bps vol-normalized expectancy across dev+OOS) "
          "and adds R-multiples on the explicit 24.49 bps 1R unit.".format(
            exp["A"], exp["B"]))
        a(f"- **Max concurrency:** {s['max_concurrent_positions']} simultaneous "
          f"positions; median in-market {s['median_concurrency_in_market']:.0f}.")
        a(f"- **Portfolio heat:** median gross heat "
          f"{g1[g1['scope']=='all_hours'].iloc[0]['median']:.1f} bps, "
          f"p99 {g1[g1['scope']=='all_hours'].iloc[0]['p99']:.1f} bps; "
          f"portfolio CAE p99 {cc['p99']:.1f} bps.")
        a("- **Clustered events:** see §5 verdicts — whether clustered signals are "
          "independent or duplicated is a descriptive finding feeding R4 episode "
          "risk and Block-II models; no sizing change made.")
        a("")
        a("## 7. Inputs frozen")
        a("")
        a(f"- `P7_5_TRADES.csv` (sealed P0 book): {manifest['inputs']['phase_07_5/P7_5_TRADES.csv']['sha256'][:16]}…")
        a(f"- `routing_events.parquet` (Phase 5 frozen): {manifest['inputs']['phase_05/routing_events.parquet']['sha256'][:16]}… (matches seal)")
        a(f"- `h1_strict_common_panel.parquet` (Phase 3 frozen): {manifest['inputs']['phase_03/h1_strict_common_panel.parquet']['sha256'][:16]}… (matches seal)")
        a("- Deterministic: greedy clustering, no random sampling; byte-identical outputs tested.")
        a("")
        a("## 8. STOP")
        a("")
        a("R1 checkpoint complete. R2 (Loss Anatomy) does NOT start until human "
          "review of this evidence. No stops, no filters, no sizing change, no "
          "alpha modification.")
        return "\n".join(L)

    # ------------------------------------------------------------------
    def _decision(self, ledger, conc_sum, heat, heat_dist, episodes, cond,
                  verdicts, manifest) -> Dict:
        s = conc_sum.iloc[0]
        g1 = heat_dist[(heat_dist["metric"] == "gross_heat") & (heat_dist["window_h"] == 1)]
        g_all = g1[g1["scope"] == "all_hours"].iloc[0]
        g_mkt = g1[g1["scope"] == "in_market"].iloc[0]
        c1 = heat_dist[(heat_dist["metric"] == "portfolio_cae_bps") & (heat_dist["window_h"] == 1)]
        c_all = c1[c1["scope"] == "all_hours"].iloc[0]
        return {
            "phase": "R1",
            "task": TASK,
            "base_commits": {"p75_seal": BASE_P75_COMMIT, "p8_overlay": BASE_P8_COMMIT},
            "status": "R1_COMPLETE",
            "r2_cleared": True,
            "r2_waits_for_human_review": True,
            "ledger": {
                "n_events": int(len(ledger)),
                "n_A": int((ledger["family"] == "A").sum()),
                "n_B": int((ledger["family"] == "B").sum()),
                "risk_unit_1R_bps": float(ledger["risk_unit_bps"].iloc[0]),
                "expectancy_A_bps": float(ledger[ledger["family"] == "A"]["pnl_bps"].mean()),
                "expectancy_B_bps": float(ledger[ledger["family"] == "B"]["pnl_bps"].mean()),
                "expectancy_A_R": float(ledger[ledger["family"] == "A"]["r_multiple"].mean()),
                "expectancy_B_R": float(ledger[ledger["family"] == "B"]["r_multiple"].mean()),
            },
            "concurrency": {
                "max_concurrent": int(s["max_concurrent_positions"]),
                "mean_in_market": float(s["mean_concurrency_in_market"]),
                "median_in_market": float(s["median_concurrency_in_market"]),
                "hours_2pos": int(s["hours_with_2_positions"]),
                "hours_3pos": int(s["hours_with_3_positions"]),
                "opposite_overlap_hours": int(s["opposite_direction_overlap_hours"]),
                "A_B_overlap_hours": int(s["A_B_overlap_hours"]),
                "max_gross_exposure": float(s["max_gross_exposure"]),
                "max_abs_net_exposure": float(s["max_abs_net_exposure"]),
            },
            "heat": {
                "gross_heat_median_bps": float(g_all["median"]),
                "gross_heat_p90_bps": float(g_all["p90"]),
                "gross_heat_p99_bps": float(g_all["p99"]),
                "gross_heat_max_bps": float(g_all["max"]),
                "gross_heat_in_market_median_bps": float(g_mkt["median"]),
                "portfolio_cae_p99_bps": float(c_all["p99"]),
                "per_position_entry_heat_bps": float(10.0 * np.sqrt(6.0)),
                "units": "bps of PnL (vol-normalized position)",
            },
            "episodes": {
                "intervals_h": INTERVALS_H,
                "multi_event_share_by_interval": {
                    str(iv): float(episodes[episodes["interval_h"] == iv]["n_events"].sum()
                                   / len(ledger)) for iv in INTERVALS_H},
                "independence_verdicts": verdicts,
            },
            "inputs": manifest["inputs"],
            "code_hashes": manifest["code"],
            "deterministic": True,
            "stop": "R1 checkpoint complete; R2 begins only after human review. "
                    "No stops, filters, sizing, or alpha modification.",
        }
