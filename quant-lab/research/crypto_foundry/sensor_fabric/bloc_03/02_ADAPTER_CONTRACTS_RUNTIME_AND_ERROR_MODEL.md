# BLOC 3 — ADAPTER CONTRACTS, RUNTIME, AND ERROR MODEL

**Planning status:** COMPLETE FOR CHAPTER 2  
**Implementation status:** NOT STARTED

---

## 1. Purpose

This chapter freezes the executable contracts that every provider adapter must satisfy.

The intent is to prevent eight providers from becoming eight bespoke calling conventions.

Provider-specific transport remains local, but orchestration, testing, evidence capture, retry behavior, and failure semantics are common.

---

## 2. Base package plan

```text
quant-lab/src/crypto_sensor_fabric/adapters/base/
  __init__.py
  enums.py
  protocol.py
  request_models.py
  result_models.py
  capability_models.py
  evidence_models.py
  error_models.py
  rate_limit.py
  retry.py
  pagination.py
  transport.py
  auth.py
  schema_fingerprint.py
  telemetry.py
  registry.py
```

Tests:

```text
quant-lab/tests/crypto_sensor_fabric/adapters/base/
  test_protocol_contract.py
  test_request_validation.py
  test_result_status.py
  test_capability_preflight.py
  test_error_taxonomy.py
  test_retry_policy.py
  test_rate_limit_policy.py
  test_pagination_guards.py
  test_raw_evidence_redaction.py
  test_schema_fingerprint.py
  test_registry.py
```

---

## 3. Frozen enums

### Provider IDs

```text
KRAKEN_FUTURES
GATE_FUTURES
BINANCE_USDM
BYBIT_LINEAR
OKX_SWAP
DERIBIT
COINALYZE
BITFINEX_COMMUNITY_ARCHIVE
```

### Sensor families

Carry Bloc 1 exactly:

```text
MECHANICAL_TRADE
MECHANICAL_LIQUIDATION
MECHANICAL_OPEN_INTEREST
MECHANICAL_FUNDING
MECHANICAL_BOOK_SNAPSHOT
MECHANICAL_BOOK_METRIC
MECHANICAL_POSITIONING
MECHANICAL_BASIS
```

### Transport modes

```text
REST
WEBSOCKET
BULK_HTTP_ARCHIVE
LOCAL_ARCHIVE
AGGREGATOR_API
```

### Query modes

```text
POINT
WINDOW
PAGINATED_WINDOW
CURSOR
SEQUENCE
ARCHIVE_PARTITION
RECENT
STREAM
```

### Adapter role

```text
PRIMARY
SECONDARY
CORROBORATOR
MICROSCOPE
CURRENT_ONLY
ARCHIVE_ONLY
DISABLED
```

---

## 4. Capability preflight contract

Before execution, every adapter calls a shared preflight routine against the active capability manifest.

Inputs:

```text
provider
sensor
venue_market
instrument
requested interval
requested granularity
query mode
```

Outputs:

```text
ALLOW
ALLOW_WITH_LIMITATION
REJECT_NOT_SUPPORTED
REJECT_HISTORY
REJECT_GRANULARITY
REJECT_INSTRUMENT
REJECT_ACCESS
REJECT_SEMANTIC
REJECT_FREE_ONLY
```

Preflight rejection must occur before making an avoidable remote request.

The result stores the capability claim ID used for the decision.

---

## 5. Request envelope

Frozen base request fields:

```text
request_id: UUID/string
correlation_id: optional UUID/string
provider_id
sensor_family
venue_market
native_instrument
canonical_asset_hint: optional
start_at: optional UTC timestamp
end_at: optional UTC timestamp
granularity: optional duration/token
query_mode
page_limit: optional
max_pages: optional
archive_partition_hint: optional
capability_manifest_version
requested_at
```

Validation rules:

- `start_at < end_at` when both exist.
- UTC-aware timestamps only.
- sensor must be supported by the adapter method invoked.
- archive requests must not silently become REST requests unless the capability manifest explicitly defines fallback.
- canonical asset hint is never used to overwrite native instrument identity.

