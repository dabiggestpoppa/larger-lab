# BLOC 2 — HISTORICAL CAPABILITY PROBE ARCHITECTURE

**Planning status:** COMPLETE CANDIDATE  
**Implementation status:** NOT STARTED  
**Parent:** Bloc 1 — Contracts & Semantics  
**Purpose:** design a deterministic, evidence-producing capability-probe harness that proves what each candidate provider actually supports before production adapters or historical backfills are allowed.

---

## 1. Mission

Bloc 2 converts documentation claims into **verified runtime evidence**.

The question is not:

> "Does Kraken/Gate/Binance/Bybit/OKX/Deribit/Coinalyze/Bitfinex say they have historical data?"

The question is:

> "For this exact sensor, instrument family, date, granularity, endpoint/file, access mode and query shape, what did the source actually return under the free-only policy, and can that result be reproduced later?"

Bloc 2 therefore builds a **probe system**, not production ingestion.

No provider is promoted from `CANDIDATE` merely because docs exist.

---

## 2. Core outputs of the implemented probe harness

The eventual Bloc 2 implementation must produce four classes of evidence:

```text
PROBE REQUEST
  exact provider/sensor/instrument/date/granularity attempt

PROBE RESPONSE EVIDENCE
  status, headers/metadata, payload fingerprint, row/timestamp summary

CAPABILITY CLAIM
  a normalized statement derived from one or more probe attempts

COVERAGE MATRIX
  provider × sensor × date-era × granularity × instrument support state
```

The output is not yet T0 market data ingestion.
It is **T-1 infrastructure evidence** describing what T0 ingestion can reasonably attempt.

---

## 3. Providers in scope

Frozen candidate set inherited from Bloc 1:

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

No candidate is guaranteed to survive.

Bloc 2 may classify a provider/sensor pair as:

```text
VERIFIED
VERIFIED_LIMITED
VERIFIED_CURRENT_ONLY
VERIFIED_ARCHIVE_ONLY
UNSUPPORTED
ACCESS_BLOCKED
GEO_BLOCKED
AUTH_BLOCKED
PAYMENT_BLOCKED
HISTORY_BLOCKED
SEMANTICALLY_UNUSABLE
TRANSIENT_FAILURE
UNVERIFIED
```

Provider-level survival is sensor-specific.
A source may be excellent for OI and useless for historical liquidations.

---

## 4. Sensors in scope

Probe the eight canonical Bloc 1 sensor families where applicable:

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

A provider capability is never summarized only as "historical data available."
Capability is always scoped to an exact sensor family.

---

## 5. Probe dimensions

Every probe claim is conditioned on the following dimensions.

### 5.1 Provider

`provider_id`

### 5.2 Venue / market family

Examples:

```text
KRAKEN_FUTURES
GATE_USDT_PERP
BINANCE_USDM
BYBIT_LINEAR
OKX_SWAP
DERIBIT_PERPETUAL
```

### 5.3 Sensor

One canonical sensor family.

### 5.4 Instrument

At minimum probe:

```text
BTC core
ETH core
one high-liquidity alt
one mid-tail alt where supported
```

Purpose:
- distinguish endpoint support from universe breadth,
- identify BTC/ETH-only products,
- detect symbol-age limitations,
- expose inconsistent long-tail behavior.

### 5.5 Historical checkpoint

Minimum test dates:

```text
2021-06-15
2022-06-15
2024-06-15
2026-06-15
RECENT_CONTROL_DATE
```

`RECENT_CONTROL_DATE` must be selected at implementation runtime so a source that works now but not historically is distinguishable from a completely broken source.

When a provider/instrument did not exist at a checkpoint, that must be recorded as `PRE_LISTING` or `PRE_PROVIDER_HISTORY`, never generic missingness.

### 5.6 Granularity

Probe the provider-native candidates relevant to the endpoint/file.

Canonical requested comparison set where available:

```text
1m
5m
15m
1h
4h
1d
RAW_EVENT
BOOK_SNAPSHOT
```

Do not invent resampling support during Bloc 2.
If only raw trades exist, capability is `RAW_EVENT`, not "1m supported" until later normalization explicitly resamples it.

