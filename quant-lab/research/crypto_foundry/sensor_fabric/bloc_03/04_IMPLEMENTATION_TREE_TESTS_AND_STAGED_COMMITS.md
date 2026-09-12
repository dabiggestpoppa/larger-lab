# BLOC 3 — IMPLEMENTATION TREE, TESTS & STAGED COMMITS

## 1. Planned source tree

```text
quant-lab/src/crypto_sensor_fabric/
  providers/
    base/
      __init__.py
      protocol.py
      models.py
      capabilities.py
      errors.py
      transport.py
      retry.py
      rate_limit.py
      pagination.py
      fingerprint.py
      raw_envelope.py
      access_gate.py
      conformance.py

    kraken/
      adapter.py
      capabilities.py
      requests.py
      parsers.py
      errors.py
      README.md

    gate/
    binance/
    bybit/
    okx/
    deribit/
    coinalyze/
    bitfinex_archive/

quant-lab/tests/crypto_sensor_fabric/
  providers/
    base/
    kraken/
    gate/
    binance/
    bybit/
    okx/
    deribit/
    coinalyze/
    bitfinex_archive/
```

Fixtures may live in tests or provider packages depending repository convention, but one convention must be used consistently.

## 2. Base models to implement

Minimum:

```text
ProviderCapabilities
SensorCapability
FetchRequest
FetchBatch
RawPayloadEnvelope
ResumeToken
RateLimitSnapshot
ProviderHealthSignal
AdapterEvidenceRef
AcquisitionFailure
```

Enums:

```text
HistoricalMode
LiveMode
PaginationMode
AuthMode
FetchPurpose
AdapterStatus
Retryability
SchemaState
```

All serialized models require schema version.

## 3. Base protocol tests

Required tests:

```text
test_provider_id_required
test_capability_declares_each_sensor
test_unsupported_returns_typed_failure
test_fetch_request_utc
test_request_fingerprint_deterministic
test_request_fingerprint_changes_on_semantic_input
test_resume_token_roundtrip
test_raw_payload_hash_deterministic
test_access_gate_blocks_paid
test_access_gate_blocks_payment_method
test_access_gate_blocks_staking
test_access_gate_blocks_transaction_required
test_retry_classification
test_retry_budget_exhaustion
test_rate_limit_snapshot_serialization
test_cursor_loop_detection
test_schema_breaking_fails_closed
```

## 4. Provider conformance suite

Every provider must run a parameterized conformance suite:

```text
provider metadata present
provider registry entry exists
capabilities backed by Bloc 2 evidence ref
free-only access valid
native instrument accepted
raw payload preserved
empty range represented distinctly
invalid symbol distinct
unsupported sensor distinct
retryable transport distinct
schema drift distinct
resume token deterministic
README present
fixtures present
```

## 5. Per-provider test minimum

Each provider/sensor path requires at least:

```text
1 happy fixture
1 empty fixture
1 boundary fixture
1 provider error fixture
1 drift/malformed fixture
```

Critical sensor paths should add pagination and duplicate-edge fixtures.

## 6. Archive-provider tests

Binance/OKX/Bitfinex archive modes require:

```text
archive_manifest_parse
checksum_success
checksum_failure
compression_integrity
path_traversal_rejection
partial_download_resume contract
missing_object handling
archive_date_semantics
```

## 7. Parser golden tests

Expected values should be provider-native.

Examples:

```text
native timestamp
native symbol
native quantity
native USD field if provider supplied it
native liquidation side/flag
native funding rate
raw record hash
```

Do not test later canonical conversion in Bloc 3.

## 8. Documentation tests

CI check can assert each provider README includes headings:

```text
Role
Capabilities
Unsupported
Access
History
Time Semantics
Units
Pagination
Known Issues
Fixtures
Examples
Non-Goals
```

## 9. Static quality

Implementation must pass repository-standard:

```text
Ruff
Pyright/mypy according to repo standard
pytest
schema serialization tests
```

Network smoke suite separate.

## 10. Planned execution commits

The eventual build agent should commit in this order.

### `SENSOR-B3-I01-base-models`

Implement:
- models/enums;
- provider protocol;
- typed failure model;
- serialization tests.

### `SENSOR-B3-I02-access-fingerprint`

