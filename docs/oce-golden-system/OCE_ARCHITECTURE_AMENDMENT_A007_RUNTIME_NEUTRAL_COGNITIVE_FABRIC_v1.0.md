# OCE Golden System
## Amendment A-007 — Runtime-Neutral Cognitive Fabric

**Document ID:** OCE-AMEND-A007  
**Version:** 1.0  
**Status:** PROPOSED FOR OPERATOR RATIFICATION  
**Parents:** OCE Constitution 1.1; A-002; A-005 proposed  
**Build authorization:** None

## 1. Decision

Larger Lab shall define durable cognitive roles independently from the current agent products that implement them.

Current preferred mapping:

- **Hermes** — CompanionRuntime candidate;
- **PO** — ExecutiveReasoner role;
- **OpenClaw** — broad WorkerRuntime/orchestration candidate;
- **Pi** — narrow engineering WorkerRuntime candidate;
- **QCAE/research workers** — ScienceRuntime candidates;
- future systems — eligible after certification against the same contracts.

No named runtime receives permanent constitutional authority merely because it is currently best-in-class.

## 2. Role boundaries

### 2.1 CompanionRuntime

Purpose: human continuity, conversation, reminders, lightweight research, summaries, and bounded referrals.

Hermes is the current preferred implementation because its natural design emphasizes persistent user continuity, learned skills, personal memory, scheduling, and cross-session interaction.

CompanionRuntime cannot become canonical OCE truth, Quant executive authority, strategy promotion authority, deployment authority, or capital authority.

### 2.2 ExecutiveReasoner

PO is the institutional executive role. It interprets operator goals, resolves ConstraintFields, prioritizes research, allocates capabilities, synthesizes evidence, manages cross-domain objectives, and escalates material decisions.

PO's role contract survives changes in the underlying model or agent harness.

### 2.3 WorkerRuntime

WorkerRuntime performs bounded tasks from TaskContracts and ContextBundles under OCE grants.

OpenClaw is a candidate for long-running, multi-step, session-rich, tool-rich, and multi-worker jobs.

Pi is a candidate for focused engineering work where a smaller harness, direct code interaction, and narrow task surface are advantageous.

Neither runtime owns institutional memory or authority.

### 2.4 ScienceRuntime

ScienceRuntime generates and critiques hypotheses, chooses bounded experiments, evaluates mechanism evidence, and synthesizes research under B7/B8 controls.

It cannot reveal sealed holdouts to itself, certify its own claims, or bypass deterministic validation.

## 3. Runtime certification

A runtime becomes eligible only after a versioned certification packet records:

- identity/version;
- supported modalities;
- tool/capability surface;
- context limits;
- deterministic invocation interface;
- state/restart behavior;
- sandbox compatibility;
- permission model or required external sandbox;
- telemetry/evidence behavior;
- interruption/cancellation semantics;
- credential boundary;
- cost and latency characteristics;
- known failure modes;
- supply-chain/license posture;
- benchmark task results;
- allowed role classes.

Runtime popularity is not certification.

## 4. AdaptiveReasoner and WorkerRuntime interfaces

The architecture shall define stable adapter interfaces so future reasoning paradigms can replace current LLM-based implementations without rewriting OCE state or domain systems.

Expected logical operations include:

- receive bounded ContextBundle/AgentCockpit;
- accept task/goal and authority envelope;
- request additional context by typed reference;
- invoke only granted capabilities;
- emit structured intermediate checkpoints when required;
- return OutcomePacket/WorkerResult;
- support interruption and ResumeCapsule reconstruction;
- expose model/runtime provenance.

## 5. Cognitive routing

PO/OCE shall route work by requirements rather than brand names.

Task requirements may include:

- capability class;
- risk;
- evidence level;
- context size;
- latency;
- cost ceiling;
- privacy/data boundary;
- deterministic-tool preference;
- concurrency need;
- sandbox requirements;
- reliability target.

Available runtimes publish verified capabilities and historical performance.

Routing favors the cheapest admissible path capable of meeting the required evidence and risk level.

## 6. Future cognitive market

The architecture shall remain compatible with abundant future intelligence.

Long-run Worker Fabric may operate as a governed cognitive market:

```text
TASK REQUIREMENTS
  -> eligible runtimes
  -> authority/data filtering
  -> reliability/cost/latency ranking
  -> bounded execution
  -> observed outcome
  -> reliability update
```

This is scheduling, not authority delegation. OCE remains the grant and evidence authority.

## 7. Hermes / OpenClaw relationship

A-007 revises the runtime-specific implication in A-002 that Hermes must permanently replace OpenClaw.

The preferred near-term architecture is:

- Hermes owns the Companion role;
- OpenClaw may operate as a Worker Fabric runtime;
- cross-role memory is not shared by default;
- both communicate with OCE through typed contracts;
- failure or removal of either must not damage canonical institutional continuity.

If future evidence favors another runtime, the role can migrate without changing its authority contract.

## 8. Context and memory isolation

Canonical memory namespaces remain separate from runtime-native memory.

Runtime-native memory may improve usability within its role, but important facts, decisions, grants, artifacts, experiments, and state required for institutional continuity must be promoted into OCE contracts.

No product-specific memory database becomes a mandatory system dependency.

## 9. Worker composition

A broad WorkerRuntime may delegate a narrow subtask to another certified WorkerRuntime only through an OCE-approved delegation contract.

Example:

```text
PO
 -> OpenClaw worker: inspect external quant repo
      -> Pi worker: implement bounded compatibility probe
      -> deterministic scanner: license/dependency checks
      -> research worker: compare methodology
 -> synthesis returned to PO/OCE
```

Authority never implicitly propagates with delegation depth.

## 10. Acceptance tests

A-007 is accepted only if future implementation proves that:

1. the same TaskContract can be executed by two certified worker runtimes;
2. switching runtimes does not alter OCE authority semantics;
3. Hermes can fail while PO/OCE continue;
4. OpenClaw can fail while Hermes personal continuity remains intact;
5. a Pi-like worker with broad host permissions is safely constrained by external OCE sandbox policy;
6. a task can resume on a different runtime using ResumeCapsule/state references;
7. runtime reliability history can influence routing without promoting runtime claims to truth;
8. recursive delegation cannot expand authority.

## 11. Operator decision

Proposed decision: `RATIFY_A007_RUNTIME_NEUTRAL_COGNITIVE_FABRIC`.

Ratification updates architecture and future planning only. It does not install or migrate Hermes, OpenClaw, Pi, or any model.