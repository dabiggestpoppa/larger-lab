# TEMPORAL ANALYSIS PROTOCOL — LOWER-FIELD-13 (MANDATORY)

Every temporal object in LF13 reports BOTH static-horizon and rolling-window
values. Disagreements between the two are REPORTED, never silently resolved.

## Static horizons (forward-looking, fixed window)

- 1D / 3D / 7D / 14D / 30D / 60D
- Measures: peer negative fraction, peer touch fraction, forward signed
  return, forward rank velocity, forward cumulative magnitude.
- 60D is NOT available in the LF12 frame for several measures — reported as
  n/a rather than fabricated (see `lf13_common.STATIC_MAP`).

## Rolling windows (trailing, PIT-safe)

- 3D / 7D / 14D / 30D (60D only when support is adequate)
- Computed as trailing MARKET-LEVEL means over past dates (closed='left'),
  so only past information feeds the window — no lookahead.
- Columns: `roll_<measure>_<horizon>` (see `lf13_common.rolling_protocol`).

## Per-object reporting requirement

For each temporal object:

- static-horizon value(s)
- rolling-window value(s)
- peak / trough across static horizons
- first meaningful deviation
- normalization / persistence (last static vs peak)
- subperiod stability (consistency across the five subperiods)

If static and rolling interpretations DISAGREE, the output records the
disagreement in its note (e.g., output 26: static and rolling agree there is
no early reach advantage; output 15: species differ in static reach but share
rolling context).

## Hard-parked objects (referenced only, not reopened)

Cumulative damage acceleration · branching/criticality · relational-distance
routing at daily resolution · universal recovery clock · relational-state
prediction · static peer graph · standalone EARLY_CONTAGION · rescue PRD
subtypes.

## Scope

Research only: no strategy, no PnL, no execution, no sizing, no leverage.
