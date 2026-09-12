# SENSOR-B3-I07 — OKX Swap Production Adapter Implementation Evidence

**Checkpoint verdict:** `HOLD_PASS_SENSOR_B3_I07_OKX_ADAPTER_OFFLINE_PENDING_I07R1`.
Kraken + Gate were frozen; this is the THIRD hard real provider adapter built on
the hardened common foundation.  **This is NOT a global Bloc 3 PASS.**

**I07R1 repair:** see `BLOC_03_I07R1_OKX_SEAL_EVIDENCE.md` — historical
funding/trade fetches are now never certified complete (window-truth
invariant), parser required-field sets were sealed to the closed schema
fingerprints, `seqId` uses exact int typing, book levels require at least
`[price, size]`, and the `markPrice` claim was reconciled (additive/unverified,
not evidence-backed).

**Operator authorization:** `SENSOR-B3-I07 — OKX_SWAP` only, granted by
`SENSOR-B3-I06-RATIFY` (which froze Gate offline implementation and repaired the
stale provider-authorization ledger text).  Deribit is NOT authorized yet.

## Identity

| Field | Value |
|---|---|
| adapter_id | `OKX_SWAP.PUBLIC_REST.V1` |
| adapter_version | `okx-adapter-v1` |
| provider | `OKX_SWAP` |
| package | `quant-lab/src/crypto_sensor_fabric/providers/okx/` |
| implementation head | `be075378` (I07A) + `699a2ede` (I07B+C) + (I07C) |
| network_smoke_status | `NOT_RUN` (reserved for SENSOR-B3-I14) |

## Supported sensor paths (exactly three, I14-promoted)

| Sensor | Role | Method pin | Verified history |
|---|---|---|---|
| MECHANICAL_BOOK_SNAPSHOT | CURRENT_ONLY | `okx_swap-book_snapshot` | 2026-08-30T13:55:11.250844Z..2026-08-30T13:55:11.250844Z |
| MECHANICAL_FUNDING | PRIMARY | `okx_swap-funding` | 2021-06-15Z..2026-08-23T14:55:10.584064Z |
| MECHANICAL_TRADE | PRIMARY | `okx_swap-trade` | 2021-06-15Z..2026-08-30T13:55:11.053007Z |

An exact-set test derives the declared production set directly from
`source_promotion_candidates.yaml`; it equals the three OKX promotion-candidate
rows (no omission, no fourth path).

## Unsupported sensor paths (typed `CapabilityUnavailable`)

- MECHANICAL_BASIS, MECHANICAL_BOOK_METRIC, MECHANICAL_LIQUIDATION,
  MECHANICAL_OPEN_INTEREST, MECHANICAL_POSITIONING — NOT promoted by CURRENT I14.

These stay typed unsupported through the correct protocol methods; never
`[]` / `0` / `None` / `EMPTY_VALID`.  Queued OKX premium/basis and deeper
historical-book research MUST NOT broaden I07.

## Production symbol scope

Evidence-derived (`evidence/bloc_02/08_HISTORY_BOUNDARIES.csv`, provider x
sensor x instrument): `BTC-USDT-SWAP` for all three promoted paths.  Derived via
`ProviderNativeCapabilityEvidence.instruments`; probe/control instruments
`ETH-USDT-SWAP` / `SOL-USDT-SWAP` / `DOGE-USDT-SWAP` remain in
`OKX_PROBE_INSTRUMENT_SCOPE` for characterization history only and fail
production requests with typed `InvalidInstrument` before transport.

## Native acquisition mode per promoted path (evidence-backed, I05 seam)

| Sensor | historical_mode | pagination_mode | endpoint family |
|---|---|---|---|
| MECHANICAL_BOOK_SNAPSHOT | None (CURRENT_ONLY) | — | `okx-swap-market-books` |
| MECHANICAL_FUNDING | REST_CURSOR | CURSOR | `okx-swap-funding-rate-history` |
| MECHANICAL_TRADE | REST_CURSOR | CURSOR | `okx-swap-history-trades` |

- FUNDING: `GET /api/v5/public/funding-rate-history` (PUBLIC namespace, NEVER
  `/market`), `instId` + `limit`; after/before keyed around `fundingTime`
  (epoch ms) — NOT trade ids; no invented interval query parameter.
- TRADE: `GET /api/v5/market/history-trades`, `instId` + `limit`; after/before
  keyed around provider native trade ids (cursor meanings SEPARATE from funding).
- BOOK_SNAPSHOT: `GET /api/v5/market/books`, `instId` + `sz=400`; CURRENT
  snapshot only, no `start`/`end`/`after`/`before`, no historical depth.

The BOOK_SNAPSHOT capability carries NO native historical grant: its
`historical_mode` stays `None` — a CURRENT_ONLY surface can never be given a
historical/rest acquisition mode.

