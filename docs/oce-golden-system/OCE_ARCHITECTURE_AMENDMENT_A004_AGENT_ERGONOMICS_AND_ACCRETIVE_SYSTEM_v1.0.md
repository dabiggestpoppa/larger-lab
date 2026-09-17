# OCE Golden System
## Architecture Amendment A-004 — Agent Ergonomics and Accretive System

**Document ID:** OCE-A004-001  
**Version:** 1.0  
**Status:** PROPOSED — OPERATOR REVIEW REQUIRED  
**Applies to:** Blocks 0–10; PO; workers; Quant Lab/Watch; reusable platform surfaces  
**Does not authorize:** deployment, broker access, execution, capital, architecture self-modification, or autonomous promotion

## 1. Purpose

This amendment makes the OCE/PO/Quant system easier for an agent to understand correctly, operate economically, recover after interruption, and improve cumulatively without turning accumulated history into context pollution.

The target is not “more agent features.” The target is a coherent control system in which every agent-facing abstraction answers six questions cheaply and deterministically:

1. What is true now?
2. What am I allowed to do?
3. What matters for this task?
4. What is the cheapest trustworthy path to progress?
5. What evidence would prove or falsify completion?
6. What should survive this run for future work?

The permanent rule is:

> **canonical state outside the model; minimum sufficient context inside the model.**

Agents may reason richly, but they may not become the storage layer, authority layer, or final source of truth.

## 2. System model — a tower of linked abstractions

The system shall expose one linked control tower rather than many unrelated subsystems:

**L0 Constitutional Law**  
identity, sovereignty, authority, prohibited states, truth labels

**L1 World Truth**  
project/repository/data/service/environment state, versions, freshness, health, provenance

**L2 Capability Graph**  
what tools, workers, datasets, models, services and kernels exist; cost, risk, prerequisites, side effects and evidence quality

**L3 Work Graph**  
active goals, plans, dependencies, blockers, budgets, stop conditions and expected artifacts

**L4 Domain State**  
application-specific projections such as Quant market state, strategy state, experiment state and portfolio state

**L5 Evidence Graph**  
claims linked to runs, manifests, tests, source records, effects and independent verification

**L6 Practice Graph**  
validated reusable methods, failure signatures, repair recipes, templates and skills with scope/confidence/expiry

**L7 Operator Surface**  
one decision-oriented projection of exceptions, pending approvals, uncertainty, cost and leverage points

Every lower layer may reference higher-authority layers by stable identifiers and versions. No layer may silently duplicate another layer's canonical truth.

## 3. Agent Cockpit contract

Every PO or worker run begins from a machine-generated `AgentCockpit` snapshot. It is a projection, never a new source of truth.

Minimum fields:

- `run_identity`
- `goal_id` and `task_id`
- `authority_grant_ids`
- `canonical_state_refs`
- `dependency_status`
- `relevant_claims` with truth labels and freshness
- `capability_candidates` ranked by admissibility and expected cost
- `budget_remaining` for tokens/time/compute/network/mutations
- `risk_class`
- `expected_outputs`
- `required_evidence`
- `stop_conditions`
- `open_contradictions`
- `operator_decisions_required`
- `resume_token`

The cockpit MUST be reconstructible from OCE after process death. A model transcript is not required for reconstruction.

## 4. Progressive context disclosure

Context shall be loaded in tiers rather than dumping the program into every prompt.

**Tier 0 — control kernel:** goal, authority, invariants, current state, stop conditions. Always present.

**Tier 1 — task context:** exact contracts, dependencies, affected interfaces, recent evidence and relevant decisions.

**Tier 2 — supporting evidence:** source excerpts, historical incidents, prior experiments, code neighborhoods and counterexamples. Retrieved only when needed.

**Tier 3 — deep archive:** full transcripts, superseded planning, broad history and low-confidence observations. Never injected by default.

Every context item carries source, version, confidence, freshness/expiry and reason-for-inclusion. Context compaction must preserve stable IDs and unresolved contradictions rather than prose summaries alone.

## 5. Capability discovery and selection

OCE shall maintain a canonical `CapabilityGraph`, not a flat tool list.

Each capability node records:

- identity and version;
- semantic purpose;
- input/output contract;
- deterministic vs model-dependent behavior;
- authority/risk class;
- side effects;
- latency and cost profile;
- environment prerequisites;
- data/security boundary;
- expected evidence strength;
- failure modes;
- rollback/compensation support;
- known substitutes;
- composition constraints;
- success/failure history by task class.

PO must prefer the least expensive admissible capability path that can satisfy the required evidence. Deterministic services are preferred for deterministic work. Large-model reasoning is reserved for ambiguity, synthesis, critique and design where it adds value.

