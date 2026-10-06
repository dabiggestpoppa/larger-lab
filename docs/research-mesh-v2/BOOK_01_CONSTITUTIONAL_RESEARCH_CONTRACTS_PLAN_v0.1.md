# OCE Research Mesh V2 — Book 1 Plan
## Constitutional Research Contracts

**Document ID:** RMV2-B1-PLAN-001  
**Version:** 0.1  
**Branch:** `agent/oce-research-mesh-v2`  
**Status:** PLANNING BASELINE — NOT YET FROZEN  
**System role:** standalone-first research institution, OCE-compatible by contract, Hermes-operated  
**Scope:** general research across domains; not trading-specific  
**Parent:** `INSTITUTIONAL_RESEARCH_MESH_MASTER_PLAN_v0.1.md`

---

## 0. Book 1 mission

Book 1 defines the constitutional laws that every later Research Mesh component must obey.

It does **not** build retrieval quality, citation intelligence, synthesis, research agents, or OCE integration. It defines the objects, states, authority boundaries, truth rules, provenance requirements, rights rules, and lifecycle laws those later books must consume.

The governing boundary is:

```text
OCE             = what objective must be executed?
Research Mesh   = what must the institution know?
QCAE            = what must the institution be able to do?
Institution     = what validated experience may change the institution?
Hermes          = operates Research Mesh; does not own epistemic authority.
```

Book 1 must make invalid institutional research states unrepresentable or fail-closed wherever practical.

---

# 1. Book structure

Book 1 contains five chapters with five sections each.

| Chapter | Name | Primary question |
|---|---|---|
| B1.C1 | System Identity & Institutional Boundary | What is Research Mesh, and what is it not? |
| B1.C2 | Epistemic Objects & Research State | What objects exist, and what do their states mean? |
| B1.C3 | Evidence, Provenance & Reproducibility | What must accompany every material claim? |
| B1.C4 | Authority, Rights & Governance | Who may do what, under what data and authority constraints? |
| B1.C5 | Truth, Uncertainty, Contradiction & Promotion | How does research become increasingly trusted without becoming self-ratifying? |

The Book 1 exit gate is **not** "code exists." It is:

> every later Book can reference one canonical definition for identity, lifecycle, provenance, authority, rights, uncertainty, contradiction, and promotion boundaries, with adversarial tests proving favorable-default and authority-collapse defects are refused.

---

# 2. B1.C1 — System Identity & Institutional Boundary

## B1.C1.S1 — Mission and non-mission

Define Research Mesh as the institution's **epistemic acquisition and synthesis system**.

### It owns

- unknown identification;
- research-question registration;
- research planning;
- source acquisition;
- evidence normalization;
- evidence evaluation;
- claim extraction;
- contradiction recording;
- corroboration analysis;
- synthesis;
- knowledge-gap detection;
- research dossiers;
- doctrine candidates;
- epistemic provenance.

### It does not own

- executable capability proving;
- capability procurement;
- repository acquisition;
- production authority;
- capital authority;
- OCE institutional mutation;
- doctrine self-ratification;
- model-weight mutation;
- client acceptance as truth;
- trading-model promotion.

### Deliverables

- `constitution/system_identity.py`
- `constitution/BOUNDARY.md`
- explicit ownership table for Research Mesh / Hermes / QCAE / OCE / Institution.

### Adversarial tests

- Research Mesh cannot emit a CapabilityReceipt.
- Research Mesh cannot mark its own dossier as institutional doctrine.
- Hermes cannot override institutional ownership by caller flag.
- "research complete" cannot imply "objective executable."

---

## B1.C1.S2 — Standalone-first / OCE-compatible contract

Adopt the QCAE structural rule:

> **Standalone now. OCE-compatible by contract. OCE-governed later.**

Research Mesh must run without:
- active OCE runtime;
- QCAE runtime;
- institutional stress-suite runtime;
- Hermes itself.

Hermes is a replaceable operator. OCE is a future governing integration, not a boot dependency.

### Required properties

- local CLI/service works independently;
- IDs and records are OCE-ready;
- event references are additive, not required for local operation;
- no import-time dependency on unfinished OCE institutional modules;
- future adapter can be added without rewriting research-domain records.

### Tests

- importing Research Mesh with OCE unavailable succeeds;
- provider search/local store work without Hermes;
- disabling every external integration leaves local evidence readable;
- OCE adapter absence is reported as NOT_CONFIGURED, never silently bypassed.

---

## B1.C1.S3 — General-domain neutrality

