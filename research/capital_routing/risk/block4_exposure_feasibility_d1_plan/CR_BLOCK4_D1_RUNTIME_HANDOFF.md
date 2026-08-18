# CR-BLOCK4-D1 RUNTIME HANDOFF

## Ownership boundary

**Capital Routing owns:** economic exposure target, physical feasibility
science, scientific acceptability of distortion, broker quantity requirements.

**Execution Runtime (execution-runtime-foundation) owns:** AccountRegistry,
BrokerSession, actual instrument observations, orders, fills, reconciliation,
runtime lifecycle, fleet, secrets.

## Interface evidence (read-only, frozen heads)

- execution-runtime-foundation `52e39b13f37812221cab7c283afc302623a61bc6` (QL-EXEC-R2.1-MT5-FILL-POLICY-AND-RESULT-TRUTH-REPAIR)
  — generic contracts: AccountProfile, AccountObservedState, BrokerCapabilities
  (tri-state SUPPORTED/UNSUPPORTED/UNKNOWN, fail closed on UNKNOWN), SymbolInfo
  (digits/point/contract_size/volume_min/volume_step/volume_max/tick), AccountState
  (balance/equity/margin/free margin), MT5 symbol mapping, FakeMT5 fixture contract
  (never promoted to truth).
- tb-forward-engine `b48fd35255b41865026a3cba333ae2a2a0d6a004` (TB-R6.1D-BOOT-FLOW-STACK: supervisor owns watcher + dashboard, full stack auto-starts at logon) — PROVEN
  ENGINEERING REFERENCE only; no code imported into Capital Routing.

## Handoff sequence

    CapitalTranslationCore (D0.1) -> EconomicExposureTarget
    -> D1 feasibility (structural) -> broker quantity requirements
    -> execution-runtime-foundation (account control plane) -> BrokerSession

No broker infrastructure is duplicated in Capital Routing.
