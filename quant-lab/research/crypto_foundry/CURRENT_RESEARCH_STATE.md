# QUANT BOX — Crypto Quant Foundry Current Research State

**Checkpoint:** `CRYPTO-DATA-1.3-CANONICAL-FREEZE-AND-EVIDENCE-RECONCILIATION`
**Branch:** `agent/crypto-quant-foundry`
**Decision:** `PASS_CANONICAL_CRYPTO_DATA_FOUNDATION` (DATA-1 frozen)
**Strategy research:** NOT STARTED
**Execution:** NOT AUTHORIZED

## Completed Checkpoints

### CRYPTO-0-PLANNING-ANCHOR ✅
### CRYPTO-DATA-0-VENUE-AND-MARKET-REALITY-AUDIT ✅
### CRYPTO-DATA-0.1-TRUTH-REPAIR-AND-DATA1-PREREGISTRATION ✅
### CRYPTO-DATA-1-CANONICAL-COLLECTOR-FOUNDATION ✅ (PARTIAL as delivered; full closure in 1.2/1.3)
### CRYPTO-DATA-1.1-BLOCKED-LANES-AND-TRUTH-CLOSURE ✅ (PARTIAL)
### CRYPTO-DATA-1.2-FINAL-DATA-TRUTH-CLOSURE ✅ (PARTIAL — corrected)
### **CRYPTO-DATA-1.3-CANONICAL-FREEZE-AND-EVIDENCE-RECONCILIATION ✅ (PASS — DATA-1 FROZEN)**

## DATA-1 Freeze Summary (1.3)

All canonical datasets have persisted raw evidence, nonzero manifests with
sha256, and consistent quality status:

| dataset | rows | status |
|---|---|---|
| bn_btcusdt_spot_5m / bn_ethusdt_spot_5m | 420,464 each | VALID |
| hl_btc/eth_perp_state_5m | 5,041 / 5,040 | VALID |
| hl_btc/eth_funding_hourly | 28,175 each | VALID |
| eth_weth_usdc_swap | 1,057 | VALID |
| eth_wbtc_usdc_swap | 205 | VALID |
| base_weth_usdc_swap | 4,035 | VALID |
| cbBTC/Base | — | DEMOTED_NO_SUITABLE_CANONICAL_POOL |

Parity (Binance spot 1H vs Hyperliquid 1H, persisted): BTC 3,400 overlap,
median -4.78 bps, corr 0.999998; ETH 3,400 overlap, median -4.70 bps,
corr 0.999999.

Freeze evidence object: `data_1/CRYPTO_DATA_FOUNDATION_FREEZE.json`.
MECH-1 must consume only datasets listed there.

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
