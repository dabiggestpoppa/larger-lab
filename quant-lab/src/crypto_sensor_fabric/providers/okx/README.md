# OKX Swap — Bloc 3 Production Adapter (OKX_SWAP)

SENSOR-B3-I07. Provider-native acquisition + raw-evidence preservation. This is
an **acquisition boundary**: it preserves native fields/units and never performs
canonical normalization, cross-venue synthesis, or research compute.

## Role

`OKX_SWAP` — three I14-promoted production paths:

| Sensor | Role | History | Provider |
|---|---|---|---|
| MECHANICAL_BOOK_SNAPSHOT | CURRENT_ONLY | CURRENT_ONLY | 2nd-party exchange (free public REST) |
| MECHANICAL_FUNDING | PRIMARY | HISTORICAL | 2nd-party exchange (free public REST) |
| MECHANICAL_TRADE | PRIMARY | HISTORICAL | 2nd-party exchange (free public REST) |

## Capabilities

- `fetch_trades(TRADE)` -> `/api/v5/market/history-trades` (historical raw
  trade events, PRIMARY).
- `fetch_funding(FUNDING)` -> `/api/v5/public/funding-rate-history` (historical
  funding records, PRIMARY).
- `fetch_book(BOOK_SNAPSHOT)` -> `/api/v5/market/books` (CURRENT snapshot only).

Production instrument scope is evidence-backed `BTC-USDT-SWAP` for all three
paths (from `08_HISTORY_BOUNDARIES.csv`). `list_instruments()` returns this
configured production evidence scope — it is NOT live provider discovery.

## Unsupported

Under the CURRENT I14 freeze these are typed `CapabilityUnavailable` (never
`[]`/`0`/`None`/EMPTY_VALID): MECHANICAL_BASIS, MECHANICAL_BOOK_METRIC,
MECHANICAL_LIQUIDATION, MECHANICAL_OPEN_INTEREST, MECHANICAL_POSITIONING.
A queued future OKX premium/basis or deeper historical-book research queue
must NOT broaden I07.

## Access

FREE-AUTOMATED public REST, `NO_AUTH`, `$0`. The free-only access gate runs
BEFORE every transport call. No trading key, account key, wallet, or payment.
No trading endpoints.

## History

- FUNDING: verified history `2021-06-15Z .. 2026-08-23T14:55:10.584064Z`
  (I14; ragged/verified per era).
- TRADE: verified history `2021-06-15Z .. 2026-08-30T13:55:11.053007Z` (I14).
- BOOK_SNAPSHOT: CURRENT_ONLY — the frozen I14 boundary is a single timestamp
  (`2026-08-30T13:55:11.250844Z`). No historical book surface is claimed; the
  public traderecords daily-zip archive is Bloc 2 characterization ONLY (never
  substituted as production REST, never extends the I14 boundary).

## Time Semantics

OKX timestamps are millisecond-epoch **STRINGS** (funding `fundingTime`, trade
`ts`, book `ts`). They are validated strictly (`type(v) is str` + numeric-string
syntax); `None` / bool / int / float are SchemaDrift (no silent coercion). A
convenience UTC datetime is derived ONLY after validation; the native string is
preserved.

## Units

Unchanged provider-native: funding `fundingRate`/`realizedRate` (decimal
fraction — the interval is NOT frozen to "8h") + `formulaType`/`method`
(PIT-relevant, preserved when present); trade `px` (USD) / `sz` (base asset) /
`side` (aggressor, preserved verbatim) / `tradeId` / `ts`; book `bids`/`asks`
(native `[px, sz, ...]` lists — at minimum `[price, size]` per level). No
canonical conversion in Bloc 3.  Schema handling is fail-closed: the funding
and trade rows are closed fingerprint records (every structural field
required), `seqId` must be an exact int (bool rejected), and a malformed or
non-integer timestamp is SchemaDrift.

## Pagination

The two HISTORICAL surfaces (`history-trades`, `funding-rate-history`) are
provider-cursor surfaces (`after`/`before`) with **sensor-specific cursor
meanings**: trade keys around provider trade ids; funding keys around
`fundingTime`. Their continuation **direction is UNRESOLVED by committed I13
evidence**, so production issues a single evidence-backed request window
(`instId` + `limit`) and does NOT invent a continuation cursor. Deeper
multi-window after/before traversal is recorded as UNRESOLVED. The CURRENT_ONLY
book has no pagination.

### Completion truth (SENSOR-B3-I07R1)

`is_complete=True` means the adapter has evidence-backed grounds that the
requested acquisition unit is complete — it does NOT mean merely that transport
succeeded or that a page had few rows.  For HISTORICAL funding/trade fetches
this checkpoint NEVER certifies completeness: the single returned page is
returned with `is_complete=False`, no `next_resume_token`, and a truthful
`PARTIAL_INTERVAL` (rows overlap the requested window) or `GAP_DETECTED` (rows
entirely outside it) quality flag.  Requested `start_time`/`end_time` are
preserved separately from the actual returned timestamps.  **Arbitrary-range
historical replay is therefore NOT fully satisfiable yet** — an old requested
window cannot be honored as a complete replay while continuation direction is
unresolved.  The CURRENT_ONLY book snapshot is complete per acquisition unit
(it makes no window promise).

## Known Issues

- Funding/trade multi-window cursor continuation is UNRESOLVED (evidence does
  not pin `after`/`before` direction) — constrained to a single window; a
  historical fetch is never certified complete (I07R1 window-truth invariant).
- Arbitrary historical-window replay is LIMITED until continuation semantics
  are evidenced (I14 network smoke is the natural characterization point).
- `markPrice` on funding rows is an OPTIONAL/UNVERIFIED additive field (probe
  fixture only; not in the committed schema fingerprint) — preserved when
  present, never required.
- No live network validation occurred in I07/I07R1 (network smoke is reserved
  for SENSOR-B3-I14).

## Fixtures

Offline, from committed evidence. Marked `SYNTHETIC_SCHEMA_FIXTURE` where
synthetically reconstructed from the committed schema fingerprints
(`09_SCHEMA_FINGERPRINTS.jsonl` + `live_probe_contracts.yaml` + probe fixture
shapes). Per promoted sensor: happy / EMPTY_VALID / additive / malformed
timestamp / missing field / provider error / rate limit.

## Examples

```python
from crypto_sensor_fabric.providers.okx import OkxAdapter
from tests...providers.okx._fake import request, FakeOkxTransport

adapter = OkxAdapter(transport=FakeOkxTransport(routes={"/history-trades": (200, FX.TRADE_HAPPY)}))
batch = adapter.fetch_trades(request(TRADE))   # FetchBatch, native fields preserved
```

## Non-Goals

- No historical book surface, no book replay, no REST_RANGE for the
  CURRENT_ONLY book.
- No funding annualization / sign-flip / carry / normalization.
- No CVD / buy-sell pressure / order-flow state from trades.
- No liquidation/OI/positioning/basis/book-metric production paths under I07.
- No parity/reference-price logic ("premium/basis") — queued research.
- No cross-provider blending, no T1/T2 state, no research signals, no Bloc 4+.