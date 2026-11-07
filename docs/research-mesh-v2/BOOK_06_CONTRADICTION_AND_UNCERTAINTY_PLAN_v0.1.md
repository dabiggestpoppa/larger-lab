# OCE Research Mesh V2 — Book 6 Plan
## Contradiction & Uncertainty

**Document ID:** RMV2-B6-PLAN-001  
**Version:** 0.1  
**Branch:** `agent/oce-research-mesh-v2`  
**Status:** PLANNING BASELINE — NOT YET FROZEN  
**System role:** standalone-first research institution, OCE-compatible by contract, Hermes-operated  
**Scope:** uncertainty decomposition, contradiction adjudication, discriminating-evidence planning, reopenability, escalation/stop rules  
**Parents:** Books 1–5

---

## 0. Book 6 mission

Book 6 turns claim-level evidence structure into explicit uncertainty structure.

Book 5 answers:

> What claims exist, what evidence bears on them, what depends on what, and where do comparable claims conflict?

Book 6 answers:

> Why are we uncertain, what kind of contradiction exists, what evidence would actually discriminate among competing explanations, when should the institution continue researching, when should it preserve unresolved state, and when must it stop or ask the operator?

The governing path is:

```text
Claims + ClaimEvidenceLinks
        ↓
Corroboration / contradiction structures
        ↓
Uncertainty decomposition
        ↓
Comparability / admissibility checks
        ↓
Competing explanation set
        ↓
Discriminator identification
        ↓
Evidence-needed plan
        ↓
Resolve / qualify / remain unresolved / reopen / escalate
        ↓
UncertaintyReceipt
        ↓
Book 7 Synthesis & Dossiers
```

Hard rule:

> Uncertainty is not one number. Contradiction is not a vote. Absence of resolution is not failure.

Book 6 adopts the institutional stress-suite laws:

- no scalar transition authority;
- evaluation contracts freeze within a run/window;
- unresolved states need no forced classification;
- negative knowledge remains reopenable unless explicitly and validly sealed;
- provenance survives every lifecycle transition;
- same inputs + same contract versions => same deterministic resolution outcome where the rules are deterministic.

---

# 1. Book structure

Book 6 contains five chapters with five sections each.

| Chapter | Name | Primary question |
|---|---|---|
| B6.C1 | Uncertainty Model | What kinds of uncertainty exist and how are they represented? |
| B6.C2 | Contradiction Adjudication | When are competing claims truly contradictory and what explains disagreement? |
| B6.C3 | Discriminating Evidence & Research Closure | What new evidence could actually reduce uncertainty? |
| B6.C4 | Lifecycle, Reopening, Stop & Escalation | When do we resolve, remain unresolved, reopen, stop, or ask the operator? |
| B6.C5 | Qualification & Book 7 Handoff | How do we prove uncertainty handling does not fabricate certainty or mutate criteria mid-run? |

Book 6 exits only when uncertainty is decomposed into inspectable channels, contradiction classes are adjudicated under frozen contracts, discriminating evidence is explicit, unresolved states remain durable, reopening is provenance-preserving, and stop/escalation behavior is deterministic and fail-closed where required.

---

# 2. B6.C1 — Uncertainty Model

## B6.C1.S1 — Uncertainty taxonomy

Define first-class uncertainty classes.

Initial classes:

- EVIDENCE_INSUFFICIENCY
- EVIDENCE_CONFLICT
- SCOPE_UNCERTAINTY
- POPULATION_UNCERTAINTY
- TEMPORAL_UNCERTAINTY
- DEFINITIONAL_UNCERTAINTY
- MEASUREMENT_UNCERTAINTY
- METHODOLOGICAL_UNCERTAINTY
- MODEL_UNCERTAINTY
- IDENTITY_UNCERTAINTY
- SOURCE_PROVENANCE_UNCERTAINTY
- DEPENDENCY_UNCERTAINTY
- EXTERNAL_VALIDITY_UNCERTAINTY
- RIGHTS_OR_ACCESS_LIMITATION
- COVERAGE_UNCERTAINTY
- REVISION_UNCERTAINTY
- UNKNOWN_UNCERTAINTY

These classes may coexist.

A claim can have strong direct evidence and still carry high external-validity uncertainty.

---

## B6.C1.S2 — UncertaintyVector contract

Define `UncertaintyVector`.

