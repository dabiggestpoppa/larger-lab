# BLOC 6 — QUALITY, REDUNDANCY & FAILOVER ARCHITECTURE

**Planning status:** COMPLETE FOR THIS SUB-BLOC  
**Implementation status:** NOT STARTED  
**Branch:** `agent/crypto-sensor-fabric-plan`  
**Parent:** Bloc 5 PIT Identity & Semantic Normalization  
**Purpose:** define how the sensor fabric distinguishes provider health from sensor health, measures redundancy and disagreement, routes around provider failures without erasing provenance, and fails closed when the remaining evidence is not sufficient for a requested research use.

---

## 1. Mission

Bloc 6 turns the multi-provider fabric from a collection of feeds into a **quality-aware evidence network**.

The core problem is not merely uptime.

A provider may be online while a specific sensor is stale, semantically incompatible, historically incomplete, duplicated through an aggregator, or structurally inconsistent with independent venues.

Conversely, one provider may be down while the **economic sensor remains healthy** because several independent providers still cover the same mechanical phenomenon.

Therefore the system must answer separately:

1. Is the provider reachable?
2. Is the endpoint/feed healthy?
3. Is the specific provider×sensor×instrument observation healthy?
4. Is the canonical sensor family adequately covered?
5. Are remaining sources independent?
6. Are observations semantically comparable?
7. Do sources broadly agree or materially disagree?
8. Is disagreement itself informative or evidence of bad data?
9. Is there enough evidence to continue in FULL / DEGRADED / RESEARCH_ONLY mode?
10. Must the requested use fail closed?

---

## 2. Governing doctrine

Inherited hard rules:

```text
T0 = immutable provider evidence
T1 = provider-preserving PIT canonical observations
T2 = derived mechanical observables / cross-venue synthesis
```

Bloc 6 is a control plane spanning T0/T1 quality metadata and T2 eligibility.

It **does not** create cross-venue economic composites at T1.

Provider disagreement may be measured at the quality layer, but any economic aggregation such as:

```text
CROSS_VENUE_LIQUIDATION_STATE
CROSS_VENUE_OI_BREADTH
FLOW_CONSENSUS
```

belongs to Bloc 9 T2 observable construction.

---

## 3. Core distinction: provider health != sensor health

### 3.1 ProviderHealth

Provider-level operational status.

Examples:

- DNS/transport reachable
- API responding
- archive host reachable
- authentication state valid where applicable
- public access still free
- rate-limit budget available
- schema fingerprint recognized
- provider-wide outage detected

### 3.2 FeedHealth

Endpoint/feed/file-family health.

Examples:

- Gate contract stats endpoint healthy
- Binance monthly archive index healthy
- OKX historical book download endpoint degraded
- Kraken analytics endpoint schema drifted

### 3.3 ObservationHealth

Provider×venue×instrument×sensor×time-bucket status.

Examples:

- BYBIT_LINEAR BTCUSDT OI fresh and valid
- KRAKEN_FUTURES ETH liquidation volume stale
- GATE_FUTURES SOL taker flow missing in current bucket
- OKX_SWAP BTC orderbook sequence broken

### 3.4 CanonicalSensorHealth

Quality of the **economic sensor family** after considering all valid independent sources.

Examples:

```text
LIQUIDATIONS = HEALTHY
OPEN_INTEREST = DEGRADED
FUNDING = HEALTHY
ORDER_FLOW = HEALTHY
DEPTH = PARTIAL
```

The canonical sensor can remain usable when one provider fails.

---

## 4. Core quality objects

### 4.1 `ProviderHealthSnapshot`

```text
provider_id
as_of
reachability_state
access_state
schema_state
rate_limit_state
latency_state
recent_error_rate
last_success_at
last_failure_at
free_only_gate_state
health_status
quality_flags[]
evidence_refs[]
```

### 4.2 `FeedHealthSnapshot`

```text
provider_id
feed_id
sensor_families[]
as_of
freshness_state
schema_state
pagination_state
coverage_state
latency_ms
error_rate
health_status
quality_flags[]
```

