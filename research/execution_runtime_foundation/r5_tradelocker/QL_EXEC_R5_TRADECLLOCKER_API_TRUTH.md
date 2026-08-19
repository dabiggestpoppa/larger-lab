# QL-EXEC-R5 — TradeLocker Official API Truth (frozen 2026-08-18)

Primary authority: official Public API reference (`https://public-api.tradelocker.com/`)
and the official Python client source
(`https://github.com/TradeLocker/tradelocker-python`,
`src/tradelocker/tradelocker_api.py`). Nothing in this file is coded from memory.

## Base URL

`{environment}/backend-api` — e.g. `https://demo.tradelocker.com/backend-api`.
Environment is part of the base URL; R5 code/config uses demo only.

## Auth

| Endpoint | Method | Notes |
|---|---|---|
| `/auth/jwt/token` | POST | body `{email, password, server}`; NO auth headers, NO accNum; returns `{accessToken, refreshToken}` at TOP level |
| `/auth/jwt/refresh` | POST | body `{refreshToken}`; returns new token pair |
| `/auth/jwt/all-accounts` | GET | Bearer token, NO accNum; returns accounts at TOP level (`{accounts:[{id, accNum, name, ...}]}`) |

Headers on authed requests: `Authorization: Bearer <jwt>`, `accNum: <str>`,
optional `developer-api-key`. Token refresh threshold in the official client:
30 minutes before access-token expiry.

## Config

- `GET /trade/config` → `{s, d: {ordersConfig:{columns:[{id}]}, positionsConfig,
  filledOrdersConfig, executionsConfig, accountDetailsConfig, instrumentsConfig,
  priceHistoryConfig, limits:[{limitType,limit}], rateLimits:[{rateLimitType,
  limit, seconds}]}}`
- Column layouts are DYNAMIC — resolved by `id`, never hardcoded index.

## Instruments / routes

- `GET /trade/accounts/{accountId}/instruments` → `{s, d:{instruments:[...]}}`
  with `tradableInstrumentId`, `name`, `id`, `routes:[{id, type}]`.
- Route types: `INFO` (market data), `TRADE` (execution). Route ids are
  provider-native truth, cached with account/instrument binding.

## Orders

- `GET /trade/accounts/{accountId}/orders` — non-final orders.
- `GET /trade/accounts/{accountId}/ordersHistory` — all orders (session).
- `POST /trade/accounts/{accountId}/orders` — body:
  `{price, qty (STRING), routeId, side (buy|sell), validity, tradableInstrumentId
  (STRING), type (market|limit|stop), takeProfit, takeProfitType, stopLoss,
  stopLossType, stopPrice, strategyId}` → `{s, d:{orderId}}`.
- `DELETE /trade/accounts/{accountId}/orders` — delete all (optional
  `tradableInstrumentId` filter); per-order delete by id.
- Validity: **market → IOC (mandatory)**; **limit/stop → GTC (mandatory)**.
  Market orders with a price: price is ignored (official client).
- `strategyId` max 32 chars.
- Order rows carry `status` (Pending/Filled/Rejected/...) and `positionId` once
  a position exists.

## Positions

- `GET /trade/accounts/{accountId}/positions` → `{s, d:{positions:[...]}}`.
- `DELETE /trade/accounts/{accountId}/positions` — close all (optional
  `tradableInstrumentId` filter).
- `DELETE /trade/positions/{positionId}` — body `{qty: STRING}`; qty=0 closes
  fully, qty>0 reduces by that amount (partial close). The official client
  attempts IOC then GTC closing order — **close request != closed truth**.

## Fills / history

- `GET /trade/accounts/{accountId}/executions` — fills in current session.
- `GET /trade/history?tradableInstrumentId=&routeId=&resolution=&from=&to=`
  → `{s, d:{barDetails:[[t,o,h,l,c,v],...]}}`; capped by `QUOTES_HISTORY_BARS`
  limit from `/config`.

## Quotes (INFO route)

- `GET /trade/quotes?tradableInstrumentId=&routeId=` → `{s, d:{bp, ap,
  serverTime}}`.

## Critical semantics implemented in R5

1. **orderId != positionId** — submit returns the order id; a position only
   exists when positions truth says so.
2. **Accepted order != filled position** — market orders are IOC (immediate
   fill), limit/stop are pending.
3. **Close request != closed truth** — must confirm via positions.
4. **No blind retry** — ambiguous POST is reconciled, never resent.
