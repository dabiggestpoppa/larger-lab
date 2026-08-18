# QL_EXEC_R0_PROTOCOL
## ACCOUNT TOPOLOGY AND RUNTIME GENERALIZATION PLAN

Checkpoint: `QL-EXEC-R0-ACCOUNT-TOPOLOGY-AND-RUNTIME-GENERALIZATION-PLAN`

---

## 0. Status

`PLANNING ONLY`. This checkpoint produces architecture and extraction artifacts. It does not refactor the runtime, does not open broker sessions, does not execute trades, and does not alter any active deployment.

`human_review_required = true` and `next_checkpoint_authorized = false` at the end of this checkpoint unless the human explicitly says otherwise.

---

## 1. Purpose

Generalize the proven TB Forward execution/runtime pattern into a reusable Quant Lab execution substrate that can operate multiple strategies, runtime instances, broker sessions, accounts, portfolio masters, and strategy masters — **without modifying sealed strategy science**.

This is execution / account infrastructure. It is not a new trading strategy.

---

## 2. Authority (frozen for this checkpoint)

| Authority | Branch | SHA | Role |
|---|---|---|---|
| TB Forward | `tb-forward-engine` | `df5f349e02ac932491cb067df7aff25cb71c50ac` | Canonical engineering reference for persistent runtime, supervisor/worker, runtime DB, write-ahead intent, basket ledger, broker ownership, reconciliation, restart recovery, execution safety, demo identity gates, PnL ownership, heartbeat, dashboard, desired state, atomic basket execution, broker truth, partial-failure recovery, market-state handling. |
| Capital Routing | `capital-routing` | `40d237123ac2b709cc0ebce1d7f057bbfde25dab` | Scientific authority for family allocation, portfolio f semantics, gross heat (H1), admission, robust scale region, A/B interaction. |
| main / OCE | `main` | `9f61288679eea56a298e08f718c314f2ca509bc5` | Operator sovereignty, truth hierarchy, fail-closed behavior, evidence promotion, authority boundaries, drift control, persistent project memory. |
| This workstream | `execution-runtime-foundation` | branch created at `df5f349e` | Owns only the reusable account/runtime substrate and R0 artifacts. |

TB strategy science is READ-ONLY. Capital Routing scientific semantics are READ-ONLY. OCE governance is READ-ONLY from this branch.

---

## 3. Scope boundaries

IN SCOPE (this checkpoint):
- Comprehensive audit of the frozen TB Forward runtime.
- Classification of every relevant component as generic / TB-specific / MT5-specific / account-profile / test-harness.
- Direct MT5 coupling inventory.
- Conceptual Account Control Plane and its schemas (AccountRegistry, AccountRole, PortfolioGroup, StrategyAccountBinding, RuntimeProfile).
- Conceptual StrategyAdapter, CapitalPolicyAdapter, and BrokerSession contracts.
- Broker capability, hedging/netting compatibility, and ownership namespace design.
- State isolation, atomic heat reservation, restart/reconciliation, fleet supervision, and external-copier boundary plans.
- Bounded implementation block plan and test plan.
- TB non-regression plan.

OUT OF SCOPE (this checkpoint, and any of it requires separate authorization):
- Runtime refactor, file moves, or new broker API code.
- Real account sessions or broker execution.
- TradeLocker integration.
- Copier follower replication.
- Live or production sizing, Kelly, or dynamic drawdown sizing.

---

## 4. Method

1. `git fetch`; verify authoritative reference branches and record exact SHAs.
2. Freeze authority SHAs. If an authority moved, finish against the frozen SHA and record the drift (section 60).
3. Audit the TB runtime tree at `df5f349e` read-only.
4. Audit Capital Routing at `40d23712` read-only.
5. Audit main/OCE governance read-only.
6. Emit the 30 R0 artifacts under `research/execution_runtime_foundation/r0/`.
7. Commit and push only on `execution-runtime-foundation`.

---

## 5. Fundamental execution lifecycle (preserved, not reinvented)

STRATEGY SCIENCE → signal/decision → durable intent → capital decision (where applicable) → account binding → execution translation → execution gate → broker submission → broker verification → durable state → reconciliation → restart recovery → runtime telemetry.

---

## 6. Account routing order (binding before notional)

VALID EVENT → strategy identity → family / capital policy → requested_f → portfolio heat admission → ACCOUNT ROUTING → account_id → account role validation → account-state snapshot → account equity → normalized risk/sensitivity budget → notional → broker quantity → actual translated heat → order intent.

Percent-of-equity is never computed until the account whose equity is the denominator is known.

---

## 7. Pass gate

R0 passes only if all of the following are true:
- TB runtime comprehensively audited.
- generic vs TB-specific vs MT5-specific boundaries explicit.
- direct MT5 coupling inventoried.
- Account Control Plane fully specified.
- account roles conceptually frozen.
- shared portfolio vs exclusive master semantics explicit.
- broker abstraction coherent.
- state isolation coherent.
- hedging/netting safety explicit.
- ownership namespace explicit.
- atomic reservation architecture explicit.
- restart/reconciliation plan explicit.
- fleet supervision explicit.
- Capital Routing boundary explicit.
- TB non-regression path explicit.
- implementation divided into bounded checkpoints.
- no active execution code altered.

If any fundamental account/execution semantic remains unresolved, status is `BLOCKED_R0_ARCHITECTURE`. Ambiguity is recorded, not hidden.

---

## 8. Red lines (never violated by this workstream)

- No plaintext credentials in git.
- No modification of TB strategy math, z thresholds, weights, control logic, primary shadow state, broker gates, lot formulas, current account identity, or deployment runtime.
- No interruption of the active TB deployment.
- No push to `tb-forward-engine`, `capital-routing`, strategy-foundry branches, MVE branches, or `main`.
- No live trading, real-money deployment, broker production access, production account sizing, MT5/TradeLocker live execution, Kelly, or dynamic drawdown sizing.
