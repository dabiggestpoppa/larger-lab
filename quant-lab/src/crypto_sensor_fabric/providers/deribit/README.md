# Deribit — Production Adapter (SENSOR-B3-I08)

Deribit v2 public JSON-RPC production adapter on the hardened common
foundation.  Deribit is the **mechanism microscope**: trade-level execution /
liquidation anatomy, never interval aggregate truth.

## Role

- `MECHANICAL_BOOK_SNAPSHOT` — `CURRENT_ONLY` (current snapshot surface)
- `MECHANICAL_FUNDING` — `SECONDARY` (historical hourly funding records)
- `MECHANICAL_LIQUIDATION` — `MECHANISM_MICROSCOPE` (trade-level forced
  liquidation anatomy)
- `MECHANICAL_TRADE` — `MECHANISM_MICROSCOPE` (native trade events)

All four paths are `PIT_READY_WITH_METHOD_VERSION` with methodology pins
(`deribit-book_snapshot`, `deribit-funding`,
`deribit-trade-level-liquidation-anatomy`).  No Deribit path is PRIMARY and
none is upgraded from these roles.

## Capabilities

Exactly four I14-promoted production paths:

| Sensor | Role | History |
|---|---|---|
| MECHANICAL_BOOK_SNAPSHOT | CURRENT_ONLY | CURRENT_ONLY |
| MECHANICAL_FUNDING | SECONDARY | HISTORICAL |
| MECHANICAL_LIQUIDATION | MECHANISM_MICROSCOPE | HISTORICAL |
| MECHANICAL_TRADE | MECHANISM_MICROSCOPE | HISTORICAL |

Production instrument scope (evidence-derived from
`08_HISTORY_BOUNDARIES.csv`): **BTC-PERPETUAL ONLY** for all four paths.

## Unsupported

Typed `CapabilityUnavailable` under CURRENT I14:

- MECHANICAL_BASIS
- MECHANICAL_BOOK_METRIC
- MECHANICAL_OPEN_INTEREST
- MECHANICAL_POSITIONING

Never `[]` / `0` / `None` / `EMPTY_VALID` for these.

## Access

- `PUBLIC_REST` / `NO_AUTH` / `FREE_AUTOMATED` / `$0`
- Free-only access gate runs BEFORE every transport call.
- No API key, no trading account, no payment, no private endpoint.

## History

I14 verified history stays LITERAL:

- BOOK_SNAPSHOT: `2026-08-30T13:55:12.240279Z` (single current snapshot)
- FUNDING: `2021-06-15T00:00:00Z .. 2026-08-23T14:55:12.048205Z`
- LIQUIDATION: `2026-08-23T14:55:11.833559Z` (single timestamp)
- TRADE: `2026-08-30T13:55:11.474770Z` (single timestamp)

Historical *request* capability does NOT imply verified deep historical
*coverage*: the LIQUIDATION/TRADE verified bounds are literal single
timestamps; older evidence-basis probe ids do not move the verified boundary.

## Time Semantics

- Request `start_timestamp` / `end_timestamp`: **epoch MILLISECONDS** (int).
- Response `timestamp` (trade/liquidation/funding rows, book result):
  **epoch MILLISECONDS** (int).
- Strict `type(v) is int` validation; `True`/`False`/float/string/`None`
  timestamps are schema drift and fail closed (raw payload preserved in the
  failure envelope).  No silent coercion.

## Units

- Trade: `price` USD, `amount`/`contracts` base, `direction` = provider-native
  taker/aggressor side (preserved verbatim, never reinterpreted).
- Liquidation: trade-level events; the `liquidation` flag
  (`"liquidation" | "taker" | "maker"`) marks forced liquidations.  NEVER
  summed/bucketed into interval liquidation totals (T2-SEM-06).
- Funding: `index_price`, `prev_index_price`, `interest_1h`, `interest_8h`
  (decimal fractions).  `funding_rate`/`funding_1h`/`funding_8h` are
  probe-fixture-only UNVERIFIED additive fields — preserved when present,
  never required, never collapsed.
- Book: levels `[price, amount, ...]` numeric as returned (no conversion).

No canonicalization.  No annualization.  No carry/regime/health/signal.

## Pagination

- Trade/liquidation: the result envelope carries `has_more`; rows live under
  `result.trades`.  `include_old=true` is REQUIRED for historical depth.
- Funding: `result` is a **raw list** (observed LIVE) — never `{data:[...]}`.
- Book: current-only snapshot, no pagination.

**Continuation beyond the evidenced single request window is NOT proven by
committed I13 evidence** — no `next_resume_token` is ever invented
(pagination/resume = **LIMITED**).

## Completion semantics

Completion is decided FIRST; quality flags are assigned AFTER, so a
`COMPLETE` batch never carries `PARTIAL_INTERVAL` (PARTIAL means partial,
COMPLETE means complete; PARTIAL/GAP are mutually exclusive).

