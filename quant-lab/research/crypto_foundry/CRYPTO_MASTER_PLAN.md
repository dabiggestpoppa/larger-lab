# QUANT BOX — Crypto Quant Foundry Master Plan

**Branch:** `agent/crypto-quant-foundry`  
**Status:** PLANNING / RESEARCH ONLY  
**Execution authority:** NONE  
**Live capital authority:** NONE

## Mission

Build a crypto-native research and execution stack for QUANT BOX using transparent spot/AMM/on-chain state, perpetual/futures markets, options, liquidity provision, and state-conditioned payoff routing.

The program is not a port of the FX stack. It reuses QUANT BOX scientific discipline while allowing crypto-native market structure to define the models.

Core principle:

> Observe state and constraints first; choose the payoff structure second.

## Hard Research Boundary

The Crypto Quant Foundry will **not** compete in latency-sensitive market making or arbitrage.

Explicitly out of scope:

- sub-second scalping
- mempool sniping
- sandwiching / MEV racing
- liquidation sniping
- atomic cross-DEX arbitrage
- microspread HFT
- any strategy whose edge depends primarily on being first

These behaviors may be consumed as market data, but they are not the desired alpha source.

Preferred research horizons are structural: minutes, hours, days, funding cycles, distribution cycles, and state transitions.

---

# 1. Research Architecture

The crypto stack is separated into independent laboratories.

## Lab A — AMM / Spot Constraint Lab

Primary ecosystems:

- Ethereum
- Base
- BNB Chain
- Solana later as a separate non-EVM lane

Primary venues:

- Ethereum: Uniswap v3
- Base: Uniswap + Aerodrome
- BNB Chain: PancakeSwap
- Solana: Raydium + Orca

Purpose:

- pool-state constraints
- spot triangular relationships
- liquidity distribution
- swap-flow state
- pool-to-pool divergence
- DEX-vs-DEX price discovery
- DEX-vs-perp price discovery
- LP fee/IL anatomy

Initial core asset family:

- BTC representation
- ETH representation
- stablecoin numeraire

No long-tail token scan in the first phase.

## Lab B — Perpetual / Futures State Lab

Primary benchmark venue:

- Hyperliquid

Secondary / portability venues:

- Aster
- Drift
- Avantis
- Jupiter Perps
- Kraken/Coinbase regulated derivatives where useful
- additional Nautilus-supported venues only after audit

Purpose:

- market depth
- trades
- mark/index/oracle relationships
- funding
- open interest
- liquidations
- spot-perp basis
- relative-value spreads
- execution science

Hyperliquid remains a primary research and eventual execution candidate.

## Lab C — Options / Convexity Lab

Initial venue candidates:

- Deribit as reference options tape
- Derive as on-chain options/perps candidate
- Aevo as secondary on-chain options venue
- GammaSwap as LP/gamma-specific research object

Purpose:

- IV term structure
- skew
- gamma / vega / theta state
- realized-vs-implied volatility
- tail hedging
- LP convexity hedging
- synthetic straddles / spreads

## Lab D — Liquidity / Yield Lab

Infrastructure candidates:

- Gamma
- Arrakis
- native Uniswap / Aerodrome / PancakeSwap LP positions

Purpose:

- concentrated liquidity payoff geometry
- fee yield
- active-range occupancy
- impermanent loss
- LP delta/gamma exposure
- state-conditioned range management
- perp-hedged LP structures
- option-hedged LP structures

## Lab E — Capital / Payoff Routing

Purpose:

Given a market state, select the most appropriate payoff shape rather than forcing every state into LONG / SHORT.

Possible outputs:

- directional perp
- relative-value perp basket
- neutral grid
- directional grid
- concentrated LP
- LP + perp hedge
- LP + options hedge
- options / convexity
- carry / funding
- leveraged rebalance
- stand down

---

# 2. Price Objects Must Remain Separate

Never collapse different price mechanisms into one field.

Maintain separate canonical fields for:

- AMM pool price
- spot order-book mid
- perp last
- perp mark
- index/oracle price
- executable bid
- executable ask
- estimated impact price

A strategy may consume multiple price objects, but they are not interchangeable.

---

# 3. Initial Data Stack

The first goal is not a backtest. It is data sovereignty and venue truth.

## Required raw data classes

### AMM / DEX

- block time / block or slot
- pool address / market identifier
- token pair
- swap direction
- amount in / out
- effective execution price
- fee tier
- pool state
- active liquidity
- tick / price state where applicable
- liquidity additions/removals
- gas / transaction cost where relevant
- wallet / route metadata where responsibly available