External repositories, tools and strategies enter through **capability extraction**, not wholesale adoption. The reusable unit is the capability or practice pattern, not the repository identity.

## 6. Work decomposition as contracts, not chat

Every non-trivial run is compiled into a typed work DAG. A task node records objective, dependencies, context refs, grant, budget, outputs, evidence, retry policy and termination criteria.

Agents should see only their task subgraph plus the minimum ancestor/consumer context necessary to avoid local optimization that breaks the system.

Workers return structured `OutcomePacket`s containing:

- disposition: PASS / FAIL / BLOCKED / PARTIAL / CANCELLED;
- produced artifacts and hashes;
- claims made;
- evidence refs;
- observed side effects;
- unresolved uncertainty;
- contradictions discovered;
- cost consumed;
- recommended next action;
- reusable lesson candidates.

PO synthesizes packets. It must not concatenate worker prose and call that synthesis.

## 7. Resume and handoff ergonomics

Every task checkpoint emits a `ResumeCapsule`:

- exact goal/task/plan versions;
- last verified state;
- completed nodes and evidence;
- remaining nodes;
- current blockers;
- pending operator decision;
- active leases/grants and expiry;
- cleanup obligations;
- next safe action.

A fresh agent must be able to resume from the capsule and canonical state without reading the full previous conversation.

Handoffs use stable object references rather than copied history. When a worker, PO, Hermes or future domain agent crosses a boundary, only an explicit packet crosses.

## 8. Evidence-first control loop

The standard loop becomes:

**OBSERVE → ORIENT → PLAN → SIMULATE → ACT → VERIFY EFFECT → REDUCE EVIDENCE → LEARN → CHECKPOINT**

`ACT` never directly implies success. A successful tool response is only an action observation. Completion requires independent effect/evidence reconciliation appropriate to risk.

Every run exposes an `EvidenceGap` list: the smallest missing observations preventing the desired truth promotion. Agents should optimize work toward closing evidence gaps rather than maximizing activity.

## 9. Resource economy

Every plan and task carries explicit budgets for:

- model tokens;
- wall-clock time;
- local CPU/RAM/disk;
- remote compute spend;
- network/API calls;
- external mutations;
- operator interruptions.

PO shall reason over expected **value of information per unit cost**. The default progression is:

1. inspect canonical state;
2. reuse cached/reproducible evidence if fresh;
3. run deterministic/static checks;
4. run affected local tests;
5. run narrow experiments;
6. escalate to broader CI/compute only when cheaper evidence cannot answer the question;
7. request operator attention only for genuine authority/ambiguity decisions.

Full-suite tests, expensive models and remote compute are not status symbols; they are escalation steps.

## 10. Accretive learning

The system becomes accretive by converting repeated experience into durable, scoped capability — not by increasing prompt size.

Promotion ladder:

**Observation → LessonCandidate → PracticePattern → Skill/Template/Test/Policy/Capability update**

Promotion requires evidence, scope, confidence, counterexamples, applicability test, owner, version, last verification and expiry/review trigger.

Every promoted practice must measurably improve at least one of:

- correctness;
- evidence strength;
- latency;
- cost;
- recovery quality;
- operator burden;
- context size;
- failure containment.

If it does not improve an observable control metric, it remains a note rather than becoming system behavior.

## 11. Negative knowledge is first-class

Nulls, falsifications, failed integrations, unsupported capabilities and known-bad paths remain queryable as `NegativeKnowledge` records.

Before starting work, PO checks whether the proposed route has already failed under equivalent conditions. Repeating a falsified route requires new evidence explaining why conditions differ.

This rule applies directly to Quant research: failed hypotheses remain searchable but cannot become active strategy memory.

## 12. External capability intake

A future `Capability Intake` surface shall accept repositories, papers, services, APIs, tools and operator notes and classify them as:

- already covered;
- upgrade candidate;
- new capability;
- new sensor/data surface;
- new research hypothesis;
- reusable practice;
- execution/infrastructure capability;
- park;
- high-impact architectural candidate.

Intake produces no authority. Promotion requires code/source inspection, compatibility analysis, sandbox verification where applicable, duplication check, license/security review, evidence of benefit and an explicit home in the abstraction tower.

Large strategy repositories are treated primarily as **hypothesis corpora** and implementation examples. They do not bypass B7/B8 research specifications, leakage controls, realistic cost/fill models, holdouts or promotion gates.

Agent harness repositories are treated as **capability/design donors**. Useful patterns may be adapted, but OCE remains the constitutional spine and PO remains its governed high-level operator.