Coverage truth comes from the FULL SOURCE page (schema-validated source-row
timestamps), never from a filtered projection: for LIQUIDATION the semantic
view (only forced-liquidation events) can be narrower than the acquisition
surface, and a projection can never manufacture completeness.

- **BOOK_SNAPSHOT** (CURRENT_ONLY): complete per current-snapshot unit.
- **TRADE / LIQUIDATION**: `is_complete=True` ONLY when the semantic output
  is non-empty, EVERY source-page row lies inside the requested
  `[start_time, end_time)` window, and `has_more == false` (provider-native
  terminal flag for the current request window).
- **FUNDING**: **never** certified complete.  The "short page under the count
  cap is exhaustive" rule is only a characterization heuristic; committed
  evidence does not prove `get_funding_rate_history` returns ALL window
  records whenever `len(result) < count` (`completion_proof = LIMITED`).

Incomplete non-empty pages are returned truthfully with `PARTIAL_INTERVAL`
(in-window coverage) or `GAP_DETECTED` (no in-window coverage); empty pages
are `EMPTY_VALID` with `is_complete=False` (never GAP from an empty
response).  Unknown continuation != complete acquisition.

## Endpoints

- `GET https://www.deribit.com/api/v2/public/get_last_trades_by_instrument`
  — TRADE + LIQUIDATION (same physical surface, distinct logical sensors;
  never a combined state)
- `GET https://www.deribit.com/api/v2/public/get_funding_rate_history`
  — FUNDING
- `GET https://www.deribit.com/api/v2/public/get_order_book` — BOOK
  (current-only, `depth=25`, no historical cursor)

## JSON-RPC errors

Provider errors may ride HTTP 200 inside `{"error": {"code": <int>, ...}}`.
HTTP 200 does NOT imply success.  Typed mapping (probe.CODE_FAILURE, refined
by committed runtime evidence where any):

- `40400` → InvalidInstrument
- `10001` → RateLimited
- `10000` / `10002` → AuthenticationRequired
- `-32601` / `-32602` → ProviderSemanticError
- unknown JSON-RPC error → ProviderSemanticError
- HTTP 429 / 403 / 5xx → RateLimited / AccessClassViolation /
  ProviderUnavailable

Provider errors are NEVER `EMPTY_VALID`.

## Raw preservation

After a successful transport response the adapter materializes an immutable
`RawPayloadEnvelope` (provider, sensor, request fingerprint, raw body, content
hash, retrieval metadata, schema state, I14 evidence ref, adapter version)
BEFORE any parsed convenience output.  Schema drift raises typed `SchemaDrift`
carrying the exact raw envelope.  A liquidation page with zero forced
liquidations still preserves the nonempty raw payload (`EMPTY_VALID`).

## Fixtures

All offline fixtures are **SYNTHETIC_SCHEMA_FIXTURE**, reconstructed from the
committed 09 schema fingerprints, live_probe_contracts.yaml, and the committed
Bloc 2 probe payloads.  Synthetic fixtures never establish capability, history,
symbol support, cursor direction, or field existence.

## Known Issues / Known Limitations

- Trade/liquidation/funding continuation beyond a single request window:
  UNRESOLVED by committed evidence → LIMITED, no invented resume.
- Funding completion proof: LIMITED — funding is never certified complete
  because the short-page-under-cap rule lacks a proven provider contract.
- Verified history bounds are literal I14 values (single timestamps for
  trade/liquidation); no deep-history claim.
- `funding_rate`/`funding_1h`/`funding_8h` are unverified additive fields.
- Liquidation is a trade-level mechanism microscope (forced-liquidation
  events) — never aggregated numerically with Gate/Kraken liquidation totals.
- Live network validation: I10 baseline PASS (all four Deribit paths;
  liquidation genuinely EMPTY_VALID in its closed window); no I10R1/I10R2
  rerun required.  See `evidence/bloc_03/BLOC_03_I10_NETWORK_SMOKE_*` and
  `BLOC_03_I10R2_SEMANTIC_SEAL_EVIDENCE.md`.

## Examples

```python
from crypto_sensor_fabric.providers.deribit import DeribitAdapter
from crypto_sensor_fabric.contracts.enums import SensorFamily

adapter = DeribitAdapter(transport=my_injected_transport)  # FAKE in tests
caps = adapter.capabilities()
batch = adapter.fetch_liquidations(fetch_request_for(SensorFamily.MECHANICAL_LIQUIDATION))
```

## Non-Goals

- NO interval liquidation totals, liquidation pressure, CVD, or directional
  interpretation.
- NO funding-state / carry / regime model; no annualization.
- NO book imbalance / spread / depth score / health.
- NO cross-venue normalization or aggregation.
- NO private account endpoints, NO trading, NO archive substitution, NO Bloc 4.
