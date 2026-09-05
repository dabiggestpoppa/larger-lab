# OCE Stress Suite Execution Gates

**Document ID:** OCE-STRESS-GATES-001  
**Version:** 1.0  
**Status:** AGENT HANDOFF CONTRACT  
**Parents:** Institutional Stress Suite Book; Scenario Catalog

## 1. Purpose

This document defines when the Institutional Stress Suite is ready to hand to an implementation agent and how that agent must progress without collapsing the entire program into one opaque build.

## 2. Readiness state

The planning package is considered `READY_FOR_AGENT_PROMPT` when all of the following exist:

- architecture branch is current with authoritative OCE planning lineage;
- A-009 and A-010 exist;
- adversarial matrix exists;
- stress-suite book exists;
- canonical scenario catalog exists;
- milestone/commit discipline exists;
- terminal artifacts and acceptance gates are defined;
- no scenario requires live capital or production mutation;
- contradictions found during execution are allowed to block rather than be patched silently.

## 3. Execution gates

### G0 — Planning Intake

Agent must read, in order:

1. OCE Constitution / Golden System Atlas relevant control sections;
2. `LARGER_LAB_INSTITUTIONAL_ARCHITECTURE_v1.1.md`;
3. A-009;
4. A-010;
5. A-010 adversarial matrix;
6. Stress Suite Book;
7. Scenario Catalog;
8. this execution-gates document.

Agent must produce a dependency map before writing code.

Exit: `PASS_G0_PLANNING_INGESTION`.

### G1 — Harness Contracts

Build only schemas, validators, phase-state engine, fixture loader, evidence object models, and forbidden-transition checks.

No scenario-specific cleverness may be hardcoded into the engine.

Required proof:

- legal transition tests;
- illegal transition tests;
- lifecycle tests;
- authority non-escalation tests;
- deterministic replay.

Exit: `PASS_G1_HARNESS_CONTRACTS`.

### G2 — Core Phase Control

Implement S01–S05.

Required proof:

- slow theory death escalates eventually;
- false revolution can end NO_CHANGE;
- PatchPressure escalates scope;
- leaf failure stays local;
- plural models survive without forced synthesis.

Exit: `PASS_G2_CORE_PHASE_CONTROL`.

### G3 — Cognitive Ecology

Implement S06–S09.

Required proof:

- raw agent count != independence;
- independence accounting is explicit;
- epistemic friction can create information value;
- counter-attractor review can fail cleanly.

Exit: `PASS_G3_COGNITIVE_ECOLOGY`.

### G4 — Memory and Epochs

Implement S10–S13.

Required proof:

- dormant knowledge reactivation;
- negative knowledge reopen conditions;
- bounded active context under large archive;
- complete epoch reconstruction under runtime replacement.

Exit: `PASS_G4_MEMORY_EPOCHS`.

### G5 — Domain Stress

Implement S14–S19.

Required proof:

- large fake alpha cannot weaken validation;
- novel alpha can originate from unresolved ontology;
- CEREBUS manual and reproduced contradiction remain separate;
- provider disagreement stays at source layer until evidence warrants escalation;
- sensor gaps produce DATA_BLOCKED rather than false precision;
- cross-domain analogy requires transfer evidence.

Exit: `PASS_G5_DOMAIN_BOUNDARIES`.

### G6 — Constitutional Attack

Implement S20–S24.

Required proof:

- Governor cannot change its own active threshold contract;
- high worker capability cannot self-expand authority;
- operator preference cannot fabricate evidence status;
- medium reversible work can continue under existing grants if operator unavailable;
- unknown governance failure remains representable without forced classification.

Exit: `PASS_G6_CONSTITUTIONAL_ATTACK`.

### G7 — Sensitivity and Metamorphic Audit

Run independence/persistence/reversibility/centrality/operator/evidence-quality/environment variations plus metamorphic tests.

Exit: `PASS_G7_SENSITIVITY_METAMORPHIC`.

### G8 — Cross-Scenario Contradiction Audit

Search for cases where equivalent evidence caused inconsistent phase/authority behavior.

Any material unresolved contradiction blocks ratification.

Exit: `PASS_G8_CROSS_SCENARIO_COHERENCE` or `BLOCKED_G8_ARCHITECTURE_CONTRADICTION`.

### G9 — Invariant Extraction

Derive candidate institutional genes from the scenarios that survived.

No invariant is accepted because it sounded philosophically attractive before testing.

Exit: `PASS_G9_INVARIANT_EXTRACTION`.

### G10 — Ratification Packet

Produce final results and proposed architecture change requests.

Agent does NOT amend A-004–A-010 automatically.

Exit: `READY_FOR_OPERATOR_RATIFICATION`.

## 4. Commit contract

Each gate requires multiple granular commits where implementation materially changes.

One giant “stress suite complete” commit is prohibited.

Every commit message should identify gate/scenario, e.g.:

```text
STRESS-G1: add phase-transition contract
STRESS-S01: implement slow-theory-death trace
STRESS-S01R: harden centrality hysteresis assertions
STRESS-G3: add independence accounting
STRESS-S14: add fake-alpha validation fixture
```

## 5. Stop conditions

The implementation agent MUST stop and report rather than self-repair architecture when:

- expected behavior contradicts A-009/A-010;
- two scenarios require mutually incompatible rules;
- a required authority boundary is ambiguous;
- current repo contracts make the planned test dishonest;
- a domain scenario requires information not currently supported by authoritative materials;
- a proposed fix changes the constitutional rule being tested;
- live/production/capital access would be required.

## 6. Agent output after each gate

The agent reports only:

- gate status;
- commits;
- test counts;
- evidence receipts;
- contradictions;
- known gaps;
- next authorized gate.

Do not bury failures under long narrative.

## 7. Master handoff status

With the Stress Suite Book, Scenario Catalog, A-009, A-010, adversarial matrix, and this gate contract present, the planning package qualifies as:

`READY_FOR_AGENT_PROMPT`

The next step is to issue a master implementation prompt that instructs the agent to begin at G0 and stop at each gate boundary for commit/evidence review.