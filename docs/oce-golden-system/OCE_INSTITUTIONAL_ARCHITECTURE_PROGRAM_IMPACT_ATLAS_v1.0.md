# OCE Golden System
## Institutional Architecture Program Impact Atlas

**Document ID:** OCE-IMPACT-IA-001  
**Version:** 1.0  
**Status:** PROPOSED CROSS-PROGRAM PATCH MAP — NO BUILD AUTHORIZATION  
**Inputs:** `LARGER_LAB_INSTITUTIONAL_ARCHITECTURE_v1.0.md`, A-004, proposed A-005 through A-008  
**Purpose:** Map institutional-intelligence changes into the Golden System without locally optimizing one block or silently rewriting ratified history.

---

## 1. Cross-program doctrine

The Golden System shall evolve from a program that can build governed systems into a program that can operate a continuously learning research institution.

The architecture remains:

```text
OPERATOR
   |
HERMES / CompanionRuntime
   |
bounded referrals
   v
PO / ExecutiveReasoner
   |
   v
OCE EPISTEMIC + CONSTITUTIONAL SPINE
   |
   +-------------------+--------------------+
   |                   |                    |
WORKER FABRIC      SCIENCE FABRIC     DOMAIN SYSTEMS
   |                   |                    |
OpenClaw/Pi/etc.      QCAE          Quant Lab / Crypto OS
   |                   |                    |
   +-------------------+--------------------+
                       |
             DETERMINISTIC KERNELS
                       |
                    EVIDENCE
                       |
                INSTITUTIONAL LEARNING
                       |
                 BETTER QUESTIONS
                       |
                AUTONOMOUS DISCOVERY
```

The architecture must preserve the existing castle doctrine and block gates. These amendments alter future contracts, not completed evidence.

---

## 2. Existing architecture retained

The following prior decisions remain strong and should not be discarded:

- Operator remains final authority.
- OCE remains canonical state/evidence/authority/recovery.
- PO remains the high-level OCE/Quant/Larger Lab operator.
- Hermes remains separate from PO and preferred for personal/companion continuity.
- Workers remain task-scoped with minimum context and authority.
- Local-first development/validation remains default.
- Quant research remains upstream of execution.
- B7 deterministic kernels remain the certification substrate.
- B9 remains separately authorized and capital-gated.
- Raw events, interpretation, and promoted lessons remain distinct.

The new architecture primarily increases abstraction quality, runtime neutrality, discovery autonomy, and compounding.

---

## 3. A-002 impact

### Preserve

- PO/Hermes separation.
- distinct memory namespaces.
- typed WorkReferral/OutcomePacket.
- Hermes cannot operate Quant/capital by default.
- agent memory is not OCE state.

### Revise

A-002 Section 7 currently treats Hermes as a permanent replacement for OpenClaw in the supplemental runtime role.

Future revision should instead define:

- `CompanionRuntime` as the durable role;
- Hermes as current preferred implementation;
- OpenClaw as eligible WorkerRuntime rather than competing personal runtime;
- runtime migration/certification rather than product replacement as the architectural mechanism.

No change is required to the constitutional separation between companion and executive cognition.

---

## 4. A-004 impact

A-004 remains directionally correct and becomes a foundational dependency.

Its AgentCockpit, CapabilityGraph, WorkGraph, OutcomePacket, ResumeCapsule, EvidenceGap, AffectedSurface, NegativeKnowledge, and ResourceBudget primitives should be elevated into B3/B4 shared contracts through A-005.

A-004's progressive context disclosure becomes the default context doctrine across PO, workers, scouts, and science agents.

---

## 5. B3 — OCE Constitutional Spine

B3 is the earliest block materially affected.

### B3.C1 Canonical Contracts

Future contract revisions should add or reserve identities for:

- ConstraintField;
- EvidenceGap;
- NegativeKnowledge;
- ResumeCapsule;
- AffectedSurface;
- AgentCockpit;
- CapabilityAtom / CapabilityEdge;
- SourceRecord / SourceReference;
- runtime certification records.

