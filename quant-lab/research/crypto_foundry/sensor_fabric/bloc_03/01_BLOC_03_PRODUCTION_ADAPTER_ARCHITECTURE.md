# BLOC 3 — PRODUCTION PROVIDER ADAPTER ARCHITECTURE

**Planning status:** COMPLETE CANDIDATE  
**Implementation status:** NOT STARTED  
**Parent:** Bloc 2 capability-probe plan  
**Branch:** `agent/crypto-sensor-fabric-plan`

## 1. Purpose

Bloc 3 defines how verified external data sources become reusable production acquisition adapters without allowing provider-specific semantics to leak into the canonical sensor model.

Bloc 3 is architecture/planning only. It does not perform historical backfills, build the raw lake, or compute research features.

The governing path is:

```text
PROVIDER ENDPOINT / ARCHIVE / STREAM
        ↓
PROVIDER ADAPTER
        ↓
RAW RESPONSE ENVELOPE
        ↓
T0 IMMUTABLE RAW EVIDENCE
        ↓
BLOC 4+ NORMALIZATION / IDENTITY / STORAGE
```

A provider adapter is an evidence acquisition boundary, not a research model.

## 2. Adapter invariants

Every adapter MUST:

1. preserve native payloads before interpretation;
2. preserve provider and venue identity;
3. expose capability metadata rather than pretending unsupported functions exist;
4. support deterministic request boundaries;
5. emit explicit missing/failure reasons;
6. support restart/resume without duplicate corruption;
7. obey the free-only cost gate;
8. expose native pagination/cursor semantics behind a common checkpoint contract;
9. never silently coerce provider units into canonical units;
10. never compute cross-venue composites;
11. never emit T2 mechanical observables;
12. never use trading/execution credentials;
13. be offline-testable with recorded fixtures;
14. retain enough request/response metadata for reproducibility.

## 3. Common adapter interface

Target Python abstraction:

```python
class MechanicalProviderAdapter(Protocol):
    provider_id: ProviderId

    def capabilities(self) -> ProviderCapabilities: ...
    def list_instruments(self, request: InstrumentListRequest) -> InstrumentListResult: ...
    def fetch_trades(self, request: FetchRequest) -> FetchBatch: ...
    def fetch_liquidations(self, request: FetchRequest) -> FetchBatch: ...
    def fetch_open_interest(self, request: FetchRequest) -> FetchBatch: ...
    def fetch_funding(self, request: FetchRequest) -> FetchBatch: ...
    def fetch_book(self, request: FetchRequest) -> FetchBatch: ...
    def fetch_book_metrics(self, request: FetchRequest) -> FetchBatch: ...
    def fetch_positioning(self, request: FetchRequest) -> FetchBatch: ...
    def fetch_basis(self, request: FetchRequest) -> FetchBatch: ...
```

Unsupported methods return a typed `CapabilityUnavailable`, not `[]`, `0`, or `None` without reason.

## 4. Capability negotiation

Every adapter MUST expose a `ProviderCapabilities` object describing, per sensor family:

```text
supported
access_mode
historical_mode
live_mode
min_granularity
max_granularity
max_rows_per_request
pagination_mode
symbol_scope
auth_requirement
free_access_status
expected_latency
archive_mode
request_cost_class
known_geo_constraints
known_history_start
verified_history_start
verified_at
probe_evidence_ref
```

Bloc 2 evidence is authoritative for initial values. Bloc 3 implementation may not upgrade capability claims without new evidence.

## 5. FetchRequest

Canonical acquisition request:

```text
provider_id
sensor_family
native_instrument_id
start_time
end_time
granularity
page_size_hint
resume_token
request_id
purpose = PROBE | BACKFILL | LIVE_RECOVERY | LIVE_POLL
```

Rules:

- time intervals use UTC;
- boundaries are explicit `[start, end)` unless provider forces alternate semantics, which must be recorded;
- native symbol is required at adapter boundary;
- canonical asset identity is not resolved inside the adapter;
- each request gets a stable deterministic request fingerprint.

