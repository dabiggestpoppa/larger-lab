# CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-R1.1-TRUTH-SYNC-AND-HANDOFF-SEAL — Progress

**Checkpoint:** CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-R1.1-TRUTH-SYNC-AND-HANDOFF-SEAL
**Base:** `00bef1b5` (CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-PLANNING-R1-POSITION-SCALING-ACCOUNT-BOUNDARY-TRUTH-REPAIR)
**Science:** UNCHANGED (890 events · A 432 / B 458 · 826 accepted / 64 rejected)
**Status:** PASS

## What was done

### Issue 1 — summary notional statistics reconciled (event-level source truth)
Recomputed DIRECTLY from `CR_EXEC_R1_EVENT_NOTIONAL_MULTIPLIERS.csv`
(status == ACCEPT_FULL), trusting no prose:

| group | n | median | p95 | p99 | max |
|---|---|---|---|---|---|
| POOLED | 826 | **1.9842×** | **7.6105×** | **16.0364×** | **32.7663×** |
| A | 371 | 3.3513× | 11.4407× | 17.2065× | 32.7663× |
| B | 455 | 1.2850× | 4.1231× | 6.7105× | 22.2754× |

The R1 decision `audit_facts` and R1 report were already correct. The stale
prose (median 2.29× / p95 8.77× / p99 12.9×) lived ONLY in
`CR_EXEC_TRANSLATION_PLANNING_R1_PROGRESS.md` — **repaired** to the canonical
numbers. Engine-recomputed crosscheck matches (same stats from `compute_facts`
frames). `summary_drift_repaired = true`.

### Issue 3 — execution-runtime-foundation authority
At checkpoint start the branch was at `17cfe08e` (QL-EXEC-R0, PASS). The branch
**advanced mid-checkpoint** to `9e11db92` (**QL-EXEC-R1-GENERIC-CONTRACTS-AND-ACCOUNT-REGISTRY, PASS**)
— per the brief, the newer HEAD was recorded and its decision inspected before
freezing. R1's decision explicitly references our R1 repair
(`capital_translation_authority_sha = 00bef1b5`, status PENDING_SEALED_REPAIR).
Frozen: `9e11db928ad3c330fcde06d075e20a6e5b349d89`.

### Issue 4 — TB engineering authority
Frozen: `d12005988ce61170d9bc5478089baa5ce54cc2a9`
(TB-R6.1B-FIX-WORKER-STATE-LATCH) = **PROVEN_ENGINEERING_REFERENCE**, not a CR
dependency. No code imported.

### Issue 5 — Capital Policy vs Translation boundary repaired
`model_heat_after` (and H1, family, requested/admitted f) are immutable
**upstream audit inputs** from the CapitalDecision; Capital Translation Core
consumes them, never recomputes them:
`translation_recomputes_h1 = false`, `translation_recomputes_family = false`,
`translation_recomputes_model_heat = false`. REJECTED → NO_EXPOSURE /
target_notional = 0 without H1 reconsideration. Pure output is the
EconomicExposureTarget with **no broker fields** (lots, margin, buying power,
order type, fill mode, slippage, broker symbol).

## Artifacts (research/capital_routing/risk/block3_execution_translation_r1_1/)
Protocol · source SHA manifest · accepted notional summary CSV · summary drift
audit · cross-workstream authority · capital decision contract · capital
translation request schema · economic target schema · handoff boundary ·
nonregression · test audit · report · decision.

## Tests
16 new narrow tests (`tests/test_exec_translation_planning_r1_1.py`) covering
all 14 required checks; R1 + R1.1 suites 47/47; determinism byte-identical.

## Boundaries
- Capital Routing owns: A/B science, allocation, H1/model heat, f-space, pos_t,
  1R semantics, economic target exposure, translation request, parity.
- execution-runtime-foundation owns: AccountRegistry/Profile/ObservedState,
  BrokerSession, ownership, reservations, runtime/fleet, MT5/TradeLocker,
  generic reconciliation, secrets.
- **Portfolio Master invariant:** A+B = ONE shared capital policy / H1 authority
  / portfolio_group_id. Independent A/B heat ledgers are NOT equivalent.

## Next (NOT started, awaiting human review)
CR-RISK-BLOCK-IV-CAPITAL-TRANSLATION-CORE-D0 — pure deterministic translation
core only; no broker adapter, runtime, MT5, TradeLocker, or fleet management.
