# Larger Lab Model Foundry
## MF-A001 — Post-Adversarial Architecture Reconciliation

**Document ID:** LL-MF-A001  
**Version:** 1.0  
**Status:** PROPOSED ARCHITECTURE AMENDMENT — NO BUILD AUTHORIZATION  
**Parent:** `LARGER_LAB_MODEL_FOUNDRY_DOMAIN_INSTITUTION_BOOK_v1.0.md`  
**Evidence parents:**
- `LARGER_LAB_MODEL_FOUNDRY_ADVERSARIAL_MATRIX_v1.0.md`
- `LARGER_LAB_MODEL_FOUNDRY_ARCHITECTURE_REVIEW_REGISTER_v1.0.md`
- `LARGER_LAB_MODEL_FOUNDRY_EVIDENCE_AND_EVALUATION_BOOK_v1.0.md`

**Purpose:** Apply the smallest architecture changes required by the first red-team pass while preserving the original Foundry mission and One-OCE boundary.

---

# 0. Amendment rule

The v1.0 Foundry Book remains the architectural parent and historical record.

Where this amendment conflicts with the v1.0 wording, **MF-A001 controls for future planning** unless later superseded.

No change here authorizes implementation.

The amendment does not create a second OCE, second authority system, second EvidenceGraph, or second evaluation constitution.

---

# 1. Refined North Star

The Foundry must distinguish four layers that the first draft sometimes treated too closely:

```text
COGNITIVE ARTIFACT
learned structure / weights / adapters / future equivalent
        ↓
COGNITIVE RUNTIME
how that artifact executes
        ↓
COGNITIVE SYSTEM
runtime + context + tools + retrieval + scaffolding
        ↓
OCE INSTITUTION
truth + authority + canonical memory + workflow + governance
```

The Foundry may design and evaluate the first three.

Only OCE owns the fourth.

---

# 2. Object hierarchy revision

## 2.1 New upper abstraction — `CognitiveArtifactSpec`

`ModelSpec` is no longer the highest durable abstraction.

`CognitiveArtifactSpec` covers:

- neural weights;
- adapters;
- recurrent/stateful learned structures;
- modular learned components;
- non-token models;
- future cognitive architectures.

`ModelSpec` remains a current specialization.

## 2.2 `CognitiveRuntimeSpec`

Separates artifact from:

- framework;
- quantization;
- decoding;
- state semantics;
- tool interface;
- context interface;
- runtime implementation.

## 2.3 `CognitiveSystemSpec`

Represents the evaluated composed system:

```text
artifact + runtime + context/retrieval + tools + scaffold
```

System-level evidence cannot silently promote artifact-level claims.

## 2.4 Identity invariant

Every capability measurement records whether it applies to:

- ARTIFACT;
- RUNTIME;
- SYSTEM.

This distinction is mandatory in MF-B4 onward.

---

# 3. One-OCE provenance boundary

Foundry domain objects do not become independent generic evidence authorities.

Target integration pattern:

```text
OCE canonical envelope
    identity / provenance / authority / lifecycle
              ↓
Foundry domain payload
    model / dataset / training / evaluation semantics
```

Examples:

- Foundry source metadata is a domain extension of OCE `SourceRecord` semantics;
- Foundry run evidence is registered through OCE evidence surfaces when available;
- Foundry artifacts use OCE artifact identity/storage contracts when available;
- Foundry NegativeKnowledge uses institutional reopen/lifecycle semantics when available.

Before convergence, local equivalents must be marked:

`NONCANONICAL_OCE_TEST_DOUBLE`

and must expose an explicit replacement mapping.

---

# 4. Evaluation-governance boundary

The Foundry owns:

- benchmark content;
- model-domain metrics;
- task packs;
- contamination analysis;
- capability interpretation;
- model-domain comparison.

OCE owns or will own:

- generic evaluator identity;
- authority to freeze/activate evaluator versions;
- institutional promotion authority;
- same-window self-change prohibition;
- audit/reconstruction semantics.

Until operational convergence, Foundry-local `EvaluationProtocol` must mirror the tested G6 freeze rules and cannot ratify its own consequence-bearing changes.

---

# 5. Evaluation tier ratification

