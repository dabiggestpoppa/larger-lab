# Chapter 14.3 — Authority Requests

## Mission

Define how QCAE requests permission for protected actions without embedding OCE policy logic into workers.

## Request Envelope

```text
request_id
principal/worker identity
action
resource/capability
purpose
requested scope
duration if applicable
contract/lifecycle state
evidence envelope refs
risk/data class
requested constraints
```

## Decision Envelope

```text
decision_id
ALLOW / DENY / REQUIRE_APPROVAL / ALLOW_WITH_CONSTRAINTS
scope
constraints
expiry
policy rule refs
required follow-up
reason
```

## Examples

Protected requests may include:

- persist vendor/fork integration;
- access confidential data class;
- use external service with private source;
- write to protected repository/environment;
- obtain production-class secret;
- promote capability to governed use;
- enable trading/capital authority.

## No Authority Caching Beyond Scope

A prior `ALLOW` may be reused only within its explicit action/resource/scope/expiry. Broad conversational permission is not a durable authority token.

## Replay Protection

Requests/decisions should use stable identities and expiry/idempotency semantics so stale grants cannot be replayed for different actions.

## Invariants

1. Protected authority is requested explicitly.
2. Evidence accompanies authority requests.
3. Decisions are scoped and expiring where appropriate.
4. Prior approval cannot be generalized to new actions.
5. Workers consume decisions but do not implement OCE policy themselves.
6. Denial/ambiguity never becomes implicit local fallback.

## Exit Criteria

QCAE can ask OCE for narrowly scoped authority while remaining ignorant of OCE's internal policy engine implementation.
