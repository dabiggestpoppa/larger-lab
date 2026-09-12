# CRYPTO US ACCESS NOTES

## Summary

U.S. access varies significantly by venue. Data research may use any publicly
available data. Execution eligibility is a separate gate.

## ACCEPTED (U.S.-accessible for execution research)

| Venue | Markets | Notes |
|-------|---------|-------|
| **Hyperliquid** | BTC/ETH/SOL perps + spot | Decentralized L1. No KYC for usage. U.S. users can access via self-custodial wallet. Funding available. |
| **Kraken** | BTC/ETH futures + spot | Regulated U.S. exchange. Full KYC required. BTC/ETH futures available. Options not available. |
| **Coinbase** | BTC/ETH/SOL spot + BTC futures | Regulated U.S. exchange. Full KYC. BTC futures launched 2024. |
| **Uniswap (Base)** | All CL AMMs | Permissionless. No KYC. Low gas on Base. |
| **Aerodrome** | All CL AMMs | Permissionless. No KYC. Base chain. |
| **PancakeSwap** | All AMMs | Permissionless. No KYC. BNB Chain. |
| **Gamma** | Vault management | Permissionless. No KYC. |
| **Arrakis** | Vault management | Permissionless. No KYC. |

## RESTRICTED (data research only — no U.S. execution)

| Venue | Restriction | Notes |
|-------|-------------|-------|
| **Deribit** | No options for U.S. persons | Can use perps (some restrictions). Full options chain for research data only. |
| **Binance** | Not U.S.-accessible | Full API for historical data research. Cannot execute. |

## WATCH (unclear / limited)

| Venue | Status | Notes |
|-------|--------|-------|
| **Crypto.com** | Limited in some U.S. states | Grid bot product available. Perps restricted in U.S. |
| **Drift** | Decentralized, self-custodial | Solana-based. U.S. users can access via wallet. |
| **Derive** | Early stage | No clear U.S. policy yet. |
| **Aevo** | Unclear | No clear U.S. policy. |

## Key Principle

Data research does NOT require venue access. Public on-chain data and public
REST APIs are accessible to all. Execution eligibility requires separate
verification per venue.

Do NOT use VPN or location falsification as part of the system.
