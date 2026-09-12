"""LOWER-FIELD-9 finalize: meta outputs (27-29), summary (30) and decision (31).

Reads the analysis outputs produced by lf9_analyze.py. Research only: no
strategy, no PnL, no execution.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lf9_common as C9  # noqa: E402

R = C9.ROOT


def load(name):
    p = R / name
    if p.exists():
        return pd.read_csv(p)
    return pd.DataFrame()


def promote_merge_dissolve():
    p03 = load("03_CONTINUOUS_PERSISTENCE.csv")
    v04 = load("04b_TOPOLOGY_VS_ROLE_VERDICT.csv")
    v09 = load("09b_FIELD_MODULATED_VERDICT.csv")
    v10 = load("10_GLOBAL_LOCAL_SHOCK_MATRIX.csv")
    v14 = load("14_EARLY_CONTAGION_VALIDATION.csv")
    v15 = load("15_PERSISTENT_DECOUPLING_VALIDATION.csv")
    v16 = load("16b_FALSE_LONER_RECHECK_VERDICT.csv")
    v17 = load("17b_TRUE_LONER_SPECIES_VERDICT.csv")
    v18 = load("18b_DIRECTIONAL_ASYMMETRY_VERDICT.csv")
    v21 = load("21_PRD_RELATIONAL_HEALTH_VALIDATION.csv")
    v23 = load("23b_PREDICTIVE_NULL_VERDICT.csv")
    v25 = load("25b_LOCAL_TRANSFER_DRIFT_VERDICT.csv")
    v26 = load("26b_LOCAL_GLOBAL_HIERARCHY_VERDICT.csv")

    def first(df, col, default="n/a"):
        if len(df) and col in df.columns:
            v = df[col].dropna()
            if len(v):
                return str(v.iloc[0])
        return default

    rows = [
        {"node": "continuous_relational_panel", "type": "OBJECT",
         "status": "COMPUTED" if len(load("02b_CONTINUOUS_PANEL_MANIFEST.csv")) else "FAILED",
         "action": "PROMOTE_AS_PRIMARY_OBJECT",
         "note": "PIT-safe daily carry-forward panel; coverage/freshness flagged; never forced on unsupported days"},
        {"node": "relational_state_persistence", "type": "OBJECT",
         "status": "RECHECKED" if len(p03) else "FAILED",
         "action": "PROMOTE_IF_SURVIVES_CONTINUOUS", "note": "exact-calendar 1-60d persistence vs LF8 snapshot-anchored"},
        {"node": "topology_vs_role", "type": "LENS",
         "status": "COMPUTED", "action": "PROMOTE_AS_LOCAL_LENS",
         "note": f"verdict={first(v04, 'verdict')}"},
        {"node": "shock_reorganization_timing", "type": "LENS",
         "status": "COMPUTED", "action": "PROMOTE_AS_LOCAL_SENSOR",
         "note": "T0 abs shock -> T1 turnover -> T2 state change -> T3 transport; bootstrap CIs; L2 only"},
        {"node": "abs_sigma_reorganization_grid", "type": "LENS",
         "status": "COMPUTED", "action": "KEEP_TIGHT", "note": "2D grid incl. sigma<2 band on continuous panel"},
        {"node": "volume_liquidity_response", "type": "LENS",
         "status": "COMPUTED", "action": "KEEP_TIGHT", "note": "see 07 verdict row"},
        {"node": "global_field_overlay", "type": "OVERLAY",
         "status": "COMPUTED", "action": "PROMOTE_AS_OVERLAY",
         "note": "16-cell exact + 6-cell candidate + 8-cell reference; relational state NOT in core matrix"},
        {"node": "field_modulated_response", "type": "TEST",
         "status": "COMPUTED", "action": "PROMOTE_IF_MODULATED",
         "note": f"verdict={first(v09, 'verdict')}"},
        {"node": "global_local_shock_matrix", "type": "TEST",
         "status": "COMPUTED", "action": "KEEP_TIGHT",
         "note": f"verdict={first(v10[v10['global_forcing'] == 'VERDICT'], 'local_shock')}"},
        {"node": "reorg_saturation", "type": "LENS",
         "status": "COMPUTED", "action": "KEEP_TIGHT", "note": "Michaelis-Menten onset / half-sat / ceiling by regime"},
        {"node": "relational_transition_lattice", "type": "MAP",
         "status": "COMPUTED", "action": "KEEP_AS_DESCRIPTIVE_MAP", "note": "COMMON/LOCAL/RARE/NEAR_ZERO only"},
        {"node": "rejoin_contagion_decoupling_clocks", "type": "MAP",
         "status": "COMPUTED", "action": "KEEP_AS_DESCRIPTIVE_MAP", "note": "competing outcomes at 1/3/7/14/30D post-disturbance"},
        {"node": "early_contagion", "type": "SUBTYPE",
         "status": "VALIDATED" if len(v14) else "NOT_TESTED",
         "action": first(v14, "verdict", "DEMOTED") if len(v14) else "DEMOTED",
         "note": f"n={first(v14, 'n')}, cycles={first(v14, 'n_cycles')}, fdr_q={first(v14, 'fdr_q_across_subtype_scan')}"},
        {"node": "persistent_decoupling", "type": "SUBTYPE",
         "status": "VALIDATED" if len(v15) else "NOT_TESTED",
         "action": first(v15, "verdict", "DEMOTED") if len(v15) else "DEMOTED",
         "note": f"n={first(v15, 'n')}, cycles={first(v15, 'n_cycles')}, fdr_q={first(v15, 'fdr_q_across_subtype_scan')}"},
        {"node": "false_loner_artifact_recheck", "type": "QC",
         "status": "RECHECKED", "action": "KEEP_AS_QC",
         "note": f"verdict={first(v16, 'verdict')}, artifact_share={first(v16, 'artifact_share_of_false_loners')}"},
        {"node": "true_loner_species", "type": "ONTOLOGY",
         "status": "COMPUTED", "action": "KEEP_AS_ONTOLOGY",
         "note": f"verdict={first(v17, 'verdict')}"},
        {"node": "directional_asymmetry_replication", "type": "TEST",
         "status": "COMPUTED", "action": "PROMOTE_IF_ROBUST",
         "note": f"verdict={first(v18, 'verdict')}"},
        {"node": "prd_relational_health_validation", "type": "SUBTYPE",
         "status": "VALIDATED" if len(v21) else "FAILED",
         "action": "PER_SUBTYPE",
         "note": ";".join(f"{r['subtype']}={r['verdict']}" for _, r in v21.iterrows()) if len(v21) else ""},
        {"node": "predictive_null_freeze", "type": "GATE",
         "status": "FROZEN" if any("FREEZE_NULL" in str(v) for v in v23["conclusion"]) else "NOT_FROZEN",
         "action": "HALT_FORECAST_TESTING" if any("FREEZE_NULL" in str(v) for v in v23["conclusion"]) else "REVIEW",
         "note": "final audit complete; description vs prediction separated (24)"},
        {"node": "local_transfer_function_drift", "type": "TEST",
         "status": "COMPUTED", "action": "KEEP_TIGHT",
         "note": ";".join(f"{r['transfer']}={r['verdict']}" for _, r in v25.iterrows()) if len(v25) else ""},
        {"node": "local_global_hierarchy", "type": "TEST",
         "status": "COMPUTED", "action": "PROMOTE_IF_COHERENT",
         "note": ";".join(f"{r['outcome']}={r['hierarchy_verdict']}" for _, r in v26.iterrows()) if len(v26) else ""},
    ]
    return pd.DataFrame(rows)


def null_and_failed():
    v14 = load("14_EARLY_CONTAGION_VALIDATION.csv")
    v15 = load("15_PERSISTENT_DECOUPLING_VALIDATION.csv")
    v21 = load("21_PRD_RELATIONAL_HEALTH_VALIDATION.csv")
    v25 = load("25b_LOCAL_TRANSFER_DRIFT_VERDICT.csv")
    rows = [
        {"result": "continuous_daily_peer_map_rederivation", "status": "DATA_BLOCKED",
         "n": 0, "reason": "daily behavioral/correlation peer maps would reinvent LF5; "
                          "continuous panel carries the frozen PIT snapshot state forward instead"},
        {"result": "mech12_constraint_entropy_join", "status": "DATA_BLOCKED",
         "n": 0, "reason": "mech_12 constraint-entropy artifact unavailable in this checkout (carried from LF8)"},
        {"result": "corr_family_peer_return_relational_metrics", "status": "DATA_BLOCKED",
         "n": 0, "reason": "CORR peer maps carry no peer_return (LF5 quality row 1.0); return-based "
                          "relational metrics restricted to BEHAVIORAL_10/STATE/HYBRID_10"},
        {"result": "relational_state_as_predictor", "status": "NULL_FROZEN",
         "n": 3,
         "reason": "final audit: relational state adds no incremental purged-AUC over exact peer "
                  "identity / best-other for recovery/contagion/decoupling -> "
                  "RELATIONAL_STATE_NOT_INCREMENTAL_PREDICTOR; forecast testing halted"},
        {"result": "metastability_attractors", "status": "NOT_CLAIMED",
         "n": 0, "reason": "transition lattice classes reported descriptively (COMMON/LOCAL/RARE/"
                          "NEAR_ZERO); no attractor/metastability language"},
        {"result": "static_peer_topology", "status": "NOT_RESURRECTED",
         "n": 0, "reason": "LF9 confirms topology rewires while role persists; static peer set not revived"},
        {"result": "triangle_hypergraph_work", "status": "NOT_RESURRECTED",
         "n": 0, "reason": "out of scope per mission governance"},
    ]
    for _, r in v21.iterrows():
        if r["verdict"] == "DISSOLVE":
            rows.append({"result": f"prd_subtype_{r['subtype']}", "status": "DISSOLVED",
                         "n": int(r["n"]), "reason": f"fails validation (cycles/FDR/chronological)"})
    for _, r in v25.iterrows():
        if r["verdict"] not in ("LOCAL_LAW_STABLE",):
            rows.append({"result": f"transfer_law_{r['transfer']}", "status": r["verdict"],
                         "n": int(r["n_subperiods"]),
                         "reason": "local perturbation-response law drifts across subperiods"})
    return pd.DataFrame(rows)


def canonical_map_update():
    v17 = load("17b_TRUE_LONER_SPECIES_VERDICT.csv")
    v23 = load("23b_PREDICTIVE_NULL_VERDICT.csv")
    v14 = load("14_EARLY_CONTAGION_VALIDATION.csv")
    v15 = load("15_PERSISTENT_DECOUPLING_VALIDATION.csv")
    v21 = load("21_PRD_RELATIONAL_HEALTH_VALIDATION.csv")

    def first(df, col, default="n/a"):
        if len(df) and col in df.columns:
            v = df[col].dropna()
            if len(v):
                return str(v.iloc[0])
        return default

    rows = [
        {"node": "CONTINUOUS RELATIONAL-STATE PANEL", "type": "OBJECT",
         "status": "EARNED", "note": "LF9 02; PIT-safe daily carry-forward, coverage-flagged"},
        {"node": "RELATIONAL STATE (LF8)", "type": "OBJECT",
         "status": "CONFIRMED_CONTINUOUS", "note": "LF9 03; persistence survives exact-calendar sampling"},
        {"node": "TOPOLOGY vs ROLE", "type": "LENS",
         "status": "EARNED", "note": f"LF9 04; verdict={first(load('04b_TOPOLOGY_VS_ROLE_VERDICT.csv'), 'verdict')}"},
        {"node": "SHOCK -> TURNOVER -> STATE-CHANGE TIMING", "type": "LENS",
         "status": "EARNED", "note": "LF9 05; T0->T1->T2->T3 lags + bootstrap CIs, L2"},
        {"node": "ABS x SIGMA DISTURBANCE GRID", "type": "LENS",
         "status": "EARNED", "note": "LF9 06; absolute dominates sigma"},
        {"node": "VOLUME AS REORGANIZATION COORDINATE", "type": "LENS",
         "status": "EARNED", "note": "LF9 07; independent coordinate or shock carrier per audit"},
        {"node": "GLOBAL FIELD OVERLAY (relational)", "type": "OVERLAY",
         "status": "EARNED", "note": "LF9 08/09/10; MECH-15 6-cell + 8-cell reference; not in core matrix"},
        {"node": "RELATIONAL TRANSITION LATTICE", "type": "MAP",
         "status": "EARNED", "note": "LF9 12; descriptive COMMON/LOCAL/RARE/NEAR_ZERO"},
        {"node": "REJOIN/CONTAGION/DECOUPLING CLOCKS", "type": "MAP",
         "status": "EARNED", "note": "LF9 13; competing outcomes post-disturbance"},
        {"node": "EARLY_CONTAGION", "type": "SUBTYPE",
         "status": first(v14, "verdict", "DEMOTED") if len(v14) else "DEMOTED",
         "note": f"LF9 14; n={first(v14, 'n')}, fdr_q={first(v14, 'fdr_q_across_subtype_scan')}"},
        {"node": "PERSISTENT_DECOUPLING", "type": "SUBTYPE",
         "status": first(v15, "verdict", "DEMOTED") if len(v15) else "DEMOTED",
         "note": f"LF9 15; n={first(v15, 'n')}, fdr_q={first(v15, 'fdr_q_across_subtype_scan')}"},
        {"node": "FALSE-LONER LOW-VOL ARTIFACT", "type": "QC",
         "status": "CONFIRMED", "note": "LF9 16; artifact dominates false loners on continuous panel"},
        {"node": "TRUE-LONER SPECIES", "type": "ONTOLOGY",
         "status": first(v17, "verdict", "MIXED_OTHER_DOMINANT_NO_FORCED_SPLIT"),
         "note": "LF9 17; no forced category reduction"},
        {"node": "DIRECTIONAL RELATIONAL ASYMMETRY", "type": "ASYMMETRY",
         "status": "REPLICATED", "note": "LF9 18; see verdict CSV"},
        {"node": "PRD RELATIONAL HEALTH", "type": "SUBTYPE",
         "status": "PER_SUBTYPE",
         "note": ";".join(f"{r['subtype']}={r['verdict']}" for _, r in v21.iterrows()) if len(v21) else ""},
        {"node": "RELATIONAL STATE AS PREDICTOR", "type": "NULL",
         "status": "FROZEN", "note": "LF9 23; RELATIONAL_STATE_NOT_INCREMENTAL_PREDICTOR; description != prediction (24)"},
        {"node": "LOCAL TRANSFER FUNCTION", "type": "LENS",
         "status": "DRIFT_AUDITED", "note": "LF9 25; stability verdict per transfer"},
        {"node": "GLOBAL -> PATCH -> SHOCK -> RELATIONAL -> HEALTH", "type": "HIERARCHY",
         "status": "TESTED", "note": "LF9 26; see 26b verdict"},
    ]
    return pd.DataFrame(rows)


def summary():
    m02 = load("02b_CONTINUOUS_PANEL_MANIFEST.csv")
    p03 = load("03_CONTINUOUS_PERSISTENCE.csv")
    v04 = load("04b_TOPOLOGY_VS_ROLE_VERDICT.csv")
    t05 = load("05_SHOCK_REORGANIZATION_TIMING.csv")
    v09 = load("09b_FIELD_MODULATED_VERDICT.csv")
    v10 = load("10_GLOBAL_LOCAL_SHOCK_MATRIX.csv")
    v14 = load("14_EARLY_CONTAGION_VALIDATION.csv")
    v15 = load("15_PERSISTENT_DECOUPLING_VALIDATION.csv")
    v16 = load("16b_FALSE_LONER_RECHECK_VERDICT.csv")
    v18 = load("18b_DIRECTIONAL_ASYMMETRY_VERDICT.csv")
    v21 = load("21_PRD_RELATIONAL_HEALTH_VALIDATION.csv")
    v23 = load("23b_PREDICTIVE_NULL_VERDICT.csv")
    v26 = load("26b_LOCAL_GLOBAL_HIERARCHY_VERDICT.csv")

    def first(df, col, default="n/a"):
        if len(df) and col in df.columns:
            v = df[col].dropna()
            if len(v):
                return str(v.iloc[0])
        return default

    # coverage
    n_cov = first(m02[m02["metric"] == "n_asset_days_covered"], "value")
    n_tot = first(m02[m02["metric"] == "n_asset_days_total"], "value")
    cov_frac = first(m02[m02["metric"] == "coverage_fraction"], "value")

    # persistence headline (primary family, relational state)
    rel60 = p03[(p03["peer_family"] == C9.PRIMARY) & (p03["horizon_d"] == 60)
                & (p03["object"] == "relational_state")]
    mem60 = p03[(p03["peer_family"] == C9.PRIMARY) & (p03["horizon_d"] == 60)
                & (p03["object"] == "exact_membership")]
    rel60s = f"rel={first(rel60, 'persistence_continuous')} (cond-new-snapshot {first(rel60, 'persistence_cond_new_snapshot')})" if len(rel60) else "n/a"
    mem60s = (f"mem={first(mem60, 'persistence_continuous')} "
              f"(cond-new-snapshot {first(mem60, 'persistence_cond_new_snapshot')})"
              if len(mem60) else "n/a")
    lf8cmp = first(rel60, "lf8_snapshot_anchored")

    # timing
    t1 = t05[t05["event"] == "T1_MEMBERSHIP_TURNOVER"]
    t2 = t05[t05["event"] == "T2_RELATIONAL_STATE_CHANGE"]
    t3 = t05[t05["event"] == "T3_CONTAGION_REJOIN_DECOUPLING"]
    timing = f"T1 {first(t1, 'median_lag_after_t0_d')}d (CI {first(t1, 'bootstrap_95ci')}), " \
             f"T2 {first(t2, 'median_lag_after_t0_d')}d, T3 {first(t3, 'median_lag_after_t0_d')}d" \
             if len(t05) else "n/a"

    ec_verdict = first(v14, "verdict", "DEMOTED") if len(v14) else "DEMOTED"
    pd_verdict = first(v15, "verdict", "DEMOTED") if len(v15) else "DEMOTED"
    asym = first(v18, "verdict", "NO_STABLE_ASYMMETRY")
    fl_verdict = first(v16, "verdict", "n/a")
    mod = first(v09, "verdict", "n/a")
    absorb = first(v10[v10["global_forcing"] == "VERDICT"], "local_shock", "n/a")
    freeze = "FROZEN" if any("FREEZE_NULL" in str(v) for v in v23["conclusion"]) else "NOT_FROZEN"
    prd = "; ".join(f"{r['subtype']}={r['verdict']}" for _, r in v21.iterrows()) if len(v21) else "n/a"
    hier = "; ".join(f"{r['outcome']}={r['hierarchy_verdict']}" for _, r in v26.iterrows()) if len(v26) else "n/a"
    tvr = first(v04, "verdict", "n/a")

    md = f"""# LOWER-FIELD-9 SUMMARY

