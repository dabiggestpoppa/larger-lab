# BLOC 03 — SENSOR-B3-I08 DERIBIT IMPLEMENTATION EVIDENCE

Status: **SENSOR-B3-I08 COMPLETE (OFFLINE)** — proposed verdict
`PASS_SENSOR_B3_I08_DERIBIT_ADAPTER_OFFLINE` (NOT `PASS_BLOC_03`).

## 1. Lineage

| Item | Value |
|---|---|
| Starting SHA | `9960b65109123fbe4532394aec071a2ed380fbfb` (branch `agent/crypto-sensor-fabric-build`) |
| Governance | `c8164313` — SENSOR-B3-I07R2-RATIFY (operator freezes OKX, authorizes Deribit) |
| I08A | `f6acec7e` — freeze Deribit I14 capability + native acquisition contract |
| I08B+C | `82e23c52` — Deribit requests/errors/adapter/parsers/fixtures + tests |
| Final SHA | (see ledger / `git log`) |
| Verdict | `PASS_SENSOR_B3_I08_DERIBIT_ADAPTER_OFFLINE` (proposed) |

## 2. Exact I14 production set (4)

- MECHANICAL_BOOK_SNAPSHOT — CURRENT_ONLY
- MECHANICAL_FUNDING — SECONDARY (HISTORICAL)
- MECHANICAL_LIQUIDATION — MECHANISM_MICROSCOPE (HISTORICAL)
- MECHANICAL_TRADE — MECHANISM_MICROSCOPE (HISTORICAL)

Exact-set equality derives from `source_promotion_candidates.yaml`
(`capabilities_from_promotion`): declared set == I14 Deribit set == exactly
these four.  No fifth sensor.

Unsupported under CURRENT I14 (typed `CapabilityUnavailable`):
MECHANICAL_BASIS, MECHANICAL_BOOK_METRIC, MECHANICAL_OPEN_INTEREST,
MECHANICAL_POSITIONING.

## 3. Production symbol scope

Evidence-derived from `08_HISTORY_BOUNDARIES.csv` (provider × sensor ×
instrument rows): **BTC-PERPETUAL** for all four paths (grant
`ProviderNativeCapabilityEvidence.instruments`).  Probe universe
(`probe.NATIVE_INSTRUMENTS`: BTC/ETH/SOL-PERPETUAL) is characterization scope
only; ETH/SOL are NOT production grants and fail production requests with
typed `InvalidInstrument` BEFORE transport.  MID_TAIL_CONTROL is not mapped.

## 4. Roles / PIT / methodology

| Sensor | Role | PIT | Methodology pin |
|---|---|---|---|
| BOOK_SNAPSHOT | CURRENT_ONLY | PIT_READY_WITH_METHOD_VERSION | deribit-book_snapshot |
| FUNDING | SECONDARY | PIT_READY_WITH_METHOD_VERSION | deribit-funding |
| LIQUIDATION | MECHANISM_MICROSCOPE | PIT_READY_WITH_METHOD_VERSION | deribit-trade-level-liquidation-anatomy |
| TRADE | MECHANISM_MICROSCOPE | PIT_READY_WITH_METHOD_VERSION | deribit-trade-level-liquidation-anatomy |

No role is upgraded; MECHANISM_MICROSCOPE stays a mechanism microscope and is
never interval aggregate truth (common `promotion_bound_violations` #19).

## 5. Verified history (I14 literal)

- BOOK_SNAPSHOT: `2026-08-30T13:55:12.240279Z..same`
- FUNDING: `2021-06-15Z..2026-08-23T14:55:12.048205Z`
- LIQUIDATION: `2026-08-23T14:55:11.833559Z..same`
- TRADE: `2026-08-30T13:55:11.474770Z..same`

The LIQUIDATION/TRADE evidence_basis contains older probe ids
(`deribit_liquidation_btc-perpetual_2022_1h`,
`deribit_trade_btc-perpetual_2021_raw_event`, ...), but the I14 VERIFIED
HISTORY BOUND is literal.  Historical request capability != verified deep
coverage; the adapter never claims deeper verified history.

## 6. Endpoints / request contract (frozen from live_probe_contracts.yaml +
probe.py, runtime fingerprints)

