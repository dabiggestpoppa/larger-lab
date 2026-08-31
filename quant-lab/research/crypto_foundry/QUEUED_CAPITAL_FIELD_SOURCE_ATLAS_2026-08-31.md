# QUEUED CAPITAL FIELD + SOURCE ATLAS — 2026-08-31

**Status:** QUEUED / DEFERRED  
**Authority:** operator idea capture only  
**Implementation authorization:** NONE  
**Schema mutation authorization:** NONE  
**Alpha-generation authorization:** NONE

This document preserves the operator's future crypto observability / capital-routing architecture without interrupting the active Sensor Fabric / mechanical-field build.

## 1. Scheduling rule

The active program remains:

**Sensor Fabric → mechanical observables / MECH restart → only then capital-field expansion → only later alpha/sentiment.**

This queue MUST NOT delay the active Bloc 3 provider-adapter sequence unless a future operator review explicitly reopens source expansion.

No NFT program is planned. Social/attention intelligence is explicitly FAR-LATER and is not part of the current build.

## 2. Long-run architecture

```text
CEX + DEX VENUE MECHANICS
        |
        v
MECHANICAL FIELD
        |
        +-------------------------+
        |                         |
        v                         v
ONCHAIN / CROSS-CHAIN FLOW   CREDIT / YIELD
        |                         |
        +------------+------------+
                     |
                     v
               CAPITAL FIELD
                     |
          +----------+----------+
          |                     |
          v                     v
   PROTOCOL ECONOMICS       RWA STATE
          |                     |
          +----------+----------+
                     |
                     v
               MARKET HEALTH
                     |
                     v
              CAPITAL ROUTING
                     |
                [LATER ONLY]
              STRUCTURAL ALPHA
                THIN ALPHA
```

The design principle is unchanged: **observe first, preserve provider-native semantics, derive state only after evidence.**

## 3. Source classes

### A. Core CEX mechanical spine — CURRENT PROGRAM

Production-candidate spine remains governed by Sensor Fabric I14 and Bloc 3:

- KRAKEN_FUTURES — built / offline frozen.
- GATE_FUTURES — built / awaiting operator ratification.
- OKX_SWAP — next production candidate after Gate review.
- DERIBIT — production candidate after OKX.

Reference / excluded current sources remain evidence-only unless a later evidence packet reopens them:

- BINANCE_USDM — live REST geo-restricted; public archive useful for historical reference.
- BYBIT_LINEAR — geo-restricted from current region; no bypass.
- BITFINEX community archive — corroboration/reference only.

### B. Future DEX / onchain mechanical venue registry — HIGH VALUE, DEFERRED

These should eventually be characterized as independent venue-mechanics sources, NOT as alpha products:

- HYPERLIQUID — perp premium/oracle/mark, OI, funding, trades, L2 book.
- LIGHTER — decentralized CLOB/perp venue; book/trade/funding/OI characterization target.
- RISE / RISEx — onchain perp/CLOB mechanics; book/trade/OI/funding characterization target.
- DYDX — order book, trades, funding, perpetual-market context.
- COINBASE derivatives / public market surfaces — index/mark/funding/books where public and legally/technically observable.
- BINANCE_US_SPOT — SPOT reference/flow only; NEVER substitute for BINANCE_USDM derivative state.

Future scientific use:

- CEX-vs-DEX OI migration.
- funding dispersion.
- premium/basis dispersion.
- order-book depth dispersion.
- venue lead/lag.
- liquidation divergence.
- liquidity fragmentation.
- one-venue capital expansion without same-scale confirmation elsewhere.

No such derived state is authorized now.

### C. Basis / book-depth expansion targets — IMPORTANT FUTURE GAP CLOSURE

Current Sensor Fabric evidence leaves provider-native BASIS and BOOK_METRIC relatively concentrated.

High-value future characterization targets:

1. **OKX**
   - provider-native premium / index / mark relationships.
   - historical order-book surfaces if still publicly available.
   - preserve provider-native semantics; do not silently declare Kraken basis equivalence.

