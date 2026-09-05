# G0 — Architecture Ingestion Packet
## OCE Institutional Stress Suite — Dependency / Contradiction Map

**Document ID:** STRESS-G0-INGESTION-001
**Version:** 1.0
**Gate:** G0 (Planning / Architecture Ingestion)
**Status:** COMPLETE — pending operator review
**Implementation branch:** `agent/oce-institutional-stress-suite-build`
**Base SHA (planning source head):** `7105347f6e8e4807cca2d8d450baa149b5fa0aeb`
**Base branch:** `agent/oce-agent-ergonomics-amendment` (remote head, fetched 2026-08-31)
**Author:** Stress Suite implementation agent (G0 only)
**Exit label:** `PASS_G0_PLANNING_INGESTION` (see §20; contradictions and ambiguities recorded, none fatal to proceeding)

---

## 0. Purpose

This packet is the G0 deliverable of the OCE Institutional Stress Suite. It records:

1. what is authoritative (completed OCE authority);
2. what is under test (proposed architecture);
3. what is test harness (does not exist yet — G1);
4. what is test evidence (does not exist yet — G2+);
5. the canonical state machines the harness must enforce;
6. the knowledge lifecycle the scenarios assume;
7. the evidence-object contracts the harness must instantiate;
8. the Transformation Governor roles and scope ladder under test;
9. hard authority boundaries that may never be crossed by any scenario;
10. Quant / Crypto / CEREBUS / manual domain boundaries;
11. known conflicts among A-002/A-004/A-005/A-006/A-007/A-008/A-009/A-010;
12. assumptions the Stress Suite depends on;
13. architectural ambiguities that could change expected scenario outcomes;
14. existing repository contracts that can be reused;
15. proposed new implementation surfaces;
16. parts that MUST remain simulation-only;
17. stop-condition check results;
18. the adversarial review summary (full answers in `G0_ADVERSARIAL_REVIEW.md`).

This packet does **not** authorize G1 or any implementation. It is the ingestion record only.

---

## 1. Epistemic posture

Per the master implementation prompt, this suite attempts to **falsify** A-009 and A-010
(and, through the scenario program, the proposed A-004 through A-008 package). Nothing in
this packet converts operator preference into evidence, agent confidence into canonical
truth, high capability into expanded authority, or high apparent profit into reduced
validation requirements. Where the specification is silent or contradictory, this packet
records the silence or the contradiction rather than choosing the interpretation the agent
prefers.

---

## 2. Authority hierarchy — COMPLETED vs PROPOSED

### 2.1 COMPLETED AUTHORITY (ratified / gated; not under test)

| ID | Document | Status | Notes |
|---|---|---|---|
| CONST-1.1 | OCE Golden System Architecture Constitution v1.1 (`OCE_GOLDEN_SYSTEM_ARCHITECTURE_CONSTITUTION_v1.1.md`) | Ratified amended constitutional baseline (2026-08-17); includes A-001 | Owner and final authority: Operator. Binding on everything, including the harness. |
| A-001 | Holistic Build Cycle + Hybrid Cloud (inside Constitution 1.1) | Ratified | Principles 13–15, Articles XVII–XIX. |
| A-003 | Local-First Cloud Activation Deferred (`OCE_ARCHITECTURE_AMENDMENT_A003_...`) | RATIFIED BY OPERATOR DECISION | `LOCAL_FIRST_CLOUD_ACTIVATION_DEFERRED`; no cloud purchase/provisioning/deployment; cloud state `DEFERRED_BY_OPERATOR`; zero cloud cost. |
| ATLAS-1.0 | OCE Master Program Atlas v1.0 (`OCE_MASTER_PROGRAM_ATLAS_v1.0.md`) | Ratified program map; B0 gated complete; B1 planning ratified | B0 `GATED_COMPLETE`; B1 `ARTICULATING`; Blocks 2–10 `MAPPED`. |
| B0 | Constitutional Control | GATED_COMPLETE (per Atlas) | 25 sections approved; contradiction/adversarial reviews passed. |
| B1 Local Ground (incl. B1-L8R4 lineage) | Local-ground ledger evidence on `oce`/`oce-program-build` | Gated complete per lineage (d3df9eb4 = `B1-L8R4: record final-runtime closure cycle in Local Ground ledger`) | Not re-audited in G0; treated as completed lineage evidence. |
| B2 | Control Plane canonical contracts (commit `dbf12836` `B2-C1: build control plane canonical contracts and schemas`) | B2-era evidence on lineage | Source of `infrastructure/control-plane/contracts/*.schema.json` (see §15). |
| B3 | Worker Fabric (`infrastructure/control-plane/B3-EVIDENCE-RECORD.md`) | `COMPLETE / CLOSURE_REPAIR_DONE / GATED_COMPLETE` on `oce-program-build` (implementation head `2e63c765`, run `33383000302`, 288/288 tests, independent gate PASS, cost $0) | Authoritative completed evidence. Includes R1–R10 repair history; premature closure corrected (B3-R1). B3-EVIDENCE-RECORD.md is present on this branch and is the authoritative record. |
| A-002 (partial) | PO/Hermes boundary (`OCE_ARCHITECTURE_AMENDMENT_A002_...`) | PROPOSED for operator ratification — see conflict CON-01 | Included in "proposed" set; constitutional separation content (PO≠Hermes, distinct namespaces) is treated as planning doctrine, but A-002 §7 (Hermes replaces OpenClaw) is **not** authoritative per A-007 §7 / Impact Atlas §3. |

### 2.2 PROPOSED ARCHITECTURE — UNDER TEST (nothing here is self-validating truth)

