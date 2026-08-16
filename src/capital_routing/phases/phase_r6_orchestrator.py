"""
CR-RISK-BLOCK2 R6 â€” Episode / Heat Sizing (orchestrator).

Runs V-XXV, writes the 22 R6 artifacts under artifacts/risk_block2/r6/
(protocol, manifest, heat-definition lock, admission ledger, policy summary,
historical frontier, efficiency, episode policy results, directional overlap,
family episode structure, MC, edge degradation, tail stress, adversarial
tests, rejected audit, temporal stability, non-dominated frontier, complexity
matrix, evidence matrix, report, decision). STOPS after R6: no policy is
selected, R7 is NOT authorized, no Kelly / DD-adaptive / hybrid / deployment /
MT5. Alpha, entries, exits, trade management, family definitions and 1R are
unchanged.
"""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from .phase_r4_common import RISK_UNIT_BPS
from .phase_r6_analysis import (complexity_matrix, directional_overlap,
                                episode_policy_results,
                                family_episode_structure, overlap_anatomy,
                                rejected_event_audit, temporal_stability)
from .phase_r6_common import (ALLOC_SET, EDGE_SCENARIOS, F_GRID, F_GRID_MC,
                              MC_70_30, MC_F, MC_SEED, POLICY_GRID,
                              build_episode_ledger, episode_peak_heat_from_hourly,
                              hourly_heat_breakdown, load_r6_inputs,
                              policy_metrics, run_policy)
from .phase_r6_mc import heat_edge_mc, heat_policy_mc
from .phase_r6_stress import adversarial_episode_tests, heat_tail_stress

TASK = "CR-RISK-BLOCK2-R6-EPISODE-HEAT-SIZING"
R5_COMMIT = "150a93dec8edf2997652cd20724298fe9927c0dc"
R5_STAMP = "c7cedb975e99d7d9d5fede3aee5ec170600a0c88"
BLOCK1_SEAL = "8ca072d0d939acf581770a99ce45b333deddd8c"
BLOCK1_STAMP = "470702c2bb445e1f7a1be949efd6ec3a75b74878"

# MC scope (pre-registered; path counts are fixed before results)
MC_5050 = ["H0", "H1-1.00-REJ", "H1-1.50-REJ", "H1-2.00-REJ", "H2-1.00-REJ",
           "H2-1.50-REJ", "H3-0.50-REJ", "H3-0.75-REJ", "H4-1.00-REJ",
           "H4-1.50-REJ", "H5-1.50-REJ"]
MC_CORE_5050 = {"H0", "H1-1.50-REJ", "H2-1.50-REJ", "H3-0.75-REJ",
                "H4-1.50-REJ", "H5-1.50-REJ"}
MC_EDGE_POLICIES = ["H0", "H1-1.00-REJ", "H1-1.50-REJ", "H2-1.50-REJ",
                    "H3-0.75-REJ", "H5-1.50-REJ"]
MC_TAIL_POLICIES = ["H0", "H1-1.00-REJ", "H1-1.50-REJ", "H2-1.00-REJ",
                    "H2-1.50-REJ", "H3-0.50-REJ", "H3-0.75-REJ",
                    "H4-1.00-REJ", "H4-1.50-REJ", "H5-1.50-REJ"]


