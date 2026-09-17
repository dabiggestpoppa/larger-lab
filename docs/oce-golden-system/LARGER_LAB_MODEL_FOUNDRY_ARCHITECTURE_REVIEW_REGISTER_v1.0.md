# Larger Lab Model Foundry
## Architecture Review Register — Contradictions, Ambiguities, and Required Revisions

**Document ID:** LL-MF-REVIEW-001  
**Version:** 1.0  
**Status:** OPEN REVIEW REGISTER — ARCHITECTURE REVISION REQUIRED — NO BUILD AUTHORIZATION  
**Parents:**
- `LARGER_LAB_MODEL_FOUNDRY_DOMAIN_INSTITUTION_BOOK_v1.0.md`
- `LARGER_LAB_MODEL_FOUNDRY_ADVERSARIAL_MATRIX_v1.0.md`
- `OCE_CONVERGENCE_END_STATE_AND_BRANCH_ROLES_v1.0.md`

**Purpose:** Prevent the first Foundry architecture draft from becoming canon merely because it is detailed. This register records where the design currently overlaps OCE, overstates what can be proven, or leaves decision-critical semantics underspecified.

---

# 0. Review doctrine

A contradiction means two architectural commitments cannot both remain true without a defined relationship or revision.

An ambiguity means the architecture permits multiple materially different implementations, at least one of which could violate the intended institution.

Neither class is resolved by choosing the implementation the current agent happens to prefer.

Required workflow:

```text
FINDING
  ↓
classify CON / AMB
  ↓
identify affected surfaces
  ↓
smallest architecture revision
  ↓
adversarial re-check
  ↓
operator review where constitutional
```

---

# 1. Open contradictions

## CON-MF-01 — Foundry provenance objects can become a second OCE evidence/source system

**Conflict:** The Foundry Book defines `SourceRecord`, `DatasetManifest`, evaluation evidence, artifact lineage, and model-specific evidence while One-OCE doctrine says generic evidence/provenance ownership belongs to OCE.

**Risk:** Foundry-local provenance grows into a parallel EvidenceGraph/SourceGraph.

**Required revision:** distinguish:

- OCE canonical envelope/identity/provenance ownership;
- Foundry domain payload/schema carried inside or referenced by that envelope.

`FoundrySourceRecord` should eventually be a domain specialization/projection of the canonical OCE source contract rather than an unrelated authority.

**Disposition:** OPEN — must be resolved before MF-B2 schema ratification.

---

## CON-MF-02 — EvaluationProtocol can duplicate OCE Evaluation Service / Governor semantics

**Conflict:** The Foundry freezes benchmark/evaluator rules, while OCE B6 Evaluation Service and institutional A010/G6 work already govern evaluator immutability, authority, and self-change.

**Risk:** Foundry creates a second evaluation constitution with different freeze/ratification semantics.

**Required revision:** Foundry owns model-domain evaluation **content**; OCE owns generic evaluation identity, freeze, authority, lifecycle, and effect on institutional promotion where available.

Until OCE integration, local evaluation fixtures must explicitly declare `NONCANONICAL_OCE_TEST_DOUBLE` and mirror tested G6 freeze semantics.

**Disposition:** OPEN — must be resolved before MF-B4.

---

## CON-MF-03 — Foundry runtime certification overlaps A007/OCE runtime certification authority

**Conflict:** MF-B10 is named OCE Runtime Certification, but the Foundry constitution says it cannot grant OCE consequence-bearing status.

**Risk:** a domain institution certifies its own product.

**Required revision:** MF-B10 may produce a `RuntimeCertificationCandidatePackage` and Foundry-domain evidence. Final OCE `VERIFIED_WORKERRUNTIME` status belongs outside the Foundry through A007 / future operational OCE certification.

Suggested Foundry terminal labels:

- `REJECTED_NEGATIVE_KNOWLEDGE`
- `RESEARCH_ONLY`
- `SANDBOX_RUNTIME_CANDIDATE`
- `READY_FOR_OCE_RUNTIME_CERTIFICATION`

not `OCE_CERTIFIED`.

**Disposition:** OPEN — high priority.

