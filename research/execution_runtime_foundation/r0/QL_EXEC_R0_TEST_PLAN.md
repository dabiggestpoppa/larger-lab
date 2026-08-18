# QL_EXEC_R0_TEST_PLAN

Designed for future checkpoints (R1+). R0 plans only; no tests are required to pass for R0 itself.

---

## 1. Registry / schema

- account schema validation (required fields, enums).
- duplicate account_id rejected.
- duplicate runtime_id rejected.
- strategy-account binding validation (role, symbols, namespace).
- portfolio group binding (one capital policy, strategy allowlist).
- secret exclusion from committed config (no `password|secret|token|api_key|private_key` values).

## 2. Identity gate

- identity mismatch (wrong company/server/currency/environment) → EXECUTION BLOCKED.
- wrong account currency → blocked.
- wrong server → blocked.
- wrong environment (REAL vs DEMO) → blocked.

## 3. State / process isolation

- runtime state isolation (A cannot read B's DB/ledger/log).
- ledger isolation.
- log isolation.
- PID singleton per runtime (second instance fails closed).
- multiple independent runtimes coexist.

## 4. Broker abstraction parity

- broker adapter parity (MT5 vs Sim vs Replay on the same scenarios).
- fake broker parity (TB full-engine harness scenarios: all-fill, per-leg reject, placed-not-filled, fill-timeout, spread-explosion, wrong-side, wrong-size).
- direct MT5 coupling elimination (BrokerSession is the only MT5-importing module set).

## 5. Ownership / safety

- ownership namespace uniqueness (no two bindings share magic+comment).
- foreign position preserved (never modified).
- hedging ticket isolation.
- netting same-symbol overlap blocked.

## 6. Reservation / concurrency

- atomic heat reservation.
- simultaneous admissions do not exceed cap.
- restart with active reservation.
- restart with active position.

## 7. Reconciliation / idempotency

- unknown broker position → block.
- missing ledger intent for owned exposure → block.
- duplicate event → dedup, no double order.
- partial fill.
- failed order.
- stale account state.
- stale broker state.

## 8. Fleet / lifecycle

- fleet heartbeat aggregation.
- intentional stop (no auto-restart).
- unexpected worker death (bounded backoff restart).

## 9. TB regression

- full TB parity suite (see `QL_EXEC_R0_TB_NONREGRESSION_PLAN.md`): signal parity, market-data synchronization, shadow-only primary, control demo behavior, identity gate, ownership, foreign-position protection, write-ahead lifecycle, reconciliation, restart recovery, dashboard PnL, generation semantics.
