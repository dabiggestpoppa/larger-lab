# QUANT BOX — Crypto Quant Foundry Current Research State

**Checkpoint:** `CRYPTO-DATA-0-VENUE-AND-MARKET-REALITY-AUDIT`  
**Branch:** `agent/crypto-quant-foundry`  
**Decision:** `PASS_CRYPTO_DATA_FOUNDATION`  
**Strategy research:** NOT STARTED  
**Execution:** NOT AUTHORIZED  

## Completed Checkpoints

### CRYPTO-0-PLANNING-ANCHOR ✅
- Master plan written
- Research state established
- Decision: READY_FOR_CRYPTO_DATA_0

### CRYPTO-DATA-0-VENUE-AND-MARKET-REALITY-AUDIT ✅
- All venues audited (15+ venues across AMM, perp, options, LP)
- Primary venues identified: Hyperliquid, Binance, Uniswap v3, Aerodrome, Deribit, Gamma
- Secondary venues identified: PancakeSwap, Raydium, Orca, Drift, Kraken, Coinbase, Arrakis, Aster
- Data source matrices produced
- Cost models documented
- Wrapper risks catalogued
- Nautilus reuse audit completed
- Open-source infrastructure inventoryed
- US access notes documented
- Existing data in repo verified
- Decision: PASS_CRYPTO_DATA_FOUNDATION

## Current Venue Shortlist (Post DATA-0)

### Primary
| Venue | Role | Markets | US Access |
|-------|------|---------|-----------|
| Hyperliquid | Perp benchmark + execution | BTC/ETH/SOL perps + spot | YES |
| Binance | Historical data source | BTC/ETH/SOL 8yr candles | Data only |
| Uniswap v3 (Ethereum) | AMM reference | WETH/USDC, WBTC/USDC | YES |
| Aerodrome (Base) | Low-cost AMM lab | WETH/USDC, cbBTC/USDC | YES |
| Deribit | Options reference | BTC/ETH options | Data only |
| Gamma | LP vault data | Managed CL vaults | YES |

### Secondary
PancakeSwap, Raydium, Orca, Drift, Kraken, Coinbase, Arrakis, Aster

## Existing Data Assets
- `btc_5m_4yr.json` — Hyperliquid BTC-PERP 5m (4 years)
- `btc_usdt_1460d.json` — Binance BTCUSDT 5m (4 years)
- `eth_usdt_1460d.json` — Binance ETHUSDT 5m (4 years)
- `sol_usdt_1460d.json` — Binance SOLUSDT 5m (4 years)
- `hyperliquid_fetcher.py` — HL candle fetcher (working)
- `binance_fetcher.py` — Binance candle fetcher (working)
- `.exec-runtime/.../hyperliquid_instruments.py` — Full HL instrument definitions

## Nautilus Reuse
- Hyperliquid adapter: BUNDLED in Nautilus 1.221.0 (reuse directly)
- Binance adapter: BUNDLED (data research only, not U.S. execution)
- Coinbase/Kraken/Deribit adapters: BUNDLED
- DEX adapters: NOT BUNDLED (need custom collectors)

## Current Hypothesis Families

### CTB — Crypto Triangular / Constraint Resolution
Question: Does medium-horizon BTC/ETH/stable displacement predict resolution after realistic cost?

### CAS — Crypto Atomic Structure
Question: Does 24/7 crypto exhibit stable normalized range/loop/checkpoint structure?

### CCR — Crypto Capital Routing
Question: Do BTC/ETH/stablecoin/alt capital-share states predict future risk-bucket leadership?

### CLH — Crypto Liquidity Hedge
Question: Can LP fee exposure be conditionally combined with perps/options?

### CLR — Crypto Leveraged Rebalance
Question: Can state-conditioned perp target weights harvest relative dispersion?

## Next Checkpoint

`CRYPTO-DATA-1-CANONICAL-COLLECTOR-FOUNDATION`

Scope:
1. Wire Nautilus Hyperliquid adapter for BTC/ETH perps
2. Build Binance historical backfill pipeline
3. Build Uniswap v3 subgraph adapter
4. Build Aerodrome subgraph adapter
5. Store raw + normalized layers with provenance
6. Validate data quality
7. Produce canonical price series

## STOP Rule

Do not proceed to model building merely because data is available.

CRYPTO-DATA-1 must first produce a clean, validated, provenance-tracked data foundation before any mechanism research begins.