Each funding/trade grant's `evidence_ids` resolve into its own I14
`evidence_basis`; native evidence only REFINES acquisition mechanics, never
broadens scope/role/PIT/methodology/access/live/archive/sensor-set.

## Request timestamp units

Funding/trade/book request surfaces use no time-range query parameter (they are
cursor / snapshot surfaces): instId + limit / instId + sz.  NO invented
`from`/`to`/`start`/`end`/`after`/`before` continuation value is sent.

## Response timestamp units (ms-epoch STRINGS)

- FUNDING row `fundingTime` = native epoch MILLISECONDS as a **string**.
- TRADE row `ts` = native epoch MILLISECONDS as a **string**.
- BOOK row `ts` = native epoch MILLISECONDS as a **string**.

Convenience `FetchBatch` datetimes derive ONLY after strict validation of the
native ms-epoch string; the parsed native string is never replaced.  A dedicated
test set fails closed on string/float/bool/None timestamps (no silent coercion
to int).

## I14 evidence refs (evidence_basis per sensor)

- BOOK_SNAPSHOT: `okx_swap_book_snapshot_btc-usdt-swap_RECENT_CONTROL_book_snapshot`
- FUNDING: `okx_swap_funding_btc-usdt-swap_RECENT_CONTROL_1h` /
  `...2021_1h` / `...2022_1h` / `...2024_1h` / `...2026_1h`
- TRADE: `okx_swap_trade_btc-usdt-swap_RECENT_CONTROL_raw_event` /
  `...2021_raw_event` / `...2022_raw_event` / `...2024_raw_event` /
  `...2026_raw_event`

## Bloc 2 evidence refs (schema fingerprints, 09_SCHEMA_FINGERPRINTS.jsonl)

- FUNDING: envelope `dict{code:str,data:[{formulaType,fundingRate,fundingTime,
  instId,instType,method,realizedRate}],msg}` — fundingTime str (ms).
- TRADE: envelope `dict{code:str,data:[{instId,px,side,source,sz,tradeId,ts}],
  msg}` — ts str (ms); side aggressor.
- BOOK: envelope `dict{code:str,data:[{asks:list[list[str]],bids:list[list[str]],
  seqId:int,ts:str}],msg}`.

## Schema contracts / parser fields preserved by sensor (I07R1-sealed)

- FUNDING: closed SEVEN-field record — `fundingTime`, `fundingRate`,
  `realizedRate`, `formulaType`, `instId`, `instType`, `method` are all
  structurally required per the 09 fingerprint.  `markPrice` is NOT in the
  committed runtime fingerprint (probe fixture only): it is an
  OPTIONAL/UNVERIFIED additive field — preserved when present (ADDITIVE),
  never required.  fundingRate vs realizedRate stay distinguishable; interval
  NOT frozen to 8h.
- TRADE: closed SEVEN-field record — `instId`, `tradeId`, `px`, `sz`, `side`,
  `ts`, `source` all structurally required.  `side` is the provider-native
  aggressor side preserved verbatim (never reinterpreted into strategy
  direction; no CVD / buy-sell pressure / order-flow state).
- BOOK: closed FOUR-field record — `ts`, `bids`, `asks` (list-of-list
  `[px, sz, ...]`, at minimum `[price, size]`), `seqId` (EXACT int; bool
  rejected).  No imbalance / slippage / spread / depth score / book health is
  derived.

Structural fail-closed: missing required field / wrong timestamp type /
bad level shape / malformed seqId => BREAKING/UNKNOWN (raw preserved, parsed
blocked); extra field => ADDITIVE (flagged, parsed); missing required fields
never default to zero.

## OKX v5 error model

Envelope `{code, msg, data}`: success is `code == "0"`.  A NONZERO provider
code is a provider failure even on HTTP 200 — it is NEVER EMPTY_VALID.
Evidence-grounded code classes (probe.CODE_FAILURE, refined by committed
runtime evidence): 50011/50012/50110/50111 -> `RateLimited`; 51001
("Instrument ID does not exist") -> `InvalidInstrument`; 50113 ("Please login")
-> `AuthenticationRequired`; any other nonzero code -> `ProviderSemanticError`.
HTTP band: 429 -> rate-limit; 403 -> `AccessClassViolation`; 5xx -> \
`ProviderUnavailable`; other 4xx -> `ProviderSemanticError`.

## Forbidden raw paths proved absent

- Funding is NEVER composed as `/api/v5/market/funding-rate-history` (test
  asserts the PUBLIC namespace).
- The book request contains no `start`/`end`/`after`/`before` (test asserts no
  historical cursor can be produced).

## Archive boundary

The public traderecords daily-zip archive remains Bloc 2 characterization code
(`probe.py`); it is NOT substituted as a production REST path and does NOT
extend the frozen I14 verified-history boundary (I14 access_path = PUBLIC_REST).

