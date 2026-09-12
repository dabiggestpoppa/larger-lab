# BLOC 9 — TEMPORAL BASELINES, STATE TRANSITIONS & MATERIALITY

## 1. Purpose

Define how raw mechanical values become context-aware state without confusing statistical extremeness with economic importance.

---

## 2. Physical amplitude and standardized amplitude are separate

Every normalized observable should preserve physical magnitude where economically meaningful.

Example:

```text
liquidation_notional_usd = 25,000,000
liquidation_percentile = 97.2
liquidation_robust_sigma = 2.4
```

The fabric must not collapse these into one number.

A 2σ event can be physically small. A 1σ event can be physically huge in a structurally larger regime.

---

## 3. Baseline families

Permitted baseline types:

```text
ROLLING_EMPIRICAL
ROLLING_ROBUST_Z
EXPANDING_PIT
VENUE_LOCAL_SEASONAL
CROSS_SECTIONAL_PIT
EVENT_RELATIVE
```

Each baseline registry entry records:

```text
baseline_id
version
family
lookback
minimum_samples
calendar_controls
winsorization_policy
missingness_policy
valid_from
invalid_from
```

No hidden baseline changes.

---

## 4. Frozen multi-horizon protocol

For research-facing temporal states, support both:

```text
STATIC HORIZONS
1D / 3D / 7D / 14D / 30D / 60D

ROLLING WINDOWS
3D / 7D / 14D / 30D
+ 60D when support is adequate
```

Intraday layers may additionally expose:

```text
1m / 5m / 15m / 1h / 4h / 12h
```

Static and rolling results must remain separately named.

---

## 5. State transition objects

Bloc 9 may derive descriptive transitions such as:

```text
QUIET → ELEVATED
ELEVATED → BURST
EXPANSION → COMPRESSION
WITHDRAWAL → RECOVERY
DISPERSED → CONSENSUS
LOCAL → BROAD
```

Every transition stores:

```text
from_state
to_state
transition_at
horizon
methodology_version
input_quality
lineage_ref
```

Transitions are observations about state evolution, not predictions.

---

## 6. Transition velocity and persistence

Candidate temporal coordinates:

```text
state_age
transition_count
transition_velocity
persistence_duration
time_since_last_transition
recovery_duration
```

No universal clock is assumed.

Clock behavior may differ by sensor family, asset rank, venue, regime, or event type.

---

## 7. Materiality envelope

Statistical extremeness alone is insufficient.

A materiality envelope may include separate coordinates:

```text
physical_amplitude
standardized_amplitude
breadth
persistence
coverage
independent_source_count
venue_concentration
```

No single scalar materiality score is frozen in v1.

Instead, downstream research can test which combination matters.

---

## 8. Event-relative slices

For research episodes, T2 computation must support aligned event windows:

```text
T-30D
T-14D
T-7D
T-3D
T-1D
T0
T+1D
T+3D
T+7D
T+14D
T+30D
```

and finer intraday windows where source support exists.

This allows later LF14-style questions:

```text
What diverged before absorption?
What changed during reorganization?
What broadened during propagation?
What normalized during containment?
```

---

## 9. State-local percentile doctrine

Percentiles may be conditioned by a clearly versioned local context only when justified.

Possible contexts:

```text
venue
asset
instrument type
rank tier
global field state
calendar bucket
```

But over-conditioning can manufacture extremes from tiny samples.

Therefore every contextual baseline must expose sample support and fall back only under explicit policy.

---

## 10. Calendar / seasonality handling

Bloc 9 may expose calendar-conditioned descriptive baselines, but must never assume seasonality is causal.

Calendar context may include:

```text
hour-of-day
session
weekday
month
quarter
```

Any seasonal normalization must remain reconstructable PIT and must not leak later years into earlier baselines.

---

## 11. Regime adaptation

Baselines can drift over time.

The fabric supports versioned dynamic baselines rather than freezing one 2021 distribution forever.

However, dynamic adaptation must preserve:

```text
baseline_at_t
sample history used
methodology version
```

so historical replay remains reproducible.

---

## 12. Coverage-aware windows

A rolling window must not quietly compute on 20% of expected samples.

Every methodology defines:

```text
min_coverage_fraction
min_sample_count
max_allowed_gap
```

Failure emits:

```text
INSUFFICIENT_COVERAGE
```

not a weakly supported number disguised as normal.

---

## 13. State labels are secondary

Continuous coordinates remain primary.

Labels such as:

```text
BURST
BROAD_COMPRESSION
LIQUIDITY_WITHDRAWAL
```

are convenience descriptions built on continuous surfaces.

Research should be able to bypass labels and use the underlying coordinates directly.

---

## 14. Frozen rule

Bloc 9 may describe how state changed, how broad it became, how persistent it was, and how physically/statistically large it was.

It may not turn those states into trade permission or future-return labels.