Research Mesh must be general research infrastructure.

No base object may require:
- ticker;
- instrument;
- market;
- strategy;
- trade;
- portfolio;
- PnL;
- broker;
- exchange.

Domain-specific metadata belongs in typed extensions or tags.

### Initial domain-neutral examples

- AI / ML;
- biology;
- medicine;
- physics;
- mathematics;
- law;
- economics;
- engineering;
- cybersecurity;
- history;
- social science;
- standards/specifications;
- finance/trading as one consumer among many.

### Tests

- a neuroscience paper, legal standard, mathematical paper, biology review, and market-microstructure paper normalize through the same base evidence contract;
- no trading-specific field is required to construct a valid core record.

---

## B1.C1.S4 — Registry and ownership separation

Research Mesh owns epistemic registries. Cross-system references may exist, but ownership may not merge.

### Research Mesh registries

- source registry;
- acquisition registry;
- canonical work registry;
- claim registry;
- contradiction registry;
- synthesis registry;
- dossier registry;
- knowledge-gap registry;
- doctrine-candidate registry.

### External registry references

- QCAE capability IDs;
- OCE objective IDs;
- institutional amendment/epoch IDs;
- Hermes task IDs.

References are foreign keys/URIs only. They do not transfer lifecycle authority.

### Tests

- a Research Dossier may reference a QCAE capability gap but cannot mutate it;
- a QCAE receipt may reference a research dossier but cannot mutate its evidence;
- external IDs never become local primary authority by coincidence.

---

## B1.C1.S5 — Canonical hierarchy and amendment discipline

Book 1 establishes the internal hierarchy:

```text
operator instruction
→ Research Mesh Constitution / Book 1
→ ratified Book plans
→ frozen schemas/contracts
→ implementation
→ runtime convenience
```

No implementation shortcut outranks a frozen contract.

### Required artifacts

- amendment record schema;
- supersession links;
- effective-from version;
- reason;
- operator authorization reference where required.

Historical records remain readable under the contract version that created them.

### Gate C1

**PASS_B1_C1_SYSTEM_IDENTITY** requires:
- all ownership boundaries encoded;
- standalone import/test path proven;
- no trading-specific base dependency;
- cross-registry mutation forbidden;
- amendment hierarchy documented and tested.

---

# 3. B1.C2 — Epistemic Objects & Research State

## B1.C2.S1 — Canonical object taxonomy

Define the first-class objects.

### Required objects

- `ResearchQuestion`
- `ResearchPlan`
- `SourceDescriptor`
- `AcquisitionObservation`
- `EvidenceArtifact`
- `CanonicalWork`
- `Claim`
- `ClaimEvidenceLink`
- `ContradictionRecord`
- `CorroborationRecord`
- `KnowledgeGap`
- `SynthesisArtifact`
- `ResearchDossier`
- `DoctrineCandidate`
- `ResearchTaskReceipt`

Every object gets:
- immutable ID;
- created_at;
- contract_version;
- provenance refs;
- lifecycle state where applicable.

No generic free-form "research result" may substitute for these objects once Book 1 freezes.

---

## B1.C2.S2 — Evidence lifecycle state machine

Freeze lifecycle vocabulary:

```text
DISCOVERED
ACQUIRED
PARSED
NORMALIZED
DISTILLED
CLAIMS_EXTRACTED
CORROBORATED
CONTRADICTED
SYNTHESIZED
DOSSIERED
DOCTRINE_CANDIDATE
ARCHIVED
REOPENED
```

### Laws

- states describe processing/epistemic handling, not truth;
- CORROBORATED does not mean universally true;
- CONTRADICTED does not imply rejected;
- ARCHIVED does not erase provenance;
- REOPENED preserves history;
- no caller may skip required predecessor evidence by asserting a later state.

### State-transition table

Each transition defines:
- required inputs;
- refusing conditions;
- emitted receipt;
- reversible/non-reversible effects;
- evidence retained.

---

## B1.C2.S3 — Source status and missingness taxonomy

Provider failure must never collapse into "no evidence."

Freeze status vocabulary:

- OK
- NO_RESULTS
- PARTIAL_RESULTS
- RATE_LIMITED
- AUTH_FAILURE
- ACCESS_BLOCKED
- PAYMENT_REQUIRED
- PROVIDER_FAILURE
- SCHEMA_DRIFT
- TEMPORAL_SEMANTIC_REVIEW
- UNSUPPORTED_QUERY
- NOT_CONFIGURED
- RIGHTS_RESTRICTED
- SOURCE_REMOVED
- UNKNOWN