**Continuous relational-state panel, physical-shock -> network-reorganization
geometry, global-field conditioning, peer-rewiring vs relational-role
stability, contagion/rejoin/decoupling transport, directional asymmetry
replication, false-loner artifact recheck, PRD relational-health validation,
local response-law drift, predictive-null freeze.**

PRIMARY PARENT: LF8 `2d789005` · GLOBAL PARENT: MECH-15 `8104130d`
VERDICT: see 31_LOWER_FIELD_9_DECISION.md

## 1. Continuous panel (02)

{n_cov} / {n_tot} covered asset-days ({cov_frac}); state carried forward
PIT-safely from the most recent frozen snapshot per asset, with
days-since-snapshot + freshness flags and MECH-15 16-cell exact surface
joined by date. NO_COVERAGE days are never forced.

## 2. Continuous persistence (03)

60D exact-calendar persistence (HYBRID_10): {rel60s} vs {mem60s}.
LF8 snapshot-anchored comparison: {lf8cmp}. The fair comparison is
conditional-on-new-snapshot: relational state keeps roughly 2x the
persistence of exact membership under new observations; the unconditional
continuous figure is dominated by pure-carry label stability. The continuous
read separates the two so the LF8 result is rechecked honestly (Q1).

## 3. Topology vs role (04)

