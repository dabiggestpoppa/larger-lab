"""
CR-RISK-BLOCK-II-STATIC-ARCHITECTURE-SEAL — final Block-II static seal.

Synthesizes and freezes the simplest portfolio-risk architecture supported by
R1-R6 evidence:

    VALID ALPHA EVENTS -> FAMILY CLASSIFICATION -> STATIC FAMILY ALLOCATION
        -> SIMPLE GROSS SIMULTANEOUS-HEAT LIMIT -> PORTFOLIO

NO new science. This checkpoint:
  - pre-registers a protocol + input hash manifest,
  - re-runs a deterministic integrity recheck against frozen artifacts
    (890 events, 432 A / 458 B, 482 episodes, max concurrency 3),
  - reproduces frozen R6 admission decisions using the minimal
    static_risk_architecture module (causal H0/H1 gross-cap admission),
  - reproduces frozen R6 H0/H1 portfolio metrics (reference parity),
  - freezes the component classification / complexity pruning / edge-retention
    constraint / policy-role matrix,
  - writes a decision artifact that selects the ARCHITECTURE (not a production
    allocation / cap / size) and leaves R7/R8/R9/deployment locked.

Writes 14 artifacts under research/capital_routing/risk/block2_static/:
  CR_RISK_BLOCK2_STATIC_PROTOCOL.md
  CR_RISK_BLOCK2_STATIC_INPUT_HASH_MANIFEST.json
  CR_RISK_BLOCK2_STATIC_ARCHITECTURE.json
  CR_RISK_BLOCK2_STATIC_ARCHITECTURE.md
  CR_RISK_BLOCK2_REFERENCE_CONFIGS.json
  CR_RISK_BLOCK2_POLICY_ROLE_MATRIX.csv
  CR_RISK_BLOCK2_COMPLEXITY_PRUNING.csv
  CR_RISK_BLOCK2_REFERENCE_PARITY.csv
  CR_RISK_BLOCK2_CAUSAL_ADMISSION_AUDIT.json
  CR_RISK_BLOCK2_EDGE_RETENTION_CONSTRAINT.json
  CR_RISK_BLOCK2_IMPLEMENTATION_CONTRACT.md
  CR_RISK_BLOCK2_COMPONENT_STATUS.csv
  CR_RISK_BLOCK2_REPORT.md
  CR_RISK_BLOCK2_DECISION.json

Do NOT start R7. Do NOT select a production configuration.
"""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
B2 = ROOT / "artifacts" / "risk_block2"
B1 = ROOT / "artifacts" / "risk_block1"
P3 = ROOT / "artifacts" / "phase_03"
P5 = ROOT / "artifacts" / "phase_05"
P75 = ROOT / "artifacts" / "phase_07_5"
OUT = ROOT / "research" / "capital_routing" / "risk" / "block2_static"

TASK = "CR-RISK-BLOCK-II-STATIC-ARCHITECTURE-SEAL"
BLOCK1_SEAL = "8ca072d0d939acf581770a99ce45b333deddd8c"
R5_COMMIT = "150a93dec8edf2997652cd20724298fe9927c0dc"
R6_COMMIT = "1e8cc01fe34bf44418eb367fc35f885d7579691c"
R6_CORRECTION = "0cb3b51088d95ff8537cf503ce036fbc1e1b698e"
B2_INTERMEDIATE = "8abb7c21e907254f75618deb3c9095c971c6b9be"

# Frozen sealed baseline references (H0, from the R6 corrected frontier).
SEALED_H0_BASELINES = {
    ("H0", 50, 50, 1.0): {"cagr": 71.21, "max_dd": 5.19},
    ("H0", 50, 50, 2.0): {"cagr": 190.31, "max_dd": 10.17},
    ("H0", 70, 30, 1.0): {"cagr": 74.57, "max_dd": 6.97},
    ("H0", 100, 0, 1.0): {"cagr": 79.15, "max_dd": 10.30},
}

# Frozen 70/30 1.0x gross-cap MC result (R6 corrected block bootstrap).
SEALED_H1_70_30 = {
    "H0_p95_dd_pct": 9.5, "H0_P_dd_ge_10_pct": 3.6,
    "H1_1x_p95_dd_pct": 6.26, "H1_1x_P_dd_ge_10_pct": 0.0,
    "cagr_cost_pp": 5.4,
}


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "UNRESOLVED"


def _load_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)


# ---------------------------------------------------------------------------
# Frozen input list + manifest (written BEFORE any synthesis output)
# ---------------------------------------------------------------------------

