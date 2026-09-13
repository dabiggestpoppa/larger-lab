# BLOC 3 — ADAPTER QA, RESUME, RETRY & FAILURE SEMANTICS

## 1. Purpose

This book defines the exact robustness contract every provider adapter must satisfy before it is allowed to feed later raw-lake/backfill blocs.

A successful HTTP 200 response is not enough. The adapter must prove semantic, temporal, pagination, integrity, and restart correctness.

## 2. QA layers

Every adapter is tested at five layers:

```text
Q0 CONTRACT
Q1 PARSER
Q2 ACQUISITION MECHANICS
Q3 HISTORICAL BOUNDARY / RESUME
Q4 PROVIDER DEGRADATION / DRIFT
```

### Q0 CONTRACT

Tests:
- common protocol implemented;
- capability object validates;
- unsupported methods emit `CapabilityUnavailable`;
- provider identity immutable;
- free-only gate executes before network request;
- request fingerprint deterministic.

### Q1 PARSER

Tests:
- known fixture parses exactly;
- missing required field fails closed;
- additive field tolerated/archived;
- breaking field change raises `SchemaDrift`;
- native units retained;
- timestamp precision retained;
- raw payload retrievable from parsed record provenance.

### Q2 ACQUISITION MECHANICS

Tests:
- valid range fetch;
- empty valid range;
- rate limit;
- retryable 5xx;
- terminal 4xx;
- invalid symbol;
- unsupported interval;
- provider timeout;
- checksum/archive integrity where relevant.

### Q3 HISTORICAL BOUNDARY / RESUME

Tests:
- exact start boundary;
- exact end boundary;
- adjacent requests do not drop edge records;
- provider inclusive/exclusive semantics documented;
- cursor resume reproduces same remaining rows;
- crash after page N resumes from page N checkpoint;
- repeated page/cursor loop detected;
- deterministic request IDs across rerun.

### Q4 PROVIDER DEGRADATION / DRIFT

Tests:
- changed rate-limit headers;
- missing expected field;
- extra field;
- endpoint returns HTML/error instead of JSON;
- archive file unavailable;
- geo/access restriction;
- provider marks historical endpoint deprecated;
- endpoint now requires payment/auth beyond registry classification.

## 3. Fixture doctrine

Unit tests MUST NOT require network.

Each provider gets versioned fixtures:

```text
fixtures/<provider>/<sensor>/
  happy_path/
  empty/
  boundary/
  error_rate_limit/
  error_access/
  schema_additive/
  schema_breaking/
  malformed/
```

Fixtures must include request metadata and retrieval provenance. Sanitized free API keys are never stored.

## 4. Golden fixture policy

For each critical provider/sensor pair, keep at least one golden fixture with expected:

```text
row_count
first_timestamp
last_timestamp
native_key set
parser semantic version
hash of normalized raw-record representation
```

Golden fixtures catch silent parser drift.

## 5. Resume correctness

A backfill task is represented as deterministic shards.

Planned key:

```text
provider / sensor / native_instrument / interval / shard_start / shard_end
```

State machine:

```text
PLANNED
→ IN_PROGRESS
→ PARTIAL_CHECKPOINT
→ COMPLETE

or
→ FAILED_RETRYABLE
→ FAILED_TERMINAL
→ ACCESS_REVIEW_REQUIRED
```

Resume never marks a partial shard complete without completion evidence.

## 6. Checkpoint evidence

At every successful page/archive object:

```text
request_fingerprint
provider_cursor/page
last_native_record_id if available
last_timestamp
raw_response_hash
row_count
retrieved_at
```

If the process dies, recovery starts from the last durable checkpoint rather than restarting blindly.

## 7. Idempotency

Repeated acquisition of the same deterministic request may produce multiple raw observations because providers can revise or reorder data.

Therefore:

- acquisition is idempotent at task/state level;
- raw evidence is append/preserve, not destructive overwrite;
- same request fingerprint + same payload hash = exact repeat;
- same request fingerprint + changed payload hash = revision evidence.

Bloc 4/5 decides canonical revision policy.

## 8. Pagination loop detection

Terminal `PaginationFailure` if any occurs:

```text
same cursor repeated >1 cycle
page number advances but identical content hash repeats unexpectedly
last timestamp moves backward beyond documented overlap
resume token fails deterministic round-trip
provider returns records outside requested range repeatedly
```

Do not silently skip problematic pages.

## 9. Gap detection at adapter level

Adapters may report mechanical gaps without imputing them.

Gap evidence:

```text
expected cadence
actual timestamp gap
provider returned empty
archive object absent
symbol not yet listed
provider history unavailable
```

Adapter emits a gap annotation; later quality layer interprets severity.

## 10. Rate-limit safety

Tests must prove:

- 429 honors Retry-After;
- adapter surfaces weight/cost metadata where provider exposes it;
- concurrency is externally controllable;
- retries stop at budget;
- no recursive retry stack;
- no busy loops.