Minimum dimensions:

```text
evidence_sufficiency
evidence_conflict
scope_clarity
population_clarity
temporal_stability
definition_stability
measurement_reliability
method_robustness
model_dependence
identity_confidence
provenance_completeness
dependency_knownness
external_validity
coverage_completeness
revision_stability
rights_access_completeness
```

Each dimension stores:
- state;
- basis;
- source/claim refs;
- unknown reason;
- policy version;
- last evaluated generation.

Initial states:

- LOW_UNCERTAINTY
- MODERATE_UNCERTAINTY
- HIGH_UNCERTAINTY
- BLOCKING_UNCERTAINTY
- NOT_APPLICABLE
- UNKNOWN

No weighted sum is canonical.

---

## B6.C1.S3 — Evidence channel preservation

Book 5 evidence channels remain intact.

Book 6 may interpret but not overwrite:

```text
direct_primary_evidence
replication_evidence
methodological_support
independent_dataset_support
secondary_synthesis
mechanistic_support
external_validity
contradictory_evidence
negative_evidence
provenance_quality
coverage_completeness
```

Any uncertainty conclusion must point back to the channels that produced it.

A derived uncertainty label with no channel basis is invalid.

---

## B6.C1.S4 — Unknown versus adverse

Unknown is not the same as negative.

Examples:

```text
funding independence = UNKNOWN
!=
funding dependence = DEPENDENT

replication evidence = UNKNOWN
!=
failed replication

coverage incomplete
!=
evidence of absence
```

Book 6 must preserve this distinction in every summary and downstream handoff.

---

## B6.C1.S5 — UncertaintyReceipt

Every decision-grade uncertainty evaluation emits a receipt.

Minimum fields:

```text
uncertainty_receipt_id
claim_ids[]
contradiction_ids[]
corroboration_ids[]
uncertainty_vector
policy_versions
evaluation_contract_id
input_generation_ids[]
created_at
deterministic_components[]
model_assisted_components[]
unresolved_dimensions[]
blocking_dimensions[]
receipt_digest
```

### Gate C1

**PASS_B6_C1_UNCERTAINTY_MODEL** requires:
- uncertainty taxonomy encoded;
- vector model implemented;
- unknown/adverse distinction preserved;
- no scalar truth authority;
- every uncertainty assessment has channel provenance and receipt.

---

# 3. B6.C2 — Contradiction Adjudication

## B6.C2.S1 — Frozen comparability contract

Before adjudicating contradiction, freeze a comparison contract.

A `ComparisonContract` includes:

```text
comparison_contract_id
claim_a_id
claim_b_id
scope_fields
population_fields
temporal_fields
definition_fields
measurement_fields
method_fields
effect_fields
admissibility_rules
blocking_conditions
policy_version
created_at
```

Once evaluation starts, this contract cannot change mid-run.

Changing criteria requires:
- terminate/supersede current run;
- create new comparison contract;
- preserve prior result.

---

## B6.C2.S2 — Contradiction cause model

For comparable claims, disagreement may be explained by:

- TRUE_EFFECT_CONFLICT
- POPULATION_HETEROGENEITY
- TEMPORAL_REGIME_CHANGE
- DEFINITION_SHIFT
- MEASUREMENT_DIFFERENCE
- METHOD_DIFFERENCE
- DATASET_DIFFERENCE
- IMPLEMENTATION_DIFFERENCE
- SAMPLE_SIZE_OR_POWER
- REVISION_OR_VERSION_DIFFERENCE
- DEPENDENCY_ARTIFACT
- SELECTION_OR_PUBLICATION_BIAS_CANDIDATE
- SOURCE_ERROR_CANDIDATE
- UNKNOWN_CAUSE

Multiple causes may coexist.

No single "contradiction resolved" flag is sufficient.

---

## B6.C2.S3 — CompetingExplanationSet

Contradictions produce competing explanations.

Define:

```text
explanation_set_id
contradiction_id
explanations[]
supporting_evidence_by_explanation
contradicting_evidence_by_explanation
assumptions_by_explanation
required_discriminators[]
eliminated_explanations[]
unresolved_explanations[]
generation_id
```

Each explanation must be evidence-linked.

LLM-generated explanations are hypotheses until supported.

---

## B6.C2.S4 — Adjudication outcomes

