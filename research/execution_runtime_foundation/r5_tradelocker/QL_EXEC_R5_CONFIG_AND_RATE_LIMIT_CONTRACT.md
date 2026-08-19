# QL-EXEC-R5 — Config & Rate-Limit Contract

## `/config` snapshot

- `TradeLockerConfigSnapshot` holds dynamic column ids (ordersConfig,
  ordersHistoryConfig, positionsConfig, filledOrdersConfig, executionsConfig,
  accountDetailsConfig, instrumentsConfig, priceHistoryConfig), `limits`, and
  `rateLimits`.
- Column positions are NEVER hardcoded: positions/orders/executions rows arrive
  as value-arrays and are resolved by column id from the snapshot.
- The snapshot is version-hashed (`cfg_<sha256[:16]>`); any semantic config
  change is a visible version bump → config-drift detection.

## Rate limiting

- `TradeLockerRateLimiter` enforces global + per-route windows from `/config`
  `rateLimits` truth.
- 429 → honor `Retry-After`; bounded attempts (max 3 total) then
  `TradeLockerRateLimitExceeded`. Never infinite retry.
- Bounded exponential backoff on transport/5xx failures (cap 60s), reset on
  success.
- Order POST retry policy is EXTRA conservative: the limiter only gates when a
  request may be attempted; it never decides retry safety. Ambiguous sends are
  never retried (reconcile first).

## Tests

- `test_12` config parsing + stable hash.
- `test_14` rate-limit parsing.
- `test_15` enforcement (10/60s window → exceeded).
- `test_16` bounded 429 backoff.
- `test_40` config drift → different version hash.
- `test_41` route-id drift fails closed.
