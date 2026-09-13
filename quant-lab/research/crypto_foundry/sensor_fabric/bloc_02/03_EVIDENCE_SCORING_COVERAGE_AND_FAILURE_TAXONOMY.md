# BLOC 2 — EVIDENCE SCORING, COVERAGE & FAILURE TAXONOMY

**Status:** PLANNING COMPLETE CANDIDATE  
**Purpose:** prevent capability probing from degenerating into undocumented yes/no judgments. Every provider/sensor result must end in reproducible evidence, explicit failure classes, coverage scoring and a defensible promotion role.

---

## 1. Evidence hierarchy

Bloc 2 distinguishes evidence strength.

```text
E0 — CLAIM ONLY
  marketing/docs statement, not runtime verified

E1 — DOC-CONTRACT VERIFIED
  official documentation defines endpoint/schema/access

E2 — LIVE RECENT VERIFIED
  recent-control probe succeeds

E3 — HISTORICAL CHECKPOINT VERIFIED
  at least one requested historical era succeeds

E4 — MULTI-ERA VERIFIED
  multiple target eras succeed

E5 — REPRODUCIBLE COVERAGE VERIFIED
  history traversal, pagination, timestamp/unit semantics and reproducible evidence all pass
```

A source cannot be production-adapter eligible above the capability confidence supported by evidence.

---

## 2. Evidence source class

Inherited from Bloc 1, but applied operationally here.

Suggested evidence classes:

```text
FIRST_PARTY_RUNTIME
FIRST_PARTY_ARCHIVE
FIRST_PARTY_DOCUMENTATION
THIRD_PARTY_AGGREGATOR
COMMUNITY_RECONSTRUCTION
COMMUNITY_ARCHIVE
```

Evidence class does not determine usefulness by itself.

It determines how strongly a claim may be treated as canonical truth.

---

## 3. Capability claim identity

A normalized capability claim must include:

```text
provider_id
sensor_family
venue_market
instrument_scope
granularity_scope
access_mode
history_start_verified
history_end_verified
capability_status
evidence_level
evidence_ids
semantic_equivalence_class
PIT_readiness
free_only_status
claim_version
valid_from
supersedes_claim_id optional
```

Claims are versioned because provider capabilities change.

---

## 4. Capability statuses

### `VERIFIED`

The tested sensor is accessible, free-only compliant, historically usable, semantically understood and reproducible for the claimed scope.

### `VERIFIED_LIMITED`

Works, but one or more limitations materially reduce scope:

- limited history,
- limited assets,
- limited granularity,
- strict free quota,
- opaque precomputed methodology,
- archive-only workflow.

### `VERIFIED_CURRENT_ONLY`

Recent/live capability works but historical support does not satisfy research requirements.

### `VERIFIED_ARCHIVE_ONLY`

Historical public files work but there is no equivalent current API/live surface relevant to the probe.

### `UNSUPPORTED`

The source does not expose the requested sensor.

### `ACCESS_BLOCKED`

Source cannot be used from intended environment for a non-paid access reason.

### `GEO_BLOCKED`

Region access prevents reproducible use. No bypass attempted.

### `AUTH_BLOCKED`

Required authentication could not be obtained under allowed free-only conditions.

### `PAYMENT_BLOCKED`

Necessary data requires paid subscription, payment method, staking or transaction.

### `HISTORY_BLOCKED`

Current data exists but historical depth needed for research does not.

### `SEMANTICALLY_UNUSABLE`

Payload exists but timestamp/unit/methodology semantics cannot be made reliable enough for PIT-safe canonical mapping.

### `TRANSIENT_FAILURE`

Temporary network/server/rate issue; capability remains unresolved.

### `UNVERIFIED`

Insufficient evidence.

---

## 5. Failure taxonomy

Failures must be machine-readable.

```text
F_ACCESS_GEO
F_ACCESS_AUTH
F_ACCESS_PAYMENT
F_ACCESS_RATE_LIMIT
F_NETWORK_TIMEOUT
F_NETWORK_DNS
F_NETWORK_TLS
F_SERVER_5XX
F_CLIENT_4XX
F_ENDPOINT_REMOVED
F_ARCHIVE_NOT_FOUND
F_SYMBOL_NOT_FOUND
F_PRE_LISTING
F_HISTORY_TRUNCATED
F_EMPTY_VALID_WINDOW
F_PAGINATION_LOOP
F_PAGINATION_TRUNCATED
F_SCHEMA_CHANGED
F_TIMESTAMP_UNCLEAR
F_UNIT_UNCLEAR
F_METHOD_UNCLEAR
F_DUPLICATE_EXCESS
F_GAP_EXCESS
F_CHECKSUM_FAILURE
F_PAYLOAD_CORRUPT
F_QUOTA_EXHAUSTED
F_DOC_RUNTIME_CONTRADICTION
F_UNSUPPORTED_SENSOR
F_UNKNOWN
```

