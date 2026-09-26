# Larger Lab Model Foundry
## MF-B0 Adversarial Review — Program Constitution and Scientific Boundary

**Document ID:** LL-MF-B0-REDTEAM-001  
**Version:** 1.0  
**Status:** ADVERSARIAL REVIEW — NO BUILD AUTHORIZATION  
**Parent:** `LARGER_LAB_MODEL_FOUNDRY_MF_B0_PROGRAM_CONSTITUTION_AND_SCIENTIFIC_BOUNDARY_PLAN_v1.0.md`  
**Branch:** `agent/oce-institutional-stress-suite-build`

---

# 0. Review objective

MF-B0 is supposed to freeze the scientific constitution so later technology can move quickly without turning the Model Foundry into a second OCE, a benchmark casino, or a model-training vanity project.

This review therefore attacks the boundary itself.

The question is not whether MF-B0 sounds disciplined. The question is whether an implementation agent could still exploit ambiguity to:

- create parallel truth/authority systems;
- leak evaluation data into training;
- overclaim CEREBUS rediscovery;
- let budget convenience override scientific validity;
- hide failed runs;
- make model capability imply authority;
- let current toolchains harden into architecture;
- produce irreproducible evidence.

A finding is useful even if it delays build authorization.

---

# 1. Findings register

## B0-R1 — Sandbox-local fixtures can become shadow OCE

**Attack:** MF-B0 allows narrow sandbox-local fixtures until operational OCE services exist. A builder expands these fixtures into identity, evidence, approvals, workflow, and memory because it is convenient.

**Failure:** Model Foundry becomes a second OCE in practice while still claiming temporary scaffolding.

**Required closure:** every noncanonical fixture must declare:

- canonical OCE service it substitutes for;
- exact missing dependency;
- supported test scope;
- prohibited production use;
- deletion/replacement trigger;
- migration path.

**Disposition:** CONFIRMED RISK — close in B0/B1 contracts.

---

## B0-R2 — “Model output is observation” can still be mistaken for evidence

**Attack:** model output is registered with provenance and therefore treated as evidence without an independent applicability/reliability check.

**Failure:** logging becomes evidence laundering.

**Required closure:** distinguish:

`RuntimeObservation -> EvidenceCandidate -> Evidence`

Registration alone is insufficient.

**Disposition:** CONFIRMED — must carry into evaluation book implementation.

---

## B0-R3 — Capability vector can be Goodharted

**Attack:** a model is optimized against the exact capability dimensions used for promotion.

**Failure:** capability vector becomes one composite reward surface despite the ban on one scalar.

**Required closure:** preserve hidden confirmation tasks, rotating/degrading benchmarks, and behavior-based stress cases not used for tuning.

**Disposition:** COVERED IN PRINCIPLE — requires MF-B4 enforcement.

---

## B0-R4 — CEREBUS withholding is underspecified for pretrained ancestry

**Attack:** an open base model already saw public/private derivative CEREBUS material before Foundry acquisition.

**Failure:** “rediscovery” is claimed where the model may be recalling prior exposure.

**Required closure:** use three claim classes:

- BLIND_TASK_PERFORMANCE;
- CONTROLLED_INDEPENDENT_REDISCOVERY;
- POST_REVEAL_REPRODUCTION.

Unknown ancestry never upgrades into independent rediscovery.

**Disposition:** CLOSED BY MF-A001 / Eval Book; enforce in B2/B4/B9.

---

## B0-R5 — Rights metadata can be self-declared

**Attack:** source records contain `training_allowed=true` without documentary basis.

**Failure:** provenance schema exists but rights verification is fictional.

**Required closure:** every rights decision needs a basis class:

- explicit license;
- public-domain status;
- operator-owned;
- provider terms;
- legal/rights review required;
- unknown.

UNKNOWN defaults away from training.

**Disposition:** CONFIRMED — B2 blocker.

---

## B0-R6 — “Cheap compute” can distort experimental design

**Attack:** experiments are chosen because the current marketplace GPU is inexpensive rather than because they close the highest-value EvidenceGap.

**Failure:** provider economics silently becomes research agenda.

**Required closure:** compute routing occurs after experiment protocol and required evidence class are defined.

**Disposition:** CONFIRMED — B1 must encode.

---

## B0-R7 — Reproducibility can be impossible for marketplace infrastructure

**Attack:** exact GPU/provider image disappears.

**Failure:** Foundry treats provider-level reproducibility as mandatory and blocks useful science, or silently weakens reproducibility.

**Required closure:** define reproducibility levels:

- BIT/ENVIRONMENT REPRODUCIBLE where practical;
- FUNCTIONALLY REPRODUCIBLE;
- STATISTICALLY REPRODUCIBLE;
- NONREPRODUCIBLE.

Reproducibility claim must match what is actually preserved.

**Disposition:** CONFIRMED — B1/B4.

---

## B0-R8 — NegativeKnowledge can suppress innovation

**Attack:** a failed recipe/architecture becomes a broad “do not retry” rule.

**Failure:** past compute conditions, model scale, data quality, or implementation bugs become permanent dogma.

**Required closure:** failure records bind exact conditions and explicit reopen triggers.

**Disposition:** COVERED IN PRINCIPLE — enforce in B3/B6/B10.

---

## B0-R9 — Tool competence can become hidden tool dependence

**Attack:** model appears strong because Python/retrieval scaffolding performs most of the task.

**Failure:** cognitive model capability and cognitive system capability are conflated.

**Required closure:** maintain separate assessments for:

- CognitiveArtifact;
- CognitiveRuntime;
- CognitiveSystem.

