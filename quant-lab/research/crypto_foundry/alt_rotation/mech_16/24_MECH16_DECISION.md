# CRYPTO-ALT-MECH-16 — DECISION

## Verdict

**PASS_MECH16_TOPOLOGY_STABLE_TRANSFER_DRIFT**

## Decision questions

- **1. Was the MECH-15 chronological failure reproduced?** yes on 16-cell propagation ordering (rho -0.50), while 16-cell topology (branch/self-transition/dir-entropy) mean 0.77 — reproduced and localized to transfer metrics (prop/rank) on sparse cells
- **2. Is it topology drift or transfer-function drift?** MIXED_DRIFT — topology 6-cell chrono 0.87 (LOSO 0.99) vs transfer -0.07: roads stable, conditional response reorders (WS3 + WS4 drift fraction 0.68)
- **3. Does 6-cell or 8-cell representation survive better?** both stable; DUAL_RESOLUTION (rank retention 0.96 vs 0.74)
- **4. Should Market OS carry dual resolution?** yes — DUAL_RESOLUTION
- **5. Is state x age transportable?** UNSTABLE_CLOCK
- **6. Is entropy transportable?** ENTROPY_RESPONSE_DRIFT
- **7. Is common forcing transportable?** FULL_FORCING_DRIFT
- **8. Are rank activation thresholds drifting?** DEEP_THRESHOLDS_DRIFT — deep-patch audit: 6 STATIONARY (incl. saturated) / 1 DRIFT patches
- **9. Are roads stable while traffic rates change?** FULL_STABILITY
- **10. Did birth geometry change?** BOTH
- **11. Which nodes qualify as near-invariants?** BREADTH_X_DISPERSION_STATE_TOPOLOGY; SPATIAL_ACTIVATION_COORDINATE; LOCAL_HIGHWAYS_EXITS
- **12. Is Field Model v1 ready for freeze after this checkpoint?** CONDITIONAL_FREEZE_INPUT — 3/8 invariant nodes; see 22_FIELD_MODEL_V1_FREEZE_INPUT.md

## Node actions

- DISSOLVE: 16-CELL_RAW_SURFACE (REPLACED_BY_REDUCED)
- PROMOTE: 6-CELL_OPERATIONAL_SURFACE (DUAL_RESOLUTION)
- PROMOTE: 8-CELL_RANK_SURFACE (DUAL_RESOLUTION)
- DESCRIPTIVE: 4-CELL_SURFACE (NOT_SELECTED)
- PROMOTE: 4-STATE_BASELINE (EARNED)
- PROMOTE: MARKET_OS_STATE_SURFACE (FREEZE_CANDIDATE)
- PROMOTE: BREADTH_X_DISPERSION_STATE_TOPOLOGY (INVARIANT)
- DISSOLVE: STATE_X_AGE_CLOCK_LAW (DISSOLVE)
- PROMOTE: SPATIAL_ACTIVATION_COORDINATE (INVARIANT)
- LOCAL_NODE: AGE_RESIDUALIZED_ENTROPY (REGIME_MODULATED)
- LOCAL_NODE: COMMON_FORCING_COORDINATE (REGIME_MODULATED)
- DESCRIPTIVE: THRESHOLD_HIERARCHY (LOCAL_ONLY)
- LOCAL_NODE: PHYSICAL_VS_SIGMA_SEPARATION (REGIME_MODULATED)
- PROMOTE: LOCAL_HIGHWAYS_EXITS (INVARIANT)

## Formal negatives / not carried

- Metastability: dead. Universal sequence grammar: demoted.
- Single hidden coordinate / single initiation primitive: null.
- Chronological instability on the raw 16-cell is an artifact of sparse cells, not evidence of topology drift.
- No changepoint is forced; only aligned multi-coordinate windows are reported.
- SoSoValue ETF context: DATA_BLOCKED (no local data).
- DAR remains pilot.

## Limits

- Descriptive (<= L2); no strategy translation.
- Regime definitions use law signatures, never price direction.
- 8-cell is a research surface; 6-cell remains operational unless human review prefers dual resolution.

`human_review_required = TRUE`
`next_checkpoint_authorized = FALSE`
NO STRATEGY · NO PNL · NO EXECUTION · NO ENTRY/EXIT · NO SIZING · NO LEVERAGE · NO DEPLOYMENT
