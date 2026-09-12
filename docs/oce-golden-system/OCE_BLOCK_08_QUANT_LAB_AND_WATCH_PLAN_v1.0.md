# OCE Golden System
## Block 8 — Quant Lab and Quant Watch Planning Dossier

**Document ID:** OCE-B8-PLAN-001  
**Version:** 1.0  
**Status:** READY_FOR_OPERATOR_REVIEW — BUILD LOCKED  
**Dependency:** B7 deterministic quant foundation  
**Exit gate:** PO and bounded research agents generate registered hypotheses, run governed experiments, monitor validated strategies, and present evidence without execution authority

## 1. Block contract

Block 8 builds the primary domain PO will operate. PO is the high-level Quant Lab/Watch operator; research workers are bounded; Hermes has no default strategy, portfolio, broker or operational-memory access. All research passes through deterministic Block 7 kernels. This block ends at research-to-shadow handoff readiness, not execution.

## 2. Chapter 1 — Research Intelligence

| Section | Contract | Deliverables | Evidence/gate |
|---|---|---|---|
| B8.C1.S1 Source ingestion | Register papers, books, manuals, market observations, datasets and operator notes with rights, provenance and retrieval boundaries. | SourceRecord/Pack pipeline | Exact source supports claims; copyrighted/private payload retention controlled. |
| B8.C1.S2 Hypothesis generation | PO/workers propose mechanism, market, horizon, expected behavior, falsifiers, data and cost sensitivity. | HypothesisSpec | Ideas cannot enter testing without mechanism and falsification criteria. |
| B8.C1.S3 Mechanism critique | Independent critic challenges causality, leakage, crowding, microstructure, regime, confounds and feasibility. | critique report and disposition | Unresolved fatal mechanism issue blocks experiment. |
| B8.C1.S4 Strategy registration | Convert surviving hypothesis into immutable B7 StrategySpec, lineage and research budget. | registry entry and approval state | No anonymous/ad-hoc backtest or retroactive spec. |
| B8.C1.S5 Research prioritization | Rank by expected information value, cost, novelty, dependency, risk and portfolio relevance—not predicted profit alone. | research queue and rationale | Priority changes are versioned and budget-bounded. |

## 3. Chapter 2 — Experiment Orchestration

| Section | Contract | Deliverables | Evidence/gate |
|---|---|---|---|
| B8.C2.S1 Protocol generation | Compile spec into data, baseline, split, engine, costs, metrics, falsification, stress and promotion protocol. | ExperimentProtocol | Protocol frozen before outcome visibility. |
| B8.C2.S2 Worker scheduling | Allocate local first, then authorized disposable compute by capability, data boundary, budget and trust. | scheduler/task contracts | Remote worker receives no durable authority/secrets and returns verifiable artifacts. |
| B8.C2.S3 Result normalization | Validate schemas, units, run IDs, manifests, missing outputs and comparable metrics without hiding differences. | normalized RunResult | Malformed/incomplete/mixed-run results quarantined. |
| B8.C2.S4 Comparative analysis | Compare baselines/variants/regimes/costs with multiplicity and dependence awareness. | comparison dossier | Cherry-picked winner and incompatible comparison rejected. |
| B8.C2.S5 Falsification record | Preserve failed hypotheses, reasons, evidence, parameter search and lessons to prevent repeated data mining. | FalsificationRecord | Failure is searchable; it does not become active strategy memory. |

## 4. Chapter 3 — Quant Watch

| Section | Contract | Deliverables | Evidence/gate |
|---|---|---|---|
| B8.C3.S1 Market state | Compute observable regimes, sessions, liquidity/volatility and data health with versioned definitions. | MarketStateSnapshot | State separates observation from interpretation and handles stale data. |
| B8.C3.S2 Strategy state | Track registered strategy eligibility, expected environment, last evidence, paper/shadow readiness and blockers. | StrategyState projection | Research status cannot imply execution enablement. |
| B8.C3.S3 Data drift | Monitor coverage, schema, missingness, distribution, provider revisions and feature availability. | drift detectors/alerts | Known synthetic drift detected within threshold; false alarms measured. |
| B8.C3.S4 Performance decay | Define evidence-aware deviation, sample sufficiency, cost/capacity change and regime attribution. | decay assessment | Small samples/noise cannot automatically kill or promote strategy. |
| B8.C3.S5 Alert evidence | Produce deduplicated, severity-ranked alerts with cause candidates, evidence, uncertainty and required action. | AlertEnvelope/inbox | Alert is replayable, rate-limited and cannot place orders. |

