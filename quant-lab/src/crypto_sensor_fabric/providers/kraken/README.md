# Kraken Futures — Production Adapter (SENSOR-B3-I05)

Provider package for `KRAKEN_FUTURES` — the FIRST production provider adapter
built on the Bloc 3 common foundation (SENSOR-B3-I01..I04R2).

**Checkpoint verdict:** `PASS_SENSOR_B3_I05_KRAKEN_ADAPTER_OFFLINE` (pending
operator review) — production code + offline fixtures + common conformance only.
**No live network validation occurred in I05** (reserved for the opt-in tiny
network smoke at SENSOR-B3-I14).

## Role

Kraken Market Analytics is a **provider-computed analytics surface**.  The
adapter acquires and preserves provider-native evidence; it does NOT
reconstruct raw exchange events, cross-venue CVD, locally derived OI/book
depth, trade-level liquidation anatomy, or canonical T1/T2 state.  A
provider-computed metric is NOT automatically `EXACT_EQUIVALENT` to a
Fabric-derived metric — where Bloc 2 evidence says `NORMALIZABLE_COMPARABLE`
or weaker, that class is preserved.  This adapter performs **no economic
normalization** (that belongs to Bloc 5+).

## Capabilities

Exactly six I14-promoted production paths
(`source_promotion_candidates.yaml`, schema_version 2.0):

| Sensor | I14 role | history_scope | verified history | redundancy | methodology pin |
|---|---|---|---|---|---|
| MECHANICAL_BASIS | PRIMARY | HISTORICAL | 2022-06-15 → | R1_SINGLE_INDEPENDENT | `kraken_futures-basis` |
| MECHANICAL_BOOK_METRIC | PRIMARY | HISTORICAL | 2024-06-15 → | R1_SINGLE_INDEPENDENT | `kraken_futures-book_metric` |
| MECHANICAL_FUNDING | SECONDARY | HISTORICAL | 2026-06-15 → | R3_THREE_PLUS_INDEPENDENT | `kraken_futures-funding` |
| MECHANICAL_LIQUIDATION | PRIMARY | HISTORICAL | 2021-06-15 → | R3_THREE_PLUS_INDEPENDENT | `kraken-market-analytics-liquidation-volume` |
| MECHANICAL_OPEN_INTEREST | PRIMARY | HISTORICAL | 2024-06-15 → | R2_TWO_INDEPENDENT | `kraken_futures-open_interest` |
| MECHANICAL_POSITIONING | PRIMARY | HISTORICAL | 2024-06-15 → | R2_TWO_INDEPENDENT | `kraken_futures-positioning` |

Each capability carries the exact native acquisition mode granted by
`ProviderNativeCapabilityEvidence` (SENSOR-B3-I05 seam):

- `historical_mode = REST_RANGE`
- `pagination_mode = TIME_RANGE`
- endpoint family `kraken-market-analytics/{analytics_type}` — the Market
  Analytics family `https://futures.kraken.com/api/charts/v1/analytics/{symbol}/{analytics_type}`
- `since`/`to` in epoch seconds, `interval` in seconds
- completion: `result.more == false`; resume: re-issue `since` at the oldest
  bucket

The declared production set equals the I14 promotion set exactly (exact-set
test) — no silent omission, no seventh path.

## Unsupported

- **MECHANICAL_TRADE** — NOT promoted by I14.  Kraken `/derivatives/api/v3/history`
  experienced current-surface/schema problems (I13R1 `F_SCHEMA_CHANGED`,
  "payload shape does not match sensor contract").  Typed `CapabilityUnavailable`.
- **MECHANICAL_BOOK_SNAPSHOT** — NOT promoted by I14.  `/orderbook` snapshot
  assumptions hit the same schema problem.  Typed `CapabilityUnavailable`.

These never return `[]` / `0` / `None` / `EMPTY_VALID`; the adapter raises the
canonical typed `CapabilityUnavailable`.

## Access

- Free-only access gate runs **before any transport call** (no bypass).
- `access_path = PUBLIC_REST`, `auth = NO_AUTH` — no trading credentials, no
  account credentials, no signing secrets, no wallet interaction.
