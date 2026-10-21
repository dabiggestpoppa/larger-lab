# Chapter 1.4 — Build/Borrow Spectrum

## 1.4.1 Purpose

QCAE must not collapse every investigation into a binary choice between "use the repo" and "build it ourselves."

Real capability acquisition spans a spectrum of ownership and coupling. The same external source may be best used as a direct dependency, wrapped behind an adapter, mined for a specification, selectively extracted, forked, vendored, or rejected while retaining architectural prior art.

This chapter defines the canonical acquisition outcomes and the conditions under which each is appropriate.

---

## 1.4.2 Governing Principle

> Choose the acquisition form that satisfies the capability contract with the least justified long-term burden.

The decision is not "open source good" versus "custom code good."

The decision is about ownership economics, reversibility, trust, maintenance, legal fit, and capability coverage.

---

## 1.4.3 Canonical Acquisition Outcomes

QCAE recognizes the following primary outcomes:

```text
USE_DIRECT
USE_DEPENDENCY
WRAP_LIBRARY
WRAP_SERVICE
FORK
VENDOR
EXTRACT_COMPONENT
EXTRACT_ALGORITHM
EXTRACT_SCHEMA
EXTRACT_TESTS
REIMPLEMENT_FROM_SPEC
REIMPLEMENT_FROM_PAPER
USE_AS_REFERENCE
USE_AS_ARCHITECTURAL_PRIOR
DEFER
REJECT
```

These are recommendation states. Promotion still requires the authority rules defined in Block 0.

---

## 1.4.4 USE_DIRECT

### Definition

Use the upstream artifact substantially as intended with minimal adaptation.

### Appropriate when

- the capability contract closely matches upstream behavior;
- the component is focused rather than framework-heavy;
- license is compatible;
- security surface is acceptable;
- dependency burden is justified;
- upstream maintenance quality is strong;
- Quant Lab does not need substantial behavioral divergence.

### Risk

Direct use can create hidden architectural dependence if upstream APIs spread throughout Quant Lab.

Therefore even `USE_DIRECT` should normally retain a bounded integration boundary where practical.

---

## 1.4.5 USE_DEPENDENCY

### Definition

Consume a versioned package as a standard dependency.

### Appropriate when

- packaging is mature;
- releases are reproducible;
- semantic/versioning discipline is acceptable;
- dependency supply chain is manageable;
- upstream API stability is adequate.

### Required records

- ecosystem;
- package name;
- exact accepted version/range;
- lock/digest information where available;
- transitive dependency surface;
- license state;
- reviewed upstream source revision when traceable.

---

## 1.4.6 WRAP_LIBRARY

### Definition

Use an external library behind a Quant Lab-owned interface.

### Default preference

For many acquisitions this should be preferred over exposing upstream APIs directly.

### Benefits

- containment;
- replaceability;
- testing against stable internal contracts;
- simpler future migration;
- reduced architectural contamination.

### Example

```text
Quant Lab Interface
      ↓
QCAE-approved adapter
      ↓
External Library
```

If the external library changes, only the adapter should ideally require modification.

---

## 1.4.7 WRAP_SERVICE

### Definition

Consume an external or separately deployed service behind a controlled interface.

### Appropriate when

- capability is operationally complex but well-served externally;
- local ownership cost is excessive;
- data/security policy permits service use;
- latency and availability constraints permit it;
- lock-in risk is understood.

### Additional concerns

- network failure;
- vendor availability;
- credential management;
- data egress;
- pricing drift;
- SLA dependence;
- API changes.

Service wrapping carries a higher governance burden than a local pure library when proprietary data is involved.

---

## 1.4.8 FORK

### Definition

Create an independently maintained descendant of upstream source.

### Fork only when

- direct upstream contribution is insufficient or impractical;
- required changes are material and persistent;
- upstream direction conflicts with Quant Lab needs;
- license permits the intended use;
- ownership benefit exceeds permanent merge and maintenance burden.

### Fork tax

Every fork creates a future responsibility:

```text
upstream tracking
security patch intake
conflict resolution
release management
license monitoring
internal maintenance
```

