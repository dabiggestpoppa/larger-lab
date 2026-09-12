# QCAE Amendment A-001 — Research Mesh Boundary and Economic Experience

**Document ID:** QCAE-AMEND-A001  
**Version:** 1.0  
**Status:** OPERATOR-DIRECTED ADDITIVE AMENDMENT  
**Canon affected:** QCAE v0.1 Books I–VI remain COMPLETE / FROZEN  
**Primary seams:** Blocks 2, 8, 9, 11, 12, 14, 15, 16, 18  
**Build authorization:** INTERFACE/PLANNING ONLY; no autonomous capital or marketplace authority

---

## 1. Decision

QCAE shall remain the institution's **capability-acquisition system**, not become a second autonomous research institution.

The boundary is:

```text
OCE             = what objective must be executed?
Research Mesh   = what must the institution know?
QCAE            = what must the institution be able to do?
Institution     = what validated experience may change the institution?
```

Research Mesh owns epistemic acquisition: unknown identification, research planning, source acquisition, evidence evaluation, synthesis, contradiction handling, consensus, and doctrine-candidate production.

QCAE owns capability acquisition: capability-gap specification, prior-art consumption, build/borrow/buy/rent decisions, extraction/reimplementation, proving, packaging, integration, registry promotion, monitoring, and retirement.

Neither system receives authority merely because it produced an artifact.

---

## 2. Freeze preservation

This amendment does not rewrite QCAE Books I–VI or Blocks 0–18. It constrains how frozen canon is interpreted at the Research Mesh boundary.

In particular, Chapter 2.5 `Research Discovery` remains valid as **capability prior-art discovery**, but broad epistemic investigation is delegated to Research Mesh whenever Research Mesh is available.

QCAE may still locate specifications, papers, standards, implementations, benchmarks, and reproducibility assets needed to investigate a capability candidate. It must not duplicate Research Mesh's general research queues, evidence synthesis, knowledge graph, doctrine lifecycle, or research-agent institution.

---

## 3. Gap taxonomy

Before work is routed, the originating system should classify the narrowest applicable gap.

### `KNOWLEDGE_GAP`
A claim, mechanism, domain fact, uncertainty, or evidence question prevents sound action.

**Owner:** Research Mesh.

### `CAPABILITY_GAP`
The desired behavior is understood sufficiently, but OCE cannot execute it under the required contract.

**Owner:** QCAE.

### `EXECUTION_FAILURE`
A known capability failed to perform its existing contract. It is not automatically a new capability gap.

**Owner:** execution/service owner first; QCAE only if evidence shows acquisition, repair, or replacement is required.

### `INSTITUTIONAL_LEARNING_CANDIDATE`
Repeated experience suggests a policy, ontology, architecture, or stable-epoch assumption may deserve review.

**Owner:** Institution / Transformation Governor path. QCAE and Research Mesh may submit evidence but may not self-promote the change.

### Mixed gaps
One objective may generate multiple linked gaps. They remain separately typed and separately owned.

---

## 4. Research Mesh → QCAE handoff

QCAE may issue a `ResearchCapabilityHandoff` when capability acquisition depends on unresolved knowledge.

Minimum request content:

```text
request_id
origin_objective_id
capability_gap_id
research_question
capability_context
known_constraints
budget envelope
deadline
data-rights classification
source allow/deny policy
required outputs
```

Research Mesh returns, at minimum where applicable:

```text
status
evidence package
source/provenance lineage
synthesized finding
uncertainty/confidence statement
assumptions
contradictions / unresolved questions
testable claims
specification or behavioral contract inputs
recommended next evidence action
```

QCAE must preserve this lineage in resulting Capability Receipts.

A Research Mesh conclusion is evidence input, not proof that an implementation works. QCAE proving obligations remain unchanged.

---

## 5. Standalone-first fallback

QCAE's frozen invariant remains:

> Standalone now. OCE-compatible by contract. OCE-governed later.

Therefore Research Mesh absence must not make QCAE unusable.

When Research Mesh is unavailable, QCAE may invoke a bounded `ResearchFallbackAdapter` only to gather capability-specific prior art necessary to continue or to determine that work must stop.

Fallback restrictions:

- no autonomous doctrine promotion;
- no attempt to recreate Research Mesh consensus/synthesis infrastructure;
- explicit source provenance;
- explicit uncertainty;
- bounded source/time/compute budget;
- result marked `LOCAL_FALLBACK_RESEARCH`;
- revalidation through Research Mesh required before any high-dependency knowledge claim is treated as institutional knowledge.