**Disposition:** CLOSED BY MF-A001 conceptually; test in B4/B7.

---

## B0-R10 — Open-weight reputation can contaminate base-model tournament

**Attack:** public leaderboard status influences shortlist, stopping rules, or interpretation.

**Failure:** tournament becomes confirmation exercise.

**Required closure:** candidate inclusion criteria and local evaluation protocol frozen before local scores are visible.

**Disposition:** B5 requirement.

---

## B0-R11 — Hidden holdout access becomes implicit authority

**Attack:** an agent that can inspect hidden evaluation artifacts can indirectly choose models/recipes and leak the answers.

**Failure:** evaluator independence collapses.

**Required closure:** holdout access is a capability/authority boundary; builder runtime must not receive hidden payloads.

**Disposition:** CONFIRMED — B4 hard gate.

---

## B0-R12 — Checkpoint selection can become retrospective tuning

**Attack:** many checkpoints are evaluated and the best is selected without accounting for repeated selection.

**Failure:** hidden multiple testing.

**Required closure:** checkpoint-selection policy frozen in recipe; final promotion requires separate confirmation evaluation.

**Disposition:** B4/B6.

---

## B0-R13 — Cost controls can bias against negative results

**Attack:** failed runs are truncated/hidden because they consume budget without producing a usable model.

**Failure:** economic pressure creates publication bias.

**Required closure:** negative/failed run receipts are first-class outputs and count as experiment completion when scientifically informative.

**Disposition:** B1/B6.

---

## B0-R14 — Framework adapters can smuggle semantics

**Attack:** a Hugging Face/Unsloth/JAX adapter silently changes tokenizer behavior, padding, precision, optimizer semantics, or checkpoint loading.

**Failure:** “same model” is not actually same experiment.

**Required closure:** framework adapter owns an explicit semantic translation/conformance record.

**Disposition:** B1/B3/B6.

---

## B0-R15 — Synthetic data self-consumption loop

**Attack:** model-generated examples recursively dominate future training.

**Failure:** Foundry becomes self-referential and loses external grounding.

**Required closure:** synthetic data remains separately tagged, source-model lineage preserved, and human/external truth controls retained.

**Disposition:** B2/B3/B6.

---

## B0-R16 — Dataset quality score becomes false authority

**Attack:** one numeric quality score hides licensing, contamination, diversity, recency, correctness, and representativeness tradeoffs.

**Failure:** scalar Goodharting.

**Required closure:** data quality is a vector + reasoned disposition, not one master score.

**Disposition:** B2/B3.

---

## B0-R17 — “Scientific method” fine-tuning can cause style mimicry

**Attack:** the model learns to say “insufficient evidence,” “falsify,” etc. without actually behaving scientifically.

**Failure:** epistemic theater.

**Required closure:** evaluation scores actions/outcomes, not wording alone; tool-use and experiment-design tasks must reveal whether behavior matches claims.

**Disposition:** B4/B7.

---

## B0-R18 — Model-generated benchmark contamination

**Attack:** same model family helps author benchmark tasks and later competes on them.

**Failure:** hidden evaluator-model coupling.

**Required closure:** benchmark authorship/model lineage recorded; high-consequence confirmation includes independently authored or procedurally generated tasks.

**Disposition:** B4.

---

## B0-R19 — Operator can accidentally destroy blind discovery

**Attack:** operator discusses CEREBUS terminology in prompts/logs/working context before B9.

**Failure:** blind condition contaminated despite dataset partitions being clean.

**Required closure:** blind discovery includes **context exposure controls**, not only dataset controls.

**Disposition:** CONFIRMED — B9 and B4 sealed-context contract.

---

## B0-R20 — Model Foundry success can pressure OCE authority expansion

**Attack:** a highly capable specialist earns broader autonomous permissions because it is “trusted.”

**Failure:** capability→authority creep.

**Required closure:** Foundry certification never grants authority; it emits evidence/candidate status only.

**Disposition:** CLOSED CONCEPTUALLY; must remain OCE integration invariant.

---

# 2. Required B0 amendments / carry-forward contracts

MF-B0 is viable if the following become binding in downstream dossiers:

1. sandbox-local OCE substitutes carry explicit replacement/deletion contracts;
2. runtime output enters `Observation`, not institutional `Evidence`, by default;
3. rights basis is explicit and UNKNOWN fails away from training;
4. experiment question/protocol precedes compute-provider selection;
5. reproducibility level is typed rather than binary;
6. hidden-holdout access is an authority/capability boundary;
7. checkpoint selection and repeated evaluation are treated as multiplicity;
8. failed/negative runs remain first-class evidence;
9. framework adapters require semantic conformance records;
10. synthetic-data lineage never disappears;
11. data/evaluation quality remains vector-valued;
12. scientific behavior is evaluated behaviorally, not stylistically;
13. benchmark author/model lineage is visible;
14. blind discovery controls working-context exposure as well as dataset exposure;
15. capability certification cannot expand authority.

---

# 3. Gate decision

**Decision:** `PASS_MF_B0_ADVERSARIAL_REVIEW_WITH_BINDING_CARRYFORWARDS`

MF-B0 does not show an architecture-level contradiction that requires rewriting the Model Foundry concept.

It does reveal implementation traps that must be closed concretely by MF-B1 through MF-B4 before any material training program is authorized.

The correct next planning sequence is therefore:

`MF-B1 Compute/Experiment Resource Layer -> MF-B2 Data Constitution -> MF-B3 Dataset Refinery -> MF-B4 Frozen Evaluation Institution`

No model-training master prompt is authorized yet.
