# PFT Pre-Build Planning — B0 through B3

Purpose: design the laboratory before economic backtesting. This document freezes the intended pre-PnL build scope for the next master prompt.

## Current Gate

```text
PFT PROGRAM       = APPROVED
A0 GENESIS        = REGISTERED
A1 DEEPERS v2.2   = FROZEN
Q0 TRANSMISSION   = REGISTERED
B0 CONSTITUTION   = READY TO BUILD
B1 SPEC SEAL      = READY TO BUILD
B2 DATA TRUTH     = READY TO BUILD/AUDIT
B3 MATH/CAUSALITY = READY TO BUILD/TEST
ECONOMIC PNL      = NOT AUTHORIZED
CONFIRMATION      = UNTOUCHED
HOLDOUT           = UNTOUCHED
```

## B0 — Program Constitution

### Experiment Identity

Every experiment gets a permanent immutable ID such as:

- `PFT-A1-K1-RAW-001`
- `PFT-A1-K2-RAW-001`
- `PFT-A1-K3-RAW-001`
- `PFT-A1-K4-RAW-001`
- `PFT-A1-FULL-RAW-001`
- `PFT-Q0-BASE-001`

One experiment identity binds spec, data, code, costs, execution model, parameters and seed. A material change creates a new experiment generation.

### Generation IDs

Every artifact/result carries:

- `SPEC_GEN`
- `DATA_GEN`
- `ENGINE_GEN`
- `COST_GEN`
- `EXEC_GEN`
- commit/code hash
- deterministic seed if applicable

### Data-Use Ledger

Record every access to development/confirmation/holdout with dataset, date range, purpose, agent, timestamp and experiment ID. Confirmation and holdout must fail closed during B0-B11 unless specifically authorized later.

### Result Immutability

Completed runs are never deleted. Bugged runs are marked invalid and superseded by a new generation.

### Agent Authority

Builder may implement code/tests/audits/artifacts and approved experiments. Builder may not tune thresholds, change Deepers v2.2, inspect holdout, change split because of PnL, replace instruments, alter costs after results, promote candidates, deploy capital or use Kelly.

## B1 — Specification Seal

### Machine-Readable Spec

Create a structured A1 v2.2 configuration/specification containing all assets, windows, time semantics, constants, schedules, state rules, fail-closed behavior and execution precedence. Implementation should reference the spec rather than scattering magic numbers.

### Formula Registry

At minimum identify:

- `A1.F01.LOG_RETURN`
- `A1.F02.PARKINSON_14H`
- `A1.F03.GAMMA_RAW`
- `A1.F04.GAMMA_SMA3`
- `A1.F05.ACCELERATION`
- `A1.F06.DMD_OPERATOR`
- `A1.F07.PHASE_DISTANCE`
- `A1.F08.VR_DISTANCE`
- `A1.F09.K3_OLS`
- `A1.F10.K4_RV6`
- `A1.F11.COMMUTATOR`
- `A1.F12.DRAWDOWN`

### RAW/TWIN Isolation

Physically separate RAW and TWIN implementations. RAW must not import TWIN behavior.

### Fail-Closed Cases

Examples:

- no eligible DMD mode -> `w3=0`, reason logged.
- K3 literal OLS singular/unstable -> `K3_OLS_VALID=false`, `w2=0`, reason logged.
- missing required market input beyond allowed stale condition -> affected kernel invalid.
- terminal DD kill -> no future signals without explicit reset/new generation.

### Frozen Precedence

`Data -> Features -> K1/K2/K3/K4 -> FSM -> GrossCap -> Fade -> DD -> LegStop -> Target -> Execution`

## B2 — Data Truth

### Required Primary Data

- ICE Brent front-month/continuous H1 signal history.
- Brent CFD execution history or documented execution proxy.
- EURUSD H1.
- USDCAD H1.
- EURCAD H1 direct executable series.
- GDAXI cash index H1 signal history.
- DAX CFD execution history or documented execution proxy.

### Evidence Grades

- A: exchange/broker executable data.
- B: institutional-quality vendor.
- C: reputable historical provider.
- D: reconstructed/proxy.

Results must state whether execution evidence is observed or proxy.

### Brent Roll Audit

Retain contract, expiry, roll date, roll method and adjustment method. Roll flags are mandatory so futures roll discontinuities cannot masquerade as oil acceleration.

### Canonical Synchronization

Canonical timezone: `America/New_York`.

Every asset record should carry:

- `bar_valid`
- `market_open`
- `stale`
- `stale_age_hours`
- `source_timestamp`
- `canonical_timestamp`
- `price_origin` = observed / carried-stale

Deepers RAW uses carried last price and `r=0` for expected closed/stale slots, but the stale provenance must remain explicit.

### Missingness Categories

