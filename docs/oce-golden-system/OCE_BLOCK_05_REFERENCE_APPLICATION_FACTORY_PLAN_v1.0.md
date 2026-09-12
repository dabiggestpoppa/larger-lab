# OCE Golden System
## Block 5 — Reference Application Factory Planning Dossier

**Document ID:** OCE-B5-PLAN-001  
**Version:** 1.0  
**Status:** READY_FOR_OPERATOR_REVIEW — BUILD LOCKED  
**Dependency:** B4 governed PO workflow verified  
**Exit gate:** One narrow application specified, built, locally operated, deployment-packaged, recovered, changed, and independently verified through OCE

## 1. Block contract

Block 5 proves the Golden System can produce a real application. Selection favors broad lifecycle coverage with low external and financial risk. The reference must exercise identity, intent, planning, workers, deterministic logic, artifacts, evidence, operator review, release packaging, observability, recovery and change without becoming a disguised platform rewrite.

## 2. Chapter 1 — Reference Selection

| Section | Contract | Deliverables | Evidence/gate |
|---|---|---|---|
| B5.C1.S1 Candidate criteria | Define lifecycle coverage, deterministic kernel, operator value, bounded data, local operation, risk and completion window. | weighted criteria and disqualifiers | Criteria fixed before scoring; no favored candidate tailoring. |
| B5.C1.S2 Workflow coverage | Map candidates to OCE/PO contracts, approvals, workers, artifacts, recovery and learning. | coverage matrix | Selected candidate exercises all critical Block 4 paths. |
| B5.C1.S3 Risk ceiling | Exclude capital, regulated submissions, sensitive mass data, public write access and irreversible external effects. | risk assessment | Candidate stays within approved local/read-only or reversible scope. |
| B5.C1.S4 Selection decision | Compare evidence, cost, dependencies, reuse potential and unknowns; record ADR. | decision packet | Operator selects; scoring and dissent preserved. |
| B5.C1.S5 Frozen scope | Freeze users, outcome, inputs, outputs, interfaces, non-goals, budget, acceptance and change process. | Product Charter | No feature expansion without versioned change. |

## 3. Chapter 2 — Product Contract

| Section | Contract | Deliverables | Evidence/gate |
|---|---|---|---|
| B5.C2.S1 User outcome | Define observable operator problem solved, success measures, latency and explanation needs. | outcome contract and scenarios | Human can determine success without reading code. |
| B5.C2.S2 Domain model | Define entities, invariants, state, IDs, provenance and deterministic logic separate from agents. | schemas and domain kernel spec | Illegal states and LLM-as-database shortcuts rejected. |
| B5.C2.S3 Interfaces | Specify local CLI/API/UI, PO tool surface, inputs, outputs, pagination, errors and versioning. | interface contracts and fixtures | Contract tests cover real production path. |
| B5.C2.S4 Failure behavior | Define dependency outage, invalid data, partial task, crash, stale state, retry and cancellation behavior. | failure matrix and recovery plan | No failure returns false success or loses canonical state. |
| B5.C2.S5 Acceptance protocol | Bind requirements to unit, integration, E2E, adversarial, restart, usability and evidence checks. | acceptance registry | Every requirement has executable or explicit human evidence. |

## 4. Chapter 3 — Governed Construction

| Section | Contract | Deliverables | Evidence/gate |
|---|---|---|---|
| B5.C3.S1 Plan generation | PO compiles charter into bounded dependency plan with grants, budgets, gates and staged commits. | ratified build plan | Plan traceable to every acceptance requirement. |
| B5.C3.S2 Build execution | Implement through authorized increments, isolated branches and task-scoped workers; deterministic core first. | code/config/migrations | Git lineage proves bounded changes and reviews. |
| B5.C3.S3 Test layers | Build domain, contract, integration, E2E, negative, property, failure and restart coverage. | test registry and reports | Tests execute real paths; mutation/negative evidence proves sensitivity. |
| B5.C3.S4 Artifact lineage | Link source, dependencies, build, configuration, migration, SBOM, test and package digests. | release manifest/SBOM | Rebuild from declared inputs matches or divergence explained. |
| B5.C3.S5 Operator review | Present functionality, limitations, evidence, risks, cost and denied capabilities in legible form. | review packet | Operator can approve/revise without trusting agent narrative. |

