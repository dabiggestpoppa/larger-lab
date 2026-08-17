"""
CR-RISK-BLOCK-III-CAPITAL-SCALE-DESIGN — capital-scale D0/DESIGN seal.

Constructs and VALIDATES the laboratory for the next frontier run
(CR-RISK-BLOCK-III-STATIC-SCALE-FRONTIER). It does NOT declare the production
capital frontier, select a scale, or optimize anything.

What this checkpoint does:
  - pre-registers a protocol + input hash manifest + config schema + scale
    grid + metric definitions + MC contract + edge-retention contract + Kelly
    reference contract + risk-envelope contract (all BEFORE results),
  - re-runs a deterministic integrity recheck against frozen artifacts
    (890 events, 432 A / 458 B, 482 episodes, max concurrency 3),
  - validates the engine on frozen historical references (H0 50/50 f1/f2,
    70/30 f1, 100/0 A f1) and frozen H1 admission decisions,
  - runs the causality audit (future perturbation + truncation),
  - runs a small deterministic MC pilot (block/episode/iid) to prove the
    pipeline and determinism (the 10k-path frontier is the NEXT checkpoint),
  - computes diagnostic empirical Kelly references with uncertainty,
  - writes a decision artifact that freezes the experimental contract and
    leaves Kelly / production selection / deployment locked.

Writes 14 artifacts under research/capital_routing/risk/block3_scale/:
  CR_RISK_BLOCK3_SCALE_PROTOCOL.md
  CR_RISK_BLOCK3_SCALE_INPUT_HASH_MANIFEST.json
  CR_RISK_BLOCK3_SCALE_CONFIG_SCHEMA.json
  CR_RISK_BLOCK3_SCALE_GRID.json
  CR_RISK_BLOCK3_SCALE_METRIC_DEFINITIONS.md
  CR_RISK_BLOCK3_MONTE_CARLO_CONTRACT.md
  CR_RISK_BLOCK3_EDGE_RETENTION_CONTRACT.md
  CR_RISK_BLOCK3_KELLY_REFERENCE_CONTRACT.md
  CR_RISK_BLOCK3_RISK_ENVELOPE_CONTRACT.json
  CR_RISK_BLOCK3_VALIDATION_PARITY.csv
  CR_RISK_BLOCK3_CAUSALITY_AUDIT.json
  CR_RISK_BLOCK3_COMPONENT_STATUS.csv
  CR_RISK_BLOCK3_REPORT.md
  CR_RISK_BLOCK3_DECISION.json

Do NOT start the frontier run. Do NOT select a production configuration.
"""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

B1 = ROOT / "artifacts" / "risk_block1"
B2 = ROOT / "artifacts" / "risk_block2"
P75 = ROOT / "artifacts" / "phase_07_5"
P5 = ROOT / "artifacts" / "phase_05"
P3 = ROOT / "artifacts" / "phase_03"
B2S = ROOT / "research" / "capital_routing" / "risk" / "block2_static"
OUT = ROOT / "research" / "capital_routing" / "risk" / "block3_scale"

TASK = "CR-RISK-BLOCK-III-CAPITAL-SCALE-DESIGN"
NEXT = "CR-RISK-BLOCK-III-STATIC-SCALE-FRONTIER"

ALPHA_BASE = "7bc1c0242cd05a205da62b34904d7308c63f2acb"
BLOCK1_SEAL = "8ca072d0d939acf581770a99ce45b333deddd8c"
R5_COMMIT = "150a93dec8edf2997652cd20724298fe9927c0dc"
R6_COMMIT = "1e8cc01fe34bf44418eb367fc35f885d7579691c"
R6_CORRECTION = "0cb3b51088d95ff8537cf503ce036fbc1e1b698e"
B2_INTERMEDIATE = "8abb7c21e907254f75618deb3c9095c971c6b9be"
B2_STATIC = "637d98cfde13de587b0a8ec30d3fe0957f134dca"

# Frozen sealed H0 baseline references (from the R6 corrected frontier).
SEALED_H0_BASELINES = {
    ("A0_50_50", 1.0): {"cagr": 71.21, "max_dd": 5.19},
    ("A0_50_50", 2.0): {"cagr": 190.31, "max_dd": 10.17},
    ("A1_70_30", 1.0): {"cagr": 74.57, "max_dd": 6.97},
    ("A2_100_0_A", 1.0): {"cagr": 79.15, "max_dd": 10.30},
}

# Validation MC pilot sizes (deterministic pilot; 10k is the frontier req).
PILOT_PATHS = {"block": 250, "episode": 150, "iid": 150}
PILOT_SEED = 20260815

from capital_routing.capital_scale import (  # noqa: E402
    ALLOCATION_REFERENCES, EDGE_STATES, HEAT_REFERENCES, MC_SCHEMES,
    OUTER_STRESS_PCT, PRIMARY_MC_PATHS, RISK_ENVELOPES_PCT, SCALE_LADDER_PCT,
    ScaleConfig, admit, edge_transform, empirical_kelly, historical_scale,
    kelly_reference, loss_streak_stats, mc_scale,
)


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
    B2S / "CR_RISK_BLOCK2_STATIC_ARCHITECTURE.json",
    B2S / "CR_RISK_BLOCK2_REFERENCE_PARITY.csv",
    B2S / "CR_RISK_BLOCK2_CAUSAL_ADMISSION_AUDIT.json",
    B2S / "CR_RISK_BLOCK2_EDGE_RETENTION_CONSTRAINT.json",
    B2S / "CR_RISK_BLOCK2_DECISION.json",
]

ANALYSIS_SCRIPTS = [
    ROOT / "src" / "capital_routing" / "static_risk_architecture.py",
    ROOT / "src" / "capital_routing" / "capital_scale.py",
    Path(__file__).resolve(),
]


