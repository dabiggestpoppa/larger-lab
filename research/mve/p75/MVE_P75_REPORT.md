# MVE-P7.5 — Core State Seal Report

**Checkpoint:** MVE-P7.5-CORE-STATE-SEAL
**Base:** bda32020d439a780e9aa4b7c2c45dd4254e533f0 (P7)
**Status:** PASS — seal checkpoint, zero new science

---

## Summary

After acceptance (P4), rekey (P6), and signal models (P7) all failed to earn
independent predictive credit, P7.5 formally defines and seals the minimal
surviving MVE object: the **causal morphic field state** — price mapped
through causal structural anchors and volatility into morphic coordinates and
sigma states.

A deterministic wrapper (`src/mve/core_state.py`) reproduces the sealed P7
pipeline series with **exact parity (max diff 0.0)** and passes the bounded
causality regression (future perturbation 0.0, truncation 0.0, 0 blocked
components, 0 leakage unknowns, 0 causal→ex-post dependencies). 2026 remains
untouched (holdout_rows_read = 0).

The core state is a causal representation of market structure, **not** a
validated alpha. Predictive alpha, standalone strategy, and economic
translation all remain unvalidated (false).

---

## Q1. What survived the MVE research program?

The **causal morphic field state**: causal structural anchors (trailing
extremes), causal volatility normalization (close_to_close), morphic
coordinates, and frozen sigma states — plus descriptive state transition /
survival primitives. These four components are classified
**CAUSAL_STATE_PRIMITIVE** (transitions: **CAUSAL_DESCRIPTIVE_PRIMITIVE**).

## Q2. What was falsified?

- **Acceptance** (P4): REDUNDANT — raw continuation lift fully explained by
  coordinate distance. PRUNED_PREDICTIVE.
- **RKEY-A / RKEY-B** (P6): REDUNDANT — LR flags n.s. after coordinate/sigma
  controls; B's delay buys nothing. PRUNED_PREDICTIVE.
- **Model A / Model B** (P7): REJECTED_REDUNDANT — no incremental info beyond
  coordinate/sigma/vol controls + baseline flag.
- **Model C** (P7): ARCHIVED_CONDITIONAL_NOT_INCREMENTAL — dev LR marginally
  significant, not confirmed, below N gate, displacement worse than direct 2σ.

## Q3. What remains blocked?

- **Model D**: BLOCKED_LOGIC_SPEC (unsatisfiable d1 conditions).
- **Model E**: BLOCKED_LOGIC_SPEC (whole-sample Q repaint).
- **generate_all_signals**: BLOCKED_AGGREGATE (includes Model E).
- **2026**: FINAL_HOLDOUT_PENDING.

## Q4. What exactly is the minimal MVE core?

```
PRICE
→ STRUCTURAL ANCHOR (causal trailing extremes, shift(1))
→ CAUSAL VOLATILITY NORMALIZATION (close_to_close)
→ MORPHIC COORDINATE (signed, vol-normalized)
→ SIGMA STATE (frozen quantization)
→ STATE TRANSITION / SURVIVAL DESCRIPTION
```

Formal definition in `MVE_P75_CORE_STATE_DEFINITION.md`; machine-readable
schema in `MVE_P75_CORE_STATE_SCHEMA.json`; deterministic implementation in
`src/mve/core_state.py`.

## Q5. Does the core have validated predictive alpha?

**NO / NOT YET.** `predictive_alpha_validated = false`. The core state
describes structure; P4-P7 established that the higher-order layers built on
it carry no independent predictive information, and the core field itself has
not been validated as a standalone edge.

## Q6. Why were acceptance and rekey removed?

Both were implemented causally and tested correctly. In both cases the raw
continuation behavior existed but **collapsed once coordinate distance and
sigma state were controlled** — the market continued because it was already
farther through the coordinate field, not because acceptance/rekey added
information. LR flag tests were n.s. (P4: acceptance explained by distance;
P6: q≈0.78 for RKEY effects).

## Q7. Why were Models A/B removed?

Both are near-deterministic transforms of the coordinate field: A is a
1σ-crossing + 1-bar confirmation, B is a threshold + 3-bar occupancy (itself a
coordinate transform). In paired incremental tests against the plain crossing
baseline with coordinate/sigma/vol controls, the model flag added no
information (A: dev LR p=0.21; B: p=0.084 — both n.s.). They are
REJECTED_REDUNDANT.

## Q8. Why was Model C not promoted?

Dev LR p=0.0147 (q=0.044) is nominally significant, but: N=111 below the
preregistered HIGH gate (N≥200); confirmation LR p=0.19 (effect does not
confirm); forward displacement is *worse* than the direct 2σ baseline (dev
−2.39, CI [−4.44, −0.12]); and the result rests on an extreme direction
asymmetry (102 negative-side vs 9 positive-side events). Disposition:
ARCHIVED_CONDITIONAL_NOT_INCREMENTAL — reopen only on a new independent
dataset with a preregistered hypothesis (see `MVE_P75_MODEL_C_ARCHIVE.md`).

## Q9. What does the core represent structurally?

A causal normalized structural-state representation: at every bar, where price
sits relative to evolving structural anchors, normalized by causal volatility,
quantized into sigma states, with a description of state transitions and
persistence. It is a **regime/conditioning lens**, not an entry system.

## Q10. What kind of future research is still scientifically legitimate?

All hypotheses for future work, none started here, each requiring separate
authorization:

1. Cross-asset / cross-pair generalization of the core state.
2. Regime descriptive study using the core state.
3. Core state as a conditioning variable for already-validated external alphas.
4. Independent-dataset validation of conditional Model C behavior.
5. State-transition forecasting with a new preregistered hypothesis.
6. Core state as a descriptive regime lens in the Shallow Well Foundry.

**Strategic recommendation (not tested):** the most likely valuable path is
**MVE core state as a regime/conditioning engine**, not MVE as a standalone
entry system.

---

## Verification record

| gate | result |
|------|--------|
| core parity (anchor/vol/coordinate/sigma vs sealed P7) | PASS — max diff 0.0 |
| future perturbation (coordinate/sigma/anchor/vol series) | 0.0 |
| truncation invariance | 0.0 |
| static leakage | 0 blocked, 0 unknowns |
| blocked-component isolation | PASS (no signals/rekey/acceptance events) |
| causal→ex-post dependencies | 0 |
| holdout | FINAL_HOLDOUT_PENDING, rows_read = 0, 0 rows in 2026 field |
| tests (MVE scope) | 242 passed, 3 skipped (incl. 17 new P7.5) |

## Decision

**mve_p75_core_state_seal_pass = true**

P7 conclusions frozen correctly, no model rescue, minimal core defined,
schema complete, wrapper deterministic, parity passes, causality passes,
registry complete, Model C disposition explicit, D/E blocked, holdout
untouched, no new science, no trading rule, P8 not auto-authorized.

Next recommended checkpoint: **MVE-P8-*** (generalization / regime
conditioning / external-alpha conditioning) — **NOT AUTHORIZED**, pending
human review.