| Sensor | Endpoint | Params |
|---|---|---|
| TRADE | GET `/api/v2/public/get_last_trades_by_instrument` | `instrument_name`, `start_timestamp` (epoch ms), `end_timestamp` (epoch ms), `count` (<=1000), `include_old=true` |
| LIQUIDATION | GET `/api/v2/public/get_last_trades_by_instrument` | same physical surface |
| FUNDING | GET `/api/v2/public/get_funding_rate_history` | `instrument_name`, `start_timestamp`, `end_timestamp` (epoch ms), `count` (<=1000) |
| BOOK | GET `/api/v2/public/get_order_book` | `instrument_name`, `depth=25` (current-only) |

Native acquisition mode (grant): HISTORICAL sensors = `REST_RANGE` /
`TIME_RANGE`; BOOK = CURRENT_ONLY, no historical grant
(`historical_mode=None`).

## 7. Timestamp contract

Request `start_timestamp`/`end_timestamp` and response `timestamp`
(trade/liquidation/funding rows, book result) are provider-native epoch
MILLISECOND INTEGERS.  Strict `type(v) is int` (bool rejected).  `True` /
`False` / float / string / `None` / mixed → BREAKING → `SchemaDrift` with the
exact `RawPayloadEnvelope` preserved; no silent coercion.  Convenience UTC
datetimes are derived ONLY after native validation.

## 8. Response envelope semantics

JSON-RPC v2 style.  `result`:

- TRADE/LIQUIDATION: dict `{has_more: bool, trades: [rows]}` (has_more is
  structurally required; missing/non-bool → BREAKING).
- FUNDING: **raw list** (observed LIVE; `{data:[...]}` is BREAKING, never
  repaired).
- BOOK: dict with `bids`/`asks` levels `list[list[float]]` (min `[price,
  amount]`, numeric family, bool rejected).

Provider error may ride HTTP 200 inside `{"error": {"code": <int>, ...}}`.
HTTP 200 does NOT imply success; a JSON-RPC error is never
`EMPTY_VALID`/`[]`/`0`/`None`.

## 9. Error mapping (probe.CODE_FAILURE, no committed runtime refinement)

- `40400` → InvalidInstrument
- `10001` → RateLimited
- `10000` / `10002` → AuthenticationRequired
- `-32601` / `-32602` → ProviderSemanticError
- unknown JSON-RPC error → ProviderSemanticError
- HTTP 429 / 403 / 5xx → RateLimited / AccessClassViolation /
  ProviderUnavailable

## 10. Trade schema (native fields preserved)

Closed THIRTEEN-field runtime record (09 fingerprint RECENT_CONTROL): `amount,
contracts, direction, index_price, instrument_name, mark_price, price,
starbase_match_id, starbase_timestamp, tick_direction, timestamp, trade_id,
trade_seq` — every field structurally required.  `direction` is the
provider-native taker/aggressor side preserved verbatim (never reinterpreted).
`liquidation` flag (characterization-backed: `"liquidation" | "taker" |
"maker"`) is KNOWN-OPTIONAL, preserved when present.  Numeric semantic family
for price/amount fields (int|float, bool rejected); exact int for
timestamp/sequence/id fields.  No CVD / flow / pressure fields.

## 11. Liquidation sensor (mechanism microscope)

Same physical `get_last_trades_by_instrument` payload; the LIQUIDATION view
projects ONLY rows whose `liquidation == "liquidation"`.  Rows with
`"taker"`/`"maker"` or no flag are ordinary trades, excluded from the
liquidation view.  A page with zero forced-liquidation events yields
`row_count=0` / `EMPTY_VALID` while the FULL raw payload is preserved.  The
same payload as TRADE retains all rows.  Adversarial proof: mixed page →
liquidation batch row_count 1 vs trade batch row_count 3, identical raw
content hash, native flag values and direction preserved; no
`liquidation_usd`/`long_liq`/`short_liq`/`liq_pressure` fields anywhere.