### Core law

`NO_RESULTS != PROVIDER_FAILURE != NOT_CONFIGURED != ACCESS_BLOCKED`

Every synthesis must be able to disclose which surfaces were actually searched successfully.

---

## B1.C2.S4 — Research question and scope contract

A research question must carry:

- question_id;
- exact question;
- scope;
- excluded scope;
- requested depth;
- target decision/use;
- time boundary if any;
- source allow/deny policy;
- rights constraints;
- budget envelope;
- deadline;
- required outputs;
- stopping conditions;
- operator/Hermes origin reference.

### Scope laws

- widening scope requires an amendment/child plan;
- unanswered subquestions remain explicit;
- "general research" does not mean unbounded research;
- the plan records what was not searched.

---

## B1.C2.S5 — Negative and unresolved knowledge

Institutional research must preserve:
- failed searches;
- null findings;
- contradictory results;
- inconclusive results;
- inaccessible sources;
- insufficient-evidence states;
- abandoned hypotheses;
- invalidated interpretations.

Define first-class states:
- `UNRESOLVED`
- `INSUFFICIENT_EVIDENCE`
- `NO_SUPPORT_FOUND_WITHIN_SCOPE`
- `CONFLICTING_EVIDENCE`
- `SOURCE_ACCESS_INCOMPLETE`

None may be coerced into SUPPORTS/REFUTES to simplify UI.

### Gate C2

**PASS_B1_C2_EPISTEMIC_OBJECTS** requires:
- object schemas defined;
- lifecycle transitions versioned;
- provider missingness separated;
- question scope contract enforced;
- unresolved/negative knowledge survives round trip.

---

# 4. B1.C3 — Evidence, Provenance & Reproducibility

## B1.C3.S1 — Evidence envelope

Every material evidence artifact must carry at minimum:

- evidence_id;
- evidence_class;
- source_id;
- source_locator;
- acquisition_id;
- acquired_at;
- content hash;
- raw payload hash where available;
- parser name/version;
- source revision;
- publication/update date if known;
- rights class;
- transformation lineage;
- parent artifact IDs;
- completeness/missingness state;
- limitations;
- contract version.

No important research artifact may be stored as prose without an envelope reference.

---

## B1.C3.S2 — Evidence classes and source-role separation

Freeze base evidence classes:

- EXTERNAL_SCHOLARLY
- INTERNAL_DOCUMENT
- INTERNAL_EMPIRICAL
- WEB_DISCOVERY
- CODE_OR_SPECIFICATION
- USER_SUPPLIED
- INSTITUTIONAL_CANON_REFERENCE

Evidence class is descriptive, not a truth ranking.

Additional descriptors may include:
- peer_review_status;
- replication_status;
- primary/secondary/tertiary;
- experimental/observational/theoretical;
- standard/specification;
- authoritative legal/regulatory;
- first-party/third-party;
- direct/derived.

No universal scalar "source quality score" is constitutional.

---

## B1.C3.S3 — Transformation lineage

Any transformation must reference its parent.

Examples:

```text
raw provider payload
→ parsed metadata
→ normalized work
→ extracted passage
→ claim
→ claim/evidence relation
→ synthesis
→ dossier
```

Each step records:
- transformer/version;
- timestamp;
- input IDs/hashes;
- output ID/hash;
- parameters;
- failure/partial notes.

A synthesis must be traceable to evidence, not merely to prior summaries.

---

## B1.C3.S4 — Deterministic replay and contract fingerprints

Where deterministic processing is possible:

> same inputs + same contract versions + same parameters => same normalized output.

Versioned definitions receive fingerprints.

Examples:
- canonicalization policy;
- dedup policy;
- source-status mapping;
- claim-relation vocabulary;
- rights policy;
- lifecycle transition table.

Nondeterministic model-assisted steps must carry:
- model/provider identifier;
- prompt/template version;
- decoding parameters where accessible;
- input artifact IDs;
- output artifact ID;
- explicit `NONDETERMINISTIC_TRANSFORM` marker.

Model output itself is not source evidence.

---

## B1.C3.S5 — Evidence correction without historical rewrite

Adopt institutional stress-suite discipline:

- false historical claims remain historical;
- correction is additive;
- superseding artifact points to prior artifact;
- previous evidence is not silently edited to look correct;
- latest-current view may resolve supersession but audit view preserves lineage.

Define:
- `supersedes`
- `superseded_by`
- `retracts`
- `corrects`
- `reinterprets`

