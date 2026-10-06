# OCE Golden System
## Block 3 — OCE Constitutional Spine Planning Dossier

**Document ID:** OCE-B3-PLAN-001  
**Version:** 1.0  
**Status:** READY_FOR_OPERATOR_REVIEW — BUILD LOCKED  
**Dependency:** B2 canonical-source registry ratified  
**Exit gate:** One verified identity, authority, event, evidence, recovery, and audit spine

## 1. Block contract

Block 3 turns the reality-sealed repository into one enforceable Golden System spine. It consolidates constitutional contracts and deterministic enforcement beneath PO, Hermes, applications, and workers. It does not build the complete PO workflow or any domain application.

## 2. Chapter 1 — Canonical Contracts

| Section | Implementation contract | Deliverables | Evidence and exit |
|---|---|---|---|
| B3.C1.S1 Schema governance | Establish registry, owners, semantic versions, compatibility classes, migrations, validation and retirement. | schema registry/API, linter, decision records | Unknown/duplicate versions rejected; fixtures cover forward/backward cases. |
| B3.C1.S2 Identity contracts | Define stable Operator, PO, Hermes, service, app and worker identities, authentication provenance and session binding. | AgentIdentity/ServiceIdentity schemas and resolver | Impersonation, missing identity and cross-role confusion fail closed. |
| B3.C1.S3 Intent and plan | Canonicalize Intent, Plan, TaskContract, ContextBundle, referral and outcome envelopes without embedding raw memory. | versioned schemas and builders | Round-trip, bounds, amendment and invalid-state tests pass. |
| B3.C1.S4 Artifact and evidence | Define artifact identity, source/input hashes, producer, environment, status, manifest and retention links. | ArtifactRef, EvidenceRef, Manifest contracts | Mutable/missing/mismatched artifacts cannot support promotion. |
| B3.C1.S5 Version compatibility | Enforce producer/consumer matrix, migrations, deprecation and unsupported-version refusal. | compatibility engine and matrix | Mixed/unsupported versions rejected with actionable evidence. |

## 3. Chapter 2 — Authority Engine

| Section | Implementation contract | Deliverables | Evidence and exit |
|---|---|---|---|
| B3.C2.S1 Capability grants | Encode actor, action, target, environment, limits, expiry, approval, idempotency and evidence obligations. | grant schema, issuer/verifier, registry | Missing, forged, replayed, wrong-target and expired grants denied. |
| B3.C2.S2 Risk classes | Classify read, local write, external write, deployment, destructive, messaging, broker and capital actions. | risk taxonomy and capability mapping | Every enabled mutation maps to one class and required control. |
| B3.C2.S3 Approval gates | Implement operator review packets, separation of request/approval, scoped confirmation and anti-confusion UI contracts. | approval state machine and evidence | Agents cannot approve their own request; ambiguity blocks. |
| B3.C2.S4 Revocation and expiry | Make grants revocable, time-bound and checked at admission and before side effect; define in-flight cancellation. | revocation registry and propagation | Revocation race, clock skew and restart tests prevent stale action. |
| B3.C2.S5 Denial evidence | Record safe reason codes, policy/version, actor, request and remediation without leaking secrets. | denial envelope and audit views | Every denial is attributable and replay-verifiable. |

## 4. Chapter 3 — Event and State

| Section | Implementation contract | Deliverables | Evidence and exit |
|---|---|---|---|
| B3.C3.S1 Event envelope | Standardize ID, type, schema, actor, authority, causality, target, hashes, environment, result and evidence. | event schema, producer SDK, validators | Missing/duplicate/malformed events rejected deterministically. |
| B3.C3.S2 State machines | Define legal states/transitions for plans, tasks, grants, artifacts, deployments, incidents and strategies. | transition registries and diagrams | Illegal, skipped and terminal-state mutation tests fail closed. |
| B3.C3.S3 Causality | Preserve parent/root correlation, ordering facts, monotonic sequence where applicable and clock uncertainty. | causality index and query surface | Orphans, cycles and contradictory order quarantined. |
| B3.C3.S4 Idempotency/retries | Bind idempotency to actor/action/target/input/version; define retry classes and exactly-once effect verification. | idempotency store and retry policy | Duplicate delivery never duplicates consequential effect. |
| B3.C3.S5 Quarantine | Isolate invalid events/state with reason, evidence, owner, review and safe replay path. | quarantine store and operator queue | Quarantine cannot silently re-enter canonical projections. |

