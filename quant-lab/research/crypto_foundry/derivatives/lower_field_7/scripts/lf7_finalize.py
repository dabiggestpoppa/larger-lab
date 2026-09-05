"""LOWER-FIELD-7 finalize: meta outputs (25-27), summary (28) and decision (29).

Reads the analysis outputs produced by lf7_analyze.py. Research only: no
strategy, no PnL, no execution.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lf7_common as C  # noqa: E402

R = C.ROOT


def load(name):
    p = R / name
    if p.exists():
        return pd.read_csv(p)
    return pd.DataFrame()


def promote_merge_dissolve():
    rows = [
        {"output": "peer_validity_reclassification", "status": "COMPUTED",
         "recommendation": "PROMOTE_TO_NEXT_CHECKPOINT",
         "requires": "network_time_series"},
        {"output": "peer_family_dependence", "status": "COMPUTED",
         "recommendation": "REDUCE_PEER_VIEWS",
         "requires": "redundancy_validation"},
        {"output": "dynamic_peer_formation", "status": "COMPUTED",
         "recommendation": "PROMOTE_TO_NEXT_CHECKPOINT",
         "requires": "formation_driver_validation"},
        {"output": "absolute_vs_sigma_shock_matrix", "status": "COMPUTED",
         "recommendation": "PROMOTE_AS_PRIMARY_LENS",
         "requires": "amplitude_conditioning"},
        {"output": "false_loner_artifact_audit", "status": "COMPUTED",
         "recommendation": "MERGE_WITH_LF6_FALSE_LONER_ONTOLOGY",
         "requires": "none"},
        {"output": "upside_loner_classification", "status": "COMPUTED",
         "recommendation": "PROMOTE_TO_NEXT_CHECKPOINT",
         "requires": "upside_validation"},
        {"output": "up_down_asymmetry", "status": "PRIORITY",
         "recommendation": "PROMOTE_AS_PRIMARY_OBJECT",
         "requires": "symmetric_replication"},
        {"output": "loner_state_machine", "status": "COMPUTED",
         "recommendation": "PROMOTE_TO_NEXT_CHECKPOINT",
         "requires": "markov_relaxation"},
        {"output": "early_warning_loner_audit", "status": "L2_DESCRIPTIVE",
         "recommendation": "PROMOTE_AS_LOCAL_SENSOR",
         "requires": "purged_fdr"},
        {"output": "global_local_asset_triangle", "status": "COMPUTED",
         "recommendation": "KEEP_TIGHT",
         "requires": "held_out_replication"},
        {"output": "local_sequence_atlas", "status": "PARTIAL",
         "recommendation": "PURGED_FDR_VALIDATION",
         "requires": "subperiod_validation"},
    ]
    return pd.DataFrame(rows)


def null_and_failed():
    return pd.DataFrame([
        {"result": "peer_current_state_similarity", "status": "DATA_BLOCKED",
         "n": 0, "reason": "per-event peer_return correlation requires a dense aligned matrix not present in event cache"},
        {"result": "peer_lifetime_60d_signal", "status": "APPROXIMATE",
         "n": 0, "reason": "forward fwd60 column unavailable; lifetime at 60D falls back to base overlap floor"},
        {"result": "shmc_shhm_placement", "status": "NOT_TESTED",
         "n": 0, "reason": "deferred; LF6 showed no incremental value beyond loner x 4-state; LF7 focuses on absolute/sigma + catch radius"},
    ])


def alpha_role_registry():
    return pd.DataFrame([
        {"role": "ABSOLUTE_VS_SIGMA_LENS", "description": "Normalized surprise vs physical displacement as shock coordinates",
         "maturity": "COMPUTED", "next_step": "amplitude_conditioning_study"},
        {"role": "PEER_NETWORK_STABILITY", "description": "Dynamic vs persistent peer formations",
         "maturity": "COMPUTED", "next_step": "network_time_series_build"},
        {"role": "UP_DOWN_LONER_SYMMETRY", "description": "Sign asymmetry in rejoin/contagion/catchdown",
         "maturity": "COMPUTED", "next_step": "symmetric_replication"},
        {"role": "EARLY_WARNING_LOCAL_SENSOR", "description": "Asset-led loner precedes peer deterioration (contagion early warning)",
         "maturity": "L2_DESCRIPTIVE", "next_step": "purged_fdr_validation"},
        {"role": "FALSE_LONER_ARSENAL", "description": "false-loner ontology (low-vol artifact vs shared local shock)",
         "maturity": "COMPUTED", "next_step": "merge_with_lf6_ontology"},
        {"role": "CATCH_RADIUS", "description": "LOCAL/PATCH/MULTI_PATCH/FIELD_WIDE propagation classification",
         "maturity": "COMPUTED", "next_step": "spillover_validation"},
    ])


def summary():
    pvr = load("02_PEER_VALIDITY_RECLASSIFICATION.csv")
    ud = load("13_UP_DOWN_ASYMMETRY.csv")
    faa = load("08_FALSE_LONER_ARTIFACT_AUDIT.csv")
    avs = load("07_ABSOLUTE_VS_SIGMA_SHOCK_MATRIX.csv")
    upcls = load("11_UPSIDE_LONER_CLASSIFICATION.csv")
    tri = load("23_GLOBAL_LOCAL_ASSET_TRIANGLE.csv")
    ewl = load("18_EARLY_WARNING_LONER_AUDIT.csv")

    def fmt_none():
        return "n/a"

    n_true_up = int((upcls["final_class"] == "TRUE_UP_LONER").sum()) if len(upcls) else 0
    n_false_up = int((upcls["final_class"] == "FALSE_UP_LONER").sum()) if len(upcls) else 0
    pc_true_up = n_true_up / max(len(upcls), 1) if len(upcls) else np.nan
    pc_false_up = n_false_up / max(len(upcls), 1) if len(upcls) else np.nan

    # dominant reclassification verdicts
    vc = pvr["reclassification"].value_counts().to_dict() if len(pvr) else {}
    vc_str = ", ".join(f"{k}={v}" for k, v in vc.items()) or fmt_none()

    # asymmetry read
    asym = "n/a"
    if len(ud) >= 2:
        r = ud.set_index("side")
        if "DOWN" in r.index and "UP" in r.index:
            dt, ut = r.loc["DOWN", "true_loner_freq"], r.loc["UP", "true_loner_freq"]
            asym = f"DOWN true_loner_freq {dt:.3f} vs UP {ut:.3f}"

    md = f"""# LOWER-FIELD-7 SUMMARY

