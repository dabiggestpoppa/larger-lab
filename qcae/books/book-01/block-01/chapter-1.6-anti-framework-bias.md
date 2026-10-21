# Chapter 1.6 — Anti-Framework Bias

## 1.6.1 Purpose

QCAE must actively resist a predictable failure mode: solving a narrow capability need by importing an entire framework, runtime, workflow philosophy, storage model, and dependency tree.

This chapter turns the constitutional preference for the smallest viable capability into an operational decision rule.

Anti-framework bias does **not** mean frameworks are bad. It means whole-framework adoption carries a burden of proof.

---

## 1.6.2 Governing Rule

> **Prefer the smallest independently useful capability unit that satisfies the contract. Adopt a framework only when the framework-level behavior itself is required and its systemic burden is justified.**

This rule exists because architecture can be captured accidentally by convenience.

---

## 1.6.3 Why Framework Capture Happens

Common causes:

- search results surface popular frameworks before focused components;
- README demos make broad systems look easier than they are;
- one useful module is tightly marketed with the full project;
- developers underestimate transitive dependency burden;
- framework abstractions leak into business logic;
- initial integration cost is visible while future migration cost is hidden;
- "already built" is mistaken for "cheap to own."

QCAE must make those hidden costs explicit.

---

## 1.6.4 Framework Definition

For QCAE purposes, a framework is any external system that imposes substantial architectural control beyond the requested capability.

Signals include:

- required application lifecycle;
- required plugin architecture;
- mandatory storage model;
- required dependency-injection model;
- required orchestration runtime;
- extensive domain types that propagate internally;
- required service mesh or distributed components;
- broad configuration model;
- project-specific state or metadata becoming canonical.

A library can become framework-like if it controls enough of the host architecture.

---

## 1.6.5 Focused Component Preference

Given equivalent contract coverage, QCAE should prefer candidates with:

- narrow API;
- small dependency graph;
- isolated state;
- minimal side effects;
- standards-based inputs/outputs;
- independent tests;
- low configuration burden;
- clear extraction boundary;
- stable packaging;
- easy replacement.

---

## 1.6.6 Framework Adoption Burden of Proof

A framework should only be recommended when QCAE can answer yes to most of the following:

1. Does the capability contract genuinely require multiple coordinated behaviors the framework provides?
2. Would recreating those coordination semantics internally be more expensive or risky?
3. Is the framework architecture compatible with Quant Lab's intended boundaries?
4. Can proprietary data and secrets remain controlled?
5. Is the dependency/runtime burden justified by concrete required capability?
6. Is there a credible long-term maintenance path?
7. Can the framework be isolated behind stable Quant Lab interfaces?
8. Is exit/migration cost understood?
9. Are license obligations compatible?
10. Is there evidence that the framework works under the intended environment?

If the main argument is "it has many features we might use later," adoption should fail unless those future consumers are concrete and near-term.

---

## 1.6.7 Framework Feature Inflation

QCAE must distinguish:

```text
required capability
```

from:

```text
available framework features
```

A candidate does not gain value merely because it does more.

Unused features increase:

- attack surface;
- cognitive burden;
- dependency count;
- upgrade surface;
- failure modes;
- architecture capture.

Feature count is therefore not equivalent to capability value.

---

## 1.6.8 Extraction Before Adoption

When a framework contains a useful capability atom, QCAE should investigate in this order:

```text
Can the atom be used as an independent package?
        ↓ no
Can the component be cleanly extracted?
        ↓ no
Can the algorithm/specification be recovered?
        ↓ no
Can the framework be wrapped with acceptable containment?
        ↓ no
Only then consider deep framework adoption.
```

This ordering formalizes anti-framework bias.

---

## 1.6.9 Dependency Surface Test

QCAE should compare:

```text
required atom dependency graph
```

against:

```text
whole framework dependency graph
```

If the framework imports a materially larger surface for no required capability, the excess becomes negative acquisition value.

---

## 1.6.10 Architecture Leakage Test

A framework has high leakage when internal Quant Lab code must directly depend on:

- framework base classes;
- framework event types;
- framework global registries;
- framework lifecycle hooks;
- framework storage primitives;
- framework configuration everywhere.

Leakage raises switching cost.

Preferred pattern:

```text
Quant Lab Domain
      ↓ stable contract
Adapter Boundary
      ↓
External Framework
```

Framework-specific semantics should remain below the adapter wherever feasible.

---

## 1.6.11 State Ownership Test

QCAE should ask:

> Who owns canonical state after adoption?

Framework risk is high when removal requires migrating core state that only the framework understands.

Lower-risk patterns:

- stateless computation;
- standard data formats;
- Quant Lab-owned persistence schema;
- exportable state;
- reproducible derived state.

Higher-risk patterns:

- opaque proprietary databases;
- framework-managed metadata essential to operation;
- nonportable serialized objects;
- state transitions only understandable through framework internals.

---

## 1.6.12 Control-Plane Test

QCAE should distinguish data-plane capability from control-plane capture.

Example:

Quant Lab needs a scheduler algorithm.

A large platform may also require owning:

- job queue;
- auth;
- worker registration;
- persistence;
- deployment;
- monitoring.

If only scheduling logic is needed, importing the control plane is likely unjustified.

---

## 1.6.13 Ecosystem Gravity

Some frameworks create escalating dependence because their easiest integration path encourages use of additional project-specific components.

QCAE should identify ecosystem gravity:

```text
first component
    ↓
framework-native storage
    ↓
framework-native orchestration
    ↓
framework-native monitoring
    ↓
framework-native deployment
```

This may be desirable if the entire ecosystem solves a real architectural need. It is dangerous when it happens accidentally.