| ID | Document | Status | Role in suite |
|---|---|---|---|
| LL-ARCH-1.1 | LARGER_LAB_INSTITUTIONAL_ARCHITECTURE_v1.1.md | PROPOSED SUPERSEDING ARCHITECTURE — NO BUILD AUTHORIZATION | Highest-level object under test: identity vs implementation, cybernetic circuit, stabilize/transform, epistemic lifecycle, falsification list (§23). |
| A-004 | Agent Ergonomics and Accretive System v1.0 | PROPOSED — OPERATOR REVIEW REQUIRED | Under test (esp. accretion model vs A-009 metabolism — CON-04). |
| A-005 | Institutional Intelligence Architecture v1.0 | PROPOSED FOR OPERATOR RATIFICATION | Under test (esp. static-truth framing vs A-009 — CON-05). |
| A-006 | Autonomous Discovery and Knowledge Refinery v1.0 | PROPOSED FOR OPERATOR RATIFICATION | Under test (esp. gap-only discovery vs anomaly-driven — CON-06). |
| A-007 | Runtime-Neutral Cognitive Fabric v1.0 | PROPOSED FOR OPERATOR RATIFICATION | Under test (esp. routing without independence criteria — CON-07). |
| A-008 | Autonomous Quant Research Institution v1.0 | PROPOSED FOR OPERATOR RATIFICATION | Under test (esp. Genome ontology prison — CON-08). |
| A-009 | Cybernetic Evolution and Organic Alignment v1.0 | PROPOSED FOR OPERATOR RATIFICATION | Primary object under test (epochs, lifecycle, anomaly protocol, sovereignty). |
| A-010 | Transformation Governor and Epistemic Phase Control v1.0 | PROPOSED FOR OPERATOR RATIFICATION | Primary object under test (Governor machine, channels, hysteresis, scope ladder, admissibility). |
| A010-RT | A-010 Transformation Governor Adversarial Matrix v1.0 | PROPOSED ADVERSARIAL REVIEW INPUT | Threat list (T1–T24) that the suite operationalizes. |
| PM-RM | OCE Post-Michels Architecture Revision Matrix v1.0 | PROPOSED REVISION MAP — NO BUILD AUTHORIZATION | Records required revisions of A-004..A-008 (see §12 CON-04..08 and AMB-02). |
| STRESS-BOOK | OCE Institutional Stress Suite Book v1.0 | EXECUTION-READY PLANNING BOOK — NO PRODUCTION MUTATION AUTHORIZATION | Test specification (S01–S24, harness contract, receipts). |
| STRESS-CAT | OCE Stress Suite Scenario Catalog v1.0 | EXECUTION-READY CATALOG | Scenario index + classes + mandatory artifacts + assertion set. |
| STRESS-GATES | OCE Stress Suite Execution Gates v1.0 | AGENT HANDOFF CONTRACT | Gate discipline (G0–G10), commit contract, stop conditions. |

### 2.3 TEST HARNESS (does not exist yet — built in G1)

Generic machinery only: schemas, validators, phase-state engine, lifecycle engine, fixture
loader, forbidden-transition validation, authority-state checks, deterministic replay.
No scenario-specific cleverness inside the generic engine (STRESS-GATES G1, Stress Suite
Book §Stage 0).

### 2.4 TEST EVIDENCE (does not exist yet — produced G2+)

Run receipts, phase traces, forbidden-transition negatives, contradiction ledger, sensitivity
matrix, metamorphic results, invariant candidates, ratification packet. Evidence receipts
must be machine-readable and human-readable (Book §37, Master Prompt §13).

---

## 3. Documents under test — clause map to scenarios

| Scenario | Primary clauses under test |
|---|---|
| S01 Old Theory Dies Slowly | A-009 §5/§6/§8; A-010 §3/§4.1/§4.3/§4.5/§6/§7/§8; Book §7 |
| S02 False Revolution | A-010 §4.3/§4.4/§6/§12/§13; A-009 §12; Book §8; T2/T3 |
| S03 Patch Maze | A-010 §7/§8; Book §9; T7/T9 |
| S04 Leaf Failure | A-010 §7 (narrowest scope); Book §10; T8 |
| S05 Two Non-Dominated Models | A-010 §16; Book §11; T15 |
| S06 Ten Correlated Agents Agree | A-010 §11; A-009 §14; Book §12; T4 |
| S07 Independent Weaker Agents | A-007 §5/§6 + PM-RM §6; A-010 §11; Book §13 |
| S08 Reflective Bypass | A-009 §13; A-010 §12; Book §14 |
| S09 Counter-Attractor False Alarm | A-010 §12; Book §15; T10 |
| S10 Dormant Knowledge Returns | A-009 §9/§10; Book §16; T17 |
| S11 Negative Knowledge Dogma | A-009 §10; A-004 §11; Book §17; T18 |
| S12 Institutional Hyperthymesia | A-009 §11; A-004 §4/§10; Book §18; T17 |
| S13 Total Runtime Replacement | A-007 §1–§4/§8/§10; A-010 §14; Book §19 |
| S14 Huge Fake Alpha | A-008 §5/§11; A-010 §4.1/§4.4/§18; Book §20; T21 |
| S15 New Alpha Family | A-009 §12/§17.3; A-010 §13/§18; A-008 + PM-RM §7; Book §21 |
| S16 CEREBUS Contradiction | A-008 §7; A-010 §18; Book §22; AMB-09 |
| S17 Crypto Provider Disagreement | A-010 §19; A-009 §18; Book §23; AMB-10 |
| S18 Sensor Gap / DATA_BLOCKED | A-009 §10; A-010 §13/§19; Book §24 |
| S19 Crypto→FX Invalid Transfer | A-008 §8; A-009 §19.4; Book §25; T22 |
| S20 Governor Self-Threshold Change | A-010 §6/§9.9/§20/§21.12; Book §26; T6 |
| S21 Capable Worker Requests Authority | Constitution Article X/§9; A-007 §2.3; Book §27; T20 |
| S22 Operator Wants Unsupported Change | Constitution Article I/§9; A-010 §10; Book §28 |
| S23 Operator Unavailable | A-010 §8/§14; Book §29; T14 |
| S24 Unknown Governance Failure | A-010 §20/§21; A010-RT T24; Book §30 |

