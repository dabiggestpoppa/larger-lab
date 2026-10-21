# Chapter 15.2 — Core Domain Boundaries

## Mission

Define which objects and rules belong to QCAE's stable domain so infrastructure/provider choices cannot silently rewrite system semantics.

## Core Domain Objects

```text
CapabilityContract
CapabilityAtom
CompositeCapability
Relationship
Candidate
Evaluation
EvidenceRef
LifecycleState
AcquisitionDecision
CapabilityReceipt
AuthorityRequest/Decision interfaces
Job/Step state contracts
```

## Core Rules

Core owns:

- contract/atom identity and versioning;
- lifecycle transition legality;
- acquisition outcome vocabulary;
- evidence/verification state semantics;
- hard-gate representation;
- Capability Conservation semantics;
- provenance relationships.

## Forbidden Dependencies

`core/` must not depend directly on:

```text
GitHub SDKs
DeepWiki clients
LLM provider SDKs
Docker/Kubernetes clients
database engines
web frameworks
OCE implementation packages
backtest engines
```

Those implement ports used by higher layers.

## Service Layer

Application/orchestration services compose domain objects with provider interfaces. They may depend on core and abstract ports; adapters depend on provider SDKs.

## Domain Validation

Invalid state transitions or malformed core objects fail before provider execution.

## Invariants

1. Core semantics are infrastructure-independent.
2. Provider SDKs never enter core.
3. Lifecycle rules are centralized and testable.
4. Adapters cannot invent new verification states or acquisition forms ad hoc.
5. Domain objects are serializable/versioned for persistence/handoffs.

## Exit Criteria

The coding agent can draw a hard dependency line around QCAE's stable semantics and protect them from vendor/runtime drift.