### 4.3 `ObservationHealthSnapshot`

```text
provider_id
venue_id
instrument_id
sensor_family
window_start
window_end
expected_observation_state
observed_row_count
freshness_seconds
completeness_ratio
integrity_state
semantic_state
revision_state
quality_status
quality_flags[]
lineage_refs[]
```

### 4.4 `CanonicalSensorHealthSnapshot`

```text
sensor_family
universe_scope
as_of
eligible_sources[]
independent_source_groups[]
source_count_raw
source_count_independent
venue_count
coverage_ratio
freshness_score
completeness_score
independence_score
agreement_state
disagreement_score
semantic_compatibility_state
redundancy_class
operating_mode
quality_status
quality_flags[]
evidence_refs[]
```

### 4.5 `FailoverDecision`

```text
sensor_family
requested_scope
failed_source
candidate_replacements[]
selected_source_set[]
rejected_sources[]
rejection_reasons[]
mode_before
mode_after
continuation_allowed
human_review_required
created_at
```

### 4.6 `SourceDependencyGraph`

Represents whether two apparent sources are truly independent.

```text
source_id
upstream_origin_ids[]
provider_type
venue_ids[]
aggregator_of[]
derived_from[]
shared_archive_origin[]
independence_group_id
confidence
```

---

## 5. Health status vocabulary

Minimum shared status vocabulary:

```text
HEALTHY
PARTIAL
DEGRADED
STALE
GAPPED
SCHEMA_DRIFT
SEMANTIC_REVIEW_REQUIRED
ACCESS_BLOCKED
RATE_LIMITED
PROVIDER_DOWN
HISTORY_INCOMPLETE
INTEGRITY_FAILURE
REVISION_CONFLICT
UNVERIFIED
DATA_BLOCKED
```

Status must never be inferred from a single boolean `is_ok`.

---

## 6. Operating modes

The fabric needs explicit operating modes rather than silent fallback.

### `FULL`

All critical quality requirements for the requested scope are satisfied.

### `DEGRADED_REDUNDANT`

One or more preferred sources unavailable, but enough independent equivalent/comparable evidence remains.

### `DEGRADED_PARTIAL`

Useful evidence remains but coverage, venue breadth, or semantic equivalence is incomplete.

### `RESEARCH_ONLY`

Data may support descriptive/manual research, but not canonical runtime state or strict replay claims.

### `DATA_BLOCKED`

Evidence insufficient or invalid for requested use.

No system component may silently reinterpret `DEGRADED_PARTIAL` as `FULL`.

---

## 7. Critical-sensor redundancy targets

Initial targets are design goals, not fabricated guarantees.

```text
LIQUIDATIONS
  target independent redundancy: >=2
  preferred: Kraken + Gate
  specialist corroboration: Deribit
  third-party corroboration: Coinalyze / Bitfinex archive

OPEN_INTEREST
  target independent redundancy: >=2
  preferred: Bybit + Gate + Kraken
  secondary: Binance / Coinalyze

FUNDING
  target independent redundancy: >=3 where universe permits
  providers: Bybit / Kraken / Gate / Binance / OKX / Deribit / Coinalyze

ORDER_FLOW
  target independent redundancy: >=2
  providers: Binance reconstructed / Kraken analytics / Gate taker / Bybit trades / OKX trades

DEPTH_LIQUIDITY
  target independent redundancy: >=2 for U0
  preferred: OKX + Kraken
  secondary reconstruction: Binance
```

Long-tail U2 instruments may legitimately have lower redundancy and therefore lower operating mode.

---

## 8. Provider priority is contextual, not universal

No single provider has one global rank.

Priority must be keyed by:

```text
sensor_family
instrument_family
historical_vs_live
requested_granularity
requested_time_range
universe_tier
```

Example:

- Deribit may be first-choice for liquidation-tagged trade anatomy on BTC/ETH.
- Gate may be first-choice for broad-alt liquidation statistics.
- Binance may be first-choice for historical raw aggressor-flow reconstruction.
- OKX may be first-choice for deeper historical books.

