# OCE Golden System
## Block 6 — Reusable Platform Surfaces Planning Dossier

**Document ID:** OCE-B6-PLAN-001  
**Version:** 1.0  
**Status:** READY_FOR_OPERATOR_REVIEW — BUILD LOCKED  
**Dependency:** B5 reference-application evidence and correction decisions  
**Exit gate:** A second application reuses the platform with materially less bespoke foundation code and no governance bypass

## 1. Block contract

Block 6 extracts only reuse proven by Block 5. It creates stable developer/operator surfaces and shared services without turning OCE into premature multi-tenant infrastructure. APIs remain local-first and provider-neutral; cloud packaging is optional deployment output.

## 2. Chapter 1 — Developer Surface

| Section | Contract | Deliverables | Evidence/gate |
|---|---|---|---|
| B6.C1.S1 API boundary | Expose versioned OCE functions without leaking storage internals or bypassing authority. | OpenAPI/protocol contracts and auth scopes | Consumer contract, denial and compatibility tests pass. |
| B6.C1.S2 SDK | Provide typed local clients for identity, intents, tasks, events, artifacts, evidence and approvals. | SDK packages, examples, generated types | SDK invokes canonical API; no duplicated business rules. |
| B6.C1.S3 Templates | Package app skeleton, domain kernel boundary, migrations, tests, telemetry and deployment manifests. | versioned templates | Generated app starts/tests cleanly and declares inherited versions. |
| B6.C1.S4 Local harness | One command/dev profile starts required local services, fixtures, fake externals and evidence capture. | harness and environment fingerprint | Fresh-machine developer path reproducible without cloud. |
| B6.C1.S5 Compatibility policy | Define support windows, feature detection, migration, deprecation and breaking-change process. | compatibility matrix and tooling | Old supported consumer passes; unsupported version fails clearly. |

## 3. Chapter 2 — Operator Surface

| Section | Contract | Deliverables | Evidence/gate |
|---|---|---|---|
| B6.C2.S1 Capability view | Show identities, proven capabilities, ceilings, status, versions and evidence links. | operator capability explorer | No scaffold/simulation displayed as operational proof. |
| B6.C2.S2 Approval inbox | Present action/target/effect/cost/reversibility/expiry/evidence and allow scoped approve/deny. | approval UI/API | Replay, stale, wrong-target and self-approval attacks denied. |
| B6.C2.S3 Evidence explorer | Navigate intent→plan→task→artifact→evaluation→gate with hashes and source identity. | evidence query/view | Random samples reconcile to immutable manifests. |
| B6.C2.S4 Incident view | Display severity, impact, containment, owners, timeline, recovery and unresolved risk. | incident console | Failure drills become legible within defined latency. |
| B6.C2.S5 Cost/capacity | Attribute provider/model/worker/storage/CI cost and capacity to task/app while separating estimate/actual. | cost ledger and alerts | Budgets/ceilings trigger before excess where controllable. |

## 4. Chapter 3 — Shared Services

| Section | Contract | Deliverables | Evidence/gate |
|---|---|---|---|
| B6.C3.S1 Identity service | Centralize actor/service/app identity and credential-reference metadata without storing raw secrets in clients. | identity API and adapters | Cross-app isolation and revocation pass. |
| B6.C3.S2 Workflow service | Execute versioned state machines, leases, retries, cancellations and approvals. | workflow API/engine | Crash/replay/concurrency tests preserve legal state. |
| B6.C3.S3 Knowledge service | Store governed facts, sources, lessons and retrieval metadata separate from agent memory. | knowledge API and promotion policy | Tenant/project/scope and provenance isolation pass. |
| B6.C3.S4 Artifact service | Register immutable artifacts, manifests, retention, storage classes and retrieval authorization. | artifact API/store adapters | Tamper, missing, stale and unauthorized retrieval rejected. |
| B6.C3.S5 Evaluation service | Run registered evaluators, independent gates, comparisons and promotion decisions. | evaluation API/runner | Builder cannot silently change evaluator or result. |

## 5. Chapter 4 — Domain Adapter Pattern

| Section | Contract | Deliverables | Evidence/gate |
|---|---|---|---|
| B6.C4.S1 Adapter contract | Define domain identity, schemas, capabilities, deterministic kernel, errors, evidence and lifecycle hooks. | adapter interface and conformance kit | Adapter cannot bypass OCE identity/authority/events. |
| B6.C4.S2 External identity | Map provider/broker/source IDs to canonical IDs with revision and ambiguity handling. | identity map contract | Collision, rename and unknown mapping fail safely. |
| B6.C4.S3 Data translation | Validate units, time, precision, nulls, revisions and provenance at boundaries. | translation schemas and golden fixtures | Round-trip/loss tests expose any semantic change. |
| B6.C4.S4 Failure isolation | Bound timeout, retry, circuit, queue, quarantine and degradation per external dependency. | resilience policy and simulators | One adapter failure does not corrupt shared spine. |
| B6.C4.S5 Certification | Require contract, security, determinism, recovery, observability and evidence tests before enablement. | certification report and registry state | Uncertified adapter cannot become active. |

## 6. Chapter 5 — Reuse Proof

| Section | Contract | Deliverables | Evidence/gate |
|---|---|---|---|
| B6.C5.S1 Second-app scope | Choose a distinct, bounded application testing reuse and one new domain kernel. | charter and risk ceiling | Not a clone of reference app; no capital/public mutation. |
| B6.C5.S2 Reuse measurements | Measure generated/reused/custom code, setup time, defects, duplicated rules and operator steps. | baseline comparison | Material improvement evidenced, not asserted. |
| B6.C5.S3 New domain kernel | Implement deterministic domain logic behind adapter without leaking into OCE shared services. | kernel and property tests | Domain semantics remain app-owned and reproducible. |
| B6.C5.S4 Cross-app isolation | Prove identities, data, tasks, artifacts, approvals, failures and costs remain isolated. | isolation test suite | Cross-app reads/writes and noisy failure denied/contained. |
| B6.C5.S5 Platform gate | Decide retained APIs/templates/services, remove speculative abstractions and freeze B7 contract. | platform release and ADRs | Operator ratifies reusable surface and limitations. |

## 7. Implementation increments

| Increment | Future scope | Gate |
|---|---|---|
| B6-I0 | Freeze extraction decisions, API principles, compatibility and conformance baseline | Only B5-proven reuse included |
| B6-I1 | C1 API/SDK | Canonical path and compatibility pass |
| B6-I2 | C1 templates/local harness | Fresh generated app starts locally |
| B6-I3 | C2 capability/approval/evidence views | Operator truth/authority tests pass |
| B6-I4 | C2 incident/cost plus C3 identity/workflow | Failure/cost trace end-to-end |
| B6-I5 | C3 knowledge/artifact/evaluation | Provenance, tamper and independent gate pass |
| B6-I6 | C4 adapter contract/translation/isolation/certification | Conformance kit rejects bad adapters |
| B6-I7 | C5 second application and reuse measurement | Material reuse and cross-app isolation demonstrated |
| B6-I8 | Independent API/security/compatibility/recovery audit | No governance bypass or speculative claim |
| B6-I9 | Platform gate and B7 quant-foundation dependency contract | Operator-only completion |

## 8. Non-goals

No Kubernetes by default, multi-tenant SaaS, generalized plugin marketplace, domain logic inside OCE, public unauthenticated API, cloud-only SDK, or Quant execution.
