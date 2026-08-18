# QL_EXEC_R0_IMPLEMENTATION_BLOCK_PLAN

Bounded future checkpoints. R0 may revise names/boundaries if evidence supports better. No giant one-shot migration. Each block ends with `human_review_required = true` and `next_checkpoint_authorized = false` unless explicitly overridden.

---

## R1 — GENERIC CONTRACTS + ACCOUNT REGISTRY
Pure schemas/interfaces/config. `AccountRegistry`, `AccountRole`, `PortfolioGroup`, `StrategyAccountBinding`, `RuntimeProfile`, `StrategyAdapter`, `CapitalPolicyAdapter`, `BrokerSession` contracts. Secret-reference contract and config hashing. No TB migration, no broker execution.

## R2 — MT5 BROKER SESSION EXTRACTION
Wrap current MT5 behavior (data adapter + triangular execution layer + DemoEnvironment identity/truth) behind a generic `BrokerSession`. Prove parity with the existing MT5 path.

## R3 — GENERIC SINGLE-INSTANCE RUNTIME
Extract supervisor/worker/runtime-DB/ledger lifecycle into a generic worker. TB runs through a `TBStrategyAdapter` in shadow or an isolated test instance.

## R4 — TB FULL NONREGRESSION MIGRATION
Prove the generic runtime reproduces current TB runtime behavior (full R6.1A/R6.2 parity). Active deployment is NOT switched automatically.

## R5 — MULTI-INSTANCE FLEET + ACCOUNT REGISTRY
Run multiple simulated/demo runtime profiles independently (tb-master-01, rekey-master-01, etc.). FleetSupervisor + per-runtime isolation.

## R6 — PORTFOLIO MASTER + SHARED CAPITAL RESERVATION
Integrate Capital Routing semantics (A/B, H1, f_total) with the atomic shared heat ledger. No production.

## R7 — SECOND STRATEGY ADAPTER
Prove the architecture is truly generic with another validated strategy adapter.

## R8 — MULTI-ACCOUNT DEMO FLEET
Multiple actual demo accounts where available (identity gate per account, terminal/session binding).

## R9 — COPIER-MASTER OBSERVABILITY
Master status only. No follower execution.

## R10 — PRODUCTION READINESS REVIEW
Human authorization only. No production transition is automatic.

---

## Sequencing rationale

Contracts and registry first (zero runtime risk). Broker abstraction second (isolate MT5). Single-instance generic runtime third (prove equivalence with TB before any fleet work). Multi-instance, portfolio, and second-adapter only after single-instance equivalence. Production is last and human-gated.