Do not force all objects into one mega-schema. Use small versioned contracts joined by stable identifiers.

### B3.C2 Authority Engine

Add role-neutral capability grants. Permissions target capability and effect classes, not product names.

Examples:

- `repo.read` rather than `openclaw.read_repo`;
- `sandbox.code.write` rather than `pi.write`;
- `quant.experiment.run` rather than `qcae.run`.

Runtime adapters consume grants; they do not define them.

### B3.C3 Event and State

Add event semantics for:

- evidence-gap creation/closure;
- negative-knowledge promotion/reopen;
- runtime admission/demotion;
- source discovery/intake;
- capability promotion/deprecation;
- context/resume checkpoints.

### B3.C4 Evidence System

Generalize evidence lineage beyond build artifacts to scientific and capability evidence while preserving domain-specific validators.

### B3.C5 Operational Integrity

Runtime swaps and scout failures must be restart-safe. OCE must remain operable if all adaptive-agent runtimes are unavailable.

### B3 build posture

Do not reopen completed B3 evidence merely because planning evolved. Introduce these additions only through explicitly authorized future amendments/increments after impact review.

---

## 6. B4 — PO Governed Builder

B4 is where A-004/A-005/A-007 become operational cognition.

### B4.C1 Intent and Reasoning

Goal decomposition should compile an initial ConstraintField and update it as evidence resolves uncertainty.

Alternatives should be pruned by constraints, negative knowledge, reversibility, expected information value, and capability cost.

### B4.C2 Memory and Context

Project-state retrieval becomes graph/projection based rather than transcript based.

Context assembler outputs AgentCockpit + progressive disclosure references.

ResumeCapsule becomes mandatory for long-running or interruptible work.

### B4.C3 Governed Tools

Tool Registry evolves into CapabilityGraph.

A tool is an implementation of a capability, not the capability itself.

Tool selection may therefore switch implementations without rewriting task plans.

### B4.C4 Worker Orchestration

Introduce `WorkerRuntime` certification and routing.

TaskContract remains authoritative; OpenClaw/Pi/future workers are interchangeable implementations where certified.

Delegation evaluates AffectedSurface and evidence requirements before choosing fan-out/review depth.

### B4.C5 Learning PO

Learning promotion targets executable structure whenever appropriate:

- test;
- skill;
- procedure;
- policy;
- template;
- capability adapter;
- negative knowledge.

PO cannot self-promote a lesson that expands its own authority.

---

## 7. B5 — Reference Application Factory

B5 should not become a dependency for institutional discovery itself, but it remains valuable as a proof that runtime-neutral cognition and capability contracts can build a domain-neutral product.

The reference app should exercise at least one WorkerRuntime swap and one ResumeCapsule restart if timing allows without expanding B5 beyond its purpose.

---

## 8. B6 — Reusable Platform Surfaces

B6 becomes the generic institutional-intelligence platform layer.

Recommended reusable surfaces:

### B6 discovery surface

- SourceRecord/SourceGraph API;
- SearchDemand;
- ScoutTask;
- SourceAdapter;
- novelty classifier;
- intake/quarantine workflow;
- license/rights metadata;
- recheck scheduling.

### B6 knowledge-refinery surface

- CapabilityAtom;
- MechanismCard generic base;
- extraction lineage;
- deduplication/identity resolution;
- internal archaeology adapter;
- promotion/demotion lifecycle;
- NegativeKnowledge query.

### B6 cognitive-runtime surface

- CompanionRuntime interface;
- WorkerRuntime interface;
- AdaptiveReasoner interface;
- runtime certification registry;
- reliability observations;
- route selection.

### B6 context surface

- AgentCockpit projection service;
- progressive disclosure resolver;
- ResumeCapsule;
- context budget policy.

B6 owns generic machinery. It must not embed trading-specific semantics.

---

## 9. B7 — Quant Foundation

B7 remains deterministic truth and validation infrastructure.

### B7.C1 Market Data Truth

Integrate external dataset candidates only through DatasetManifest/PIT/quality contracts.

