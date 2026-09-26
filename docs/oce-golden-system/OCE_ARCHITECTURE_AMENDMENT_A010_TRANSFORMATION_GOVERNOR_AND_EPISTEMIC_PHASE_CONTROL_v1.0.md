# OCE Golden System
## Amendment A-010 — Transformation Governor and Epistemic Phase Control

**Document ID:** OCE-AMEND-A010  
**Version:** 1.0  
**Status:** PROPOSED FOR OPERATOR RATIFICATION  
**Parents:** OCE Constitution 1.1; A-005; A-009 proposed  
**Architectural basis:** `LARGER_LAB_INSTITUTIONAL_ARCHITECTURE_v1.1.md`  
**Build authorization:** NONE

---

## 1. Decision

OCE shall not permit any single agent, score, anomaly count, model, metric, or rule to control whether the institution remains in a stable operating epoch or enters a transformation window.

The stabilize/transform decision shall be governed by a **Transformation Governor** that combines independent evidence channels, scope classification, persistence, reversibility, dependency load, and operator authority.

The Governor is not an autonomous sovereign. It is a constitutional phase-control mechanism whose purpose is to prevent both pathological ossification and pathological self-reconstruction.

---

## 2. The problem being solved

A-009 defines stable epochs and transformation windows but leaves a critical control problem:

> Who decides when current structure deserves preservation and when current structure itself has become the problem?

Naive solutions fail symmetrically:

- **PO-only switch** creates epistemic sovereignty in one adaptive reasoner.
- **hard-rule switch** can freeze obsolete assumptions into permanent law.
- **anomaly-count switch** can reward noise and cause chronic paradigm churn.
- **operator-only switch** preserves safety but prevents meaningful semi-autonomous institutional learning.
- **single composite score** becomes a Goodhart target and obscures disagreement among evidence classes.

A-010 therefore uses distributed evidence and staged authority.

---

## 3. Transformation Governor state machine

Canonical phase states:

```text
STABLE
  |
  | ordinary anomaly / contradiction
  v
WATCH
  |
  | persistence + materiality + independence
  v
ESCALATION_REVIEW
  |
  +----------------------------+
  |                            |
  v                            v
HOMEOSTATIC_REPAIR       TRANSFORMATION_CANDIDATE
                               |
                               | admissibility + authorization
                               v
                    TRANSFORMATION_WINDOW
                               |
                  sandbox / compare / falsify
                               |
                               v
                         RECONSOLIDATION
                          /          \
                         v            v
                    NEW_STABLE     ROLLBACK
```

No direct path from ordinary anomaly to architecture mutation is permitted.

---

## 4. Evidence channels

The Governor consumes a vector of evidence channels rather than one scalar.

### 4.1 Reliability degradation

Evidence that the current model or procedure no longer performs its intended function.

Examples:

- repeated deterministic failure;
- falling predictive reliability;
- strategy decay unexplained by execution cost alone;
- repeated worker/task failure under unchanged task class;
- worsening reproduction rate.

### 4.2 Exception burden

Evidence that the current structure requires increasing patches, overrides, special cases, or manual intervention.

High exception burden is evidence that the abstraction may be wrong even if surface output remains acceptable.

### 4.3 Independent contradiction

Contradictory evidence generated from sufficiently independent sources, models, datasets, methods, or runtime paths.

Correlated repetitions do not count as independent confirmation merely because they are numerous.

### 4.4 Unresolved-pattern density

Growth in credible observations that current ontology cannot classify without distortion.

The Governor must distinguish unresolved-pattern growth from simple data-quality failure.

### 4.5 Dependency centrality

How much of the institution depends on the challenged object.

A highly central assumption receives slower transformation authority and broader review than a leaf-level hypothesis.

### 4.6 External-environment shift

Evidence that the operating environment changed materially:

- market regime;
- provider semantics;
- regulation;
- execution venue;
- dependency ecosystem;
- model/runtime behavior;
- hardware/platform constraints.

This prevents internal blame when the world changed.

### 4.7 Opportunity cost of stability

Evidence that preserving the existing structure blocks high-value learning or capability.

This channel must never alone authorize transformation.

### 4.8 Cost and reversibility

Estimated cost, blast radius, and reversibility of candidate reconstruction.

Cheap, reversible ontology experiments can open with lower authority than irreversible authority or capital changes.

---

## 5. No scalar phase score

The Governor may compute derived summaries for operator legibility, but no single transformation score may become sufficient authority.

The system must preserve the shape of disagreement across evidence channels.

Example:

```text
reliability degradation     HIGH
exception burden            HIGH
independent contradiction   MEDIUM
unresolved-pattern density  LOW
dependency centrality       VERY HIGH
environment shift           HIGH
reversibility               LOW
```

This vector communicates a materially different situation from a mathematically identical aggregate produced by many low-grade anomalies.

---

## 6. Persistence and hysteresis

The Governor shall include hysteresis to prevent phase flapping.

### Entering WATCH