Provider ordering is a routing policy, not a truth hierarchy.

---

## 9. Failover doctrine

Failover is allowed only when the replacement source is eligible for the requested **economic sensor**, not merely because it has a similarly named field.

Before replacement:

1. access/free-only gate passes;
2. provider is operationally healthy enough;
3. sensor capability is verified;
4. instrument identity is compatible;
5. requested time/granularity is covered;
6. semantic equivalence class is sufficient;
7. source is not merely an upstream duplicate of an already-counted source;
8. PIT availability rules pass;
9. quality floor passes.

Failover never rewrites venue identity.

Example:

```text
Kraken BTC liquidation feed stale
Gate BTC liquidation statistics healthy
Deribit BTC liquidation-tagged trades healthy

=> canonical liquidation sensor may continue in DEGRADED_REDUNDANT

NOT:
Gate data relabeled as Kraken data
```

---

## 10. Provider disagreement is first-class information

Source disagreement has two possible meanings:

### A. Expected economic heterogeneity

Different venues genuinely experience different:

- liquidations
- OI changes
- funding
- aggressive flow
- depth withdrawal

This is useful market information.

### B. Data-quality disagreement

Differences caused by:

- unit mismatch
- stale data
- wrong contract mapping
- interval misalignment
- revision mismatch
- parser bug
- provider methodology drift

Bloc 6 must distinguish these classes before Bloc 9 uses disagreement as an observable.

---

## 11. No blind majority vote

Three providers agreeing does not automatically make them correct.

Reasons:

- two may be aggregators of the same upstream source;
- all may share one bad conversion methodology;
- one specialist first-party source may be more precise for a narrow field;
- different venues may legitimately diverge.

The fabric therefore uses evidence-aware source sets rather than simplistic voting.

---

## 12. Independence is separate from provider count

Raw count:

```text
source_count_raw = 4
```

may reduce to:

```text
source_count_independent = 2
```

if:

- Coinalyze aggregates Binance + Bybit;
- a community archive mirrors Bitfinex directly;
- two local adapters read the exact same public archive.

Independence grouping is mandatory for redundancy claims.

---

## 13. Fail-closed principle

The fabric must return `DATA_BLOCKED` when:

- no semantically eligible source remains;
- only stale sources remain beyond tolerance;
- all apparent redundancy comes from one upstream origin where independent evidence is required;
- schema/semantic drift is unresolved;
- PIT availability cannot be established for strict replay;
- integrity/revision ambiguity blocks deterministic interpretation;
- a requested U0 critical sensor falls below its configured research/runtime quorum.

The system must prefer an explicit data wall over fake continuity.

---

## 14. Out of scope

Bloc 6 does NOT define:

- cross-venue economic composite formulas;
- liquidation breadth formulas;
- leverage scores;
- CVD consensus;
- trading signals;
- alpha weights;
- provider PnL relevance;
- live execution failover.

Those belong downstream.

---

## 15. Core implementation modules planned

```text
quant-lab/src/crypto_sensor_fabric/quality/
  models.py
  health.py
  freshness.py
  gaps.py
  independence.py
  comparability.py
  disagreement.py
  redundancy.py
  quorum.py
  routing.py
  failover.py
  operating_mode.py
  policy.py
  evidence.py

quant-lab/config/crypto_sensor_fabric/
  quality_policy.yaml
  redundancy_policy.yaml
  source_dependencies.yaml
  failover_routes.yaml
```

---

## 16. Bloc 6 success condition

Bloc 6 is successful when a downstream component can ask:

> "Can I trust the liquidation/OI/funding/order-flow/depth sensor for this asset, time, universe and use case right now?"

and receive a deterministic answer containing:

- source set;
- independent-source set;
- exact quality state;
- coverage;
- disagreement;
- failover decisions;
- degraded/full mode;
- explicit blockers;
- evidence references.

No hidden substitution.

`human_review_required = TRUE`