## Offline fixture inventory (`tests/.../okx/fixtures/responses.py`)

All `SYNTHETIC_SCHEMA_FIXTURE` reconstructed from committed fingerprints +
live_probe_contracts.yaml + probe fixture shapes, per promoted sensor: happy,
empty-valid, additive, malformed timestamp (string/float/bool/None), missing
required field, bad level shape, schema drift, invalid instrument, rate limit,
provider error.  No network calls to obtain fixtures.

## Common conformance result — `PRODUCTION_CANDIDATE` mode

Run with the REAL `OkxAdapter` + fake transport.  `summarize_conformance`
reports **0 failed**, covering provider identity, registry/free-only, I14 exact
capability set, promotion bounds, resolving evidence refs, native-mode evidence,
symbol-scope evidence, behavioral dispatch, empty-valid vs unsupported, raw
preservation, schema-drift fail-closed, retry classification, native-instrument
requirement, and resume determinism (single-window).

## Provider-specific tests

- provider_id frozen `OKX_SWAP`; exactly three promoted paths; exact I14 set
- roles: book CURRENT_ONLY; funding + trade PRIMARY
- five unpromoted sensors typed `CapabilityUnavailable`
- free-only gate before transport; trading auth blocked before transport
- foreign provider request blocked before transport (requested sensor preserved)
- production/probe symbol separation; BTC-USDT-SWAP passes; ETH/SOL/DOGE fail typed
- trade/funding/book request contracts (paths, params, no forbidden cursors)
- method/sensor identity guards incl. unsupported named methods
- ms-epoch STRING timestamp schema (string ok; float/bool/None/int fail closed)
- fundingRate vs realizedRate distinct; native trade side preserved; no canonical fields
- raw envelope hash deterministic; SchemaDrift carries envelope per sensor
- empty-valid distinct from unsupported / provider error; nonzero code != EMPTY_VALID
- full PRODUCTION_CANDIDATE conformance via real adapter

## Free-only result

Pass — public REST, NO_AUTH, $0; DEFAULT_FREE_ONLY_POLICY (FREE_AUTOMATED, cost
0, no payment/staking/transaction).  OkxAdapter never touches credentials.

## Error mapping

`{code, msg}` + HTTP status -> typed errors (see **OKX v5 error model** above).
Retry classification: rate-limit / provider-unavailable retryable; instrument /
auth / access / schema terminal (asserted via `classify_retryability`).

## Pagination / resume status (I07R1 window-truth correction)

Trade and funding are REST_CURSOR surfaces with sensor-specific `after`/`before`
cursor meanings, but their continuation **direction is UNRESOLVED by committed
I13 evidence** — production issues a single evidence-backed request window
(`instId` + `limit`) and does NOT invent a continuation cursor.  Because the
returned page can never be proven to satisfy an arbitrary requested
`[start_time, end_time)` window, a HISTORICAL funding/trade fetch is NEVER
certified complete: `is_complete=False`, `next_resume_token=None`, and a
truthful `PARTIAL_INTERVAL` / `GAP_DETECTED` quality flag (see
`BLOC_03_I07R1_OKX_SEAL_EVIDENCE.md`).  Requested vs actual boundaries stay
separate.  The CURRENT_ONLY book is complete per snapshot unit and has no
pagination.  Resume-token determinism (round-trip) itself still passes via the
common suite.

## Known limitations

1. Funding/trade multi-window after/before continuation direction UNRESOLVED
   from committed evidence (single-request window enforced).
2. No live network validation in I07 (fake transport only).
3. OKX funding interval is NOT frozen to "8h" — frequency may differ by
   instrument/regime/methodology; no interval query parameter is sent.
4. The public traderecords archive is not a production REST substitute.

## Promotion / readiness status

Three promoted OKX paths: `ADAPTER_READY` (offline evidence earned; readiness
matrix updated).  Unpromoted OKX sensors = `NOT_PLANNED`.  No global Bloc 3 PASS.

## No capability exceeded I14

The native-evidence/conformance gate binds sensor set, role, history scope,
verified range, PIT, methodology, access, live/archive status, and production
symbol scope to `source_promotion_candidates.yaml`.  Nothing broadens it —
including the queued premium/basis and historical-book research.

## No network validation

SENSOR-B3-I07 made ZERO network calls (fake transport only).  Network smoke
remains reserved for SENSOR-B3-I14.

## Commit SHA

- SENSOR-B3-I06-RATIFY: `8b3792d3` (governance — froze Gate, authorized OKX)
- SENSOR-B3-I07A: `be075378` (capability + native acquisition contract)
- SENSOR-B3-I07B+C: `699a2ede` (requests, errors, parsers, adapter, fixtures)
- SENSOR-B3-I07C: (this commit — README / evidence / readiness / ledger)