## 13. Fresh-context adversarial review

Any change capable of altering shared control flow, authority, credentials, data durability, concurrency/retry behavior, spend, public contracts, capital/risk, or widely imported helpers receives an independent fresh-context review before promotion.

Review depth scales with blast radius measured by consumers/callers, not file count. Reviewer context should exclude authoring rationale until after its first fault-finding pass where practical.

Green tests are evidence, not independent review.

## 14. Local verification economy

Local verification should target affected behavior plus static/type/lint/schema checks. Authoritative CI performs the broad suite when required by the gate.

Agents must compute an `AffectedSurface` from dependency/caller relationships. When impact cannot be bounded confidently, escalation to broader testing is required.

This rule reduces repeated local full-suite cost while preserving safety.

## 15. Operator interaction rule

The system should interrupt the operator only for:

- authority expansion or irreversible/high-risk mutation;
- unresolved ambiguity that changes material outcomes;
- conflicting evidence requiring judgment;
- architecture/risk/budget/sequence amendment;
- terminal gate decisions.

Routine recoverable failures, retries, capability substitution, evidence gathering and deterministic reconciliation should be handled autonomously inside pre-authorized bounds.

Operator-facing output is exception-oriented: current state, important change, evidence, uncertainty, cost, decision requested and consequence of each option.

## 16. Metrics

OCE/PO shall eventually track agent-operability metrics:

- context bytes/tokens per completed task;
- reconstruction success from cold start;
- evidence-closure rate;
- verified side-effect rate;
- cost per verified outcome;
- operator interruptions per outcome;
- duplicate-work rate;
- repeated-falsification rate;
- recovery success after interruption;
- capability reuse rate;
- stale-context incident rate;
- contradiction escape rate;
- independent-review defect catch rate.

Optimization targets these system metrics, not raw task throughput alone.

## 17. Block impacts

**B0:** add abstraction-tower ontology, AgentOperability metrics and amendment-controlled capability/practice promotion.

**B1:** expose environment/cost/health facts as WorldTruth and CapabilityGraph inputs; retain local-first economics.

**B2:** Reality Seal additionally inventories agent entrypoints, duplicate context stores, hidden capability surfaces and state that exists only in process/chat memory.

**B3:** canonical schemas add AgentCockpit, CapabilityGraph, WorkGraph, OutcomePacket, ResumeCapsule, EvidenceGap, AffectedSurface and NegativeKnowledge. Event/evidence/replay remain authoritative.

**B4:** PO consumes those projections as its primary operating interface; progressive disclosure, value-of-information planning, fresh-context review and resource budgeting become mandatory behaviors.

**B5–B6:** the application factory and shared surfaces prove the same agent-facing contracts work across products and domain adapters.

**B7:** deterministic quant kernels expose machine-legible capability manifests, affected-surface information and evidence-gap outputs.

**B8:** source intake becomes capability/hypothesis intake; research prioritization explicitly uses information value, unresolved field-model gaps and sensor VOI; Quant Watch projects domain state into AgentCockpit.

**B9:** execution remains separately authorized; all control decisions consume the same canonical projections rather than bespoke execution-agent memory.

**B10:** operational compounding promotes proven practices and capability improvements while tracking whether they actually reduce cost/error/context/operator burden.

## 18. Source inspirations and adaptation boundary

Two external resources motivated this amendment's emphasis but do not become dependencies:

- **QM (`yc-software/qm`)** demonstrates useful patterns for scoped durable workspaces, model/harness interchangeability, shared skills, durable background work, a small stable core tool surface, organization-level policy, durable state outside process memory, fresh-context review, solving fixes at shared layers, and local affected-test economy. OCE adapts these as governed abstractions rather than adopting QM as the system spine.
- **FMZ Square / `fmzquant/strategies`** demonstrates the value of a large, searchable multi-language strategy corpus and reusable trading templates. OCE/Quant treats such corpora as source/hypothesis/capability intake, never as validated alpha.

No external design overrides OCE constitutional authority, CEREBUS doctrine handling, B7 validation gates, B8 research governance, or B9 capital boundaries.

## 19. Acceptance criteria for ratification

A-004 is ready for ratification when:

1. it creates no new autonomous authority;
2. all new objects are projections or governed records with canonical owners;
3. existing block dossier changes can be expressed as amendments rather than sequence rewrites;
4. cold-start reconstruction is explicitly testable;
5. context minimization and evidence preservation are simultaneously testable;
6. cost/resource optimization never weakens mandatory evidence gates;
7. external capability intake cannot bypass validation or security;
8. operator sovereignty and local-first doctrine remain intact.

Until operator ratification, this amendment is planning input only.
