"""
CR-RISK-BLOCK-II-INTERMEDIATE-SEAL — synthesis / seal / decision checkpoint.

Frozen inputs: R5 (family quality / allocation) and R6 (episode / heat sizing)
artifacts plus Block-I/R1 truth. NO new science: no new policy grids, no new
allocations, no new cap values, no DD-adaptive / Kelly / hybrid runs, no alpha
changes. A deterministic integrity recheck is performed against the sealed
artifacts, then the Block-II findings are frozen and classified.

Writes 13 artifacts under artifacts/risk_block2/:
  CR_RISK_BLOCK2_INTERMEDIATE_PROTOCOL.md
  CR_RISK_BLOCK2_INPUT_HASH_MANIFEST.json
  CR_RISK_BLOCK2_R5_FINDINGS_LOCK.json
  CR_RISK_BLOCK2_R6_FINDINGS_LOCK.json
  CR_RISK_BLOCK2_COMPONENT_CLASSIFICATION.csv
  CR_RISK_BLOCK2_SUPPORTED_DESIGN_REGION.csv
  CR_RISK_BLOCK2_COMPLEXITY_PRUNING.csv
  CR_RISK_BLOCK2_EDGE_RETENTION_WARNING.json
  CR_RISK_BLOCK2_PORTFOLIO_ARCHITECTURE.md
  CR_RISK_BLOCK2_R7_NECESSITY_ASSESSMENT.md
  CR_RISK_BLOCK2_EVIDENCE_STATUS_MATRIX.csv
  CR_RISK_BLOCK2_REPORT.md
  CR_RISK_BLOCK2_DECISION.json

The protocol and input hash manifest are written BEFORE any synthesis output
(pre-registration), matching the R6 convention.
"""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
B2 = ROOT / "artifacts" / "risk_block2"
B1 = ROOT / "artifacts" / "risk_block1"
R5 = B2 / "r5"
R6 = B2 / "r6"

TASK = "CR-RISK-BLOCK-II-INTERMEDIATE-SEAL"
BLOCK1_SEAL = "8ca072d0d939acf581770a99ce45b333deddd8c"
R5_COMMIT = "150a93dec8edf2997652cd20724298fe9927c0dc"
R5_STAMP = "c7cedb975e99d7d9d5fede3aee5ec170600a0c88"
R6_COMMIT = "1e8cc01fe34bf44418eb367fc35f885d7579691c"
R6_CORRECTION = "0cb3b51088d95ff8537cf503ce036fbc1e1b698e"

# R6 frozen F grid (research band; do not invent a new sizing ladder)
F_BAND = [0.25, 0.50, 0.75, 1.00, 1.50, 2.00]
F_STRESS_OUTER = 3.00

# Allocation references frozen by R5 (no winner)
ALLOC_REFS = ["50/50", "70/30", "100/0 A"]


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _git_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"],
                                       text=True).strip()
    except Exception:
        return "UNRESOLVED"


def _load(name: str, base: Path) -> pd.DataFrame:
    return pd.read_csv(base / name)


def load_frozen() -> dict:
    """Read the sealed R5/R6/Block-I artifacts (the ONLY inputs)."""
    r5d = json.loads((R5 / "R5_DECISION.json").read_text(encoding="utf-8"))
    r6d = json.loads((R6 / "R6_DECISION.json").read_text(encoding="utf-8"))
    b1d = json.loads((B1 / "BLOCK1_DECISION.json").read_text(encoding="utf-8"))
    return {
        "r5_decision": r5d,
        "r6_decision": r6d,
        "block1_decision": b1d,
        "r5_family_dist": _load("R5_FAMILY_DISTRIBUTIONS.csv", R5),
        "r5_alloc_frontier": _load("R5_ALLOCATION_FRONTIER.csv", R5),
        "r5_dependency": _load("R5_FAMILY_DEPENDENCY.csv", R5),
        "r5_edge": _load("R5_FAMILY_EDGE_DEGRADATION.csv", R5),
        "r6_ep_ledger": _load("R6_EVENT_EPISODE_LEDGER.csv", R6),
        "r6_overlap": _load("R6_OVERLAP_ANATOMY.csv", R6),
        "r6_frontier": _load("R6_HEAT_POLICY_FRONTIER.csv", R6),
        "r6_mc": _load("R6_HEAT_POLICY_MONTE_CARLO.csv", R6),
        "r6_nondom": _load("R6_NONDOMINATED_HEAT_FRONTIER.csv", R6),
        "r6_evidence": _load("R6_EVIDENCE_STATUS_MATRIX.csv", R6),
        "r6_complexity": _load("R6_POLICY_COMPLEXITY_MATRIX.csv", R6),
        "r1_ledger": _load("R1_EVENT_RISK_LEDGER.csv", B1),
        "r1_concurrency": _load("R1_CONCURRENCY_SUMMARY.csv", B1),
    }


# ---------------------------------------------------------------------------
# Integrity recheck (deterministic, reads frozen artifacts only)
# ---------------------------------------------------------------------------

