# BLOC 3 — PRODUCTION PROVIDER ADAPTER ARCHITECTURE

**Planning status:** IN PROGRESS  
**Implementation status:** NOT STARTED  
**Branch:** `agent/crypto-sensor-fabric-plan`  
**Parent:** Bloc 2 capability-probe plan  
**Purpose:** define the production acquisition layer that turns verified provider capability into immutable T0 evidence without allowing provider-specific semantics to leak into the canonical T1/T2 model.

---

## 1. Bloc 3 mission

Bloc 2 answers:

> What can each provider actually deliver, under what access/history/semantic constraints?

Bloc 3 answers:

> How do we acquire that verified evidence repeatedly, reproducibly, safely, and provider-independently?

Bloc 3 is the production adapter layer.

It does **not** yet own:

- T1 canonical unit normalization,
- cross-provider identity resolution,
- cross-venue aggregation,
- T2 feature construction,
- historical bulk backfill orchestration,
- live cross-provider synthesis,
- research model logic.

Those are later blocs.

The adapter's job is narrower and stricter:

```text
VERIFIED CAPABILITY CLAIM
        ↓
PROVIDER ADAPTER
        ↓
PROVIDER-NATIVE REQUEST
        ↓
IMMUTABLE T0 RAW EVIDENCE
        ↓
PROVIDER-NATIVE PARSED RECORD
        ↓
HANDOFF TO T1 NORMALIZATION
```

---

## 2. Non-negotiable architectural boundary

The adapter layer MUST preserve provider reality.

A Kraken adapter does not emit a generic `market_liquidation_state`.

It emits Kraken liquidation evidence with Kraken semantics.

A Gate adapter does not pretend its interval liquidation statistics are identical to Deribit trade-level liquidation flags.

The adapter boundary therefore separates:

```text
PROVIDER TRANSPORT / FORMAT
from
CANONICAL ECONOMIC SEMANTICS
```

Provider adapters may parse payloads into typed provider-native records, but they may not perform cross-provider economic interpretation beyond transformations explicitly required for safe parsing.

Forbidden in Bloc 3:

- combining venues,
- converting provider observations into cross-venue consensus,
- declaring one provider's field equivalent to another provider's field,
- silently converting inverse/linear contract economics,
- replacing native units with USD-normalized values,
- generating signal/research scores.

---

## 3. Adapter framework topology

Planned package boundary:

```text
quant-lab/src/crypto_sensor_fabric/
  adapters/
    base/
      protocol.py
      models.py
      capabilities.py
      requests.py
      responses.py
      errors.py
      retry.py
      rate_limit.py
      pagination.py
      auth.py
      evidence.py
      manifests.py
      fixtures.py

    kraken/
    gate/
    binance/
    bybit/
    okx/
    deribit/
    coinalyze/
    bitfinex_archive/
```

Provider implementation code must depend inward on `adapters/base`, not sideways on other provider adapters.

No provider adapter imports another provider adapter.

---

## 4. Core adapter protocol

Every production provider adapter implements the same capability-aware interface.

Conceptual contract:

```python
class MechanicalProviderAdapter(Protocol):
    provider_id: ProviderId

    def capabilities(self) -> AdapterCapabilityManifest: ...
    def list_instruments(self, request: InstrumentDiscoveryRequest) -> ProviderResult: ...
    def fetch_trades(self, request: TradeRequest) -> ProviderResult: ...
    def fetch_liquidations(self, request: LiquidationRequest) -> ProviderResult: ...
    def fetch_open_interest(self, request: OpenInterestRequest) -> ProviderResult: ...
    def fetch_funding(self, request: FundingRequest) -> ProviderResult: ...
    def fetch_book_snapshots(self, request: BookSnapshotRequest) -> ProviderResult: ...
    def fetch_book_metrics(self, request: BookMetricRequest) -> ProviderResult: ...
    def fetch_positioning(self, request: PositioningRequest) -> ProviderResult: ...
    def fetch_basis(self, request: BasisRequest) -> ProviderResult: ...
```

Unsupported methods must return typed `NOT_SUPPORTED` results or raise the framework's typed capability exception.