---

## 4. Canonical state machines — inventory (AMB-01/AMB-07)

The suite must distinguish these machines. They are **not** one machine.

| # | Machine | Source | States | Owns |
|---|---|---|---|---|
| M1 | Capability truth-label ladder | Constitution Article II | IDEA → SPECIFIED → SCAFFOLDED → IMPLEMENTED_UNVERIFIED → VERIFIED_ISOLATED → VERIFIED_INTEGRATED → VERIFIED_E2E → OPERATIONALLY_PROVEN; QUARANTINED; FALSIFIED; DEPRECATED | Components and capabilities |
| M2 | General system lifecycle | Constitution §11.1 | Intent → Specification → Bounded build → Verification → E2E proof → Release decision → Observed operation → Learning/governed change | Products and builds |
| M3 | Atlas planning status | Atlas §1.3 | MAPPED → ARTICULATING → READY_FOR_REVIEW → RATIFIED → BUILDING → VERIFYING → GATED_COMPLETE; BLOCKED; QUARANTINED; SUPERSEDED | Program units |
| M4 | A-009 knowledge lifecycle | A-009 §9 | OBSERVED, CANDIDATE, TESTED, PROMOTED, ACTIVE, CHALLENGED, REVALIDATED, DEMOTED, DORMANT, REACTIVATED, SUPERSEDED | Knowledge objects |
| M5 | A-010 Governor phase machine | A-010 §3 (+ Book §5 terminal states) | STABLE → WATCH → ESCALATION_REVIEW → HOMEOSTATIC_REPAIR / TRANSFORMATION_CANDIDATE → TRANSFORMATION_WINDOW → RECONSOLIDATION → NEW_STABLE / ROLLBACK / NO_CHANGE; holding/terminal: UNRESOLVED, PLURAL_MODEL_STATE, OPERATOR_HOLD, DATA_BLOCKED, AUTHORITY_BLOCKED | Institutional phase |
| M6 | A-008 strategy promotion ladder | A-008 §12 | SOURCE_CANDIDATE → HYPOTHESIS → CRITIQUED → EXPERIMENT_REGISTERED → FALSIFICATION_PASSED → VALIDATED_RESEARCH → PORTFOLIO_REVIEWED → SHADOW_CANDIDATE (B9 owns paper/shadow/live) | Strategies |
| M7 | A-004 practice promotion ladder | A-004 §10 | Observation → LessonCandidate → PracticePattern → Skill/Template/Test/Policy/Capability update | Practices |
| M8 | Quant research-to-capital lifecycle | Constitution §11.3 | idea → strategy spec → fast falsification → genuine engine backtest → holdout → walk-forward → cost/slippage stress → paper → shadow → proposal → live (explicit approval only) | Quant research |

**G1 decision required (recorded as AMB-01/AMB-07):** M4 and M5 are the two machines the
Governor drives, but M1 also binds every capability the scenarios touch. The harness must
implement M5 (phase) and M4 (knowledge) as separate engines with an explicit transition
mapping, and must not let scenario terminal states (which the Catalog expresses in M4/M6
vocabulary, e.g. `REJECTED/NEGATIVE_KNOWLEDGE` for S14) be misread as M5 phase states.

---

## 5. Knowledge lifecycle states (M4) and transition gaps

A-009 §9 states (flat list): OBSERVED, CANDIDATE, TESTED, PROMOTED, ACTIVE, CHALLENGED,
REVALIDATED, DEMOTED, DORMANT, REACTIVATED, SUPERSEDED.

Active/Dormant/Archival semantics (A-009 §9; LL-ARCH-1.1 §10.1):
- **ACTIVE** — included in ordinary agent projections when relevant.
- **DORMANT** — retained, excluded from default context until reopen conditions detected.
- **ARCHIVAL** — retrievable history, does not influence ordinary cognition by default.

Reopen conditions (A-009 §10): every demoted or negative-knowledge record defines what could
legitimately cause reconsideration; a rejection without reopen conditions is presumed too
coarse for automation.

**G1 decision required (AMB-06):** the legal transition edges of M4 are not specified
anywhere. Examples the Book implies but A-009 does not define: DORMANT→CANDIDATE/CHALLENGED
on reopen (Book S10) vs `REACTIVATED` as a state (A-009 §9); DEMOTED→DORMANT;
CHALLENGED→REVALIDATED vs CHALLENGED→DEMOTED. The harness must ship a default legal-edge
table for M4, overrideable per-scenario via the scenario spec, and `forbidden_transitions.json`.

---

## 6. Proposed evidence-object contracts (Book §4; A-004 §17; PM-RM §9)

Canonical objects the harness must model (logical objects; JSON fixtures acceptable):

- `EvidenceRecord`
- `ContradictionRecord`
- `EvidenceGap`
- `UnresolvedPatternRecord` (incl. `UNRESOLVED_PATTERN` state, anomaly quarantine)
- `NegativeKnowledgeRecord` (scope, evidence, reopen conditions)
- `PatchPressureRecord`
- `IndependenceRecord` / `IndependenceBudget`
- `AffectedSurface`
- `ConstraintField` (A-005 §2.1 + PM-RM §4)
- `PhaseDecisionRecord`
- `TransformationWindowSpec` (A-010 §15)
- `EpochManifest` (A-010 §14)
- `OutcomePacket` (A-004 §6)
- `ResumeCapsule` (A-004 §7 / A-005 §2.4)
- `StressScenarioSpec` (Book §3, incl. `hidden_ground_truth` sealed from decision roles)
- `UnresolvedGovernanceEvent` (A010-RT T24, Book S30) — for S24