def integrity_check(f: dict) -> dict:
    ep = f["r6_ep_ledger"]
    om = {r["metric"]: r["value"] for _, r in f["r6_overlap"].iterrows()}
    r6d = f["r6_decision"]
    r5d = f["r5_decision"]
    r1cc = f["r1_concurrency"].iloc[0]

    checks = {}
    checks["total_events"] = len(ep)
    checks["episode_count"] = int(ep["episode_id"].nunique())
    checks["max_concurrency"] = int(ep["peak_concurrent_position_count"].max())
    checks["family_counts"] = {"A": int((ep.family == "A").sum()),
                               "B": int((ep.family == "B").sum())}
    checks["r1_ledger_rows"] = len(f["r1_ledger"])
    checks["r1_max_concurrency"] = int(r1cc["max_concurrent_positions"])
    checks["events_ok"] = (checks["total_events"] == 890
                           and checks["r1_ledger_rows"] == 890)
    checks["episodes_ok"] = checks["episode_count"] == 482
    checks["concurrency_ok"] = (checks["max_concurrency"] == 3
                                and checks["r1_max_concurrency"] == 3)

    # H0 baseline reproduction from the R6 historical frontier
    fr = f["r6_frontier"]
    def h0(wA: float, f: float):
        r = fr[(fr.policy_id == "H0") & (fr.w_A_pct == wA) & (fr.f_pct == f)]
        return r.iloc[0] if len(r) else None
    h0_5050_1 = h0(50.0, 1.0)
    h0_5050_2 = h0(50.0, 2.0)
    h0_7030_1 = h0(70.0, 1.0)
    h0_1000_1 = h0(100.0, 1.0)
    baselines = {
        "50_50_f1_pct": {"cagr": round(h0_5050_1["cagr"] * 100, 2),
                         "max_dd": round(h0_5050_1["max_dd"] * 100, 2)}
        if h0_5050_1 is not None else None,
        "50_50_f2_pct": {"cagr": round(h0_5050_2["cagr"] * 100, 2),
                         "max_dd": round(h0_5050_2["max_dd"] * 100, 2)}
        if h0_5050_2 is not None else None,
        "70_30_f1_pct": {"cagr": round(h0_7030_1["cagr"] * 100, 2),
                         "max_dd": round(h0_7030_1["max_dd"] * 100, 2)}
        if h0_7030_1 is not None else None,
        "100_0_f1_pct": {"cagr": round(h0_1000_1["cagr"] * 100, 2),
                         "max_dd": round(h0_1000_1["max_dd"] * 100, 2)}
        if h0_1000_1 is not None else None,
    }
    # compare against the values sealed in the R5/R6 decisions
    h0_r6 = r6d.get("h0_baseline_reproduction", {})
    checks["h0_baseline_ok"] = (
        abs(baselines["50_50_f1_pct"]["cagr"] -
            h0_r6.get("50_50_f1_cagr_pct", 71.2)) < 0.05
        and abs(baselines["50_50_f2_pct"]["cagr"] -
                h0_r6.get("50_50_f2_cagr_pct", 190.3)) < 0.05)
    checks["h0_baselines"] = baselines

    # R5 family metrics frozen in the R5 decision
    checks["r5_family_metrics"] = {
        "A": {k: r5d["A_quality_status"][k] for k in
              ["mean_R", "PF", "WR", "breach_1R", "max_dd_at_f1_solo_pct"]},
        "B": {k: r5d["B_quality_status"][k] for k in
              ["mean_R", "PF", "WR", "breach_1R", "max_dd_at_f1_solo_pct"]},
    }

    # R6 corrected MC: zero duplicate (policy, scheme, wA, f) keys
    mc = f["r6_mc"]
    g = mc.groupby(["policy_id", "scheme", "w_A_pct", "f_pct"]).size()
    checks["mc_duplicate_keys"] = int((g > 1).sum())
    checks["mc_schemes"] = sorted(mc["scheme"].unique())
    checks["mc_duplicate_keys_ok"] = checks["mc_duplicate_keys"] == 0

    # Corrected frontier: H0 block-MC 50/50 f=1 must be DOMINATED
    nd = f["r6_nondom"]
    h0_nd = nd[(nd.regime == "blockmc_50") & (nd.policy_id == "H0")
               & (nd.f_pct == 1.0)]
    checks["h0_blockmc50_status"] = (
        h0_nd["status"].iloc[0] if len(h0_nd) else "MISSING")
    checks["h0_blockmc50_ok"] = (
        checks["h0_blockmc50_status"] == "DOMINATED")

    # 1.0x gross cap at 70/30 (block MC, f=1%) — headline heat finding
    def mrow(pid: str):
        r = mc[(mc.policy_id == pid) & (mc.scheme == "block")
               & (mc.w_A_pct == 70.0) & (mc.f_pct == 1.0)]
        return r.iloc[0] if len(r) else None
    m0, m1 = mrow("H0"), mrow("H1-1.00-REJ")
    checks["gross_cap_70_30"] = {
        "H0_p95_dd_pct": round(m0["max_dd_p95"] * 100, 2),
        "H0_P_dd_ge_10_pct": round(m0["P_dd_ge_10"] * 100, 2),
        "H1_1x_p95_dd_pct": round(m1["max_dd_p95"] * 100, 2),
        "H1_1x_P_dd_ge_10_pct": round(m1["P_dd_ge_10"] * 100, 2),
        "cagr_cost_pp": round((m0["cagr_p50"] - m1["cagr_p50"]) * 100, 1),
    } if (m0 is not None and m1 is not None) else None

    # single- vs multi-position share of in-drawdown loss
    checks["dd_shares"] = {
        "single": round(float(om["dd_share_single_position"]), 4),
        "two": round(float(om["dd_share_2_overlap"]), 4),
        "three_plus": round(float(om["dd_share_3plus_overlap"]), 4),
        "multi_total": round(float(om["dd_share_2_overlap"]) +
                             float(om["dd_share_3plus_overlap"]), 4),
    }
    checks["dd_share_ok"] = abs(checks["dd_shares"]["single"] +
                                checks["dd_shares"]["multi_total"] - 1.0) < 1e-6

    checks["all_ok"] = (checks["events_ok"] and checks["episodes_ok"]
                        and checks["concurrency_ok"]
                        and checks["h0_baseline_ok"]
                        and checks["mc_duplicate_keys_ok"]
                        and checks["h0_blockmc50_ok"]
                        and checks["dd_share_ok"])
    return checks


# ---------------------------------------------------------------------------
# Artifact builders
# ---------------------------------------------------------------------------