Failure detail may carry provider-native code/message after redaction.

---

## 6. Missingness reason mapping

Capability probe failures must map cleanly into later Bloc 1 missingness semantics.

Examples:

```text
F_PRE_LISTING -> PRE_LISTING
F_SYMBOL_NOT_FOUND -> UNSUPPORTED_INSTRUMENT or UNKNOWN_SYMBOL
F_HISTORY_TRUNCATED -> OUTSIDE_PROVIDER_RETENTION
F_ACCESS_PAYMENT -> PAYMENT_BLOCKED
F_ACCESS_GEO -> GEO_BLOCKED
F_UNSUPPORTED_SENSOR -> SENSOR_NOT_SUPPORTED
F_SCHEMA_CHANGED -> PROVIDER_SCHEMA_BREAK
```

The implementation may expand exact enums but must preserve these distinctions.

---

## 7. Coverage dimensions

Coverage is multidimensional.

For each provider/sensor, calculate or record:

```text
H = historical coverage
G = granularity coverage
U = universe/instrument coverage
P = pagination/archive reliability
T = timestamp-semantic clarity
N = native-unit clarity
A = free-only accessibility
R = reproducibility
S = semantic fit to canonical contract
Q = data continuity/quality
```

Do not collapse these immediately into one score for science decisions.

A composite score is only a triage convenience.

---

## 8. Suggested normalized coordinate scoring

Each dimension may be represented as:

```text
0.00 unusable
0.25 weak
0.50 limited
0.75 good
1.00 strong
```

Examples:

### Historical coverage `H`

```text
1.00 = verifies 2021, 2022, 2024, 2026 + recent control
0.75 = verifies 2022 onward
0.50 = verifies 2024 onward
0.25 = recent short history only
0.00 = no usable history
```

Provider listing start must be considered before penalizing legitimate pre-listing absence.

### Timestamp clarity `T`

```text
1.00 explicit event/effective semantics
0.75 mostly clear with minor ambiguity
0.50 inferable but requires methodology assumption
0.25 materially ambiguous
0.00 unusable for PIT
```

### Free-only accessibility `A`

```text
1.00 public no-auth or clearly free API key
0.75 free account/key with manageable constraints
0.50 severe free quota but usable for limited role
0.00 paid/payment/stake/transaction required
```

---

## 9. Composite capability score

If needed for prioritization only:

```text
CAPABILITY_SCORE =
0.20 H
+ 0.10 G
+ 0.10 U
+ 0.10 P
+ 0.10 T
+ 0.10 N
+ 0.10 A
+ 0.10 R
+ 0.05 S
+ 0.05 Q
```

This weighting is an initial planning default, not scientific truth.

Hard blockers override score:

```text
A == 0 -> cannot be required runtime source
T == 0 -> cannot be PIT-ready
S == 0 -> cannot map to canonical sensor
```

A 0.90 score cannot override a paid dependency.

---

## 10. PIT readiness classification

```text
PIT_READY
PIT_READY_WITH_METHOD_VERSION
PIT_LIMITED
NOT_PIT_READY
```

### PIT_READY

- event/effective timestamp clear,
- retrieval semantics understood,
- no forward leakage required.

### PIT_READY_WITH_METHOD_VERSION

Requires explicit reconstruction/normalization later but raw timestamp semantics are sufficient.

### PIT_LIMITED

Useful for historical description/corroboration but cannot safely drive exact replay without caveats.

### NOT_PIT_READY

Timestamp/publication semantics too ambiguous.

---

## 11. Semantic fit score

Map provider-native data to Bloc 1 classes:

```text
EXACT_EQUIVALENT
NORMALIZABLE_COMPARABLE
CORROBORATION_ONLY
NOT_COMPARABLE
```

This is attached at field/sensor mapping level, not just provider level.

Example:

```text
provider: DERIBIT
field: liquidation flag on trade
canonical target: interval liquidation volume
class: NORMALIZABLE_COMPARABLE only after aggregation methodology
```

or `CORROBORATION_ONLY` if native semantics do not justify direct volume comparison.

---

## 12. Historical-depth confidence

Earliest history has two fields:

```text
earliest_claimed_history
earliest_verified_history
```

Never replace verified with claimed.

Confidence:

```text
EXACT_ARCHIVE_BOUNDARY
MONTH_BOUNDARY_VERIFIED
ERA_BOUNDARY_VERIFIED
APPROXIMATE
UNKNOWN
```

---

## 13. Continuity evidence

For interval sensors:

```text
coverage_ratio
largest_gap_seconds
median_gap_seconds
gap_count
expected_rows
observed_rows
```

For event sensors:

```text
event_count
active_periods_sampled
unexpected_empty_windows
sequence_discontinuities
```

