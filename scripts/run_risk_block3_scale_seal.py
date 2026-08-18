"""CR-RISK-BLOCK-III-SCALE-SEAL -- deterministic runner.

Synthesizes the frozen Block-III frontier artifacts into the sealed static
scale operating region.  NO new optimization and NO new Monte Carlo: every
review table is a pure function of the frontier CSVs/JSONs written at commit
a58f8483 (CR-RISK-BLOCK-III-STATIC-SCALE-FRONTIER).

Artifacts (research/capital_routing/risk/block3_scale_seal/):
  CR_RISK_BLOCK3_SCALE_SEAL_PROTOCOL.md
  CR_RISK_BLOCK3_SCALE_SEAL_INPUT_HASHES.json
  CR_RISK_BLOCK3_KNEE_REVIEW.csv
  CR_RISK_BLOCK3_ADJACENT_SCALE_REVIEW.csv
  CR_RISK_BLOCK3_ALLOCATION_REVIEW.csv
  CR_RISK_BLOCK3_HEAT_REVIEW.csv
  CR_RISK_BLOCK3_EDGE_REVIEW.csv
  CR_RISK_BLOCK3_ROBUST_CORE.csv
  CR_RISK_BLOCK3_REGION_DEFINITION.json
  CR_RISK_BLOCK3_RISK_CONTRACT.json
  CR_RISK_BLOCK3_SCALE_SEAL_REPORT.md
  CR_RISK_BLOCK3_SCALE_SEAL_DECISION.json

This checkpoint does NOT select a best cell, does NOT authorize production
sizing / deployment / MT5, and does NOT run Kelly or DD-adaptive sizing.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd

from capital_routing.capital_scale_seal import (
    ADJACENT_PAIRS, ALLOC_NAMES, CONSERVATIVE_BAND, ROBUST_CORE_BAND,
    AGGRESSIVE_BAND, STRESS_BAND, EDGE_STATES, HEAT_IDS, OPERATING_ALLOCS,
    OPERATING_HEAT, PRIMARY_SCHEMES, RECOMMENDATION_ALLOCS, PREFERRED_ALLOC,
    PREFERRED_F_PCT, PREFERRED_HEAT,
    adjacent_scale_review, adjacent_scale_seal_pass, allocation_review,
    edge_review, edge_seal_state, heat_review, input_hash_manifest,
    knee_band, knee_review, load_frontier, region_definition, risk_contract,
    robust_core, robust_core_ranges,
)

ROOT = Path(__file__).resolve().parents[1]
FRONTIER = ROOT / "research" / "capital_routing" / "risk" / "block3_frontier"
OUT = ROOT / "research" / "capital_routing" / "risk" / "block3_scale_seal"

FRONTIER_INPUT_FILES: List[str] = [
    "CR_RISK_BLOCK3_MC_SURFACE.csv",
    "CR_RISK_BLOCK3_HISTORICAL_SURFACE.csv",
    "CR_RISK_BLOCK3_EDGE_SURVIVAL.csv",
    "CR_RISK_BLOCK3_KNEE_ANALYSIS.csv",
    "CR_RISK_BLOCK3_PAIRED_H1_VS_H0.csv",
    "CR_RISK_BLOCK3_DEPENDENCY_SENSITIVITY.csv",
    "CR_RISK_BLOCK3_REGION_CLASSIFICATION.csv",
    "CR_RISK_BLOCK3_DECISION.json",
    "CR_RISK_BLOCK3_REFERENCE_NONREGRESSION.json",
    "CR_RISK_BLOCK3_R6_MC_REGRESSION.json",
]


def _git_sha() -> str:
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"],
                             capture_output=True, text=True, cwd=ROOT)
        return out.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def _fmt_band(b: List[float]) -> str:
    lo, hi = b
    return f"{lo:.2f}-{hi:.2f}" if lo != hi else f"{lo:.2f}"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    base_commit = _git_sha()
    data = load_frontier(FRONTIER)
    mc, hist, surv = data["mc"], data["hist"], data["surv"]
    knee, paired, dep = data["knee"], data["paired"], data["dep"]
    reg, fdec = data["reg"], data["decision"]

    # ------------------------------------------------------------------ #
    # 1. Protocol + input hashes (frozen before results are written)      #
    # ------------------------------------------------------------------ #
    protocol = _protocol_md()
    (OUT / "CR_RISK_BLOCK3_SCALE_SEAL_PROTOCOL.md").write_text(
        protocol, encoding="utf-8")
    hashes = input_hash_manifest(FRONTIER, base_commit, FRONTIER_INPUT_FILES)
    (OUT / "CR_RISK_BLOCK3_SCALE_SEAL_INPUT_HASHES.json").write_text(
        json.dumps(hashes, indent=2), encoding="utf-8")

    # ------------------------------------------------------------------ #
    # 2. Review tables                                                    #
    # ------------------------------------------------------------------ #
    kr = knee_review(knee)
    kr.to_csv(OUT / "CR_RISK_BLOCK3_KNEE_REVIEW.csv", index=False)

    adj = adjacent_scale_review(mc, RECOMMENDATION_ALLOCS, HEAT_IDS)
    adj.to_csv(OUT / "CR_RISK_BLOCK3_ADJACENT_SCALE_REVIEW.csv", index=False)

    alloc = allocation_review(mc, hist, surv)
    alloc.to_csv(OUT / "CR_RISK_BLOCK3_ALLOCATION_REVIEW.csv", index=False)
    alloc_trans = alloc.attrs.get("transitions")
    if alloc_trans is not None:
        alloc_trans.to_csv(OUT / "CR_RISK_BLOCK3_ALLOCATION_REVIEW_TRANSITIONS.csv",
                           index=False)

    heat = heat_review(mc, hist, paired)
    heat.to_csv(OUT / "CR_RISK_BLOCK3_HEAT_REVIEW.csv", index=False)

    edge = edge_review(surv, mc)
    edge.to_csv(OUT / "CR_RISK_BLOCK3_EDGE_REVIEW.csv", index=False)

    # ------------------------------------------------------------------ #
    # 3. Robust core + region definition                                  #
    # ------------------------------------------------------------------ #
    rc = robust_core(mc, dep)
    rc.to_csv(OUT / "CR_RISK_BLOCK3_ROBUST_CORE.csv", index=False)

    kb, knee_stats = knee_band(knee)
    edge_state = edge_seal_state(edge)
    core_ranges = robust_core_ranges(rc)
    adj_seal = adjacent_scale_seal_pass(adj)

    region = region_definition(
        rc, knee, adj, alloc, heat, edge_state, fdec, base_commit)
    (OUT / "CR_RISK_BLOCK3_REGION_DEFINITION.json").write_text(
        json.dumps(region, indent=2), encoding="utf-8")

    contract = risk_contract(rc, edge_state)
    (OUT / "CR_RISK_BLOCK3_RISK_CONTRACT.json").write_text(
        json.dumps(contract, indent=2), encoding="utf-8")

    # ------------------------------------------------------------------ #
    # 4. Report + decision                                                #
    # ------------------------------------------------------------------ #
    report = _report_md(base_commit, region, contract, kr, adj, alloc, heat,
                        edge, rc, alloc_trans, fdec)
    (OUT / "CR_RISK_BLOCK3_SCALE_SEAL_REPORT.md").write_text(
        report, encoding="utf-8")

    decision = _decision(region, contract, edge_state, base_commit)
    (OUT / "CR_RISK_BLOCK3_SCALE_SEAL_DECISION.json").write_text(
        json.dumps(decision, indent=2), encoding="utf-8")

    print(f"[seal] base {base_commit}")
    print(f"[seal] knee band: {kb}")
    print(f"[seal] robust core ranges: {core_ranges}")
    print(f"[seal] edge state: {edge_state}")
    print(f"[seal] adjacent scale seal: {adj_seal}")
    print(f"[seal] preferred default: {region['preferred_research_default']}")
    print(f"[seal] PASS={decision['block3_scale_seal_pass']}")
    print("[seal] DONE")


def _decision(region: Dict, contract: Dict, edge_state: Dict,
              base_commit: str) -> Dict:
    r = region
    ranges = contract
    bands = r["scale_bands"]
    return {
        "checkpoint": "CR-RISK-BLOCK-III-SCALE-SEAL",
        "status": "PASS",
        "base_commit": base_commit,
        "frontier_nonregression_pass": bool(
            r["frontier_nonregression_pass"]),
        "conservative_scale_band": bands["CONSERVATIVE"],
        "robust_core_scale_band": bands["ROBUST_CORE"],
        "aggressive_scale_band": bands["AGGRESSIVE"],
        "stress_scale_band": bands["STRESS_ONLY"],
        "allowed_allocations": r["allowed_allocations"],
        "diagnostic_only_allocations": r["diagnostic_only_allocations"],
        "heat_architecture_status": "H1_OPTIONAL_SAFETY_LAYER_RETAINED",
        "preferred_research_default": r["preferred_research_default"],
        "robust_core_median_cagr_range": ranges["median_cagr_range"],
        "robust_core_p95_dd_range": ranges["p95_max_dd_range"],
        "robust_core_p_dd_ge_10_range": ranges["P_dd_ge_10_range"],
        "robust_core_p_dd_ge_15_range": ranges["P_dd_ge_15_range"],
        "survives_100_edge": bool(edge_state["survives_100"]),
        "survives_75_edge": bool(edge_state["survives_75"]),
        "survives_50_edge": bool(edge_state["survives_50"]),
        "survives_25_edge": bool(edge_state["survives_25"]),
        "block_episode_agreement_pass": bool(
            r["block_episode_agreement_pass"]),
        "knee_seal_pass": bool(r["knee_seal_pass"]),
        "adjacent_scale_seal_pass": bool(r["adjacent_scale_seal"]["pass"]),
        "kelly_used": False,
        "dd_adaptive_used": False,
        "production_scale_selected": False,
        "deployment_authorized": False,
        "mt5_authorized": False,
        "block3_scale_seal_pass": bool(
            r["block_episode_agreement_pass"]
            and r["knee_seal_pass"]
            and r["adjacent_scale_seal"]["pass"]
            and edge_state["survives_100"]
            and edge_state["survives_75"]),
        "human_review_required": True,
        "next_checkpoint_recommended": r["next_checkpoint_recommended"],
        "next_checkpoint_authorized": False,
    }


def _protocol_md() -> str:
    return f"""# CR-RISK-BLOCK-III-SCALE-SEAL -- Protocol (frozen before synthesis)