## 6. FetchBatch

Every successful acquisition emits:

```text
provider_id
sensor_family
native_instrument_id
request_fingerprint
requested_start
requested_end
actual_first_timestamp
actual_last_timestamp
raw_payloads[]
row_count
next_resume_token
is_complete
provider_cursor
http_status / transport_status
retrieved_at
rate_limit_snapshot
quality_flags
adapter_version
```

The raw payload must remain byte/text-equivalent where feasible. Parsed convenience objects are secondary.

## 7. Request fingerprint

Fingerprint inputs:

```text
provider_id
endpoint_or_archive_family
sensor_family
native_instrument
start
end
granularity
page/cursor parameters
adapter_semantic_version
```

Use a deterministic hash. This supports idempotency, resume, deduplication, and audit.

## 8. Adapter state boundary

Persistent adapter state may contain only acquisition mechanics:

```text
last_success_cursor
last_success_timestamp
retry_state
rate_limit_state
archive_manifest_etag/checksum
provider_health
```

It must not contain research labels, market state, or alpha logic.

## 9. Historical modes

Adapters must explicitly declare one or more:

```text
REST_RANGE
REST_CURSOR
REST_PAGE
BULK_ARCHIVE_DAILY
BULK_ARCHIVE_MONTHLY
PUBLIC_OBJECT_STORAGE
WEBSOCKET_ONLY
LIVE_REST_ONLY
THIRD_PARTY_ARCHIVE
```

The build agent must not force all providers into REST-range semantics.

## 10. Live vs historical separation

Historical acquisition and live collection may share parsing code but MUST have separate orchestration interfaces.

```text
HistoricalAdapterPath
LiveAdapterPath
```

Why:

- rate limits differ;
- retry semantics differ;
- late/revised data differ;
- websocket sequence handling differs;
- live collectors need heartbeat/gap detection;
- backfills need checkpointable partitions.

## 11. Auth doctrine

Data acquisition may use:

```text
NO_AUTH
FREE_API_KEY
OPTIONAL_PUBLIC_KEY
```

Hard-block:

```text
PAID_KEY
TRADING_KEY
WITHDRAWAL_PERMISSION
SIGNING_SECRET
WALLET_SIGNATURE
STAKING_UNLOCK
TRANSACTION_REQUIRED
```

Secrets, where unavoidable for a free key, come from environment/secret store and are never logged or written into raw manifests.

## 12. Rate-limit doctrine

Adapter must expose normalized rate-limit telemetry:

```text
limit_known
limit_capacity
limit_remaining
reset_at
provider_weight_cost
retry_after
```

Or explicit `UNKNOWN`.

Central orchestration later decides concurrency. Individual adapters must not implement uncontrolled sleep loops.

## 13. Retry classification

Retryable:

```text
TIMEOUT
DNS_TRANSIENT
CONNECTION_RESET
HTTP_408
HTTP_425
HTTP_429
HTTP_5XX
ARCHIVE_TEMP_UNAVAILABLE
```

Usually terminal for the request:

```text
HTTP_400_SEMANTIC
HTTP_401_UNAUTHORIZED
HTTP_403_ACCESS_BLOCK
HTTP_404_UNAVAILABLE_RESOURCE
PAYMENT_REQUIRED
INVALID_SYMBOL
UNSUPPORTED_GRANULARITY
HISTORY_NOT_AVAILABLE
SCHEMA_INCOMPATIBLE
```

The exact provider error must be preserved.

## 14. Backoff contract

Common policy:

- bounded exponential backoff + jitter;
- respect `Retry-After` where present;
- no infinite retry;
- per-request attempt budget;
- per-provider circuit breaker later;
- terminal evidence recorded after exhaustion.

No adapter should hammer an endpoint to overcome access restrictions.

## 15. Pagination contract

Common `ResumeToken` wraps provider-native pagination:

```text
mode
provider_cursor
page_number
last_timestamp
last_native_id
archive_object_key
checksum
```

