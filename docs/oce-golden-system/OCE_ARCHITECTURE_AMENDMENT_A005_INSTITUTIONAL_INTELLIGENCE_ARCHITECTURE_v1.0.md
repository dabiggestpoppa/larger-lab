# OCE Golden System
## Amendment A-005 — Institutional Intelligence Architecture

**Document ID:** OCE-AMEND-A005  
**Version:** 1.0  
**Status:** PROPOSED FOR OPERATOR RATIFICATION  
**Parent:** OCE Constitution 1.1  
**Architectural basis:** `LARGER_LAB_INSTITUTIONAL_ARCHITECTURE_v1.0.md`  
**Build authorization:** None

## 1. Decision

OCE shall be defined as the epistemic and constitutional operating system of Larger Lab, not as a model runtime, personal assistant, research model, or application shell.

Its permanent responsibilities are canonical truth, authority, evidence, state, causality, recovery, capability identity, learning promotion, and bounded context projection. Adaptive cognition is replaceable and operates over OCE-managed institutional state.

## 2. New universal primitives

### 2.1 ConstraintField

A versioned machine-readable representation of the active admissible state space for an objective. It includes goal, known state, unknowns, authority, dependencies, capabilities, budgets, required evidence, prohibitions, negative knowledge, rollback properties, unresolved contradictions, and completion conditions.

OCE shall prefer narrowing the admissible field as evidence accumulates rather than expanding plans indefinitely.

### 2.2 EvidenceGap

The smallest unresolved observation, proof, or experiment preventing a claim, task, capability, or plan from advancing.

Planning and worker allocation should optimize for closing the highest-value EvidenceGap at the lowest admissible cost.

### 2.3 NegativeKnowledge

A canonical record for falsified, demoted, blocked, unsafe, duplicated, irreproducible, or data-insufficient paths. It must preserve scope, evidence, exceptions, and reopen conditions.

### 2.4 ResumeCapsule

A minimum reconstruction packet containing objective, plan revision, last verified state, completed/remaining work, evidence, blockers, grants, cleanup obligations, and next safe action.

No long-running workflow may require raw transcript replay to resume correctly.

### 2.5 AffectedSurface

A machine-readable blast-radius projection of changed contracts, direct consumers, transitive consumers, authority/security impact, data/state impact, and required test/review depth.

Review depth and test radius follow the affected surface rather than line or file count.

## 3. Knowledge-to-execution gradient

OCE learning must support promotion from raw source or observation into progressively more executable institutional structure:

`source -> claim -> observation -> normalized knowledge -> mechanism -> validated relationship -> practice -> procedure -> test -> policy/template -> capability -> governed autonomous behavior`.

Promotion is not automatic. Each transition requires provenance, scope, evidence, confidence, counterexamples, and an expiry/review rule appropriate to the object.

## 4. Linked institutional graphs

OCE shall provide canonical identities and relationships for:

- EvidenceGraph;
- CapabilityGraph;
- WorkGraph;
- SourceGraph;
- NegativeKnowledgeGraph;
- domain-specific Research Genomes.

Implementation may use relational, document, graph, or hybrid storage, but the logical contracts remain stable and queryable independently of storage technology.

## 5. Agent Cockpit

OCE shall expose a minimum-sufficient `AgentCockpit` projection for each bounded operation. It includes applicable authority, current truth, active objective, relevant dependencies, capability options, evidence gaps, budget, blockers, and next admissible actions.

The cockpit is rebuilt from canonical state and must survive model/runtime replacement.

Context is progressively disclosed:

- Tier 0 — control kernel;
- Tier 1 — task contracts and active state;
- Tier 2 — supporting evidence;
- Tier 3 — deep archive and superseded history.

Higher tiers are retrieved only as required.

## 6. Resource-economy rule

OCE shall prefer the cheapest admissible method that can generate evidence strong enough for the claim being resolved.

Default escalation order is conceptually:

1. reuse fresh canonical evidence;
2. deterministic inspection or calculation;
3. affected local tests;
4. bounded sandbox experiment;
5. wider integration/CI evaluation;
6. disposable remote compute;
7. operator interruption or high-cost review.

The exact order may vary by risk class, but expensive cognition/compute cannot be the default merely because it is available.

## 7. Shared scientific doctrine

OCE planning and Quant/crypto research shall preserve the following epistemic principles:

- observation before prediction;
- state before action;
- constraints before direction;
- potential is not realization;
- nulls and failures are first-class evidence;
- repeated behavior is not automatically causal;
- named abstractions require incremental evidence;
- unresolved questions remain unresolved rather than filled by model recall;
- research stops when observation resolution is insufficient.

This doctrine does not make all domains identical. It defines a common evidence discipline.

## 8. Required downstream revisions

Ratification requires planned revisions to:

- B3 Evidence System and Event/State contracts;
- B4 intent/context/workers/learning;
- B6 reusable platform surfaces;
- B7 research and lineage contracts;
- B8 research intelligence and Quant Watch;
- B10 compounding and institutional learning;
- A-002 and A-004 terminology where runtime-specific assumptions conflict.

## 9. Prohibited interpretations

A-005 does not authorize:

- autonomous self-modification of authority;
- model-generated truth promotion without evidence;
- shared mutable agent memory as canonical state;
- execution or capital access;
- unrestricted recursive workers;
- unbounded external crawling;
- replacing B7 deterministic validation with agent judgment.

## 10. Acceptance tests

A-005 is accepted only if later implementation demonstrates that:

1. a workflow can restart on another runtime from canonical OCE state;
2. an agent can reconstruct a correct cockpit without raw chat history;
3. a known failed path is surfaced before redundant work begins;
4. a one-line high-blast-radius change receives deeper review than a large isolated change;
5. evidence gaps drive next actions more reliably than generic to-do expansion;
6. a promoted practice can become a test/policy without losing provenance;
7. agent replacement does not alter authority or evidence semantics.

## 11. Operator decision

Proposed decision: `RATIFY_A005_INSTITUTIONAL_INTELLIGENCE_ARCHITECTURE`.

Ratification changes planning and contracts only. It authorizes no implementation.