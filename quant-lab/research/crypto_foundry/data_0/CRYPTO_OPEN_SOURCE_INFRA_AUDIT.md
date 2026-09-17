# CRYPTO OPEN-SOURCE INFRA AUDIT

## Official SDKs & Clients

| Project | Language | Purpose | Maturity | Notes |
|---------|----------|---------|----------|-------|
| **hyperliquid-python-sdk** | Python | HL REST + WebSocket client | Production | Official. Used by our fetcher. pip install hyperliquid. |
| **nktkas/hyperliquid** | TypeScript | HL client | Production | Community TypeScript SDK. |
| **infinitefield/hypersdk** | Rust | HL client | Early | Community Rust SDK. |
| **CCXT** | Python/JS/etc | Multi-exchange API | Production | Supports Hyperliquid, Binance, Coinbase, Kraken, etc. Unified interface. Mature. |
| **Uniswap SDK** | TypeScript | Uniswap v3 interactions | Production | Official by Uniswap Labs. |
| **Aerodrome SDK** | TypeScript | Aerodrome interactions | Early | Community-built. |
| **Raydium SDK** | TypeScript | Raydium interactions | Production | Official Raydium SDK. |
| **Drift SDK** | TypeScript/Rust | Drift protocol interactions | Production | Official Drift SDK. |
| **Deribit Python API** | Python | Deribit REST/WS | Production | Community maintained. Well documented. |
| **Gamma API** | REST | Vault management | Production | Official Gamma API. |
| **Arrakis SDK** | TypeScript | Vault management | Production | Official Arrakis SDK. |

## Data Indexers

| Project | Purpose | Maturity | Notes |
|---------|---------|----------|-------|
| **The Graph** | Subgraph indexing for EVM chains | Production | Uniswap, Aerodrome, PancakeSwap subgraphs available. Free tier generous. |
| **Dune Analytics** | SQL on-chain analytics | Production | Free tier. Query any EVM data. Historical swap/trade analysis. |
| **Flipside Crypto** | SQL on-chain analytics | Production | Alternative to Dune. Solana + EVM support. |
| **Goldsky** | Managed subgraph hosting | Production | Alternative to hosted Graph. |
| **Solana FM / Solscan** | Solana indexer | Production | Solana RPC + indexed data. |

## Historical Data Sources

| Source | Assets | Depth | Cost | Notes |
|--------|--------|-------|------|-------|
| **Binance public API** | All Binance pairs | 2017+ | Free | Our fetcher already uses this. BTCUSDT 4yr 5m data in repo. |
| **Hyperliquid public API** | HL perps | 2023+ | Free | Our fetcher uses this. BTC 4yr 5m JSON in repo. |
| **Coinbase Exchange API** | All Coinbase pairs | 2014+ | Free | Full historical candles. |
| **Kraken public API** | All Kraken pairs | 2013+ | Free | Full historical OHLC. Deepest spot BTC data. |
| **Deribit public API** | Options + perps | 2018+ | Free | Full options chain history. |
| **The Graph** | All indexed DEX data | Protocol launch | Free tier | Subgraph queries for Uniswap/Aero/etc. |
| **Dune** | EVM on-chain data | varies | Free tier | SQL access to all EVM data. |
| **CryptoDataDownload** | Aggregated | varies | Free/Paid | Pre-built CSV datasets. |
| **CoinGecko/CoinMarketCap** | Aggregated | varies | Free tier | Daily data. Not suitable for M5 research. |

## Existing Local Data

| File | Source | Coverage | Notes |
|------|--------|----------|-------|
| `btc_usdt_1460d.json` | Binance | BTCUSDT 5m ~4 years | In repo. Ready to use. |
| `btc_5m_4yr.json` | Hyperliquid | BTC-PERP 5m ~4 years | In repo. Ready to use. |
| `eth_usdt_1460d.json` | Binance | ETHUSDT 5m ~4 years | In repo. |
| `sol_usdt_1460d.json` | Binance | SOLUSDT 5m ~4 years | In repo. |
| `BTCUSD_D1.csv` | Unknown (MT5?) | BTC D1 from 2022-06 | In repo. Low quality (vol=0). |
| `ETHUSD_D1.csv` | Unknown (MT5?) | ETH D1 from 2020-06 | In repo. Low quality (vol=0). |
| `BNBUSD_M5.csv` | MT5 broker | BNB M5 from 2022-01 | In repo. 435K rows. |
| `LTCUSD_M5.csv` | MT5 broker | LTC M5 from 2022-01 | In repo. 386K rows. |

## Key Finding

The existing repo already contains usable BTC/ETH/SOL historical 5-minute data
from both Binance (4 years) and Hyperliquid (4 years). The Hyperliquid Python
SDK and Binance fetcher are already written and functional. Nautilus bundles
adapters for both venues. The data foundation for CRYPTO-DATA-1 is substantially
ahead of what needs to be built.
