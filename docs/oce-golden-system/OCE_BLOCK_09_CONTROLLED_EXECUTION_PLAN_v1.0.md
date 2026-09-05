# OCE Golden System
## Block 9 — Controlled Execution Planning Dossier

**Document ID:** OCE-B9-PLAN-001  
**Version:** 1.0  
**Status:** READY_FOR_OPERATOR_REVIEW — BUILD LOCKED  
**Dependencies:** B8 research gate; B1 worker/security durability; separate operator authorization  
**Exit gate:** Paper and shadow reconcile under failure; independent risk and approval gates proven; live remains a separately authorized state

## 1. Block contract

Block 9 introduces order lifecycle gradually: paper, shadow, independent risk, broker integrity, then a live-authority design. Planning and even completion of B9.C1–C4 never authorize live capital. PO may propose and supervise; deterministic risk and execution services admit and reconcile; Hermes has no execution access.

## 2. Chapter 1 — Paper Operation

| Section | Contract | Deliverables | Evidence/gate |
|---|---|---|---|
| B9.C1.S1 Order intent | Convert approved strategy state into immutable order proposal with instrument, side, type, size, limits, rationale, expiry and lineage. | OrderIntent schema | Invalid/stale/unregistered strategy intent rejected. |
| B9.C1.S2 Simulated admission | Run the same identity, market-state, limits and approval admission intended for later stages against simulated venue. | admission service and receipt | Agent narrative cannot bypass deterministic denial. |
| B9.C1.S3 Fill state | Model acknowledgements, pending, partial, filled, canceled, rejected, expired and corrected events with realistic assumptions. | paper order state machine | Illegal/out-of-order/duplicate events quarantined. |
| B9.C1.S4 Portfolio impact | Apply fills to canonical paper ledger, cash, exposures, limits and costs. | paper portfolio ledger | Independent reconciliation and property tests pass. |
| B9.C1.S5 Reconciliation | Compare intents, admitted orders, simulated venue events, ledger and evidence every cycle. | reconciliation report | Unexplained break blocks continued paper operation. |

## 3. Chapter 2 — Shadow Operation

| Section | Contract | Deliverables | Evidence/gate |
|---|---|---|---|
| B9.C2.S1 Live data mirror | Consume live/near-live data read-only with timestamp, latency, quality and outage state. | shadow feed adapter | Stale/degraded data blocks or downgrades decision explicitly. |
| B9.C2.S2 Broker observation | Read account/instrument/order capability metadata under read-only credentials where supported. | observation adapter and boundary | No order endpoint/credential scope enabled during observation. |
| B9.C2.S3 Counterfactual fills | Produce venue-aware hypothetical orders/fills without submission, including spread, latency, partial/non-fill. | shadow simulator | Counterfactual clearly separated from broker fact. |
| B9.C2.S4 Divergence | Measure paper/shadow/model versus observed market and later broker outcomes by cause class. | divergence ledger | Large/unexplained divergence blocks promotion. |
| B9.C2.S5 Shadow gate | Require duration/sample, data health, reconciliation, risk drills, incidents, capacity and operator review. | shadow gate packet | No automatic transition; live credentials absent. |

## 4. Chapter 3 — Independent Risk

| Section | Contract | Deliverables | Evidence/gate |
|---|---|---|---|
| B9.C3.S1 Rule versioning | Freeze deterministic limits, scope, effective time, owner, change approval and rollback. | RiskRuleSet registry | Every admission cites exact active rules. |
| B9.C3.S2 Deterministic admission | Independently evaluate identity, grant, strategy, market/data, account, sizing, exposure, loss, liquidity and order semantics. | risk decision engine | PO/execution adapter cannot override deny. |
| B9.C3.S3 Kill controls | Provide operator, automatic and infrastructure kill states that block new orders and define cancel/flatten policies separately. | kill-state machine and drills | Kill survives restart/network partition and is fail-closed. |
| B9.C3.S4 Limit breach | Define prevention, detection, containment, notification, cancellation, reconciliation and incident escalation. | breach playbooks/tests | Synthetic breaches trigger expected safe state. |
| B9.C3.S5 Risk audit | Independently replay every decision using immutable inputs/rules and compare results. | risk audit report | Non-replayable/mismatched decision is critical incident. |

## 5. Chapter 4 — Execution Integrity