Rules:

- never infer completion solely from short page unless provider semantics prove it;
- repeated cursor is loop detection failure;
- non-monotonic timestamp pagination is quality-flagged;
- resume token is serializable and deterministic.

## 16. Duplicate handling

Adapters do not destructively deduplicate raw evidence.

They MAY detect duplicates and annotate:

```text
POSSIBLE_DUPLICATE
EXACT_DUPLICATE
REPEATED_PAGE
```

True deduplication belongs to canonicalization/storage layers with methodology versioning.

## 17. Schema drift

Every parser must distinguish:

```text
KNOWN_SCHEMA
ADDITIVE_SCHEMA_CHANGE
BREAKING_SCHEMA_CHANGE
UNKNOWN_SCHEMA
```

Unknown/breaking payloads are archived raw and fail closed from parsed output.

No `dict.get(..., 0)` behavior for new/missing fields.

## 18. Provider time semantics

Adapters must document:

- event timestamp;
- interval open/close timestamp;
- publication timestamp when available;
- archive file date semantics;
- whether `end` is inclusive/exclusive;
- timezone;
- timestamp precision;
- possible clock skew.

The adapter preserves provider time semantics; Bloc 4 converts to canonical PIT fields.

## 19. Adapter output levels

Allowed from Bloc 3 adapter:

```text
RAW_PAYLOAD
RAW_RECORD
ACQUISITION_METADATA
CAPABILITY_METADATA
```

Forbidden:

```text
CANONICAL OI USD
CROSS-VENUE CVD
LIQUIDATION STATE
SIGN ASYMMETRY FEATURE
```

## 20. Provider package shape

Target source layout:

```text
quant-lab/src/crypto_sensor_fabric/providers/
  base/
    protocol.py
    models.py
    errors.py
    retry.py
    rate_limit.py
    pagination.py
    fingerprint.py
  kraken/
  gate/
  binance/
  bybit/
  okx/
  deribit/
  coinalyze/
  bitfinex_archive/
```

Each provider package eventually contains:

```text
adapter.py
capabilities.py
parsers.py
requests.py
errors.py
fixtures/
README.md
```

## 21. Common error taxonomy

Minimum typed errors:

```text
ProviderUnavailable
CapabilityUnavailable
AuthenticationRequired
AccessClassViolation
RateLimited
GeoRestricted
InvalidInstrument
UnsupportedGranularity
HistoricalRangeUnavailable
PaginationFailure
ArchiveIntegrityFailure
SchemaDrift
ProviderSemanticError
TransportFailure
RetryExhausted
```

Every exception includes provider ID, sensor family, request fingerprint, retryability, and original provider evidence where safe.

## 22. Observability

Every acquisition call later logs structured fields:

```text
trace_id
request_id
provider
sensor
instrument
start/end
attempt
latency_ms
row_count
bytes_received
status
error_class
rate_limit_remaining
resume_progress
```

No raw secret material.

## 23. Free-only enforcement

Adapter construction requires matching provider registry entry.

Before any network call:

```text
assert cost_usd_required == 0
assert payment_method_required == false
assert staking_required == false
assert transaction_required == false
assert access_class in FREE_AUTOMATED | FREE_LIMITED_AUTOMATED
```

If provider access changes, adapter enters `ACCESS_REVIEW_REQUIRED` and must not silently continue through paid endpoints.

## 24. Research independence

Provider adapters MUST NOT import from:

```text
alt_rotation/
lower_field_*/
strategy/
backtest/
opportunity/
```

Research consumes the sensor fabric; the sensor fabric does not depend on research conclusions.

## 25. Bloc 3 stop boundary

Bloc 3 plans the adapters and their implementation contracts.

It does NOT yet:

- run bulk historical backfill;
- define raw-lake partition storage in full;
- canonicalize symbols/units;
- synthesize provider failover values;
- compute T2 features;
- resume MECH-21/LF14.

Those are later blocs.

`human_review_required = TRUE`
