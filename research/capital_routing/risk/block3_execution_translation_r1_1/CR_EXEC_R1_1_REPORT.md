# CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-R1.1 -- Report

**Checkpoint:** CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-R1.1-TRUTH-SYNC-AND-HANDOFF-SEAL · **Status:** PASS
**Base:** 00bef1b5b52db63c22a29b3287799742631930db · **Parent:** CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-PLANNING-R1-POSITION-SCALING-ACCOUNT-BOUNDARY-TRUTH-REPAIR (science UNCHANGED)

## Issue 1 — summary notional statistics reconciled (event-level source truth)
Recomputed directly from `CR_EXEC_R1_EVENT_NOTIONAL_MULTIPLIERS.csv`
(status == ACCEPT_FULL). Canonical stats:

| group | n | min | p1 | p5 | p25 | median | p75 | p95 | p99 | max |
|---|---|---|---|---|---|---|---|---|---|---|
| POOLED | 826 | 0.1352 | 0.2693 | 0.5145 | 1.1023 | **1.9842** | 3.5134 | **7.6105** | **16.0364** | **32.7663** |
| A | 371 | 0.4713 | 0.6202 | 1.0231 | 2.1407 | **3.3513** | 5.3053 | **11.4407** | 17.2065 | **32.7663** |
| B | 455 | 0.1352 | 0.2500 | 0.4313 | 0.7952 | **1.2850** | 2.0116 | **4.1231** | 6.7105 | **22.2754** |

Drift audit: R1 decision audit_facts match canonical (True);
R1 report prose correct; R1 progress file contained stale values
(median 2.29x / p95 8.77x / p99 12.9x) — **repaired** to the canonical numbers
(True). Engine-recomputed crosscheck:
True.
`summary_drift_repaired = True`.

## Issue 3/4 — cross-workstream authority frozen
- execution-runtime-foundation: `9e11db928ad3c330fcde06d075e20a6e5b349d89`
  (QL-EXEC-R1-GENERIC-CONTRACTS-AND-ACCOUNT-REGISTRY, PASS)
  — advanced mid-checkpoint from 17cfe08e
  (R0) to the newer HEAD; newer decision inspected and frozen.
- tb-forward-engine: `d12005988ce61170d9bc5478089baa5ce54cc2a9`
  (TB-R6.1B-FIX-WORKER-STATE-LATCH, PROVEN_ENGINEERING_REFERENCE)
Both audited READ-ONLY; no commits to either branch.

## Issue 5 — Capital Policy / Translation boundary repaired
CapitalTranslationRequest now carries the immutable CapitalDecisionReference
(decision_id, policy_id, requested_f_pct, admitted_f_pct, status,
model_heat_before, model_heat_after, decision_timestamp, configuration_hash).
Capital Translation Core consumes these values; it does NOT recompute H1,
family, or model heat (`translation_recomputes_h1 = false`,
`translation_recomputes_family = false`). REJECTED -> NO_EXPOSURE, zero
notional, no H1 reconsideration. Pure output = EconomicExposureTarget with no
broker fields.

## Nonregression (science unchanged)
890 events · A 432 · B 458 · accepted 826 (A 371 / B 455) ·
rejected 64 · risk_unit 24.49489742783178 bps (NOT a hard stop) ·
gross parity PASS (max err 6.94e-18) ·
research-modeled net parity PASS · execution net parity
BROKER_DEPENDENT_UNRESOLVED · H1 parity PASS · worst observed account impacts
A -2.5588% /
B -0.9939%.

## Decision
summary_drift_repaired = true · capital_policy_translation_boundary_repaired = true ·
broker_execution_performed = false · implementation_ready = true ·
implementation_authorized = false · production_authorized = false ·
human_review_required = true.
Next (NOT started): CR-RISK-BLOCK-IV-CAPITAL-TRANSLATION-CORE-D0.