---

## 6. Registry ownership

### Research Mesh owns

- research observations;
- source/evidence records;
- contradiction records;
- synthesized knowledge artifacts;
- doctrine candidates and doctrine lifecycle;
- epistemic provenance.

### QCAE owns

- capability requests;
- capability atoms/graphs;
- implementation candidates;
- proving evidence specific to executable behavior;
- Capability Receipts;
- capability registry and lifecycle;
- implementation/runtime provenance.

### OCE / Institution

OCE may query both domains. Institution governs high-level promotion and epoch change.

References may cross registries, but ownership and lifecycle authority do not merge.

---

## 7. No-duplication rules

QCAE shall not independently rebuild Research Mesh primitives merely because they are useful during acquisition.

Prohibited duplication includes a second general-purpose:

- autonomous literature ingestion institution;
- research task generator;
- evidence-consensus engine;
- doctrine promotion pipeline;
- generalized knowledge graph/ontology lifecycle;
- research gap queue;
- paper distillation institution;
- epistemic synthesis authority.

QCAE may consume these through contracts and maintain only the minimum local cache/index required for capability workflows.

Research Mesh likewise should not absorb QCAE proving labs, sandbox acquisition, dependency containment, repository forensics, capability receipts, or executable capability registry.

---

## 8. Capability economics extension

A capability gap does not imply `BUILD`.

QCAE acquisition decisions expand to:

```text
USE      existing proven internal capability
BORROW   reuse an internal/shared capability without new ownership
RENT     invoke an external agent/service for bounded work
BUY      consume an external API/service/product under contract
ACQUIRE  absorb a reusable implementation/component
BUILD    implement/reimplement strategically valuable capability
RESEARCH route unresolved knowledge to Research Mesh
DECLINE  reject when expected institutional value does not justify burden/risk/cost
```

Decision evidence should include:

- expected frequency of reuse;
- strategic transferability;
- external price and reliability;
- switching cost/vendor dependence;
- privacy/data-rights constraints;
- latency/SLA;
- reputation/counterparty risk;
- security/trust boundary;
- build and maintenance burden;
- reversibility;
- total cost of ownership.

External agent marketplaces may therefore become both **supply surfaces** for QCAE procurement and **demand surfaces** for OCE revenue work.

---

## 9. Commercial Research Mesh isolation

Research Mesh may operate in at least these modes:

- `INTERNAL_ACQUISITION`
- `QCAE_CAPABILITY_RESEARCH`
- `CLIENT_RESEARCH_SERVICE`

`CLIENT_RESEARCH_SERVICE` artifacts are not institutional doctrine merely because they were delivered or paid for.

Client work may contain:

- client-specific assumptions;
- licensed/proprietary material;
- confidential context;
- deliberately narrow scope;
- acceptance criteria that are not institutional truth criteria.

Therefore commercial outputs require de-identification, rights review, abstraction, reproduction where needed, and normal Research Mesh/Institution promotion before any generalized lesson becomes internal doctrine.

---

## 10. Economic Experience boundary

External paid work produces `EconomicExperienceRecord` artifacts. These records are evidence about real execution under external constraints.

They may include:

```text
source
opportunity_id
objective_type
payout
direct_cost
compute_cost
tool_cost
human_intervention
capabilities_used
research_used
knowledge_gaps_found
capability_gaps_found
errors_encountered
client_revisions
QA_result
customer_acceptance
execution_time
reusability_score
transferability_score
data_rights
lesson_candidates
```

An Economic Experience record is **not an instruction to self-modify**.

Permitted downstream outputs include:

- `KNOWLEDGE_GAP` → Research Mesh;
- `CAPABILITY_GAP` → QCAE;
- reliability/exception/patch evidence → Institution;
- market/economic observations → Opportunity Exchange/allocator;
- candidate lessons → institutional promotion pipeline.

---

## 11. Promotion firewall

No external job, buyer preference, payout, rating, single failure, or single success may directly alter frozen canon, institutional doctrine, trading models, or high-level policy.

Canonical path:

```text
external experience
→ rights/privacy filtering
→ de-identification
→ abstraction
→ classification
→ independent reproduction/testing where material
→ evidence review
→ appropriate registry candidate
→ institutional phase/governance process
→ promotion only if admitted
```

