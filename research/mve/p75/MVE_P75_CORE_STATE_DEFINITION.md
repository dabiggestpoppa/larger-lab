# MVE Core State — Formal Definition (P7.5)

## Statement

**MVE is a causal normalized structural-state representation that maps price
relative to evolving structural anchors into morphic/sigma coordinates.**

The core state is a **CAUSAL REPRESENTATION OF MARKET STRUCTURE**.
It is **NOT** a validated trading strategy, a positive-EV signal, a deployable
engine, or profitable alpha. No claim of predictive edge is made by this
definition.

## Canonical Architecture (what survived falsification)

```
PRICE
→ STRUCTURAL ANCHOR (causal trailing extremes, shift(1))
→ CAUSAL VOLATILITY NORMALIZATION (close_to_close)
→ MORPHIC COORDINATE (signed, vol-normalized)
→ SIGMA STATE (frozen quantization)
→ STATE TRANSITION / SURVIVAL DESCRIPTION
```

This is the entire surviving scientific core. The following were tested and
failed to earn independent predictive credit, so they are **not** layers of
the canonical architecture:

- acceptance (P4: REDUNDANT)
- rekey (P6: REDUNDANT / INSUFFICIENT_N)
- Model A / Model B (P7: REDUNDANT)
- Model C (P7: CONDITIONAL_NOT_INCREMENTAL)

## What each primitive is

| primitive | definition | causal at bar t? |
|-----------|-----------|------------------|
| structural anchor | trailing max/min of close over 50 bars, `shift(1)` | yes (uses data through t-1) |
| volatility | `close_to_close` estimator (sealed) | yes |
| morphic coordinate | `ln(close/anchor)/vol`, signed per boundary family | yes |
| sigma state | `sign(x)*floor(\|x\|/STEP)`, STEP=1.0 (P7 convention); unsigned `floor(\|x\|)` band (P4/P6 convention) | yes |
| state transition | UP/DOWN/STAY vs previous sigma state | yes (descriptive) |

The `src/mve/core_state.py` wrapper exposes these per-bar. It reuses sealed
implementations (no duplicated math), imports no pruned/blocked science, and
contains no strategy/PnL logic.

## Schema

See `MVE_P75_CORE_STATE_SCHEMA.json` for the full machine-readable contract.
Every field is causal: all inputs at bar t use data with index <= t, and
`causal_known_time == timestamp` for every row.

## Distinctions preserved

1. **Core state ≠ alpha.** The core state describes structure; it does not
   claim to predict price.
2. **Descriptive vs predictive.** State transitions and survival are
   descriptive primitives. P4-P7 established they carry no *independent
   predictive* information beyond the field itself.
3. **Legacy architecture deprecated.** Any document showing
   `coordinates → acceptance → rekey → model signal` is
   `LEGACY_RESEARCH_ARCHITECTURE` (see `MVE_P75_LEGACY_ARCHITECTURE_MAP.md`).

## Future research (NOT started here)

Legitimate directions, each requiring separate authorization:

- cross-asset / cross-pair generalization of the core state
- regime descriptive study using the core state
- core state as a conditioning variable for already-validated external alphas
- independent-dataset validation of conditional Model C behavior
- state-transition forecasting with a new preregistered hypothesis
- core state as a regime/conditioning lens in the Shallow Well Foundry

All are hypotheses for future work. None are assumed to work.