- Registry policy: `DEFAULT_FREE_ONLY_POLICY` (FREE_AUTOMATED, $0, no payment/
  staking/transaction requirement).
- `list_instruments` returns an explicit **configured** native instrument scope
  (`PI_XBTUSD`, `PI_ETHUSD`, `PI_SOLUSD`, `PI_DOGEUSD`) from the Bloc 2 probe
  instrument map — I05 does NOT invent an instrument-discovery endpoint.

## History

History is **ragged by sensor and sometimes by instrument** — that raggedness
is observational evidence and is preserved:

- LIQUIDATION: strong multi-era 2021–2026 evidence.
- BASIS: effective verified history from 2022 (2021 window absent).
- BOOK_METRIC: effective verified history from 2024.
- OPEN_INTEREST: effective verified history from 2024; older 2021/2022 windows
  are `EMPTY_VALID` (BTC and ETH alike).  Evidence-backed on both `PI_XBTUSD`
  and `PI_ETHUSD`.
- POSITIONING: effective verified history from 2024.
- FUNDING: older 2021/2022/2024 checkpoints are `EMPTY_VALID`; positive
  verified coverage is 2026 + recent.

`EMPTY_VALID` is never rewritten as zero / unsupported / missing /
pre-listing / history unavailable — an empty valid response is an observation.

## Time Semantics

- Analytics bucket `timestamp` arrays are **epoch seconds** per the committed
  Bloc 2 probe fixture and the corrected live probe contract
  (`live_probe_contracts.yaml`).  The I13R1 schema fingerprint
  (09_SCHEMA_FINGERPRINTS.jsonl) pins the type as `int` only; no finer
  precision is invented.  A value that is not a plausible epoch-second
  timestamp yields `actual_first/last_timestamp = None` while the raw value
  remains preserved in the envelope.
- Requests use `[start, end)` with `since`/`to` in epoch seconds.
- Whether a bucket timestamp is interval open/close/publication is NOT
  resolved by committed Bloc 2 evidence — this is a stated limitation (see
  Known Issues).  PIT readiness stays tied to the frozen methodology pin
  (`PIT_READY_WITH_METHOD_VERSION`); no new precision claim was added.

## Units

Provider-native units are preserved untouched.  No Bloc 3 conversion:

- OI stays the Kraken-native analytic representation.
- Funding stays the Kraken-native rate representation.
- Basis stays the Kraken-native basis representation.
- Book metric stays the Kraken-calculated metric representation.
- Positioning stays the Kraken-native long/short analytic representation.
- Liquidation stays the Kraken-native liquidation-volume methodology.

Any later economic normalization belongs to Bloc 5+.

## Pagination

- `result.more == true` → the batch carries a deterministic `ResumeToken`
  whose provider-native state is `since = oldest bucket` (TIME_RANGE mode).
- Re-issuing the token re-issues `since` at the oldest bucket — exact,
  re-runnable continuation; no cursor loops, no short-page guessing.
- No infinite traversal: one fetch call returns one page; continuation is
  explicit.
- Non-monotonic timestamps are flagged (`NON_MONOTONIC_TIMESTAMPS`), never
  silently dropped; duplicate page edges are annotated, not destructively
  removed.

## Rate Limits / Retry

No committed evidence exposes a known Kraken rate-limit capacity for this
surface, so `RateLimitSnapshot(limit_known=False)` is the correct default —
values are never invented.  Retryable transport failures (429 / 5xx /
timeouts) stay separate from terminal semantic/schema failures
(`RateLimited` is RETRYABLE; `SchemaDrift`, `InvalidInstrument`,
`AccessClassViolation`, `GeoRestricted` are TERMINAL and never retried).

## Schema

Common fail-closed policy per sensor, grounded in 09_SCHEMA_FINGERPRINTS.jsonl:

- KNOWN_SCHEMA → parsed native rows allowed.
- ADDITIVE_SCHEMA_CHANGE → flagged (`SCHEMA_ADDITIVE`), parsed output allowed
  only while required semantics remain intact.