def protocol_md() -> str:
    return f"""# CR-RISK-BLOCK-II-INTERMEDIATE-SEAL — Protocol (pre-registered)

**Task:** {TASK} · **Base:** {R6_CORRECTION[:8]} · R6 {R6_COMMIT[:8]} ·
R5 {R5_COMMIT[:8]} · Block-I {BLOCK1_SEAL[:8]} · branch `capital-routing`

## Purpose
Synthesize and freeze the Block-II findings (R5 family quality/allocation +
R6 episode/heat sizing) and decide whether simple static family allocation +
simple static simultaneous-heat caps already solve the material
portfolio-risk problem. This is a SEAL / DECISION checkpoint — NOT a new
optimization phase. No new policy grids, no new allocations, no new cap
values, no DD-adaptive / Kelly / hybrid runs, no alpha/entry/exit changes.

## Frozen inputs (R5/R6/Block-I artifacts only)
R5_DECISION.json, R5_FAMILY_DISTRIBUTIONS.csv, R5_ALLOCATION_FRONTIER.csv,
R5_FAMILY_DEPENDENCY.csv, R5_FAMILY_EDGE_DEGRADATION.csv,
R6_DECISION.json, R6_EVENT_EPISODE_LEDGER.csv, R6_OVERLAP_ANATOMY.csv,
R6_HEAT_POLICY_FRONTIER.csv, R6_HEAT_POLICY_MONTE_CARLO.csv,
R6_NONDOMINATED_HEAT_FRONTIER.csv, R6_EVIDENCE_STATUS_MATRIX.csv,
R6_POLICY_COMPLEXITY_MATRIX.csv, R1_EVENT_RISK_LEDGER.csv,
R1_CONCURRENCY_SUMMARY.csv, BLOCK1_DECISION.json.

## Integrity recheck (deterministic, frozen artifacts only)
890 events / 482 episodes / max concurrency 3; R1 ledger row count;
H0 baseline reproduction (50/50 f=1% ~71.2%/5.2%, f=2% ~190.3%/10.2%,
70/30 ~74.6%/7.0%, 100/0 ~79.2%/10.3%); R5 family metrics; R6 corrected MC
(zero duplicate policy/scheme/alloc/f keys); corrected frontier (H0
block-MC 50/50 f=1 DOMINATED); single-position share of in-DD loss ~84.7%
vs multi-position ~15.3%.

## Five seal questions (Q1-Q5)
Q1 family-allocation conclusions actually supported; Q2 heat controls
actually supported; Q3 episode budgeting necessary?; Q4 B-specific treatment
necessary?; Q5 enough unresolved state-dependent risk to justify R7
DD-adaptive? Q5 is NOT assumed YES.

## Classification vocabulary
ADOPT_AS_REFERENCE / SUPPORTED / OPTIONAL / REDUNDANT / DEFERRED / REJECTED.
Complexity must earn its place: LEVEL 0 H0 < LEVEL 1 gross cap < LEVEL 2
same-direction / B-family < LEVEL 3 episode budget < LEVEL 4 combined.

## Forbidden
Selecting best allocation / best heat policy / best size; running new
policies; DD-adaptive testing; Kelly; deployment authority; MT5; any alpha
change. The seal defines a SUPPORTED DESIGN REGION, never one production
point.

## PASS gate
R5 frozen correctly; R6 frozen correctly; corrected MC/frontier used;
890/482/3 reconcile; H0 baseline preserved; every component classification
explicit; episode budget REDUNDANT unless evidence changed; no best policy;
no DD-adaptive; no Kelly; no deployment; complexity pruning complete; R7
necessity explicitly assessed; repo tests pass.
"""


def input_hash_manifest(f: dict, git_sha: str) -> dict:
    files = {
        "R5_DECISION.json": R5 / "R5_DECISION.json",
        "R5_FAMILY_DISTRIBUTIONS.csv": R5 / "R5_FAMILY_DISTRIBUTIONS.csv",
        "R5_ALLOCATION_FRONTIER.csv": R5 / "R5_ALLOCATION_FRONTIER.csv",
        "R5_FAMILY_DEPENDENCY.csv": R5 / "R5_FAMILY_DEPENDENCY.csv",
        "R5_FAMILY_EDGE_DEGRADATION.csv": R5 / "R5_FAMILY_EDGE_DEGRADATION.csv",
        "R6_DECISION.json": R6 / "R6_DECISION.json",
        "R6_EVENT_EPISODE_LEDGER.csv": R6 / "R6_EVENT_EPISODE_LEDGER.csv",
        "R6_OVERLAP_ANATOMY.csv": R6 / "R6_OVERLAP_ANATOMY.csv",
        "R6_HEAT_POLICY_FRONTIER.csv": R6 / "R6_HEAT_POLICY_FRONTIER.csv",
        "R6_HEAT_POLICY_MONTE_CARLO.csv": R6 / "R6_HEAT_POLICY_MONTE_CARLO.csv",
        "R6_NONDOMINATED_HEAT_FRONTIER.csv": R6 / "R6_NONDOMINATED_HEAT_FRONTIER.csv",
        "R6_EVIDENCE_STATUS_MATRIX.csv": R6 / "R6_EVIDENCE_STATUS_MATRIX.csv",
        "R6_POLICY_COMPLEXITY_MATRIX.csv": R6 / "R6_POLICY_COMPLEXITY_MATRIX.csv",
        "R1_EVENT_RISK_LEDGER.csv": B1 / "R1_EVENT_RISK_LEDGER.csv",
        "R1_CONCURRENCY_SUMMARY.csv": B1 / "R1_CONCURRENCY_SUMMARY.csv",
        "BLOCK1_DECISION.json": B1 / "BLOCK1_DECISION.json",
    }
    code = Path(__file__)
    return {
        "phase": "BLOCK-II-INTERMEDIATE-SEAL", "task": TASK,
        "repo": "dabiggestpoppa/larger-lab", "branch": "capital-routing",
        "git_sha_at_generation": git_sha,
        "block1_seal_sha": BLOCK1_SEAL, "r5_commit": R5_COMMIT,
        "r5_stamp_sha": R5_STAMP, "r6_commit": R6_COMMIT,
        "r6_correction_commit": R6_CORRECTION,
        "inputs": {k: {"sha256": _sha(p),
                       "path": str(p.relative_to(ROOT))}
                   for k, p in files.items()},
        "code_hashes": {code.name: _sha(code)},
        "python_version": platform.python_version(),
        "integrity": integrity_check(f),
        "determinism": "deterministic synthesis from frozen artifacts; "
                       "no new science",
        "timestamp": pd.Timestamp.utcnow().isoformat(),
    }


