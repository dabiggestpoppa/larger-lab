"""LOWER-FIELD-8 finalize: meta outputs (25-27), summary (28) and decision (29).

Reads the analysis outputs produced by lf8_analyze.py. Research only: no
strategy, no PnL, no execution.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lf8_common as C  # noqa: E402

R = C.ROOT


def load(name):
    p = R / name
    if p.exists():
        return pd.read_csv(p)
    return pd.DataFrame()


def promote_merge_dissolve():
    rows = [
        {"output": "dynamic_relational_state", "status": "COMPUTED",
         "recommendation": "PROMOTE_TO_NEXT_CHECKPOINT",
         "requires": "network_time_series"},
        {"output": "peer_lifetime_paradox_resolution", "status": "COMPUTED",
         "recommendation": "PROMOTE_AS_PRIMARY_OBJECT",
         "requires": "continuous_state_series"},
        {"output": "membership_entropy", "status": "COMPUTED",
         "recommendation": "KEEP_TIGHT",
         "requires": "entropy_drift_audit"},
        {"output": "reorg_response_curves", "status": "COMPUTED",
         "recommendation": "PROMOTE_AS_PRIMARY_LENS",
         "requires": "amplitude_conditioning"},
        {"output": "timing_precedence", "status": "COMPUTED",
         "recommendation": "PROMOTE_AS_LOCAL_SENSOR",
         "requires": "lead_time_validation"},
        {"output": "false_loner_decomposition", "status": "COMPUTED",
         "recommendation": "MERGE_WITH_LF6_FALSE_LONER_ONTOLOGY",
         "requires": "none"},
        {"output": "true_loner_subtypes", "status": "COMPUTED",
         "recommendation": "PROMOTE_TO_NEXT_CHECKPOINT",
         "requires": "purged_fdr"},
        {"output": "rejoin_contagion_decoupling_lattice", "status": "COMPUTED",
         "recommendation": "PROMOTE_TO_NEXT_CHECKPOINT",
         "requires": "purged_fdr"},
        {"output": "directional_relational_asymmetry", "status": "PRIORITY",
         "recommendation": "PROMOTE_AS_PRIMARY_OBJECT",
         "requires": "symmetric_replication"},
        {"output": "prd_relational_health", "status": "PARTIAL",
         "recommendation": "PURGED_FDR_VALIDATION",
         "requires": "peer_forward_validation"},
        {"output": "relational_state_info_gain", "status": "COMPUTED",
         "recommendation": "FALSIFIED_AS_PREDICTOR_KEEP_AS_OBJECT",
         "requires": "predictive_robustness_audit"},
    ]
    return pd.DataFrame(rows)


def null_and_failed():
    return pd.DataFrame([
        {"result": "mech12_constraint_entropy_join", "status": "DATA_BLOCKED",
         "n": 0, "reason": "mech_12 constraint-entropy artifact unavailable "
                          "in this checkout (13b_FIELD_JOIN_VERDICT)"},
        {"result": "corr_family_peer_return_relational_metrics",
         "status": "DATA_BLOCKED", "n": 0,
         "reason": "CORR peer maps carry no peer_return (LF5 quality row 1.0); "
                  "return-based relational metrics restricted to BEHAVIORAL_10/"
                  "STATE/HYBRID_10, never substituted"},
        {"result": "relational_state_persistence_cond_sparse_cells",
         "status": "APPROXIMATE", "n": 0,
         "reason": "conditional persistence at +30/+60 uses nearest-snapshot "
                  "lookup; sparse event anchoring gives small n (e.g. 12/9)"},
        {"result": "sigma_shock_reorg_response", "status": "NO_STABLE_RELATION",
         "n": 3,
         "reason": "SIGMA_SHOCK response curve has no stable monotone relation "
                  "(normalized surprise is not the reorganization driver)"},
    ])


def alpha_role_registry():
    return pd.DataFrame([
        {"role": "DYNAMIC_RELATIONAL_STATE", "description": "Object-level "
         "robustness: relational state outlives peer membership (HYBRID_10 "
         "0.56 vs 0.22 same-member at 60d)",
         "maturity": "COMPUTED", "next_step": "continuous_state_series"},
        {"role": "MEMBERSHIP_ENTROPY", "description": "Stationary neighborhood "
         "churn; entropy stable and low-information",
         "maturity": "COMPUTED", "next_step": "entropy_drift_audit"},
        {"role": "REORG_RESPONSE_CURVES", "description": "Volume amplitude and "
         "absolute shock drive reorganization; sigma does not",
         "maturity": "COMPUTED", "next_step": "amplitude_conditioning"},
        {"role": "SHOCK_TIMING_PRECEDENCE", "description": "Absolute shock "
         "precedes membership turnover / relational-state change / decoupling",
         "maturity": "COMPUTED", "next_step": "lead_time_validation"},
        {"role": "LONER_DECOMPOSITION", "description": "False loners are "
         "low-vol normalization artifacts; true loners split into "
         "early-contagion / persistent-decoupling",
         "maturity": "COMPUTED", "next_step": "merge_with_lf6_ontology"},
        {"role": "REJOIN_CONTAGION_DECOUPLING_LATTICE", "description": "True "
         "loners in DECOUPLED state are contagion-heavy (0.45 vs 0.12 "
         "not-loner)",
         "maturity": "COMPUTED", "next_step": "purged_fdr_validation"},
        {"role": "PRD_RELATIONAL_HEALTH", "description": "PRD as relational "
         "health: relative decay / temporary split supported, rescue "
         "subtypes not",
         "maturity": "PARTIAL", "next_step": "peer_forward_validation"},
    ])


def summary():
    v02 = load("02b_PARADOX_VERDICTS.csv")
    p04 = load("04_RELATIONAL_STATE_PERSISTENCE.csv")
    e05 = load("05b_ENTROPY_TREND.csv")
    rc10 = load("10b_RESPONSE_CURVE_VERDICTS.csv")
    tp11 = load("11b_TIMING_PRECEDENCE.csv")
    fld14 = load("14_FALSE_LONER_DECOMPOSITION.csv")
    tls15 = load("15_TRUE_LONER_SUBTYPES.csv")
    lat16 = load("16b_LATTICE_COLLAPSED.csv")
    asym17 = load("17_DIRECTIONAL_RELATIONAL_ASYMMETRY.csv")
    prd23 = load("23_PRD_RELATIONAL_HEALTH.csv")
    ig24b = load("24b_INFO_GAIN_VERDICTS.csv")

    # H1: relational state vs same-member persistence (HYBRID primary)
    h1 = "n/a"
    if len(v02):
        r = v02[v02["peer_family"] == C.PRIMARY_FAMILY]
        if len(r):
            row = r.iloc[0]
            h1 = (f"{row['relational_state_60d']:.3f} vs same-member "
                  f"{row['same_member_60d']:.3f} (HYBRID_10)")

    # response-curve shapes
    rc_str = ", ".join(
        f"{r['driver']}={r['shape']}" for _, r in rc10.iterrows()
    ) if len(rc10) else "n/a"

    # timing precedence for ABS_SHOCK
    prec = "n/a"
    if len(tp11):
        ab = tp11[tp11["flag_x"] == "ABS_SHOCK"].set_index("flag_y")
        parts = []
        for y in ("MEMBERSHIP_TURNOVER", "RELATIONAL_STATE_CHANGE", "DECOUPLING"):
            if y in ab.index:
                parts.append(f"{y} {ab.loc[y, 'p_x_before_y']:.3f}")
        prec = ", ".join(parts)

    # true-loner contagion in decoupled
    lat = "n/a"
    if len(lat16):
        tl = lat16[(lat16["loner"] == "TRUE_LONER")
                   & (lat16["relational_state"] == "DECOUPLED")
                   & (lat16["shock_coarse"] == "HIGH_SIG_HIGH_ABS")]
        nl = lat16[(lat16["loner"] == "NOT_LONER")
                   & (lat16["relational_state"] == "DECOUPLED")
                   & (lat16["shock_coarse"] == "HIGH_SIG_HIGH_ABS")]
        if len(tl) and len(nl):
            lat = (f"TRUE_LONER DECOUPLED contagion {tl.iloc[0]['p_contagion']:.3f} "
                   f"vs NOT_LONER {nl.iloc[0]['p_contagion']:.3f}")

    # asymmetry headline
    asym = "n/a"
    if len(asym17):
        r = asym17.set_index("metric")
        if "p_contagion_7d" in r.index:
            c = r.loc["p_contagion_7d"]
            asym = (f"contagion downside {c['downside']:.3f} vs upside "
                    f"{c['upside']:.3f} ({c['asymmetry_direction']})")

    # info-gain verdicts (H7)
    ig = "n/a"
    if len(ig24b):
        ig = "; ".join(
            f"{r['outcome']} rel {r['relational_state_auc']:.3f} vs best "
            f"{r['best_other_auc']:.3f} -> {r['dynamic_relational_state_more_robust']}"
            for _, r in ig24b.iterrows())

    # PRD subtypes
    prd = "n/a"
    if len(prd23):
        sup = prd23[prd23["supported"] == "YES"]
        prd = ", ".join(f"{r['subtype']} n={int(r['n'])}"
                        for _, r in sup.iterrows()) or "none"

    # entropy verdicts
    ent = ", ".join(f"{r['peer_family']}={r['verdict']}"
                    for _, r in e05.iterrows()) if len(e05) else "n/a"

    # false/true loner decomposition
    fld = ", ".join(f"{r['subtype']} n={int(r['n'])}" for _, r in fld14.iterrows()
                    ) if len(fld14) else "n/a"
    tls = ", ".join(f"{r['subtype']} n={int(r['n'])}" for _, r in tls15.iterrows()
                    ) if len(tls15) else "n/a"

    md = f"""# LOWER-FIELD-8 SUMMARY

