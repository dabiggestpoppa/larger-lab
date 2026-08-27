# OCE Golden System
## Block 10 — Operational Compounding Planning Dossier

**Document ID:** OCE-B10-PLAN-001  
**Version:** 1.0  
**Status:** READY_FOR_OPERATOR_REVIEW — BUILD LOCKED  
**Dependency:** Operational evidence from Blocks 1–9  
**Exit gate:** Demonstrated improvement in reliability, efficiency and future builds without authority, truth, reproducibility or operator-legibility drift

## 1. Block contract

Block 10 makes learning operational but never grants self-amendment. PO may discover and propose improvements; fixed evaluators, OCE policy and the operator decide promotion. Hermes personal learning remains separate. Improvements are reversible, versioned, compared to anchors and continuously eligible for demotion.

## 2. Chapter 1 — Reliability

| Section | Contract | Deliverables | Evidence/gate |
|---|---|---|---|
| B10.C1.S1 Service objectives | Define user/outcome SLOs, indicators, windows, exclusions, owners and consequence by service criticality. | SLO registry | Indicators derive from real events; targets ratified and measurable. |
| B10.C1.S2 Failure budgets | Translate SLO misses into release/experiment/capacity constraints without hiding incidents. | budget ledger and policy | Exhaustion triggers defined action; no metric gaming. |
| B10.C1.S3 Incident response | Standardize detect, declare, contain, communicate, recover, reconcile and review. | incident automation/runbooks | Multi-failure drills preserve authority/evidence. |
| B10.C1.S4 Recovery exercises | Schedule restore, failover, restart, provider-loss, key-revocation and operator-absence drills. | exercise registry/results | Objectives observed; failed drills create blockers. |
| B10.C1.S5 Reliability trends | Analyze rates, duration, recurrence, detection, recovery and confidence with changing denominators. | trend reports | Narrative distinguishes signal, noise and instrumentation change. |

## 3. Chapter 2 — Resource Intelligence

| Section | Contract | Deliverables | Evidence/gate |
|---|---|---|---|
| B10.C2.S1 Cost attribution | Attribute cloud, model, worker, CI, storage, data, broker and human review cost to app/task/outcome. | cost event/ledger | Actual vs estimate and shared allocation explicit. |
| B10.C2.S2 Capacity signals | Observe CPU/GPU/memory/storage/queue/latency/data/model/token constraints and forecast thresholds. | capacity model/alerts | Scaling recommendation cites sustained evidence. |
| B10.C2.S3 Burst optimization | Select local/durable/burst placement by trust, data, cost, latency and reproducibility; benchmark providers. | placement policy and experiments | Marketplace worker never gains durable authority. |
| B10.C2.S4 Storage lifecycle | Classify canonical, evidence, artifact, cache, raw observation and tombstone retention/archival/deletion. | lifecycle policies and dry runs | Required lineage/restores survive; secrets/private data minimized. |
| B10.C2.S5 Provider portability | Exercise replacement/export/restore for cloud, model, storage, Telegram, data and broker adapters. | portability drills and exit packs | Constitutional state remains operator-controlled. |

## 4. Chapter 3 — Practice Intelligence

| Section | Contract | Deliverables | Evidence/gate |
|---|---|---|---|
| B10.C3.S1 Pattern discovery | Mine normalized observations for recurring mechanisms while preserving counterexamples and selection bias. | PatternCandidate registry | Frequency alone cannot promote. |
| B10.C3.S2 Lesson evaluation | Test candidates on held tasks/anchors with fixed evaluator, uncertainty and regression guardrails. | evaluation protocol/results | Builder cannot alter evaluator during epoch; harms visible. |
| B10.C3.S3 Playbook promotion | Promote validated lessons to scoped playbook/test/template/policy/tool with owner and expiry. | promotion event and versions | Operator/policy approval matches impact; rollback exists. |
| B10.C3.S4 Tool improvement | Propose/build tool changes in sandbox, compare to anchors, canary, monitor and revert. | ToolImprovementPackage | No self-granted tool authority or silent replacement. |
| B10.C3.S5 Knowledge retirement | Demote stale, contradicted, harmful or out-of-scope practices while preserving tombstone/rationale. | retirement event and retrieval exclusion | Retired knowledge cannot remain active through caches. |

