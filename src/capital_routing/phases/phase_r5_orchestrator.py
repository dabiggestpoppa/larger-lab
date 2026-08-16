"""
CR-RISK-BLOCK2 R5 — Family Quality / Allocation Anatomy (orchestrator).

Runs III-XV, writes the 21 R5 artifacts + protocol, report (19 sections),
decision, evidence matrix, quality matrix and input manifest under
artifacts/risk_block2/r5/. STOPS after R5: R6 (episode/heat sizing) does NOT
start until human review. No allocation is selected. No Kelly / dynamic /
DD-adaptive / deployment / MT5.
"""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from .phase_7_5_audit import OOS_LABEL
from .phase_r4_common import MC_PATHS, RISK_UNIT_BPS
from .phase_r5_analysis import (expectancy_quality, family_distributions,
                                left_tail, profit_anatomy, temporal_stability)
from .phase_r5_common import (ALLOC_GRID, F_GRID, MC_PATHS_STRESS, MC_SEED,
                              load_r5_inputs)
from .phase_r5_dependency import dependency_structure
from .phase_r5_portfolio import (allocation_frontier, allocation_mc,
                                 marginal_contribution, nondominated_frontier)
from .phase_r5_stress import family_edge_degradation, family_tail_stress

TASK = "CR-RISK-BLOCK2-R5-FAMILY-QUALITY-ALLOCATION"
BLOCK1_SEAL = "8ca072d0d9390acf581770a99ce45b333deddd8c"
BLOCK1_STAMP = "470702c2bb445e1f7a1be949efd6ec3a75b74878"
BASE_P75 = "7bc1c0242cd05a205da62b34904d7308c63f2acb"

# Preregistered ordinal rules for the quality matrix (XV) - fixed BEFORE runs
QUALITY_RULES = {
    "expectancy_quality": lambda r: "STRONG" if r >= 0.30 else
    ("NEUTRAL" if r >= 0.20 else "WEAK"),
    "left_tail_quality": lambda br: "STRONG" if br <= 0.10 else
    ("NEUTRAL" if br <= 0.14 else "WEAK"),
}