Initial adjudication outcomes:

- RESOLVED_TRUE_CONTRADICTION
- RESOLVED_SCOPE_DIFFERENCE
- RESOLVED_POPULATION_DIFFERENCE
- RESOLVED_TEMPORAL_DRIFT
- RESOLVED_METHOD_DIFFERENCE
- RESOLVED_DEFINITION_DIFFERENCE
- RESOLVED_DATASET_DIFFERENCE
- MULTICAUSAL_DIFFERENCE
- NOT_COMPARABLE
- INSUFFICIENT_EVIDENCE
- UNRESOLVED_CONTRADICTION
- OPERATOR_REVIEW_REQUIRED

Outcome must name:
- comparison contract;
- evidence basis;
- rejected alternatives;
- unresolved discriminators.

---

## B6.C2.S5 — No-majority / no-popularity firewall

Forbidden adjudication shortcuts:

- paper count majority;
- citation count;
- venue prestige;
- author prestige;
- provider count;
- LLM agreement count;
- embedding similarity;
- reranker score;
- "consensus" inferred from repeated citation.

These may be descriptive metadata, never contradiction authority.

### Gate C2

**PASS_B6_C2_CONTRADICTION_ADJUDICATION** requires:
- frozen comparison contracts;
- multi-cause model;
- competing explanations;
- explicit unresolved discriminator list;
- no majority/popularity shortcut;
- changed criteria create a new run rather than rewriting old result.

---

# 4. B6.C3 — Discriminating Evidence & Research Closure

## B6.C3.S1 — Discriminator model

A discriminator is evidence that would distinguish among competing explanations.

Define `EvidenceDiscriminator`:

```text
discriminator_id
target_contradiction_id
target_explanation_ids[]
question
required_evidence_type
required_population_or_scope
required_method_property
required_time_window
minimum_provenance_requirements
expected_resolution_effect
cost_class
access_constraints
rights_constraints
priority_basis
status
```

Examples:
- independent replication on a new dataset;
- same method on different population;
- same population under standardized measurement;
- exact source version;
- primary dataset inspection;
- preregistration/protocol comparison;
- temporal replication after regime change.

---

## B6.C3.S2 — Information-gain framing without false precision

Research priority may use ordinal or vector information-gain concepts.

Possible dimensions:

- number of competing explanations affected;
- blocking uncertainty reduced;
- independence gained;
- directness gained;
- scope clarified;
- temporal ambiguity reduced;
- provenance repaired;
- access feasibility;
- cost.

Book 6 must not invent precise expected information gain when inputs do not support it.

Initial priority labels:

- CRITICAL_DISCRIMINATOR
- HIGH_VALUE
- MODERATE_VALUE
- LOW_VALUE
- REDUNDANT
- NOT_ACTIONABLE
- UNKNOWN_VALUE

---

## B6.C3.S3 — EvidenceNeed / next-evidence contract

Define `EvidenceNeed`.

Minimum fields:

```text
evidence_need_id
origin_claim_ids[]
origin_contradiction_ids[]
origin_uncertainty_receipt_id
need_type
exact_question
discriminator_ids[]
source_classes_preferred[]
source_classes_excluded[]
scope
stopping_conditions
budget_envelope
priority
created_at
status
```

This becomes the core handoff to Book 8 Research Orchestration later.

Book 6 identifies what evidence is needed. It does not autonomously launch unbounded research.

---

## B6.C3.S4 — Closure conditions

A research question/contradiction may reach:

- RESOLVED_WITHIN_SCOPE
- QUALIFIED_WITHIN_SCOPE
- UNRESOLVED_BUT_STABLE
- INSUFFICIENT_EVIDENCE
- ACCESS_BLOCKED
- RIGHTS_BLOCKED
- BUDGET_EXHAUSTED
- DIMINISHING_RETURNS
- NO_ACTIONABLE_DISCRIMINATOR
- OPERATOR_STOP
- OPERATOR_REVIEW_REQUIRED

Closure is always scoped.

"Resolved" never means universally true.

---

## B6.C3.S5 — Saturation and diminishing returns

Research may stop when additional evidence is not materially changing the uncertainty structure.

Saturation signals may include:
- repeated retrieval of same dependent evidence;
- no new independent source class;
- no discriminator satisfied;
- new sources repeat same method/data;
- no uncertainty dimension changes across bounded refreshes.