- BREAKING / UNKNOWN → raw evidence preserved; parsed output BLOCKED
  (`SchemaDrift`).  Missing fields are never `dict.get(field, 0)`-defaulted.

Fingerprint shapes per path: OI `data: list[list[str]]`; funding
`data: dict{rate, relativeRate}` (each `list[list[str]]`); basis
`data: dict{basis: list[str]}`; positioning `data: list[str]`; liquidation
`data: list[str]`; book metric `data: dict{ask: {...}, bid: {...}}` (per-side
metric lists).

## Known Issues

1. **Bucket timestamp semantics** (open/close/publication) are not resolved by
   committed Bloc 2 evidence — stated as a limitation, not invented.
2. **Funding timestamp unit** — the Bloc 2 probe module comment mentions epoch
   ms "probe-observed", but no committed runtime artifact pins it; the
   committed probe fixture and live probe contract use epoch seconds, so the
   adapter treats funding bucket timestamps as epoch seconds and flags the
   ambiguity here rather than claiming ms.
3. **Rate-limit capacity unknown** — `limit_known=False` until runtime
   evidence exists.
4. **Liquidation methodology** is `kraken-market-analytics-liquidation-volume`
   (analytics family) — never merged numerically with trade-level `/history`
   `type=liquidation` rows.
5. **OI instrument scope** — evidence-backed for `PI_XBTUSD` and `PI_ETHUSD`;
   `PI_SOLUSD` / `PI_DOGEUSD` are the configured probe scope, not promoted
   claims.
6. **No live validation** — all I05 behavior is offline (fake transport).

## Fixtures

`quant-lab/tests/crypto_sensor_fabric/providers/kraken/fixtures/analytics.py`
is a **SYNTHETIC_SCHEMA_FIXTURE** matrix (labeled; never presented as raw
observed evidence) reconstructed strictly to the committed I13R1 schema
fingerprints.  Per promoted sensor:

1. valid/happy response
2. EMPTY_VALID response (e.g. OI 2022 `data:[]`, funding `rate:[]`)
3. historical/boundary response
4. provider error response (symbol-not-found envelope)
5. schema drift / malformed response
6. continuation/resume response (`more: true`) where pagination exists

The Bloc 2 probe fixtures under
`quant-lab/tests/crypto_sensor_fabric/fixtures/probe_payloads/kraken/` remain
the committed probe evidence.  No new network calls were made to obtain any
fixture.

## Examples

```python
from crypto_sensor_fabric.contracts.enums import SensorFamily
from crypto_sensor_fabric.providers.base.models import FetchRequest
from crypto_sensor_fabric.providers.base.enums import FetchPurpose
from crypto_sensor_fabric.providers.kraken import KrakenAdapter
from tests.crypto_sensor_fabric.providers.kraken._fake import FakeKrakenTransport

adapter = KrakenAdapter(transport=FakeKrakenTransport())  # offline only

request = FetchRequest(
    provider_id="KRAKEN_FUTURES",
    sensor_family=SensorFamily.MECHANICAL_OPEN_INTEREST,
    native_instrument_id="PI_XBTUSD",
    start_time=..., end_time=...,
    request_id="r1",
    purpose=FetchPurpose.BACKFILL,
    adapter_semantic_version="kraken-adapter-v1",
)
batch = adapter.fetch_open_interest(request)
# batch.raw_payloads[0] preserves the raw envelope + content hash
# batch.row_count / quality_flags (EMPTY_VALID) / next_resume_token
```

## Non-Goals

- No live network calls in I05 (reserved for SENSOR-B3-I14).
- No history backfill at scale; no T0 data lake; no Parquet/DuckDB/PostgreSQL
  ingestion; no WebSocket recorder.
- No canonical unit conversion, no cross-venue blending, no consensus, no
  order-flow / liquidation / funding / positioning STATE derivation.
- No exact-equivalence claims beyond what frozen semantic-equivalence evidence
  earned.
- No trade or book-snapshot production paths.
- No research compute; no strategies / signals / alpha / PnL.