Additional objects from amendments that the harness may need for authority-state checks:
`CapabilityGrant`, `AgentCockpit` (projection), `CapabilityGraph` node, `WorkGraph` node,
`SearchDemand` (A-006 §2), `EpistemicTensionRecord` (A-009 §5), `InstitutionalAttractorRecord`
(A-009 §4), `KnowledgeActivationState` (PM-RM §9), `CognitiveIndependenceRequirement` (PM-RM §9).

---

## 7. Transformation Governor roles (A-010 §10 / A-009 §7)

| Role | Duty | Independence note |
|---|---|---|
| Sentinel | Detects tension/anomalies/patch pressure/drift; must not propose preferred architecture during first-pass detection | First-pass independence |
| Steward | Defends incumbent using original + current evidence | Exposes its own losing conditions (T11) |
| Challenger | Builds strongest evidence-backed case against incumbent | Measured by discriminatory value, not by causing change (T10) |
| Explorer | Produces alternatives incl. ontology-expanding options | — |
| Auditor | Designs/runs discriminating evidence; shielded from Integrator's preferred answer | Staged reveal / preregistration (T13) |
| Integrator | Smallest reconstruction supported by evidence; cannot create evidence | — |
| Governor | Evaluates phase-transition admissibility + authority state; does not invent theory | Deterministic service where possible |
| Operator / Authorized Gate | Ratifies constitutional / high-AffectedSurface / capital / irreversible transitions | S22/S23 |

Epistemic sovereignty firewall (A-010 §17): no adaptive reasoner may simultaneously define
the anomaly, choose its own evaluation rule, alter that rule, certify the new rule, and grant
itself expanded authority.

---

## 8. Scope ladder (A-010 §7)

```
L0 RESULT / OBSERVATION
L1 IMPLEMENTATION
L2 CAPABILITY / PROCEDURE
L3 METHOD / VALIDATION RULE
L4 MECHANISM / DOMAIN MODEL
L5 ONTOLOGY / DOMAIN ARCHITECTURE
L6 INSTITUTIONAL ARCHITECTURE
L7 AUTHORITY / CONSTITUTION
```

Rules: narrowest plausible level; escalation follows evidence not frustration; repeated
L0/L1 repairs with same causal signature may promote upward (PatchPressure); a high-level
contradiction does not invalidate all lower-level evidence.

---

## 9. Hard authority boundaries (never crossed by any scenario)

From Constitution (Articles I, III, IV, V, VIII, X, XI, XII, XIX; §2.3; §9; §11.3; Book §40;
A-003):

1. No scenario mutates production infrastructure, cloud, capital systems, or live venues.
   (A-003: cloud `DEFERRED_BY_OPERATOR`; Book §40: no live trading / broker / capital /
   production cloud mutation / external crawling beyond authorized tests.)
2. No scenario grants, expands, or self-grants authority. Authority changes must equal
   `NONE` (Master Prompt §13). Capability ≠ authority (S21).
3. Operator preference cannot fabricate evidence status (S22); operator may authorize
   actions, not rewrite the EvidenceGraph.
4. No agent self-ratifies changes to its own evaluation standard or authority (A-010 §9.9,
   S20, S21).
5. Research autonomy never implies execution/capital autonomy (Constitution §2.3/§9;
   A-008 §10/§15; Book §1 rule 13).
6. Deterministic truth stays outside the LLM (Constitution Article V): kernels, state
   machines, permissions, calculations are deterministic code with tests.
7. Correlated agents are not independent confirmation (Book §1 rule 5; A-010 §4.3/§11).
8. No direct path from ordinary anomaly to architecture mutation (A-010 §3).
9. Secrets/credentials never enter fixtures, receipts, or reports.
10. The harness itself must not silently amend A-009/A-010 or the Book. Contradictions are
    recorded; smallest candidate amendments are proposed for operator review only (Book §38).

---

## 10. Domain boundaries

### Quant (A-008; Constitution §7.9; Book Book IV)
- Five knowledge spaces: Observation, Mechanism, Strategy, Execution, Evidence. Strategy
  Space may never become the only or dominant representation.
- Research Genome atoms with provenance/promotion state; whole strategies are immutable
  compositions.
- Promotion ladder M6; B7 deterministic validation is the certification substrate; profit
  does not reduce validation requirements (S14; T21).
- Quant Watch generates research demand from drift/decay/regime/unexplained residuals (S15).

### Crypto (A-009 §18; A-010 §19; LL-ARCH-1.1 §19.4)
- Crypto OS is a specialized Quant domain under OCE, not a parallel sovereign intelligence.
- Provider-native semantics survive normalization; nulls survive; global/local fields are
  not collapsed; research halts at observational resolution limits; future sensors create
  legitimate reopen conditions.
- Provider disagreement challenges source/normalization layers before field ontology (S17).
- Sensor insufficiency escalates to SearchDemand rather than model patching (S18).
- Domain-transfer requires explicit invariant mapping and independent validation (S19; T22).

### CEREBUS / manual (A-008 §7; A-010 §18; PM-RM §15)
- CEREBUS is a high-authority operator-provided doctrine source for FX logic; manual claims
  remain distinguishable from reproduced empirical findings.
- Structural invalidation, checkpoint logic, constraint-first reasoning, state-dependent
  action are reusable institutional principles; empirical CEREBUS trading claims remain
  domain-specific and manual-first.