---

## 6. Sensor request subtypes

Use separate typed request classes because different sensors have different legitimate controls.

### TradeRequest

Additional fields:

```text
trade_mode: raw | aggregate
sequence_start
sequence_end
include_liquidation_flags_if_native
```

### LiquidationRequest

```text
aggregation_interval
side_filter: optional
native_event_mode: trade_flag | event | interval_metric | aggregate
```

### OpenInterestRequest

```text
aggregation_interval
requested_native_unit: optional hint only
```

### FundingRequest

```text
funding_mode: settlement | historical_rate | predicted_if_supported
```

Predicted funding must never be silently mixed with realized funding.

### BookSnapshotRequest

```text
levels
sampling_interval
snapshot_mode
```

### BookMetricRequest

```text
metric_set
aggregation_interval
```

### PositioningRequest

```text
population_type
aggregation_interval
```

### BasisRequest

```text
basis_reference
aggregation_interval
```

---

## 7. Result envelope

Frozen fields:

```text
request_id
provider_id
sensor_family
status
records
raw_evidence_refs
started_at
completed_at
attempt_count
page_count
row_count
bytes_received
completeness
quality_flags
warnings
rate_limit_snapshot
schema_fingerprint
adapter_version
capability_claim_id
error: optional AdapterError
```

`records` are provider-native typed records.

Result objects must be serializable without live client/session objects.

---

## 8. Completeness model

Completeness is not binary.

```text
COMPLETE
PARTIAL_PROVIDER_LIMIT
PARTIAL_TRANSIENT
PARTIAL_GAP_DETECTED
PARTIAL_PAGE_CAP
EMPTY_VERIFIED
UNKNOWN
```

`SUCCESS_PARTIAL` must carry a completeness reason.

Research and later backfill code must be able to reject partial results explicitly.

---

## 9. Error taxonomy

Every error has:

```text
error_code
error_family
retryable
provider_id
sensor_family
request_id
http_status_if_any
provider_message_redacted
context
first_seen_at
```

### Access errors

```text
AUTH_REQUIRED
AUTH_INVALID
AUTH_SCOPE_INSUFFICIENT
GEO_BLOCKED
PAYMENT_REQUIRED
FREE_TIER_EXHAUSTED
TERMS_ACCESS_CHANGED
```

### Capability errors

```text
NOT_SUPPORTED
HISTORY_OUT_OF_RANGE
GRANULARITY_NOT_SUPPORTED
INSTRUMENT_NOT_SUPPORTED
PRE_LISTING
ARCHIVE_NOT_AVAILABLE
SEMANTICALLY_BLOCKED
```

### Transient errors

```text
TIMEOUT
CONNECTION_ERROR
RATE_LIMITED
PROVIDER_5XX
TEMPORARY_ARCHIVE_UNAVAILABLE
DNS_ERROR
```

### Data/schema errors

```text
INVALID_JSON
MALFORMED_CSV
SCHEMA_FIELD_MISSING
SCHEMA_TYPE_CHANGED
SCHEMA_BREAKING_DRIFT
UNEXPECTED_ENUM
TIMESTAMP_PARSE_FAILURE
UNIT_PARSE_FAILURE
CORRUPT_ARCHIVE
CHECKSUM_MISMATCH
```

### Pagination errors

```text
CURSOR_LOOP
PAGE_REPEAT
NON_MONOTONIC_PAGE
WINDOW_GAP
WINDOW_OVERLAP_EXCESSIVE
SILENT_TRUNCATION_SUSPECTED
MAX_PAGE_GUARD
```

### Evidence/storage boundary errors

```text
RAW_CAPTURE_FAILED
RAW_HASH_FAILED
MANIFEST_WRITE_FAILED
REDACTION_FAILED
```

---

## 10. Retry matrix

Frozen default behavior:

