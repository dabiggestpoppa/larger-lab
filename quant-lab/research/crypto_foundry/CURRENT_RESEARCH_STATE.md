# QUANT BOX — Crypto Quant Foundry Current Research State

**Checkpoint:** `CRYPTO-DATA-0.1-TRUTH-REPAIR-AND-DATA1-PREREGISTRATION`
**Branch:** `agent/crypto-quant-foundry`
**Decision:** `PASS_TRUTH_REPAIRED_DATA1_PREREGISTERED`
**Strategy research:** NOT STARTED
**Execution:** NOT AUTHORIZED

## Completed Checkpoints

### CRYPTO-0-PLANNING-ANCHOR ✅
### CRYPTO-DATA-0-VENUE-AND-MARKET-REALITY-AUDIT ✅
### CRYPTO-DATA-0.1-TRUTH-REPAIR-AND-DATA1-PREREGISTRATION ✅

## Truth Repairs Applied (DATA-0.1)

1. **Hyperliquid US access** — Corrected from YES to RESTRICTED for execution. Data research = ACCEPT_PRIMARY.
2. **btc_5m_4yr.json provenance** — QUARANTINED. File pre-dates Hyperliquid by 11 months. Is relabeled Binance data. SHA256: 2f76a9ad...
3. **Drift status** — Reclassified to WATCH/RESEARCH_ONLY. Security status requires revalidation.
4. **Access taxonomy v2** — Explicit data vs execution fields in CRYPTO_ACCESS_REGISTRY_V2.csv.
5. **Source authority** — All operational claims now attributed in CRYPTO_SOURCE_AUTHORITY_REGISTRY.csv.

## Verified Local Data

| File | Source | Status | SHA256 |
|------|--------|--------|--------|
| btc_usdt_1460d.json | Binance | VERIFIED | e9c977e3... |
| eth_usdt_1460d.json | Binance | VERIFIED | 88fbaae3... |
| sol_usdt_1460d.json | Binance | VERIFIED | da79caa9... |
| btc_5m_4yr.json | Unknown | QUARANTINED | 2f76a9ad... |

## Nautilus Adapter Audit (Import Verified)

| Adapter | Status | Module |
|---------|--------|--------|
| Binance | IMPORTABLE | nautilus_trader.adapters.binance |
| Hyperliquid | IMPORTABLE | nautilus_trader.adapters.hyperliquid |
| Coinbase | IMPORTABLE | nautilus_trader.adapters.coinbase_intx |
| Bybit | IMPORTABLE | nautilus_trader.adapters.bybit |
| OKX | IMPORTABLE | nautilus_trader.adapters.okx |
| Deribit | NOT PRESENT | (DATA-0 was wrong) |
| dYdX | BLOCKED | Missing v4_proto |

## DATA-1 Preregistered Lanes

| Lane | Name | Primary Venue | Markets | Role |
|------|------|---------------|---------|------|
| A | PERP_STATE | Hyperliquid | BTC-PERP, ETH-PERP | State research (NO execution) |
| B | DEEP_HISTORICAL_SPOT | Binance | BTCUSDT, ETHUSDT | Historical reference (data only) |
| C | ETHEREUM_AMM | Uniswap v3 | WETH/USDC, WBTC/USDC | AMM event research |
| D | BASE_AMM | Aerodrome or Uniswap v3 | WETH/USDC, cbBTC/USDC | Low-cost AMM lab |

Options / LP: DATA-2_CANDIDATE (not in DATA-1 scope)

## Next Checkpoint

`CRYPTO-DATA-1-CANONICAL-COLLECTOR-FOUNDATION`

Scope:
1. Fetch fresh Hyperliquid BTC/ETH perp data (candles + funding + OI from May 2023)
2. Backfill Binance deeper history if needed beyond existing 4yr files
3. Build Uniswap v3 subgraph adapter for ETH/USDC on Ethereum
4. Select and verify Base AMM pool candidates
5. Store raw + normalized with provenance manifests
6. Run data quality gates
7. Cross-source parity check (Binance spot vs HL perp)
8. Produce test fixtures for Git
