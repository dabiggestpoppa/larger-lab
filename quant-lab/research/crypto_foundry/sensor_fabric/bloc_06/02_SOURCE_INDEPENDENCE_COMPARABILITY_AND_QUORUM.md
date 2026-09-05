# BLOC 6 — SOURCE INDEPENDENCE, COMPARABILITY & QUORUM

**Planning status:** COMPLETE FOR THIS SUB-BLOC  
**Implementation status:** NOT STARTED

---

## 1. Objective

A redundant sensor fabric is only real if the sources being counted are:

1. sufficiently independent;
2. semantically comparable for the requested use;
3. available at the requested point in time;
4. healthy enough to satisfy an explicit quorum.

This document freezes the logic that prevents fake redundancy.

---

## 2. Independence graph

The system must maintain a versioned `SourceDependencyGraph` rather than equating provider name with independence.

Each source node records:

```text
source_id
provider_id
provider_type
venue_ids[]
endpoint_or_archive_id
upstream_origins[]
aggregates_sources[]
mirrors_source[]
derives_from[]
shared_methodology_ids[]
independence_group_id
valid_from
valid_to
confidence
review_status
```

### Provider types

```text
FIRST_PARTY_EXCHANGE
FIRST_PARTY_PROTOCOL
THIRD_PARTY_AGGREGATOR
COMMUNITY_ARCHIVE
MIRROR
LOCAL_RECONSTRUCTION
DERIVED_PROVIDER_ANALYTIC
```

A local reconstruction from Binance public trades remains Binance-origin evidence even if our code computes aggressor flow independently.

---

## 3. Independence classes

For a requested sensor, source-pair relationships may be:

```text
INDEPENDENT_VENUES
SAME_VENUE_DIFFERENT_FEED
SAME_SOURCE_DIFFERENT_RETRIEVAL
AGGREGATOR_DEPENDENT
MIRROR_DEPENDENT
SHARED_UPSTREAM_UNKNOWN
PARTIALLY_DEPENDENT
UNKNOWN
```

Only `INDEPENDENT_VENUES` automatically contributes one full independent redundancy unit.

`PARTIALLY_DEPENDENT` may contribute to corroboration but not to strict quorum unless policy explicitly permits it.

---

## 4. Aggregator double-count protection

Suppose:

```text
Binance direct OI
Bybit direct OI
Coinalyze aggregate OI including Binance + Bybit
```

Raw source count = 3.

Independent-source count is **not** 3.

Coinalyze can provide:

- methodology corroboration;
- coverage corroboration;
- external aggregate comparison;

but must not be counted as a third independent venue observation if its value is derived from the first two.

The dependency graph must therefore support upstream-venue sets.

Example:

```text
COINALYZE_BTC_OI.upstream_origins = {BINANCE, BYBIT, ...}
```

If exact upstream constituents are unknown:

```text
independence = UNKNOWN
```

and the conservative policy applies.

---

## 5. Semantic comparability gate

Bloc 1 froze four semantic-equivalence classes:

```text
EXACT_EQUIVALENT
NORMALIZABLE_COMPARABLE
CORROBORATION_ONLY
NOT_COMPARABLE
```

Bloc 6 converts those classes into usage eligibility.

### Strict numeric comparison

Allowed:

```text
EXACT_EQUIVALENT
NORMALIZABLE_COMPARABLE
```

### Directional/state corroboration

Allowed:

```text
EXACT_EQUIVALENT
NORMALIZABLE_COMPARABLE
CORROBORATION_ONLY
```

### Cross-venue composite eligibility

Requires:

```text
EXACT_EQUIVALENT or NORMALIZABLE_COMPARABLE
```

plus T1 normalization method compatibility.

### No comparison

`NOT_COMPARABLE` remains visible as evidence but cannot enter agreement/quorum calculations for that use.

---

## 6. Sensor-specific comparability examples

### Liquidations

Comparable:

- venue long/short liquidation notional aggregated over the same economic interval after unit normalization.

Corroboration only:

- Deribit liquidation-tagged individual trades versus Gate interval liquidation totals.

These observe related mechanics but are not identical statistics.

### OI

Comparable only after confirming:

- contract type;
- native OI meaning;
- multiplier;
- base/quote exposure conversion;
- timestamp alignment.

### Funding

Native funding rates with different intervals require explicit interval semantics.

An 8h-equivalent transformation can be comparable if methodology is frozen, while native rates remain preserved.

### Order flow

Kraken provider CVD and Binance locally reconstructed CVD may be `NORMALIZABLE_COMPARABLE` only if aggressor convention, interval, instrument scope and notional basis are aligned.

### Depth

Top-N levels from one venue are not automatically comparable with fixed-bps depth from another.

Cross-venue depth comparison should use normalized economic bands or slippage metrics where possible.

---