---

## 1.6.14 Framework Exception: Platform Capability

Sometimes the framework *is* the capability.

Examples:

- workflow orchestration;
- distributed execution runtime;
- event-processing platform;
- comprehensive observability substrate;
- model-serving platform.

In these cases, QCAE should evaluate the framework at system level rather than artificially fragmenting it.

Anti-framework bias must not create false atomization when coordination semantics are the core value.

---

## 1.6.15 Framework Exception: Standard Ecosystem

A mature framework may effectively function as an industry standard with broad interoperability and reduced custom maintenance.

Potential advantages:

- known operational model;
- ecosystem tooling;
- established integrations;
- abundant expertise;
- stable compatibility conventions.

QCAE may recommend it when those benefits exceed coupling cost.

Popularity alone is still insufficient evidence.

---

## 1.6.16 Framework Exception: Internal Convergence

If multiple Quant Lab systems independently require the same coordinated framework capabilities, a common platform may reduce total architecture burden.

QCAE should require concrete consumers and compare:

```text
shared platform burden
```

against:

```text
sum of duplicated local solutions
```

This turns platform adoption into an engineering-capital allocation decision rather than speculative infrastructure building.

---

## 1.6.17 Anti-Microservice Corollary

Anti-framework bias also means QCAE should not solve dependency concerns by automatically wrapping everything as a service.

A service adds:

- network failure;
- deployment;
- auth;
- observability;
- versioning;
- operations.

Use a service when service-level isolation or scaling is actually valuable, not as reflexive containment.

---

## 1.6.18 Anti-Reimplementation Corollary

Likewise, "smallest component" does not imply "rewrite everything."

Reimplementation creates its own burden:

- correctness ownership;
- testing;
- maintenance;
- protocol drift;
- security patch responsibility.

If a focused mature dependency already fits cleanly, using it may create less burden than custom code.

Anti-framework bias is anti-unnecessary-system, not anti-dependency.

---

## 1.6.19 Decision Sequence

Canonical sequence for a capability atom:

```text
1. Internal capability already sufficient?
   ├─ yes → retain unless change justified
   └─ no

2. Standard/specification solves the need?
   ├─ yes → evaluate focused implementations/reimplementation
   └─ no

3. Focused component/library available?
   ├─ yes → evaluate
   └─ no

4. Extractable component inside larger system?
   ├─ yes → evaluate extraction
   └─ no

5. Wrapper can contain larger dependency?
   ├─ yes → evaluate wrapped use
   └─ no

6. Framework-level capability genuinely required?
   ├─ yes → evaluate framework adoption
   └─ no → build/reimplement/defer/reject
```

---

## 1.6.20 Framework Burden Record

For framework candidates QCAE should record:

```text
framework_id
required_atoms
unused_major_capabilities
direct_dependencies
transitive_dependencies
required_services
state_ownership
control_plane_ownership
architecture_leakage
adapter_feasibility
migration_path
lockin_risk
operational_burden
security_surface
license_surface
concrete_consumers
adoption_justification
```

---

## 1.6.21 Example A — Focused Library Wins

Need:

> changepoint detection.

Candidate A:

- broad ML platform;
- distributed execution;
- model registry;
- 90 dependencies;
- changepoint plugin.

Candidate B:

- focused changepoint library;
- six dependencies;
- independent tests;
- stable numerical API.

If both satisfy the contract, QCAE should investigate B first.

---

## 1.6.22 Example B — Framework Wins

Need:

> durable distributed workflow orchestration across heterogeneous long-running QCAE workers with retries, persistence, scheduling, observability, and resumable state.

A framework providing these coordination semantics may be preferable to independently assembling queue, scheduler, persistence, retry, and worker-state atoms.

The framework's systemic behavior is now part of the contract.

---

## 1.6.23 Example C — Reject Strategy, Keep Atom

A trading framework claims strong returns and includes:

- strategy engine;
- broker integration;
- backtester;
- a useful robust covariance estimator.

Independent quant validation rejects the trading strategy.

QCAE may still classify the covariance estimator as a separate atom and evaluate it independently.

Framework-level rejection must not destroy atom-level intelligence.

---

## 1.6.24 Framework Drift Monitoring

When an accepted framework adds dependencies, changes architecture, or expands required services, QCAE should reassess whether the original Capability Conservation decision still holds.

An acquisition that was rational at version 1 can become irrational at version 5.

---

## 1.6.25 Failure Modes Prevented

Anti-framework bias prevents:

- architecture capture by convenience;
- speculative platform adoption;
- dependency explosions;
- framework types leaking across domain code;
- control-plane imports for data-plane needs;
- state lock-in;
- hidden migration cost;
- accepting unrelated features as value;
- rewriting focused mature libraries merely to avoid dependencies.

---

## 1.6.26 Chapter Invariants

1. Framework adoption carries a burden of proof.
2. The smallest viable capability is preferred, not the smallest code artifact.
3. Extraction and specification recovery are investigated before unnecessary whole-system adoption.
4. Framework-level capability may legitimately justify framework adoption.
5. Architectural leakage and state ownership are first-class concerns.
6. Service wrapping is not automatically cheaper than local dependency use.
7. Reimplementation is not automatically superior to a clean focused dependency.
8. Framework adoption must satisfy Capability Conservation over the intended ownership horizon.

---

## 1.6.27 Milestone Exit Criteria

Chapter 1.6 is complete when QCAE can determine whether a large external framework is:

- genuinely the capability needed;
- merely a container around one useful atom;
- containable behind an adapter;
- better mined for a specification/component;
- or unjustified architecture burden.