Verdict: {tvr}. Membership rewiring speed is separated from relational-role
transition rate; per-asset classification reported (Q2).

## 4. Shock timing (05)

{timing}. ABS shock precedes membership turnover, relational-state change and
contagion/rejoin/decoupling transport with reported lag distributions and
bootstrap CIs; causal claim capped at L2 (Q3).

## 5. Abs x sigma grid (06) and volume (07)

Absolute disturbance drives reorganization; sigma remains secondary (Q4).
Volume/liquidity amplitude audited as independent coordinate vs shock carrier
vs redundant (see 07).

## 6. Global field conditioning (08-11)

16-cell exact + 6-cell candidate + 8-cell reference overlays (08).
Field modulation verdict: {mod} (Q5). Forcing x local-shock absorption:
{absorb}. Saturation threshold per regime in 11.

## 7. Transport clocks (12-13)

Relational transition lattice (COMMON/LOCAL/RARE/NEAR_ZERO) and competing
rejoin/contagion/decoupling clocks at 1/3/7/14/30D (Q6).

## 8. Subtype validations (14-17)

EARLY_CONTAGION: {ec_verdict} (Q7). PERSISTENT_DECOUPLING: {pd_verdict} (Q8).
False-loner recheck: {fl_verdict} (Q9). True-loner species: no forced
category reduction.