## 7. Quorum is use-case specific

No single global quorum exists.

A `QuorumPolicy` is keyed by:

```text
sensor_family
universe_tier
use_case
historical_or_live
granularity
instrument_family
```

Use cases initially:

```text
STRICT_HISTORICAL_REPLAY
CANONICAL_RESEARCH_PANEL
SHADOW_LIVE_RUNTIME
DESCRIPTIVE_RESEARCH
CORROBORATION_ONLY
```

---

## 8. Initial quorum templates

These are configurable starting rules, not scientific claims.

### U0 / strict research

Liquidations:

```text
minimum_eligible_sources = 2
minimum_independent_sources = 2
minimum_first_party_sources = 1
```

OI:

```text
minimum_eligible_sources = 2
minimum_independent_sources = 2
```

Funding:

```text
minimum_eligible_sources = 2
minimum_independent_sources = 2
preferred >=3
```

Order flow:

```text
minimum_independent_sources = 2 for cross-venue state
single source allowed for venue-specific research
```

Depth/liquidity:

```text
minimum_independent_sources = 2 for cross-venue U0 liquidity state
single venue allowed for venue-local microstructure analysis
```

### U1

May run with reduced quorum when provider coverage is structurally thinner, but must emit `DEGRADED_PARTIAL` rather than silently pretend U0 quality.

### U2

Single-source descriptive sensors may be allowed, explicitly labeled `R1_SINGLE_SOURCE` / `RESEARCH_ONLY` depending on use.

---

## 9. Redundancy class

Canonical vocabulary:

```text
R0_NONE
R1_SINGLE_INDEPENDENT
R2_TWO_INDEPENDENT
R3_THREE_PLUS_INDEPENDENT
RX_DEPENDENCY_AMBIGUOUS
```

A separate first-party field is required:

```text
first_party_count
third_party_count
community_count
```

Thus:

```text
R2_TWO_INDEPENDENT
```

is not enough to know evidence quality by itself.

---

## 10. Quorum evaluation object

`QuorumResult`:

```text
sensor_family
scope
use_case
policy_id
raw_source_count
eligible_source_count
independent_source_count
first_party_count
venue_count
excluded_sources[]
exclusion_reasons[]
quorum_required
quorum_met
redundancy_class
operating_mode
quality_flags[]
```

---

## 11. Source exclusions

Sources must be excluded from quorum when:

- access class became disallowed;
- freshness failed;
- integrity failed;
- schema drift unresolved;
- semantic equivalence insufficient;
- instrument mapping unresolved;
- revision ambiguity unresolved;
- history unavailable for requested as-of;
- source is upstream duplicate and strict independence is required;
- provider evidence level is below configured floor.

Exclusion does not delete evidence.

---

## 12. Specialist-source rule

A specialist source may remain scientifically valuable even when it cannot count toward generic quorum.

Example:

```text
Deribit liquidation-tagged trades
```

may not replace a broad cross-venue liquidation total, but may be the highest-value evidence for **maker/taker liquidation anatomy**.

Therefore eligibility is sensor-subtype aware.

---

## 13. Venue-local versus market-wide claims

The system must separate:

```text
VENUE_LOCAL_VALID
CROSS_VENUE_VALID
MARKET_WIDE_PROXY
```

A single Binance trade reconstruction may support:

> Binance aggressive sell flow was elevated.

It cannot automatically support:

> market-wide aggressive sell flow was elevated.

The latter requires cross-venue quorum or a research-specific proxy policy.

---

## 14. Independence confidence

Dependency knowledge itself may be imperfect.

Use:

```text
VERIFIED
HIGH_CONFIDENCE
PARTIAL
UNKNOWN
```

If aggregator upstream composition is unknown, redundancy calculations must not assume independence.

Conservative default:

```text
UNKNOWN -> does not increase strict independent quorum
```

---

## 15. Dependency graph revisions

Provider methodologies and aggregator constituents can change over time.

Therefore dependency edges are PIT-versioned:

```text
valid_from
valid_to
known_from
```

Strict historical replay must use the dependency understanding appropriate to the replay policy.

---

## 16. Tests required

Implementation must cover:

1. three provider names but one upstream origin -> independent count 1;
2. two first-party venues -> independent count 2;
3. aggregator + two direct venues -> aggregator does not inflate quorum;
4. specialist source remains visible but excluded from numeric composite quorum;
5. semantic class change invalidates prior routing version, not historical records;
6. U0 quorum fails while U2 descriptive mode can continue;
7. unknown dependency fails conservative strict-quorum path;
8. venue-local query succeeds when cross-venue query fails.

---

## 17. Frozen principle

> **Provider count measures interfaces. Independent-source count measures evidence redundancy. Semantic comparability determines whether that redundancy is usable for the requested claim.**

`human_review_required = TRUE`
