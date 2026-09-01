# Gate Futures — Production Adapter (SENSOR-B3-I06)

Second real production provider adapter on the hardened common foundation.
Provider id `GATE_FUTURES`, public v4 USD-settled futures REST surface.

## Role

All four promoted Gate paths are **SECONDARY**.  Provider richness does not
imply source authority; Gate is never upgraded to PRIMARY by this adapter or by
any Bloc 3 code.  Roles are frozen by I14
(`source_promotion_candidates.yaml`) and enforced by the common conformance
suite.

## Capabilities

Exact I14-promoted production set (four paths, all SECONDARY):

- `MECHANICAL_FUNDING` — `GET /api/v4/futures/usdt/funding_rate` (single
  contract), R3_THREE_PLUS_INDEPENDENT, `gate_futures-funding`.
- `MECHANICAL_LIQUIDATION` — `GET /api/v4/futures/usdt/contract_stats`,
  R3_THREE_PLUS_INDEPENDENT, `gate_futures-liquidation`.
- `MECHANICAL_OPEN_INTEREST` — `GET /api/v4/futures/usdt/contract_stats`,
  R2_TWO_INDEPENDENT, `gate_futures-open_interest`.
- `MECHANICAL_POSITIONING` — `GET /api/v4/futures/usdt/contract_stats`
  (PUBLIC market-wide statistics), R2_TWO_INDEPENDENT,
  `gate-contract-stats-public-lsr`.

OI / LIQUIDATION / POSITIONING come from the SAME physical `contract_stats`
payload, but they are SEPARATE sensor contracts.  A shared physical endpoint
does **not** make a combined sensor — no `GateMechanicalState`, no composite,
no T2 state, no signal is built.

Production symbol scope is evidence-derived (`08_HISTORY_BOUNDARIES.csv`):
`BTC_USDT` for all four promoted paths.

## Unsupported

- `MECHANICAL_TRADE` — typed `CapabilityUnavailable` (observed but NOT promoted
  by I14).
- `MECHANICAL_BOOK_SNAPSHOT` — typed `CapabilityUnavailable` (not promoted).

Neither returns `[]` / `0` / `None` / `EMPTY_VALID` for these surfaces.

## Access

PUBLIC_REST, NO_AUTH, $0.  The free-only access gate runs BEFORE any transport
call.  No trading key, account key, wallet, exchange login, private account
endpoint, staking, subscription, or paid API is ever used.

**Market-wide positioning NEVER uses the private user `/positions` endpoint.**
A test proves no production request URL can contain `/positions`.

## History

Verified effective history (I14-frozen, ragged by sensor):

- FUNDING: `2026-06-15Z .. 2026-08-23T15:44:40.901129Z`
- LIQUIDATION: `2026-06-15Z .. 2026-08-23T14:55:06.963000Z`
- OPEN_INTEREST: `2026-06-15Z .. 2026-08-23T14:55:05.522441Z`
- POSITIONING: `2026-06-15Z .. 2026-08-23T14:55:07.337755Z`

A rolling ~180-day provider retention boundary rejects older `from` values.
That rejection is typed `HistoricalRangeUnavailable` — never EMPTY_VALID, never
auth, never unsupported, never geo.  It is preserved in redacted provider-native
context.  No historical coverage is fabricated beyond I14.

## Time Semantics

- `contract_stats` request **`from` = epoch SECONDS**; provider `interval` is a
  STRING bucket (`"1h"`) — never integer seconds; NO `to` is invented.
- `contract_stats` response row **`time` = native epoch SECONDS** (current
  contract, live-verified I10R1 with exact hourly bucket alignment).  The
  I05-era probe sample (2022) recorded epoch MILLISECONDS — a provider
  semantic transition adjudicated in `BLOC_03_I10R1_STRUCTURAL_ADJUDICATION.json`;
  old-millisecond rows are NOT magnitude-rescued (convenience datetime is
  un-derivable and the smoke temporal guard flags them).
- `funding_rate` request **`from` / `to` = epoch SECONDS**; response row
  **`t` = epoch SECONDS**; `r` is a provider-native decimal string.
- Request-unit and response-unit semantics are DIFFERENT and kept distinct; a
  test prevents second/millisecond inversion.
- All four paths are `PIT_READY_WITH_METHOD_VERSION`.  Exact publication latency
  and interval open/close meaning are NOT claimed (not evidenced).

## Units

Provider-native units are preserved; no Bloc 3 normalization or reconciliation:

- liquidation sizes: contracts; liquidation USD fields: provider-supplied USD
  notionals.
- `open_interest`: contracts; `open_interest_usd`: provider-supplied USD
  notional (NOT a canonical OI-USD conversion).
- funding `r`: provider-native decimal funding rate.
- positioning LSR fields: provider-native long/short analytics.

## Pagination

No invented pagination.  `contract_stats` traversal is the evidence-backed
single `from` / `interval` / `limit` window; `funding_rate` is a bounded `from`
/ `to` window.  Multi-window traversal / resume mechanics are **UNRESOLVED**
(no invented `from + interval` advancement, no cursor).  Each buffer returns a
single request window (`is_complete=True`, no resume token) and the limitation
is recorded in the implementation evidence.  Funding likewise returns a bounded
window.

## Known Issues

- Deeper contract_stats windowed traversal resume semantics are UNRESOLVED
  from committed evidence (single-request window only).
- Exact interval-close vs publication timestamp semantics are not evidenced.
- ~180-day rolling retention caps request depth (typed
  `HistoricalRangeUnavailable`); the I14 verified range remains the authority.
- No network validation occurred in I06 (offline only; network smoke reserved
  for SENSOR-B3-I14).

## Fixtures

Offline `SYNTHETIC_SCHEMA_FIXTURE` payloads reconstructed exactly from the
committed Bloc 2 schema fingerprints for each promoted sensor (happy, empty,
additive, schema drift, malformed timestamp, invalid contract, retention,
rate limit, provider error), plus the shared-physical-response and
sensor-specific-projection cases.  No live network calls are made to obtain
fixtures.

## Examples

```python
from crypto_sensor_fabric.providers.gate import GateAdapter
from crypto_sensor_fabric.providers.gate import PROVIDER_ID
from ...base.models import FetchRequest
from ...base.enums import FetchPurpose

adapter = GateAdapter(transport=my_injected_transport)

req = FetchRequest(
    provider_id=PROVIDER_ID,
    sensor_family="MECHANICAL_OPEN_INTEREST",
    native_instrument_id="BTC_USDT",
    start_time=...,
    end_time=...,
    request_id="r1",
    purpose=FetchPurpose.BACKFILL,
    adapter_semantic_version="gate-adapter-v1",
)
batch = adapter.fetch_open_interest(req)   # or dispatch_fetch(adapter, req)
```

## Non-Goals

- No canonical unit conversion, cross-venue CVD, liquidation/funding/positioning
  state, T2 features, signals, alpha, PnL, risk, or portfolio logic.
- No private `/positions`, no plural `POST /funding_rates` production path.
- Gate trade / book snapshot are NOT promoted.
- No network calls in I06.