Client proprietary content is excluded from cross-domain reuse unless explicit rights exist. General methods learned while solving a job may be retained only after they are separable from client-protected material.

---

## 12. OCE event contracts

QCAE should be able to consume or emit references for:

```text
CapabilityGapDetected
KnowledgeGapDetected
ResearchHandoffRequested
ResearchHandoffCompleted
ExternalCapabilityCandidateFound
CapabilityProcurementProposed
CapabilityAcquisitionStarted
CapabilityProved
CapabilityRejected
CapabilityPromoted
EconomicExperienceRecorded
InstitutionalLearningCandidateRaised
```

Events carry immutable IDs and provenance. Events communicate facts/proposals; they do not bypass authority gates.

---

## 13. Implementation impact map

### P0 — Skeleton + Domain Schemas
Add gap-type, Research Mesh handoff, external procurement, and Economic Experience references.

### P1 — Evidence + Registry Spine
Support cross-registry provenance without collapsing knowledge and capability ownership.

### P2 — Job Runtime + Local Governance
Enforce fallback research budgets and authority classes.

### P3 — Discovery Vertical Slice
Keep capability prior-art discovery; add an explicit Research Mesh delegation seam.

### P4–P7
No weakening of repository intelligence, trust, or proving requirements. Research conclusions remain claims until executable contracts are proved.

### P8 — Acquisition + Integration Workflow
Extend acquisition decisions to `RENT` and `BUY`; preserve rollback/vendor-risk analysis.

### P9 — Quant Validation
No commercial/client experience may bypass independent quant validation or trading authority.

### P10 — Agent Orchestration
Add typed worker handoffs; do not create generalized research workers that compete with Research Mesh.

### P11 — Monitoring + Reverse Acquisition
External service drift may trigger revalidation/build-vs-buy review.

### P12 — OCE Adapter / Governance Migration
Wire the full OCE ↔ Research Mesh ↔ QCAE ↔ Institution event boundary and registry federation.

---

## 14. Required contract tests

At minimum, qualification must cover:

1. known capability, no research required;
2. genuine knowledge gap routed to Research Mesh;
3. capability gap with sufficient knowledge;
4. mixed knowledge + capability gap;
5. Research Mesh unavailable → bounded fallback;
6. fallback result cannot self-promote doctrine;
7. Research Mesh returns uncertainty / unresolved contradiction;
8. QCAE refuses to treat literature claim as implementation proof;
9. external service is cheaper than build → `RENT/BUY` proposal;
10. reusable strategic capability favors `ACQUIRE/BUILD` under evidence;
11. proprietary client artifact cannot enter doctrine/capability corpus improperly;
12. repeated external failures raise institutional candidate without self-mutation;
13. paid client acceptance does not equal epistemic validation;
14. external provider drift triggers revalidation;
15. OCE absent: standalone QCAE remains functional.

---

## 15. Invariants added by A-001

1. Research Mesh answers **what must be known**; QCAE answers **what must be executable**.
2. Knowledge and capability registries may reference each other but never silently merge authority.
3. QCAE consumes Research Mesh evidence and specifications; it does not inherit epistemic sovereignty.
4. Research Mesh cannot prove executable capability merely by describing it.
5. External work is evidence and curriculum, never direct self-modification authority.
6. Paid acceptance is not proof of institutional truth.
7. Client-protected information is not an institutional learning asset by default.
8. Capability gaps may be solved by use, borrow, rent, buy, acquire, build, research, or decline.
9. Net Capability Gain must still exceed New System Burden.
10. Frozen QCAE canon remains frozen; this amendment governs interfaces and implementation interpretation.

---

## 16. Relationship to institutional evolution

QCAE may create evidence that a capability architecture is repeatedly inadequate. It may submit an `INSTITUTIONAL_LEARNING_CANDIDATE`, but it may not decide that a new institutional epoch is warranted.

That decision belongs to OCE's institutional governance, including the stable-epoch / transformation-window discipline and Transformation Governor where applicable.

The desired loop is therefore:

```text
OCE encounters objective
→ gap classification
→ Research Mesh closes knowledge gaps
→ QCAE closes executable capability gaps
→ OCE executes
→ QA / external result / economics
→ EconomicExperienceRecord
→ governed abstraction and validation
→ Research Mesh / QCAE / Institution receive only the lessons they own
→ future OCE execution improves
```

This is a coupled learning institution, not overlapping autonomous subsystems.