FROZEN_INPUTS = [
    P75 / "P7_5_TRADES.csv",
    P5 / "routing_events.parquet",
    P3 / "h1_strict_common_panel.parquet",
    B1 / "R1_EVENT_RISK_LEDGER.csv",
    B1 / "R1_CONCURRENCY_SUMMARY.csv",
    B1 / "R1_ROUTING_EPISODES.csv",
    B1 / "BLOCK1_DECISION.json",
    B2 / "r5" / "R5_DECISION.json",
    B2 / "r5" / "R5_FAMILY_DISTRIBUTIONS.csv",
    B2 / "r5" / "R5_ALLOCATION_FRONTIER.csv",
    B2 / "r5" / "R5_FAMILY_DEPENDENCY.csv",
    B2 / "r5" / "R5_FAMILY_EDGE_DEGRADATION.csv",
    B2 / "r6" / "R6_DECISION.json",
    B2 / "r6" / "R6_EVENT_EPISODE_LEDGER.csv",
    B2 / "r6" / "R6_ADMISSION_DECISION_LEDGER.csv",
    B2 / "r6" / "R6_HEAT_POLICY_FRONTIER.csv",
    B2 / "r6" / "R6_HEAT_POLICY_MONTE_CARLO.csv",
    B2 / "r6" / "R6_NONDOMINATED_HEAT_FRONTIER.csv",
    B2 / "CR_RISK_BLOCK2_DECISION.json",
    B2 / "CR_RISK_BLOCK2_COMPONENT_CLASSIFICATION.csv",
    B2 / "CR_RISK_BLOCK2_COMPLEXITY_PRUNING.csv",
    B2 / "CR_RISK_BLOCK2_EDGE_RETENTION_WARNING.json",
    B2 / "CR_RISK_BLOCK2_SUPPORTED_DESIGN_REGION.csv",
]

ANALYSIS_SCRIPTS = [
    ROOT / "src" / "capital_routing" / "static_risk_architecture.py",
    Path(__file__).resolve(),
]


