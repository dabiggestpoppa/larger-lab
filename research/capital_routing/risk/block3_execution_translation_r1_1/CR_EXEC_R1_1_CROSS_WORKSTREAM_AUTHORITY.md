# Cross-workstream authority (frozen, read-only)

Verified after `git fetch` on the parent repository. Neither branch was
modified by this checkpoint.

## execution-runtime-foundation
- **HEAD (frozen):** `9e11db928ad3c330fcde06d075e20a6e5b349d89` — QL-EXEC-R1-GENERIC-CONTRACTS-AND-ACCOUNT-REGISTRY — **PASS**
- At checkpoint start: `17cfe08eccadf77f5089f7c776bafdf671fbf5cd`
  (QL-EXEC-R0-ACCOUNT-TOPOLOGY-AND-RUNTIME-GENERALIZATION-PLAN, PASS).
- **Branch advanced mid-checkpoint** (R0 -> R1); per the brief the newer HEAD
  was recorded and its decision inspected before freezing.
- Newer-decision notes: QL-EXEC-R1 freezes generic contracts + account registry; references capital_translation_authority_sha 00bef1b5 (our R1 repair) as PENDING_SEALED_REPAIR.
- Role: future generic execution dependency; Capital Routing consumes its eventual interfaces, never copies runtime code.
- Audit mode: READ_ONLY. Modified: False.

## tb-forward-engine
- **HEAD:** `d12005988ce61170d9bc5478089baa5ce54cc2a9` — TB-R6.1B-FIX-WORKER-STATE-LATCH — PROVEN_ENGINEERING_REFERENCE
- Role: engineering reference for ledger/idempotency/reconciliation patterns; NOT a Capital Routing dependency; no code imported.
- Audit mode: READ_ONLY. Modified: False.

## Portfolio Master invariant
A + B were scientifically validated as ONE shared portfolio (A1_70_30 + H1).
Preserve ONE shared capital policy, ONE H1 heat authority, ONE
portfolio_group_id scope for canonical execution. Independent A/B accounts with
independent heat ledgers are NOT equivalent to the sealed portfolio. If
physical execution is ever distributed across accounts, shared portfolio
admission must remain globally authoritative (later execution architecture).

## Authority split
**Capital Routing owns:** event/family science, allocation, H1/model heat,
f-space, pos_t, R-unit semantics, economic target exposure, translation
request, research parity.
**execution-runtime-foundation owns/will own:** AccountProfile,
AccountObservedState, ExecutionAuthority, AccountRegistry,
StrategyAccountBinding, RuntimeProfile, BrokerSession, ownership, reservation
infrastructure, runtime/fleet lifecycle.
