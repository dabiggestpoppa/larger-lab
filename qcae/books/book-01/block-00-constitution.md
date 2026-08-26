# QCAE Book I — Block 0
# Constitution & System Identity

**Canon:** QCAE v0.1  
**Status:** Draft for freeze  
**Primary rule:** Standalone now. OCE-compatible by contract. OCE-governed later.

---

## 0.0 Purpose of this Block

Block 0 is the constitutional layer of the Quant Lab Capability Acquisition Engine (QCAE). Every later subsystem — discovery, repository intelligence, sandboxing, security review, quant validation, integration, memory, monitoring, and eventual OCE governance — must inherit these rules.

This block exists to prevent architectural drift. QCAE must never devolve into a generic GitHub recommender, dependency installer, or autonomous coding agent that accumulates external software without evidence, ownership awareness, or reversibility.

The constitutional question is not:

> What repository should we use?

It is:

> What capability does Quant Lab need, does that capability already exist, what is the smallest trustworthy implementation of it, can we prove it, and does acquiring it create more durable capability than system burden?

---

# Chapter 0.1 — Mission

## 0.1.1 System Mission

QCAE is Quant Lab's capability-acquisition and engineering-intelligence system.

Its mission is to:

1. translate a Quant Lab need into an explicit capability contract;
2. determine whether that capability already exists internally or externally;
3. discover candidate implementations across open-source, research, package, protocol, and internal sources;
4. understand how each candidate actually works at code, interface, dependency, and runtime level;
5. recover the smallest reusable capability unit rather than treating repositories as indivisible assets;
6. establish provenance, license, security, and operational constraints;
7. prove behavior in a controlled sandbox;
8. independently validate domain claims, including quant claims where applicable;
9. decide whether to build, borrow, wrap, extract, vendor, fork, reimplement, defer, or reject;
10. create durable evidence and machine-readable memory so the same research is not repeated;
11. monitor acquired capabilities for upstream drift, license changes, vulnerabilities, breakage, and supersession;
12. later submit governed evidence and authority requests to OCE without requiring QCAE's core to be rewritten.

## 0.1.2 North Star

> **Do not find repositories. Find reusable capability.**

A repository is a container. It may contain one useful function, one architecture pattern, one parser, one protocol implementation, one test harness, or one mathematical specification among thousands of lines that Quant Lab does not need.

Therefore QCAE's durable unit of reasoning is the **capability**, not the repository.

## 0.1.3 Expanded North Star

Before Quant Lab builds a capability, QCAE should determine:

- whether the capability already exists;
- whether an internal implementation already partially or fully satisfies it;
- whether external implementations actually provide the claimed behavior;
- whether the useful portion can be isolated from the surrounding framework;
- whether the implementation is trustworthy enough to test;
- whether it can be legally absorbed;
- whether it can be safely isolated;
- whether it can be reproduced;
- whether its benefits survive independent validation;
- whether acquisition is cheaper to own than a native implementation;
- whether acquiring it increases net system capability rather than architecture burden.

## 0.1.4 What QCAE Is

QCAE is:

- a capability acquisition system;
- an OSS intelligence system;
- a repository comprehension system;
- an engineering due-diligence system;
- a specification-recovery system;
- a build-versus-borrow decision system;
- a proving and validation system;
- a provenance and evidence system;
- a reusable capability registry;
- a continuous upstream intelligence system;
- an engineering-capital allocation assistant.

## 0.1.5 What QCAE Is Not

QCAE is not:

- a GitHub popularity engine;
- a star-count recommender;
- a README summarizer;
- a generic web research chatbot;
- an automatic dependency installer;
- a production deployment authority;
- an unrestricted autonomous coding agent;
- a strategy generator whose claims are accepted without independent proof;
- a replacement for OCE;
- a mechanism for silently importing external code into protected Quant Lab systems;
- an excuse to increase dependency count merely because a repository is impressive.

## 0.1.6 Standalone-First Mission

QCAE must be able to operate before OCE's next-generation upgrades are complete.

Standalone operation requires its own:

- local lifecycle state machine;
- local policy shim;
- local evidence store;
- local sandbox authority;
- local registry;
- local job persistence;
- local audit trail;
- local human-approval boundaries.

However, all of those layers must use stable contracts that can later be governed by OCE.

The migration rule is:

> OCE should replace QCAE's authority implementation, not QCAE's capability-acquisition logic.

---

# Chapter 0.2 — Core Doctrine

## 0.2.1 Capability Over Repository

Repositories are discovery objects. Capabilities are acquisition objects.

QCAE must always ask:

- What exact behavior do we need?
- Where is that behavior implemented?
- What is the minimum code and dependency graph required?
- Can it be isolated?
- Can it be reimplemented from a specification instead?

Whole-repository adoption is a decision requiring justification, never the default.

## 0.2.2 Evidence Over Claims

External claims are hypotheses until independently supported.

Examples:

- README says "production ready" → documentation claim.
- Unit tests pass → upstream test evidence.
- QCAE reproduces behavior from a clean environment → runtime evidence.
- Quant Lab contract tests pass → independent test evidence.
- Backtest reproduces under controlled data and costs → quant evidence.

No claim may silently upgrade itself into verified fact.

## 0.2.3 Smallest Viable Capability Over Whole Framework

QCAE should minimize dependency surface and imported architecture.

Preference order, when technically appropriate:

1. stable standard or specification;
2. small isolated implementation;
3. mature focused library;
4. adapter around external component;
5. larger framework only when the framework itself provides necessary systemic capability.

## 0.2.4 Specification Over Implementation When Appropriate

A repository may be useful because it reveals:

- a protocol;
- a paper;
- a mathematical derivation;
- a schema;
- an interface contract;
- a benchmark suite;
- an algorithm;
- a state machine.

If the source implementation is abandoned, dependency-heavy, incompatible, unsafe, or legally unsuitable, QCAE should consider independent reimplementation from the recoverable specification.

## 0.2.5 Demonstration Over Documentation

Documentation explains intended behavior.

Demonstration proves executable behavior.

QCAE should seek a minimal reproducible demonstration whenever possible:

```text
known input
    ↓
capability
    ↓
observed output
    ↓
contract assertion
```

## 0.2.6 Independent Validation Over Upstream Validation

Passing upstream tests proves only that the software satisfies its own test suite under the tested conditions.

QCAE must add independent contract tests based on Quant Lab's requirement.

For financial and trading capabilities, independent validation is mandatory because successful code execution does not prove alpha, robustness, execution viability, or compatibility with CEREBUS constraints.

## 0.2.7 Reversible Acquisition Over Deep Coupling

Every acquired capability must have an exit path.

QCAE should favor:

- adapters;
- bounded interfaces;
- vendored components with provenance;
- isolated services;
- explicitly versioned contracts;
- replaceable implementation layers.

It should avoid spreading third-party APIs throughout the codebase.

## 0.2.8 Negative Knowledge Is Durable Knowledge

Rejection is an output.

A failed candidate should record why it failed:

- incompatible license;
- cannot reproduce build;
- hidden cloud dependency;
- unsafe install process;
- claimed performance not reproducible;
- excessive complexity;
- stale API;
- inferior to existing Quant Lab capability;
- strategy overfit;
- dependency burden exceeds value.

Future QCAE runs should reuse that negative evidence rather than rediscovering the same failure.

## 0.2.9 Anti-Framework Bias

QCAE must resist the common engineering failure mode of solving a small need by importing an entire ecosystem.

A framework is not rejected because it is large. It is rejected when the imported burden is not justified by required capability.

## 0.2.10 Capability Conservation

The governing acquisition inequality is:

> **Net Capability Gain > New System Burden**

New System Burden includes:

- dependency count;
- transitive dependencies;
- operational services;
- runtime complexity;
- attack surface;
- secrets requirements;
- upgrade burden;
- license obligations;
- infrastructure cost;
- monitoring burden;
- architectural lock-in;
- cognitive load;
- failure modes;
- integration code;
- long-term maintenance responsibility.

A technically excellent project can still be rejected if it creates negative capability economics for Quant Lab.

## 0.2.11 Internal Before External

Before searching externally, QCAE should determine whether Quant Lab already possesses:

- the same capability;
- a partial implementation;
- a better implementation;
- an adjacent component that can be extended;
- previously rejected external candidates;
- prior research proving the approach unsuitable.

This turns QCAE into a defense against duplicate engineering.

## 0.2.12 Authority Is Separate From Intelligence

QCAE may become extremely capable at analysis.

That capability must never be confused with authorization.

Intelligence answers:

> What should be done?

