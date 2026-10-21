# Chapter 1.5 — Capability Value Model

## 1.5.1 Purpose

QCAE requires a disciplined way to compare candidate acquisitions without pretending that one popularity score or one arbitrary weighted number can replace engineering judgment.

The capability value model is therefore a structured decision framework, not a magical ranking formula.

Its purpose is to make tradeoffs explicit, comparable, auditable, and revisable.

---

## 1.5.2 Governing Equation

The constitutional rule from Block 0 is:

> **Net Capability Gain > New System Burden**

A conceptual decomposition is:

```text
Net Capability Gain
=
Capability Coverage
+ Evidence Strength
+ Integration Fit
+ Operational Fit
+ Maintainability
+ Reuse Potential
+ Strategic Leverage

-
Dependency Surface
-
Security Surface
-
License Friction
-
Operational Complexity
-
Maintenance Burden
-
Lock-In
-
Migration Cost
-
Uncertainty
```

This is not necessarily calculated as one scalar. QCAE should retain the underlying dimensions so humans and later policy engines can understand why one candidate was preferred.

---

## 1.5.3 Hard Gates vs Comparative Factors

Some conditions are disqualifying.

Others are ranking factors.

### Hard gate examples

- cannot satisfy required behavior;
- prohibited data egress;
- incompatible license under intended acquisition form;
- unreproducible runtime when reproduction is required;
- critical security risk without acceptable containment;
- quant strategy fails required domain validation.

### Comparative factor examples

- maintenance activity;
- documentation quality;
- dependency count;
- latency;
- adapter complexity;
- community size.

Hard failures must not be averaged away by high scores elsewhere.

---

## 1.5.4 Capability Coverage

Coverage asks:

> How much of the actual contract does this candidate satisfy?

Coverage should be evaluated against required atoms and behaviors, not marketing features.

Possible representation:

```text
required_atom_A: full
required_atom_B: partial
required_atom_C: absent
optional_atom_D: full
```

A candidate with 100 features but only 50% required contract coverage is weaker than a focused candidate that satisfies all required behavior.

---

## 1.5.5 Evidence Strength

Candidate confidence should reflect the strongest relevant evidence obtained.

Potential factors:

- source located;
- build reproduced;
- upstream tests pass;
- independent contract tests pass;
- benchmark reproduced;
- domain validation passes;
- integration verified.

A candidate should not outrank another solely because it makes stronger claims.

---

## 1.5.6 Integration Fit

Integration fit measures how naturally the capability can enter Quant Lab.

Consider:

- interface compatibility;
- supported language/runtime;
- data model compatibility;
- state model;
- error semantics;
- deployment assumptions;
- required adapters;
- existing internal abstractions;
- ease of replacement.

A technically excellent component may have poor integration economics.

---

## 1.5.7 Operational Fit

Operational fit includes:

- local vs cloud requirements;
- CPU/GPU needs;
- storage needs;
- network dependencies;
- process model;
- startup behavior;
- observability;
- fault recovery;
- deterministic operation where required.

QCAE should distinguish "runs in a demo" from "fits the intended operating environment."

---

## 1.5.8 Maintainability

Maintainability is not simply recent commits.

Relevant signals include:

- clarity of architecture;
- test coverage quality;
- release discipline;
- issue responsiveness;
- bus factor;
- code readability;
- API stability;
- dependency discipline;
- upgrade history;
- documentation quality;
- frequency and severity of breaking changes.

A quiet, stable protocol library can be healthier than a hyperactive framework.

---

## 1.5.9 Reuse Potential

Some capability atoms can unlock multiple Quant Lab systems.

Examples:

- generic provenance engine;
- robust time-series alignment;
- deterministic event replay;
- common market-data normalization;
- dependency intelligence.

QCAE may assign additional strategic value when a capability can safely satisfy multiple known contracts.

This must not be used to justify speculative platform building without concrete consumers.

---

## 1.5.10 Strategic Leverage

Strategic leverage captures second-order benefits such as:

- enables future autonomous workflows;
- removes repeated manual research;
- becomes a common verification primitive;
- reduces duplicated code across projects;
- standardizes an important interface.

Strategic leverage should be documented, not hand-waved.

---

## 1.5.11 Dependency Surface

Dependency burden should include more than direct package count.

Record:

- direct dependencies;
- transitive dependencies;
- native libraries;
- required system packages;
- external services;
- database requirements;
- runtime agents;
- hardware dependencies;
- install-time downloads.

A package with five direct dependencies may pull hundreds transitively.

---

## 1.5.12 Security Surface

Factors include:

- network access;
- shell execution;
- dynamic code loading;
- binary blobs;
- credential access;
- filesystem access;
- package-manager hooks;
- external update channels;
- data exfiltration potential;
- vulnerability history.

Security burden remains separate from functional quality.

---

## 1.5.13 License Friction

License friction should capture:

- compatibility with intended acquisition form;
- redistribution obligations;
- source disclosure implications;
- notice/attribution requirements;
- network-use provisions;
- ambiguity or missing license;
- mixed-license components.

The model should not treat license as a moral quality score. It is an acquisition-fit constraint.

---

## 1.5.14 Operational Complexity

Operational burden includes:

- number of services;
- deployment complexity;
- configuration surface;
- failure modes;
- recovery procedures;
- observability requirements;
- infrastructure cost;
- orchestration needs.

QCAE should ask whether the capability requires a new mini-platform to exist.

---

## 1.5.15 Maintenance Burden

This is the long-run cost Quant Lab inherits.

Possible contributors:

- custom adapters;
- patch maintenance;
- fork divergence;
- frequent API changes;
- specialized knowledge requirements;
- custom build systems;
- platform-specific code;
- revalidation cost.