- A reproduced contradiction does NOT silently rewrite the manual: it opens an
  amendment/evidence-review pathway (S16). Operator required for doctrine amendment.

---

## 11. Dependency graph (conceptual)

```
COMPLETED AUTHORITY
  OCE Constitution 1.1 (incl. A-001) ────────────────┐
  A-003 (ratified, local-first) ─────────────────────┤
  Master Program Atlas 1.0 (B0 gated complete) ──────┤
  B1 Local Ground / B2 contracts / B3 Worker Fabric  │  (evidence lineage)
          │                                          │
          v                                          │
PROPOSED ARCHITECTURE (under test)
  LARGER_LAB_INSTITUTIONAL_ARCHITECTURE v1.1 ────────┤
  A-004 → A-005 → A-006 → A-007 → A-008 ─────────────┤  (PM-RM records revisions)
          │                                          │
          v                                          │
  A-009  Cybernetic evolution / epochs / lifecycle ──┤  (governs A-004..A-008 evolution)
          │                                          │
          v                                          │
  A-010  Transformation Governor / phase control ────┤  (controls A-009 epochs)
          │                                          │
          v                                          │
TEST HARNESS (G1, generic only)
  phase machine M5 + knowledge lifecycle M4 + evidence objects + authority checks
          │                                          │
          v                                          │
SCENARIOS S01–S24 (fixtures; Class A deterministic / Class B ecology / Class C domain)
          │                                          │
          v                                          v
TEST EVIDENCE  ──────────────►  future ratification evidence (G10 packet)
```

Separation of duties (Book §6, Master Prompt §15): COMPLETED AUTHORITY (2.1) /
PROPOSED ARCHITECTURE (2.2) / TEST HARNESS (2.3) / TEST EVIDENCE (2.4) are never blended.

---

## 12. Known conflicts among amendments (CON register)

| ID | Parties | Conflict | Resolution status | Impact |
|---|---|---|---|---|
| CON-01 | A-002 §7 vs A-007 §7 / Impact Atlas §3 | A-002 treats Hermes as replacing OpenClaw in the supplemental role; A-007 defines CompanionRuntime (Hermes candidate) + WorkerRuntime (OpenClaw eligible). A-002 v1.0 §7 unamended. | Resolution direction recorded in Impact Atlas §3 and A-007 §7; A-002 revision pending ratification | S13 (runtime replacement), S07 (runtime diversity). Fixtures must follow A-007 semantics. |
| CON-02 | A-009 §16 vs A-010 §2 | A-009: PO "regulates ... stabilize/transform posture"; A-010: no single agent (PO-only switch) may control the stabilize/transform decision — Governor does. A-010 never explicitly carves out A-009 §16. | A-010 is the operative control; A-009 §16 needs a clarifying carve-out (smallest candidate amendment: PO regulates the *inputs* — attention, topology, information flow — Governor owns the *decision*) | S08 (reflective bypass), S20. Harness must not let PO short-circuit the Governor. Open red-team question PM-RM §18 Q9. |
| CON-03 | A-010 §6 vs A010-RT T5 | Thresholds "preregistered or operator-approved where practical" vs "some thresholds/review routing may remain non-agent-visible". Preregistered = Goodhartable; hidden = unpreregistered. | Unresolved design tension | S20, G7 sensitivity. Needs operator decision on transparency policy before G2. |
| CON-04 | A-004 §10 vs A-009 §9/§11 | A-004 promotion ladder (Observation→…→Capability update) has no DEMOTED/DORMANT/PRUNE legs; A-009 requires full epistemic metabolism. | PM-RM §3 records required revision; A-004 v1.0 not amended | S10/S11/S12; G4. |
| CON-05 | A-005 v1.0 vs A-009 (PM-RM §4) | A-005's framing risks static "canonical truth"; A-009 defines truth as strongest currently defensible state with confidence/lineage/expiry/challenge. | PM-RM §4 records required revision | S10/S11/S12; G4. |
| CON-06 | A-006 §2 vs A-009 §12/§13 (PM-RM §5) | A-006 v1.0 search demand originates from known institutional state (gap-driven only); anomaly-driven discovery (unknown questions) is absent. | PM-RM §5 records required revision | S15, S18; G5. |
| CON-07 | A-007 §5/§6 vs PM-RM §6 / S06–S07 | A-007 routing ranks by reliability/cost/latency only; no error-correlation/independence criteria → converges to monoculture. | PM-RM §6 records required revision | S06/S07; G3. |
| CON-08 | A-008 v1.0 vs A-009 §17.3 / A-010 §18 (PM-RM §7) | A-008's five knowledge spaces + Research Genome lack an UNRESOLVED_PATTERN quant state; genome can become ontology prison. | PM-RM §7 records required revision | S15; G5. |
| CON-09 | Book §5 vs A-010 §3 | Book §5 "illegal examples" mixes phase transitions (STABLE→NEW_STABLE) with knowledge/evidence-category errors (UNRESOLVED_PATTERN→promoted ontology; agent confidence→independent confirmation); Book adds terminal states not in A-010's graph (UNRESOLVED, PLURAL_MODEL_STATE, OPERATOR_HOLD, DATA_BLOCKED, AUTHORITY_BLOCKED). | Not a contradiction; a spec-ambiguity — see AMB-01 | Every scenario trace; G1/G2. |

CON-01..CON-08 are **proposed-vs-proposed** conflicts (no ratified authority is
contradicted). CON-02 and CON-03 are the only *open* tensions requiring architecture-side
clarification; CON-04..08 are documented revision obligations whose resolution direction
already exists in the Post-Michels matrix. AMB-02 governs how they are treated during
execution.

---

## 13. Architectural ambiguities (AMB register)