Crypto Sensor Fabric remains a specialized upstream provider of canonical mechanical observations where domain contracts are satisfied.

### B7.C2 Research Kernel

Extend StrategySpec lineage to reference Research Genome atom revisions.

Feature and strategy generation may come from agents or external donors, but execution in the canonical engine remains deterministic/reproducible.

### B7.C3 Validation Kernel

Add family-aware/multiplicity-aware tests for corpus mining and agent-generated combinatorial research.

The system must track search breadth and related variants so 1,000 near-identical strategies cannot masquerade as 1,000 independent discoveries.

### B7.C4 Portfolio/Risk

Research prioritization should expose portfolio novelty and correlation value back to B8 SearchDemand without granting research agents execution authority.

### B7.C5 Lineage

CEREBUS, TB Forward, MVE, Capital Routing, internal strategy wells, and imported external research all use the SourceGraph/Research Genome model while preserving source-specific doctrine and evidence status.

---

## 10. B8 — Quant Lab and Quant Watch

B8 receives the largest domain-level expansion.

### B8.C1 Research Intelligence

Extend source ingestion into autonomous Quant SearchDemand and domain scouts.

Hypothesis generation queries:

- current market/domain ConstraintField;
- Research Genome;
- NegativeKnowledge;
- available sensors;
- unresolved evidence gaps;
- external SourceGraph.

Mechanism critique remains independent.

### B8.C2 Experiment Orchestration

Add corpus/family research mode with cheap staged falsification before full canonical runs.

Worker scheduling may use OpenClaw/Pi/science workers through B6/B4 runtime-neutral contracts.

### B8.C3 Quant Watch

Quant Watch becomes a source of new research questions, not only alerts.

Examples:

- unexplained residual;
- regime-transition anomaly;
- persistent data disagreement;
- new sensor availability;
- strategy decay;
- execution/capacity deterioration;
- portfolio concentration;
- contradiction to promoted mechanism.

### B8.C4 Operator Experience

Add institutional research brief surfaces:

- what the lab learned;
- what changed;
- highest-value unresolved questions;
- resource discoveries and dispositions;
- promoted/demoted capabilities;
- experiments likely to alter decisions.

### B8.C5 Research Governance

Add agent-search breadth and corpus-mining multiplicity controls.

Source discovery and hypothesis generation may be autonomous; promotion remains independently gated.

---

## 11. B9 — Controlled Execution

Minimal architectural change.

B9 continues to consume immutable, validated candidate packages.

The new research institution must not convert continuous discovery into continuous execution.

WorkerRuntime and AdaptiveReasoner abstractions may later assist paper/shadow operations, but deterministic independent risk and operator holds remain mandatory.

---

## 12. B10 — Operational Compounding

B10 becomes the second half of the institutional flywheel.

It should evaluate not only application reliability but the value of institutional learning.

Candidate compounding measures include:

- repeated-error reduction;
- search duplication avoided;
- percent of work using promoted practices;
- context cost per successful task;
- runtime routing efficiency;
- evidence-gap closure cost/time;
- useful capability promotions;
- failed hypothesis reuse avoidance;
- research information gain;
- external-resource hit rate;
- internal archaeology value;
- time from discovery to validated capability;
- time from unresolved question to evidence-backed answer.

B10 may feed SearchPolicy and CapabilityGraph reliability but cannot weaken authority or validation gates.

---

## 13. Crypto OS integration

Crypto OS remains a domain beneath OCE/Quant governance.

Current sequencing must be respected:

`Sensor Fabric -> mechanical observables / MECH restart -> capital-field expansion -> later alpha/sentiment`.

The institutional architecture adds:

- SourceGraph links for current/future providers;
- sensor EvidenceGaps as SearchDemand;
- Crypto Research Genome atoms;
- negative knowledge from MECH/LOWER-FIELD;
- capital-field source candidates through the refinery;
- domain ConstraintField projections;
- transferable lessons only after explicit cross-domain validation.