Maintenance burden applies even when the upstream project itself is free.

---

## 1.5.16 Lock-In

Lock-in measures future switching cost.

High lock-in examples:

- vendor-specific data model becomes canonical;
- proprietary service API leaks throughout internal code;
- custom storage format becomes irreversible state;
- external framework owns orchestration and domain logic.

Low lock-in examples:

- small library behind internal interface;
- standards-based component;
- stateless replaceable service adapter.

---

## 1.5.17 Migration Cost

QCAE should estimate the effort required to replace or remove an acquired capability.

This includes:

- code changes;
- data migration;
- retraining;
- config migration;
- operational retraining;
- test rewrites;
- downtime or transition complexity.

Reversibility from Block 0 becomes measurable here.

---

## 1.5.18 Uncertainty Penalty

Unknowns are risk.

Examples:

- unclear license;
- unknown dependency behavior;
- undocumented state assumptions;
- benchmark cannot be reproduced;
- only partial source understanding;
- upstream roadmap uncertain.

QCAE should not fill unknowns with optimistic assumptions.

Unknowns either:

- trigger more investigation;
- reduce confidence;
- or fail a hard gate when the uncertainty concerns a protected boundary.

---

## 1.5.19 Candidate Comparison Matrix

A comparison may look like:

| Dimension | Candidate A | Candidate B | Internal C |
|---|---|---|---|
| Required coverage | Full | Full | Partial |
| Independent tests | Pass | Pass | Pass |
| Dependency surface | High | Low | Low |
| Security surface | Medium | Low | Low |
| Integration effort | High | Low | Medium |
| License friction | Low | Low | None |
| Maintenance burden | High | Low | Medium |
| Lock-in | High | Low | Low |
| Decision | Reject | Prefer | Extend only if B fails |

The point is explainability, not cosmetics.

---

## 1.5.20 Pareto Reasoning

QCAE should identify dominated candidates.

Candidate A is dominated when Candidate B is at least as good on all relevant dimensions and strictly better on one or more, with no compensating strategic reason.

Dominated candidates can be triaged out early.

This reduces expensive forensic work.

---

## 1.5.21 Candidate Tiers

For operational efficiency, QCAE may use coarse tiers after hard gates:

```text
TIER A — strong acquisition candidate
TIER B — viable with known compromises
TIER C — research/reference value only
TIER D — reject/defer
```

Tiers must remain derived from recorded dimensions and evidence, not arbitrary model intuition.

---

## 1.5.22 Scoring Policy

Numeric scores may be used internally for ranking large candidate sets, but they must obey rules:

1. hard-gate failures cannot be rescued by aggregate score;
2. weights must be versioned policy;
3. underlying factors must remain visible;
4. scores are triage aids, not authority decisions;
5. final recommendations require evidence-backed rationale.

---

## 1.5.23 Context Dependence

There is no universal best implementation.

A candidate may rank differently for:

- disposable research;
- production market data;
- live execution;
- offline batch analysis;
- proprietary-data environments.

Value is evaluated against a capability contract and intended acquisition form.

---

## 1.5.24 Quant-Specific Value Adjustment

For quant capabilities, claimed performance cannot count as capability value until independently validated.

Examples that cannot be credited at claim level:

- Sharpe;
- win rate;
- CAGR;
- max drawdown;
- alpha;
- regime accuracy.

QCAE may use such claims to prioritize investigation, but validated domain evidence determines actual value.

---

## 1.5.25 Internal Capability Comparison

Every external candidate should be compared against the current internal alternative where one exists.

Possible outcomes:

- external clearly superior;
- internal clearly superior;
- external supplies only one missing atom;
- hybrid is best;
- no change justified.

The existence of a good external implementation does not create an obligation to replace working internal capability.

---

## 1.5.26 Expected Ownership Horizon

Decision economics depend on expected lifespan.

A short-lived research experiment may tolerate more dependency burden than a foundational ten-year internal service.

QCAE should record intended horizon:

```text
ephemeral
experimental
medium-term
core-infrastructure
```

Longer horizon increases the importance of maintainability, standards, provenance, and reversibility.

---

## 1.5.27 Value Record

Future candidate evaluations should capture at least:

```text
contract_id
candidate_id
coverage
hard_gate_results
evidence_strength
integration_fit
operational_fit
maintainability
reuse_potential
strategic_leverage
dependency_surface
security_surface
license_friction
operational_complexity
maintenance_burden
lockin
migration_cost
uncertainties
candidate_tier
recommendation
policy_version
```

---

## 1.5.28 Failure Modes Prevented

This model prevents:

- star-count selection;
- one-dimensional performance ranking;
- hiding dependency burden;
- averaging away security failures;
- adopting frameworks because they have more features;
- replacing superior internal code without economic justification;
- treating free software as zero-cost software;
- pretending uncertain facts are favorable facts.

---

## 1.5.29 Chapter Invariants

1. Hard failures cannot be averaged away.
2. Value is contract-specific.
3. Claims do not count as verified capability value.
4. Total ownership burden matters, not purchase price.
5. Internal alternatives are part of candidate comparison.
6. Numeric scoring is optional and subordinate to evidence.
7. Underlying dimensions remain auditable.
8. Uncertainty is recorded rather than optimistically imputed.
9. Reversibility and migration cost are first-class dimensions.
10. Capability Conservation is the final economic constraint.

---

## 1.5.30 Milestone Exit Criteria

Chapter 1.5 is complete when QCAE can compare two implementations and explain not only which one it prefers, but precisely:

- what capability each provides;
- what evidence supports that conclusion;
- what burdens each imports;
- which hard gates apply;
- how the decision would change under a different contract or operating context.