| ID | Ambiguity | Could change outcome of | Needed decision |
|---|---|---|---|
| AMB-01 | Phase machine (M5) vs knowledge lifecycle (M4): one trace, two machines. Book §5 illegal examples mix them; Catalog S14 terminal state is M4 vocabulary; holding states (OPERATOR_HOLD, DATA_BLOCKED, PLURAL_MODEL_STATE, UNRESOLVED, AUTHORITY_BLOCKED) not in A-010 §3 graph. | All scenarios; trace validation (Book §10 assertion 2) | Harness defines two engines + mapping; scenario specs declare which machine each assertion targets. |
| AMB-02 | Which amendment versions are under test: A-004..A-008 v1.0 as written, or as revised per PM-RM (itself proposed)? | G2–G5 pass/fail meaning | Recorded assumption §14; operator may override. Recommendation: test v1.0 texts; PM-RM is the documented revision obligation; failures that implicate unamended v1.0 clauses are evidence for PM-RM, not bugs. |
| AMB-03 | Independence has dimensions (A-010 §11) and a qualitative target (Book S06: "≈1 evidence lineage") but no operational aggregation function. | S06/S07, G3, G8 | Harness provides IndependenceRecord primitive + accounting; aggregation policy is fixture/spec-level, preregistered per scenario. |
| AMB-04 | S14 (data-quality failure) vs S15 (genuine anomaly): "survives data-quality checks" is the discriminator (A-010 §4.4) but the decision procedure is undefined. | S14/S15, G5 | Fixtures must freeze the check list + pass/fail semantics (PIT, execution realism, cost sensitivity, family multiplicity, OOS/WF, mechanism plausibility — Book §20). |
| AMB-05 | Threshold preregistration mechanics: A-010 §6 "preregistered or operator-approved ... where practical" — no schema for the frozen evaluation contract at window opening. | S20, G6, G7 | G1 adds frozen-evaluation-contract object; window-opening snapshot semantics. |
| AMB-06 | M4 legal transition edges unspecified (DORMANT→CANDIDATE vs REACTIVATED state; DEMOTED→DORMANT; CHALLENGED→REVALIDATED/DEMOTED). | S10/S11, G4, G8 | G1 default edge table + per-scenario overrides; forbidden transitions must include M4 illegal edges. |
| AMB-07 | Constitution Article II labels (M1) vs A-009 lifecycle (M4): two status vocabularies, no mapping (FALSIFIED↔DEMOTED? QUARANTINED↔DORMANT?), no per-class ownership rule. | G4, G8, invariant extraction (G9) | G1 defines object-class → machine ownership; receipts record which machine asserted. |
| AMB-08 | "Reversible low-scope transformation remains autonomous within grants" (A-010 §8; T14 defense) is unquantified. | S23, G6, G7 | Scenario specs must pin the reversible/medium-scope boundary; Governor exposes the classification. |
| AMB-09 | CEREBUS manual has no machine-readable representation on this branch; "exact defined conditions" (Book S16) cannot be canonical yet. Only `quant-lab/research/CEREBUS_STRATEGY_ANALYSIS.md` (analysis, 857 lines) exists. | S16, G5 | Operator decision or doctrine-ingestion contract; fixtures may carry a synthetic-but-labeled manual-claim object. |
| AMB-10 | Crypto doctrine/artifacts (MECH21/LF14, provider semantics, Sensor Fabric philosophy) referenced by A-009 §18/A-010 §19 live on sibling branches (`agent/crypto-quant-foundry`, `agent/crypto-sensor-fabric-build`), not on this branch. | S17–S19, G5 | Read-only doctrine extraction from sibling branches is authorized for fixture grounding (no merge); operator confirmation requested. |
| AMB-11 | Causal-signature clustering for PatchPressure (A-010 §8; T7 defense: "repeated causal signature") has no similarity definition. | S03, G2, G8 | PatchPressureRecord schema defines signature fields; clustering policy is spec-level, but the field must exist in G1. |
| AMB-12 | EpochManifest (A-010 §14) lists fields but "reconstruction" has no operational checklist (which graphs must rehydrate). | S13, G4 | G4 defines a reconstruction checklist; S13 asserts it. |

---

## 14. Assumptions the Stress Suite depends on

1. A-009 and A-010 are the operative control doctrine under test; the Book/Catalog/Gates are
   the test specification; the Constitution's ratified articles bind the harness (no
   authority expansion, deny-by-default, evidence-bounded truth, deterministic kernels).
2. Amendment versions under test are the v1.0 texts as written; the Post-Michels matrix is a
   documented revision obligation, not silently applied (AMB-02).
3. M5 and M4 are implementable as deterministic engines driven by fixtures; no live model
   calls are required for Class A; Class B may use synthetic/mock outputs; Class C uses
   doctrine-grounded synthetic fixtures (Book §39).
4. All scenarios run in simulation: no live capital, brokers, exchanges, production cloud,
   or production mutation (Book §40; A-003; Master Prompt §10). Cloud cost target $0.
5. Hidden ground truth is sealed from decision roles via the harness's sealed-field
   mechanism (Book §3).
6. Independence is modeled explicitly (overlap dimensions recorded); raw vote count and
   effective independence are kept separate (Master Prompt §11).
7. A failing scenario is a successful research result; the harness preserves failing traces
   and never patches the architecture to go green (Master Prompt §12; Book §38).
8. Operator behavior in S22/S23 is modeled as an authority actor (can authorize actions,
   cannot fabricate evidence); no operator automation is assumed to exist.
9. CEREBUS manual claims and Crypto doctrine can be represented as labeled fixture doctrine
   for G5 (AMB-09/AMB-10), pending operator confirmation.