MF-A001 adopts the three-tier architecture from the Evaluation Book:

```text
DEVELOPMENT_EVAL
PROMOTION_EVAL
SEALED_CONFIRMATION_EVAL
```

This resolves the first-draft conflict between:

- needing feedback to develop models;
- and needing hidden evidence to confirm claims.

No tier may be promoted after the fact because a result is impressive.

Benchmark exposure and retirement are first-class state.

---

# 6. MF-B10 authority correction

The v1.0 phrase **OCE Runtime Certification** is too strong for Foundry-owned authority.

MF-B10 is revised to:

> **OCE Runtime Readiness + Research Frontier**

The strongest Foundry-owned runtime terminal state is:

`READY_FOR_OCE_RUNTIME_CERTIFICATION`

Other permitted terminal states include:

- `REJECTED_NEGATIVE_KNOWLEDGE`
- `RESEARCH_ONLY`
- `SANDBOX_RUNTIME_CANDIDATE`
- `DORMANT_RESEARCH_ARTIFACT`

Final OCE certification remains external to the Foundry.

---

# 7. Runtime Dynamics parent-child relationship

The existing Runtime Dynamics / RLT program is a **child research institution of the Model Foundry**, not a duplicate MF-B10 implementation.

Architecture:

```text
MODEL FOUNDRY
    ↓
MF-B10 Research Frontier
    ↓
Runtime Dynamics Program
    RD-B0 → RD-B8
    ↓
Foundry evidence registration
    ↓
possible OCE amendment/certification candidate
```

The RLT branch may develop independently for experimental cleanliness, but its evidence and promotion path belong to the Foundry/OCE hierarchy.

---

# 8. PC-ALM relationship

PC-ALM remains a Foundry learning-dynamics track.

Its initial outputs may be:

- reproduction evidence;
- learning-dynamics measurements;
- architecture comparisons;
- candidate mechanisms;
- candidate OCE analogies.

No local-learning result directly modifies A009/A010.

An institutional analogy is an `ARCHITECTURE_HYPOTHESIS`, not an amendment.

---

# 9. Compute-routing boundary

MF-B1 owns the compute needs of a Foundry experiment.

It does not permanently own generic provider-market intelligence.

The durable split is:

```text
Foundry ExperimentProtocol
      ↓
ComputeRequest
      ↓
OCE Resource Intelligence / COMPUTE.GPU.RENT
      ↓
provider implementation
      ↓
ComputeReceipt
      ↓
Foundry TrainingRun / EvaluationRun
```

Before B10 Resource Intelligence is operational, Foundry may use a narrow local router as a replaceable research implementation.

Its provider observations should be structured so they can later migrate into OCE Resource Intelligence.

---

# 10. Capability boundary

The Foundry owns `CapabilityAssessment` evidence.

It does not directly own the global OCE `CapabilityGraph` status.

Flow:

```text
Foundry evaluation
      ↓
CapabilityAssessment
      ↓
reproduction / confirmation
      ↓
READY_FOR_OCE_CAPABILITY_REVIEW
      ↓
OCE capability promotion if authorized
```

A Foundry capability score never grants authority.

---

# 11. NegativeKnowledge boundary

Foundry failures use the same conceptual structure as institutional NegativeKnowledge:

- claim/path tried;
- exact scope;
- conditions;
- evidence;
- failure mechanism if known;
- equivalence conditions;
- reopen conditions;
- provenance;
- lifecycle state.

The Foundry may maintain a domain index before full OCE integration, but it must not invent incompatible reopen semantics.

---

# 12. Rights / policy uncertainty

Foundry source governance must separate:

1. observed source/license facts;
2. organization/operator policy disposition;
3. unresolved legal/rights uncertainty.

Adopt candidate states:

- `RIGHTS_VERIFIED_BY_POLICY`
- `RIGHTS_RESTRICTED`
- `RIGHTS_UNKNOWN`
- `REVIEW_REQUIRED`
- `EXCLUDED_BY_POLICY`

Unknown rights do not become training permission.

The Foundry is not a universal legal adjudicator.

---

# 13. CEREBUS reconstruction claim correction

MF-A001 formally adopts three different scientific claims.