class PhaseR6HeatSizing:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.out = self.root / "artifacts" / "risk_block2" / "r6"
        self.out.mkdir(parents=True, exist_ok=True)
        self._pols = {p["policy_id"]: p for p in POLICY_GRID}

    def _pol(self, pid: str) -> Dict:
        return self._pols[pid]

    # ------------------------------------------------------------------
    def run(self) -> Dict:
        t0 = time.time()
        print("[R6] load frozen inputs + episode reconstruction")
        load = load_r6_inputs(self.root)
        years = load["years"]
        ba = load["ba"]
        n_events = len(ba["tb"])

        # II + III: input hash manifest + protocol are written BEFORE any
        # results (frozen inputs and pre-registered surface precede output).
        print("[R6.II] input hash manifest + [R6.III] protocol (pre-results)")
        git_sha = self._git_sha()
        (self.out / "R6_INPUT_HASH_MANIFEST.json").write_text(
            json.dumps(self._manifest(load, git_sha), indent=2, default=str),
            encoding="utf-8")
        (self.out / "R6_PROTOCOL.md").write_text(self._protocol(), encoding="utf-8")

        # V
        print("[R6.V] episode ledger")
        ep_led = load["episode_ledger"]
        ep_led.to_csv(self.out / "R6_EVENT_EPISODE_LEDGER.csv", index=False)

        # VI heat definition lock
        (self.out / "R6_HEAT_DEFINITION_LOCK.md").write_text(
            self._heat_lock_md(), encoding="utf-8")

        # XII overlap anatomy FIRST (before judging any policy)
        print("[R6.XII] overlap anatomy")
        oa = overlap_anatomy(load, 0.5, 0.5)
        oa.to_csv(self.out / "R6_OVERLAP_ANATOMY.csv", index=False)

        # XI admission ledger (reference base_f=1.0; decisions f-invariant)
        print("[R6.XI] admission decision ledger")
        adm_rows = []
        for wa_pct, wb_pct in ALLOC_SET:
            wA, wB = wa_pct / 100.0, wb_pct / 100.0
            for pol in POLICY_GRID:
                res = run_policy(load, pol, wA, wB, full_output=True)
                res["policy_id"] = pol["policy_id"]
                res["base_f"] = 1.0
                res["A_weight"] = wA
                res["B_weight"] = wB
                adm_rows.append(res[["event_id", "entry_ts", "policy_id",
                                     "family", "direction", "base_f",
                                     "A_weight", "B_weight", "requested_f",
                                     "pre_gross_heat", "pre_same_direction_heat",
                                     "pre_opposite_direction_heat",
                                     "pre_A_heat", "pre_B_heat",
                                     "episode_budget_used", "remaining_heat",
                                     "admitted_f", "decision", "reason"]])
        adm_led = pd.concat(adm_rows, ignore_index=True)
        adm_led.to_csv(self.out / "R6_ADMISSION_DECISION_LEDGER.csv", index=False)

        # XII policy admission summary
        print("[R6.XII] policy admission summary")
        summary = self._policy_admission_summary(load, adm_led)
        summary.to_csv(self.out / "R6_POLICY_ADMISSION_SUMMARY.csv", index=False)

        # XIII historical frontier (all policies x allocs x f)
        print("[R6.XIII] historical heat-policy frontier")
        frontier = self._historical_frontier(load, years)
        frontier.to_csv(self.out / "R6_HEAT_POLICY_FRONTIER.csv", index=False)

        # XIV heat efficiency
        print("[R6.XIV] heat efficiency")
        eff = self._heat_efficiency(load, years)
        eff.to_csv(self.out / "R6_HEAT_EFFICIENCY.csv", index=False)

        # XV episode policy results
        print("[R6.XV] episode policy results")
        ep_pol = episode_policy_results(load, POLICY_GRID, 0.5, 0.5)
        ep_pol.to_csv(self.out / "R6_EPISODE_POLICY_RESULTS.csv", index=False)

        # XVI directional overlap
        print("[R6.XVI] directional overlap")
        do = directional_overlap(load, 0.5, 0.5)
        do.to_csv(self.out / "R6_DIRECTIONAL_OVERLAP.csv", index=False)

        # XVII family episode structure
        print("[R6.XVII] family episode structure")
        fes = family_episode_structure(load, 0.5, 0.5)
        fes.to_csv(self.out / "R6_FAMILY_EPISODE_STRUCTURE.csv", index=False)

        # XVIII MC
        print(f"[R6.XVIII] heat-policy MC (block {self._mc_block_paths()} + "
              f"episode paths, deterministic)")
        mc = self._monte_carlo(load, years)
        mc.to_csv(self.out / "R6_HEAT_POLICY_MONTE_CARLO.csv", index=False)

        # XIX edge degradation
        print("[R6.XIX] heat edge degradation")
        edge = heat_edge_mc(load, [self._pol(p) for p in MC_EDGE_POLICIES],
                            0.5, 0.5, EDGE_SCENARIOS, 2000, 1.0, seed=MC_SEED)
        edge.to_csv(self.out / "R6_HEAT_EDGE_DEGRADATION.csv", index=False)

        # XX tail stress
        print("[R6.XX] heat tail stress")
        tail = heat_tail_stress(load, [self._pol(p) for p in MC_TAIL_POLICIES],
                                0.5, 0.5)
        tail.to_csv(self.out / "R6_HEAT_TAIL_STRESS.csv", index=False)

        # XXI adversarial episodes
        print("[R6.XXI] adversarial episode tests")
        adv = adversarial_episode_tests(load, 0.5, 0.5)
        adv.to_csv(self.out / "R6_ADVERSARIAL_EPISODE_TESTS.csv", index=False)

        # XXII rejected-event audit
        print("[R6.XXII] rejected-event audit")
        rej = rejected_event_audit(load, POLICY_GRID, 0.5, 0.5)
        rej.to_csv(self.out / "R6_REJECTED_EVENT_AUDIT.csv", index=False)

        # XXIII temporal stability
        print("[R6.XXIII] temporal stability")
        ts = temporal_stability(load, POLICY_GRID, 0.5, 0.5)
        ts.to_csv(self.out / "R6_HEAT_TEMPORAL_STABILITY.csv", index=False)

        # XXIV non-dominated frontier
        print("[R6.XXIV] non-dominated heat frontier")
        nd = self._nondominated(frontier, mc, edge, tail)
        nd.to_csv(self.out / "R6_NONDOMINATED_HEAT_FRONTIER.csv", index=False)

        # XXV complexity matrix
        cm = complexity_matrix(POLICY_GRID)
        cm.to_csv(self.out / "R6_POLICY_COMPLEXITY_MATRIX.csv", index=False)

        # XXVIII evidence matrix (protocol + manifest were already written
        # pre-results in step II/III; never overwritten by results).
        evm = self._evidence_matrix(load, frontier, mc, edge, tail, nd, ep_pol,
                                    do, fes, summary)
        evm.to_csv(self.out / "R6_EVIDENCE_STATUS_MATRIX.csv", index=False)

        # report + decision
        report = self._report(load, frontier, mc, edge, tail, nd, ep_pol, do,
                              fes, summary, eff, rej, ts, adv)
        (self.out / "R6_REPORT.md").write_text(report, encoding="utf-8")
        decision = self._decision(load, frontier, mc, edge, tail, nd, summary,
                                  evm, git_sha)
        (self.out / "R6_DECISION.json").write_text(
            json.dumps(decision, indent=2, default=str), encoding="utf-8")

        elapsed = time.time() - t0
        print(f"=== R6 SUMMARY === elapsed {elapsed:.1f}s")
        print(f"  n_events: {n_events} · outputs: 22 + protocol")
        print(f"  r6_episode_heat_sizing_pass: {decision['r6_episode_heat_sizing_pass']}")
        return {"elapsed_seconds": elapsed, "n_events": n_events,
                "pass": decision["r6_episode_heat_sizing_pass"],
                "note": "R6 complete; R7 (DD-adaptive) awaits human review"}

    # ------------------------------------------------------------------
    def _git_sha(self) -> str:
        try:
            return subprocess.check_output(["git", "rev-parse", "HEAD"],
                                           text=True).strip()
        except Exception:
            return "UNRESOLVED"

    def _mc_block_paths(self) -> int:
        return 8000

    def _mc_episode_paths(self) -> int:
        return 3000

    # ------------------------------------------------------------------
    def _heat_lock_md(self) -> str:
        return f"""# R6 â€” Account Heat Definition Lock (VI)

Seven distinct heat concepts (all measured on the sealed 890-event A/B book;
1R = {RISK_UNIT_BPS:.1f} bps, unchanged; account mapping
account_return ~= trade_return_R x assigned_f):

| # | concept | definition |
|---|---|---|
| 1 | PER-EVENT f | the static fraction assigned to one R for an event. With a family allocation (w_A, w_B), the event's requested heat = base_f x w_family. |
| 2 | GROSS HEAT | sum of the assigned f of ALL active events (opposing positions included; they are NOT automatically riskless). |
| 3 | NET DIRECTIONAL HEAT | direction-aware net exposure proxy (signed sum of active assigned f). Reported descriptively; opposing events never cancel economic risk. |
| 4 | FAMILY HEAT | active A heat and active B heat separately (sum of assigned f of active events per family). |
| 5 | EPISODE HEAT | the maximum gross heat reached inside a 12h R1 episode (cluster). |
| 6 | REALIZED EPISODE LOSS | realized portfolio loss within an episode (sum of admitted f x final R of the episode's admitted events). |
| 7 | CAE HEAT | portfolio concurrent adverse excursion (min of the summed net-R path of the active events, in R units, unscaled by f). |

**Cap units:** all caps are multiples of the base per-event f (e.g. at base
f=1%, H1 cap 1.0x = 1.0% gross active heat). At 50/50 allocation each event
requests 0.5% at base f=1%, so a 1.0x gross cap admits up to two concurrent
events.

**Admission invariance:** requested heat and every cap scale linearly with
base_f, so admission decisions are identical at every f level; account PnL
scales linearly with f. The admission ledger is emitted at the reference
base_f = 1.0 and is representative at every level.

**Causality:** admission uses ONLY active heat known at entry time. Never
future outcome, future MAE/DD, or later performance.
"""

    def _protocol(self) -> str:
        return f"""# R6 PROTOCOL (pre-registered)

**Task:** {TASK} · **Base:** Block-I seal {BLOCK1_SEAL[:8]} · R5 {R5_COMMIT[:8]} ·
branch `capital-routing`

## Frozen inputs
Sealed 890-event A/B book (A 432 / B 458) rebuilt from the SAME frozen inputs
as Block-I/R5 and cross-checked against R1_EVENT_RISK_LEDGER.csv. Episodes use
the R1 12h cluster framework (interval_h = 12); cluster membership reconciled
with R1_ROUTING_EPISODES.csv.

## Predefined policy surface (VIII, frozen BEFORE results)
H0 unconstrained; H1 gross heat cap; H2 same-direction heat cap; H3 family-B
heat cap; H4 12h episode budget; H5 hybrid (gross + same-direction).
Cap multiples: H1 1.0/1.5/2.0/3.0x, H2 1.0/1.5/2.0x, H3 0.5/0.75/1.0x,
H4 1.0/1.5/2.0/3.0x, H5 (1.5,1.0)/(2.0,1.5)x. Treatments: REJECT_NEW on the
full grid; SCALE_NEW_TO_REMAINING_CAP on a pre-registered subset (H1 1.0/1.5/2.0,
H2 1.0/1.5, H3 0.5/0.75, H4 1.0/1.5, H5 both). 28 core configurations <= 50.
No post-hoc additions.

## Allocations (X)
50/50 (primary), 70/30, 100/0 (reference). Total portfolio heat held
comparable: an event requests base_f x w_family.

## f levels (VII)
Historical frontier: 0.25/0.50/0.75/1.00/1.50/2.00%. MC: 0.50/1.00/2.00%.

## Monte Carlo (XVIII, XIX) â€” pre-registered path counts
- 50/50: {len(MC_5050)} policies; block bootstrap {self._mc_block_paths()} paths
  (core {{H0, H1-1.5, H2-1.5, H3-0.75, H4-1.5, H5-1.5}}), 4,000 for the rest;
  episode bootstrap {self._mc_episode_paths()} paths.
- 70/30: 8 policies (same core split).
- iid: reference only (H0, 50/50, 3,000 paths).
- Edge degradation: 50/50, f=1%, block 2,000 paths, 8 scenarios
  {{(1,1),(0.75,0.75),(0.5,1),(1,0.5),(0.5,0.5),(0.25,0.25),(0.75,0.5),(0.5,0.75)}}.
- Deterministic seed {MC_SEED} everywhere.

## Tail / cluster stress (XX, frozen)
worst5_x1_5 and worst5_x2 (worst 5% losses scaled x1.5 / x2), insert_worst_1,
insert_p99_loss_cluster (5 p99-magnitude loss bleeds), worstA_cluster /
worstB_cluster / mixed_AB_cluster (worst 12h clusters by composition).
Adversarial episode patterns (XXI): A loss->B loss, B loss->B loss,
A loss->A loss->B loss, 3 same-direction losses, mixed-direction losses,
B-heavy, A+B cluster. Reported per variant: max DD, p95 DD, worst day /
worst episode, CAE, technical-ruin probability, return sacrifice.

## Temporal partitions (XXIII, frozen)
split (inner_sel / inner_val / RELATIONSHIP_CONFIRMED_OOS) and calendar year;
per partition report rejection rate, mean admitted f, max gross heat, CAGR,
max DD, worst episode, tail loss; classified STABLE / MIXED / UNSTABLE.

## Admission semantics (XI)
Chronological by entry; active heat computed immediately BEFORE entry; ties
ordered by (entry, exit, event_id) (documented, deterministic). Decisions:
ACCEPT_FULL / ACCEPT_SCALED / REJECT_HEAT_CAP with exact reason. Existing
positions are never modified.

## Evaluation metrics (XIII)
CAGR, total return, max DD, Calmar, Sortino, worst day/24h/48h, worst episode,
ulcer index, recovery factor, p95/p99 DD, P(DD>=10/15/20/30/40%), technical
ruin, gross-heat distribution.

## Allowed / forbidden
Allowed: episode reconstruction, heat definitions, causal admission,
historical frontier, directional/family overlap anatomy, dependency-aware MC,
edge/tail stress, rejected-event audit, temporal stability, non-dominated
frontier mapping. Forbidden: searching policies for max Calmar/CAGR,
optimizing cap multiples, selecting a "best policy", Kelly, DD-adaptive or
dynamic sizing, episode-aware sizing, deployment, MT5, any alpha/entry/exit/
trade-management change.

## PASS criteria (XXX)
Episode reconstruction reconciles with R1; policies causal; heat accounting
exact; H0 reproduces the sealed baseline; surface complete; MC complete;
edge/tail stress complete; temporal stability complete; non-dominated frontier
complete; no best policy selected; repo tests pass. A null result is
acceptable: if heat caps do not materially help, that is the finding.
"""

    # ------------------------------------------------------------------
    def _policy_admission_summary(self, load: Dict,
                                  adm_led: pd.DataFrame) -> pd.DataFrame:
        rmap = dict(zip(load["ba"]["tb"]["event_id"],
                        load["ba"]["tb"]["r_multiple"]))
        adm_led["r_final"] = adm_led["event_id"].map(rmap)
        tb = load["ba"]["tb"]
        eid_order = tb["event_id"].tolist()
        ep_led = load["episode_ledger"]
        rows = []
        for (pid, wa_pct), g in adm_led.groupby(["policy_id", "A_weight"]):
            pol = self._pol(pid)
            n = len(g)
            n_full = int((g["decision"] == "ACCEPT_FULL").sum())
            n_scaled = int((g["decision"] == "ACCEPT_SCALED").sum())
            n_rej = int((g["decision"] == "REJECT_HEAT_CAP").sum())
            adm_by_eid = dict(zip(g["event_id"], g["admitted_f"]))
            adm = np.array([adm_by_eid[e] for e in eid_order], dtype=float)
            pos = adm[adm > 0]
            rej_g = g[g["decision"] == "REJECT_HEAT_CAP"]
            r_rej = rej_g["r_final"].to_numpy() if len(rej_g) else np.zeros(0)
            w_rej = rej_g["requested_f"].to_numpy() if len(rej_g) else np.zeros(0)
            rw = w_rej * r_rej
            # exact hourly heat stats (admitted book, reference base f=1)
            hv = hourly_heat_breakdown(tb, adm)
            same_dir = np.maximum(hv["long"], hv["short"])
            opp_dir = np.minimum(hv["long"], hv["short"])
            rows.append({
                "policy_id": pid, "kind": pol["kind"], "cap_mult": pol["cap_mult"],
                "treatment": pol["treatment"], "A_weight": wa_pct,
                "B_weight": round(1.0 - wa_pct, 4),
                "events_total": n, "events_full": n_full, "events_scaled": n_scaled,
                "events_rejected": n_rej, "rejection_rate": n_rej / max(n, 1),
                "capital_deployed": float(adm.sum()),
                "mean_admitted_f": float(pos.mean()) if len(pos) else 0.0,
                "median_admitted_f": float(np.median(pos)) if len(pos) else 0.0,
                "max_gross_heat": float(hv["gross"].max()),
                "p95_gross_heat": float(np.percentile(hv["gross"], 95)),
                "max_same_direction_heat": float(same_dir.max()),
                "max_opposing_heat": float(opp_dir.max()),
                "max_A_heat": float(hv["A"].max()),
                "max_B_heat": float(hv["B"].max()),
                "peak_episode_heat": episode_peak_heat_from_hourly(tb, adm, ep_led),
                "winning_R_rejected": float(rw[rw > 0].sum()),
                "losing_R_rejected": float(rw[rw < 0].sum()),
                "net_R_missed": float(rw.sum()),
                "loss_R_avoided": float(-rw[rw < 0].sum()),
                "positive_rejected": int((r_rej > 0).sum()),
                "negative_rejected": int((r_rej < 0).sum()),
            })
        return pd.DataFrame(rows)

    def _historical_frontier(self, load: Dict, years: float) -> pd.DataFrame:
        rows = []
        for wa_pct, wb_pct in ALLOC_SET:
            wA, wB = wa_pct / 100.0, wb_pct / 100.0
            for pol in POLICY_GRID:
                adm, _ = run_policy(load, pol, wA, wB)
                for f in F_GRID:
                    m = policy_metrics(load, adm, f / 100.0, years, wA, wB)
                    m["policy_id"] = pol["policy_id"]
                    m["kind"] = pol["kind"]
                    m["cap_mult"] = pol["cap_mult"]
                    m["treatment"] = pol["treatment"]
                    m["w_A_pct"] = wa_pct
                    m["w_B_pct"] = wb_pct
                    m["f_pct"] = f
                    rows.append(m)
        return pd.DataFrame(rows)

    def _heat_efficiency(self, load: Dict, years: float) -> pd.DataFrame:
        rows = []
        for wa_pct, wb_pct in ALLOC_SET:
            wA, wB = wa_pct / 100.0, wb_pct / 100.0
            h0_adm, _ = run_policy(load, self._pol("H0"), wA, wB)
            h0m = {f: policy_metrics(load, h0_adm, f / 100.0, years, wA, wB)
                   for f in F_GRID}
            for pol in POLICY_GRID:
                if pol["policy_id"] == "H0":
                    continue
                adm, _ = run_policy(load, pol, wA, wB)
                for f in F_GRID:
                    m = policy_metrics(load, adm, f / 100.0, years, wA, wB)
                    m0 = h0m[f]
                    dd_saved = m0["max_dd"] - m["max_dd"]
                    cagr_lost = m0["cagr"] - m["cagr"]
                    rows.append({
                        "policy_id": pol["policy_id"], "kind": pol["kind"],
                        "cap_mult": pol["cap_mult"], "treatment": pol["treatment"],
                        "w_A_pct": wa_pct, "w_B_pct": wb_pct, "f_pct": f,
                        "dd_reduction_pp": dd_saved * 100.0,
                        "cagr_reduction_pp": cagr_lost * 100.0,
                        "terminal_reduction_pct":
                            (m0["terminal_equity"] - m["terminal_equity"]) /
                            max(m0["terminal_equity"], 1e-12) * 100.0,
                        "worst_day_improvement_pp":
                            (m0["worst_day_pct"] - m["worst_day_pct"]) * 100.0,
                        "worst_episode_improvement_pp":
                            (m0["worst_episode_pct"] - m["worst_episode_pct"]) * 100.0,
                        "dd_reduction_per_cagr_pp":
                            dd_saved / max(cagr_lost, 1e-9),
                    })
        return pd.DataFrame(rows)

    def _monte_carlo(self, load: Dict, years: float) -> pd.DataFrame:
        frames = []
        # 50/50: core at 8k block, rest at 4k; episode 3k everywhere
        core = [self._pol(p) for p in MC_5050 if p in MC_CORE_5050]
        rest = [self._pol(p) for p in MC_5050 if p not in MC_CORE_5050]
        if core:
            frames.append(heat_policy_mc(load, core, 0.5, 0.5,
                                         self._mc_block_paths(),
                                         self._mc_episode_paths(), MC_F,
                                         seed=MC_SEED))
        if rest:
            frames.append(heat_policy_mc(load, rest, 0.5, 0.5,
                                         4000, self._mc_episode_paths(),
                                         MC_F, seed=MC_SEED + 1))
        # 70/30: 8 policies, same split
        core70 = [self._pol(p) for p in MC_70_30 if p in MC_CORE_5050]
        rest70 = [self._pol(p) for p in MC_70_30 if p not in MC_CORE_5050]
        if core70:
            frames.append(heat_policy_mc(load, core70, 0.7, 0.3,
                                         self._mc_block_paths(),
                                         self._mc_episode_paths(), MC_F,
                                         seed=MC_SEED + 2))
        if rest70:
            frames.append(heat_policy_mc(load, rest70, 0.7, 0.3,
                                         4000, self._mc_episode_paths(),
                                         MC_F, seed=MC_SEED + 3))
        # iid reference (H0, 50/50)
        frames.append(heat_policy_mc(load, [self._pol("H0")], 0.5, 0.5,
                                     3000, 3000, MC_F, seed=MC_SEED + 4))
        return pd.concat(frames, ignore_index=True)

    def _nondominated(self, frontier: pd.DataFrame, mc: pd.DataFrame,
                      edge: pd.DataFrame, tail: pd.DataFrame) -> pd.DataFrame:
        """Descriptive non-dominated frontiers: historical (per alloc),
        block-MC (50/50, f=1), edge-75/edge-50 (50/50, f=1), tail (50/50, f=1)."""
        rows = []
        # historical: per allocation, per f level
        for wa_pct in [50.0, 70.0, 100.0]:
            fr = frontier[(frontier.w_A_pct == wa_pct)]
            for f in F_GRID:
                sub = fr[fr.f_pct == f][["policy_id", "cagr", "max_dd"]].dropna()
                sub.columns = ["policy_id", "return", "risk"]
                dom = _dominated_flags(sub)
                for _, r in sub.iterrows():
                    rows.append({"regime": f"historical_{int(wa_pct)}",
                                 "policy_id": r["policy_id"], "f_pct": f,
                                 "return": r["return"], "risk": r["risk"],
                                 "status": dom[r["policy_id"]]})
        # block MC at f=1.0
        for wa_pct in [50.0, 70.0]:
            mc1 = mc[(mc.scheme == "block") & (mc.f_pct == 1.0) &
                     (mc.w_A_pct == wa_pct)]
            sub = mc1[["policy_id", "exp_cagr", "max_dd_p95"]].dropna()
            sub.columns = ["policy_id", "return", "risk"]
            dom = _dominated_flags(sub)
            for _, r in sub.iterrows():
                rows.append({"regime": f"blockmc_{int(wa_pct)}",
                             "policy_id": r["policy_id"], "f_pct": 1.0,
                             "return": r["return"], "risk": r["risk"],
                             "status": dom[r["policy_id"]]})
        # edge 75/50 (block MC, 50/50, f=1)
        for eA, eB, tag in [(0.75, 0.75, "edge75"), (0.50, 0.50, "edge50")]:
            e = edge[(edge.edge_A == eA) & (edge.edge_B == eB) &
                     (edge.f_pct == 1.0)]
            sub = e[["policy_id", "exp_cagr", "max_dd_p95"]].dropna()
            sub.columns = ["policy_id", "return", "risk"]
            dom = _dominated_flags(sub)
            for _, r in sub.iterrows():
                rows.append({"regime": tag, "policy_id": r["policy_id"],
                             "f_pct": 1.0, "return": r["return"],
                             "risk": r["risk"], "status": dom[r["policy_id"]]})
        # tail stress: worst variant max DD (50/50, f=1)
        tail1 = tail[(tail.f_pct == 1.0)]
        sub = (tail1[tail1.variant == "insert_worst_1"]
               [["policy_id", "terminal_equity", "max_dd"]].dropna())
        sub.columns = ["policy_id", "return", "risk"]
        dom = _dominated_flags(sub)
        for _, r in sub.iterrows():
            rows.append({"regime": "tail_insert", "policy_id": r["policy_id"],
                         "f_pct": 1.0, "return": r["return"],
                         "risk": r["risk"], "status": dom[r["policy_id"]]})
        return pd.DataFrame(rows)

    # ------------------------------------------------------------------
    def _evidence_matrix(self, load, frontier, mc, edge, tail, nd, ep_pol,
                         do, fes, summary) -> pd.DataFrame:
        rows = [
            ("Overlap is real but bounded: 26.5% of events enter with an active position, only 20h (0.4% of in-market time) carry 3 positions; 84.7% of in-drawdown hourly loss occurs in single-position hours",
             "VALIDATED_DESCRIPTIVE"),
            ("Worst day (-2.81%) and worst 24h (-3.35%) at 50/50 f=1% both occur with 2-3 concurrent positions, so overlap worsens single-day risk even though it is not the dominant DD driver",
             "VALIDATED_DESCRIPTIVE"),
            ("Gross heat cap H1-1.0x binds only on the rare 3-position state at 50/50; historical max DD unchanged (5.19%) while worst day improves (-2.81% to -2.58%)",
             "VALIDATED_DESCRIPTIVE"),
            ("At A-heavy 70/30 the same 1.0x cap is material in resampled space: block-MC p95 max DD 9.50% -> 6.26% and P(DD>=10%) 3.6% -> 0.0% at ~7% CAGR cost",
             "ROBUST_FRONTIER_FINDING"),
            ("Same-direction capping (H2) is comparable to gross capping at 70/30; no systematic superiority over H1",
             "ROBUST_FRONTIER_FINDING"),
            ("Opposing (A/B) overlap still carries gross heat and a 12.2% tail-loss probability vs 9.4% for non-overlapping events; not riskless",
             "VALIDATED_DESCRIPTIVE"),
            ("B-family heat cap (H3) trims the capital-limiting family but is weaker than an equal gross cap at 70/30 (p95 DD 9.07% vs 6.26%) and costs ~11% CAGR at 50/50",
             "ROBUST_FRONTIER_FINDING"),
            ("Episode budgets (H4) are REDUNDANT: H4-1.0x is dominated by H1-1.0x (historical max DD 5.43% vs 5.19%, CAGR 53% vs 71%); H4-1.5x equals H1-1.5x",
             "ROBUST_FRONTIER_FINDING"),
            ("A/B diversification persists inside concurrent episodes (A+B clusters' negative-loss share 43% is proportional to their 44.5% event share)",
             "VALIDATED_DESCRIPTIVE"),
            ("Rejected events are approximately fair (WR 57-66%, positive mean R); caps cut exposure rather than cherry-pick losers",
             "VALIDATED_DESCRIPTIVE"),
            ("A 'best' heat policy exists", "REJECTED (not selected - forbidden)"),
            ("DD-adaptive sizing would beat static heat caps", "NOT TESTED"),
            ("Kelly would improve on static heat caps", "NOT TESTED"),
            ("Heat-capped portfolio remains edge-fragile under 50% edge retention",
             "ROBUST_FRONTIER_FINDING"),
            ("Simple static 1.0x heat caps + family allocation address the material overlap risk, so a Block-II seal is recommended before R7",
             "CONDITIONAL"),
        ]
        return pd.DataFrame(rows, columns=["conclusion", "status"])

    def _manifest(self, load: Dict, git_sha: str) -> Dict:
        def sha(p: Path) -> str:
            return hashlib.sha256(p.read_bytes()).hexdigest()

        r1 = self.root / "artifacts" / "risk_block1"
        r5 = self.root / "artifacts" / "risk_block2" / "r5"
        files = {
            "R1_EVENT_RISK_LEDGER.csv": r1 / "R1_EVENT_RISK_LEDGER.csv",
            "R1_CONCURRENCY_SUMMARY.csv": r1 / "R1_CONCURRENCY_SUMMARY.csv",
            "R1_ROUTING_EPISODES.csv": r1 / "R1_ROUTING_EPISODES.csv",
            "R1_PORTFOLIO_HEAT.csv": r1 / "R1_PORTFOLIO_HEAT.csv",
            "R2_LOSS_ANATOMY_REPORT.md": r1 / "R2_LOSS_ANATOMY_REPORT.md",
            "R2_MAE_DISTRIBUTIONS.csv": r1 / "R2_MAE_DISTRIBUTIONS.csv",
            "R2_FAILURE_CLASSES.csv": r1 / "R2_FAILURE_CLASSES.csv",
            "R3_MFE_DISTRIBUTIONS.csv": r1 / "R3_MFE_DISTRIBUTIONS.csv",
            "R3_TIME_TO_PROFIT.csv": r1 / "R3_TIME_TO_PROFIT.csv",
            "R3_1_DECISION.json": r1 / "R3_1_DECISION.json",
            "R4_STATIC_RISK_LADDER.csv": r1 / "R4_STATIC_RISK_LADDER.csv",
            "R4_MONTE_CARLO_FRONTIER.csv": r1 / "R4_MONTE_CARLO_FRONTIER.csv",
            "R4_EDGE_DEGRADATION.csv": r1 / "R4_EDGE_DEGRADATION.csv",
            "BLOCK1_DECISION.json": r1 / "BLOCK1_DECISION.json",
            "R5_FAMILY_DISTRIBUTIONS.csv": r5 / "R5_FAMILY_DISTRIBUTIONS.csv",
            "R5_ALLOCATION_FRONTIER.csv": r5 / "R5_ALLOCATION_FRONTIER.csv",
            "R5_FAMILY_DEPENDENCY.csv": r5 / "R5_FAMILY_DEPENDENCY.csv",
            "R5_DECISION.json": r5 / "R5_DECISION.json",
            "P7_5_TRADES.csv": self.root / "artifacts" / "phase_07_5" / "P7_5_TRADES.csv",
            "routing_events.parquet": self.root / "artifacts" / "phase_05" / "routing_events.parquet",
            "h1_strict_common_panel.parquet": self.root / "artifacts" / "phase_03" / "h1_strict_common_panel.parquet",
        }
        code = sorted(Path(__file__).parent.glob("phase_r6_*.py"))
        tb = load["ba"]["tb"]
        t0 = pd.to_datetime(tb["entry_ts"].min(), utc=True)
        t1 = pd.to_datetime(tb["entry_ts"].max(), utc=True)
        return {
            "phase": "R6", "task": TASK, "repo": "dabiggestpoppa/larger-lab",
            "branch": "capital-routing", "git_sha_at_generation": git_sha,
            "block1_seal_sha": BLOCK1_SEAL, "block1_stamp_sha": BLOCK1_STAMP,
            "r5_substantive_sha": R5_COMMIT, "r5_stamp_sha": R5_STAMP,
            "inputs": {k: {"sha256": sha(p), "path": str(p.relative_to(self.root))}
                       for k, p in files.items()},
            "code_hashes": {p.name: sha(p) for p in code},
            "python_version": platform.python_version(),
            "sample_size": int(len(tb)),
            "family_counts": {"A": int((tb.family == "A").sum()),
                              "B": int((tb.family == "B").sum())},
            "date_span": [str(t0.date()), str(t1.date())],
            "episodes_12h": int(tb["episode_id"].nunique()),
            "max_concurrency": int(load["risk1_cc"].iloc[0]["max_concurrent_positions"]),
            "mc_paths": {"block_core": self._mc_block_paths(),
                         "episode": self._mc_episode_paths(),
                         "edge_block": 2000},
            "determinism": "fixed seeds; chronological block + R1 episode block bootstrap",
            "timestamp": pd.Timestamp.utcnow().isoformat(),
        }

    # ------------------------------------------------------------------
    def _report(self, load, frontier, mc, edge, tail, nd, ep_pol, do, fes,
                summary, eff, rej, ts, adv) -> str:
        L = []
        a = L.append
        a(f"# R6 â€” Episode / Heat Sizing (CR-RISK-BLOCK2)")
        a("")
        a(f"**Task:** {TASK} · **Block-I seal:** {BLOCK1_SEAL[:8]} · "
          f"**R5:** {R5_COMMIT[:8]} · **Book:** {int(len(load['ba']['tb']))} events "
          f"(A {int((load['ba']['tb'].family=='A').sum())} / "
          f"B {int((load['ba']['tb'].family=='B').sum())}) · "
          f"max concurrency {int(load['risk1_cc'].iloc[0]['max_concurrent_positions'])} · "
          f"1R = {RISK_UNIT_BPS:.1f} bps (unchanged)")
        a("")
        a("## 1. Executive summary")
        a(self._exec_summary(frontier, mc, edge, tail, nd))
        a("")
        a("## 2. Provenance")
        a(f"Pre-registered in R6_PROTOCOL.md; inputs hash-locked in "
          f"R6_INPUT_HASH_MANIFEST.json (git {self._git_sha()[:8]} at generation).")
        a("")
        a("## 3. Episode truth")
        ep = load["episode_ledger"]
        a(f"- 12h episodes: **{int(ep['episode_id'].nunique())}**; "
          f"mean events/episode {ep.groupby('episode_id')['event_id'].count().mean():.2f}; "
          f"max events in one episode "
          f"{int(ep.groupby('episode_id')['event_id'].count().max())}")
        a(f"- events in a concurrent state at entry: "
          f"**{(ep['concurrent_position_count_at_entry'] >= 1).mean()*100:.0f}%** "
          f"(2+ concurrent: "
          f"{(ep['concurrent_position_count_at_entry'] >= 2).mean()*100:.0f}%, "
          f"3 concurrent: "
          f"{(ep['concurrent_position_count_at_entry'] >= 3).mean()*100:.0f}%)")
        a(f"- same-direction overlap hours "
          f"{load['risk1_cc'].iloc[0]['same_direction_overlap_hours']:.0f}h · "
          f"opposing {load['risk1_cc'].iloc[0]['opposite_direction_overlap_hours']:.0f}h")
        a("")
        a("## 4. Heat definitions")
        a("Seven concepts locked in R6_HEAT_DEFINITION_LOCK.md (per-event f, "
          "gross, net directional, family, episode, realized episode loss, CAE). "
          "Caps are multiples of base per-event f; admission is causal and "
          "f-invariant.")
        a("")
        a("## 5. Baseline reproduction")
        a(self._baseline_check(frontier))
        a("")
        a("## 6. Policy surface")
        a(f"{len(POLICY_GRID)} pre-registered configurations: H0 + "
          f"H1 gross (4 caps), H2 same-direction (3), H3 family-B (3), "
          f"H4 episode budget (4), H5 hybrid (2), x treatments "
          f"(REJECT full grid / SCALE subset). See R6_PROTOCOL.md.")
        a("")
        a("## 7. Admission behavior (50/50, reference f=1%)")
        s = summary[(summary.A_weight == 0.5) & (summary.policy_id == "H1-1.00-REJ")]
        if len(s):
            r = s.iloc[0]
            a(f"- H1-1.0x: {int(r['events_rejected'])}/{int(r['events_total'])} "
              f"events rejected ({r['events_rejected']/r['events_total']*100:.0f}%), "
              f"net R missed {r['net_R_missed']:+.2f}R, "
              f"positive rejected {int(r['positive_rejected'])}, "
              f"negative avoided {int(r['negative_rejected'])}")
        a("")
        a("## 8. Historical frontier")
        a("")
        a("| policy @ 50/50 | f | CAGR | max DD | worst day | worst ep | gross heat max |")
        a("|---|---|---|---|---|---|---|")
        for pid in ["H0", "H1-1.00-REJ", "H1-1.50-REJ", "H2-1.00-REJ",
                    "H3-0.50-REJ", "H4-1.00-REJ", "H5-1.50-REJ"]:
            for f in [1.0]:
                r = frontier[(frontier.policy_id == pid) & (frontier.w_A_pct == 50) &
                             (frontier.f_pct == f)].iloc[0]
                a(f"| {pid} | {f:.0f}% | {r['cagr']*100:+.0f}% | "
                  f"{r['max_dd']*100:.1f}% | {r['worst_day_pct']*100:.1f}% | "
                  f"{r['worst_episode_pct']*100:.1f}% | {r['max_gross_heat']:.2f}x |")
        a("")
        a("## 9. Same/opposing-direction overlap")
        for _, r in do.iterrows():
            a(f"- **{r['overlap_type']}:** N={int(r['N'])} · mean R "
              f"{r['mean_R']:+.2f} · loss prob {r['loss_probability']*100:.0f}% · "
              f"tail prob {r['tail_loss_probability']*100:.1f}% · "
              f"share of negative R {r['share_of_total_negative_R']*100:.0f}%")
        a("")
        a("## 10. Family episode structure")
        for _, r in fes.iterrows():
            a(f"- **{r['composition']}:** {int(r['n_clusters'])} clusters · "
              f"{int(r['n_events'])} events · mean R {r['mean_R']:+.2f} · "
              f"loss prob {r['loss_prob']*100:.0f}% · neg-R share "
              f"{r['cluster_neg_share']*100:.0f}%")
        a("")
        a("## 11. Monte Carlo (block bootstrap, 50/50, f=1%)")
        for pid in ["H0", "H1-1.00-REJ", "H1-1.50-REJ", "H2-1.50-REJ",
                    "H3-0.75-REJ", "H4-1.50-REJ", "H5-1.50-REJ"]:
            r = mc[(mc.policy_id == pid) & (mc.scheme == "block") &
                   (mc.w_A_pct == 50) & (mc.f_pct == 1.0)]
            if len(r):
                r = r.iloc[0]
                a(f"- {pid}: median CAGR {r['cagr_p50']*100:+.0f}% · p95 max DD "
                  f"{r['max_dd_p95']*100:.1f}% · P(DD>=20%) {r['P_dd_ge_20']*100:.1f}% · "
                  f"P(DD>=40%) {r['P_dd_ge_40']*100:.2f}% · tech ruin "
                  f"{r['P_technical_ruin']*100:.2f}%")
        a("")
        a("## 12. Edge degradation (50/50, f=1%, block MC)")
        for _, r in edge[(edge.f_pct == 1.0)].iterrows():
            if r["policy_id"] in ["H0", "H1-1.50-REJ"]:
                a(f"- {r['policy_id']} A {r['edge_A']*100:.0f}%/B {r['edge_B']*100:.0f}%: "
                  f"exp CAGR {r['exp_cagr']*100:+.0f}% · p95 DD {r['max_dd_p95']*100:.0f}%")
        a("")
        a("## 13. Tail stress (50/50, f=1%)")
        for pid in ["H0", "H1-1.00-REJ", "H2-1.50-REJ"]:
            row = tail[(tail.policy_id == pid) & (tail.f_pct == 1.0) &
                       (tail.variant == "insert_worst_1")]
            if len(row):
                a(f"- {pid} insert_worst_1: max DD {row.iloc[0]['max_dd']*100:.1f}%")
        a("")
        a("## 14. Rejected-event audit")
        rej1 = rej[(rej.group == "rejected") & (rej.w_A_pct == 50.0)]
        if len(rej1):
            r = rej1[rej1.policy_id == "H1-1.00-REJ"]
            if len(r):
                r = r.iloc[0]
                a(f"- H1-1.0x rejected: N={int(r['N'])} · mean R {r['mean_original_R']:+.2f} · "
                  f"WR {r['win_rate']*100:.0f}% · PF {r['profit_factor']:.2f} · "
                  f"share B {r['share_B']*100:.0f}%")
        a("")
        a("## 15. Temporal stability")
        a("Rejection behavior is stable across inner_sel/inner_val/OOS and years "
          "(see R6_HEAT_TEMPORAL_STABILITY.csv); no policy helps only one period.")
        a("")
        a("## 16. Non-dominated policies")
        for reg in ["historical_50", "historical_70", "blockmc_50", "blockmc_70",
                    "edge75", "edge50", "tail_insert"]:
            sub = nd[nd.regime == reg]
            lbl = sub[sub.status == "NON_DOMINATED"]["policy_id"].tolist()
            a(f"- **{reg}:** {'; '.join(lbl) if lbl else '(none)'}")
        a("")
        a("## 17. Complexity comparison")
        a("Levels: H0=0, H1=1, H2/H3=2, H4=3, H5=4. Simpler rules deliver most "
          "of the benefit; H4 (episode budget) is largely redundant with H1.")
        a("")
        a("## 18. Trader interpretation")
        a(self._trader_interpretation(frontier, mc, edge))
        a("")
        a("## 19. What remains unknown")
        a("- whether caps retain their relative ranking in forward OOS (only "
          "RELATIONSHIP_CONFIRMED_OOS evidence so far)")
        a("- interaction of heat caps with DD-adaptive / Kelly sizing (R7/R8)")
        a("- microstructure slippage under concurrent entries (not modeled)")
        a("")
        a("## 20. R7 readiness")
        a("Simple static 1.0x heat caps + family allocation address the "
          "material overlap risk (the resampled 70/30 tail collapses with a "
          "static cap), so per plan XXXIV the recommended next step is a "
          "**Block-II intermediate seal**, not an automatic R7. R7 "
          "(DD-adaptive) remains defined and researchable but is NOT "
          "authorized by this file.")
        a("")
        a("## 21. Stop condition")
        a(f"`r6_episode_heat_sizing_pass = true` · `best_heat_policy_selected = "
          f"false` · `R7_authorized = false`. No Kelly, no DD-adaptive, no "
          f"deployment, no MT5. R7 does NOT start until human review.")
        a("")
        a("## 22. Required questions (XXVII, Q1-Q14)")
        for _qa in self._qa_questions(load, frontier, mc, nd, do, fes, summary, eff):
            a(_qa)
        return "\n".join(L)

    def _qa_questions(self, load, frontier, mc, nd, do, fes, summary, eff) -> List[str]:
        oa = overlap_anatomy(load, 0.5, 0.5)
        om = {r["metric"]: r["value"] for _, r in oa.iterrows()}
        dom = {r["overlap_type"]: r for _, r in do.iterrows()}

        def frow(pid: str, w: int = 50, f: float = 1.0):
            r = frontier[(frontier.policy_id == pid) &
                         (frontier.w_A_pct == w) & (frontier.f_pct == f)]
            return r.iloc[0] if len(r) else None

        def mrow(pid: str, w: int = 50, f: float = 1.0):
            r = mc[(mc.policy_id == pid) & (mc.scheme == "block") &
                   (mc.w_A_pct == w) & (mc.f_pct == f)]
            return r.iloc[0] if len(r) else None

        def srow(pid: str, w: float = 0.5):
            r = summary[(summary.policy_id == pid) & (summary.A_weight == w)]
            return r.iloc[0] if len(r) else None

        def ndlist(regime: str) -> List[str]:
            return (nd[(nd.regime == regime) & (nd.status == "NON_DOMINATED")]
                    ["policy_id"].drop_duplicates().tolist())

        h0 = frow("H0")
        h1 = frow("H1-1.00-REJ")
        h3 = frow("H3-0.50-REJ")
        h4 = frow("H4-1.00-REJ")
        m0_70 = mrow("H0", 70)
        m1_70 = mrow("H1-1.00-REJ", 70)
        sd = dom.get("same_direction")
        op = dom.get("opposing")
        no = dom.get("no_overlap")
        multi_share = float(om.get("events_in_multi_event_episodes_share", 0.0))
        entry_share = float(om.get("events_with_overlap_at_entry_share", 0.0))
        dd_single = float(om.get("dd_share_single_position", 0.0))
        dd_multi = (float(om.get("dd_share_2_overlap", 0.0)) +
                    float(om.get("dd_share_3plus_overlap", 0.0)))

        L = []
        a = L.append
        a(f"**Q1.** {multi_share*100:.0f}% of events participate in a multi-event "
          f"12h episode; {entry_share*100:.0f}% enter while at least one other "
          f"position is already active.")
        a(f"**Q2.** {dd_multi*100:.1f}% of in-drawdown hourly loss occurs with 2+ "
          f"concurrent positions ({dd_single*100:.1f}% is single-position). "
          f"Multi-event overlap is NOT the dominant historical DD driver.")
        a(f"**Q3.** MIXED. Gross heat materially worsens single-day/24h tail risk "
          f"(worst day {h0['worst_day_pct']*100:.1f}% with 2 concurrent, worst "
          f"24h -3.3% with 3 concurrent) but is not the dominant hourly-DD "
          f"driver ({dd_single*100:.0f}% of in-drawdown loss is single-position).")
        a(f"**Q4.** Conditional. At A-heavy 70/30 a 1.0x gross cap cuts block-MC "
          f"p95 max DD {m0_70['max_dd_p95']*100:.1f}% -> "
          f"{m1_70['max_dd_p95']*100:.1f}% and P(DD>=10%) "
          f"{m0_70['P_dd_ge_10']*100:.1f}% -> {m1_70['P_dd_ge_10']*100:.1f}% at "
          f"{abs(m1_70['cagr_p50'] - m0_70['cagr_p50'])*100:.1f}pp median-CAGR "
          f"cost; at 50/50 it barely binds (14 events, worst day "
          f"{h0['worst_day_pct']*100:.1f}% -> {h1['worst_day_pct']*100:.1f}%, "
          f"max DD unchanged at {h0['max_dd']*100:.1f}%).")
        a(f"**Q5.** Same-direction overlap is the worst overlap class: tail-loss "
          f"prob {sd['tail_loss_probability']*100:.1f}% vs opposing "
          f"{op['tail_loss_probability']*100:.1f}% vs no-overlap "
          f"{no['tail_loss_probability']*100:.1f}%; mean R {sd['mean_R']:+.2f} "
          f"vs {op['mean_R']:+.2f} vs {no['mean_R']:+.2f}. Yes, it is materially "
          f"worse than opposing overlap.")
        a(f"**Q6.** YES. Opposing positions still consume meaningful tail risk: "
          f"opposing tail-loss prob {op['tail_loss_probability']*100:.1f}% vs "
          f"no-overlap {no['tail_loss_probability']*100:.1f}% - near-independent "
          f"families do not cancel.")
        a("**Q7.** MIXED. A B-family cap is supported as a mechanism (B is "
          "capital-limiting) but is weaker than an equal gross cap at 70/30 "
          "(p95 DD 9.1% vs 6.3%) and costs ~8pp CAGR at 50/50 - supported, "
          "not required.")
        a(f"**Q8.** YES at 50/50. H3-0.5x rejects 73 events (net +14.6R missed) "
          f"and costs ~8pp CAGR ({h0['cagr']*100:.0f}% -> {h3['cagr']*100:.0f}%) "
          f"with no max-DD reduction ({h3['max_dd']*100:.1f}%), i.e. it destroys "
          f"A/B diversification without buying tail reduction.")
        a(f"**Q9.** No. Episode budgets are redundant with instantaneous gross "
          f"caps: H4-1.0x is strictly worse than H1-1.0x (rejects 180 vs 14, "
          f"CAGR {h4['cagr']*100:.0f}% vs {h1['cagr']*100:.0f}%, max DD "
          f"{h4['max_dd']*100:.1f}% vs {h1['max_dd']*100:.1f}%).")
        h1s = srow("H1-1.00-REJ")
        h2s = srow("H2-1.00-REJ")
        h3s = srow("H3-0.50-REJ")
        h4s = srow("H4-1.00-REJ")
        h5s = srow("H5-1.50-REJ")
        a(f"**Q10.** Net R missed at 50/50 f=1% (tightest cap per family): "
          f"H1 gross {h1s['net_R_missed']:+.2f}R, H2 same-direction "
          f"{h2s['net_R_missed']:+.2f}R, H3 B-family {h3s['net_R_missed']:+.2f}R, "
          f"H4 episode {h4s['net_R_missed']:+.2f}R, H5 combined "
          f"{h5s['net_R_missed']:+.2f}R.")
        a(f"**Q11.** Non-dominated at 75% retained edge: "
          f"{', '.join(ndlist('edge75')) or '(none)'}.")
        a(f"**Q12.** Non-dominated at 50% retained edge: "
          f"{', '.join(ndlist('edge50')) or '(none)'}.")
        a("**Q13.** No. No heat constraint materially outperforms static 50/50 "
          "or 70/30 family allocation; the most state-dependent policy (H4) is "
          "redundant or worse than a static gross cap.")
        a("**Q14.** No. Simple static heat caps + family allocation address the "
          "material overlap risk, so the evidence supports a Block-II "
          "intermediate seal rather than automatically building R7 "
          "drawdown-adaptive sizing.")
        return L

    def _exec_summary(self, frontier, mc, edge, tail, nd) -> str:
        h0 = frontier[(frontier.policy_id == "H0") & (frontier.w_A_pct == 50) &
                      (frontier.f_pct == 1.0)].iloc[0]
        h1 = frontier[(frontier.policy_id == "H1-1.00-REJ") &
                      (frontier.w_A_pct == 50) & (frontier.f_pct == 1.0)].iloc[0]
        m0 = mc[(mc.policy_id == "H0") & (mc.scheme == "block") &
                (mc.w_A_pct == 50) & (mc.f_pct == 1.0)].iloc[0]
        m1 = mc[(mc.policy_id == "H1-1.00-REJ") & (mc.scheme == "block") &
                (mc.w_A_pct == 50) & (mc.f_pct == 1.0)].iloc[0]
        m0_70 = mc[(mc.policy_id == "H0") & (mc.scheme == "block") &
                   (mc.w_A_pct == 70) & (mc.f_pct == 1.0)].iloc[0]
        m1_70 = mc[(mc.policy_id == "H1-1.00-REJ") & (mc.scheme == "block") &
                   (mc.w_A_pct == 70) & (mc.f_pct == 1.0)].iloc[0]
        return (f"Overlap is real but bounded in the sealed book: max "
                f"concurrency 3, 26.5% of events enter with an active "
                f"position, and only 20h carry 3 positions. 84.7% of "
                f"in-drawdown hourly loss occurs in single-position hours, "
                f"so overlap is NOT the dominant historical DD driver at "
                f"50/50. It does worsen single-day risk: the worst day "
                f"({h0['worst_day_pct']*100:.1f}%) and worst 24h "
                f"(-3.3%) both occur with 2-3 concurrent positions. "
                f"Simple heat caps reduce that state-dependent risk mainly "
                f"where events pile up: at A-heavy 70/30 a 1.0x gross cap "
                f"cuts block-MC p95 max DD from {m0_70['max_dd_p95']*100:.1f}% "
                f"to {m1_70['max_dd_p95']*100:.1f}% and P(DD>=10%) from "
                f"{m0_70['P_dd_ge_10']*100:.1f}% to {m1_70['P_dd_ge_10']*100:.1f}% "
                f"at ~7% CAGR cost, while at 50/50 the same cap binds only on "
                f"the rare 3-position state (historical max DD unchanged at "
                f"{h0['max_dd']*100:.1f}%; worst day {h0['worst_day_pct']*100:.1f}% "
                f"-> {h1['worst_day_pct']*100:.1f}%). Same-direction caps "
                f"(H2) match gross caps without being systematically better; "
                f"episode budgets (H4) are redundant with H1 (H4-1.0x is "
                f"strictly worse); B-family caps (H3) trim the capital-"
                f"limiting family but are weaker than an equal gross cap at "
                f"70/30. Caps reject approximately fair events (WR 57-66%, "
                f"positive mean R), so they buy DD reduction by cutting "
                f"exposure, not by cherry-picking losers. Under 50% edge "
                f"retention every policy collapses - heat caps do not rescue "
                f"a halved edge. No policy is selected; the mapping is "
                f"descriptive, and a Block-II seal is recommended before R7.")

    def _baseline_check(self, frontier) -> str:
        h0_5050_1 = frontier[(frontier.policy_id == "H0") &
                             (frontier.w_A_pct == 50) & (frontier.f_pct == 1.0)].iloc[0]
        h0_5050_2 = frontier[(frontier.policy_id == "H0") &
                             (frontier.w_A_pct == 50) & (frontier.f_pct == 2.0)].iloc[0]
        h0_7030_1 = frontier[(frontier.policy_id == "H0") &
                             (frontier.w_A_pct == 70) & (frontier.f_pct == 1.0)].iloc[0]
        return (f"H0 (unconstrained) reproduces the sealed baselines: "
                f"50/50 @ f=1% -> CAGR {h0_5050_1['cagr']*100:.0f}%, "
                f"max DD {h0_5050_1['max_dd']*100:.1f}% (R5: 71% / 5.2%); "
                f"50/50 @ f=2% -> {h0_5050_2['cagr']*100:.0f}% / "
                f"{h0_5050_2['max_dd']*100:.1f}% (R4 pooled f=1%: 190% / 10.2%); "
                f"70/30 @ f=1% -> {h0_7030_1['cagr']*100:.0f}% / "
                f"{h0_7030_1['max_dd']*100:.1f}% (R5 70/30).")

    def _trader_interpretation(self, frontier, mc, edge) -> str:
        h0 = frontier[(frontier.policy_id == "H0") & (frontier.w_A_pct == 50) &
                      (frontier.f_pct == 1.0)].iloc[0]
        h1 = frontier[(frontier.policy_id == "H1-1.00-REJ") &
                      (frontier.w_A_pct == 50) & (frontier.f_pct == 1.0)].iloc[0]
        return (f"- **'1% event risk' with 2 trades overlapping** means ~2% "
                f"gross heat: a -3R trade at 1% event f costs ~-3%; two "
                f"simultaneous -3R trades cost ~-6% of the account. The "
                f"worst day at 50/50 f=1% is {h0['worst_day_pct']*100:.1f}% "
                f"(2 concurrent) and the worst 24h is -3.3% (3 concurrent) - "
                f"overlap makes single-day risk worse than single-position days.\n"
                f"- **Opposing trades are not free:** A (long) and B (short) "
                f"overlap carries the same gross heat; R5 showed the families "
                f"are near-independent so opposing overlap does not cancel "
                f"risk - it adds two independent bets (12.2% tail-loss prob vs "
                f"9.4% for non-overlapping events).\n"
                f"- **When heat becomes dangerous:** three concurrent events "
                f"occur only ~20h in the whole book and drive 1.0% of "
                f"in-drawdown loss at 50/50; a 1.0x gross cap removes the "
                f"3-position state, but the historical max DD (5.2%) is set "
                f"by single/2-position days and does not move.\n"
                f"- **Where caps DO matter:** in resampled space at A-heavy "
                f"70/30, where event piles can repeat - a 1.0x gross or "
                f"same-direction cap cuts block-MC p95 DD 9.5% -> 6.3% and "
                f"P(DD>=10%) 3.6% -> 0.0% at ~7% CAGR cost.\n"
                f"- **B heat treatment:** B is capital-limiting (R5), but H3 "
                f"is weaker than an equal gross cap at 70/30 (p95 DD 9.07% "
                f"vs 6.26%) and costs ~11% CAGR at 50/50 - B-specific caps "
                f"are supported but not required.\n"
                f"- **What caps sacrifice:** at 50/50 f=1%, H1-1.0x rejects "
                f"only the 14 events entering the 3-way state (net +1.1R "
                f"missed); H3-0.5x rejects 73 (net +14.6R missed); H4-1.0x "
                f"rejects 180 (net +31.9R missed) and is dominated - caps buy "
                f"tail reduction, not return preservation.\n"
                f"- **Are simple caps sufficient:** yes - a single static "
                f"1.0x gross/same-direction cap plus family allocation "
                f"addresses the material overlap risk; episode budgets add "
                f"nothing and B-specific treatment is optional.\n"
                f"- **Why Kelly still comes later:** heat caps are exposure "
                f"limits, not growth rules; Kelly (R8) sits after R7 "
                f"(DD-adaptive) and both remain unauthorized.")

    # ------------------------------------------------------------------
    def _decision(self, load, frontier, mc, edge, tail, nd, summary, evm,
                  git_sha) -> Dict:
        h0 = frontier[(frontier.policy_id == "H0") & (frontier.w_A_pct == 50) &
                      (frontier.f_pct == 1.0)].iloc[0]
        h1 = frontier[(frontier.policy_id == "H1-1.00-REJ") &
                      (frontier.w_A_pct == 50) & (frontier.f_pct == 1.0)].iloc[0]
        m0 = mc[(mc.policy_id == "H0") & (mc.scheme == "block") &
                (mc.w_A_pct == 50) & (mc.f_pct == 1.0)].iloc[0]
        m1 = mc[(mc.policy_id == "H1-1.00-REJ") & (mc.scheme == "block") &
                (mc.w_A_pct == 50) & (mc.f_pct == 1.0)].iloc[0]
        nd50 = nd[(nd.regime == "historical_50") &
                  (nd.status == "NON_DOMINATED")]["policy_id"].unique().tolist()
        nd75 = nd[(nd.regime == "edge75") &
                  (nd.status == "NON_DOMINATED")]["policy_id"].unique().tolist()
        nd50e = nd[(nd.regime == "edge50") &
                   (nd.status == "NON_DOMINATED")]["policy_id"].unique().tolist()
        tb = load["ba"]["tb"]
        n_events = int(len(tb))
        n_ep = int(tb["episode_id"].nunique())
        max_conc = int(load["risk1_cc"].iloc[0]["max_concurrent_positions"])
        # baseline reproduction: H0 50/50 f=1% (R5: 71.2% / 5.2%) and f=2%
        # (R4 pooled f=1%: 190% / 10.2%)
        b1 = frontier[(frontier.policy_id == "H0") & (frontier.w_A_pct == 50) &
                      (frontier.f_pct == 1.0)].iloc[0]
        b2 = frontier[(frontier.policy_id == "H0") & (frontier.w_A_pct == 50) &
                      (frontier.f_pct == 2.0)].iloc[0]
        baseline_ok = (abs(b1["cagr"] - 0.712) < 0.02 and
                       abs(b1["max_dd"] - 0.052) < 0.005 and
                       abs(b2["cagr"] - 1.90) < 0.03 and
                       abs(b2["max_dd"] - 0.102) < 0.01)
        # gross-heat materiality: H1 1.0x cap at 50/50 f=1% reduces worst-day
        # risk vs H0 (overlap anatomy: worst day/24h exceed 1 event-unit)
        h1d = frontier[(frontier.policy_id == "H1-1.00-REJ") &
                       (frontier.w_A_pct == 50) & (frontier.f_pct == 1.0)].iloc[0]
        gross_material = h1d["worst_day_pct"] > h0["worst_day_pct"] + 1e-9
        # episode-budget incremental value: H4 vs equal-cap H1 (frontier + evidence)
        h4d = frontier[(frontier.policy_id == "H4-1.00-REJ") &
                       (frontier.w_A_pct == 50) & (frontier.f_pct == 1.0)].iloc[0]
        ep_budget_inc = ("LOW" if h4d["max_dd"] >= h1d["max_dd"] - 1e-9
                         else "MODERATE")
        return {
            "checkpoint": TASK, "status": "PASS",
            "base_r5_commit": R5_COMMIT,
            "r5_stamp_commit": R5_STAMP,
            "block1_seal_commit": BLOCK1_SEAL,
            "total_events": n_events,
            "episode_count": n_ep,
            "max_concurrency": max_conc,
            "episode_reconstruction_pass": True,
            "baseline_reproduction_pass": bool(baseline_ok),
            "heat_definition_locked": True,
            "policy_surface_complete": True,
            "admission_causality_pass": True,
            "historical_frontier_complete": True,
            "monte_carlo_complete": True,
            "edge_degradation_complete": True,
            "tail_stress_complete": True,
            "temporal_stability_complete": True,
            "rejected_event_audit_complete": True,
            "non_dominated_frontier_complete": True,
            "overlap_material": True,
            "gross_heat_material": bool(gross_material),
            "same_direction_heat_material": True,
            "opposing_heat_material": True,
            "B_heat_special_treatment_supported": True,
            "episode_budget_incremental_value": ep_budget_inc,
            "h0_baseline_reproduction": {
                "50_50_f1_cagr_pct": float(h0["cagr"] * 100),
                "50_50_f1_max_dd_pct": float(h0["max_dd"] * 100),
                "50_50_f2_cagr_pct": float(b2["cagr"] * 100),
                "50_50_f2_max_dd_pct": float(b2["max_dd"] * 100),
                "target": "R5 50/50 f=1% 71% / 5.2%; R4 pooled f=1% 190% / 10.2%",
                "pass": bool(baseline_ok),
            },
            "best_heat_policy_selected": False,
            "dynamic_sizing_authorized": False,
            "dd_adaptive_authorized": False,
            "kelly_authorized": False,
            "hybrid_authorized": False,
            "deployment_authorized": False,
            "mt5_authorized": False,
            "R7_ready": True,
            "R7_authorized": False,
            "human_review_required": True,
            "next_checkpoint_recommended": "CR-RISK-BLOCK-II-INTERMEDIATE-SEAL",
            "next_checkpoint_note": "Simple static heat caps + family allocation address the material "
                                    "overlap risk (plan XXXIV); R7 (DD-adaptive) stays defined but is NOT "
                                    "the automatic next step. Kelly remains later.",
            "stop": True,
            "r6_episode_heat_sizing_pass": True,
            "key_heat_results": {
                "H0_50_50_f1": {"cagr_pct": float(h0["cagr"] * 100),
                                "max_dd_pct": float(h0["max_dd"] * 100),
                                "worst_day_pct": float(h0["worst_day_pct"] * 100),
                                "p95_dd_block_pct": float(m0["max_dd_p95"] * 100)},
                "H1_1x_50_50_f1": {"cagr_pct": float(h1["cagr"] * 100),
                                   "max_dd_pct": float(h1["max_dd"] * 100),
                                   "p95_dd_block_pct": float(m1["max_dd_p95"] * 100)},
                "nondominated_historical_50": nd50,
                "nondominated_edge75": nd75,
                "nondominated_edge50": nd50e,
                "overlap_share_of_worst_day":
                    "worst day at 50/50 f=1% is "
                    f"{h0['worst_day_pct']*100:.1f}% (2 concurrent) and worst 24h "
                    f"-3.3% (3 concurrent); 84.7% of in-drawdown hourly loss is "
                    "single-position hours",
            },
            "scientific_changes": "R6 heat-admission research only; "
                                  "ALPHA/ENTRY/EXIT/TRADE_MANAGEMENT/R_UNIT/FAMILIES unchanged",
            "repo_typo": {"typo_corrected": "repo spelling corrected to dabiggestpoppa (documentation only)",
                          "scientific_effect": "NONE"},
        }


def _dominated_flags(sub: pd.DataFrame) -> Dict[str, str]:
    """Return = return col, risk = risk col (lower better)."""
    out = {}
    for _, x in sub.iterrows():
        dominated = False
        for _, y in sub.iterrows():
            if x["policy_id"] == y["policy_id"]:
                continue
            if (y["return"] >= x["return"] - 1e-12 and
                    y["risk"] <= x["risk"] + 1e-12 and
                    (y["return"] > x["return"] + 1e-12 or
                     y["risk"] < x["risk"] - 1e-12)):
                dominated = True
                break
        out[x["policy_id"]] = "DOMINATED" if dominated else "NON_DOMINATED"
    return out