## 5. Chapter 4 — Security Evolution

| Section | Contract | Deliverables | Evidence/gate |
|---|---|---|---|
| B10.C4.S1 Threat review | Periodically update assets, actors, trust boundaries, abuse cases and mitigations from incidents/changes. | threat model revisions | Every material architecture change assessed. |
| B10.C4.S2 Permission audit | Reconcile issued/effective/used grants, roles, services and workers; identify excess and orphan authority. | least-privilege report | Unused/excess access revoked or explicitly justified. |
| B10.C4.S3 Secret rotation | Inventory secret references/owners/ages/scopes and perform safe staged rotation with revocation evidence. | rotation plans/drills | Secret values never enter repo/prompt/evidence. |
| B10.C4.S4 Supply-chain review | Verify dependencies, actions, containers, models, datasets and tools by source, pin, license, vulnerability and provenance. | SBOM/attestation/risk register | Floating/untrusted critical input blocked or sandboxed. |
| B10.C4.S5 Abuse simulation | Exercise prompt injection, confused deputy, replay, data poisoning, exfiltration, privilege escalation and kill failure. | red-team suites/reports | Critical bypass blocks promotion/deployment. |

## 6. Chapter 5 — Constitutional Evolution

| Section | Contract | Deliverables | Evidence/gate |
|---|---|---|---|
| B10.C5.S1 Drift review | Compare implementation, runtime, docs, permissions and operator understanding to constitution/atlas/amendments. | drift report | Unapproved drift quarantined or amended. |
| B10.C5.S2 Amendment candidates | Form amendments from contradiction/evidence with alternatives, consequences, falsifiers and authority impact. | amendment dossier | Convenience alone cannot silently change constitution. |
| B10.C5.S3 Downstream impact | Resolve affected contracts, data, migrations, tests, agents, apps, costs, security and rollback. | impact graph and migration plan | No ratification with unknown critical consumers. |
| B10.C5.S4 Migration | Execute authorized amendment through versioned, staged, reversible migration and compatibility window. | migration evidence | Old/new truth reconciles; failed migration rolls back safely. |
| B10.C5.S5 Ratification | Independent review and operator decision activate amendment, update canonical index and schedule revalidation. | ratification record | Agents cannot ratify their own authority/evaluator changes. |

## 7. Implementation increments

| Increment | Future scope | Gate |
|---|---|---|
| B10-I0 | Freeze learning/evaluation/anchor, SLO, cost and amendment contracts | No self-modification authority |
| B10-I1 | C1 SLO/budget/incident | Measurement and failure response pass |
| B10-I2 | C1 exercises/trends plus C2 cost/capacity | Reliability/cost truth reconciles |
| B10-I3 | C2 placement/storage/portability | Local-first and provider-exit drills pass |
| B10-I4 | C3 discovery/evaluation | Fixed-evaluator anchor comparisons pass |
| B10-I5 | C3 promotion/tool/retirement | Canary, rollback and stale-cache tests pass |
| B10-I6 | C4 threat/permission/secret/supply-chain | Least privilege and safe rotation drills pass |
| B10-I7 | C4 abuse plus C5 drift/amendment/migration/ratification | Governance resists self-expansion |
| B10-I8 | Independent long-horizon regression and constitutional audit | Improvement without anchor/security regression |
| B10-I9 | Program gate, continuing cadence and operator decision | OCE remains governed; no finality claim |

## 8. Co-evolution boundary

Builder/evaluator improvement may use epoch-based fixed evaluators and anchor tasks. During an epoch, the builder cannot modify the evaluator, anchors or scoring policy. Candidate changes promote only after independent comparison, safety/regression gates and operator-controlled policy. Online runtime self-modification remains prohibited.

## 9. PO and Hermes learning separation

PO improvement uses operational observations from OCE/Quant/Larger Lab. Hermes improvement uses personal/supplemental interactions under privacy rules. Cross-promotion requires typed proposal, operator visibility and explicit destination; miscellaneous Hermes behavior cannot become PO doctrine automatically.

## 10. Non-goals

No unbounded self-improvement, autonomous constitutional amendment, automatic live-risk escalation, metric gaming, infinite retention, secret preservation, or claim that the program becomes permanently complete.