---

## CON-MF-04 — ComputeRequest / routing overlaps B10 Resource Intelligence

**Conflict:** Model Foundry needs rented GPU orchestration, but One-OCE doctrine places generic provider discovery, cost/capacity intelligence, and placement in B10 Resource Intelligence.

**Risk:** Foundry builds the permanent Compute Market Router itself.

**Required revision:** MF-B1 owns the **experiment compute requirement** and consumes a generic compute-routing capability. During early research, a narrow provider adapter may exist as a replaceable test implementation, but provider history/routing is targeted for B10/CMR convergence.

**Disposition:** OPEN — must shape MF-B1.

---

## CON-MF-05 — Foundry NegativeKnowledge can fork institutional NegativeKnowledge

**Conflict:** the Foundry wants durable failed recipes/models/experiments while A004/A009 define institutional NegativeKnowledge with reopen semantics.

**Risk:** two incompatible failure memories and reopen rules.

**Required revision:** define Foundry negative records as domain-specific negative-knowledge payloads using canonical OCE lifecycle/reopen semantics when integrated. Local research implementation must preserve scope, blocker, evidence, equivalence conditions, and reopen conditions compatible with the institutional contract.

**Disposition:** OPEN.

---

## CON-MF-06 — Practical pretrained bases cannot guarantee CEREBUS-independent rediscovery

**Conflict:** MF-B9 wants blind CEREBUS reconstruction, while useful specialist models will usually start from pretrained weights whose training corpus is partly unknown.

**Risk:** a model appears to rediscover structure that was already represented in upstream training.

**Required revision:** split the scientific claim classes:

1. `BLIND_TASK_PERFORMANCE` — CEREBUS withheld from Foundry training/retrieval after model acquisition, but upstream provenance may be unknown;
2. `CONTROLLED_INDEPENDENT_REDISCOVERY` — requires a sufficiently controlled base/from-scratch model or evidence that target doctrine was absent;
3. `POST_REVEAL_REPRODUCTION` — doctrine available; tests reproduction rather than rediscovery.

A pretrained model with unknown upstream data cannot receive the strongest independence label.

**Disposition:** OPEN — foundational to MF-B9.

---

## CON-MF-07 — Evaluation-before-training conflicts with base-model selection and iterative research unless evaluation roles are tiered

**Conflict:** the Book correctly freezes evaluation before specialization, but base-model tournaments and training development necessarily require feedback.

**Risk:** either researchers never learn from experiments, or hidden evaluation becomes development data.

**Required revision:** formalize at least three evaluation layers:

- `DEVELOPMENT_EVAL` — reusable, visible, expected to influence training;
- `PROMOTION_EVAL` — limited exposure and versioned access budget;
- `SEALED_CONFIRMATION_EVAL` — strongest hidden holdout, sparse use, retirement rules.

Public benchmarks are not automatically promotion evidence.

**Disposition:** OPEN — must be solved in Evidence/Evaluation Book.

---

## CON-MF-08 — Foundry-generated/OCE-generated training trajectories can create evaluator-policy feedback loops

**Conflict:** long-term trajectory distillation is desirable, but OCE evaluation and research behaviors may become both the training source and evaluator for future models.

**Risk:** the Foundry optimizes models to imitate its current institutional blind spots, increasing internal coherence while reducing reality coupling.

**Required revision:** trajectory datasets must carry generator/evaluator/policy lineage; later models require fresh external anchors and out-of-lineage evaluation. OCE-generated data cannot count as independent evidence of OCE-native behavior by itself.

**Disposition:** OPEN — relevant to MF-B10/M15-equivalent future work.

---

## CON-MF-09 — CapabilityAssessment is domain truth but CapabilityGraph is institutional truth

**Conflict:** the Foundry measures model capability while OCE owns reusable institutional capability semantics.

**Risk:** Foundry score becomes equivalent to OCE capability registration.

**Required revision:** Foundry produces `CapabilityAssessment` evidence. A separate mapping/promotion step may update OCE CapabilityGraph after applicable review. Preserve assessment dimensions and uncertainty rather than directly writing global capability status.