## 5. Chapter 4 — Release and Operation

| Section | Contract | Deliverables | Evidence/gate |
|---|---|---|---|
| B5.C4.S1 Deployment | Produce local deployment and cloud-ready package; deploy only under separate authority after B1. | package, dry run, rollback | Local install works; remote mutation remains hold-gated. |
| B5.C4.S2 Observability | Expose user outcome, service health, task/evidence state, cost and privacy-safe telemetry. | dashboards/queries/runbook | Operator detects failure and traces request locally. |
| B5.C4.S3 Failure injection | Inject process, dependency, storage, malformed input, timeouts and partial write failures. | chaos matrix/results | Safety and evidence survive every mandatory injection. |
| B5.C4.S4 Recovery | Restore state/artifacts, resume/cancel tasks, reconcile projections and verify no duplicate effect. | recovery drills | RTO/RPO and consistency objectives demonstrated. |
| B5.C4.S5 Change cycle | Apply one meaningful requirement change through new intent, plan, migration, tests, release and rollback. | change dossier | Change does not bypass original governance or corrupt prior evidence. |

## 6. Chapter 5 — Factory Evaluation

| Section | Contract | Deliverables | Evidence/gate |
|---|---|---|---|
| B5.C5.S1 Time/effort | Attribute human, agent, CI, compute, rework and blocked time by phase. | cost/time ledger | Measurements distinguish estimate from observation. |
| B5.C5.S2 Reuse achieved | Measure reused OCE/PO contracts/services versus bespoke platform code. | reuse inventory | Claimed reuse verified through imports/runtime paths. |
| B5.C5.S3 Human clarity | Test operator comprehension of state, approval, failure, evidence and recovery. | usability protocol/results | Critical decisions understood without hidden context. |
| B5.C5.S4 Learning captured | Normalize failures, corrections, practices and counterexamples with disposition. | learning ledger | No meaningful observation silently discarded. |
| B5.C5.S5 Factory corrections | Decide what belongs in OCE/PO, template, docs, test or app; prohibit app-specific platform leakage. | correction ADRs and B6 contract | Operator ratifies reusable extraction scope. |

## 7. Implementation increments

| Increment | Future scope | Gate |
|---|---|---|
| B5-I0 | Freeze candidate criteria, risk ceiling and evaluation protocol | Selection process ratified |
| B5-I1 | C1 compare/select/freeze application | Operator-approved Product Charter |
| B5-I2 | C2 outcome/domain/interfaces | Deterministic product contracts pass |
| B5-I3 | C2 failures/acceptance and construction plan | Requirement-test registry complete |
| B5-I4 | C3 deterministic kernel and first vertical slice | Local real path passes |
| B5-I5 | C3 complete build/tests/lineage/operator review | Release candidate evidence complete |
| B5-I6 | C4 local deployment, observability and recovery | Clean local install/restart/restore pass |
| B5-I7 | C4 change cycle plus C5 measurements/learning | Governed change demonstrated |
| B5-I8 | Independent E2E, adversarial, usability and evidence audit | Zero critical bypass or false claim |
| B5-I9 | Factory gate and B6 reusable-extraction contract | Operator-only completion |

## 8. Selection constraint

The exact reference application is deliberately selected at B5-I1 using current evidence. The plan forbids using a high-risk quant execution application merely because Quant is strategically important. The reference may be quant-adjacent only if it has no capital authority and remains narrow.

## 9. Non-goals

No general SDK/platform extraction before evidence, no public SaaS, no live trading, no mass agent fleet, no cloud-only development path, and no success claim based solely on a demo.
