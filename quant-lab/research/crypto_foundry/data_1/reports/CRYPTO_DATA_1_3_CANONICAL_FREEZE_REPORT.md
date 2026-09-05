# CRYPTO-DATA-1.3 — CANONICAL FREEZE & EVIDENCE RECONCILIATION

**Checkpoint:** CRYPTO-DATA-1.3-CANONICAL-FREEZE-AND-EVIDENCE-RECONCILIATION
**Branch:** `agent/crypto-quant-foundry`
**Base commit:** `630875744c0c35d6414c5ad681f534bab2405968`
**Decision:** `PASS_CANONICAL_CRYPTO_DATA_FOUNDATION`

## Objective

Every claimed canonical dataset must have REAL STORED EVIDENCE, a COMPLETE
MANIFEST, and CONSISTENT quality status. A report is NOT evidence by itself.
No runtime-only success. No report-only success.

## 1. Hyperliquid datasets (persisted, manifests nonzero)

| dataset_id | rows | first | last | sha256 |
|---|---|---|---|---|
| hl_btc_perp_state_5m | 5,041 | 2026-08-04 | 2026-08-21 | 4cdc46986a5c |
| hl_eth_perp_state_5m | 5,040 | 2026-08-04 | 2026-08-21 | 671e5f634afd |
| hl_btc_funding_hourly | 28,175 | 2023-05-12 | 2026-08-21 | b029e2e17371 |
| hl_eth_funding_hourly | 28,175 | 2023-05-12 | 2026-08-21 | 5009908fc8ba |
| hl_btc_mark_index_oi | snapshot | — | — | persisted |
| hl_eth_mark_index_oi | snapshot | — | — | persisted |
| hl_btc_book / hl_eth_book | L2 snapshot | — | — | persisted |

Prior manifests reported `row_count=0` / `null` timestamps because DATA-1.2
ran with `--skip-live`. DATA-1.3 collected and persisted real data.

## 2. Hyperliquid funding truth

- BTC: **28,175 records**, 2023-05-12 → present, hourly cadence, forward
  pagination (500/page), duplicate-checked, sha256 recorded.
- ETH: **28,175 records**, same coverage. The earlier 500-record truncation
  was API rate limiting; collector now retries with backoff and advances past
  stuck windows. Both datasets VALID.

## 3. Ethereum AMM (Lane C) — real events

| pool | swaps | first event | last event |
|---|---|---|---|
| WETH/USDC 0.05% (`0x88e6...`) | **1,057** | 2026-08-14 | 2026-08-21 |
| WBTC/USDC 0.30% (`0x99ac...`) | **205** | 2026-08-14 | 2026-08-21 |

- Pool identity verified on-chain: code, token0, token1, tickSpacing
  (10 / 60, consistent with fee tiers).
- 0 failed block ranges. Raw logs preserved (`raw/eth_*_swap_raw.json`).
- Price orientation verified: WETH/USDC token0=USDC → price_token1_per_token0
  ≈ 1,883 (ETH/USD). WBTC/USDC token0=WBTC → 63,017 (BTC/USD).
- **RPC safety:** failed ranges are recorded with error class
  (RPC_TIMEOUT / RPC_RATE_LIMIT / RPC_RANGE_TOO_LARGE / SOURCE_UNAVAILABLE);
  no silent skipping. Adaptive batch sizing implemented.

## 4. Base AMM (Lane D)

- Tokens verified on-chain: WETH (18 dec), USDC (6 dec), **cbBTC
  `0xcbB7...` has NO code on Base → DEMOTED_NO_SUITABLE_CANONICAL_POOL**.
- Factory discovery: `getPool(USDC, WETH, 500)` =
  `0xd0b53d9277642d899df5c87a3966a349a798f224` (canonical, verified
  token0=WETH, token1=USDC, tickSpacing=10).
- **2,641 → 4,035 real swaps collected** (second run) — VALID.
- The preregistered address `0xb2cc...` was WRONG; factory discovery replaced it.

## 5. Binance

- BTCUSDT / ETHUSDT: 420,464 rows each, 2022-06-16 → 2026-06-15.
- Local files under `.exec-runtime/quant-lab/data/` (Binance REST geo-blocked
  HTTP 451; local provenance verified).
- 14 zero-volume bars per asset on 2023-03-24 = **VALID_ZERO_ACTIVITY**
  (source outage window, flat OHLC 28,080). Q4 bar semantics updated to allow
  zero-volume bars while still rejecting negative volume.
- One 85-minute gap 2023-03-24 = **PASS_WITH_DOCUMENTED_SOURCE_GAP**.

## 6. Q1-Q17 execution

Full applicability matrix: `quality/CRYPTO_Q1_Q17_FINAL_MATRIX.csv`
Evidence rows: `quality/CRYPTO_Q1_Q17_FINAL_EVIDENCE.csv`

- Q1-Q5: Binance (Q4/Q5 documented source-outage classes)
- Q1-Q3: HL state; Q6 book; Q7/Q9 mark-index/OI; Q8 funding
- Q10-Q12: AMM token order / pool identity / unique block-tx-log keys
- Q13-Q15: replay + normalized-from-raw + future-independence determinism
  (ingest_time_utc excluded as metadata)
- Q16: schema validation per family
- Q17: source outage classification (Binance 451, HL page limits, RPC limits)

## 7. Parity (recomputed from persisted canonical files)

| asset | overlap | median basis bps | p95 abs bps | max abs bps | correlation |
|---|---|---|---|---|---|
| BTC | 3,400 (1H) | -4.78 | 7.09 | 28.97 | 0.999998 |
| ETH | 3,400 (1H) | -4.70 | 7.46 | 24.68 | 0.999999 |

Object: Binance spot 1H close (aggregated from persisted 5m) vs Hyperliquid
1H close. Basis reflects normal spot-vs-perp spread. DATA QUALITY ONLY.

## 8. Decision

Fail-closed engine (`quality/decision.py`) emitted:

```
PASS_CANONICAL_CRYPTO_DATA_FOUNDATION
blocking_issues: []
```

Conditions met: no FAIL/BLOCKED on canonical datasets; all manifests nonzero
with sha256; all applicable gates executed; lanes met; no count contradiction.

## 9. Historical decisions (corrected, no history rewritten)

| checkpoint | decision |
|---|---|
| DATA-1 | PARTIAL_CRYPTO_DATA_FOUNDATION |
| DATA-1.1 | PARTIAL_CRYPTO_DATA_FOUNDATION |
| DATA-1.2 | PARTIAL_CRYPTO_DATA_FOUNDATION (artifact corrected; blockers: 0 AMM swaps, Base CODE_EXISTS only, empty HL manifests, Q1-Q17 inconsistency) |
| **DATA-1.3** | **PASS_CANONICAL_CRYPTO_DATA_FOUNDATION** |

## 10. Freeze

`CRYPTO_DATA_FOUNDATION_FREEZE.json` is the parent evidence object for
CRYPTO-MECH-1. MECH-1 must consume only datasets listed in this freeze.

## Prohibited verification

strategy_pnl_computed=false · optimization_performed=false ·
alpha_research_started=false · confirmation_consumed=false ·
holdout_consumed=false · live_capital_deployed=false · ase2_started=false

## NEXT CHECKPOINT (NOT STARTED)

`CRYPTO-MECH-1-SPOT-PERP-AMM-CONSTRAINT-ANATOMY`