They may not return empty success results that look like valid zero-row market data.

---

## 5. Capability-aware execution

Production adapters do not hard-code provider assumptions from planning docs.

They consume a versioned capability manifest generated from Bloc 2 evidence.

The manifest includes, per provider/sensor scope:

```text
provider
venue
sensor
instrument_scope
access_mode
capability_status
evidence_level
earliest_verified_history
latest_verified_history
granularity_set
query_modes
pagination_mode
native_units
timestamp_semantics
semantic_equivalence_class
rate_limit_model
known_gaps
known_failures
free_only_status
verified_at
```

Before any fetch, the adapter performs a preflight check.

Example:

```text
request = Gate BTC liquidation 5m for 2022-06
manifest says VERIFIED_MULTI_ERA + 5m supported
→ allowed

request = Binance historical liquidation for 2022
manifest says HISTORY_BLOCKED
→ fail closed before remote call
```

This prevents later code from repeatedly rediscovering known unsupported surfaces.

---

## 6. Request objects

All provider requests derive from one base envelope.

Minimum fields:

```text
provider_id
sensor_family
venue_market
native_instrument
canonical_asset_hint      # hint only; not canonical truth
start_at
end_at
granularity
query_mode
pagination_policy
request_id
correlation_id
capability_manifest_version
```

Optional provider-specific fields may exist in provider-local request extensions.

Provider-specific fields may never become required fields of the generic interface unless promoted through an architecture amendment.

---

## 7. Result envelope

Every call returns a structured result rather than naked lists/dataframes.

Minimum conceptual schema:

```text
ProviderResult
  request
  provider
  status
  records
  raw_evidence_refs
  pagination_state
  attempts
  rate_limit_state
  received_at
  completeness
  quality_flags
  warnings
  error
  adapter_version
```

Statuses:

```text
SUCCESS
SUCCESS_PARTIAL
NOT_SUPPORTED
OUT_OF_VERIFIED_HISTORY
PRE_LISTING
EMPTY_VALID
RATE_LIMITED
AUTH_BLOCKED
GEO_BLOCKED
PAYMENT_BLOCKED
TRANSIENT_FAILURE
PROVIDER_FAILURE
SCHEMA_DRIFT
SEMANTIC_BLOCK
CORRUPT_PAYLOAD
```

`EMPTY_VALID` requires explicit evidence that the source successfully returned a valid empty interval.

Zero rows alone do not imply `EMPTY_VALID`.

---

## 8. T0 raw-evidence rule

Every successful or materially informative remote/file interaction must preserve immutable evidence before provider-native parsing is considered canonical for later stages.

T0 evidence envelope includes:

```text
request_id
provider
endpoint_or_archive
request_parameters_redacted
http_status_or_file_status
response_headers_relevant
received_at
content_hash
content_type
raw_size_bytes
source_locator
adapter_version
capability_manifest_version
```

Secrets/auth tokens must never be archived.

For public archive files, T0 should preserve:

```text
source URL/path
provider checksum if published
local checksum
file size
retrieved_at
archive partition identity
```

For live/public REST responses, T0 should preserve exact response bytes or lossless JSON representation where lawful/practical.

---

## 9. Raw-evidence ordering invariant

Processing order must be:

```text
REMOTE RESPONSE / FILE
      ↓
CAPTURE RAW EVIDENCE
      ↓
VERIFY HASH / BASIC INTEGRITY
      ↓
PARSE PROVIDER-NATIVE RECORDS
      ↓
VALIDATE PROVIDER SCHEMA
      ↓
RETURN ProviderResult
```

Do not parse and discard the raw source first.

If raw persistence fails for a source configured as evidence-required, the fetch must fail closed rather than return untraceable data.

---

## 10. Provider-native parsed records

Bloc 3 may define typed provider-native record objects solely to eliminate format ambiguity and make Bloc 4/5 normalization deterministic.

Examples:

```text
KrakenLiquidationMetricRecord
GateContractStatsRecord
BinanceAggTradeRecord
BybitOpenInterestRecord
OkxBookRecord
DeribitTradeRecord
CoinalyzeLiquidationRecord
BitfinexCommunityLiquidationRecord
```