| Section | Contract | Deliverables | Evidence/gate |
|---|---|---|---|
| B9.C4.S1 Broker adapters | Certify per broker/venue instruments, order types, auth, rate limits, errors, sessions and idempotency. | adapter conformance pack | Unsupported semantics rejected; provider independence preserved. |
| B9.C4.S2 Acknowledgements | Distinguish submitted, transport-accepted, broker-accepted, venue-acknowledged and unknown. | acknowledgement model | Timeout never becomes assumed rejection or fill. |
| B9.C4.S3 Partial fills | Handle multi-event fills, fees, average price, remaining quantity, cancel/replace and corrections. | execution ledger | Duplicate/out-of-order/corrected events reconcile exactly. |
| B9.C4.S4 Restart recovery | On crash, query external truth, reconstruct local state, fence old workers and resume only after reconciliation. | recovery coordinator | Crash at every lifecycle point causes no duplicate order. |
| B9.C4.S5 External reconciliation | Compare broker statements, positions, cash, orders, fills and fees to OCE at defined intervals. | reconciliation service and breaks queue | Any material unexplained break blocks new risk. |

## 6. Chapter 5 — Live Authority

| Section | Contract | Deliverables | Evidence/gate |
|---|---|---|---|
| B9.C5.S1 Credential boundary | Store broker credentials outside agents/repos, scope minimally, rotate, audit access and separate read/trade/withdrawal. | secret references and access policy | Withdrawal capability absent; secret never enters prompt/log/evidence. |
| B9.C5.S2 Operator approval | Present strategy, account, instruments, limits, duration, capital, risks, rollback and kill test for explicit signature. | LiveCapabilityGrant workflow | Approval is scoped/expiring/revocable and cannot be inferred from chat. |
| B9.C5.S3 Capital envelope | Enforce maximum capital, per-trade/strategy/day loss, exposure, turnover and staged ramp independently. | capital envelope engine | Attempts beyond envelope denied and audited. |
| B9.C5.S4 Live monitoring | Monitor data, orders, fills, positions, P&L, risk, latency, divergence and service health with operator alerts. | live operations view/runbook | Detection and response drills meet defined objectives. |
| B9.C5.S5 Revocation | Stop new orders, revoke grants/credentials, fence workers, reconcile and choose cancel/flatten/hold through policy. | revocation drill and evidence | Operator can reliably return system to no-new-risk state. |

## 7. Windows and MT5 boundary

MT5 is a separately admitted Windows worker from B1.C5.S4, never OCE's durable control plane. Prefer deterministic terminal/config/report interfaces over GUI clicking. Where GUI automation is unavoidable, run it in an isolated disposable Windows desktop/VM with screenshot/action trace, stable display profile, application/window identity checks, bounded coordinates or accessibility selectors, focus verification, timeout, kill control and human-visible replay. GUI success never proves broker state; terminal/broker reports and OCE reconciliation do.

MQL code authoring, compilation and backtests are permitted only in local/research stages with versioned source, terminal build, data/model settings, report hashes and no live credential. An agent may open/click MT5 only under a task-scoped worker grant; it cannot inherit broker authority.

## 8. Implementation increments

| Increment | Future scope | Gate |
|---|---|---|
| B9-I0 | Freeze execution lifecycle, no-live invariant, adapters and evidence contracts | Explicit operator authorization; credentials absent |
| B9-I1 | C1 order intent/admission/state | Paper lifecycle and denials pass |
| B9-I2 | C1 portfolio/reconciliation plus C2 live-data mirror | Paper ledger and data quality reconcile |
| B9-I3 | C2 observation/counterfactual/divergence/gate | Read-only shadow evidence sufficient |
| B9-I4 | C3 rules/admission/kill | Independent risk and kill drills pass |
| B9-I5 | C3 breaches/audit plus C4 adapter/acks | Replay and unknown-state handling pass |
| B9-I6 | C4 fills/restart/external reconciliation, including MT5 boundary where authorized | No duplicate order; breaks block risk |
| B9-I7 | C5 live-authority controls implemented disabled and tested with fakes | Live remains disabled; revocation verified |
| B9-I8 | Independent red-team, failure, broker-simulation and evidence audit | Zero capital/authority bypass |
| B9-I9 | Paper/shadow gate packet and separate live-authorization hold | Completion never equals live approval |

## 9. Mandatory promotion gates

Paper, shadow and live are separate states with separate operator decisions. Each transition requires source/data health, sample duration, reconciliation, incidents, realistic costs/fills, independent risk, recovery/kill drills, credential scope and unresolved-risk review. Failure at a later stage demotes to a safe earlier state.

## 10. Non-goals

No autonomous live enablement, withdrawal, Telegram trading commands, Hermes execution, PO risk override, hidden broker state, guaranteed fills, martingale authority, or GUI-only reconciliation.