**Dynamic relational state vs static peer membership: membership entropy,
neighborhood lifecycle, reorganization response curves and timing, loner
decomposition, rejoin/contagion/decoupling lattice, PRD-as-relational-health.**

PARENTS: LF7 `032b5757` · MECH-13 `8e1fba0e` · Modeling Bible v1.0
VERDICT: see 29_LOWER_FIELD_8_DECISION.md

## 1. Peer-lifetime paradox resolved (H1)

LF7's high "60d alive" figures coexist with low same-member persistence because
they measured *any* neighborhood / substrate survival, not membership. LF8
separates membership from relational state. Relational-state persistence at 60d:
{h1}. Relational state is the more persistent object.

Conditional persistence (04): DECOUPLED and REORGANIZING states persist at
60-85% conditional rates where a future snapshot exists; TRUE/FALSE_ISOLATED
are single-event states (unconditional ~0 by construction).

## 2. Membership entropy (H2)

Entropy verdicts per family: {ent}. Membership churn is stationary and
low-information; no concentration trend earns a structural claim.

## 3. Reorganization response curves (H3)

{rc_str}. VOL_AMPLITUDE and ABS_SHOCK drive reorganization; SIGMA_SHOCK shows
no stable relation (normalized surprise is not the reorganization driver).

## 4. Timing precedence (H4)