These objects preserve:

- native field names in metadata/mapping,
- provider units,
- provider timestamps,
- native symbol,
- contract market,
- provider sequence IDs if available,
- source record identity.

They do not replace native values with normalized values.

---

## 11. Adapter determinism

Given:

```text
same raw evidence bytes
same adapter version
same parsing configuration
```

the adapter parser must produce identical provider-native records.

Any parsing change that alters records requires adapter version increment and fixture regeneration.

This is essential for historical reproducibility.

---

## 12. Network and archive adapters share one evidence contract

Some sources are APIs.
Some are public bulk files.
Some may be community archives.

The framework therefore distinguishes transport type:

```text
REST
WEBSOCKET_LIVE
BULK_HTTP_ARCHIVE
OBJECT_ARCHIVE
LOCAL_IMPORTED_ARCHIVE
AGGREGATOR_API
```

But all feed the same T0 evidence architecture.

The Bitfinex community archive must not be forced into fake REST semantics.

Binance public-data bulk archives must not be treated as live API responses.

---

## 13. Sync vs async

Production implementation should support asynchronous network I/O internally where useful, but research callers should not be required to manage raw HTTP concurrency.

Preferred shape:

```text
async provider client internals
+ deterministic bounded concurrency
+ explicit sync orchestration wrapper where needed
```

Concurrency must respect per-provider rate limits and archive host limits.

No unbounded `gather()` fan-out.

---

## 14. Retry doctrine

Retry only when the failure is plausibly transient.

Retryable examples:

```text
429 where Retry-After/backoff permits
5xx transient provider error
connection reset
timeout
archive temporary unavailable
```

Non-retryable examples:

```text
PAYMENT_BLOCKED
GEO_BLOCKED
AUTH_BLOCKED due missing required auth contract
NOT_SUPPORTED
OUT_OF_VERIFIED_HISTORY
PRE_LISTING
schema incompatibility
semantic ambiguity
invalid symbol
```

Retries must not turn deterministic hard failures into latency storms.

---

## 15. Pagination doctrine

Pagination must be provider-local but framework-observable.

Every page records:

```text
page_index
cursor_in
cursor_out
request_window
row_count
first_native_timestamp
last_native_timestamp
content_hash
```

The adapter must detect:

- repeated cursors,
- repeated pages,
- non-monotonic pages,
- timestamp overlap,
- gaps created by limit boundaries,
- silent truncation.

Historical pagination is considered complete only when the requested interval is demonstrably covered or a typed limitation is returned.

---

## 16. Rate-limit doctrine

Rate limits are data-quality infrastructure, not an afterthought.

Per provider define:

```text
limit type
window
weight model
burst allowance
remaining quota visibility
retry-after semantics
concurrency ceiling
```

A central rate-limit interface should expose permit acquisition but provider-specific policies remain local.

No adapter should sleep arbitrary hard-coded seconds scattered throughout provider methods.

---

## 17. Authentication isolation

The first fabric is designed for public/free sources.

Where a free API key is legitimately required, credentials must enter only through the auth subsystem.

Rules:

- no keys in code,
- no keys in manifests committed to Git,
- no key in T0 raw evidence,
- no key in logs,
- no provider adapter reading arbitrary environment variables itself,
- auth requirements declared in provider capability config.

Free-only policy remains hard:

```text
cost_usd_required = 0
payment_method_required = false
staking_required = false
transaction_required = false
```

A free API key is allowed only when no paid commitment/payment method is required.

---

## 18. Geo/access behavior

Do not bypass provider restrictions.

When an endpoint is inaccessible from the intended runtime region:

```text
GEO_BLOCKED
```

is emitted and recorded.

No VPN/proxy evasion logic belongs in the adapter framework.

Provider-role decisions may later route that sensor to another source.

---

## 19. Schema-drift handling

Every provider adapter must fingerprint the payload schema used by parsing fixtures and runtime observations.

Schema drift states:

```text
NO_CHANGE
ADDITIVE_COMPATIBLE
SEMANTICALLY_UNCERTAIN
BREAKING
```

Unexpected field removal/type change must fail closed if it affects canonical parsing.

Unknown additive fields may be archived and ignored until reviewed.

Do not opportunistically reinterpret new fields at runtime.

---

## 20. Provider time semantics

Adapters must preserve all native time concepts available:

```text
event_time
exchange_timestamp
interval_start
interval_end
publication_time
settlement_time
funding_time
server_time
```

Bloc 3 does not decide final `effective_at` semantics globally; it delivers enough provider-native timing information for T1 PIT normalization to do so deterministically.

Where Bloc 2 marked timestamp semantics ambiguous, the production adapter may capture raw data but must preserve `SEMANTIC_BLOCK` against PIT-ready promotion.

---

## 21. No silent coercion

Examples of forbidden adapter behavior:

```text
string -> 0 when parse fails
missing field -> 0
NaN -> 0
unknown side -> SELL
unknown unit -> USD
unknown timestamp -> response time
empty response -> no market event
```

Instead emit typed parsing/quality states.

---

## 22. Observability

Every adapter call should emit structured operational telemetry:

```text
provider
sensor
request_id
latency_ms
attempts
rows
bytes
status
rate_limit_wait_ms
pages
raw_evidence_count
schema_fingerprint
```

Telemetry does not contain secrets or full market payloads.

Metrics must distinguish provider failure from legitimate empty market data.

---

## 23. Idempotency

A historical request should be safely repeatable.

Re-running the same source interval may create a new evidence retrieval record, but storage logic should identify byte-identical evidence and avoid accidental duplicate canonical source rows later.

Use stable source identity components where available:

```text
provider
endpoint/archive
native instrument
sensor
source event/sequence ID
provider timestamp
content hash
```

Deduplication policy itself belongs primarily to later storage/normalization blocs, but adapters must expose sufficient identity.

---

## 24. Provider adapter role classes

After Bloc 2 execution, each provider/sensor role may be configured as:

```text
PRIMARY
SECONDARY
CORROBORATOR
MICROSCOPE
CURRENT_ONLY
ARCHIVE_ONLY
DISABLED
```

These roles influence orchestration priority but do not change underlying evidence semantics.

A `MICROSCOPE` source such as trade-level liquidation data may be lower-coverage but higher-mechanism-resolution.

---

## 25. Adapter selection

Higher layers request an economic sensor + venue/provider scope through capability-aware orchestration.

They do not import provider clients directly.

Selection logic later may ask:

```text
Give me all verified liquidation sources for BTC at 2022-06-15 5m
```

The registry can return provider adapters able to serve the request.

Bloc 3 supplies the adapter registry contract; cross-source synthesis remains later.

---

## 26. First implementation wave

Wave A — core broad coverage:

```text
KRAKEN_FUTURES
GATE_FUTURES
BINANCE_USDM
BYBIT_LINEAR
```

Wave B — specialized / additional independence:

```text
OKX_SWAP
DERIBIT
```

Wave C — corroboration:

```text
COINALYZE
BITFINEX_COMMUNITY_ARCHIVE
```

Every provider gets its own implementation commit and fixtures.

---

## 27. Hard stop gate

Bloc 3 implementation is not considered complete because the Python class imports successfully.

Each production adapter must prove:

1. it consumes Bloc 2 capability claims,
2. unsupported history fails closed,
3. request objects are deterministic,
4. raw evidence is captured,
5. parsing is reproducible from fixtures,
6. pagination terminates safely,
7. retries respect error class,
8. rate limits are centrally controlled,
9. schema drift is detectable,
10. secrets are absent from logs/evidence,
11. provider-native units/timestamps survive parsing,
12. no T2 synthesis occurs.

---

## 28. Planning decision for this chapter

Bloc 3 will be planned as a reusable acquisition subsystem, not eight unrelated API scripts.

The core abstraction is:

> verified capability + deterministic request + immutable evidence + typed provider-native parse.

Everything above that boundary belongs to later normalization/research layers.
