# Chapter 16.2 — Contract Tests

## Mission

Prove that every provider/adaptor implementation obeys the stable QCAE interface it claims to implement.

## Contract Suites

Shared suites should cover:

```text
DiscoveryProvider
RepositoryComprehensionProvider
AuthorityProvider
IdentityProvider
SecretProvider
EvidenceSink
Registry/Persistence ports
SandboxBackend
MarketData/Backtest adapters
GovernanceEventSink
```

Standalone, fake, and future OCE/provider implementations run the same abstract behavior tests.

## Required Behaviors

Test success, partial result, malformed provider output, timeout, unavailability, idempotency, authorization denial, stale input, and version incompatibility.

Provider-specific features may add tests but cannot weaken the common contract.

## Compatibility

Schema/interface version changes require explicit compatibility tests and migrations rather than silent breakage.

## Invariants

1. Provider replacement is proven, not assumed.
2. Fake providers and real providers share behavioral contract tests.
3. Failure semantics are first-class.
4. Provider-specific convenience cannot redefine QCAE semantics.
5. Version compatibility is explicit.

## Exit Criteria

GitHub, DeepWiki, local/OCE governance, storage, sandbox, and quant-engine adapters can be swapped without changing the application contract.
