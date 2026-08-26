# Chapter 8.2 — Adapter-First Integration

## Mission

Place a Quant Lab-owned boundary between acquired capability and the rest of the system so upstream APIs, types, lifecycle, and churn do not spread through internal architecture.

## Adapter Contract

The adapter implements the Book II recovered internal interface and translates upstream inputs, outputs, errors, configuration, state, and lifecycle.

## Boundary Rules

- upstream-specific types stop at adapter;
- capability contract tests run against adapter;
- policy/telemetry hooks live outside candidate core where possible;
- version-specific quirks remain localized;
- no hidden global registration across Quant Lab.

## Thinness

Adapters should translate and isolate, not become a second implementation full of business logic. If substantial semantics move into the adapter, reassess the acquisition boundary.

## Multiple Implementations

The same internal interface should permit current internal, candidate, fork, and reimplementation variants where practical, enabling shadow comparison and exit.

## Invariants

1. Quant Lab owns the consuming interface.
2. Upstream types/lifecycle do not leak unnecessarily.
3. Contract tests target the owned boundary.
4. Adapters isolate churn rather than hide new business logic.
5. Implementation substitutability is preserved where practical.

## Exit Criteria

The capability can be consumed without making Quant Lab structurally dependent on the upstream API surface.
