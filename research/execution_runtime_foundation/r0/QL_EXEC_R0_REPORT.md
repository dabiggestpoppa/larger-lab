# QL_EXEC_R0_REPORT
## ACCOUNT TOPOLOGY AND RUNTIME GENERALIZATION PLAN

Checkpoint: `QL-EXEC-R0-ACCOUNT-TOPOLOGY-AND-RUNTIME-GENERALIZATION-PLAN`
Status: `PASS` (planning checkpoint; no implementation performed)

---

## 1. Ground truth and drift

- Workstream branch `execution-runtime-foundation` created at frozen base `df5f349e02ac932491cb067df7aff25cb71c50ac`.
- TB authority frozen at `df5f349e` (`TB-R6.2-NATURAL-CANARY-EVIDENCE-PLAN`); stable seal `223fd024` (`TB-R6.1A-STABLE-LOCAL-RUNTIME-SEAL`).
- **Drift detected**: `tb-forward-engine` advanced to `d1200598` (`TB-R6.1B-FIX-WORKER-STATE-LATCH`) — one post-freeze commit, a worker state-latch fix, not strategy math. Per protocol section 60, this checkpoint finishes against the frozen SHA and flags the drift for human review.
- Capital Routing frozen at `40d23712` (`CR-RISK-BLOCK-III-SCALE-SEAL-R1-FAIL-CLOSED-GATE`) — no drift.
- main/OCE at `9f612886` (OCE Block 0 constitutional control ratified).

## 2. What is generic vs TB-specific vs MT5-specific

### Genuinely generic (extract)
Runtime DB (status/heartbeat/errors/NAV), supervisor/worker process separation + backoff + heartbeat + desired-state + PID singleton, log rotation, disk guard, append-only event ledger (dedup key, payload hash, transition validation, derived cache), reconciler pattern, identity-gate pattern, write-ahead intent, broker-truth precedence, market-data adapter Protocol, order-intent lifecycle.

### TB-specific (keep / do not touch)
Triangular basis/z/entry/exit/weight math (`triangular_basis_engine`, `triangular_basis_live`), TB-B weights + leg-sides map, StrategyModelConfig thresholds (PRIMARY 3.0/+0.25, CONTROL 2.5/0.0, stop 6.0, lookback 200), basket lifecycle graph (BROKEN_HEDGE/FLATTENING), canonical symbols GBPAUD/GBPNZD/AUDNZD + `.PRO` broker symbols, frozen CUR_TO_USD, London session/time semantics, synchronized-triangle feed, TB magic values.

### MT5-specific (move to MT5 adapter)
`MT5MarketDataAdapter`, `TriangularExecutionLayer`'s `order_check/order_send/positions_get/orders_get/symbol_info*`, `DemoEnvironment`'s `account_info/terminal_info/symbol_info`, fill-mode probing, `broker_truth`'s `positions_get/orders_get/history_deals_get`, order-send accounting monkeypatch.

### Account-profile (new)
`Ox Securities` / `OxSecurities-Demo` / `USD` / trade_mode DEMO identity gate, symbols, magics, strategy ids → AccountRegistry / StrategyAccountBinding.

## 3. Direct MT5 coupling

4 canonical runtime modules import MetaTrader5 directly: `tb_worker.py`, `engines/tb_r6_demo_canary.py`, `mt5/triangular_execution_layer.py`, `tb_live/snapshot.py` (data-only). The durable domain layer (`state_machine`, `persistence`, `reconciliation`, `market_data`) is MT5-free by construction (enforced by `tb_r3_tests.py`). A large legacy/parallel MT5 surface (`mt5/*` symmetry_trap/p90/dmr/production, `engines/*` harnesses) is deferred and out of the validated TB path.

## 4. Account Control Plane

AccountRegistry, AccountRole (EXCLUSIVE_STRATEGY_MASTER / PORTFOLIO_MASTER / FOLLOWER+MIRROR), PortfolioGroup, StrategyAccountBinding, RuntimeProfile all specified as JSON schemas. Truth states separate configured/reachable/authenticated/identity-matched/execution-enabled. No plaintext credentials. One runtime process per directly controlled account (default). Binding before notional.

## 5. Key architectural correction to TB

TB sizes via a fixed `BASKET_NOTIONAL_USD = 5000.0` constant. The generalized chain inserts account routing and account-equity-denominated sizing between capital admission and notional translation. Percent-of-equity is never computed before the account is known.

## 6. Safety decisions

- Hedging/netting: shared netting + same-symbol overlap → BLOCKED_PENDING_VIRTUAL_LEDGER; unknown account mode → UNSAFE/fail-closed.
- Ownership: deterministic `account_id|runtime_id|strategy_id|generation|intent_id` namespace; one magic per binding, not one global magic; TB's shared primary/control magic is acceptable only because primary is shadow.
- Heat reservation: atomic + idempotent + recoverable; one authoritative shared heat ledger for PORTFOLIO_MASTER (single account-runtime hosting multiple adapters recommended).
- Restart: verify durable state → connect → identity gate → read account/orders/positions/deals → reconstruct → reconcile → warm → only then allow risk; ambiguity blocks.
- External copier: observability only; no follower replication; MASTER validation != FOLLOWER validation.

## 7. Capital Routing boundary

Consumes only the approved decision. Preserves A/B, A1_70_30 (A0_50_50 allowed), H1-1.00-REJ, f_total 1.00%, and `1R = 24.49489742783178 bps` (not a stop). Integration lands in R6, not R0.

## 8. Implementation blocks

R1 contracts+registry → R2 MT5 broker session → R3 generic single-instance runtime → R4 TB full non-regression → R5 multi-instance fleet → R6 portfolio master + shared reservation → R7 second strategy adapter → R8 multi-account demo fleet → R9 copier-master observability → R10 production readiness (human only).

## 9. Invariants held

No active execution code altered. No strategy math altered. No broker execution. No live/production authorization. TB active runtime untouched (read-only inspection).

## 10. Recommendation

R0 PASSES. Recommend `QL-EXEC-R1-GENERIC-CONTRACTS-AND-ACCOUNT-REGISTRY` as the next checkpoint, with `r1_authorized = false` and `human_review_required = true`. STOP for human review.