Do not apply fixed-bar completeness assumptions to naturally sparse liquidation events.

---

## 14. Schema stability evidence

Capture a deterministic `payload_schema_fingerprint`.

Suggested content:

- sorted field names,
- nested structural paths,
- observed scalar types,
- key optionality sampled across rows.

Do not hash actual sensitive/auth data.

When recent vs historical payload schemas differ, record both.

---

## 15. Documentation-runtime contradiction register

Maintain explicit contradictions:

```text
contradiction_id
provider
sensor
documentation_claim
runtime_observation
severity
evidence_refs
resolution_status
```

Severity:

```text
INFO
MATERIAL
BLOCKING
```

Example:

```text
Docs imply unlimited history.
Probe stops at 1500 bars.
Severity = MATERIAL.
```

---

## 16. Provider role selection

A capability claim feeds a sensor-specific role decision.

Candidate roles:

```text
PRIMARY
SECONDARY
FALLBACK
CORROBORATOR
MECHANISM_MICROSCOPE
CURRENT_ONLY
ARCHIVE_ONLY
REFERENCE_ONLY
EXCLUDED
```

Role considerations:

- evidence class,
- history,
- semantic fidelity,
- universe breadth,
- free access stability,
- redundancy contribution,
- quality.

Highest raw score does not automatically mean PRIMARY.

A narrower first-party source may be a microscope while a broader exchange-native archive becomes primary.

---

## 17. Sensor-level redundancy score

After all providers are probed, compute:

```text
R0 no verified source
R1 one independent source
R2 two independent sources
R3 three+ independent sources
```

Also calculate **evidence diversity**:

```text
FIRST_PARTY_COUNT
AGGREGATOR_COUNT
COMMUNITY_COUNT
VENUE_COUNT
```

Three sources derived from the same upstream exchange do not equal three independent venues.

---

## 18. Sensor-gap matrix

Required output example:

| Sensor | 2021 | 2022 | 2024 | 2026 | Recent | Redundancy | Status |
|---|---:|---:|---:|---:|---:|---|---|
| Liquidations | ? | ? | ? | ? | ? | R? | probe |
| OI | ? | ? | ? | ? | ? | R? | probe |
| Funding | ? | ? | ? | ? | ? | R? | probe |
| Order flow | ? | ? | ? | ? | ? | R? | probe |
| Depth | ? | ? | ? | ? | ? | R? | probe |

Actual implementation will break this out by provider and granularity.

---

## 19. Promotion threshold

A provider/sensor pair is eligible for Bloc 3 production-adapter planning when all mandatory gates pass:

```text
free_only = PASS
recent_control = PASS
runtime_evidence >= E2
sensor_semantics = ADEQUATE
native_units = KNOWN
PIT_readiness != NOT_PIT_READY
reproducible_request = YES
```

Historical adapter/backfill eligibility additionally requires:

```text
runtime_evidence >= E3
history_scope characterized
pagination/archive behavior understood
```

---

## 20. Critical-research sensor threshold

Before LF14 mechanical-gap research may consume a sensor family, prefer:

```text
LIQUIDATIONS: R2 or R1 + strong first-party microscope/corroboration
OI: R2
FUNDING: R2
ORDER FLOW: R2 through independent venue-native or reconstruction paths
DEPTH: R1 high-quality + at least one secondary crosscheck where possible
```

If threshold is not met, research must carry a source-concentration flag.

---

## 21. Do-not-average rule

Capability scores are not data values.

Never use them to numerically average provider market observations.

They control:

- provider role,
- trust weighting metadata,
- source eligibility,
- quality flags,
- research caveats.

Cross-venue market synthesis belongs to later T2 work.

---

## 22. Probe run quality status

Each run ends:

```text
COMPLETE
COMPLETE_WITH_LIMITATIONS
PARTIAL
ABORTED_HARD_BLOCK
ABORTED_TRANSIENT
```

A `PARTIAL` run cannot silently produce definitive unsupported claims for unattempted cells.

Unattempted remains `UNVERIFIED`.

---

## 23. Human review packet

At the end of Bloc 2 implementation, reviewer should receive:

1. provider coverage matrix,
2. sensor gap matrix,
3. provider role recommendations,
4. blocking contradictions,
5. free-only violations,
6. PIT limitations,
7. historical coverage heatmap,
8. schema-drift observations,
9. proposed production-adapter set,
10. excluded/demoted provider list with reasons.

---

## 24. Final planning decision

`BLOC_02_EVIDENCE_AND_SCORING_READY`

Capability decisions are now governed by explicit evidence levels, failure classes, PIT readiness, coverage dimensions, semantic fit, redundancy and provider roles rather than undocumented judgment.

`human_review_required = TRUE`
`implementation_authorized = FALSE`