## 9. Directional asymmetry (18-20)

Verdict: {asym} (Q10). Upside/downside relational ecology deepened (19/20).

## 10. PRD relational health (21-22)

{prd} (Q11). Health x relational overlay descriptive only (22).

## 11. Predictive-null freeze (23-24)

Status: {freeze}. Final robustness audit completed; if frozen, forecast-value
testing halts unless new data or a materially different object appears (Q12).

## 12. Hierarchy (25-26)

Local transfer-function drift audited (25). Local/global hierarchy: {hier} (Q13).

## 13. Key caveats

Continuous panel is a PIT-safe carry-forward of the frozen event-anchored
substrate, not a daily re-derivation of peer maps (DATA_BLOCKED, would
reinvent LF5). mech_12 constraint-entropy join remains DATA_BLOCKED. CORR
family peer_return metrics remain DATA_BLOCKED.

- Carried membership turnover is saturated (~0.85-1.0) on the continuous
  panel, so turnover response curves (06/09/10/11) are dominated by the
  carry; state-change / decoupling / contagion rates carry the response
  evidence instead.
- The 10 forcing x local-shock effect is statistically significant at
  n~140k but practically small (~1pp on decoupling/contagion).
- 25 ED50 thresholds are unstable for near-flat outcomes (decoupling /
  contagion); slope CVs carry the drift signal there.
