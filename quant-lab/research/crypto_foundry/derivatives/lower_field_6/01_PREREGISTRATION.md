# LOWER-FIELD-6 — PREREGISTRATION

**TRUE-vs-FALSE LONER GEOMETRY · MULTI-SIGMA RECOVERY LADDERS · PEER REJOIN vs
PEER CATCHDOWN · RANK-PATCH / BASKET ANATOMY · HEALTH-STATE HARMONIZATION ·
LOCAL SEQUENCE & PROPAGATION STRUCTURE**

AGENT 2 — DERIVATIVE / SIDE-LANE FALSIFIER

PARENTS:
- TRUE-PEER LF5 `8bd8cfbd` — PIT peer substrate + five true peer families
- MECH-10 `decf75bc` — temporal delivery, 4-state hazards, PRD local mechanism
- POST-MECH10 SYNTHESIS `805461c9` — hold point synthesis

STATUS: **PREREGISTERED** — human_review_required = TRUE,
next_checkpoint_authorized = FALSE.

---

## 0. Purpose

LF6 deepens the true-peer research that LF5's infrastructure unlocked. LF5
answered *what percentage of rank-only loners are false loners under true
peer definitions* (~1 in 5). LF6 asks *what the true/false loner geometry
looks like, whether recovery is a multi-sigma ladder, whether the asset
rejoins peers or peers catch down, where in rank space isolation is
genuine, and whether the two agents' PRICE×RANK health states can be
harmonized*.

No strategy. No PnL. No execution. No entry/exit rules. No sizing.
No leverage. No deployment.

## 1. Event universe

Same as LF5 primary research object: **ISOLATED downside events, z1 >= 2σ,
rank bands 26-2000** (EVENT_BANDS = PRIMARY 501-2000 + COMPARE 26-500).
3σ lens kept as a secondary amplitude lens. Peer maps are frozen LF5
outputs (outcome-free, PIT-safe).

Event-level base outcomes (all LF5 precomputed on the PIT substrate):
- signed_fwd{h} = event_sign × fwd{h}_cum for h in 1..30
- rev{h} reversal, recover1s{h} = signed_fwd{h} >= sigma_t0 × sqrt(h)
- fwd_rank_vel_{h}d = fwd_rank_{h}d - rank

## 2. Definitions fixed up front

| Object | Definition |
|--------|-----------|
| TRUE_LONER (per family) | \|ret_1d − peer_median\| >= peer_disp (peer dispersion > 0) |
| FALSE_LONER (per family) | \|ret_1d − peer_median\| < peer_disp |
| Consensus classes | TRUE_MULTI_PEER_LONER (>=3/5 families TRUE), X_FALSE (dominant false family), AMBIGUOUS (mixed / insufficient) |
| Recovery from shock anchor | recovery_sigma(h) = signed_fwd{h} / sigma_t0 (positive = recovery in event direction) |
| 1σ / 2σ / 3σ checkpoints | recovery_sigma >= 1 / 2 / 3 |
| Full repair (30D) | recover1s30 (>= 1σ at 30D) |
| Rank repair | fwd_rank_vel_{h}d > 0 |
| Peer rejoin (7D) | asset up, peers flat (\|peer_med7\| < 0.5σ), \|resid7\| < \|residual0\| |
| Peer catchdown | peer_med7 < −0.5σ |
| Local contagion | asset up AND peers down at 7D |
| Persistent decoupling | asset down, peers flat at 7D |
| Propagation radius | band spillover = events in same rank_band on t0+h; adjacent = any band |

## 3. Peer families

DEEP_FAMILIES = BEHAVIORAL_10, CORR_60_10, CORR_120_10, STATE, HYBRID_10
(frozen LF5 maps; CORR peer returns reconstructed from the PIT substrate at
the event date so isolation can be scored on the same residual scale).

## 4. Pre-registered allowed verdicts

Peer families: VALID / VALID_WITH_LIMITATIONS / WEAK / UNSTABLE / NULL.
Reversal primitives: GLOBAL_PRIMITIVE / CONDITIONAL_PRIMITIVE / LOCAL_NODE / NULL.
Named sequence patterns require >= 50 effective events and >= 3 subperiods.
PRD harmonization: LEGACY_AGENT1 / LEGACY_AGENT2 / HARMONIZED_CANONICAL with
exact counts; no merged claims before resolution.

## 5. Required outputs (29)

01_PREREGISTRATION.md · 02_PEER_VALIDATION_DEPTH.csv ·
03_CONSENSUS_LONER_CLASSIFICATION.csv · 04_RANK_DEPTH_LONER_MAP.csv ·
05_RANK_PATCH_BASKET_GEOMETRY.csv · 06_TRUE_FALSE_LONER_OUTCOMES.csv ·
07_MULTI_SIGMA_RECOVERY_LADDER.csv · 08_SHOCK_RECOVERY_AMPLITUDE_MATRIX.csv ·
09_LONER_SIGMA_MATRIX.csv · 10_PEER_REJOIN_CATCHDOWN.csv ·
11_PEER_CATCHDOWN_LEADLAG.csv · 12_TRUE_DISLOCATION_SEQUENCE.csv ·
13_FALSE_LONER_SEQUENCE.csv · 14_PRD_DEFINITION_HARMONIZATION.md ·
15_HARMONIZED_PRICE_RANK_MATRIX.csv · 16_PRD_BETA_RESCUE_ANATOMY.csv ·
17_HEALTH_TRANSITION_SEQUENCES.csv · 18_REVERSAL_DEPTH_TRUE_PEER_CONTROL.csv ·
19_REVERSAL_PRIMITIVE_AUDIT.csv · 20_FAILURE_MIRRORS.csv ·
21_PROPAGATION_RADIUS.csv · 22_LONER_4STATE_AGE_MATRIX.csv ·
23_SHMC_SHHM_PEER_PLACEMENT.csv · 24_LOCAL_SEQUENCE_ATLAS.csv ·
25_PROMOTE_MERGE_DISSOLVE.csv · 26_NULL_AND_FAILED_RESULTS.csv ·
27_ALPHA_ROLE_REGISTRY.csv · 28_LOWER_FIELD_6_SUMMARY.md ·
29_LOWER_FIELD_6_DECISION.md

## 6. Governance

Statistical terrain first. Do not confuse peer structure with tradable
alpha. STOP AFTER LOWER-FIELD-6. WAIT FOR HUMAN REVIEW.