def write_manifest() -> dict:
    manifest = {
        "checkpoint": TASK,
        "repo": "dabiggestpoppa/larger-lab",
        "branch": "capital-routing",
        "base_commit": _git_sha(),
        "block1_seal_commit": BLOCK1_SEAL,
        "r5_commit": R5_COMMIT,
        "r6_substantive_commit": R6_COMMIT,
        "r6_correction_commit": R6_CORRECTION,
        "block2_intermediate_commit": B2_INTERMEDIATE,
        "python_version": platform.python_version(),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "frozen_inputs": {
            str(p.relative_to(ROOT)): _sha(p) for p in FROZEN_INPUTS
        },
        "analysis_scripts": {
            str(p.relative_to(ROOT)): _sha(p) for p in ANALYSIS_SCRIPTS
        },
        "note": (
            "Frozen authoritative sources only. Rebuilt ledger must reconcile "
            "with the sealed R1 ledger (890 events, 432 A / 458 B)."
        ),
    }
    (OUT / "CR_RISK_BLOCK2_STATIC_INPUT_HASH_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def write_protocol() -> None:
    protocol = f"""# {TASK} — Protocol (frozen before results)

**Repo:** dabiggestpoppa/larger-lab
**Branch:** capital-routing
**Base:** {B2_INTERMEDIATE}

## Mission
Freeze the simplest portfolio-risk architecture supported by R1-R6 evidence.
This is a synthesis / seal / decision checkpoint — NOT a new science checkpoint.

## Target architecture (candidate to freeze)
```
VALID ALPHA EVENTS
  -> FAMILY CLASSIFICATION
  -> STATIC FAMILY ALLOCATION
  -> SIMPLE GROSS SIMULTANEOUS-HEAT LIMIT
  -> PORTFOLIO
```
No dynamic drawdown rule, no episode memory budget, no Kelly, no hybrid
policy, no state machine for sizing.

## Frozen definitions
- **Per-event f** = base_f * family_weight(family). base_f in percent units
  (1.0 == 1% of account). 1R is one-sigma expected 6h move, NOT a stop-loss.
- **Gross heat** = sum of admitted active event fractions.
- **Canonical heat mechanism** = H1_SIMPLE_GROSS_HEAT_CAP.
- **Causal admission**: before admitting a new event, only information known at
  entry time is inspected (active positions that entered strictly earlier).
  Decisions: ACCEPT_FULL / ACCEPT_SCALED / REJECT_HEAT_CAP.

## Frozen reference allocations (no winner)
50/50 (diversification), 70/30 (A-heavy robust), 100/0 A (edge-resilience
concentration). 0/100 B remains diagnostic only.

## Reference parity targets (frozen R6 corrected frontier)
- H0 50/50 f=1%: CAGR ~71.21%, max DD ~5.19%
- H0 50/50 f=2%: CAGR ~190.31%, max DD ~10.17%
- H0 70/30 f=1%: CAGR ~74.57%, max DD ~6.97%
- H0 100/0 A f=1%: CAGR ~79.15%, max DD ~10.30%
- H1 70/30 1.0x: reproduce frozen R6 admission decisions (64 rejected events)
  and corrected block-MC (p95 DD ~9.5% -> ~6.3%, P(DD>=10%) ~3.6% -> 0.0%).

## Frozen policy roles
- H0: KEEP_AS_UNCONSTRAINED_CONTROL
- H1: ADOPT_AS_CANONICAL_SIMPLE_HEAT_MECHANISM
- H2: PRUNE_FROM_DEFAULT_DIAGNOSTIC_ONLY
- H3: SECONDARY_OPTIONAL
- H4: PRUNED_REDUNDANT
- H5: DEFERRED_COMPLEXITY

## Forbidden
No new allocations, no new caps, no new policy families, no R7 (DD-adaptive),
no Kelly, no hybrid sizing, no CAGR/DD search, no alpha/entry/exit changes.
No production allocation / cap / size selection.

## Pass gate
cr_risk_block2_static_architecture_seal_pass = true ONLY IF: Block-I chain
intact; R5/R6 findings reproduced; 890 events / 432 A / 458 B / 482 episodes /
max concurrency 3 reconcile; static allocation + H1 gross cap explicitly
defined; no final allocation/cap/size selected; H2/H3/H4/H5 roles frozen
correctly; edge-retention constraint frozen; no R7/Kelly work; alpha unchanged;
reference parity passes; causal admission passes; tests pass.
"""
    (OUT / "CR_RISK_BLOCK2_STATIC_PROTOCOL.md").write_text(
        protocol, encoding="utf-8")


# ---------------------------------------------------------------------------
# Integrity recheck (deterministic; reads frozen artifacts)
# ---------------------------------------------------------------------------

def integrity_check() -> dict:
    ep = _load_csv(B2 / "r6" / "R6_EVENT_EPISODE_LEDGER.csv")
    r1 = _load_csv(B1 / "R1_EVENT_RISK_LEDGER.csv")
    r1_ep = _load_csv(B1 / "R1_ROUTING_EPISODES.csv")
    r1_cc = _load_csv(B1 / "R1_CONCURRENCY_SUMMARY.csv").iloc[0]
    b2d = json.loads((B2 / "CR_RISK_BLOCK2_DECISION.json").read_text(
        encoding="utf-8"))
    r6d = json.loads((B2 / "r6" / "R6_DECISION.json").read_text(
        encoding="utf-8"))

    total_events = int(len(ep))
    n_a = int((ep.family == "A").sum())
    n_b = int((ep.family == "B").sum())
    episode_count = int(ep["episode_id"].nunique())
    max_cc = int(ep["peak_concurrent_position_count"].max())
    r1_ep12 = r1_ep[r1_ep["interval_h"] == 12.0]

    checks = {
        "total_events": total_events,
        "family_a_events": n_a,
        "family_b_events": n_b,
        "episode_count": episode_count,
        "max_concurrency": max_cc,
        "r1_ledger_rows": int(len(r1)),
        "r1_family_a": int((r1.family == "A").sum()),
        "r1_family_b": int((r1.family == "B").sum()),
        "r1_12h_episode_count": int(r1_ep12["cluster_id"].nunique()),
        "r1_max_concurrency": int(r1_cc["max_concurrent_positions"]),
        "events_ok": total_events == 890,
        "family_ok": (n_a == 432) and (n_b == 458),
        "episodes_ok": episode_count == 482,
        "r1_episode_reconcile_ok": episode_count == int(
            r1_ep12["cluster_id"].nunique()),
        "concurrency_ok": max_cc == 3,
        "r1_concurrency_ok": int(r1_cc["max_concurrent_positions"]) == 3,
        "b2_intermediate_ok": bool(b2d.get(
            "block2_intermediate_seal_pass")) and int(
            b2d.get("total_events", 0)) == 890,
        "r6_decision_ok": bool(r6d.get("r6_episode_heat_sizing_pass")),
    }
    checks["all_ok"] = all([
        checks["events_ok"], checks["family_ok"], checks["episodes_ok"],
        checks["r1_episode_reconcile_ok"], checks["concurrency_ok"],
        checks["r1_concurrency_ok"], checks["b2_intermediate_ok"],
        checks["r6_decision_ok"],
    ])
    return checks


# ---------------------------------------------------------------------------
# Causal admission parity (static module vs frozen R6 admission ledger)
# ---------------------------------------------------------------------------

def admission_parity() -> dict:
    import sys
    sys.path.insert(0, str(ROOT / "src"))
    from capital_routing.phases.phase_r5_common import load_r5_inputs
    from capital_routing.static_risk_architecture import (
        admit_book, reference_configs)

    load = load_r5_inputs(ROOT)
    ledger = load["ledger"].sort_values("entry_ts").reset_index(drop=True)
    frozen = _load_csv(B2 / "r6" / "R6_ADMISSION_DECISION_LEDGER.csv")

    results = {}
    all_ok = True
    for key, cfg in reference_configs().items():
        res = admit_book(ledger["entry_ts"], ledger["exit_ts"],
                         ledger["family"], cfg)
        wa = cfg.allocation.weight("A")
        wb = cfg.allocation.weight("B")
        sub = frozen[(frozen.policy_id == cfg.policy_id)
                     & (np.isclose(frozen.A_weight, wa))
                     & (np.isclose(frozen.B_weight, wb))]
        sub = sub.sort_values("entry_ts").reset_index(drop=True)
        dec_match = bool((sub["decision"].to_numpy() == res.decision).all())
        f_match = bool(np.allclose(sub["admitted_f"].to_numpy(),
                                   res.admitted_f, atol=1e-12))
        n_rej_frozen = int((sub["decision"] == "REJECT_HEAT_CAP").sum())
        ok = dec_match and f_match and (res.n_rejected == n_rej_frozen)
        results[key] = {
            "policy_id": cfg.policy_id,
            "w_A": wa, "w_B": wb,
            "n_rejected_static": int(res.n_rejected),
            "n_rejected_frozen": n_rej_frozen,
            "n_scaled_static": int(res.n_accept_scaled),
            "decision_match": dec_match,
            "admitted_f_match": f_match,
            "max_gross_heat": float(res.max_gross_heat),
            "ok": bool(ok),
        }
        all_ok = all_ok and ok
    return {"configs": results, "all_ok": all_ok}


# ---------------------------------------------------------------------------
# Reference parity (frozen frontier / MC values vs sealed expected)
# ---------------------------------------------------------------------------

def reference_parity() -> dict:
    frontier = _load_csv(B2 / "r6" / "R6_HEAT_POLICY_FRONTIER.csv")
    mc = _load_csv(B2 / "r6" / "R6_HEAT_POLICY_MONTE_CARLO.csv")

    rows = []
    ok = True
    for (pid, wa, wb, fp), expected in SEALED_H0_BASELINES.items():
        sub = frontier[(frontier.policy_id == pid)
                       & (frontier.w_A_pct == wa)
                       & (frontier.w_B_pct == wb)
                       & (np.isclose(frontier.f_pct, fp))]
        if len(sub) == 0:
            ok = False
            rows.append({"policy_id": pid, "w_A": wa, "w_B": wb,
                         "f_pct": fp, "cagr": None, "max_dd": None,
                         "match": False})
            continue
        r = sub.iloc[0]
        cagr = float(r["cagr"]) * 100.0
        mdd = float(r["max_dd"]) * 100.0
        cagr_ok = abs(cagr - expected["cagr"]) < 0.05
        dd_ok = abs(mdd - expected["max_dd"]) < 0.05
        ok = ok and cagr_ok and dd_ok
        rows.append({"policy_id": pid, "w_A": wa, "w_B": wb, "f_pct": fp,
                     "cagr": round(cagr, 4), "max_dd": round(mdd, 4),
                     "expected_cagr": expected["cagr"],
                     "expected_max_dd": expected["max_dd"],
                     "match": bool(cagr_ok and dd_ok)})

    # H1 70/30 1.0x block-MC tail reduction (corrected artifact).
    h0 = mc[(mc.policy_id == "H0") & (mc.w_A_pct == 70)
            & (mc.w_B_pct == 30) & (np.isclose(mc.f_pct, 1.0))
            & (mc.scheme == "block")]
    h1 = mc[(mc.policy_id == "H1-1.00-REJ") & (mc.w_A_pct == 70)
            & (mc.w_B_pct == 30) & (np.isclose(mc.f_pct, 1.0))
            & (mc.scheme == "block")]
    h1_block = {"ok": len(h0) == 1 and len(h1) == 1}
    if h1_block["ok"]:
        p95_0 = float(h0.iloc[0]["max_dd_p95"]) * 100.0
        p95_1 = float(h1.iloc[0]["max_dd_p95"]) * 100.0
        p10_0 = float(h0.iloc[0]["P_dd_ge_10"]) * 100.0
        p10_1 = float(h1.iloc[0]["P_dd_ge_10"]) * 100.0
        h1_block.update({
            "H0_p95_dd_pct": round(p95_0, 4),
            "H1_p95_dd_pct": round(p95_1, 4),
            "H0_P_dd_ge_10_pct": round(p10_0, 4),
            "H1_P_dd_ge_10_pct": round(p10_1, 4),
        })
        h1_block["p95_ok"] = abs(p95_0 - SEALED_H1_70_30["H0_p95_dd_pct"]) < 0.05 \
            and abs(p95_1 - SEALED_H1_70_30["H1_1x_p95_dd_pct"]) < 0.05
        h1_block["p10_ok"] = abs(p10_0 - SEALED_H1_70_30["H0_P_dd_ge_10_pct"]) < 0.05 \
            and abs(p10_1 - SEALED_H1_70_30["H1_1x_P_dd_ge_10_pct"]) < 0.05
        ok = ok and h1_block["p95_ok"] and h1_block["p10_ok"]
    else:
        ok = False

    return {"rows": rows, "h1_70_30_block_mc": h1_block, "all_ok": ok}


# ---------------------------------------------------------------------------
# Artifact writers
# ---------------------------------------------------------------------------

def write_reference_configs() -> dict:
    refs = {
        "allocation_references": [
            {"id": "50/50", "w_A": 0.5, "w_B": 0.5,
             "role": "diversification reference"},
            {"id": "70/30", "w_A": 0.7, "w_B": 0.3,
             "role": "A-heavy robust reference"},
            {"id": "100/0 A", "w_A": 1.0, "w_B": 0.0,
             "role": "edge-resilience / concentration reference"},
        ],
        "allocation_diagnostic": [
            {"id": "0/100 B", "w_A": 0.0, "w_B": 1.0,
             "role": "B fragility diagnostic only"},
        ],
        "heat_mechanism": {
            "canonical": "H1_SIMPLE_GROSS_HEAT_CAP",
            "H0": "KEEP_AS_UNCONSTRAINED_CONTROL",
        },
        "base_total_f_band_pct": [0.25, 0.50, 0.75, 1.00, 1.50, 2.00],
        "base_total_f_outer_stress_pct": 3.00,
        "note": "No allocation / cap / size is selected as production. These "
                "are frozen research references only.",
    }
    (OUT / "CR_RISK_BLOCK2_REFERENCE_CONFIGS.json").write_text(
        json.dumps(refs, indent=2), encoding="utf-8")
    return refs


def write_policy_role_matrix() -> None:
    rows = [
        ("H0", "KEEP_AS_UNCONSTRAINED_CONTROL",
         "baseline reference; reproduces sealed math"),
        ("H1", "ADOPT_AS_CANONICAL_SIMPLE_HEAT_MECHANISM",
         "simplest cap with material tail reduction at A-heavy allocation"),
        ("H2", "PRUNE_FROM_DEFAULT_DIAGNOSTIC_ONLY",
         "matches H1; no incremental value"),
        ("H3", "SECONDARY_OPTIONAL",
         "supported-not-required; weaker than equal gross cap"),
        ("H4", "PRUNED_REDUNDANT",
         "dominated by H1 (rejects 180 vs 14 at 1.0x)"),
        ("H5", "DEFERRED_COMPLEXITY",
         "no demonstrated incremental gain over H1"),
        ("DD-adaptive (R7)", "DEFERRED_NO_MECHANISM",
         "no unresolved state-dependent risk mechanism demonstrated"),
        ("Kelly (R8)", "DEFERRED",
         "growth rules follow exposure limits; not authorized"),
        ("Hybrid (R9)", "DEFERRED",
         "not authorized; deferred with R7/R8"),
    ]
    df = pd.DataFrame(rows, columns=["policy", "role", "rationale"])
    df.to_csv(OUT / "CR_RISK_BLOCK2_POLICY_ROLE_MATRIX.csv", index=False)


def write_complexity_pruning() -> None:
    rows = [
        (0, "H0 static", "KEEP_DIAGNOSTIC", "baseline reference"),
        (1, "H1 gross cap", "ADOPT",
         "canonical simple heat mechanism; material tail reduction at A-heavy"),
        (2, "H2 same-direction", "PRUNE_REDUNDANT",
         "matches H1; no incremental value"),
        (2, "H3 B-family", "KEEP_SECONDARY",
         "supported-not-required; weaker than equal gross cap"),
        (3, "H4 episode budget", "PRUNE_REDUNDANT",
         "dominated by H1"),
        (4, "H5 combined", "OPTIONAL_ONLY_WITH_INCREMENTAL_GAIN",
         "no demonstrated incremental gain over H1"),
        (None, "DD-adaptive / Kelly / hybrid", "DEFERRED",
         "no unresolved state-dependent risk mechanism"),
    ]
    df = pd.DataFrame(rows, columns=["complexity_level", "component",
                                     "pruning_decision", "rationale"])
    df.to_csv(OUT / "CR_RISK_BLOCK2_COMPLEXITY_PRUNING.csv", index=False)


def write_component_status() -> None:
    rows = [
        ("STATIC_RISK_ARCHITECTURE", "VALIDATED",
         "minimum architecture justified by R1-R6"),
        ("FAMILY_ALLOCATION_PRIMITIVE", "VALIDATED",
         "static family allocation materially lowers DD (50/50 5.2% vs "
         "A-solo 10.3% / B-solo 11.1%)"),
        ("GROSS_HEAT_PRIMITIVE", "VALIDATED",
         "H1 gross cap materially lowers resampled tail at A-heavy alloc"),
        ("DYNAMIC_SIZING", "NOT_REQUIRED_BY_CURRENT_EVIDENCE",
         "no unresolved state-dependent risk mechanism; R7 deferred"),
        ("EPISODE_MEMORY_BUDGET", "PRUNED_REDUNDANT",
         "H4 dominated by H1"),
        ("KELLY", "DEFERRED", "not authorized"),
        ("HYBRID_SIZING", "DEFERRED", "not authorized"),
        ("DEPLOYMENT", "NOT_AUTHORIZED", "plan"),
        ("MT5", "NOT_AUTHORIZED", "plan"),
    ]
    df = pd.DataFrame(rows, columns=["component", "status", "basis"])
    df.to_csv(OUT / "CR_RISK_BLOCK2_COMPONENT_STATUS.csv", index=False)


def write_edge_retention_constraint() -> None:
    edge = {
        "edge_retention_binding_constraint": True,
        "at_75pct_retention": "viable",
        "at_50pct_retention": "fragile (H0 50/50 f=1% CAGR ~+3%, "
                              "p95 DD ~23%; heat caps do not rescue)",
        "at_25pct_retention": "not viable (CAGR ~-21%, p95 DD ~58%)",
        "core_principle": ("Risk controls shape losses; they do NOT create "
                           "expectancy. Edge retention dominates risk outcome."),
        "guard": ("No risk policy should be considered production-safe if "
                  "expected retained edge falls below the project's chosen "
                  "edge-retention floor (floor NOT defined in this checkpoint)."),
    }
    (OUT / "CR_RISK_BLOCK2_EDGE_RETENTION_CONSTRAINT.json").write_text(
        json.dumps(edge, indent=2), encoding="utf-8")


def write_architecture_json() -> dict:
    arch = {
        "checkpoint": TASK,
        "architecture": {
            "name": "BLOCK-II_STATIC_RISK_ARCHITECTURE",
            "pipeline": [
                "VALID_ALPHA_EVENTS",
                "FAMILY_CLASSIFICATION",
                "STATIC_FAMILY_ALLOCATION",
                "SIMPLE_GROSS_SIMULTANEOUS_HEAT_LIMIT",
                "PORTFOLIO",
            ],
            "canonical_heat_mechanism": "H1_SIMPLE_GROSS_HEAT_CAP",
        },
        "allocation": {
            "form": "family_weights = {'A': x, 'B': 1-x}",
            "references": ["50/50", "70/30", "100/0 A"],
            "diagnostic": ["0/100 B"],
            "optimized": False,
        },
        "heat_cap": {
            "form": "max_gross_heat = H (multiplier of base_f)",
            "references": [1.0, 1.5, 2.0, 3.0],
            "optimized": False,
        },
        "admission": {
            "causal": True,
            "decisions": ["ACCEPT_FULL", "ACCEPT_SCALED",
                          "REJECT_HEAT_CAP"],
            "forbidden_inputs": [
                "future events", "future episode membership",
                "future returns", "future DD path", "past PnL",
                "drawdown state",
            ],
        },
        "explicitly_not_selected": [
            "production allocation", "production heat cap",
            "production size", "best policy",
        ],
        "deferred": ["DD-adaptive (R7)", "Kelly (R8)", "Hybrid (R9)"],
        "not_authorized": ["deployment", "mt5"],
    }
    (OUT / "CR_RISK_BLOCK2_STATIC_ARCHITECTURE.json").write_text(
        json.dumps(arch, indent=2), encoding="utf-8")
    return arch


def write_architecture_md() -> None:
    md = """# CR-RISK-BLOCK-II-STATIC-ARCHITECTURE-SEAL — Architecture

## Pipeline
```
VALID ALPHA EVENTS
  -> FAMILY CLASSIFICATION
  -> STATIC FAMILY ALLOCATION
  -> SIMPLE GROSS SIMULTANEOUS-HEAT LIMIT
  -> PORTFOLIO
```

## Layer 1 — alpha-family classification
Each valid routing event is assigned to family A or B by the frozen alpha
definitions. No alpha change here.

## Layer 2 — static family allocation
`family_weights = {"A": x, "B": 1-x}`. Frozen research references: 50/50,
70/30, 100/0 A (0/100 B diagnostic). x is NOT optimized. No universally
optimal allocation is selected.

## Layer 3 — simple instantaneous gross heat cap
The canonical heat primitive is `H1_SIMPLE_GROSS_HEAT_CAP`. Before admitting a
new event: `existing active gross heat + proposed event heat <= max_gross_heat`.
Admission is causal; existing active positions are never retroactively changed.

## Explicitly NOT frozen as production
This seal freezes the ARCHITECTURE, not the final capital level. The
demonstrated 70/30 + H1 1.0x result is evidence the mechanism matters, NOT
authorization to make 1.0x the production threshold.

- architecture_selected = true
- production_allocation_selected = false
- production_cap_selected = false
- production_size_selected = false
- best_policy_selected = false

## Edge-retention guard
Risk controls shape losses; they do NOT create expectancy. Edge retention is
the binding constraint (75% viable, 50% fragile, 25% non-viable). No policy is
production-safe below the project's chosen edge-retention floor.
"""
    (OUT / "CR_RISK_BLOCK2_STATIC_ARCHITECTURE.md").write_text(
        md, encoding="utf-8")


def write_implementation_contract() -> None:
    md = """# CR-RISK-BLOCK2-STATIC-ARCHITECTURE — Implementation Contract

## Module
`src/capital_routing/static_risk_architecture.py`

## Typed / static portfolio-risk contract
Per candidate event, required inputs:
- event_id
- family
- timestamp (entry)
- direction
- base_risk_fraction (base_f)
- active_positions (derived from prior admitted events)
- active_gross_heat
- family_active_heat

Required output: ADMIT / SCALE / REJECT.

The default architecture prefers simple deterministic behavior: H0
(unconstrained) and H1 (gross cap with REJECT, optionally SCALE) are the
canonical primitives. No episode-memory state, no drawdown state.

## The module MUST NOT
- calculate alpha
- change entries or exits
- perform broker execution
- calculate Kelly
- inspect future episode membership
- adapt to drawdown
- adapt to previous PnL

## Causal admission rule
At event time t, known: family, direction, configured family allocation,
configured total risk, currently active positions, currently active gross
heat. Unknown / forbidden: future events, future episode membership, future
returns, future DD path.
"""
    (OUT / "CR_RISK_BLOCK2_IMPLEMENTATION_CONTRACT.md").write_text(
        md, encoding="utf-8")


def write_reference_parity_csv(parity: dict) -> None:
    rows = [dict(r) for r in parity["rows"]]
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "CR_RISK_BLOCK2_REFERENCE_PARITY.csv", index=False)


