# CRYPTO-DATA-0.1 TRUTH REPAIR & DATA-1 PREREGISTRATION REPORT

**Checkpoint:** CRYPTO-DATA-0.1-TRUTH-REPAIR-AND-DATA1-PREREGISTRATION
**Branch:** agent/crypto-quant-foundry
**Base:** e46dff3f (CRYPTO-DATA-0)
**Decision:** PASS_TRUTH_REPAIRED_DATA1_PREREGISTERED

---

## REPAIR 1 — HYPERLIQUID U.S. ACCESS

**Finding:** DATA-0 incorrectly classified Hyperliquid as "US_ACCESS: YES" for execution.

**Repair:** Every affected artifact updated. Hyperliquid classification:
- PUBLIC_DATA_ACCESS = YES
- RESEARCH_DATA = ACCEPT_PRIMARY
- PERP_STATE_REFERENCE = ACCEPT_PRIMARY
- US_EXECUTION = RESTRICTED / NOT AUTHORIZED
- NON_US_EXECUTION_CANDIDATE = CONDITIONAL_ON_ELIGIBILITY

**Artifacts repaired:**
- CRYPTO_US_ACCESS_NOTES.md
- CRYPTO_VENUE_REGISTRY.csv
- CRYPTO_DATA_0_REPORT.md
- CRYPTO_DATA_0_DECISION.json
- CURRENT_RESEARCH_STATE.md
- CRYPTO_ACCESS_REGISTRY_V2.csv (new)

No self-custody or protocol reachability described as execution eligibility.

---

## REPAIR 2 — HYPERLIQUID FILE PROVENANCE

**Finding:** `btc_5m_4yr.json` is NOT native Hyperliquid data.

Evidence:
- First timestamp: 2022-06-16 21:00 UTC
- Hyperliquid BTC-PERP launched: May 2023
- File PRE-DATES Hyperliquid by ~11 months
- OHLCV values identical to `btc_usdt_1460d.json` (Binance) at same timestamps
- Same 85-minute gap at 2023-03-24 12:35 in both files
- Only difference: btc_5m_4yr starts 4 bars (20 min) earlier

**Classification:** RELABELED_ORIGIN — this is Binance BTCUSDT data with a misleading filename.

**Repair:**
- `btc_5m_4yr.json` → PROVENANCE_UNVERIFIED for Hyperliquid use
- DO NOT use as canonical Hyperliquid history in DATA-1
- `btc_usdt_1460d.json` → VERIFIED_BINANCE (use this as canonical Binance BTC source)
- `eth_usdt_1460d.json` → VERIFIED_BINANCE
- `sol_usdt_1460d.json` → VERIFIED_BINANCE

SHA256 hashes computed and recorded in CRYPTO_LOCAL_DATA_PROVENANCE_AUDIT.csv.

**Consequence:** No genuine pre-2023 Hyperliquid M5 data exists locally. DATA-1 must fetch fresh Hyperliquid data starting from May 2023 via the Hyperliquid REST API.

---

## REPAIR 3 — DRIFT OPERATIONAL STATUS

**Finding:** DATA-0 classified Drift as ACCEPT_SECONDARY without verifying current operational status.

**Repair:**
- HISTORICAL_RESEARCH = WATCH / RESEARCH_ONLY
- LIVE_DATA = VERIFY_CURRENTLY_AVAILABLE
- EXECUTION = NOT_APPROVED
- SECURITY_STATUS = REQUIRES_REVALIDATION

Drift remains on the research map but is not execution-ready until independently verified.

---

## REPAIR 4 — ACCESS TAXONOMY

**Finding:** DATA-0 used simplistic YES/NO for venue access.

**Repair:** New CRYPTO_ACCESS_REGISTRY_V2.csv with explicit fields:
- public_data_access
- account_required
- kyc_required
- us_data_access
- us_spot_execution
- us_derivatives_execution
- non_us_execution_candidate
- self_custodial
- terms_restricted
- status_verified_at
- source_class

Key distinction: permissionless settlement ≠ execution eligibility.

---

## REPAIR 5 — SOURCE AUTHORITY

**Finding:** DATA-0 cited operational facts without source attribution.

**Repair:** New CRYPTO_SOURCE_AUTHORITY_REGISTRY.csv recording:
- source (official docs / API / on-chain / terms)
- source_date
- verified_at
- source_class

---

## NAUTILUS ADAPTER AUDIT (IMPORT VERIFIED)

