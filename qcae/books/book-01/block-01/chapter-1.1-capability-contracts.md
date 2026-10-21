# Chapter 1.1 — Capability Contracts

## 1.1.1 Purpose

A capability contract is QCAE's normalized statement of need. Every acquisition job begins with one before external discovery is allowed to meaningfully influence the solution.

The contract prevents search results from rewriting the requirement. Without it, the first impressive repository can silently redefine the problem around its own architecture.

The contract therefore separates:

- what Quant Lab actually needs;
- what implementation form the requester initially imagined;
- what evidence will count as success;
- what constraints cannot be violated.

A capability contract is not a prompt. It is a versioned domain object.

---

## 1.1.2 Raw Request vs Normalized Capability

Raw requests may be implementation-biased:

> Find a Python repo for replaying order books.

QCAE should normalize this to the underlying need:

> Reconstruct a deterministic sequence of order-book states from timestamped market events with specified fidelity, latency, and data-format constraints.

The words `Python` and `repo` may remain preferences or constraints if they are genuinely required. They must not automatically become the capability itself.

Normalization rule:

> Preserve required behavior. Challenge assumed implementation form.

---

## 1.1.3 Contract Layers

Every contract should distinguish five layers.

### A. Intent

Why the capability is needed.

Examples:

- research;
- production execution;
- simulation;
- ingestion;
- validation;
- observability;
- model training;
- developer tooling.

### B. Functional behavior

What must happen.

### C. Non-functional behavior

How well it must happen.

Examples:

- latency;
- throughput;
- memory;
- determinism;
- portability;
- fault tolerance;
- precision.

### D. Constraints

What boundaries the solution must respect.

Examples:

- local-only data;
- no external SaaS;
- compatible license;
- Linux support;
- Python interoperability;
- no persistent network access;
- no proprietary data egress.

### E. Acceptance evidence

What must be demonstrated before the capability is considered satisfied.

---

## 1.1.4 Canonical Contract Fields

The future machine-readable schema should support at minimum:

```text
capability_id
contract_version
request_id
title
problem_statement
intent
required_behaviors
optional_behaviors
explicit_non_goals
inputs
outputs
state_model
failure_semantics
performance_requirements
precision_requirements
latency_requirements
throughput_requirements
runtime_constraints
platform_constraints
language_constraints
integration_constraints
security_class
data_classification
network_policy
secret_policy
license_constraints
cost_constraints
maintenance_constraints
quant_domain
cerebus_relevance
acceptance_tests
required_evidence_classes
forbidden_conditions
preferred_acquisition_forms
forbidden_acquisition_forms
priority
owner
created_at
supersedes_contract
```

Not every field must be populated for every request. Missing required information must be explicit rather than silently guessed.

---

## 1.1.5 Capability Identity

A capability ID identifies behavior, not an implementation.

Bad identity:

```text
ccxt-market-data
```

Better identity:

```text
normalized-multi-venue-market-data-ingestion
```

The implementation may later change from CCXT to native venue adapters without changing the underlying capability identity.

This is essential for durable memory.

---

## 1.1.6 Contract Versioning

Requirements change. QCAE must preserve that history.

Example:

```text
CAP-MD-001 v1
local historical ingestion

CAP-MD-001 v2
adds streaming support

CAP-MD-001 v3
adds deterministic replay requirement
```

Old candidate verdicts remain scoped to the contract version against which they were evaluated.

A candidate rejected under v1 may become viable under v3, and vice versa.

---

## 1.1.7 Required vs Preferred vs Forbidden

Contracts must distinguish these explicitly.

### REQUIRED

Failure means the candidate cannot satisfy the contract.

### PREFERRED

Influences ranking but does not hard-fail the candidate.

### FORBIDDEN

Presence disqualifies the candidate or acquisition form.

Example:

```text
REQUIRED: deterministic replay
PREFERRED: Python-native API
FORBIDDEN: sending proprietary market data to third-party SaaS
```

This prevents soft preferences from becoming accidental hard constraints.

---

## 1.1.8 Non-Goals

Every meaningful contract should state what QCAE is not solving.

Example order-book replay non-goals:

- exchange connectivity;
- strategy execution;
- charting;
- portfolio accounting.

Non-goals resist framework creep during discovery.

---

## 1.1.9 Acceptance Tests as First-Class Contract Elements

The contract should define observable acceptance conditions before candidate selection.

Example:

```text
Given ordered events E0...En,
reconstructed book state at checkpoint k
must match reference state Rk exactly
for all provided fixtures.
```

This enables later QCAE workers to generate candidate-independent tests.

Acceptance tests may initially be declarative rather than executable, but the observable condition should exist before promotion.

---

## 1.1.10 Evidence Requirements

Capability contracts should state the minimum evidence tier needed.

Examples:

### Low-risk developer utility

May require:

- source evidence;
- sandbox reproduction;
- independent contract tests.

### External service touching internal data

Additionally requires:

- security review;
- data-egress review;
- integration evidence.

### Trading strategy capability

Additionally requires:

- independent quant validation;
- execution-cost modeling;
- relevant CEREBUS compatibility;
- authority separation before live use.

Evidence requirements belong to the contract because risk is part of the need, not an afterthought.

---

## 1.1.11 Contract Decomposition Trigger

A contract is too broad when it contains behaviors that could be independently sourced, tested, replaced, or retired.

Example:

> Build a crypto intelligence engine.

Possible atoms:

- chain data ingestion;
- transaction decoding;
- entity labeling;
- clustering;
- anomaly detection;
- graph storage;
- query interface.

QCAE should decompose before discovery whenever independent acquisition choices are plausible.

---

## 1.1.12 Contract Compatibility

Two contracts may relate as:

- identical;
- superseding;
- overlapping;
- narrower;
- broader;
- conflicting;
- composable.

This is important for internal discovery. QCAE may already possess 80% of a new requirement as existing capabilities.

---

## 1.1.13 Contract Freeze Point

Discovery should not begin expensive forensic evaluation until the contract reaches a local `CONTRACT_READY` checkpoint.

That checkpoint means:

- core behavior is unambiguous enough to test;
- hard constraints are known;
- implementation assumptions have been separated from actual requirements;
- acceptance conditions exist;
- major non-goals are explicit.

The contract may still be amended later, but amendments invalidate affected candidate comparisons.

---

## 1.1.14 Contract Quality Checks

Before discovery, QCAE should ask:

1. Is this stated as behavior rather than a product name?
2. Can success be observed?
3. Are hard requirements separated from preferences?
4. Are forbidden conditions explicit?
5. Is the scope atomic enough for acquisition decisions?
6. Are security/data boundaries represented?
7. Is the intended operating context known?
8. Is the required evidence level proportional to risk?
9. Are non-goals sufficient to resist framework creep?
10. Could a different implementation satisfy the same contract?

If #10 is no because the contract names a specific repository without reason, the contract is likely implementation-captured.

---

## 1.1.15 Example Contract

```yaml
capability_id: CAP-REPLAY-001
contract_version: 1
title: deterministic-order-book-replay
intent: research-and-backtest-infrastructure
required_behaviors:
  - reconstruct L2 book state from ordered event stream
  - expose state at deterministic checkpoints
  - preserve event ordering
inputs:
  - timestamped normalized market events
outputs:
  - deterministic book snapshots
required:
  - local execution
  - reproducible results
preferred:
  - Python interoperability
  - component usable without full trading framework
forbidden:
  - mandatory external SaaS
  - proprietary data egress
acceptance_tests:
  - reference fixture snapshots must match exactly
required_evidence_classes:
  - source
  - sandbox
  - independent-contract
  - benchmark
```

The syntax is illustrative. The schema is defined later in implementation books.

---

## 1.1.16 Failure Modes Prevented

Capability contracts prevent:

- repository-first reasoning;
- vendor/product capture;
- requirement drift;
- framework creep;
- ambiguous success criteria;
- untestable acquisition decisions;
- unsafe external-service adoption;
- comparing candidates against different standards;
- forgetting why a capability exists.

---

## 1.1.17 Chapter Invariants

1. Every acquisition job maps to a capability contract.
2. Capability identity is implementation-independent.
3. Requirements, preferences, and prohibitions are distinct.
4. Acceptance criteria exist before candidate promotion.
5. Contract revisions are versioned.
6. Candidate verdicts are scoped to contract versions.
7. Broad contracts trigger decomposition.
8. Discovery may suggest contract amendments but may not silently rewrite the requirement.

---

## 1.1.18 Milestone Exit Criteria

Chapter 1.1 is complete when later QCAE subsystems can answer, from the contract alone:

- what capability is being sought;
- why it is needed;
- what behavior is mandatory;
- what must not occur;
- what evidence will constitute success;
- whether the requirement should be decomposed before discovery.