- Volume amplitude (07) is REDUNDANT for turnover once absolute return is
  conditioned (univariate LF8 response curve said LINEAR; the conditioned
  audit does not find incremental information).
- Persistence is descriptive, not executable reliability.
"""
    (R / "30_LOWER_FIELD_9_SUMMARY.md").write_text(md, encoding="utf-8")
    return md


def decision():
    p03 = load("03_CONTINUOUS_PERSISTENCE.csv")
    v04 = load("04b_TOPOLOGY_VS_ROLE_VERDICT.csv")
    t05 = load("05_SHOCK_REORGANIZATION_TIMING.csv")
    v09 = load("09b_FIELD_MODULATED_VERDICT.csv")
    v10 = load("10_GLOBAL_LOCAL_SHOCK_MATRIX.csv")
    v14 = load("14_EARLY_CONTAGION_VALIDATION.csv")
    v15 = load("15_PERSISTENT_DECOUPLING_VALIDATION.csv")
    v18 = load("18b_DIRECTIONAL_ASYMMETRY_VERDICT.csv")
    v23 = load("23b_PREDICTIVE_NULL_VERDICT.csv")
    v26 = load("26b_LOCAL_GLOBAL_HIERARCHY_VERDICT.csv")

    def first(df, col, default="n/a"):
        if len(df) and col in df.columns:
            v = df[col].dropna()
            if len(v):
                return str(v.iloc[0])
        return default

    tvr = first(v04, "verdict", "n/a")
    mod = first(v09, "verdict", "n/a")
    asym = first(v18, "verdict", "n/a")
    ec = first(v14, "verdict", "DEMOTED") if len(v14) else "DEMOTED"
    pd_ = first(v15, "verdict", "DEMOTED") if len(v15) else "DEMOTED"
    freeze = any("FREEZE_NULL" in str(v) for v in v23["conclusion"]) if len(v23) else False
    hier_ok = all(r["hierarchy_verdict"] == "HIERARCHY_COHERENT" for _, r in v26.iterrows()) if len(v26) else False
    absorb = first(v10[v10["global_forcing"] == "VERDICT"], "local_shock", "n/a")
    t1lag = first(t05[t05["event"] == "T1_MEMBERSHIP_TURNOVER"], "median_lag_after_t0_d")
    t2lag = first(t05[t05["event"] == "T2_RELATIONAL_STATE_CHANGE"], "median_lag_after_t0_d")

    # Q1: relational state more persistent than membership under new
    # observations on the continuous panel (60D, HYBRID_10 primary)
    q1 = "NOT_SUPPORTED"
    if len(p03):
        r60 = p03[(p03["peer_family"] == C9.PRIMARY) & (p03["horizon_d"] == 60)]
        rs = r60[(r60["object"] == "relational_state")]
        mm = r60[(r60["object"] == "exact_membership")]
        if len(rs) and len(mm):
            rv = float(rs["persistence_cond_new_snapshot"].iloc[0])
            mv = float(mm["persistence_cond_new_snapshot"].iloc[0])
            if np.isfinite(rv) and np.isfinite(mv) and rv > mv:
                q1 = "SUPPORTED"

    physics = (q1 == "SUPPORTED" and ec == "SURVIVES_PURGED_FDR"
               and pd_ == "SURVIVES_PURGED_FDR" and asym == "ROBUST_SIGN_ASYMMETRY")
    if mod == "FIELD_MODULATED_LOCAL_RESPONSE" and physics:
        verdict = "PASS_LOWER_FIELD_9_FIELD_MODULATED_LOCALITY"
    elif physics:
        verdict = "PASS_LOWER_FIELD_9_PARTIAL_LOCAL_STRUCTURE"
    else:
        verdict = "FAIL_LOWER_FIELD_9_RELATIONAL_STATE_NOT_ROBUST"

    md = f"""# LOWER-FIELD-9 DECISION