Implement:
- free-only access gate;
- request fingerprint;
- raw envelope hashing;
- tests.

### `SENSOR-B3-I03-retry-rate-pagination`

Implement:
- retry classifier/policy;
- rate-limit model;
- resume token;
- cursor loop protection;
- fake transport tests.

### `SENSOR-B3-I04-conformance-suite`

Implement common adapter conformance harness before any real provider.

### `SENSOR-B3-I05-kraken`

Implement verified Kraken capability paths + fixtures + README + conformance evidence.

### `SENSOR-B3-I06-gate`

Gate paths + fixtures + tests.

### `SENSOR-B3-I07-binance`

Binance REST/archive paths + checksum/archive tests.

### `SENSOR-B3-I08-bybit`

Bybit history/cursor paths.

### `SENSOR-B3-I09-okx`

OKX historical trade/book/download path.

### `SENSOR-B3-I10-deribit`

Deribit trade/liquidation-tag paths.

### `SENSOR-B3-I11-coinalyze`

Coinalyze free-key aggregation paths.

### `SENSOR-B3-I12-bitfinex-archive`

Community archive reader/provenance.

### `SENSOR-B3-I13-adapter-matrix`

Generate adapter readiness/capability matrix from code + Bloc 2 evidence.

### `SENSOR-B3-I14-network-smoke`

Add opt-in tiny-query network smoke harness and evidence outputs.

### `SENSOR-B3-I15-final-validation`

Run full offline suite, lint/type, fixture coverage, free-only checks, docs audit.

### `SENSOR-B3-I16-handoff`

Produce Bloc 3 implementation report + Bloc 4 storage/raw-lake handoff.

## 11. Commit discipline

Each provider commit must be independently reviewable.

Do NOT combine multiple providers into one implementation commit.

A provider commit should contain only:
- its package;
- fixtures;
- provider tests;
- registry/capability adjustments strictly required by verified evidence;
- README.

No unrelated research changes.

## 12. Evidence generated by implementation

Each adapter implementation should output a small evidence artifact such as:

```text
adapter_id
adapter_version
provider
supported_sensor_paths
bloc2_evidence_refs
offline_tests
network_smoke_status
free_only_gate
known_failures
promotion_status
commit_sha
```

## 13. Provider readiness matrix

Generated table:

```text
provider | sensor | planned | implemented | offline_pass | smoke_pass | access_pass | resume_pass | schema_pass | status
```

Statuses:

```text
NOT_PLANNED
PLANNED
IMPLEMENTING
ADAPTER_READY
DATA_BLOCKED
ACCESS_BLOCKED
VALIDATION_FAILED
```

## 14. Bloc 3 acceptance gates

### G1 Common architecture

PASS when base protocol and typed models are stable and fully tested.

### G2 Access safety

PASS when no provider can make a network request after free-only gate fails.

### G3 Raw preservation

PASS when golden fixtures prove raw payload recovery/hash.

### G4 Resume/pagination

PASS when fake and provider-specific tests prove checkpoint/resume semantics.

### G5 Provider isolation

PASS when provider code does not leak native fields into shared T1/T2 objects.

### G6 No network unit dependency

PASS when full standard unit suite works offline.

### G7 Provider coverage

PASS when every provider candidate has one of:

```text
ADAPTER_READY
DATA_BLOCKED with evidence
ACCESS_BLOCKED with evidence
```

No ambiguous `TODO maybe works` state.

### G8 Documentation

PASS when capability limitations/time/units/pagination are documented.

## 15. Non-goals for implementation

Bloc 3 implementation must NOT:

- backfill 2020–2026 at scale;
- create final Parquet partition strategy;
- canonicalize OI units;
- reconstruct cross-venue CVD;
- define provider weights;
- perform failover synthesis;
- build LF14 features;
- resume MECH research.

## 16. Build-agent stopping point

After `SENSOR-B3-I16-handoff`, STOP and wait for human review.

Required verdict:

```text
PASS_BLOC_03_IMPLEMENTATION
PASS_BLOC_03_PARTIAL_PROVIDER_COVERAGE
FAIL_BLOC_03_CORE_ADAPTER_ARCHITECTURE
```

Partial provider coverage can still pass if critical sensor redundancy remains viable and failures are evidence-backed.

`human_review_required = TRUE`
