# CRYPTO NAUTILUS REUSE AUDIT

## Installed Version

Nautilus Trader **1.221.0** is installed in the current environment.

## Existing Crypto Infrastructure in larger-lab

### Directly Reusable

| Component | Location | Status | Notes |
|-----------|----------|--------|-------|
| **Hyperliquid instrument definitions** | `.exec-runtime/quant-lab/strategies/hyperliquid_instruments.py` | REUSE_DIRECTLY | Full CryptoPerpetual definitions for BTC/ETH/SOL with tick sizes, fees, margin. Production-ready for backtesting. |
| **Hyperliquid data fetcher** | `quant-lab/data/hyperliquid_fetcher.py` | REUSE_DIRECTLY | Fetches OHLCV candles from Hyperliquid REST API. Supports 1m-1d intervals. Pagination built in. |
| **Binance data fetcher** | `quant-lab/data/binance_fetcher.py` | REUSE_DIRECTLY | Fetches OHLCV from Binance public API. No key needed. Pagination. |
| **Nautilus backtest framework** | `.exec-runtime/quant-lab/engines/` | REUSE_DIRECTLY | Existing Nautilus BacktestEngine configuration. CSV manual run available. |
| **DMR strategy (FX)** | `.exec-runtime/quant-lab/strategies/dmr_strategy.py` | REFERENCE_ONLY | Shows Nautilus strategy structure. Can reference for crypto strategy patterns. |
| **Hyperliquid Nautilus adapter** | Nautilus upstream | REUSE_DIRECTLY | Nautilus 1.221.0 includes upstream Hyperliquid adapter for market data + execution. |
| **Binance adapter** | Nautilus upstream | REUSE_DIRECTLY | Nautilus includes Binance spot/perp adapter. Not wired into larger-lab crypto yet. |

### Reusable After Repair

| Component | Location | Status | Notes |
|-----------|----------|--------|-------|
| **CEREBUS crypto engine** | `.exec-runtime/crypto/CEREBUS_Crypto_Engine.py` | REPAIR | Crypto trading engine exists but likely outdated. Needs audit. |
| **CEREBUS crypto backtest** | `.exec-runtime/crypto/CEREBUS_Crypto_Backtest.py` | REPAIR | Backtest code exists but uses custom execution. Needs Nautilus migration. |
| **Execution runtime foundation** | `.exec-runtime/` | REUSE | General execution infrastructure. Needs crypto-specific wiring. |

### Reference Only

| Component | Location | Status | Notes |
|-----------|----------|--------|-------|
| **FX strategies (symmetry trap, etc.)** | `.exec-runtime/quant-lab/strategies/` | REFERENCE | Strategy patterns reference. Do not import FX-specific logic. |
| **Capital routing** | `capital-routing/` | REFERENCE | Architecture reference. Crypto capital routing will be different. |

### Not Relevant for Crypto

| Component | Location | Status | Notes |
|-----------|----------|--------|-------|
| **MT5 data fetcher** | `quant-lab/data/mt5_data_fetcher.py` | NOT_RELEVANT | MetaTrader is FX-only. |
| **FX-specific atomic structure** | `quant-lab/src/strategy_foundry/atomic_structure/` | NOT_RELEVANT | ASE is FX-specific. Crypto will have its own atomic structure module. |

## Nautilus Adapter Availability for Crypto

| Venue | Data Adapter | Execution Adapter | Status in Nautilus 1.221.0 |
|-------|-------------|-------------------|---------------------------|
| Hyperliquid | Yes (upstream) | Yes (upstream) | BUNDLED — can wire into larger-lab |
| Binance | Yes (upstream) | Yes (upstream) | BUNDLED — not U.S. accessible |
| Bybit | Yes (upstream) | Yes (upstream) | BUNDLED — not wired in |
| OKX | Yes (upstream) | Yes (upstream) | BUNDLED — not wired in |
| Deribit | Yes (upstream) | Yes (upstream) | BUNDLED — options support exists |
| Coinbase | Yes (upstream) | Yes (upstream) | BUNDLED — U.S. accessible |
| Kraken | Yes (upstream) | Yes (upstream) | BUNDLED — U.S. accessible |
| dYdX | Yes (upstream) | No | BUNDLED — data only |
| Uniswap v3 | No upstream | No upstream | NOT BUNDLED — needs custom adapter |
| Aerodrome | No upstream | No upstream | NOT BUNDLED — needs custom adapter |
| PancakeSwap | No upstream | No upstream | NOT BUNDLED — needs custom adapter |
| Drift | No upstream | No upstream | NOT BUNDLED — needs custom or use Drift SDK |
| Gamma | No upstream | No upstream | NOT BUNDLED — API-only integration |

## Key Finding

Nautilus already bundles Hyperliquid and several CEX adapters. The primary gap
is DEX/AMM adapters for Uniswap/Aerodrome/PancakeSwap, which require custom
on-chain collectors or subgraph integrations. For CRYPTO-DATA-0, no new adapter
code is needed — only inventory and audit.

## Recommendation for CRYPTO-DATA-1

Wire Nautilus Hyperliquid adapter into the larger-lab crypto foundry first.
Then build a lightweight Uniswap subgraph adapter for AMM data.