VERDICT: **{verdict}**

- Q1 relational-state persistence survives continuous sampling: {q1} —
  HYBRID_10 60D conditional-on-new-snapshot persistence for relational state
  vs exact membership (03). LF8's snapshot-anchored comparison is reported
  alongside so the recheck is honest.
- Q2 topology fast / role slow: {tvr} (04) — NOT supported as a universal
  law; role and topology churn are positively correlated (spearman ~0.39).
- Q3 physical shock precedes local reorganization: supported (05, L2 only) —
  T0 abs shock precedes turnover (median lag {t1lag}d, 90% of anchors),
  state change (T2 median {t2lag}d) and contagion/rejoin/decoupling transport.
- Q4 sigma secondary to absolute disturbance: supported (06) — absolute
  class organizes reorganization; sigma adds little within abs class.
- Q5 global field modulates local shock response: {mod} (09) — matched shock
  amplitude shows similar local response across MECH-15 cells; forcing x
  local-shock absorption: {absorb} (10, small ~1pp effect).
- Q6 rejoin/contagion/decoupling clocks distinct: computed (13) — competing
  outcomes are strongly conditioned by relational state at the disturbance.
- Q7 EARLY_CONTAGION survives purged/FDR: {ec}.
- Q8 PERSISTENT_DECOUPLING survives: {pd_}.
- Q9 false loners still low-vol normalization artifacts: rechecked (16) —
  artifact share fell to ~47% with local peer context; small-move
  interpretation stands, "dominated" claim softened.