### 5.7 Access mode

```text
PUBLIC_REST
PUBLIC_WEBSOCKET
PUBLIC_ARCHIVE
FREE_API_KEY
COMMUNITY_ARCHIVE
```

### 5.8 Query mode

```text
TIME_RANGE
CURSOR
SEQUENCE
PAGE
DOWNLOAD_FILE
LATEST_ONLY
```

These dimensions form the identity of a probe.

---

## 6. Probe date strategy

The four historical eras are chosen deliberately.

### 2021

Tests deep historical support and overlap with early Field Model windows.

### 2022

Mandatory due to the large response-law / market-mechanics event family already isolated in global research.

### 2024

Tests medium-depth history and captures a more recent exchange/API era.

### 2026

Tests modern schema behavior and overlap with the current research panel.

### Recent control

Tests whether the endpoint works under present conditions at all.

A failure in 2021 plus success in 2026 means `HISTORY_LIMITED`, not `SOURCE_DOWN`.

---

## 7. Probe request contract

The implementation should expose a provider-independent object similar to:

```python
CapabilityProbeRequest(
    provider_id,
    sensor_family,
    venue_market,
    instrument_native,
    requested_start,
    requested_end,
    requested_granularity,
    access_mode,
    query_mode,
    probe_run_id,
)
```

Optional provider-native hints may exist beneath the adapter/probe layer but cannot become required fields above it.

---

## 8. Probe response contract

Every attempted request emits evidence even when it fails.

Required fields:

```text
probe_run_id
probe_id
provider_id
sensor_family
venue_market
instrument_native
requested_start
requested_end
requested_granularity
request_method
request_fingerprint
response_status_class
http_status_or_file_status
rows_returned
first_timestamp_returned
last_timestamp_returned
native_timestamp_fields
native_units_summary
pagination_detected
pagination_complete
rate_limit_metadata
requires_auth
requires_payment
geo_block_detected
payload_schema_fingerprint
payload_hash_sample
error_class
error_detail_redacted
started_at
finished_at
probe_version
```

Secrets/tokens may never be written into evidence.

---

## 9. Probe evidence must be immutable

Probe outputs are evidence records.

Re-running a probe creates a **new evidence record**, not an in-place rewrite.

Later runs may supersede earlier conclusions through a versioned `CapabilityClaim`, but historical evidence remains available.

This matters because APIs change.

Example:

```text
2026-08-29 probe:
  Binance historical liquidation archive = unavailable

2027-03-10 probe:
  Binance archive restored
```

Both observations remain true for their respective dates.

---

## 10. Documentation is supporting evidence, not probe truth

Bloc 2 should preserve two distinct evidence channels:

```text
DOCUMENTATION_EVIDENCE
RUNTIME_PROBE_EVIDENCE
```

Documentation evidence may define:
- expected endpoint,
- parameter syntax,
- published limits,
- stated access class,
- intended semantics.

Runtime evidence verifies:
- actual accessibility,
- actual history,
- actual payload shape,
- actual symbols,
- actual timestamps,
- actual rate behavior.

A contradiction must be surfaced, not silently reconciled.

Example:

```text
DOCS: "historical endpoint"
PROBE: only recent 30 days returned
VERDICT: VERIFIED_LIMITED, docs/runtime mismatch flag
```

---

## 11. Provider capability is not binary

Every provider/sensor pair receives a **capability vector**, not one yes/no flag.

Minimum vector:

```text
accessibility
free_only_compliance
auth_mode
historical_depth
granularity_range
instrument_breadth
pagination_quality
timestamp_clarity
unit_clarity
schema_stability
rate_limit_usability
archive_reproducibility
PIT_suitability
semantic_fit
```

Each coordinate is scored/described separately.

---

## 12. Minimum probe instrument basket

Implementation default:

```text
BTC
ETH
SOL
MID_TAIL_CONTROL
```

`MID_TAIL_CONTROL` is selected per venue from a supported non-core perpetual with enough history to make the probe meaningful.

Do not require the same mid-tail symbol on all venues if listing histories differ.

Record:

```text
selection_reason
listing_start
listing_end
contract_type
```

