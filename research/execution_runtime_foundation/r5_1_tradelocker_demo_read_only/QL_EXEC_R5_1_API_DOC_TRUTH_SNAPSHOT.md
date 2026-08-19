# QL-EXEC-R5.1 — Official TradeLocker API Truth Snapshot

**Retrieval date:** 2026-08-19
**Sources:** official TradeLocker Public API documentation
(`https://public-api.tradelocker.com/`) and the official
`tradelocker-python` client source
(`src/tradelocker/tradelocker_api.py`, `main` branch).
**Drift vs R5 assumptions:** `NONE_DETECTED`.

## Frozen truth used by the R5.1 read-only audit

| Concern | Frozen truth |
|---|---|
| Base URL | `{environment}/backend-api` — demo = `https://demo.tradelocker.com/backend-api` |
| Auth | `POST /auth/jwt/token` with `{email, password, server}` → `{accessToken, refreshToken}` (top-level) |
| Refresh | `POST /auth/jwt/refresh` with `{refreshToken}` → new token pair |
| Account discovery | `GET /auth/jwt/all-accounts` → `{accounts: [{id, accNum, name, ...}]}` — `accountId` and `accNum` are distinct native fields |
| Headers | `Authorization: Bearer <jwt>`; `accNum` header for account binding; optional `developer-api-key` |
| Config | `GET /trade/config` → `d.{object}Config.columns[{id}]`; `d.limits`; `d.rateLimits[{rateLimitType, limit, seconds}]` — column indexes are DYNAMIC, never hardcoded |
| Instruments | `GET /trade/accounts/{id}/instruments` → rows carry `tradableInstrumentId`, `name`, `routes[{id, type}]` with `INFO` and `TRADE` route types |
| Quotes | `GET /trade/quotes?tradableInstrumentId=&routeId=` (INFO route) → `d.{bp, ap, serverTime}` |
| History | `GET /trade/history?tradableInstrumentId=&routeId=&resolution=&from=&to=` → `d.barDetails` |
| Account state | `GET /trade/accounts/{id}/state` → `d.accountDetailsData` (value-array aligned to `accountDetailsConfig`) |
| Positions | `GET /trade/accounts/{id}/positions` → `d.positions` |
| Orders | `GET /trade/accounts/{id}/orders` (non-final), `GET /trade/accounts/{id}/ordersHistory` |
| Fills | `GET /trade/accounts/{id}/executions` → `d.executions` (orderId and positionId distinct) |
| Place order | `POST /trade/accounts/{id}/orders` body `{price, qty (string), routeId, side, validity, tradableInstrumentId, type, stopPrice, strategyId, stopLoss, takeProfit, ...}` |
| Validity | market orders = `IOC`; limit/stop orders = `GTC` (adapter-owned mapping) |
| Close | `DELETE /trade/positions/{positionId}` with `{qty}` (0 = full) — places a closing ORDER (IOC then GTC); close request != closed truth |
| Cancel | `DELETE /trade/accounts/{id}/orders/{orderId}`; `DELETE /trade/accounts/{id}/orders` (all) |
| Identity | `orderId` ≠ `positionId`; accepted order ≠ filled position; `strategyId` ≤ 32 chars; min lot 0.01; qty as string |

## How the audit consumes this truth

- Column resolution: `TradeLockerConfigParser` builds a version-hashed snapshot
  from `/config`; every positions/orders/executions/state row is resolved by
  column id — config drift is a visible hash bump.
- Routes: INFO route for market data, TRADE route for execution; resolved per
  instrument from the instruments payload, never invented.
- Timestamps: provider `serverTime` is preserved as source truth (clock audit
  compares it to local UTC; local time never substitutes for broker time).
- Identity: `orderId` and `positionId` are kept separate in the normalized
  fills (`executions`), matching provider truth.