| Adapter | Import Status | Data Client | Exec Client | Notes |
|---------|--------------|-------------|-------------|-------|
| binance | IMPORTABLE | BinanceDataClientConfig + LiveDataClientFactory | BinanceExecClientConfig + LiveExecClientFactory + HistoricalDataLoader | Full |
| hyperliquid | IMPORTABLE | HyperliquidDataClientConfig + LiveDataClientFactory | HyperliquidExecClientConfig + LiveExecClientFactory | Full |
| coinbase_intx | IMPORTABLE | CoinbaseIntxDataClientConfig + LiveDataClientFactory | CoinbaseIntxExecClientConfig + LiveExecClientFactory | Note: module name is coinbase_intx not coinbase |
| bybit | IMPORTABLE | BybitDataClientConfig + LiveDataClientFactory | BybitExecClientConfig + LiveExecClientFactory | HistoricalDataLoader available |
| okx | IMPORTABLE | OKXDataClientConfig + LiveDataClientFactory | OKXExecClientConfig + LiveExecClientFactory | Full |
| deribit | NOT PRESENT | N/A | N/A | DATA-0 was WRONG — no Deribit adapter in Nautilus 1.221.0 |
| dYdX | BLOCKED | N/A | N/A | Missing v4_proto dependency |

---

## CANONICAL DATA-1 LANES (PREREGISTERED)

### LANE A — PERP STATE
- **Primary:** Hyperliquid public market data
- **Initial Markets:** BTC, ETH (SOL optional descriptive)
- **Raw objects:** trades, L2 book, mark, index/oracle, funding, OI, liquidations
- **Candles:** derived/convenience only, not canonical
- **No execution connection**

### LANE B — DEEP HISTORICAL SPOT REFERENCE
- **Primary:** Binance public historical data
- **Initial:** BTCUSDT, ETHUSDT
- **Role:** RESEARCH_DATA_ONLY
- **No Binance execution assumptions**

### LANE C — ETHEREUM AMM
- **Primary:** Uniswap v3
- **Initial Pools:** WETH/USDC, WBTC/USDC
- **Required:** exact pool addresses, fee tiers, swap events, mint/burn events, tick/sqrtPrice/liquidity
- **Store event-level raw records. Bars are DERIVED later.**

### LANE D — BASE AMM
- **Primary:** Aerodrome and/or Base Uniswap
- **Initial:** WETH/USDC, cbBTC/USDC
- **Selection basis:** actual depth, history, event accessibility, clean token contracts

### OPTIONS / LP
- **Status:** DATA-2_CANDIDATE
- **Not built in DATA-1**

---

## PREREGISTERED MARKETS

| Lane | Market | Venue | Chain | Contract/Address |
|------|--------|-------|-------|-----------------|
| A | BTC-PERP | Hyperliquid | Hyperliquid L1 | On-chain order book |
| A | ETH-PERP | Hyperliquid | Hyperliquid L1 | On-chain order book |
| B | BTCUSDT | Binance | CEX | REST API klines |
| B | ETHUSDT | Binance | CEX | REST API klines |
| C | WETH/USDC | Uniswap v3 | Ethereum | 0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640 (0.05% fee) |
| C | WBTC/USDC | Uniswap v3 | Ethereum | 0x99ac8cA7087fA4A2A1FB6357269965A2014ABc35 (0.30% fee) |
| D | WETH/USDC | Aerodrome | Base | To be verified in DATA-1 |
| D | cbBTC/USDC | Aerodrome | Base | To be verified in DATA-1 |

---

## BLOCKERS

1. No genuine Hyperliquid historical data in repo — DATA-1 must fetch from scratch
2. Hyperliquid U.S. execution restricted — data research only
3. Deribit not in Nautilus adapter package — options integration will require custom work
4. Drift security status unverified — defer to later phase
5. Base AMM pool addresses need on-chain verification in DATA-1

---

## PASS CONDITIONS VERIFICATION

| Condition | Status |
|-----------|--------|
| Hyperliquid U.S. execution classified | ✅ REPAIRED |
| btc_5m_4yr.json provenance verified/quarantined | ✅ QUARANTINED as RELABELED |
| All local datasets have truthful provenance | ✅ VERIFIED with SHA256 |
| Drift status correctly classified | ✅ REPAIRED |
| Access taxonomy distinguishes data vs execution | ✅ V2 PRODUCED |
| Source authority recorded | ✅ REGISTRY CREATED |
| DATA-1 contracts frozen | ✅ PREREGISTERED |
| No alpha/model/PnL work | ✅ CONFIRMED |
