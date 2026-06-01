# API Execution Architecture — 2026-05-31 21:45 EDT

## MAD Directive
"Pull data via API like MT5, circumvent NT8 GUI entirely — ensure same execution on live"

## Research Findings

### NT8 REST API (Official)
- URL: developer.ninjatrader.com/products/api
- REST API with Swagger spec → Python client generation
- Headless: submit/modify/cancel orders, stream quotes, account data
- Requires API credentials from NT8
- Does NOT require NT8 Desktop GUI

### IBKR Native Python API (ibapi) — RECOMMENDED
- Direct Python → Interactive Brokers (TWS/Gateway)
- Single socket connection for: data + execution + account
- Free with IBKR account
- Supports: historical data pull, live orders, portfolio monitoring
- No middleman platform needed

### Proposed Architecture
```
CEREBUS Python Engines (ST + P90)
        ↓ signals
IBKR TWS API (Python ibapi)
   ├── Historical data pull (OHLCV for any asset)
   ├── Live order submission
   └── Account/position monitoring
```

### NautilusTrader Crypto Results
- EURUSD forex: 112 tr, 77.7% WR — runner validated ✅
- BTCUSD: 3 tr, scale bug ($3600 move ÷ 0.01 pip = meaningless)
- ETHUSD: 0 trades — crypto needs separate calibration
- Fix: define crypto-specific pip sizes ($1/pip BTC, $0.10/pip ETH)

## Pending Questions for MAD
1. What broker for live trading? (IBKR? NT8? Both?)
2. If IBKR → build entire pipeline Python → ibapi
3. If NT8 → use NT8 REST API with similar architecture

## NT8 .cs Files Status
- 7/7 written (ST, P90, BacktestHarness, DeployConfig, TradeCopier, AssetPresets, CryptoAssetScanner)
- Can be imported via NT8 REST API instead of GUI

---
*Logged: 2026-05-31 21:45 EDT*