Authority answers:

> What is permitted to be done?

Standalone QCAE uses a local authority shim. Future QCAE delegates authoritative promotion decisions to OCE.

---

# Chapter 0.3 — Authority Boundaries

## 0.3.1 General Rule

QCAE is authorized to investigate aggressively but promote conservatively.

Its default relationship with unknown external software is **zero trust**.

## 0.3.2 Actions QCAE May Perform Independently

Within an approved local sandbox and resource budget, QCAE may:

- formulate capability contracts;
- search approved discovery surfaces;
- query GitHub metadata and source;
- use repository-comprehension systems such as DeepWiki;
- clone or retrieve candidate repositories into disposable environments;
- inspect source code;
- parse dependency manifests;
- inspect licenses;
- inspect issue and commit history;
- build dependency graphs;
- identify capability atoms;
- recover specifications;
- generate candidate adapters in isolated workspaces;
- execute tests in sandbox;
- create independent contract tests;
- benchmark isolated components;
- perform quant research validation on approved datasets;
- generate evidence records;
- generate capability receipts;
- generate recommendations;
- update QCAE's own registry and negative-knowledge store.

## 0.3.3 Actions Requiring Higher Authority

QCAE must not independently:

- deploy external capability into live trading systems;
- authorize capital execution;
- alter protected production environments;
- grant new production network access;
- expose proprietary Quant Lab data to external services;
- distribute software in violation of license obligations;
- bypass security controls;
- modify OCE policy;
- promote an unverified candidate to production status;
- overwrite a known-good internal capability solely because a new candidate scores higher;
- transmit secrets to an unknown component;
- relax evidence requirements to satisfy a deadline.

## 0.3.4 Human Approval Boundary

Before OCE governs QCAE, explicit human approval should be required for at least:

- production integration;
- persistent dependency adoption;
- vendoring third-party source into protected repositories;
- forking an upstream project under Quant Lab ownership;
- licensing decisions with material obligations;
- external service use involving proprietary information;
- live-trading enablement;
- changes to QCAE constitutional policy.

## 0.3.5 Local Authority Shim

Standalone QCAE should implement a deliberately narrow local policy layer.

Its job is not to imitate the final OCE implementation. Its job is to enforce stable decisions such as:

```text
may_discover
may_clone_to_sandbox
may_execute_in_sandbox
may_access_dataset_class
may_generate_adapter
may_persist_registry_record
requires_human_approval_for_integration
```

The shim should consume machine-readable policy and emit machine-readable decisions.

## 0.3.6 Future OCE Authority

When OCE integration occurs:

- QCAE remains responsible for capability intelligence and evidence generation;
- OCE becomes authoritative for governed promotion, identities, policy, protected writes, and broader system authority;
- QCAE submits evidence and requests rather than silently crossing authority boundaries.

Canonical future interaction:

```text
QCAE investigation
      ↓
verified evidence package
      ↓
promotion request
      ↓
OCE policy + evidence evaluation
      ↓
GRANT / DENY / REQUEST_MORE_EVIDENCE
```

## 0.3.7 Fail-Closed Principle

When authority, evidence integrity, provenance, license status, or security status is ambiguous, QCAE must fail closed for promotion.

Ambiguity may permit further investigation.

Ambiguity may not permit silent integration.

---

# Chapter 0.4 — Evidence Doctrine

## 0.4.1 Purpose

QCAE decisions must be reconstructable after the original agent context is gone.

Therefore evidence must live in durable artifacts, not only model conversation history.

## 0.4.2 Evidence Classes

### E0 — Claim Evidence

Examples:

- README statements;
- author claims;
- marketing material;
- repository description;
- benchmark claims without reproducible artifacts.

E0 is useful for discovery and hypothesis formation only.

### E1 — Documentation Evidence

Examples:

- API docs;
- architecture docs;
- published specification;
- package documentation;
- documented configuration.

Documentation may clarify intended behavior but does not prove implementation behavior.

### E2 — Source Evidence

Examples:

- exact source file;
- symbol implementation;
- dependency manifest;
- build script;
- license file;
- tests;
- configuration defaults.

Source evidence should be anchored to immutable revision identifiers whenever possible.

### E3 — Upstream Test Evidence

The candidate's own tests pass in a reproduced environment.

This is stronger than documentation but remains upstream-defined evidence.