10. Epoch/phase state is fully reconstructable from canonical artifacts (EpochManifest,
    canonical graphs, ResumeCapsules) without runtime-native memory (S13).

---

## 15. Reusable existing repository components

| Component | Location | Reuse |
|---|---|---|
| B2-era canonical contract schemas | `infrastructure/control-plane/contracts/` (agent-identity, capability-grant, event-envelope, evidence-manifest, job-envelope, worker-identity, worker-capability-manifest, artifact-ref, denial-envelope, schema-registry) | Schema-governance patterns; event-envelope as audit wrapper for PhaseDecisionRecords; capability-grant/denial-envelope for authority-state checks (S20/S21/S23) |
| B3 production contract | `infrastructure/control-plane/contracts/b3-production-contract.json` | Authority/evidence discipline reference (fail-closed, no self-authorization, immutable audit) |
| B3 migrations | `infrastructure/control-plane/migrations/0001–0005` | Durable-state conventions (PostgreSQL authoritative) if harness persistence is added later |
| B3 adversarial test patterns | `infrastructure/control-plane/tests/test_b3_adversarial*.py`, `test_b3_end_to_end_jobs.py`, `test_b3_worker_fabric_store_integration.py` | Test conventions: fail-closed, independent gate, manifest re-verification, truthful skip |
| B3 evidence record + run structure | `infrastructure/control-plane/B3-EVIDENCE-RECORD.md`, `evidence/runs/<run_id>/` | Receipt format precedent (superseded-run honesty, independent gate, cost/mutation counters) |
| B1-I2 contracts | `infrastructure/cloud-ground/contracts/b1-i2-clean-host*.json` | Validation fixture patterns |
| CEREBUS analysis | `quant-lab/research/CEREBUS_STRATEGY_ANALYSIS.md` | Doctrine grounding for S16 fixture construction |
| pytest conventions | `pyproject.toml [tool.pytest.ini_options]`; `tests/` | Test layout + run command |

## 16. Proposed new implementation surfaces (G1+; NOT built in G0)

```
stress-suite/
  planning/            <- G0 (this packet + adversarial review + receipt)
  schemas/             <- G1: JSON Schemas for evidence objects, StressScenarioSpec,
                           phase graph M5, knowledge lifecycle graph M4,
                           forbidden transitions, frozen evaluation contract
  engine/              <- G1: phase-state engine, lifecycle engine, transition validators
                           (legal + forbidden), fixture loader, authority-state checks,
                           sealed-ground-truth handling, deterministic replay
  scenarios/           <- G2+: S01–S24 specs (scenario.yaml/json + expected_phase_trace +
                           forbidden_transitions + stimulus_events.jsonl)
  fixtures/            <- G2+: initial epoch/state/authority/knowledge fixtures + synthetic
                           domain fixtures (CEREBUS, crypto providers, quant experiments)
  tests/               <- G1+: pytest suite (legal transitions, illegal transitions,
                           lifecycle, authority non-escalation, replay)
  evidence/            <- run receipts (machine + human readable)
  reports/             <- final deliverables: executive result, contradiction ledger,
                           phase coverage, independence audit, invariant candidates,
                           architecture change requests, ratification packet
```

Constraint: no scenario-specific hacks inside `engine/`; scenario logic lives in
`scenarios/` + `fixtures/` (STRESS-GATES G1).

## 17. Parts that MUST remain simulation-only

- All S01–S24 stimulus/ground-truth fixtures (synthetic or archived evidence).
- CEREBUS manual claims in fixtures (labeled; not the real manual unless operator provides a
  canonical representation — AMB-09).
- Crypto provider/sensor fixtures (S17–S19) — doctrine-grounded synthetic data, no live
  provider contact.
- Runtime topologies: mocks / certified mocks; no real Hermes/OpenClaw/Pi activation.
- Any "transformation window" execution: sandboxed simulation only (Book §40).
- No broker/exchange connection, no capital allocation, no production cloud mutation, no
  external crawling beyond separately authorized discovery tests, no secret/credential use.

---

## 18. Stop-condition check results (Master Prompt §5; STRESS-GATES §5)

| Stop condition | Result |
|---|---|
| Direct contradiction with existing constitutional authority | **NOT FOUND.** CON-01..08 are proposed-vs-proposed. Constitution Article I (operator sovereignty) and Article II (truth labels) are compatible with S22/S24 handling. |
| A-009 and A-010 require mutually incompatible behavior | **NOT FOUND as incompatibility.** A-010 is explicitly the control mechanism for A-009's open problem (A-010 §2). Internal tension CON-02 (PO posture vs Governor decision) is recorded, not fatal. |
| Two stress scenarios require incompatible institutional rules | **NOT FOUND.** S05 vs S16, S22 vs S23, S14 vs S15 all distinguish on recorded dimensions (plurality, authority-vs-evidence, data-quality-vs-anomaly). No scenario pair found that demands opposite rules for identical evidence. G8 will re-audit empirically. |
| Stress book assumes an already-built capability | **NOT FOUND.** Book explicitly requires harness construction (Stage 0) and gates G1–G10; it assumes the architecture documents exist (they do) and that fixtures can be synthetic (authorized). |
| Domain truth necessary for a scenario missing | **PARTIAL — AMB-09/AMB-10.** CEREBUS manual and Crypto MECH/LF domain materials are not canonically represented on this branch. Synthetic-labeled fixtures are authorized by the Book; operator confirmation requested. Does not block G0/G1. |
| Implementation would require production/live/capital mutation | **NOT FOUND.** All execution is simulation; cloud cost target $0; Book §40 prohibitions hold. |
| Authoritative current OCE lineage differs materially from planning assumptions | **NOT FOUND.** Planning branch head `7105347f` is a descendant of `origin/oce` head (`d3df9eb4` = B1-L8R4). Base verified; no divergence. (Local shared checkout `oce` at `64f7c754` is a different, older local line — irrelevant to this branch.) |
| Branch ancestry wrong | **NOT FOUND.** `agent/oce-institutional-stress-suite-build` created from `origin/agent/oce-agent-ergonomics-amendment` head `7105347f`; ancestry verified. |
| Completing the test honestly requires modifying the architecture before testing | **NOT FOUND.** The suite is designed to test the proposed architecture as written; CON-02/CON-03 ambiguities are testable as-is and their outcomes are evidence. |

