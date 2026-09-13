# BLOC 03 — SENSOR-B3-I10 CONTROLLED PRODUCTION-ADAPTER NETWORK SMOKE — EVIDENCE

**Checkpoint:** `SENSOR-B3-I10` — CONTROLLED PRODUCTION-ADAPTER NETWORK SMOKE
(the FIRST authorized live-network checkpoint).

**Overall verdict (proposed, per doctrine §43):**
`HOLD_SENSOR_B3_I10_SCHEMA_ADDITIVE_REVIEW`

**Ledger state (per doctrine §47):** `SENSOR-B3-I10 = EXECUTED_WITH_BLOCKER`
— NOT `COMPLETE`. `next_checkpoint_authorized = FALSE`.

---

## 1. Identity

| field | value |
|---|---|
| run_id | `i10-live` |
| checkpoint starting SHA | `1088bdb671abd2564426f5c3a01f609ca8f847f7` (mandated start) |
| ratification SHA | `e3da112161aae5248267c9242cdd100b3b7e962d` (SENSOR-B3-I09R1-RATIFY) |
| harness SHA | `f92d6bd9802ec8529af60779caa950f60fc3fce4` (SENSOR-B3-I10A) |
| run starting SHA (captured before request #1) | `f92d6bd9802ec8529af60779caa950f60fc3fce4` |
| run manifest hash | `2c2e791bfad10fb4` (SHA-256 prefix, frozen BEFORE any request) |
| UTC run anchor (run_timestamp_utc) | `2026-09-01T01:23:57.492186Z` |
| evidence SHA | `c4bc5c3e60eeae9e45c9dae334c1d4a80523f87a` (SENSOR-B3-I10B) |
| reconcile SHA | (this commit — SENSOR-B3-I10C) |
| branch | `agent/crypto-sensor-fabric-build` |

Artifacts:

- `BLOC_03_I10_NETWORK_SMOKE_PLAN.json` — frozen plan (18 requests), written to
  disk BEFORE request #1.
- `BLOC_03_I10_NETWORK_SMOKE_RESULTS.json` — all bounded outcomes, written
  BEFORE the final pass/fail assertion.
- this file — human-readable evidence.
- `SENSOR_FABRIC_IMPLEMENTATION_PROGRESS.md` — ledger (I10C).

## 2. Scope and doctrine compliance

- **Frozen production adapters only** — KRAKEN_FUTURES, GATE_FUTURES, OKX_SWAP,
  DERIBIT.  Real frozen adapters + `dispatch_fetch` were used; the free-only
  access gate ran before every transport call.  **Provider code modifications:
  NONE.**
- Targets derived from the canonical `PRODUCTION_ADAPTER_MATRIX.csv`
  (`production_symbol_scope`), never invented: **17 logical paths, 18 physical
  requests** (KRAKEN_FUTURES/MECHANICAL_OPEN_INTEREST carries both
  `PI_XBTUSD` and `PI_ETHUSD`).
- Request cap 20; **actual network calls = 18; retries = 0**; sequential,
  concurrency 1.
- Transport: HTTPS-only, host allowlist
  (`futures.kraken.com`, `api.gateio.ws`, `www.okx.com`, `www.deribit.com`),
  GET-only, cross-host redirects rejected, TLS verification ON, timeout ≤ 15 s,
  response cap 2 MiB, no cookies / persisted session / proxy credentials.
- Credentials: **secrets used = NONE**.  No API keys, no Authorization /
  Cookie / X-API-KEY / OK-ACCESS-KEY headers, no environment enumeration.
  `COINALYZE_API_KEY` was never read.  The only env opt-in was
  `SENSOR_NETWORK_SMOKE=1`.
- Paid endpoints = 0; trading endpoints = 0; private/account endpoints = 0.
- No list-instruments network call; no archive/CDN host; no Binance / Bybit /
  CoinAlyze / Bitfinex.
- Windows: small recent CLOSED windows relative to the run anchor (interval
  paths: `[anchor-26h, anchor-2h)`; raw trades: `[anchor-15m, anchor-5m)`;
  Deribit liquidation: `[anchor-65m, anchor-5m)`; book: nominal current-only
  window).  Page size hint 25 everywhere (cap ≤ 50).
- Every request used `FetchPurpose.PROBE`.  No backfill semantics claimed.
- A successful live observation does **NOT** expand I14
  `verified_history_start/end`, role, PIT, methodology pin, symbol scope or
  redundancy class.  The I09 offline matrix
  (`PRODUCTION_ADAPTER_MATRIX.csv/.json`) was **NOT touched** —
  `network_smoke_status` stays `NOT_RUN` there; this I10 artifact is the live
  validation overlay.

## 3. Frozen endpoint map (derived from the frozen request builders)

| provider | sensor family | endpoint family (host + path) |
|---|---|---|
| KRAKEN_FUTURES | MECHANICAL_BASIS | `https://futures.kraken.com/api/charts/v1/analytics/{symbol}/future-basis` |
| KRAKEN_FUTURES | MECHANICAL_BOOK_METRIC | `https://futures.kraken.com/api/charts/v1/analytics/{symbol}/orderbook` |
| KRAKEN_FUTURES | MECHANICAL_FUNDING | `https://futures.kraken.com/api/charts/v1/analytics/{symbol}/funding` |
| KRAKEN_FUTURES | MECHANICAL_LIQUIDATION | `https://futures.kraken.com/api/charts/v1/analytics/{symbol}/liquidation-volume` |
| KRAKEN_FUTURES | MECHANICAL_OPEN_INTEREST | `https://futures.kraken.com/api/charts/v1/analytics/{symbol}/open-interest` |
| KRAKEN_FUTURES | MECHANICAL_POSITIONING | `https://futures.kraken.com/api/charts/v1/analytics/{symbol}/long-short-ratio` |
| GATE_FUTURES | MECHANICAL_FUNDING | `https://api.gateio.ws/api/v4/futures/usdt/funding_rate` |
| GATE_FUTURES | MECHANICAL_LIQUIDATION / OPEN_INTEREST / POSITIONING | `https://api.gateio.ws/api/v4/futures/usdt/contract_stats` |
| OKX_SWAP | MECHANICAL_FUNDING | `https://www.okx.com/api/v5/public/funding-rate-history` |
| OKX_SWAP | MECHANICAL_TRADE | `https://www.okx.com/api/v5/market/history-trades` |
| OKX_SWAP | MECHANICAL_BOOK_SNAPSHOT | `https://www.okx.com/api/v5/market/books` |
| DERIBIT | MECHANICAL_TRADE / LIQUIDATION | `https://www.deribit.com/api/v2/public/get_last_trades_by_instrument` |
| DERIBIT | MECHANICAL_FUNDING | `https://www.deribit.com/api/v2/public/get_funding_rate_history` |
| DERIBIT | MECHANICAL_BOOK_SNAPSHOT | `https://www.deribit.com/api/v2/public/get_order_book` |

## 4. Per-request results (18/18, execution order retained)

| provider | sensor | symbol | HTTP | result class | rows | complete | quality flags | schema | raw content hash (SHA-256) | ms | bytes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| DERIBIT | MECHANICAL_BOOK_SNAPSHOT | BTC-PERPETUAL | 200 | LIVE_PASS_NONEMPTY | 1 | True | — | KNOWN_SCHEMA | `25ea4221…16da7` | 250 | 2476 |
| DERIBIT | MECHANICAL_FUNDING | BTC-PERPETUAL | 200 | LIVE_PASS_NONEMPTY | 24 | False | PARTIAL_INTERVAL | KNOWN_SCHEMA | `0157f60e…175d6` | 1217 | 3741 |
| DERIBIT | MECHANICAL_LIQUIDATION | BTC-PERPETUAL | 200 | LIVE_PASS_EMPTY_VALID | 0 | False | EMPTY_VALID | KNOWN_SCHEMA | `656333f0…7a406` | 219 | 8066 |
| DERIBIT | MECHANICAL_TRADE | BTC-PERPETUAL | 200 | LIVE_PASS_NONEMPTY | 25 | False | DUPLICATE_EDGE; PARTIAL_INTERVAL | KNOWN_SCHEMA | `d37d3cdf…2829b` | 187 | 8034 |
| GATE_FUTURES | MECHANICAL_FUNDING | BTC_USDT | 200 | LIVE_PASS_NONEMPTY | 3 | True | — | KNOWN_SCHEMA | `108af4a9…02c38` | 812 | 96 |
| GATE_FUTURES | MECHANICAL_LIQUIDATION | BTC_USDT | 200 | LIVE_PASS_NONEMPTY | 26 | True | — | KNOWN_SCHEMA | `0c13154f…6f42` | 891 | 17100 |
| GATE_FUTURES | MECHANICAL_OPEN_INTEREST | BTC_USDT | 200 | LIVE_PASS_NONEMPTY | 26 | True | — | KNOWN_SCHEMA | `0c13154f…6f42` | 905 | 17100 |
| GATE_FUTURES | MECHANICAL_POSITIONING | BTC_USDT | 200 | LIVE_PASS_NONEMPTY | 26 | True | — | KNOWN_SCHEMA | `0c13154f…6f42` | 891 | 17100 |
| KRAKEN_FUTURES | MECHANICAL_BASIS | PI_XBTUSD | 200 | LIVE_PASS_NONEMPTY | 24 | True | — | KNOWN_SCHEMA | `e1756356…9b79` | 265 | 564 |
| KRAKEN_FUTURES | MECHANICAL_BOOK_METRIC | PI_XBTUSD | 200 | LIVE_PASS_NONEMPTY | 24 | True | — | KNOWN_SCHEMA | `041c46cd…5efed` | 250 | 5701 |
| KRAKEN_FUTURES | MECHANICAL_FUNDING | PI_XBTUSD | 200 | **SCHEMA_ADDITIVE_REVIEW** | 24 | True | SCHEMA_ADDITIVE | ADDITIVE_SCHEMA_CHANGE | `48c2aae5…709f2` | 234 | 4956 |
| KRAKEN_FUTURES | MECHANICAL_LIQUIDATION | PI_XBTUSD | 200 | LIVE_PASS_NONEMPTY | 24 | True | — | KNOWN_SCHEMA | `63333abb…e7751` | 233 | 420 |
| KRAKEN_FUTURES | MECHANICAL_OPEN_INTEREST | PI_ETHUSD | 200 | LIVE_PASS_NONEMPTY | 24 | True | — | KNOWN_SCHEMA | `266e72bd…5e8c2a` | 266 | 1332 |
| KRAKEN_FUTURES | MECHANICAL_OPEN_INTEREST | PI_XBTUSD | 200 | LIVE_PASS_NONEMPTY | 24 | True | — | KNOWN_SCHEMA | `43aa1d7f…1f4a2` | 233 | 1332 |
| KRAKEN_FUTURES | MECHANICAL_POSITIONING | PI_XBTUSD | 200 | LIVE_PASS_NONEMPTY | 24 | True | — | KNOWN_SCHEMA | `82e22e14…1aa02` | 233 | 492 |
| OKX_SWAP | MECHANICAL_BOOK_SNAPSHOT | BTC-USDT-SWAP | 200 | LIVE_PASS_NONEMPTY | 1 | True | — | KNOWN_SCHEMA | `994cd017…1b5e55` | 328 | 21772 |
| OKX_SWAP | MECHANICAL_FUNDING | BTC-USDT-SWAP | 200 | LIVE_PASS_NONEMPTY | 25 | False | PARTIAL_INTERVAL | KNOWN_SCHEMA | `7916b71e…133aa` | 282 | 4813 |
| OKX_SWAP | MECHANICAL_TRADE | BTC-USDT-SWAP | 200 | LIVE_PASS_NONEMPTY | 25 | False | DUPLICATE_EDGE; GAP_DETECTED | KNOWN_SCHEMA | `9a233c0e…6e4e6` | 280 | 3137 |

Full 256-bit content hashes, request fingerprints, request start/end windows
and sanitized summaries: `BLOC_03_I10_NETWORK_SMOKE_RESULTS.json`.

## 5. Result-class tally

| class | count |
|---|---|
| LIVE_PASS_NONEMPTY | 16 |
| LIVE_PASS_EMPTY_VALID | 1 |
| SCHEMA_ADDITIVE_REVIEW | 1 |
| ACCESS_BLOCKED / GEO_BLOCKED / RATE_LIMITED / TRANSPORT_FAILURE / PROVIDER_ERROR / SCHEMA_BREAKING / UNEXPECTED_RESPONSE / INTERNAL_FAILURE | 0 / 0 / 0 / 0 / 0 / 0 / 0 / 0 |

`pass_result_count = 17`, `blocking_result_count = 1`.

## 6. Provider-level summary (logical paths passed / total)

| provider | logical paths | physical requests |
|---|---|---|
| KRAKEN_FUTURES | **5 / 6** | 6 / 7 |
| GATE_FUTURES | 4 / 4 | 4 / 4 |
| OKX_SWAP | 3 / 3 | 3 / 3 |
| DERIBIT | 4 / 4 | 4 / 4 |

Kraken's only non-pass is the additive-funding case below.  No provider score,
no weighting, no ranking.

## 7. Sensor-level coverage (operational reachability, NOT economic agreement)

| sensor family | logical paths live-pass | physical requests live-pass |
|---|---|---|
| MECHANICAL_BASIS | 1/1 | 1/1 |
| MECHANICAL_BOOK_METRIC | 1/1 | 1/1 |
| MECHANICAL_BOOK_SNAPSHOT | 2/2 | 2/2 |
| MECHANICAL_FUNDING | **3/4** | 3/4 |
| MECHANICAL_LIQUIDATION | 3/3 | 3/3 |
| MECHANICAL_OPEN_INTEREST | 2/2 | 3/3 |
| MECHANICAL_POSITIONING | 2/2 | 2/2 |
| MECHANICAL_TRADE | 2/2 | 2/2 |

## 8. The one blocking outcome — additive schema drift (HUMAN REVIEW REQUIRED)

**KRAKEN_FUTURES / MECHANICAL_FUNDING / PI_XBTUSD → `SCHEMA_ADDITIVE_REVIEW`**

- HTTP 200; response handled by the real frozen Kraken adapter; raw payload
  preserved in-memory in a `RawPayloadEnvelope` (content hash
  `48c2aae5…709f2`; body NOT committed per doctrine §27/§28).
- The frozen offline evidence pins the funding analytics `result.data` metric
  set as exactly `{rate, relativeRate}` (09_SCHEMA_FINGERPRINTS.jsonl
  `kraken_futures_funding_pi_xbtusd_RECENT_CONTROL_1h`; test fixture
  `_funding_happy`).  The live response's `result.data` dict contained **at
  least one additional metric key** beyond that set → the fail-closed schema
  classifier returned `ADDITIVE_SCHEMA_CHANGE`.
- The parser allowed parsed output (required semantics still valid):
  24 rows, `is_complete=True`, quality flag `SCHEMA_ADDITIVE`; no
  `SchemaDrift` was raised.
- **No automatic action was taken**: fingerprints, fixtures, parser required
  sets and the I09 matrix were NOT edited.  No provider code was modified.
- **Operator decision needed**: whether the new metric key is an expected
  provider addition (→ promote to the additive/known set under a repair
  checkpoint) or a genuine contract surprise (→ deeper review).  A targeted
  `SENSOR-B3-I10R1` repair/recheck (operator-authorized, separate run) should
  capture the exact added key name from the live raw body.

## 9. Truthful non-failures (recorded, not errors)

- **EMPTY_VALID (1):** DERIBIT/MECHANICAL_LIQUIDATION — the closed 60-minute
  window genuinely contained zero forced-liquidation events.  No row was
  manufactured; no rerun was forced.
- **Truthfully partial (frozen LIMITED continuation):**
  - OKX funding + trade: `is_complete=False` (single evidenced page; after/
    before continuation direction unresolved) — NOT a smoke failure (§16).
  - Gate: single tiny request only; deep traversal intentionally not
    attempted (§17).
  - Deribit funding/trade/liquidation: `is_complete=False` where continuation
    is LIMITED (§18); Deribit liquidation stays a TRADE-LEVEL MECHANISM
    MICROSCOPE — no aggregation, no cross-provider numeric comparison.
  - `DUPLICATE_EDGE` / `GAP_DETECTED` / `PARTIAL_INTERVAL` flags are
    acquisition truth, preserved and annotated, never destructive.

## 10. Safety / access / schema / transport results

- Access results: **no ACCESS_BLOCKED / GEO_BLOCKED / RATE_LIMITED** —
  all four public surfaces reachable from this region with the free-only gate
  passed before every request.
- Schema results: 17 KNOWN_SCHEMA, 1 ADDITIVE_SCHEMA_CHANGE, 0 BREAKING.
- Provider errors: none (all HTTP 200, no provider-native error envelopes).
- Transport errors: none (no timeout / TLS / DNS / cap violations).
- Redirects observed: none; cross-host redirect enforcement active.
- HTTPS/host safety: 18/18 requests HTTPS + allowlisted hosts.
- Credentials used: NONE.  Paid endpoints: 0.  Trading endpoints: 0.

## 11. Offline regression (pre-run and post-run)

| run | result |
|---|---|
| pre-network full suite (§39) | 1338 passed / 0 failed / 1 skipped |
| post-network full suite (§41) | 1338 passed / 0 failed / 1 skipped |
| ruff (project-wide) | clean |
| mypy (changed scope: network_smoke.py + both test files) | clean (0 errors; 10 pre-existing probe/rest errors unchanged) |

The 1 skip is `test_live_production_network_smoke` without the
`SENSOR_NETWORK_SMOKE=1` gate — proving a normal `pytest` never touches the
network.  Kraken / Gate / OKX / Deribit regressions and cross-provider matrix
tests are part of the full suite and stayed green.

## 12. Non-mutation statements

- I09 offline matrix (`PRODUCTION_ADAPTER_MATRIX.csv/.json`): **untouched**,
  `network_smoke_status = NOT_RUN` preserved (historical evidence).
- Frozen provider adapters: **no modifications**.
- Fingerprints / fixtures / parsers / promotion authority: **no modifications**.
- No Bloc 4 / MECH21 / LF14 / capital-field / alpha work.
- SENSOR-B3-I11 (final Bloc 3 validation) was **NOT started**.

## 13. Verdicts

- FULL I10 PASS: **NOT earned** (1 blocking-class outcome, §42).
- Proposed verdict: **`HOLD_SENSOR_B3_I10_SCHEMA_ADDITIVE_REVIEW`** (§43 —
  additive drift only; no geo/access/transport/provider-contract blocker).
- Ledger: `SENSOR-B3-I10 = EXECUTED_WITH_BLOCKER` (§47).
- `next_checkpoint_authorized = FALSE`.
- Recommended next: **targeted `SENSOR-B3-I10R1` repair/recheck** — operator
  review of the additive funding metric, capture the exact added key from the
  live raw body, then a controlled recheck.  No automatic repair was
  performed.
- The offline closure (I09 / I09R1 seals, all four adapters OFFLINE_FROZEN)
  remains valid — a live additive observation does not invalidate offline
  evidence (§44).

---
*Evidence packet generated by the SENSOR-B3-I10 network-smoke harness
(`providers/network_smoke.py`, commit f92d6bd9) and reconciled in commit
`c4bc5c3e` → I10C.  Secrets used: NONE.  Retries: 0.  Total network requests: 18.*