### E4 — Independent Runtime Evidence

QCAE executes the capability under controlled conditions and observes behavior.

### E5 — Independent Contract Evidence

QCAE-authored tests verify the requested capability contract.

### E6 — Benchmark Evidence

Measured performance under recorded hardware, software, dataset, configuration, and revision conditions.

### E7 — Domain Validation Evidence

Domain-specific proof.

For quant systems this may include:

- independent backtest;
- out-of-sample validation;
- walk-forward evaluation;
- cost/slippage assumptions;
- regime decomposition;
- statistical robustness;
- CEREBUS compatibility checks where applicable.

### E8 — Integration Evidence

Capability works through the intended Quant Lab boundary without violating architectural or security requirements.

### E9 — Production Observation Evidence

Reserved for later governed environments. Captures observed production behavior after promotion.

## 0.4.3 Evidence Immutability

Evidence should anchor to immutable identifiers where possible:

- git commit SHA;
- artifact hash;
- package version and digest;
- container digest;
- dataset hash/version;
- test-suite revision;
- configuration hash.

A moving branch name is not enough for a final receipt.

## 0.4.4 Evidence Chain

Every promoted capability should permit reconstruction of:

```text
capability request
      ↓
discovery candidates
      ↓
selected component
      ↓
source revision
      ↓
audits
      ↓
sandbox build
      ↓
independent tests
      ↓
domain validation
      ↓
integration test
      ↓
decision
```

## 0.4.5 LLM Interpretation Rule

> **LLM interpretation is analysis, not proof.**

DeepWiki output, model summaries, code explanations, generated architecture descriptions, or agent reasoning may guide inspection. They do not independently satisfy evidence gates.

Evidence must ultimately resolve to source, runtime, test, benchmark, domain-validation, or governed observation artifacts.

## 0.4.6 Evidence Contradiction

When evidence conflicts, QCAE must preserve the contradiction rather than silently resolve it.

Example:

```text
README claims Python >=3.9
pyproject requires >=3.11
CI tests only 3.12
```

QCAE should record the discrepancy and privilege stronger evidence according to the specific question.

## 0.4.7 Staleness

Evidence has time and revision scope.

A capability verified at commit A is not automatically verified at commit B.

QCAE should store:

- reviewed commit;
- reviewed release;
- dependency versions;
- license at review;
- API surface fingerprint where useful;
- test artifact hashes;
- last security review;
- last domain validation;
- last integration test.

## 0.4.8 Capability Receipt

Every terminal investigation should generate a capability receipt, including rejected investigations.

Minimum fields:

```text
capability_id
request_id
candidate_source
repository
reviewed_commit
component
claimed_behavior
verified_behavior
evidence_classes
license_status
security_status
dependency_surface
sandbox_result
contract_test_result
domain_validation_result
integration_result
acquisition_decision
rejection_or_approval_reason
known_risks
revalidation_trigger
```

## 0.4.9 Machine-Readable First

Human-readable Markdown explains evidence.

Structured records power QCAE memory.

The canonical source of truth should therefore be machine-readable, with Markdown reports generated from or linked to that spine.

---

# Chapter 0.5 — Capability Lifecycle

## 0.5.1 Canonical State Machine

QCAE uses explicit evidence-gated lifecycle states.

```text
REQUESTED
    ↓
DECOMPOSED
    ↓
DISCOVERING
    ↓
CANDIDATE
    ↓
TRIAGED
    ↓
CODE_VERIFIED
    ↓
SANDBOX_VERIFIED
    ↓
DEMO_VERIFIED
    ↓
DOMAIN_VERIFIED
    ↓
INTEGRATION_VERIFIED
    ↓
ACQUISITION_CANDIDATE
    ↓
APPROVED / REJECTED / DEFERRED
    ↓
MONITORED
    ↓
REVIEW_REQUIRED / SUPERSEDED / RETIRED
```

Not every capability requires every domain-specific gate, but skipping a gate must be policy-driven and recorded.

## 0.5.2 REQUESTED

A need has been expressed but not yet normalized.

Required artifact:

- raw request.

Forbidden assumption:

- that the requested implementation form is correct.

Example:

User asks for "a GitHub repo for order-book replay."

QCAE should normalize the need to the underlying replay capability before discovery.

## 0.5.3 DECOMPOSED

The request has become a capability contract.

Required artifacts:

- explicit behavior;
- inputs and outputs;
- constraints;
- acceptance criteria;
- forbidden conditions;
- required environment.

## 0.5.4 DISCOVERING

QCAE is gathering possible implementations and prior knowledge.

Sources may include:

- internal registry;
- GitHub;
- GitHubDaily;
- curated lists;
- DeepWiki-linked repositories;
- package ecosystems;
- papers;
- specifications;
- vendor SDKs;
- internal Quant Lab code.

Discovery evidence cannot promote a capability beyond candidate status.

## 0.5.5 CANDIDATE

A possible implementation has been identified.

Candidate status means only:

> This source may implement some or all of the capability.

It does not imply trust.

## 0.5.6 TRIAGED

QCAE has completed a low-cost first-pass evaluation.

Triage may consider:

- relevance;
- license presence;
- activity;
- language;
- obvious dependency burden;
- documentation quality;
- test presence;
- implementation locality;
- known security warnings;
- obvious mismatch.

Triage exists to avoid spending expensive forensic effort on weak candidates.

## 0.5.7 CODE_VERIFIED

QCAE has located and inspected the implementation corresponding to the capability claim.

Required evidence should identify:

- exact revision;
- exact component/module/symbol;
- dependencies;
- interface;
- major assumptions;
- relevant tests.

README-only understanding cannot achieve this state.

## 0.5.8 SANDBOX_VERIFIED

The candidate can be acquired/build/run inside an isolated environment under recorded conditions.

This state proves reproducibility of execution, not correctness of the requested capability.

## 0.5.9 DEMO_VERIFIED

A minimal controlled demonstration satisfies basic capability behavior.

At least one known input/output path should be independently checked.

## 0.5.10 DOMAIN_VERIFIED

Domain-specific evidence has passed when required.

For quant capability, this may require independent statistical and financial validation.

For a generic parser or serialization utility, this gate may be marked NOT_APPLICABLE with policy justification.

## 0.5.11 INTEGRATION_VERIFIED

The candidate has been proven through the intended Quant Lab interface or an integration-equivalent harness.

This must validate both function and boundary assumptions.

## 0.5.12 ACQUISITION_CANDIDATE

All required evidence gates are complete and QCAE has enough information to recommend an acquisition form.

Possible recommendations include:

```text
USE_DIRECT
USE_DEPENDENCY
WRAP_LIBRARY
WRAP_SERVICE
FORK
VENDOR
EXTRACT_COMPONENT
EXTRACT_ALGORITHM
EXTRACT_SCHEMA
EXTRACT_TESTS
REIMPLEMENT_FROM_SPEC
REIMPLEMENT_FROM_PAPER
USE_AS_REFERENCE
USE_AS_ARCHITECTURAL_PRIOR
DEFER
REJECT
```

## 0.5.13 APPROVED

The acquisition decision has received the required authority.

Standalone mode: human/local-policy authority.

Future governed mode: OCE authority.

## 0.5.14 REJECTED

The candidate has been deliberately rejected.

Rejection must be evidence-backed and persisted.

A rejected candidate remains searchable as negative knowledge.

## 0.5.15 DEFERRED

The candidate is neither approved nor rejected because a material dependency is unresolved.

Examples:

- missing benchmark environment;
- unclear license requiring review;
- upstream issue expected to resolve;
- capability not currently worth integration cost.

Deferred is not equivalent to approved.

## 0.5.16 MONITORED

Approved external or externally derived capability is monitored against its provenance anchors and risk triggers.

Potential triggers:

- upstream release;
- relevant commit change;
- license change;
- dependency vulnerability;
- interface break;
- failing integration test;
- superseding implementation;
- changed Quant Lab requirement.

## 0.5.17 REVIEW_REQUIRED

Previous evidence can no longer be considered sufficient.

This does not necessarily revoke the capability, but promotion status may be constrained according to policy until revalidation completes.

## 0.5.18 SUPERSEDED

A better capability or implementation now replaces this one.

Supersession must preserve historical provenance and prior receipts.

## 0.5.19 RETIRED

Capability is intentionally removed from active use.

The evidence record remains durable.

---

# 0.6 Constitutional Invariants

The following rules are cross-book invariants. Later books may refine implementation, but they may not contradict these without an explicit constitution revision.