May occur from one material contradiction or a cluster of weaker signals.

### Entering ESCALATION_REVIEW

Requires either:

- persistent evidence across multiple observations/time windows; or
- one severe high-confidence contradiction with material consequences.

### Opening a TRANSFORMATION_WINDOW

Requires stronger evidence than remaining in one.

### Closing the window / reconsolidating

Requires evidence that one candidate structure dominates alternatives for the relevant scope, not merely that the incumbent was weakened.

The thresholds may be domain-specific but must be preregistered or operator-approved before evaluation where practical.

---

## 7. Scope ladder

Every challenged object is assigned the narrowest plausible structural level:

```text
L0  RESULT / OBSERVATION
L1  IMPLEMENTATION
L2  CAPABILITY / PROCEDURE
L3  METHOD / VALIDATION RULE
L4  MECHANISM / DOMAIN MODEL
L5  ONTOLOGY / DOMAIN ARCHITECTURE
L6  INSTITUTIONAL ARCHITECTURE
L7  AUTHORITY / CONSTITUTION
```

Escalation follows evidence, not frustration.

Repeated L0/L1 repairs with the same causal signature may promote review upward.

A high-level contradiction does not automatically invalidate all lower-level evidence.

---

## 8. Patch-pressure escalation

Introduce `PatchPressureRecord`.

It records when repeated local fixes accumulate around one underlying dependency, abstraction, or assumption.

Candidate fields:

- challenged object;
- patch count;
- exception count;
- time span;
- repeated causal signature;
- manual override frequency;
- downstream consumers;
- estimated structural level;
- recommended escalation level.

This prevents the institution from indefinitely repairing symptoms of a broken abstraction.

---

## 9. Transformation admissibility

A transformation candidate must satisfy all applicable conditions before mutation:

1. **Problem reality:** evidence supports that a material problem exists.
2. **Scope discipline:** the challenged layer is justified.
3. **Alternative existence:** at least one concrete alternative or experimental direction exists, unless the purpose is explicit ontology exploration.
4. **Discriminating evidence:** tests capable of separating incumbent and candidate models are identified.
5. **Containment:** the experiment can be isolated sufficiently for its risk class.
6. **Lineage:** incumbent state is fully reconstructable.
7. **Rollback:** rollback or irreversible-risk handling is explicit.
8. **Authority:** required operator/constitutional approval exists.
9. **No hidden self-interest:** a runtime cannot unilaterally change the evaluation standard or authority governing itself.

---

## 10. Distributed phase roles

The A-009 transformation roles are made operationally independent where material:

### Sentinel

Detects tension, anomalies, patch pressure, and drift. Cannot propose preferred architecture during first-pass detection when independence matters.

### Steward

Defends incumbent structure using its original evidence and current supporting evidence.

### Challenger

Builds the strongest case that the incumbent model is structurally inadequate.

### Explorer

Produces alternatives, including unresolved or ontology-expanding interpretations.

### Auditor

Designs and runs discriminating evidence collection. Should be shielded from the Integrator's preferred answer where feasible.

### Integrator

Finds the narrowest reconstruction supported by evidence.

### Governor

Evaluates phase-transition admissibility and authority state. It does not invent the preferred theory.

### Operator

Retains authority over high-AffectedSurface, constitutional, capital, destructive, or irreversible transitions.

Roles may be implemented by different runtimes or deterministic services. Role identity is more durable than implementation.

---

## 11. Independence budget

Transformation review consumes an explicit `IndependenceBudget`.

Independence is treated as a scarce epistemic resource.

The system records:

- which reviewers saw prior conclusions;
- which agents share model family/provider;
- shared source overlap;
- shared retrieval/context overlap;
- shared training/runtime lineage where known;
- whether experiments were independently specified;
- whether evidence was reproduced by a different implementation path.

The Governor can require stronger independence when:

- dependency centrality is high;
- irreversible consequences are possible;
- prior consensus is unusually strong;
- correlated-agent failure is suspected.

---

## 12. Counter-attractor protocol

When the institution exhibits suspiciously strong consensus or repeated self-reinforcement, the Governor may open a bounded `COUNTER_ATTRACTOR_REVIEW` without declaring the incumbent wrong.

Possible actions:

- fresh-context alternative derivation;
- outside-source search deliberately excluding dominant vocabulary;
- alternate model/runtime review;
- reverse-premise analysis;
- adversarial dataset split;
- replication from raw evidence rather than summaries;
- deliberate ontology-free description of observations.

The objective is not contrarianism. It is to test whether coherence survives independent reconstruction.

---

## 13. Novelty protection and anomaly quarantine

A credible anomaly can be preserved without destabilizing current production truth.

`UnresolvedPatternRecord` may live in an anomaly quarantine with:

- exact provenance;
- confidence;
- affected domains;
- candidate explanations;
- data-quality checks;
- related anomalies;
- revisit triggers.

This allows the institution to protect potentially paradigm-changing observations while avoiding premature ontology mutation.

---

## 14. Stable epoch contract

