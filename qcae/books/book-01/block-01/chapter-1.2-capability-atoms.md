# Chapter 1.2 — Capability Atoms

## 1.2.1 Purpose

A capability atom is the smallest independently meaningful behavior QCAE can discover, evaluate, acquire, replace, validate, or retire without requiring the rest of a repository or subsystem to move with it.

Atoms are the bridge between a high-level capability contract and real implementations.

The purpose of atomization is not maximal fragmentation. It is to expose real acquisition boundaries.

---

## 1.2.2 Atom Definition

A capability atom must have:

- a coherent behavior;
- identifiable inputs and outputs;
- an observable acceptance condition;
- an implementation boundary that can be located or represented;
- dependencies that can be described;
- independent acquisition value.

An atom does not have to be deployable by itself. It must be independently reasoned about.

---

## 1.2.3 Examples

A repository called `crypto-toolkit` may contain:

```text
transaction-decoding
address-normalization
wallet-label-resolution
address-clustering
graph-export
historical-state-reconstruction
```

QCAE should not store `crypto-toolkit` as a single capability.

Instead:

```text
Repository: crypto-toolkit
    ├── Atom: transaction-decoding
    ├── Atom: address-normalization
    ├── Atom: wallet-label-resolution
    ├── Atom: address-clustering
    ├── Atom: graph-export
    └── Atom: historical-state-reconstruction
```

A Quant Lab request may need only `transaction-decoding` and `historical-state-reconstruction`.

---

## 1.2.4 Why Atoms Matter

Capability atoms enable QCAE to:

- compare implementations across unrelated repositories;
- avoid importing unnecessary frameworks;
- recover useful pieces from weak projects;
- isolate license and dependency effects;
- detect duplicate internal capabilities;
- replace one implementation without replacing a system;
- build granular provenance;
- perform differential revalidation;
- construct accurate build-vs-borrow decisions.

---

## 1.2.5 Atomicity Tests

A proposed atom is probably too large if:

- separate behaviors have different input/output contracts;
- one part can fail while another remains useful;
- separate parts have different licenses or dependency surfaces;
- parts could be replaced independently;
- parts require separate domain validation;
- only some parts are needed by the parent capability.

A proposed atom is probably too small if:

- it has no independent acquisition value;
- it is merely an internal helper function with no meaningful behavioral boundary;
- it cannot be described without implementation-specific detail;
- its acceptance condition only makes sense as part of a larger behavior.

---

## 1.2.6 Atom vs Function

Not every function is a capability atom.

Example:

```text
_parse_int()
```

is normally an implementation detail.

But:

```text
FIX-message-decoding
```

may be a capability atom even if implemented by several classes and dozens of functions.

Atomicity is defined by useful behavior, not code size.

---

## 1.2.7 Atom vs Service

A service may implement one atom or many atoms.

A capability atom is conceptual and behavioral.

A service is one implementation or deployment form.

This distinction lets QCAE replace a service implementation without changing the capability identity.

---

## 1.2.8 Atom vs Feature

Features are often product-language descriptions.

Atoms require testable behavior.

Feature:

> advanced analytics

Not a useful atom.

Possible atoms:

- rolling covariance estimation;
- changepoint detection;
- volatility-regime classification;
- tail-risk estimation.

---

## 1.2.9 Atom Types

QCAE should support multiple atom classes.

### Computational atom

Transforms inputs to outputs.

Examples:

- covariance estimator;
- parser;
- clustering algorithm.

### Data atom

Provides or reconstructs a data capability.

Examples:

- historical tick normalization;
- corporate-action adjustment;
- wallet label resolution.

### Protocol atom

Implements a defined protocol or standard.

### Storage atom

Provides a storage/query behavior.

### Execution atom

Provides order-routing, scheduling, or execution behavior.

### Validation atom

Tests, scores, audits, or verifies another capability.

### Observability atom

Produces logs, metrics, traces, or lineage.

### Interface atom

Normalizes access across multiple implementations.

### Research atom

Implements a repeatable research method, estimator, or experimental procedure.

### Architecture atom

Represents a reusable design pattern that may be acquired as prior art rather than direct code.

---

## 1.2.10 Composite Capabilities

A larger capability may be represented as a composition of atoms.

Example:

```text
market-data-replay
    ├── event-normalization
    ├── sequence-ordering
    ├── book-state-transition
    ├── checkpoint-snapshot
    └── replay-clock
```

The parent capability contract describes the desired system behavior.

The atom graph exposes individual sourcing and validation boundaries.

---

## 1.2.11 Mandatory vs Optional Atoms

Composite capabilities may contain:

- required atoms;
- optional atoms;
- mutually exclusive atoms;
- alternative atoms;
- conditional atoms.

Example:

```text
historical-market-data
  REQUIRED:
    ingestion
    normalization
  OPTIONAL:
    compression
  ALTERNATIVE:
    parquet-storage OR timeseries-database-storage
```

This structure later helps the discovery planner search intelligently.

---

## 1.2.12 Implementation Multiplicity

One atom can be implemented by multiple candidates.