But saturation must be versioned and explicit.

No silent "good enough" heuristic.

### Gate C3

**PASS_B6_C3_DISCRIMINATING_EVIDENCE** requires:
- discriminators first-class;
- EvidenceNeed contract implemented;
- closure states explicit;
- saturation policy versioned;
- no invented precision;
- unresolved stable state allowed.

---

# 5. B6.C4 — Lifecycle, Reopening, Stop & Escalation

## B6.C4.S1 — Uncertainty lifecycle

Define lifecycle:

```text
OPEN
ASSESSED
DISCRIMINATORS_IDENTIFIED
EVIDENCE_REQUESTED
PARTIALLY_RESOLVED
RESOLVED_WITHIN_SCOPE
UNRESOLVED_STABLE
BLOCKED
ARCHIVED
REOPENED
SUPERSEDED
```

Lifecycle state does not imply authority or truth.

ARCHIVED preserves provenance.

REOPENED creates a new generation linked to the prior closure state.

---

## B6.C4.S2 — Reopenability doctrine

Negative and unresolved knowledge is reopenable by default.

Reopen triggers include:
- new independent evidence;
- retraction/correction of material source;
- new source version;
- changed method;
- changed population;
- new discriminator;
- identity correction;
- rights/access change;
- new operator instruction.

A prior result remains historically valid as "what the institution concluded under that evidence/contract."

---

## B6.C4.S3 — Stop rules

Hard stops include:

- rights prohibition;
- authority prohibition;
- budget hard ceiling;
- unsafe/unapproved source access;
- contract corruption;
- provenance break;
- operator stop;
- evaluation contract unavailable;
- unbounded recursion risk.

Soft stops include:
- diminishing returns;
- no actionable discriminator;
- source saturation;
- repeated dependent evidence;
- low-priority unresolved state.

Soft stop never converts unresolved to resolved.

---

## B6.C4.S4 — Operator escalation

Define `OperatorReviewRequest`.

Escalate when:
- policy conflict;
- two valid institutional rules conflict;
- high-impact ambiguity cannot be resolved;
- irreversible/high-authority action would be required;
- rights classification uncertain for sensitive material;
- contradiction has no admissible automated adjudication path;
- evaluation contract itself is disputed.

Hermes may prepare the packet.

Hermes may not self-answer the escalation.

---

## B6.C4.S5 — Lifecycle receipts and supersession

Every transition emits:

`UncertaintyLifecycleReceipt`

with:
- prior state;
- next state;
- trigger;
- evidence refs;
- contract version;
- authority basis;
- timestamp;
- supersession refs.

No lifecycle transition deletes old receipts.

### Gate C4

**PASS_B6_C4_LIFECYCLE_ESCALATION** requires:
- reopenability works;
- hard/soft stop separated;
- operator escalation typed;
- Hermes cannot self-ratify escalations;
- old closure states remain inspectable after reopen.

---

# 6. B6.C5 — Qualification & Book 7 Handoff

## B6.C5.S1 — Golden uncertainty corpus

Build a multi-domain offline corpus covering:

1. true contradiction;
2. apparent contradiction from population difference;
3. temporal drift;
4. definition mismatch;
5. measurement mismatch;
6. method mismatch;
7. same dataset / fake replication;
8. unknown dependency;
9. retracted supporting source;
10. future correction;
11. insufficient sample;
12. access-blocked evidence;
13. rights-blocked evidence;
14. unresolved but stable question;
15. new evidence reopening archived conclusion;
16. conflicting evaluation criteria;
17. no actionable discriminator;
18. high-value discriminator;
19. model-generated explanation unsupported by evidence;
20. operator escalation case.

---

## B6.C5.S2 — Deterministic replay and frozen evaluation

For deterministic resolution rules:

> same inputs + same contract versions + same policy versions => same outcome.

Qualification must prove:
- comparison contract cannot mutate mid-run;
- changing contract creates a new run ID;
- receipt identifies tested input generations;
- absent/empty verification inputs fail closed;
- no favorable default.

Model-assisted hypothesis generation may vary, but adjudication state must record that nondeterminism.

---

## B6.C5.S3 — Uncertainty integrity tests

Integrity checks include:

- every uncertainty dimension has basis or UNKNOWN reason;
- every resolved contradiction cites comparison contract;
- every competing explanation has evidence/assumption refs;
- every EvidenceNeed traces to uncertainty/contradiction;
- every closure state has stopping basis;
- every reopen links to prior generation;
- no resolved state hides blocking uncertainty;
- no operator-review state is auto-completed.

---

## B6.C5.S4 — Book 6 adversarial matrix

| ID | Attack / case | Required result |
|---|---|---|
| B6-A01 | evidence channels averaged into one transition score | REFUSE |
| B6-A02 | UNKNOWN treated as favorable | REFUSE |
| B6-A03 | criteria changed mid-adjudication | REFUSE / NEW RUN REQUIRED |
| B6-A04 | unresolved contradiction forced into nearest class | REFUSE |
| B6-A05 | paper majority resolves contradiction | REFUSE |
| B6-A06 | high-citation source overrides direct contradictory evidence | REFUSE |
| B6-A07 | model-generated explanation treated as established cause | REFUSE |
| B6-A08 | missing provenance dimension defaults LOW_UNCERTAINTY | REFUSE |
| B6-A09 | closure says RESOLVED while blocking uncertainty remains | REFUSE |
| B6-A10 | budget exhaustion converted to evidence insufficiency without label | REFUSE |
| B6-A11 | archived unresolved state cannot reopen on new evidence | REFUSE |
| B6-A12 | reopening deletes prior conclusion | REFUSE |
| B6-A13 | soft saturation converts unresolved to resolved | REFUSE |
| B6-A14 | Hermes answers operator escalation itself | REFUSE |
| B6-A15 | no discriminator exists and system invents one without basis | REFUSE |
| B6-A16 | dependent evidence treated as information gain | REFUSE |
| B6-A17 | evaluation input absent and gate passes | REFUSE |
| B6-A18 | same deterministic inputs produce different adjudication | REFUSE |
| B6-A19 | all model assistance disabled | DETERMINISTIC/MANUAL MODE PASS |
| B6-A20 | unresolved stable state persists across replay | PASS |

---

## B6.C5.S5 — Freeze package and Book 7 handoff

Book 6 freeze emits:

- uncertainty taxonomy fingerprint;
- UncertaintyVector contract;
- ComparisonContract fingerprint;
- contradiction-cause vocabulary;
- EvidenceDiscriminator schema;
- EvidenceNeed schema;
- closure-state policy;
- saturation policy;
- reopenability policy;
- operator-escalation schema;
- golden uncertainty corpus;
- adversarial qualification receipt;
- deterministic replay receipt;
- known limitations;
- Book 7 handoff manifest.

### Gate C5

**PASS_B6_C5_UNCERTAINTY_QUALIFICATION** requires:
- C1–C4 gates pass;
- A01–A20 pass;
- no scalar transition authority;
- no favorable defaults;
- frozen evaluation proven;
- unresolved persistence proven;
- reopenability proven;
- operator escalation firewall proven.

---

# 7. Book 6 uncertainty philosophy

The system must be able to say:

```text
We have strong direct evidence,
but weak external validity,
a method-specific contradiction,
unknown funding independence,
and insufficient temporal replication.
```

That is preferable to:

```text
confidence = 71%
```

Ergonomic summaries may exist later, but they are views over the vector.

The vector remains the institutional record.

---

# 8. Contradiction philosophy

Contradiction is not inherently a defect.

A contradiction can reveal:

- hidden regime changes;
- population heterogeneity;
- measurement differences;
- method sensitivity;
- version drift;
- invalid assumptions;
- real instability in the phenomenon.

Therefore contradiction should often produce **research direction**, not automatic winner selection.

Book 6 converts contradictions into discriminating questions.

---

# 9. Planned implementation layout

```text
oce/research_mesh_v2/
  uncertainty/
    __init__.py
    vocabulary.py
    models.py
    vectors.py
    receipts.py

    comparison/
      contracts.py
      comparability.py
      adjudication.py
      causes.py
      explanations.py

    discriminators/
      models.py
      identify.py
      priority.py
      evidence_need.py

    closure/
      states.py
      saturation.py
      stop_rules.py
      reopen.py

    escalation/
      models.py
      operator_review.py
      firewall.py

    lifecycle/
      state_machine.py
      receipts.py

  tests/book_06/
    test_c1_uncertainty_model.py
    test_c2_contradiction_adjudication.py
    test_c3_discriminating_evidence.py
    test_c4_lifecycle_escalation.py
    test_c5_qualification.py
    test_b6_adversarial.py
    fixtures/uncertainty/
```