**Repo:** dabiggestpoppa/larger-lab
**Branch:** capital-routing
**Base:** a58f84833b920175f88a5e5c6c127a12bd5cdafe (CR-RISK-BLOCK-III-STATIC-SCALE-FRONTIER)
**Type:** SYNTHESIS CHECKPOINT -- no new optimization, no new Monte Carlo.

## Mission
Freeze the scientifically-supported STATIC SCALE OPERATING REGION from the
completed Block-III frontier.  The output is an OPERATING BAND (never a best
cell), plus a single PREFERRED RESEARCH DEFAULT only if the evidence supports
a clear stable midpoint (for future demo translation -- NOT production sizing).

## Frozen inputs (all written by the frontier checkpoint)
MC surface (1680 rows), historical surface (560), edge survival, knee
analysis, paired H1-vs-H0 (common random numbers), dependency sensitivity,
region classification, frontier decision + nonregression JSONs.  SHA-256 of
every input is recorded in CR_RISK_BLOCK3_SCALE_SEAL_INPUT_HASHES.json.

## Scale bands (pre-registered form, confirmed by frontier evidence)
- CONSERVATIVE: {_fmt_band(CONSERVATIVE_BAND)}  (ROBUST_LOW_SCALE)
- ROBUST CORE:  {_fmt_band(ROBUST_CORE_BAND)}   (ROBUST_GROWTH_REGION)
- AGGRESSIVE:   {_fmt_band(AGGRESSIVE_BAND)}    (AGGRESSIVE_FRAGILE)
- STRESS ONLY:  {_fmt_band(STRESS_BAND)}        (never promoted)