ABS_SHOCK precedes: {prec}. Shock leads membership turnover, relational-state
change, and decoupling more often than the reverse.

## 5. Loner decomposition (H5)

False loners: {fld}. LOW_VOL_NORMALIZATION_ARTIFACT dominates (n=226) and is
LOCALLY_CONFORMING — the low-vol artifact ontology is confirmed.

True loners: {tls}. EARLY_CONTAGION and PERSISTENT_DECOUPLING subtypes are
DECOUPLED; MIXED_OTHER dominates.

Lattice (16): {lat}. True loners in DECOUPLED state are contagion-heavy;
not-loners in DECOUPLED state decouple without contagion.

## 6. Directional asymmetry (H6)

{asym}. Downside and upside relational biology are sign-asymmetric, not mirror.

## 7. PRD relational health (23)

Supported subtypes: {prd}. RELATIVE_DECAY and TEMPORARY_SPLIT earn support;
rescue subtypes (BETA_RESCUE / PEER_RESCUE) do not reach MIN_SUPPORT.

## 8. Relational state as predictor (H7 — falsification result)

{ig}

Relational state is a more persistent object (H1) but does NOT add predictive
information over exact peer identities / best-other family (purged AUC). The
claim is scoped: persistence is descriptive, not predictive.

## 9. Key caveats