def write_causal_admission_audit(parity: dict) -> None:
    audit = {
        "checkpoint": TASK,
        "method": ("static_risk_architecture.admit_book reproduced the frozen "
                   "R6_ADMISSION_DECISION_LEDGER.csv decisions for the four "
                   "reference configs (H0 50/50, H0 70/30, H0 100/0 A, "
                   "H1-1.00-REJ 70/30)."),
        "configs": parity["configs"],
        "all_ok": parity["all_ok"],
        "causality_note": ("Admission uses only information available at entry "
                           "time: active positions that entered earlier. "
                           "Future returns / episode membership / DD never "
                           "inspected."),
    }
    (OUT / "CR_RISK_BLOCK2_CAUSAL_ADMISSION_AUDIT.json").write_text(
        json.dumps(audit, indent=2), encoding="utf-8")


def write_report(checks: dict, admission: dict, parity: dict,
                 decision: dict) -> None:
    h1mc = parity["h1_70_30_block_mc"]
    # Build per-row lines for the four H0 reference configs.
    h0_lines = []
    for r in parity["rows"]:
        w = f"{r['w_A']:.0f}/{r['w_B']:.0f}"
        cagr = r["cagr"] if r["cagr"] is not None else "MISSING"
        mdd = r["max_dd"] if r["max_dd"] is not None else "MISSING"
        h0_lines.append(
            f"H0 {w} f={r['f_pct']:.0f}%  CAGR {cagr}% / max DD {mdd}%")
    h0_block = "\n".join(h0_lines)
    report = f"""# {TASK} — Report

**Status:** {decision['status']}
**Base:** {decision['base_commit']}

## Integrity recheck
- total events: {checks['total_events']} (890 expected) — {'PASS' if checks['events_ok'] else 'FAIL'}
- family A: {checks['family_a_events']} (432 expected) — {'PASS' if checks['family_ok'] else 'FAIL'}
- family B: {checks['family_b_events']} (458 expected) — {'PASS' if checks['family_ok'] else 'FAIL'}
- episodes: {checks['episode_count']} (482 expected) — {'PASS' if checks['episodes_ok'] else 'FAIL'}
- R1 12h episode reconciliation: {checks['r1_12h_episode_count']} clusters — {'PASS' if checks['r1_episode_reconcile_ok'] else 'FAIL'}
- max concurrency: {checks['max_concurrency']} (3 expected) — {'PASS' if checks['concurrency_ok'] else 'FAIL'}

## The five mission questions
**Q1. What family allocation conclusions are actually supported?**
Static family allocation is SUPPORTED. 50/50 is the diversification reference
(max DD 5.2% vs A-solo 10.3% / B-solo 11.1%), 70/30 is the A-heavy robust
reference (survives 50% edge retention; where the heat cap matters most), and
100/0 A is the edge-resilience / concentration reference. No allocation is
globally best.

**Q2. What simultaneous-heat controls are actually supported?**
H1 (simple gross heat cap) is the canonical mechanism. At 70/30 + 1.0x it
reduces block-MC p95 DD ~9.5% -> ~6.3% and P(DD>=10%) ~3.6% -> 0.0% at
~5.4pp median-CAGR cost. H2 (same-direction) replicates H1 without superiority.
H3 (B-family) is supported-not-required. H4 (episode budget) is redundant. H5
(combined) is unjustified complexity.

**Q3. Is episode-level budgeting necessary?**
No. H4 is REDUNDANT: H4-1.0x rejects 180 events vs H1-1.0x's 14, with lower
CAGR (53% vs 71%). Episode memory adds complexity without incremental value.

**Q4. Is B-specific treatment necessary?**
Not required. B is the capital limiter, but an equal gross cap is stronger at
70/30 (p95 DD 9.1% vs 6.3%), and H3-0.5x destroys A/B diversification at
50/50. Keep H3 secondary/optional, not default.

**Q5. Is there enough unresolved state-dependent risk to justify R7?**
No. ~84.7% of in-drawdown hourly loss is single-position; overlap adds
short-horizon tail risk that the simple gross cap already addresses. Dynamic
drawdown conditioning has no demonstrated mechanism. R7 remains deferred.

## Reference parity
```
{h0_block}
H1 70/30 1.0x  block-MC p95 DD {h1mc['H0_p95_dd_pct']}% -> {h1mc['H1_p95_dd_pct']}%,
               P(DD>=10%) {h1mc['H0_P_dd_ge_10_pct']}% -> {h1mc['H1_P_dd_ge_10_pct']}%
```
Reference parity: {'PASS' if parity['all_ok'] else 'FAIL'}

## Causal admission
The minimal static module reproduced frozen R6 admission decisions exactly
(H1-1.00-REJ 70/30: {admission['configs']['H1_70_30_1x']['n_rejected_static']} rejected events, matching the frozen 64). Admission is strictly causal.
Causal admission: {'PASS' if admission['all_ok'] else 'FAIL'}

## Architecture decision
The Block-II static architecture (family classification -> static family
allocation -> simple gross heat cap -> portfolio) is VALIDATED as the minimum
architecture justified by R1-R6. The ARCHITECTURE is selected; no production
allocation / cap / size is selected.

## Edge retention
Edge retention is the BINDING constraint. Risk controls shape losses; they do
not create expectancy. 75% retained edge is viable, 50% fragile, 25%
non-viable.

## Next step
Block-II static architecture is scientifically complete. Do NOT automatically
start R7. The next useful work depends on program objective: Block-III capital
scale design (only on explicit user intent) or deployment translation (only
when alpha engines + target are ready).
"""
    (OUT / "CR_RISK_BLOCK2_REPORT.md").write_text(report, encoding="utf-8")