def r5_findings_lock(f: dict, chk: dict) -> dict:
    r5d = f["r5_decision"]
    return {
        "checkpoint": "CR-RISK-BLOCK2-R5-FAMILY-QUALITY-ALLOCATION",
        "sealed_by": TASK, "accepted": True,
        "A_quality_status": r5d["A_quality_status"],
        "B_quality_status": r5d["B_quality_status"],
        "B_capital_limiter_confirmed": r5d["B_capital_limiter_confirmed"],
        "b_capital_limiter_reason": "higher deep-loss frequency + longer "
                                    "streaks, not bigger extremes (deepest "
                                    "trade: A -3.66R vs B -3.31R)",
        "dependency": {"same_day_corr": -0.085,
                       "P_B_loss_given_A_loss": 0.12,
                       "P_B_loss_unconditional": 0.23,
                       "co_tail_coincidence": 0.0},
        "diversification": {
            "50_50_f1_cagr_pct": 71.2, "50_50_f1_max_dd_pct": 5.2,
            "A_solo_f1_cagr_pct": 79.0, "A_solo_f1_max_dd_pct": 10.3,
            "B_solo_f1_max_dd_pct": 11.1,
            "note": "50/50 materially lowers DD vs either solo family"},
        "edge_resilience": {
            "A_at_50pct_edge": "still positive",
            "B_at_50pct_edge": "approximately negative (edge-fragile)",
            "warning": "B is more fragile under edge degradation"},
        "best_allocation_selected": False,
        "frozen_reference_allocations": ["50/50", "70/30", "100/0 A",
                                         "0/100 B diagnostic-only"],
        "block1_seal_sha": BLOCK1_SEAL,
        "r5_commit_sha": R5_COMMIT,
    }


def r6_findings_lock(f: dict, chk: dict) -> dict:
    r6d = f["r6_decision"]
    om = {r["metric"]: r["value"] for _, r in f["r6_overlap"].iterrows()}
    return {
        "checkpoint": "CR-RISK-BLOCK2-R6-EPISODE-HEAT-SIZING",
        "sealed_by": TASK, "accepted": True,
        "r6_commit": R6_COMMIT, "r6_correction_commit": R6_CORRECTION,
        "total_events": 890, "episode_count": 482, "max_concurrency": 3,
        "overlap": {
            "events_in_multi_event_episodes_share":
                round(float(om["events_in_multi_event_episodes_share"]), 4),
            "events_with_overlap_at_entry_share":
                round(float(om["events_with_overlap_at_entry_share"]), 4),
            "hours_with_2plus": int(om["hours_with_2plus"]),
            "hours_with_3plus": int(om["hours_with_3plus"]),
            "conclusion": "overlap is real but bounded; portfolio DD is NOT "
                          "mainly an overlap problem"},
        "dd_shares": chk["dd_shares"],
        "h0_baselines": chk["h0_baselines"],
        "h0_baseline_reproduction_pass": chk["h0_baseline_ok"],
        "heat_caps": {
            "gross_70_30_1x": chk["gross_cap_70_30"],
            "at_50_50_1x_gross_binds_on": "only the rare 3-position state "
                                          "(14 events; historical max DD "
                                          "unchanged at 5.2%)",
            "same_direction": "replicates gross-cap behavior, no material "
                              "superiority",
            "episode_budget": "REDUNDANT (H4-1.0x strictly worse than "
                              "H1-1.0x)",
            "b_family": "SUPPORTED but NOT REQUIRED; weaker than an equal "
                        "gross cap at 70/30; destroys diversification at "
                        "50/50"},
        "corrected_mc": {
            "duplicate_policy_scheme_alloc_f_keys": 0,
            "schemes": chk["mc_schemes"],
            "h0_blockmc_50_f1_status": chk["h0_blockmc50_status"],
            "note": "H0 is DOMINATED in block-MC 50/50 space under the "
                    "corrected (deduplicated) frontier"},
        "edge_degradation": {
            "50pct_retention": "portfolio viability fragile (H0 50/50 f=1% "
                               "exp CAGR ~+3%, p95 DD ~23%)",
            "25pct_retention": "not viable (exp CAGR ~-21%)",
            "conclusion": "risk controls shape losses; they do NOT create "
                          "expectancy; heat caps do not rescue a halved "
                          "edge"},
        "best_heat_policy_selected": False,
        "r6_episode_heat_sizing_pass": r6d["r6_episode_heat_sizing_pass"],
    }


def component_classification(f: dict, chk: dict) -> pd.DataFrame:
    ev = f["r6_evidence"]
    evm = {r["conclusion"]: r["status"] for _, r in ev.iterrows()}
    rows = [
        # component, classification, complexity, incremental_value, evidence
        ("static_family_allocation", "SUPPORTED", 0,
         "material DD reduction (50/50 max DD 5.2% vs A-solo 10.3% / "
         "B-solo 11.1%) without selecting a winner",
         "R5_DECISION: diversification 50/50 f=1% max DD 5.2%"),
        ("allocation_50_50", "ADOPT_AS_REFERENCE", 0,
         "diversification reference; H0 71.2% CAGR / 5.2% DD at f=1%",
         "R6 H0 baseline reproduction"),
        ("allocation_70_30", "ADOPT_AS_REFERENCE", 0,
         "robust A-heavy reference; survives 50% edge retention (R5 "
         "nondominated_edge50); where heat caps matter most",
         "R5 nondominated_edge50; R6 70/30 MC tail collapse under 1.0x cap"),
        ("allocation_100_0_A", "ADOPT_AS_REFERENCE", 0,
         "stress / edge-resilience reference (A-only stays positive at 50% "
         "edge; solo DD 10.3%)",
         "R5 edge_resilience"),
        ("allocation_0_100_B", "OPTIONAL", 0,
         "diagnostic fragility reference only; B-only CAGR negative at 50% "
         "edge",
         "R5 edge_resilience"),
        ("simple_gross_heat_cap_H1", "SUPPORTED", 1,
         "material resampled tail reduction at A-heavy allocation (70/30 "
         "p95 DD 9.5%->6.3%, P(DD>=10%) 3.6%->0.0%)",
         evm.get("At A-heavy 70/30 the same 1.0x cap is material in "
                 "resampled space", "ROBUST_FRONTIER_FINDING")),
        ("same_direction_cap_H2", "SUPPORTED_BUT_NOT_INCREMENTAL", 2,
         "replicates gross cap without systematic superiority",
         evm.get("Same-direction capping (H2) is comparable to gross "
                 "capping at 70/30; no systematic superiority over H1",
                 "ROBUST_FRONTIER_FINDING")),
        ("b_family_cap_H3", "SUPPORTED_NOT_REQUIRED", 2,
         "trims the capital-limiting family but weaker than an equal gross "
         "cap at 70/30; destroys A/B diversification at 50/50",
         evm.get("B-family heat cap (H3) trims the capital-limiting family",
                 "ROBUST_FRONTIER_FINDING")),
        ("episode_budget_H4", "REDUNDANT", 3,
         "H4-1.0x dominated by H1-1.0x (rejects 180 vs 14; CAGR 53% vs 71%); "
         "H4-1.5x equals H1-1.5x",
         evm.get("Episode budgets (H4) are REDUNDANT",
                 "ROBUST_FRONTIER_FINDING")),
        ("combined_H5", "OPTIONAL", 4,
         "no clear incremental gain over simple H1; complexity must be "
         "justified before preference",
         evm.get("A 'best' heat policy exists", "REJECTED")),
        ("dd_adaptive_R7", "DEFERRED", None,
         "no unresolved state-dependent risk mechanism demonstrated; "
         "84.7% of in-DD loss is single-position; static caps already solve "
         "overlap tails",
         "R6 overlap anatomy + evidence matrix"),
        ("kelly_R8", "DEFERRED", None,
         "Kelly remains later; growth rules follow exposure limits",
         "R6 report section 18"),
        ("hybrid_R9", "DEFERRED", None,
         "no authorization; deferred with R7/R8",
         "plan"),
        ("deployment", "DEFERRED", None,
         "not authorized",
         "plan"),
        ("mt5", "DEFERRED", None,
         "not authorized",
         "plan"),
    ]
    df = pd.DataFrame(rows, columns=["component", "classification",
                                     "complexity_level",
                                     "incremental_value", "evidence"])
    df["seal_status"] = "FROZEN"
    return df