2. **Hyperliquid**
   - premium, oraclePx, markPx.
   - L2 depth.

3. **dYdX / Lighter / RISEx / Coinbase / Deribit**
   - raw books as independent mechanical evidence.

Long-run architecture for book metrics:

```text
T1 provider-native raw books
        ->
T2 standardized mechanical book observables
        spread / depth-at-bps / imbalance / impact / slippage / slope / convexity
```

Provider-native precomputed metrics (for example Kraken book analytics) remain useful controls, but the preferred cross-venue comparison layer should ultimately be built from raw books under one explicit QUANT BOX methodology.

Basis/premium follows the same doctrine: Kraken basis, OKX premium, Hyperliquid premium, mark-index/oracle relationships remain separate T1 semantics; only a later T2 methodology may compare/normalize them.

### D. Aggregator corroboration — DEFERRED

- COINALYZE — future controlled probe for funding, predicted funding, OI, liquidation, positioning. A credential exists OUT-OF-BAND; runtime must read only `COINALYZE_API_KEY` (or approved secret store). **NEVER commit credential values.**
- DEFILLAMA — broad DeFi/yield/TVL/bridge/stablecoin discovery and corroboration; aggregator never silently replaces first-party/onchain truth.
- TOKEN TERMINAL — high-quality protocol fundamentals benchmark/reference; paid API must not become a required free-only runtime dependency.
- SOSOVALUE — research/ETF/market-context corroboration.
- SPECTRE AI — external intelligence candidate / watchlist, not canonical mechanical truth.
- VALUEVERSE — derived protocol valuation/fundamental lens, later only.

### E. Capital plumbing / cross-chain routing — HIGH VALUE, POST-SENSOR

- LI.FI / JUMPER — route topology, supported chains/tokens/bridges/DEX routes.

Important distinction:

- route availability = **possible capital pathway**;
- bridge/onchain transfer events = **realized capital movement**.

Future Capital Field should compare both rather than treating router quotes as realized flow.

### F. Credit / lending — POST-SENSOR / POST-MECH

Candidate first-party protocol families:

- AAVE
- MORPHO / MORPHO VAULTS
- COMPOUND
- SPARK
- EULER
- KAMINO where relevant

Future raw observables may include:

- supplied assets / supplied notional.
- borrowed assets / borrowed notional.
- available liquidity.
- utilization.
- supply / borrow rates.
- collateral factors / LTV / liquidation thresholds.
- liquidation activity.
- market/vault allocations.
- reward rates.

Derived future states such as CREDIT_STRESS, CAPITAL_ROUTING or MARKET_HEALTH are NOT source fields and are NOT authorized now.

### G. Vault / yield optimization — POST-SENSOR / POST-MECH

- BEEFY — vault definitions, underlying strategies, APY/APY breakdown, TVL, share price, fees, harvest state.
- YEARN — future candidate.
- MORPHO VAULTS — credit + vault junction.
- YIELDZ — route/UI composition reference; underlying protocols remain preferred truth sources.

Future purpose: reconstruct delegated capital topology, e.g.

```text
user capital -> vault -> strategy -> underlying protocol -> pool/market -> asset
```

### H. Yield markets — POST-SENSOR / HIGH FUTURE VALUE

- PENDLE
- BOROS / Pendle funding-yield markets

Future raw targets:

- SY / PT / YT market identity.
- maturity.
- TVL / liquidity.
- volume.
- underlying yield.
- implied/fixed yield where provider-native.
- funding-yield contracts / cross-venue funding dispersion where observable.

Future derived use: lending spot rate vs vault realized rate vs market-implied future yield. No yield-alpha implementation now.

### I. RWA / tokenized-assets observability — POST-SENSOR

- Base tokenized-stock / RWA ecosystems.
- Robinhood Chain Stock Tokens / public observable RWA state.
- StonkBrokers — EXPERIMENTAL Robinhood-chain ecosystem probe/reference only.
- future tokenized Treasury / equity protocols (e.g. Ondo/Centrifuge-class sources) only when separately researched and evidenced.

Potential future raw observables:

- circulating token supply.
- provider/oracle/mark price.
- DEX liquidity.
- lending collateral eligibility/use.
- vault integration.
- bridge location / chain distribution.

Never treat tokenized exposure as identical legal/economic ownership without preserving source semantics.

### J. Entity / project / venture graph — MUCH LATER

- ROOTDATA — project/team/investor/funding relationship metadata.
- CRYPTORANK — fundraising, token sales, investors, vesting/unlocks/project lifecycle context.
- FRONTRUN — venture/project-emergence reference; paid dependency not required.

These belong beside a future entity/ecosystem graph, not inside mechanical market sensors.

### K. Social / attention intelligence — FAR-LATER ONLY

Captured but intentionally outside current and near-term scope:

- PUREALPHA
- ALPHAGATE
- MONI
- related social/mindshare/wallet-social tools

Future role only: independent attention/diffusion corroboration after mechanical + capital fields exist.

No social adapter, sentiment score, alpha model or prompt-driven signal system is authorized by this document.

## 4. Explicit exclusions

- NFT/mint ecosystem: **not part of the planned Crypto OS scope**.
- mint/sniping execution tools: no sensor role.
- private-key/browser-wallet utilities: no infrastructure dependency.
- unverified airdrop/mint tools: no OCE integration.
- paid aggregators: may be reference/benchmark sources but may not become required runtime dependencies under FREE_ONLY without a new operator decision.

## 5. Deferred source-adjudication protocol

When this queue is eventually reopened, every candidate source must pass a small evidence pipeline before any adapter work:

```text
DISCOVERED
-> DOCUMENTED
-> ACCESS VERIFIED
-> PROVIDER-NATIVE CONTRACT VERIFIED
-> HISTORY / PIT CHARACTERIZED
-> SEMANTICS CHARACTERIZED
-> ROLE ADJUDICATED
-> ONLY THEN ADAPTER CANDIDATE
```

Candidate roles:

- PRIMARY_CANDIDATE
- SECONDARY_CANDIDATE
- CORROBORATOR
- REFERENCE_ONLY
- CURRENT_ONLY
- SEMANTICALLY_DISTINCT
- DATA_BLOCKED
- PAID_REFERENCE
- DEFERRED
- NOT_ELIGIBLE

No source enters production because documentation looks attractive.

## 6. Future arc model

The eventual system may observe disagreements such as:

- capital expanding on a DEX while CEX OI remains flat;
- CEX funding repricing without equivalent DEX premium response;
- bridge inflow into one chain without same-scale lending/vault deployment;
- lending utilization rising while spot price remains unchanged;
- vault inflows concentrating into a specific underlying market;
- Pendle/Boros implied yield repricing before realized lending rates;
- RWA liquidity/collateral moving across chains;
- protocol fundamentals diverging from token market valuation.

These are **research questions**, not current signals.

## 7. Reopen condition

Do NOT execute this queue now.

Recommended reopen only after one of the following:

1. core Sensor Fabric providers and mechanical observables are complete or near-complete; or
2. MECH21 / LF14 restart explicitly identifies a missing observable best satisfied by one of these sources; or
3. operator explicitly authorizes source expansion.

At reopen, prioritize:

1. DEX mechanical venue characterization.
2. basis/raw-book redundancy.
3. cross-chain/bridge flow.
4. lending/credit.
5. yield markets/vaults.
6. RWA.
7. protocol fundamentals.
8. entity/project graph.
9. social/attention last.

## 8. Immediate program return point

This queue does not change the active Sensor Fabric truth.

At capture time:

- `agent/crypto-sensor-fabric-build` HEAD = `ea61cb63bce2cbb1256658ea9c81a0fd84da9ece`.
- Gate I06 is implemented offline and awaits operator ratification.
- Kraken remains frozen offline.
- active next-provider decision must remain I14-bound.
- after Gate ratification, **OKX_SWAP is the natural next production adapter**, followed by DERIBIT, then Bloc 3 adapter matrix / network smoke / final validation / handoff according to the frozen architecture and current promotion authority.

No queued source in this document silently alters I14.