| Error family | Default retry? | Notes |
|---|---:|---|
| RATE_LIMITED | yes | obey provider delay/limiter |
| TIMEOUT | yes | bounded |
| CONNECTION_ERROR | yes | bounded |
| PROVIDER_5XX | yes | bounded exponential backoff |
| TEMPORARY_ARCHIVE_UNAVAILABLE | yes | bounded |
| AUTH_* | no | configuration/human action |
| GEO_BLOCKED | no | no bypass |
| PAYMENT_REQUIRED | no | free-only hard stop |
| HISTORY_OUT_OF_RANGE | no | capability limitation |
| PRE_LISTING | no | legitimate state |
| SCHEMA_BREAKING_DRIFT | no | review required |
| CHECKSUM_MISMATCH | limited | one clean re-download, then fail |
| CURSOR_LOOP | no | implementation/provider issue |

Default maximum transient attempts should be small and configurable, e.g. 3–5 depending on provider policy.

No infinite retries.

---

## 11. Backoff contract

Shared backoff supports:

```text
provider Retry-After
fixed minimum delay
exponential component
bounded jitter
maximum delay
attempt ceiling
```

Deterministic tests use seeded/no-jitter policy.

Provider adapters may override values through configuration, not ad hoc sleeps.

---

## 12. Rate-limit coordinator

Plan a provider-scoped limiter object.

Interface concept:

```python
await limiter.acquire(cost=weight)
limiter.observe(headers_or_response)
limiter.penalize(retry_after)
```

Required state:

```text
provider
bucket_id
window_seconds
capacity
remaining_if_known
reset_at_if_known
last_observed_at
weight_model_version
```

Unknown provider quotas are represented as unknown, not guessed as infinite.

---

## 13. Pagination state machine

Common pagination engine coordinates provider-specific page functions.

State:

```text
page_index
cursor
window_start
window_end
last_record_key
seen_cursor_hashes
seen_page_hashes
row_count
```

Guards:

- max pages,
- max wall-clock duration,
- repeated cursor detection,
- repeated content detection,
- monotonicity validation where expected,
- requested-window termination.

Provider adapter defines:

```text
make_next_request(previous_page)
extract_cursor(page)
record_order_key(record)
termination_condition(page)
```

---

## 14. Archive partition state machine

Bulk sources require a separate pattern.

Process:

```text
resolve archive partition
→ HEAD/list/check existence if possible
→ download
→ verify provider checksum if published
→ hash locally
→ preserve T0 manifest
→ decompress/read
→ parse provider-native rows
```

Archive states:

```text
FOUND
NOT_FOUND
PRE_LISTING
KNOWN_PROVIDER_GAP
DOWNLOAD_FAILED
CHECKSUM_FAILED
CORRUPT
PARSED
```

Missing archive file does not automatically mean zero market events.

---

## 15. Auth contract

Central credential provider:

```text
CredentialRef
  provider
  credential_type
  secret_locator
  scope
```

Adapters receive a token/credential through a narrow interface at runtime.

They do not know how secrets are stored.

For the initial free-only build, expected auth patterns:

```text
NONE
FREE_API_KEY
```

Any requirement for paid account/payment method must trip the free-only gate.

---

## 16. Raw evidence model

`RawEvidenceManifest` fields:

```text
evidence_id
provider_id
sensor_family
request_id
transport_mode
source_locator
request_fingerprint
response_status
content_hash_sha256
raw_size_bytes
content_type
compression
retrieved_at
local_storage_uri_or_path
provider_checksum
provider_checksum_type
adapter_version
capability_manifest_version
schema_fingerprint
redaction_status
```

Raw evidence itself is not committed to Git.

Git contains schemas, manifests/examples, fixtures, and checksums only.

---

## 17. Request fingerprint

A deterministic request fingerprint should exclude volatile secrets and include economically meaningful query dimensions.

Example source components:

```text
provider
sensor
endpoint/archive family
native instrument
start/end
granularity
query mode
semantic request options
```

Fingerprint supports:

- reproducibility,
- cache lookup,
- evidence traceability,
- duplicate-request analysis.

It must not be treated as source-event identity.

---

## 18. Schema fingerprint

