# BLOC 2 — PROBE OUTPUT TEMPLATES

**Status:** PLANNING COMPLETE CANDIDATE  
**Purpose:** freeze the shape of the evidence packet so later implementation and human review use the same vocabulary.

---

## 1. Capability evidence record

Illustrative machine-readable shape:

```yaml
probe_id: kraken_open_interest_btc_2022_5m_001
probe_run_id: run_2026_08_29_001
provider_id: KRAKEN_FUTURES
sensor_family: MECHANICAL_OPEN_INTEREST
venue_market: KRAKEN_FUTURES
instrument_native: PI_XBTUSD
canonical_asset_hint: BTC
requested_start: 2022-06-15T00:00:00Z
requested_end: 2022-06-16T00:00:00Z
requested_granularity: 5m
access_mode: PUBLIC_REST
query_mode: TIME_RANGE
response_status_class: VERIFIED_SAMPLE
http_status_or_file_status: 200
rows_returned: null
first_timestamp_returned: null
last_timestamp_returned: null
native_timestamp_fields: []
native_units_summary: {}
pagination_detected: false
pagination_complete: null
rate_limit_metadata: {}
requires_auth: false
requires_payment: false
geo_block_detected: false
payload_schema_fingerprint: null
payload_hash_sample: null
error_class: null
error_detail_redacted: null
started_at: null
finished_at: null
probe_version: sensor-probe-v1
```

Values above are examples/templates only, not verified runtime evidence.

---

## 2. Capability claim template

```yaml
claim_id: null
provider_id: null
sensor_family: null
venue_market: null
instrument_scope: []
granularity_scope: []
access_mode: null
capability_status: UNVERIFIED
evidence_level: E0
earliest_claimed_history: null
earliest_verified_history: null
history_boundary_confidence: UNKNOWN
latest_verified_history: null
PIT_readiness: NOT_PIT_READY
semantic_equivalence_class: null
free_only_status: UNVERIFIED
known_gaps: []
limitations: []
evidence_ids: []
claim_version: 1
valid_from: null
supersedes_claim_id: null
```

---

## 3. Provider/sensor coverage matrix template

Required logical columns:

```text
provider_id
sensor_family
venue_market
instrument_scope
access_mode
2021_status
2022_status
2024_status
2026_status
recent_status
earliest_verified_history
latest_verified_history
granularity_scope
PIT_readiness
unit_clarity
pagination_quality
schema_stability
semantic_equivalence_class
evidence_level
provider_role
capability_score
promotion_eligible
blocking_reason
```

---

## 4. Historical checkpoint matrix template

```text
provider_id,sensor_family,instrument,granularity,checkpoint,status,evidence_id,rows_returned,first_ts,last_ts,failure_class
```

One row per attempted cell.

Unattempted cells do not appear as failures; the report generator may render them separately as `UNVERIFIED`.

---

## 5. Sensor-gap matrix template

```text
sensor_family,era,verified_provider_count,verified_venues,redundancy_class,first_party_count,aggregator_count,community_count,PIT_ready_provider_count,gap_status,notes
```

Example statuses:

```text
COVERED
SINGLE_SOURCE
PARTIAL_HISTORY
NO_PIT_SOURCE
NO_FREE_SOURCE
UNVERIFIED
```

---

## 6. Provider role recommendation template

```yaml
provider_id: null
sensor_family: null
recommended_role: null
reason:
  evidence_strength: null
  history: null
  semantics: null
  redundancy_value: null
  limitations: []
required_followup: []
production_adapter_candidate: false
```

---

## 7. Failure record template

```yaml
failure_id: null
probe_id: null
provider_id: null
sensor_family: null
failure_class: F_UNKNOWN
provider_native_code: null
provider_native_message_redacted: null
retryable: false
hard_block: false
missingness_mapping: null
evidence_ref: null
```

---

## 8. Documentation/runtime contradiction template

```yaml
contradiction_id: null
provider_id: null
sensor_family: null
documentation_claim: null
documentation_source_ref: null
runtime_observation: null
runtime_evidence_ids: []
severity: INFO
resolution_status: OPEN
notes: null
```

---

## 9. Free-only audit template

```text
provider_id,sensor_family,access_mode,api_key_required,account_required,payment_method_required,paid_subscription_required,staking_required,transaction_required,free_quota,access_class,eligible_required_runtime,evidence_refs
```

Hard requirement:

```text
payment_method_required = false
paid_subscription_required = false
staking_required = false
transaction_required = false
```

for any required runtime provider.

---

## 10. PIT readiness matrix template

```text
provider_id,sensor_family,effective_timestamp_understood,observation_timestamp_understood,publication_delay_understood,forward_info_required,PIT_readiness,methodology_required,blocking_reason
```

---

## 11. History-boundary template

```text
provider_id,sensor_family,instrument,granularity,earliest_claimed,earliest_verified,boundary_confidence,latest_verified,probe_method,evidence_ids
```

---

## 12. Schema fingerprint template

```yaml
provider_id: null
sensor_family: null
evidence_id: null
schema_fingerprint: null
fields:
  - path: null
    observed_types: []
    nullable_observed: null
sample_period: null
```

---

## 13. Final source promotion packet

The implementation should generate a machine-readable packet conceptually shaped as:

```yaml
fabric_version: sensor-fabric-v1
probe_version: sensor-probe-v1
generated_at: null
providers:
  - provider_id: KRAKEN_FUTURES
    sensors: []
  - provider_id: GATE_FUTURES
    sensors: []
critical_sensor_redundancy:
  MECHANICAL_LIQUIDATION: R0
  MECHANICAL_OPEN_INTEREST: R0
  MECHANICAL_FUNDING: R0
  MECHANICAL_TRADE: R0
  MECHANICAL_BOOK_SNAPSHOT: R0
blocking_contradictions: []
promotion_candidates: []
excluded_or_limited: []
```

The R0 values above are planning placeholders only.

---

## 14. Human report skeleton

```markdown
# Sensor Fabric Capability Report

## Executive result

## Critical sensor coverage

## Provider results

### Kraken
### Gate
### Binance
### Bybit
### OKX
### Deribit
### Coinalyze
### Bitfinex community archive

## Historical coverage heatmap

## PIT readiness

## Semantic-equivalence issues

## Documentation/runtime contradictions

## Free-only audit

## Redundancy map

## Recommended production adapters

## Demoted/excluded sources

## Open gaps

## Bloc 3 handoff
```

---

## 15. Naming and version rules

All generated evidence must carry:

```text
fabric_version
probe_version
provider_probe_version
```

Do not encode mutable provider URLs into canonical IDs.

IDs should remain stable even if endpoint URLs change.

---

## 16. Final planning decision

`BLOC_02_OUTPUT_TEMPLATES_READY`

The eventual build agent has machine/human evidence shapes defined before live probing, reducing the risk that each provider develops incompatible reports or ad hoc capability judgments.

`human_review_required = TRUE`
`implementation_authorized = FALSE`