## 11. Circuit-breaker handoff

Bloc 3 adapter exposes provider health signals but does not own global failover.

Signals:

```text
consecutive_failures
last_success_at
last_failure_at
failure_class
rate_limited
access_review_required
schema_drift
```

Later orchestration can open circuit or select another evidence source.

## 12. Access drift

Critical behavior:

If a previously free endpoint begins returning:

```text
payment required
subscription upgrade
credit requirement
mandatory wallet/transaction
stake requirement
trading-auth requirement
```

adapter MUST emit `AccessClassViolation` / `ACCESS_REVIEW_REQUIRED`.

It must not:
- sign up;
- fall through to paid endpoint;
- request trading permissions;
- use cached data as fresh data.

## 13. Geo restriction

`GeoRestricted` is distinct from:

```text
HISTORY_NOT_AVAILABLE
PROVIDER_DOWN
AUTH_REQUIRED
```

Reason: another deployment location or alternate provider may resolve it later, but current runtime must fail closed.

## 14. Schema drift policy

### Additive change

New unknown optional key:
- raw payload preserved;
- parser can continue if required semantics unchanged;
- emit `SCHEMA_ADDITIVE` quality flag;
- CI fixture update required before promotion to known schema.

### Breaking change

Required key changed/removed or type semantics changed:
- parsed output blocked;
- raw payload archived;
- `SchemaDrift` emitted;
- human review required.

## 15. Semantic drift policy

More dangerous than schema drift.

Examples:
- provider changes OI from contracts to base asset;
- liquidation field changes side convention;
- funding timestamps move from effective to publication time;
- depth snapshot methodology changes.

Any documented or empirically detected semantic change requires new methodology version and possibly new validity interval.

Do not rewrite historical rows under the new meaning.

## 16. Provider revision handling

If provider historical responses can change:

```text
revision_id
retrieval_time
response_hash
supersedes_hash (later storage layer)
```

must be retained.

Research replay should eventually be able to distinguish what was known when vs latest revised history where relevant.

## 17. Archive integrity

For bulk files:

Required where available:

```text
Content-Length
ETag
provider checksum
local SHA-256
compression integrity
row parse count
```

A corrupt archive is `ArchiveIntegrityFailure`; never partially treat it as complete.

## 18. Time-boundary QA

For every sensor/provider:

Test requests at:

```text
exact midnight UTC
month boundary
year boundary
DST transition dates even if provider uses UTC
symbol launch boundary
known archive gap boundary
latest partially closed interval
```

Adapters must not include incomplete future/ongoing interval unless explicitly requested and marked partial.

## 19. Historical reproducibility tests

For a fixed verified historical checkpoint, repeat the same request and compare:

```text
status
record count
coverage bounds
content hash
schema signature
```

Differences are logged as provider revision/drift evidence, not silently ignored.

## 20. Latency and throughput benchmarks

Bloc 3 implementation should record but NOT optimize prematurely:

```text
requests/sec
rows/sec
MB/sec
p50/p95 latency
archive decompression rate
```

Purpose: size backfill orchestration later.

No provider is rejected merely because another is faster if it contributes unique coverage.

## 21. Security tests

Must verify:

- no secrets in logs;
- no secrets in request fingerprint;
- no secrets in raw file paths;
- TLS verification enabled;
- redirects constrained to expected provider/archive domains where practical;
- downloaded archive filenames sanitized;
- decompression path traversal blocked.

## 22. Offline contract suite

Base adapter tests should include fake provider transport implementing:

```text
success
empty
429
500→success
permanent403
schema drift
cursor loop
archive checksum mismatch
```

All real provider adapters inherit/pass the same conformance suite.

## 23. Network smoke tests

Separate from unit CI.

Optional explicit smoke command:

```text
pytest -m sensor_network_smoke
```

Rules:
- disabled by default;
- $0 endpoints only;
- tiny query ranges;
- no uncontrolled download;
- results produce evidence artifact;
- failure does not mutate schemas automatically.

## 24. Promotion gate

A provider/sensor adapter is `ADAPTER_READY` only if:

- Bloc 2 evidence >= required level;
- common conformance suite passes;
- provider fixtures pass;
- free-only access gate passes;
- boundary/resume tests pass;
- raw preservation proven;
- native semantics documented;
- no unresolved breaking schema drift;
- no hidden execution credentials.

Otherwise status is:

```text
PLANNED
IMPLEMENTING
VALIDATION_FAILED
ACCESS_BLOCKED
DATA_BLOCKED
ADAPTER_READY
```

## 25. Stop rule

Bloc 3 validation proves acquisition correctness only.

It does not imply the resulting provider data is scientifically sufficient for LF14/MECH21 until later cross-provider/quality/backfill blocs are complete.

`human_review_required = TRUE`
