# FIELD MODEL v1 — FREEZE INPUT (MECH-16)

**Status**: input artifact only. No production code, no strategy translation, no execution.

## 1. Surface

- MECH-15 6-cell reduced surface survives transportability checks (topology chrono rho 0.87, LOSO 0.99); 8-cell carried for rank research (rank retention 0.96 vs 0.74).
- WS2 freeze recommendation: DUAL_RESOLUTION.
- WS16 roads test: FULL_STABILITY.

## 2. Invariant nodes (freeze candidates)

- **BREADTH_X_DISPERSION_STATE_TOPOLOGY**: INVARIANT — 4-state ordering mean rho=0.729 (42 tests)
- **STATE_X_AGE_CLOCK_LAW**: DISSOLVE — WS6=UNSTABLE_CLOCK
- **SPATIAL_ACTIVATION_COORDINATE**: INVARIANT — HA-vs-LA prop7 gap sign per subperiod: {'2020-2021': 1, '2022': 1, '2023': 1, '2024': 1, '2025-2026': 1}
- **AGE_RESIDUALIZED_ENTROPY**: REGIME_MODULATED — WS8=ENTROPY_RESPONSE_DRIFT
- **COMMON_FORCING_COORDINATE**: REGIME_MODULATED — WS9=FULL_FORCING_DRIFT
- **THRESHOLD_HIERARCHY**: LOCAL_ONLY — only deep patches have estimable thresholds (shallow always-on); hierarchy not fully testable
- **PHYSICAL_VS_SIGMA_SEPARATION**: REGIME_MODULATED — corr(|ret|,sigma) mean=0.43 sd=0.21; rho(phys,std) max=0.87
- **LOCAL_HIGHWAYS_EXITS**: INVARIANT — WS16=FULL_STABILITY

## 3. Regime modulation

- Transfer functions: DRIFT_SLOPES (WS4 drift fraction 0.68).
- Covariate/conditional shift: MIXED_DRIFT.
- Law regimes: NO_NAMED_REGIMES.
- Changepoint aligned windows: 1.
- Rank thresholds: DEEP_THRESHOLDS_DRIFT; saturation law: SATURATED_STABLE; forcing law: FULL_FORCING_DRIFT.
- State x age clock: UNSTABLE_CLOCK; entropy law: ENTROPY_RESPONSE_DRIFT.
- Direction constraint transport: DIRECTION_CONSTRAINT_TRANSPORTS.

## 4. Open questions before final freeze

- Chronological 80/20 remains the weak test; reduce to 6-cell + 4-state as the canonical ordering surfaces.
- Rank-threshold drift deserves a dedicated deep-patch audit if 8-cell is carried operationally.
- DAR stays pilot; relational state and asset health remain downstream overlays.

`human_review_required = TRUE` · `next_checkpoint_authorized = FALSE`