QCAE must price this tax explicitly.

---

## 1.4.9 VENDOR

### Definition

Copy a bounded third-party source component into Quant Lab's controlled source tree while preserving attribution, license, provenance, and reviewed version.

### Appropriate when

- component is small and stable;
- reproducible dependency retrieval is undesirable;
- supply-chain minimization is valuable;
- upstream churn is low;
- license permits vendoring.

### Danger

Vendored code can become invisible technical debt. It must remain linked to upstream provenance and monitoring rules.

---

## 1.4.10 EXTRACT_COMPONENT

### Definition

Acquire only the smallest reusable implementation unit from a larger source container.

This is a core QCAE outcome.

### Required questions

- Can the component legally be extracted?
- What internal dependencies must move with it?
- Does extraction preserve testability?
- Can the interface be stabilized?
- Is extraction cheaper than clean reimplementation?

### Example

A large execution framework contains a self-contained FIX parser. Quant Lab needs only the parser.

QCAE may recommend extracting or reproducing that component rather than adopting the execution framework.

---

## 1.4.11 EXTRACT_ALGORITHM

### Definition

Recover algorithmic logic independently of surrounding implementation architecture.

Possible sources:

- source code;
- paper;
- spec;
- tests;
- examples.

This can lead to a Quant Lab-native implementation when direct code adoption is undesirable.

Legal and provenance distinctions between idea, specification, and copyrighted expression must remain explicit; QCAE records evidence and routes ambiguous cases for review rather than making unsupported legal conclusions.

---

## 1.4.12 EXTRACT_SCHEMA

### Definition

Reuse a data model, message schema, registry schema, protocol shape, or ontology where appropriate.

This is particularly relevant to resources such as curated capability catalogs: the codebase itself may not be valuable, while its structured taxonomy is useful prior art.

Schema extraction should preserve attribution/provenance where required and still undergo compatibility review.

---

## 1.4.13 EXTRACT_TESTS

### Definition

Use upstream or reference tests as validation prior art without adopting the implementation.

This is highly valuable when reimplementing standards or protocols.

Tests can reveal:

- edge cases;
- expected semantics;
- compatibility requirements;
- hidden assumptions.

Upstream tests remain upstream-defined evidence; QCAE should supplement them with independent contract tests.

---

## 1.4.14 REIMPLEMENT_FROM_SPEC

### Definition

Build an independent Quant Lab implementation from a sufficiently clear public specification or standard.

### Appropriate when

- source implementation has incompatible architecture;
- license friction makes direct source reuse undesirable;
- dependencies are excessive;
- implementation quality is poor;
- Quant Lab needs tighter control;
- specification is stable and complete enough to reproduce behavior.

### Benefit

Preserves capability while reducing coupling.

### Cost

Transfers maintenance and correctness responsibility to Quant Lab.

---

## 1.4.15 REIMPLEMENT_FROM_PAPER

### Definition

Implement a method from research literature rather than adopting the reference repository.

Especially useful in quant research when:

- reference code is stale;
- implementation mixes research logic with experiment scaffolding;
- licensing is unclear;
- independent validation is required anyway.

A paper is not automatically a complete specification. Missing operational details must be treated as unresolved assumptions and tested.

---

## 1.4.16 USE_AS_REFERENCE

### Definition

Do not adopt code or runtime dependency, but retain the source as engineering reference material.

Useful when the implementation exposes:

- edge cases;
- naming conventions;
- API behavior;
- interoperability details;
- examples;
- benchmark ideas.

The capability graph should preserve this relationship so later work can rediscover the prior art.

---

## 1.4.17 USE_AS_ARCHITECTURAL_PRIOR

### Definition

Use the project as evidence that a system decomposition or architectural pattern exists, without importing its implementation.

This is appropriate when QCAE learns from:

- plugin layouts;
- registry structures;
- worker orchestration;
- sandbox models;
- event schemas;
- provenance systems.

Architectural prior art must not be mistaken for proof that the architecture fits Quant Lab.

---

## 1.4.18 DEFER