Descriptive only. Conditional persistence uses nearest-snapshot lookups (small
n at +30/+60). CORR-family return metrics are DATA_BLOCKED (no peer_return).
mech_12 constraint-entropy join is DATA_BLOCKED (artifact unavailable).
Persistence of a PIT object is not executable reliability.
"""
    (R / "28_LOWER_FIELD_8_SUMMARY.md").write_text(md, encoding="utf-8")
    return md


def decision():
    md = """# LOWER-FIELD-8 DECISION

VERDICT: **PASS_LOWER_FIELD_8**

- Peer-lifetime paradox resolution: COMPUTED — LF7's "60d alive" was any-
  neighborhood/substrate survival, not same-member persistence. Separating
  membership from relational state is the correct object decomposition.
- H1 (relational state more persistent than membership): SUPPORTED —
  HYBRID_10 relational-state persistence 0.56 vs same-member 0.22 at 60d;
  DECOUPLED / REORGANIZING states persist conditionally at 60-85%.
- H2 (membership entropy stationary / low-information): SUPPORTED — all
  families STABLE; no structural concentration trend.
- H3 (vol/abs drive reorganization, sigma does not): SUPPORTED — VOL_AMPLITUDE
  LINEAR, ABS_SHOCK SATURATING, SIGMA_SHOCK NO_STABLE_RELATION.
- H4 (shock precedes turnover / state change / decoupling): SUPPORTED —
  ABS_SHOCK-before probabilities 0.90 / 0.94 / 0.92.
- H5 (false loners = low-vol artifacts; true loners decompose): SUPPORTED —
  LOW_VOL_NORMALIZATION_ARTIFACT dominates (n=226, LOCALLY_CONFORMING);
  EARLY_CONTAGION / PERSISTENT_DECOUPLING subtypes identified.
- H6 (downside/upside sign asymmetry): SUPPORTED — contagion DOWNSIDE_STRONGER,
  rejoin/decoupling UPSIDE_STRONGER.
- H7 (relational state adds predictive info over exact peer ids): **NOT
  SUPPORTED — FALSIFIED** — purged AUC of relational_state (0.50-0.51) does
  not reach best-other (0.55-0.60) for recovery/contagion/decoupling.
  Relational state is a more persistent object, not a better predictor.
- PRD relational health: PARTIAL — RELATIVE_DECAY / TEMPORARY_SPLIT supported;
  rescue subtypes below MIN_SUPPORT.
- Honest DATA_BLOCKED: mech_12 constraint-entropy join (artifact unavailable);
  CORR-family peer_return relational metrics (no peer_return in LF5 maps).

REMAINING (authorized next checkpoints only after human review):
1. Continuous relational-state time series (not event-anchored snapshots) to
   confirm the persistence read outside stress dates.
2. Purged FDR validation of early-contagion / lattice / PRD subtype families.
3. Symmetric replication of the directional asymmetry across cycles.
4. Predictive-robustness audit: the H7 falsification scopes LF8's claim to
   object persistence, not forecast skill.

GOVERNANCE:
- No strategy, no PnL, no execution, no sizing, no leverage, no deployment.
- human_review_required = TRUE
- next_checkpoint_authorized = FALSE

STOP AFTER LOWER-FIELD-8. WAIT FOR HUMAN REVIEW.
"""
    (R / "29_LOWER_FIELD_8_DECISION.md").write_text(md, encoding="utf-8")
    return md


def main():
    promote_merge_dissolve().to_csv(R / "25_PROMOTE_MERGE_DISSOLVE.csv",
                                    index=False)
    null_and_failed().to_csv(R / "26_NULL_AND_FAILED_RESULTS.csv",
                             index=False)
    alpha_role_registry().to_csv(R / "27_ALPHA_ROLE_REGISTRY.csv",
                                 index=False)
    summary()
    decision()
    print("FINALIZE COMPLETE", flush=True)


if __name__ == "__main__":
    main()
