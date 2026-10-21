# Chapter 13.4 — Local Secrets Boundary

## Mission

Provide standalone QCAE with a minimal, explicit secret-access layer that preserves Block 5's least-authority rules and can later be replaced by OCE-managed identity/secrets services.

## Principles

- no worker reads host-wide secret stores directly;
- secrets are requested by class/purpose, not raw path;
- production trading credentials are outside ordinary QCAE proving authority;
- test credentials are scoped, disposable, and revocable;
- raw secret values never enter evidence artifacts or model prompts unless absolutely required by the approved tool boundary.

## Secret Provider Contract

Conceptual interface:

```text
request_secret(secret_class, purpose, scope, ttl, worker_id)
→ DENY / REQUIRE_APPROVAL / secret_handle
```

Workers should receive handles/injected environment where possible rather than persistent plaintext.

## Local Implementation

Initial local implementation may use OS keychain, encrypted local store, environment injection, or another approved mechanism. The domain contract must remain provider-neutral.

## Rotation/Revocation

Every non-static test identity should define expiration and revocation. Failed or suspicious runs can trigger immediate revocation.

## Audit

Record who/what requested which secret class, purpose, scope, policy decision, and whether access was granted—never the raw value.

## Invariants

1. Secret access is mediated by a provider contract.
2. Workers never inherit broad host credentials by default.
3. Production trading secrets remain outside proving authority.
4. Test secrets are least-privileged and revocable.
5. Raw secret values are excluded from evidence/logging.
6. Local implementation can later be replaced by OCE without changing worker contracts.

## Exit Criteria

Standalone QCAE can use necessary test credentials without turning the host environment into an implicit authority source.