### Gate C3

**PASS_B1_C3_PROVENANCE** requires:
- envelope minimum fields enforced;
- transformation lineage complete;
- policy fingerprints versioned;
- deterministic paths replay;
- corrections preserve history;
- missing provenance causes refusal for decision-grade outputs.

---

# 5. B1.C4 — Authority, Rights & Governance

## B1.C4.S1 — Authority classes

Authority is separate from evidence, phase, confidence, source prestige, citation count, or Hermes role.

Initial authority classes:

- READ_LOCAL
- READ_EXTERNAL_PUBLIC
- READ_EXTERNAL_AUTHENTICATED
- ACQUIRE_METADATA
- ACQUIRE_DOCUMENT
- WRITE_RESEARCH_STORE
- CREATE_RESEARCH_TASK
- CREATE_SYNTHESIS
- CREATE_DOSSIER
- CREATE_DOCTRINE_CANDIDATE
- MODIFY_SOURCE_POLICY
- MODIFY_RESEARCH_POLICY
- PROMOTE_INSTITUTIONAL_DOCTRINE
- MUTATE_OCE_CANON
- MUTATE_QCAE_CANON

Research Mesh/Hermes default authority must exclude the final three and any equivalent future institutional mutation rights.

---

## B1.C4.S2 — Hermes authority firewall

Hermes can operate approved workflows but cannot turn operator convenience into sovereignty.

Hermes may:
- create scoped research tasks;
- invoke approved providers;
- request synthesis/dossiers;
- retrieve stored evidence;
- schedule bounded refreshes when enabled.

Hermes may not:
- alter constitutional policies;
- suppress contradictory evidence;
- reclassify failures as success;
- change rights class;
- promote doctrine;
- mutate OCE/QCAE;
- bypass source policy with arbitrary browsing credentials.

Every Hermes task emits a receipt.

---

## B1.C4.S3 — Rights, privacy and data-use classes

Freeze initial rights classes:

- PUBLIC_METADATA
- PUBLIC_OPEN_ACCESS
- PUBLIC_RESTRICTED_REUSE
- LICENSED_INTERNAL
- USER_PROVIDED_PRIVATE
- CLIENT_CONFIDENTIAL
- PROPRIETARY_INTERNAL
- UNKNOWN_RIGHTS
- PROHIBITED_FOR_REUSE

Rights state controls:
- storage;
- quoting;
- redistribution;
- embeddings/vectorization;
- cross-project reuse;
- external model disclosure;
- dossier export.

Unknown rights fail closed for redistribution and cross-domain reuse.

---

## B1.C4.S4 — Source policy / egress policy

Every provider/source class declares:
- network authority required;
- authentication class;
- rate budget;
- cost class;
- retry policy;
- allowed data classes;
- retention policy;
- rights expectations;
- failure semantics.

Adapters may not read arbitrary credentials directly. Credential access belongs behind a future governed secret/config boundary.

Book 1 requires the contract even if Book 2 implements the full fabric.

---

## B1.C4.S5 — Budget, concurrency and stop authority

Research must be bounded.

A ResearchPlan may define:
- max provider calls;
- max results;
- max documents acquired;
- max wall-clock;
- max model tokens;
- max model cost;
- max concurrent workers;
- max recursion depth;
- stop-on-saturation;
- stop-on-rights-block;
- stop-on-budget;
- stop-on-operator-review.

Only declared stop conditions may terminate a plan as "completed." Other interruption states remain explicit.

### Gate C4

**PASS_B1_C4_GOVERNANCE** requires:
- authority vocabulary enforced;
- Hermes firewall tested;
- rights classes tested;
- egress/source policy schema exists;
- budgets/stops cannot be bypassed by caller booleans;
- institutional mutation denied by default.

---

# 6. B1.C5 — Truth, Uncertainty, Contradiction & Promotion

## B1.C5.S1 — Claim model

A Claim is not free prose.

Minimum fields:
- claim_id;
- proposition;
- scope;
- qualifiers;
- temporal validity if known;
- domain;
- extractor/origin;
- supporting evidence links;
- contradicting evidence links;
- status;
- uncertainty descriptor;
- assumptions;
- version.

Claim status vocabulary:
- OBSERVED
- PROPOSED
- SUPPORTED
- QUALIFIED
- CONTESTED
- REFUTED_WITHIN_SCOPE
- UNRESOLVED
- SUPERSEDED

No claim may be SUPPORTED merely because it appears in a paper.

---

