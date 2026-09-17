# BLOC 3 — FREEZE MANIFEST

**Planning status:** COMPLETE  
**Implementation status:** NOT STARTED  
**Branch:** `agent/crypto-sensor-fabric-plan`  
**Purpose:** freeze production provider-adapter architecture before any implementation agent writes real acquisition code.

## 1. Frozen decisions

### F1 — Adapters are acquisition boundaries

Provider adapters acquire and preserve external evidence. They do not own canonical market semantics or research logic.

### F2 — One common protocol, provider-native mechanics

All providers implement a common external contract while retaining native pagination, archive, timestamp, auth, and rate-limit behavior.

### F3 — Unsupported is typed

Unsupported sensors return `CapabilityUnavailable`, never zero/empty without reason.

### F4 — Capability claims are evidence-backed

Bloc 2 runtime evidence controls what a provider may advertise.

### F5 — Deterministic request fingerprints

Every fetch is auditable/idempotent at request level.

### F6 — Raw evidence survives

Raw payload plus acquisition metadata is preserved before downstream normalization.

### F7 — Resume is first-class

Cursor/page/archive checkpoints are serializable and restartable.

### F8 — Free-only gate runs before network access

No paid/staked/transaction/trading-auth source may silently enter the stack.

### F9 — Historical and live paths are separate orchestration modes

They may share parsers but not assumptions.

### F10 — Schema/semantic drift fail closed

Breaking schema or semantic changes require explicit review/versioning.

### F11 — Provider errors remain explicit

Geo restriction, access block, history absence, unsupported capability, provider outage, and malformed data are distinct states.

### F12 — Provider disagreement is not resolved in adapter layer

Economic synthesis happens later.

### F13 — Research never calls provider adapters directly

Research consumes canonical/replay services after later blocs.

## 2. Frozen provider implementation books

Initial implementation set:

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

Each provider has role-specific expectations, fixture requirements, and special QA documented in `02_PROVIDER_IMPLEMENTATION_BOOKS.md`.

## 3. Frozen common interface families

Adapter methods plan for:

```text
list_instruments
fetch_trades
fetch_liquidations
fetch_open_interest
fetch_funding
fetch_book
fetch_book_metrics
fetch_positioning
fetch_basis
```

Providers need implement only verified capabilities.

## 4. Frozen acquisition objects

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

## 5. Frozen error taxonomy

Minimum:

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

## 6. Frozen QA layers

```text
Q0 CONTRACT
Q1 PARSER
Q2 ACQUISITION MECHANICS
Q3 HISTORICAL BOUNDARY / RESUME
Q4 PROVIDER DEGRADATION / DRIFT
```

Normal unit tests remain offline. Tiny network smoke tests are opt-in only.

## 7. Frozen implementation sequence

```text
SENSOR-B3-I01 base models
SENSOR-B3-I02 access gate + fingerprints
SENSOR-B3-I03 retry/rate/pagination
SENSOR-B3-I04 conformance suite
SENSOR-B3-I05 Kraken
SENSOR-B3-I06 Gate
SENSOR-B3-I07 Binance
SENSOR-B3-I08 Bybit
SENSOR-B3-I09 OKX
SENSOR-B3-I10 Deribit
SENSOR-B3-I11 Coinalyze
SENSOR-B3-I12 Bitfinex archive
SENSOR-B3-I13 readiness matrix
SENSOR-B3-I14 network smoke harness
SENSOR-B3-I15 final validation
SENSOR-B3-I16 handoff
```

Each provider is an independent reviewable commit.

## 8. Frozen promotion statuses

```text
NOT_PLANNED
PLANNED
IMPLEMENTING
ADAPTER_READY
DATA_BLOCKED
ACCESS_BLOCKED
VALIDATION_FAILED
ACCESS_REVIEW_REQUIRED
```

No ambiguous unsupported state is allowed at completion.

## 9. Planning commits

```text
SENSOR-PLAN-B3A
  production adapter architecture/common contract

SENSOR-PLAN-B3B
  provider-specific implementation books

SENSOR-PLAN-B3C
  QA/resume/retry/drift/failure semantics

SENSOR-PLAN-B3D
  implementation tree/tests/staged commits

SENSOR-PLAN-B3E
  downstream integration and handoff boundaries

SENSOR-PLAN-B3F
  freeze manifest
```

## 10. Bloc 3 completion checklist

- [x] common adapter protocol defined
- [x] capability negotiation defined
- [x] request/fetch batch contracts defined
- [x] request fingerprint/idempotency defined
- [x] pagination/resume model defined
- [x] retry/rate-limit rules defined
- [x] access/auth/free-only rules defined
- [x] raw preservation defined
- [x] schema + semantic drift rules defined
- [x] provider-specific books defined
- [x] fixture doctrine defined
- [x] conformance suite defined
- [x] archive integrity rules defined
- [x] security requirements defined
- [x] staged implementation commits defined
- [x] provider readiness matrix defined
- [x] downstream boundaries defined
- [x] Bloc 4 input contract defined

## 11. Bloc 4 handoff

Bloc 4 should design the **immutable T0 raw evidence lake and manifest system** around Bloc 3 outputs.

It must decide:

1. exact partition layout;
2. file/record envelopes;
3. compression/file formats;
4. manifest/index strategy;
5. append/revision semantics;
6. checksums/integrity;
7. atomic writes;
8. local disk retention;
9. archive compaction rules without loss of raw evidence;
10. DuckDB discovery layer;
11. PostgreSQL operational metadata role;
12. resume/job-state durability;
13. storage quotas and L2 book retention;
14. backup/export policy;
15. raw evidence query/replay contract.

Bloc 4 must support partial provider coverage. It cannot assume every adapter exists or every historical period is available.

## 12. Final planning verdict

`PASS_BLOC_03_PLAN_FROZEN`

Rationale:

The provider adapter layer now has a complete provider-independent protocol, provider-specific implementation books, fail-closed access/error semantics, deterministic acquisition/resume rules, fixture and conformance requirements, staged implementation commits, and a strict downstream boundary into immutable raw evidence storage.

`human_review_required = TRUE`
`next_bloc_planning_authorized = FALSE until operator asks for Bloc 4`
