# Chapter 1.3 — Capability Graph

## 1.3.1 Purpose

The capability graph is QCAE's durable relationship model. It connects needs, capability atoms, implementations, repositories, specifications, tests, datasets, dependencies, interfaces, decisions, and provenance.

A flat repository table cannot answer the questions QCAE eventually needs to ask:

- Which internal capability already satisfies 70% of this new contract?
- Which external implementations provide the same atom?
- Which accepted capabilities depend on a vulnerable package?
- Which rejected project revealed a useful specification?
- Which acquired implementation is superseded by a better candidate?
- Which tests must rerun after a component changes?

The graph exists to make those relationships explicit and queryable.

---

## 1.3.2 Graph Principle

> Store entities separately from relationships.

A repository is not a capability.

A component is not a repository.

A test is not evidence by itself until linked to a run and revision.

A paper is not an implementation.

QCAE must preserve those distinctions.

---

## 1.3.3 Core Entity Classes

The initial ontology should include at least:

### Need

A raw or normalized Quant Lab problem statement.

### Capability Contract

The versioned desired behavior.

### Capability Atom

The smallest independently meaningful acquisition behavior.

### Composite Capability

A capability composed of atoms.

### Implementation Candidate

A particular implementation proposed to satisfy an atom or capability.

### Component

A concrete source/code/runtime unit within an implementation.

### Repository

A source container and history boundary.

### Package

A versioned distributable dependency.

### Service

An externally or locally addressable runtime dependency.

### Specification

A normative or descriptive definition from which behavior may be recovered.

### Paper / Research Source

Research prior art, method description, empirical claim, or derivation.

### Interface

A boundary through which a capability is exposed.

### Dataset

A versioned data artifact relevant to proof or operation.

### Test Definition

A test specification.

### Test Run

An observed execution of a test definition under recorded conditions.

### Benchmark Run

Measured performance evidence.

### Evidence Artifact

A hashable source/runtime/test/report artifact.

### Acquisition Decision

Approved, rejected, deferred, or other terminal recommendation/authority result.

### Integration

A Quant Lab binding between capability and implementation.

### Policy Decision

Standalone or OCE-issued authority result.

### Vulnerability / Risk Finding

A security, operational, legal, or domain-risk object.

---

## 1.3.4 Canonical Relationship Vocabulary

QCAE should use a controlled relationship vocabulary rather than arbitrary prose.

Initial relationships:

```text
requested_by
normalized_as
composed_of
implements
partially_implements
contained_in
exposed_through
depends_on
optional_dependency_on
conflicts_with
substitutes_for
extends
supersedes
wraps
vendors
forked_from
extracted_from
derived_from
specified_by
described_by
validated_by
tested_by
benchmarked_by
observed_in
requires_data
produces_data
compatible_with
incompatible_with
integrated_as
approved_by
rejected_by
triggered_revalidation_of
```

The implementation books may refine naming, but semantic meaning should remain stable.

---

## 1.3.5 Direction Matters

Relationships should have defined direction.

Example:

```text
CapabilityAtom --implemented_by--> Component
Component --contained_in--> Repository
Component --depends_on--> Package
```

Avoid ambiguous symmetric edges unless the relationship is genuinely symmetric.

---

## 1.3.6 Evidence-Scoped Relationships

Some relationships are factual and revision-scoped.

Example:

> Component X implements Atom Y.

This should include context such as:

- reviewed commit;
- confidence/evidence class;
- source symbols;
- verification status.

QCAE must be able to distinguish:

```text
CLAIMED_IMPLEMENTATION
```

from:

```text
CODE_VERIFIED_IMPLEMENTATION
```

and:

```text
CONTRACT_VERIFIED_IMPLEMENTATION
```

---

## 1.3.7 Capability Coverage Edges

An implementation may satisfy only part of a contract.

Coverage should be represented granularly.

Example:

```text
Candidate A
  implements atom-1 fully
  implements atom-2 partially
  does not implement atom-3
```

This allows QCAE to compose acquisitions rather than searching endlessly for one perfect repository.

---

## 1.3.8 Dependency Graph as Subgraph

Dependencies are not merely package lists.

QCAE should represent:

```text
Component
  ↓ depends_on
Package
  ↓ depends_on
Package

Component
  ↓ requires
Service

Component
  ↓ reads
Dataset
```

Dependency edges should support attributes such as:

- required/optional;
- runtime/build/test-only;
- version constraint;
- network requirement;
- license;
- vulnerability state;
- replaceability.

---

## 1.3.9 Provenance Graph

Every acquired capability should have a reconstructable lineage.

Example:

```text
Paper P
   ↓ described_by
Specification S
   ↓ reference_implemented_by
Repository R / Component C
   ↓ inspired
Quant Lab Implementation Q
   ↓ integrated_as
Capability Atom A
```

This matters especially when QCAE reimplements instead of directly adopts.

---