---

## 13. Historical search algorithm

Bloc 2 should not brute-force entire archives.

Use staged discovery:

```text
1. RECENT CONTROL
2. EXACT TARGET CHECKPOINTS
3. EARLIEST-HISTORY BINARY SEARCH / BOUNDED SEARCH IF NEEDED
4. LOCAL GAP SAMPLING
5. STOP
```

If the provider offers explicit archive listings, inspect manifest/index first rather than probing arbitrary dates blindly.

If history is sequence/cursor based rather than timestamp based, use provider-native navigation while preserving requested target date in the evidence.

---

## 14. Earliest-history estimation

When documentation does not state a trustworthy earliest date, estimate `earliest_verified_history`.

Preferred procedure:

```text
A. test recent control
B. test 2024
C. test 2022
D. test 2021
E. if boundary lies between eras, perform bounded binary search by month/quarter
F. stop once boundary precision reaches one month unless a tighter boundary is scientifically necessary
```

Do not waste requests discovering the first individual millisecond of history.

---

## 15. Gap detection strategy

A source may return the requested endpoints but contain internal gaps.

For each verified history era, sample:

```text
start-window
middle-window
end-window
```

When archive files expose calendar partitions, enumerate partition continuity directly.

Metrics:

```text
expected_intervals
observed_intervals
coverage_ratio
largest_gap
number_of_gaps
gap_reason_if_known
```

For event data, use expected-active-period heuristics rather than pretending a fixed event should occur every interval.

---

## 16. Timestamp semantics audit

Every provider/sensor must answer:

```text
What event does the timestamp represent?
UTC?
interval open?
interval close?
publication time?
funding effective time?
snapshot observation time?
trade execution time?
server receipt time?
```

If semantics are unclear:

`TIMESTAMP_SEMANTICS_UNCLEAR`

and the capability cannot be marked `PIT_READY`.

---

## 17. Unit semantics audit

For every quantity field record native unit.

Examples:

```text
contracts
base asset
quote asset
USD notional
coin-margined contract units
percentage
fraction
bps
```

Do not normalize inside the probe harness.

Bloc 2 only determines whether enough metadata exists for Bloc 5 normalization to do so safely.

---

## 18. Liquidation semantic audit

Liquidation data is especially non-equivalent.

Probe must identify whether a source represents:

```text
individual forced-order executions
liquidation event messages
interval liquidation volume
long/short liquidation totals
partial snapshots
aggregated vendor estimates
```

Then map to Bloc 1 equivalence class.

A trade-level liquidation flag and an hourly aggregated liquidation total are not `EXACT_EQUIVALENT`.

---

## 19. Order-flow semantic audit

Order-flow candidates may expose:

```text
aggressor side on individual trades
isBuyerMaker-like maker flag
interval taker buy/sell volume
CVD
aggressor differential
```

Probe must document whether side semantics are explicit or reconstructed.

Reconstruction belongs to later normalization/observable blocs, not Bloc 2.

---

## 20. Book/depth semantic audit

Historical books must distinguish:

```text
full-depth event stream
periodic L2 snapshot
N-level snapshot
precomputed depth metric
spread metric
slippage metric
```

Book support is not a single boolean.

The coverage matrix must preserve book type and depth count/band semantics.

---

## 21. Funding semantics audit

Probe must record:

```text
funding value unit
funding interval
funding effective timestamp
historical publication timing
predicted vs realized funding
```

Predicted funding may not silently substitute for realized funding.

---

## 22. Open-interest semantics audit

Probe must determine whether OI is expressed as:

```text
contracts
base units
quote notional
USD notional
venue aggregate
instrument-specific
```

If multiple OI fields coexist, record all native field names and meanings.

---

## 23. Rate-limit probe

Do not intentionally abuse endpoints.

Use a conservative rate-limit audit:

```text
published rate limit
response headers if present
successful small sequential request set
429/limit behavior if naturally encountered
retry-after semantics
```

Never stress-test a free endpoint aggressively.

The goal is scheduler design, not capacity testing.

---

## 24. Authentication probe

Classify:

