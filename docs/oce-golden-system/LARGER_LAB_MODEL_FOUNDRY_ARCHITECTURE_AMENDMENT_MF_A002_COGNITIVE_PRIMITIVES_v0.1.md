# Larger Lab Model Foundry
## MF-A002 — System-One and Cognitive Primitives

**Document ID:** LL-MF-A002

**Version:** 0.1

**Status:** PROPOSED FOUNDRY AMENDMENT — NO BUILD OR TRAINING AUTHORIZATION

**Parents:** Model Foundry Domain Institution Book v1.0; MF-A001; Evidence and Evaluation Book v1.0

**OCE parent candidate:** A-012 Model-Sparse Institutional Intelligence

**Research basis:** `OPH_CADENCE_SOPHONTIC_INSTITUTIONAL_SYNTHESIS_v0.1.md`

---

## 0. Amendment rule

The Foundry mission expands from manufacturing and evaluating model candidates to manufacturing and evaluating **cognitive primitives and composed cognitive systems**.

MF-A001 already established `CognitiveArtifactSpec`, `CognitiveRuntimeSpec`, and `CognitiveSystemSpec`. MF-A002 adds a lower-granularity research object and a dedicated evidence lane. It does not create a second OCE, authority system, evidence constitution, or runtime-certification authority.

MF-B0 through MF-B4 remain unchanged as the current substrate build. This amendment enters only after that substrate can enforce provenance, rights, lineage, contamination, frozen evaluation, and reproducibility.

---

## 1. Decision

The Foundry shall not assume that the best future cognitive organ is a monolithic language model.

It shall support governed research over:

- deterministic programs and exact tools;
- classifiers and calibrators;
- rerankers and retrieval components;
- embeddings and representation systems;
- direct-logit or bounded semantic decision models;
- statistical, optimization, and symbolic solvers;
- time-series and dynamical models;
- recurrent/stateful architectures;
- neuro-symbolic and modular hybrids;
- specialist language models;
- tool-using cognitive systems;
- embodied/world-coupled policies;
- general reasoners;
- future architectures not yet named.

The unit of competition is the minimum sufficient cognitive system for a declared task and evidence contract.

---

## 2. New object — `CognitivePrimitiveSpec`

A cognitive primitive is a bounded component that transforms observations, state, constraints, or candidate actions into a typed output.

Candidate fields:

```yaml
CognitivePrimitiveSpec:
  primitive_id: string
  primitive_class: string
  implementation_identity: string
  artifact_runtime_system_scope: ARTIFACT | RUNTIME | SYSTEM
  input_contract: string
  output_contract: string
  state_semantics: string
  training_or_construction_lineage: string
  calibration_scope: string
  authority_class: NONE
  known_failure_modes: []
  composition_constraints: []
  evidence_protocol_ref: string
  dependency_profile_ref: string | null
```

`authority_class` is fixed to `NONE` because primitives supply capability, not institutional authority.

---

## 3. Primitive families

### 3.1 Exact and algorithmic

Parsers, validators, state machines, numerical methods, search, optimization, theorem tools, and deterministic transforms.

### 3.2 Bounded semantic cognition

Classification, ranking, similarity, anomaly detection, semantic routing, direct decision interfaces, and small learned representations.

### 3.3 Stateful and dynamical cognition

Recurrent networks, persistent-state systems, Cadence-like architectures, reservoir methods, learned filters, world models, and other temporal organizations.

### 3.4 Specialist cognition

Domain models for code, science, mathematics, research, time series, quantitative analysis, or other bounded fields.

### 3.5 Composed and hybrid cognition

Systems combining deterministic, symbolic, learned, retrieval, tool, memory, and verification components.

### 3.6 General cognition

Broad reasoners evaluated as one component class rather than presumed default or institutional identity.

---

## 4. Common evaluation envelope

Every primitive family competes under a shared outer evidence envelope while retaining family-specific metrics.

Required dimensions include:

- exact task capability;
- abstention and obstruction quality;
- calibration;
- robustness to irrelevant variation;
- response to causal-premise intervention;
- out-of-distribution behavior;
- state contamination and reset semantics;
- retention and forgetting;
- compute, memory, latency, and cost;
- evidence debt;
- operator burden;
- reproducibility;
- morphology/topology dependency;
- substitution and continuation behavior;
- model/provider concentration;
- independent verification requirements.

No universal scalar silently determines the winner.

---

## 5. Mandatory controls

Every learned or novel primitive must be compared, where applicable, against:

- a deterministic baseline;
- a simple statistical baseline;
- a current specialist baseline;
- a general-reasoner baseline;
- ablations removing claimed state/memory/repair mechanisms;
- cost-matched and compute-matched controls;
- frozen task and contamination definitions.

Novel architecture claims fail if gains disappear under fair identity, data, compute, or system-boundary accounting.

---

## 6. System-One research lane

“System-One” is used operationally for fast, bounded, frequently invoked cognition. It does not imply human phenomenology or consciousness.

Create a child lane under the Foundry research frontier:

### CP-B0 — Claim and source fidelity

- exact external claim extraction;
- code/paper/version identity;
- license and rights disposition;
- reproduction boundary;
- unsupported-claim quarantine.

