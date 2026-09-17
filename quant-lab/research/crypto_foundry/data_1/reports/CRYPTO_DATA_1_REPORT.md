# CRYPTO-DATA-1: Canonical Collector Foundation Report

**Checkpoint:** CRYPTO-DATA-1-CANONICAL-COLLECTOR-FOUNDATION
**Base Commit:** 761ee00c2c41ca68998e3c7ad0e9d61c58c9d5cb
**Decision:** PASS_CANONICAL_CRYPTO_DATA_FOUNDATION
**Tests:** 39/39 passed

---

## Lane A: Hyperliquid Perp State

**Status: PASS**

Markets: BTC-PERP, ETH-PERP

### Data Collected (Live API)

| Object | BTC | ETH | Notes |
|--------|-----|-----|-------|
| Candles 5m (7d) | 2017 | 2017 | Full 7-day history |
| L2 Book | 20 levels | 20 levels | Live snapshot |
| Recent Trades | 10 | 10 | REST snapshot |
| Mark/Index/OI | mark=77317, oi=33955 | mark=2391, oi=901362 | Live state |
| Funding | BLOCKED | BLOCKED | Endpoint returns empty |

### API Format Notes

Different endpoints require different serialization:
- `candleSnapshot` → requires `req` wrapper
- `metaAndAssetCtxs` → flat format
- `l2Book` → flat format
- `recentTrades` → flat format
- `fundingHistory` → requires `req` wrapper but returns empty

### Access Classification

- Public data: ACCEPT_PRIMARY
- US execution: RESTRICTED / NOT AUTHORIZED
- Historical backfill: Feasible (API works with pagination)

---

## Lane B: Binance Historical Spot

**Status: PASS**

Markets: BTCUSDT, ETHUSDT

### Data Collected

| File | Records | Status | SHA256 |
|------|---------|--------|--------|
| btc_usdt_1460d.json | 420,464 | VERIFIED | e9c977e3... |
| eth_usdt_1460d.json | 420,464 | VERIFIED | 88fbaae3... |

### Live API Status

HTTP 451 (Unavailable For Legal Reasons) — geo-restricted from US location.
Local files verified as genuine Binance origin.

### Role

RESEARCH_DATA_ONLY. No execution assumptions.

---

## Lane C: Uniswap v3 Ethereum

**Status: BLOCKED**

### Pool Contracts (Registered)

| Pool | Address | Fee |
|------|---------|-----|
| WETH/USDC | 0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640 | 0.05% |
| WBTC/USDC | 0x99ac8cA7087fA4A2A1FB6357269965A2014ABc35 | 0.30% |

### Blocker

The Graph gateway now requires API key authentication. Free tier deprecated.

### Resolution Path

- Obtain Graph API key (free tier with account)
- OR build direct Ethereum RPC log collector
- OR use alternative indexer (Goldsky, SubQuery)

---

## Lane D: Base AMM

**Status: PARTIAL**

### Pool Selection

| Pair | Selected | Status |
|------|----------|--------|
| WETH/USDC | Uniswap v3 Base | PRIMARY_CANDIDATE — needs on-chain verification |
| cbBTC/USDC | TBD | NEEDS_VERIFICATION — no confirmed pool address |

### Blockers

1. Base AMM subgraph requires auth
2. Pool addresses need on-chain verification
3. cbBTC/USDC pool location unknown

---

## Schema Validation

All schemas from preregistration implemented and validated:

| Dataset | Result |
|---------|--------|
| HL BTC candles | 100/100 passed |
| HL ETH candles | 100/100 passed |
| BN BTCUSDT | 100/100 passed |
| BN ETHUSDT | 100/100 passed |

## Quality Gates

| Dataset | Q1 Duplicates | Q2 Monotonic | Q3 Price | Q4 Size | Total |
|---------|:---:|:---:|:---:|:---:|:---:|
| HL BTC | PASS | PASS | PASS | PASS | 4/4 |
| HL ETH | PASS | PASS | PASS | PASS | 4/4 |
| BN BTCUSDT | PASS | PASS | PASS | PASS | 4/4 |
| BN ETHUSDT | PASS | PASS | PASS | PASS | 4/4 |

## Cross-Source Parity

BTC spot vs perp: INSUFFICIENT_OVERLAP
Reason: Binance local file (ends ~Jun 2026) doesn't overlap Hyperliquid 7-day window. Parity infrastructure works; needs full HL backfill for overlap.

## Nautilus Adapter Audit

| Adapter | Importable | Notes |
|---------|:---:|-------|
| binance | YES | Full adapter present |
| hyperliquid | YES | Full adapter present |
| coinbase_intx | YES | Coinbase International (not US retail) |
| bybit | YES | Full adapter present |
| okx | YES | Full adapter present |
| deribit | NO | Not in Nautilus 1.221.0 |
| dydx | NO | Blocked: missing v4_proto |

---

## Prohibited Verification

- strategy_pnl_computed = false
- optimization_performed = false
- alpha_research_started = false
- live_capital_deployed = false
- execution_connected = false
- confirmation_consumed = false
- holdout_consumed = false
- ase2_started = false

---

## Decision

**PASS_CANONICAL_CRYPTO_DATA_FOUNDATION**

Lanes A (Hyperliquid) and B (Binance) provide a credible raw data foundation for BTC/ETH perps and deep historical spot. Lanes C and D are blocked by subgraph auth requirements — resolvable with API key acquisition or RPC-based collectors.

## Next Checkpoint

CRYPTO-DATA-1.1 — Fix blocked lanes (Graph API key or RPC collector), extend HL candle backfill, verify Base pool addresses on-chain.

Then: CRYPTO-MECH-1-SPOT-PERP-AMM-CONSTRAINT-ANATOMY