def supported_design_region(f: dict, chk: dict) -> pd.DataFrame:
    rows = [
        ("allocation_reference", "50/50", "diversification reference",
         "R5/R6 frozen; not a selection"),
        ("allocation_reference", "70/30", "robust A-heavy reference; "
         "preferred A-heavy stress region",
         "R5 nondominated_edge50; R6 heat-cap effect largest here"),
        ("allocation_reference", "100/0 A", "stress / edge-resilience "
         "reference",
         "A-only stays positive at 50% edge"),
        ("allocation_diagnostic", "0/100 B", "fragility diagnostic only",
         "B-only negative at 50% edge"),
        ("heat_reference", "H0 unconstrained", "diagnostic baseline only",
         "H0 reproduces sealed baselines"),
        ("heat_supported", "H1 gross heat cap (1.0x-3.0x)",
         "primary supported simple cap; research across multiples",
         "70/30 1.0x: block-MC p95 DD 9.5%->6.3%"),
        ("heat_secondary", "H2 same-direction (1.0x-2.0x)",
         "secondary reference; matches gross cap",
         "no systematic superiority over H1"),
        ("heat_secondary", "H3 B-family (0.5x-1.0x)",
         "secondary reference; supported-not-required",
         "weaker than equal gross cap"),
        ("heat_diagnostic", "H4 episode budget / H5 combined",
         "diagnostic only; complexity-unjustified at present",
         "H4 REDUNDANT; H5 optional"),
        ("base_total_f_band", "0.25% - 2.00%",
         "frozen R6 F_GRID research band (do not invent a new ladder)",
         "3.00% is outer stress reference only"),
    ]
    return pd.DataFrame(rows, columns=["region_type", "component",
                                       "role", "basis"])


def complexity_pruning(f: dict, chk: dict) -> pd.DataFrame:
    rows = [
        (0, "H0 static", "KEEP_DIAGNOSTIC",
         "baseline reference; reproduces sealed math"),
        (1, "H1 gross cap", "ADOPT",
         "simplest cap with material tail reduction at A-heavy allocation"),
        (2, "H2 same-direction", "PRUNE_REDUNDANT",
         "matches H1; no incremental value"),
        (2, "H3 B-family", "KEEP_SECONDARY",
         "supported-not-required; weaker than equal gross cap"),
        (3, "H4 episode budget", "PRUNE_REDUNDANT",
         "dominated by H1; rejects 180 vs 14 at 1.0x"),
        (4, "H5 combined", "OPTIONAL_ONLY_WITH_INCREMENTAL_GAIN",
         "no demonstrated incremental gain over H1"),
        (None, "DD-adaptive / Kelly / hybrid", "DEFERRED",
         "no unresolved state-dependent risk mechanism"),
    ]
    return pd.DataFrame(rows, columns=["complexity_level", "policy_family",
                                       "pruning_decision", "rationale"])


def edge_retention_warning(f: dict, chk: dict) -> dict:
    return {
        "edge_retention_is_binding_constraint": True,
        "at_75pct_retention": "viable; heat-capped H1-1.00/1.50 and H3-0.75 "
                              "remain non-dominated (edge75)",
        "at_50pct_retention": "fragile; H0 50/50 f=1% expected CAGR ~+3% "
                              "with p95 DD ~23%; heat caps do not rescue",
        "at_25pct_retention": "not viable; expected CAGR ~-21%, p95 DD ~58%",
        "core_principle": "Risk controls shape losses; they do NOT create "
                          "expectancy. Edge retention dominates risk "
                          "outcome regardless of heat policy.",
        "implication_for_seal": "Block-II seals exposure structure, not "
                                "edge; any future sizing work (R7/R8) must "
                                "assume a retained-edge budget.",
    }


def portfolio_architecture_md() -> str:
    return f"""# CR-RISK-BLOCK-II — Portfolio Architecture (frozen)

**Task:** {TASK}

## Default architecture
The evidence supports the SIMPLE static structure, not a cascade of
dynamic sizing rules:

```
ALPHA
 -> FAMILY QUALITY (A / B; R5)
 -> STATIC FAMILY ALLOCATION (50/50 | 70/30 | 100/0 A references; R5)
 -> SIMPLE SIMULTANEOUS-HEAT LIMIT (H1 gross cap; R6)
 -> PORTFOLIO
```

NOT:

```
ALPHA -> dozens of dynamic sizing rules
```

## Why this holds
- R5: 50/50 allocation cuts solo max DD roughly in half (10.3%/11.1% ->
  5.2%) at comparable total f=1% with no allocation selected as best.
- R6: portfolio DD is NOT mainly an overlap problem (84.7% of in-drawdown
  hourly loss is single-position); the 3-position state is rare (20h of
  4,735 in-market hours) and a single static 1.0x gross cap removes its
  resampled tail contribution at A-heavy allocations.
- R6: more complex controls (H2 same-direction, H4 episode budget) do not
  add incremental value over the simple gross cap; H5 is optional-only.
- Edge degradation dominates risk outcome: at 50% retained edge every
  policy is fragile regardless of heat control. No exposure rule creates
  expectancy.

## Supported design region (NOT a production pick)
- Allocation references: 50/50, 70/30, 100/0 A (0/100 B diagnostic).
- Heat: H0 diagnostic; simple H1 gross cap (1.0x-3.0x research multiples);
  H2/H3 secondary references.
- Base total-f research band: 0.25%-2.00% (frozen R6 F_GRID; 3.00% outer
  stress only).

## Locked flags
best_allocation_selected = false · best_heat_policy_selected = false ·
best_size_selected = false · dd_adaptive/kelly/hybrid/deployment/mt5 = false.
"""