### Definition

Do not acquire now, but preserve candidate and evidence for future reevaluation.

Common reasons:

- contract priority is low;
- OCE integration dependency is unresolved;
- upstream is undergoing major rewrite;
- required data or hardware is unavailable;
- legal/security question is unresolved;
- internal alternative is good enough for now.

Deferred candidates should have explicit reactivation triggers.

---

## 1.4.19 REJECT

### Definition

Conclude that the candidate or acquisition path should not be pursued under the evaluated contract/revision.

Rejection reasons should be typed, for example:

```text
CAPABILITY_MISMATCH
LICENSE_INCOMPATIBLE
SECURITY_UNACCEPTABLE
DEPENDENCY_BURDEN
UNREPRODUCIBLE
PERFORMANCE_FAILURE
DOMAIN_VALIDATION_FAILURE
UPSTREAM_ABANDONED
INTERNAL_SUPERIOR
EXCESSIVE_LOCKIN
MAINTENANCE_COST
EVIDENCE_INSUFFICIENT
```

Rejected knowledge remains durable.

---

## 1.4.20 Mixed Acquisition

One capability may require more than one acquisition form.

Example:

```text
Protocol spec → REIMPLEMENT_FROM_SPEC
Reference test vectors → EXTRACT_TESTS
Upstream architecture → USE_AS_REFERENCE
Companion parser package → WRAP_LIBRARY
```

QCAE must support composite decisions rather than forcing one label per repository.

---

## 1.4.21 Acquisition Form Is Atom-Scoped

A repository can receive different outcomes for different atoms.

Example:

```text
Repo R
  Atom A → WRAP_LIBRARY
  Atom B → REIMPLEMENT_FROM_SPEC
  Atom C → REJECT
  Architecture → USE_AS_REFERENCE
```

This is another reason repository-level verdicts are too coarse.

---

## 1.4.22 Ownership Gradient

The spectrum can be understood as increasing ownership responsibility:

```text
External Service
    ↓
External Dependency
    ↓
Wrapped Dependency
    ↓
Vendored Component
    ↓
Fork
    ↓
Independent Reimplementation
    ↓
Fully Internal Capability
```

Increasing ownership may improve control while increasing maintenance responsibility.

QCAE should not assume either extreme is inherently superior.

---

## 1.4.23 Reversibility Gradient

QCAE must explicitly consider replacement cost.

High reversibility:

- narrow adapter;
- clean package boundary;
- stateless service abstraction.

Low reversibility:

- upstream types spread across internal code;
- external storage schema becomes canonical internal state;
- proprietary API semantics leak into business logic;
- fork diverges deeply from upstream.

Lower reversibility requires stronger justification.

---

## 1.4.24 Decision Record

Every acquisition recommendation should record:

```text
capability_atom
candidate
recommended_form
alternatives_considered
coverage
required_adapter
ownership_burden
lockin_risk
reversibility
license_status
security_status
maintenance_assessment
reason
revalidation_trigger
```

---

## 1.4.25 Failure Modes Prevented

This spectrum prevents:

- false build-vs-buy binaries;
- whole-repo adoption by default;
- missing specification-recovery opportunities;
- unnecessary forks;
- dependency sprawl;
- treating rejected codebases as worthless knowledge;
- architectural lock-in hidden inside convenience decisions.

---

## 1.4.26 Chapter Invariants

1. Acquisition outcomes are capability/atom scoped, not repository scoped.
2. Direct dependency is one option, not the default.
3. Forking carries explicit permanent maintenance tax.
4. Reimplementation is a valid acquisition outcome when evidence supports it.
5. Reference material and tests can be acquired conceptually without code adoption.
6. Mixed acquisition decisions are allowed.
7. Reversibility is part of acquisition quality.
8. Authority approval remains separate from QCAE recommendation.

---

## 1.4.27 Milestone Exit Criteria

Chapter 1.4 is complete when QCAE can represent a candidate outcome without forcing it into "use" or "reject," and can explain the ownership, coupling, provenance, and reversibility implications of the selected acquisition form.