## B1.C5.S2 — Claim/evidence relation vocabulary

Relations must be explicit:

- SUPPORTS
- PARTIALLY_SUPPORTS
- QUALIFIES
- CONTRADICTS
- REFUTES_WITHIN_SCOPE
- REPLICATES
- FAILS_TO_REPLICATE
- EXTENDS
- DEPENDS_ON
- USES_SAME_DATA
- USES_OVERLAPPING_DATA
- CITES_ONLY
- BACKGROUND_ONLY
- METHOD_ONLY
- INCOMPARABLE

This prevents citation edges from masquerading as evidentiary support.

---

## B1.C5.S3 — Independence and corroboration

Corroboration is a vector, not a source count.

Initial independence dimensions:
- dataset independence;
- author/team independence;
- institution independence;
- method independence;
- funding/sponsor independence where available;
- source/provider independence;
- temporal replication;
- implementation/code independence.

The system must be able to represent:
- five papers from one dataset;
- two independent replications;
as materially different corroboration structures.

No constitutional scalar consensus score is required in Book 1.

---

## B1.C5.S4 — Contradiction and uncertainty model

A contradiction record includes:
- claim A;
- claim B;
- contradiction type;
- comparability status;
- scope overlap;
- temporal overlap;
- methodological differences;
- population/data differences;
- unresolved discriminators;
- evidence refs;
- adjudication state.

Contradictions may end as:
- TRUE_CONTRADICTION
- SCOPE_DIFFERENCE
- TEMPORAL_DRIFT
- METHOD_DIFFERENCE
- DATASET_DIFFERENCE
- DEFINITION_DIFFERENCE
- NOT_COMPARABLE
- UNRESOLVED

Research Mesh must never force a contradiction resolution it cannot evidence.

---

## B1.C5.S5 — Synthesis and promotion firewall

A synthesis or dossier is a research artifact, not institutional doctrine.

Promotion path:

```text
evidence
→ claims
→ contradiction/corroboration analysis
→ synthesis
→ Research Dossier
→ DoctrineCandidate
→ external institutional review/promotion path
```

Research Mesh may emit `DoctrineCandidate`. It may not emit `InstitutionalDoctrine`.

Required candidate fields:
- candidate_id;
- source dossiers;
- claim set;
- unresolved contradictions;
- confidence/uncertainty basis;
- scope;
- assumptions;
- expiry/review trigger if applicable;
- required independent validation;
- promotion authority = EXTERNAL_TO_RESEARCH_MESH.

### Gate C5

**PASS_B1_C5_TRUTH_AND_PROMOTION** requires:
- claim object frozen;
- claim/evidence relations frozen;
- independence represented as a vector;
- contradiction states preserve unresolved cases;
- synthesis cannot self-promote;
- citation count/source count cannot directly create truth state.

---

# 7. Book 1 build artifacts

Proposed package:

```text
oce/research_mesh_v2/
  constitution/
    __init__.py
    system_identity.py
    vocabulary.py
    authority.py
    rights.py
    lifecycle.py
    provenance.py
    claims.py
    contradiction.py
    promotion.py
    fingerprints.py
  contracts/
    research_question.py
    research_plan.py
    evidence.py
    task_receipt.py
    dossier.py
    doctrine_candidate.py
  tests/book_01/
    test_c1_system_identity.py
    test_c2_epistemic_objects.py
    test_c3_provenance.py
    test_c4_governance.py
    test_c5_truth_promotion.py
    test_b1_adversarial.py
```

Schemas may begin as frozen dataclasses/Pydantic models, but every public record must serialize deterministically and forbid unknown fields once frozen.

---

# 8. Book 1 adversarial qualification matrix

At minimum Book 1 must prove these cases:

| ID | Attack / case | Required result |
|---|---|---|
| B1-A01 | Hermes marks synthesis as institutional doctrine | REFUSE |
| B1-A02 | provider failure reported as no results | REFUSE |
| B1-A03 | five duplicate-source papers counted as five independent confirmations | REFUSE |
| B1-A04 | evidence without source/provenance lineage enters decision-grade dossier | REFUSE |
| B1-A05 | caller asserts CORROBORATED without required relation artifacts | REFUSE |
| B1-A06 | archived evidence is deleted during lifecycle transition | REFUSE |
| B1-A07 | correction overwrites historical claim | REFUSE |
| B1-A08 | UNKNOWN_RIGHTS artifact exported/reused broadly | REFUSE |
| B1-A09 | high citation count directly upgrades claim truth state | REFUSE |
| B1-A10 | unresolved contradiction forced to nearest resolved class | REFUSE |
| B1-A11 | research plan silently widens scope | REFUSE |
| B1-A12 | budget ceiling bypassed by caller boolean | REFUSE |
| B1-A13 | Research Mesh mutates QCAE/OCE registry object | REFUSE |
| B1-A14 | trading-specific field required for general evidence | REFUSE |
| B1-A15 | same deterministic input + same contract version yields different canonical bytes | REFUSE |
| B1-A16 | nondeterministic model output presented as source evidence | REFUSE |
| B1-A17 | source count treated as consensus | REFUSE |
| B1-A18 | client/private material promoted into general institutional corpus without rights | REFUSE |
| B1-A19 | no OCE runtime available | STANDALONE PASS |
| B1-A20 | no Hermes available | STANDALONE PASS |

---

# 9. Book 1 implementation sequence

## B1-I0 — Archaeology and contract lock
- inventory current V0 objects;
- map old Research Mesh concepts;
- map QCAE A-001 boundary;
- map institutional stress-suite laws;
- record conflicts/open questions;
- no production behavior changes beyond tests/fixtures.

**Exit:** `PASS_B1_I0_ARCHAEOLOGY`

## B1-I1 — C1 system identity
Build identity/boundary/registry ownership/amendment contracts.

**Exit:** `PASS_B1_C1_SYSTEM_IDENTITY`

## B1-I2 — C2 epistemic objects
Build canonical object schemas, lifecycle, source status, scope, unresolved states.

**Exit:** `PASS_B1_C2_EPISTEMIC_OBJECTS`

## B1-I3 — C3 provenance
Build evidence envelopes, lineage, policy fingerprints, correction/supersession model.

**Exit:** `PASS_B1_C3_PROVENANCE`

## B1-I4 — C4 governance
Build authority, Hermes firewall, rights, source policy, budget/stop contracts.

**Exit:** `PASS_B1_C4_GOVERNANCE`

## B1-I5 — C5 truth/promotion
Build claims, relations, independence vector, contradiction model, doctrine-candidate firewall.

**Exit:** `PASS_B1_C5_TRUTH_AND_PROMOTION`

## B1-I6 — Cross-chapter adversarial suite
Run A01–A20 plus serialization, determinism, mutation and fail-closed attacks.

**Exit:** `PASS_B1_ADVERSARIAL_QUALIFICATION`

## B1-I7 — Freeze package
Emit:
- Book 1 freeze manifest;
- schema fingerprints;
- test artifact/receipt;
- known limitations;
- unresolved questions;
- exact tested tree;
- supersession policy;
- Book 2 handoff.

**Exit:** `PASS_BOOK_1_CONSTITUTIONAL_RESEARCH_CONTRACTS`

---

# 10. Book 1 exit gate

Book 1 can freeze only when:

1. all five chapter gates pass;
2. A01–A20 pass;
3. no favorable-default authority path exists;
4. provider failure/missingness semantics are distinct;
5. deterministic public records round-trip;
6. provenance cannot be omitted for decision-grade artifacts;
7. rights restrictions survive transforms;
8. historical corrections are additive;
9. Hermes cannot self-promote doctrine or mutate policy;
10. OCE/QCAE absence does not break standalone research operation;
11. all unresolved items are recorded, not hidden;
12. Book 2 can consume Book 1 contracts without redefining them.

**Final gate:** `PASS_BOOK_1_CONSTITUTIONAL_RESEARCH_CONTRACTS`

---

# 11. Explicit non-goals for Book 1

Do not build yet:
- full OpenAlex/arXiv/S2 production hardening;
- Crossref/PubMed/SSRN/Zenodo adapters;
- PDF download pipeline;
- OCR;
- embeddings/vector database;
- BM25/reranking;
- citation crawling;
- claim-extraction LLM;
- autonomous research agents;
- synthesis engine;
- Research Hub UI;
- OCE runtime integration;
- QCAE live handoff;
- institutional doctrine promotion.

Book 1 creates the laws these later systems must obey.

---

# 12. Book 2 handoff

Book 2 — Acquisition Fabric — receives:

- frozen source-status vocabulary;
- evidence envelope;
- authority contract;
- rights contract;
- source-policy schema;
- acquisition identity requirements;
- lifecycle entry conditions;
- provenance/fingerprint requirements;
- bounded budget semantics.

Book 2 may implement providers and storage, but it may not redefine Book 1 constitutional semantics without a separately reviewed amendment.