```text
Atom: changepoint-detection
    ├── Repo A / Component X
    ├── Repo B / Library Y
    ├── Paper C / Reference implementation
    └── Quant Lab internal implementation Z
```

The atom is the stable comparison object.

Implementations are candidates.

---

## 1.2.13 Multi-Atom Components

One component can implement several atoms.

QCAE should therefore use many-to-many relationships rather than forcing a one-component-one-capability schema.

Example:

```text
Component: orderbook-engine
implements:
  - book-state-transition
  - checkpoint-snapshot
  - replay-clock
```

If those behaviors cannot be cleanly isolated, QCAE records shared implementation coupling.

---

## 1.2.14 Atom Coupling

Atoms may be conceptually separate but operationally coupled.

QCAE should record coupling classes:

- none;
- weak;
- shared-library;
- shared-state;
- shared-runtime;
- shared-service;
- inseparable-in-current-implementation.

This prevents false assumptions that conceptual decomposition guarantees cheap extraction.

---

## 1.2.15 Extraction Boundary

For each candidate atom QCAE should attempt to locate:

```text
entry interface
implementation symbols
required internal modules
external dependencies
state dependencies
configuration
side effects
tests
runtime requirements
```

This becomes the preliminary extraction envelope.

---

## 1.2.16 Atom Provenance

An acquired atom may be:

- directly imported;
- adapted;
- vendored;
- extracted;
- reimplemented from specification;
- reimplemented from paper;
- inspired by architecture prior art;
- internally developed.

The atom's provenance must preserve the path from source to final implementation.

---

## 1.2.17 Atom Versioning

Capability behavior can evolve independently of implementation.

Example:

```text
CAP-ATOM-OB-STATE v1
L2 snapshot reconstruction

CAP-ATOM-OB-STATE v2
adds per-event deterministic replay
```

Implementation compatibility should be evaluated against atom versions.

---

## 1.2.18 Atom Equivalence

Two candidates may implement the same atom with different semantics.

QCAE must not assume naming equivalence implies behavioral equivalence.

Potential differences:

- precision;
- ordering guarantees;
- state persistence;
- edge-case handling;
- timezone assumptions;
- supported protocols;
- performance.

Equivalence requires contract-level comparison.

---

## 1.2.19 Atom Discovery from Repositories

Repository intelligence should answer:

1. What independently useful behaviors exist here?
2. Which are relevant to current contracts?
3. Which are reusable outside the repository's main application?
4. Which are tightly coupled?
5. Which reveal a specification or algorithm more useful than the code itself?

This lets QCAE discover unexpected capability inside repositories whose titles do not match the requirement.

---

## 1.2.20 Atom Discovery from Internal Quant Lab

QCAE should atomize internal systems too.

This enables questions such as:

> Which capability are we implementing three times?

> Which internal atom is superior to external alternatives?

> Which planned atom is already solved elsewhere?

The same ontology must represent internal and external capability.

---

## 1.2.21 Quant-Specific Atomization

Trading systems must not be stored as monolithic strategy capabilities when their components can be independently validated.

Possible atoms:

```text
signal-definition
feature-transform
regime-classifier
entry-rule
exit-rule
position-sizing
cost-model
execution-model
risk-kill-switch
```

This matters because an external strategy can contain a useful estimator while its claimed alpha is invalid.

QCAE should be capable of rejecting the strategy while acquiring the estimator.

---

## 1.2.22 Atom Record

A future machine-readable atom record should contain at least:

```text
atom_id
atom_version
name
type
description
parent_capabilities
inputs
outputs
state
acceptance_conditions
implementation_candidates
dependencies
coupling
security_class
domain
provenance
status
```

---

## 1.2.23 Decomposition Procedure

Canonical process:

```text
Capability Contract
      ↓
Identify independent behaviors
      ↓
Test replacement boundaries
      ↓
Test validation boundaries
      ↓
Test dependency boundaries
      ↓
Create candidate atoms
      ↓
Merge meaningless fragments
      ↓
Record composition + coupling
```

---

## 1.2.24 Failure Modes Prevented

Capability atoms prevent:

- whole-repo thinking;
- unnecessary dependency adoption;
- losing useful code inside rejected projects;
- conflating strategy validity with component validity;
- duplicate internal engineering;
- coarse monitoring that revalidates everything after any upstream change;
- inability to replace implementation layers.

---

## 1.2.25 Chapter Invariants

1. Atoms are behavioral, not code-size objects.
2. Atomization exposes acquisition boundaries; it does not maximize fragmentation.
3. Repositories and components may map many-to-many with atoms.
4. Conceptual independence does not imply implementation independence.
5. Coupling must be recorded.
6. Internal and external capabilities use the same atom model.
7. Strategy rejection does not automatically reject reusable non-alpha atoms.
8. Atom identity survives implementation replacement.

---

## 1.2.26 Milestone Exit Criteria

Chapter 1.2 is complete when QCAE can take a broad contract and represent:

- its meaningful component behaviors;
- their composition;
- their acquisition independence;
- their coupling;
- multiple implementations per atom;
- shared implementations across atoms;
- atom-level provenance and validation status.