## 1.3.10 Decision Graph

QCAE should preserve not only what was chosen but the alternatives considered.

```text
Capability Contract
   ├── Candidate A → REJECTED: license friction
   ├── Candidate B → REJECTED: dependency burden
   ├── Candidate C → ACCEPTED: extracted component
   └── Internal D → retained for fallback
```

This creates durable engineering memory.

---

## 1.3.11 Negative Knowledge Graph

Rejected candidates remain connected to the capability and rejection evidence.

Future discovery should query this graph before re-investigating.

If the candidate changed materially, QCAE may create a new evaluation against the new revision rather than overwrite the old rejection.

---

## 1.3.12 Time and Revision

The graph is temporal.

A relationship may be true only for a revision range.

Example:

```text
Repository R @ commit A
implements Atom X

Repository R @ commit B
no longer exposes compatible interface
```

QCAE should avoid pretending the latest state retroactively changes historical evidence.

---

## 1.3.13 Confidence and Verification State

Graph edges that originate from analysis should support verification state.

Example levels:

```text
DISCOVERED
DOCUMENTED
SOURCE_LOCATED
CODE_VERIFIED
RUNTIME_VERIFIED
CONTRACT_VERIFIED
DOMAIN_VERIFIED
```

This keeps hypotheses and proven relationships inside one graph without conflating them.

---

## 1.3.14 Graph Queries QCAE Must Eventually Support

Examples:

```text
Find all verified implementations of capability atom X.

Find all accepted capabilities transitively dependent on package Y.

Find rejected candidates for contract family Z and their reasons.

Find all atoms implemented by repository R.

Find all capabilities affected by license change in dependency D.

Find all internal components substitutable by accepted external implementations.

Find all capability atoms whose evidence is older than their upstream revision.

Find all strategy components whose execution model has never been domain validated.
```

If the ontology cannot support these queries cleanly, it is too weak.

---

## 1.3.15 Graph Storage Strategy

The conceptual model is graph-shaped, but the first implementation does not require a graph database.

Block 0 already favors a structured machine-readable spine. Early storage may use relational/DuckDB/Parquet tables such as:

```text
capabilities
atoms
repositories
components
implementations
dependencies
evaluations
evidence
relationships
```

The key requirement is preserving normalized entities and typed edges.

QCAE should not introduce graph-database operational burden unless graph-specific capability later justifies it under Capability Conservation.

---

## 1.3.16 Stable IDs

Entity identity should not depend on display name.

QCAE should use stable internal IDs for:

- capabilities;
- atoms;
- evaluations;
- source snapshots;
- evidence packages;
- integrations.

External identifiers such as GitHub URLs and package coordinates remain attributes.

---

## 1.3.17 Merge and Deduplication

Discovery may find the same implementation through multiple sources.

QCAE needs deduplication rules based on canonical source identity:

- repository owner/name + immutable commit;
- package ecosystem/name/version/digest;
- paper DOI/arXiv ID;
- service identity;
- internal repository path + commit.

Duplicate discovery records should merge into one entity while preserving all discovery paths.

---

## 1.3.18 Entity Resolution

Different names may represent the same capability.

Example:

```text
structural break detector
changepoint detector
regime boundary detector
```

QCAE should allow aliasing and semantic linkage without prematurely declaring exact equivalence.

Capability equivalence is a behavioral conclusion, not a text-matching conclusion.

---

## 1.3.19 OCE Integration Implication

The graph should be designed so future OCE can govern entities and transitions without owning QCAE's semantic reasoning.

QCAE produces:

- capability entities;
- evidence entities;
- relationship assertions;
- promotion requests.

OCE later attaches:

- identity;
- authority;
- policy decisions;
- governance state.

This keeps the integration boundary clean.

---

## 1.3.20 Failure Modes Prevented

The capability graph prevents:

- repository-centric memory;
- duplicate evaluations;
- lost provenance;
- opaque dependency exposure;
- inability to calculate blast radius;
- overwriting historical decisions;
- confusing claims with verified relationships;
- revalidating entire systems when one component changes;
- losing useful specifications from rejected codebases.

---

## 1.3.21 Chapter Invariants

1. Entities and relationships are separate.
2. Relationships use a controlled vocabulary.
3. Evidence-backed and claimed edges are distinguishable.
4. Graph history is revision-scoped.
5. Negative knowledge remains connected to capability context.
6. Internal and external implementations coexist in the same graph.
7. Graph-shaped semantics do not force a graph database.
8. Provenance must remain reconstructable after implementation replacement.

---

## 1.3.22 Milestone Exit Criteria

Chapter 1.3 is complete when the ontology can represent:

- contracts composed of atoms;
- multiple implementations per atom;
- components inside repositories;
- direct and transitive dependencies;
- specifications and research prior art;
- test/evidence relationships;
- rejected alternatives;
- historical revisions;
- future OCE authority attachments.