## 13.1 `BLIND_TASK_PERFORMANCE`

CEREBUS is withheld from Foundry training/retrieval during the relevant program, but upstream pretrained-model exposure may be unknown.

This tests whether the runtime can recover similar structure under the blind task.

It does **not** prove zero prior exposure.

## 13.2 `CONTROLLED_INDEPENDENT_REDISCOVERY`

Requires sufficiently controlled training lineage, typically through a from-scratch/control model or other strong evidence that target doctrine was unavailable.

This is the strongest rediscovery claim.

## 13.3 `POST_REVEAL_REPRODUCTION`

Doctrine is visible and the model attempts to reproduce or challenge it empirically.

This is reproduction, not rediscovery.

These labels may never be merged for marketing convenience.

---

# 14. CEREBUS comparison neutrality

CEREBUS remains a source-bound domain doctrine/research lineage.

When blind discoveries are compared against it, valid terminal states include:

- strong correspondence;
- partial correspondence;
- no correspondence;
- empirical contradiction;
- novel candidate;
- inconclusive.

CEREBUS is not declared wrong because one model disagrees.

The model is not declared wrong merely because CEREBUS differs.

The comparison produces evidence and may open reproduction/review.

---

# 15. Trajectory/synthetic-data lineage

Future OCE-generated research trajectories, model-generated tasks, synthetic corpora, distillation data, and judge outputs must carry transitive generator lineage.

At minimum:

- generator artifact/runtime;
- teacher lineage;
- source inputs;
- policy/evaluator version;
- acceptance method;
- verifier lineage;
- derivation depth;
- target model relationship.

A model trained on OCE-generated trajectories cannot use performance on the same lineage as independent evidence that it learned OCE-native science.

External anchors remain required.

---

# 16. Separate Foundry state machines

MF-A001 adopts the state-machine separation proposed by the review register.

## M1 — Source/data role

```text
DISCOVERED
→ REVIEWED
→ assigned TRAIN / DEV_EVAL / PROMOTION_EVAL / SEALED / RETRIEVAL / QUARANTINED / EXCLUDED
```

## M2 — Experiment/run

```text
PLANNED
→ FROZEN
→ RUNNING
→ COMPLETED / FAILED / CANCELLED / UNDERPOWERED / INVALID
```

## M3 — Cognitive artifact

```text
REGISTERED
→ BASELINED
→ EXPERIMENTAL
→ DOMAIN_VALIDATED
→ DORMANT / REJECTED / REOPENED
```

## M4 — Benchmark

```text
DRAFT
→ VALIDATED
→ FROZEN
→ ACTIVE
→ DEGRADED / COMPROMISED / SATURATED / STALE
→ RETIRED
```

## M5 — Capability evidence

```text
UNASSESSED
→ MEASURED
→ PROMOTION_EVAL_PASSED
→ REPRODUCED
→ SEALED_CONFIRMATION_PASSED
→ READY_FOR_OCE_CAPABILITY_REVIEW
```

## M6 — OCE authority

Outside Foundry ownership.

No implementation may compress these into one `status` field.

---

# 17. Underpowered and inconclusive science

The Foundry must allow experiments to terminate without a positive/negative scientific verdict.

Required states include:

- `UNDERPOWERED`
- `INCONCLUSIVE`
- `DATA_BLOCKED`
- `RIGHTS_BLOCKED`
- `COMPUTE_BLOCKED`
- `CONTAMINATED`
- `PROTOCOL_VIOLATION`

This prevents cheap-compute constraints or incomplete data from being converted into false certainty.

---

# 18. Multi-vector economics

No universal scalar may silently define the best model or compute provider.

Preserve at minimum:

```text
capability
latency
VRAM/RAM
accelerator time
context/tokens
provider cost
failure/restart risk
operator burden
reproducibility
security/trust
```

A task-specific routing utility may select among these, but the original vector remains inspectable.

---

# 19. Benchmark evolution without benchmark self-modification

Benchmark evolution is allowed only across explicit versions/epochs.

A benchmark may become:

- degraded;
- compromised;
- saturated;
- stale;
- retired.

The evaluator used to judge a current promotion run cannot modify itself based on that run's result.

