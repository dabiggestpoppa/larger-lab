# CRYPTO-DATA-1 CANONICAL COLLECTOR FOUNDATION — PREREGISTRATION

**Checkpoint:** CRYPTO-DATA-1-CANONICAL-COLLECTOR-FOUNDATION
**Branch:** agent/crypto-quant-foundry
**Preregistered by:** CRYPTO-DATA-0.1-TRUTH-REPAIR

## Purpose

DATA-1 is a DATA FOUNDATION checkpoint only. No mechanism research. No CTB. No Atomic Structure. No Capital Routing. No PnL.

## Canonical Lanes

### LANE A — PERP STATE (Hyperliquid)

**Venue:** Hyperliquid (public data only, NO execution)
**Markets:** BTC-PERP, ETH-PERP (SOL optional descriptive)
**Raw objects (canonical):**
- trades (WebSocket market trades)
- L2 book snapshots (WebSocket)
- mark price
- index/oracle price
- funding rate history
- open interest history
- liquidation events (if genuinely available)
- candles (derived convenience only)

**Collection method:** hyperliquid-python-sdk `Info` class (public read-only)
**Time standard:** UTC, timezone-aware
**Storage:** raw/ per-event, normalized/ for derived candles

### LANE B — DEEP HISTORICAL SPOT (Binance)

**Venue:** Binance (RESEARCH_DATA_ONLY — no execution assumptions)
**Markets:** BTCUSDT, ETHUSDT
**Raw objects:**
- historical OHLCV candles (1m-1d)
- provenance tracking per bar set

**Collection method:** Binance REST API `/api/v3/klines` (public, no key)
**Existing data:** btc_usdt_1460d.json (verified, SHA256: e9c977e3...) — 4yr M5
**Time standard:** UTC
**Storage:** raw/ for original JSON, normalized/ for standardized format

### LANE C — ETHEREUM AMM (Uniswap v3)

**Venue:** Uniswap v3 on Ethereum mainnet (chain_id: 1)
**Pools (to verify exact addresses in DATA-1):**
- WETH/USDC 0.05% fee tier
- WBTC/USDC 0.30% fee tier

**Raw objects (event-level):**
- Swap events (amount0, amount1, sqrtPriceX96, tick)
- Mint/Burn events (liquidity changes)
- Pool state (tick, sqrtPrice, liquidity) at block level
- Block timestamp, tx hash, log index

**Collection method:** The Graph subgraph + path to raw RPC/log reproduction
**Time standard:** UTC (block timestamps)
**Storage:** raw/ for event records, normalized/ for derived bars

### LANE D — BASE AMM (Aerodrome or Uniswap v3)

**Venue:** Base chain (chain_id: 8453)
**Candidates (verify in DATA-1):**
- Aerodrome WETH/USDC CL
- Uniswap v3 WETH/USDC
- Aerodrome cbBTC/USDC CL

**Selection criteria:** actual depth, history length, event accessibility, clean token contracts
**Raw objects:** Same as Lane C (event-level AMM data)
**Collection method:** Subgraph + RPC

## Storage Contract

```
data_1/
  contracts/          # Frozen market/source contracts
  collectors/         # Collector code
  raw/               # Venue-original format (never modified)
    hyperliquid/      # Per event type
    binance/          # Per market
    uniswap_v3/       # Per pool, per event type
    base_amm/         # Per pool
  normalized/         # Standardized schema across venues
  manifests/          # Per-dataset provenance manifests
  quality/            # Quality check results
  tests/              # Test fixtures + unit tests
  reports/            # Cross-source parity reports
```

## Time Standard

Canonical: UTC
All timestamps timezone-aware.
Session/timezone transforms are derived features — NOT in DATA-1 raw storage.

## Schema Version

Schema v1.0.0 — frozen at DATA-1 preregistration.