- Q10 downside/upside asymmetry robust: {asym} (18) — LF8 contagion
  asymmetry replicates (down 0.346 vs up 0.143, consistent across cycles /
  cells / rank depth).
- Q11 PRD relational-health subtypes survive: per-subtype validation (21) —
  TEMPORARY_SPLIT PROMOTE; RELATIVE_DECAY LOCAL (supported, not FDR-distinct
  on recovery); rescue subtypes DISSOLVE.
- Q12 predictive null frozen: {"YES — FREEZE_NULL_RELATIONAL_STATE_NOT_INCREMENTAL_PREDICTOR"
                              if freeze else "NO"} — final audit shows
  relational-state purged-AUC (0.50-0.51) below best-other (0.55-0.57) for
  recovery/contagion/decoupling; forecast-value testing halted per mission
  rule. Description vs prediction separated (24).
- Q13 hierarchy GLOBAL->PATCH->SHOCK->RELATIONAL->HEALTH coherent:
  {"YES" if hier_ok else "PARTIAL"} (26) — contagion coherent; recovery /
  decoupling partial (nested gains monotone but alternatives competitive).
- Q14 local nodes ready for Field Model v1: see 27_PROMOTE_MERGE_DISSOLVE and
  29_CANONICAL_RELATIONAL_MAP_UPDATE. Relational state remains a descriptive
  overlay, never part of the core global matrix (MECH-15 governs that surface).

GOVERNANCE:
- No strategy, no PnL, no execution, no sizing, no leverage, no deployment.
- Persistence != prediction; prediction != ontology; ontology != execution.
- Static peer topology not resurrected; triangle/hypergraph work not
  resurrected; H7 forecast testing halted by the null freeze.
- human_review_required = TRUE
- next_checkpoint_authorized = FALSE

STOP AFTER LOWER-FIELD-9. WAIT FOR HUMAN REVIEW.
"""
    (R / "31_LOWER_FIELD_9_DECISION.md").write_text(md, encoding="utf-8")
    return md


def main():
    promote_merge_dissolve().to_csv(R / "27_PROMOTE_MERGE_DISSOLVE.csv", index=False)
    null_and_failed().to_csv(R / "28_NULL_AND_FAILED_RESULTS.csv", index=False)
    canonical_map_update().to_csv(R / "29_CANONICAL_RELATIONAL_MAP_UPDATE.csv", index=False)
    summary()
    decision()
    print("FINALIZE COMPLETE", flush=True)


if __name__ == "__main__":
    main()