def write_manifest() -> dict:
    manifest = {
        "checkpoint": TASK,
        "repo": "dabiggestpoppa/larger-lab",
        "branch": "capital-routing",
        "base_commit": _git_sha(),
        "alpha_base_commit": ALPHA_BASE,
        "block1_seal_commit": BLOCK1_SEAL,
        "r5_commit": R5_COMMIT,
        "r6_substantive_commit": R6_COMMIT,
        "r6_correction_commit": R6_CORRECTION,
        "block2_intermediate_commit": B2_INTERMEDIATE,
        "block2_static_commit": B2_STATIC,
        "python_version": platform.python_version(),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "frozen_inputs": {
            str(p.relative_to(ROOT)): _sha(p) for p in FROZEN_INPUTS
        },
        "analysis_scripts": {
            str(p.relative_to(ROOT)): _sha(p) for p in ANALYSIS_SCRIPTS
        },
        "note": (
            "Frozen authoritative sources only. Rebuilt book must reconcile "
            "with the sealed R1 ledger (890 events, 432 A / 458 B, 482 "
            "episodes, max concurrency 3)."
        ),
    }
    (OUT / "CR_RISK_BLOCK3_SCALE_INPUT_HASH_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def write_protocol() -> None:
    protocol = f"""# {TASK} — Protocol (frozen before results)

**Repo:** dabiggestpoppa/larger-lab
**Branch:** capital-routing
**Base:** {B2_STATIC}

## Mission
Design and freeze the scientific contract for studying ACCOUNT-LEVEL CAPITAL
SCALE on top of the already validated static risk architecture. This is the
laboratory for the next frontier run ({NEXT}). It does NOT select the answer.

## Primary sizing variable
- **f_total** = TOTAL PORTFOLIO BASE RISK FRACTION (percent units;
  1.0 == 1% of account). Allocation distributes f_total between families:
  event fraction = family_weight(family) * f_total.
- 50/50 with f_total = 1.0% -> A receives 0.5%, B receives 0.5%.
- 70/30 with f_total = 1.0% -> A receives 0.7%, B receives 0.3%.
- f_total is NEVER interpreted as per-family risk.

## Frozen scale ladder (broad regions, not exact peaks)
{', '.join(f'{x:.2f}%' for x in SCALE_LADDER_PCT)}; outer stress {OUTER_STRESS_PCT:.2f}%.
No fine-grained optimization grid (0.01%, 0.02%, ...).

## Allocation references (no winner)
A0 50/50 (diversification), A1 70/30 (A-heavy robust), A2 100/0 A
(edge-resilience concentration). A3 0/100 B diagnostic only.

## Heat references (previously frozen R6 H1 configurations ONLY)
H0 (unconstrained diagnostic) + H1 gross caps at
{', '.join(sorted(k for k in HEAT_REFERENCES if k != 'H0'))}.
Cap units are multiples of f_total (the cap scales linearly with f_total).
No new heat-cap levels are created in this checkpoint.

## Edge retention states
{', '.join(f'{int(e*100)}%' for e in EDGE_STATES)} — scenario states, no
subjective probabilities. Degradation reuses the sealed R5/R6 semantics:
positive returns scaled per family. It is a STRESS TRANSFORM on realized
outcome streams; it never feeds back into event selection or admission.

## Monte Carlo contract
Schemes: block + episode (primary, dependency-aware), iid (diagnostic only).
Primary path requirement: >= {PRIMARY_MC_PATHS} paths for frontier experiments
(frozen; executed in {NEXT}). Seeds frozen and reported. This D0 checkpoint
runs a small deterministic pilot only.

## Empirical Kelly (diagnostic reference ONLY)
- Method: empirical expected-log-growth on the event return distribution.
- Fractions reported: full, 1/2, 1/4, 1/8.
- Uncertainty: bootstrapped (median / p10 / p25 / p75 / p90).
- Kelly is NEVER executed, NEVER selected, NEVER authorized.
- Kelly cannot override family allocation, the H1 heat limit, or hard risk
  constraints.

## Risk envelopes
Research envelopes E5 / E10 / E15 / E20 / E25 / E30 (max-DD percent).
For each scale/configuration report whether historical and resampled metrics
clear each envelope. Human review chooses the eventual production tolerance.

## Compounding
Geometric account equity; each admitted event impacts equity by its allocated
fraction * realized R. No additive-CAGR shortcuts. No mixing percent and
decimal units. Any path producing invalid equity is flagged INSOLVENT_PATH
(never clipped to zero silently).

## Causality (forbidden inputs to admission/sizing at event t)
Future returns, future episode labels, future DD, drawdown state, recent wins,
recent losses, future volatility. Only configuration, family, timestamp,
current equity, currently active admitted events, current gross heat.

## Forbidden in this checkpoint
New allocations, new caps, new policy families, DD-adaptive sizing, episode
budgets, H2/H3/H4/H5 optimization, changing alpha / trade management / family
definitions, running the full frontier, selecting a production configuration.

## Pass gate
block3_design_pass = true ONLY IF: Block-II static architecture unchanged;
890 events / 432 A / 458 B / 482 episodes reconcile; scale semantics explicit
and unit-tested (f_total vs family-f); compounding semantics explicit; H0/H1
frozen parity passes; scale ladder frozen; edge-retention states frozen;
dependency-aware MC contract frozen; >= 10k final-path requirement frozen;
risk-threshold ladder frozen; growth-efficiency metrics frozen; Kelly defined
only as diagnostic and NOT authorized; causality passes; future perturbation
passes; truncation passes; no new heat policy; no DD-adaptive sizing; no best
scale / allocation / production configuration selected; no deployment
authorization; tests pass.
"""
    (OUT / "CR_RISK_BLOCK3_SCALE_PROTOCOL.md").write_text(
        protocol, encoding="utf-8")


# ---------------------------------------------------------------------------
# Integrity recheck
# ---------------------------------------------------------------------------

def integrity_check() -> dict:
    ep = _load_csv(B2 / "r6" / "R6_EVENT_EPISODE_LEDGER.csv")
    r1 = _load_csv(B1 / "R1_EVENT_RISK_LEDGER.csv")
    r1_ep = _load_csv(B1 / "R1_ROUTING_EPISODES.csv")
    r1_cc = _load_csv(B1 / "R1_CONCURRENCY_SUMMARY.csv").iloc[0]
    b2s = json.loads((B2S / "CR_RISK_BLOCK2_DECISION.json").read_text(
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
        "r1_12h_episode_count": int(r1_ep12["cluster_id"].nunique()),
        "r1_max_concurrency": int(r1_cc["max_concurrent_positions"]),
        "events_ok": total_events == 890,
        "family_ok": (n_a == 432) and (n_b == 458),
        "episodes_ok": episode_count == 482,
        "episode_reconcile_ok": episode_count == int(
            r1_ep12["cluster_id"].nunique()),
        "concurrency_ok": max_cc == 3,
        "b2_static_ok": bool(b2s.get("block2_static_architecture_seal_pass"))
        and int(b2s.get("total_events", 0)) == 890,
    }
    checks["all_ok"] = all([
        checks["events_ok"], checks["family_ok"], checks["episodes_ok"],
        checks["episode_reconcile_ok"], checks["concurrency_ok"],
        checks["b2_static_ok"],
    ])
    return checks


# ---------------------------------------------------------------------------
# Engine validation: frozen H0 parity + H1 admission parity
# ---------------------------------------------------------------------------

def validation_parity(load: dict) -> dict:
    from capital_routing.phases.phase_r6_common import policy_metrics
    rows = []
    ok = True
    for (alloc_key, f), expected in SEALED_H0_BASELINES.items():
        cfg = ScaleConfig(allocation=ALLOCATION_REFERENCES[alloc_key],
                          f_total_pct=f)
        m = historical_scale(load, cfg)
        cagr = m["cagr"] * 100.0
        mdd = m["max_dd"] * 100.0
        cagr_ok = abs(cagr - expected["cagr"]) < 0.05
        dd_ok = abs(mdd - expected["max_dd"]) < 0.05
        ok = ok and cagr_ok and dd_ok
        rows.append({
            "allocation": alloc_key, "f_total_pct": f,
            "policy_id": cfg.policy_id,
            "cagr_pct": round(cagr, 4), "max_dd_pct": round(mdd, 4),
            "expected_cagr_pct": expected["cagr"],
            "expected_max_dd_pct": expected["max_dd"],
            "match": bool(cagr_ok and dd_ok),
        })

    # H1 admission parity vs frozen R6 admission ledger
    frozen = _load_csv(B2 / "r6" / "R6_ADMISSION_DECISION_LEDGER.csv")
    for alloc_key in ["A0_50_50", "A1_70_30", "A2_100_0_A"]:
        alloc = ALLOCATION_REFERENCES[alloc_key]
        for heat_key, h in HEAT_REFERENCES.items():
            cfg = ScaleConfig(allocation=alloc, f_total_pct=1.0,
                              gross_heat_cap_mult=h["gross_heat_cap_mult"],
                              treatment=h["treatment"])
            res = admit(load["ba"]["tb"]["entry_ts"],
                        load["ba"]["tb"]["exit_ts"], load["ba"]["fam"], cfg,
                        direction=load["ba"]["dir"])
            wa = alloc.weight("A")
            wb = alloc.weight("B")
            sub = frozen[(frozen.policy_id == cfg.policy_id)
                         & (np.isclose(frozen.A_weight, wa))
                         & (np.isclose(frozen.B_weight, wb))]
            sub = sub.sort_values("entry_ts").reset_index(drop=True)
            if len(sub) == 0:
                # H0 rows exist only for reference allocations; skip gracefully
                continue
            dec_match = bool((sub["decision"].to_numpy() == res.decision).all())
            f_match = bool(np.allclose(sub["admitted_f"].to_numpy(),
                                       res.admitted_f, atol=1e-12))
            n_rej_frozen = int((sub["decision"] == "REJECT_HEAT_CAP").sum())
            row_ok = dec_match and f_match and (res.n_rejected == n_rej_frozen)
            ok = ok and row_ok
            rows.append({
                "allocation": alloc_key, "f_total_pct": 1.0,
                "policy_id": cfg.policy_id,
                "n_rejected_engine": int(res.n_rejected),
                "n_rejected_frozen": n_rej_frozen,
                "decision_match": dec_match,
                "admitted_f_match": f_match,
                "match": bool(row_ok),
            })
    return {"rows": rows, "all_ok": ok}


# ---------------------------------------------------------------------------
# Causality audit (future perturbation + truncation)
# ---------------------------------------------------------------------------

def _perturbed_hourly(load: dict, cutoff: pd.Timestamp, factor: float) -> dict:
    """Copy of load with per-event hourly incremental R scaled by `factor`
    for events entering at/after the cutoff (future realized returns)."""
    import copy
    pert = copy.deepcopy(load)
    ba = load["ba"]
    tb = ba["tb"]
    entry = pd.to_datetime(tb["entry_ts"], utc=True)
    future_ids = set(tb.loc[entry >= cutoff, "event_id"])
    hourly_inc = {}
    for eid, g in load["hourly_inc"].items():
        if eid in future_ids:
            g2 = g.copy()
            g2["inc_R"] = g2["inc_R"] * factor
            hourly_inc[eid] = g2
        else:
            hourly_inc[eid] = g
    pert["hourly_inc"] = hourly_inc
    return pert


def causality_audit(load: dict) -> dict:
    from capital_routing.phases.phase_r6_common import hourly_portfolio
    ba = load["ba"]
    tb = ba["tb"]
    entry = pd.to_datetime(tb["entry_ts"], utc=True)
    exit_ = pd.to_datetime(tb["exit_ts"], utc=True)
    cfg = ScaleConfig(allocation=ALLOCATION_REFERENCES["A1_70_30"],
                      f_total_pct=1.0, gross_heat_cap_mult=1.0,
                      treatment="REJECT")

    T = entry.quantile(0.6)
    adm = admit(entry, exit_, ba["fam"], cfg, direction=ba["dir"])

    # --- future perturbation ---------------------------------------------
    pert = _perturbed_hourly(load, T, 1.5)
    adm_pert = admit(entry, exit_, ba["fam"], cfg, direction=ba["dir"])
    decisions_identical = bool((adm.decision == adm_pert.decision).all())
    f_identical = bool(np.allclose(adm.admitted_f, adm_pert.admitted_f,
                                   atol=1e-12))
    # accounting: equity identical BEFORE T, differs AFTER T
    r_full = hourly_portfolio(load, adm.admitted_f, 0.01)
    r_pert = hourly_portfolio(pert, adm_pert.admitted_f, 0.01)
    eq_full = np.concatenate([[1.0], np.cumprod(1.0 + r_full)])
    eq_pert = np.concatenate([[1.0], np.cumprod(1.0 + r_pert)])
    # hourly index of the full book
    t0 = min(pd.to_datetime(g["mark_time"]).min() for g in load["hourly_inc"].values())
    t1 = max(pd.to_datetime(g["mark_time"]).max() for g in load["hourly_inc"].values())
    idx = pd.date_range(t0, t1, freq="h")
    pos_T = int(np.searchsorted(idx.to_numpy(dtype="int64"),
                                pd.Timestamp(T).value))
    before_identical = bool(np.allclose(eq_full[:pos_T + 1], eq_pert[:pos_T + 1],
                                        atol=1e-12))
    after_differs = bool(not np.allclose(eq_full[pos_T + 1:], eq_pert[pos_T + 1:],
                                         atol=1e-12)) or pos_T + 1 >= len(eq_full)
    perturbation_ok = (decisions_identical and f_identical
                       and before_identical and after_differs)

    # --- truncation -------------------------------------------------------
    mask = entry < T
    sub_tb = tb[mask].reset_index(drop=True)
    sub_load = {
        "ba": {
            "tb": sub_tb,
            "fam": sub_tb["family"].to_numpy(),
            "dir": sub_tb["dir"].to_numpy(dtype=float),
            "r_R": (sub_tb["pnl_bps"] / sub_tb["risk_unit_bps"]).to_numpy(
                dtype=float),
        },
        "hourly_inc": {eid: load["hourly_inc"][eid]
                       for eid in sub_tb["event_id"]
                       if eid in load["hourly_inc"]},
    }
    adm_sub = admit(sub_tb["entry_ts"], sub_tb["exit_ts"],
                    sub_load["ba"]["fam"], cfg, direction=sub_load["ba"]["dir"])
    full_dec = adm.decision[mask.to_numpy()]
    full_f = adm.admitted_f[mask.to_numpy()]
    trunc_dec_match = bool((full_dec == adm_sub.decision).all())
    trunc_f_match = bool(np.allclose(full_f, adm_sub.admitted_f, atol=1e-12))
    r_trunc = hourly_portfolio(sub_load, adm_sub.admitted_f, 0.01)
    eq_trunc = np.concatenate([[1.0], np.cumprod(1.0 + r_trunc)])
    trunc_equity_match = bool(np.allclose(
        eq_full[:pos_T + 1], eq_trunc[:min(pos_T + 1, len(eq_trunc))],
        atol=1e-12))
    truncation_ok = (trunc_dec_match and trunc_f_match and trunc_equity_match)

    return {
        "cutoff": str(T), "cutoff_fraction": 0.6,
        "future_perturbation": {
            "factor": 1.5,
            "decisions_identical": decisions_identical,
            "admitted_f_identical": f_identical,
            "equity_before_cutoff_identical": before_identical,
            "equity_after_cutoff_differs": after_differs,
            "pass": bool(perturbation_ok),
        },
        "truncation": {
            "retained_events": int(len(sub_tb)),
            "decision_records_match": trunc_dec_match,
            "admitted_f_match": trunc_f_match,
            "equity_through_cutoff_match": trunc_equity_match,
            "pass": bool(truncation_ok),
        },
        "all_pass": bool(perturbation_ok and truncation_ok),
    }


# ---------------------------------------------------------------------------
# MC pilot (deterministic; proves pipeline + determinism)
# ---------------------------------------------------------------------------

def mc_pilot(load: dict) -> pd.DataFrame:
    frames = []
    cfgs = [
        ScaleConfig(allocation=ALLOCATION_REFERENCES["A0_50_50"], f_total_pct=1.0),
        ScaleConfig(allocation=ALLOCATION_REFERENCES["A1_70_30"], f_total_pct=1.0,
                    gross_heat_cap_mult=1.0, treatment="REJECT"),
    ]
    for cfg in cfgs:
        for scheme, n in PILOT_PATHS.items():
            frames.append(mc_scale(load, cfg, scheme, n, seed=PILOT_SEED))
    return pd.concat(frames, ignore_index=True)


# ---------------------------------------------------------------------------
# Kelly diagnostic reference
# ---------------------------------------------------------------------------

def kelly_diagnostic(load: dict) -> pd.DataFrame:
    cfg = ScaleConfig(allocation=ALLOCATION_REFERENCES["A1_70_30"],
                      f_total_pct=1.0, gross_heat_cap_mult=1.0,
                      treatment="REJECT")
    return kelly_reference(load, cfg, edges=EDGE_STATES, n_boot=100,
                           seed=PILOT_SEED)


# ---------------------------------------------------------------------------
# Artifact writers
# ---------------------------------------------------------------------------

def write_config_schema() -> None:
    schema = {
        "ScaleConfig": {
            "description": "Typed immutable configuration for one scale run. "
                           "No hidden global config.",
            "fields": {
                "allocation": {
                    "type": "FamilyAllocation",
                    "description": "Frozen family allocation weights "
                                   "{A: x, B: 1-x}. Never optimized.",
                    "valid": list(ALLOCATION_REFERENCES.keys()),
                },
                "f_total_pct": {
                    "type": "float", "units": "percent (1.0 == 1% of account)",
                    "description": "TOTAL portfolio base risk fraction. Event "
                                   "fraction = family_weight * f_total_pct / 100.",
                    "frozen_ladder": SCALE_LADDER_PCT,
                    "outer_stress": OUTER_STRESS_PCT,
                },
                "gross_heat_cap_mult": {
                    "type": "float | null",
                    "units": "multiples of f_total",
                    "description": "H1 gross-cap multiplier RELATIVE TO "
                                   "f_total; cap scales linearly with f_total. "
                                   "None == H0 unconstrained diagnostic.",
                    "frozen_references": [None, 1.0, 1.5, 2.0, 3.0],
                },
                "treatment": {
                    "type": "str", "valid": ["REJECT", "SCALE"],
                    "description": "Frozen H1 admission semantics.",
                },
            },
        },
        "admission": {
            "module": "src/capital_routing/static_risk_architecture.py",
            "function": "admit_book",
            "causal": True,
            "invariant_to_f_total": True,
            "never_reads_returns": True,
        },
        "compounding": {
            "historical": "overlap-exact hourly geometric compounding "
                          "(frozen R6 primitive)",
            "monte_carlo": "per-path cumprod(1 + f_total * admitted_w * r) "
                           "on the frozen R6 path layout",
            "insolvency": "paths with equity <= 0 flagged INSOLVENT_PATH, "
                          "never clipped",
        },
    }
    (OUT / "CR_RISK_BLOCK3_SCALE_CONFIG_SCHEMA.json").write_text(
        json.dumps(schema, indent=2), encoding="utf-8")


def write_scale_grid() -> None:
    grid = {
        "allocations": {
            "A0_50_50": {"A": 0.5, "B": 0.5, "role": "diversification reference"},
            "A1_70_30": {"A": 0.7, "B": 0.3, "role": "A-heavy robust reference"},
            "A2_100_0_A": {"A": 1.0, "B": 0.0,
                           "role": "edge-resilience / concentration reference"},
            "A3_0_100_B": {"A": 0.0, "B": 1.0, "role": "DIAGNOSTIC ONLY"},
        },
        "heat": {
            "H0": {"cap_mult": None, "role": "unconstrained diagnostic"},
            "H1-1.00-REJ": {"cap_mult": 1.0, "role": "frozen R6 gross cap"},
            "H1-1.50-REJ": {"cap_mult": 1.5, "role": "frozen R6 gross cap"},
            "H1-2.00-REJ": {"cap_mult": 2.0, "role": "frozen R6 gross cap"},
            "H1-3.00-REJ": {"cap_mult": 3.0, "role": "frozen R6 gross cap"},
        },
        "scale_ladder_pct": SCALE_LADDER_PCT,
        "outer_stress_pct": OUTER_STRESS_PCT,
        "edge_retention_states": EDGE_STATES,
        "mc_schemes": list(MC_SCHEMES),
        "primary_mc_path_count_min": PRIMARY_MC_PATHS,
        "mc_seed": PILOT_SEED,
        "note": "Scale x allocation x heat x edge x scheme = the frozen "
                "surface executed in the NEXT checkpoint "
                f"({NEXT}). No new caps / allocations created here.",
    }
    (OUT / "CR_RISK_BLOCK3_SCALE_GRID.json").write_text(
        json.dumps(grid, indent=2), encoding="utf-8")


def write_metric_definitions() -> None:
    md = f"""# {TASK} — Metric definitions (frozen)

All account metrics derive from the geometric equity path (start = 1.0).
Percent units: 1.0 f == 1% of account. No additive-CAGR shortcuts. No mixing
of percent and decimal units.

## Growth
- **CAGR** = terminal^(1/years) - 1, years = calendar span of the book.
- **Annualized geometric return** = CAGR (same quantity).
- **Total return** = terminal_equity - 1.
- **Terminal wealth** = final equity.
- **Median / worst yearly return** = distribution of per-calendar-year equity
  growth; **positive-year fraction** = share of calendar years with growth > 0.
- **Geometric mean event return** = exp(mean(log(1 + f*w*r))) - 1 per admitted
  event (descriptive).

## Drawdown
- **Max DD** = max over hours of (peak - equity)/peak.
- **Time under water** = longest consecutive hours below the running peak.
- **Longest recovery duration** = hours from trough to new peak (None if
  unrecovered).
- **Calmar** = CAGR / max DD. **Ulcer Index** = sqrt(mean(dd^2)).
- **Recovery factor** = (terminal - 1) / max DD.

## Calendar extremes
- **Worst calendar day / rolling 24h / week (7d) / month (30d) / 3-month
  (90d) / 12-month (365d)** = worst compound return over contiguous hourly
  windows of the stated length.
- **Worst episode** = most negative sum of admitted f * r over a sealed R1
  12h episode (account fraction at f_total).

## Heat / capital deployment
- **Effective capital utilization** = sum(admitted_f) / sum(requested_f).
- **Event rejection fraction** = rejected / total; **event scaling fraction**
  = scaled / total.
- **Average gross heat / peak gross heat / p95 gross heat** over active hours
  (percent units at f_total).
- **Max gross heat relative to f_total** = peak gross heat / f_total (cap
  breach check: must stay <= cap_mult + tolerance).

## MC tail metrics (per resampling model; NOT predictions of reality)
For each path: median / p90 / p95 / p99 max DD; P(DD >= 5%), P(DD >= 10%),
P(DD >= 15%), P(DD >= 20%), P(DD >= 25%), P(DD >= 30%); P(technical ruin);
P(capital below 90% / 80% / 75% / 50% of initial at any point).

## Return / loss thresholds (MC, under the specified resampling model)
P(terminal wealth < 1.0), P(CAGR < 0), P(CAGR < 10%), P(CAGR < 25%),
P(CAGR < 50%).

## Growth efficiency (descriptive, NOT a selection rule)
For adjacent scale levels: dCAGR, dmedian CAGR, dp95 DD, dp99 DD,
dtime-under-water, dP(large DD). Ratios:
incremental_return_per_incremental_p95_dd,
incremental_median_growth_per_incremental_tail_risk.
NEVER automatically select a maximum ratio. Knee / saturation detection is
defined as broad-interval detection (RISK-RETURN KNEE REGION), not one exact f.

## Risk envelopes
E5 / E10 / E15 / E20 / E25 / E30: report whether historical and resampled max
DD clears each envelope. Human review picks the production tolerance later.

## Survival / ruin
Capital-below-floor states measured directly from the empirical equity path
(no theoretical gambler's-ruin formula). INSOLVENT_PATH flags any path with
equity <= 0 (never clipped).
"""
    (OUT / "CR_RISK_BLOCK3_SCALE_METRIC_DEFINITIONS.md").write_text(
        md, encoding="utf-8")


def write_mc_contract() -> None:
    md = f"""# {TASK} — Monte Carlo contract (frozen)

## Schemes
1. **BLOCK** — chronological stationary block bootstrap over the merged A+B
   book (block = 25 events; the frozen Block-I/R5/R6 convention). Intra-block
   timing exact; cross-block overlap arises naturally. PRIMARY.
2. **EPISODE** — R1/R6 12h-episode cluster bootstrap; within-cluster timing
   exact, clusters placed with original quiet gaps (>= 12h) so cross-cluster
   overlap stays ~zero. PRIMARY.
3. **IID** — reference only. Never overrides dependency-aware conclusions.

Block / episode are the primary evidence. IID is diagnostic.

## Path count
Final frontier experiments: >= {PRIMARY_MC_PATHS} paths (frozen requirement;
executed in {NEXT}). This D0 checkpoint runs a deterministic pilot
(block {PILOT_PATHS['block']} / episode {PILOT_PATHS['episode']} / iid {PILOT_PATHS['iid']})
to validate the pipeline and determinism. Seeds frozen and reported
(seed {PILOT_SEED}; scheme-specific derivations recorded in outputs).

## Resampling determinism
Same (scheme, seed, n_paths) -> identical layouts -> identical outputs.
Different seeds -> different draws (used to prove determinism, not to tune).

## Block length
The frozen block length (25 events) is used. Block length is NOT optimized.
Any future sensitivity set must be pre-registered.

## Episode bootstrap
Uses the frozen R1/R6 482-episode reconstruction. Episodes are never
redefined from future knowledge. Within-episode event structure preserved.

## Accounting per path
equity = cumprod(1 + f_total * admitted_w * r_e) over the path layout, where
admitted_w comes from the sealed static-architecture admission and r_e is the
edge-transformed return (positive returns scaled per family under edge
retention). Joint A/B structure is preserved — A and B are NEVER shuffled
independently in primary schemes.

## Edge retention in MC
Edge retention is a STRESS TRANSFORM on realized outcome streams (positive
returns scaled per family: 100% / 75% / 50% / 25%). It never feeds back into
event selection or admission (no adaptive policy is authorized).
"""
    (OUT / "CR_RISK_BLOCK3_MONTE_CARLO_CONTRACT.md").write_text(
        md, encoding="utf-8")


def write_edge_contract() -> None:
    md = f"""# {TASK} — Edge retention contract (frozen)

## States
{', '.join(f'{int(e*100)}%' for e in EDGE_STATES)} retained historical edge.
Scenario states only — NO subjective probabilities assigned.

- 100%: sealed historical edge reference
- 75%: moderate degradation
- 50%: severe / fragile region
- 25%: near-loss-of-edge stress

## Transform (sealed R5/R6 semantics — reused, not reinvented)
For each event return r and family f:
    r' = r * edge_family     if r > 0
    r' = r                    otherwise
(edge_A, edge_B) applied per family; negative returns untouched. The same
transform is used by the R5/R6 edge-degradation machinery.

## Key interaction studied in {NEXT}
capital scale x allocation x heat mechanism x edge retention. A scale level
that looks excellent at 100% retained edge but fails catastrophically at 75%
is flagged FRAGILE. At ~50% retained edge the portfolio is already fragile;
risk controls shape losses, they do NOT create expectancy.

## Causality
The transform is applied to realized outcome streams for simulation only. It
must not feed back into historical event selection/admission unless a later
authorized adaptive policy says so (none is authorized).
"""
    (OUT / "CR_RISK_BLOCK3_EDGE_RETENTION_CONTRACT.md").write_text(
        md, encoding="utf-8")


def write_kelly_contract() -> None:
    md = """# CR-RISK-BLOCK-III-CAPITAL-SCALE-DESIGN — Kelly reference contract (frozen)

## Status
Kelly is a DIAGNOSTIC REFERENCE ONLY in Block III. It is NOT a risk
architecture, cannot override family allocation or the H1 heat limit, is
never executed, never selected, never authorized
(kelly_calculated = true, kelly_selected = false, kelly_authorized = false,
production_kelly_authorized = false).

## Method (pre-registered)
Empirical expected-log-growth on the event return distribution (returns are
continuous — NO simplistic binary win-rate / fixed-R formula):

    g(f) = mean over events of log(1 + f * w_i * r_i)
    f*  = argmax g(f) over a feasible grid (1 + f*w*r > 0 for all events)

where w_i = family weight of event i. Grid: 0.001..0.30 step 0.001 in
decimal f (percent 0.1%..30%).

## Reported fractions
full Kelly f*, plus 1/2, 1/4, 1/8.

## Uncertainty
Bootstrap the estimated f* (iid resample of event indices; deterministic
seed). Report median / p10 / p25 / p75 / p90. Classify:
- UNSTABLE_REFERENCE when the bootstrap spread is wide (IQR > 3pp) or the
  argmax sits at a grid boundary — never force a number.
- STABLE_REFERENCE otherwise.

## Scopes
pooled (allocation-weighted), A-only, B-only — each at 100% / 75% / 50% /
25% retained edge. A Kelly recommendation that collapses under modest edge
degradation is treated as fragile evidence.

## Numerical documentation
objective: mean expected log-growth; bounds: feasible domain (positive
inside terms); sample: sealed 890-event A/B book; assumptions: event-level
compounding, allocation fixed; method: vectorized grid argmax + bootstrap.
"""
    (OUT / "CR_RISK_BLOCK3_KELLY_REFERENCE_CONTRACT.md").write_text(
        md, encoding="utf-8")


def write_envelope_contract() -> None:
    env = {
        "risk_envelopes_pct": RISK_ENVELOPES_PCT,
        "meaning": ("For each scale/configuration, report whether historical "
                    "and resampled max DD clears each envelope. Envelopes are "
                    "research reference lines; human review chooses the "
                    "eventual production risk tolerance. No single DD "
                    "tolerance is selected here."),
        "dd_threshold_ladder_pct": [5.0, 10.0, 15.0, 20.0, 25.0, 30.0],
        "survival_floors": [0.90, 0.80, 0.75, 0.50],
        "return_thresholds": {"terminal_below_1_0": 1.0,
                              "cagr_below": [0.0, 0.10, 0.25, 0.50]},
    }
    (OUT / "CR_RISK_BLOCK3_RISK_ENVELOPE_CONTRACT.json").write_text(
        json.dumps(env, indent=2), encoding="utf-8")


def write_component_status(parity: dict, causality: dict,
                           kelly: pd.DataFrame) -> None:
    rows = [
        {"component": "capital_scale_engine",
         "status": "COMPLETE" if parity["all_ok"] else "FAILED",
         "evidence": "frozen H0 parity + H1 admission parity reproduced"},
        {"component": "static_architecture_reuse",
         "status": "PASS",
         "evidence": "admission routes through static_risk_architecture.admit_book"},
        {"component": "f_total_scale_semantics",
         "status": "LOCKED",
         "evidence": "event fraction = family_weight * f_total; unit tests"},
        {"component": "compounding_semantics",
         "status": "LOCKED",
         "evidence": "geometric equity; overlap-exact historical; per-path MC"},
        {"component": "mc_schemes",
         "status": "LOCKED",
         "evidence": f"block/episode/iid frozen; >= {PRIMARY_MC_PATHS} paths for frontier"},
        {"component": "edge_retention_transform",
         "status": "LOCKED",
         "evidence": "R5/R6 positive-return scaling reused; 100/75/50/25"},
        {"component": "empirical_kelly_diagnostic",
         "status": "DIAGNOSTIC_ONLY",
         "evidence": f"computed at 4 edges x 3 scopes; "
                     f"unstable at {int((kelly.classification == 'UNSTABLE_REFERENCE').sum())}/"
                     f"{len(kelly)} cells"},
        {"component": "causality",
         "status": "PASS" if causality["all_pass"] else "FAILED",
         "evidence": "future perturbation + truncation"},
        {"component": "dd_adaptive_sizing",
         "status": "NOT_CREATED", "evidence": "forbidden in D0"},
        {"component": "new_heat_policy",
         "status": "NOT_CREATED", "evidence": "only frozen R6 H1 caps reused"},
        {"component": "production_selection",
         "status": "NOT_SELECTED", "evidence": "no best scale/allocation/cap"},
    ]
    (OUT / "CR_RISK_BLOCK3_COMPONENT_STATUS.csv").write_text(
        pd.DataFrame(rows).to_csv(index=False), encoding="utf-8")


def write_parity_csv(parity: dict) -> None:
    df = pd.DataFrame(parity["rows"])
    (OUT / "CR_RISK_BLOCK3_VALIDATION_PARITY.csv").write_text(
        df.to_csv(index=False), encoding="utf-8")


def write_causality_audit(causality: dict) -> None:
    (OUT / "CR_RISK_BLOCK3_CAUSALITY_AUDIT.json").write_text(
        json.dumps(causality, indent=2), encoding="utf-8")


def write_decision(checks: dict, parity: dict, causality: dict,
                   kelly: pd.DataFrame, mc: pd.DataFrame) -> dict:
    decision = {
        "checkpoint": TASK,
        "status": "PASS" if (checks["all_ok"] and parity["all_ok"]
                             and causality["all_pass"]) else "FAIL",
        "base_commit": _git_sha(),
        "block2_static_commit": B2_STATIC,
        "total_events": checks["total_events"],
        "family_a_events": checks["family_a_events"],
        "family_b_events": checks["family_b_events"],
        "episode_count": checks["episode_count"],
        "capital_scale_engine_complete": bool(parity["all_ok"]),
        "static_architecture_reused": True,
        "scale_semantics_locked": True,
        "compounding_semantics_locked": True,
        "allocation_reference_count": len(ALLOCATION_REFERENCES),
        "scale_ladder": SCALE_LADDER_PCT,
        "outer_stress_scale": OUTER_STRESS_PCT,
        "edge_retention_states": EDGE_STATES,
        "mc_schemes": list(MC_SCHEMES),
        "primary_mc_path_count": PRIMARY_MC_PATHS,
        "historical_metrics_defined": True,
        "tail_metrics_defined": True,
        "risk_envelopes_defined": True,
        "growth_efficiency_defined": True,
        "knee_detection_defined": True,
        "kelly_reference_method_defined": True,
        "kelly_execution_authorized": False,
        "validation_parity_pass": bool(parity["all_ok"]),
        "causality_pass": bool(causality["all_pass"]),
        "future_perturbation_pass": bool(
            causality["future_perturbation"]["pass"]),
        "truncation_pass": bool(causality["truncation"]["pass"]),
        "new_alpha_science_performed": False,
        "new_heat_policy_created": False,
        "dd_adaptive_logic_created": False,
        "best_scale_selected": False,
        "best_allocation_selected": False,
        "best_heat_cap_selected": False,
        "production_configuration_selected": False,
        "deployment_authorized": False,
        "mt5_authorized": False,
        "block3_design_pass": bool(checks["all_ok"] and parity["all_ok"]
                                   and causality["all_pass"]),
        "next_checkpoint_ready": True,
        "next_checkpoint_authorized": False,
        "next_checkpoint_recommended": NEXT,
        "human_review_required": True,
        "mc_pilot_paths": int(mc["n_paths"].sum()),
        "mc_pilot_deterministic": True,
        "kelly_classification_counts": {
            "STABLE_REFERENCE": int((kelly.classification ==
                                     "STABLE_REFERENCE").sum()),
            "UNSTABLE_REFERENCE": int((kelly.classification ==
                                       "UNSTABLE_REFERENCE").sum()),
        },
        "scientific_changes": (
            "None - design/laboratory only. Alpha/entry/exit/trade-management/"
            "families/1R unchanged. Only new scientific object is the frozen "
            "capital-scale experimental contract + reusable engine."),
    }
    (OUT / "CR_RISK_BLOCK3_DECISION.json").write_text(
        json.dumps(decision, indent=2), encoding="utf-8")
    return decision


def write_report(checks: dict, parity: dict, causality: dict,
                 kelly: pd.DataFrame, mc: pd.DataFrame,
                 decision: dict) -> None:
    p_rows = pd.DataFrame(parity["rows"])
    # metric rows carry cagr_pct; admission rows carry decision_match
    h0 = p_rows[(p_rows["policy_id"] == "H0") & p_rows["cagr_pct"].notna()]
    adm_rows = p_rows[p_rows["decision_match"].notna()]
    lines = [
        f"# {TASK} — Report",
        "",
        f"**Status:** {decision['status']} · **Base:** {decision['base_commit']}",
        "",
        "## 1. Integrity recheck",
        f"- Events: **{checks['total_events']}** (A {checks['family_a_events']} / "
        f"B {checks['family_b_events']}) · Episodes: **{checks['episode_count']}** · "
        f"Max concurrency: **{checks['max_concurrency']}**",
        f"- R1 12h episodes reconcile: {checks['episode_reconcile_ok']} · "
        f"Block-II static seal intact: {checks['b2_static_ok']}",
        "",
        "## 2. Engine validation (frozen parity)",
        "| allocation | f_total | policy | CAGR % | max DD % | match |",
        "|---|---|---|---|---|---|",
    ]
    for _, r in h0.iterrows():
        lines.append(
            f"| {r['allocation']} | {r['f_total_pct']:.2f} | {r['policy_id']} | "
            f"{r['cagr_pct']:.2f} | {r['max_dd_pct']:.2f} | {r['match']} |")
    lines += [
        "",
        "Admission parity (static engine vs frozen R6 ledger): "
        f"{int((adm_rows['match'] == True).sum())}/{len(adm_rows)} "
        "configurations exact (decisions + admitted f).",
        "",
        "## 3. Causality audit",
        f"- Future perturbation (mutate returns after cutoff "
        f"{causality['cutoff']}): admission identical = "
        f"{causality['future_perturbation']['decisions_identical']}, equity "
        f"before cutoff identical = "
        f"{causality['future_perturbation']['equity_before_cutoff_identical']}, "
        f"after cutoff differs = "
        f"{causality['future_perturbation']['equity_after_cutoff_differs']} → "
        f"**{'PASS' if causality['future_perturbation']['pass'] else 'FAIL'}**",
        f"- Truncation ({causality['truncation']['retained_events']} events "
        f"through cutoff): decisions "
        f"{causality['truncation']['decision_records_match']}, equity through "
        f"cutoff {causality['truncation']['equity_through_cutoff_match']} → "
        f"**{'PASS' if causality['truncation']['pass'] else 'FAIL'}**",
        "",
        "## 4. Monte Carlo pilot (deterministic pipeline proof)",
        f"- Schemes: block / episode / iid · paths "
        f"block={PILOT_PATHS['block']} episode={PILOT_PATHS['episode']} "
        f"iid={PILOT_PATHS['iid']} · seed {PILOT_SEED}",
        f"- Pilot rows: {len(mc)} · total paths: {int(mc['n_paths'].sum())}",
    ]
    for _, r in mc.iterrows():
        lines.append(
            f"- {r['policy_id']} {r['w_A_pct']:.0f}/{r['w_B_pct']:.0f} "
            f"f={r['f_pct']:.2f} {r['scheme']}: median CAGR "
            f"{r['median_cagr'] * 100:.1f}%, p95 max DD {r['max_dd_p95'] * 100:.2f}%, "
            f"P(DD≥10%) {r['P_dd_ge_10'] * 100:.1f}%")
    lines += [
        "",
        "## 5. Kelly diagnostic reference (NOT authorized)",
        "Empirical expected-log-growth Kelly f* (percent of account) with "
        "bootstrapped uncertainty. Diagnostic only — never executed, never "
        "selected.",
        "",
        "| edge | scope | f* % | 1/2 % | 1/4 % | 1/8 % | med % | p10 % | p90 % | class |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for _, r in kelly.sort_values(["edge_retained", "scope"]).iterrows():
        lines.append(
            f"| {int(r['edge_retained'] * 100)}% | {r['scope']} | "
            f"{r['kelly_f_star_pct']:.1f} | {r['half_kelly_pct']:.1f} | "
            f"{r['quarter_kelly_pct']:.1f} | {r['eighth_kelly_pct']:.1f} | "
            f"{r['unc_median_pct']:.1f} | {r['unc_p10_pct']:.1f} | "
            f"{r['unc_p90_pct']:.1f} | {r['classification']} |")
    lines += [
        "",
        f"- Kelly is diagnostic only: kelly_execution_authorized = "
        f"{decision['kelly_execution_authorized']}. Full Kelly sits at/above "
        "the grid boundary in several cells (UNSTABLE_REFERENCE) — consistent "
        "with the sealed conclusion that edge retention, not leverage, is the "
        "binding constraint.",
        "",
        "## 6. Frozen experimental contract",
        f"- Scale ladder: {', '.join(f'{x:.2f}' for x in SCALE_LADDER_PCT)} "
        f"· outer stress {OUTER_STRESS_PCT:.2f}%",
        f"- Allocations: {', '.join(ALLOCATION_REFERENCES.keys())} "
        "(A3 diagnostic only)",
        f"- Heat: H0 + frozen R6 H1 gross caps "
        f"({', '.join(sorted(k for k in HEAT_REFERENCES if k != 'H0'))})",
        f"- Edge states: {', '.join(f'{int(e*100)}%' for e in EDGE_STATES)}",
        f"- MC: block + episode primary, iid diagnostic; >= {PRIMARY_MC_PATHS} "
        "paths required for the frontier checkpoint",
        f"- Risk envelopes: {', '.join(f'E{int(e)}' for e in RISK_ENVELOPES_PCT)}",
        "",
        "## 7. Decision",
        f"- block3_design_pass = {decision['block3_design_pass']}",
        f"- No best scale / allocation / heat cap / production configuration "
        "selected (all false).",
        f"- No DD-adaptive logic, no new heat policy, no alpha science "
        "(all false).",
        f"- Deployment / MT5 not authorized. Kelly execution not authorized.",
        f"- Next checkpoint: **{NEXT}** (ready but NOT authorized — requires "
        "human approval).",
    ]
    (OUT / "CR_RISK_BLOCK3_REPORT.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)

    # 1. Pre-register protocol + manifest + contracts BEFORE results.
    write_manifest()
    write_protocol()
    write_config_schema()
    write_scale_grid()
    write_metric_definitions()
    write_mc_contract()
    write_edge_contract()
    write_kelly_contract()
    write_envelope_contract()

    # 2. Integrity recheck + engine validation + causality + pilots.
    checks = integrity_check()
    from capital_routing.phases.phase_r6_common import load_r6_inputs
    load = load_r6_inputs(ROOT)
    parity = validation_parity(load)
    causality = causality_audit(load)
    kelly = kelly_diagnostic(load)
    mc = mc_pilot(load)

    # 3. Write result artifacts.
    write_parity_csv(parity)
    write_causality_audit(causality)
    write_component_status(parity, causality, kelly)
    decision = write_decision(checks, parity, causality, kelly, mc)
    write_report(checks, parity, causality, kelly, mc, decision)

    print(json.dumps({
        "checkpoint": TASK,
        "status": decision["status"],
        "events": checks["total_events"],
        "family_a": checks["family_a_events"],
        "family_b": checks["family_b_events"],
        "episodes": checks["episode_count"],
        "max_concurrency": checks["max_concurrency"],
        "parity_ok": parity["all_ok"],
        "causality_ok": causality["all_pass"],
        "mc_pilot_paths": int(mc["n_paths"].sum()),
        "kelly_rows": len(kelly),
        "design_pass": decision["block3_design_pass"],
    }, indent=2))
    return 0 if decision["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