**Disposition:** OPEN.

---

## CON-MF-10 — Rights classification is necessary but the Foundry cannot manufacture legal certainty

**Conflict:** SourceRecord requires license/rights decisions, but many data/model licenses and web-source rights may be unclear or jurisdiction/context dependent.

**Risk:** `TRAIN_ALLOWED=true` is interpreted as legal advice/certainty beyond evidence.

**Required revision:** distinguish observed license/provenance facts from policy disposition. Use states such as:

- `RIGHTS_VERIFIED_BY_POLICY`
- `RIGHTS_RESTRICTED`
- `RIGHTS_UNKNOWN`
- `REVIEW_REQUIRED`

The Foundry enforces operator/org policy; it does not declare universal legal truth.

**Disposition:** OPEN — must be solved before MF-B2 build.

---

## CON-MF-11 — RLT exists as a child research branch and as an MF-B10 frontier item

**Conflict:** Runtime Dynamics already has `agent/oce-rlt-runtime-dynamics-lab`, while the Foundry Book places Transformer-vs-RLT research inside MF-B10.

**Risk:** duplicate governance, duplicate hypotheses, diverging evidence.

**Required revision:** Model Foundry is parent scientific institution; Runtime Dynamics is a separately versioned child research program whose evidence is registered back into the Foundry. MF-B10 references/consumes RD-B0→B8 rather than rebuilding it.

**Disposition:** OPEN — easy structural fix.

---

## CON-MF-12 — Stable object model may be too weight-centric for future cognitive architectures

**Conflict:** the Foundry claims innovation durability, but many core objects assume a monolithic model/checkpoint/tokenizer/training-run paradigm.

**Risk:** modular agents, continual learners, external-memory systems, neuromorphic systems, non-token architectures, or composed cognitive systems require schema rupture.

**Required revision:** introduce an upper abstraction such as `CognitiveArtifactSpec` / `CognitiveRuntimeSpec`, with `ModelSpec` and `ModelCheckpoint` as current specializations. Tokenizer may be optional/non-applicable.

**Disposition:** OPEN — important for the stated long-horizon mission.

---

# 2. Open ambiguities

## AMB-MF-01 — What is the atomic object being certified?

Is it:

- weights;
- weights + tokenizer;
- model + quantization;
- model + runtime wrapper;
- full agent/tool scaffold;
- or composed cognitive system?

**Required clarification:** define separate identities for cognitive artifact, runtime implementation, and deployed/scaffolded system. Certification must name which one it applies to.

---

## AMB-MF-02 — What exactly qualifies a source for TRAIN / EVAL / RETRIEVAL?

The roles exist but transition authority and policy are not fully specified.

**Need:** role-state machine, issuer/reviewer, derivation inheritance, revocation, and audit trail.

---

## AMB-MF-03 — Contamination is not binary

Exact duplicate, paraphrase, same solution, same source family, benchmark explanation, latent upstream exposure, and CEREBUS numeric leakage have different strength.

**Need:** contamination taxonomy and evidence strength rather than CLEAN/CONTAMINATED only.

---

## AMB-MF-04 — Hidden-holdout exposure budget

How many evaluations, aggregates, failures, or investigator interactions make a holdout development data?

**Need:** exposure accounting and benchmark-specific retirement/rekey policy; do not guess one universal number.

---

## AMB-MF-05 — Independence requirements for evaluation

When is one deterministic evaluator enough? When are independent model judges, fresh-context reviewers, alternate implementations, or external reproduction required?

**Need:** consequence/evidence-strength based independence policy.

---

## AMB-MF-06 — Capability lifecycle

The Book names assessments/candidates but not one complete domain lifecycle.

**Need candidate lifecycle:**

```text
DISCOVERED
→ BASELINED
→ EXPERIMENTAL
→ VALIDATED_DOMAIN_CAPABILITY
→ READY_FOR_OCE_CERTIFICATION
→ REJECTED / DORMANT / REOPENED
```

Exact names require later review.

---

## AMB-MF-07 — Benchmark lifecycle