Result: **no stop condition triggers. G0 proceeds to PASS with recorded CON/AMB registers.**

---

## 19. Adversarial review summary

The 17 adversarial questions of Master Prompt §4 are answered honestly (not optimistically)
in `G0_ADVERSARIAL_REVIEW.md`. Headline findings:

- **Canonical truth static?** Yes, in A-005 v1.0 (CON-05); A-009 corrects. Suite tests A-009 semantics.
- **Epistemic sovereignty risk?** Real, via two paths: PO controlling stabilize/transform inputs (CON-02, PM-RM Q9) and Governor-channel Goodharting (CON-03/T5). S08/S20/S21 exercise both.
- **NegativeKnowledge dogma risk?** Real (T17/T18); S11 + reopen-condition review are the tests.
- **Volume-forces-transformation risk?** Real (T3 anomaly spam); A-010 §4.4 requires anomaly credibility/clustering independent of raw count — the distinguishing procedure is AMB-04/AMB-11, must be frozen in fixtures.
- **Runtime independence overstated?** Yes (T4); S06/S07 + IndependenceRecord.
- **Scenario assumes its own property?** Not found among the 24; closest risk is S06/S07 requiring the independence model they test — resolved by modeling independence from overlap dimensions rather than assuming it.
- **Stable-epoch incumbent bias / window novelty bias?** Both real (T1/T2/T16); S01/S02 and EpochManifest challenge conditions are the tests.
- **Operator authority vs evidence status?** Cleanly separated in S22; Constitution supports.
- **CEREBUS contradiction without silent override?** Yes via S16 contract (MANUAL_PRESERVED + CONTRADICTION_OPEN / AMENDED / REPRODUCTION_REJECTED); representation gap is AMB-09.
- **Crypto sensor disagreement contained at provider layer?** Yes via S17 challenge sequence; doctrine grounding gap is AMB-10.
- **Research autonomy → capital autonomy?** Prohibited explicitly; S14/T21/S21 enforce.
- **Dormant/archive erasure?** S10/S12 + T17; archival retention is mandatory.
- **Novel governance failure without forced classification?** S24 UNRESOLVED_GOVERNANCE_EVENT + safe hold.

Full per-question analysis: `G0_ADVERSARIAL_REVIEW.md`.

---

## 20. G0 evidence receipt (human-readable)

```
gate_id:                 G0
milestone_id:            STRESS-G0
status:                  PASS_G0_PLANNING_INGESTION
branch:                  agent/oce-institutional-stress-suite-build
base_sha:                7105347f6e8e4807cca2d8d450baa149b5fa0aeb
starting_sha:            7105347f6e8e4807cca2d8d450baa149b5fa0aeb
commits:                 see git log (STRESS-G0: ...)
scenario_ids:            none executed (G0 is planning-only)
tests_run:               0
pass_count:              0
fail_count:              0
known_gaps:              AMB-09 (CEREBUS canonical representation), AMB-10 (Crypto doctrine
                         extraction), AMB-02 (amendment version under test)
contradictions:          CON-01..CON-09 (register in §12; CON-02, CON-03 open; CON-04..08
                         documented revision obligations; CON-01, CON-09 spec-level)
phase_transition_coverage: n/a (harness not built; M5 graph recorded in §4)
forbidden_transition_coverage: n/a (negative tests are G1 work; illegal classes recorded in §4/§5)
artifacts:               stress-suite/planning/G0_ARCHITECTURE_INGESTION.md,
                         stress-suite/planning/G0_ADVERSARIAL_REVIEW.md,
                         stress-suite/planning/G0_EVIDENCE_RECEIPT.json
cost:                    $0
cloud_mutations:         0
production_mutations:    0
capital_mutations:       0
authority_changes:       NONE
next_gate:               G1 (HARNESS_CONTRACTS) — requires operator authorization
```

---

## 21. Recommended next action

**AUTHORIZE_G1** — with the following recorded conditions carried into G1:

1. G1 builds only generic harness machinery (schemas, phase engine M5, lifecycle engine M4,
   fixture loader, legal/forbidden transition validators, authority-state checks,
   deterministic replay, sealed ground truth) — no scenario hacks in the engine.
2. G1 schemas incorporate the G1-decision items of AMB-01/05/06/07/11 (two-machine mapping,
   frozen evaluation contract, M4 edge table, object-class machine ownership,
   PatchPressureRecord signature fields).
3. Contradictions CON-02 and CON-03 remain open; G1/G2 must not silently resolve them —
   scenario outcomes involving them are evidence, and the smallest candidate amendments
   (A-009 §16 carve-out; threshold transparency policy) are proposed to the operator only
   after testing, per Book §38.
4. No mutation of production, cloud, capital, or ratified evidence (B3 record untouched).
5. Domain fixtures for G5 require operator confirmation on AMB-09/AMB-10 (CEREBUS
   representation; read-only Crypto doctrine extraction).

If the operator prefers to resolve CON-02/CON-03 before building, the alternative is
`ARCHITECTURE_REVIEW_REQUIRED` before G1.

---

*End of G0 architecture ingestion packet. This document records, it does not authorize
implementation.*