### Perps / Futures

- timestamp
- venue
- symbol
- best bid / ask
- depth bands
- trades
- mark
- index/oracle
- funding
- open interest
- liquidations where available
- volume
- spread
- basis
- venue status

### Options

- underlying
- strike
- expiry
- call/put
- bid/ask
- mid
- volume
- OI
- IV
- delta
- gamma
- vega
- theta
- index/forward
- realized-vol reference

### Yield / LP

- TVL
- active-range liquidity
- fee tier
- actual fee generation
- incentive yield separately
- turnover / TVL
- realized volatility
- range occupancy
- rebalance count
- gas/rebalance cost
- LP concentration
- IL estimate

---

# 4. Initial Crypto Constraint Experiment

The first direct analogue to canonical TB should be a clean BTC / ETH / stablecoin triangle.

Candidate relationship:

`ETH/BTC × BTC/USD-like ≈ ETH/USD-like`

Possible implementations depend on venue and token representation.

The experiment must remain descriptive first:

1. construct synchronized legs
2. prove algebraic / unit parity
3. characterize residual / basis distribution
4. test severity monotonicity
5. inspect event timing by liquidity epoch
6. measure convergence path
7. estimate executable cost
8. only then consider a frozen strategy contract

No broad triangle scan in the first round.

---

# 5. Crypto-Native Atomic Structure

Do not force FX session assumptions into crypto.

Research recurring crypto-native clocks such as:

- UTC day boundary
- Asia / Europe / U.S. liquidity transitions
- U.S. ETF trading hours
- perpetual funding timestamps
- futures/options expiry windows
- weekday/weekend transitions

Goal:

Find whether uncertainty about remaining distribution collapses at recurring checkpoints.

State candidates:

- structural tier
- normalized unit / AU-like scale
- loop count
- delivered distribution
- remaining distribution
- time completion
- directional imbalance
- liquidity state
- funding state
- OI state
- options-volatility state

The model should eventually output a distribution contract, not merely BUY / SELL.

Example output object:

- center
- normalized structural unit
- p25 / p50 / p75 or p10-p90 envelope
- expected range life
- directional skew
- loop count
- breakout probability
- range confidence

---

# 6. Grid Layer

Three different grid concepts must be kept distinct.

## Perp Grid

Discrete leveraged or unleveraged orders on perpetual/futures venues.

Potential execution stack:

- Nautilus controller
- Hyperliquid primary
- regulated CEX/futures venues or other supported venues as portability lanes

## Liquidity Grid

Concentrated-liquidity ranges on AMMs.

Potential infrastructure:

- Gamma
- Arrakis
- direct protocol integration later

Grid bands are liquidity ranges, not limit orders.

## Rebalance Grid

State-conditioned portfolio rebalancing across perp exposures.

Example:

- BTC target beta
- ETH target beta
- SOL target beta

Rebalance only when deviation exceeds a frozen threshold.

This may be directional or near-market-neutral.

---

# 7. LP / Options / Perp Hybrid Research

Liquidity provision must be modeled as a payoff structure, not "free yield."

For every LP strategy decompose:

- swap fee income
- incentive income
- underlying directional exposure
- impermanent loss
- negative convexity / gamma-like exposure
- hedge cost
- funding carry
- option premium
- gas / rebalance cost
- smart-contract / venue risk

Candidate structures for later testing:

- LP only
- LP + delta hedge using perps
- LP + tail options
- LP + perp + options
- range-conditioned LP deployment
- state-conditioned withdrawal / widening / narrowing

No LP strategy is promoted using advertised APR alone.

---

# 8. Leveraged Rebalancing

Exchange-native spot rebalancing bots are reference implementations only.

QUANT BOX should eventually control a leveraged rebalance engine directly through its execution layer.

Potential state-conditioned targets:

- BTC-heavy leadership
- ETH leadership
- alt expansion
- deleveraging / stablecoin preference

Possible implementation:

- long/short perp basket
- gross exposure cap
- net beta target
- rebalance threshold
- turnover cap
- funding-aware routing
- liquidation-distance guardrail

This is a research engine, not capital authorization.

---

# 9. Existing Infrastructure Reuse

Before building new execution infrastructure, audit the existing `larger-lab` repository.

Priority reuse candidates:

- Nautilus Trader integration
- existing exchange adapters
- backtest framework
- execution-runtime foundation
- capital-routing infrastructure
- data-truth / provenance utilities
- strategy-foundry governance

The crypto program must not alter active canonical/CTBT forward collectors.

Use an isolated branch/worktree.