New benchmark versions enter later evaluations with preserved lineage.

---

# 20. Foundry scientific ecology

The Foundry should cultivate reciprocal constraints rather than one optimization target.

```text
SPECIALIZATION   <-> RETENTION
capability gain      catastrophic forgetting

SPEED            <-> REPRODUCIBILITY
iteration            causal legibility

SYNTHETIC SCALE  <-> EXTERNAL GROUNDING
cheap data            reality coupling

NOVELTY          <-> BASELINE DISCIPLINE
innovation            fair comparison

CAPABILITY       <-> RESOURCE COST
performance           efficiency

AUTOMATION       <-> INDEPENDENT REVIEW
throughput            self-confirmation resistance
```

No subsystem optimizes the entire Foundry objective alone.

---

# 21. Revised Foundry block names / responsibilities

## MF-B0 — Program Constitution + Scientific Boundary

Owns:

- One-OCE boundary;
- object identities;
- lifecycle separation;
- rights/research ethics;
- reproducibility law;
- CEREBUS withholding/claim classes;
- authority/budget boundary.

## MF-B1 — Experiment Resource Interface

Owns Foundry `ComputeRequest`/resource need and temporary adapters.

Targets future OCE Resource Intelligence for generic routing.

## MF-B2 — Data Constitution + Source Role Governance

Owns domain-specific data provenance/role payloads under OCE envelopes.

## MF-B3 — Dataset Refinery + Corpus Lineage

Owns transformations, dedupe, quality, partition construction, fingerprints.

## MF-B4 — Evaluation Institution

Owns domain benchmark content/metrics using the Evaluation Book and OCE-compatible freeze semantics.

## MF-B5 — Base Cognitive Artifact Tournament

Not limited conceptually to monolithic LLM weights, though first implementation may be.

## MF-B6 — Specialist Adaptation

Owns controlled adaptation research and forgetting audits.

## MF-B7 — Scientific Tool + Coding Competence

Owns end-to-end tool/coding evaluation/training.

## MF-B8 — Raw Quant Discovery Institution

Owns blind raw-market research behavior before CEREBUS comparison.

## MF-B9 — CEREBUS Reconstruction + Doctrine Comparison

Uses the three claim classes defined above.

## MF-B10 — OCE Runtime Readiness + Research Frontier

Produces candidate packages for external OCE certification and hosts/coordinates child research programs such as Runtime Dynamics and PC-ALM tracks.

---

# 22. Revised pre-build gate

Material GPU training is not authorized until the minimum required portions of MF-B0 through MF-B4 can prove:

1. artifact/runtime/system identity separation;
2. One-OCE integration boundary;
3. source-role governance;
4. rights/policy disposition;
5. transitive data lineage;
6. contamination taxonomy;
7. evaluation tier separation;
8. protocol freeze;
9. benchmark lifecycle;
10. hidden exposure accounting;
11. run registry including failures;
12. capability-vector evaluation;
13. underpowered/inconclusive terminal states;
14. exact evaluation receipts;
15. CEREBUS blind claim classes;
16. no Foundry object can grant OCE authority.

Tiny smoke tests may occur only to validate infrastructure and must not be reported as model research evidence.

---

# 23. Required future convergence map

Each Foundry block dossier must include a table with:

- Foundry domain object;
- temporary sandbox implementation if any;
- target OCE canonical service;
- owner before convergence;
- owner after convergence;
- migration evidence required;
- deletion/retirement condition for the temporary implementation.

This table is mandatory to prevent prototype infrastructure from silently surviving as OCE #2.

---

# 24. Amendment exit

MF-A001 resolves the first architecture-level contradictions directionally but does not claim the program is build-ready.

The next planning work should use:

- Foundry Book v1.0 as original parent;
- MF-A001 as controlling architecture delta;
- Evidence & Evaluation Book v1.0 as the evaluation constitution draft;
- Adversarial Matrix + Review Register as open attack surfaces.

The next phase is detailed block decomposition beginning with **MF-B0**, followed by independent adversarial review before any GPU training authorization.

The governing end state remains:

> **The Foundry may continuously replace and improve Larger Lab's cognitive organs without ever becoming the authority that decides its own scientific success.**
