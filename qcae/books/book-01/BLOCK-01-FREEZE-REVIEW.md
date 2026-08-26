# QCAE Book I — Block 1 Freeze Review

**Block:** Capability Model  
**Canon:** QCAE v0.1  
**Review result:** READY TO FREEZE  

## 1. Review Objective

Confirm that Chapters 1.1–1.6 form one coherent capability model and that later QCAE books can consume the model without redefining core terms.

## 2. Chapter Dependency Chain

The chapters intentionally build in this order:

```text
1.1 Capability Contracts
        ↓ defines the need
1.2 Capability Atoms
        ↓ decomposes the need
1.3 Capability Graph
        ↓ relates needs, atoms, implementations, evidence, and dependencies
1.4 Build/Borrow Spectrum
        ↓ defines legal acquisition outcomes
1.5 Capability Value Model
        ↓ compares outcomes and ownership burden
1.6 Anti-Framework Bias
        ↓ constrains architecture capture and applies Capability Conservation
```

No chapter requires repository-centric identity.

## 3. Canonical Terms Frozen by Block 1

### Capability Contract
A versioned, implementation-independent statement of required behavior, constraints, and acceptance evidence.

### Capability Atom
The smallest independently meaningful behavior that can be discovered, evaluated, acquired, replaced, validated, or retired.

### Composite Capability
A capability composed of atoms whose composition and coupling are explicitly represented.

### Implementation Candidate
A concrete possible implementation of one or more capability atoms.

### Capability Graph
The typed, revision-scoped relationship model connecting contracts, atoms, implementations, components, repositories, specs, dependencies, evidence, decisions, and integrations.

### Acquisition Form
The selected ownership/integration path such as dependency use, wrapping, extraction, vendoring, forking, reimplementation, reference use, deferral, or rejection.

### Capability Value
Contract-specific benefit supported by evidence and considered against full system burden.

### Capability Conservation
The constitutional requirement that Net Capability Gain exceed New System Burden.

### Anti-Framework Bias
The rule that whole-framework adoption carries a burden of proof and smaller independently useful capability boundaries are preferred when they satisfy the contract.

## 4. Cross-Chapter Coherence Checks

### Contract identity vs implementation identity
PASS. Capability identity remains independent of repository/package/service identity.

### Decomposition vs over-fragmentation
PASS. Atomization is behavioral and acquisition-driven, not function-level fragmentation.

### Graph vs storage technology
PASS. Graph semantics are frozen without requiring a graph database. DuckDB/Parquet remains viable for the first implementation.

### Acquisition taxonomy vs authority
PASS. Acquisition outcome is a QCAE recommendation; approval authority remains separated under Block 0.

### Value model vs hard safety gates
PASS. Security, license, capability mismatch, and required domain failures cannot be averaged away by aggregate scoring.

### Anti-framework bias vs anti-dependency extremism
PASS. Focused mature dependencies remain valid and may be preferable to internal reimplementation.

### Quant-specific behavior
PASS. Strategy-level rejection does not automatically reject reusable non-alpha atoms. Claimed financial performance cannot count as verified value without domain validation.

### OCE compatibility
PASS. Capability/evidence semantics are independent from final authority implementation. OCE can later attach governance without redefining QCAE core objects.

## 5. Required Machine-Readable Objects Implied by Book I

Later implementation books must provide schemas for at least:

```text
CapabilityContract
CapabilityAtom
CompositeCapability
ImplementationCandidate
Component
RepositoryRef
SpecificationRef
DependencyRef
Relationship
CandidateEvaluation
AcquisitionDecision
EvidenceRef
IntegrationRef
```

Block 1 intentionally specifies semantics before serialization format.

## 6. Discovery Requirements Implied for Book II

Book II must be able to consume a frozen contract and atom model and produce candidate graph assertions without changing the requirement.

Discovery must therefore support:

- internal-first lookup;
- atom-level external search;
- multiple discovery hypotheses per atom;
- candidate deduplication;
- source identity;
- claimed vs verified relationship states;
- prior rejection lookup;
- specification/paper discovery;
- DeepWiki-assisted repository comprehension without treating model output as evidence.

## 7. Proving Requirements Implied for Book III

Book III must validate candidate implementations against the acceptance conditions defined by contracts/atoms rather than against repository claims.

It must preserve:

- hard gates;
- evidence classes;
- sandbox isolation;
- independent tests;
- quant-domain validation where applicable;
- license/security constraints;
- revision-scoped proof.

## 8. Acquisition Requirements Implied for Book IV

Book IV must preserve the full acquisition spectrum rather than flattening decisions to ACCEPT/REJECT.

It must also persist:

- rejected candidates;
- alternative acquisition forms;
- provenance;
- ownership burden;
- revalidation triggers;
- supersession relationships.

## 9. Agent Architecture Requirements Implied for Book V

Workers must exchange typed capability/evidence artifacts instead of only prose.

No worker may silently mutate a capability contract because it discovered a convenient candidate.

The orchestrator may propose an amendment, but contract revisions must be explicit and versioned.

## 10. Qualification Requirements Implied for Book VI

QCAE itself must eventually be tested against benchmark tasks where correct acquisition behavior is known, including cases designed to expose:

- repository popularity bias;
- framework capture;
- false equivalence between similarly named capabilities;
- hidden transitive dependencies;
- unsafe service/data egress;
- misleading quant claims;
- repeated investigation of previously rejected candidates.

## 11. Block 1 Freeze Invariants

1. Capability identity is independent of implementation identity.
2. Every meaningful acquisition begins from a versioned contract.
3. Capability atoms expose real acquisition boundaries.
4. Conceptual atom independence does not imply implementation independence; coupling is recorded.
5. Graph relationships are typed and revision-scoped.
6. Claim-level and verified relationships are distinguishable.
7. Acquisition is a spectrum, not build-vs-buy binary.
8. Decision outcomes are atom/capability scoped rather than repository scoped.
9. Hard gates cannot be averaged away.
10. Value is evaluated against the actual contract and intended operating context.
11. Internal implementations participate in the same comparison model as external candidates.
12. Framework adoption requires explicit systemic justification.
13. Focused dependency use is valid when it minimizes total ownership burden.
14. Reimplementation is valid when specification recovery and ownership economics justify it.
15. Every decision preserves provenance, reversibility, and revalidation context.
16. Net Capability Gain must exceed New System Burden.

## 12. Freeze Decision

**READY TO FREEZE.**

Block 1 is internally coherent with Block 0 and supplies a stable semantic foundation for Books II–VI.

Future changes to these definitions should be handled as explicit canon amendments because changing capability identity, atomization, graph semantics, acquisition forms, or the value model would affect discovery, proving, memory, orchestration, and OCE integration downstream.