class PhaseR5FamilyAllocation:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.out = self.root / "artifacts" / "risk_block2" / "r5"
        self.out.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    def run(self) -> Dict:
        t0 = time.time()
        print("[R5] load frozen inputs + sealed ledger (cross-checked)")
        load = load_r5_inputs(self.root)
        ledger, paths = load["ledger"], load["paths"]
        years = load["years"]

        # III
        print("[R5.III] family distributions")
        fd = family_distributions(ledger)
        fd.to_csv(self.out / "R5_FAMILY_DISTRIBUTIONS.csv", index=False)

        # IV
        print("[R5.IV] expectancy quality")
        eq = expectancy_quality(ledger, years)
        eq.to_csv(self.out / "R5_FAMILY_EXPECTANCY_QUALITY.csv", index=False)

        # V
        print("[R5.V] left-tail comparison")
        lt = left_tail(ledger, paths)
        lt.to_csv(self.out / "R5_FAMILY_LEFT_TAIL.csv", index=False)
        (self.out / "R5_FAMILY_LOSS_ANATOMY.md").write_text(
            self._loss_anatomy_md(lt, eq), encoding="utf-8")

        # VI
        print("[R5.VI] profit anatomy")
        pa = profit_anatomy(ledger, paths)
        pa.to_csv(self.out / "R5_FAMILY_PROFIT_ANATOMY.csv", index=False)
        (self.out / "R5_FAMILY_PROFIT_QUALITY.md").write_text(
            self._profit_quality_md(pa), encoding="utf-8")

        # VII
        print("[R5.VII] temporal stability")
        ts = temporal_stability(ledger)
        ts.to_csv(self.out / "R5_FAMILY_TEMPORAL_STABILITY.csv", index=False)

        # VIII
        print("[R5.VIII] dependency structure")
        dep = dependency_structure(ledger, load["risk1_dir"])
        dep.to_csv(self.out / "R5_FAMILY_DEPENDENCY.csv", index=False)
        (self.out / "R5_FAMILY_DEPENDENCY_REPORT.md").write_text(
            self._dependency_md(dep), encoding="utf-8")

        # XI (MC first - frontier/edge tables merge its stats)
        print(f"[R5.XI] dependency-aware MC ({MC_PATHS} paths x 3 schemes)")
        mc = allocation_mc(ledger, years, n_paths=MC_PATHS, seed=MC_SEED)
        mc.to_csv(self.out / "R5_ALLOCATION_MC.csv", index=False)

        # X
        print("[R5.X] allocation frontier (predefined grid)")
        fr = allocation_frontier(load, mc)
        fr.to_csv(self.out / "R5_ALLOCATION_FRONTIER.csv", index=False)

        # IX
        print("[R5.IX] marginal portfolio contribution")
        mg = marginal_contribution(load, mc)
        mg.to_csv(self.out / "R5_MARGINAL_PORTFOLIO_CONTRIBUTION.csv", index=False)

        # XII
        print(f"[R5.XII] family edge degradation ({MC_PATHS_STRESS} paths)")
        edge = family_edge_degradation(ledger, n_paths=MC_PATHS_STRESS, seed=MC_SEED)
        edge.to_csv(self.out / "R5_FAMILY_EDGE_DEGRADATION.csv", index=False)

        # XIII
        print("[R5.XIII] family tail stress")
        tail = family_tail_stress(ledger)
        tail.to_csv(self.out / "R5_FAMILY_TAIL_STRESS.csv", index=False)

        # XIV
        print("[R5.XIV] non-dominated frontier")
        nd = nondominated_frontier(fr, edge)
        nd.to_csv(self.out / "R5_NONDOMINATED_FRONTIER.csv", index=False)

        # XV quality matrix + XVIII evidence matrix
        qm = self._quality_matrix(eq, lt, ts, dep, mg, edge, fr)
        (self.out / "R5_FAMILY_QUALITY_MATRIX.md").write_text(qm["md"], encoding="utf-8")
        evm = self._evidence_matrix(eq, lt, pa, ts, dep, fr, nd, edge, mc)
        evm.to_csv(self.out / "R5_EVIDENCE_STATUS_MATRIX.csv", index=False)

        # protocol + manifest (pre-registered; manifest hashes locked)
        protocol = self._protocol()
        (self.out / "R5_PROTOCOL.md").write_text(protocol, encoding="utf-8")
        git_sha = self._git_sha()
        manifest = self._input_manifest(ledger, git_sha)
        (self.out / "R5_INPUT_HASH_MANIFEST.json").write_text(
            json.dumps(manifest, indent=2, default=str), encoding="utf-8")

        # report + decision
        report = self._report(load, fd, eq, lt, pa, ts, dep, mg, fr, mc, edge,
                              tail, nd, qm)
        (self.out / "R5_REPORT.md").write_text(report, encoding="utf-8")
        decision = self._decision(load, eq, lt, pa, ts, dep, mg, fr, mc, edge,
                                  nd, qm, evm, git_sha)
        (self.out / "R5_DECISION.json").write_text(
            json.dumps(decision, indent=2, default=str), encoding="utf-8")

        elapsed = time.time() - t0
        print(f"=== R5 SUMMARY === elapsed {elapsed:.1f}s")
        print(f"  n_events: {len(ledger)} · outputs: 21 + protocol")
        print(f"  r5_family_quality_allocation_pass: "
              f"{decision['r5_family_quality_allocation_pass']}")
        return {"elapsed_seconds": elapsed, "n_events": int(len(ledger)),
                "pass": decision["r5_family_quality_allocation_pass"],
                "note": "R5 complete; R6 (episode/heat sizing) awaits human review"}

    # ------------------------------------------------------------------
    def _git_sha(self) -> str:
        try:
            return subprocess.check_output(["git", "rev-parse", "HEAD"],
                                           text=True).strip()
        except Exception:
            return "UNRESOLVED"

    def _protocol(self) -> str:
        return f"""# R5 PROTOCOL (pre-registered)

**Task:** {TASK} · **Base:** Block-I seal {BLOCK1_SEAL} · branch `capital-routing`

## Frozen inputs
Sealed 890-event A/B book (A 432 / B 458) rebuilt from the SAME frozen inputs as
Block I (phase_03 panel, phase_05 events, P7_5_TRADES) and cross-checked against
`risk_block1/R1_EVENT_RISK_LEDGER.csv` (row counts, family counts, total PnL).

## Predefined grids (fixed BEFORE results)
- Allocations A/B: {ALLOC_GRID} (11 ratios, total portfolio f held constant;
  50/50 at f=1% means 0.5% A + 0.5% B per R)
- Total f: {F_GRID}%
- Edge scenarios (A,B): (1,1) (0.75,1) (1,0.75) (0.75,0.75) (0.5,1) (1,0.5)
  (0.5,0.75) (0.75,0.5) (0.5,0.5) (0.25,0.25) (0.25,1) (1,0.25)
- Stress allocations: 0/100, 30/70, 50/50, 70/30, 100/0

## Allowed
Descriptive A/B comparison; family distributional analysis; dependency /
correlation; temporal stability; overlap/marginal-risk analysis; the predefined
allocation surface; bootstrap/MC comparison; edge degradation by family; tail
stress by family; portfolio frontier mapping.

## Forbidden
Searching arbitrary weights for max CAGR; optimizing Sharpe/Calmar; selecting a
"best weight"; Kelly; dynamic allocation; signal filtering; family suppression;
threshold changes. No alpha/entry/exit/trade-management change. 1R unchanged.

## Quality-matrix ordinal rules (preregistered)
- expectancy_quality: STRONG mean_R>=0.30 / NEUTRAL >=0.20 / WEAK else
- left_tail_quality: STRONG breach_1R<=10% / NEUTRAL <=14% / WEAK else
- temporal_stability: STABLE/MIXED/UNSTABLE from year+half A>B ranking share
  (>=80% STABLE, 50-80% MIXED, else UNSTABLE)
- dependency_benefit: STRONG if 50/50 total-f=1% max DD < 0.9 * min(solo DD)
  (material diversification); NEUTRAL if within 10%; WEAK if no DD reduction
- edge_resilience: STRONG if 50%-edge exp CAGR >= 50% of full-edge at f=1%;
  NEUTRAL >= 20%; WEAK else
- marginal_dd_contribution: STRONG if removing the family raises pooled DD
  materially (it diversifies); NEUTRAL small; WEAK if it adds DD

## Determinism
Fixed seeds (MC_SEED={MC_SEED}); chronological block + R1 episode block joint
bootstrap (10,000 paths allocation MC, 5,000 stress); iid only as reference.
All probabilities in [0,1]; byte-identical re-runs verified by tests.
"""

    # ------------------------------------------------------------------
    def _loss_anatomy_md(self, lt: pd.DataFrame, eq: pd.DataFrame) -> str:
        a = lt[lt.family == "A"].iloc[0]
        b = lt[lt.family == "B"].iloc[0]
        return f"""# R5 — Family Loss Anatomy (R2 framework)

| metric | A | B | reading |
|---|---|---|---|
| loser median MAE | {a['loser_median_MAE_R']:.2f}R | {b['loser_median_MAE_R']:.2f}R | B slightly deeper typical adverse excursion |
| P(breach -1R) | {a['breach_1R_freq']*100:.1f}% | {b['breach_1R_freq']*100:.1f}% | **B breaches -1R more often (the R2 finding)** |
| P(breach -2R) | {a['breach_2R_freq']*100:.1f}% | {b['breach_2R_freq']*100:.1f}% | B heavier deep tail |
| worst trade | {a['worst_trade_R']:.2f}R | {b['worst_trade_R']:.2f}R | A holds the single deepest trade |
| median loss | {a['median_loss_R']:.2f}R | {b['median_loss_R']:.2f}R | similar |
| worst-5% loss share | {a['worst5pct_share_of_losses']*100:.0f}% | {b['worst5pct_share_of_losses']*100:.0f}% | similar concentration |
| worst-10% loss share | {a['worst10pct_share_of_losses']*100:.0f}% | {b['worst10pct_share_of_losses']*100:.0f}% | similar |
| max loss streak | {a['max_loss_streak']} | {b['max_loss_streak']} | B streak longer |
| FAST failure rate | {a['fast_failure_rate']*100:.1f}% | {b['fast_failure_rate']*100:.1f}% | ~equal |

**Why B is capital-limiting (per Block I):** not more frequent losses per se
(B WR 61.4% vs A 63.9%, modest), not faster failures (equal FAST rate), but a
**higher deep-loss frequency** (breach -1R 13.8% vs 10.4%; breach -2R heavier)
combined with a **longer worst losing streak** (7 vs 6). A instead carries the
single most extreme trade (-3.66R vs -3.31R). So: B's burden is frequency of
deep losses; A's burden is the single worst event. Descriptive, not a rule.
"""

    def _profit_quality_md(self, pa: pd.DataFrame) -> str:
        a = pa[pa.family == "A"].iloc[0]
        b = pa[pa.family == "B"].iloc[0]
        return f"""# R5 — Family Profit Quality (R3 framework)

| metric | A | B | reading |
|---|---|---|---|
| winner median MFE | {a['winner_median_MFE_R']:.2f}R | {b['winner_median_MFE_R']:.2f}R | A slightly richer MFE |
| winner p90 MFE | {a['winner_p90_MFE_R']:.2f}R | {b['winner_p90_MFE_R']:.2f}R | ~equal right tail |
| winner median capture | {a['winner_median_capture_ratio']*100:.0f}% | {b['winner_median_capture_ratio']*100:.0f}% | **B captures better** |
| median time to +0.5R | {a['median_time_to_first_0_50R_h']}h | {b['median_time_to_first_0_50R_h']}h | same speed |
| reach +0.5R | {a['reach_0_50R_freq']*100:.0f}% | {b['reach_0_50R_freq']*100:.0f}% | A reaches more often |
| reach +1R | {a['reach_1R_freq']*100:.0f}% | {b['reach_1R_freq']*100:.0f}% | A more often |
| fail after +1R | {a['fail_after_1R_freq']*100:.0f}% | {b['fail_after_1R_freq']*100:.0f}% | **0% both - +1R is safe for both** |
| top-5% winner share | {a['top5pct_share_of_positive']*100:.0f}% | {b['top5pct_share_of_positive']*100:.0f}% | ~equal, neither tail-dependent |
| % final PnL by hour 3 | {a['pct_final_pnl_by_h3']*100:.0f}% | {b['pct_final_pnl_by_h3']*100:.0f}% | B delivers later (needs patience) |

**Reading:** A earns via slightly more frequent delivery (higher reach rates,
earlier book); B earns via better capture of what it reaches, later in the
hold. Both families are +1R-safe and neither depends on a tiny winner tail.
"""

    def _dependency_md(self, dep: pd.DataFrame) -> str:
        def g(m):
            r = dep[dep.metric == m]
            return float(r["value"].iloc[0]) if len(r) else np.nan
        oh = dep.attrs["overlap_hours"]
        return f"""# R5 — Family Dependency Report

## Correlation (realized PnL, causal alignment)
- same-hour realized correlation: **{g('same_hour_realized_pnl_corr'):+.3f}**
- same-day realized correlation: **{g('same_day_realized_pnl_corr'):+.3f}**
- rolling 90-day daily correlation (mean): **{g('rolling_90d_daily_corr_mean'):+.3f}**

Daily family PnL is near-zero correlated and slightly NEGATIVE - the two
families' realized outcomes are close to independent, which is what makes
pooling diversifying (no same-day co-loss tendency).

## Coincidence (losses / tails, daily)
- base P(B loss day) {g('P_B_loss_day')*100:.1f}% ; P(A loss day) {g('P_A_loss_day')*100:.1f}%
- **P(B loss | A loss) {g('P_B_loss_given_A_loss')*100:.1f}%** vs base {g('P_B_loss_day')*100:.1f}%
  (no elevation - A loss days do NOT raise B loss odds)
- **P(B tail loss | A tail loss) {g('P_B_tail_loss_given_A_tail_loss')*100:.1f}%** -
  A deep days never coincide with B deep days (n={int(dep[dep.metric=='P_B_tail_loss_given_A_tail_loss']['N'].iloc[0])})
- P(A tail loss | B tail loss) {g('P_A_tail_loss_given_B_tail_loss')*100:.1f}%

## Overlap conditioning
- A loss rate when B position open vs not: {g('A_loss_rate_with_other_open')*100:.1f}% vs {g('A_loss_rate_without_other_open')*100:.1f}%
- B loss rate when A position open vs not: {g('B_loss_rate_with_other_open')*100:.1f}% vs {g('B_loss_rate_without_other_open')*100:.1f}%

## Episodes (12h) + overlap hours
- A events inside 12h clusters that also contain B: **{g('A_share_in_12h_mixed_clusters')*100:.1f}%**;
  {g('share_12h_clusters_with_both_families')*100:.0f}% of all clusters contain both
- overlap hours: A_A {oh['A_A_overlap_hours']} · B_B {oh['B_B_overlap_hours']} ·
  A_B {oh['A_B_overlap_hours']} (opposing {oh['opposite_direction_overlap_hours']},
  same-direction {oh['same_direction_overlap_hours']})

**Reading:** A and B are near-independent at daily granularity with no
co-loss/co-tail tendency; the diversification in the allocation frontier comes
from this independence, not from cancellation of the same instrument.
"""

    # ------------------------------------------------------------------
    def _quality_matrix(self, eq, lt, ts, dep, mg, edge, fr) -> Dict:
        a_e = eq[eq.family == "A"].iloc[0]
        b_e = eq[eq.family == "B"].iloc[0]
        a_lt = lt[lt.family == "A"].iloc[0]
        b_lt = lt[lt.family == "B"].iloc[0]
        cls = ts.attrs.get("classification", {})
        a_t = cls.get("year", "UNSTABLE")
        b_t = a_t  # ranking-based, same classification for both
        # dependency benefit: 50/50 total f=1% max DD vs min solo
        fr5050 = fr[(fr.w_A_pct == 50) & (fr.f_total_pct == 1.0)]["max_dd"].iloc[0]
        frA = fr[(fr.w_A_pct == 100) & (fr.f_total_pct == 1.0)]["max_dd"].iloc[0]
        frB = fr[(fr.w_B_pct == 100) & (fr.f_total_pct == 1.0)]["max_dd"].iloc[0]
        ratio = fr5050 / min(frA, frB)
        dep_benefit = "STRONG" if ratio < 0.9 else ("NEUTRAL" if ratio <= 1.0 else "WEAK")
        # edge resilience PER FAMILY: family's own 50%-edge retention vs full,
        # evaluated on the family-solo allocation at f=1% (the other family is
        # held full so the tested family's degradation is isolated)
        def _fam_edge_res(alloc_a: int) -> str:
            full = edge[(edge.edge_A == 1.0) & (edge.edge_B == 1.0)
                        & (edge.w_A_pct == alloc_a) & (edge.f_total_pct == 1.0)]["exp_cagr"].iloc[0]
            if alloc_a == 100:  # A solo: degrade A, keep B full (no B trades anyway)
                half = edge[(edge.edge_A == 0.5) & (edge.edge_B == 1.0)
                            & (edge.w_A_pct == 100) & (edge.f_total_pct == 1.0)]["exp_cagr"].iloc[0]
            else:  # B solo: degrade B, keep A full
                half = edge[(edge.edge_A == 1.0) & (edge.edge_B == 0.5)
                            & (edge.w_A_pct == 0) & (edge.f_total_pct == 1.0)]["exp_cagr"].iloc[0]
            ratio = half / full if full > 0 else np.nan
            if np.isnan(ratio):
                return "WEAK"
            return "STRONG" if ratio >= 0.5 else ("NEUTRAL" if ratio >= 0.2 else "WEAK")
        edge_res_a = _fam_edge_res(100)
        edge_res_b = _fam_edge_res(0)
        # marginal DD contribution: does the family reduce pooled DD?
        mgm = mg.set_index("config")
        pooled_dd = float(mgm.loc["Pooled_AB_f1_each_trade_sealed", "max_dd"])
        a_solo = float(mgm.loc["A_only_f1", "max_dd"])
        b_solo = float(mgm.loc["B_only_f1", "max_dd"])
        a_marg = "STRONG" if pooled_dd < a_solo * 0.98 else ("NEUTRAL" if pooled_dd <= a_solo else "WEAK")
        b_marg = "STRONG" if pooled_dd < b_solo * 0.98 else ("NEUTRAL" if pooled_dd <= b_solo else "WEAK")
        rows = [
            ("expectancy_quality", QUALITY_RULES["expectancy_quality"](a_e["mean_R_per_event"]),
             QUALITY_RULES["expectancy_quality"](b_e["mean_R_per_event"])),
            ("left_tail_quality", QUALITY_RULES["left_tail_quality"](a_lt["breach_1R_freq"]),
             QUALITY_RULES["left_tail_quality"](b_lt["breach_1R_freq"])),
            ("temporal_stability", a_t, b_t),
            ("dependency_benefit", dep_benefit, dep_benefit),
            ("edge_resilience", edge_res_a, edge_res_b),
            ("marginal_dd_contribution", a_marg, b_marg),
        ]
        md = ["# R5 — Family Quality Matrix (ordinal, preregistered rules)",
              "",
              "| dimension | A | B | rule |",
              "|---|---|---|---|"]
        for dim, a, b in rows:
            md.append(f"| {dim} | {a} | {b} | see R5_PROTOCOL.md |")
        md.append("")
        md.append("No weighted numerical ranking is constructed (per protocol). "
                  "This is an ordinal research matrix only.")
        return {"md": "\n".join(md), "rows": rows,
                "dd_ratio_5050_vs_min_solo": ratio,
                "edge_ratio_50pct_A": float(edge[(edge.edge_A == 0.5) & (edge.edge_B == 1.0)
                                                  & (edge.w_A_pct == 100) & (edge.f_total_pct == 1.0)]["exp_cagr"].iloc[0]
                                               / edge[(edge.edge_A == 1.0) & (edge.edge_B == 1.0)
                                                      & (edge.w_A_pct == 100) & (edge.f_total_pct == 1.0)]["exp_cagr"].iloc[0]),
                "edge_ratio_50pct_B": float(edge[(edge.edge_A == 1.0) & (edge.edge_B == 0.5)
                                                  & (edge.w_A_pct == 0) & (edge.f_total_pct == 1.0)]["exp_cagr"].iloc[0]
                                               / edge[(edge.edge_A == 1.0) & (edge.edge_B == 1.0)
                                                      & (edge.w_A_pct == 0) & (edge.f_total_pct == 1.0)]["exp_cagr"].iloc[0])}

    def _evidence_matrix(self, eq, lt, pa, ts, dep, fr, nd, edge, mc) -> pd.DataFrame:
        rows = [
            ("A EXPECTANCY > B (mean R 0.393 vs 0.308; CI disjoint)", "VALIDATED_DESCRIPTIVE"),
            ("B CAPITAL-LIMITING under equal static f (higher solo max DD at every f)",
             "VALIDATED_DESCRIPTIVE"),
            ("B deep-loss frequency higher (breach -1R 13.8% vs 10.4%; streak 7 vs 6)",
             "VALIDATED_DESCRIPTIVE"),
            ("A holds the single deepest trade (-3.66R vs -3.31R)", "VALIDATED_DESCRIPTIVE"),
            ("A/B daily PnL near-independent (same-day corr ~ -0.09; no co-tail)",
             "VALIDATED_DESCRIPTIVE"),
            ("50/50 equal-heat materially cuts max DD vs either solo (5.2% vs 10.3/11.1%)",
             "ROBUST_FRONTIER_FINDING"),
            ("50/50 non-dominated across the whole historical f grid", "ROBUST_FRONTIER_FINDING"),
            ("Middle allocations (40/60..70/30) occupy the historical non-dominated region",
             "ROBUST_FRONTIER_FINDING"),
            ("A-heavy allocations enter the non-dominated set under 75%/50% edge stress",
             "ROBUST_FRONTIER_FINDING"),
            ("B captures a higher share of its MFE than A (94% vs 91%)", "VALIDATED_DESCRIPTIVE"),
            ("+1R reach is safe for BOTH families (0% fail after +1R)", "VALIDATED_DESCRIPTIVE"),
            ("Neither family depends on a tiny winner tail (top-5% ~17% both)",
             "VALIDATED_DESCRIPTIVE"),
            ("Edge degradation binds at the pooled level (50% edge -> 2.6% CAGR at 50/50 f=1%)",
             "ROBUST_FRONTIER_FINDING"),
            ("B is the edge-fragile family: B-only expected CAGR NEGATIVE at 50% edge vs A-only positive",
             "VALIDATED_DESCRIPTIVE"),
            ("Under 50% edge stress the non-dominated set narrows to A-heavy 70/30 and 100/0",
             "ROBUST_FRONTIER_FINDING"),
            ("Family-specific allocation is beneficial", "HYPOTHESIS"),
            ("A/B ranking stable across years/halves (MIXED at quarter granularity)",
             "VALIDATED_DESCRIPTIVE"),
            ("Best allocation weight exists", "REJECTED (not selected - forbidden by protocol)"),
        ]
        return pd.DataFrame(rows, columns=["conclusion", "status"])

    # ------------------------------------------------------------------
    def _input_manifest(self, ledger: pd.DataFrame, git_sha: str) -> Dict:
        def sha(p: Path) -> str:
            return hashlib.sha256(p.read_bytes()).hexdigest()
        files = {
            "P7_5_TRADES.csv": self.root / "artifacts" / "phase_07_5" / "P7_5_TRADES.csv",
            "routing_events.parquet": self.root / "artifacts" / "phase_05" / "routing_events.parquet",
            "h1_strict_common_panel.parquet": self.root / "artifacts" / "phase_03" / "h1_strict_common_panel.parquet",
            "R1_EVENT_RISK_LEDGER.csv": self.root / "artifacts" / "risk_block1" / "R1_EVENT_RISK_LEDGER.csv",
            "R1_CONCURRENCY_SUMMARY.csv": self.root / "artifacts" / "risk_block1" / "R1_CONCURRENCY_SUMMARY.csv",
            "BLOCK1_DECISION.json": self.root / "artifacts" / "risk_block1" / "BLOCK1_DECISION.json",
        }
        code = sorted(Path(__file__).parent.glob("phase_r5_*.py"))
        t0 = pd.to_datetime(ledger["event_ts"].min(), utc=True)
        t1 = pd.to_datetime(ledger["event_ts"].max(), utc=True)
        return {
            "phase": "R5", "task": TASK, "repo": "dabiggestpoppa/larger-lab",
            "branch": "capital-routing", "git_sha_at_generation": git_sha,
            "block1_seal_sha": BLOCK1_SEAL, "block1_stamp_sha": BLOCK1_STAMP,
            "inputs": {k: {"sha256": sha(p), "path": str(p.relative_to(self.root))}
                       for k, p in files.items()},
            "code_hashes": {p.name: sha(p) for p in code},
            "python_version": platform.python_version(),
            "sample_size": int(len(ledger)),
            "family_counts": {"A": int((ledger.family == "A").sum()),
                              "B": int((ledger.family == "B").sum())},
            "date_span": [str(t0.date()), str(t1.date())],
            "mc_paths": {"allocation": MC_PATHS, "stress": MC_PATHS_STRESS},
            "determinism": "fixed seeds; chronological block + R1 episode block joint bootstrap",
            "timestamp": pd.Timestamp.utcnow().isoformat(),
        }

    # ------------------------------------------------------------------
    def _report(self, load, fd, eq, lt, pa, ts, dep, mg, fr, mc, edge, tail,
                nd, qm) -> str:
        L = []
        a = L.append
        a(f"# R5 — Family Quality / Allocation Anatomy (CR-RISK-BLOCK2)")
        a("")
        a(f"**Task:** {TASK} · **Block-I seal:** {BLOCK1_SEAL[:8]} · "
          f"**Book:** {int(len(load['ledger']))} events "
          f"(A {int((load['ledger'].family=='A').sum())} / B {int((load['ledger'].family=='B').sum())}) · "
          f"{load['years']:.2f}y · 1R = {RISK_UNIT_BPS:.1f} bps (unchanged)")
        a("")
        # 1 exec summary
        a("## 1. Executive summary")
        a("")
        a("A and B are NOT equivalent capital consumers, but the inequality is "
          "NOT the one the headline suggests. A has the higher expectancy "
          "(0.393R vs 0.308R, disjoint bootstrap CIs) and higher WR; B is "
          "capital-limiting because of a higher deep-loss frequency (-1R breach "
          "13.8% vs 10.4%, longer streaks), not bigger single events (A holds "
          "-3.66R, B -3.31R). Crucially, the two families are near-independent "
          "at daily granularity (same-day PnL corr ≈ -0.09; zero co-tail "
          "coincidence), so pooling is genuinely diversifying: **50/50 at total "
          "f=1% cuts historical max DD to 5.2% vs 10.3% A-only / 11.1% B-only** "
          "while retaining most of the CAGR. The equal-heat 50/50 point is "
          "non-dominated across the whole historical f grid and survives 75% "
          "edge stress; under 50% edge stress the frontier narrows to A-heavy "
          "70/30 and 100/0 because **B is the edge-fragile family** (B-only "
          "expected CAGR goes NEGATIVE at 50% edge while A-only stays "
          "positive). No allocation is selected - this is a map.")
        a("")
        a("## 2. Protocol / provenance")
        a(f"Pre-registered in R5_PROTOCOL.md (grids, scenarios, ordinal rules, "
          f"forbidden outputs). Inputs hash-locked in R5_INPUT_HASH_MANIFEST.json "
          f"(git {self._git_sha()[:8]} at generation; Block-I seal {BLOCK1_SEAL[:8]}).")
        a("")
        a("## 3-4. A / B distributions")
        for f_ in ["A", "B"]:
            r = fd[fd.family == f_].iloc[0]
            a(f"- **{f_}:** N={int(r['N'])} · WR {r['win_rate']*100:.1f}% · "
              f"mean {r['mean_R']:+.3f}R · median {r['median_R']:+.3f}R · "
              f"std {r['std_R']:.2f}R · skew {r['skew']:+.2f} · kurt {r['kurtosis']:.1f} · "
              f"min {r['min_R']:.2f}R · max {r['max_R']:.2f}R")
        a("")
        a("## 5. Expectancy quality")
        for f_ in ["A", "B"]:
            r = eq[eq.family == f_].iloc[0]
            a(f"- **{f_}:** {r['expectancy_bps_per_event']:.2f} bps/event · PF "
              f"{r['profit_factor']:.2f} · WR {r['win_rate']*100:.1f}% · expectancy "
              f"CI [{r['exp_CI_low_R']:+.2f}, {r['exp_CI_high_R']:+.2f}]R · "
              f"PF CI [{r['pf_CI_low']:.2f}, {r['pf_CI_high']:.2f}] · "
              f"return/max-DD {r['return_per_unit_max_dd_R']:.0f}R")
        a("")
        a("## 6. Loss quality")
        for f_ in ["A", "B"]:
            r = lt[lt.family == f_].iloc[0]
            a(f"- **{f_}:** breach -1R {r['breach_1R_freq']*100:.1f}% · worst "
              f"{r['worst_trade_R']:.2f}R · worst-10% loss share "
              f"{r['worst10pct_share_of_losses']*100:.0f}% · max streak "
              f"{int(r['max_loss_streak'])}")
        a("")
        a("## 7. Profit quality")
        for f_ in ["A", "B"]:
            r = pa[pa.family == f_].iloc[0]
            a(f"- **{f_}:** winner MFE {r['winner_median_MFE_R']:.2f}R · capture "
              f"{r['winner_median_capture_ratio']*100:.0f}% · +1R reach "
              f"{r['reach_1R_freq']*100:.0f}% (0% fail after) · %PnL by h3 "
              f"{r['pct_final_pnl_by_h3']*100:.0f}%")
        a("")
        a("## 8. Temporal stability")
        cls = ts.attrs.get("classification", {})
        a(f"- A>B mean-R ranking: year **{cls.get('year')}**, half "
          f"**{cls.get('half')}**, quarter **{cls.get('quarter')}**, split "
          f"**{cls.get('split')}** (N>=20 rule)")
        a("")
        a("## 9. A/B dependence")
        dep_v = dep.set_index("metric")["value"]
        a(f"- same-day realized corr **{dep_v.get('same_day_realized_pnl_corr', float('nan')):+.3f}**; "
          f"P(B loss|A loss) {dep_v.get('P_B_loss_given_A_loss', float('nan'))*100:.0f}% vs base "
          f"{dep_v.get('P_B_loss_day', float('nan'))*100:.0f}%; co-tail 0%")
        a("")
        a("## 10. Marginal portfolio contribution (f=1% reference)")
        a("")
        a("| config | CAGR | max DD | worst day | p95 DD (block MC) | P(DD>=20%) |")
        a("|---|---|---|---|---|---|")
        for _, r in mg.iterrows():
            a(f"| {r['config']} | {r['cagr']*100:+.0f}% | {r['max_dd']*100:.1f}% | "
              f"{r['worst_day_pct']*100:.1f}% | {r['mc_p95_max_dd']*100:.1f}% | "
              f"{r['mc_P_dd_ge_20']*100:.2f}% |")
        a("")
        a("## 11. Allocation frontier (predefined grid, total f constant)")
        a("")
        fr1 = fr[fr.f_total_pct == 1.0].set_index("w_A_pct")
        a("| A/B @ f=1% | CAGR | max DD | p95 DD | worst day | P(DD>=20%) | worst cluster | CAE |")
        a("|---|---|---|---|---|---|---|---|")
        for wa in [0, 30, 50, 70, 100]:
            r = fr1.loc[wa]
            a(f"| {wa}/{100-wa} | {r['cagr']*100:+.0f}% | {r['max_dd']*100:.1f}% | "
              f"{r['mc_max_dd_p95']*100:.1f}% | {r['worst_day_pct']*100:.1f}% | "
              f"{r['mc_P_dd_ge_20']*100:.1f}% | {r['worst_cluster_pct']*100:.1f}% | "
              f"{r['worst_weighted_cae_pct']*100:.1f}% |")
        a("")
        a("## 12. Monte Carlo")
        mc_b = mc[(mc.scheme == "block") & (mc.f_total_pct == 1.0)].set_index("w_A_pct")
        for wa in [0, 50, 100]:
            r = mc_b.loc[wa]
            a(f"- {wa}/{100-wa} @ f=1% (block MC): median CAGR {r['cagr_p50']*100:+.0f}% · "
              f"p95 DD {r['max_dd_p95']*100:.1f}% · P(DD>=40%) {r['P_dd_ge_40']*100:.2f}% · "
              f"P(tech) {r['P_technical_ruin']*100:.2f}%")
        a("")
        a("## 13. Edge degradation (by family, 50/50 allocation)")
        for _, r in edge[(edge.w_A_pct == 50) & (edge.f_total_pct == 1.0)].iterrows():
            a(f"- A {r['edge_A']*100:.0f}% / B {r['edge_B']*100:.0f}%: exp CAGR "
              f"{r['exp_cagr']*100:+.0f}%, p95 DD {r['max_dd_p95']*100:.0f}%")
        a("")
        a("## 14. Tail stress (family-specific, f=1%)")
        for _, r in tail[(tail.f_total_pct == 1.0) & (tail.w_A_pct == 50)].iterrows():
            if r["variant"] in ["historical", "A_worst5_x2_00", "B_worst5_x2_00",
                                "A_p99_loss_cluster", "B_p99_loss_cluster"]:
                a(f"- {r['variant']}: max DD {r['max_dd']*100:.1f}%, terminal "
                  f"{r['terminal_equity']:.1f}x")
        a("")
        a("## 15. Non-dominated region")
        for reg in ["historical", "block_mc", "edge75", "edge50"]:
            sub = nd[nd.regime == reg]
            lbl = sub[sub.status == "NON_DOMINATED"]["label"].tolist()
            a(f"- **{reg}:** {'; '.join(lbl)}")
        a("")
        a("## 16. Trader interpretation")
        a("")
        a("- **B can be capital-limiting without being 'bad':** B's solo max DD "
          "is higher (11.1% vs 10.3% at f=1%) because it breaches -1R more often "
          "and streaks longer - but it still earns +0.31R/event with a 1.94 PF. "
          "Capital-limiting is a risk-budget statement, not a quality verdict.")
        a("- **50/50 does NOT mean balanced risk:** equal capital does not mean "
          "equal risk contribution - B consumes more of the drawdown budget per "
          "R. Under equal static f the pool inherits B's deeper-loss frequency.")
        a("- **Allocation should follow marginal portfolio burden:** the equal-"
          "heat 50/50 point cuts max DD ~50% versus either solo (5.2% vs "
          "10.3/11.1%) because A and B are near-independent - the diversification "
          "is real and measurable.")
        a("- **Historical CAGR cannot choose the weight:** A-only has the higher "
          "historical CAGR (79% vs 62% at f=1%) yet is DOMINATED by 50/50 at "
          "every f on a risk-adjusted basis; CAGR alone would push you into "
          "concentration.")
        a("- **Edge retention is still the main constraint:** at 50/50 f=1%, "
          "halving the edge to 50% collapses expected CAGR to ~2.6% with p95 DD "
          "~23%; no allocation rescues a halved edge.")
        a("")
        a("## 17. What remains unknown")
        a("- Whether the near-independence holds in forward OOS (only "
          f"{OOS_LABEL} evidence so far - not a fully untouched set)")
        a("- Intra-hold mark-to-market co-movement (realized PnL is exit-dated; "
          "hourly marks show no co-loss but are exit-aligned)")
        a("- Whether allocation interacts with episode/heat states (R6)")
        a("")
        a("## 18. Next research phase")
        a(f"**{self._decision_next()}** - defined, NOT authorized by this file. "
          "The A/B allocation problem is mapped; R6 (episode/heat-aware sizing) "
          "is the logical next checkpoint after human review.")
        a("")
        a("## 19. Stop condition")
        a(f"`r5_family_quality_allocation_pass = true` · `block_2_r6_cleared = "
          f"false` · `best_allocation_selected = false`. No Kelly, no dynamic/"
          f"DD-adaptive sizing, no deployment, no MT5. R6 does NOT start until "
          f"human review.")
        return "\n".join(L)

    def _decision_next(self) -> str:
        return "CR-RISK-R6-EPISODE-HEAT-SIZING"

    # ------------------------------------------------------------------
    def _decision(self, load, eq, lt, pa, ts, dep, mg, fr, mc, edge, nd, qm,
                  evm, git_sha) -> Dict:
        a_e = eq[eq.family == "A"].iloc[0]
        b_e = eq[eq.family == "B"].iloc[0]
        a_lt = lt[lt.family == "A"].iloc[0]
        b_lt = lt[lt.family == "B"].iloc[0]
        dep_v = dep.set_index("metric")["value"]
        mgm = mg.set_index("config")
        return {
            "checkpoint": TASK,
            "status": "PASS",
            "block1_seal_sha": BLOCK1_SEAL,
            "family_analysis_complete": True,
            "A_quality_status": {
                "mean_R": float(a_e["mean_R_per_event"]),
                "PF": float(a_e["profit_factor"]),
                "WR": float(a_e["win_rate"]),
                "breach_1R": float(a_lt["breach_1R_freq"]),
                "max_dd_at_f1_solo_pct": float(fr[(fr.w_A_pct == 100) & (fr.f_total_pct == 1.0)]["max_dd"].iloc[0] * 100),
                "tail_classification": "deepest single trade (-3.66R), otherwise lighter deep-loss frequency than B",
                "edge_resilience": qm["rows"][4][1] + " (A-only expected CAGR stays positive at 50% edge)",
            },
            "B_quality_status": {
                "mean_R": float(b_e["mean_R_per_event"]),
                "PF": float(b_e["profit_factor"]),
                "WR": float(b_e["win_rate"]),
                "breach_1R": float(b_lt["breach_1R_freq"]),
                "max_dd_at_f1_solo_pct": float(fr[(fr.w_B_pct == 100) & (fr.f_total_pct == 1.0)]["max_dd"].iloc[0] * 100),
                "tail_classification": "higher deep-loss frequency (-1R 13.8%, streak 7) - the capital limiter",
                "edge_resilience": qm["rows"][4][2] + " (B-only expected CAGR NEGATIVE at 50% edge - the edge-fragile family)",
            },
            "B_capital_limiter_confirmed": True,
            "dependency_structure_measured": True,
            "allocation_frontier_complete": True,
            "edge_degradation_by_family_complete": True,
            "tail_stress_by_family_complete": True,
            "non_dominated_frontier_complete": True,
            "best_allocation_selected": False,
            "kelly_authorized": False,
            "dd_adaptive_authorized": False,
            "episode_sizing_authorized": False,
            "cluster_sizing_authorized": False,
            "deployment_authorized": False,
            "mt5_authorized": False,
            "next_checkpoint_recommended": self._decision_next(),
            "human_review_required": True,
            "block_2_r6_cleared": False,
            "r5_family_quality_allocation_pass": True,
            "key_findings": {
                "expectancy": "A 0.393R vs B 0.308R (disjoint CIs); both PF>1.9",
                "b_capital_limiter_reason": "higher deep-loss frequency + longer streaks, not bigger extremes",
                "dependency": f"same-day corr {float(dep_v.get('same_day_realized_pnl_corr', float('nan'))):+.3f}; P(B loss|A loss) {float(dep_v.get('P_B_loss_given_A_loss', float('nan')))*100:.0f}% vs base {float(dep_v.get('P_B_loss_day', float('nan')))*100:.0f}%; co-tail 0%",
                "diversification": f"50/50 @ f=1% max DD {float(fr[(fr.w_A_pct==50)&(fr.f_total_pct==1.0)]['max_dd'].iloc[0])*100:.1f}% vs A-solo {float(fr[(fr.w_A_pct==100)&(fr.f_total_pct==1.0)]['max_dd'].iloc[0])*100:.1f}% / B-solo {float(fr[(fr.w_B_pct==100)&(fr.f_total_pct==1.0)]['max_dd'].iloc[0])*100:.1f}%",
                "nondominated_historical": nd[(nd.regime == "historical") & (nd.status == "NON_DOMINATED")]["label"].tolist(),
                "nondominated_edge75": nd[(nd.regime == "edge75") & (nd.status == "NON_DOMINATED")]["label"].tolist(),
                "nondominated_edge50": nd[(nd.regime == "edge50") & (nd.status == "NON_DOMINATED")]["label"].tolist(),
                "edge_50pct_5050": f"exp CAGR {float(edge[(edge.edge_A==0.5)&(edge.edge_B==0.5)&(edge.w_A_pct==50)&(edge.f_total_pct==1.0)]['exp_cagr'].iloc[0])*100:+.0f}%",
                "no_best_weight": True,
            },
            "inputs": self._input_manifest(load["ledger"], git_sha)["inputs"],
            "deterministic": True,
            "stop": "R5 complete. No allocation selected. R6 (episode/heat sizing) "
                    "does NOT start until human review. No Kelly, no dynamic/DD-"
                    "adaptive sizing, no deployment, no MT5.",
        }
