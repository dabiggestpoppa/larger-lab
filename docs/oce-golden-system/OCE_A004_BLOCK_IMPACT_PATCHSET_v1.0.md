# OCE Golden System
## A-004 Block Impact Patchset

**Document ID:** OCE-A004-PATCH-001  
**Version:** 1.0  
**Status:** PROPOSED — accompanies A-004; BUILD LOCKED  
**Purpose:** Convert A-004 from design intent into concrete amendments to existing block plans without rewriting ratified history.

## 1. Amendment method

The existing Atlas and Block 4/7/8 dossiers remain preserved at their current versions. This patchset defines additive requirements to apply when those documents are next revised or ratified. No block sequence changes. No build authorization changes.

A-004 introduces the following canonical objects for future B3 schema ownership:

- `AgentCockpit`
- `CapabilityGraph`
- `WorkGraph`
- `OutcomePacket`
- `ResumeCapsule`
- `EvidenceGap`
- `AffectedSurface`
- `NegativeKnowledge`
- `ResourceBudget`

## 2. Atlas patch

Add to the permanent planning grammar:

### Agent-legibility invariant
Every section that exposes behavior to PO or workers must identify:

- canonical state owner;
- machine-readable projection consumed by the agent;
- minimum context required;
- authority/grant dependency;
- evidence required for completion;
- restart/resume state;
- resource-cost class;
- downstream consumers.

### Cold-start test
A block may not claim agent-operable completion if a fresh authorized agent cannot reconstruct the active state and next safe action from canonical records without relying on an earlier chat transcript.

### Evidence-gap rule
Plans must define what observation would change the current truth label. Work should target the smallest admissible evidence gap, not merely complete a checklist of actions.

### Accretion rule
Learning is promoted only when it becomes a scoped reusable object — test, policy, template, skill, capability, playbook or architecture decision — and demonstrates observable benefit.

## 3. Block 3 — Constitutional Spine patch

Add to B3.C1 Canonical Contracts:

- schema families for the nine A-004 canonical objects;
- stable object IDs and version references so compaction/handoff does not depend on prose summaries;
- explicit projection ownership: AgentCockpit and ResumeCapsule are derived views, not parallel truth stores.

Add to B3.C2 Authority Engine:

- CapabilityGraph filtering by grants, risk and environment;
- per-task ResourceBudget ceilings;
- operator-interruption criteria as policy rather than prompt convention.

Add to B3.C3 Event and State:

- checkpoint/resume events;
- work-DAG node state and lease/expiry semantics;
- activity/effect distinction.

Add to B3.C4 Evidence System:

- `EvidenceGap` calculation;
- `NegativeKnowledge` linkage to prior failed/falsified routes;
- independent-review evidence type distinct from test evidence.

Add to B3.C5 Operational Integrity:

- cold-start reconstruction drill;
- stale-context incident detection;
- resume-after-crash proof.

## 4. Block 4 — PO Governed Builder patch

### B4.C1 Intent and Reasoning

**S1 Goal interpretation:** output operator-value, uncertainty and interruption criteria in addition to objective/constraints.

**S2 Facts/assumptions:** every included claim carries a reason-for-inclusion and freshness. The planner must prefer canonical current state over narrative recall.

**S3 Decomposition:** PlanContract becomes a typed `WorkGraph`; each node has ResourceBudget, EvidenceGap target, stop conditions and consumer-facing success contract. Compute an `AffectedSurface` from dependency/caller relationships where possible.

**S4 Alternatives:** alternatives are ranked by expected information value, reversibility, evidence strength, resource cost and operator burden — not model preference.

**S5 Plan contract:** compile an initial `AgentCockpit` and require explicit escalation thresholds.

### B4.C2 Memory and Context

**S1 Constitutional retrieval:** Tier-0 control kernel is mandatory and minimal.

**S2 Project state:** produce canonical state refs and a projected cockpit rather than broad summaries.

**S3 Episodic traces:** classify archive depth. Tier-3 history is excluded by default.

**S4 Source grounding:** support source/capability intake classification and negative-knowledge lookup.

**S5 Context handoff:** add `ResumeCapsule`; all boundaries use stable refs/packets. No transcript-as-state.

### B4.C3 Governed Tools

**S1 Tool registry:** upgrade flat registry to `CapabilityGraph` with substitutes, composition constraints, expected evidence, latency/cost and task-class reliability.

**S2 Sandboxing:** sandbox selection is capability-path dependent and least-privilege.

**S3 Mutation controls:** no change except that mutation plan must reference WorkGraph node and ResourceBudget.

**S4 Side-effect verification:** effect receipt closes an explicit EvidenceGap; tool acknowledgement never does.

**S5 Rollback:** rollback/compensation capability becomes part of capability selection ranking.

### B4.C4 Worker Orchestration

**S1 Worker identity:** worker enters from AgentCockpit subset and receives no unrelated project memory.

**S2 Task contracts:** include budget, EvidenceGap, stop condition, expected OutcomePacket and resume semantics.

**S3 Delegation limits:** add model/tool escalation ladder and value-of-information scheduling.

**S4 Result synthesis:** worker outputs are `OutcomePacket`s; reducer resolves claims/evidence/conflicts and does not concatenate prose.

**S5 Worker failure:** every recoverable task writes ResumeCapsule before retry/substitution where possible.

### B4.C5 Learning PO

**S1 Observation capture:** add cost/context/operator-interruption telemetry.

**S2 Error clustering:** link clusters to AffectedSurface and capability versions.