Every stable epoch should have a reconstructable `EpochManifest` containing:

- epoch ID;
- start cause;
- governing architecture versions;
- active ontologies;
- active high-dependency assumptions;
- active runtime certifications;
- major capabilities;
- known tensions;
- unresolved-pattern backlog;
- negative knowledge revisions;
- validation rules;
- operator ratifications;
- predecessor epoch;
- transformation evidence that created it.

Institutional time may therefore be queried by state epoch as well as wall-clock time.

---

## 15. Transformation window contract

A transformation window must define:

- exact challenged object(s);
- scope ceiling;
- allowed mutation surface;
- competing candidate models;
- discriminating tests;
- evidence budget;
- compute/time budget;
- independence requirements;
- rollback point;
- operator hold points;
- reconsolidation criteria;
- unresolved outcomes permitted.

The window may conclude with `NO_CHANGE` if evidence does not justify reconstruction.

Failure to choose is valid when the evidence remains insufficient.

---

## 16. Reconsolidation rule

A new stable epoch is not created because a novel candidate is exciting.

Reconsolidation requires evidence that the chosen structure offers a better institutional trade-off for the challenged scope, considering:

- explanatory compression;
- predictive/operational reliability;
- exception burden;
- falsifiability;
- complexity cost;
- compatibility with unaffected evidence;
- reversibility;
- downstream migration cost;
- uncertainty retained honestly.

Where two models remain genuinely non-dominated, the system may preserve a plural model state rather than force a winner.

---

## 17. Epistemic sovereignty firewall

No adaptive reasoner may simultaneously:

1. define the anomaly;
2. choose its own evaluation rule;
3. alter that evaluation rule;
4. certify the new rule;
5. grant itself expanded authority.

The more of these roles one runtime occupies, the stronger the required independent checks.

OCE's constitutional boundary remains outside adaptive-runtime preference.

---

## 18. Quant-specific phase control

Examples:

### Strategy degradation

Do not jump from PnL decay to parameter optimization.

Governor review distinguishes:

- data fault;
- implementation fault;
- cost/liquidity shift;
- regime shift;
- mechanism decay;
- portfolio interaction;
- ontology failure.

### Strategy-corpus research

A large number of failing variants from one mechanism family should increase mechanism-level tension more than raw failure count.

### New alpha family

Repeated `UNRESOLVED_PATTERN` records may justify an ontology-exploration window before any strategy is generated.

### CEREBUS

Manual doctrine remains authoritative within governed CEREBUS implementations, but repeated independently reproduced contradictions should create an amendment/evidence-review pathway rather than silent reinterpretation.

---

## 19. Crypto-specific phase control

Crypto Foundry and Sensor Fabric are natural proving grounds.

Examples:

- provider disagreement first challenges source/normalization layers, not field ontology;
- repeated sensor insufficiency may escalate to SearchDemand rather than model patching;
- repeated global/local divergence should preserve separate models unless transfer evidence appears;
- unresolved MECH/LF phenomena remain parked until sensor resolution improves;
- post-Sensor-Fabric MECH21/LF14 restart may compare old and new observation regimes as an explicit epoch boundary.

---

## 20. Failure modes of the Governor

The Governor itself must be red-teamed for:

- chronic conservatism;
- chronic transformation;
- anomaly inflation;
- metric gaming;
- consensus capture;
- reviewer monoculture;
- hidden dependence among supposedly independent agents;
- operator fatigue from over-escalation;
- transformation windows that never close;
- under-scoped local repair;
- over-scoped architecture rewrite;
- novelty bias;
- incumbent bias;
- inability to preserve plural models;
- silent change to threshold definitions.

Governor configuration changes are themselves governed structural changes.

---

## 21. Acceptance tests

A-010 is not implemented until evidence shows that:

1. one anomaly enters WATCH without mutating architecture;
2. repeated local patches escalate through PatchPressureRecord;
3. the Governor distinguishes local implementation failure from ontology-level tension;
4. correlated agent agreement is not counted as independent confirmation;
5. a transformation window can end in NO_CHANGE;
6. two non-dominated models can survive reconsolidation without forced consensus;
7. an adaptive agent cannot alter the rule used to certify itself;
8. a high-centrality change requires stronger independence/authority than a leaf change;
9. stable-epoch state is fully reconstructable from EpochManifest;
10. a counter-attractor review can challenge consensus without destabilizing canonical production state;
11. anomaly quarantine preserves novel evidence without premature promotion;
12. phase-transition thresholds cannot silently change during the evaluation they govern;
13. Quant strategy decay can be routed to the correct structural level before optimization;
14. Crypto sensor gaps can trigger search/research demand without forcing false model precision.

---

## 22. Ratification posture

Proposed operator decision:

`RATIFY_A010_TRANSFORMATION_GOVERNOR_AND_EPISTEMIC_PHASE_CONTROL`

Ratification changes architecture and future planning only. It authorizes no autonomous architecture mutation, model training, deployment, broker connection, capital action, or production self-modification.