# Hyperliquid Funding Audit (DATA-1.1)

Correct: `{"type": "fundingHistory", "coin": "BTC", "startTime": <ms>}`
Incorrect (422): req wrapper, omitting startTime
Max 500/request, forward pagination, ~28K records May 2023-present