Hard invariant: DERIBIT TRADE-LEVEL LIQUIDATIONS != interval liquidation
totals.  Nothing is summed, bucketed, or converted; no liquidation-notional
derivation; no join with interval totals (T2-SEM-06).

## 12. Funding schema / envelope

`result` raw list of closed FIVE-field rows: `index_price, interest_1h,
interest_8h, prev_index_price, timestamp` (all required; timestamp strict
epoch-ms int).  `funding_rate` / `funding_1h` / `funding_8h` appear only in
the Bloc 2 probe/synthetic fixture (NOT the runtime fingerprint) and are
modeled as OPTIONAL/UNVERIFIED additive fields — present → ADDITIVE + preserved
under native names; absent → KNOWN (never required).  No annualization, no
carry/regime model.

## 13. Book schema

Structural core required: `timestamp` (strict epoch-ms int),
`instrument_name` (str), `bids` + `asks` (list of levels).  Every other
fingerprint-listed result field is KNOWN-OPTIONAL (validated when present:
numeric family for prices/amounts, exact int for `change_id`/`open_interest`,
str `state`, dict `stats`); unknown extra fields → ADDITIVE.  Levels are
`list[float]` with min `[price, amount]`; `[]`, one-element, bool, string
levels → BREAKING.  Values preserved as returned (no conversion).  No
imbalance/spread/depth/slippage derivation.

## 14. Completion semantics (window truth)

**CORRECTED by SENSOR-B3-I08R1** (see
`BLOC_03_I08R1_DERIBIT_COMPLETION_SEAL_EVIDENCE.md`):

- COMPLETE never carries `PARTIAL_INTERVAL` (flags are assigned AFTER the
  completion decision; PARTIAL/GAP mutually exclusive; empty page =
  `EMPTY_VALID` only).
- Coverage truth comes from the FULL schema-validated SOURCE page, never the
  filtered liquidation projection (a projection cannot manufacture
  completeness).
- FUNDING is never certified complete: the "short page under count cap 1000
  is exhaustive" rule is only a characterization heuristic, not a proven
  provider contract (`completion_proof = LIMITED`).
- TRADE/LIQUIDATION are complete only when semantic output is non-empty,
  every source-page row lies inside the requested `[start_time, end_time)`
  window, and `has_more == false`.

Superseded I08 wording: "...terminal condition holds (FUNDING: page under
count cap 1000; ...)" — the funding clause was demoted; the rest of the
window-truth doctrine (requested vs actual boundaries stay separate;
order-invariant overlap from ANY validated row timestamp; BOOK_SNAPSHOT
complete per snapshot unit) stands unchanged.

## 15. Pagination / resume

`has_more` flag is preserved and drives the terminal condition for a single
window, but continuation mechanics BEYOND the evidenced single request window
(window shifting for deep traversal) are NOT proven by committed I13 evidence.
Production never invents a `next_resume_token` (resume = LIMITED).  No
`next_offset`-style synthetic cursor is treated as production evidence.
Resume-token tests: wrong provider / wrong sensor / wrong instrument remain
covered by the common conformance suite (no token is ever produced).

## 16. Raw evidence boundary

Transport → JSON-RPC error check → provider-native schema assessment →
immutable `RawPayloadEnvelope` (provider_id, sensor_family,
request_fingerprint, raw body, content hash, retrieval metadata, schema state,
I14 evidence ref, adapter version) → semantic release decision.  Schema drift
raises typed `SchemaDrift` carrying the exact raw envelope; hash is
deterministic.  Raw payload is preserved even for zero-row liquidation /
EMPTY_VALID responses.

## 17. Guard rails (I05R1/I05R2/I07 pattern preserved)

