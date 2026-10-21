# Chapter 4.3 — Interface Recovery

## Mission

Recover the narrowest stable interface Quant Lab needs to consume the capability without inheriting unnecessary upstream types or lifecycle semantics.

## 4.3.1 Interface Layers

Distinguish:

```text
upstream public API
actual capability boundary
host-framework boundary
proposed Quant Lab adapter interface
```

These may be different.

## 4.3.2 Interface Elements

Recover:

- operations/methods;
- input/output types;
- state ownership;
- lifecycle;
- concurrency assumptions;
- error model;
- configuration;
- callbacks/events;
- serialization/protocol rules.

## 4.3.3 Type Leakage

Flag upstream-specific types that would spread into Quant Lab. Prefer translation at adapter boundaries when cost is justified.

## 4.3.4 Error Semantics

Error behavior is part of capability semantics. Recover exceptions/status codes/retryability/failure states rather than exposing arbitrary upstream failures directly.

## 4.3.5 Lifecycle Semantics

Identify initialization, teardown, persistence, thread/process ownership, connection management, and resource cleanup.

## 4.3.6 Proposed Internal Contract

The forensic package should propose an implementation-independent Quant Lab-facing interface when feasible.

This is a design proposal subject to later implementation review, not an authority decision.

## 4.3.7 Interface Compatibility Tests

Recovered interface semantics should be convertible into contract tests so multiple implementations can be compared behind the same boundary.

## Invariants

1. Upstream API is not automatically the desired internal interface.
2. Type leakage and lifecycle capture are minimized.
3. Error semantics are explicit.
4. State/resource ownership is explicit.
5. Proposed interfaces remain implementation-independent where practical.

## Exit Criteria

QCAE can define how Quant Lab should talk to the capability without forcing the rest of Quant Lab to speak the upstream framework's language.
