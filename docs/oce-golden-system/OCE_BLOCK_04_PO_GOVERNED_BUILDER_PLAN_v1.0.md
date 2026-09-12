# OCE Golden System
## Block 4 — PO Governed Builder Planning Dossier

**Document ID:** OCE-B4-PLAN-001  
**Version:** 1.0  
**Status:** READY_FOR_OPERATOR_REVIEW — BUILD LOCKED  
**Dependencies:** B3 constitutional spine; Amendment A-002  
**Exit gate:** PO completes a bounded build with authority, context, worker, evidence, restart, and learning proof

## 1. Block contract

Block 4 makes PO the high-level OCE/Quant/Larger Lab operator. PO reasons and delegates through OCE; it is not canonical truth and not a personal assistant. Hermes remains separate and may only send bounded referrals. This block proves a domain-neutral build workflow without building the reference application itself.

## 2. Chapter 1 — Intent and Reasoning

| Section | Contract | Deliverables | Evidence/gate |
|---|---|---|---|
| B4.C1.S1 Goal interpretation | Convert operator input into objective, outcomes, constraints, risk, unknowns and authority need without silently adding scope. | IntentContract builder and review view | Ambiguity/contradiction generates clarification; exact operator corrections version intent. |
| B4.C1.S2 Facts/assumptions | Separate verified facts, operator assertions, model inference, hypotheses and unknowns with provenance/expiry. | claim ledger and grounding resolver | Inference cannot masquerade as fact; stale facts demote. |
| B4.C1.S3 Decomposition | Produce dependency graph, critical path, parallel groups, deterministic-service preference, budgets and stop conditions. | PlanContract and graph validator | Cycles, unreachable steps, missing dependencies and hidden scope rejected. |
| B4.C1.S4 Alternatives | Generate bounded alternatives, tradeoffs, reversibility, evidence needs and chosen rationale for material decisions. | decision candidate set and ADR proposal | Choice cites constraints/evidence; uncertainty remains visible. |
| B4.C1.S5 Plan contract | Freeze versioned plan, tasks, gates, approvals, budgets, expected artifacts, failure policy and completion definition. | canonical Plan/Task schemas and compiler | Agent cannot execute unratified or incompatible plan. |

## 3. Chapter 2 — Memory and Context

| Section | Contract | Deliverables | Evidence/gate |
|---|---|---|---|
| B4.C2.S1 Constitutional retrieval | Assemble applicable constitution, amendment, plan, grants and policies with exact versions before reasoning. | policy context assembler | Missing/contradictory authority blocks execution. |
| B4.C2.S2 Project state | Retrieve canonical project/object summaries, active decisions, blockers and evidence instead of relying on chat memory. | project context projection | Restarted PO reconstructs same active state from OCE. |
| B4.C2.S3 Episodic traces | Retain bounded action/decision episodes with provenance and disposition; exclude raw misc chatter. | episode schema, TTL and promotion pipeline | PO context budget resists irrelevant-history pollution. |
| B4.C2.S4 Source grounding | Bind sources, quotations, datasets, versions, timestamps and confidence; preserve contradiction and copyright limits. | SourcePack and citation validator | Unsupported claims are UNKNOWN/BLOCKED, not filled by model recall. |
| B4.C2.S5 Context handoff | Build minimum ContextBundle for PO workers and typed WorkReferral/OutcomePacket for Hermes boundary. | context policy and packet schemas | No raw PO/Hermes/worker transcript crosses boundary; anchors survive compaction. |

## 4. Chapter 3 — Governed Tools

| Section | Contract | Deliverables | Evidence/gate |
|---|---|---|---|
| B4.C3.S1 Tool registry | Register identity, owner, version, inputs, outputs, risk, side effects, prerequisites, cost and evidence. | signed capability manifest | Unregistered/version-drifted tools unavailable. |
| B4.C3.S2 Sandboxing | Select task-specific filesystem, network, process, credential and resource boundary with deny-by-default. | sandbox profiles and probes | Escape, cross-task and unauthorized-network tests denied. |
| B4.C3.S3 Mutation controls | Separate inspect/plan/dry-run/apply; require grant and exact target for writes. | mutation admission adapter | Wrong target, stale plan, broadened glob and missing approval fail closed. |
| B4.C3.S4 Side-effect verification | Observe actual filesystem/Git/service/message/cloud effect and reconcile to intended effect. | effect receipt and reconciler | Tool success text cannot prove effect; unexpected effect triggers incident. |
| B4.C3.S5 Rollback | Define preconditions, backups, inverse/compensating actions, limits and operator holds. | rollback contract and drills | Reversible classes restore; irreversible class cannot run without stronger gate. |