```text
NO_AUTH
FREE_API_KEY
ACCOUNT_REQUIRED_NO_PAYMENT
PAYMENT_METHOD_REQUIRED
PAID_SUBSCRIPTION_REQUIRED
UNVERIFIED
```

Bloc 1 free-only gate remains authoritative.

If payment method or subscription is required for the necessary history:

`PAYMENT_BLOCKED`

regardless of how useful the source would be.

---

## 25. Geo/access failure handling

A request failing from the current environment does not automatically prove the source is globally unavailable.

Classify separately:

```text
GEO_BLOCKED
DNS_BLOCKED
TLS_FAILURE
SOURCE_5XX
CLIENT_4XX
AUTH_BLOCKED
RATE_LIMITED
NETWORK_TIMEOUT
```

Do not bypass geo restrictions.

A geo-blocked source may remain reference evidence but cannot be required for the local runtime if the intended deployment region cannot use it.

---

## 26. Reproducibility requirement

Each probe must be reproducible from a generated command/specification without preserving secrets.

Evidence should record:

```text
adapter_probe_version
provider_endpoint_id
normalized request parameters
request timestamp
environment class
```

A future developer should be able to rerun the same logical probe.

---

## 27. Probe harness architecture

Target implementation structure later:

```text
crypto_sensor_fabric/
  probes/
    models.py
    runner.py
    planner.py
    evidence.py
    scoring.py
    coverage.py
    failures.py
    redaction.py

  providers/
    <provider>/probe.py

  config/
    probe_targets.yaml
    historical_checkpoints.yaml
```

Provider `probe.py` is intentionally smaller than future full production adapter.

It only needs enough provider-native knowledge to verify capability.

---

## 28. Probe lifecycle

```text
PLAN
  ↓
VALIDATE FREE-ONLY ACCESS ASSUMPTIONS
  ↓
ATTEMPT RECENT CONTROL
  ↓
ATTEMPT HISTORICAL CHECKPOINTS
  ↓
AUDIT PAGINATION / TIMESTAMPS / UNITS
  ↓
STORE IMMUTABLE EVIDENCE
  ↓
DERIVE CAPABILITY CLAIM
  ↓
UPDATE COVERAGE MATRIX
  ↓
HUMAN REVIEW
```

No production adapter promotion occurs automatically.

---

## 29. Probe scheduling

During initial build:

- deterministic manual/CLI execution,
- provider-by-provider,
- sensor-by-sensor,
- low concurrency,
- cached docs metadata where useful.

Do not build distributed orchestration yet.

Later CI may run a **small recent-control smoke subset**, not the entire historical matrix on every commit.

---

## 30. Expected final capability artifacts

After implementation the harness should emit:

```text
provider_coverage_matrix.parquet
provider_coverage_matrix.csv
provider_capability_claims.jsonl
probe_evidence.jsonl
probe_failures.jsonl
provider_coverage_report.md
sensor_gap_matrix.csv
source_promotion_candidates.yaml
```

The CSV/Markdown outputs are human review surfaces.
The JSONL/Parquet outputs are machine-readable evidence.

---

## 31. Bloc boundary

Bloc 2 ends when capability is **verified and evidenced**.

Bloc 2 does NOT:

- build complete historical backfill pipelines,
- download the entire history,
- define raw-lake partitioning implementation,
- normalize all provider data,
- construct T2 mechanical observables,
- run MECH/LF research.

Those belong to later blocs.

---

## 32. Completion doctrine

A provider/sensor pair may proceed to production adapter planning only if:

1. free-only gate passes,
2. at least one real request/file probe succeeds,
3. historical behavior is characterized,
4. timestamp semantics are adequate,
5. native units are identified,
6. pagination/archive mechanics are understood,
7. evidence is reproducible,
8. semantic mapping to Bloc 1 is defensible.

Otherwise it remains limited, corroborative, blocked, or excluded.

---

## 33. Planning decision

`BLOC_02_CAPABILITY_ARCHITECTURE_READY`

This file defines the probe system boundary, evidence model, historical-date matrix, provider/sensor dimensions, semantic audits, access/failure handling and required output artifacts.

`human_review_required = TRUE`
`implementation_authorized = FALSE`