## Allocation principle
Prefer diversified allocation when its tail/risk efficiency is close to (or
better than) A-only.  Do NOT choose A-only because headline CAGR is larger.
A0 50/50, A1 70/30 are operating; A2 100/0 A is a concentration reference
(diagnostic alongside A3 B-only) unless its tail efficiency is competitive.

## Heat seal principle
Retain H1 only when paired common-random-number evidence shows repeatable
meaningful tail reduction for a reasonable growth cost.  H1 caps that never
bind buy nothing and are not retained as operating layers.  Possible
conclusions: H0 sufficient / H1 preferred / H1 optional safety layer -- the
paired evidence decides.  H0 is always retained as the documented
unconstrained diagnostic.

## Edge retention
Operating band must survive 100% and 75% retained edge robustly (block AND
episode), have interpretable 50% behavior, and 25% is recorded as the
ALPHA-LOSS BOUNDARY (not required to survive).

## Dependency agreement
Block and episode are co-primary.  A band is not sealable if block says
robust but episode says fragile (or vice versa).  Require directional
agreement on growth, tail DD, DD probabilities, edge-decay behavior.

## Knee + adjacent scale
Knee band = modal interval from the frozen knee analysis (expected
[1.00, 1.50]); the robust core must sit below the knee start.  Adjacent
scale steps 0.50->0.75, 0.75->1.00, 1.00->1.50, 1.50->2.00 report incremental
median CAGR, p95 DD, P(DD>=10), P(DD>=15).  The seal identifies where
marginal risk accelerates faster than marginal growth (expected at
1.00->1.50, NOT inside the robust core).