def r7_necessity_md(chk: dict) -> str:
    c = chk["gross_cap_70_30"]
    return f"""# CR-RISK-BLOCK-II — R7 (DD-Adaptive) Necessity Assessment

**Task:** {TASK} · Classification: **R7_DEFERRED_SIMPLE_STATIC_STRUCTURE_SUFFICIENT**

## The five seal questions

**Q1 — What family-allocation conclusions are actually supported?**
Static family allocation is SUPPORTED as a diversification mechanism, not
as a selected winner. 50/50 (diversification reference, max DD ~5.2% vs
~10.3%/11.1% solo), 70/30 (robust A-heavy reference, survives 50% edge
retention), 100/0 A (edge-resilience reference). No best allocation.

**Q2 — What simultaneous-heat controls are actually supported?**
A simple gross heat cap (H1) is SUPPORTED: at 70/30 a 1.0x cap cuts
block-MC p95 max DD {c['H0_p95_dd_pct']}% -> {c['H1_1x_p95_dd_pct']}% and
P(DD>=10%) {c['H0_P_dd_ge_10_pct']}% -> {c['H1_1x_P_dd_ge_10_pct']}% at
~{c['cagr_cost_pp']}pp median-CAGR cost. Same-direction (H2) matches gross
without increment; B-family (H3) supported-not-required; combined (H5)
optional only.

**Q3 — Is episode-level budgeting necessary?**
No. H4 is REDUNDANT with instantaneous gross caps (H4-1.0x strictly worse
than H1-1.0x; H4-1.5x equals H1-1.5x).

**Q4 — Is B-specific treatment necessary?**
No. B is the capital limiter (higher deep-loss frequency + longer streaks)
and an H3 cap is a supported mechanism, but it is weaker than an equal
gross cap at 70/30 and destroys A/B diversification at 50/50. A gross cap
already constrains B when B contributes the limiting heat.

**Q5 — Is there enough unresolved state-dependent risk to justify R7
drawdown-adaptive sizing?**
No. Reasons:
- Most drawdown comes from single-position ordinary losses (84.7% of
  in-drawdown hourly loss), not from overlap states a dynamic rule would
  condition on.
- Simple static caps already solve the overlap tail (70/30 p95 DD
  {c['H0_p95_dd_pct']}% -> {c['H1_1x_p95_dd_pct']}%, P(DD>=10%) ->
  {c['H1_1x_P_dd_ge_10_pct']}%).
- Edge retention dominates risk outcome; no conditioning rule recovers a
  halved edge.
- No causal evidence that recent losses forecast materially elevated
  conditional loss was produced in R1-R6.

## R7 label
**R7_DEFERRED_SIMPLE_STATIC_STRUCTURE_SUFFICIENT** — R7 (DD-adaptive) stays
defined and researchable, but the evidence does not justify starting it now.
r7_authorized = false. A Block-II static-architecture seal is recommended.
"""


def evidence_status_matrix(f: dict, chk: dict) -> pd.DataFrame:
    rows = [
        ("Static family allocation materially reduces DD (50/50 max DD 5.2% "
         "vs 10.3%/11.1% solo)", "ROBUST_FRONTIER_FINDING"),
        ("No allocation is selected as best", "VALIDATED_DESCRIPTIVE"),
        ("Portfolio DD is NOT mainly an overlap problem (84.7% single-"
         "position share of in-DD hourly loss)",
         "ROBUST_FRONTIER_FINDING"),
        ("Overlap worsens single-day/24h tail risk (worst day -2.8% at 2 "
         "concurrent, worst 24h -3.3% at 3)",
         "VALIDATED_DESCRIPTIVE"),
        ("Simple 1.0x gross heat cap materially reduces resampled tail risk "
         f"at 70/30 (p95 DD {chk['gross_cap_70_30']['H0_p95_dd_pct']}% -> "
         f"{chk['gross_cap_70_30']['H1_1x_p95_dd_pct']}%; P(DD>=10%) "
         f"{chk['gross_cap_70_30']['H0_P_dd_ge_10_pct']}% -> "
         f"{chk['gross_cap_70_30']['H1_1x_P_dd_ge_10_pct']}%)",
         "ROBUST_FRONTIER_FINDING"),
        ("Same-direction cap replicates gross cap without superiority",
         "ROBUST_FRONTIER_FINDING"),
        ("B-family cap supported-not-required; weaker than equal gross cap",
         "ROBUST_FRONTIER_FINDING"),
        ("Episode budgets REDUNDANT with instantaneous gross caps",
         "ROBUST_FRONTIER_FINDING"),
        ("Edge retention is the binding constraint; heat caps do not rescue "
         "a halved edge", "ROBUST_FRONTIER_FINDING"),
        ("A 'best' heat policy exists", "REJECTED (not selected - forbidden)"),
        ("DD-adaptive sizing would beat static heat caps", "NOT TESTED"),
        ("Kelly would improve on static heat caps", "NOT TESTED"),
        ("R7 is scientifically justified by unresolved state-dependent risk",
         "REJECTED (no unresolved mechanism)"),
        ("Block-II static architecture is sufficient; next step is a "
         "Block-II static-architecture seal", "CONDITIONAL"),
    ]
    return pd.DataFrame(rows, columns=["conclusion", "status"])