- Foreign `FetchRequest.provider_id` → typed `ProviderSemanticError` carrying
  the ACTUAL requested sensor, zero transport calls (all four sensors tested).
- Named-method / sensor identity: `fetch_trades(FUNDING request)` →
  `ProviderSemanticError`; correctly invoked unpromoted methods →
  `CapabilityUnavailable`; mismatch is never a false "surface unsupported".
- No-transport → `ProviderUnavailable` naming the requested sensor.
- Free-only access gate runs BEFORE any transport call (TRADING_KEY → blocked,
  zero calls).
- Production symbol scope guard → `InvalidInstrument` before transport.
- `UnsupportedGranularity` for explicit non-native granularity before
  transport (trade/liq = RAW_EVENT, funding = 1h, book = BOOK_SNAPSHOT).

## 18. Fixtures

All offline fixtures are **SYNTHETIC_SCHEMA_FIXTURE** reconstructed from the
committed 09 fingerprints + live_probe_contracts.yaml + committed Bloc 2 probe
payloads.  Fixtures never establish capability/history/cursor/field
existence.  Matrix per sensor: happy, empty/EMPTY_VALID, additive, missing
required field, malformed/None/bool/float/string timestamp, wrong envelope,
provider error (JSON-RPC on HTTP 200 + HTTP bands).  Trade: has_more
true/false/missing/malformed, descending + mixed pages.  Liquidation: mixed
page, no-events, missing flag, union combo row, malformed flag.  Funding:
raw-list envelope vs `{data:[...]}` drift.  Book: level cardinality, minimal
core, empty levels, bool/string levels.

## 19. Conformance

Real `DeribitAdapter` + FAKE transport under `PRODUCTION_CANDIDATE`:
**0 failed**.  I14 exact-set equality, free-only policy, evidence resolution,
symbol scope, dispatch, empty-vs-unsupported, raw preservation, schema drift,
error typing, method identity all pass.  Common suite unchanged.

## 20. Test / validation results

- Deribit provider tests: **168 passed / 0 failed** (capability 20, requests
  14, errors 15, parsers 45, adapter 74).
- Full crypto_sensor_fabric suite: **1242 passed / 0 failed** (parent floor
  1074 → +168).
- Kraken + Gate + OKX regressions: green (frozen, unchanged).
- ruff: clean.  mypy: clean on the changed Deribit modules.
- Network calls: **0** (FAKE TRANSPORT ONLY; no-transport adapter raises
  typed `ProviderUnavailable`).

## 21. Zero-network / scope statements

- Zero network calls.  Network smoke reserved for SENSOR-B3-I14.
- No OKX/Kraken/Gate production-code changes (frozen providers untouched).
- No other provider (Deribit is the 4th real adapter).
- No Bloc 4 code.
- No `source_promotion_candidates.yaml` mutation.

## 22. Limitations (recorded, not hidden)

- Trade/liquidation/funding continuation beyond one evidence-backed request
  window: UNRESOLVED → LIMITED, no invented resume.
- Funding completion proof: LIMITED (short-page-under-cap rule lacks a proven
  provider contract; never certified complete).
- LIQUIDATION/TRADE verified history is a single I14 timestamp (literal); no
  deep-history claim despite older probe evidence ids.
- `funding_rate`/`funding_1h`/`funding_8h` unverified-additive.
- Network validation NOT_RUN.

## 23. Readiness (see ADAPTER_READINESS_MATRIX.csv)

| Provider / Sensor | Status | Notes |
|---|---|---|
| DERIBIT / BOOK_SNAPSHOT | ADAPTER_READY | CURRENT_ONLY |
| DERIBIT / FUNDING | ADAPTER_READY | SECONDARY; resume LIMITED |
| DERIBIT / LIQUIDATION | ADAPTER_READY | MECHANISM_MICROSCOPE; resume LIMITED |
| DERIBIT / TRADE | ADAPTER_READY | MECHANISM_MICROSCOPE; resume LIMITED |

network_validation: NOT_RUN.
