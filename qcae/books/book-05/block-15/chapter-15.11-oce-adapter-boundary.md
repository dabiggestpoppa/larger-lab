# Chapter 15.11 — OCE Adapter Boundary

## Mission

Translate Block 14 governance contracts into concrete adapter packages without allowing OCE implementation details into QCAE domain/application layers.

## Adapter Modules

```text
governance/oce/authority.py
governance/oce/identity.py
governance/oce/evidence.py
governance/oce/events.py
governance/oce/registry.py
governance/oce/secrets.py
```

Exact filenames may change; adapter responsibility does not.

## Contract Tests

Each OCE adapter must pass the same abstract provider contract suite as standalone providers, plus OCE-specific transport/authentication tests.

## Translation Layer

Adapters own mapping between QCAE domain envelopes and OCE API/schema vocabulary. Mapping is versioned and observable.

## Failure Mapping

OCE transport/auth/policy failures are normalized into QCAE governance result types. Core workers never branch on vendor-specific HTTP/status details.

## Shadow Mode

Adapters support non-authoritative/shadow submission where OCE architecture permits, enabling policy-migration comparison before cutover.

## Feature Detection

If OCE lacks a capability required by the QCAE governance contract, adapter initialization reports explicit unsupported state rather than silently emulating broader authority.

## Invariants

1. OCE-specific code lives only in integration adapters.
2. Abstract provider contract tests apply to standalone and OCE implementations.
3. Schema/transport translation is versioned.
4. Provider-specific errors are normalized at the boundary.
5. Missing OCE functionality does not trigger permissive fallback.
6. Shadow/dual evaluation is supported for migration testing.

## Exit Criteria

The implementation agent has an exact place to wire finished OCE services later without touching QCAE core packages.
