# BLOC 12 — RESEARCH READINESS SCORING + RESTART POLICY

## 1. Purpose

Define exactly when the finished sensor fabric is allowed to hand evidence back to research.

The system must never collapse readiness to `data_ready = true`.

---

## 2. Readiness is scoped

Every readiness decision is keyed by:

```text
research_program
sensor_family
asset_or_universe
venue_scope
start
end
granularity
required_windows
required_redundancy
required_quality
required_event_overlap
replay_mode
generation_lock
```

A scope can be ready while another remains blocked.

---

## 3. Readiness dimensions

Each research scope reports a vector, not only one score.

```text
ACCESS
HISTORICAL_DEPTH
EVENT_OVERLAP
T0_INTEGRITY
T1_PIT_VALIDITY
IDENTITY_CONFIDENCE
SEMANTIC_CONFIDENCE
INDEPENDENT_REDUNDANCY
COVERAGE
FRESHNESS
LIVE_VALIDATION
REPLAY_DETERMINISM
LINEAGE_COMPLETENESS
NULL_BURDEN
PROVIDER_CONCENTRATION
```

For convenience a summary score may be shown, but hard gates override it.

---

## 4. Readiness classes

```text
R0_NOT_READY
R1_LOCAL_DESCRIPTIVE
R2_LOCAL_MECHANISM_READY
R3_CROSS_PROVIDER_READY
R4_CROSS_VENUE_READY
R5_MULTI_ERA_READY
R6_SHADOW_LIVE_READY
```

### R1_LOCAL_DESCRIPTIVE
One valid source/venue can support descriptive inspection only.

### R2_LOCAL_MECHANISM_READY
Local mechanism study is valid with sufficient history/quality but no broad cross-venue claims.

### R3_CROSS_PROVIDER_READY
Independent corroboration exists, but cross-venue arithmetic may still be restricted.

### R4_CROSS_VENUE_READY
Semantic comparability, independence and coverage support cross-venue breadth/consensus/dispersion.

### R5_MULTI_ERA_READY
The scope spans the required historical eras and event windows with stable replay semantics.

### R6_SHADOW_LIVE_READY
Historical and live compilers have passed equivalence on the same closed intervals.

---

## 5. Hard blocking conditions

The following force `R0_NOT_READY` for affected scope:

- free-only violation;
- broken T0 lineage;
- unresolved PIT leakage;
- unknown unit/side semantics in a required sensor;
- source mutation ambiguity without explicit revision selection;
- replay nondeterminism;
- historical/live semantic mismatch;
- required event-window data unavailable;
- quality mode `DATA_BLOCKED` for a required mechanic;
- requested cross-venue operation forbidden by comparability/independence policy.

No weighted score can overcome these.

---

## 6. NULL burden

Readiness must quantify not only coverage percentage but where missingness occurs.

Required fields:

```text
null_fraction_total
null_fraction_pre_event
null_fraction_event
null_fraction_post_event
null_fraction_by_sign
null_fraction_by_rank
null_fraction_by_era
null_reason_breakdown
```

This is especially important for LF14 because asymmetric mechanical availability across upside/downside events can bias the mechanism comparison.

---

## 7. Event-window readiness

For event-driven research the fabric must answer:

```text
PRECONDITION
INITIATION
ABSORPTION
REORGANIZATION
PROPAGATION
CONTAINMENT
RECOVERY / REJOIN / DECOUPLING
```

For each stage:
- sensor availability;
- provider count;
- independent count;
- quality mode;
- coverage;
- static/rolling history support;
- NullBoundary reason where absent.

A year-level coverage score does not substitute for event-stage overlap.

---

## 8. Static + rolling readiness

Where temporal analysis is requested, the research packet must expose both:

```text
STATIC
1D / 3D / 7D / 14D / 30D / 60D

ROLLING
3D / 7D / 14D / 30D
60D where supported
```

For every horizon report:
- N;
- valid fraction;
- source set;
- independent source count;
- baseline support;
- quality mode.

A horizon with inadequate support is returned as unsupported/NULL, not interpolated.

---

## 9. Restart policy for MECH-21

MECH-21 may resume when the relevant global mechanic scopes satisfy, at minimum:

1. replay deterministic under `AS_KNOWN_THEN`;
2. required T2 states accessible through Bloc 10;
3. liquidation / OI / funding / flow mechanics have declared coverage across sentinel eras;
4. liquidity/depth may be local or partially blocked, but the gap must be explicit;
5. forcing-family analyses can request canonical state packets without provider-native code;
6. transfer/realization analyses know exactly which mechanics are observed vs missing;
7. 2022 and recurrent low-gain periods have declared mechanical coverage;
8. any seasonality test includes availability/confounding metadata.

MECH-21 does not require every sensor to be R6. It requires honest scope-specific readiness for the questions it asks.

---

## 10. Restart policy for LF14

LF14 has a stricter mechanical requirement because sign-asymmetry localization is its primary unresolved problem.

Minimum restart packet should attempt, subject to actual data availability:

```text
liquidation intensity
liquidation breadth
OI level/change/velocity
funding level/change
aggressor imbalance
signed flow / CVD
spread expansion
depth withdrawal
slippage / liquidity recovery
venue breadth
venue concentration
venue dispersion
```

LF14 may resume with partial mechanical coverage only if:
- missingness is explicit by event/sign/stage;
- matched samples are recomputed under sensor availability;
- no missing mechanic is silently proxied;
- sign residual estimates are labeled conditional on available mechanics;
- DATA_BLOCKED remainder remains legal final status.

---

## 11. Final restart verdicts

For each research program:

```text
RESTART_AUTHORIZABLE_FULL
RESTART_AUTHORIZABLE_SCOPED
RESTART_LOCAL_ONLY
HOLD_DATA_BLOCKED
HOLD_VALIDATION_FAILED
```

The infrastructure agent may only recommend one of these.

Human operator authorization is still mandatory.

---

## 12. Promotion firewall

Research statuses remain:

```text
PROMOTED
LOCAL
DESCRIPTIVE
PARKED
NULL
DATA_BLOCKED
```

Bloc 12 cannot promote a mechanism.

It can only say whether the measurement substrate is ready to test it.

---

## 13. Research readiness report

Required final human-facing report sections:

1. what is fully ready;
2. what is degraded but usable;
3. what is local-only;
4. what remains DATA_BLOCKED;
5. what historical eras are strong/weak;
6. what event stages are strong/weak;
7. what sensors are provider-concentrated;
8. where sign-conditional missingness exists;
9. what can be re-run reproducibly today;
10. recommended MECH-21/LF14 restart scope.