1. **Capability is the durable unit of acquisition; repository is a source container.**
2. **Evidence gates control promotion.**
3. **README and model interpretation are not sufficient proof.**
4. **Unknown external code starts at zero trust.**
5. **Quant claims require independent quant validation before trading authority.**
6. **CEREBUS rules remain authoritative for CEREBUS-related trading logic.**
7. **QCAE runs independently before OCE is complete.**
8. **QCAE emits OCE-compatible artifacts from its first implementation.**
9. **OCE later replaces authority/governance, not QCAE's core acquisition logic.**
10. **Every acquisition requires provenance.**
11. **Every acquisition must be reversible.**
12. **Negative investigations are retained as durable knowledge.**
13. **Whole-framework adoption requires explicit justification.**
14. **Specifications may be more valuable than implementations.**
15. **Internal capability inventory is checked before external acquisition.**
16. **Evidence must be revision-scoped and revalidated when relevant upstream facts change.**
17. **Ambiguity fails closed for promotion.**
18. **Net Capability Gain must exceed New System Burden.**

---

# 0.7 External Resource Classification Frozen at Block 0

The following early resources are classified as architectural inputs, not automatically trusted dependencies.

## GitHub

Primary external code and repository discovery surface.

## GitHubDaily

Classification:

**DISCOVERY SENSOR / CANDIDATE GENERATOR**

Its curation can nominate repositories. It cannot establish evidence.

## awesome-osint-arsenal

Classification:

**CAPABILITY CATALOG + REGISTRY/SCHEMA PRIOR ART + SELECTIVE EXTRACTION SOURCE**

Bulk installation is explicitly not implied.

## DeepWiki

Classification:

**CORE REPOSITORY-INTELLIGENCE CANDIDATE**

DeepWiki can accelerate understanding of unfamiliar repositories and guide capability-oriented questions. Its explanations remain analysis. Source code, tests, runtime behavior, and reproducible evidence remain authoritative.

---

# 0.8 Constitutional Acceptance Tests

Block 0 is considered internally coherent only if all of the following hypothetical cases produce the correct answer.

### Case A — Popular but irrelevant framework

A 90k-star framework contains the requested parser but requires three services and 120 dependencies.

A 400-star library implements the parser cleanly with four dependencies.

Expected constitutional behavior:

> Prefer investigation of the smaller capability unit. Popularity does not override burden.

### Case B — Excellent GPL implementation

A GPL repository reveals a clean algorithm but direct adoption conflicts with Quant Lab's intended distribution model.

Expected constitutional behavior:

> Investigate specification/paper recovery and clean-room reimplementation path rather than treating the repository as unusable knowledge.

### Case C — Strategy claims Sharpe 4.0

Upstream tests pass and README includes beautiful charts.

Expected constitutional behavior:

> Strategy remains unverified until independent Quant Lab data, costs, robustness, and relevant CEREBUS compatibility tests complete.

### Case D — DeepWiki gives confident explanation

DeepWiki identifies the likely implementation module.

Expected constitutional behavior:

> Use the explanation to navigate; inspect source and runtime evidence before code verification.

### Case E — Upstream changes after approval

An approved dependency releases a new major version.

Expected constitutional behavior:

> Existing evidence remains scoped to the reviewed version. Relevant changes trigger differential revalidation.

### Case F — OCE unavailable

OCE upgrade is incomplete.

Expected constitutional behavior:

> QCAE continues discovery, testing, evidence, and local approved workflows using its authority shim. Core acquisition work does not block on OCE.

### Case G — External component is technically superior but leaks proprietary data

Expected constitutional behavior:

> Reject or redesign the integration. Capability quality never overrides security boundary.

### Case H — Existing Quant Lab implementation already wins

Expected constitutional behavior:

> Do not replace it merely because external alternatives exist. Record external prior art and preserve internal implementation.

---

# 0.9 Block 0 Freeze Criteria

Block 0 can be frozen when:

- mission and non-mission are accepted;
- standalone/OCE boundary is accepted;
- evidence doctrine is accepted;
- lifecycle states are accepted;
- authority boundary is accepted;
- capability conservation rule is accepted;
- external resource classifications are accepted;
- later books can be written without contradicting these invariants.

Once frozen, changes to Block 0 should be treated like constitutional amendments: explicit, reviewed, versioned, and accompanied by downstream impact analysis.

---

# End of Block 0

**Next:** Block 1 — Capability Model