## 5. Chapter 4 — Worker Orchestration

| Section | Contract | Deliverables | Evidence/gate |
|---|---|---|---|
| B4.C4.S1 Worker identity | Give every subagent/service worker unique run identity, role, provider, version, parent and trace. | WorkerIdentity and admission registry | Anonymous/shared identity rejected. |
| B4.C4.S2 Task contracts | Issue minimum objective, refs, constraints, outputs, tests, budget, expiry and grant. | TaskContract compiler | Worker cannot access unlisted context or exceed scope. |
| B4.C4.S3 Delegation limits | Bound depth, fan-out, cost, concurrency, recursion and authority; prefer deterministic tools. | delegation policy and scheduler | Runaway spawning, circular delegation and inherited authority blocked. |
| B4.C4.S4 Result synthesis | Validate structured WorkerResults, evidence and conflicts; synthesize rather than concatenate. | reducer and OutcomeArtifact | Conflict/failed critical task cannot become success. |
| B4.C4.S5 Worker failure | Handle timeout, partial output, provider failure, bad evidence, cancellation and cleanup with bounded retry. | failure taxonomy and recovery state | No lost task, double effect or fabricated completion after crash. |

## 6. Chapter 5 — Learning PO

| Section | Contract | Deliverables | Evidence/gate |
|---|---|---|---|
| B4.C5.S1 Observation capture | Emit intent, environment, action, result, failure, correction and contradiction observations. | ObservationEnvelope and capture hooks | Useful failure evidence persists without secrets/raw noise. |
| B4.C5.S2 Error clustering | Group normalized errors by mechanism while preserving instances and avoiding premature causal claims. | cluster registry and review UI | Similar messages alone do not prove same cause. |
| B4.C5.S3 Lesson validation | Test lesson candidates against evidence, counterexamples, scope and expiration. | lesson evaluator | One success/failure cannot silently become doctrine. |
| B4.C5.S4 Practice retrieval | Retrieve only applicable validated patterns with version/confidence/counterexamples. | practice index and relevance tests | Stale/out-of-scope lesson cannot override current plan. |
| B4.C5.S5 Governed improvement | Propose prompt, tool, test, policy or architecture changes through evaluation and operator review. | ImprovementProposal lifecycle | PO cannot modify its own authority/evaluator in the same promotion run. |

## 7. Implementation increments

| Increment | Future scope | Gate |
|---|---|---|
| B4-I0 | Freeze PO identity, context, task, tool, worker and learning contracts | A-002 and B3 compatibility verified |
| B4-I1 | C1 intent/claims/decomposition | Ambiguity, provenance and graph tests pass |
| B4-I2 | C1 alternatives/plan plus C2 policy/project context | Restart reconstructs plan from OCE |
| B4-I3 | C2 episodic/source/handoff boundaries | PO/Hermes/worker context isolation proven |
| B4-I4 | C3 tool registry, sandbox and mutation admission | Unauthorized/escape/wrong-target denied |
| B4-I5 | C3 effect verification and rollback | Observed effects reconcile; recovery drills pass |
| B4-I6 | C4 identity/contracts/delegation | Scope, cost, recursion and authority bounds pass |
| B4-I7 | C4 synthesis/failure plus C5 learning integration | Complete bounded build and restart demonstration |
| B4-I8 | Independent adversarial evaluation of full PO workflow | No authority, memory, evidence or cleanup bypass |
| B4-I9 | Gate packet, learning ledger and B5 dependency contract | Operator-only completion |

## 8. Required demonstration

From a clean local environment, PO receives a bounded operator goal, clarifies it, creates a plan, obtains appropriate local-write authority, delegates at least two independent tasks, uses a deterministic tool, synthesizes evidence, survives interruption, resumes from OCE, verifies side effects, records lessons, and returns an operator-legible outcome. The demonstration must work without Hermes, cloud, deployment, messaging, broker access or capital.

## 9. Non-goals

No generic personal memory in PO; no second Hermes; no reference-product domain expansion; no production deployment; no autonomous architectural self-modification; no live Quant operation.