When does a benchmark become SATURATED, COMPROMISED, STALE, RETIRED, or REACTIVATED?

**Need:** benchmark lifecycle separate from model lifecycle.

---

## AMB-MF-08 — How much abstention is good?

A model can game `INSUFFICIENT_EVIDENCE` by refusing difficult work.

**Need:** abstention evaluated jointly with correctness, answerability, calibration, and missed-opportunity cost.

---

## AMB-MF-09 — What counts as hallucination in tool/research tasks?

Text factual error, unsupported causal inference, fabricated file, incorrect computation claim, or ignoring tool result are distinct.

**Need:** failure taxonomy with deterministic labels where possible.

---

## AMB-MF-10 — Cost-to-close objective

Should routing optimize expected dollars, wall time, reliability, energy, reproducibility, security, or some vector?

**Need:** preserve vector; any routing scalar/utility must be task-contract specific rather than universal.

---

## AMB-MF-11 — Weekly experimental budget semantics

The user's practical $10–30/week intent is a current operating envelope, not constitutional law.

**Need:** ResourceBudget configuration, not hardcoded architecture.

---

## AMB-MF-12 — Checkpoint retention

Full checkpoints, optimizer state, logs, and adapters can become expensive quickly.

**Need:** retention classes tied to reproducibility value, promotion state, storage cost, and lineage preservation.

---

## AMB-MF-13 — Synthetic-data acceptance

What fraction/role is acceptable for CPT, SFT, coding traces, math solutions, research behavior, and evaluator training?

**Need:** no universal percentage; require lineage, task-specific policy, external grounding, and synthetic-generation audits.

---

## AMB-MF-14 — Base-model license compatibility

A base license may permit research/fine-tuning but constrain redistribution or commercial use.

**Need:** license facts + intended-use policy; candidate tournament must include downstream-use compatibility.

---

## AMB-MF-15 — Tool-use competence boundary

Does the model need to produce valid code, execute it, inspect results, repair failures, and cite artifacts? Which capabilities belong to model vs runtime scaffold?

**Need:** layered tool-use evaluation with ablations.

---

## AMB-MF-16 — Raw quant discovery benchmark construction

Using historical markets risks data snooping even without CEREBUS.

**Need:** discovery eras, sealed future/holdout periods, provider/vintage control, multiplicity tracking, and no result-driven feature-space expansion without new protocol version.

---

## AMB-MF-17 — CEREBUS correspondence scoring

What makes a discovered structure 'the same' as a CEREBUS rule?

**Need:** compare variable, scope, threshold/tolerance, conditionality, transition geometry, time/session semantics, predictive/discriminatory behavior, and out-of-sample reproduction. No single similarity score by default.

---

## AMB-MF-18 — Novel discoveries during CEREBUS comparison

A discovery absent from doctrine may be real, noise, or a different description of the same mechanism.

**Need:** preserve as `NOVEL_CANDIDATE` / `UNRESOLVED_PATTERN` and test independently before doctrine amendment.

---

## AMB-MF-19 — Model-generated research curriculum

When can a stronger model/agent generate training tasks for a weaker specialist without simply copying its own biases?

**Need:** teacher lineage, quality verification, counterexamples, independent anchors.

---

## AMB-MF-20 — Persistent/recurrent state retention

Should raw recurrent state be stored, encrypted, discarded, or checkpointed for research?

**Need:** runtime-state data class, privacy/security policy, retention, and explicit statement that raw state is never canonical institutional truth.

---

## AMB-MF-21 — Architecture comparison fairness

Matched parameter count can mismatch FLOPs; matched FLOPs can mismatch memory; matched wall time can mismatch maturity/tuning effort.

**Need:** at least two reporting regimes:

- controlled/matched comparison;
- best-practical implementation comparison.

Do not claim one universal fairness scalar.

---

## AMB-MF-22 — Statistical power / minimum experiment adequacy

Tiny runs are useful for smoke tests but may not support capability claims.

**Need:** protocol-specific adequacy criteria and terminal `INCONCLUSIVE / UNDERPOWERED` state.

---

## AMB-MF-23 — Evaluation of research methodology

