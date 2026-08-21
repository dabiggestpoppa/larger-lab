# QUANT BOX — Crypto Quant Foundry Current Research State

**Checkpoint:** `CRYPTO-0-PLANNING-ANCHOR`  
**Branch:** `agent/crypto-quant-foundry`  
**Decision:** `READY_FOR_CRYPTO_DATA_0`  
**Strategy research:** NOT STARTED  
**Execution:** NOT AUTHORIZED

## Current Working Decisions

### 1. Hyperliquid stays central

Hyperliquid remains the primary perp/futures benchmark and a serious eventual execution candidate.

The crypto stack should use transparent spot/AMM/on-chain state for research while expressing many trades through perpetual/futures markets when appropriate.

### 2. Do not choose one chain for everything

Use different venues for different scientific purposes.

- Ethereum: long-history AMM control
- Base: current low-cost EVM lab
- BNB Chain: PancakeSwap / high-activity EVM comparison
- Solana: later high-frequency/routed-liquidity lane
- Hyperliquid: on-chain order-book / perp-state benchmark

### 3. Research venue != execution venue

A signal may be derived from:

- AMM liquidity
- spot flow
- dominance/capital migration
- wallet/on-chain flow
- funding/OI
- options state

while the trade is expressed through a perp/futures venue.

### 4. No latency-dependent alpha

Do not pursue:

- MEV
- mempool racing
- atomic arbitrage
- sub-second scalping
- liquidation sniping
- microspread HFT

QUANT BOX should trade slower structural states and consume HFT/arb behavior as mechanism data.

### 5. Payoff routing is a target architecture

The eventual system should choose between:

- directional perp
- relative-value basket
- neutral grid
- directional grid
- concentrated liquidity
- LP + perp hedge
- LP + options hedge
- volatility/convexity
- carry/funding
- leveraged rebalance
- no position

### 6. Three grid concepts

Keep separate:

- **Perp Grid:** discrete orders on a leveraged futures/perp venue
- **Liquidity Grid:** concentrated-liquidity ranges on AMMs
- **Rebalance Grid:** threshold-based rebalancing of multi-asset perp exposures

### 7. LP data matters even if QUANT BOX never LPs

Pool liquidity distribution can become a structural feature:

- active liquidity above/below spot
- thin/thick regions
- liquidity additions/removals
- fee generation
- pool imbalance
- swap pressure

This can inform perp trades without requiring LP capital.

### 8. Options are a first-class hedge/payoff layer

Options should later be used to:

- cap LP tails
- buy back convexity
- express breakout probability
- compare implied vs expected realized volatility
- construct hybrid LP/perp/option positions

### 9. Existing infrastructure should be reused

Audit existing larger-lab components before coding new execution plumbing, especially:

- Nautilus Trader
- exchange adapters
- execution-runtime foundation
- capital-routing infrastructure
- data-truth/provenance tooling
- foundry governance patterns

## Current Hypothesis Families

These are hypotheses, not accepted strategies.

### CTB — Crypto Triangular / Constraint Resolution

Start with BTC / ETH / stablecoin relationships.

Question:

Does medium-horizon constraint displacement predict resolution after realistic cost?

### CAS — Crypto Atomic Structure

Question:

Does 24/7 crypto exhibit stable normalized range/loop/checkpoint structure that predicts remaining distribution?

### CCR — Crypto Capital Routing

Question:

Do BTC/ETH/stablecoin/alt capital-share and flow states predict future risk-bucket leadership?

### CLH — Crypto Liquidity Hedge

Question:

Can LP fee exposure be conditionally combined with perps/options to produce better risk-adjusted payoff geometry?

### CLR — Crypto Leveraged Rebalance

Question:

Can state-conditioned perp target weights harvest medium-horizon relative dispersion without relying on latency?

## Current Venue Watchlist

### AMM / spot

- Ethereum / Uniswap v3
- Base / Uniswap
- Base / Aerodrome
- BNB Chain / PancakeSwap
- Solana / Raydium
- Solana / Orca

### perps/futures

- Hyperliquid
- Aster
- Drift
- Avantis
- Jupiter Perps
- Kraken derivatives/futures
- Coinbase futures
- other Nautilus-supported venues only after audit

### options / convexity

- Deribit
- Derive
- Aevo
- GammaSwap

### LP automation / vault infrastructure

- Gamma
- Arrakis

## Next Checkpoint

`CRYPTO-DATA-0-VENUE-AND-MARKET-REALITY-AUDIT`

No strategy PnL.

The next checkpoint must identify the exact viable markets, pools, historical sources, live APIs, cost models, and existing larger-lab/Nautilus integrations before any quant model is designed.

## STOP Rule

Do not proceed to model building merely because data is available.

CRYPTO-DATA-0 must first produce a human-reviewed shortlist of canonical venue/market/data contracts.