Do not allow A-006 autonomous discovery to interrupt the active Sensor Fabric provider-adapter sequence unless operator policy prioritizes a gap that genuinely blocks current research.

---

## 14. CEREBUS integration

CEREBUS doctrine remains a privileged operator-provided source in the FX domain.

Required preservation rules:

- manual terminology and structural logic remain traceable;
- manual claim, reproduced finding, later amendment, and external analogy remain distinct;
- CEREBUS's constraint-first logic informs institutional decision grammar but is not used to assert unrelated empirical market claims;
- generic imported strategies cannot override CEREBUS rules within governed CEREBUS strategies without explicit amendment/testing.

---

## 15. Current external-resource mapping

The following current resources illustrate the architecture but do not receive automatic integration approval:

### FMZ strategy corpus

Role: strategy/research ore.

Use: parse, deduplicate, cluster, extract atoms, run staged falsification, promote useful mechanisms/components.

Do not: import thousands of strategies as canonical alpha.

### QuantMind

Role: Quant capability donor / possible isolated sidecar.

Interesting surfaces: factor research, model factory, inference/drift UX, remote-compute patterns, Qlib/TradingAgents/RD-Agent integration patterns.

Constraint: licensing and research-governance review before code reuse; no bypass of B7.

### QM

Role: architecture/practice donor.

Useful lessons: durable state, fresh-context review, shared-layer fixes, affected-test economics, scoped environments.

Do not: replace OCE constitutional spine.

### Hermes

Role: preferred CompanionRuntime.

### OpenClaw

Role: broad WorkerRuntime / orchestration candidate.

### Pi

Role: focused engineering WorkerRuntime candidate; requires OCE-managed sandbox/permission boundary.

---

## 16. Contradiction audit

### C1 — Hermes replaces OpenClaw

**Status:** REVISE.

A-002's role separation is preserved, but product replacement language becomes runtime-role language under A-007.

### C2 — PO as all-purpose worker

**Status:** REJECT.

PO is executive cognition and should delegate bounded execution where a cheaper/specialized runtime is admissible.

### C3 — Agent memory as long-term institutional learning

**Status:** REJECT.

Runtime memory may improve continuity but institutional knowledge must promote into OCE-managed structures.

### C4 — External quant platform as replacement Quant Lab

**Status:** REJECT.

External systems are donors/sidecars/adapters behind B7/B8 contracts.

### C5 — More autonomous discovery means earlier live execution

**Status:** REJECT.

Discovery autonomy increases research throughput only. B9 authority remains separate.

### C6 — More data automatically means better research

**Status:** REJECT.

Data acquisition is prioritized by EvidenceGap, information value, quality, rights, and domain need.

### C7 — One universal field model across markets

**Status:** REJECT.

ConstraintField is a universal decision contract, not a claim that all market physics are identical. Domain models retain their own empirical semantics.

---

## 17. Proposed planning sequence

No implementation should begin from this impact atlas.

Recommended planning order:

1. Operator review of `LARGER_LAB_INSTITUTIONAL_ARCHITECTURE_v1.0.md`.
2. Joint review of A-005 through A-008.
3. Independent contradiction/adversarial pass against Constitution, Atlas, A-002, A-004, B3/B4/B6/B7/B8/B10.
4. Revise amendments to v1.1 if required.
5. Produce a single ratification packet with explicit operator decisions.
6. Rebase/port ratified planning changes onto the current authoritative OCE planning/build lineage without rewriting completed evidence.
7. Modify future block dossiers only after ratification.
8. Preserve current authorized build sequence unless operator explicitly changes it.

---

## 18. Long-horizon success test

The architecture succeeds if, years from now, Larger Lab can replace models, workers, data vendors, backtest engines, and external libraries while preserving a growing institutional core that knows:

- what it can do;
- what it knows;
- why it believes it;
- what has failed;
- which questions matter;
- what evidence is missing;
- which capabilities are weak;
- which research paths are promising;
- which actions are admissible;
- and when the operator must decide.

That institutional continuity — not any current agent or quant framework — is the intended moat.