## 5. Chapter 4 — Evidence System

| Section | Implementation contract | Deliverables | Evidence and exit |
|---|---|---|---|
| B3.C4.S1 Evaluation protocol | Register requirement, test, environment, inputs, evaluator version, expected/observed and falsification criteria. | evaluation schema/runner interface | Static claims cannot substitute for execution. |
| B3.C4.S2 Manifests/hashes | Produce deterministic manifests after mutable output closes; support required/optional artifacts and outer archive digest. | manifest builder/verifier | Tamper, missing artifact and stale hash rejected. |
| B3.C4.S3 Independent verification | Separate builder result from gate evaluator and operator ratification; freeze evaluator per run. | independent gate and verifier report | Builder cannot modify its evaluator/evidence during final gate. |
| B3.C4.S4 Truth promotion | Promote claims through SCAFFOLDED→SIMULATED→OBSERVED→VERIFIED with explicit evidence and demotion triggers. | promotion ledger and policy | Promotion without sufficient evidence is rejected; staleness demotes. |
| B3.C4.S5 Replay | Reconstruct decisions/results from immutable inputs, versions and evidence or explain non-replayability. | replay harness and divergence report | Same inputs reproduce or produce bounded documented divergence. |

## 6. Chapter 5 — Operational Integrity

| Section | Implementation contract | Deliverables | Evidence and exit |
|---|---|---|---|
| B3.C5.S1 Health/readiness | Separate process liveness, dependency readiness, capability readiness and safe-to-operate state. | health contract and probes | False-green and partial-dependency tests return DEGRADED/BLOCKED. |
| B3.C5.S2 Structured telemetry | Correlate logs, metrics, traces, events and costs; redact secrets and constrain cardinality. | telemetry envelope and local viewer | One request traceable end-to-end without sensitive leakage. |
| B3.C5.S3 Restart recovery | Rebuild projections, leases, in-flight tasks and idempotency from durable truth. | recovery coordinator and drills | Crash at every transition yields no corruption/duplicate effect. |
| B3.C5.S4 Incident state | Define detection, severity, containment, evidence, communication, resolution and learning promotion. | incident state machine/runbook | Simulated incidents preserve authority and audit chain. |
| B3.C5.S5 Restore drills | Verify database, events, artifacts, configuration and keys against recovery objectives without trusting backup existence. | restore harness and reports | Successful clean restore plus reconciliation required. |

## 7. Implementation increments

| Increment | Future scope | Gate |
|---|---|---|
| B3-I0 | Freeze canonical registries, migrations, threat model and regression baseline | Contracts/version policy ratified |
| B3-I1 | C1 schemas, identity and compatibility | One authoritative registry; duplicates disabled |
| B3-I2 | C2 grants and risk taxonomy | Admission/denial deterministic |
| B3-I3 | C2 approvals, revocation and denial evidence | Self-approval/replay/race adversarial pass |
| B3-I4 | C3 event envelope, states and causality | Legal lifecycle and audit trace pass |
| B3-I5 | C3 idempotency, retries and quarantine | Duplicate-effect and invalid-state tests pass |
| B3-I6 | C4 evaluation, manifest, promotion and replay | Independent gate and tamper rejection pass |
| B3-I7 | C5 health, telemetry, restart, incident and restore integration | Complete local spine demonstration |
| B3-I8 | Independent security/failure/recovery reconciliation | Zero mandatory inconsistency or bypass |
| B3-I9 | Operator gate, archive, learning ledger and B4 dependency contract | Operator-only `GATED_COMPLETE` |

## 8. Architecture invariants

OCE remains the single constitutional spine; adapters cannot own truth. PO and Hermes have separate identities and memories. Local harnesses exist for all services. Cloud supplies deployment/durability later. Every external or consequential effect is admitted and verified. PostgreSQL/event truth is not replaced by LLM memory, Redis, logs or Telegram.

## 9. Non-goals

No complete PO builder, reference application, reusable UI, quant kernel, broker execution, unrestricted autonomous improvement, or mass legacy deletion is authorized.
