# Chapter 14.4 — Identity

## Mission

Provide stable identities for QCAE runtime instances, orchestrators, workers, users, and automated principals so evidence and authority decisions can be attributed without binding core logic to one authentication technology.

## Principal Classes

```text
human operator
qcae runtime
orchestrator
worker
scheduled monitor
integration service
```

## Identity Attributes

```text
principal_id
principal_type
runtime/session context
capabilities/roles
attestation/provider metadata
expiry/rotation state
```

## Standalone Identity

Before OCE, QCAE may use local runtime/worker identities sufficient for audit and local policy. These identities must be explicitly marked local and cannot masquerade as OCE-governed identities.

## OCE Identity

When connected, OCE-provided principal identities become the authority context for protected actions. Worker contracts continue to reference generic principal IDs.

## Delegation

The orchestrator may delegate bounded work to a worker, but the worker receives only the authority needed for that step. Delegation scope is explicit and traceable.

## Evidence Attribution

Every evidence envelope records the producing principal/runtime so later audit can distinguish model/tool/provider versions and execution contexts.

## Invariants

1. Every protected action is attributable to a principal.
2. Identity provider technology is abstracted.
3. Local identity is never presented as OCE authority.
4. Delegation is scoped and traceable.
5. Worker identity does not inherit full orchestrator authority.
6. Evidence remains attributable after provider migration.

## Exit Criteria

QCAE can migrate from local identities to OCE-governed principals without changing worker/domain schemas.