- EXPECTED_CLOSED
- UNEXPECTED_MISSING
- BAD_BAR

Unexpected missing data must not silently become a zero-return expected-closure observation.

### OHLC Invariants

Require:

- `H >= max(O,C)`
- `L <= min(O,C)`
- `H >= L`

Bad bars are quarantined, not silently repaired.

### Extreme-Event Audit

Flag extreme returns as REAL / ROLL / BAD_PRINT / UNRESOLVED. Do not auto-delete genuine tail events.

### Direct vs Synthetic EURCAD Parity

Diagnostic only:

`r_synth = r_EURUSD + r_USDCAD`

`tri_error = r_direct_EURCAD - r_synth`

Use to detect timing/bad-bar/stale convention mismatches, not to rewrite RAW.

### Coverage Report

Report start/end, canonical slots, valid, stale, missing, bad and common synchronized coverage for every asset.

### Hashing

SHA256 all raw inputs, normalized datasets and synchronized panels.

## B3 — Mathematical and Causal Conformance

No economic interpretation until conformance passes.

### Required Reference Fixtures

1. Log-return hand fixture.
2. Parkinson 14H hand fixture, plus future perturbation.
3. Gamma fixture using `H=100,L=90,C=99 -> gamma=-0.8`; v2.2 oil sign must produce long direction when activation is otherwise valid.
4. DMD synthetic linear system with known complex eigenvalues/modes.
5. Circular phase wrapping fixture near +/-pi.
6. VR point-cloud fixtures: no hole, one unfilled loop, filled loop.
7. K3 OLS fixture with known coefficients and strict lagged fit.
8. K3 singular/collinear fixture -> fail closed, no pseudoinverse.
9. K4 commutator hand fixture, including intentional use of current A_t/B_t for k=1.
10. RV6 fixture: exactly six returns, `ddof=1`, nonannualized.
11. Exhaustive FSM transition table including repeated flip and neutral during fade.
12. Gross-cap fixture verifying sum(abs(weights)) <= 1.
13. DD fixtures at <12%, 15%, 18%, and terminal 19.5%.
14. Terminal-state persistence fixture.
15. Leg-stop fixture including 12-H1-bar execution ban.
16. Future perturbation invariance.
17. Truncation invariance.
18. Same-bar execution prohibition / next-executable-price contract.
19. Numerical determinism from identical data/spec/code/seed.

### Pre-PnL Diagnostics

Before calculating strategy returns, emit feature/activation distributions only.

K1:
- valid-mode rate
- DeltaPhi quantiles
- activation rate `DeltaPhi>1.57`

K2:
- gamma quantiles
- acceleration quantiles
- joint threshold activation rate

K3:
- NO_HOLE / FRAGILE / PERSISTENT / OLS_INVALID counts and rates

K4:
- alpha_D quantiles
- `|w_total|>=0.05` activation rate

### Activation Census

Create `ACTIVATION_CENSUS.csv` with at least:

- valid_observations
- invalid_observations
- activation_count
- activation_rate
- mean_duration
- median_duration
- overlap_with_other_kernels
- stale_market_fraction
- session_distribution
- year_distribution

### Signal Funnel

Track:

`All H1 -> Valid synchronized -> K4 active cluster -> K1/K2 availability -> K3 state -> Nonzero target -> Gross cap -> Fade -> DD -> Leg stop -> Executable position`

Purpose: distinguish no edge from a gating system that is practically inert.

## Pre-Registered Null Families

Write these before economic PnL:

- K1 spectral null: randomized phase preserving appropriate magnitude structure.
- K2 directional null: preserve activation times, randomize gamma sign.
- K3 topology null: random market-node labels / appropriate topology surrogate.
- K4 timing null: dependency-aware block permutation of A relative to B.
- Market null: matched-volatility periods without qualifying oil state.
- Timing shifts: preregistered `-24,-12,-6,-3,+3,+6,+12,+24h` diagnostic shifts.
- Simple baselines: Brent momentum, Brent mean reversion, EURCAD momentum, DAX fade, simple oil-to-CAD directional relation.

Nulls and twins are not authorized to overwrite RAW.

## Still Prohibited Before B3 Review

- threshold search
- parameter grid optimization
- best-lag search
- best-instrument selection
- PF/Sharpe/DD optimization
- feature selection from PnL
- confirmation access
- holdout access
- economic A0/A1/Q0 PnL

## Pre-Economic Stop Condition

The B0-B3 builder must stop and report for human review after producing:

- B0 constitution/artifacts
- B1 frozen machine spec/formula registry
- B2 data truth/hash/coverage evidence or explicit blockers
- B3 conformance/causality test report
- activation census and feature distributions only
- no economic strategy PnL

The next master prompt should authorize B0-B3 only and explicitly prohibit advancing to B4 without operator approval.