---

# 10. Book 6 implementation sequence

## B6-I0 — Uncertainty archaeology + corpus
- inspect Book 5 claim/contradiction structures;
- inspect institutional stress-suite vector/frozen-evaluation laws;
- build golden uncertainty corpus;
- identify deterministic versus model-assisted components.

**Exit:** `PASS_B6_I0_UNCERTAINTY_CHARACTERIZATION`

## B6-I1 — C1 uncertainty model
Implement taxonomy, UncertaintyVector and receipts.

**Exit:** `PASS_B6_C1_UNCERTAINTY_MODEL`

## B6-I2 — C2 contradiction adjudication
Implement ComparisonContract, cause model, competing explanations and outcomes.

**Exit:** `PASS_B6_C2_CONTRADICTION_ADJUDICATION`

## B6-I3 — C3 discriminators / EvidenceNeed
Implement discriminator identification, priority and closure semantics.

**Exit:** `PASS_B6_C3_DISCRIMINATING_EVIDENCE`

## B6-I4 — C4 lifecycle/reopen/stop/escalate
Implement lifecycle state machine, hard/soft stops and operator firewall.

**Exit:** `PASS_B6_C4_LIFECYCLE_ESCALATION`

## B6-I5 — deterministic replay + frozen evaluation
Prove same inputs/contracts replay; forbid favorable defaults and mid-run criteria mutation.

**Exit:** `PASS_B6_FROZEN_EVALUATION_REPLAY`

## B6-I6 — explanation/audit surface
Expose compact and full uncertainty/contradiction traces.

**Exit:** `PASS_B6_UNCERTAINTY_EXPLAINABILITY`

## B6-I7 — adversarial qualification
Run golden corpus and A01–A20.

**Exit:** `PASS_B6_C5_UNCERTAINTY_QUALIFICATION`

## B6-I8 — freeze
Emit fingerprints, receipts, limitations and Book 7 handoff.

**Exit:** `PASS_BOOK_6_CONTRADICTION_AND_UNCERTAINTY`

---

# 11. Book 6 hard invariants

1. Uncertainty is a vector, not a scalar.
2. Unknown never defaults favorable.
3. Contradiction requires frozen comparability rules.
4. Evaluation criteria cannot change mid-run.
5. Majority vote cannot resolve epistemic conflict.
6. Popularity cannot resolve epistemic conflict.
7. Model hypotheses are not adjudicated causes without evidence.
8. Every uncertainty dimension has basis or unknown reason.
9. Blocking uncertainty cannot be hidden by a summary label.
10. Every resolution is scoped.
11. Unresolved is a valid durable state.
12. Negative knowledge is reopenable by default.
13. Reopening preserves prior conclusion history.
14. Saturation can stop research but cannot manufacture resolution.
15. Budget/access/rights stops remain distinct from epistemic insufficiency.
16. Discriminators must be evidence-grounded.
17. EvidenceNeeds are bounded and traceable.
18. Operator escalation cannot be self-ratified by Hermes.
19. Deterministic components replay identically under same versions.
20. Book 7 receives unresolved structure, not cleaned-up certainty.

---

# 12. Explicit non-goals for Book 6

Do not build yet:
- narrative synthesis;
- executive research dossiers;
- doctrine candidates;
- autonomous research orchestration;
- recurring research agents;
- OCE/QCAE live integration;
- institutional promotion.

Those belong to Books 7+.

---

# 13. Book 7 handoff

Book 7 — Synthesis & Dossiers — receives:

- claims and claim states;
- evidence-channel vectors;
- UncertaintyVectors;
- contradiction adjudications;
- CompetingExplanationSets;
- EvidenceDiscriminators;
- EvidenceNeeds;
- closure states;
- unresolved dimensions;
- operator-review flags;
- complete source/provenance chain;
- all contract/policy generation pins.

Book 7 may compress this structure into readable synthesis and decision-support artifacts. It may not hide unresolved contradictions, discard blocking uncertainty, convert scoped resolution into universal truth, or promote doctrine.

**Final gate:** `PASS_BOOK_6_CONTRADICTION_AND_UNCERTAINTY`
