# OCE Golden System
## Architecture Amendment A-012 — Model-Sparse Institutional Intelligence

**Document ID:** OCE-AMEND-A012

**Version:** 0.1

**Status:** PROPOSED FOR OPERATOR REVIEW — NO BUILD AUTHORIZATION

**Parents:** OCE Constitution 1.1; A-004; A-005; A-007; A-009; A-010

**Research basis:** `OPH_CADENCE_SOPHONTIC_INSTITUTIONAL_SYNTHESIS_v0.1.md`

**Impact review:** `OCE_OPH_CADENCE_SOPHONTIC_ARCHITECTURE_IMPACT_REVIEW_v0.1.md`

---

## 1. Decision

OCE shall become **model-sparse institutional intelligence**.

Model-sparse means:

> Use the least-general admissible cognitive mechanism that can close the current evidence gap while preserving required truth, authority, risk, cost, recovery, and continuation contracts.

It does not mean model-free, anti-LLM, or permanently committed to a fixed capability ladder. General reasoners, specialist models, bounded semantic models, symbolic systems, statistical methods, deterministic programs, tools, and humans remain eligible according to the work contract.

The institution must survive the loss or replacement of any particular cognitive implementation.

---

## 2. Constitutional boundary

No cognitive mechanism owns:

- canonical institutional state;
- truth promotion;
- authority creation;
- operator approval;
- mandate or grant semantics;
- verified-effect status;
- its own evaluation constitution;
- the right to certify its replacement as equivalent;
- permanent placement on the operational critical path.

Learned cognition may interpret, rank, predict, propose, simulate, critique, or act inside an existing grant. Capability and confidence do not create authority.

---

## 3. Cognitive mechanism classes

OCE shall remain compatible with at least the following classes:

| Class | Examples | Typical strength | Typical risk |
|---|---|---|---|
| deterministic | validation, parsing, exact calculation, state machine, database query | replayability and exact contract closure | brittle outside declared domain |
| statistical / optimization | estimation, forecasting, search, allocation, solvers | efficient structured inference | hidden assumptions and regime sensitivity |
| symbolic / hybrid | rules, theorem tools, constraint solvers, neuro-symbolic systems | explicit structure and inspectability | ontology lock or incomplete world model |
| bounded semantic | classifier, reranker, embedding, direct-logit decision model | cheap local ambiguity reduction | calibration and distribution shift |
| specialist learned | domain model, time-series model, coding/science specialist | high task density | domain overreach and lineage dependence |
| stateful / dynamical | recurrent systems, Cadence-like candidates, world models | streaming memory and temporal organization | contamination, instability, opaque state |
| general reasoner | broad LLM or future general architecture | synthesis across ambiguous domains | cost, correlated failure, fluent unsupported claims |
| human / operator | judgment, values, authority, novel interpretation | consequence-aware governance | scarcity, fatigue, inconsistent recall |

These are evaluation classes, not permanent routing ranks. A deterministic method is preferred for deterministic work, but a rigid hierarchy must not force a narrow tool beyond its validated envelope.

---

## 4. Routing law

Every material task shall expose:

1. the EvidenceGap to close;
2. required evidence strength;
3. risk and authority class;
4. deterministic and learned capability candidates;
5. state and context requirements;
6. acceptable latency and cost;
7. privacy and data boundary;
8. safe degraded behavior;
9. substitution and recovery requirements;
10. stop/obstruction conditions.

Routing then follows:

```text
define evidence gap
-> exclude inadmissible capabilities
-> identify minimum sufficient candidates
-> compare full cost/risk/dependency vector
-> execute boundedly
-> verify effect independently where required
-> update capability evidence
-> preserve failure and obstruction
```

The original vector remains inspectable. No universal scalar chooses the best cognition for every task.

---

## 5. `CognitiveDependencyProfile`

Every material capability on an operational or recovery-critical path shall eventually publish:

```yaml
CognitiveDependencyProfile:
  capability_id: string
  dependency_class: NONE | OPTIONAL | DEGRADABLE | REQUIRED
  primary_cognitive_implementation: string
  fallbacks: []
  safe_degraded_behavior: string
  state_dependency: string
  evidence_dependency: string
  authority_dependency: string
  morphology_dependencies: []
  provider_dependencies: []
  max_outage_tolerance: string
  recovery_contract: string
  continuation_contract_ref: string | null
  substitution_test_refs: []
  last_exercised_at: string | null
```

Rules:

- a declared fallback is not a proven fallback until exercised against the applicable contract;
- `REQUIRED` dependencies require an explicit operator-visible justification and remediation plan;
- canonical state in a cognitive implementation is prohibited;
- single-model and single-provider critical dependencies are tracked as architectural risk;
- dependency claims expire or re-enter review after material implementation change.

---

## 6. Private cognition and the public institution

OCE shall distinguish:

- **private cognitive state** — activations, scratchpads, local recurrent state, speculative plans, counterfactuals, internal simulations;
- **public candidate state** — structured claims or proposals exposed through typed ports with provenance;
- **canonical institutional state** — governed records accepted under OCE truth, evidence, and authority contracts.

Private cognition may be rich. It is never witnessed evidence merely because it is persistent, coherent, or confidently reported.

Required firewall:

```text
private simulation
-> typed candidate output
-> provenance and authority check
-> independent observation / verification where required
-> canonical promotion or explicit obstruction
```

---

## 7. Consensus and public-claim law

Consensus may:

- identify shared interpretation;
- reduce coordination cost;
- nominate a candidate public claim;
- reveal a stable interface or translation;
- justify an independence review.

Consensus may not by itself:

- establish external truth;
- prove causal structure;
- satisfy independent verification;
- grant authority;
- erase incompatible evidence;
- certify continuation or consciousness.

OCE shall preserve the difference between agreement count, evidence-lineage count, and effective independence.

---

## 8. Obstruction and safe incompleteness

The following are valid outcomes:

- insufficient evidence;
- no admissible capability;
- no trusted translation;
- incompatible protected observations;
- continuation equivalence unproven;
- evaluator unavailable;
- authority unavailable;
- safe degraded mode only;
- plural non-dominated interpretations.

OCE shall prefer a precise obstruction over fabricated coherence or unauthorized continuation.

---

## 9. Cognitive continuation and substitution

Cognitive substitution claims shall use the `CognitiveContinuationContract` defined by the existing-amendment patchset.

Replacement evidence must be scoped. Depending on consequence, it may include:

- canonical-state reconstruction;
- protected-observation preservation;
- forbidden-behavior preservation;
- equivalent authority handling;
- equivalent evidence semantics;
- task behavioral signatures;
- failure/degradation behavior;
- recovery and rollback;
- morphology/topology impact;
- model/provider independence.

A more capable replacement is not automatically an equivalent replacement.

Institutional identity is stricter than model equivalence: OCE continuity additionally requires canonical truth, authority, evidence, active work, holds, unresolved state, and verified-effect history to survive.

---

## 10. Institutional morphology

OCE shall treat material organization as part of the evaluated cognitive system.

Morphology includes:

- worker and service topology;
- port and schema structure;
- placement of canonical and ephemeral state;
- context-sharing topology;
- latency and bandwidth;
- checkpoint frequency;
- evaluator independence;
- authority distribution;
- repair path length;
- operator visibility;
- failure isolation.

Runtime neutrality means constitutional/interface neutrality, not an assumption that every topology produces equivalent cognition.

Material morphology changes require an AffectedSurface and the appropriate continuation/capability re-evaluation.

---

## 11. Causal-density research metric

OCE and Model Foundry may research:

```text
causal density
= independently verified load-bearing distinctions
  / (parameters + compute + state cost + evidence debt)
```

This is a research vector/ratio, not a governance score.

At minimum, reports must keep its components visible. It may guide experiments only after the terms are operationally defined for the task class. It cannot weaken mandatory evidence, safety, authority, or continuation gates.

---

## 12. Operator surface and dependency observability

OCE should eventually expose:

- percent of operational work completed without general reasoning;
- percent completed in safe degraded mode;
- critical dependencies by model, provider, runtime, and morphology;
- untested declared fallbacks;
- canonical state located in cognition, which must remain zero;
- substitution pass/fail/unknown status;
- evidence and recovery debt;
- operator interventions by genuine authority versus missing automation.

No target proportion of deterministic, specialist, or general cognition is frozen in advance. The dashboard reports observed dependency architecture.

---

## 13. Block impacts

### B0 — Constitutional Control

Add model-sparse routing, cognition/authority separation, and the prohibition on canonical state inside cognitive implementations.

### B2 — Reality Seal

Inventory cognitive and provider dependencies, private/canonical state boundaries, fallbacks, and substitution evidence.

### B3 — Constitutional Spine

Plan canonical envelopes for `CognitiveDependencyProfile`, `CognitiveContinuationContract`, cognitive implementation identity, and substitution evidence. Do not duplicate domain-specific evaluation payloads.

### B4 — PO Governed Builder

PO routes by evidence gap and admissibility, exposes obstructions, and cannot prefer a runtime merely because it is fluent or familiar.

### B5–B6 — Application and reusable surfaces

Applications consume typed cognition ports and dependency/continuation projections rather than embed permanent model dependencies.

### B7–B8 — Quant foundation and research

Deterministic/statistical/time-series/specialist/general mechanisms compete under frozen scientific evaluation. Cognitive implementation never overrides leakage, execution, or doctrine controls.

### B9 — Controlled Execution

Execution authority remains independent. Cognitive substitution cannot expand capital or deployment grants.

### B10 — Operational Compounding

Track dependency concentration, exercised fallbacks, recovery evidence, causal-density research, and replacement history.

---

## 14. Acceptance tests

A-012 is not implemented until evidence demonstrates:

1. deterministic work routes without a general model when it is the minimum sufficient path;
2. an ambiguous task may route to a general reasoner when narrower candidates cannot meet the contract;
3. removing required evidence produces obstruction, not confident completion;
4. consensus cannot promote a claim without the required evidence path;
5. private simulation cannot appear as witnessed history;
6. a cognitive implementation can fail without canonical-state loss;
7. a model/provider substitution preserves authority and evidence semantics;
8. an unproven fallback is reported as unproven;
9. a more capable but non-equivalent replacement is rejected for the protected scope;
10. a morphology change triggers re-evaluation when it changes protected behavior;
11. single-model and single-provider critical dependencies are observable;
12. operator hold occurs when safe continuation cannot be established.

---

## 15. Prohibited interpretations

A-012 does not claim:

- OPH is established physics;
- Cadence or any recurrent architecture is AGI;
- sophontic identity or consciousness has been detected;
- deterministic methods are universally superior;
- a fixed percentage of work must be model-free;
- all cognition is interchangeable;
- behavioral equivalence proves metaphysical identity;
- cognitive efficiency can override evidence or authority;
- OCE may self-ratify architecture changes.

---

## 16. Operator decision

Proposed decision:

`RATIFY_A012_MODEL_SPARSE_INSTITUTIONAL_INTELLIGENCE`

Ratification changes architecture and future planning only. It does not authorize implementation, model training, runtime migration, provider use, stress campaigning, deployment, capital action, or self-modification.