For structured responses, fingerprint at least:

```text
field names
nested paths where relevant
basic primitive types
required/optional observed presence
```

Do not fingerprint literal values.

Version provider parser expectations separately from observed fingerprint.

Runtime behavior:

```text
known compatible fingerprint → parse
additive unknown fingerprint → parse + warning if safe
breaking fingerprint → SCHEMA_DRIFT fail closed
```

---

## 19. Provider-native record base fields

Every parsed record should expose common provenance metadata even though payload fields remain provider-specific:

```text
provider_id
sensor_family
venue_market
native_instrument
source_record_id: optional
native_timestamp_fields
raw_evidence_id
raw_row_or_item_index
adapter_version
```

Provider-specific records then add native economic values.

---

## 20. Logging contract

Structured adapter logs:

```text
level
event
provider
sensor
request_id
correlation_id
status
attempt
page
latency_ms
```

Never log:

- API keys,
- auth headers,
- full raw responses by default,
- private filesystem secret locations.

Raw market evidence belongs in T0 storage, not application logs.

---

## 21. Telemetry counters

Planned metrics:

```text
adapter_requests_total
adapter_request_latency_seconds
adapter_rows_total
adapter_bytes_total
adapter_failures_total
adapter_retry_total
adapter_rate_limit_wait_seconds
adapter_schema_drift_total
adapter_raw_capture_failures_total
adapter_partial_results_total
```

Labels must be bounded: provider, sensor, status.

Do not label metrics by native symbol if it would create excessive cardinality.

---

## 22. Adapter registry

Registry keys:

```text
provider_id
transport_variant if needed
```

Registry entry stores:

```text
factory
adapter_version
supported_sensor_methods
capability_manifest_ref
configuration_schema
```

Higher layers resolve adapter instances through registry rather than direct provider imports.

---

## 23. Configuration model

Provider config files should live under:

```text
quant-lab/config/crypto_sensor_fabric/providers/
```

Per provider:

```text
enabled
base endpoints/archive roots
timeout
concurrency
retry policy
rate-limit policy
auth ref
raw evidence requirements
parser version
capability manifest ref
```

Do not encode endpoint URLs in research notebooks.

---

## 24. Unit-test doctrine

All default tests are offline.

Network interactions are represented with recorded/synthetic fixtures that contain no credentials.

Required generic contract tests run against every adapter class:

```text
implements protocol
unsupported method fails typed
capability preflight honored
result envelope complete
raw evidence ref present on success
native units retained
native timestamps retained
retry semantics correct
schema drift detected
no secret leakage
```

Provider-specific integration tests are separate and opt-in.

---

## 25. Golden fixtures

For each supported sensor/provider pair, preserve at least:

```text
one normal successful payload
one empty legitimate payload if observable
one malformed/drift payload
one pagination/archive edge case if relevant
```

Fixtures must be small and legal to retain in repo.

If provider terms make raw payload fixtures inappropriate, construct shape-equivalent synthetic fixtures and store hash/evidence references to live proof separately.

---

## 26. Integration-test profiles

Planned markers/profiles:

```text
unit
provider_live
provider_archive
free_key_required
slow
```

CI default runs `unit` only.

Scheduled/manual evidence workflows may run provider integration profiles.

---

## 27. Version policy

Three versions remain distinct:

```text
adapter_version
parser_methodology_version
capability_manifest_version
```

Changing an endpoint URL alone may not require parser version change.

Changing economic field interpretation does.

Changing capability evidence does not rewrite the adapter version automatically.

---

## 28. Bloc 3 runtime acceptance

Framework-level implementation is acceptable when:

- all request/result/error models validate,
- capability preflight blocks illegal calls,
- retry and rate-limit policies are deterministic under tests,
- pagination guards trip correctly,
- raw evidence manifests redact secrets,
- schema fingerprints detect expected drift fixtures,
- registry loads provider adapters from config,
- generic contract tests can execute against a dummy/reference adapter.

Provider-specific acceptance is defined in later Bloc 3 chapters.