---

# 10. Scientific Program

## CRYPTO-DATA-0 — Venue & Market Reality Audit

No PnL.

Audit exact:

- chains
- venues
- market IDs / pool addresses
- launch dates
- available historical depth
- free historical sources
- API limitations
- WebSocket support
- archive/raw-log support
- funding/OI history
- liquidation history
- option-chain history
- LP history
- fee models
- wrapper/bridge risk
- U.S. accessibility / account constraints where relevant
- Nautilus adapter availability

Deliverable: venue/resource matrix with ACCEPT / WATCH / REJECT.

## CRYPTO-DATA-1 — Canonical Collector Foundation

Build raw-first collectors and storage contracts.

No alpha model.

Requirements:

- deterministic timestamps
- provenance
- venue-specific schemas
- replayability
- duplicate detection
- raw + normalized layers
- no forward fill across missing market states without explicit rule

## CRYPTO-MECH-1 — Spot / AMM vs Perp Constraint Anatomy

Test whether structural dislocations carry medium-horizon information after realistic cost.

No optimization.

Start BTC / ETH / stablecoin family only.

## CRYPTO-MECH-2 — Capital Routing / Dominance Anatomy

Test BTC / ETH / stablecoin / alt capital migration as state variables.

Dominance is a state input, not automatically a trade signal.

## CRYPTO-MECH-3 — Atomic Distribution State

Test crypto-native time checkpoints, normalized structural units, loop states, distribution completion, and remaining-range uncertainty.

## CRYPTO-PAYOFF-1 — Policy Comparison

Only after mechanism layers pass.

Compare frozen payoff policies:

- directional perp
- relative-value basket
- neutral/directional grid
- LP
- LP + hedge
- options
- leveraged rebalance

Same state engine, same development period, no result shopping.

## CRYPTO-CONFIRM-1 — One-Shot Confirmation

Freeze:

- data contract
- model/state engine
- policy
- costs
- pass/fail gates

Then open confirmation once.

No rescue after failure.

---

# 11. Current Venue Priority

This is a research priority list, not a production authorization.

## AMM / Spot

1. Ethereum / Uniswap v3 — long-history control
2. Base / Uniswap + Aerodrome — current low-cost EVM lab
3. BNB Chain / PancakeSwap — high-activity EVM comparison
4. Solana / Raydium + Orca — high-frequency non-EVM lane later

## Perp / Futures

1. Hyperliquid — primary benchmark and candidate execution venue
2. Aster — BNB/multi-chain portability candidate
3. Drift — Solana structural perp lab
4. Avantis — Base-native perp comparison
5. Jupiter Perps — Solana execution comparison
6. regulated U.S.-accessible futures venues as additional execution lanes

## Options

1. Deribit — reference tape
2. Derive — on-chain options/perps candidate
3. Aevo — secondary on-chain options venue
4. GammaSwap — LP/gamma-specific research

---

# 12. Immediate Next Steps

Do not build strategy logic yet.

Next work session should execute **CRYPTO-DATA-0** only.

Required outputs:

- `CRYPTO_VENUE_REGISTRY.csv`
- `CRYPTO_MARKET_REGISTRY.csv`
- `CRYPTO_DATA_SOURCE_MATRIX.csv`
- `CRYPTO_API_CAPABILITY_MATRIX.csv`
- `CRYPTO_HISTORY_DEPTH_MATRIX.csv`
- `CRYPTO_COST_MODEL_REGISTRY.csv`
- `CRYPTO_US_ACCESS_NOTES.md`
- `CRYPTO_NAUTILUS_REUSE_AUDIT.md`
- `CRYPTO_DATA_0_REPORT.md`
- `CRYPTO_DATA_0_DECISION.json`

The report must answer:

1. Where can we get the longest clean free history?
2. Which venues expose the richest live state?
3. Which exact BTC/ETH/stable markets are viable?
4. Which wrapper/bridge assets should be rejected?
5. Which venues can Nautilus already control?
6. Which datasets require custom collectors?
7. Can real cost be reconstructed?
8. Which venue combinations deserve CRYPTO-DATA-1?

STOP after CRYPTO-DATA-0 for human review.

---

# Truth Vocabulary

Use:

- SOURCE_CLAIM
- HYPOTHESIS
- OBSERVED
- DESCRIPTIVE
- DEVELOPMENT
- CONFIRMATION
- HOLDOUT
- FORWARD_SHADOW
- DEMO_EXECUTION
- PRODUCTION_AUTHORIZED

No venue, bot, LP strategy, or model is authorized for capital by this planning document.