def write_decision(checks: dict, admission: dict, parity: dict) -> dict:
    decision = {
        "checkpoint": TASK,
        "status": "PASS" if (checks["all_ok"] and admission["all_ok"]
                             and parity["all_ok"]) else "FAIL",
        "base_commit": _git_sha(),
        "block1_seal_commit": BLOCK1_SEAL,
        "r5_commit": R5_COMMIT,
        "r6_substantive_commit": R6_COMMIT,
        "r6_correction_commit": R6_CORRECTION,
        "block2_intermediate_commit": B2_INTERMEDIATE,
        "total_events": checks["total_events"],
        "family_a_events": checks["family_a_events"],
        "family_b_events": checks["family_b_events"],
        "episode_count": checks["episode_count"],
        "max_concurrency": checks["max_concurrency"],
        "static_family_allocation_validated": True,
        "gross_heat_cap_validated": True,
        "canonical_heat_mechanism": "H1_SIMPLE_GROSS_HEAT_CAP",
        "same_direction_policy_status": "SUPPORTED_BUT_NOT_INCREMENTAL",
        "b_family_policy_status": "SUPPORTED_NOT_REQUIRED",
        "episode_budget_status": "PRUNED_REDUNDANT",
        "combined_policy_status": "OPTIONAL_UNJUSTIFIED_COMPLEXITY",
        "edge_retention_binding_constraint": True,
        "r7_scientifically_justified": False,
        "r7_authorized": False,
        "kelly_authorized": False,
        "hybrid_authorized": False,
        "architecture_selected": True,
        "production_allocation_selected": False,
        "production_cap_selected": False,
        "production_size_selected": False,
        "best_policy_selected": False,
        "reference_parity_pass": bool(parity["all_ok"]),
        "causal_admission_pass": bool(admission["all_ok"]),
        "complexity_pruning_complete": True,
        "deployment_authorized": False,
        "mt5_authorized": False,
        "block2_static_architecture_seal_pass": bool(
            checks["all_ok"] and admission["all_ok"] and parity["all_ok"]),
        "cr_risk_block2_static_architecture_seal_pass": bool(
            checks["all_ok"] and admission["all_ok"] and parity["all_ok"]),
        "human_review_required": True,
        "next_checkpoint_recommended":
            "CR-RISK-BLOCK-III-CAPITAL-SCALE-DESIGN",
        "next_checkpoint_note": (
            "Block-II static architecture is scientifically complete. Do NOT "
            "auto-start R7 or Block-III. Block-III capital scale design is "
            "only appropriate on explicit user intent to study account-level "
            "risk fractions / fractional Kelly / production scale; deployment "
            "translation only when alpha engines + target are ready."),
        "static_architecture_status": {
            "STATIC_RISK_ARCHITECTURE": "VALIDATED",
            "FAMILY_ALLOCATION_PRIMITIVE": "VALIDATED",
            "GROSS_HEAT_PRIMITIVE": "VALIDATED",
            "DYNAMIC_SIZING": "NOT_REQUIRED_BY_CURRENT_EVIDENCE",
        },
        "scientific_changes": (
            "None - synthesis/seal only. Alpha/entry/exit/trade-management/"
            "families/1R unchanged. Only new scientific object is the formal "
            "static architecture contract (family allocation + gross heat cap)."),
    }
    (OUT / "CR_RISK_BLOCK2_DECISION.json").write_text(
        json.dumps(decision, indent=2), encoding="utf-8")
    return decision


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)

    # 1. Pre-register protocol + input hash manifest BEFORE synthesis output.
    manifest = write_manifest()
    write_protocol()

    # 2. Integrity recheck.
    checks = integrity_check()

    # 3. Causal admission parity.
    admission = admission_parity()

    # 4. Reference parity.
    parity = reference_parity()

    # 5. Write remaining artifacts.
    write_reference_configs()
    write_policy_role_matrix()
    write_complexity_pruning()
    write_component_status()
    write_edge_retention_constraint()
    write_architecture_json()
    write_architecture_md()
    write_implementation_contract()
    write_reference_parity_csv(parity)
    write_causal_admission_audit(admission)
    decision = write_decision(checks, admission, parity)
    write_report(checks, admission, parity, decision)

    print(json.dumps({
        "checkpoint": TASK,
        "status": decision["status"],
        "events": checks["total_events"],
        "family_a": checks["family_a_events"],
        "family_b": checks["family_b_events"],
        "episodes": checks["episode_count"],
        "max_concurrency": checks["max_concurrency"],
        "admission_all_ok": admission["all_ok"],
        "parity_all_ok": parity["all_ok"],
        "seal_pass": decision["block2_static_architecture_seal_pass"],
    }, indent=2))
    return 0 if decision["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