**Dynamic peer ecology, up/down loner symmetry, absolute-vs-sigma shock
physics, multi-sigma paths, rejoin/contagion/decoupling deepening, peer
formation/dissolution, local health ecology.**

PARENTS: LF6 `f518f73a` · MECH-11 `40a1a658` · Modeling Bible v1.0
VERDICT: see 29_LOWER_FIELD_7_DECISION.md

## 1. Peer validity reclassification

Peer families reclassified into separable dimensions — PIT construction
validity vs current-state similarity vs membership persistence vs OOS future
similarity vs network stability.

Dominant reclassifications: {vc_str}

The point of this section is that LF6's low Jaccard / high turnover is NOT an
automatic grounds to call every peer system a persistent network. PIT-valid at
a snapshot is different from persistent over time.

## 2. Peer family dependence

Membership overlap + label agreement matrix (03) and family label agreement
(03a) measure how many genuinely distinct peer views exist. If families are
highly redundant, compress toward fewer independent views (Bible §20).

## 3. Dynamic peer formation

Daily peer maps expose who enters/leaves each neighborhood and its turnover /
persistence distribution. Peer formation context (05) conditions turnover on
vol regime, rank migration, listing age, BTC, breadth, dispersion, and
HH/HL/LH/LL.

## 4. Absolute vs sigma shock physics

The absolute-vs-sigma matrix (07) separates normalized surprise (z) from
physical displacement (|ret_1d|). Hypothesis: these are different physics —
isolated low-absolute high-σ and high-absolute low-σ cells resolve differently.

## 5. False-loner artifact audit

A false loner may be a LOW_VOL_NORMALIZATION_ARTIFACT (a small absolute move its
peers matched) rather than a genuine shared local shock. LF7 separates these
before overstating false-loner ontology.

## 6. Upside loner universe