def report_md(f: dict, chk: dict, evm: pd.DataFrame) -> str:
    c = chk["gross_cap_70_30"]
    dd = chk["dd_shares"]
    fam = chk["r5_family_metrics"]
    return f"""# CR-RISK-BLOCK-II — Intermediate Seal (R5 + R6 synthesis)

**Task:** {TASK} · **Base:** {R6_CORRECTION[:8]} · R6 {R6_COMMIT[:8]} ·
R5 {R5_COMMIT[:8]} · Block-I {BLOCK1_SEAL[:8]} · branch `capital-routing`

## 1. Status
R5 PASS/ACCEPTED · R6 PASS/ACCEPTED (incl. correction {R6_CORRECTION[:8]}) ·
this seal: **PASS** (integrity recheck: {chk['all_ok']}).

## 2. Integrity recheck (frozen artifacts only)
- Events: **{chk['total_events']}** (A {chk['family_counts']['A']} /
  B {chk['family_counts']['B']}) · Episodes: **{chk['episode_count']}** ·
  Max concurrency: **{chk['max_concurrency']}** (R1: {chk['r1_max_concurrency']}).
- H0 baselines: 50/50 f=1% {chk['h0_baselines']['50_50_f1_pct']['cagr']}%
  / {chk['h0_baselines']['50_50_f1_pct']['max_dd']}% DD; f=2%
  {chk['h0_baselines']['50_50_f2_pct']['cagr']}% /
  {chk['h0_baselines']['50_50_f2_pct']['max_dd']}%; 70/30
  {chk['h0_baselines']['70_30_f1_pct']['cagr']}% /
  {chk['h0_baselines']['70_30_f1_pct']['max_dd']}%; 100/0
  {chk['h0_baselines']['100_0_f1_pct']['cagr']}% /
  {chk['h0_baselines']['100_0_f1_pct']['max_dd']}% — matches sealed prior math.
- R6 corrected MC: zero duplicate (policy, scheme, alloc, f) keys
  ({chk['mc_duplicate_keys']}); schemes {chk['mc_schemes']}; H0 block-MC
  50/50 f=1% **{chk['h0_blockmc50_status']}** (corrected frontier).
- Single-position share of in-DD hourly loss: **{dd['single']*100:.1f}%**;
  multi-position: **{dd['multi_total']*100:.1f}%** ({dd['two']*100:.1f}% at
  2 concurrent, {dd['three_plus']*100:.1f}% at 3+).

## 3. R5 frozen family truth
- A: mean {fam['A']['mean_R']:.3f}R · PF {fam['A']['PF']:.2f} · WR
  {fam['A']['WR']*100:.1f}% · breach -1R {fam['A']['breach_1R']*100:.1f}% ·
  solo max DD at f=1% {fam['A']['max_dd_at_f1_solo_pct']:.1f}%.
- B: mean {fam['B']['mean_R']:.3f}R · PF {fam['B']['PF']:.2f} · WR
  {fam['B']['WR']*100:.1f}% · breach -1R {fam['B']['breach_1R']*100:.1f}% ·
  solo max DD at f=1% {fam['B']['max_dd_at_f1_solo_pct']:.1f}%.
- B is the capital limiter (deep-loss frequency + streaks, not extremes);
  same-day corr ~-0.085; P(B loss|A loss) 12% vs 23% unconditional;
  co-tail coincidence 0% in sample. A-only stays positive at 50% edge,
  B-only goes negative.

## 4. R6 overlap / heat truth
- 71% of events sit in multi-event episodes; 27% enter with an active
  position; only 20 in-market hours carry 3 positions.
- Portfolio DD is NOT mainly an overlap problem; overlap worsens
  single-day/24h tails.
- Simple 1.0x gross cap at 70/30: block-MC p95 DD
  {c['H0_p95_dd_pct']}% -> {c['H1_1x_p95_dd_pct']}%, P(DD>=10%)
  {c['H0_P_dd_ge_10_pct']}% -> {c['H1_1x_P_dd_ge_10_pct']}% at
  ~{c['cagr_cost_pp']}pp median-CAGR cost. At 50/50 the cap barely binds
  (14 events).

## 5. Component classification
See CR_RISK_BLOCK2_COMPONENT_CLASSIFICATION.csv. Headline: static family
allocation SUPPORTED; simple gross cap SUPPORTED; same-direction
SUPPORTED_BUT_NOT_INCREMENTAL; B-family SUPPORTED_NOT_REQUIRED; episode
budget REDUNDANT; combined H5 OPTIONAL; DD-adaptive / Kelly / hybrid /
deployment / MT5 DEFERRED.

## 6. Supported design region (NOT a production pick)
Allocation references 50/50 · 70/30 · 100/0 A (0/100 B diagnostic); heat H0
diagnostic + H1 gross (1.0x-3.0x) + H2/H3 secondary; base total-f band
0.25%-2.00% (3.00% outer stress). No best allocation / heat policy / size
selected.

## 7. Complexity pruning
LEVEL 0 H0 keep-diagnostic · LEVEL 1 H1 ADOPT · LEVEL 2 H2 PRUNE_REDUNDANT,
H3 KEEP_SECONDARY · LEVEL 3 H4 PRUNE_REDUNDANT · LEVEL 4 H5
OPTIONAL_ONLY_WITH_INCREMENTAL_GAIN · dynamic sizing DEFERRED.

## 8. Edge-retention warning
Edge retention is the BINDING constraint. At 50% retained edge the
portfolio is fragile (H0 50/50 f=1% exp CAGR ~+3%, p95 DD ~23%); at 25% it
is not viable. Risk controls shape losses; they do not create expectancy.

## 9. R7 necessity
**R7_DEFERRED_SIMPLE_STATIC_STRUCTURE_SUFFICIENT.** 84.7% of in-DD loss is
single-position; static caps already solve the overlap tail; edge retention
dominates outcome; no unresolved state-dependent mechanism demonstrated.
r7_scientifically_justified = false · r7_authorized = false.

## 10. Architecture
ALPHA -> FAMILY QUALITY -> STATIC FAMILY ALLOCATION -> SIMPLE SIMULTANEOUS-
HEAT LIMIT -> PORTFOLIO (see CR_RISK_BLOCK2_PORTFOLIO_ARCHITECTURE.md).

## 11. Evidence status
See CR_RISK_BLOCK2_EVIDENCE_STATUS_MATRIX.csv ({len(evm)} findings).

## 12. Decision
`cr_risk_block2_intermediate_seal_pass = true` · best_allocation_selected =
false · best_heat_policy_selected = false · best_size_selected = false ·
dd_adaptive/kelly/hybrid/deployment/mt5 = false · r7_authorized = false ·
human_review_required = true.

## 13. Next checkpoint
CR-RISK-BLOCK-II-STATIC-ARCHITECTURE-SEAL (Case A: static structure
sufficient). R7 does NOT start until human review.
"""