## 5. Chapter 4 — Operator Experience

| Section | Contract | Deliverables | Evidence/gate |
|---|---|---|---|
| B8.C4.S1 Research inbox | Show hypotheses, critiques, blockers, budgets and pending decisions ordered by operator value. | local UI/API and PO tools | State agrees with canonical registry and access controls. |
| B8.C4.S2 Experiment explorer | Navigate protocol, data, code, parameters, runs, failures, comparisons and manifests. | explorer and evidence links | Any displayed metric traces to exact run and assumption. |
| B8.C4.S3 Strategy dossier | Present mechanism, history, evidence, robustness, costs, capacity, risks, portfolio role and status. | dossier generator | Claims labeled by evidence; uncertainty and failure history visible. |
| B8.C4.S4 Portfolio view | Show research portfolio interactions, exposure simulations, scenario effects and constraints without broker authority. | analytical portfolio surface | Values reconcile to B7 kernels; clearly simulated. |
| B8.C4.S5 Decision journal | Capture operator decisions, rationale, evidence viewed, alternatives, expiry and later outcome. | DecisionRecord UI/API | Decision lineage survives restart and can be reviewed for bias. |

## 6. Chapter 5 — Research Governance

| Section | Contract | Deliverables | Evidence/gate |
|---|---|---|---|
| B8.C5.S1 Agent limits | Bound PO/research-worker datasets, tools, compute, iteration, holdout access and promotion authority. | quant capability policy | Agent cannot access sealed holdout or enable execution. |
| B8.C5.S2 Promotion gates | Require B7 validation, independent review, portfolio/risk assessment and operator decision for stage changes. | research lifecycle | Missing evidence or evaluator conflict blocks promotion. |
| B8.C5.S3 Bias controls | Track search breadth, multiple testing, selective reporting, repeated tuning and narrative after-the-fact. | research audit metrics | Hidden trials and result-dependent protocol changes detected. |
| B8.C5.S4 Reproducibility audit | Re-run random promoted/rejected samples in clean environment and compare manifests/results. | audit reports | Non-reproducible strategy demoted/quarantined. |
| B8.C5.S5 Research-to-shadow handoff | Produce immutable candidate package for B9 containing spec, evidence, risk, limits, monitoring and explicit operator hold. | ShadowCandidatePacket | No orders/credentials; B9 remains separately authorized. |

## 7. Implementation increments

| Increment | Future scope | Gate |
|---|---|---|
| B8-I0 | Freeze research lifecycle, PO/worker limits, source and experiment schemas | Execution capability absent |
| B8-I1 | C1 source/hypothesis/mechanism | Grounded falsifiable ideas registered |
| B8-I2 | C1 strategy/priority plus C2 protocol/scheduling | Frozen protocols and bounded workers pass |
| B8-I3 | C2 normalization/comparison/falsification | Mixed-run/cherry-pick/hidden-failure tests pass |
| B8-I4 | C3 market/strategy/data state | Stale/drift/status separation pass |
| B8-I5 | C3 decay/alerts plus C4 inbox/explorer | Evidence-traceable observation path pass |
| B8-I6 | C4 dossiers/portfolio/journal | Operator decisions and simulated values reconcile |
| B8-I7 | C5 limits/promotion/bias/audit/handoff | Research-to-shadow packet produced with hard hold |
| B8-I8 | Independent leakage, multiplicity, reproducibility, security and usability audit | Zero critical research-governance bypass |
| B8-I9 | Block gate and B9 dependency contract | Operator-only completion; execution remains locked |

## 8. PO and Hermes boundary

PO may operate all Block 8 surfaces under OCE grants. Hermes may receive only operator-approved summaries, reminders or public/light research tasks and cannot retrieve PO operational memory, sealed datasets, strategy parameters, portfolio state, credentials or worker traces by default.

## 9. Non-goals

No broker connectivity, paper/shadow/live orders, autonomous promotion, social signal scraping without rights, performance guarantee, or personal-memory mixing into PO.