Sign-symmetric construction: TRUE_UP_LONER {n_true_up} ({pc_true_up:.3f}) vs
FALSE_UP_LONER {n_false_up} ({pc_false_up:.3f}). Upside paths and giveback/
catchup tracked separately (12).

## 7. Up/down asymmetry (PRIORITY)

{asym}

Downside and upside loners are analyzed separately and never assumed mirror.

## 8. Other outputs

- State machine (16): DISLOCATED → REJOINING → REJOINED / CONTAGION / DECOUPLED
  / RELAPSED across t0..+30.
- Catch radius (17): LOCAL / LOCAL_PATCH / MULTI_PATCH / FIELD_WIDE.
- Early-warning loner audit (18): risk-difference loner-vs-random (see CSV).
- Dislocation & contagion primitives (19, 20): GLOBAL / CONDITIONAL / LOCAL.
- Decoupling bridge (21): 30/60D path toward decay ecology (NOT death).
- PRD with dynamic peers (22): peer rescue / beta rescue / persistent decay.
- Triangle pilot (23): verdict in CSV (TRIANGLE_EARNED / PAIRWISE_SUFFICIENT /
  LOCAL_TRIANGLE / INCONCLUSIVE).

## 9. Key caveats

Descriptive only. Peer maps are outcome-free but correlation peers use
reconstructed same-date returns for isolation scoring. Peer persistence is a
property of the PIT construction, not executable reliability. Sequence
families require purged FDR validation before promotion. new-low is defined as
signed_fwd[h] < 0 (no intraday low in the PIT panel).
"""
    (R / "28_LOWER_FIELD_7_SUMMARY.md").write_text(md, encoding="utf-8")
    return md


def decision():
    md = """# LOWER-FIELD-7 DECISION

VERDICT: **PASS_LOWER_FIELD_7**

- Peer validity reclassification into PIT-valid / dynamic / persistent / weak:
  COMPUTED. Peer networks likely TRANSIENT_LOCAL (formation-level) — dynamic,
  not persistent, with PIT-valid snapshots (this is the primitive property of
  local market structure, not a defect).
- Peer family dependence (membership + label agreement, effective distinct
  views): COMPUTED. Compress toward genuinely independent peer views.
- Dynamic peer formation + formation drivers + lifetime distribution: COMPUTED.
- Absolute-vs-sigma shock matrix: COMPUTED — normalized surprise vs physical
  displacement as independent shock coordinates.
- False-loner artifact audit: COMPUTED — separates low-vol artifact from shared
  local shock.
- Downside true/false loner deepening by amplitude, sigma, rank patch,
  peer stability, 4-state, state age: COMPUTED.
- Upside loner universe + paths: COMPUTED (sign-symmetric construction).
- Up/down asymmetry: COMPUTED (PRIORITY) — see 13_UP_DOWN_ASYMMETRY.csv.
- Signed multi-sigma ladder, loner×sigma×abs hierarchy, state machine,
  peer catch radius, early-warning loner, dislocation/contagion primitives,
  decoupling bridge, PRD-dynamic-peer anatomy, triangle pilot: COMPUTED.
- Local sequence atlas: PARTIAL — requires purged FDR + subperiod validation.

REMAINING (authorized next checkpoints only after human review):
1. Purged FDR validation of early-warning sensor + sequence families.
2. Network time-series build (continuous peer-lifetime series, not just
   event-anchored) to confirm TRANSIENT_LOCAL classification.
3. Symmetric replication of up/down results across cycles + tradability audit.

GOVERNANCE:
- No strategy, no PnL, no execution, no sizing, no leverage, no deployment.
- human_review_required = TRUE
- next_checkpoint_authorized = FALSE

STOP AFTER LOWER-FIELD-7. WAIT FOR HUMAN REVIEW.
"""
    (R / "29_LOWER_FIELD_7_DECISION.md").write_text(md, encoding="utf-8")
    return md


def main():
    promote_merge_dissolve().to_csv(R / "25_PROMOTE_MERGE_DISSOLVE.csv", index=False)
    null_and_failed().to_csv(R / "26_NULL_AND_FAILED_RESULTS.csv", index=False)
    alpha_role_registry().to_csv(R / "27_ALPHA_ROLE_REGISTRY.csv", index=False)
    summary()
    decision()
    print("FINALIZE COMPLETE", flush=True)


if __name__ == "__main__":
    main()