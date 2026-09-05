# BLOC 12 — MECH-21 / LF14 RESEARCH RESTART PACKET CONTRACT

## 1. Purpose

Define the exact handoff from infrastructure certification back into the paused research programs.

The restart packet must allow MECH-21 and LOWER-FIELD-14 to resume without touching provider APIs, provider-native schemas, raw filesystem paths or hidden normalization assumptions.

---

## 2. Common restart packet

Both research agents receive a versioned `ResearchRestartPacket` containing:

```text
packet_id
created_at
system_validation_run_id
recommended_restart_verdict
human_review_required
next_checkpoint_authorized
certified_generations
replay_mode
research_scope
sensor_readiness_matrix
historical_coverage_matrix
source_independence_matrix
provider_concentration_matrix
null_boundary_index
quality_policy_version
observable_registry_version
baseline_registry_version
reproducibility_receipts
known_limitations
blocking_issues
```

Default:

```text
human_review_required = TRUE
next_checkpoint_authorized = FALSE
```

---

## 3. MECH-21 packet

### 3.1 Parent research state

Primary parent:

`MECH20 @ da4b9cd7302c6dcf8790ae51eed29f21dfb98df1`

MECH-21 planned scope remains unchanged conceptually; the new packet enriches its mechanical evidence layer.

### 3.2 Required canonical mechanic groups

Where certified, expose:

```text
LeverageState
FundingState
OrderFlowState
LiquidationState
LiquidityState
PositioningState
BasisState

LeverageCompression
FundingConsensus
FlowConsensus
LiquidationBreadth
LiquidityWithdrawalBreadth
VenueDispersion
```

### 3.3 MECH-21 research joins

Packet must support joins around:

- response-law gain transitions;
- ceiling transitions;
- saturation onset/slope/ceiling;
- sterile saturation;
- threshold × transfer realization;
- absorptive capacity;
- forcing-family composition;
- load-resolution mismatch;
- recurrent low-gain states;
- 2022 modulation;
- calendar/seasonal hypotheses;
- viable birth / abort pathways.

Infrastructure must not encode a conclusion about these joins.

### 3.4 Mandatory temporal support

When relevant, provide both:

```text
STATIC 1D / 3D / 7D / 14D / 30D / 60D
ROLLING 3D / 7D / 14D / 30D / 60D where supported
```

with support and quality metadata.

### 3.5 Transfer target-overlap safety

Because MECH-20 explicitly raised transfer-target overlap/leakage risk, the restart packet must identify:

- exact T2 features used as candidate transfer mechanics;
- any temporal overlap between target labels and mechanical windows;
- whether mechanics were available strictly before target realization;
- any features disallowed for pre-event causal/predictive interpretation.

The packet itself does not fix research leakage; it gives MECH-21 enough temporal lineage to audit it.

---

## 4. LF14 packet

### 4.1 Parent research state

Primary parent:

`LF13 @ 9243201b4797b4b98cc446d1f13871668907ca79`

LF14 remains the final focused local precision turn.

### 4.2 Primary unresolved question

Mechanically localize the downside propagation/sign-asymmetry residual after matching structural and state covariates.

The packet must therefore maximize direct mechanical evidence around matched upside/downside events.

### 4.3 Required event mechanics

Where available:

```text
LIQUIDATIONS
  long_liq_usd
  short_liq_usd
  total_liq_usd
  liquidation_imbalance
  liquidation_intensity_vs_oi
  liquidation_breadth
  liquidation_acceleration

LEVERAGE
  oi_usd
  oi_change
  oi_velocity
  oi_acceleration
  leverage_compression

FUNDING
  funding_native
  normalized contextual equivalent
  funding_change
  funding_percentile
  funding_dispersion

ORDER FLOW
  taker_buy_usd
  taker_sell_usd
  taker_imbalance
  signed_flow
  cvd
  cvd_slope
  cross_venue_flow_consensus

LIQUIDITY
  spread_bps
  spread_expansion
  depth_5bps / 10bps / 25bps / 50bps
  depth_withdrawal
  book_imbalance
  slippage
  liquidity_recovery

CROSS-VENUE
  breadth
  concentration
  dispersion
  independent_source_count
```

### 4.4 Stage alignment

Packet must support alignment to LF stages:

```text
PRE-SHOCK / PRECONDITION
INITIATION
ABSORPTION
REORGANIZATION
PROPAGATION
CONTAINMENT
REACTIVATION / PERSISTENCE
REJOIN / DECOUPLING
```

LF14 owns exact stage definitions.

### 4.5 Matching / missingness contract

For every event and mechanic expose:

```text
available
quality_mode
provider_set
independent_provider_count
coverage
first_available_at
last_available_at
null_reason
```

LF14 must be able to recompute matched samples under identical mechanical availability.

A mechanical feature cannot enter the sign-residual model if availability itself makes the sign comparison non-comparable without an explicit sensitivity test.

### 4.6 Final sign-mechanism verdict vocabulary

Infrastructure preserves LF14 planned result states:

```text
MECHANICALLY_EXPLAINED
PARTIALLY_MECHANICAL
STAGE_LOCAL_SIGN_LAW
IRREDUCIBLE_AFTER_MECHANICS
DATA_BLOCKED_REMAINDER
```

Bloc 12 does not choose the verdict.

---

## 5. Research packet file outputs

Implementation should generate a directory such as:

```text
quant-lab/research/crypto_foundry/restart_packets/<validation_run_id>/
  SYSTEM_READINESS.md
  SYSTEM_READINESS.json
  MECH21_RESTART.md
  MECH21_RESTART.json
  LF14_RESTART.md
  LF14_RESTART.json
  SENSOR_READINESS.parquet
  EVENT_COVERAGE.parquet
  NULL_BOUNDARIES.parquet
  SOURCE_INDEPENDENCE.parquet
  GENERATION_LOCK.json
  REPRODUCIBILITY.json
```

Large data remains outside Git; Git may store manifests, schema and compact evidence summaries.

---

## 6. Dry-run requirement

Before human restart authorization, execute a **research dry run** for both packets.

### MECH-21 dry run

Must prove an agent can:
- request response-law event mechanics;
- request static/rolling windows;
- retrieve quality/coverage;
- retrieve lineage;
- handle NULL regions;
- perform joins without provider-native code.

### LF14 dry run

Must prove an agent can:
- request matched sign events;
- retrieve stage-aligned mechanics;
- filter on equal sensor availability;
- inspect liquidation/OI/funding/flow/liquidity coverage;
- preserve sign-conditional missingness;
- reproduce packet query from receipt.

Dry run does NOT execute substantive MECH-21/LF14 scientific conclusions.

---

## 7. Handoff rule

Final packet can recommend:

```text
RESTART_AUTHORIZABLE_FULL
RESTART_AUTHORIZABLE_SCOPED
RESTART_LOCAL_ONLY
HOLD_DATA_BLOCKED
HOLD_VALIDATION_FAILED
```

But actual research execution waits for operator authorization.