'Good research behavior' can become ideological if one rubric encodes one scientific style.

**Need:** distinguish hard failures (leakage, fabricated evidence, post-result protocol change) from plural legitimate methodological strategies.

---

## AMB-MF-24 — Model family diversity vs independence

Two independently trained models with different architectures may share data/teacher/evaluator lineage; two same-family models may have genuinely independent evidence paths.

**Need:** multi-axis independence, never architecture-name counting.

---

## AMB-MF-25 — Operator override of experiment stopping

Operator may rationally authorize extra exploratory compute, but doing so after seeing results changes interpretation.

**Need:** allowed as a new experiment/protocol version with explicit post-result status, not retroactive extension of the frozen run.

---

# 3. Required architecture revisions before Evidence/Evaluation Book ratification

The next revision pass should amend or supplement the Foundry Book with at least these changes:

1. Introduce `CognitiveArtifactSpec` / `CognitiveRuntimeSpec` above today's weight-centric model objects.
2. Explicitly separate Foundry domain payloads from OCE canonical provenance/evidence envelopes.
3. Rename MF-B10's final state from OCE certification to **readiness for OCE runtime certification**.
4. Make Runtime Dynamics a child program consumed by MF-B10, not duplicated inside it.
5. Make MF-B1 compute routing a consumer/future feeder of B10 Resource Intelligence rather than permanent provider platform ownership.
6. Define evaluation tiers: Development, Promotion, Sealed Confirmation.
7. Define benchmark lifecycle and exposure accounting.
8. Define contamination taxonomy with graded/typed evidence.
9. Split CEREBUS reconstruction claims into blind-task, controlled-independent, and post-reveal reproduction classes.
10. Add transitive generator/teacher/evaluator lineage for synthetic/OCE trajectory training.
11. Define model-domain capability assessment as evidence feeding OCE CapabilityGraph rather than direct global capability truth.
12. Add explicit rights-policy disposition states that preserve uncertainty.
13. Define underpowered/inconclusive experiment state.
14. Define capability/model/runtime/benchmark lifecycles as separate state machines.
15. Preserve multi-vector cost/performance rather than introducing one universal Foundry score.

These revisions do not yet authorize implementation.

---

# 4. Proposed Foundry state-machine separation

The Foundry should not collapse all progress into one status.

At minimum preserve separate machines:

### M1 — Source/data role

```text
DISCOVERED → REVIEWED → TRAIN / EVAL / RETRIEVAL / QUARANTINED / EXCLUDED
```

### M2 — Experiment/run state

```text
PLANNED → FROZEN → RUNNING → COMPLETED / FAILED / CANCELLED / UNDERPOWERED
```

### M3 — Model/cognitive artifact lifecycle

```text
REGISTERED → BASELINED → EXPERIMENTAL → DOMAIN_VALIDATED → DORMANT / REJECTED
```

### M4 — Benchmark lifecycle

```text
DRAFT → FROZEN → ACTIVE → DEGRADED / COMPROMISED / SATURATED → RETIRED
```

### M5 — Capability evidence

```text
UNASSESSED → MEASURED → REPRODUCED → READY_FOR_OCE_CAPABILITY_REVIEW
```

### M6 — OCE authority

Remains outside Foundry lifecycle.

A model can therefore legitimately be:

```text
Artifact: DOMAIN_VALIDATED
Benchmark: ACTIVE
Capability: REPRODUCED
OCE authority: NONE
```

This separation should become explicit in later schemas.

---

# 5. Review conclusion

The v1.0 Foundry Book has a strong governing direction and should remain the parent architecture draft, but it is **not yet ready for implementation or master prompt generation**.

The adversarial review found no reason to abandon the Model Foundry concept. It found a more important requirement:

> **The Foundry must be stricter about separating the thing being trained, the system running it, the evidence measuring it, and the institution deciding what that evidence means.**

The next document should be the **Model Foundry Evidence & Evaluation Book**, but it must explicitly incorporate the open findings above rather than treating the v1.0 architecture as settled.

No contradiction here requires a second OCE. Most are resolved by making the Foundry a cleaner domain institution beneath OCE.
