# 22:40 EDT — MAD: Option A Confirmed (Tradovate REST API for Track A)

## MAD's Directive (#5884)
"Please do option a for track a use the rest api again look at the file if u have question if you still need clarity after ask me but please refer to the file gang"

**Option A = Tradovate REST API** (bypass NT8 GUI entirely)

## Architecture Confirmed
- Python CEREBUS engines (ST + P90) → truth source, unchanged
- New layer: Tradovate REST API client (orders) + WebSocket client (market data)
- Risk gate embedded at API layer: daily loss 0.40%, correlation cap, position sizing, 12PM hard exit
- Per-asset configs from asset_configs.py, no hardcoded forex values

## Items to Build (once credentials received)
1. `tradovate/rest_client.py` — REST client (auth, accounts, contracts, orders)
2. `tradovate/ws_client.py` — WebSocket client (market data, fills, order strategies)
3. `tradovate/executor.py` — bridges CEREBUS signals → Tradovate orders with risk gate

## Blocking Item
Need from MAD:
1. Tradovate email/login
2. API key (from account settings → API access)
3. Account ID (for order routing)

## Build Estimate
Once credentials received: 2-3 hours to build + test with paper trading

---
*Logged: 2026-05-31 22:40 EDT — Awaiting Tradovate API credentials from MAD*
