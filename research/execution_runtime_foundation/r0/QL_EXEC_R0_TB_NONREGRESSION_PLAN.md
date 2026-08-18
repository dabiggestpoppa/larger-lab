# QL_EXEC_R0_TB_NONREGRESSION_PLAN

No migration receives authority without TB regression evidence. TB is the reference implementation; the stable local runtime remains authoritative and must not be interrupted.

---

## 1. Frozen invariants that must be preserved

- Strategy math: basis formula, rolling-z (lookback 200, ddof=0, previous-bars-only), direction convention, TB-B weighting, z=6.0 stop semantics, session semantics (London 3-12 EST, fixed UTC-5, no DST), hard-exit semantics, re-entry semantics, cost assumptions.
- Signal parity: 265,809 bars / 194 primary / 405 control events / 0 mismatches (R1.1).
- Market-data synchronization: raw MT5 bar-open-time strategy key, closed-bar semantics, forming-bar exclusion.
- Primary shadow-only behavior (PRIMARY never executes).
- Control demo behavior (CONTROL executes only on the approved demo environment).
- Account identity gate (`Ox Securities` / `OxSecurities-Demo` / trade_mode 0 / USD).
- Broker ownership (magic + `TB|` comment token OR persisted fill linkage).
- Foreign-position protection (never touched).
- Write-ahead lifecycle (intent persisted before any order).
- Broker reconciliation outcomes (BLOCKED_LEDGER / BLOCKED_RECONCILIATION).
- Restart recovery (adopt open basket, never flatten without ownership).
- Dashboard PnL semantics (owned deals + open positions only).
- Deployment generation semantics (GEN-* baseline).

---

## 2. Regression gates per implementation block

| Block | Gate |
|---|---|
| R1 (contracts/registry) | No TB code touched; TB runtime byte-identical. |
| R2 (MT5 broker session) | BrokerSession reproduces the MT5MarketDataAdapter + execution layer behavior; parity harness passes. |
| R3 (generic single-instance runtime) | TB adapter drives the generic worker; identical lifecycle in shadow/isolated test. |
| R4 (TB full migration) | Generic runtime reproduces current TB runtime behavior; active deployment NOT auto-switched. |
| R5+ | Multiple runtimes; TB runtime still passes the R4 suite unchanged. |

---

## 3. Non-regression evidence sources

- `research/tb_forward/r6_1a/TB_R6_1A_*` (stable runtime seal artifacts) — the current behavior baseline.
- `research/tb_forward/r6_2/TB_R6_2_NATURAL_CANARY_EVIDENCE_PLAN.md` — the natural-canary forward plan (parked; do not disturb).
- Existing parity CSVs (`TB_R11_Z_NONREGRESSION.csv`, `TB_R11_WEIGHT_PARITY.csv`, R1.1 weight/z parity).

---

## 4. Rules

- Do not improve or optimize TB during extraction.
- Do not change z thresholds, weighting, control logic, primary shadow state, broker gates, lot formulas, account identity, or deployment runtime.
- Prove TB equivalence before any generic migration is authorized.
- The active TB deployment (stable local lineage, Task Scheduler task, DB, ledger, broker login) is never stopped, restarted, or force-traded during this planning checkpoint — all inspection is READ-ONLY.

---

## 5. Post-freeze drift note

`tb-forward-engine` advanced one commit after the frozen authority: `d1200598 TB-R6.1B-FIX-WORKER-STATE-LATCH` (ONLINE_MARKET_CLOSED no longer sticks after market recovery). This checkpoint audits the frozen `df5f349e`. Before R2-R4 migration, re-baseline against the human's chosen TB authority (either adopt the R6.1B fix or stay on the frozen SHA deliberately).
