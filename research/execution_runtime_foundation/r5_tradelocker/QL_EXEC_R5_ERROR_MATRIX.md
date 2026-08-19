# QL-EXEC-R5 — Error Matrix

| Failure | Behavior | Test |
|---|---|---|
| 401 expired token | forced refresh → single safe retry | `test_35` |
| 401 refresh failure | `TradeLockerAuthError`; fail closed | `test_04` |
| 403 permission | `TRANSPORT_ERROR`; no retry of write | `test_36` |
| 404 bad account/instrument | cancel/close → `INVALID_REQUEST` | `test_37` |
| 429 rate limit | `Retry-After` honored, bounded; then `TradeLockerRateLimitExceeded` | `test_15`, `test_16` |
| 5xx provider error | `TRANSPORT_ERROR`; no blind write retry | `test_38` |
| network timeout pre-send | `TRANSPORT_ERROR` (nothing sent) | `test_32` |
| network timeout ambiguous send | `TRANSPORT_ERROR` + reconcile-before-retry | `test_33`, `test_34` |
| malformed JSON | `TradeLockerApiError`; reads fail soft, writes fail closed | `test_39` |
| schema drift (config) | version hash changes → drift detected | `test_40` |
| route-id drift | stale cached route rejected; fails closed | `test_41` |
| order rejected by provider | `ORDER_REJECTED` (400 s:error) | `test_31` |
| refresh failure (degraded) | no new risk | `test_04` |

Write-method rule: POST/DELETE transport failures are NEVER retried by the
client — the request may have reached the provider; reconcile first.