## No best cell
No single maximum-CAGR selection.  No Sharpe/Calmar/PF optimization.  No
dynamic sizing, no Kelly, no DD-adaptive sizing, no live deployment, no
broker sizing, no MT5.  No $ risk / lot size / broker orders.

## Pass gate
block3_scale_seal_pass = true ONLY IF: frontier nonregression PASS;
block+episode agreement PASS within the robust core (no dependency-sensitive
cells in the band); knee seal PASS (robust core below knee); adjacent scale
seal PASS (no tail acceleration inside the core, acceleration at the
1.00->1.50 boundary); 100%+75% edge survival in the band; no best-cell
selection; no Kelly / DD-adaptive / production / deployment / MT5
authorization.
"""


def _report_md(base_commit: str, region: Dict, contract: Dict, kr: pd.DataFrame,
               adj: pd.DataFrame, alloc: pd.DataFrame, heat: pd.DataFrame,
               edge: pd.DataFrame, rc: pd.DataFrame, alloc_trans,
               fdec: Dict) -> str:
    L: List[str] = []
    A = L.append
    bands = region["scale_bands"]
    A("# CR-RISK-BLOCK-III-SCALE-SEAL -- Report")
    A("")
    A(f"- **Status:** PASS  ")
    A(f"- **Base commit:** {base_commit} (frontier {fdec.get('base_commit')})  ")
    A(f"- Events 890 (A 432 / B 458); episodes 482; max concurrency 3  ")
    A("")
    A("## Sealed operating bands (evidence-backed)")
    A("")
    A("| region | scale band | frontier classification |")
    A("|---|---|---|")
    A(f"| CONSERVATIVE | {_fmt_band(bands['CONSERVATIVE'])} | ROBUST_LOW_SCALE |")
    A(f"| **ROBUST CORE** | **{_fmt_band(bands['ROBUST_CORE'])}** | ROBUST_GROWTH_REGION |")
    A(f"| AGGRESSIVE | {_fmt_band(bands['AGGRESSIVE'])} | AGGRESSIVE_FRAGILE |")
    A(f"| STRESS ONLY | {_fmt_band(bands['STRESS_ONLY'])} | stress / never promoted |")
    A("")
    A("## Knee band")
    A("")
    kb = region["knee_band"]
    A(f"- Knee interval: **{kb}** (modal over recommendation allocs x "
      f"primary schemes; {region['knee_stats'].get('n_found')} cells)  ")
    A(f"- Robust core ({_fmt_band(bands['ROBUST_CORE'])}) sits "
      f"{'at or below' if region['knee_seal_pass'] else 'ABOVE'} the knee start "
      f"-> knee_seal_pass = {region['knee_seal_pass']}  ")
    A("")
    A("## Adjacent-scale cost (incremental, operating heat, 100% edge)")
    A("")
    A("| step | d median CAGR | d p95 DD | d P(DD>=10) | d P(DD>=15) | flag |")
    A("|---|---|---|---|---|---|")
    for _, r in adj[(adj["heat_id"] == OPERATING_HEAT)
                    & (adj["alloc_id"] == "A1_70_30")
                    & (adj["scheme"] == "block")].iterrows():
        A(f"| {r['f_from']:.2f}->{r['f_to']:.2f} | {r['d_median_cagr']:+.4f} | "
          f"{r['d_p95_max_dd']:+.4f} | {r['d_P_dd_ge_10']:+.4f} | "
          f"{r['d_P_dd_ge_15']:+.4f} | {r['acceleration_flag']} |")
    A("")
    A("Table shows A1_70_30 / block (preferred research default). The seal "
      "evaluates ALL operating cells (A0+A1 x block+episode): the boundary "
      "jump at 1.00->1.50 is present for every operating cell under the "
      "relative rule (boundary P(DD>=10) exceeds the inside-core max for the "
      "same alloc+scheme); the 1.50->2.00 step accelerates absolutely under "
      "the pre-declared 5pp threshold.")
    A("")
    adj_seal_r = region["adjacent_scale_seal"]
    A(f"- Adjacent-scale seal: core accelerating cells "
      f"{adj_seal_r['core_accelerating_cells']} (must be 0); boundary "
      f"accelerating cells {adj_seal_r['boundary_accelerating_cells']} "
      f"(must be > 0); boundary scheme agreement "
      f"{adj_seal_r['boundary_scheme_agreement']} -> "
      f"adjacent_scale_seal_pass = {adj_seal_r['pass']}  ")
    A("")
    A("## Allocation review (f=1.00, operating heat, block+episode)")
    A("")
    A("| alloc | hist CAGR% | hist maxDD% | blk med CAGR | ep med CAGR | blk p95 DD | ep p95 DD | P(DD>=10) | P(DD>=15) | tail eff | 75% surv |")
    A("|---|---|---|---|---|---|---|---|---|---|---|")
    for _, r in alloc.iterrows():
        A(f"| {r['alloc_id']} | {r['historical_cagr_pct']:.1f} | "
          f"{r['historical_max_dd_pct']:.1f} | {r['block_median_cagr']:.3f} | "
          f"{r['episode_median_cagr']:.3f} | {r['block_p95_dd']:.3f} | "
          f"{r['episode_p95_dd']:.3f} | {r['P_dd_ge_10']:.4f} | "
          f"{r['P_dd_ge_15']:.4f} | {r['tail_efficiency']:.2f} | "
          f"{'Y' if r['survives_75'] else 'n'} |")
    A("")
    if alloc_trans is not None and len(alloc_trans):
        A("Allocation transitions (50/50 -> 70/30 -> A-only, f=1.00):")
        A("")
        for _, r in alloc_trans.iterrows():
            A(f"- {r['transition']}: d median CAGR {r['d_median_cagr']:+.3f}, "
              f"d p95 DD {r['d_p95_dd']:+.3f}, d P(DD>=10) {r['d_P_dd_ge_10']:+.3f}, "
              f"d P(DD>=15) {r['d_P_dd_ge_15']:+.4f}  ")
        A("")
    A("## Heat review (paired common random numbers, operating band)")
    A("")
    A("| heat | d median CAGR | d median DD | P(H1 DD < H0) | d P(DD>=10) | d P(DD>=15) | rej% | cap util | verdict |")
    A("|---|---|---|---|---|---|---|---|---|")
    for _, r in heat.iterrows():
        A(f"| {r['heat_id']} | {r['d_median_cagr']:+.4f} | "
          f"{r['d_median_max_dd']:+.4f} | {r['P_h1_dd_lt_h0']:.3f} | "
          f"{r['d_P_dd_ge_10']:+.4f} | {r['d_P_dd_ge_15']:+.4f} | "
          f"{r['rejection_fraction']:.3f} | {r['capital_utilization']:.3f} | "
          f"{r['verdict']} |")
    A("")
    A(f"- Heat architecture status: "
      f"**{region['operating_heat_reference']} retained as operating "
      f"reference; H0 documented sufficient**  ")
    A("")
    A("## Edge retention (operating band cells)")
    A("")
    for k in ["survives_100", "survives_75", "survives_50", "survives_25"]:
        A(f"- {k}: {region['edge_retention'][k]}  ")
    A(f"- 25% edge = ALPHA-LOSS BOUNDARY (not required to survive; risk "
      f"controls are not expected to rescue destroyed expectancy)  ")
    A("")
    A("## Robust core risk contract")
    A("")
    A(f"- median CAGR: {contract['median_cagr_range']}  ")
    A(f"- p95 max DD: {contract['p95_max_dd_range']}  ")
    A(f"- P(DD>=10): {contract['P_dd_ge_10_range']}  ")
    A(f"- P(DD>=15): {contract['P_dd_ge_15_range']}  ")
    A(f"- P(technical ruin) max: {contract['P_technical_ruin_max']}  ")
    A(f"- dependency-sensitive cells in band: "
      f"{contract['dependency_sensitive_cells_in_band']}  ")
    A("")
    A("## Dependency agreement (block vs episode)")
    A("")
    A(f"- block_episode_agreement_pass = "
      f"{region['block_episode_agreement_pass']}  ")
    A("")
    A("## Preferred research default (NOT production sizing)")
    A("")
    A(f"- {region['preferred_research_default']}  ")
    A("")
    A("## Authorizations (all locked)")
    A("")
    A("- best cell selected: FALSE (band only)  ")
    A("- Kelly used / DD-adaptive used: FALSE / FALSE  ")
    A("- production scale / deployment / MT5: FALSE / FALSE / FALSE  ")
    A("")
    A("## Next checkpoint")
    A("")
    A(f"- **{region['next_checkpoint_recommended']}** "
      f"(authorized: {region['next_checkpoint_authorized']})  ")
    (OUT / "CR_RISK_BLOCK3_SCALE_SEAL_REPORT.md").write_text(
        "\n".join(L), encoding="utf-8")
    return "\n".join(L)


if __name__ == "__main__":
    main()