**S3 Lesson validation:** lesson must show measurable expected benefit and include applicability test.

**S4 Practice retrieval:** retrieve the smallest applicable validated practice set, not all nearby lessons.

**S5 Governed improvement:** candidate improvements can target prompt, skill, capability graph, test, policy, template or architecture; same-run self-authority remains prohibited.

### B4 implementation gate additions

B4-I0 must freeze A-004 schemas.

B4-I2 must prove cold-start plan reconstruction.

B4-I3 must prove progressive disclosure and transcript-independent handoff.

B4-I6 must prove low-cost capability selection and bounded escalation.

B4-I7 must report context/token cost, operator interruptions, verified outcome cost and restart recovery.

B4-I8 fresh-context adversarial review is mandatory for shared control-flow changes.

## 5. Block 7 — Quant Foundation patch

### Market Data Truth
Dataset and feature services expose machine-legible capability manifests: universe, temporal coverage, PIT properties, latency/cost, missingness, provider risks and exact evidence they can support.

### Research Kernel
Every StrategySpec/FeatureSpec/engine/cost model becomes discoverable through CapabilityGraph without granting execution authority.

Backtest paths return explicit `EvidenceGap`s when data, fill realism, sample size, time semantics or engine compatibility prevent stronger claims.

### Validation Kernel
Fast falsification becomes the cheapest-evidence stage in an escalation ladder. Holdout/walk-forward/stress are invoked because the desired truth promotion requires them, not because every exploratory idea automatically consumes the full stack.

`NegativeKnowledge` stores rejected/falsified paths with equivalence conditions so the system can avoid repeatedly testing the same idea under materially identical assumptions.

### Portfolio and Risk
Risk and portfolio engines remain deterministic and independent. Their current state is exposed to agents as projections; agents cannot override it through memory or narrative.

### Lineage Integration
Canonical strategy wells add machine-readable research-state projections so agents can discover existing equivalent strategies, prior falsifications and reusable components before creating another lineage.

## 6. Block 8 — Quant Lab and Watch patch

### B8.C1 Research Intelligence

**Source ingestion** becomes generalized `Source/Capability Intake`. URLs, repos, papers, books, datasets and operator observations receive provenance, rights, duplication, security and expected-information-value classification.

**Hypothesis generation** must reference which existing field-model or strategy EvidenceGap the hypothesis closes, or explicitly mark itself as exploratory novelty.

**Mechanism critique** queries NegativeKnowledge and prior strategy wells before authorizing new compute.

**Strategy registration** reuses existing capability atoms where possible rather than copying strategy implementations.

**Research prioritization** adds sensor VOI, unresolved mechanism dependence, duplication risk, expected evidence gain per cost and operator burden.

### B8.C2 Experiment Orchestration

Protocols compile to WorkGraph nodes. The scheduler prefers cached evidence, deterministic local computation and narrow falsification before expensive experiments.

Result normalization emits OutcomePackets. Failed experiments update NegativeKnowledge and can create validated repair/practice candidates.

### B8.C3 Quant Watch

Market, strategy, data-drift and performance projections are valid DomainState inputs to AgentCockpit.

Alerts should be emitted only when they close or create a decision-relevant EvidenceGap; repeated low-value alerts are suppressed.

### B8.C4 Operator Experience

The research inbox becomes exception-oriented: highest-value decisions, unresolved contradictions, blocked EvidenceGaps, cost-to-resolve and consequence of waiting.

Experiment explorer and strategy dossiers expose exact lineage plus negative/failure evidence without requiring the operator or PO to reconstruct history manually.

### B8.C5 Research Governance

Agent limits include context, model, API, compute and operator-interruption budgets.

Promotion audits include duplicate-work rate, holdout consumption, cost per verified result and whether an existing negative record should have blocked the run.

## 7. External resource dispositions from this review

### FMZ Square and `fmzquant/strategies`
Disposition: **NEW RESEARCH/CAPABILITY CORPUS — useful, not canonical alpha.**

Use cases:

- strategy-idea ingestion;
- taxonomy mining;
- implementation examples across Python/JavaScript/C++/Pine and other FMZ formats;
- execution-pattern examples such as grid, market making, copy trading, TWAP/iceberg and funding arbitrage;
- negative-control/baseline strategy generation.

Do not bulk-import strategies into the canonical strategy well. Build an indexer/intake adapter later and promote individual ideas only through B8→B7 validation.

### `yc-software/qm`
Disposition: **HIGH-VALUE ARCHITECTURE/PRACTICE DONOR — do not replace OCE.**

Patterns worth adapting:

- scoped durable workspaces;
- scope-owned/shareable skills with governed promotion;
- interchangeable model/harness interfaces;
- durable background work;
- small stable agent tool surface with sandbox execution behind it;
- durable state rather than process-memory state;
- fresh-context independent review;
- caller/blast-radius based test selection;
- fixing at shared layers and preferring simplification;
- org-level policy/security posture with narrower scopes able to tighten.

OCE already has stronger constitutional authority, evidence, quant separation and capital boundaries. Therefore QM is a donor of ergonomics and operating practices, not a platform dependency.

## 8. Ratification effect

If the operator ratifies A-004, the next formal revisions should be:

- Atlas v1.1
- B3 Plan v1.1
- B4 Plan v1.1
- B7 Plan v1.1
- B8 Plan v1.1
- Full Program Build Roadmap v1.1

Revision must preserve prior text/version lineage and mark A-004 as the reason for change. Until then this patchset is planning evidence only.
