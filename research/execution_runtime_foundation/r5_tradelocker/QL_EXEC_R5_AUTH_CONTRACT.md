# QL-EXEC-R5 — Auth Contract (TradeLockerAuthProvider)

## Flow

1. `authenticate()` — POST `/auth/jwt/token` with `{email, password, server}`
   resolved at call time from the injected `secret_provider` by reference name
   (`email_ref`, `password_ref`, `server`, optional `developer_api_key_ref`).
2. Every authed request uses `get_access_token()`:
   - no token → `authenticate()`;
   - access-token expiry (decoded from the JWT payload, no third-party JWT
     dependency) below 30 minutes → proactive refresh;
   - 401 from the server → **forced** refresh (server rejection is the only
     authoritative expiry signal; local JWT exp can look valid while the server
     revoked it) → single retry (401 means the request was NOT executed).

## Refresh singleflight

`refresh_access_token(force=False)` holds a refresh lock: concurrent callers
share ONE refresh. A caller that acquires the lock after a concurrent refresh
sees a fresh token and returns without hitting the endpoint. Test evidence:
6 threads → exactly 1 refresh (`test_05`).

## Secrets

- Never persisted in repo, DB, or logs. Credentials exist only as injected
  values (env-var style references) and fake test values.
- No token is logged; auth failures log status + truncated body.

## Failure semantics

- Bad credentials → `TradeLockerAuthError`, no fake success.
- Refresh failure → provider state degraded, `TradeLockerAuthError`; the
  session fails closed (`NOT_CONNECTED`-style path for new risk).

## Test evidence

`test_01..test_05` — success, failure, refresh, refresh-failure, singleflight.