### CP-B1 — Primitive contract and baselines

- typed input/output;
- task envelope;
- deterministic/statistical/general controls;
- initial cost and calibration baselines.

### CP-B2 — Representation and bounded decision

- classifier/reranker/embedding/direct-decision studies;
- semantic sufficiency and failure surfaces;
- confidence versus evidence separation.

### CP-B3 — State and dynamics

- recurrence;
- persistent local state;
- attractor/metastability mapping;
- hysteresis;
- reset, checkpoint, and contamination.

### CP-B4 — Continual and developmental behavior

- acquisition;
- retention;
- relevant forgetting;
- transfer;
- protected responses;
- catastrophic interference.

### CP-B5 — Composition and morphology

- primitive composition;
- topology and port structure;
- tool/retrieval/verification coupling;
- evaluator independence;
- morphology-sensitive behavior.

### CP-B6 — Continuation and substitution

- behavioral signatures;
- protected observations;
- model/runtime/provider swap;
- safe degraded behavior;
- recovery and rollback.

### CP-B7 — OCE readiness disposition

Permitted outcomes:

- `READY_FOR_OCE_CAPABILITY_REVIEW`;
- `SANDBOX_COGNITIVE_PRIMITIVE`;
- `RESEARCH_ONLY`;
- `INCONCLUSIVE`;
- `DATA_BLOCKED`;
- `COMPUTE_BLOCKED`;
- `CONTAMINATED`;
- `REJECTED_NEGATIVE_KNOWLEDGE`.

The Foundry cannot issue final OCE certification.

---

## 7. Cadence, OpenJev, RLT, and future donors

External projects enter as research donors, never dependencies.

- Cadence may contribute hypotheses about recurrent state, overlap repair, protected responses, detuning, imagination, consequence readback, and checkpointing.
- OpenJev or Jev-like work may contribute bounded semantic decision-interface hypotheses.
- RLT may contribute recurrent dynamics and state-instrumentation candidates.
- PC-ALM may contribute local-learning and constraint-dynamics hypotheses.
- future systems enter through the same claim, provenance, baseline, and evaluation gates.

No donor's branding, architecture narrative, unpublished claim, or benchmark result substitutes for reproduction.

---

## 8. Private imagination test boundary

Stateful systems may be evaluated for counterfactual or generative internal dynamics only if the system boundary distinguishes:

- internal simulation;
- proposed observation;
- actual observation;
- attempted action;
- actual consequence;
- independently verified effect.

A system that improves task scores by leaking simulated state into evidence records fails the institutional-readiness boundary regardless of benchmark performance.

---

## 9. Causal-density research

The Foundry may operationalize causal-density candidates by testing whether:

- causal premise interventions change outputs appropriately;
- irrelevant wording or representation changes preserve protected results;
- removing evidence creates abstention/obstruction;
- contradictions trigger repair or escalation;
- implementation swaps preserve declared behavior;
- cost and evidence debt remain explicit.

Causal density remains a multi-component research construct until validated. It cannot become a single promotion score.

---

## 10. Relationship to existing Foundry blocks

| Existing block | MF-A002 impact |
|---|---|
| MF-B0 | no current-build change; future terminology recognizes primitive/system research |
| MF-B1 | resource requests support non-LLM experiments without provider lock |
| MF-B2 | source and rights law applies to all training/research inputs |
| MF-B3 | lineage covers generated state traces, trajectories, and hybrid-system data |
| MF-B4 | frozen evaluation becomes the shared outer envelope for primitive families |
| MF-B5 | tournament may compare cognitive artifacts/systems, not only base LLMs |
| MF-B6 | adaptation includes bounded primitive training and continual-learning tests |
| MF-B7 | tool competence evaluates composed systems without miscrediting components |
| MF-B8–B9 | raw discovery and CEREBUS comparison preserve implementation identity and contamination law |
| MF-B10 | hosts CP-B0 through CP-B7 and emits candidates for external OCE review |

The current MF-B0 through MF-B4 build prompt and implementation remain unchanged.

---

## 11. Acceptance tests

MF-A002 is not ready for implementation until planning can prove:

1. every primitive has exact artifact/runtime/system identity;
2. family-specific metrics live inside a common evidence envelope;
3. simple baselines cannot be omitted because a novel architecture is attractive;
4. component capability is not miscredited from system scaffolding;
5. private simulation cannot enter witnessed evidence;
6. stateful candidates expose reset, checkpoint, and contamination behavior;
7. morphology/topology changes are part of the evaluated subject identity;
8. substitution claims bind a continuation contract;
9. no primitive score grants authority;
10. no donor becomes a mandatory dependency;
11. failures become scoped NegativeKnowledge with reopen conditions;
12. MF-B0 through MF-B4 remain sufficient prerequisites rather than being redesigned around one candidate.

---

## 12. Operator decision

Proposed decision:

`RATIFY_MF_A002_SYSTEM_ONE_AND_COGNITIVE_PRIMITIVES`

Ratification changes Foundry planning only. It authorizes no new dataset, model download, training, GPU spend, Cadence/OpenJev/RLT implementation, benchmark activation, OCE runtime certification, or deployment.