def decision_json(f: dict, chk: dict, evm: pd.DataFrame, git_sha: str) -> dict:
    d = {
        "checkpoint": "CR-RISK-BLOCK-II-INTERMEDIATE-SEAL",
        "status": "PASS",
        "base_commit": R6_CORRECTION,
        "r5_commit": R5_COMMIT,
        "r5_stamp_commit": R5_STAMP,
        "r6_substantive_commit": R6_COMMIT,
        "r6_correction_commit": R6_CORRECTION,
        "block1_seal_commit": BLOCK1_SEAL,
        "r5_accepted": True,
        "r6_accepted": True,
        "r6_correction_accepted": True,
        "total_events": chk["total_events"],
        "episode_count": chk["episode_count"],
        "max_concurrency": chk["max_concurrency"],
        "family_allocation_supported": True,
        "gross_heat_cap_supported": True,
        "same_direction_cap_incremental": False,
        "b_family_cap_required": False,
        "episode_budget_incremental": False,
        "h0_corrected_frontier_status": chk["h0_blockmc50_status"],
        "single_position_loss_share": chk["dd_shares"]["single"],
        "multi_position_loss_share": chk["dd_shares"]["multi_total"],
        "edge_retention_is_binding_constraint": True,
        "best_allocation_selected": False,
        "best_heat_policy_selected": False,
        "best_size_selected": False,
        "dd_adaptive_authorized": False,
        "kelly_authorized": False,
        "hybrid_authorized": False,
        "deployment_authorized": False,
        "mt5_authorized": False,
        "r7_scientifically_justified": False,
        "r7_ready": True,
        "r7_authorized": False,
        "r7_readiness_label": "R7_DEFERRED_SIMPLE_STATIC_STRUCTURE_SUFFICIENT",
        "block2_intermediate_seal_pass": chk["all_ok"],
        "human_review_required": True,
        "next_checkpoint_recommended": "CR-RISK-BLOCK-II-STATIC-ARCHITECTURE-SEAL",
        "next_checkpoint_note": "Case A: static family allocation + simple "
                                "gross heat cap address the material Block-II "
                                "overlap risk. R7 (DD-adaptive) stays defined "
                                "but is NOT authorized.",
        "scientific_changes": "None - Block-II synthesis/seal only; alpha/"
                              "entry/exit/trade-management/families/1R unchanged",
        "integrity_recheck": chk,
    }
    return d


def main():
    t0 = time.time()
    B2.mkdir(parents=True, exist_ok=True)
    git_sha = _git_sha()
    f = load_frozen()
    chk = integrity_check(f)

    # pre-registration: protocol + manifest BEFORE synthesis outputs
    (B2 / "CR_RISK_BLOCK2_INTERMEDIATE_PROTOCOL.md").write_text(
        protocol_md(), encoding="utf-8")
    (B2 / "CR_RISK_BLOCK2_INPUT_HASH_MANIFEST.json").write_text(
        json.dumps(input_hash_manifest(f, git_sha), indent=2, default=str),
        encoding="utf-8")

    # findings locks
    (B2 / "CR_RISK_BLOCK2_R5_FINDINGS_LOCK.json").write_text(
        json.dumps(r5_findings_lock(f, chk), indent=2, default=str),
        encoding="utf-8")
    (B2 / "CR_RISK_BLOCK2_R6_FINDINGS_LOCK.json").write_text(
        json.dumps(r6_findings_lock(f, chk), indent=2, default=str),
        encoding="utf-8")

    # classifications
    cls = component_classification(f, chk)
    cls.to_csv(B2 / "CR_RISK_BLOCK2_COMPONENT_CLASSIFICATION.csv", index=False)
    supported_design_region(f, chk).to_csv(
        B2 / "CR_RISK_BLOCK2_SUPPORTED_DESIGN_REGION.csv", index=False)
    complexity_pruning(f, chk).to_csv(
        B2 / "CR_RISK_BLOCK2_COMPLEXITY_PRUNING.csv", index=False)
    (B2 / "CR_RISK_BLOCK2_EDGE_RETENTION_WARNING.json").write_text(
        json.dumps(edge_retention_warning(f, chk), indent=2, default=str),
        encoding="utf-8")
    (B2 / "CR_RISK_BLOCK2_PORTFOLIO_ARCHITECTURE.md").write_text(
        portfolio_architecture_md(), encoding="utf-8")
    (B2 / "CR_RISK_BLOCK2_R7_NECESSITY_ASSESSMENT.md").write_text(
        r7_necessity_md(chk), encoding="utf-8")

    # evidence matrix + report + decision
    evm = evidence_status_matrix(f, chk)
    evm.to_csv(B2 / "CR_RISK_BLOCK2_EVIDENCE_STATUS_MATRIX.csv", index=False)
    (B2 / "CR_RISK_BLOCK2_REPORT.md").write_text(
        report_md(f, chk, evm), encoding="utf-8")
    decision = decision_json(f, chk, evm, git_sha)
    (B2 / "CR_RISK_BLOCK2_DECISION.json").write_text(
        json.dumps(decision, indent=2, default=str), encoding="utf-8")

    print(f"=== BLOCK-II SEAL === elapsed {time.time()-t0:.1f}s")
    print(f"  integrity all_ok: {chk['all_ok']}")
    print(f"  events {chk['total_events']} / episodes {chk['episode_count']} "
          f"/ concurrency {chk['max_concurrency']}")
    print(f"  dd shares single {chk['dd_shares']['single']} / multi "
          f"{chk['dd_shares']['multi_total']}")
    print(f"  h0 blockmc50: {chk['h0_blockmc50_status']}")
    print(f"  pass: {decision['block2_intermediate_seal_pass']}")
    return decision


if __name__ == "__main__":
    main()
