# 22:33 EDT — TRADOVATE API DISCOVERY

## MAD's Message
Sent Tradovate API docs link: https://api.tradovate.com/#section/Getting-Started-With-the-Tradovate-API

## Research: Tradovate API Capabilities
- REST API: auth, accounts, order placement (market/limit), positions, contracts
- WebSocket: market data streaming, fill events, order strategy commands
- **Orders-only mode:** "allow sending orders with no Market data subscriptions" — use our own MT5 CSV data
- Multi-bracket strategies via WebSocket: entry + TP + SL in one call
- API access: free with Tradovate account (enable API key in settings)
- CME data subscription NOT needed if using external data feed

## New Proposed Architecture
```
CEREBUS Python Engines (ST + P90)
    ↓ signals
tradovate_api.py + tradovate_ws.py + tradovate_executor.py
    ↓ HTTPS / WSS
TRADOVATE API
    ↓
Prop firm execution
```

NT8 .cs files become FALLBACK, not primary path.

## MAD's Feedback on Previous Work
- Reiterated: don't research IBKR, don't use CLI-Anything, stop drifting
- Tradovate API is THE answer for bypassing GUI

## Pending
- MAD to provide: Tradovate email + API key
- MAD to confirm: Tradovate API replaces NT8 as primary execution path?
- Build: tradovate_api.py, tradovate_ws.py, tradovate_executor.py (2-3 files)

---
*Logged: 2026-05-31 22:33 EDT*
